"""Create a frozen endpoint manifest from the fixed 200-record baseline.

This is a local, non-networking utility. It changes only endpoint metadata;
record IDs, conditions, request order, and the statistical contract remain
identical to the baseline manifest.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


def safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("._") or "endpoint"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--model-alias", required=True)
    parser.add_argument("--provider-label", required=True)
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--api-key-env", required=True)
    parser.add_argument("--smoke-provider", required=True)
    parser.add_argument("--protocol", required=True)
    parser.add_argument("--endpoint-provenance", required=True)
    parser.add_argument("--request-interval-seconds", type=float, default=0.0)
    parser.add_argument("--request-body-extra", default="{}")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest: dict[str, Any] = json.loads(
        args.base_manifest.read_text(encoding="utf-8")
    )
    request_body_extra = json.loads(args.request_body_extra)
    if not isinstance(request_body_extra, dict):
        raise ValueError("--request-body-extra must decode to a JSON object")
    manifest.update(
        {
            "pilot_name": f"sob_{safe_name(args.provider_label)}_{safe_name(args.model_alias)}_200x3x5_v1",
            "analysis_stage": "prospective_endpoint_panel",
            "frozen_before_api_calls": True,
            "model_alias": args.model_alias,
            "provider_label": args.provider_label,
            "base_url": args.base_url.rstrip("/"),
            "api_key_env": args.api_key_env,
            "smoke_provider": args.smoke_provider,
            "protocol": args.protocol,
            "endpoint_provenance": args.endpoint_provenance,
            "requires_smoke_record": True,
            "request_interval_seconds": float(args.request_interval_seconds),
            "request_body_extra": request_body_extra,
            "require_smoke_request_contract_match": True,
            "thinking_mode": "omitted_provider_default",
            "multiple_testing": (
                "Holm across the two model-local primary contrasts; no cross-model ranking."
            ),
        }
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote frozen manifest to {args.output}")
    print(
        json.dumps(
            {
                "provider_label": args.provider_label,
                "model_alias": args.model_alias,
                "base_url": args.base_url.rstrip("/"),
                "request_interval_seconds": args.request_interval_seconds,
                "expected_requests": manifest.get("expected_requests"),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
