"""Tests for forward-v1 +/-5Q and hydraulic tap-refresh delta."""

from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path

from tools.analyze.build_forward_v1_pm5_hydraulic_delta import build_package


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class ForwardV1Pm5HydraulicDeltaTests(unittest.TestCase):
    def test_summary_keeps_no_go_and_no_training_expansion(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            out = Path(tmp)
            summary = build_package(out)

            self.assertEqual(summary["final_forward_v1_status"], "blocked_no_go_final_forward_v1_not_admitted")
            self.assertEqual(summary["pm5_harvest_rows"], 4)
            self.assertEqual(summary["pm5_closure_fit_admissible_terminal_gate_rows"], 4)
            self.assertEqual(summary["independent_training_expansion_rows"], 0)
            self.assertEqual(summary["component_fit_admissible_rows"], 0)
            self.assertFalse(summary["h1_faithful_launchable"])
            self.assertFalse(summary["forward_v1_admitted"])
            self.assertFalse(summary["native_solver_outputs_mutated"])
            self.assertFalse(summary["registry_mutated"])
            self.assertFalse(summary["external_fluid_modified"])
            self.assertFalse(summary["scheduler_action_taken"])

    def test_delta_rows_capture_landed_evidence_and_blockers(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            out = Path(tmp)
            build_package(out)
            rows = {row["delta_id"]: row for row in read_csv(out / "forward_v1_gate_delta_after_pm5_hydraulic.csv")}

            for delta_id in {
                "pm5_terminal_harvest",
                "pm5_boundary_heat_targets",
                "pm5_f6_onset_candidates",
                "hyd_tap_centerline_refresh",
                "forward_v1_status_after_delta",
            }:
                self.assertIn(delta_id, rows)

            self.assertIn("does not expand independent", rows["pm5_terminal_harvest"]["forward_v1_effect"])
            self.assertIn("Do not add +/-5Q rows", rows["pm5_terminal_harvest"]["do_not_claim"])
            self.assertIn("Do not use CFD cooler duty", rows["pm5_boundary_heat_targets"]["do_not_claim"])
            self.assertIn("Do not fit component/cluster K", rows["hyd_tap_centerline_refresh"]["do_not_claim"])

    def test_thesis_table_has_citable_numbers(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            out = Path(tmp)
            build_package(out)
            rows = {row["table_id"]: row for row in read_csv(out / "thesis_pm5_hydraulic_progress_table.csv")}

            self.assertIn("rows=4", rows["pm5_terminal_harvest"]["numbers_to_cite"])
            self.assertIn("independent_training_expansion_rows=0", rows["pm5_terminal_harvest"]["numbers_to_cite"])
            self.assertIn("cooling_branch_total_removal_mean_W_range=", rows["pm5_heat_targets"]["numbers_to_cite"])
            self.assertIn("component_fit_admissible_rows=0", rows["tap_length_refresh"]["numbers_to_cite"])

    def test_next_actions_remain_gate_driven(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            out = Path(tmp)
            build_package(out)
            actions = {row["action_id"]: row for row in read_csv(out / "next_gate_actions_after_pm5_hydraulic.csv")}

            self.assertEqual(
                set(actions),
                {
                    "pm5_matched_pressure_upcomer_metrics",
                    "perturbation_split_policy",
                    "f6_score_after_admitted_re_variation",
                    "boundary_hx_score_targets",
                    "forward_v1_delta_refresh",
                },
            )
            self.assertIn("no runtime predictive leakage", actions["pm5_matched_pressure_upcomer_metrics"]["acceptance"])
            self.assertIn("no thermal fitting", actions["f6_score_after_admitted_re_variation"]["acceptance"])
            self.assertIn("without realized wallHeatFlux", actions["boundary_hx_score_targets"]["acceptance"])

    def test_outputs_written(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            out = Path(tmp)
            build_package(out)
            for name in {
                "README.md",
                "forward_v1_gate_delta_after_pm5_hydraulic.csv",
                "thesis_pm5_hydraulic_progress_table.csv",
                "next_gate_actions_after_pm5_hydraulic.csv",
                "source_manifest.csv",
                "summary.json",
            }:
                self.assertTrue((out / name).exists(), name)

            parsed = json.loads((out / "summary.json").read_text(encoding="utf-8"))
            self.assertEqual(parsed["task"], "AGENT-362")


if __name__ == "__main__":
    unittest.main()
