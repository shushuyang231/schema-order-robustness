"""Freeze the completed 100x5x5 SOB experiments with provenance hashes.

The frozen bundle intentionally excludes restricted gold contents.  Their source
path, size, and SHA256 are recorded so the local analysis remains auditable
without duplicating restricted material into the result bundle.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


COPY_PATHS = (
    Path("data/processed/sob_mve_100_public.jsonl"),
    Path("protocol/13_confirmatory_repeated_mve.md"),
    Path("protocol/14_gpt55_cross_model_replication.md"),
    Path("protocol/sonnet5_confirmatory_manifest.json"),
    Path("protocol/gpt55_cross_model_manifest.json"),
    Path("results/api/sob_sonnet5_confirmatory.jsonl"),
    Path("results/api/sob_sonnet5_confirmatory_report.json"),
    Path("results/api/sob_sonnet5_confirmatory_report.md"),
    Path("results/api/sob_gpt55_cross_model.jsonl"),
    Path("results/api/sob_gpt55_cross_model_report.json"),
    Path("results/api/sob_gpt55_cross_model_report.md"),
    Path("src/evaluate_sob_repeated_pilot.py"),
    Path("src/run_sob_metamorphic.py"),
    Path("src/sob_metamorphic.py"),
)

HASH_ONLY_PATHS = (Path("data/restricted/sob_mve_100_gold.jsonl"),)

EXPERIMENTS = (
    {
        "name": "sonnet5_confirmatory",
        "manifest": Path("protocol/sonnet5_confirmatory_manifest.json"),
        "predictions": Path("results/api/sob_sonnet5_confirmatory.jsonl"),
        "report": Path("results/api/sob_sonnet5_confirmatory_report.json"),
    },
    {
        "name": "gpt55_cross_model",
        "manifest": Path("protocol/gpt55_cross_model_manifest.json"),
        "predictions": Path("results/api/sob_gpt55_cross_model.jsonl"),
        "report": Path("results/api/sob_gpt55_cross_model_report.json"),
    },
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("results/frozen/sob_100x5x5_20260718"),
    )
    return parser.parse_args()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def validate_experiment(spec: dict[str, Any]) -> dict[str, Any]:
    manifest = json.loads(spec["manifest"].read_text(encoding="utf-8"))
    report = json.loads(spec["report"].read_text(encoding="utf-8"))
    rows = load_jsonl(spec["predictions"])
    successes = [row for row in rows if row.get("status") == "ok"]
    errors = [row for row in rows if row.get("status") != "ok"]
    latest_successes = {str(row["request_key"]): row for row in successes}
    response_ids = [
        str(row["response_id"])
        for row in latest_successes.values()
        if row.get("response_id")
    ]
    expected = int(manifest["expected_requests"])
    checks = {
        "expected_request_count": expected,
        "raw_log_line_count": len(rows),
        "successful_log_line_count": len(successes),
        "error_log_line_count": len(errors),
        "unique_successful_request_key_count": len(latest_successes),
        "provided_successful_response_id_count": len(response_ids),
        "unique_successful_response_id_count": len(set(response_ids)),
        "error_types": dict(
            sorted(
                Counter(
                    str(row.get("error", "unknown")).split(":", 1)[0]
                    for row in errors
                ).items()
            )
        ),
        "report_prediction_count": int(report["prediction_count"]),
        "report_decision": report["decision"],
        "report_operational_gate_passed": bool(report["operational_gate_passed"]),
        "returned_model_counts": report["returned_model_counts"],
    }
    checks["coverage_passed"] = (
        len(latest_successes) == expected == int(report["prediction_count"])
    )
    checks["response_id_uniqueness_passed"] = (
        not response_ids or len(response_ids) == len(set(response_ids))
    )
    checks["all_validation_checks_passed"] = (
        checks["coverage_passed"]
        and checks["response_id_uniqueness_passed"]
        and checks["report_operational_gate_passed"]
    )
    if not checks["all_validation_checks_passed"]:
        raise ValueError(f"Freeze validation failed for {spec['name']}: {checks}")
    return checks


def file_entry(path: Path, *, copied_to: Path | None) -> dict[str, Any]:
    item = {
        "source_path": path.as_posix(),
        "size_bytes": path.stat().st_size,
        "sha256": sha256_file(path),
        "copied": copied_to is not None,
    }
    if copied_to is not None:
        item["frozen_path"] = copied_to.as_posix()
    return item


def verify_existing_freeze(output_root: Path, manifest_path: Path) -> dict[str, Any]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for item in manifest["files"]:
        source = Path(item["source_path"])
        if not source.is_file():
            raise FileNotFoundError(f"Previously frozen source is missing: {source}")
        if source.stat().st_size != int(item["size_bytes"]):
            raise ValueError(f"Previously frozen source size changed: {source}")
        if sha256_file(source) != item["sha256"]:
            raise ValueError(f"Previously frozen source hash changed: {source}")
        frozen_path = item.get("frozen_path")
        if frozen_path:
            frozen = output_root / frozen_path
            if not frozen.is_file() or sha256_file(frozen) != item["sha256"]:
                raise ValueError(f"Frozen snapshot is missing or changed: {frozen}")
    return manifest


def main() -> int:
    args = parse_args()
    missing = [path.as_posix() for path in COPY_PATHS + HASH_ONLY_PATHS if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Freeze inputs missing: {missing}")

    manifest_path = args.output_root / "freeze_manifest.json"
    if manifest_path.is_file():
        existing = verify_existing_freeze(args.output_root, manifest_path)
        print(
            json.dumps(
                {
                    "freeze_manifest": manifest_path.as_posix(),
                    "status": "ALREADY_FROZEN_AND_VERIFIED",
                    "generated_at": existing["generated_at"],
                    "validations": existing["validations"],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    validations = {
        str(spec["name"]): validate_experiment(spec) for spec in EXPERIMENTS
    }
    sonnet_manifest = json.loads(
        Path("protocol/sonnet5_confirmatory_manifest.json").read_text(encoding="utf-8")
    )
    gpt_manifest = json.loads(
        Path("protocol/gpt55_cross_model_manifest.json").read_text(encoding="utf-8")
    )
    if sonnet_manifest["record_ids"] != gpt_manifest["record_ids"]:
        raise ValueError("Model manifests do not contain the same ordered record IDs")
    if sonnet_manifest["conditions"] != gpt_manifest["conditions"]:
        raise ValueError("Model manifests do not contain the same conditions")

    files: list[dict[str, Any]] = []
    for source in COPY_PATHS:
        destination = args.output_root / "snapshot" / source
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        files.append(file_entry(source, copied_to=destination.relative_to(args.output_root)))
    for source in HASH_ONLY_PATHS:
        files.append(file_entry(source, copied_to=None))

    manifest = {
        "freeze_name": args.output_root.name,
        "generated_at": datetime.now(UTC).isoformat(),
        "purpose": "Immutable local snapshot of the completed two-model SOB 100x5x5 experiments.",
        "claim_boundary": (
            "The gateway aliases and returned model strings are recorded verbatim; "
            "upstream weights and provider identity are not independently verified."
        ),
        "restricted_material_policy": (
            "Restricted gold is not copied. Only its local source path, size, and SHA256 are recorded."
        ),
        "paired_design_validated": True,
        "record_count": len(sonnet_manifest["record_ids"]),
        "condition_count": len(sonnet_manifest["conditions"]),
        "validations": validations,
        "files": files,
    }
    args.output_root.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "freeze_manifest": manifest_path.as_posix(),
                "copied_file_count": len(COPY_PATHS),
                "hash_only_file_count": len(HASH_ONLY_PATHS),
                "validations": validations,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
