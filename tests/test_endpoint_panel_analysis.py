from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def report(effect_a: float, p_a: float, effect_b: float, p_b: float) -> dict:
    return {
        "operational_gate": True,
        "contrasts": {
            "property_order": {
                "normalized_excess_disagreement": effect_a,
                "normalized_excess_ci95": [effect_a - 0.01, effect_a + 0.01],
                "normalized_energy_permutation_p": p_a,
                "normalized_energy_holm_p": min(1.0, p_a * 2),
                "confirmed": effect_a >= 0.05,
            },
            "additional_keyword_order_given_reversed_properties": {
                "normalized_excess_disagreement": effect_b,
                "normalized_excess_ci95": [effect_b - 0.01, effect_b + 0.01],
                "normalized_energy_permutation_p": p_b,
                "normalized_energy_holm_p": min(1.0, p_b * 2),
                "confirmed": effect_b >= 0.05,
            },
        },
    }


class EndpointPanelAnalysisTests(unittest.TestCase):
    def test_panel_summary_requires_and_corrects_all_six_tests(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            inputs = []
            for index, item in enumerate(
                (
                    report(0.10, 0.001, 0.08, 0.01),
                    report(0.04, 0.02, 0.03, 0.03),
                    report(0.06, 0.04, 0.02, 0.05),
                )
            ):
                path = root / f"report_{index}.json"
                path.write_text(json.dumps(item), encoding="utf-8")
                inputs.extend(("--report", f"deployment_{index}", str(path)))
            json_output = root / "summary.json"
            markdown_output = root / "summary.md"
            command = [
                sys.executable,
                str(ROOT / "src/summarize_endpoint_panel.py"),
                *inputs,
                "--json-output",
                str(json_output),
                "--markdown-output",
                str(markdown_output),
            ]
            completed = subprocess.run(
                command,
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            summary = json.loads(json_output.read_text(encoding="utf-8"))
            panel_values = [
                item["panel_holm_p"]
                for deployment in summary["deployments"].values()
                for item in deployment["contrasts"].values()
            ]
            self.assertEqual(len(panel_values), 6)
            self.assertEqual(min(panel_values), 0.006)
            self.assertIn("Deployments are not independent", markdown_output.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
