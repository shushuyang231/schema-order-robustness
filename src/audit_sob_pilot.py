"""Static and deterministic gates for the frozen SOB 5x5 pilot."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

from audit_sob_schema_variants import schema_signature
from sob_metamorphic import VARIANTS, build_messages, compact_json, load_jsonl, prompt_hash


BANNED = ("ground_truth", "data/restricted", "data\\restricted", "sol_sql", "test_cases")


def stable_hash(value: Any) -> str:
    return hashlib.sha256(compact_json(value).encode("utf-8")).hexdigest()


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
    ids = list(manifest["record_ids"])
    if len(ids) != len(set(ids)) or not set(ids) <= set(public):
        raise ValueError("Pilot manifest has duplicate or missing record IDs")
    overlap = sorted(set(ids) & confirmatory_ids)
    if overlap:
        raise ValueError(f"Pilot records overlap the frozen confirmatory sample: {overlap}")
    if tuple(manifest["variants"]) != VARIANTS:
        raise ValueError("Pilot manifest variants differ from frozen implementation")

    prompt_hashes: list[str] = []
    leakage_hits: list[dict[str, str]] = []
    equivalence_failures: list[dict[str, str]] = []
    changed = Counter()
    for record_id in ids:
        row = public[record_id]
        original = json.loads(row["schema_variants"]["original"])
        original_signature = schema_signature(original)
        for variant in VARIANTS:
            schema_text = row["schema_variants"][variant]
            if schema_signature(json.loads(schema_text)) != original_signature:
                equivalence_failures.append({"record_id": record_id, "variant": variant})
            if schema_text != row["schema_variants"]["original"]:
                changed[variant] += 1
            first = build_messages(row, variant)
            second = build_messages(row, variant)
            if first != second or prompt_hash(first) != prompt_hash(second):
                raise AssertionError(f"Non-deterministic prompt: {record_id}/{variant}")
            digest = prompt_hash(first)
            prompt_hashes.append(digest)
            lower = compact_json(first).lower()
            for fragment in BANNED:
                if fragment in lower:
                    leakage_hits.append(
                        {"record_id": record_id, "variant": variant, "fragment": fragment}
                    )

    status = "GO_FOR_25_CALL_PILOT" if not leakage_hits and not equivalence_failures else "STOP"
    unchanged_variants = [
        variant for variant in VARIANTS if variant != "original" and changed[variant] != len(ids)
    ]
    if unchanged_variants:
        status = "STOP"
    report = {
        "status": status,
        "record_count": len(ids),
        "confirmatory_record_count": len(confirmatory_ids),
        "overlap_with_confirmatory": overlap,
        "job_count": len(prompt_hashes),
        "record_ids_sha256": stable_hash(ids),
        "prompt_hashes_sha256": stable_hash(prompt_hashes),
        "complexity_counts": dict(sorted(Counter(public[item]["schema_complexity"] for item in ids).items())),
        "changed_counts": dict(sorted(changed.items())),
        "variants_not_changed_for_every_record": unchanged_variants,
        "leakage_hits": leakage_hits,
        "equivalence_failures": equivalence_failures,
        "model_alias": manifest["model_alias"],
        "sampling_parameters": manifest["sampling_parameters"],
        "max_tokens": manifest["max_tokens"],
        "request_order": manifest["request_order"],
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if status == "GO_FOR_25_CALL_PILOT" else 1


if __name__ == "__main__":
    raise SystemExit(main())
