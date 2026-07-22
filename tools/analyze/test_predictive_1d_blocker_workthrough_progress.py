import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from tools.analyze import build_predictive_1d_blocker_workthrough_progress as builder


class Predictive1DBlockerWorkthroughProgressTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.out = Path(cls.tmp.name) / "predictive_workthrough"
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

    def test_summary_keeps_release_freeze_and_score_closed(self):
        self.assertEqual(
            self.summary["decision"],
            "predictive_1d_blockers_progressed_no_release_no_freeze",
        )
        self.assertEqual(self.summary["top_remaining_blocker"], "row_specific_source_property_release")
        self.assertEqual(self.summary["final_score_values"], 0)
        for key in [
            "source_property_release",
            "Qwall_release",
            "candidate_freeze",
            "coefficient_admission",
            "validation_holdout_external_scoring",
            "s11_s12_s13_s15_s6_trigger",
        ]:
            self.assertFalse(self.summary[key], key)

    def test_blocker_progress_has_expected_lanes(self):
        rows = self.read_rows("blocker_progress_matrix.csv")
        self.assertEqual(len(rows), 6)
        blockers = {row["blocker"]: row for row in rows}
        self.assertIn("row_specific_source_property_release", blockers)
        self.assertIn("S13_bulk_integral_residual_complete_energy_balance", blockers)
        self.assertIn("PASSIVE_H2_runtime_wall_operator", blockers)
        self.assertEqual(blockers["row_specific_source_property_release"]["release_or_score_allowed"], "False")
        self.assertIn("F_wall_mean", blockers["S13_bulk_integral_residual_complete_energy_balance"]["evidence"])
        self.assertEqual(
            blockers["S13_bulk_integral_residual_complete_energy_balance"]["latest_status"],
            "residual_contract_complete_fail_closed",
        )
        self.assertIn(
            "residual_value_released_rows=0",
            blockers["S13_bulk_integral_residual_complete_energy_balance"]["evidence"],
        )

    def test_execution_gates_allow_only_diagnostic_or_separate_runtime_work(self):
        gates = {row["gate"]: row for row in self.read_rows("execution_readiness_gates.csv")}
        self.assertEqual(gates["candidate_source_property_release"]["status"], "blocked")
        self.assertEqual(gates["s13_heat_partition_model_direction"]["status"], "diagnostic_pass")
        self.assertIn("residual_value_released_rows=0", gates["s13_heat_partition_model_direction"]["evidence"])
        self.assertEqual(gates["passive_h2_runtime_implementation"]["status"], "ready_to_launch_separate_row")
        self.assertEqual(gates["freeze_or_final_score"]["status"], "closed_no_candidate")

    def test_next_work_queue_moves_past_completed_s13_contract(self):
        rows = self.read_rows("next_work_queue.csv")
        self.assertEqual(rows[0]["task"], "claim/finish H2 runtime implementation row")
        self.assertEqual(
            rows[1]["task"],
            "S13 throughflow endpoint/cp/property residual-input harvest preflight",
        )

    def test_source_property_requests_are_all_not_release_ready(self):
        rows = self.read_rows("source_property_request_table.csv")
        self.assertEqual(len(rows), 4)
        self.assertEqual({row["release_ready"] for row in rows}, {"False"})
        self.assertEqual({row["protected_row_release"] for row in rows}, {"False"})

    def test_methodology_and_summary_files_exist(self):
        self.assertTrue((self.out / "methodology_and_assumptions.md").exists())
        with (self.out / "summary.json").open(encoding="utf-8") as handle:
            summary = json.load(handle)
        self.assertFalse(summary["native_solver_outputs_mutated"])
        self.assertFalse(summary["fluid_or_external_edit"])
        self.assertFalse(summary["residual_absorbed_into_internal_Nu"])


if __name__ == "__main__":
    unittest.main()
