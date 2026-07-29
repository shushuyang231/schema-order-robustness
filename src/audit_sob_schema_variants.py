from __future__ import annotations

import argparse
import copy
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq
from jsonschema import Draft202012Validator


def compact_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def stable_hash(value: Any) -> str:
    return hashlib.sha256(compact_json(value).encode("utf-8")).hexdigest()


def walk_schema(value: Any):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk_schema(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk_schema(child)


def reverse_property_order(value: Any) -> Any:
    if isinstance(value, list):
        return [reverse_property_order(item) for item in value]
    if not isinstance(value, dict):
        return value

    result: dict[str, Any] = {}
    for key, child in value.items():
        if key == "properties" and isinstance(child, dict):
            result[key] = {
                name: reverse_property_order(schema)
                for name, schema in reversed(list(child.items()))
            }
        else:
            result[key] = reverse_property_order(child)
    return result


def reverse_required_order(value: Any) -> Any:
    if isinstance(value, list):
        return [reverse_required_order(item) for item in value]
    if not isinstance(value, dict):
        return value

    result: dict[str, Any] = {}
    for key, child in value.items():
        if key == "required" and isinstance(child, list):
            result[key] = list(reversed(child))
        else:
            result[key] = reverse_required_order(child)
    return result


def reverse_keyword_order(value: Any) -> Any:
    if isinstance(value, list):
        return [reverse_keyword_order(item) for item in value]
    if not isinstance(value, dict):
        return value
    return {
        key: reverse_keyword_order(child)
        for key, child in reversed(list(value.items()))
    }


def descriptions_first(value: Any) -> Any:
    if isinstance(value, list):
        return [descriptions_first(item) for item in value]
    if not isinstance(value, dict):
        return value

    transformed = {key: descriptions_first(child) for key, child in value.items()}
    if "description" not in transformed:
        return transformed
    return {
        "description": transformed["description"],
        **{key: child for key, child in transformed.items() if key != "description"},
    }


VARIANTS = {
    "original": lambda schema: copy.deepcopy(schema),
    "properties_reversed": reverse_property_order,
    "required_reversed": reverse_required_order,
    "keywords_reversed": reverse_keyword_order,
    "descriptions_first": descriptions_first,
}

JSON_SCHEMA_KEYWORDS = {
    "$defs",
    "$id",
    "$ref",
    "$schema",
    "additionalProperties",
    "allOf",
    "anyOf",
    "const",
    "default",
    "dependentRequired",
    "dependentSchemas",
    "description",
    "else",
    "enum",
    "exclusiveMaximum",
    "exclusiveMinimum",
    "format",
    "if",
    "items",
    "maxItems",
    "maxLength",
    "maxProperties",
    "maximum",
    "minItems",
    "minLength",
    "minProperties",
    "minimum",
    "multipleOf",
    "not",
    "oneOf",
    "pattern",
    "patternProperties",
    "prefixItems",
    "properties",
    "propertyNames",
    "required",
    "then",
    "title",
    "type",
    "unevaluatedItems",
    "unevaluatedProperties",
    "uniqueItems",
}


def schema_signature(value: Any, *, parent_key: str | None = None) -> Any:
    """Normalize order-insensitive JSON Schema constructs for an equivalence audit."""
    if isinstance(value, dict):
        return {
            key: schema_signature(child, parent_key=key)
            for key, child in sorted(value.items())
        }
    if isinstance(value, list):
        normalized = [schema_signature(child, parent_key=parent_key) for child in value]
        if parent_key in {"required", "enum"}:
            return sorted(normalized, key=compact_json)
        return normalized
    return value


def choose_fixed_sample(rows: list[dict[str, Any]], per_group: int) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        groups.setdefault(str(row["schema_complexity"]), []).append(row)

    selected: list[dict[str, Any]] = []
    for complexity in sorted(groups):
        ranked = sorted(groups[complexity], key=lambda row: stable_hash(row["record_id"]))
        selected.extend(ranked[:per_group])
    return sorted(selected, key=lambda row: row["record_id"])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--sample-public", type=Path, required=True)
    parser.add_argument("--sample-gold", type=Path, required=True)
    parser.add_argument("--per-complexity", type=int, default=50)
    args = parser.parse_args()

    rows = pq.read_table(args.input).to_pylist()
    complexity_counts = Counter(str(row["schema_complexity"]) for row in rows)
    question_counts = Counter(str(row["question_type"]) for row in rows)
    keyword_counts: Counter[str] = Counter()
    validation_failures: list[dict[str, str]] = []
    changed_counts: Counter[str] = Counter()

    parsed_rows: list[dict[str, Any]] = []
    for row in rows:
        schema = json.loads(row["json_schema"])
        ground_truth = json.loads(row["ground_truth"])
        Draft202012Validator.check_schema(schema)
        errors = list(Draft202012Validator(schema).iter_errors(ground_truth))
        if errors:
            validation_failures.append(
                {"record_id": row["record_id"], "message": errors[0].message}
            )

        for node in walk_schema(schema):
            keyword_counts.update(key for key in node if key in JSON_SCHEMA_KEYWORDS)

        original_signature = schema_signature(schema)
        variants: dict[str, str] = {}
        for name, transform in VARIANTS.items():
            transformed = transform(schema)
            if schema_signature(transformed) != original_signature:
                raise AssertionError(f"Non-equivalent transform {name}: {row['record_id']}")
            variant_text = compact_json(transformed)
            variants[name] = variant_text
            if variant_text != compact_json(schema):
                changed_counts[name] += 1

        parsed_rows.append(
            {
                **row,
                "schema_object": schema,
                "ground_truth_object": ground_truth,
                "variants": variants,
            }
        )

    selected = choose_fixed_sample(parsed_rows, args.per_complexity)
    public_records = []
    gold_records = []
    for row in selected:
        public_records.append(
            {
                "record_id": row["record_id"],
                "question_type": row["question_type"],
                "question_difficulty": row["question_difficulty"],
                "schema_complexity": row["schema_complexity"],
                "context": row["context"],
                "question": row["question"],
                "schema_variants": row["variants"],
            }
        )
        gold_records.append(
            {
                "record_id": row["record_id"],
                "ground_truth": row["ground_truth_object"],
            }
        )

    report = {
        "input": str(args.input.resolve()),
        "input_sha256": hashlib.sha256(args.input.read_bytes()).hexdigest(),
        "row_count": len(rows),
        "complexity_counts": dict(sorted(complexity_counts.items())),
        "question_type_counts": dict(sorted(question_counts.items())),
        "schema_keyword_counts": dict(keyword_counts.most_common()),
        "ground_truth_schema_validation_failures": validation_failures,
        "variant_changed_record_counts": dict(sorted(changed_counts.items())),
        "sample_count": len(public_records),
        "sample_ids_sha256": stable_hash([row["record_id"] for row in public_records]),
        "sample_complexity_counts": dict(
            sorted(Counter(row["schema_complexity"] for row in public_records).items())
        ),
        "equivalence_rule": (
            "Only JSON object member order plus required/enum array order are changed; "
            "these are validation-order-insensitive under JSON Schema."
        ),
    }

    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.sample_public.parent.mkdir(parents=True, exist_ok=True)
    args.sample_gold.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    with args.sample_public.open("w", encoding="utf-8", newline="\n") as handle:
        for record in public_records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    with args.sample_gold.open("w", encoding="utf-8", newline="\n") as handle:
        for record in gold_records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
