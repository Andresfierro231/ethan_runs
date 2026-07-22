from __future__ import annotations

import argparse
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
from tools.analyze import build_1d_train_only_setup_uq_smoke_execution as builder


class TrainOnlySetupUqSmokeExecutionTests(unittest.TestCase):
    def test_runtime_manifest_marks_forbidden_fields_unused(self) -> None:
        rows = builder.runtime_manifest_rows()
        status, illegal = builder.runtime_lint_status(rows)
        self.assertEqual(status, "pass")
        self.assertEqual(illegal, [])
        forbidden = [row for row in rows if row["input_family"] == "forbidden_runtime_field"]
        self.assertGreaterEqual(len(forbidden), 8)
        self.assertTrue(all(row["train_scope"] == "none" for row in forbidden))

    def test_variant_specs_cover_runbook_families_without_admission(self) -> None:
        class MinorLosses:
            def __init__(self, major_loss_multiplier=1.0):
                self.major_loss_multiplier = major_loss_multiplier

        specs = builder.variant_specs(MinorLosses)
        families = {spec["input_family"] for spec in specs}
        self.assertIn("heater_source_fraction", families)
        self.assertIn("cooler_hx_strength", families)
        self.assertIn("ambient_temperature", families)
        self.assertIn("external_convection_hA", families)
        self.assertIn("radiation", families)
        self.assertIn("fluid_property_mode", families)
        self.assertIn("pressure_loss_terms", families)
        self.assertIn("sensor_projection", families)
        self.assertTrue(all("F6" not in spec["variant_id"] for spec in specs))

    def test_split_guardrail_audit_never_scores_protected_rows(self) -> None:
        rows = builder.split_guardrail_audit(True, "pass", skipped=3)
        by_id = {row["audit_id"]: row for row in rows}
        self.assertEqual(by_id["protected_scoring"]["status"], "pass")
        self.assertEqual(by_id["admission_release"]["status"], "pass")
        self.assertEqual(by_id["execution_completeness"]["status"], "incomplete")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--output-dir")
    _, remaining = parser.parse_known_args()
    sys.argv = [sys.argv[0], *remaining]
    unittest.main()
