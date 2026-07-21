#!/usr/bin/env python3
"""Tests for AGENT-518 research-studies roadmap package."""

from __future__ import annotations

import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_research_studies_roadmap_and_today_start as builder  # noqa: E402


class ResearchStudiesRoadmapTests(unittest.TestCase):
    def build_tmp(self) -> Path:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        out = Path(tmp.name)
        builder.build_package(out)
        return out

    def read_csv(self, path: Path) -> list[dict[str, str]]:
        with path.open(newline="", encoding="utf-8") as handle:
            return list(csv.DictReader(handle))

    def test_builder_outputs_required_files_and_summary(self) -> None:
        out = self.build_tmp()
        expected = {
            "README.md",
            "study_priority_matrix.csv",
            "today_start_ledger.csv",
            "multi_agent_campaign_sequence.csv",
            "thesis_roadmap.md",
            "handoff_tomorrow.md",
            "source_manifest.csv",
            "summary.json",
        }
        self.assertTrue(expected.issubset({path.name for path in out.iterdir()}))

        summary = json.loads((out / "summary.json").read_text(encoding="utf-8"))
        self.assertEqual(summary["task"], "AGENT-518")
        self.assertEqual(summary["production_closure"], "F3_shah_apparent")
        self.assertEqual(summary["scientific_admission_change"], "none")
        self.assertEqual(summary["scheduler_action"], "none")
        self.assertEqual(summary["ordinary_f6_scoreable_rows"], 0)
        self.assertGreaterEqual(summary["study_rows"], 10)
        self.assertGreaterEqual(summary["today_rows"], 6)
        self.assertGreaterEqual(summary["campaign_rows"], 6)

    def test_preserves_current_open_blockers(self) -> None:
        out = self.build_tmp()
        summary = json.loads((out / "summary.json").read_text(encoding="utf-8"))
        self.assertEqual(
            summary["open_blockers"],
            [
                "f6-friction-re-correction",
                "predictive-wall-test-section-submodels",
                "upcomer-onset-data-sparsity",
            ],
        )

    def test_every_study_has_provenance_gate_and_guardrail(self) -> None:
        rows = self.read_csv(self.build_tmp() / "study_priority_matrix.csv")
        self.assertTrue(rows)
        for row in rows:
            self.assertTrue(row["provenance"], row["study_id"])
            self.assertTrue(row["acceptance_gate"], row["study_id"])
            self.assertTrue(row["guardrail"], row["study_id"])
            self.assertTrue(row["thesis_value"], row["study_id"])

    def test_priority_matrix_contains_required_lanes(self) -> None:
        rows = self.read_csv(self.build_tmp() / "study_priority_matrix.csv")
        study_ids = {row["study_id"] for row in rows}
        for required in {
            "terminal_anchor_and_f6_gate",
            "source_envelope_refresh",
            "property_mode_carryforward",
            "reset_development_and_named_pressure",
            "cfd_validity_on_every_reduction",
            "wall_temperature_shape_physics",
            "heat_loss_separation_and_radiation_bound",
            "conditional_internal_htc_bakeoff",
            "instrumentation_pressure_and_thermal",
            "rom_archive_schema_future_only",
        }:
            self.assertIn(required, study_ids)

    def test_pm5_misuse_and_forbidden_shortcuts_are_explicitly_blocked(self) -> None:
        out = self.build_tmp()
        studies = self.read_csv(out / "study_priority_matrix.csv")
        terminal = next(row for row in studies if row["study_id"] == "terminal_anchor_and_f6_gate")
        self.assertIn("Do not fit ordinary F6 from PM5", terminal["guardrail"])
        self.assertIn("RAF < 0.01", terminal["acceptance_gate"])
        self.assertIn("RMF < 0.01", terminal["acceptance_gate"])

        campaign_text = (out / "multi_agent_campaign_sequence.csv").read_text(encoding="utf-8")
        self.assertIn("no one global friction multiplier", campaign_text)
        self.assertIn("no universal K", campaign_text)
        self.assertIn("PM5 remains diagnostic", campaign_text)

    def test_today_ledger_is_actionable_without_mutating_solver_state(self) -> None:
        rows = self.read_csv(self.build_tmp() / "today_start_ledger.csv")
        self.assertEqual([row["sequence"] for row in rows], ["1", "2", "3", "4", "5", "6"])
        joined = "\n".join(row["do_not_do"] for row in rows)
        self.assertIn("no solver", joined)
        self.assertIn("do not harvest non-terminal jobs", joined)
        self.assertIn("no universal K", joined)
        self.assertIn("do not edit reports/thesis_dossier", joined)

    def test_markdown_handoff_and_thesis_roadmap_include_guardrails(self) -> None:
        out = self.build_tmp()
        handoff = (out / "handoff_tomorrow.md").read_text(encoding="utf-8")
        thesis = (out / "thesis_roadmap.md").read_text(encoding="utf-8")
        self.assertIn("Open First", handoff)
        self.assertIn("Do Not Do", handoff)
        self.assertIn("Claims Not Yet Allowed", thesis)
        self.assertIn("No ordinary F6 closure from PM5 rows", thesis)
        self.assertIn("No final predictive claim", thesis)


if __name__ == "__main__":
    unittest.main()
