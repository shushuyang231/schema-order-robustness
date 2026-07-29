"""Evaluate the 20x5x5 repeated-measures schema-order engineering gate."""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import random
import statistics
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable

from jsonschema import Draft7Validator

from evaluate_sob_metamorphic import (
    exact_json_equal,
    flatten_leaves,
    token_f1,
    token_normalized_value,
)
from sob_metamorphic import compact_json, load_jsonl


BOOTSTRAP_SAMPLES = 5000
PERMUTATION_SAMPLES = 5000
SEED = 20260717


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--public-input", type=Path, required=True)
    parser.add_argument("--gold-input", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, required=True)
    return parser.parse_args()


def stable_seed(label: str) -> int:
    digest = hashlib.sha256(label.encode("utf-8")).digest()
    return SEED + int.from_bytes(digest[:4], "big")


def percentile(values: list[float], q: float) -> float:
    ordered = sorted(values)
    if not ordered:
        raise ValueError("Cannot take percentile of an empty list")
    position = (len(ordered) - 1) * q
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - lower
    return ordered[lower] * (1 - fraction) + ordered[upper] * fraction


def bootstrap_mean_ci(values: list[float], label: str) -> list[float]:
    rng = random.Random(stable_seed("bootstrap:" + label))
    size = len(values)
    estimates = [
        statistics.fmean(values[rng.randrange(size)] for _ in range(size))
        for _ in range(BOOTSTRAP_SAMPLES)
    ]
    return [percentile(estimates, 0.025), percentile(estimates, 0.975)]


def disagreement(signatures: list[str]) -> float:
    pairs = list(itertools.combinations(signatures, 2))
    return sum(left != right for left, right in pairs) / len(pairs) if pairs else 0.0


def cross_disagreement(left: list[str], right: list[str]) -> float:
    pairs = list(itertools.product(left, right))
    return sum(a != b for a, b in pairs) / len(pairs) if pairs else 0.0


def excess_disagreement(left: list[str], right: list[str]) -> float:
    return cross_disagreement(left, right) - 0.5 * (
        disagreement(left) + disagreement(right)
    )


def energy_permutation_p(
    groups: list[tuple[list[str], list[str]]], observed: float, label: str
) -> float:
    rng = random.Random(stable_seed("energy:" + label))
    exceed = 0
    for _ in range(PERMUTATION_SAMPLES):
        values: list[float] = []
        for left, right in groups:
            pool = left + right
            indices = list(range(len(pool)))
            rng.shuffle(indices)
            split = len(left)
            perm_left = [pool[index] for index in indices[:split]]
            perm_right = [pool[index] for index in indices[split:]]
            values.append(excess_disagreement(perm_left, perm_right))
        if statistics.fmean(values) >= observed - 1e-12:
            exceed += 1
    return (exceed + 1) / (PERMUTATION_SAMPLES + 1)


def sign_flip_p(values: list[float], label: str) -> float:
    observed = abs(statistics.fmean(values))
    rng = random.Random(stable_seed("sign:" + label))
    exceed = 0
    for _ in range(PERMUTATION_SAMPLES):
        estimate = abs(
            statistics.fmean(value if rng.random() < 0.5 else -value for value in values)
        )
        if estimate >= observed - 1e-12:
            exceed += 1
    return (exceed + 1) / (PERMUTATION_SAMPLES + 1)


def holm_adjust(p_values: dict[str, float]) -> dict[str, float]:
    ordered = sorted(p_values, key=p_values.get)
    adjusted: dict[str, float] = {}
    running = 0.0
    total = len(ordered)
    for rank, name in enumerate(ordered):
        value = min(1.0, (total - rank) * p_values[name])
        running = max(running, value)
        adjusted[name] = running
    return adjusted


def select_qualifying_signals(
    comparisons: dict[str, dict[str, Any]]
) -> list[dict[str, str]]:
    signals: list[dict[str, str]] = []
    for variant, result in comparisons.items():
        normalized_ci = result["normalized_excess_disagreement_ci95"]
        if (
            result["normalized_excess_disagreement"] >= 0.05
            and normalized_ci[0] > 0
            and result["normalized_energy_holm_p"] < 0.05
        ):
            signals.append(
                {"variant": variant, "criterion": "normalized_distribution_shift"}
            )
        leaf_ci = result["leaf_value_accuracy_difference_ci95"]
        if (
            abs(result["leaf_value_accuracy_difference"]) >= 0.03
            and (leaf_ci[0] > 0 or leaf_ci[1] < 0)
            and result["leaf_accuracy_holm_p"] < 0.05
        ):
            signals.append({"variant": variant, "criterion": "leaf_accuracy_shift"})
    return signals


