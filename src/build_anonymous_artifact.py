from __future__ import annotations

import hashlib
import json
import re
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "output" / "artifact"
ZIP_PATH = OUTPUT_DIR / "schema_order_tmlr_anonymous_artifact.zip"
MANIFEST_PATH = OUTPUT_DIR / "artifact_manifest.json"
ARCHIVE_ROOT = "schema-order-artifact"
ARTIFACT_NAME = "schema_order_tmlr_anonymous_artifact"

EXPLICIT_FILES = (
    "LICENSE",
    "LICENSES.md",
    "README.md",
    "ARTIFACT_README.md",
    "requirements-lock.txt",
    "requirements-mve.txt",
    "requirements-paper.txt",
    "requirements-structured-output.txt",
    "data/public/example_schema_tasks.jsonl",
    "paper/README.md",
    "paper/manuscript.md",
    "paper/references.bib",
    "paper/chart_contract.md",
    "paper/artifact_manifest.json",
    "paper/draft_audit.json",
    "paper/claim_evidence_audit.md",
    "paper/robustness/dialect_validation_audit.json",
    "paper/tmlr/main.tex",
    "paper/tmlr/references.bib",
    "paper/tmlr/tmlr.sty",
    "paper/tmlr/tmlr.bst",
    "paper/tmlr/fancyhdr.sty",
    "paper/tmlr/TEMPLATE_SOURCE.md",
    "paper/tmlr/submission_checklist.md",
    "paper/reviews/statistical_review.md",
    "paper/reviews/scope_review.md",
    "paper/reviews/revision_log.md",
    "protocol/12_repeated_measures_redesign.md",
    "protocol/13_confirmatory_repeated_mve.md",
    "protocol/14_gpt55_cross_model_replication.md",
    "protocol/15_cross_model_exploratory_analysis.md",
    "protocol/16_cross_model_result_decision.md",
    "protocol/17_related_work_novelty_audit.md",
    "protocol/18_paper_research_questions_and_outline.md",
    "protocol/19_reusable_tooling_gate.md",
    "protocol/20_paper_draft_gate.md",
    "protocol/21_tmlr_readiness_plan.md",
    "protocol/22_decomposed_contrast_confirmation.md",
    "protocol/23_decomposed_sonnet_result.md",
    "protocol/24_decomposed_gpt_result.md",
    "protocol/25_official_endpoint_model_panel.md",
    "protocol/26_official_deepseek_result.md",
    "protocol/related_work_matrix.csv",
    "protocol/sonnet5_confirmatory_manifest.json",
    "protocol/gpt55_cross_model_manifest.json",
    "protocol/sob_decomposed_sonnet5_manifest.json",
    "protocol/sob_decomposed_gpt55_manifest.json",
    "protocol/sob_official_deepseek_v4_flash_manifest.json",
    "protocol/sob_official_panel_freeze.json",
    "results/frozen/sob_100x5x5_20260718/freeze_manifest.json",
    "scripts/reproduce_paper_offline.ps1",
    "src/analyze_sob_contrast_decomposition.py",
    "src/analyze_sob_cross_model_exploratory.py",
    "src/analyze_sob_decomposed_cross_model.py",
    "src/audit_paper_draft.py",
    "src/audit_paper_evaluation_dialects.py",
    "src/audit_sob_pilot.py",
    "src/audit_sob_repeat_control.py",
    "src/audit_sob_repeated_pilot.py",
    "src/audit_sob_schema_variants.py",
    "src/build_anonymous_artifact.py",
    "src/build_official_panel_manifests.py",
    "src/build_paper_artifacts.py",
    "src/build_pdf_contact_sheets.py",
    "src/build_sob_confirmatory_manifest.py",
    "src/build_sob_cross_model_manifest.py",
    "src/build_tmlr_submission.py",
    "src/evaluate_sob_decomposed_confirmation.py",
    "src/evaluate_sob_metamorphic.py",
    "src/evaluate_sob_repeat_control.py",
    "src/evaluate_sob_repeated_pilot.py",
    "src/freeze_sob_results.py",
    "src/prepare_schema_metamorphic_tasks.py",
    "src/prepare_sob_decomposed_confirmation.py",
    "src/prepare_sob_pilot_holdout.py",
    "src/run_sob_metamorphic.py",
    "src/smoke_official_provider.py",
    "src/sob_metamorphic.py",
)

