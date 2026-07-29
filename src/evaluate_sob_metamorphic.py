"""Evaluate SOB metamorphic predictions against isolated restricted gold answers."""

from __future__ import annotations

import argparse
import json
import math
import re
import statistics
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from sob_metamorphic import VARIANTS, compact_json, load_jsonl


ARTICLES_RE = re.compile(r"\b(a|an|the)\b")
PUNCT_RE = re.compile(r"[^\w\s]")


def flatten_leaves(value: Any, path: tuple[Any, ...] = ()) -> dict[tuple[Any, ...], Any]:
    if isinstance(value, dict):
        result: dict[tuple[Any, ...], Any] = {}
        for key in sorted(value):
            result.update(flatten_leaves(value[key], path + (key,)))
        return result
    if isinstance(value, list):
        result = {}
        for index, item in enumerate(value):
            result.update(flatten_leaves(item, path + (index,)))
        return result
    return {path: value}


def exact_json_equal(left: Any, right: Any) -> bool:
    # bool is a subclass of int in Python, so compare JSON types as well as values.
    return type(left) is type(right) and left == right


def normalize_tokens(value: Any) -> list[str]:
    """Match the token normalization used by the official SOB evaluator."""
    if value is None:
        text = "null"
    elif isinstance(value, bool):
        text = "true" if value else "false"
    else:
        text = str(value)
    text = text.lower()
    text = PUNCT_RE.sub(" ", text)
    text = ARTICLES_RE.sub(" ", text)
    return " ".join(text.split()).split()


def token_f1(expected: Any, predicted: Any) -> float:
    expected_tokens = normalize_tokens(expected)
    predicted_tokens = normalize_tokens(predicted)
    if not expected_tokens and not predicted_tokens:
        return 1.0
    if not expected_tokens or not predicted_tokens:
        return 0.0
    expected_counts = Counter(expected_tokens)
    predicted_counts = Counter(predicted_tokens)
    overlap = sum((expected_counts & predicted_counts).values())
    if not overlap:
        return 0.0
    precision = overlap / sum(predicted_counts.values())
    recall = overlap / sum(expected_counts.values())
    return 2 * precision * recall / (precision + recall)


def token_normalized_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: token_normalized_value(value[key]) for key in sorted(value)}
    if isinstance(value, list):
        return [token_normalized_value(item) for item in value]
    if isinstance(value, str):
        return " ".join(normalize_tokens(value))
    return value


