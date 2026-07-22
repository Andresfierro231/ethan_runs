import csv
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools.analyze import build_s13_bulk_integral_heat_partition_feasibility as builder


class S13BulkIntegralHeatPartitionFeasibilityTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.out = Path(cls.tmp.name) / "bulk_heat_partition"
        cls.patch = mock.patch.object(builder, "OUT", cls.out)
        cls.patch.start()
        cls.summary = builder.build()

    @classmethod
    def tearDownClass(cls):
        cls.patch.stop()
        cls.tmp.cleanup()

    def read_rows(self, name):
        with (self.out / name).open(newline="", encoding="utf-8") as handle:
            return list(csv.DictReader(handle))

    def test_summary_selects_bulk_partition_without_fit(self):
        self.assertEqual(
            self.summary["decision"],
            "bulk_integral_heat_partition_feasible_diagnostic_no_fit_residual_next",
        )
        self.assertEqual(self.summary["case_count"], 3)
        self.assertTrue(self.summary["bulk_integral_partition_diagnostic_ready"])
        self.assertFalse(self.summary["same_basis_energy_residual_computable_now"])
        self.assertEqual(
            self.summary["recommended_next_model_direction"],
            "bulk_integral_heat_partition_then_residual_complete_open_cv",
        )
        self.assertFalse(self.summary["coefficient_admission"])
        self.assertFalse(self.summary["admission_allowed"])

    def test_partition_rows_have_stable_fwall(self):
        rows = self.read_rows("bulk_integral_heat_partition_rows.csv")
        self.assertEqual(len(rows), 3)
        self.assertEqual({row["case_id"] for row in rows}, {"salt_2", "salt_3", "salt_4"})
        for row in rows:
            f_wall = float(row["F_wall_Qwall_over_source"])
            self.assertGreater(f_wall, 0.13)
            self.assertLess(f_wall, 0.14)
            self.assertEqual(row["partition_observation"], "stable_candidate_bulk_integral_partition")
            self.assertEqual(row["production_use_allowed_now"], "False")

    def test_partition_summary_reports_stable_diagnostic_candidate(self):
        rows = {row["metric"]: row for row in self.read_rows("partition_stability_summary.csv")}
        fwall = rows["F_wall_Qwall_over_source"]
        self.assertLess(float(fwall["range"]), 0.005)
        self.assertEqual(fwall["stability_status"], "stable_diagnostic_candidate")
        self.assertLess(float(fwall["qwall_medium_fine_max_spread_percent"]), 1.0)
        self.assertIn("no coefficient", fwall["claim_boundary"])

    def test_energy_residual_is_blocked_by_same_basis_terms(self):
        rows = self.read_rows("energy_residual_feasibility.csv")
        self.assertEqual(len(rows), 3)
        self.assertEqual({row["can_compute_same_basis_energy_residual_now"] for row in rows}, {"False"})
        self.assertEqual(
            {row["current_feasibility_disposition"] for row in rows},
            {"partition_residual_support_ready_but_energy_residual_not_computable"},
        )
        self.assertTrue(all("cp" in row["next_required_evidence"] for row in rows))

    def test_model_ladder_prioritizes_heat_partition(self):
        rows = self.read_rows("bulk_integral_model_form_ladder.csv")
        self.assertEqual(rows[0]["model_direction"], "bulk_integral_heat_partition")
        self.assertEqual(rows[0]["fit_allowed_now"], "False")
        self.assertEqual(rows[2]["model_direction"], "throughflow_plus_recirc_exchange_cell")
        self.assertEqual(rows[2]["current_evidence_status"], "defer_proxy_mesh_sensitive")

    def test_progression_gate_blocks_fit_and_opens_residual_next(self):
        gates = {row["gate"]: row for row in self.read_rows("progression_gate.csv")}
        self.assertEqual(gates["bulk_integral_partition_stability"]["status"], "diagnostic_pass")
        self.assertEqual(gates["cp_property_release"]["status"], "fail_closed")
        self.assertEqual(gates["exchange_proxy_mesh_stability"]["status"], "fail_closed")
        self.assertEqual(gates["predictive_1d_next_step"]["status"], "open_next_contract_only")

    def test_guardrails_false(self):
        with (self.out / "summary.json").open(encoding="utf-8") as handle:
            summary = json.load(handle)
        for key in [
            "source_property_release",
            "Qwall_release",
            "coefficient_admission",
            "production_harvest_allowed",
            "admission_allowed",
            "scheduler_action",
            "native_solver_outputs_mutated",
            "registry_or_admission_mutated",
            "validation_holdout_external_scoring",
            "s11_s12_s13_s15_s6_trigger",
            "generated_docs_index_refreshed",
        ]:
            self.assertFalse(summary[key], key)


if __name__ == "__main__":
    unittest.main()
