"""Run a resumable SOB schema-order experiment through an OpenAI-compatible API."""

from __future__ import annotations

import argparse
import getpass
import hashlib
import json
import os
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx
from jsonschema import Draft202012Validator

from sob_metamorphic import (
    VARIANTS,
    append_jsonl,
    build_messages,
    compact_json,
    fake_value_for_schema,
    load_jsonl,
    parse_json_object,
    prompt_hash,
    request_key,
    sha256_text,
)


BANNED_PROMPT_FRAGMENTS = (
    "ground_truth",
    "data/restricted",
    "data\\restricted",
    "sol_sql",
    "test_cases",
)


class FatalRunError(RuntimeError):
    """Stop immediately rather than repeat a structurally invalid request."""


class FatalProvenanceError(FatalRunError):
    """Stop the run when the returned endpoint identity changes."""


def load_manifest(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def visible_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict) and isinstance(item.get("text"), str):
                parts.append(item["text"])
        if parts:
            return "".join(parts)
    raise RuntimeError("Gateway response content is not text")


def optional_visible_text(content: Any) -> str | None:
    return None if content is None else visible_text(content)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_smoke_record(
    path: Path,
    *,
    manifest: dict[str, Any],
    base_url: str,
    model_alias: str,
) -> tuple[str, str]:
    record = json.loads(path.read_text(encoding="utf-8"))
    if record.get("base_url", "").rstrip("/") != base_url.rstrip("/"):
        raise ValueError("Smoke record base URL differs from the frozen run")
    if record.get("requested_model") != model_alias:
        raise ValueError("Smoke record requested model differs from the frozen run")
    smoke_provider = manifest.get("smoke_provider")
    if smoke_provider and record.get("provider") != smoke_provider:
        raise ValueError("Smoke record provider differs from the frozen manifest")
    if manifest.get("require_smoke_request_contract_match"):
        if record.get("request_body_extra") != manifest.get("request_body_extra"):
            raise ValueError("Smoke request contract differs from the frozen manifest")
    gate = record.get("gate") or {}
    if gate.get("gate_passed") is not True:
        raise ValueError("Smoke record did not pass the frozen availability gate")
    returned_model = gate.get("stable_returned_model")
    if not isinstance(returned_model, str) or not returned_model:
        raise ValueError("Smoke record has no stable returned-model identifier")
    return returned_model, sha256_file(path)


