from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from smoke_official_provider import (  # noqa: E402
    PROVIDERS,
    evaluate_gate,
    sanitized_completion,
)
from run_sob_metamorphic import validate_smoke_record  # noqa: E402
from evaluate_sob_decomposed_confirmation import (  # noqa: E402
    validate_decomposed_manifest,
)


class OfficialProviderPanelTests(unittest.TestCase):
    def test_provider_defaults_use_documented_official_endpoints(self) -> None:
        self.assertEqual(
            PROVIDERS["kimi"]["base_url"], "https://api.moonshot.cn/v1"
        )
        self.assertEqual(
            PROVIDERS["deepseek"]["base_url"], "https://api.deepseek.com"
        )
        self.assertEqual(PROVIDERS["xai"]["base_url"], "https://api.x.ai/v1")
        self.assertEqual(
            PROVIDERS["gemini"]["base_url"],
            "https://generativelanguage.googleapis.com/v1beta/openai",
        )

    def test_amended_freeze_has_one_active_deepseek_manifest(self) -> None:
        freeze = json.loads(
            (ROOT / "protocol/sob_official_panel_freeze.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(
            freeze["status"],
            "AMENDED_DEEPSEEK_ONLY_PENDING_OFFICIAL_ENDPOINT_GATE",
        )
        self.assertTrue(freeze["amended_before_any_official_provider_calls"])
        self.assertEqual(len(freeze["manifests"]), 1)
        self.assertEqual(len(freeze["superseded_candidate_manifests"]), 3)

        expected_record_ids = None
        expected_conditions = None
        seen_models: set[str] = set()
        for item in freeze["manifests"]:
            manifest = json.loads(
                (ROOT / item["path"]).read_text(encoding="utf-8")
            )
            self.assertTrue(manifest["frozen_before_api_calls"])
            self.assertEqual(
                manifest["analysis_stage"],
                "preregistered_official_deepseek_replication",
            )
            self.assertEqual(manifest["expected_requests"], 3000)
            self.assertEqual(manifest["repeats_per_variant"], 5)
            self.assertEqual(len(manifest["record_ids"]), 200)
            self.assertEqual(len(manifest["conditions"]), 15)
            self.assertEqual(manifest["base_url"], item["base_url"])
            self.assertEqual(manifest["model_alias"], item["model_alias"])
            self.assertTrue(manifest["requires_smoke_record"])
            self.assertEqual(
                manifest["thinking_mode"],
                "omitted_provider_default_enabled_regular_request_effort_high",
            )
            self.assertEqual(manifest["response_format"], "omitted_text_mode")
            self.assertEqual(manifest["tools"], "omitted")
            seen_models.add(manifest["model_alias"])

            if expected_record_ids is None:
                expected_record_ids = manifest["record_ids"]
                expected_conditions = manifest["conditions"]
            else:
                self.assertEqual(manifest["record_ids"], expected_record_ids)
                self.assertEqual(manifest["conditions"], expected_conditions)

        self.assertEqual(seen_models, {"deepseek-v4-flash"})
        self.assertEqual(
            {
                item["model_alias"]
                for item in freeze["superseded_candidate_manifests"]
            },
            {"kimi-k3", "grok-4.3", "gemini-3.6-flash"},
        )

    def test_antigravity_and_gateway_multi_agent_are_excluded(self) -> None:
        protocol = (
            ROOT / "protocol/25_official_endpoint_model_panel.md"
        ).read_text(encoding="utf-8")
        self.assertIn("Antigravity managed agent is excluded", protocol)
        self.assertIn("grok-4.20-multi-agent-*", protocol)
        self.assertIn("scope was narrowed to one official replication", protocol)
        self.assertIn("Do not add another model after inspecting", protocol)

    def test_smoke_gate_requires_catalog_three_successes_and_stable_model(
        self,
    ) -> None:
        record = {
            "catalog": {"requested_model_present": True},
            "runs": [
                {
                    "status": "ok",
                    "response": {"returned_model": "deepseek-v4-flash"},
                }
                for _ in range(3)
            ],
        }
        gate = evaluate_gate(record)
        self.assertTrue(gate["gate_passed"])
        self.assertEqual(gate["stable_returned_model"], "deepseek-v4-flash")

        record["runs"][2]["response"]["returned_model"] = "other-model"
        self.assertFalse(evaluate_gate(record)["gate_passed"])
        record["catalog"]["requested_model_present"] = False
        self.assertFalse(evaluate_gate(record)["gate_passed"])

    def test_smoke_metadata_hashes_content_without_retaining_it(self) -> None:
        sanitized = sanitized_completion(
            {
                "id": "response-id",
                "model": "deepseek-v4-flash",
                "system_fingerprint": "fp_test",
                "choices": [
                    {
                        "finish_reason": "stop",
                        "message": {
                            "content": "API_OK",
                            "reasoning_content": "private reasoning",
                        },
                    }
                ],
                "usage": {"prompt_tokens": 1, "completion_tokens": 2},
            }
        )
        self.assertTrue(sanitized["content_exact_api_ok"])
        self.assertNotIn("content", sanitized)
        self.assertNotIn("reasoning_content", sanitized)
        self.assertEqual(sanitized["system_fingerprint"], "fp_test")

    def test_formal_runner_accepts_only_a_passed_matching_smoke_record(
        self,
    ) -> None:
        import tempfile

        record = {
            "provider": "deepseek",
            "base_url": "https://api.deepseek.com",
            "requested_model": "deepseek-v4-flash",
            "gate": {
                "gate_passed": True,
                "stable_returned_model": "deepseek-v4-flash",
            },
        }
        manifest = {"smoke_provider": "deepseek"}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "smoke.json"
            path.write_text(json.dumps(record), encoding="utf-8")
            returned_model, digest = validate_smoke_record(
                path,
                manifest=manifest,
                base_url="https://api.deepseek.com",
                model_alias="deepseek-v4-flash",
            )
            self.assertEqual(returned_model, "deepseek-v4-flash")
            self.assertEqual(len(digest), 64)

            record["gate"]["gate_passed"] = False
            path.write_text(json.dumps(record), encoding="utf-8")
            with self.assertRaises(ValueError):
                validate_smoke_record(
                    path,
                    manifest=manifest,
                    base_url="https://api.deepseek.com",
                    model_alias="deepseek-v4-flash",
                )

    def test_decomposed_evaluator_accepts_official_deepseek_stage(self) -> None:
        validate_decomposed_manifest(
            {"analysis_stage": "preregistered_official_deepseek_replication"}
        )
        validate_decomposed_manifest(
            {"analysis_stage": "preregistered_decomposed_contrast_confirmation"}
        )
        with self.assertRaises(ValueError):
            validate_decomposed_manifest({"analysis_stage": "unrelated_analysis"})


if __name__ == "__main__":
    unittest.main()
