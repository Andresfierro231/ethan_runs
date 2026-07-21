#!/usr/bin/env python3
"""Tests for AGENT-466 downcomer unlock and blocker roadmap."""

from __future__ import annotations

import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_downcomer_internal_nu_unlock_and_blocker_roadmap as builder  # noqa: E402


class DowncomerInternalNuUnlockTests(unittest.TestCase):
    def test_builder_outputs_expected_blocked_downcomer_decision(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            summary = builder.build_package(out)

            self.assertEqual(summary["task"], "AGENT-466")
            self.assertEqual(summary["blocker_decision"], "not_resolved_downcomer_narrowed")
            self.assertEqual(summary["downcomer_fit_admissible_rows"], 0)
            self.assertGreaterEqual(summary["future_studies_documented"], 10)

            for filename in [
                "README.md",
                "downcomer_admission_gate.csv",
                "downcomer_policy_decision.csv",
                "litrev_gate_application.csv",
                "future_studies_and_blockers.csv",
                "blocker_resolution_decision.csv",
                "source_manifest.csv",
                "summary.json",
            ]:
                self.assertTrue((out / filename).exists(), filename)

            written = json.loads((out / "summary.json").read_text(encoding="utf-8"))
            self.assertEqual(written["downcomer_fit_admissible_rows"], 0)

    def test_downcomer_requires_all_hard_gates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            builder.build_package(out)

            with (out / "downcomer_admission_gate.csv").open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(len(rows), 1)
            row = rows[0]
            self.assertEqual(row["canonical_leg_id"], "downcomer_right_vertical")
            self.assertEqual(row["admission_decision"], "not_admitted_downcomer_policy_sign_recirculation_mesh")
            self.assertIn("sign_heat_balance", row["blocking_reason"])
            self.assertIn("recirculation", row["blocking_reason"])
            self.assertIn("mesh_gci", row["blocking_reason"])

    def test_future_studies_cover_all_current_open_blockers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            summary = builder.build_package(out)

            self.assertEqual(summary["open_blockers_covered"], summary["open_blockers_total"])
            with (out / "future_studies_and_blockers.csv").open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            blockers = {row["blocker_id"] for row in rows}
            for blocker in summary["open_blockers"]:
                self.assertIn(blocker, blockers)

    def test_upcomer_and_cooler_are_routed_away_from_ordinary_nu_fit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            builder.build_package(out)

            with (out / "future_studies_and_blockers.csv").open(newline="", encoding="utf-8") as handle:
                rows = {row["study_id"]: row for row in csv.DictReader(handle)}
            self.assertIn("upcomer_hybrid_onset_classification", rows)
            self.assertIn("single-stream", rows["upcomer_hybrid_onset_classification"]["do_not_do_guardrail"])
            self.assertIn("cooler_hx_boundary_residual_separation", rows)
            self.assertIn("internal Nu", rows["cooler_hx_boundary_residual_separation"]["do_not_do_guardrail"])


if __name__ == "__main__":
    unittest.main()
