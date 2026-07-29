"""Freeze the existing 100-record sample into a 5x5 confirmatory manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from sob_metamorphic import VARIANTS, compact_json, load_jsonl


def stable_hash(value: Any) -> str:
    return hashlib.sha256(compact_json(value).encode("utf-8")).hexdigest()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--public-input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    rows = load_jsonl(args.public_input)
    record_ids = [row["record_id"] for row in rows]
    if len(rows) != 100 or len(set(record_ids)) != 100:
        raise ValueError("Confirmatory public input must contain 100 unique records")
    conditions = [
        {"name": f"{variant}__r{repeat}", "schema_variant": variant}
        for variant in VARIANTS
        for repeat in range(1, 6)
    ]
    no_op_counts = {
        variant: sum(
            row["schema_variants"][variant]
            == row["schema_variants"]["original"]
            for row in rows
        )
        for variant in VARIANTS
        if variant != "original"
    }
    manifest = {
        "pilot_name": "sonnet5_schema_order_confirmatory_100x5x5_v1",
        "analysis_stage": "confirmatory_repeated_measures",
        "gate_status": "GO_FOR_2500_CALL_CONFIRMATORY_MVE",
        "record_ids": record_ids,
        "record_ids_sha256": stable_hash(record_ids),
        "conditions": conditions,
        "schema_variants": list(VARIANTS),
        "primary_variants": [
            "properties_reversed",
            "keywords_reversed",
            "descriptions_first",
        ],
        "exploratory_variants": ["required_reversed"],
        "repeats_per_variant": 5,
        "expected_requests": 2500,
        "model_alias": "claude-sonnet-5",
        "sampling_parameters": "omitted",
        "max_tokens": 4096,
        "request_order": (
            "Deterministic ascending SHA256 of "
            "pilot_name|record_id|condition_name."
        ),
        "confirmatory_statistics_allowed": True,
        "required_primary_replications": 2,
        "require_all_schema_serializations_distinct": False,
        "no_op_counts_by_variant": no_op_counts,
        "protocol": "protocol/13_confirmatory_repeated_mve.md",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "record_count": len(record_ids),
                "record_ids_sha256": manifest["record_ids_sha256"],
                "condition_count": len(conditions),
                "expected_requests": manifest["expected_requests"],
                "no_op_counts_by_variant": no_op_counts,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
