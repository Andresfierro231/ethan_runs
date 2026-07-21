import csv
import math
import tempfile
import unittest
from pathlib import Path

from tools.analyze import build_cooler_removal_model as crm


class CoolerRemovalModelTests(unittest.TestCase):
    def test_effectiveness_ntu_limits(self):
        self.assertEqual(crm.effectiveness_ntu(0.0, 0.5), 0.0)
        self.assertGreater(crm.effectiveness_ntu(2.0, 0.5), crm.effectiveness_ntu(1.0, 0.5))
        self.assertLessEqual(crm.effectiveness_ntu(5.0, 0.5), 1.0)

    def test_segmented_profile_conserves_energy(self):
        q_total, T_fluid_out, T_air_out, rows = crm.segmented_profile(
            total_ua_W_K=12.0,
            n_segments=8,
            mdot_fluid_kg_s=0.025,
            cp_fluid_J_kg_K=1500.0,
            mdot_air_kg_s=0.004,
            cp_air_J_kg_K=1007.0,
            T_fluid_in_K=360.0,
            T_air_in_K=300.0,
        )
        fluid_loss = 0.025 * 1500.0 * (360.0 - T_fluid_out)
        air_gain = 0.004 * 1007.0 * (T_air_out - 300.0)
        self.assertAlmostEqual(q_total, fluid_loss, places=9)
        self.assertAlmostEqual(q_total, air_gain, places=9)
        cumulative = [row["q_cumulative_W"] for row in rows]
        self.assertEqual(cumulative, sorted(cumulative))

    def test_candidate_definitions_are_one_parameter(self):
        rows = crm.candidate_definitions()
        self.assertEqual({row["candidate_id"] for row in rows}, {"HX_LUMPED_UA_NTU", "HX_SEGMENTED_UA_NTU_N4", "HX_SEGMENTED_UA_NTU_N8", "HX_SEGMENTED_UA_NTU_N16"})
        self.assertTrue(all(int(row["fitted_parameter_count"]) == 1 for row in rows))
        self.assertTrue(all(row["fit_split"] == "salt_2_only" for row in rows))

    def test_fit_parameters_do_not_fit_holdout_rows(self):
        rows = crm.fit_parameters()
        self.assertTrue(rows)
        self.assertEqual({row["fit_case_id"] for row in rows}, {"salt_2"})
        self.assertTrue(all("Salt3/Salt4" in row["fit_target_used"] for row in rows))

    def test_lumped_duty_regression_reproduces_agent438(self):
        rows = crm.duty_scorecard_rows()
        lumped = {(row["case_id"], row["split_role"]): row for row in rows if row["candidate_id"] == "HX_LUMPED_UA_NTU"}
        self.assertAlmostEqual(float(lumped[("salt_3", "validation")]["abs_error_W"]), 2.86910400386, places=6)
        self.assertEqual(lumped[("salt_3", "validation")]["duty_gate"], "pass")
        self.assertAlmostEqual(float(lumped[("salt_4", "holdout")]["abs_error_W"]), 7.50261861283, places=6)
        self.assertEqual(lumped[("salt_4", "holdout")]["duty_gate"], "pass")

    def test_runtime_audit_has_no_failures(self):
        self.assertNotIn("fail", {row["gate"] for row in crm.runtime_input_audit_rows()})
        forbidden = " ".join(row["forbidden_runtime_inputs"] for row in crm.runtime_input_audit_rows())
        self.assertIn("wallHeatFlux", forbidden)
        self.assertIn("imposed CFD cooler duty", forbidden)

    def test_default_package_emits_required_outputs(self):
        original_out = crm.OUT
        with tempfile.TemporaryDirectory() as tmp:
            crm.OUT = Path(tmp)
            try:
                summary = crm.build_package(run_fluid=False)
                self.assertFalse(summary["run_fluid"])
                required = [
                    "candidate_definitions.csv",
                    "fit_parameters.csv",
                    "duty_scorecard.csv",
                    "coupled_scorecard.csv",
                    "segmented_profile_diagnostics.csv",
                    "runtime_input_audit.csv",
                    "source_manifest.csv",
                    "model_comparison_decision.json",
                    "summary.json",
                    "README.md",
                ]
                for name in required:
                    self.assertTrue((crm.OUT / name).exists(), name)
                with (crm.OUT / "coupled_scorecard.csv").open(newline="", encoding="utf-8") as handle:
                    rows = list(csv.DictReader(handle))
                self.assertEqual(len(rows), 12)
                self.assertEqual({row["coupled_run_status"] for row in rows}, {"not_run_use_--run-fluid_on_compute_node"})
                self.assertIn("elapsed_s", rows[0])
            finally:
                crm.OUT = original_out


if __name__ == "__main__":
    unittest.main()