def median_or_none(values: list[float | int]) -> float | None:
    return float(statistics.median(values)) if values else None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--public-input", type=Path, required=True)
    parser.add_argument("--gold-input", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    record_ids = list(manifest["record_ids"])
    public = {row["record_id"]: row for row in load_jsonl(args.public_input)}
    gold = {row["record_id"]: row["ground_truth"] for row in load_jsonl(args.gold_input)}
    if not set(record_ids) <= set(public) or not set(record_ids) <= set(gold):
        raise ValueError("Manifest IDs are not covered by public and restricted inputs")

    latest: dict[tuple[str, str], dict[str, Any]] = {}
    for row in load_jsonl(args.predictions):
        if row.get("status") == "ok" and row.get("record_id") in record_ids:
            latest[(row["record_id"], row["variant"])] = row
    expected = {(record_id, variant) for record_id in record_ids for variant in VARIANTS}
    if set(latest) != expected:
        missing = sorted(expected - set(latest))
        extra = sorted(set(latest) - expected)
        raise ValueError(f"Prediction coverage mismatch; missing={missing}, extra={extra}")

    per_prediction: list[dict[str, Any]] = []
    signatures_by_record: dict[str, dict[str, str]] = {record_id: {} for record_id in record_ids}
    normalized_signatures_by_record: dict[str, dict[str, str]] = {
        record_id: {} for record_id in record_ids
    }
    for record_id in record_ids:
        gold_value = gold[record_id]
        gold_leaves = flatten_leaves(gold_value)
        for variant in VARIANTS:
            prediction = latest[(record_id, variant)]
            parsed = prediction.get("parsed_output")
            predicted_leaves = flatten_leaves(parsed) if isinstance(parsed, dict) else {}
            correct_leaves = sum(
                path in predicted_leaves
                and exact_json_equal(predicted_leaves[path], expected_value)
                for path, expected_value in gold_leaves.items()
            )
            leaf_token_f1 = sum(
                token_f1(expected_value, predicted_leaves.get(path))
                for path, expected_value in gold_leaves.items()
            ) / len(gold_leaves) if gold_leaves else math.nan
            schema = json.loads(public[record_id]["schema_variants"][variant])
            schema_errors = (
                list(Draft202012Validator(schema).iter_errors(parsed))
                if isinstance(parsed, dict)
                else []
            )
            schema_valid = isinstance(parsed, dict) and not schema_errors
            perfect = isinstance(parsed, dict) and compact_json(
                parsed, sort_keys=True
            ) == compact_json(gold_value, sort_keys=True)
            signature = (
                compact_json(parsed, sort_keys=True)
                if isinstance(parsed, dict)
                else f"__PARSE_FAILURE__:{prediction.get('parse_status')}"
            )
            signatures_by_record[record_id][variant] = signature
            normalized_signatures_by_record[record_id][variant] = (
                compact_json(token_normalized_value(parsed), sort_keys=True)
                if isinstance(parsed, dict)
                else signature
            )
            per_prediction.append(
                {
                    "record_id": record_id,
                    "variant": variant,
                    "schema_complexity": public[record_id]["schema_complexity"],
                    "parse_status": prediction.get("parse_status"),
                    "schema_valid": schema_valid,
                    "gold_leaf_count": len(gold_leaves),
                    "correct_leaf_count": correct_leaves,
                    "leaf_value_accuracy": correct_leaves / len(gold_leaves)
                    if gold_leaves
                    else math.nan,
                    "value_token_f1": leaf_token_f1,
                    "perfect_response": perfect,
                    "latency_ms": prediction.get("latency_ms"),
                    "input_tokens": prediction.get("input_tokens"),
                    "output_tokens": prediction.get("output_tokens"),
                    "returned_model": prediction.get("returned_model"),
                }
            )

    per_record: list[dict[str, Any]] = []
    for record_id in record_ids:
        signatures = signatures_by_record[record_id]
        normalized_signatures = normalized_signatures_by_record[record_id]
        pairs = [
            signatures[left] != signatures[right]
            for left_index, left in enumerate(VARIANTS)
            for right in VARIANTS[left_index + 1 :]
        ]
        normalized_pairs = [
            normalized_signatures[left] != normalized_signatures[right]
            for left_index, left in enumerate(VARIANTS)
            for right in VARIANTS[left_index + 1 :]
        ]
        original = next(
            row
            for row in per_prediction
            if row["record_id"] == record_id and row["variant"] == "original"
        )
        per_record.append(
            {
                "record_id": record_id,
                "schema_complexity": public[record_id]["schema_complexity"],
                "metamorphic_disagreement": any(pairs),
                "pairwise_disagreement_score": sum(pairs) / len(pairs),
                "unique_output_count": len(set(signatures.values())),
                "token_normalized_disagreement": any(normalized_pairs),
                "token_normalized_pairwise_disagreement_score": (
                    sum(normalized_pairs) / len(normalized_pairs)
                ),
                "token_normalized_unique_output_count": len(
                    set(normalized_signatures.values())
                ),
                "original_perfect_response": original["perfect_response"],
                "original_error": not original["perfect_response"],
            }
        )

    variant_summary: dict[str, dict[str, Any]] = {}
    for variant in VARIANTS:
        rows = [row for row in per_prediction if row["variant"] == variant]
        total_leaves = sum(row["gold_leaf_count"] for row in rows)
        correct_leaves = sum(row["correct_leaf_count"] for row in rows)
        variant_summary[variant] = {
            "responses": len(rows),
            "schema_pass_rate": sum(row["schema_valid"] for row in rows) / len(rows),
            "perfect_response_rate": sum(row["perfect_response"] for row in rows) / len(rows),
            "leaf_value_accuracy": statistics.fmean(
                row["leaf_value_accuracy"] for row in rows
            ),
            "leaf_value_accuracy_micro": correct_leaves / total_leaves if total_leaves else None,
            "value_token_f1": statistics.fmean(row["value_token_f1"] for row in rows),
            "parse_status_counts": dict(sorted(Counter(row["parse_status"] for row in rows).items())),
            "median_latency_ms": median_or_none(
                [row["latency_ms"] for row in rows if isinstance(row["latency_ms"], (int, float))]
            ),
        }

    all_rows = per_prediction
    all_leaves = sum(row["gold_leaf_count"] for row in all_rows)
    all_correct_leaves = sum(row["correct_leaf_count"] for row in all_rows)
    returned_models = Counter(str(row["returned_model"]) for row in all_rows)
    report = {
        "generated_at": datetime.now(UTC).isoformat(),
        "pilot_name": manifest["pilot_name"],
        "confirmatory_statistics_allowed": False,
        "prediction_count": len(all_rows),
        "record_count": len(record_ids),
        "returned_model_counts": dict(sorted(returned_models.items())),
        "overall_schema_pass_rate": sum(row["schema_valid"] for row in all_rows) / len(all_rows),
        "overall_perfect_response_rate": sum(row["perfect_response"] for row in all_rows) / len(all_rows),
        "overall_leaf_value_accuracy": statistics.fmean(
            row["leaf_value_accuracy"] for row in all_rows
        ),
        "overall_leaf_value_accuracy_micro": (
            all_correct_leaves / all_leaves if all_leaves else None
        ),
        "overall_value_token_f1": statistics.fmean(
            row["value_token_f1"] for row in all_rows
        ),
        "record_disagreement_rate": sum(row["metamorphic_disagreement"] for row in per_record)
        / len(per_record),
        "mean_pairwise_disagreement_score": statistics.fmean(
            row["pairwise_disagreement_score"] for row in per_record
        ),
        "token_normalized_record_disagreement_rate": sum(
            row["token_normalized_disagreement"] for row in per_record
        ) / len(per_record),
        "mean_token_normalized_pairwise_disagreement_score": statistics.fmean(
            row["token_normalized_pairwise_disagreement_score"] for row in per_record
        ),
        "fenced_json_count": sum(row["parse_status"] == "fenced_json" for row in all_rows),
        "variant_summary": variant_summary,
        "per_record": per_record,
        "per_prediction": per_prediction,
        "notes": [
            "Pilot records are excluded from later confirmatory inference.",
            "Leaf value accuracy uses exact JSON type-and-value equality at every gold leaf path.",
            "Value Token F1 matches the official SOB lowercase/punctuation/article token normalization.",
            "Pairwise disagreement is the fraction of the 10 variant pairs with different canonical JSON outputs.",
        ],
    }

    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# Sonnet 5 SOB 5x5 Pilot Report",
        "",
        "> This is an engineering pilot only; it is excluded from confirmatory statistics.",
        "",
        f"- Predictions: {report['prediction_count']}",
        f"- Schema pass rate: {report['overall_schema_pass_rate']:.1%}",
        f"- Perfect response rate: {report['overall_perfect_response_rate']:.1%}",
        f"- Leaf value accuracy (macro): {report['overall_leaf_value_accuracy']:.1%}",
        f"- Value Token F1: {report['overall_value_token_f1']:.1%}",
        f"- Record disagreement rate: {report['record_disagreement_rate']:.1%}",
        f"- Mean pairwise disagreement score: {report['mean_pairwise_disagreement_score']:.3f}",
        f"- Token-normalized record disagreement rate: {report['token_normalized_record_disagreement_rate']:.1%}",
        f"- Fenced JSON responses recovered by the parser: {report['fenced_json_count']}",
        f"- Returned models: `{json.dumps(report['returned_model_counts'], ensure_ascii=False)}`",
        "",
        "| Variant | Schema pass | Perfect response | Leaf value accuracy | Value Token F1 |",
        "|---|---:|---:|---:|---:|",
    ]
    for variant in VARIANTS:
        summary = variant_summary[variant]
        lines.append(
            f"| {variant} | {summary['schema_pass_rate']:.1%} | "
            f"{summary['perfect_response_rate']:.1%} | {summary['leaf_value_accuracy']:.1%} | "
            f"{summary['value_token_f1']:.1%} |"
        )
    args.markdown_output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in (
        "prediction_count",
        "overall_schema_pass_rate",
        "overall_perfect_response_rate",
        "overall_leaf_value_accuracy",
        "overall_value_token_f1",
        "record_disagreement_rate",
        "mean_pairwise_disagreement_score",
        "token_normalized_record_disagreement_rate",
        "mean_token_normalized_pairwise_disagreement_score",
        "fenced_json_count",
        "returned_model_counts",
    )}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
