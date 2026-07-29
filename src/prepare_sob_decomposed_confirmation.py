"""Freeze a disjoint SOB sample for decomposed Schema-order confirmation."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq
from jsonschema import Draft202012Validator

from analyze_sob_contrast_decomposition import property_order_signature
from audit_sob_schema_variants import VARIANTS, compact_json, schema_signature
from sob_metamorphic import load_jsonl


STUDY_NAME = "sob_decomposed_confirmatory_200x3x5_v1"
SCHEMA_VARIANTS = ("original", "properties_reversed", "keywords_reversed")
REPEATS = 5


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--exclude-public", type=Path, action="append", default=[])
    parser.add_argument("--public-output", type=Path, required=True)
    parser.add_argument("--gold-output", type=Path, required=True)
    parser.add_argument("--report-output", type=Path, required=True)
    parser.add_argument(
        "--manifest",
        nargs=2,
        action="append",
        metavar=("MODEL_ALIAS", "OUTPUT_PATH"),
        required=True,
    )
    parser.add_argument("--per-complexity", type=int, default=100)
    return parser.parse_args()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def stable_rank(record_id: str) -> str:
    return sha256_bytes(f"{STUDY_NAME}|{record_id}".encode("utf-8"))


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def file_sha256(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def main() -> int:
    args = parse_args()
    excluded_ids = {
        str(row["record_id"])
        for path in args.exclude_public
        for row in load_jsonl(path)
    }
    source_rows = pq.read_table(args.source).to_pylist()
    unique_rows: dict[str, dict[str, Any]] = {}
    identical_duplicates = 0
    for row in source_rows:
        record_id = str(row["record_id"])
        if record_id in unique_rows:
            if row != unique_rows[record_id]:
                raise ValueError(f"Non-identical rows share record_id {record_id}")
            identical_duplicates += 1
            continue
        unique_rows[record_id] = row

    candidates: dict[str, list[tuple[dict[str, Any], dict[str, str], Any]]] = {
        "medium": [],
        "hard": [],
    }
    rejected_non_distinct = 0
    rejected_property_mismatch = 0
    for record_id, row in unique_rows.items():
        complexity = str(row["schema_complexity"])
        if record_id in excluded_ids or complexity not in candidates:
            continue
        schema = json.loads(row["json_schema"])
        ground_truth = json.loads(row["ground_truth"])
        Draft202012Validator.check_schema(schema)
        errors = list(Draft202012Validator(schema).iter_errors(ground_truth))
        if errors:
            raise ValueError(
                f"Ground truth fails Schema for {record_id}: {errors[0].message}"
            )
        signature = schema_signature(schema)
        objects = {name: VARIANTS[name](schema) for name in SCHEMA_VARIANTS}
        if any(schema_signature(value) != signature for value in objects.values()):
            raise AssertionError(f"Validation signature changed for {record_id}")
        texts = {name: compact_json(value) for name, value in objects.items()}
        if len(set(texts.values())) != len(texts):
            rejected_non_distinct += 1
            continue
        if property_order_signature(objects["properties_reversed"]) != property_order_signature(
            objects["keywords_reversed"]
        ):
            rejected_property_mismatch += 1
            continue
        candidates[complexity].append((row, texts, ground_truth))

    selected: list[tuple[dict[str, Any], dict[str, str], Any]] = []
    for complexity in ("medium", "hard"):
        ranked = sorted(
            candidates[complexity], key=lambda item: stable_rank(str(item[0]["record_id"]))
        )
        if len(ranked) < args.per_complexity:
            raise ValueError(f"Insufficient {complexity} candidates")
        selected.extend(ranked[: args.per_complexity])
    selected.sort(key=lambda item: str(item[0]["record_id"]))

    public_rows: list[dict[str, Any]] = []
    gold_rows: list[dict[str, Any]] = []
    for row, texts, ground_truth in selected:
        record_id = str(row["record_id"])
        public_rows.append(
            {
                "record_id": record_id,
                "question_type": row["question_type"],
                "question_difficulty": row["question_difficulty"],
                "schema_complexity": row["schema_complexity"],
                "context": row["context"],
                "question": row["question"],
                "schema_variants": texts,
            }
        )
        gold_rows.append({"record_id": record_id, "ground_truth": ground_truth})

    write_jsonl(args.public_output, public_rows)
    write_jsonl(args.gold_output, gold_rows)
    record_ids = [row["record_id"] for row in public_rows]
    record_ids_sha256 = sha256_bytes(
        json.dumps(record_ids, separators=(",", ":")).encode("utf-8")
    )
    conditions = [
        {"name": f"{variant}__r{repeat}", "schema_variant": variant}
        for variant in SCHEMA_VARIANTS
        for repeat in range(1, REPEATS + 1)
    ]
    for model_alias, output_text in args.manifest:
        manifest = {
            "pilot_name": STUDY_NAME,
            "analysis_stage": "preregistered_decomposed_contrast_confirmation",
            "frozen_before_api_calls": True,
            "record_ids": record_ids,
            "record_ids_sha256": record_ids_sha256,
            "schema_variants": list(SCHEMA_VARIANTS),
            "conditions": conditions,
            "repeats_per_variant": REPEATS,
            "expected_requests": len(record_ids) * len(conditions),
            "model_alias": model_alias,
            "sampling_parameters": "omitted",
            "max_tokens": 4096,
            "primary_contrasts": {
                "property_order": ["original", "properties_reversed"],
                "additional_keyword_order_given_reversed_properties": [
                    "properties_reversed",
                    "keywords_reversed",
                ],
            },
            "minimum_practical_effect": 0.05,
            "confirmation_rule": (
                "For each primary contrast: normalized excess >= 0.05, "
                "record-bootstrap CI lower bound > 0, and Holm-adjusted "
                "within-record permutation p < 0.05. Report both contrasts and "
                "retain null/contrary results."
            ),
            "independent_unit": "record",
            "resamples": 5000,
            "request_order": (
                "Ascending SHA256 of study_name|record_id|condition_name"
            ),
        }
        output_path = Path(output_text)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    report = {
        "status": "FROZEN_READY_FOR_OFFLINE_GATE",
        "study_name": STUDY_NAME,
        "source_sha256": file_sha256(args.source),
        "source_rows": len(source_rows),
        "source_unique_records": len(unique_rows),
        "identical_duplicate_rows_excluded": identical_duplicates,
        "excluded_record_count": len(excluded_ids),
        "selected_record_count": len(public_rows),
        "selected_record_ids_sha256": record_ids_sha256,
        "complexity_counts": dict(
            sorted(Counter(str(row["schema_complexity"]) for row in public_rows).items())
        ),
        "question_type_counts": dict(
            sorted(Counter(str(row["question_type"]) for row in public_rows).items())
        ),
        "overlap_with_excluded": sorted(set(record_ids) & excluded_ids),
        "rejected_non_distinct": rejected_non_distinct,
        "rejected_property_order_mismatch": rejected_property_mismatch,
        "public_sha256": file_sha256(args.public_output),
        "gold_sha256": file_sha256(args.gold_output),
        "model_aliases": [item[0] for item in args.manifest],
        "expected_requests_per_model": len(record_ids) * len(conditions),
        "selection_rule": (
            "After excluding all prior study IDs and requiring three byte-distinct, "
            "validation-equivalent representations with matching recursive property "
            "order in the decomposed contrast, select the first 100 medium and 100 "
            "hard records by SHA256(study_name|record_id)."
        ),
    }
    if report["overlap_with_excluded"]:
        raise AssertionError("New confirmation overlaps a prior study")
    args.report_output.parent.mkdir(parents=True, exist_ok=True)
    args.report_output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
