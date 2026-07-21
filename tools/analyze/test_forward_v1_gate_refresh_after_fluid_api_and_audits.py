"""Tests for the forward-v1 gate refresh after Fluid API and audit evidence."""

from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path

from tools.analyze.build_forward_v1_gate_refresh_after_fluid_api_and_audits import build_package


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class ForwardV1GateRefreshTests(unittest.TestCase):
    def test_summary_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            summary = build_package(Path(tmp))

            self.assertEqual(summary["final_forward_v1_status"], "blocked_no_go_final_forward_v1_not_admitted")
            self.assertFalse(summary["forward_v1_admitted"])
            self.assertTrue(summary["fluid_reset_development_api_implemented"])
            self.assertFalse(summary["h1_launchable_after_fluid_api"])
            self.assertEqual(summary["pm5_independent_training_expansion_rows"], 0)
            self.assertFalse(summary["salt1_affects_current_salt234_score_split"])
            self.assertFalse(summary["native_solver_outputs_mutated"])
            self.assertFalse(summary["registry_mutated"])
            self.assertFalse(summary["scheduler_action_taken"])
            self.assertFalse(summary["external_fluid_modified_by_this_task"])

    def test_gate_rows_encode_updated_fluid_api_and_pending_pm5(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            out = Path(tmp)
            build_package(out)
            rows = {row["gate_id"]: row for row in read_csv(out / "forward_v1_gate_checklist_refreshed.csv")}

            self.assertEqual(rows["fluid_reset_development_api"]["refreshed_status"], "api_implemented_evidence_blocked")
            self.assertIn("reset/development K", rows["fluid_reset_development_api"]["current_evidence"])
            self.assertEqual(rows["pm5_matched_pressure_upcomer_metrics"]["refreshed_status"], "pending_terminal")
            self.assertIn("job 3295901", rows["pm5_matched_pressure_upcomer_metrics"]["current_evidence"])
            self.assertIn("Do not infer F6", rows["pm5_matched_pressure_upcomer_metrics"]["do_not_claim"])

    def test_residual_skeleton_has_required_formulas(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            out = Path(tmp)
            build_package(out)
            rows = {row["residual_lane"]: row for row in read_csv(out / "forward_v1_residual_attribution_skeleton.csv")}

            self.assertEqual(rows["hydraulic_mdot"]["formula"], "e_mdot = mdot_1d - mdot_cfd")
            self.assertEqual(rows["sensor_temperature"]["formula"], "e_T(sensor) = T_1d(sensor) - T_cfd(sensor)")
            self.assertEqual(rows["boundary_hx_heat"]["formula"], "e_Q(role) = Q_1d(role) - Q_cfd_reference(role)")
            self.assertIn("Do not consume diagnostic upcomer Nu", rows["internal_nu_thermal"]["do_not_claim"])

    def test_perturbation_policy_does_not_expand_training(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            out = Path(tmp)
            build_package(out)
            rows = {row["row_id"]: row for row in read_csv(out / "perturbation_split_policy_next.csv")}

            for row_id in ["salt2_lo5q", "salt2_hi5q", "salt4_lo5q", "salt4_hi5q"]:
                self.assertEqual(rows[row_id]["independent_training_expansion_now"], "no")
            self.assertEqual(rows["salt1_hi10q"]["family"], "salt1_training_context")
            self.assertEqual(rows["salt1_hi10q"]["current_use"], "training_admissible_perturbed_q")
            self.assertEqual(rows["salt1_hi10q"]["independent_training_expansion_now"], "outside_current_salt234_final_score_split")

    def test_outputs_written(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            out = Path(tmp)
            build_package(out)
            for name in {
                "README.md",
                "forward_v1_gate_checklist_refreshed.csv",
                "forward_v1_scorecard_input_contract_next.csv",
                "forward_v1_blocking_gate_burndown.csv",
                "forward_v1_residual_attribution_skeleton.csv",
                "perturbation_split_policy_next.csv",
                "math_assumptions_theory.md",
                "source_manifest.csv",
                "summary.json",
            }:
                self.assertTrue((out / name).exists(), name)

            parsed = json.loads((out / "summary.json").read_text(encoding="utf-8"))
            self.assertEqual(parsed["task"], "AGENT-366")


if __name__ == "__main__":
    unittest.main()
