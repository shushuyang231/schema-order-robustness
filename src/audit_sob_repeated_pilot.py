"""Gate the 20x5x5 repeated-measures pilot before any API request."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from audit_sob_schema_variants import schema_signature
from sob_metamorphic import build_messages, compact_json, load_jsonl, prompt_hash


BANNED = ("ground_truth", "data/restricted", "data\\restricted", "sol_sql", "test_cases")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--public-input", type=Path, required=True)
    parser.add_argument("--confirmatory-public", type=Path)
    parser.add_argument("--excluded-public", type=Path, action="append", default=[])
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    public_rows = load_jsonl(args.public_input)
    public = {row["record_id"]: row for row in public_rows}
    confirmatory_ids = (
        {row["record_id"] for row in load_jsonl(args.confirmatory_public)}
        if args.confirmatory_public
        else set()
    )
    other_excluded_ids = {
        row["record_id"]
        for path in args.excluded_public
        for row in load_jsonl(path)
    }
    record_ids = list(manifest["record_ids"])
    conditions = list(manifest["conditions"])
    failures: list[dict[str, Any]] = []

    if len(public_rows) != len(public):
        failures.append({"reason": "duplicate_public_record_ids"})
    if len(record_ids) != len(set(record_ids)):
        failures.append({"reason": "duplicate_manifest_record_ids"})
    if set(record_ids) != set(public):
        failures.append({"reason": "manifest_public_id_mismatch"})
    overlap_confirmatory = sorted(set(record_ids) & confirmatory_ids)
    overlap_other = sorted(set(record_ids) & other_excluded_ids)
    if overlap_confirmatory:
        failures.append(
            {"reason": "confirmatory_overlap", "record_ids": overlap_confirmatory}
        )
    if overlap_other:
        failures.append({"reason": "prior_pilot_overlap", "record_ids": overlap_other})

    condition_counts = Counter(item["schema_variant"] for item in conditions)
    expected_variants = set(manifest["schema_variants"])
    if set(condition_counts) != expected_variants or any(
        count != manifest["repeats_per_variant"]
        for count in condition_counts.values()
    ):
        failures.append(
            {"reason": "condition_balance_failure", "counts": dict(condition_counts)}
        )
    if len({item["name"] for item in conditions}) != len(conditions):
        failures.append({"reason": "duplicate_condition_names"})

    leakage_hits: list[dict[str, str]] = []
    equivalence_failures: list[dict[str, str]] = []
    prompt_hash_counts: dict[str, dict[str, int]] = {}
    no_op_counts: Counter[str] = Counter()
    require_distinct = bool(
        manifest.get("require_all_schema_serializations_distinct", True)
    )
    for record_id in record_ids:
        if record_id not in public:
            continue
        row = public[record_id]
        signatures = {
            variant: schema_signature(json.loads(row["schema_variants"][variant]))
            for variant in manifest["schema_variants"]
        }
        original_signature = signatures["original"]
        for variant, signature in signatures.items():
            if signature != original_signature:
                equivalence_failures.append(
                    {"record_id": record_id, "variant": variant}
                )
        schema_texts = [
            row["schema_variants"][variant] for variant in manifest["schema_variants"]
        ]
        for variant in manifest["schema_variants"]:
            if (
                variant != "original"
                and row["schema_variants"][variant]
                == row["schema_variants"]["original"]
            ):
                no_op_counts[variant] += 1
        if require_distinct and len(set(schema_texts)) != len(schema_texts):
            failures.append(
                {"reason": "schema_serializations_not_distinct", "record_id": record_id}
            )

        hashes: dict[str, list[str]] = defaultdict(list)
        for condition in conditions:
            variant = condition["schema_variant"]
            messages = build_messages(row, variant)
            digest = prompt_hash(messages)
            hashes[variant].append(digest)
            lower = compact_json(messages).lower()
            for fragment in BANNED:
                if fragment in lower:
                    leakage_hits.append(
                        {
                            "record_id": record_id,
                            "condition": condition["name"],
                            "fragment": fragment,
                        }
                    )
        prompt_hash_counts[record_id] = {
            variant: len(set(values)) for variant, values in hashes.items()
        }
        if any(len(values) != manifest["repeats_per_variant"] for values in hashes.values()):
            failures.append({"reason": "repeat_count_failure", "record_id": record_id})
        if any(len(set(values)) != 1 for values in hashes.values()):
            failures.append(
                {"reason": "within_variant_prompts_not_identical", "record_id": record_id}
            )
        if (
            require_distinct
            and len({values[0] for values in hashes.values()}) != len(expected_variants)
        ):
            failures.append(
                {"reason": "variant_prompts_not_distinct", "record_id": record_id}
            )

    expected_jobs = len(record_ids) * len(conditions)
    if expected_jobs != manifest["expected_requests"]:
        failures.append(
            {"reason": "expected_job_count_mismatch", "computed": expected_jobs}
        )
    failures.extend(
        {"reason": "schema_equivalence_failure", **item}
        for item in equivalence_failures
    )
    failures.extend(
        {"reason": "prompt_leakage", **item} for item in leakage_hits
    )
    go_status = manifest.get("gate_status", "GO_FOR_500_CALL_REPEATED_PILOT")
    status = go_status if not failures else "STOP"
    report = {
        "status": status,
        "record_count": len(record_ids),
        "condition_count": len(conditions),
        "job_count": expected_jobs,
        "complexity_counts": dict(
            sorted(Counter(public[item]["schema_complexity"] for item in record_ids).items())
        ),
        "condition_counts": dict(sorted(condition_counts.items())),
        "require_all_schema_serializations_distinct": require_distinct,
        "no_op_counts_by_variant": dict(sorted(no_op_counts.items())),
        "confirmatory_record_count": len(confirmatory_ids),
        "overlap_with_confirmatory": overlap_confirmatory,
        "overlap_with_prior_pilots": overlap_other,
        "within_variant_unique_prompt_hash_counts": prompt_hash_counts,
        "equivalence_failure_count": len(equivalence_failures),
        "leakage_hit_count": len(leakage_hits),
        "failures": failures,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