class GatewayClient:
    def __init__(
        self,
        base_url: str,
        api_key: str,
        timeout_seconds: float,
        request_interval_seconds: float = 0.0,
    ) -> None:
        self.url = base_url.rstrip("/") + "/chat/completions"
        self.request_interval_seconds = max(0.0, request_interval_seconds)
        self._last_request_started: float | None = None
        self.client = httpx.Client(
            timeout=timeout_seconds,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "User-Agent": "sob-metamorphic-study/0.1",
            },
        )

    def close(self) -> None:
        self.client.close()

    def complete(
        self,
        *,
        model_alias: str,
        messages: list[dict[str, str]],
        max_tokens: int,
        request_body_extra: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        started = time.perf_counter()
        attempts: list[dict[str, Any]] = []
        payload: dict[str, Any] = {
            "model": model_alias,
            "messages": messages,
            "max_tokens": max_tokens,
            "stream": False,
        }
        if request_body_extra:
            collisions = set(payload).intersection(request_body_extra)
            if collisions:
                raise ValueError(
                    "Frozen request_body_extra overrides core request fields: "
                    f"{sorted(collisions)}"
                )
            payload.update(request_body_extra)
        for attempt in range(1, 4):
            try:
                if self._last_request_started is not None:
                    elapsed = time.monotonic() - self._last_request_started
                    remaining = self.request_interval_seconds - elapsed
                    if remaining > 0:
                        time.sleep(remaining)
                self._last_request_started = time.monotonic()
                # Sampling parameters are intentionally absent: Sonnet 5 rejects
                # non-default temperature/top_p/top_k on the official API.
                response = self.client.post(
                    self.url,
                    json=payload,
                )
                attempts.append({"attempt": attempt, "status_code": response.status_code})
                if response.status_code == 429 or response.status_code >= 500:
                    if attempt < 3:
                        time.sleep(2 ** (attempt - 1))
                        continue
                if 400 <= response.status_code < 500 and response.status_code != 429:
                    raise FatalRunError(
                        f"Non-retryable HTTP {response.status_code}: "
                        f"{response.text[:1000]}"
                    )
                response.raise_for_status()
                payload = response.json()
                choices = payload.get("choices") or []
                if not choices:
                    raise RuntimeError("Gateway response contains no choices")
                choice = choices[0]
                message = choice.get("message") or {}
                raw = visible_text(message.get("content"))
                reasoning_content = optional_visible_text(
                    message.get("reasoning_content")
                )
                usage = payload.get("usage") or {}
                return {
                    "raw_response": raw,
                    "response_id": payload.get("id"),
                    "returned_model": payload.get("model"),
                    "system_fingerprint": payload.get("system_fingerprint"),
                    "finish_reason": choice.get("finish_reason"),
                    "input_tokens": usage.get("prompt_tokens"),
                    "output_tokens": usage.get("completion_tokens"),
                    "usage": usage,
                    "reasoning_content_length": (
                        len(reasoning_content)
                        if reasoning_content is not None
                        else None
                    ),
                    "reasoning_content_sha256": (
                        hashlib.sha256(reasoning_content.encode("utf-8")).hexdigest()
                        if reasoning_content is not None
                        else None
                    ),
                    "latency_ms": round((time.perf_counter() - started) * 1000, 3),
                    "http_attempts": attempts,
                }
            except (httpx.TimeoutException, httpx.NetworkError) as exc:
                attempts.append({"attempt": attempt, "error": type(exc).__name__})
                if attempt < 3:
                    time.sleep(2 ** (attempt - 1))
                    continue
                raise
        raise RuntimeError("Gateway request exhausted retries")


def mock_complete(schema_text: str, model_alias: str) -> dict[str, Any]:
    schema = json.loads(schema_text)
    raw = compact_json(fake_value_for_schema(schema))
    return {
        "raw_response": raw,
        "response_id": None,
        "returned_model": f"mock:{model_alias}",
        "system_fingerprint": None,
        "finish_reason": "stop",
        "input_tokens": 0,
        "output_tokens": 0,
        "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
        "reasoning_content_length": None,
        "reasoning_content_sha256": None,
        "latency_ms": 0.0,
        "http_attempts": [{"attempt": 1, "status_code": 200, "mock": True}],
    }


def latest_successes(path: Path) -> dict[str, dict[str, Any]]:
    if not path.exists():
        return {}
    successes: dict[str, dict[str, Any]] = {}
    for row in load_jsonl(path):
        if row.get("status") == "ok":
            successes[str(row["request_key"])] = row
    return successes


def missing_successful_request_keys(
    expected_keys: set[str],
    successes: dict[str, dict[str, Any]],
) -> list[str]:
    """Return frozen request keys that still lack a successful response."""

    return sorted(expected_keys - set(successes))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--public-input", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--model-alias", default="claude-sonnet-5")
    parser.add_argument("--base-url", default=os.environ.get("GATEWAY_BASE_URL", ""))
    parser.add_argument(
        "--api-key-env",
        default="GATEWAY_API_KEY",
        help="Environment variable containing the API key (prompted securely if absent).",
    )
    parser.add_argument(
        "--provider-label",
        default="third_party_gateway",
        help="Non-secret provider/provenance label written to every result row.",
    )
    parser.add_argument(
        "--no-key-prompt",
        action="store_true",
        help="Fail instead of securely prompting when --api-key-env is unset.",
    )
    parser.add_argument(
        "--smoke-record",
        type=Path,
        help=(
            "Sanitized availability-gate JSON. Required by official-provider "
            "manifests that declare requires_smoke_record."
        ),
    )
    parser.add_argument("--max-tokens", type=int, default=4096)
    parser.add_argument("--request-timeout", type=float, default=240.0)
    parser.add_argument(
        "--request-interval",
        type=float,
        default=None,
        help=(
            "Minimum seconds between request starts. If omitted, use the frozen "
            "manifest value (required for rate-limited institutional endpoints)."
        ),
    )
    parser.add_argument("--mock", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.mock and not args.base_url:
        print(
            "GATEWAY_BASE_URL is not set and --base-url was not provided.",
            file=sys.stderr,
        )
        return 2
    api_key = os.environ.get(args.api_key_env)
    if not args.mock and not api_key and not args.no_key_prompt and sys.stdin.isatty():
        api_key = getpass.getpass(
            f"Enter the {args.provider_label} API key (input is hidden): "
        ).strip()
    if not args.mock and not api_key:
        print(
            f"{args.api_key_env} is not set and no API key was entered.",
            file=sys.stderr,
        )
        return 2

    manifest = load_manifest(args.manifest)
    if manifest.get("model_alias") != args.model_alias and not args.mock:
        print("Model alias differs from the frozen pilot manifest.", file=sys.stderr)
        return 2
    frozen_provider = manifest.get("provider_label")
    if frozen_provider and frozen_provider != args.provider_label and not args.mock:
        print("Provider label differs from the frozen pilot manifest.", file=sys.stderr)
        return 2
    frozen_base_url = manifest.get("base_url")
    if (
        frozen_base_url
        and str(frozen_base_url).rstrip("/") != args.base_url.rstrip("/")
        and not args.mock
    ):
        print("Base URL differs from the frozen pilot manifest.", file=sys.stderr)
        return 2
    frozen_max_tokens = int(manifest.get("max_tokens", args.max_tokens))
    if args.max_tokens != frozen_max_tokens and not args.mock:
        print("Max tokens differs from the frozen pilot manifest.", file=sys.stderr)
        return 2
    frozen_request_interval = float(manifest.get("request_interval_seconds", 0.0))
    request_interval = (
        frozen_request_interval
        if args.request_interval is None
        else float(args.request_interval)
    )
    if abs(request_interval - frozen_request_interval) > 1e-9 and not args.mock:
        print(
            "Request interval differs from the frozen pilot manifest.",
            file=sys.stderr,
        )
        return 2
    request_body_extra = manifest.get("request_body_extra") or {}
    if not isinstance(request_body_extra, dict):
        print("Manifest request_body_extra must be an object.", file=sys.stderr)
        return 2

    expected_returned_model: str | None = None
    smoke_record_sha256: str | None = None
    if manifest.get("requires_smoke_record") and not args.mock:
        if args.smoke_record is None:
            print(
                "This manifest requires --smoke-record from a passed "
                "availability gate.",
                file=sys.stderr,
            )
            return 2
        try:
            expected_returned_model, smoke_record_sha256 = validate_smoke_record(
                args.smoke_record,
                manifest=manifest,
                base_url=args.base_url,
                model_alias=args.model_alias,
            )
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            print(f"Invalid smoke record: {exc}", file=sys.stderr)
            return 2
    record_ids = list(manifest["record_ids"])
    if "conditions" in manifest:
        conditions = [
            (str(item["name"]), str(item["schema_variant"]))
            for item in manifest["conditions"]
        ]
    else:
        variants = tuple(manifest["variants"])
        if variants != VARIANTS:
            raise ValueError("Manifest variant order does not match the implementation")
        conditions = [(variant, variant) for variant in variants]
    if len({name for name, _ in conditions}) != len(conditions):
        raise ValueError("Manifest condition names must be unique")
    if any(schema_variant not in VARIANTS for _, schema_variant in conditions):
        raise ValueError("Manifest condition references an unknown schema variant")
    public_by_id = {row["record_id"]: row for row in load_jsonl(args.public_input)}
    missing = sorted(set(record_ids) - set(public_by_id))
    if missing:
        raise ValueError(f"Pilot IDs missing from public data: {missing}")

    jobs: list[
        tuple[dict[str, Any], str, str, list[dict[str, str]], str, str]
    ] = []
    for record_id in record_ids:
        row = public_by_id[record_id]
        for condition_name, schema_variant in conditions:
            messages = build_messages(row, schema_variant)
            digest = prompt_hash(messages)
            prompt_text = compact_json(messages).lower()
            hits = [fragment for fragment in BANNED_PROMPT_FRAGMENTS if fragment in prompt_text]
            if hits:
                raise ValueError(
                    f"Prompt leakage guard failed for {record_id}/{condition_name}: {hits}"
                )
            key = request_key(record_id, condition_name, args.model_alias, digest)
            jobs.append(
                (row, condition_name, schema_variant, messages, digest, key)
            )

    # Avoid coupling a schema variant to an early/late request position while
    # retaining a fully reproducible order for interruption and resume.
    jobs.sort(
        key=lambda job: sha256_text(
            "|".join((manifest["pilot_name"], job[0]["record_id"], job[1]))
        )
    )

    if len(jobs) != int(manifest["expected_requests"]):
        raise ValueError("Job count differs from frozen manifest")
    expected_keys = {job[-1] for job in jobs}
    existing = latest_successes(args.output)
    initially_remaining = missing_successful_request_keys(expected_keys, existing)
    print(
        f"Resume status: {len(expected_keys) - len(initially_remaining)}/"
        f"{len(expected_keys)} frozen request keys already successful; "
        f"{len(initially_remaining)} will be attempted.",
        flush=True,
    )
    existing_returned_models = {
        str(row.get("returned_model"))
        for row in existing.values()
        if row.get("returned_model") is not None
    }
    if expected_returned_model is not None and existing_returned_models not in (
        set(),
        {expected_returned_model},
    ):
        raise FatalProvenanceError(
            "Existing successful rows contain a returned-model identity that "
            "differs from the passed smoke gate."
        )
    existing_fingerprints = {
        str(row.get("system_fingerprint"))
        for row in existing.values()
        if row.get("system_fingerprint") is not None
    }
    if len(existing_fingerprints) > 1:
        raise FatalProvenanceError(
            "Existing successful rows contain multiple non-null system fingerprints."
        )
    expected_fingerprint = next(iter(existing_fingerprints), None)
    client = (
        None
        if args.mock
        else GatewayClient(
            args.base_url,
            str(api_key),
            args.request_timeout,
            request_interval,
        )
    )
    consecutive_request_errors = 0
    try:
        for index, (
            row,
            condition_name,
            schema_variant,
            messages,
            digest,
            key,
        ) in enumerate(jobs, start=1):
            fatal_error: FatalRunError | None = None
            if key in existing:
                continue
            started = time.perf_counter()
            try:
                result = (
                    mock_complete(
                        row["schema_variants"][schema_variant], args.model_alias
                    )
                    if args.mock
                    else client.complete(
                        model_alias=args.model_alias,
                        messages=messages,
                        max_tokens=args.max_tokens,
                        request_body_extra=request_body_extra,
                    )
                )
                if (
                    expected_returned_model is not None
                    and result["returned_model"] != expected_returned_model
                ):
                    raise FatalProvenanceError(
                        "Returned model differs from the passed smoke gate: "
                        f"{result['returned_model']!r} != "
                        f"{expected_returned_model!r}"
                    )
                if (
                    expected_fingerprint is not None
                    and result["system_fingerprint"] is not None
                    and str(result["system_fingerprint"]) != expected_fingerprint
                ):
                    raise FatalProvenanceError(
                        "System fingerprint differs from the existing successful "
                        f"deployment rows: {result['system_fingerprint']!r} != "
                        f"{expected_fingerprint!r}"
                    )
                parsed, parse_status = parse_json_object(result["raw_response"])
                schema = json.loads(row["schema_variants"][schema_variant])
                schema_errors = (
                    [error.message for error in Draft202012Validator(schema).iter_errors(parsed)]
                    if parsed is not None
                    else []
                )
                record = {
                    "record_id": row["record_id"],
                    "variant": condition_name,
                    "schema_variant": schema_variant,
                    "provider_label": args.provider_label,
                    "base_url": args.base_url.rstrip("/"),
                    "model_alias": args.model_alias,
                    "returned_model": result["returned_model"],
                    "system_fingerprint": result["system_fingerprint"],
                    "smoke_record_sha256": smoke_record_sha256,
                    "request_key": key,
                    "prompt_hash": digest,
                    "raw_response": result["raw_response"],
                    "response_id": result["response_id"],
                    "parsed_output": parsed,
                    "parse_status": parse_status,
                    "schema_valid": parsed is not None and not schema_errors,
                    "schema_errors": schema_errors[:5],
                    "finish_reason": result["finish_reason"],
                    "input_tokens": result["input_tokens"],
                    "output_tokens": result["output_tokens"],
                    "usage": result["usage"],
                    "reasoning_content_length": result[
                        "reasoning_content_length"
                    ],
                    "reasoning_content_sha256": result[
                        "reasoning_content_sha256"
                    ],
                    "request_parameters": {
                        "max_tokens": args.max_tokens,
                        "request_interval_seconds": request_interval,
                        "stream": False,
                        "sampling_parameters": "omitted",
                        "thinking": (
                            "disabled_explicitly"
                            if request_body_extra.get("enable_thinking") is False
                            else "omitted_provider_default"
                        ),
                        "request_body_extra": request_body_extra,
                        "response_format": (
                            request_body_extra.get("response_format")
                            or "omitted_text_mode"
                        ),
                        "tools": "omitted",
                    },
                    "latency_ms": result["latency_ms"],
                    "http_attempts": result["http_attempts"],
                    "timestamp": datetime.now(UTC).isoformat(),
                    "status": "ok",
                    "mock": args.mock,
                }
            except Exception as exc:
                if isinstance(exc, FatalRunError):
                    fatal_error = exc
                record = {
                    "record_id": row["record_id"],
                    "variant": condition_name,
                    "schema_variant": schema_variant,
                    "provider_label": args.provider_label,
                    "base_url": args.base_url.rstrip("/"),
                    "model_alias": args.model_alias,
                    "smoke_record_sha256": smoke_record_sha256,
                    "request_key": key,
                    "prompt_hash": digest,
                    "raw_response": None,
                    "parsed_output": None,
                    "parse_status": "request_error",
                    "schema_valid": False,
                    "latency_ms": round((time.perf_counter() - started) * 1000, 3),
                    "timestamp": datetime.now(UTC).isoformat(),
                    "status": "error",
                    "error": f"{type(exc).__name__}: {exc}",
                    "mock": args.mock,
                }
            append_jsonl(args.output, record)
            print(
                f"[{index}/{len(jobs)}] {row['record_id'][:8]} {condition_name} "
                f"status={record['status']} parse={record['parse_status']} "
                f"schema={record['schema_valid']}",
                flush=True,
            )
            if record["status"] == "ok":
                consecutive_request_errors = 0
            else:
                consecutive_request_errors += 1
            if fatal_error is not None:
                raise fatal_error
            if consecutive_request_errors >= 5:
                raise RuntimeError(
                    "Paused after five consecutive request errors; inspect the "
                    "saved rows before resuming the identical request keys."
                )
    finally:
        if client is not None:
            client.close()
    final_successes = latest_successes(args.output)
    remaining = missing_successful_request_keys(expected_keys, final_successes)
    if remaining:
        completed = len(expected_keys) - len(remaining)
        print(
            f"Run incomplete: {completed}/{len(expected_keys)} frozen request "
            f"keys have successful responses; {len(remaining)} remain. "
            "Rerun the identical command to retry only those keys.",
            file=sys.stderr,
        )
        return 1
    print(
        f"Run complete: {len(expected_keys)}/{len(expected_keys)} frozen request "
        "keys have successful responses.",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
