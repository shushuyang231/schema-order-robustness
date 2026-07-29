from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from analyze_sob_decomposed_cross_model import record_contrast  # noqa: E402


class DecomposedCrossModelTests(unittest.TestCase):
    def test_record_contrast_returns_distribution_and_treatment_minus_baseline_accuracy(self):
        summary = {
            ("r", "a"): {
                "normalized_signatures": ["x", "x"],
                "leaf_value_accuracy": 0.75,
            },
            ("r", "b"): {
                "normalized_signatures": ["y", "y"],
                "leaf_value_accuracy": 0.50,
            },
        }
        distribution, accuracy = record_contrast(summary, "r", "a", "b")
        self.assertEqual(distribution, 1.0)
        self.assertEqual(accuracy, -0.25)


if __name__ == "__main__":
    unittest.main()
