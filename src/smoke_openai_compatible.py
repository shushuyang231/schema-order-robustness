"""Authenticated catalog and three-call smoke gate for a custom OpenAI API.

The helper is intentionally provider-agnostic. It records only sanitized
catalog/completion metadata and never writes the API key or completion text.
It is suitable for institutional endpoints and documented aggregators whose
API follows the OpenAI-compatible ``/models`` and ``/chat/completions`` paths.
"""

from __future__ import annotations

import argparse
import getpass
import hashlib
import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--provider-label", required=True)
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--api-key-env", required=True)
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--catalog-only", action="store_true")
    parser.add_argument("--timeout", type=float, default=120.0)
    return parser.parse_args()


def safe_label(label: str) -> str:
    value = re.sub(r"[^A-Za-z0-9_.-]+", "_", label).strip("._")
    return value or "custom_provider"


def request_json(
    url: str,
    api_key: str,
    timeout: float,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "User-Agent": "schema-order-endpoint-audit/0.2",
    }
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        headers=headers,
        method="GET" if payload is None else "POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def visible_text(content: Any) -> str | None:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = [
            str(item["text"])
            for item in content
            if isinstance(item, dict) and isinstance(item.get("text"), str)
        ]
        return "".join(parts) if parts else None
    return None


def sanitize_completion(payload: dict[str, Any]) -> dict[str, Any]:
    choices = payload.get("choices") or []
    message = choices[0].get("message") or {} if choices else {}
    content = visible_text(message.get("content"))
    reasoning = visible_text(message.get("reasoning_content"))
    return {
        "id": payload.get("id"),
        "object": payload.get("object"),
        "created": payload.get("created"),
        "returned_model": payload.get("model"),
        "system_fingerprint": payload.get("system_fingerprint"),
        "usage": payload.get("usage"),
        "finish_reason": choices[0].get("finish_reason") if choices else None,
        "content_length": len(content) if content is not None else None,
        "content_sha256": (
            hashlib.sha256(content.encode("utf-8")).hexdigest()
            if content is not None
            else None
        ),
        "content_exact_api_ok": content.strip() == "API_OK" if content else False,
        "reasoning_content_length": len(reasoning) if reasoning is not None else None,
        "reasoning_content_sha256": (
            hashlib.sha256(reasoning.encode("utf-8")).hexdigest()
            if reasoning is not None
            else None
        ),
    }


def gate_status(record: dict[str, Any], required_repeats: int) -> dict[str, Any]:
    catalog = record.get("catalog") or {}
    runs = record.get("runs") or []
    ok_runs = [run for run in runs if run.get("status") == "ok"]
    returned = [run.get("response", {}).get("returned_model") for run in ok_runs]
    returned = [model for model in returned if model]
    stable = (
        returned[0]
        if len(runs) == required_repeats
        and len(ok_runs) == required_repeats
        and len(set(returned)) == 1
        else None
    )
    catalog_passed = (
        not catalog.get("error")
        and catalog.get("requested_model_present") is True
    )
    api_contract_passed = (
        len(ok_runs) == required_repeats
        and all(
            run.get("response", {}).get("content_exact_api_ok") is True
            for run in ok_runs
        )
    )
    runs_passed = stable is not None and api_contract_passed
    return {
        "required_repeats": required_repeats,
        "catalog_passed": catalog_passed,
        "successful_runs": len(ok_runs),
        "stable_returned_model": stable,
        "api_contract_passed": api_contract_passed,
        "runs_passed": runs_passed,
        "gate_passed": catalog_passed and runs_passed,
    }


