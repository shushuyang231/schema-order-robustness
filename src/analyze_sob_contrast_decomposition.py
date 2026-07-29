"""Post-hoc decomposition of the frozen Schema serialization contrasts.

This analysis does not alter either preregistered model-level decision.  It
addresses a construct-validity issue: ``keywords_reversed`` also reverses the
entries of every ``properties`` object.  Comparing it directly with
``properties_reversed`` isolates the additional non-property object-member
reordering while holding property order fixed.
"""

from __future__ import annotations

import argparse
import json
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any

from evaluate_sob_repeated_pilot import (
    bootstrap_mean_ci,
    energy_permutation_p,
    excess_disagreement,
    holm_adjust,
    score_prediction,
    sign_flip_p,
)
from sob_metamorphic import load_jsonl


CONTRASTS = {
    "property_order": ("original", "properties_reversed"),
    "required_array_order": ("original", "required_reversed"),
    "description_member_placement": ("original", "descriptions_first"),
    "additional_keyword_order_given_reversed_properties": (
        "properties_reversed",
        "keywords_reversed",
    ),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--public-input", type=Path, required=True)
    parser.add_argument("--gold-input", type=Path, required=True)
    parser.add_argument(
        "--run",
        nargs=3,
        action="append",
        metavar=("LABEL", "MANIFEST", "PREDICTIONS"),
        required=True,
        help="May be supplied more than once.",
    )
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, required=True)
    return parser.parse_args()


def property_order_signature(value: Any) -> Any:
    """Return only recursively observable JSON Schema property ordering."""
    if isinstance(value, list):
        return [property_order_signature(item) for item in value]
    if not isinstance(value, dict):
        return None
    signature: list[Any] = []
    properties = value.get("properties")
    if isinstance(properties, dict):
        signature.append(
            (
                "properties",
                tuple(properties),
                tuple(
                    (name, property_order_signature(child))
                    for name, child in properties.items()
                ),
            )
        )
    for key, child in value.items():
        if key != "properties":
            nested = property_order_signature(child)
            if nested not in (None, [], [None]):
                signature.append((key, nested))
    return signature


def load_run_cells(
    *,
    manifest_path: Path,
    predictions_path: Path,
    public: dict[str, dict[str, Any]],
    gold: dict[str, dict[str, Any]],
) -> tuple[list[str], dict[tuple[str, str], list[dict[str, Any]]]]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    record_ids = [str(value) for value in manifest["record_ids"]]
    conditions = list(manifest["conditions"])
    condition_to_variant = {
        str(item["name"]): str(item["schema_variant"]) for item in conditions
    }
    if set(record_ids) != set(public) or set(record_ids) != set(gold):
        raise ValueError("Public, gold, and manifest record IDs differ")

    latest: dict[tuple[str, str], dict[str, Any]] = {}
    for row in load_jsonl(predictions_path):
        if row.get("status") == "ok":
            latest[(str(row["record_id"]), str(row["variant"]))] = row
    expected = {
        (record_id, str(condition["name"]))
        for record_id in record_ids
        for condition in conditions
    }
    if set(latest) != expected:
        raise ValueError(
            f"Prediction coverage mismatch for {predictions_path}: "
            f"missing={len(expected - set(latest))}, "
            f"extra={len(set(latest) - expected)}"
        )

    cells: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for record_id in record_ids:
        for condition in conditions:
            condition_name = str(condition["name"])
            variant = condition_to_variant[condition_name]
            prediction = latest[(record_id, condition_name)]
            if prediction.get("schema_variant") != variant:
                raise ValueError(
                    f"Stored Schema variant mismatch: {record_id}/{condition_name}"
                )
            schema = json.loads(public[record_id]["schema_variants"][variant])
            cells[(record_id, variant)].append(
                score_prediction(prediction, schema, gold[record_id])
            )

    repeats = int(manifest["repeats_per_variant"])
    for key, values in cells.items():
        if len(values) != repeats:
            raise ValueError(f"Cell {key} has {len(values)} rows, expected {repeats}")
    return record_ids, cells


def summarize_cell(values: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "normalized_signatures": [row["normalized_signature"] for row in values],
        "exact_signatures": [row["exact_signature"] for row in values],
        "leaf_value_accuracy": statistics.fmean(
            row["leaf_value_accuracy"] for row in values
        ),
        "perfect_response_rate": statistics.fmean(
            row["perfect_response"] for row in values
        ),
    }


