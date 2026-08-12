from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from audit_schema_canonicalization import audit_rows  # noqa: E402
from canonicalize_json_schema import (  # noqa: E402
    canonical_schema_text,
    canonicalize_schema,
)


class SchemaCanonicalizationTests(unittest.TestCase):
    def test_object_and_required_order_collapse(self) -> None:
        left = {
            "type": "object",
            "properties": {"b": {"type": "string"}, "a": {"type": "integer"}},
            "required": ["b", "a"],
        }
        right = {
            "required": ["a", "b"],
            "properties": {"a": {"type": "integer"}, "b": {"type": "string"}},
            "type": "object",
        }
        self.assertEqual(canonical_schema_text(left), canonical_schema_text(right))

    def test_non_required_arrays_keep_order(self) -> None:
        schema = {"type": "array", "prefixItems": [{"type": "string"}, {"type": "integer"}]}
        canonical = canonicalize_schema(schema)
        self.assertEqual(canonical["prefixItems"], schema["prefixItems"])

    def test_duplicate_required_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "duplicate required"):
            canonicalize_schema({"required": ["a", "a"]})

    def test_public_variant_audit(self) -> None:
        variants = {
            "original": json.dumps(
                {"type": "object", "properties": {"a": {"type": "string"}}, "required": ["a"]}
            ),
            "keywords_reversed": json.dumps(
                {"required": ["a"], "properties": {"a": {"type": "string"}}, "type": "object"}
            ),
        }
        report = audit_rows([{"record_id": "r1", "schema_variants": variants}])
        self.assertTrue(report["all_variants_collapse_per_record"])


if __name__ == "__main__":
    unittest.main()