def main() -> int:
    args = parse_args()
    if args.repeats != 3:
        print("This frozen availability gate requires exactly --repeats 3.", file=sys.stderr)
        return 2
    base_url = args.base_url.rstrip("/")
    api_key = os.environ.get(args.api_key_env)
    if not api_key and sys.stdin.isatty():
        api_key = getpass.getpass(
            f"Enter the {args.provider_label} API key (input is hidden): "
        ).strip()
    if not api_key:
        print(
            f"{args.api_key_env} is not set and no hidden API key was entered.",
            file=sys.stderr,
        )
        return 2

    timestamp = datetime.now(UTC)
    record: dict[str, Any] = {
        "timestamp_utc": timestamp.isoformat(),
        "provider": args.provider_label,
        "base_url": base_url,
        "api_key_source": args.api_key_env,
        "requested_model": args.model,
        "request_body_extra": {},
        "request_contract": {
            "max_tokens": 512,
            "stream": False,
            "sampling_parameters": "omitted",
            "response_format": "omitted",
            "tools": "omitted",
        },
        "catalog": None,
        "runs": [],
    }

    try:
        catalog = request_json(f"{base_url}/models", api_key, args.timeout)
        model_ids = [
            str(item.get("id"))
            for item in catalog.get("data", [])
            if isinstance(item, dict) and item.get("id")
        ]
        record["catalog"] = {
            "object": catalog.get("object"),
            "model_ids": model_ids,
            "requested_model_present": args.model in model_ids,
        }
        print(f"{args.provider_label} model IDs:")
        for model_id in model_ids:
            print(f"  {model_id}")
    except Exception as exc:
        record["catalog"] = {"error": f"{type(exc).__name__}: {exc}"}
        print(f"[WARN] model catalog unavailable: {type(exc).__name__}: {exc}", file=sys.stderr)

    catalog_passed = bool(
        isinstance(record["catalog"], dict)
        and record["catalog"].get("requested_model_present") is True
        and not record["catalog"].get("error")
    )
    if args.catalog_only:
        record["gate"] = gate_status(record, args.repeats)
    elif not catalog_passed:
        print(
            "[STOP] Requested model is not confirmed in the authenticated catalog; "
            "no completion smoke calls were sent.",
            file=sys.stderr,
        )
        record["gate"] = gate_status(record, args.repeats)
    else:
        for repeat_index in range(1, args.repeats + 1):
            payload = {
                "model": args.model,
                "messages": [
                    {"role": "system", "content": "Return exactly API_OK and nothing else."},
                    {"role": "user", "content": "Connectivity check."},
                ],
                "max_tokens": 512,
                "stream": False,
            }
            try:
                response = request_json(
                    f"{base_url}/chat/completions", api_key, args.timeout, payload
                )
                sanitized = sanitize_completion(response)
                record["runs"].append(
                    {"repeat_index": repeat_index, "status": "ok", "response": sanitized}
                )
                print(
                    f"[OK] {args.model} run {repeat_index}/{args.repeats}: "
                    f"returned model={sanitized['returned_model']}"
                )
            except urllib.error.HTTPError as exc:
                body = exc.read().decode("utf-8", errors="replace")
                body = body.replace(api_key, "[REDACTED]")[:2000]
                record["runs"].append(
                    {
                        "repeat_index": repeat_index,
                        "status": "http_error",
                        "http_status": exc.code,
                        "error_body": body,
                    }
                )
                print(f"[ERROR] {args.model} run {repeat_index}/{args.repeats}: HTTP {exc.code}", file=sys.stderr)
            except Exception as exc:
                record["runs"].append(
                    {
                        "repeat_index": repeat_index,
                        "status": "error",
                        "error": f"{type(exc).__name__}: {exc}",
                    }
                )
                print(
                    f"[ERROR] {args.model} run {repeat_index}/{args.repeats}: "
                    f"{type(exc).__name__}: {exc}",
                    file=sys.stderr,
                )
        record["gate"] = gate_status(record, args.repeats)

    output_dir = Path("data/raw/official_smoke")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{safe_label(args.provider_label)}_{timestamp.strftime('%Y%m%dT%H%M%SZ')}.json"
    output_path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved sanitized metadata to {output_path}")
    print(json.dumps(record["gate"], ensure_ascii=False, indent=2))
    return 0 if (record["gate"]["catalog_passed"] if args.catalog_only else record["gate"]["gate_passed"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
