"""Freeze the matched 100-record Qwen-Plus JSON Mode ablation."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SOURCE_MANIFEST = ROOT / "protocol/sob_official_qwen_plus_resource_interim100_manifest.json"
SOURCE_REPORT = ROOT / "results/api/sob_official_qwen_plus_resource_interim100_report.json"
PUBLIC_INPUT = ROOT / "data/processed/sob_decomposed_200_public.jsonl"
OUTPUT_MANIFEST = ROOT / "protocol/sob_official_qwen_plus_json_mode_100_manifest.json"
OUTPUT_FREEZE = ROOT / "protocol/sob_official_qwen_plus_json_mode_freeze.json"
STUDY_NAME = "sob_qwen_plus_json_mode_ablation_100_20260802_v1"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_frozen_json(path: Path, value: dict[str, Any]) -> None:
    rendered = json.dumps(value, ensure_ascii=False, indent=2) + "\n"
    if path.exists() and path.read_text(encoding="utf-8") != rendered:
        raise RuntimeError(f"Refusing to overwrite differing frozen file: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(rendered, encoding="utf-8")


def main() -> int:
    source = json.loads(SOURCE_MANIFEST.read_text(encoding="utf-8"))
    interim = json.loads(SOURCE_REPORT.read_text(encoding="utf-8"))
    if interim.get("decision") != "CONTINUE_TO_FULL_160":
        raise ValueError("The disclosed text-mode interim did not authorize continuation")
    if int(interim.get("successful_response_count", 0)) != 1500:
        raise ValueError("The disclosed text-mode 100-record arm is incomplete")
    if len(source.get("record_ids", [])) != 100:
        raise ValueError("Expected the already-frozen balanced 100-record sample")
    if len(source.get("conditions", [])) != 15:
        raise ValueError("Expected three representations with five repeats each")

    request_body_extra = {
        "enable_thinking": False,
        "response_format": {"type": "json_object"},
    }
    manifest = {
        "frozen_before_api_calls": True,
        "frozen_date": "2026-08-02",
        "pilot_name": STUDY_NAME,
        "analysis_stage": "prospective_qwen_plus_json_mode_ablation_100",
        "source_text_mode_manifest": str(SOURCE_MANIFEST.relative_to(ROOT)).replace("\\", "/"),
        "source_text_mode_manifest_sha256": sha256_file(SOURCE_MANIFEST),
        "source_text_mode_interim_report": str(SOURCE_REPORT.relative_to(ROOT)).replace("\\", "/"),
        "source_text_mode_interim_report_sha256": sha256_file(SOURCE_REPORT),
        "source_report_metadata_revision": (
            "Before any JSON Mode API call, the interim report was regenerated "
            "to add maximum_record_count=160 and correct prose that had said 200. "
            "The decision and all effect estimates were unchanged."
        ),
        "source_public_input_sha256": sha256_file(PUBLIC_INPUT),
        "selection_disclosure": (
            "This matched mode ablation was designed after inspecting the Qwen-Plus "
            "text-mode 100-record futility report. The record IDs themselves were "
            "frozen by SHA-256 ranking before any Qwen-Plus response."
        ),
        "record_ids": source["record_ids"],
        "record_ids_sha256": source["record_ids_sha256"],
        "schema_variants": source["schema_variants"],
        "conditions": source["conditions"],
        "repeats_per_variant": source["repeats_per_variant"],
        "expected_requests": source["expected_requests"],
        "model_alias": "qwen-plus",
        "provider_label": "alibaba_bailian_qwen_plus_json_mode_official",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "api_key_env": "DASHSCOPE_API_KEY",
        "requires_smoke_record": True,
        "require_smoke_request_contract_match": True,
        "smoke_provider": "qwen_plus",
        "sampling_parameters": "omitted",
        "request_body_extra": request_body_extra,
        "thinking_mode": "explicitly_disabled",
        "response_format": "json_object_syntax_mode_not_json_schema",
        "max_tokens": 4096,
        "primary_contrasts": source["primary_contrasts"],
        "minimum_practical_effect": 0.05,
        "mode_interaction_minimum_effect": 0.03,
        "mode_interaction_definition": (
            "record-level JSON-Mode excess disagreement minus the matched "
            "text-mode excess disagreement"
        ),
        "mode_interaction_inference": (
            "record bootstrap 95% CI and two-sided record-level sign-flip test; "
            "Holm correction across the two decomposed contrasts"
        ),
        "independent_unit": "record",
        "request_order": "ascending SHA256 of pilot_name|record_id|condition_name",
        "reporting_rule": (
            "Retain attenuation, persistence, amplification, and inconclusive "
            "outcomes. Do not add another model or replace records based on this result."
        ),
    }
    write_frozen_json(OUTPUT_MANIFEST, manifest)
    freeze = {
        "status": "FROZEN_BEFORE_JSON_MODE_API_CALLS",
        "frozen_date": "2026-08-02",
        "study_name": STUDY_NAME,
        "manifest": str(OUTPUT_MANIFEST.relative_to(ROOT)).replace("\\", "/"),
        "manifest_sha256": sha256_file(OUTPUT_MANIFEST),
        "new_request_count": manifest["expected_requests"],
        "text_mode_requests_reused": source["expected_requests"],
        "strict_schema_decoding_claim_allowed": False,
        "refreeze_note": manifest["source_report_metadata_revision"],
        "terminology": "Alibaba Qwen-Plus JSON Mode (`json_object`), not JSON Schema constrained decoding",
        "known_text_mode_interim_effects": {
            name: item["interim_mean_excess"]
            for name, item in interim["contrasts"].items()
        },
        "analysis_plan": {
            "within_json_mode": "Apply the existing two-contrast 0.05 confirmation rule.",
            "mode_interaction": manifest["mode_interaction_inference"],
            "material_mode_change_threshold": manifest["mode_interaction_minimum_effect"],
        },
    }
    write_frozen_json(OUTPUT_FREEZE, freeze)
    print(json.dumps(freeze, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
