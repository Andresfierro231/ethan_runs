#!/usr/bin/env python3
"""Tests for AGENT-538 source-envelope/property carryforward package."""

from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path

from tools.analyze import build_source_envelope_property_carryforward as builder


class SourceEnvelopePropertyCarryforwardTests(unittest.TestCase):
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
            "source_property_label_contract.csv",
            "future_scorecard_label_contract.csv",
            "scorecard_adoption_audit.csv",
            "final_scorecard_case_coverage_audit.csv",
            "blockers_research_paths_next_steps.csv",
            "source_manifest.csv",
            "summary.json",
        ]:
            self.assertTrue((out / name).exists(), name)
        summary = json.loads((out / "summary.json").read_text(encoding="utf-8"))
        self.assertEqual(summary["task"], "AGENT-538")
        self.assertEqual(summary["scientific_admission_change"], "none")
        self.assertEqual(summary["scheduler_action"], "none")
        self.assertGreaterEqual(summary["source_property_label_rows"], 90)
        self.assertEqual(summary["future_scorecard_contract_rows"], 6)
        self.assertGreater(summary["missing_source_property_coverage_rows"], 0)

    def test_label_contract_carries_source_and_property_fields(self) -> None:
        rows = self.rows(self.build_tmp() / "source_property_label_contract.csv")
        required = {
            "case_id",
            "section_or_segment",
            "property_mode",
            "property_mode_status",
            "property_sensitivity_label",
            "source_validity_envelope_status",
            "source_overlap_counts",
            "provenance_author_title",
            "source_paths",
        }
        self.assertTrue(required.issubset(rows[0]))
        self.assertTrue(any(row["property_mode"] == "jin_viscosity_parida_cp_santini_k" for row in rows))
        self.assertTrue(all(row["property_sensitivity_label"] for row in rows))
        self.assertTrue(all(row["source_validity_envelope_status"] for row in rows))
        self.assertTrue(any("outside" in row["source_overlap_counts"] for row in rows))

    def test_future_scorecard_contract_requires_labels(self) -> None:
        rows = self.rows(self.build_tmp() / "future_scorecard_label_contract.csv")
        packages = {row["target_package"] for row in rows}
        self.assertIn("final_predictive_scorecard_or_thesis_claim", packages)
        self.assertIn("branchwise_internal_HTC_bakeoff", packages)
        for row in rows:
            required = set(row["required_label_columns"].split(";"))
            self.assertTrue(
                {
                    "property_mode",
                    "property_sensitivity_label",
                    "source_validity_envelope_status",
                    "source_overlap_status",
                    "source_use_category",
                    "provenance_author_title",
                }.issubset(required),
                row,
            )
            self.assertIn("blocked_or_diagnostic", row["default_status_until_labels_present"])

    def test_current_final_shell_gap_is_explicit_not_admitted(self) -> None:
        rows = self.rows(self.build_tmp() / "scorecard_adoption_audit.csv")
        by_name = {Path(row["artifact"]).name: row for row in rows}
        final_shell = by_name["prediction_join_shell.csv"]
        self.assertEqual(final_shell["adoption_status"], "missing_labels")
        self.assertEqual(final_shell["has_property_sensitivity_label"], "no")
        self.assertEqual(final_shell["has_source_validity_envelope_status"], "no")

    def test_salt1_and_future_coverage_missing_is_conservative(self) -> None:
        rows = self.rows(self.build_tmp() / "final_scorecard_case_coverage_audit.csv")
        by_case = {row["case_key"]: row for row in rows}
        self.assertEqual(by_case["salt1_nominal"]["source_property_label_coverage"], "source_or_property_gate_missing")
        self.assertEqual(by_case["salt2_jin_nominal"]["source_property_label_coverage"], "source_property_labels_available")
        self.assertEqual(by_case["salt2_lo5q"]["source_property_label_coverage"], "source_or_property_gate_missing")
        self.assertEqual(by_case["salt3_q_insulation_matrix"]["source_property_label_coverage"], "source_or_property_gate_missing")
        self.assertEqual(by_case["val_salt2"]["source_property_label_coverage"], "source_or_property_gate_missing")

    def test_only_open_blockers_are_carried(self) -> None:
        rows = self.rows(self.build_tmp() / "blockers_research_paths_next_steps.csv")
        blocker_ids = {row["blocker_or_path"] for row in rows if row["category"] == "blocker_label"}
        self.assertEqual(
            blocker_ids,
            {
                "upcomer-onset-data-sparsity",
                "predictive-wall-test-section-submodels",
                "f6-friction-re-correction",
            },
        )
        self.assertNotIn("closure-qoi-mesh-gci", blocker_ids)
        self.assertNotIn("thermal-cfd-1d-parity", blocker_ids)


if __name__ == "__main__":
    unittest.main()