def analyze_run(
    label: str,
    record_ids: list[str],
    cells: dict[tuple[str, str], list[dict[str, Any]]],
) -> dict[str, Any]:
    summaries = {key: summarize_cell(values) for key, values in cells.items()}
    results: dict[str, dict[str, Any]] = {}
    raw_normalized_p: dict[str, float] = {}
    raw_leaf_p: dict[str, float] = {}

    for contrast_name, (left_name, right_name) in CONTRASTS.items():
        normalized_groups: list[tuple[list[str], list[str]]] = []
        normalized_excesses: list[float] = []
        leaf_differences: list[float] = []
        perfect_differences: list[float] = []
        for record_id in record_ids:
            left = summaries[(record_id, left_name)]
            right = summaries[(record_id, right_name)]
            group = (
                left["normalized_signatures"],
                right["normalized_signatures"],
            )
            normalized_groups.append(group)
            normalized_excesses.append(excess_disagreement(*group))
            leaf_differences.append(
                right["leaf_value_accuracy"] - left["leaf_value_accuracy"]
            )
            perfect_differences.append(
                right["perfect_response_rate"] - left["perfect_response_rate"]
            )

        normalized_mean = statistics.fmean(normalized_excesses)
        leaf_mean = statistics.fmean(leaf_differences)
        seed_label = f"decomposition:{label}:{contrast_name}"
        raw_normalized_p[contrast_name] = energy_permutation_p(
            normalized_groups, normalized_mean, seed_label + ":normalized"
        )
        raw_leaf_p[contrast_name] = sign_flip_p(
            leaf_differences, seed_label + ":leaf"
        )
        results[contrast_name] = {
            "left": left_name,
            "right": right_name,
            "normalized_excess_disagreement": normalized_mean,
            "normalized_excess_ci95": bootstrap_mean_ci(
                normalized_excesses, seed_label + ":normalized"
            ),
            "leaf_value_accuracy_difference": leaf_mean,
            "leaf_accuracy_ci95": bootstrap_mean_ci(
                leaf_differences, seed_label + ":leaf"
            ),
            "perfect_response_rate_difference": statistics.fmean(
                perfect_differences
            ),
            "perfect_response_ci95": bootstrap_mean_ci(
                perfect_differences, seed_label + ":perfect"
            ),
        }

    normalized_holm = holm_adjust(raw_normalized_p)
    leaf_holm = holm_adjust(raw_leaf_p)
    for name in CONTRASTS:
        results[name]["normalized_energy_permutation_p"] = raw_normalized_p[name]
        results[name]["normalized_energy_holm_p"] = normalized_holm[name]
        results[name]["leaf_accuracy_sign_flip_p"] = raw_leaf_p[name]
        results[name]["leaf_accuracy_holm_p"] = leaf_holm[name]

    return {
        "label": label,
        "record_count": len(record_ids),
        "analysis_status": "POST_HOC_EXPLORATORY_ONLY",
        "contrasts": results,
    }


def audit_property_order(public: dict[str, dict[str, Any]]) -> dict[str, Any]:
    mismatches: list[str] = []
    byte_identical = 0
    for record_id, row in public.items():
        properties = json.loads(row["schema_variants"]["properties_reversed"])
        keywords = json.loads(row["schema_variants"]["keywords_reversed"])
        if property_order_signature(properties) != property_order_signature(keywords):
            mismatches.append(record_id)
        if row["schema_variants"]["properties_reversed"] == row["schema_variants"][
            "keywords_reversed"
        ]:
            byte_identical += 1
    return {
        "record_count": len(public),
        "matching_recursive_property_order_count": len(public) - len(mismatches),
        "property_order_mismatch_ids": mismatches,
        "byte_identical_schema_count": byte_identical,
        "interpretation": (
            "The direct properties_reversed versus keywords_reversed contrast "
            "holds recursive property order fixed and changes additional JSON "
            "object-member ordering. It does not isolate one individual keyword."
        ),
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Post-hoc Schema Contrast Decomposition",
        "",
        "**Status: exploratory only; preregistered decisions are unchanged.**",
        "",
        "`keywords_reversed` also reverses every `properties` mapping. The final "
        "contrast below therefore compares it directly with `properties_reversed` "
        "to hold recursive property order fixed.",
        "",
    ]
    audit = report["property_order_audit"]
    lines.extend(
        [
            f"Property-order audit: {audit['matching_recursive_property_order_count']}/"
            f"{audit['record_count']} records match.",
            "",
        ]
    )
    for run in report["runs"]:
        lines.extend(
            [
                f"## {run['label']}",
                "",
                "| Contrast | Left | Right | Normalized excess (95% CI) | Holm p | "
                "Leaf accuracy difference (95% CI) |",
                "|---|---|---|---:|---:|---:|",
            ]
        )
        for name, item in run["contrasts"].items():
            nci = item["normalized_excess_ci95"]
            lci = item["leaf_accuracy_ci95"]
            lines.append(
                f"| {name} | {item['left']} | {item['right']} | "
                f"{item['normalized_excess_disagreement']:.4f} "
                f"[{nci[0]:.4f}, {nci[1]:.4f}] | "
                f"{item['normalized_energy_holm_p']:.4f} | "
                f"{item['leaf_value_accuracy_difference']:.4f} "
                f"[{lci[0]:.4f}, {lci[1]:.4f}] |"
            )
        lines.append("")
    lines.extend(
        [
            "## Interpretation boundary",
            "",
            "This analysis was specified after the formal outcomes were observed. "
            "It can refine construct interpretation and motivate a disjoint "
            "confirmatory control, but it cannot create a new confirmatory claim.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    public = {str(row["record_id"]): row for row in load_jsonl(args.public_input)}
    gold = {
        str(row["record_id"]): row["ground_truth"] for row in load_jsonl(args.gold_input)
    }
    if set(public) != set(gold):
        raise ValueError("Public and gold record IDs differ")

    runs = []
    for label, manifest_text, predictions_text in args.run:
        record_ids, cells = load_run_cells(
            manifest_path=Path(manifest_text),
            predictions_path=Path(predictions_text),
            public=public,
            gold=gold,
        )
        runs.append(analyze_run(label, record_ids, cells))

    report = {
        "analysis_status": "POST_HOC_EXPLORATORY_ONLY",
        "formal_decisions_unchanged": True,
        "property_order_audit": audit_property_order(public),
        "runs": runs,
    }
    if report["property_order_audit"]["property_order_mismatch_ids"]:
        raise ValueError("Property order is not held fixed in the incremental contrast")

    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    args.markdown_output.write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
