#!/usr/bin/env python3
"""Tests for the two-tap blocker roadmap package."""

from __future__ import annotations

import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_two_tap_blocker_roadmap as builder  # noqa: E402


class TwoTapBlockerRoadmapTests(unittest.TestCase):
    def build_tmp(self) -> Path:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        out = Path(tmp.name)
        builder.build_package(out)
        return out

    def rows(self, path: Path) -> list[dict[str, str]]:
        with path.open(newline="", encoding="utf-8") as handle:
            return list(csv.DictReader(handle))

    def test_outputs_and_summary(self) -> None:
        out = self.build_tmp()
        for name in [
            "README.md",
            "blocker_matrix.csv",
            "research_path_matrix.csv",
            "next_step_queue.csv",
            "admission_decision_rules.csv",
            "roadmap_summary.csv",
            "source_manifest.csv",
            "summary.json",
        ]:
            self.assertTrue((out / name).exists(), name)
        summary = json.loads((out / "summary.json").read_text(encoding="utf-8"))
        self.assertEqual(summary["task"], "TODO-TWO-TAP-BLOCKER-ROADMAP")
        self.assertEqual(summary["blocker_rows"], 7)
        self.assertEqual(summary["research_paths"], 6)
        self.assertEqual(summary["next_steps"], 7)
        self.assertEqual(summary["admission_rules"], 7)
        self.assertEqual(summary["sampling_jobs_launched"], 0)
        self.assertEqual(summary["ordinary_admissions"], 0)
        self.assertEqual(summary["scientific_admission_change"], "none")

    def test_blocker_matrix_represents_all_launch_gates(self) -> None:
        rows = self.rows(self.build_tmp() / "blocker_matrix.csv")
        self.assertEqual(len(rows), 7)
        gates = {row["gate"] for row in rows}
        self.assertEqual(
            gates,
            {
                "task_scope",
                "target_taps_resolved",
                "pressure_velocity_basis",
                "straight_reference_component_isolation",
                "recirculation_metrics",
                "same_qoi_uncertainty",
                "F6_separation",
            },
        )
        straight = next(row for row in rows if row["gate"] == "straight_reference_component_isolation")
        self.assertIn("negative K_local", straight["why_blocks_admission"])
        self.assertIn("without clipping", straight["acceptance_signal"])
        recirc = next(row for row in rows if row["gate"] == "recirculation_metrics")
        self.assertIn("RAF < 0.01", recirc["acceptance_signal"])
        self.assertIn("RMF < 0.01", recirc["acceptance_signal"])

    def test_research_paths_are_decision_complete_and_guarded(self) -> None:
        rows = self.rows(self.build_tmp() / "research_path_matrix.csv")
        path_ids = {row["research_path_id"] for row in rows}
        self.assertEqual(path_ids, {"PATH-A", "PATH-B", "PATH-C", "PATH-D", "PATH-E", "PATH-F"})
        path_a = next(row for row in rows if row["research_path_id"] == "PATH-A")
        self.assertIn("lower_leg__s04/right_leg__s00", path_a["method"])
        self.assertIn("7915/7618/10000", path_a["method"])
        self.assertIn("No login-node heavy OpenFOAM run", path_a["guardrail"])
        path_f = next(row for row in rows if row["research_path_id"] == "PATH-F")
        self.assertIn("No F6 fit", path_f["guardrail"])
        self.assertIn("no component-K admission", path_f["guardrail"])

    def test_next_step_queue_is_ordered_and_non_mutating_until_claimed(self) -> None:
        rows = self.rows(self.build_tmp() / "next_step_queue.csv")
        self.assertEqual([row["step_id"] for row in rows], [f"STEP-{index:02d}" for index in range(1, 8)])
        self.assertEqual(rows[0]["title"], "Claim staged-copy cfd-pp row")
        self.assertIn("before any sampling", rows[0]["action"])
        sampler = next(row for row in rows if row["step_id"] == "STEP-02")
        self.assertIn("lower_leg__s04 and right_leg__s00", sampler["action"])
        self.assertIn("Do not substitute left_lower_leg__s00", sampler["do_not_do"])
        admission = next(row for row in rows if row["step_id"] == "STEP-07")
        self.assertIn("Do not overwrite AGENT-530", admission["do_not_do"])
        self.assertIn("fit F6", admission["do_not_do"])

    def test_admission_rules_forbid_shortcuts(self) -> None:
        rows = self.rows(self.build_tmp() / "admission_decision_rules.csv")
        shortcuts = " ".join(row["forbidden_shortcut"] for row in rows)
        self.assertIn("infer endpoint pressure", shortcuts)
        self.assertIn("clip negative K_local", shortcuts)
        self.assertIn("reuse unrelated GCI", shortcuts)
        f6 = next(row for row in rows if row["rule_id"] == "RULE-07")
        self.assertEqual(f6["decision"], "route_to_separate_nonrecirculating_anchor_task")


if __name__ == "__main__":
    unittest.main()
