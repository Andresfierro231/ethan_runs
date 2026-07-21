import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.analyze import build_test_section_wall_fluid_coupling_candidate as study


class TestSectionWallFluidCouplingCandidateTests(unittest.TestCase):
    def test_selected_source_is_agent511_salt2_only_lambda_zero(self):
        selection = study.selected_heater_source()
        self.assertEqual(selection["selection_status"], "selected_from_salt2_only")
        self.assertEqual(float(selection["heater_lambda"]), 0.0)
        self.assertIn("HS1_salt2_fit_heater_source_shift", selection.get("selected_candidate_id", ""))
        self.assertIn("lam_0p00", selection.get("selected_candidate_id", ""))

    def test_series_resistance_is_bounded_by_direct_external_loss(self):
        loss = study.series_resistance_loss_W(
            T_bulk_K=500.0,
            ambient_K=300.0,
            hA_W_K=2.0,
            coverage_multiplier=1.0,
            segment_length_m=1.0,
            R_i_prime_K_m_W=0.1,
            R_wall_prime_K_m_W=0.2,
        )
        self.assertGreater(loss, 0.0)
        self.assertLessEqual(loss, 2.0 * (500.0 - 300.0))
        self.assertEqual(
            study.series_resistance_loss_W(
                T_bulk_K=300.0,
                ambient_K=300.0,
                hA_W_K=2.0,
                coverage_multiplier=1.0,
                segment_length_m=1.0,
                R_i_prime_K_m_W=0.1,
                R_wall_prime_K_m_W=0.2,
            ),
            0.0,
        )

    def test_contracts_cover_two_coolers_three_cases_with_one_series_test_section_row(self):
        rows = study.scenario_contract_rows()
        self.assertEqual(len(rows), 2 * 3)
        self.assertEqual({row["case_id"] for row in rows}, {"salt_2", "salt_3", "salt_4"})
        self.assertEqual({row["cooler_candidate_id"] for row in rows}, set(study.COOLER_IDS))
        self.assertEqual({row["series_coupling_role_count"] for row in rows}, {1})
        for row in rows:
            payload = json.loads(row["scenario_json"])
            series = [role for role in payload["role_rows"] if role.get("coupling_model") == study.COUPLING_MODEL]
            self.assertEqual(len(series), 1)
            self.assertEqual(series[0]["parent_segment"], "left_upper_vertical")
            self.assertEqual(series[0]["role"], "test_section")
            self.assertEqual(series[0]["drive_selector"], "fluid_segment_bulk_temperature_for_v1_setup_mode")

    def test_runtime_audit_names_forbidden_inputs_and_requires_execution(self):
        audit = study.runtime_input_audit_rows(study.scenario_contract_rows(), run_fluid=False)
        self.assertEqual([row["gate"] for row in audit], ["pass", "pass", "pass", "pending"])
        text = " ".join(row["forbidden_runtime_input"] + " " + row["evidence"] for row in audit)
        self.assertIn("realized wallHeatFlux", text)
        self.assertIn("validation/holdout probe temperatures", text)
        self.assertIn("Salt2", text)
        self.assertIn("series-coupled role rows", text)

    def test_default_coupled_rows_are_pending_srun(self):
        rows, probes = study.coupled_scorecard_rows(
            study.scenario_contract_rows(),
            run_fluid=False,
            timeout_seconds=study.DEFAULT_TIMEOUT_SECONDS,
        )
        self.assertEqual({row["coupled_run_status"] for row in rows}, {"not_run_submit_background_srun"})
        self.assertEqual({row["coupled_gate"] for row in rows}, {"pending_background_fluid_score"})
        self.assertEqual(probes, [])

    def test_admission_requires_validation_and_holdout_all_metrics(self):
        rows = [
            {
                "candidate_id": "candidate",
                "case_id": "salt_3",
                "split_role": "validation",
                "coupled_run_status": "completed",
                "mdot_error_pct": "0.1",
                "tp_rmse_K": "99.0",
                "tw_rmse_K": "99.0",
                "all_probe_rmse_K": "99.0",
            }
        ]
        deltas = study.coupled_delta_rows(rows)
        self.assertEqual(deltas[0]["score_gate"], "fail")
        runtime = [
            {"gate": "pass"},
            {"gate": "pass"},
            {"gate": "pass"},
            {"gate": "pass"},
        ]
        admission = study.candidate_admission_review_rows(deltas, runtime)
        self.assertEqual(admission[0]["admission_decision"], "not_admitted")
        self.assertIn("holdout", admission[0]["blocking_reasons"])

    def test_local_behavior_is_limited_to_test_section_and_adjacent_upcomer_probes(self):
        probes = [
            {
                "candidate_id": "c",
                "case_id": "salt_3",
                "split_role": "validation",
                "sensor": "TP5",
                "kind": "TP",
                "predicted_K": "442",
                "target_K": "464",
                "error_K": "-22",
                "abs_error_K": "22",
                "prediction_source_segment": "test_section",
                "prediction_source_fraction": "1",
            },
            {
                "candidate_id": "c",
                "case_id": "salt_3",
                "split_role": "validation",
                "sensor": "TW8",
                "kind": "TW",
                "predicted_K": "438",
                "target_K": "462",
                "error_K": "-24",
                "abs_error_K": "24",
                "prediction_source_segment": "left_upper_vertical",
                "prediction_source_fraction": "0.5",
            },
            {
                "candidate_id": "c",
                "case_id": "salt_3",
                "split_role": "validation",
                "sensor": "TW10",
                "kind": "TW",
                "predicted_K": "580",
                "target_K": "399",
                "error_K": "181",
                "abs_error_K": "181",
                "prediction_source_segment": "cooled_incline_hx_active",
                "prediction_source_fraction": "0.5",
            },
        ]
        rows = study.local_test_section_behavior_rows(probes)
        self.assertEqual([row["sensor"] for row in rows], ["TP5", "TW8"])
        self.assertEqual({row["observed_behavior"] for row in rows}, {"underpredicts_local_temperature"})

    def test_build_emits_required_outputs_in_tempdir(self):
        original_out = study.OUT
        with tempfile.TemporaryDirectory() as tmp:
            study.OUT = Path(tmp) / "out"
            try:
                summary = study.build(run_fluid=False)
                self.assertEqual(summary["task"], study.TASK)
                required = [
                    "wall_candidate_definitions.csv",
                    "candidate_definitions.csv",
                    "scenario_contracts.csv",
                    "runtime_input_audit.csv",
                    "coupled_scorecard.csv",
                    "coupled_delta_vs_m3.csv",
                    "probe_error_localization.csv",
                    "local_test_section_behavior.csv",
                    "candidate_admission_review.csv",
                    "background_run_contract.csv",
                    "blocker_decision.json",
                    "source_manifest.csv",
                    "summary.json",
                    "README.md",
                ]
                for name in required:
                    self.assertTrue((study.OUT / name).exists(), name)
                with (study.OUT / "scenario_contracts.csv").open(newline="", encoding="utf-8") as handle:
                    rows = list(csv.DictReader(handle))
                self.assertEqual(len(rows), 2 * 3)
            finally:
                study.OUT = original_out


if __name__ == "__main__":
    unittest.main()
