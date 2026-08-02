"""Freeze the resource-efficient Qwen-Plus 100/160-record design."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from sob_metamorphic import load_jsonl


ROOT = Path(__file__).resolve().parents[1]
SOURCE_MANIFEST = ROOT / "protocol/sob_decomposed_sonnet5_manifest.json"
PUBLIC_INPUT = ROOT / "data/processed/sob_decomposed_200_public.jsonl"
QWEN37_PILOT_MANIFEST = (
    ROOT / "protocol/sob_official_qwen3_7_plus_interim40_manifest.json"
)
QWEN37_PILOT_REPORT = (
    ROOT / "results/api/sob_official_qwen3_7_plus_interim40_report.json"
)
QWEN37_PILOT_PREDICTIONS = (
    ROOT / "results/api/sob_official_qwen3_7_plus_2026_05_26.jsonl"
)
MODEL_ID = "qwen-plus"
BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
STUDY_NAME = "sob_qwen_plus_resource_staged_validation_20260801_v1"
INTERIM_RECORDS_PER_STRATUM = 50


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stable_rank(record_id: str) -> str:
    return hashlib.sha256(f"{STUDY_NAME}|{record_id}".encode()).hexdigest()


def ids_digest(record_ids: list[str]) -> str:
    return hashlib.sha256("\n".join(record_ids).encode("utf-8")).hexdigest()


def write_frozen_json(path: Path, value: dict[str, Any]) -> None:
    rendered = json.dumps(value, ensure_ascii=False, indent=2) + "\n"
    if path.exists() and path.read_text(encoding="utf-8") != rendered:
        raise RuntimeError(f"Refusing to overwrite differing frozen file: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(rendered, encoding="utf-8")


def main() -> int:
    source = json.loads(SOURCE_MANIFEST.read_text(encoding="utf-8"))
    pilot_manifest = json.loads(QWEN37_PILOT_MANIFEST.read_text(encoding="utf-8"))
    pilot_report = json.loads(QWEN37_PILOT_REPORT.read_text(encoding="utf-8"))
    if pilot_report.get("decision") != "CONTINUE_TO_FULL_200":
        raise ValueError("The completed Qwen3.7 pilot did not pass its frozen GO rule")
    if int(pilot_report.get("successful_response_count", 0)) != 600:
        raise ValueError("The Qwen3.7 exploratory pilot is not complete")

    rows = {str(row["record_id"]): row for row in load_jsonl(PUBLIC_INPUT)}
    source_ids = [str(value) for value in source["record_ids"]]
    pilot_ids = {str(value) for value in pilot_manifest["record_ids"]}
    if len(source_ids) != 200 or set(source_ids) != set(rows):
        raise ValueError("Expected the frozen decomposed 200-record source sample")
    if len(pilot_ids) != 40 or not pilot_ids.issubset(source_ids):
        raise ValueError("Expected the completed 40-record Qwen3.7 pilot subset")

    remaining_ids = [record_id for record_id in source_ids if record_id not in pilot_ids]
    strata: dict[str, list[str]] = {"medium": [], "hard": []}
    for record_id in remaining_ids:
        stratum = str(rows[record_id]["schema_complexity"])
        if stratum not in strata:
            raise ValueError(f"Unexpected schema complexity: {stratum}")
        strata[stratum].append(record_id)
    if {name: len(values) for name, values in strata.items()} != {
        "medium": 80,
        "hard": 80,
    }:
        raise ValueError("Pilot-excluded sample is not balanced 80 medium / 80 hard")

    interim_ids = sorted(
        [
            record_id
            for values in strata.values()
            for record_id in sorted(values, key=stable_rank)[
                :INTERIM_RECORDS_PER_STRATUM
            ]
        ],
        key=stable_rank,
    )
    full_ids = sorted(remaining_ids, key=stable_rank)
    if len(interim_ids) != 100 or len(full_ids) != 160:
        raise ValueError("Qwen-Plus staged sample sizes are incorrect")

    interim_design = {
        "design": "single_futility_interim_no_early_success",
        "display_name": "Qwen-Plus 100-Record Futility Interim",
        "maximum_record_count": 160,
        "interim_record_count": 100,
        "interim_strata": {"medium": 50, "hard": 50},
        "maximum_strata": {"medium": 80, "hard": 80},
        "practical_effect_threshold": 0.05,
        "per_contrast_continuation_probability": 0.10,
        "continue_decision": "CONTINUE_TO_FULL_160",
        "stop_decision": "STOP_FOR_FUTILITY",
        "probability_method": (
            "Plug-in normal prediction for the final record mean, conditional on "
            "the interim mean and sample standard deviation: future records are "
            "assumed iid with the interim moments."
        ),
        "futility_rule": (
            "Stop after 100 records only when both primary contrasts have "
            "conditional probability < 0.10 of reaching a final 160-record point "
            "estimate >= 0.05. Otherwise continue to all 160 records."
        ),
        "reporting_rule": (
            "No efficacy claim or formal confirmation is allowed at interim. The "
            "interim result is retained whether the run stops or continues."
        ),
    }
    common = {
        "frozen_before_api_calls": True,
        "frozen_date": "2026-08-01",
        "study_name": STUDY_NAME,
        "source_manifest": str(SOURCE_MANIFEST.relative_to(ROOT)).replace("\\", "/"),
        "source_manifest_sha256": sha256_file(SOURCE_MANIFEST),
        "source_public_input_sha256": sha256_file(PUBLIC_INPUT),
        "excluded_qwen3_7_pilot_manifest": str(
            QWEN37_PILOT_MANIFEST.relative_to(ROOT)
        ).replace("\\", "/"),
        "excluded_qwen3_7_record_ids_sha256": ids_digest(sorted(pilot_ids)),
        "qwen3_7_pilot_report_sha256": sha256_file(QWEN37_PILOT_REPORT),
        "qwen3_7_pilot_predictions_sha256": sha256_file(QWEN37_PILOT_PREDICTIONS),
        "schema_variants": source["schema_variants"],
        "conditions": source["conditions"],
        "repeats_per_variant": source["repeats_per_variant"],
        "model_alias": MODEL_ID,
        "provider_label": "alibaba_bailian_qwen_plus_resource_official",
        "base_url": BASE_URL,
        "api_key_env": "DASHSCOPE_API_KEY",
        "requires_smoke_record": True,
        "smoke_provider": "qwen_plus",
        "sampling_parameters": "omitted",
        "request_body_extra": {"enable_thinking": False},
        "max_tokens": 4096,
        "primary_contrasts": source["primary_contrasts"],
        "minimum_practical_effect": 0.05,
        "independent_unit": "record",
        "request_order": source["request_order"],
        "interim_design": interim_design,
        "record_level_separation_note": (
            "All 40 records inspected in the fixed-snapshot Qwen3.7 pilot are "
            "excluded from this Qwen-Plus validation."
        ),
    }
    interim_manifest = {
        **common,
        "pilot_name": f"{STUDY_NAME}_interim100",
        "analysis_stage": "prospective_qwen_plus_resource_futility_interim_100",
        "bootstrap_seed_namespace": "qwen-plus-resource-futility-interim",
        "record_ids": interim_ids,
        "record_ids_sha256": ids_digest(interim_ids),
        "expected_requests": len(interim_ids) * len(source["conditions"]),
    }
    full_manifest = {
        **common,
        "pilot_name": f"{STUDY_NAME}_full160",
        "analysis_stage": "prospective_qwen_plus_resource_confirmation_full_160",
        "record_ids": full_ids,
        "record_ids_sha256": ids_digest(full_ids),
        "expected_requests": len(full_ids) * len(source["conditions"]),
        "final_confirmation_rule": source["confirmation_rule"],
        "resamples": source["resamples"],
    }

    interim_path = ROOT / "protocol/sob_official_qwen_plus_resource_interim100_manifest.json"
    full_path = ROOT / "protocol/sob_official_qwen_plus_resource_full160_manifest.json"
    write_frozen_json(interim_path, interim_manifest)
    write_frozen_json(full_path, full_manifest)
    freeze = {
        "status": "FROZEN_BEFORE_QWEN_PLUS_API_CALLS",
        "frozen_date": "2026-08-01",
        "study_name": STUDY_NAME,
        "requested_model_alias": MODEL_ID,
        "base_url": BASE_URL,
        "thinking_mode": "explicitly_disabled",
        "resource_plan_scope": (
            "Requested alias qwen-plus, real-time chat completions, non-thinking; "
            "billing eligibility remains an Alibaba Cloud account property."
        ),
        "prior_exploratory_qwen3_7_result": {
            "record_count": 40,
            "successful_responses": 600,
            "decision": pilot_report["decision"],
            "property_order_interim_mean": pilot_report["contrasts"]["property_order"]["interim_mean_excess"],
            "additional_keyword_order_interim_mean": pilot_report["contrasts"]["additional_keyword_order_given_reversed_properties"]["interim_mean_excess"],
            "report_sha256": sha256_file(QWEN37_PILOT_REPORT),
            "predictions_sha256": sha256_file(QWEN37_PILOT_PREDICTIONS),
            "role": "reported exploratory fixed-snapshot example; not pooled with Qwen-Plus inference",
        },
        "interim_manifest": str(interim_path.relative_to(ROOT)).replace("\\", "/"),
        "interim_manifest_sha256": sha256_file(interim_path),
        "full_manifest": str(full_path.relative_to(ROOT)).replace("\\", "/"),
        "full_manifest_sha256": sha256_file(full_path),
        "interim_design": interim_design,
    }
    write_frozen_json(
        ROOT / "protocol/sob_official_qwen_plus_resource_freeze.json", freeze
    )
    print(json.dumps(freeze, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
