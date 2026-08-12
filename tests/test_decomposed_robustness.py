import statistics
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from analyze_sob_decomposed_robustness import concentration_summary, trimmed_mean


class DecomposedRobustnessTests(unittest.TestCase):
    def test_trimmed_mean_removes_both_tails(self) -> None:
        values = list(range(10))
        self.assertEqual(trimmed_mean(values), statistics.fmean(range(1, 9)))

    def test_concentration_reports_largest_decile_dependency(self) -> None:
        summary = concentration_summary([0.0] * 9 + [1.0])
        self.assertAlmostEqual(summary["mean"], 0.1)
        self.assertEqual(summary["mean_after_removing_largest_10pct"], 0.0)
        self.assertEqual(summary["largest_10pct_positive_mass_share"], 1.0)


if __name__ == "__main__":
    unittest.main()
