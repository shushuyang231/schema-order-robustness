from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from analyze_sob_contrast_decomposition import (  # noqa: E402
    CONTRASTS,
    property_order_signature,
)


class ContrastDecompositionTests(unittest.TestCase):
    def test_incremental_keyword_contrast_holds_property_variant_as_baseline(self):
        self.assertEqual(
            CONTRASTS["additional_keyword_order_given_reversed_properties"],
            ("properties_reversed", "keywords_reversed"),
        )

    def test_property_order_signature_ignores_keyword_member_order(self):
        left = {
            "type": "object",
            "properties": {
                "b": {"type": "string", "description": "B"},
                "a": {"type": "integer", "description": "A"},
            },
            "required": ["a", "b"],
        }
        right = {
            "required": ["a", "b"],
            "properties": {
                "b": {"description": "B", "type": "string"},
                "a": {"description": "A", "type": "integer"},
            },
            "type": "object",
        }
        self.assertEqual(property_order_signature(left), property_order_signature(right))

    def test_property_order_signature_detects_property_reordering(self):
        left = {"properties": {"a": {"type": "string"}, "b": {"type": "string"}}}
        right = {"properties": {"b": {"type": "string"}, "a": {"type": "string"}}}
        self.assertNotEqual(property_order_signature(left), property_order_signature(right))


if __name__ == "__main__":
    unittest.main()
