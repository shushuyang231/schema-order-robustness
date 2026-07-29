"""Prepare a deterministic SOB holdout disjoint from frozen experiment sets."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq
from jsonschema import Draft202012Validator

from audit_sob_schema_variants import VARIANTS, compact_json, schema_signature
from sob_metamorphic import load_jsonl


def stable_hash(value: Any) -> str:
    return hashlib.sha256(compact_json(value).encode("utf-8")).hexdigest()


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--confirmatory-public", type=Path, required=True)
    parser.add_argument("--exclude-public", type=Path, action="append", default=[])
    parser.add_argument("--pilot-public", type=Path, required=True)
    parser.add_argument("--pilot-gold", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--manifest-output", type=Path)
    parser.add_argument("--medium-count", type=int, default=3)
    parser.add_argument("--hard-count", type=int, default=2)
    parser.add_argument("--repeats", type=int, default=1)
    parser.add_argument("--pilot-name", default="sob_schema_order_pilot")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    confirmatory_ids = {
        row["record_id"] for row in load_jsonl(args.confirmatory_public)
    }
    extra_excluded_ids = {
        row["record_id"]
        for path in args.exclude_public
        for row in load_jsonl(path)
    }
    excluded_ids = confirmatory_ids | extra_excluded_ids
    source_rows = pq.read_table(args.source).to_pylist()
    unique_source_rows: dict[str, dict[str, Any]] = {}
    duplicate_rows = 0
    for row in source_rows:
        record_id = str(row["record_id"])
        if record_id in unique_source_rows:
            if row != unique_source_rows[record_id]:
                raise ValueError(f"Non-identical rows share record_id {record_id}")
            duplicate_rows += 1
            continue
        unique_source_rows[record_id] = row

    candidates: dict[str, list[dict[str, Any]]] = {"medium": [], "hard": []}
    for row in unique_source_rows.values():
        record_id = str(row["record_id"])
        complexity = str(row["schema_complexity"])
        if record_id in excluded_ids or complexity not in candidates:
            continue
        schema = json.loads(row["json_schema"])
        variant_texts = {
            name: compact_json(transform(schema))
            for name, transform in VARIANTS.items()
        }
        if len(set(variant_texts.values())) != len(VARIANTS):
            continue
        candidates[complexity].append(row)

    selected = (
        sorted(candidates["medium"], key=lambda row: str(row["record_id"]))[
            : args.medium_count
        ]
        + sorted(candidates["hard"], key=lambda row: str(row["record_id"]))[
            : args.hard_count
        ]
    )
    expected_count = args.medium_count + args.hard_count
    if len(selected) != expected_count:
        raise ValueError(
            f"Could not select the requested {args.medium_count}-medium/"
            f"{args.hard_count}-hard holdout"
        )
    selected = sorted(selected, key=lambda row: str(row["record_id"]))

    public_rows: list[dict[str, Any]] = []
    gold_rows: list[dict[str, Any]] = []
    equivalence_failures: list[dict[str, str]] = []
    for row in selected:
        record_id = str(row["record_id"])
        schema = json.loads(row["json_schema"])
        ground_truth = json.loads(row["ground_truth"])
        Draft202012Validator.check_schema(schema)
        validation_errors = list(Draft202012Validator(schema).iter_errors(ground_truth))
        if validation_errors:
            raise ValueError(
                f"Ground truth fails its schema for {record_id}: {validation_errors[0].message}"
            )
        signature = schema_signature(schema)
        variants: dict[str, str] = {}
        for name, transform in VARIANTS.items():
            transformed = transform(schema)
            if schema_signature(transformed) != signature:
                equivalence_failures.append({"record_id": record_id, "variant": name})
            variants[name] = compact_json(transformed)
        public_rows.append(
            {
                "record_id": record_id,
                "question_type": row["question_type"],
                "question_difficulty": row["question_difficulty"],
                "schema_complexity": row["schema_complexity"],
                "context": row["context"],
                "question": row["question"],
                "schema_variants": variants,
            }
        )
        gold_rows.append({"record_id": record_id, "ground_truth": ground_truth})

    if equivalence_failures:
        raise ValueError(f"Schema variant equivalence failures: {equivalence_failures}")
    if excluded_ids & {row["record_id"] for row in public_rows}:
        raise AssertionError("Pilot and excluded record IDs overlap")

    write_jsonl(args.pilot_public, public_rows)
    write_jsonl(args.pilot_gold, gold_rows)
    report = {
        "source_sha256": hashlib.sha256(args.source.read_bytes()).hexdigest(),
        "source_row_count": len(source_rows),
        "source_unique_record_id_count": len(unique_source_rows),
        "identical_duplicate_rows_excluded": duplicate_rows,
        "confirmatory_count": len(confirmatory_ids),
        "extra_excluded_count": len(extra_excluded_ids),
        "pilot_count": len(public_rows),
        "pilot_ids": [row["record_id"] for row in public_rows],
        "pilot_ids_sha256": stable_hash([row["record_id"] for row in public_rows]),
        "complexity_counts": dict(
            sorted(Counter(str(row["schema_complexity"]) for row in public_rows).items())
        ),
        "overlap_with_confirmatory": [],
        "overlap_with_extra_exclusions": [],
        "selection_rule": (
            "After deduplicating identical record IDs, excluding all supplied record "
            "IDs and records whose five schema "
            "serializations are not pairwise byte-distinct, select the "
            f"lexicographically first {args.medium_count} medium and "
            f"{args.hard_count} hard record IDs."
        ),
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    if args.manifest_output:
        if args.repeats < 1:
            raise ValueError("--repeats must be positive")
        conditions = [
            {"name": f"{variant}__r{repeat}", "schema_variant": variant}
            for variant in VARIANTS
            for repeat in range(1, args.repeats + 1)
        ]
        manifest = {
            "pilot_name": args.pilot_name,
            "analysis_stage": "repeated_measures_engineering_gate",
            "record_ids": [row["record_id"] for row in public_rows],
            "record_ids_sha256": report["pilot_ids_sha256"],
            "conditions": conditions,
            "schema_variants": list(VARIANTS),
            "repeats_per_variant": args.repeats,
            "expected_requests": len(public_rows) * len(conditions),
            "model_alias": "claude-sonnet-5",
            "sampling_parameters": "omitted",
            "max_tokens": 4096,
            "request_order": (
                "Deterministic ascending SHA256 of "
                "pilot_name|record_id|condition_name."
            ),
            "confirmatory_statistics_allowed": False,
            "overlap_with_frozen_100_confirmatory_records": 0,
            "go_no_go_protocol": "protocol/12_repeated_measures_redesign.md",
        }
        args.manifest_output.parent.mkdir(parents=True, exist_ok=True)
        args.manifest_output.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
