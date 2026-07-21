"""Tests for the final forward-v1 scorecard gate."""

from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path

from tools.analyze.build_final_forward_v1_scorecard_gate import build_package


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class FinalForwardV1ScorecardGateTests(unittest.TestCase):
    def test_current_evidence_produces_blocked_final_gate(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            out = Path(tmp)
            summary = build_package(out)

            self.assertEqual(summary["final_forward_v1_status"], "blocked_no_go_final_forward_v1_not_admitted")
            self.assertGreaterEqual(summary["blocking_gate_count"], 3)
            self.assertFalse(summary["native_solver_outputs_mutated"])
            self.assertFalse(summary["runtime_leakage_admitted"])
            self.assertFalse(summary["thermal_internal_nu_fit_allowed"])
            self.assertFalse(summary["h1_proxy_final_closure_admitted"])
            self.assertFalse(summary["imposed_cooler_final_predictive_evidence_admitted"])
            self.assertFalse(summary["diagnostic_thermal_rows_final_closure_admitted"])
            self.assertFalse(summary["fitted_internal_nu_rows_consumable"])
            self.assertTrue(summary["baseline_literature_default_internal_nu_required"])
            self.assertTrue(summary["cfd_pp_onset_candidates_required_for_internal_nu_reopen"])
            self.assertTrue(summary["therm_reconstr_matched_plane_extraction_required_for_internal_nu_reopen"])
            self.assertEqual(summary["upcomer_section_effective_nu_label"], "Nu_section_effective_upcomer_diagnostic")
            self.assertEqual(summary["upcomer_section_effective_nu_use"], "diagnostic_validation_only")
            self.assertEqual(summary["current_split"], "salt_2=train;salt_3=validation;salt_4=holdout")

            gates = {row["gate_id"]: row for row in read_csv(out / "forward_v1_gate_checklist.csv")}
            self.assertEqual(gates["input_contract_and_split"]["gate_status"], "pass_locked")
            self.assertEqual(gates["hydraulic_localized_h1"]["gate_status"], "blocked_proxy_only")
            self.assertEqual(gates["thermal_internal_nu"]["gate_status"], "blocked_no_fit_rows")
            self.assertEqual(gates["upcomer_section_effective_nu_diagnostic"]["gate_status"], "diagnostic_validation_only_no_fit")
            self.assertIn("Nu_section_effective_upcomer_diagnostic", gates["upcomer_section_effective_nu_diagnostic"]["admitted_now"])
            self.assertEqual(gates["cfd_pp_admitted_training_data"]["gate_group"], "cfd_admission")
            self.assertIn("Do not call aggregate fixed-K H1", gates["hydraulic_localized_h1"]["do_not_claim"])
            self.assertIn("Do not consume fitted internal Nu rows", gates["thermal_internal_nu"]["do_not_claim"])

    def test_score_rows_remain_diagnostic_proxy_rows(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            out = Path(tmp)
            build_package(out)
            rows = read_csv(out / "forward_v1_score_rows.csv")

            self.assertEqual(len(rows), 6)
            self.assertEqual({row["score_status"] for row in rows}, {"diagnostic_h1_proxy_not_final_forward_v1"})
            self.assertEqual({row["thermal_fit_used"] for row in rows}, {"false"})

            parsed = json.loads((out / "summary.json").read_text(encoding="utf-8"))
            self.assertEqual(parsed["corrected_q_rows_admitted"], 0)

    def test_waiting_inputs_prepare_future_scorecard_consumption(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            out = Path(tmp)
            build_package(out)
            waiting = {row["input_id"]: row for row in read_csv(out / "scorecard_inputs_waiting_on_agents.csv")}

            for input_id in {
                "cfd_pp_admitted_case_inventory",
                "localized_h1_hydraulic_scorecard",
                "setup_only_boundary_hx_outputs",
                "thermal_internal_nu_admission",
                "upcomer_section_effective_nu_diagnostic",
                "result_intake_contract",
            }:
                self.assertIn(input_id, waiting)

            self.assertIn("keep salt_2/salt_3/salt_4 split", waiting["cfd_pp_admitted_case_inventory"]["how_scorecard_will_consume"])
            self.assertIn("forbidden_runtime_inputs_used=false", waiting["setup_only_boundary_hx_outputs"]["expected_fields_or_contract"])
            self.assertIn("fit_eligible", waiting["thermal_internal_nu_admission"]["expected_fields_or_contract"])
            self.assertIn("never as a fitted Nu/HTC/UA row", waiting["upcomer_section_effective_nu_diagnostic"]["how_scorecard_will_consume"])

    def test_internal_nu_dependency_blockers_keep_fit_gate_closed(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            out = Path(tmp)
            build_package(out)
            blockers = {row["dependency_id"]: row for row in read_csv(out / "internal_nu_dependency_blockers.csv")}

            for dependency_id in {
                "no_fit_admissible_internal_nu_rows",
                "nu_section_effective_upcomer_diagnostic_label",
                "cfd_pp_onset_candidates",
                "therm_reconstr_matched_plane_extraction",
                "mesh_time_uncertainty_for_recirculation_metrics",
                "thermal_residual_ownership_guardrail",
            }:
                self.assertIn(dependency_id, blockers)

            self.assertIn("baseline/literature/default internal Nu", blockers["no_fit_admissible_internal_nu_rows"]["scorecard_policy_until_resolved"])
            self.assertIn("Re 150, 200, 250", blockers["cfd_pp_onset_candidates"]["required_evidence_before_reopen"])
            self.assertIn("Upcomer inlet/mid/outlet planes", blockers["therm_reconstr_matched_plane_extraction"]["required_evidence_before_reopen"])
            self.assertIn("diagnostic/validation-only", blockers["nu_section_effective_upcomer_diagnostic_label"]["scorecard_policy_until_resolved"])

    def test_requested_output_names_are_written(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            out = Path(tmp)
            build_package(out)
            self.assertTrue((out / "forward_v1_gate_checklist.csv").exists())
            self.assertTrue((out / "scorecard_inputs_waiting_on_agents.csv").exists())
            self.assertTrue((out / "internal_nu_dependency_blockers.csv").exists())
            self.assertTrue((out / "final_forward_v1_gate_table.csv").exists())


if __name__ == "__main__":
    unittest.main()
