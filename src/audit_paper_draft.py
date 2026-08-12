"""Audit manuscript references, artifacts, and frozen headline numbers."""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path
from typing import Any

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "paper"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=PAPER / "draft_audit.json")
    args = parser.parse_args()

    manuscript_path = PAPER / "manuscript.md"
    bib_path = PAPER / "references.bib"
    manuscript = manuscript_path.read_text(encoding="utf-8")
    bib = bib_path.read_text(encoding="utf-8")
    sonnet = load_json(ROOT / "results/api/sob_sonnet5_confirmatory_report.json")
    gpt = load_json(ROOT / "results/api/sob_gpt55_cross_model_report.json")
    qwen = load_json(ROOT / "results/api/sob_official_qwen_plus_resource_full160_report.json")
    endpoint_chat = load_json(ROOT / "results/api/sob_sjtu_deepseek_chat_report.json")
    endpoint_reasoner = load_json(ROOT / "results/api/sob_sjtu_deepseek_reasoner_report.json")
    endpoint_tokenrhythm = load_json(
        ROOT / "results/api/sob_tokenrhythm_deepseek_v4_flash_report.json"
    )
    endpoint_summary = load_json(ROOT / "results/api/sob_endpoint_panel_summary.json")
    endpoint_audit = load_json(
        ROOT / "results/api/sob_endpoint_panel_completion_audit.json"
    )
    interaction = load_json(
        ROOT / "results/api/sob_official_qwen_plus_mode_interaction_100_report.json"
    )
    retry_audit = load_json(ROOT / "results/api/sob_core_retry_audit.json")
    qualitative_cases = load_json(
        ROOT / "results/analysis/sob_qwen_high_effect_cases.json"
    )
    dialect = load_json(PAPER / "robustness/dialect_validation_audit.json")

    cited = set(
        re.findall(r"(?<![A-Za-z0-9._%+-])@([A-Za-z0-9_:-]+)", manuscript)
    )
    defined = set(re.findall(r"@[A-Za-z]+\{([^,\s]+)", bib))
    missing_bib = sorted(cited - defined)
    unused_bib = sorted(defined - cited)

    image_refs = re.findall(r"!\[[^\]]*\]\(([^)]+)\)", manuscript)
    image_audit: list[dict[str, Any]] = []
    missing_images: list[str] = []
    for ref in image_refs:
        path = PAPER / ref
        if not path.exists():
            missing_images.append(ref)
            continue
        with Image.open(path) as image:
            image_audit.append(
                {"path": ref, "width": image.width, "height": image.height, "mode": image.mode}
            )

    expected_snippets = [
        f"{sonnet['comparisons_vs_original']['properties_reversed']['normalized_excess_disagreement']:.3f}",
        f"{sonnet['comparisons_vs_original']['keywords_reversed']['normalized_excess_disagreement']:.3f}",
        f"{gpt['comparisons_vs_original']['properties_reversed']['normalized_excess_disagreement']:.4f}",
        f"{gpt['comparisons_vs_original']['keywords_reversed']['normalized_excess_disagreement']:.4f}",
        "17,900 successful responses",
        "100 record",
        "not independently verified",
        f"{qwen['contrasts']['property_order']['normalized_excess_disagreement']:.4f}",
        f"{qwen['contrasts']['additional_keyword_order_given_reversed_properties']['normalized_excess_disagreement']:.4f}",
        f"{interaction['contrasts']['property_order']['mode_change']:+.4f}",
        "9,000 successful responses",
        f"{endpoint_chat['contrasts']['property_order']['normalized_excess_disagreement']:.4f}",
        f"{endpoint_reasoner['contrasts']['property_order']['normalized_excess_disagreement']:.4f}",
        f"{endpoint_tokenrhythm['contrasts']['property_order']['normalized_excess_disagreement']:.4f}",
        "post-submission endpoint panel",
        "panel-wide Holm",
        "not evidence of equivalence",
        "200/200 audit pass",
        f"{retry_audit['totals']['top_level_error_rows']} standalone top-level error rows",
        f"{retry_audit['totals']['successful_rows_with_internal_retry']} successful rows",
        "a 0.03 magnitude screen",
        "The frozen 0.05 screen",
        "At 0.08",
        "sthfornothing@sjtu.edu.cn",
    ]
    missing_snippets = [value for value in expected_snippets if value not in manuscript]

    effects = csv_rows(PAPER / "tables/table2_distribution_effects.csv")
    quality = csv_rows(PAPER / "tables/table3_quality_metrics.csv")
    decomposed = csv_rows(PAPER / "tables/table5_decomposed_confirmation.csv")
    mode_interaction = csv_rows(PAPER / "tables/table7_qwen_mode_interaction.csv")
    concentration = csv_rows(PAPER / "tables/table8_effect_concentration.csv")
    table_checks = {
        "distribution_effect_rows": len(effects) == 8,
        "quality_metric_rows": len(quality) == 10,
        "decomposed_rows": len(decomposed) == 14,
        "qwen_mode_rows": len(mode_interaction) == 2,
        "concentration_rows": len(concentration) == 10,
        "qualitative_case_count": len(qualitative_cases["cases"]) == 3,
        "practical_threshold_yes_count": sum(
            row["meets_0_05_practical_threshold"] == "yes" for row in effects
        )
        == 2,
        "endpoint_panel_complete": endpoint_audit.get("status") == "PASS"
        and endpoint_audit.get("totals", {}).get("expected_successful_requests") == 9000
        and endpoint_audit.get("totals", {}).get("unique_successful_request_keys") == 9000,
        "endpoint_panel_summary_complete": endpoint_summary.get("analysis_status")
        == "SUPPLEMENTAL_POST_SUBMISSION_EVIDENCE"
        and sum(
            deployment.get("successful_response_count", 0)
            for deployment in endpoint_summary.get("deployments", {}).values()
        )
        == 9000,
    }

    required_sections = (
        "## Abstract",
        "## 1. Introduction",
        "## 2. Background and Related Work",
        "## 3. Study Design",
        "## 4. Results",
        "## 5. Engineering Method and Practical Use",
        "## 6. Discussion",
        "## 7. Threats to Validity",
        "## 8. Reproducibility and Artifact Scope",
        "## 9. Ethics and Broader Impact",
        "## 10. Conclusion",
        "## Statements and Declarations",
    )
    missing_sections = [section for section in required_sections if section not in manuscript]
    dialect_ok = (
        dialect["schema_dialect_disagreement_count"] == 0
        and dialect["total_prediction_dialect_disagreement_count"] == 0
        and dialect["paper_metric_impact"] == "none"
    )
    word_count = len(re.findall(r"\b[\w'-]+\b", manuscript))

    failures: list[str] = []
    if missing_bib:
        failures.append("missing bibliography entries")
    if missing_images:
        failures.append("missing manuscript images")
    if missing_snippets:
        failures.append("missing frozen headline statements")
    if missing_sections:
        failures.append("missing manuscript sections")
    if not all(table_checks.values()):
        failures.append("paper table shape mismatch")
    if not dialect_ok:
        failures.append("validator dialect audit not clean")

    report = {
        "status": "PASS" if not failures else "FAIL",
        "word_count": word_count,
        "citation_key_count": len(cited),
        "missing_bibliography_keys": missing_bib,
        "unused_bibliography_keys": unused_bib,
        "image_audit": image_audit,
        "missing_images": missing_images,
        "missing_expected_snippets": missing_snippets,
        "missing_required_sections": missing_sections,
        "table_checks": table_checks,
        "dialect_robustness_passed": dialect_ok,
        "failures": failures,
    }
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
