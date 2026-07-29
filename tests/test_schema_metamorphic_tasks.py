from __future__ import annotations

import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from audit_sob_schema_variants import VARIANTS, schema_signature  # noqa: E402
from prepare_schema_metamorphic_tasks import (  # noqa: E402
    build_manifest,
    jsonl_bytes,
    prepare_rows,
)


SCHEMA = {
    "type": "object",
    "description": "Extract a person.",
    "properties": {
        "first": {"type": "string", "description": "Given name"},
        "last": {"type": "string", "description": "Family name"},
    },
    "required": ["first", "last"],
    "additionalProperties": False,
}


class SchemaMetamorphicTaskTests(unittest.TestCase):
    def test_all_variants_preserve_validation_signature(self) -> None:
        signature = schema_signature(SCHEMA)
        for transform in VARIANTS.values():
            self.assertEqual(schema_signature(transform(SCHEMA)), signature)

    def test_prepare_is_deterministic_and_public_only(self) -> None:
        source = [
            {
                "record_id": "r1",
                "context": "Ada Lovelace wrote notes.",
                "question": "Who is named?",
                "json_schema": SCHEMA,
                "metadata": {"split": "test"},
            }
        ]
        first, first_audit, first_counts = prepare_rows(source)
        second, second_audit, second_counts = prepare_rows(source)
        self.assertEqual(jsonl_bytes(first), jsonl_bytes(second))
        self.assertEqual(first_audit, second_audit)
        self.assertEqual(first_counts, second_counts)
        self.assertEqual(
            set(first[0]),
            {"record_id", "context", "question", "schema_variants", "metadata"},
        )
        self.assertTrue(first_audit[0]["variant_changed"]["properties_reversed"])
        self.assertTrue(first_audit[0]["variant_changed"]["required_reversed"])

    def test_restricted_answer_fields_are_rejected(self) -> None:
        source = [
            {
                "record_id": "r1",
                "context": "context",
                "question": "question",
                "json_schema": SCHEMA,
                "ground_truth": {"first": "Ada", "last": "Lovelace"},
            }
        ]
        with self.assertRaisesRegex(ValueError, "restricted answer-side fields"):
            prepare_rows(source)

    def test_duplicate_record_ids_are_rejected(self) -> None:
        row = {
            "record_id": "duplicate",
            "context": "context",
            "question": "question",
            "json_schema": SCHEMA,
        }
        with self.assertRaisesRegex(ValueError, "Duplicate record_id"):
            prepare_rows([row, dict(row)])

    def test_manifest_counts_repeated_conditions(self) -> None:
        manifest = build_manifest(
            study_name="test",
            record_ids=["a", "b"],
            repeats=3,
            model_alias="model-a",
            max_tokens=1024,
        )
        self.assertEqual(manifest["expected_requests"], 2 * len(VARIANTS) * 3)
        self.assertEqual(len(manifest["conditions"]), len(VARIANTS) * 3)


if __name__ == "__main__":
    unittest.main()

