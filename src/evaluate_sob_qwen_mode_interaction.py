"""Compare matched Qwen-Plus text-mode and JSON-Mode order effects."""

from __future__ import annotations

import argparse
import json
import statistics
from collections import Counter
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
    parser.add_argument("--text-manifest", type=Path, required=True)
    parser.add_argument("--text-predictions", type=Path, required=True)
    parser.add_argument("--json-manifest", type=Path, required=True)
    parser.add_argument("--json-predictions", type=Path, required=True)
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, required=True)
    return parser.parse_args()


def classify_mode_change(
    mean_change: float,
    ci95: list[float],
    holm_p: float,
    threshold: float,
) -> str:
    if holm_p >= 0.05 or ci95[0] <= 0 <= ci95[1] or abs(mean_change) < threshold:
        return "NO_MATERIAL_MODE_CHANGE_CONFIRMED"
    return "MATERIAL_AMPLIFICATION" if mean_change > 0 else "MATERIAL_ATTENUATION"


def successful_rows(path: Path, record_ids: set[str]) -> list[dict[str, Any]]:
    return [
        row
        for row in load_jsonl(path)
        if row.get("status") == "ok" and str(row.get("record_id")) in record_ids
    ]


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Qwen-Plus Text Mode vs JSON Mode",
        "",
        f"Decision: **{report['decision']}**",
        "",
        "> JSON Mode means `response_format={\"type\":\"json_object\"}`. "
        "It is not strict JSON Schema constrained decoding.",
        "",
        "| Contrast | Text effect | JSON-Mode effect | Mode change (95% CI) | Holm p | Classification |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for name, item in report["contrasts"].items():
        ci = item["mode_change_ci95"]
        lines.append(
            f"| {name} | {item['text_mode_excess']:.4f} | "
            f"{item['json_mode_excess']:.4f} | {item['mode_change']:+.4f} "
            f"[{ci[0]:+.4f}, {ci[1]:+.4f}] | "
            f"{item['mode_change_holm_p']:.4f} | {item['classification']} |"
        )
    lines.extend(
        [
            "",
            "The mode change is JSON-Mode excess minus text-mode excess at the "
            "record level. A material classification requires absolute change "
            f"at least {report['material_mode_change_threshold']:.2f}, a bootstrap "
            "interval excluding zero, and Holm-adjusted p < 0.05.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    text_manifest = json.loads(args.text_manifest.read_text(encoding="utf-8"))
    json_manifest = json.loads(args.json_manifest.read_text(encoding="utf-8"))
    if json_manifest.get("analysis_stage") != "prospective_qwen_plus_json_mode_ablation_100":
        raise ValueError("JSON manifest is not the frozen mode ablation")
    if json_manifest.get("request_body_extra", {}).get("response_format") != {
        "type": "json_object"
    }:
        raise ValueError("JSON manifest does not request json_object mode")
    for field in ("record_ids", "conditions", "primary_contrasts", "model_alias"):
        if text_manifest.get(field) != json_manifest.get(field):
            raise ValueError(f"Matched mode manifests differ on {field}")

    record_ids = [str(value) for value in json_manifest["record_ids"]]
    record_id_set = set(record_ids)
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
    text_ids, text_cells = load_run_cells(
        manifest_path=args.text_manifest,
        predictions_path=args.text_predictions,
        public=public,
        gold=gold,
        allow_extra_prediction_records=True,
    )
    json_ids, json_cells = load_run_cells(
        manifest_path=args.json_manifest,
        predictions_path=args.json_predictions,
        public=public,
        gold=gold,
    )
    if text_ids != json_ids:
        raise ValueError("Matched modes use different record order")
    text_summaries = {key: summarize_cell(value) for key, value in text_cells.items()}
    json_summaries = {key: summarize_cell(value) for key, value in json_cells.items()}

    raw_p: dict[str, float] = {}
    contrasts: dict[str, dict[str, Any]] = {}
    primary = {
        name: tuple(value)
        for name, value in json_manifest["primary_contrasts"].items()
    }
    for name, (left_name, right_name) in primary.items():
        text_effects: list[float] = []
        json_effects: list[float] = []
        changes: list[float] = []
        leaf_changes: list[float] = []
        for record_id in record_ids:
            text_left = text_summaries[(record_id, left_name)]
            text_right = text_summaries[(record_id, right_name)]
            json_left = json_summaries[(record_id, left_name)]
            json_right = json_summaries[(record_id, right_name)]
            text_effect = excess_disagreement(
                text_left["normalized_signatures"],
                text_right["normalized_signatures"],
            )
            json_effect = excess_disagreement(
                json_left["normalized_signatures"],
                json_right["normalized_signatures"],
            )
            text_effects.append(text_effect)
            json_effects.append(json_effect)
            changes.append(json_effect - text_effect)
            leaf_changes.append(
                (
                    json_right["leaf_value_accuracy"]
                    - json_left["leaf_value_accuracy"]
                )
                - (
                    text_right["leaf_value_accuracy"]
                    - text_left["leaf_value_accuracy"]
                )
            )
        label = f"qwen-plus-mode-interaction:{name}"
        raw_p[name] = sign_flip_p(changes, label)
        contrasts[name] = {
            "left": left_name,
            "right": right_name,
            "text_mode_excess": statistics.fmean(text_effects),
            "json_mode_excess": statistics.fmean(json_effects),
            "mode_change": statistics.fmean(changes),
            "mode_change_ci95": bootstrap_mean_ci(changes, label),
            "leaf_accuracy_interaction": statistics.fmean(leaf_changes),
            "leaf_accuracy_interaction_ci95": bootstrap_mean_ci(
                leaf_changes, label + ":leaf"
            ),
        }

    adjusted = holm_adjust(raw_p)
    threshold = float(json_manifest["mode_interaction_minimum_effect"])
    for name, item in contrasts.items():
        item["mode_change_sign_flip_p"] = raw_p[name]
        item["mode_change_holm_p"] = adjusted[name]
        item["classification"] = classify_mode_change(
            item["mode_change"],
            item["mode_change_ci95"],
            item["mode_change_holm_p"],
            threshold,
        )

    text_rows = successful_rows(args.text_predictions, record_id_set)
    json_rows = successful_rows(args.json_predictions, record_id_set)
    json_contract_rows = [
        row
        for row in json_rows
        if (row.get("request_parameters") or {}).get("response_format")
        == {"type": "json_object"}
    ]
    returned_text = Counter(str(row.get("returned_model")) for row in text_rows)
    returned_json = Counter(str(row.get("returned_model")) for row in json_rows)
    operational_gate = (
        len(text_rows) == int(text_manifest["expected_requests"])
        and len(json_rows) == int(json_manifest["expected_requests"])
        and len(json_contract_rows) == len(json_rows)
        and len(returned_text) == 1
        and returned_text == returned_json
    )
    classifications = [item["classification"] for item in contrasts.values()]
    if not operational_gate:
        decision = "MODE_INTERACTION_INCOMPLETE"
    elif all(value == "MATERIAL_ATTENUATION" for value in classifications):
        decision = "JSON_MODE_ATTENUATES_BOTH_CONTRASTS"
    elif any(value != "NO_MATERIAL_MODE_CHANGE_CONFIRMED" for value in classifications):
        decision = "JSON_MODE_MATERIALLY_CHANGES_AT_LEAST_ONE_CONTRAST"
    else:
        decision = "NO_MATERIAL_JSON_MODE_INTERACTION_CONFIRMED"

    report = {
        "decision": decision,
        "analysis_stage": "prospective_qwen_plus_text_vs_json_mode_interaction_100",
        "selection_disclosure": json_manifest["selection_disclosure"],
        "record_count": len(record_ids),
        "text_mode_successful_responses": len(text_rows),
        "json_mode_successful_responses": len(json_rows),
        "returned_model_counts_text": dict(returned_text),
        "returned_model_counts_json": dict(returned_json),
        "json_mode_request_contract_rows": len(json_contract_rows),
        "operational_gate": operational_gate,
        "material_mode_change_threshold": threshold,
        "multiple_testing": "Holm across two mode-by-order interactions",
        "contrasts": contrasts,
    }
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    args.markdown_output.write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if operational_gate else 1


if __name__ == "__main__":
    raise SystemExit(main())
