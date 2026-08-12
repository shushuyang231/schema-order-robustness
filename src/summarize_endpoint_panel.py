"""Summarize completed endpoint reports with a six-test panel-level correction."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from evaluate_sob_repeated_pilot import holm_adjust


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--report",
        nargs=2,
        action="append",
        metavar=("LABEL", "JSON"),
        required=True,
    )
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, required=True)
    return parser.parse_args()


def render_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# Endpoint expansion: deployment-level summary",
        "",
        "**Status: supplemental post-submission evidence. Deployments are not independent model samples.**",
        "",
        "| Deployment | Contrast | Effect (95% CI) | Local Holm p | Panel Holm p | Local decision |",
        "|---|---|---:|---:|---:|---|",
    ]
    for deployment, report in summary["deployments"].items():
        for contrast, item in report["contrasts"].items():
            ci = item["normalized_excess_ci95"]
            lines.append(
                f"| {deployment} | {contrast} | "
                f"{item['normalized_excess_disagreement']:.4f} "
                f"[{ci[0]:.4f}, {ci[1]:.4f}] | "
                f"{item['normalized_energy_holm_p']:.4f} | "
                f"{item['panel_holm_p']:.4f} | "
                f"{'confirmed' if item['confirmed'] else 'not confirmed'} |"
            )
    lines.extend(
        [
            "",
            "Operational coverage: SJTU MiniMax-M2.7 and Qwen3.6-27B remain "
            "failed availability gates and are not scientific null results.",
            "",
            "The panel-level Holm values cover all six active "
            "deployment-by-contrast distributional tests. No pooling, model "
            "vote, checkpoint-identity claim, or NPU-versus-GPU claim is made.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    deployments: dict[str, dict[str, Any]] = {}
    raw_p: dict[str, float] = {}
    for label, report_path in args.report:
        if label in deployments:
            raise ValueError(f"Duplicate deployment label: {label}")
        report = json.loads(Path(report_path).read_text(encoding="utf-8"))
        if report.get("operational_gate") is not True:
            raise ValueError(f"Operational gate did not pass for {label}")
        deployments[label] = report
        for contrast, item in report["contrasts"].items():
            raw_p[f"{label}|{contrast}"] = float(
                item["normalized_energy_permutation_p"]
            )
    if len(deployments) != 3 or len(raw_p) != 6:
        raise ValueError("The frozen endpoint summary requires three deployments and six tests")
    adjusted = holm_adjust(raw_p)
    for label, report in deployments.items():
        for contrast, item in report["contrasts"].items():
            item["panel_holm_p"] = adjusted[f"{label}|{contrast}"]
    summary = {
        "analysis_status": "SUPPLEMENTAL_POST_SUBMISSION_EVIDENCE",
        "panel_multiple_testing_family": "Holm across six active deployment-by-contrast distributional tests",
        "operational_failures_retained": [
            "sjtu_zhiyuan1/minimax-m2.7",
            "sjtu_zhiyuan1/qwen3.6-27b",
        ],
        "deployments_are_independent_model_samples": False,
        "deployments": deployments,
    }
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    args.markdown_output.write_text(render_markdown(summary), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
