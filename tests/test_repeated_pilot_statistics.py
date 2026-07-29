from __future__ import annotations

import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from evaluate_sob_repeated_pilot import (  # noqa: E402
    cross_model_replication_decision,
    cross_disagreement,
    disagreement,
    excess_disagreement,
    holm_adjust,
    score_prediction,
    select_qualifying_signals,
)


class RepeatedPilotStatisticsTests(unittest.TestCase):
    def test_identical_constant_groups_have_zero_excess(self) -> None:
        left = ["A"] * 5
        right = ["A"] * 5
        self.assertEqual(disagreement(left), 0.0)
        self.assertEqual(cross_disagreement(left, right), 0.0)
        self.assertEqual(excess_disagreement(left, right), 0.0)

    def test_disjoint_constant_groups_have_maximal_excess(self) -> None:
        left = ["A"] * 5
        right = ["B"] * 5
        self.assertEqual(disagreement(left), 0.0)
        self.assertEqual(disagreement(right), 0.0)
        self.assertEqual(cross_disagreement(left, right), 1.0)
        self.assertEqual(excess_disagreement(left, right), 1.0)

    def test_within_noise_is_subtracted(self) -> None:
        left = ["A", "A", "A", "B", "B"]
        right = ["A", "A", "B", "B", "B"]
        raw_cross = cross_disagreement(left, right)
        excess = excess_disagreement(left, right)
        self.assertLess(excess, raw_cross)

    def test_holm_adjustment_is_monotone_and_bounded(self) -> None:
        adjusted = holm_adjust({"a": 0.01, "b": 0.03, "c": 0.20, "d": 0.90})
        self.assertAlmostEqual(adjusted["a"], 0.04)
        self.assertLessEqual(adjusted["a"], adjusted["b"])
        self.assertLessEqual(adjusted["b"], adjusted["c"])
        self.assertLessEqual(adjusted["c"], adjusted["d"])
        self.assertTrue(all(0.0 <= value <= 1.0 for value in adjusted.values()))

    def test_scoring_distinguishes_exact_and_token_normalized_values(self) -> None:
        schema = {
            "type": "object",
            "properties": {"event": {"type": "string"}},
            "required": ["event"],
            "additionalProperties": False,
        }
        prediction = {
            "parsed_output": {"event": "First British performance"},
            "parse_status": "exact_json",
            "returned_model": "test",
        }
        score = score_prediction(
            prediction, schema, {"event": "first British performance"}
        )
        self.assertEqual(score["leaf_value_accuracy"], 0.0)
        self.assertEqual(score["value_token_f1"], 1.0)
        self.assertFalse(score["perfect_response"])
        self.assertTrue(score["schema_valid"])

    def test_go_signal_requires_effect_ci_and_adjusted_p(self) -> None:
        base = {
            "normalized_excess_disagreement": 0.06,
            "normalized_excess_disagreement_ci95": [0.01, 0.10],
            "normalized_energy_holm_p": 0.04,
            "leaf_value_accuracy_difference": 0.0,
            "leaf_value_accuracy_difference_ci95": [-0.01, 0.01],
            "leaf_accuracy_holm_p": 1.0,
        }
        signals = select_qualifying_signals({"properties_reversed": base})
        self.assertEqual(
            signals,
            [
                {
                    "variant": "properties_reversed",
                    "criterion": "normalized_distribution_shift",
                }
            ],
        )
        below_threshold = dict(base, normalized_excess_disagreement=0.049)
        self.assertEqual(
            select_qualifying_signals({"properties_reversed": below_threshold}), []
        )

    def test_cross_model_replication_decision_is_tiered(self) -> None:
        self.assertEqual(
            cross_model_replication_decision(
                operational_gate=True,
                replicated_count=2,
                required_count=1,
                primary_count=2,
            ),
            "STRONG_CROSS_MODEL_REPLICATION",
        )
        self.assertEqual(
            cross_model_replication_decision(
                operational_gate=True,
                replicated_count=1,
                required_count=1,
                primary_count=2,
            ),
            "PARTIAL_CROSS_MODEL_REPLICATION",
        )
        self.assertEqual(
            cross_model_replication_decision(
                operational_gate=True,
                replicated_count=0,
                required_count=1,
                primary_count=2,
            ),
            "CROSS_MODEL_REPLICATION_NOT_FOUND",
        )
        self.assertEqual(
            cross_model_replication_decision(
                operational_gate=False,
                replicated_count=2,
                required_count=1,
                primary_count=2,
            ),
            "CROSS_MODEL_REPLICATION_INCOMPLETE",
        )


if __name__ == "__main__":
    unittest.main()
