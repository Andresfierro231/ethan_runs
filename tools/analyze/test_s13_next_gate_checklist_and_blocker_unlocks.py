from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from tools.analyze import build_s13_next_gate_checklist_and_blocker_unlocks as builder


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class S13NextGateChecklistTests(unittest.TestCase):
    def test_stats_distinguish_surface_preflight_from_production_release(self) -> None:
        stats = builder.source_stats()
        self.assertEqual(stats["case_count"], 3)
        self.assertEqual(stats["geometry_seed_ready_count"], 3)
        self.assertEqual(stats["seeded_surface_preflight_ready_count"], 3)
        self.assertEqual(stats["seeded_production_cv_released_count"], 0)
        self.assertTrue(stats["seeded_interface_faces_exists"])
        self.assertTrue(stats["seeded_wall_faces_exists"])

    def test_checklist_preserves_no_internal_nu_residual_absorption(self) -> None:
        rows = builder.build_next_gate_checklist(builder.source_stats())
        joined = " ".join(row["forbidden_inputs_or_actions"] for row in rows)
        self.assertIn("internal Nu", joined)
        self.assertTrue(any(row["gate_id"] == "S13-G2-seeded-surface-input-preflight" for row in rows))
        self.assertTrue(any(row["current_status"] == "blocked" for row in rows))

    def test_blocker_queue_prioritizes_coordination_and_surface_preflight(self) -> None:
        queue = builder.build_blocker_queue(builder.source_stats())
        self.assertEqual(queue[0]["blocker_id"], "board_overlap_s13_rerun_rows")
        self.assertEqual(queue[1]["blocker_id"], "seeded_surface_input_preflight")
        self.assertTrue(any(row["blocker_id"] == "Q_wall_source_sign_cp_release" for row in queue))

    def test_build_package_writes_outputs_and_guardrails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "pkg"
            payload = builder.build_package(out)
            summary = payload["summary"]
            self.assertFalse(summary["scheduler_action"])
            self.assertFalse(summary["native_output_mutation"])
            self.assertFalse(summary["residual_absorbed_into_internal_nu"])
            for name in [
                "README.md",
                "summary.json",
                "next_gate_checklist.csv",
                "s13_geometry_evidence_summary.csv",
                "blocker_unlock_queue.csv",
                "heat_path_alignment_guardrails.csv",
                "no_mutation_guardrails.csv",
                "source_manifest.csv",
            ]:
                self.assertTrue((out / name).exists(), name)
            heat_rows = read_rows(out / "heat_path_alignment_guardrails.csv")
            lanes = {row["heat_path_lane"] for row in heat_rows}
            self.assertIn("internal_Nu", lanes)
            self.assertIn("residual", lanes)


if __name__ == "__main__":
    unittest.main()
