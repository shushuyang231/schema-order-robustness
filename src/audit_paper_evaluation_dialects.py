"""Audit Draft 7 versus Draft 2020-12 validation on frozen paper responses."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

from jsonschema import Draft7Validator, Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "data/processed/sob_mve_100_public.jsonl"
PREDICTIONS = (
    ROOT / "results/api/sob_sonnet5_confirmatory.jsonl",
    ROOT / "results/api/sob_gpt55_cross_model.jsonl",
)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def latest_successes(path: Path) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for row in load_jsonl(path):
        if row.get("status") == "ok":
            rows[str(row["request_key"])] = row
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "paper/robustness/dialect_validation_audit.json",
    )
    args = parser.parse_args()

    public = {str(row["record_id"]): row for row in load_jsonl(PUBLIC)}
    schema_pairs: Counter[tuple[bool, bool]] = Counter()
    schema_failures: list[dict[str, Any]] = []
    for record_id, row in public.items():
        for variant, schema_text in row["schema_variants"].items():
            schema = json.loads(schema_text)
            draft7_ok = True
            draft2020_ok = True
            try:
                Draft7Validator.check_schema(schema)
            except Exception:
                draft7_ok = False
            try:
                Draft202012Validator.check_schema(schema)
            except Exception:
                draft2020_ok = False
            schema_pairs[(draft7_ok, draft2020_ok)] += 1
            if draft7_ok != draft2020_ok:
                schema_failures.append(
                    {
                        "record_id": record_id,
                        "variant": variant,
                        "draft7_schema_valid": draft7_ok,
                        "draft2020_schema_valid": draft2020_ok,
                    }
                )

    prediction_summaries: list[dict[str, Any]] = []
    all_disagreements: list[dict[str, Any]] = []
    for path in PREDICTIONS:
        predictions = latest_successes(path)
        outcomes: Counter[tuple[bool, bool]] = Counter()
        disagreements: list[dict[str, Any]] = []
        for row in predictions.values():
            record_id = str(row["record_id"])
            schema_variant = str(row.get("schema_variant") or row["variant"].split("__r")[0])
            schema = json.loads(public[record_id]["schema_variants"][schema_variant])
            parsed = row.get("parsed_output")
            if not isinstance(parsed, dict):
                valid7 = valid2020 = False
            else:
                valid7 = not list(Draft7Validator(schema).iter_errors(parsed))
                valid2020 = not list(Draft202012Validator(schema).iter_errors(parsed))
            outcomes[(valid7, valid2020)] += 1
            if valid7 != valid2020:
                item = {
                    "record_id": record_id,
                    "variant": row["variant"],
                    "request_key": row["request_key"],
                    "draft7_valid": valid7,
                    "draft2020_valid": valid2020,
                }
                disagreements.append(item)
                all_disagreements.append({"source": str(path.relative_to(ROOT)), **item})
        prediction_summaries.append(
            {
                "path": str(path.relative_to(ROOT)),
                "sha256": sha256(path),
                "unique_successful_requests": len(predictions),
                "outcome_counts": {
                    f"draft7_{a}_draft2020_{b}": count
                    for (a, b), count in sorted(outcomes.items())
                },
                "dialect_disagreement_count": len(disagreements),
            }
        )

    report = {
        "public_input": str(PUBLIC.relative_to(ROOT)),
        "public_input_sha256": sha256(PUBLIC),
        "schema_representation_count": sum(schema_pairs.values()),
        "schema_dialect_outcome_counts": {
            f"draft7_{a}_draft2020_{b}": count
            for (a, b), count in sorted(schema_pairs.items())
        },
        "schema_dialect_disagreement_count": len(schema_failures),
        "prediction_sources": prediction_summaries,
        "total_prediction_dialect_disagreement_count": len(all_disagreements),
        "disagreements": all_disagreements[:100],
        "paper_metric_impact": (
            "none" if not all_disagreements else "requires sensitivity re-analysis"
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if not all_disagreements and not schema_failures else 1


if __name__ == "__main__":
    raise SystemExit(main())

