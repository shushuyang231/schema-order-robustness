"""Audit completeness and provenance consistency of endpoint-panel JSONL logs.

The report contains aggregate metadata only. It never calls a model API and
does not copy response content into the generated JSON or Markdown files.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import statistics
from collections import Counter
from pathlib import Path
from typing import Any

from sob_metamorphic import load_jsonl


ROOT = Path(__file__).resolve().parents[1]
RUNS = (
    (
        "sjtu_deepseek_chat",
        "protocol/sob_sjtu_deepseek_chat_manifest.json",
        "results/api/sob_sjtu_deepseek_chat.jsonl",
    ),
    (
        "sjtu_deepseek_reasoner",
        "protocol/sob_sjtu_deepseek_reasoner_manifest.json",
        "results/api/sob_sjtu_deepseek_reasoner.jsonl",
    ),
    (
        "tokenrhythm_deepseek_v4_flash",
        "protocol/sob_tokenrhythm_deepseek_v4_flash_manifest.json",
        "results/api/sob_tokenrhythm_deepseek_v4_flash.jsonl",
    ),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--json-output",
        type=Path,
        default=ROOT / "results/api/sob_endpoint_panel_completion_audit.json",
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=ROOT / "results/api/sob_endpoint_panel_completion_audit.md",
    )
    return parser.parse_args()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def error_class(row: dict[str, Any]) -> str:
    return str(row.get("error") or "unspecified").split(":", 1)[0]


def audit_run(manifest_path: Path, predictions_path: Path) -> dict[str, Any]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    rows = load_jsonl(predictions_path)
    expected_pairs = {
        (str(record_id), str(condition["name"]))
        for record_id in manifest["record_ids"]
        for condition in manifest["conditions"]
    }
    successful_lines = [row for row in rows if row.get("status") == "ok"]
    error_lines = [row for row in rows if row.get("status") != "ok"]
    successful_by_pair: dict[tuple[str, str], dict[str, Any]] = {}
    for row in successful_lines:
        successful_by_pair[(str(row["record_id"]), str(row["variant"]))] = row
    successful_pairs = set(successful_by_pair)
    missing_pairs = expected_pairs - successful_pairs
    extra_pairs = successful_pairs - expected_pairs
    successful_rows = [successful_by_pair[pair] for pair in expected_pairs & successful_pairs]
    schema_pass_rate = (
        statistics.fmean(bool(row.get("schema_valid")) for row in successful_rows)
        if successful_rows
        else 0.0
    )
    returned_models = Counter(str(row.get("returned_model")) for row in successful_rows)
    fingerprints = Counter(str(row.get("system_fingerprint")) for row in successful_rows)
    smoke_hashes = Counter(str(row.get("smoke_record_sha256")) for row in successful_rows)
    non_null_fingerprints = {
        str(row.get("system_fingerprint"))
        for row in successful_rows
        if row.get("system_fingerprint") is not None
    }
    provenance_consistent = (
        len(returned_models) == 1
        and len(smoke_hashes) == 1
        and len(non_null_fingerprints) <= 1
    )
    missing_by_condition = Counter(condition for _, condition in missing_pairs)
    complete = (
        not missing_pairs
        and not extra_pairs
        and len(successful_lines) == len(expected_pairs)
        and len({str(row.get("request_key")) for row in successful_lines})
        == len(expected_pairs)
        and provenance_consistent
    )
    return {
        "manifest": str(manifest_path.relative_to(ROOT)).replace("\\", "/"),
        "predictions": str(predictions_path.relative_to(ROOT)).replace("\\", "/"),
        "predictions_sha256": sha256(predictions_path),
        "expected_successful_requests": len(expected_pairs),
        "raw_line_count": len(rows),
        "successful_line_count": len(successful_lines),
        "unique_successful_request_key_count": len(
            {str(row.get("request_key")) for row in successful_lines}
        ),
        "top_level_error_line_count": len(error_lines),
        "missing_successful_pair_count": len(missing_pairs),
        "missing_by_condition": dict(sorted(missing_by_condition.items())),
        "extra_successful_pair_count": len(extra_pairs),
        "duplicate_successful_line_count": len(successful_lines) - len(successful_pairs),
        "top_level_errors_by_class": dict(
            sorted(Counter(error_class(row) for row in error_lines).items())
        ),
        "returned_model_counts": dict(sorted(returned_models.items())),
        "system_fingerprint_counts": dict(sorted(fingerprints.items())),
        "smoke_record_sha256_counts": dict(sorted(smoke_hashes.items())),
        "provenance_consistent": provenance_consistent,
        "schema_pass_rate": schema_pass_rate,
        "complete": complete,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Endpoint-panel completion audit",
        "",
        "This report contains aggregate transport and provenance metadata only; it does not contain response content.",
        "",
        "| Run | Unique successes | Missing | Error rows retained | Schema pass rate | Complete |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for label, item in report["runs"].items():
        lines.append(
            f"| {label} | {item['unique_successful_request_key_count']}/"
            f"{item['expected_successful_requests']} | "
            f"{item['missing_successful_pair_count']} | "
            f"{item['top_level_error_line_count']} | "
            f"{item['schema_pass_rate']:.4f} | "
            f"{'Yes' if item['complete'] else 'No'} |"
        )
    lines.extend(
        [
            "",
            f"Panel status: **{report['status']}**. Missing requests must be "
            "retried with identical frozen request keys before inference.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    runs = {
        label: audit_run(ROOT / manifest, ROOT / predictions)
        for label, manifest, predictions in RUNS
    }
    report = {
        "status": "PASS" if all(item["complete"] for item in runs.values()) else "FAIL",
        "analysis_scope": "post-submission endpoint-panel completion and provenance audit",
        "contains_response_content": False,
        "runs": runs,
        "totals": {
            "expected_successful_requests": sum(
                item["expected_successful_requests"] for item in runs.values()
            ),
            "unique_successful_request_keys": sum(
                item["unique_successful_request_key_count"] for item in runs.values()
            ),
            "missing_successful_pairs": sum(
                item["missing_successful_pair_count"] for item in runs.values()
            ),
            "retained_top_level_error_rows": sum(
                item["top_level_error_line_count"] for item in runs.values()
            ),
        },
    }
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    args.markdown_output.write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
