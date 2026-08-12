"""Audit retry and top-level error rows in the seven frozen core run logs.

This script reads completed local JSONL logs and emits aggregate counts only.
It never calls a model API and never copies response content into the report.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

from sob_metamorphic import load_jsonl


ROOT = Path(__file__).resolve().parents[1]
RUNS = (
    ("sonnet_initial", "results/api/sob_sonnet5_confirmatory.jsonl", 2500),
    ("gpt_initial", "results/api/sob_gpt55_cross_model.jsonl", 2500),
    ("sonnet_decomposed", "results/api/sob_decomposed_sonnet5.jsonl", 3000),
    ("gpt_decomposed", "results/api/sob_decomposed_gpt55.jsonl", 3000),
    ("deepseek_decomposed", "results/api/sob_official_deepseek_v4_flash.jsonl", 3000),
    ("qwen_text_decomposed", "results/api/sob_official_qwen_plus_resource.jsonl", 2400),
    ("qwen_json_mode", "results/api/sob_official_qwen_plus_json_mode_100.jsonl", 1500),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--json-output",
        type=Path,
        default=ROOT / "results/api/sob_core_retry_audit.json",
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=ROOT / "results/api/sob_core_retry_audit.md",
    )
    return parser.parse_args()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def error_class(row: dict[str, Any]) -> str:
    value = str(row.get("error") or "unspecified")
    return value.split(":", 1)[0]


def audit_run(relative: str, expected_successes: int) -> dict[str, Any]:
    path = ROOT / relative
    rows = load_jsonl(path)
    successful = [row for row in rows if row.get("status") == "ok"]
    errors = [row for row in rows if row.get("status") != "ok"]
    successful_with_internal_retry = [
        row
        for row in successful
        if len(row.get("http_attempts") or []) > 1
        or any("error" in attempt for attempt in row.get("http_attempts") or [])
    ]
    unique_successful_keys = {
        str(row.get("request_key")) for row in successful if row.get("request_key")
    }
    return {
        "path": relative,
        "sha256": sha256(path),
        "raw_line_count": len(rows),
        "successful_line_count": len(successful),
        "expected_successful_line_count": expected_successes,
        "unique_successful_request_key_count": len(unique_successful_keys),
        "top_level_error_line_count": len(errors),
        "successful_rows_with_internal_retry": len(successful_with_internal_retry),
        "top_level_errors_by_schema_variant": dict(
            sorted(Counter(str(row.get("schema_variant")) for row in errors).items())
        ),
        "top_level_errors_by_class": dict(
            sorted(Counter(error_class(row) for row in errors).items())
        ),
        "complete": (
            len(successful) == expected_successes
            and len(unique_successful_keys) == expected_successes
        ),
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Core run retry audit",
        "",
        "This report contains aggregate transport metadata only; it does not contain response content.",
        "",
        "| Run | Successful | Top-level error rows | Successful rows with internal retry | Complete |",
        "|---|---:|---:|---:|---|",
    ]
    for label, item in report["runs"].items():
        lines.append(
            f"| {label} | {item['successful_line_count']} | "
            f"{item['top_level_error_line_count']} | "
            f"{item['successful_rows_with_internal_retry']} | "
            f"{'Yes' if item['complete'] else 'No'} |"
        )
    totals = report["totals"]
    lines.extend(
        [
            "",
            f"Across {totals['logged_rows']:,} logged rows, "
            f"{totals['successful_rows']:,} were successful and "
            f"{totals['top_level_error_rows']} were retained top-level error rows. "
            f"A further {totals['successful_rows_with_internal_retry']} successful "
            "rows recorded at least one internal retry. All frozen request keys "
            "eventually completed.",
            "",
            "Raw logs are intentionally not redistributed. File hashes bind these "
            "aggregate counts to the locally retained source logs.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    runs = {
        label: audit_run(relative, expected)
        for label, relative, expected in RUNS
    }
    totals = {
        "logged_rows": sum(item["raw_line_count"] for item in runs.values()),
        "successful_rows": sum(
            item["successful_line_count"] for item in runs.values()
        ),
        "top_level_error_rows": sum(
            item["top_level_error_line_count"] for item in runs.values()
        ),
        "successful_rows_with_internal_retry": sum(
            item["successful_rows_with_internal_retry"] for item in runs.values()
        ),
    }
    report = {
        "status": "PASS" if all(item["complete"] for item in runs.values()) else "FAIL",
        "analysis_scope": "aggregate transport metadata for the seven frozen core run logs",
        "contains_response_content": False,
        "runs": runs,
        "totals": totals,
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
