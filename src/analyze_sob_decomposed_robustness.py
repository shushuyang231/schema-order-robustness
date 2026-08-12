"""Post-hoc concentration and cross-system robustness audit for decomposed runs."""

from __future__ import annotations

import argparse
import itertools
import json
import math
import statistics
from pathlib import Path
from typing import Any

from analyze_sob_contrast_decomposition import load_run_cells, summarize_cell
from analyze_sob_cross_model_exploratory import (
    bootstrap_spearman_ci,
    permutation_correlation_p,
    spearman,
)
from evaluate_sob_repeated_pilot import excess_disagreement, holm_adjust
from sob_metamorphic import load_jsonl


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--public-input", type=Path, required=True)
    parser.add_argument("--gold-input", type=Path, required=True)
    parser.add_argument(
        "--run",
        nargs=3,
        action="append",
        metavar=("LABEL", "MANIFEST", "PREDICTIONS"),
        required=True,
        help="Label, manifest, and prediction JSONL; may be repeated.",
    )
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, required=True)
    return parser.parse_args()


def trimmed_mean(values: list[float], fraction: float = 0.10) -> float:
    if not values:
        raise ValueError("Cannot summarize an empty effect vector")
    cut = math.floor(len(values) * fraction)
    ordered = sorted(values)
    retained = ordered[cut : len(ordered) - cut] if cut else ordered
    return statistics.fmean(retained)


def concentration_summary(values: list[float]) -> dict[str, float]:
    if not values:
        raise ValueError("Cannot summarize an empty effect vector")
    removal_count = max(1, math.ceil(len(values) * 0.10))
    descending = sorted(values, reverse=True)
    without_largest = descending[removal_count:]
    positive_mass = sum(max(value, 0.0) for value in values)
    top_positive_mass = sum(max(value, 0.0) for value in descending[:removal_count])
    return {
        "mean": statistics.fmean(values),
        "median": statistics.median(values),
        "symmetric_10pct_trimmed_mean": trimmed_mean(values),
        "mean_after_removing_largest_10pct": statistics.fmean(without_largest),
        "largest_10pct_positive_mass_share": (
            top_positive_mass / positive_mass if positive_mass else 0.0
        ),
        "nonzero_record_fraction": sum(value != 0 for value in values) / len(values),
        "positive_record_fraction": sum(value > 0 for value in values) / len(values),
    }


