import csv
import json
import tempfile
import unittest
from pathlib import Path

from tools.analyze.build_forward_v1_next_step_execution_from_overnight import (
    build_package,
)


class ForwardV1NextStepExecutionTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.out = Path(self.tmp.name) / "package"
        self.scheduler_rows = [
            {
                "JobID": "3293924",
                "JobName": "saltq_sel_cont",
                "State": "RUNNING",
                "ExitCode": "0:0",
                "Elapsed": "1-00:00:00",
                "Submit": "2026-07-13T17:03:55",
                "Start": "2026-07-13T17:03:56",
                "End": "Unknown",
                "NodeList": "c318-016",
            },
            {
                "JobID": "3295989",
                "JobName": "hyd_stage",
                "State": "PENDING",
                "ExitCode": "0:0",
                "Elapsed": "00:00:00",
                "Submit": "2026-07-14T17:56:40",
                "Start": "Unknown",
                "End": "Unknown",
                "NodeList": "None assigned",
            },
            {
                "JobID": "3295901",
                "JobName": "upc_pm5q",
                "State": "CANCELLED by 890970",
                "ExitCode": "0:0",
                "Elapsed": "00:00:00",
                "Submit": "2026-07-14T16:50:37",
                "Start": "None",
                "End": "2026-07-14T17:35:03",
                "NodeList": "None assigned",
            },
        ]

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def read_csv(self, name: str) -> list[dict[str, str]]:
        with (self.out / name).open(newline="") as handle:
            return list(csv.DictReader(handle))

    def test_summary_keeps_final_forward_v1_blocked(self) -> None:
        build_package(self.out, scheduler_rows=self.scheduler_rows)

        summary = json.loads((self.out / "summary.json").read_text())
        self.assertEqual(summary["task"], "AGENT-394")
        self.assertEqual(summary["final_forward_v1_status"], "blocked_no_final_score")
        self.assertEqual(summary["ag391_status"], "complete")
        self.assertEqual(summary["ag392_status"], "complete")
        self.assertEqual(
            summary["hx_fit_primary_split_id"],
            "declared_train_salt2_validate_salt3_holdout_salt4",
        )
        self.assertFalse(summary["native_cfd_outputs_mutated"])
        self.assertFalse(summary["registry_or_admission_state_mutated"])
        self.assertFalse(summary["scheduler_mutated"])

    def test_blocker_delta_names_unblocked_work_and_closed_gates(self) -> None:
        build_package(self.out, scheduler_rows=self.scheduler_rows)

        blockers = {row["blocker_id"]: row for row in self.read_csv("forward_v1_blocker_delta.csv")}
        self.assertIn("sensor_map_policy_refresh", blockers)
        self.assertEqual(
            blockers["sensor_map_policy_refresh"]["current_state"],
            "unblocked_for_documentation_work",
        )
        self.assertEqual(blockers["internal_nu_fit_gate"]["current_state"], "blocked")
        self.assertIn("cancelled", blockers["pm5_matched_pressure_upcomer"]["current_state"])

    def test_actions_and_lane_table_prevent_diagnostic_admission(self) -> None:
        build_package(self.out, scheduler_rows=self.scheduler_rows)

        actions = {row["action_id"]: row for row in self.read_csv("today_action_queue.csv")}
        self.assertEqual(actions["write_sensor_map_policy_refresh"]["can_start_now"], "yes")
        self.assertEqual(actions["rerun_forward_scorecard_after_gates"]["can_start_now"], "no")

        lanes = {row["lane_id"]: row for row in self.read_csv("setup_only_hx_and_test_section_action_table.csv")}
        self.assertEqual(
            lanes["AGENT-391_test_section_boundary_forms"]["admission_status"],
            "diagnostic_only",
        )
        self.assertIn(
            "realized cfd wallheatflux",
            lanes["AGENT-392_external_bc_segment_equivalents"]["do_not_use_if"].lower(),
        )


if __name__ == "__main__":
    unittest.main()
