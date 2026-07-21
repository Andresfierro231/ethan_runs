#!/usr/bin/env python3
"""Tests for AGENT-512 F6 LitRev hydraulic model-form ladder."""

from __future__ import annotations

import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_f6_litrev_hydraulic_model_form_ladder as builder  # noqa: E402


class F6LitRevHydraulicModelFormLadderTests(unittest.TestCase):
    def test_builder_outputs_summary_and_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            summary = builder.build_package(out)

            self.assertEqual(summary["task"], "AGENT-512")
            self.assertEqual(summary["pm5_ordinary_anchor_rows"], 0)
            self.assertEqual(summary["pm5_recirculation_diagnostic_rows"], 12)
            self.assertEqual(summary["production_closure"], "F3_shah_apparent")
            self.assertEqual(summary["promotion_allowed"], "no")
            self.assertGreaterEqual(summary["ladder_rows"], 10)
            self.assertGreaterEqual(summary["crosswalk_rows"], 8)
            self.assertEqual(summary["forbidden_shortcut_rows"], 6)

            for name in [
                "README.md",
                "hydraulic_model_form_ladder.csv",
                "anchor_first_decision_tree.csv",
                "litrev_hydraulic_crosswalk.csv",
                "forbidden_shortcuts.csv",
                "source_manifest.csv",
                "summary.json",
            ]:
                self.assertTrue((out / name).exists(), name)

            written = json.loads((out / "summary.json").read_text(encoding="utf-8"))
            self.assertEqual(written["scheduler_action"], "none")

    def test_ladder_contains_ranked_forms_worth_trying(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            builder.build_package(out)

            with (out / "hydraulic_model_form_ladder.csv").open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))

            forms = {row["model_form"] for row in rows}
            self.assertIn("Terminal anchor harvest and ordinary F6 gate", forms)
            self.assertIn("F6 phi(Re) hydraulic friction candidate", forms)
            self.assertIn("Reset-distance / redevelopment pressure loss", forms)
            self.assertIn("Named component/cluster/branch-apparent pressure losses", forms)
            self.assertIn("Recirculation-modeled section-effective loss / onset penalty", forms)
            self.assertIn("Boundary-layer development toggles", forms)

            by_form = {row["model_form"]: row for row in rows}
            self.assertEqual(by_form["F6 phi(Re) hydraulic friction candidate"]["research_decision"], "try_after_anchor_gate")
            self.assertEqual(by_form["One global friction multiplier"]["research_decision"], "forbidden")
            self.assertEqual(by_form["Boundary-layer development toggles"]["research_decision"], "diagnostic_ready_not_executable")

    def test_anchor_tree_preserves_anchor_first_sequence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            builder.build_package(out)

            with (out / "anchor_first_decision_tree.csv").open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))

            self.assertEqual([row["sequence"] for row in rows], ["1", "2", "3", "4", "5", "6"])
            self.assertEqual(rows[0]["decision"], "diagnostic_only")
            self.assertEqual(rows[1]["decision"], "wait_for_terminal_then_harvest")
            self.assertEqual(rows[2]["decision"], "run_F6_phi_Re_bakeoff")
            self.assertIn("RAF < 0.01", rows[2]["condition"])
            self.assertIn("Salt3", rows[3]["decision"])

    def test_forbidden_shortcuts_include_litrev_guardrails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            builder.build_package(out)

            with (out / "forbidden_shortcuts.csv").open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))

            shortcuts = {row["shortcut"] for row in rows}
            self.assertIn("One global friction multiplier", shortcuts)
            self.assertIn("Fully developed f_D=64/Re as default active closure", shortcuts)
            self.assertIn("Universal K for fittings", shortcuts)
            self.assertIn("Universal f_D/K/Nu in recirculating sections", shortcuts)
            self.assertTrue(all(row["forbidden_use"] for row in rows))

    def test_crosswalk_is_hydraulic_focused_and_provenanced(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            builder.build_package(out)

            with (out / "litrev_hydraulic_crosswalk.csv").open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))

            families = {row["model_family"] for row in rows}
            self.assertIn("f6_phi_re", families)
            self.assertIn("developing_redeveloping_friction", families)
            self.assertIn("component_cluster_k", families)
            self.assertIn("upcomer_recirculation_rule", families)
            self.assertTrue(all(row["provenance_author_title"] for row in rows))
            self.assertTrue(all(row["current_ethan_evidence"] for row in rows))


if __name__ == "__main__":
    unittest.main()
