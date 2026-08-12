"""Conservatively canonicalize JSON Schema serialization for prompt stability.

The transform sorts every JSON object member and sorts only ``required`` arrays.
Other arrays are preserved because their order may carry validation, annotation,
or application meaning. This is a representation control for the transformations
studied in this repository, not a general JSON Schema equivalence theorem.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from audit_sob_schema_variants import schema_signature


def canonicalize_schema(value: Any, *, parent_key: str | None = None) -> Any:
    if isinstance(value, dict):
        return {
            key: canonicalize_schema(value[key], parent_key=key)
            for key in sorted(value)
        }
    if isinstance(value, list):
        children = [canonicalize_schema(item, parent_key=parent_key) for item in value]
        if parent_key == "required":
            if not all(isinstance(item, str) for item in children):
                raise ValueError("A JSON Schema required array must contain strings")
            if len(children) != len(set(children)):
                raise ValueError("Refusing to canonicalize duplicate required entries")
            return sorted(children)
        return children
    return value


def canonical_schema_text(schema: dict[str, Any]) -> str:
    Draft202012Validator.check_schema(schema)
    canonical = canonicalize_schema(schema)
    if schema_signature(canonical) != schema_signature(schema):
        raise AssertionError("Canonicalization changed the audited validation signature")
    return json.dumps(canonical, ensure_ascii=False, separators=(",", ":"))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit 1 when the input is valid but not already canonical.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    value = json.loads(args.input.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("The input JSON Schema must be an object")
    canonical = canonical_schema_text(value) + "\n"
    original_compact = json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(canonical, encoding="utf-8")
    elif not args.check:
        print(canonical, end="")
    if args.check and canonical != original_compact:
        print("Schema serialization is not canonical.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
