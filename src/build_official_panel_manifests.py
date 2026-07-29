"""Build the amended DeepSeek-only official-endpoint replication manifest."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "protocol/sob_decomposed_sonnet5_manifest.json"
OUTPUT_DIR = ROOT / "protocol"
STUDY_NAME = "sob_official_deepseek_200x3x5_v1"

TARGETS = (
    {
        "slug": "deepseek_v4_flash",
        "provider_label": "deepseek_official",
        "base_url": "https://api.deepseek.com",
        "model_alias": "deepseek-v4-flash",
        "api_key_env": "DEEPSEEK_API_KEY",
        "smoke_provider": "deepseek",
    },
)

SUPERSEDED_CANDIDATES = (
    {
        "path": "protocol/sob_official_kimi_k3_manifest.json",
        "model_alias": "kimi-k3",
        "reason": "Superseded before calls; unavailable candidate not replaced by Kimi K2.x.",
    },
    {
        "path": "protocol/sob_official_grok_4_3_manifest.json",
        "model_alias": "grok-4.3",
        "reason": "Superseded before calls when active scope narrowed to DeepSeek only.",
    },
    {
        "path": "protocol/sob_official_gemini_3_6_flash_manifest.json",
        "model_alias": "gemini-3.6-flash",
        "reason": "Superseded before calls when active scope narrowed to DeepSeek only.",
    },
)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    source: dict[str, Any] = json.loads(SOURCE.read_text(encoding="utf-8"))
    keep = {
        "record_ids": source["record_ids"],
        "record_ids_sha256": source["record_ids_sha256"],
        "schema_variants": source["schema_variants"],
        "conditions": source["conditions"],
        "repeats_per_variant": source["repeats_per_variant"],
        "expected_requests": source["expected_requests"],
        "max_tokens": source["max_tokens"],
        "primary_contrasts": source["primary_contrasts"],
        "minimum_practical_effect": source["minimum_practical_effect"],
        "confirmation_rule": source["confirmation_rule"],
        "independent_unit": source["independent_unit"],
        "resamples": source["resamples"],
        "request_order": source["request_order"],
    }

    summary: dict[str, Any] = {
        "status": "AMENDED_DEEPSEEK_ONLY_PENDING_OFFICIAL_ENDPOINT_GATE",
        "frozen_date": "2026-07-24",
        "amended_before_any_official_provider_calls": True,
        "amended_at": "2026-07-24T13:12:52+08:00",
        "protocol": "protocol/25_official_endpoint_model_panel.md",
        "source_manifest": str(SOURCE.relative_to(ROOT)).replace("\\", "/"),
        "source_manifest_sha256": sha256_file(SOURCE),
        "manifests": [],
        "superseded_candidate_manifests": [],
    }
    for target in TARGETS:
        manifest = {
            "pilot_name": STUDY_NAME,
            "analysis_stage": "preregistered_official_deepseek_replication",
            "frozen_before_api_calls": True,
            "frozen_date": "2026-07-24",
            "amended_at": "2026-07-24T13:12:52+08:00",
            **keep,
            "model_alias": target["model_alias"],
            "provider_label": target["provider_label"],
            "base_url": target["base_url"],
            "api_key_env": target["api_key_env"],
            "smoke_provider": target["smoke_provider"],
            "endpoint_provenance": "official_provider_documented_endpoint",
            "endpoint_gate": (
                "authenticated_catalog_contains_requested_model_and_exactly_"
                "three_smoke_completions_succeed_with_one_stable_returned_model"
            ),
            "requires_smoke_record": True,
            "sampling_parameters": "omitted_provider_defaults",
            "thinking_mode": (
                "omitted_provider_default_enabled_regular_request_effort_high"
            ),
            "scored_response_field": "choices[0].message.content",
            "reasoning_content_retention": "length_and_sha256_only",
            "response_format": "omitted_text_mode",
            "tools": "omitted",
            "operational_pause_rule": (
                "Stop on non-retryable 4xx or returned-model mismatch; pause "
                "after five consecutive request errors and resume identical keys."
            ),
            "multiple_testing": (
                "Holm across the two DeepSeek primary contrasts; this is the "
                "complete amended new-provider primary family."
            ),
        }
        output = OUTPUT_DIR / f"sob_official_{target['slug']}_manifest.json"
        output.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        summary["manifests"].append(
            {
                "path": str(output.relative_to(ROOT)).replace("\\", "/"),
                "provider_label": target["provider_label"],
                "model_alias": target["model_alias"],
                "base_url": target["base_url"],
                "sha256": sha256_file(output),
            }
        )

    for candidate in SUPERSEDED_CANDIDATES:
        candidate_path = ROOT / candidate["path"]
        summary["superseded_candidate_manifests"].append(
            {
                **candidate,
                "sha256": sha256_file(candidate_path),
            }
        )

    summary_path = OUTPUT_DIR / "sob_official_panel_freeze.json"
    summary_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