def load_effects(
    manifest_path: Path,
    predictions_path: Path,
    public_all: dict[str, dict[str, Any]],
    gold_all: dict[str, dict[str, Any]],
) -> tuple[dict[str, Any], dict[str, dict[str, float]]]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    record_ids = [str(value) for value in manifest["record_ids"]]
    public = {record_id: public_all[record_id] for record_id in record_ids}
    gold = {record_id: gold_all[record_id] for record_id in record_ids}
    loaded_ids, cells = load_run_cells(
        manifest_path=manifest_path,
        predictions_path=predictions_path,
        public=public,
        gold=gold,
        allow_extra_prediction_records=True,
    )
    summaries = {key: summarize_cell(values) for key, values in cells.items()}
    effects: dict[str, dict[str, float]] = {}
    for record_id in loaded_ids:
        effects[record_id] = {}
        for name, (left_name, right_name) in manifest["primary_contrasts"].items():
            effects[record_id][str(name)] = excess_disagreement(
                summaries[(record_id, str(left_name))]["normalized_signatures"],
                summaries[(record_id, str(right_name))]["normalized_signatures"],
            )
    return manifest, effects


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Decomposed Effect Robustness Audit",
        "",
        "**Status: post-hoc descriptive/exploratory. Confirmatory decisions are unchanged.**",
        "",
        "## Effect concentration",
        "",
        "| System | Contrast | n | Mean | 10% trimmed | Remove largest 10% | Top-decile positive mass |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for label, run in report["runs"].items():
        for contrast, item in run["contrasts"].items():
            lines.append(
                f"| {label} | {contrast} | {run['record_count']} | {item['mean']:.4f} | "
                f"{item['symmetric_10pct_trimmed_mean']:.4f} | "
                f"{item['mean_after_removing_largest_10pct']:.4f} | "
                f"{item['largest_10pct_positive_mass_share']:.1%} |"
            )
    lines.extend(
        [
            "",
            "## Cross-system record concordance",
            "",
            "| Pair | Contrast | Shared n | Spearman rho (95% CI) | Global Holm p |",
            "|---|---|---:|---:|---:|",
        ]
    )
    for item in report["cross_system_concordance"]:
        ci = item["rho_ci95"]
        lines.append(
            f"| {item['left']} vs {item['right']} | {item['contrast']} | "
            f"{item['shared_record_count']} | {item['spearman_rho']:+.3f} "
            f"[{ci[0]:+.3f}, {ci[1]:+.3f}] | {item['holm_p']:.4f} |"
        )
    lines.extend(
        [
            "",
            "The concentration deletions and all cross-system analyses were specified after "
            "observing earlier model reports. They diagnose robustness and heterogeneity; "
            "they do not replace or upgrade a frozen confirmatory decision.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    public_all = {
        str(row["record_id"]): row for row in load_jsonl(args.public_input)
    }
    gold_all = {
        str(row["record_id"]): row["ground_truth"]
        for row in load_jsonl(args.gold_input)
    }
    loaded: dict[str, dict[str, Any]] = {}
    for label, manifest_path, predictions_path in args.run:
        if label in loaded:
            raise ValueError(f"Duplicate run label: {label}")
        manifest, effects = load_effects(
            Path(manifest_path), Path(predictions_path), public_all, gold_all
        )
        contrasts: dict[str, dict[str, Any]] = {}
        for contrast in manifest["primary_contrasts"]:
            values = [effects[record_id][contrast] for record_id in effects]
            item: dict[str, Any] = concentration_summary(values)
            item["by_schema_complexity"] = {
                stratum: statistics.fmean(
                    effects[record_id][contrast]
                    for record_id in effects
                    if str(public_all[record_id]["schema_complexity"]) == stratum
                )
                for stratum in sorted(
                    {str(public_all[record_id]["schema_complexity"]) for record_id in effects}
                )
            }
            contrasts[str(contrast)] = item
        loaded[label] = {
            "manifest": str(manifest_path),
            "predictions": str(predictions_path),
            "analysis_stage": manifest.get("analysis_stage"),
            "model_alias": manifest.get("model_alias"),
            "record_count": len(effects),
            "effects": effects,
            "contrasts": contrasts,
        }

    concordance: list[dict[str, Any]] = []
    raw_p: dict[str, float] = {}
    for (left_label, left), (right_label, right) in itertools.combinations(
        loaded.items(), 2
    ):
        shared_ids = sorted(set(left["effects"]) & set(right["effects"]))
        shared_contrasts = sorted(
            set(left["contrasts"]) & set(right["contrasts"])
        )
        for contrast in shared_contrasts:
            left_values = [left["effects"][record_id][contrast] for record_id in shared_ids]
            right_values = [right["effects"][record_id][contrast] for record_id in shared_ids]
            key = f"{left_label}|{right_label}|{contrast}"
            rho = spearman(left_values, right_values)
            raw_p[key] = permutation_correlation_p(left_values, right_values, key)
            concordance.append(
                {
                    "key": key,
                    "left": left_label,
                    "right": right_label,
                    "contrast": contrast,
                    "shared_record_count": len(shared_ids),
                    "spearman_rho": rho,
                    "rho_ci95": bootstrap_spearman_ci(left_values, right_values, key),
                    "permutation_p": raw_p[key],
                }
            )
    adjusted = holm_adjust(raw_p)
    for item in concordance:
        item["holm_p"] = adjusted[item.pop("key")]

    serializable_runs = {
        label: {key: value for key, value in run.items() if key != "effects"}
        for label, run in loaded.items()
    }
    report = {
        "analysis_status": "POST_HOC_ROBUSTNESS_ONLY",
        "claim_boundary": (
            "Concentration and transfer analyses do not alter any prospectively "
            "frozen model-level decision."
        ),
        "multiple_testing": (
            "One global Holm family across all pairwise system-by-contrast "
            "record-concordance tests."
        ),
        "runs": serializable_runs,
        "cross_system_concordance": concordance,
    }
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    args.markdown_output.write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
