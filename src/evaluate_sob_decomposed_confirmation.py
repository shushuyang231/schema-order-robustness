"""Evaluate a preregistered decomposed Schema-order confirmation run."""

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
    energy_permutation_p,
    excess_disagreement,
    holm_adjust,
    sign_flip_p,
)
from sob_metamorphic import load_jsonl


DECOMPOSED_CONFIRMATION_STAGES = frozenset(
    {
        "preregistered_decomposed_contrast_confirmation",
        "preregistered_official_deepseek_replication",
        "prospective_qwen_staged_confirmation_full_200",
        "prospective_qwen_plus_resource_confirmation_full_160",
        "prospective_qwen_plus_json_mode_ablation_100",
        "prospective_endpoint_panel",
    }
)


def validate_decomposed_manifest(manifest: dict[str, Any]) -> None:
    if manifest.get("analysis_stage") not in DECOMPOSED_CONFIRMATION_STAGES:
        raise ValueError("Manifest is not a decomposed confirmation manifest")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--public-input", type=Path, required=True)
    parser.add_argument("--gold-input", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, required=True)
    return parser.parse_args()


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Decomposed Schema-Order Confirmation",
        "",
        f"Decision: **{report['decision']}**",
        "",
        f"Model alias: `{report['model_alias']}`; records: {report['record_count']}; "
        f"successful responses: {report['successful_response_count']}.",
        "",
        "| Primary contrast | Normalized excess (95% CI) | Holm p | "
        "Leaf accuracy difference (95% CI) | Confirmed |",
        "|---|---:|---:|---:|---|",
    ]
    for name, item in report["contrasts"].items():
        nci = item["normalized_excess_ci95"]
        lci = item["leaf_accuracy_ci95"]
        lines.append(
            f"| {name} | {item['normalized_excess_disagreement']:.4f} "
            f"[{nci[0]:.4f}, {nci[1]:.4f}] | "
            f"{item['normalized_energy_holm_p']:.4f} | "
            f"{item['leaf_value_accuracy_difference']:.4f} "
            f"[{lci[0]:.4f}, {lci[1]:.4f}] | "
            f"{'Yes' if item['confirmed'] else 'No'} |"
        )
    lines.extend(
        [
            "",
            "The two contrasts and the 0.05 practical threshold were frozen before "
            "these API calls. A non-confirmed contrast is retained and does not "
            "trigger record replacement, threshold changes, or model shopping.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    validate_decomposed_manifest(manifest)
    manifest_record_ids = {str(value) for value in manifest["record_ids"]}
    public = {
        str(row["record_id"]): row
        for row in load_jsonl(args.public_input)
        if str(row["record_id"]) in manifest_record_ids
    }
    gold = {
        str(row["record_id"]): row["ground_truth"]
        for row in load_jsonl(args.gold_input)
        if str(row["record_id"]) in manifest_record_ids
    }
    record_ids, cells = load_run_cells(
        manifest_path=args.manifest,
        predictions_path=args.predictions,
        public=public,
        gold=gold,
    )
    summaries = {key: summarize_cell(values) for key, values in cells.items()}
    primary = {
        name: tuple(value) for name, value in manifest["primary_contrasts"].items()
    }
    raw_distribution_p: dict[str, float] = {}
    raw_leaf_p: dict[str, float] = {}
    contrasts: dict[str, dict[str, Any]] = {}
    for name, (left_name, right_name) in primary.items():
        groups: list[tuple[list[str], list[str]]] = []
        excesses: list[float] = []
        leaf_differences: list[float] = []
        for record_id in record_ids:
            left = summaries[(record_id, left_name)]
            right = summaries[(record_id, right_name)]
            group = (
                left["normalized_signatures"],
                right["normalized_signatures"],
            )
            groups.append(group)
            excesses.append(excess_disagreement(*group))
            leaf_differences.append(
                right["leaf_value_accuracy"] - left["leaf_value_accuracy"]
            )
        mean_excess = statistics.fmean(excesses)
        mean_leaf = statistics.fmean(leaf_differences)
        label = f"decomposed-confirmation:{manifest['model_alias']}:{name}"
        raw_distribution_p[name] = energy_permutation_p(
            groups, mean_excess, label + ":distribution"
        )
        raw_leaf_p[name] = sign_flip_p(leaf_differences, label + ":leaf")
        contrasts[name] = {
            "left": left_name,
            "right": right_name,
            "normalized_excess_disagreement": mean_excess,
            "normalized_excess_ci95": bootstrap_mean_ci(
                excesses, label + ":distribution"
            ),
            "leaf_value_accuracy_difference": mean_leaf,
            "leaf_accuracy_ci95": bootstrap_mean_ci(
                leaf_differences, label + ":leaf"
            ),
        }

    distribution_holm = holm_adjust(raw_distribution_p)
    leaf_holm = holm_adjust(raw_leaf_p)
    threshold = float(manifest["minimum_practical_effect"])
    for name, item in contrasts.items():
        item["normalized_energy_permutation_p"] = raw_distribution_p[name]
        item["normalized_energy_holm_p"] = distribution_holm[name]
        item["leaf_accuracy_sign_flip_p"] = raw_leaf_p[name]
        item["leaf_accuracy_holm_p"] = leaf_holm[name]
        item["confirmed"] = (
            item["normalized_excess_disagreement"] >= threshold
            and item["normalized_excess_ci95"][0] > 0
            and item["normalized_energy_holm_p"] < 0.05
        )

    raw_rows = load_jsonl(args.predictions)
    successful_line_rows = [
        row
        for row in raw_rows
        if row.get("status") == "ok"
        and str(row.get("record_id")) in manifest_record_ids
    ]
    successful_by_key: dict[str, dict[str, Any]] = {}
    for row in successful_line_rows:
        successful_by_key[str(row.get("request_key"))] = row
    successful_rows = list(successful_by_key.values())
    returned_models = Counter(str(row.get("returned_model")) for row in successful_rows)
    smoke_hashes = {
        str(row.get("smoke_record_sha256"))
        for row in successful_rows
        if row.get("smoke_record_sha256") is not None
    }
    non_null_fingerprints = {
        str(row.get("system_fingerprint"))
        for row in successful_rows
        if row.get("system_fingerprint") is not None
    }
    response_ids = [str(row["response_id"]) for row in successful_rows if row.get("response_id")]
    schema_pass_rate = statistics.fmean(
        bool(row.get("schema_valid")) for row in successful_rows
    )
    operational_gate = (
        len(successful_rows) == int(manifest["expected_requests"])
        and len(successful_line_rows) == int(manifest["expected_requests"])
        and len(returned_models) == 1
        and len(smoke_hashes) == 1
        and len(non_null_fingerprints) <= 1
        and schema_pass_rate >= 0.95
        and (not response_ids or len(response_ids) == len(set(response_ids)))
    )
    confirmed_count = sum(item["confirmed"] for item in contrasts.values())
    if not operational_gate:
        decision = "DECOMPOSED_CONFIRMATION_INCOMPLETE"
    elif confirmed_count == len(contrasts):
        decision = "BOTH_DECOMPOSED_CONTRASTS_CONFIRMED"
    elif confirmed_count:
        decision = "PARTIAL_DECOMPOSED_CONFIRMATION"
    else:
        decision = "DECOMPOSED_CONFIRMATION_NOT_FOUND"

    token_usage = {
        "input_tokens": sum(int(row.get("input_tokens") or 0) for row in successful_rows),
        "output_tokens": sum(int(row.get("output_tokens") or 0) for row in successful_rows),
        "cached_input_tokens": sum(
            int(((row.get("usage") or {}).get("prompt_tokens_details") or {}).get("cached_tokens") or 0)
            for row in successful_rows
        ),
    }
    token_usage["total_tokens"] = (
        token_usage["input_tokens"] + token_usage["output_tokens"]
    )

    report = {
        "decision": decision,
        "analysis_stage": manifest["analysis_stage"],
        "model_alias": manifest["model_alias"],
        "record_count": len(record_ids),
        "successful_response_count": len(successful_rows),
        "overall_schema_pass_rate": schema_pass_rate,
        "returned_model_counts": dict(returned_models),
        "smoke_record_sha256_count": len(smoke_hashes),
        "non_null_system_fingerprint_count": len(non_null_fingerprints),
        "source_log_audit": {
            "raw_line_count": len(raw_rows),
            "successful_line_count": len(successful_line_rows),
            "error_line_count": sum(row.get("status") != "ok" for row in raw_rows),
            "unique_successful_request_key_count": len(successful_by_key),
        },
        "token_usage": token_usage,
        "operational_gate": operational_gate,
        "minimum_practical_effect": threshold,
        "multiple_testing_family": list(primary),
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
