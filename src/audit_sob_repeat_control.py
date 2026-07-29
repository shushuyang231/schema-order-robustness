"""Gate the identical-prompt repeatability control before API calls."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from sob_metamorphic import build_messages, compact_json, load_jsonl, prompt_hash


BANNED = ("ground_truth", "data/restricted", "data\\restricted", "sol_sql", "test_cases")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--public-input", type=Path, required=True)
    parser.add_argument("--confirmatory-public", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    public = {row["record_id"]: row for row in load_jsonl(args.public_input)}
    confirmatory_ids = {
        row["record_id"] for row in load_jsonl(args.confirmatory_public)
    }
    record_ids = list(manifest["record_ids"])
    conditions = list(manifest["conditions"])
    overlap = sorted(set(record_ids) & confirmatory_ids)
    failures: list[dict[str, Any]] = []
    hashes_by_record: dict[str, list[str]] = {}
    for record_id in record_ids:
        if record_id not in public:
            failures.append({"record_id": record_id, "reason": "missing_public_record"})
            continue
        hashes: list[str] = []
        for condition in conditions:
            if condition.get("schema_variant") != "original":
                failures.append(
                    {
                        "record_id": record_id,
                        "condition": condition.get("name"),
                        "reason": "not_original_schema",
                    }
                )
                continue
            messages = build_messages(public[record_id], "original")
            digest = prompt_hash(messages)
            hashes.append(digest)
            lower = compact_json(messages).lower()
            for fragment in BANNED:
                if fragment in lower:
                    failures.append(
                        {
                            "record_id": record_id,
                            "condition": condition.get("name"),
                            "reason": f"leakage:{fragment}",
                        }
                    )
        hashes_by_record[record_id] = hashes
        if len(hashes) != 5 or len(set(hashes)) != 1:
            failures.append(
                {"record_id": record_id, "reason": "repeat_prompts_not_identical"}
            )
    if overlap:
        failures.append({"reason": "confirmatory_overlap", "record_ids": overlap})
    expected = len(record_ids) * len(conditions)
    if expected != manifest.get("expected_requests"):
        failures.append({"reason": "request_count_mismatch", "computed": expected})
    status = "GO_FOR_REPEAT_CONTROL" if not failures else "STOP"
    report = {
        "status": status,
        "record_count": len(record_ids),
        "condition_count": len(conditions),
        "job_count": expected,
        "confirmatory_record_count": len(confirmatory_ids),
        "overlap_with_confirmatory": overlap,
        "unique_prompt_hashes_per_record": {
            record_id: len(set(hashes)) for record_id, hashes in hashes_by_record.items()
        },
        "failures": failures,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if status == "GO_FOR_REPEAT_CONTROL" else 1


if __name__ == "__main__":
    raise SystemExit(main())
