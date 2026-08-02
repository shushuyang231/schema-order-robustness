"""List models and smoke-test supported official OpenAI-compatible APIs.

The API key is read from the provider-specific environment variable or entered
through a hidden terminal prompt. It is never written to disk.
"""

from __future__ import annotations

import argparse
import getpass
import hashlib
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


PROVIDERS: dict[str, dict[str, Any]] = {
    "kimi": {
        "base_url": "https://api.moonshot.cn/v1",
        "api_key_env": "MOONSHOT_API_KEY",
        "default_model": "kimi-k3",
    },
    "deepseek": {
        "base_url": "https://api.deepseek.com",
        "api_key_env": "DEEPSEEK_API_KEY",
        "default_model": "deepseek-v4-flash",
    },
    "qwen": {
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "api_key_env": "DASHSCOPE_API_KEY",
        "default_model": "qwen3.7-plus-2026-05-26",
        "request_body_extra": {"enable_thinking": False},
    },
    "qwen_plus": {
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "api_key_env": "DASHSCOPE_API_KEY",
        "default_model": "qwen-plus",
        "request_body_extra": {"enable_thinking": False},
    },
    "xai": {
        "base_url": "https://api.x.ai/v1",
        "api_key_env": "XAI_API_KEY",
        "default_model": "grok-4.3",
    },
    "gemini": {
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai",
        "api_key_env": "GEMINI_API_KEY",
        "default_model": "gemini-3.6-flash",
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--provider", choices=sorted(PROVIDERS), required=True)
    parser.add_argument(
        "--model",
        help="Exact model ID. Defaults to the preregistered provider candidate.",
    )
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--catalog-only", action="store_true")
    parser.add_argument(
        "--json-mode",
        action="store_true",
        help=(
            "Smoke-test response_format=json_object. This verifies JSON Mode "
            "only; it is not a strict JSON Schema decoding test."
        ),
    )
    parser.add_argument("--timeout", type=float, default=120.0)
    return parser.parse_args()


def request_json(
    url: str,
    api_key: str,
    timeout: float,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "User-Agent": "schema-order-official-endpoint-audit/0.1",
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


def sanitized_completion(payload: dict[str, Any]) -> dict[str, Any]:
    choices = payload.get("choices") or []
    message = (choices[0].get("message") or {}) if choices else {}
    content = visible_text(message.get("content"))
    reasoning_content = visible_text(message.get("reasoning_content"))
    parsed_json_object: dict[str, Any] | None = None
    if content is not None:
        try:
            candidate = json.loads(content)
            if isinstance(candidate, dict):
                parsed_json_object = candidate
        except json.JSONDecodeError:
            pass
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
        "content_json_object": parsed_json_object is not None,
        "content_api_status_ok": (
            parsed_json_object.get("api_status") == "API_OK"
            if parsed_json_object is not None
            else False
        ),
        "reasoning_content_length": (
            len(reasoning_content) if reasoning_content is not None else None
        ),
        "reasoning_content_sha256": (
            hashlib.sha256(reasoning_content.encode("utf-8")).hexdigest()
            if reasoning_content is not None
            else None
        ),
    }


def evaluate_gate(record: dict[str, Any], required_repeats: int = 3) -> dict[str, Any]:
    catalog = record.get("catalog") or {}
    runs = record.get("runs") or []
    returned_models = [
        run.get("response", {}).get("returned_model")
        for run in runs
        if run.get("status") == "ok"
    ]
    returned_models = [model for model in returned_models if model]
    successful_runs = sum(run.get("status") == "ok" for run in runs)
    stable_returned_model = (
        returned_models[0]
        if len(returned_models) == required_repeats
        and len(set(returned_models)) == 1
        else None
    )
    catalog_passed = (
        not catalog.get("error")
        and catalog.get("requested_model_present") is True
    )
    json_mode = (
        (record.get("request_body_extra") or {}).get("response_format")
        == {"type": "json_object"}
    )
    json_contract_passed = (
        all(
            run.get("response", {}).get("content_json_object") is True
            for run in runs
            if run.get("status") == "ok"
        )
        if json_mode
        else True
    )
    runs_passed = (
        len(runs) == required_repeats
        and successful_runs == required_repeats
        and stable_returned_model is not None
        and json_contract_passed
    )
    return {
        "required_repeats": required_repeats,
        "catalog_passed": catalog_passed,
        "successful_runs": successful_runs,
        "stable_returned_model": stable_returned_model,
        "json_mode_requested": json_mode,
        "json_contract_passed": json_contract_passed,
        "runs_passed": runs_passed,
        "gate_passed": catalog_passed and runs_passed,
    }


def main() -> int:
    args = parse_args()
    if not 1 <= args.repeats <= 5:
        print("--repeats must be between 1 and 5.", file=sys.stderr)
        return 2
    if args.provider == "deepseek" and not args.catalog_only and args.repeats != 3:
        print(
            "The frozen DeepSeek availability gate requires exactly "
            "--repeats 3.",
            file=sys.stderr,
        )
        return 2

    provider = PROVIDERS[args.provider]
    base_url = provider["base_url"].rstrip("/")
    model = args.model or provider["default_model"]
    api_key_env = provider["api_key_env"]
    request_body_extra = dict(provider.get("request_body_extra") or {})
    if args.json_mode:
        request_body_extra["response_format"] = {"type": "json_object"}
    api_key = os.environ.get(api_key_env)
    if not api_key and sys.stdin.isatty():
        api_key = getpass.getpass(
            f"Enter the official {args.provider} API key (input is hidden): "
        ).strip()
    if not api_key:
        print(f"{api_key_env} is not set and no API key was entered.", file=sys.stderr)
        return 2

    timestamp = datetime.now(UTC)
    record: dict[str, Any] = {
        "timestamp_utc": timestamp.isoformat(),
        "provider": args.provider,
        "base_url": base_url,
        "api_key_source": api_key_env,
        "requested_model": model,
        "request_body_extra": request_body_extra,
        "catalog": None,
        "runs": [],
    }

    try:
        catalog = request_json(f"{base_url}/models", api_key, args.timeout)
        model_rows = catalog.get("data") or []
        model_ids = [
            str(item.get("id"))
            for item in model_rows
            if isinstance(item, dict) and item.get("id")
        ]
        record["catalog"] = {
            "object": catalog.get("object"),
            "model_ids": model_ids,
            "requested_model_present": model in model_ids,
        }
        print(f"Official {args.provider} model IDs:")
        for model_id in model_ids:
            print(f"  {model_id}")
    except Exception as exc:
        record["catalog"] = {"error": f"{type(exc).__name__}: {exc}"}
        print(
            f"[WARN] model catalog unavailable: {type(exc).__name__}: {exc}",
            file=sys.stderr,
        )

    catalog_passed = (
        isinstance(record["catalog"], dict)
        and record["catalog"].get("requested_model_present") is True
        and not record["catalog"].get("error")
    )
    if not args.catalog_only and not catalog_passed:
        print(
            "[STOP] Requested model is not confirmed in the authenticated "
            "catalog; no completion smoke calls were sent.",
            file=sys.stderr,
        )
    elif not args.catalog_only:
        for repeat_index in range(1, args.repeats + 1):
            if args.json_mode:
                system_content = (
                    'Return exactly the JSON object {"api_status":"API_OK"} '
                    "and nothing else."
                )
                user_content = "JSON Mode connectivity check."
            else:
                system_content = "Return exactly API_OK and nothing else."
                user_content = "Connectivity check."
            payload = {
                "model": model,
                "messages": [
                    {
                        "role": "system",
                        "content": system_content,
                    },
                    {"role": "user", "content": user_content},
                ],
                "max_tokens": 512,
                "stream": False,
            }
            payload.update(request_body_extra)
            try:
                response = request_json(
                    f"{base_url}/chat/completions",
                    api_key,
                    args.timeout,
                    payload,
                )
                sanitized = sanitized_completion(response)
                record["runs"].append(
                    {
                        "repeat_index": repeat_index,
                        "status": "ok",
                        "response": sanitized,
                    }
                )
                print(
                    f"[OK] {model} run {repeat_index}/{args.repeats}: "
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
                print(
                    f"[ERROR] {model} run {repeat_index}/{args.repeats}: "
                    f"HTTP {exc.code}",
                    file=sys.stderr,
                )
            except Exception as exc:
                record["runs"].append(
                    {
                        "repeat_index": repeat_index,
                        "status": "error",
                        "error": f"{type(exc).__name__}: {exc}",
                    }
                )
                print(
                    f"[ERROR] {model} run {repeat_index}/{args.repeats}: "
                    f"{type(exc).__name__}: {exc}",
                    file=sys.stderr,
                )

    record["gate"] = evaluate_gate(record)
    output_dir = Path("data/raw/official_smoke")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / (
        f"{args.provider}_{timestamp.strftime('%Y%m%dT%H%M%SZ')}.json"
    )
    output_path.write_text(
        json.dumps(record, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Saved sanitized metadata to {output_path}")
    print(json.dumps(record["gate"], ensure_ascii=False, indent=2))

    if args.catalog_only:
        return 0 if record["gate"]["catalog_passed"] else 1
    return 0 if record["gate"]["gate_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