GLOBS = (
    "paper/figures/*.png",
    "paper/tables/*.csv",
    "tests/test_*.py",
    "results/analysis/sob_*",
    "results/validation/sob_*",
    "results/api/sob_sonnet5_confirmatory_report.*",
    "results/api/sob_gpt55_cross_model_report.*",
    "results/api/sob_decomposed_sonnet5_report.*",
    "results/api/sob_decomposed_gpt55_report.*",
    "results/api/sob_official_deepseek_v4_flash_report.*",
)

FORBIDDEN_PARTS = {
    ".env",
    ".venv",
    "restricted",
    "raw",
    "processed",
    "vendor",
    "__pycache__",
}
TEXT_SUFFIXES = {".md", ".txt", ".py", ".ps1", ".json", ".csv", ".tex", ".bib", ".sty", ".bst"}
SECRET_PATTERNS = (
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"(?i)\b(?:api[_-]?key|token|secret)\s*[:=]\s*['\"][A-Za-z0-9_\-]{16,}"),
    re.compile(r"\bsk-[A-Za-z0-9]{20,}\b"),
    re.compile(r"(?i)\b[A-Z]:\\Users\\[^\\\r\n]+\\"),
    re.compile(r"(?i)/(?:Users|home)/[^/\r\n]+/"),
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def collect_files() -> list[Path]:
    found: set[Path] = set()
    for relative in EXPLICIT_FILES:
        path = ROOT / relative
        if path.is_file():
            found.add(path)
    for pattern in GLOBS:
        found.update(path for path in ROOT.glob(pattern) if path.is_file())
    return sorted(found, key=lambda path: path.relative_to(ROOT).as_posix())


def validate_path(path: Path) -> None:
    relative = path.relative_to(ROOT)
    lowered_parts = {part.lower() for part in relative.parts}
    if lowered_parts & FORBIDDEN_PARTS:
        raise ValueError(f"Forbidden path selected: {relative}")
    if path.suffix.lower() == ".jsonl" and relative.as_posix() != "data/public/example_schema_tasks.jsonl":
        raise ValueError(f"Raw JSONL is not allowed: {relative}")


def scan_text(path: Path) -> None:
    if path.suffix.lower() not in TEXT_SUFFIXES:
        return
    text = path.read_text(encoding="utf-8", errors="strict")
    for pattern in SECRET_PATTERNS:
        if pattern.search(text):
            raise ValueError(f"Possible secret in {path.relative_to(ROOT)}: {pattern.pattern}")


def zip_info(name: str) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o644 << 16
    return info


def main() -> int:
    files = collect_files()
    if not files:
        raise RuntimeError("Artifact allowlist selected no files")
    for path in files:
        validate_path(path)
        scan_text(path)

    entries = [
        {
            "path": path.relative_to(ROOT).as_posix(),
            "bytes": path.stat().st_size,
            "sha256": sha256(path),
        }
        for path in files
    ]
    manifest = {
        "artifact": ARTIFACT_NAME,
        "offline_only": True,
        "contains_raw_provider_responses": False,
        "contains_restricted_gold": False,
        "contains_downloaded_benchmark_contexts": False,
        "file_count": len(entries),
        "files": entries,
    }
    manifest_bytes = (json.dumps(manifest, indent=2, ensure_ascii=False) + "\n").encode("utf-8")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    temporary = ZIP_PATH.with_suffix(".zip.tmp")
    with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        archive.writestr(zip_info(f"{ARCHIVE_ROOT}/ARTIFACT_MANIFEST.json"), manifest_bytes)
        for path in files:
            relative = path.relative_to(ROOT).as_posix()
            archive.writestr(zip_info(f"{ARCHIVE_ROOT}/{relative}"), path.read_bytes())
    temporary.replace(ZIP_PATH)
    MANIFEST_PATH.write_bytes(manifest_bytes)

    with zipfile.ZipFile(ZIP_PATH, "r") as archive:
        bad = archive.testzip()
        if bad is not None:
            raise RuntimeError(f"Corrupt ZIP entry: {bad}")
        names = archive.namelist()
        if any("/data/raw/" in name or "/data/restricted/" in name or name.endswith(".env") for name in names):
            raise RuntimeError("Forbidden material entered ZIP")

    print(
        json.dumps(
            {
                "status": "PASS",
                "zip": str(ZIP_PATH.relative_to(ROOT)),
                "zip_bytes": ZIP_PATH.stat().st_size,
                "zip_sha256": sha256(ZIP_PATH),
                "file_count": len(entries),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
