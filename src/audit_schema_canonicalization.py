"""Audit whether all stored metamorphic variants collapse under canonicalization."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from canonicalize_json_schema import canonical_schema_text
from sob_metamorphic import load_jsonl


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def audit_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    failures: list[dict[str, Any]] = []
    canonical_hashes: dict[str, str] = {}
    variant_names: set[str] = set()
    for row in rows:
        record_id = str(row["record_id"])
        variants = row.get("schema_variants") or {}
        variant_names.update(str(name) for name in variants)
        texts = {
            str(name): canonical_schema_text(json.loads(str(schema_text)))
            for name, schema_text in variants.items()
        }
        hashes = {name: sha256_text(text) for name, text in texts.items()}
        if len(set(hashes.values())) != 1:
            failures.append({"record_id": record_id, "canonical_hashes": hashes})
        else:
            canonical_hashes[record_id] = next(iter(hashes.values()))
    return {
        "tool": "audit_schema_canonicalization.py",
        "scope": (
            "Sort all JSON object members and unique required-array strings; "
            "preserve all other arrays."
        ),
        "record_count": len(rows),
        "variant_names": sorted(variant_names),
        "all_variants_collapse_per_record": not failures,
        "failure_count": len(failures),
        "failures": failures,
        "canonical_hashes": canonical_hashes,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--public-input", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = audit_rows(load_jsonl(args.public_input))
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({**report, "canonical_hashes": "omitted"}, ensure_ascii=False, indent=2))
    return 0 if report["all_variants_collapse_per_record"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
