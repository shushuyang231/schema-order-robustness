"""Post-hoc exploratory comparison of the two completed SOB experiments.

This module never changes the frozen confirmatory or replication decisions.  It
uses the shared 100-record design to estimate paired model differences and to
explore whether a small, fixed set of schema features covaries with record-level
representation sensitivity.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import itertools
import json
import math
import random
import statistics
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from evaluate_sob_repeated_pilot import excess_disagreement, holm_adjust, percentile
from evaluate_sob_metamorphic import token_normalized_value
from sob_metamorphic import compact_json, load_jsonl


SEED = 20260718
RESAMPLES = 5000
FEATURES = (
    "schema_chars",
    "total_properties",
    "max_schema_depth",
    "description_chars",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--public-input", type=Path, required=True)
    parser.add_argument("--sonnet-manifest", type=Path, required=True)
    parser.add_argument("--sonnet-predictions", type=Path, required=True)
    parser.add_argument("--sonnet-report", type=Path, required=True)
    parser.add_argument("--gpt-manifest", type=Path, required=True)
    parser.add_argument("--gpt-predictions", type=Path, required=True)
    parser.add_argument("--gpt-report", type=Path, required=True)
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, required=True)
    parser.add_argument("--record-output", type=Path, required=True)
    return parser.parse_args()


def stable_seed(label: str) -> int:
    digest = hashlib.sha256(label.encode("utf-8")).digest()
    return SEED + int.from_bytes(digest[:4], "big")


def bootstrap_mean_ci(values: list[float], label: str) -> list[float]:
    rng = random.Random(stable_seed("bootstrap:" + label))
    size = len(values)
    estimates = [
        statistics.fmean(values[rng.randrange(size)] for _ in range(size))
        for _ in range(RESAMPLES)
    ]
    return [percentile(estimates, 0.025), percentile(estimates, 0.975)]


def sign_flip_p(values: list[float], label: str) -> float:
    observed = abs(statistics.fmean(values))
    rng = random.Random(stable_seed("sign:" + label))
    exceed = 0
    for _ in range(RESAMPLES):
        estimate = abs(
            statistics.fmean(value if rng.random() < 0.5 else -value for value in values)
        )
        if estimate >= observed - 1e-12:
            exceed += 1
    return (exceed + 1) / (RESAMPLES + 1)


def average_ranks(values: list[float]) -> list[float]:
    ordered = sorted(enumerate(values), key=lambda item: item[1])
    ranks = [0.0] * len(values)
    cursor = 0
    while cursor < len(ordered):
        end = cursor + 1
        while end < len(ordered) and ordered[end][1] == ordered[cursor][1]:
            end += 1
        rank = (cursor + 1 + end) / 2
        for position in range(cursor, end):
            ranks[ordered[position][0]] = rank
        cursor = end
    return ranks


def pearson(left: list[float], right: list[float]) -> float:
    left_mean = statistics.fmean(left)
    right_mean = statistics.fmean(right)
    numerator = sum(
        (a - left_mean) * (b - right_mean) for a, b in zip(left, right, strict=True)
    )
    left_scale = math.sqrt(sum((value - left_mean) ** 2 for value in left))
    right_scale = math.sqrt(sum((value - right_mean) ** 2 for value in right))
    return numerator / (left_scale * right_scale) if left_scale and right_scale else 0.0


def spearman(left: list[float], right: list[float]) -> float:
    return pearson(average_ranks(left), average_ranks(right))


def permutation_correlation_p(left: list[float], right: list[float], label: str) -> float:
    observed = abs(spearman(left, right))
    rng = random.Random(stable_seed("correlation:" + label))
    permuted = list(right)
    exceed = 0
    for _ in range(RESAMPLES):
        rng.shuffle(permuted)
        if abs(spearman(left, permuted)) >= observed - 1e-12:
            exceed += 1
    return (exceed + 1) / (RESAMPLES + 1)


def bootstrap_spearman_ci(left: list[float], right: list[float], label: str) -> list[float]:
    rng = random.Random(stable_seed("bootstrap-correlation:" + label))
    size = len(left)
    estimates: list[float] = []
    for _ in range(RESAMPLES):
        indices = [rng.randrange(size) for _ in range(size)]
        sampled_left = [left[index] for index in indices]
        sampled_right = [right[index] for index in indices]
        estimates.append(spearman(sampled_left, sampled_right))
    return [percentile(estimates, 0.025), percentile(estimates, 0.975)]


def schema_features(schema: dict[str, Any]) -> dict[str, int]:
    totals = {
        "total_properties": 0,
        "object_nodes": 0,
        "array_nodes": 0,
        "leaf_nodes": 0,
        "required_entries": 0,
        "description_chars": 0,
        "max_schema_depth": 0,
    }

    def visit(node: Any, depth: int) -> None:
        if not isinstance(node, dict):
            return
        totals["max_schema_depth"] = max(totals["max_schema_depth"], depth)
        description = node.get("description")
        if isinstance(description, str):
            totals["description_chars"] += len(description)
        required = node.get("required")
        if isinstance(required, list):
            totals["required_entries"] += len(required)
        properties = node.get("properties")
        if isinstance(properties, dict):
            totals["object_nodes"] += 1
            totals["total_properties"] += len(properties)
            for child in properties.values():
                visit(child, depth + 1)
        else:
            schema_type = node.get("type")
            if schema_type == "array":
                totals["array_nodes"] += 1
                visit(node.get("items"), depth + 1)
            else:
                totals["leaf_nodes"] += 1

    visit(schema, 1)
    totals["top_level_properties"] = len(schema.get("properties", {}))
    totals["schema_chars"] = len(compact_json(schema))
    return totals


def normalized_signature(row: dict[str, Any]) -> str:
    parsed = row.get("parsed_output")
    if isinstance(parsed, dict):
        return compact_json(token_normalized_value(parsed), sort_keys=True)
    return f"__PARSE_FAILURE__:{row.get('parse_status')}"


def load_model_cells(
    manifest_path: Path, prediction_path: Path
) -> tuple[dict[str, Any], dict[tuple[str, str], list[str]], dict[str, Any]]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    latest: dict[tuple[str, str], dict[str, Any]] = {}
    raw_rows = load_jsonl(prediction_path)
    for row in raw_rows:
        if row.get("status") == "ok":
            latest[(str(row["record_id"]), str(row["variant"]))] = row
    expected = {
        (record_id, condition["name"])
        for record_id in manifest["record_ids"]
        for condition in manifest["conditions"]
    }
    if set(latest) != expected:
        raise ValueError(
            f"Coverage mismatch for {manifest_path}: missing={len(expected-set(latest))}, "
            f"extra={len(set(latest)-expected)}"
        )
    condition_to_variant = {
        condition["name"]: condition["schema_variant"]
        for condition in manifest["conditions"]
    }
    cells: dict[tuple[str, str], list[str]] = defaultdict(list)
    for record_id in manifest["record_ids"]:
        for condition in manifest["conditions"]:
            condition_name = condition["name"]
            row = latest[(record_id, condition_name)]
            cells[(record_id, condition_to_variant[condition_name])].append(
                normalized_signature(row)
            )
    repeats = int(manifest["repeats_per_variant"])
    if any(len(signatures) != repeats for signatures in cells.values()):
        raise ValueError("At least one model/record/variant cell has the wrong repeat count")
    log_audit = {
        "raw_line_count": len(raw_rows),
        "successful_line_count": sum(row.get("status") == "ok" for row in raw_rows),
        "error_line_count": sum(row.get("status") != "ok" for row in raw_rows),
        "unique_successful_task_count": len(latest),
    }
    return manifest, dict(cells), log_audit


def record_effects(
    manifest: dict[str, Any], cells: dict[tuple[str, str], list[str]]
) -> dict[str, dict[str, float]]:
    effects: dict[str, dict[str, float]] = {}
    for record_id in manifest["record_ids"]:
        original = cells[(record_id, "original")]
        effects[record_id] = {
            variant: excess_disagreement(original, cells[(record_id, variant)])
            for variant in manifest["schema_variants"]
            if variant != "original"
        }
    return effects


def main() -> int:
    args = parse_args()
    public = {row["record_id"]: row for row in load_jsonl(args.public_input)}
    sonnet_manifest, sonnet_cells, sonnet_log = load_model_cells(
        args.sonnet_manifest, args.sonnet_predictions
    )
    gpt_manifest, gpt_cells, gpt_log = load_model_cells(
        args.gpt_manifest, args.gpt_predictions
    )
    if sonnet_manifest["record_ids"] != gpt_manifest["record_ids"]:
        raise ValueError("The model experiments do not share ordered record IDs")
    if sonnet_manifest["conditions"] != gpt_manifest["conditions"]:
        raise ValueError("The model experiments do not share identical conditions")
    record_ids = list(sonnet_manifest["record_ids"])
    if set(public) != set(record_ids):
        raise ValueError("Public data and experiment manifests have different record IDs")

    sonnet_report = json.loads(args.sonnet_report.read_text(encoding="utf-8"))
    gpt_report = json.loads(args.gpt_report.read_text(encoding="utf-8"))
    if not sonnet_report["operational_gate_passed"] or not gpt_report["operational_gate_passed"]:
        raise ValueError("At least one source experiment failed its operational gate")

    sonnet_effects = record_effects(sonnet_manifest, sonnet_cells)
    gpt_effects = record_effects(gpt_manifest, gpt_cells)
    variants = [variant for variant in sonnet_manifest["schema_variants"] if variant != "original"]

    paired_comparisons: dict[str, dict[str, Any]] = {}
    paired_raw_p: dict[str, float] = {}
    for variant in variants:
        sonnet_values = [sonnet_effects[record_id][variant] for record_id in record_ids]
        gpt_values = [gpt_effects[record_id][variant] for record_id in record_ids]
        deltas = [left - right for left, right in zip(sonnet_values, gpt_values, strict=True)]
        raw_p = sign_flip_p(deltas, "paired-model-delta:" + variant)
        paired_raw_p[variant] = raw_p
        paired_comparisons[variant] = {
            "sonnet_mean_normalized_excess": statistics.fmean(sonnet_values),
            "gpt_mean_normalized_excess": statistics.fmean(gpt_values),
            "sonnet_minus_gpt_mean_difference": statistics.fmean(deltas),
            "difference_ci95": bootstrap_mean_ci(deltas, "paired-model-delta:" + variant),
            "difference_sign_flip_p": raw_p,
            "record_direction_counts": {
                "sonnet_greater": sum(delta > 0 for delta in deltas),
                "equal": sum(delta == 0 for delta in deltas),
                "gpt_greater": sum(delta < 0 for delta in deltas),
            },
        }
    paired_adjusted = holm_adjust(paired_raw_p)
    for variant in variants:
        paired_comparisons[variant]["difference_holm_p"] = paired_adjusted[variant]

    concordance: dict[str, dict[str, Any]] = {}
    concordance_raw_p: dict[str, float] = {}
    for variant in variants:
        sonnet_values = [sonnet_effects[record_id][variant] for record_id in record_ids]
        gpt_values = [gpt_effects[record_id][variant] for record_id in record_ids]
        rho = spearman(sonnet_values, gpt_values)
        raw_p = permutation_correlation_p(
            sonnet_values, gpt_values, "cross-model-concordance:" + variant
        )
        concordance_raw_p[variant] = raw_p
        concordance[variant] = {
            "spearman_rho": rho,
            "rho_ci95": bootstrap_spearman_ci(
                sonnet_values, gpt_values, "cross-model-concordance:" + variant
            ),
            "permutation_p": raw_p,
        }
    concordance_adjusted = holm_adjust(concordance_raw_p)
    for variant in variants:
        concordance[variant]["holm_p"] = concordance_adjusted[variant]

    feature_rows: dict[str, dict[str, Any]] = {}
    complexity_counts: dict[str, int] = defaultdict(int)
    for record_id in record_ids:
        row = public[record_id]
        original_schema = json.loads(row["schema_variants"]["original"])
        features = schema_features(original_schema)
        features.update(
            {
                "record_id": record_id,
                "schema_complexity_label": str(row.get("schema_complexity", "unknown")),
                "question_difficulty": str(row.get("question_difficulty", "unknown")),
                "question_type": str(row.get("question_type", "unknown")),
                "context_chars": len(str(row.get("context", ""))),
                "question_chars": len(str(row.get("question", ""))),
            }
        )
        feature_rows[record_id] = features
        complexity_counts[features["schema_complexity_label"]] += 1

    feature_associations: dict[str, dict[str, dict[str, Any]]] = {}
    for model_name, effects in (("sonnet5", sonnet_effects), ("gpt55", gpt_effects)):
        feature_associations[model_name] = {}
        for variant in variants:
            outcomes = [effects[record_id][variant] for record_id in record_ids]
            family: dict[str, dict[str, Any]] = {}
            raw_values: dict[str, float] = {}
            for feature in FEATURES:
                values = [float(feature_rows[record_id][feature]) for record_id in record_ids]
                rho = spearman(values, outcomes)
                raw_p = permutation_correlation_p(
                    values, outcomes, f"feature:{model_name}:{variant}:{feature}"
                )
                raw_values[feature] = raw_p
                family[feature] = {
                    "spearman_rho": rho,
                    "rho_ci95": bootstrap_spearman_ci(
                        values, outcomes, f"feature:{model_name}:{variant}:{feature}"
                    ),
                    "permutation_p": raw_p,
                }
            adjusted = holm_adjust(raw_values)
            for feature in FEATURES:
                family[feature]["holm_p"] = adjusted[feature]
            feature_associations[model_name][variant] = family

    record_rows: list[dict[str, Any]] = []
    for record_id in record_ids:
        row = dict(feature_rows[record_id])
        for variant in variants:
            row[f"sonnet5_{variant}_normalized_excess"] = sonnet_effects[record_id][variant]
            row[f"gpt55_{variant}_normalized_excess"] = gpt_effects[record_id][variant]
            row[f"sonnet_minus_gpt_{variant}"] = (
                sonnet_effects[record_id][variant] - gpt_effects[record_id][variant]
            )
        record_rows.append(row)

    args.record_output.parent.mkdir(parents=True, exist_ok=True)
    with args.record_output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(record_rows[0]))
        writer.writeheader()
        writer.writerows(record_rows)

    report = {
        "generated_at": datetime.now(UTC).isoformat(),
        "analysis_status": "POST_HOC_EXPLORATORY_ONLY",
        "confirmatory_decisions_unchanged": {
            "sonnet5": sonnet_report["decision"],
            "gpt55": gpt_report["decision"],
        },
        "claim_boundary": (
            "All analyses in this file were specified after seeing the two formal reports. "
            "They generate hypotheses and do not rescue the failed preregistered replication gate."
        ),
        "model_identity_boundary": (
            "Model names are gateway aliases/returned strings; upstream identity and weights were not independently verified."
        ),
        "record_count": len(record_ids),
        "repeats_per_variant": sonnet_manifest["repeats_per_variant"],
        "source_log_audit": {"sonnet5": sonnet_log, "gpt55": gpt_log},
        "schema_complexity_label_counts": dict(sorted(complexity_counts.items())),
        "schema_features": list(FEATURES),
        "statistical_settings": {
            "resamples": RESAMPLES,
            "seed": SEED,
            "paired_difference_test": "two-sided record-level sign flip",
            "correlation": "Spearman with record-level permutation p-value",
            "multiple_testing": (
                "Holm across four variants for paired differences and concordance; "
                "Holm across four fixed features within each model-variant family"
            ),
        },
        "paired_model_comparisons": paired_comparisons,
        "cross_model_record_concordance": concordance,
        "feature_associations": feature_associations,
    }
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    lines = [
        "# Exploratory Cross-Model SOB Analysis",
        "",
        "**Status: post-hoc exploratory only. The frozen confirmatory decisions are unchanged.**",
        "",
        f"- Records: {len(record_ids)}; repeats per representation: {sonnet_manifest['repeats_per_variant']}",
        f"- Sonnet 5 decision: `{sonnet_report['decision']}`",
        f"- GPT-5.5 decision: `{gpt_report['decision']}`",
        "- Gateway aliases are reported verbatim; upstream model identity is not independently verified.",
        "",
        "## Paired model differences",
        "",
        "Positive differences mean larger representation sensitivity for Sonnet 5.",
        "",
        "| Variant | Sonnet excess | GPT excess | Difference (95% CI) | Holm p |",
        "|---|---:|---:|---:|---:|",
    ]
    for variant in variants:
        item = paired_comparisons[variant]
        ci = item["difference_ci95"]
        lines.append(
            f"| {variant} | {item['sonnet_mean_normalized_excess']:.3f} | "
            f"{item['gpt_mean_normalized_excess']:.3f} | "
            f"{item['sonnet_minus_gpt_mean_difference']:+.3f} "
            f"[{ci[0]:+.3f}, {ci[1]:+.3f}] | {item['difference_holm_p']:.4f} |"
        )
    lines.extend(
        [
            "",
            "## Record-level concordance",
            "",
            "| Variant | Spearman rho (95% CI) | Holm p |",
            "|---|---:|---:|",
        ]
    )
    for variant in variants:
        item = concordance[variant]
        ci = item["rho_ci95"]
        lines.append(
            f"| {variant} | {item['spearman_rho']:+.3f} "
            f"[{ci[0]:+.3f}, {ci[1]:+.3f}] | {item['holm_p']:.4f} |"
        )
    lines.extend(
        [
            "",
            "## Fixed schema-feature associations",
            "",
            "Only Holm-adjusted p-values below 0.05 are listed here; the JSON report contains every estimate.",
            "",
        ]
    )
    listed = 0
    for model_name, model_results in feature_associations.items():
        for variant, family in model_results.items():
            for feature, item in family.items():
                if item["holm_p"] < 0.05:
                    ci = item["rho_ci95"]
                    lines.append(
                        f"- `{model_name}` / `{variant}` / `{feature}`: "
                        f"rho={item['spearman_rho']:+.3f} "
                        f"[{ci[0]:+.3f}, {ci[1]:+.3f}], Holm p={item['holm_p']:.4f}."
                    )
                    listed += 1
    if listed == 0:
        lines.append("- No fixed feature association survived within-family Holm correction.")
    lines.extend(
        [
            "",
            "## Interpretation boundary",
            "",
            "These analyses may describe model heterogeneity or generate hypotheses about when sensitivity is larger. "
            "They do not reveal an internal neural mechanism, establish a universal ordering effect, or change the "
            "preregistered GPT-5.5 decision.",
        ]
    )
    args.markdown_output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "analysis_status": report["analysis_status"],
                "paired_model_comparisons": paired_comparisons,
                "cross_model_record_concordance": concordance,
                "significant_fixed_feature_association_count": listed,
                "json_output": args.json_output.as_posix(),
                "markdown_output": args.markdown_output.as_posix(),
                "record_output": args.record_output.as_posix(),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
