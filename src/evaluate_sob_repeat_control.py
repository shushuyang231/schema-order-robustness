"""Compare schema-variant disagreement with identical-prompt repeat disagreement."""

from __future__ import annotations

import argparse
import json
import statistics
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from evaluate_sob_metamorphic import token_normalized_value
from sob_metamorphic import compact_json, load_jsonl


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--schema-pilot-report", type=Path, required=True)
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, required=True)
    return parser.parse_args()


def pairwise_disagreement(signatures: list[str]) -> float:
    pairs = [
        signatures[left] != signatures[right]
        for left in range(len(signatures))
        for right in range(left + 1, len(signatures))
    ]
    return sum(pairs) / len(pairs)


def main() -> int:
    args = parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    schema_report = json.loads(args.schema_pilot_report.read_text(encoding="utf-8"))
    record_ids = list(manifest["record_ids"])
    condition_names = [item["name"] for item in manifest["conditions"]]

    latest: dict[tuple[str, str], dict[str, Any]] = {}
    for row in load_jsonl(args.predictions):
        key = (str(row.get("record_id")), str(row.get("variant")))
        if row.get("status") == "ok":
            latest[key] = row
    expected = {
        (record_id, condition_name)
        for record_id in record_ids
        for condition_name in condition_names
    }
    if set(latest) != expected:
        raise ValueError(
            f"Repeat-control coverage mismatch; missing={sorted(expected - set(latest))}"
        )

    per_record: list[dict[str, Any]] = []
    for record_id in record_ids:
        rows = [latest[(record_id, condition)] for condition in condition_names]
        exact_signatures = [
            compact_json(row["parsed_output"], sort_keys=True)
            if isinstance(row.get("parsed_output"), dict)
            else f"__PARSE_FAILURE__:{row.get('parse_status')}"
            for row in rows
        ]
        normalized_signatures = [
            compact_json(token_normalized_value(row["parsed_output"]), sort_keys=True)
            if isinstance(row.get("parsed_output"), dict)
            else exact_signatures[index]
            for index, row in enumerate(rows)
        ]
        per_record.append(
            {
                "record_id": record_id,
                "exact_disagreement": len(set(exact_signatures)) > 1,
                "exact_pairwise_disagreement_score": pairwise_disagreement(
                    exact_signatures
                ),
                "exact_unique_output_count": len(set(exact_signatures)),
                "token_normalized_disagreement": len(set(normalized_signatures)) > 1,
                "token_normalized_pairwise_disagreement_score": pairwise_disagreement(
                    normalized_signatures
                ),
                "token_normalized_unique_output_count": len(
                    set(normalized_signatures)
                ),
            }
        )

    repeat_exact_rate = sum(row["exact_disagreement"] for row in per_record) / len(
        per_record
    )
    repeat_pairwise = statistics.fmean(
        row["exact_pairwise_disagreement_score"] for row in per_record
    )
    repeat_normalized_rate = sum(
        row["token_normalized_disagreement"] for row in per_record
    ) / len(per_record)
    repeat_normalized_pairwise = statistics.fmean(
        row["token_normalized_pairwise_disagreement_score"] for row in per_record
    )
    schema_exact_rate = float(schema_report["record_disagreement_rate"])
    schema_pairwise = float(schema_report["mean_pairwise_disagreement_score"])
    schema_normalized_rate = float(
        schema_report["token_normalized_record_disagreement_rate"]
    )
    schema_normalized_pairwise = float(
        schema_report["mean_token_normalized_pairwise_disagreement_score"]
    )
    report = {
        "generated_at": datetime.now(UTC).isoformat(),
        "repeat_prediction_count": len(latest),
        "record_count": len(record_ids),
        "repeat_exact_record_disagreement_rate": repeat_exact_rate,
        "schema_variant_exact_record_disagreement_rate": schema_exact_rate,
        "excess_exact_record_disagreement_rate": schema_exact_rate - repeat_exact_rate,
        "repeat_exact_pairwise_disagreement_score": repeat_pairwise,
        "schema_variant_exact_pairwise_disagreement_score": schema_pairwise,
        "excess_exact_pairwise_disagreement_score": schema_pairwise - repeat_pairwise,
        "repeat_token_normalized_record_disagreement_rate": repeat_normalized_rate,
        "schema_variant_token_normalized_record_disagreement_rate": schema_normalized_rate,
        "excess_token_normalized_record_disagreement_rate": (
            schema_normalized_rate - repeat_normalized_rate
        ),
        "repeat_token_normalized_pairwise_disagreement_score": repeat_normalized_pairwise,
        "schema_variant_token_normalized_pairwise_disagreement_score": schema_normalized_pairwise,
        "excess_token_normalized_pairwise_disagreement_score": (
            schema_normalized_pairwise - repeat_normalized_pairwise
        ),
        "returned_model_counts": dict(
            sorted(
                {
                    model: sum(
                        1 for row in latest.values() if str(row.get("returned_model")) == model
                    )
                    for model in {str(row.get("returned_model")) for row in latest.values()}
                }.items()
            )
        ),
        "per_record": per_record,
        "decision_note": (
            "Five records are an engineering control, not an inferential test. "
            "A positive excess supports scaling; a near-zero or negative excess "
            "requires redesign with repeated calls per condition."
        ),
    }
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# Sonnet 5 Identical-Prompt Repeatability Control",
        "",
        "> Engineering control only; five records do not support significance claims.",
        "",
        "| Metric | Schema variants | Identical repeats | Excess |",
        "|---|---:|---:|---:|",
        f"| Exact record disagreement | {schema_exact_rate:.1%} | {repeat_exact_rate:.1%} | {schema_exact_rate - repeat_exact_rate:+.1%} |",
        f"| Exact pairwise disagreement | {schema_pairwise:.3f} | {repeat_pairwise:.3f} | {schema_pairwise - repeat_pairwise:+.3f} |",
        f"| Token-normalized record disagreement | {schema_normalized_rate:.1%} | {repeat_normalized_rate:.1%} | {schema_normalized_rate - repeat_normalized_rate:+.1%} |",
        f"| Token-normalized pairwise disagreement | {schema_normalized_pairwise:.3f} | {repeat_normalized_pairwise:.3f} | {schema_normalized_pairwise - repeat_normalized_pairwise:+.3f} |",
    ]
    args.markdown_output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                key: report[key]
                for key in (
                    "repeat_prediction_count",
                    "repeat_exact_record_disagreement_rate",
                    "schema_variant_exact_record_disagreement_rate",
                    "excess_exact_record_disagreement_rate",
                    "repeat_token_normalized_record_disagreement_rate",
                    "schema_variant_token_normalized_record_disagreement_rate",
                    "excess_token_normalized_record_disagreement_rate",
                    "returned_model_counts",
                )
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
