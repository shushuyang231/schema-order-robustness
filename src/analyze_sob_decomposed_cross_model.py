"""Post-hoc paired cross-model analysis for the decomposed confirmation study.

This analysis was specified after both model reports were observed.  It avoids
the invalid inference that an effect confirmed in one model and not another is
itself proof of a model difference.
"""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path
from typing import Any

from analyze_sob_contrast_decomposition import load_run_cells, summarize_cell
from evaluate_sob_repeated_pilot import (
    bootstrap_mean_ci,
    excess_disagreement,
    holm_adjust,
    sign_flip_p,
)
from sob_metamorphic import load_jsonl


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--public-input", type=Path, required=True)
    parser.add_argument("--gold-input", type=Path, required=True)
    parser.add_argument("--left-label", required=True)
    parser.add_argument("--left-manifest", type=Path, required=True)
    parser.add_argument("--left-predictions", type=Path, required=True)
    parser.add_argument("--right-label", required=True)
    parser.add_argument("--right-manifest", type=Path, required=True)
    parser.add_argument("--right-predictions", type=Path, required=True)
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, required=True)
    return parser.parse_args()


def record_contrast(
    summary: dict[tuple[str, str], dict[str, Any]],
    record_id: str,
    left_variant: str,
    right_variant: str,
) -> tuple[float, float]:
    left = summary[(record_id, left_variant)]
    right = summary[(record_id, right_variant)]
    distribution = excess_disagreement(
        left["normalized_signatures"], right["normalized_signatures"]
    )
    accuracy = right["leaf_value_accuracy"] - left["leaf_value_accuracy"]
    return distribution, accuracy


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Post-hoc Paired Cross-Model Decomposition",
        "",
        "**Exploratory only: specified after both formal reports were observed.**",
        "",
        f"Difference direction: `{report['difference_direction']}`.",
        "",
        "| Contrast | Distribution difference (95% CI) | Holm p | "
        "Accuracy contrast difference (95% CI) | Holm p |",
        "|---|---:|---:|---:|---:|",
    ]
    for name, item in report["contrasts"].items():
        dci = item["distribution_difference_ci95"]
        aci = item["accuracy_difference_of_differences_ci95"]
        lines.append(
            f"| {name} | {item['distribution_difference']:.4f} "
            f"[{dci[0]:.4f}, {dci[1]:.4f}] | "
            f"{item['distribution_difference_holm_p']:.4f} | "
            f"{item['accuracy_difference_of_differences']:.4f} "
            f"[{aci[0]:.4f}, {aci[1]:.4f}] | "
            f"{item['accuracy_difference_holm_p']:.4f} |"
        )
    lines.extend(
        [
            "",
            "A corrected paired difference may support an exploratory statement "
            "about heterogeneity, but it does not retroactively convert the "
            "model-specific preregistered decisions into a preregistered "
            "cross-model test.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    public = {str(row["record_id"]): row for row in load_jsonl(args.public_input)}
    gold = {
        str(row["record_id"]): row["ground_truth"] for row in load_jsonl(args.gold_input)
    }
    left_ids, left_cells = load_run_cells(
        manifest_path=args.left_manifest,
        predictions_path=args.left_predictions,
        public=public,
        gold=gold,
    )
    right_ids, right_cells = load_run_cells(
        manifest_path=args.right_manifest,
        predictions_path=args.right_predictions,
        public=public,
        gold=gold,
    )
    if left_ids != right_ids:
        raise ValueError("The model manifests do not have identical ordered record IDs")

    left_manifest = json.loads(args.left_manifest.read_text(encoding="utf-8"))
    right_manifest = json.loads(args.right_manifest.read_text(encoding="utf-8"))
    if left_manifest["primary_contrasts"] != right_manifest["primary_contrasts"]:
        raise ValueError("The model manifests do not have identical contrasts")
    contrasts = {
        name: tuple(value)
        for name, value in left_manifest["primary_contrasts"].items()
    }
    left_summary = {key: summarize_cell(values) for key, values in left_cells.items()}
    right_summary = {key: summarize_cell(values) for key, values in right_cells.items()}

    results: dict[str, dict[str, Any]] = {}
    raw_distribution_p: dict[str, float] = {}
    raw_accuracy_p: dict[str, float] = {}
    for name, (baseline, treatment) in contrasts.items():
        left_distribution: list[float] = []
        right_distribution: list[float] = []
        left_accuracy: list[float] = []
        right_accuracy: list[float] = []
        for record_id in left_ids:
            left_d, left_a = record_contrast(
                left_summary, record_id, baseline, treatment
            )
            right_d, right_a = record_contrast(
                right_summary, record_id, baseline, treatment
            )
            left_distribution.append(left_d)
            right_distribution.append(right_d)
            left_accuracy.append(left_a)
            right_accuracy.append(right_a)

        distribution_differences = [
            left - right
            for left, right in zip(left_distribution, right_distribution, strict=True)
        ]
        accuracy_differences = [
            left - right
            for left, right in zip(left_accuracy, right_accuracy, strict=True)
        ]
        label = f"decomposed-cross-model:{name}"
        raw_distribution_p[name] = sign_flip_p(
            distribution_differences, label + ":distribution"
        )
        raw_accuracy_p[name] = sign_flip_p(
            accuracy_differences, label + ":accuracy"
        )
        results[name] = {
            "baseline": baseline,
            "treatment": treatment,
            "left_distribution_effect": statistics.fmean(left_distribution),
            "right_distribution_effect": statistics.fmean(right_distribution),
            "distribution_difference": statistics.fmean(distribution_differences),
            "distribution_difference_ci95": bootstrap_mean_ci(
                distribution_differences, label + ":distribution"
            ),
            "left_accuracy_contrast": statistics.fmean(left_accuracy),
            "right_accuracy_contrast": statistics.fmean(right_accuracy),
            "accuracy_difference_of_differences": statistics.fmean(
                accuracy_differences
            ),
            "accuracy_difference_of_differences_ci95": bootstrap_mean_ci(
                accuracy_differences, label + ":accuracy"
            ),
        }

    distribution_holm = holm_adjust(raw_distribution_p)
    accuracy_holm = holm_adjust(raw_accuracy_p)
    for name, item in results.items():
        item["distribution_difference_sign_flip_p"] = raw_distribution_p[name]
        item["distribution_difference_holm_p"] = distribution_holm[name]
        item["accuracy_difference_sign_flip_p"] = raw_accuracy_p[name]
        item["accuracy_difference_holm_p"] = accuracy_holm[name]

    report = {
        "analysis_status": "POST_HOC_EXPLORATORY_ONLY",
        "claim_boundary": (
            "Direct paired model differences were specified after both formal "
            "reports were observed and do not alter either preregistered decision."
        ),
        "record_count": len(left_ids),
        "left_label": args.left_label,
        "right_label": args.right_label,
        "difference_direction": f"{args.left_label} minus {args.right_label}",
        "multiple_testing": (
            "Holm across the two primary contrasts separately for distribution "
            "and accuracy difference families"
        ),
        "contrasts": results,
    }
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    args.markdown_output.write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
