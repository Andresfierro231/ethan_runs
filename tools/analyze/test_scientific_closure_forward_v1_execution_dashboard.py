"""Tests for the scientific closure / forward-v1 execution dashboard."""

from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path

from tools.analyze.build_scientific_closure_forward_v1_execution_dashboard import build_package


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class ScientificClosureForwardV1DashboardTests(unittest.TestCase):
    def test_summary_preserves_forward_v1_no_go_guardrails(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            out = Path(tmp)
            summary = build_package(out)

            self.assertEqual(summary["final_forward_v1_status"], "blocked_no_go_final_forward_v1_not_admitted")
            self.assertGreater(summary["blocking_gate_count"], 0)
            self.assertEqual(summary["corrected_q_rows_admitted"], 0)
            self.assertFalse(summary["fitted_internal_nu_rows_consumable"])
            self.assertFalse(summary["native_solver_outputs_mutated"])
            self.assertFalse(summary["external_fluid_modified"])
            self.assertFalse(summary["generated_indexes_touched"])

    def test_workstreams_include_all_plan_lanes(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            out = Path(tmp)
            build_package(out)
            rows = {row["workstream_id"]: row for row in read_csv(out / "workstream_execution_dashboard.csv")}

            for workstream_id in {
                "terminal_cfd_admission",
                "upcomer_matched_plane_extraction",
                "internal_nu_reopen_gate",
                "f6_hydraulic_screen",
                "setup_only_boundary_api",
                "forward_v1_scorecard_refresh",
                "candidate_inventory",
            }:
                self.assertIn(workstream_id, rows)

            self.assertIn("corrected-Q rows still need terminal admission", rows["terminal_cfd_admission"]["pending_or_blocked"])
            self.assertIn("Fluid still lacks", rows["setup_only_boundary_api"]["pending_or_blocked"])
            self.assertIn("H1 and localized fixed-K remain diagnostic", rows["f6_hydraulic_screen"]["admitted_now"])

    def test_gate_requirements_forbid_shortcuts(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            out = Path(tmp)
            build_package(out)
            rows = {row["requirement_id"]: row for row in read_csv(out / "gate_landing_requirements.csv")}

            self.assertIn("terminal_cfd_admission", rows)
            self.assertIn("matched_plane_metrics", rows)
            self.assertIn("f6_re_variation", rows)
            self.assertIn("setup_only_boundary_outputs", rows)
            self.assertIn("internal_nu_reopen", rows)

            self.assertIn("live scheduler state", rows["terminal_cfd_admission"]["forbidden_shortcut"])
            self.assertIn("existing proxy rows", rows["matched_plane_metrics"]["forbidden_shortcut"])
            self.assertIn("thermal terms", rows["f6_re_variation"]["forbidden_shortcut"])
            self.assertIn("realized wallHeatFlux", rows["setup_only_boundary_outputs"]["forbidden_shortcut"])
            self.assertIn("Nu_section_effective_upcomer_diagnostic", rows["internal_nu_reopen"]["forbidden_shortcut"])

    def test_refresh_queue_names_next_artifacts(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            out = Path(tmp)
            build_package(out)
            rows = {row["queue_id"]: row for row in read_csv(out / "forward_v1_refresh_queue.csv")}

            self.assertEqual(set(rows), {"Q1_terminal_cfd", "Q2_matched_planes", "Q3_f6_hydraulics", "Q4_boundary_api", "Q5_forward_v1"})
            self.assertIn("corrected_q_terminal_admission_refresh.csv", rows["Q1_terminal_cfd"]["output_to_refresh"])
            self.assertIn("upcomer_nu_admission_refresh.csv", rows["Q2_matched_planes"]["output_to_refresh"])
            self.assertIn("f6_phi_re_hydraulic_scorecard.csv", rows["Q3_f6_hydraulics"]["output_to_refresh"])
            self.assertIn("setup_only_boundary_hx_outputs.csv", rows["Q4_boundary_api"]["output_to_refresh"])
            self.assertIn("forward_v1_residual_attribution_scorecard.csv", rows["Q5_forward_v1"]["output_to_refresh"])

    def test_outputs_are_written(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            out = Path(tmp)
            build_package(out)
            for name in {
                "README.md",
                "workstream_execution_dashboard.csv",
                "gate_landing_requirements.csv",
                "thesis_evidence_register.csv",
                "forward_v1_refresh_queue.csv",
                "source_manifest.csv",
                "summary.json",
            }:
                self.assertTrue((out / name).exists(), name)

            parsed = json.loads((out / "summary.json").read_text(encoding="utf-8"))
            self.assertEqual(parsed["task"], "AGENT-348")


if __name__ == "__main__":
    unittest.main()