def cross_model_replication_decision(
    *,
    operational_gate: bool,
    replicated_count: int,
    required_count: int,
    primary_count: int,
) -> str:
    """Return the frozen tiered decision for a cross-model replication."""
    if not operational_gate:
        return "CROSS_MODEL_REPLICATION_INCOMPLETE"
    if replicated_count >= primary_count:
        return "STRONG_CROSS_MODEL_REPLICATION"
    if replicated_count >= required_count:
        return "PARTIAL_CROSS_MODEL_REPLICATION"
    return "CROSS_MODEL_REPLICATION_NOT_FOUND"


def path_set_f1(gold_paths: set[tuple[Any, ...]], pred_paths: set[tuple[Any, ...]]) -> float:
    if not gold_paths or not pred_paths:
        return 0.0
    overlap = len(gold_paths & pred_paths)
    precision = overlap / len(pred_paths)
    recall = overlap / len(gold_paths)
    return 2 * precision * recall / (precision + recall) if precision + recall else 0.0


def score_prediction(
    prediction: dict[str, Any], schema: dict[str, Any], ground_truth: dict[str, Any]
) -> dict[str, Any]:
    parsed = prediction.get("parsed_output")
    structured = isinstance(parsed, dict)
    schema_valid = structured and not list(Draft7Validator(schema).iter_errors(parsed))
    gold_leaves = flatten_leaves(ground_truth)
    pred_leaves = flatten_leaves(parsed) if structured else {}
    coverage = path_set_f1(set(gold_leaves), set(pred_leaves))
    hardening = 1.0 if schema_valid and coverage >= 0.95 else 0.0
    exact = (
        sum(
            path in pred_leaves
            and exact_json_equal(expected, pred_leaves[path])
            for path, expected in gold_leaves.items()
        )
        / len(gold_leaves)
        if gold_leaves
        else 1.0
    ) * hardening
    value_token_f1 = (
        statistics.fmean(
            token_f1(expected, pred_leaves.get(path))
            for path, expected in gold_leaves.items()
        )
        if gold_leaves
        else 1.0
    ) * hardening
    perfect = structured and compact_json(parsed, sort_keys=True) == compact_json(
        ground_truth, sort_keys=True
    )
    exact_signature = (
        compact_json(parsed, sort_keys=True)
        if structured
        else f"__PARSE_FAILURE__:{prediction.get('parse_status')}"
    )
    normalized_signature = (
        compact_json(token_normalized_value(parsed), sort_keys=True)
        if structured
        else exact_signature
    )
    return {
        "schema_valid": schema_valid,
        "perfect_response": perfect,
        "leaf_value_accuracy": exact,
        "value_token_f1": value_token_f1,
        "path_set_f1": coverage,
        "exact_signature": exact_signature,
        "normalized_signature": normalized_signature,
        "parse_status": prediction.get("parse_status"),
        "returned_model": prediction.get("returned_model"),
        "response_id": prediction.get("response_id"),
        "input_tokens": prediction.get("input_tokens"),
        "output_tokens": prediction.get("output_tokens"),
        "latency_ms": prediction.get("latency_ms"),
    }


