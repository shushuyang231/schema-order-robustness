"""Freeze the prospective 40/200-record Qwen futility design."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from sob_metamorphic import load_jsonl


ROOT = Path(__file__).resolve().parents[1]
SOURCE_MANIFEST = ROOT / "protocol/sob_decomposed_sonnet5_manifest.json"
PUBLIC_INPUT = ROOT / "data/processed/sob_decomposed_200_public.jsonl"
MODEL_ID = "qwen3.7-plus-2026-05-26"
BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
STUDY_NAME = "sob_qwen3_7_plus_staged_futility_20260801_v1"
INTERIM_RECORDS_PER_STRATUM = 20


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stable_rank(record_id: str) -> str:
    return hashlib.sha256(f"{STUDY_NAME}|{record_id}".encode()).hexdigest()


def ids_digest(record_ids: list[str]) -> str:
    payload = "\n".join(record_ids).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def write_frozen_json(path: Path, value: dict[str, Any]) -> None:
    rendered = json.dumps(value, ensure_ascii=False, indent=2) + "\n"
    if path.exists() and path.read_text(encoding="utf-8") != rendered:
        raise RuntimeError(f"Refusing to overwrite differing frozen file: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(rendered, encoding="utf-8")


def main() -> int:
    source = json.loads(SOURCE_MANIFEST.read_text(encoding="utf-8"))
    rows = {str(row["record_id"]): row for row in load_jsonl(PUBLIC_INPUT)}
    full_ids = [str(value) for value in source["record_ids"]]
    if len(full_ids) != 200 or set(full_ids) != set(rows):
        raise ValueError("Expected the frozen decomposed 200-record source sample")

    strata: dict[str, list[str]] = {"medium": [], "hard": []}
    for record_id in full_ids:
        stratum = str(rows[record_id]["schema_complexity"])
        if stratum not in strata:
            raise ValueError(f"Unexpected schema complexity: {stratum}")
        strata[stratum].append(record_id)
    if {name: len(values) for name, values in strata.items()} != {
        "medium": 100,
        "hard": 100,
    }:
        raise ValueError("The source sample is not balanced 100 medium / 100 hard")

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
    if len(interim_ids) != 40 or len(set(interim_ids)) != 40:
        raise ValueError("Interim selection did not produce 40 unique records")

    interim_design = {
        "design": "single_nonbinding_futility_interim_no_early_success",
        "maximum_record_count": 200,
        "interim_record_count": 40,
        "interim_strata": {"medium": 20, "hard": 20},
        "practical_effect_threshold": 0.05,
        "per_contrast_continuation_probability": 0.10,
        "probability_method": (
            "Plug-in normal prediction for the final record mean, conditional on "
            "the interim mean and sample standard deviation: future records are "
            "assumed iid with the interim moments."
        ),
        "futility_rule": (
            "Stop after the 40-record interim only when each of the two primary "
            "contrasts has conditional probability < 0.10 of reaching a final "
            "200-record point estimate >= 0.05. Otherwise continue to all 200."
        ),
        "reporting_rule": (
            "No efficacy claim or formal confirmation is allowed at interim. "
            "The interim result must be retained whether the run stops or continues."
        ),
    }
    common = {
        "frozen_before_api_calls": True,
        "frozen_date": "2026-08-01",
        "study_name": STUDY_NAME,
        "source_manifest": str(SOURCE_MANIFEST.relative_to(ROOT)).replace("\\", "/"),
        "source_manifest_sha256": sha256_file(SOURCE_MANIFEST),
        "source_public_input_sha256": sha256_file(PUBLIC_INPUT),
        "schema_variants": source["schema_variants"],
        "conditions": source["conditions"],
        "repeats_per_variant": source["repeats_per_variant"],
        "model_alias": MODEL_ID,
        "provider_label": "alibaba_bailian_qwen_official",
        "base_url": BASE_URL,
        "api_key_env": "DASHSCOPE_API_KEY",
        "requires_smoke_record": True,
        "smoke_provider": "qwen",
        "sampling_parameters": "omitted",
        "request_body_extra": {"enable_thinking": False},
        "max_tokens": 4096,
        "primary_contrasts": source["primary_contrasts"],
        "minimum_practical_effect": 0.05,
        "independent_unit": "record",
        "request_order": source["request_order"],
        "interim_design": interim_design,
    }
    interim_manifest = {
        **common,
        "pilot_name": f"{STUDY_NAME}_interim40",
        "analysis_stage": "prospective_qwen_futility_interim_40",
        "record_ids": interim_ids,
        "record_ids_sha256": ids_digest(interim_ids),
        "expected_requests": len(interim_ids) * len(source["conditions"]),
    }
    full_manifest = {
        **common,
        "pilot_name": f"{STUDY_NAME}_full200",
        "analysis_stage": "prospective_qwen_staged_confirmation_full_200",
        "record_ids": full_ids,
        "record_ids_sha256": ids_digest(full_ids),
        "expected_requests": len(full_ids) * len(source["conditions"]),
        "final_confirmation_rule": source["confirmation_rule"],
        "resamples": source["resamples"],
    }

    interim_path = ROOT / "protocol/sob_official_qwen3_7_plus_interim40_manifest.json"
    full_path = ROOT / "protocol/sob_official_qwen3_7_plus_full200_manifest.json"
    write_frozen_json(interim_path, interim_manifest)
    write_frozen_json(full_path, full_manifest)
    freeze = {
        "status": "FROZEN_BEFORE_QWEN_API_CALLS",
        "frozen_date": "2026-08-01",
        "study_name": STUDY_NAME,
        "model_alias": MODEL_ID,
        "base_url": BASE_URL,
        "thinking_mode": "explicitly_disabled",
        "interim_manifest": str(interim_path.relative_to(ROOT)).replace("\\", "/"),
        "interim_manifest_sha256": sha256_file(interim_path),
        "full_manifest": str(full_path.relative_to(ROOT)).replace("\\", "/"),
        "full_manifest_sha256": sha256_file(full_path),
        "interim_design": interim_design,
        "calibration_note": (
            "The 40-record timing and 0.10 continuation probability were selected "
            "before Qwen calls using retrospective record-level calibration on "
            "the completed Sonnet, GPT, and DeepSeek runs."
        ),
    }
    write_frozen_json(ROOT / "protocol/sob_official_qwen_staged_freeze.json", freeze)
    print(json.dumps(freeze, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
