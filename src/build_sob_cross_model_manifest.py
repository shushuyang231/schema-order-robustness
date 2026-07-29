"""Freeze a cross-model replication from a successful confirmatory report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-manifest", type=Path, required=True)
    parser.add_argument("--source-report", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--model-alias", default="gpt-5.5")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source = json.loads(args.source_manifest.read_text(encoding="utf-8"))
    report = json.loads(args.source_report.read_text(encoding="utf-8"))
    if report.get("decision") != "CONFIRMED_FOR_SECOND_MODEL_REPLICATION":
        raise ValueError("Source confirmatory experiment did not pass its frozen gate")
    replicated = sorted(report.get("replicated_primary_variants", []))
    if len(replicated) < 2:
        raise ValueError("At least two confirmed primary variants are required")
    all_non_original = [
        variant for variant in source["schema_variants"] if variant != "original"
    ]
    manifest = {
        "pilot_name": "gpt55_schema_order_cross_model_100x5x5_v1",
        "analysis_stage": "cross_model_replication",
        "gate_status": "GO_FOR_2500_CALL_GPT55_REPLICATION",
        "record_ids": source["record_ids"],
        "record_ids_sha256": source["record_ids_sha256"],
        "conditions": source["conditions"],
        "schema_variants": source["schema_variants"],
        "primary_variants": replicated,
        "exploratory_variants": [
            variant for variant in all_non_original if variant not in replicated
        ],
        "repeats_per_variant": source["repeats_per_variant"],
        "expected_requests": source["expected_requests"],
        "model_alias": args.model_alias,
        "sampling_parameters": "omitted",
        "max_tokens": source["max_tokens"],
        "request_order": (
            "Deterministic ascending SHA256 of "
            "pilot_name|record_id|condition_name."
        ),
        "confirmatory_statistics_allowed": True,
        "required_primary_replications": 1,
        "strong_primary_replications": len(replicated),
        "require_all_schema_serializations_distinct": False,
        "no_op_counts_by_variant": source["no_op_counts_by_variant"],
        "source_confirmatory_report": str(args.source_report).replace("\\", "/"),
        "protocol": "protocol/14_gpt55_cross_model_replication.md",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "record_count": len(manifest["record_ids"]),
                "condition_count": len(manifest["conditions"]),
                "expected_requests": manifest["expected_requests"],
                "model_alias": manifest["model_alias"],
                "primary_variants": manifest["primary_variants"],
                "required_primary_replications": manifest[
                    "required_primary_replications"
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
