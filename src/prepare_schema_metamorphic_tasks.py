"""Prepare public schema-order metamorphic tasks from a generic JSONL file.

Each input row must contain ``record_id``, ``context``, ``question``, and
``json_schema`` (a JSON object or a JSON-encoded object).  The output is directly
consumable by ``run_sob_metamorphic.py`` and intentionally excludes answers.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from audit_sob_schema_variants import VARIANTS, compact_json, schema_signature


REQUIRED_FIELDS = ("record_id", "context", "question", "json_schema")
RESTRICTED_FIELDS = {
    "answer",
    "expected_answer",
    "gold",
    "ground_truth",
    "sol_sql",
    "test_cases",
}


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def stable_hash(value: Any) -> str:
    return sha256_bytes(compact_json(value).encode("utf-8"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON on line {line_number}: {exc}") from exc
            if not isinstance(value, dict):
                raise ValueError(f"Line {line_number} is not a JSON object")
            rows.append(value)
    return rows


def parse_schema(value: Any, record_id: str) -> dict[str, Any]:
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError as exc:
            raise ValueError(f"json_schema is invalid JSON for {record_id}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"json_schema must be an object for {record_id}")
    Draft202012Validator.check_schema(value)
    return value


def prepare_rows(
    rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], Counter[str]]:
    public_rows: list[dict[str, Any]] = []
    audit_rows: list[dict[str, Any]] = []
    changed_counts: Counter[str] = Counter()
    seen_ids: set[str] = set()

    for index, row in enumerate(rows, start=1):
        missing = [field for field in REQUIRED_FIELDS if field not in row]
        if missing:
            raise ValueError(f"Input row {index} is missing required fields: {missing}")
        restricted = sorted(RESTRICTED_FIELDS & set(row))
        if restricted:
            raise ValueError(
                f"Input row {index} contains restricted answer-side fields: {restricted}"
            )

        record_id = str(row["record_id"])
        if not record_id:
            raise ValueError(f"Input row {index} has an empty record_id")
        if record_id in seen_ids:
            raise ValueError(f"Duplicate record_id: {record_id}")
        seen_ids.add(record_id)

        schema = parse_schema(row["json_schema"], record_id)
        original_signature = schema_signature(schema)
        original_text = compact_json(schema)
        variants: dict[str, str] = {}
        changed: dict[str, bool] = {}
        for name, transform in VARIANTS.items():
            transformed = transform(schema)
            if schema_signature(transformed) != original_signature:
                raise AssertionError(
                    f"Transformation {name} changed the validation signature for {record_id}"
                )
            text = compact_json(transformed)
            variants[name] = text
            changed[name] = text != original_text
            if changed[name]:
                changed_counts[name] += 1

        public_row: dict[str, Any] = {
            "record_id": record_id,
            "context": str(row["context"]),
            "question": str(row["question"]),
            "schema_variants": variants,
        }
        if "metadata" in row:
            public_row["metadata"] = row["metadata"]
        public_rows.append(public_row)
        audit_rows.append(
            {
                "record_id": record_id,
                "schema_signature_sha256": stable_hash(original_signature),
                "variant_changed": changed,
                "variant_sha256": {
                    name: sha256_bytes(text.encode("utf-8"))
                    for name, text in variants.items()
                },
            }
        )

    return public_rows, audit_rows, changed_counts


def jsonl_bytes(rows: list[dict[str, Any]]) -> bytes:
    text = "".join(
        json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
        for row in rows
    )
    return text.encode("utf-8")


def build_manifest(
    *,
    study_name: str,
    record_ids: list[str],
    repeats: int,
    model_alias: str,
    max_tokens: int,
) -> dict[str, Any]:
    if repeats < 1:
        raise ValueError("repeats must be positive")
    conditions = [
        {"name": f"{variant}__r{repeat}", "schema_variant": variant}
        for variant in VARIANTS
        for repeat in range(1, repeats + 1)
    ]
    return {
        "pilot_name": study_name,
        "analysis_stage": "schema_serialization_metamorphic_test",
        "record_ids": record_ids,
        "record_ids_sha256": stable_hash(record_ids),
        "conditions": conditions,
        "schema_variants": list(VARIANTS),
        "repeats_per_variant": repeats,
        "expected_requests": len(record_ids) * len(conditions),
        "model_alias": model_alias,
        "sampling_parameters": "omitted",
        "max_tokens": max_tokens,
        "request_order": "ascending SHA256 of study_name|record_id|condition_name",
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--public-output", type=Path, required=True)
    parser.add_argument("--manifest-output", type=Path, required=True)
    parser.add_argument("--audit-output", type=Path, required=True)
    parser.add_argument("--study-name", required=True)
    parser.add_argument("--model-alias", required=True)
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--max-tokens", type=int, default=4096)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source_bytes = args.input.read_bytes()
    rows = load_jsonl(args.input)
    if not rows:
        raise ValueError("Input JSONL contains no records")
    public_rows, audit_rows, changed_counts = prepare_rows(rows)
    public_bytes = jsonl_bytes(public_rows)
    manifest = build_manifest(
        study_name=args.study_name,
        record_ids=[row["record_id"] for row in public_rows],
        repeats=args.repeats,
        model_alias=args.model_alias,
        max_tokens=args.max_tokens,
    )
    audit = {
        "tool": "prepare_schema_metamorphic_tasks.py",
        "equivalence_scope": (
            "JSON object member order and required-array order are normalized; "
            "all generated variants must share one validation signature."
        ),
        "input_sha256": sha256_bytes(source_bytes),
        "record_count": len(public_rows),
        "record_ids_sha256": manifest["record_ids_sha256"],
        "public_output_sha256": sha256_bytes(public_bytes),
        "variant_changed_record_counts": dict(sorted(changed_counts.items())),
        "records": audit_rows,
    }

    for path in (args.public_output, args.manifest_output, args.audit_output):
        path.parent.mkdir(parents=True, exist_ok=True)
    args.public_output.write_bytes(public_bytes)
    args.manifest_output.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.audit_output.write_text(
        json.dumps(audit, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({**audit, "records": "omitted"}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

