"""Build the non-anonymous EMSE Online Resource 1 from an explicit allowlist."""

from __future__ import annotations

from pathlib import Path

import build_anonymous_artifact as builder


ROOT = Path(__file__).resolve().parents[1]

builder.ZIP_PATH = ROOT / "output/artifact/schema_order_emse_online_resource1.zip"
builder.MANIFEST_PATH = ROOT / "output/artifact/emse_artifact_manifest.json"
builder.ARCHIVE_ROOT = "schema-order-emse-online-resource1"
builder.ARTIFACT_NAME = "schema_order_emse_online_resource1"

builder.EXPLICIT_FILES = (
    "LICENSE",
    "LICENSES.md",
    "README.md",
    "ARTIFACT_README.md",
    "requirements-lock.txt",
    "requirements-paper.txt",
    "requirements-structured-output.txt",
    "data/public/example_schema_tasks.jsonl",
    "paper/README.md",
    "paper/manuscript.md",
    "paper/references.bib",
    "paper/artifact_manifest.json",
    "paper/draft_audit.json",
    "paper/robustness/dialect_validation_audit.json",
    "paper/reviews/emse_rewrite_plan.md",
    "paper/reviews/post_tmlr_venue_novelty_adversarial_audit.md",
    "protocol/13_confirmatory_repeated_mve.md",
    "protocol/14_gpt55_cross_model_replication.md",
    "protocol/15_cross_model_exploratory_analysis.md",
    "protocol/16_cross_model_result_decision.md",
    "protocol/22_decomposed_contrast_confirmation.md",
    "protocol/23_decomposed_sonnet_result.md",
    "protocol/24_decomposed_gpt_result.md",
    "protocol/25_official_endpoint_model_panel.md",
    "protocol/26_official_deepseek_result.md",
    "protocol/27_qwen_staged_futility.md",
    "protocol/28_qwen_plus_resource_staged_validation.md",
    "protocol/29_qwen_plus_json_mode_ablation.md",
    "protocol/30_qwen_plus_resource_result.md",
    "protocol/31_qwen_plus_json_mode_result.md",
    "protocol/34_availability_gate_audit_and_recovery_amendment.md",
    "protocol/35_endpoint_panel_completion_and_analysis_amendment.md",
    "protocol/sonnet5_confirmatory_manifest.json",
    "protocol/gpt55_cross_model_manifest.json",
    "protocol/sob_decomposed_sonnet5_manifest.json",
    "protocol/sob_decomposed_gpt55_manifest.json",
    "protocol/sob_official_deepseek_v4_flash_manifest.json",
    "protocol/sob_official_panel_freeze.json",
    "protocol/sob_official_kimi_k3_manifest.json",
    "protocol/sob_official_grok_4_3_manifest.json",
    "protocol/sob_official_gemini_3_6_flash_manifest.json",
    "protocol/sob_official_qwen3_7_plus_interim40_manifest.json",
    "protocol/sob_official_qwen3_7_plus_full200_manifest.json",
    "protocol/sob_official_qwen_plus_resource_full160_manifest.json",
    "protocol/sob_official_qwen_plus_json_mode_100_manifest.json",
    "protocol/sob_official_qwen_plus_resource_freeze.json",
    "protocol/sob_official_qwen_plus_json_mode_freeze.json",
    "scripts/reproduce_paper_offline.ps1",
    "scripts/run_sob_decomposed_robustness_audit.ps1",
    "scripts/evaluate_endpoint_panel_offline.ps1",
    "scripts/finish_sjtu_deepseek_runs.ps1",
    "src/analyze_sob_contrast_decomposition.py",
    "src/analyze_sob_cross_model_exploratory.py",
    "src/analyze_sob_decomposed_cross_model.py",
    "src/analyze_sob_decomposed_robustness.py",
    "src/audit_sob_core_run_retries.py",
    "src/audit_endpoint_panel_runs.py",
    "src/audit_paper_draft.py",
    "src/audit_paper_evaluation_dialects.py",
    "src/audit_schema_canonicalization.py",
    "src/audit_sob_schema_variants.py",
    "src/build_anonymous_artifact.py",
    "src/build_emse_artifact.py",
    "src/build_emse_review_pdf.py",
    "src/build_emse_submission.py",
    "src/build_paper_artifacts.py",
    "src/build_qwen_futility_protocol.py",
    "src/build_qwen_plus_json_mode_protocol.py",
    "src/build_qwen_plus_resource_protocol.py",
    "src/build_tmlr_submission.py",
    "src/canonicalize_json_schema.py",
    "src/evaluate_sob_decomposed_confirmation.py",
    "src/evaluate_sob_metamorphic.py",
    "src/evaluate_sob_qwen_interim.py",
    "src/evaluate_sob_qwen_mode_interaction.py",
    "src/evaluate_sob_repeated_pilot.py",
    "src/prepare_schema_metamorphic_tasks.py",
    "src/prepare_sob_decomposed_confirmation.py",
    "src/run_sob_metamorphic.py",
    "src/smoke_official_provider.py",
    "src/summarize_endpoint_panel.py",
    "src/sob_metamorphic.py",
)

builder.GLOBS = (
    "paper/figures/*.png",
    "paper/tables/*.csv",
    "tests/test_contrast_decomposition.py",
    "tests/test_cross_model_exploratory.py",
    "tests/test_decomposed_cross_model.py",
    "tests/test_decomposed_robustness.py",
    "tests/test_official_provider_panel.py",
    "tests/test_repeated_pilot_statistics.py",
    "tests/test_schema_canonicalization.py",
    "tests/test_schema_metamorphic_tasks.py",
    "tests/test_endpoint_panel_analysis.py",
    "results/analysis/sob_*",
    "results/validation/sob_*",
    "results/gate/sob_schema_canonicalization_audit.json",
    "results/gate/sob_schema_variant_audit.json",
    "results/api/sob_sonnet5_confirmatory_report.*",
    "results/api/sob_gpt55_cross_model_report.*",
    "results/api/sob_decomposed_sonnet5_report.*",
    "results/api/sob_decomposed_gpt55_report.*",
    "results/api/sob_official_deepseek_v4_flash_report.*",
    "results/api/sob_official_qwen_plus_resource_full160_report.*",
    "results/api/sob_official_qwen_plus_json_mode_100_report.*",
    "results/api/sob_official_qwen_plus_mode_interaction_100_report.*",
    "results/api/sob_decomposed_robustness_audit.*",
    "results/api/sob_core_retry_audit.*",
    "results/api/sob_endpoint_panel_completion_audit.*",
    "results/api/sob_endpoint_panel_summary.*",
    "results/api/sob_sjtu_deepseek_chat_report.*",
    "results/api/sob_sjtu_deepseek_reasoner_report.*",
    "results/api/sob_tokenrhythm_deepseek_v4_flash_report.*",
    "results/api/sob_official_qwen3_7_plus_interim40_report.json",
    "results/api/sob_official_qwen_plus_resource_interim100_report.json",
    "results/analysis/sob_qwen_high_effect_cases.json",
)


def main() -> int:
    return builder.main()


if __name__ == "__main__":
    raise SystemExit(main())