def main() -> int:
    args = parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    public = {row["record_id"]: row for row in load_jsonl(args.public_input)}
    gold = {row["record_id"]: row["ground_truth"] for row in load_jsonl(args.gold_input)}
    record_ids = list(manifest["record_ids"])
    variants = list(manifest["schema_variants"])
    conditions = list(manifest["conditions"])
    condition_to_variant = {
        item["name"]: item["schema_variant"] for item in conditions
    }

    latest: dict[tuple[str, str], dict[str, Any]] = {}
    for row in load_jsonl(args.predictions):
        if row.get("status") == "ok":
            latest[(str(row["record_id"]), str(row["variant"]))] = row
    expected = {
        (record_id, condition["name"])
        for record_id in record_ids
        for condition in conditions
    }
    if set(latest) != expected:
        raise ValueError(
            f"Prediction coverage mismatch: missing={len(expected - set(latest))}, "
            f"extra={len(set(latest) - expected)}"
        )
    if set(record_ids) != set(public) or set(record_ids) != set(gold):
        raise ValueError("Public, gold, and manifest record IDs differ")

    cells: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    all_scores: list[dict[str, Any]] = []
    for record_id in record_ids:
        for condition in conditions:
            condition_name = condition["name"]
            variant = condition_to_variant[condition_name]
            prediction = latest[(record_id, condition_name)]
            if prediction.get("schema_variant") != variant:
                raise ValueError(f"Stored schema variant mismatch: {record_id}/{condition_name}")
            schema = json.loads(public[record_id]["schema_variants"][variant])
            score = score_prediction(prediction, schema, gold[record_id])
            score.update(
                {
                    "record_id": record_id,
                    "condition": condition_name,
                    "variant": variant,
                    "schema_complexity": public[record_id]["schema_complexity"],
                }
            )
            cells[(record_id, variant)].append(score)
            all_scores.append(score)

    repeats = int(manifest["repeats_per_variant"])
    for key, values in cells.items():
        if len(values) != repeats:
            raise ValueError(f"Cell {key} has {len(values)} rows, expected {repeats}")
        stored_hashes = {
            latest[(key[0], row["condition"])]["prompt_hash"] for row in values
        }
        if len(stored_hashes) != 1:
            raise ValueError(f"Cell {key} repeat prompts are not identical")

    cell_summary: dict[tuple[str, str], dict[str, Any]] = {}
    for key, values in cells.items():
        cell_summary[key] = {
            "schema_pass_rate": statistics.fmean(row["schema_valid"] for row in values),
            "perfect_response_rate": statistics.fmean(
                row["perfect_response"] for row in values
            ),
            "leaf_value_accuracy": statistics.fmean(
                row["leaf_value_accuracy"] for row in values
            ),
            "value_token_f1": statistics.fmean(row["value_token_f1"] for row in values),
            "within_exact_disagreement": disagreement(
                [row["exact_signature"] for row in values]
            ),
            "within_normalized_disagreement": disagreement(
                [row["normalized_signature"] for row in values]
            ),
            "exact_signatures": [row["exact_signature"] for row in values],
            "normalized_signatures": [row["normalized_signature"] for row in values],
        }

    variant_summary: dict[str, dict[str, Any]] = {}
    for variant in variants:
        rows = [row for row in all_scores if row["variant"] == variant]
        summaries = [cell_summary[(record_id, variant)] for record_id in record_ids]
        variant_summary[variant] = {
            "response_count": len(rows),
            "applicable_record_count": sum(
                public[record_id]["schema_variants"][variant]
                != public[record_id]["schema_variants"]["original"]
                if variant != "original"
                else True
                for record_id in record_ids
            ),
            "schema_pass_rate": statistics.fmean(row["schema_valid"] for row in rows),
            "perfect_response_rate": statistics.fmean(
                row["perfect_response"] for row in rows
            ),
            "leaf_value_accuracy": statistics.fmean(
                row["leaf_value_accuracy"] for row in rows
            ),
            "value_token_f1": statistics.fmean(row["value_token_f1"] for row in rows),
            "mean_within_exact_disagreement": statistics.fmean(
                item["within_exact_disagreement"] for item in summaries
            ),
            "mean_within_normalized_disagreement": statistics.fmean(
                item["within_normalized_disagreement"] for item in summaries
            ),
        }

    comparisons: dict[str, dict[str, Any]] = {}
    metric_p_values: dict[str, dict[str, float]] = {
        "exact_energy": {},
        "normalized_energy": {},
        "leaf_accuracy": {},
        "perfect_response": {},
    }
    for variant in variants:
        if variant == "original":
            continue
        exact_groups: list[tuple[list[str], list[str]]] = []
        normalized_groups: list[tuple[list[str], list[str]]] = []
        exact_excesses: list[float] = []
        normalized_excesses: list[float] = []
        leaf_differences: list[float] = []
        perfect_differences: list[float] = []
        token_f1_differences: list[float] = []
        for record_id in record_ids:
            original = cell_summary[(record_id, "original")]
            treatment = cell_summary[(record_id, variant)]
            exact_pair = (
                original["exact_signatures"], treatment["exact_signatures"]
            )
            normalized_pair = (
                original["normalized_signatures"],
                treatment["normalized_signatures"],
            )
            exact_groups.append(exact_pair)
            normalized_groups.append(normalized_pair)
            exact_excesses.append(excess_disagreement(*exact_pair))
            normalized_excesses.append(excess_disagreement(*normalized_pair))
            leaf_differences.append(
                treatment["leaf_value_accuracy"] - original["leaf_value_accuracy"]
            )
            perfect_differences.append(
                treatment["perfect_response_rate"] - original["perfect_response_rate"]
            )
            token_f1_differences.append(
                treatment["value_token_f1"] - original["value_token_f1"]
            )

        exact_mean = statistics.fmean(exact_excesses)
        normalized_mean = statistics.fmean(normalized_excesses)
        leaf_mean = statistics.fmean(leaf_differences)
        perfect_mean = statistics.fmean(perfect_differences)
        metric_p_values["exact_energy"][variant] = energy_permutation_p(
            exact_groups, exact_mean, variant + ":exact"
        )
        metric_p_values["normalized_energy"][variant] = energy_permutation_p(
            normalized_groups, normalized_mean, variant + ":normalized"
        )
        metric_p_values["leaf_accuracy"][variant] = sign_flip_p(
            leaf_differences, variant + ":leaf"
        )
        metric_p_values["perfect_response"][variant] = sign_flip_p(
            perfect_differences, variant + ":perfect"
        )
        comparisons[variant] = {
            "exact_excess_disagreement": exact_mean,
            "exact_excess_disagreement_ci95": bootstrap_mean_ci(
                exact_excesses, variant + ":exact"
            ),
            "normalized_excess_disagreement": normalized_mean,
            "normalized_excess_disagreement_ci95": bootstrap_mean_ci(
                normalized_excesses, variant + ":normalized"
            ),
            "leaf_value_accuracy_difference": leaf_mean,
            "leaf_value_accuracy_difference_ci95": bootstrap_mean_ci(
                leaf_differences, variant + ":leaf"
            ),
            "perfect_response_rate_difference": perfect_mean,
            "perfect_response_rate_difference_ci95": bootstrap_mean_ci(
                perfect_differences, variant + ":perfect"
            ),
            "value_token_f1_difference": statistics.fmean(token_f1_differences),
            "value_token_f1_difference_ci95": bootstrap_mean_ci(
                token_f1_differences, variant + ":token_f1"
            ),
        }

    for family, values in metric_p_values.items():
        adjusted = holm_adjust(values)
        for variant, raw_p in values.items():
            comparisons[variant][family + "_permutation_p"] = raw_p
            comparisons[variant][family + "_holm_p"] = adjusted[variant]

    returned_models = Counter(str(row["returned_model"]) for row in all_scores)
    provided_response_ids = [
        str(row["response_id"]) for row in all_scores if row.get("response_id")
    ]
    response_id_gate = not provided_response_ids or len(set(provided_response_ids)) == len(
        provided_response_ids
    )
    overall_schema_pass = statistics.fmean(row["schema_valid"] for row in all_scores)
    operational_gate = (
        len(all_scores) == int(manifest["expected_requests"])
        and len(returned_models) == 1
        and overall_schema_pass >= 0.95
        and response_id_gate
    )
    signals = select_qualifying_signals(comparisons)
    analysis_stage = manifest.get(
        "analysis_stage", "repeated_measures_engineering_gate"
    )
    primary_variants = list(
        manifest.get(
            "primary_variants", [variant for variant in variants if variant != "original"]
        )
    )
    replicated_primary_variants = sorted(
        {
            item["variant"]
            for item in signals
            if item["criterion"] == "normalized_distribution_shift"
            and item["variant"] in primary_variants
        }
    )
    if analysis_stage == "confirmatory_repeated_measures":
        required_replications = int(manifest["required_primary_replications"])
        decision = (
            "CONFIRMED_FOR_SECOND_MODEL_REPLICATION"
            if operational_gate
            and len(replicated_primary_variants) >= required_replications
            else "NOT_CONFIRMED"
        )
    elif analysis_stage == "cross_model_replication":
        required_replications = int(manifest["required_primary_replications"])
        decision = cross_model_replication_decision(
            operational_gate=operational_gate,
            replicated_count=len(replicated_primary_variants),
            required_count=required_replications,
            primary_count=len(primary_variants),
        )
    else:
        required_replications = None
        decision = (
            "GO_FOR_100_RECORD_REPEATED_MVE"
            if operational_gate and signals
            else "NO_GO"
        )

    report = {
        "generated_at": datetime.now(UTC).isoformat(),
        "pilot_name": manifest["pilot_name"],
        "analysis_stage": analysis_stage,
        "decision": decision,
        "confirmatory_statistics_allowed": bool(
            manifest.get("confirmatory_statistics_allowed", False)
        ),
        "prediction_count": len(all_scores),
        "record_count": len(record_ids),
        "variants": variants,
        "repeats_per_variant": repeats,
        "overall_schema_pass_rate": overall_schema_pass,
        "returned_model_counts": dict(sorted(returned_models.items())),
        "provided_response_id_count": len(provided_response_ids),
        "unique_response_id_count": len(set(provided_response_ids)),
        "response_id_uniqueness_gate_passed": response_id_gate,
        "operational_gate_passed": operational_gate,
        "qualifying_signals": signals,
        "primary_variants": primary_variants,
        "exploratory_variants": manifest.get("exploratory_variants", []),
        "replicated_primary_variants": replicated_primary_variants,
        "required_primary_replications": required_replications,
        "variant_summary": variant_summary,
        "comparisons_vs_original": comparisons,
        "statistical_settings": {
            "cluster_bootstrap_samples": BOOTSTRAP_SAMPLES,
            "permutation_samples": PERMUTATION_SAMPLES,
            "seed": SEED,
            "multiple_testing": "Holm within each four-variant metric family",
            "resampling_unit": "record",
        },
        "signal_rule": {
            "normalized_distribution_shift": (
                "effect >= 0.05, bootstrap lower > 0, Holm permutation p < 0.05"
            ),
            "leaf_accuracy_shift": (
                "absolute effect >= 0.03, bootstrap CI excludes 0, "
                "Holm sign-flip p < 0.05"
            ),
        },
    }
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# Repeated-Measures Schema-Order Analysis",
        "",
        f"**Decision: {decision}**",
        "",
        (
            "> Confirmatory analysis on the frozen 100-record sample."
            if report["confirmatory_statistics_allowed"]
            else "> Engineering gate only; these records are excluded from confirmatory inference."
        ),
        "",
        f"- Responses: {len(all_scores)}",
        f"- Schema pass rate: {overall_schema_pass:.1%}",
        f"- Returned models: `{json.dumps(dict(returned_models), ensure_ascii=False)}`",
        "",
        "| Variant | Leaf accuracy | Token F1 | Perfect | Within normalized disagreement |",
        "|---|---:|---:|---:|---:|",
    ]
    for variant in variants:
        item = variant_summary[variant]
        lines.append(
            f"| {variant} | {item['leaf_value_accuracy']:.1%} | "
            f"{item['value_token_f1']:.1%} | {item['perfect_response_rate']:.1%} | "
            f"{item['mean_within_normalized_disagreement']:.3f} |"
        )
    lines.extend(
        [
            "",
            "| Variant vs original | Normalized excess (95% CI) | Holm p | Leaf difference (95% CI) | Holm p |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    for variant, item in comparisons.items():
        nci = item["normalized_excess_disagreement_ci95"]
        lci = item["leaf_value_accuracy_difference_ci95"]
        lines.append(
            f"| {variant} | {item['normalized_excess_disagreement']:.3f} "
            f"[{nci[0]:.3f}, {nci[1]:.3f}] | "
            f"{item['normalized_energy_holm_p']:.4f} | "
            f"{item['leaf_value_accuracy_difference']:+.3f} "
            f"[{lci[0]:+.3f}, {lci[1]:+.3f}] | "
            f"{item['leaf_accuracy_holm_p']:.4f} |"
        )
    args.markdown_output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "decision": decision,
                "prediction_count": len(all_scores),
                "overall_schema_pass_rate": overall_schema_pass,
                "returned_model_counts": dict(sorted(returned_models.items())),
                "qualifying_signals": signals,
                "replicated_primary_variants": replicated_primary_variants,
                "comparisons_vs_original": {
                    variant: {
                        "normalized_excess_disagreement": item[
                            "normalized_excess_disagreement"
                        ],
                        "normalized_excess_ci95": item[
                            "normalized_excess_disagreement_ci95"
                        ],
                        "normalized_energy_holm_p": item[
                            "normalized_energy_holm_p"
                        ],
                        "leaf_value_accuracy_difference": item[
                            "leaf_value_accuracy_difference"
                        ],
                        "leaf_accuracy_ci95": item[
                            "leaf_value_accuracy_difference_ci95"
                        ],
                        "leaf_accuracy_holm_p": item["leaf_accuracy_holm_p"],
                    }
                    for variant, item in comparisons.items()
                },
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
