from __future__ import annotations

import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from analyze_sob_cross_model_exploratory import (  # noqa: E402
    average_ranks,
    pearson,
    schema_features,
    spearman,
)


class CrossModelExploratoryTests(unittest.TestCase):
    def test_average_ranks_handles_ties(self) -> None:
        self.assertEqual(average_ranks([10.0, 20.0, 20.0, 40.0]), [1.0, 2.5, 2.5, 4.0])

    def test_correlations_have_expected_extremes(self) -> None:
        left = [1.0, 2.0, 3.0, 4.0]
        self.assertAlmostEqual(pearson(left, left), 1.0)
        self.assertAlmostEqual(spearman(left, list(reversed(left))), -1.0)

    def test_schema_features_include_nested_objects(self) -> None:
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Person name"},
                "details": {
                    "type": "object",
                    "properties": {
                        "age": {"type": "integer", "description": "Age"},
                        "active": {"type": "boolean"},
                    },
                    "required": ["age", "active"],
                },
            },
            "required": ["name", "details"],
        }
        features = schema_features(schema)
        self.assertEqual(features["top_level_properties"], 2)
        self.assertEqual(features["total_properties"], 4)
        self.assertEqual(features["object_nodes"], 2)
        self.assertEqual(features["leaf_nodes"], 3)
        self.assertEqual(features["required_entries"], 4)
        self.assertEqual(features["max_schema_depth"], 3)
        self.assertEqual(features["description_chars"], len("Person name") + len("Age"))


if __name__ == "__main__":
    unittest.main()
