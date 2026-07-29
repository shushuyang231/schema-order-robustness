"""Shared, public-side utilities for the SOB metamorphic experiment."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any


VARIANTS = (
    "original",
    "properties_reversed",
    "required_reversed",
    "keywords_reversed",
    "descriptions_first",
)

SYSTEM_PROMPT = (
    "You are a precise information extraction system. Answer using only one JSON "
    "object that satisfies the supplied JSON Schema. Do not add markdown, "
    "explanations, comments, or fields not allowed by the schema. Use only the "
    "provided context."
)

_FENCED_JSON = re.compile(r"^```(?:json)?\s*(.*?)\s*```$", re.IGNORECASE | re.DOTALL)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
        handle.flush()


def compact_json(value: Any, *, sort_keys: bool = False) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=sort_keys,
    )


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def build_messages(row: dict[str, Any], variant: str) -> list[dict[str, str]]:
    if variant not in VARIANTS:
        raise ValueError(f"Unknown schema variant: {variant}")
    schema_text = row["schema_variants"][variant]
    user_prompt = (
        "# Context\n"
        + str(row["context"])
        + "\n\n# Question\n"
        + str(row["question"])
        + "\n\n# JSON Schema\n"
        + schema_text
        + "\n\nReturn only the JSON object."
    )
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]


def prompt_hash(messages: list[dict[str, str]]) -> str:
    return sha256_text(compact_json(messages, sort_keys=True))


def request_key(record_id: str, variant: str, model_alias: str, digest: str) -> str:
    return sha256_text("|".join((record_id, variant, model_alias, digest)))


def parse_json_object(raw: str) -> tuple[dict[str, Any] | None, str]:
    text = raw.strip().lstrip("\ufeff")
    candidates: list[tuple[str, str]] = [(text, "exact_json")]
    match = _FENCED_JSON.match(text)
    if match:
        candidates.insert(0, (match.group(1).strip(), "fenced_json"))
    start, end = text.find("{"), text.rfind("}")
    if start >= 0 and end > start and (start != 0 or end != len(text) - 1):
        candidates.append((text[start : end + 1], "extracted_json"))

    seen: set[str] = set()
    for candidate, status in candidates:
        if candidate in seen:
            continue
        seen.add(candidate)
        try:
            value = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            return value, status
        return None, "json_not_object"
    return None, "invalid_json"


def fake_value_for_schema(schema: dict[str, Any]) -> Any:
    if "const" in schema:
        return schema["const"]
    enum = schema.get("enum")
    if isinstance(enum, list) and enum:
        return enum[0]
    schema_type = schema.get("type")
    if isinstance(schema_type, list):
        schema_type = next((item for item in schema_type if item != "null"), "null")
    if schema_type == "object" or isinstance(schema.get("properties"), dict):
        properties = schema.get("properties") or {}
        required = schema.get("required") or list(properties)
        return {
            name: fake_value_for_schema(properties[name])
            for name in required
            if name in properties
        }
    if schema_type == "array":
        item_schema = schema.get("items")
        minimum = int(schema.get("minItems", 0) or 0)
        return [fake_value_for_schema(item_schema)] * minimum if isinstance(item_schema, dict) else []
    if schema_type == "integer":
        return int(schema.get("minimum", 0))
    if schema_type == "number":
        return float(schema.get("minimum", 0.0))
    if schema_type == "boolean":
        return False
    if schema_type == "null":
        return None
    return ""

