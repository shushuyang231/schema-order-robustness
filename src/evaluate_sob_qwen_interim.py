"""Evaluate the frozen 40-record Qwen futility interim without an efficacy test."""

from __future__ import annotations

import argparse
import json
import math
import statistics
from collections import Counter
from pathlib import Path
from typing import Any

from analyze_sob_contrast_decomposition import load_run_cells, summarize_cell
from evaluate_sob_repeated_pilot import bootstrap_mean_ci, excess_disagreement
from sob_metamorphic import load_jsonl


QWEN_FUTILITY_STAGES = frozenset(
    {
        "prospective_qwen_futility_interim_40",
        "prospective_qwen_plus_resource_futility_interim_100",
    }
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--public-input", type=Path, required=True)
    parser.add_argument("--gold-input", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, required=True)
    return parser.parse_args()


def normal_upper_probability(
    *, mean: float, sample_sd: float, interim_n: int, final_n: int, threshold: float
) -> float:
    remaining = final_n - interim_n
    if remaining <= 0:
        raise ValueError("Final record count must exceed interim record count")
    conditional_se = sample_sd * math.sqrt(remaining) / final_n
    if conditional_se == 0:
        return float(mean >= threshold)
    z = (threshold - mean) / conditional_se
    return 0.5 * math.erfc(z / math.sqrt(2.0))


def render_markdown(report: dict[str, Any]) -> str:
    title = report.get("display_name") or (
        f"Qwen {report['record_count']}-Record Futility Interim"
    )
    lines = [
        f"# {title}",
        "",
        f"Decision: **{report['decision']}**",
        "",
        f"Model: `{report['model_alias']}`; records: {report['record_count']}; "
        f"successful responses: {report['successful_response_count']}.",
        "",
        "| Contrast | Interim excess (descriptive 95% CI) | Conditional probability final mean >= 0.05 |",
        "|---|---:|---:|",
    ]
    for name, item in report["contrasts"].items():
        ci = item["descriptive_bootstrap_ci95"]
        lines.append(
            f"| {name} | {item['interim_mean_excess']:.4f} "
            f"[{ci[0]:.4f}, {ci[1]:.4f}] | "
            f"{item['conditional_probability_final_ge_0_05']:.4f} |"
        )
    lines.extend(
        [
            "",
            "This is the single prospectively frozen futility look. It does not "
            "perform or permit an early efficacy claim. STOP_FOR_FUTILITY means "
            "insufficient promise of reaching the study-specific 0.05 practical "
            f"magnitude at {report['maximum_record_count']} records; it does not "
            "mean an exactly zero effect.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    if manifest.get("analysis_stage") not in QWEN_FUTILITY_STAGES:
        raise ValueError("Manifest is not the frozen Qwen interim manifest")
    interim_design = manifest["interim_design"]
    expected_n = int(interim_design["interim_record_count"])
    final_n = int(interim_design["maximum_record_count"])
    threshold = float(interim_design["practical_effect_threshold"])
    continuation_probability = float(
        interim_design["per_contrast_continuation_probability"]
    )
    record_id_set = {str(value) for value in manifest["record_ids"]}
    public = {
        str(row["record_id"]): row
        for row in load_jsonl(args.public_input)
        if str(row["record_id"]) in record_id_set
    }
    gold = {
        str(row["record_id"]): row["ground_truth"]
        for row in load_jsonl(args.gold_input)
        if str(row["record_id"]) in record_id_set
    }
    record_ids, cells = load_run_cells(
        manifest_path=args.manifest,
        predictions_path=args.predictions,
        public=public,
        gold=gold,
        allow_extra_prediction_records=True,
    )
    if len(record_ids) != expected_n:
        raise ValueError("Interim record count differs from the frozen design")
    summaries = {key: summarize_cell(values) for key, values in cells.items()}
    contrasts: dict[str, dict[str, Any]] = {}
    for name, pair in manifest["primary_contrasts"].items():
        left_name, right_name = map(str, pair)
        effects = [
            excess_disagreement(
                summaries[(record_id, left_name)]["normalized_signatures"],
                summaries[(record_id, right_name)]["normalized_signatures"],
            )
            for record_id in record_ids
        ]
        mean = statistics.fmean(effects)
        sample_sd = statistics.stdev(effects)
        probability = normal_upper_probability(
            mean=mean,
            sample_sd=sample_sd,
            interim_n=len(record_ids),
            final_n=final_n,
            threshold=threshold,
        )
        seed_namespace = str(
            manifest.get("bootstrap_seed_namespace", "qwen-futility-interim")
        )
        contrasts[name] = {
            "interim_mean_excess": mean,
            "interim_sample_sd": sample_sd,
            "descriptive_bootstrap_ci95": bootstrap_mean_ci(
                effects,
                f"{seed_namespace}:{manifest['model_alias']}:{name}",
            ),
            "conditional_probability_final_ge_0_05": probability,
            "passes_continuation_probability": probability
            >= continuation_probability,
        }

    successful_rows = [
        row
        for row in load_jsonl(args.predictions)
        if row.get("status") == "ok" and str(row.get("record_id")) in record_id_set
    ]
    returned_models = Counter(str(row.get("returned_model")) for row in successful_rows)
    schema_pass_rate = statistics.fmean(
        bool(row.get("schema_valid")) for row in successful_rows
    )
    operational_gate = (
        len(successful_rows) == int(manifest["expected_requests"])
        and len(returned_models) == 1
        and schema_pass_rate >= 0.95
    )
    if not operational_gate:
        decision = "QWEN_INTERIM_INCOMPLETE"
    elif any(
        item["passes_continuation_probability"] for item in contrasts.values()
    ):
        decision = str(interim_design.get("continue_decision", "CONTINUE_TO_FULL_200"))
    else:
        decision = str(interim_design.get("stop_decision", "STOP_FOR_FUTILITY"))

    token_usage = {
        "input_tokens": sum(int(row.get("input_tokens") or 0) for row in successful_rows),
        "output_tokens": sum(int(row.get("output_tokens") or 0) for row in successful_rows),
    }
    token_usage["total_tokens"] = (
        token_usage["input_tokens"] + token_usage["output_tokens"]
    )
    report = {
        "decision": decision,
        "analysis_stage": manifest["analysis_stage"],
        "model_alias": manifest["model_alias"],
        "record_count": len(record_ids),
        "maximum_record_count": final_n,
        "successful_response_count": len(successful_rows),
        "overall_schema_pass_rate": schema_pass_rate,
        "returned_model_counts": dict(returned_models),
        "operational_gate": operational_gate,
        "minimum_practical_effect": threshold,
        "per_contrast_continuation_probability": continuation_probability,
        "no_early_efficacy_test": True,
        "display_name": interim_design.get("display_name"),
        "token_usage": token_usage,
        "contrasts": contrasts,
    }
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    args.markdown_output.write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if operational_gate else 1


if __name__ == "__main__":
    raise SystemExit(main())
