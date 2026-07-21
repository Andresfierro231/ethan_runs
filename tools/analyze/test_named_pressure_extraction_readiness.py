#!/usr/bin/env python3
"""Tests for AGENT-523 named pressure extraction readiness."""

from __future__ import annotations

import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_named_pressure_extraction_readiness as builder  # noqa: E402


class NamedPressureExtractionReadinessTests(unittest.TestCase):
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
            "named_pressure_readiness.csv",
            "next_pressure_extraction_queue.csv",
            "pressure_readiness_summary.csv",
            "source_manifest.csv",
            "summary.json",
        ]:
            self.assertTrue((out / name).exists(), name)
        summary = json.loads((out / "summary.json").read_text(encoding="utf-8"))
        self.assertEqual(summary["task"], "AGENT-523")
        self.assertEqual(summary["scientific_admission_change"], "none")
        self.assertEqual(summary["scheduler_action"], "none")
        self.assertEqual(summary["production_closure"], "F3_shah_apparent")
        self.assertEqual(summary["named_pressure_rows"], 33)
        self.assertEqual(summary["fit_ready_rows"], 0)
        self.assertEqual(summary["queue_rows"], 5)

    def test_readiness_rows_preserve_diagnostic_status(self) -> None:
        rows = self.rows(self.build_tmp() / "named_pressure_readiness.csv")
        self.assertEqual(len(rows), 33)
        statuses = {row["readiness_status"] for row in rows}
        self.assertNotIn("fit_ready_candidate", statuses)
        self.assertIn("diagnostic_or_section_effective_only", statuses)
        self.assertIn("extraction_required_component_or_cluster", statuses)
        self.assertIn("extraction_required_branch_or_straight", statuses)
        for row in rows:
            self.assertTrue(row["blocking_fields"], row)
            self.assertEqual(row["allowed_use_now"], "diagnostic_pressure_ledger_or_extraction_design")
            self.assertIn("universal_K", row["forbidden_use"])
            self.assertIn("hidden_global_friction_multiplier", row["forbidden_use"])

    def test_queue_covers_pressure_repair_lanes(self) -> None:
        rows = self.rows(self.build_tmp() / "next_pressure_extraction_queue.csv")
        queue_items = {row["queue_item"] for row in rows}
        self.assertEqual(
            queue_items,
            {
                "raw_two_tap_connector_and_component_repair",
                "pressure_and_velocity_basis_finalization",
                "recirculation_mask_and_section_effective_policy",
                "same_qoi_mesh_time_uncertainty_attachment",
                "reset_development_basis_to_Fluid_API_contract",
            },
        )
        by_item = {row["queue_item"]: row for row in rows}
        self.assertIn("centerline_tap_length", by_item["raw_two_tap_connector_and_component_repair"]["required_fields"])
        self.assertIn("static_pressure_basis", by_item["pressure_and_velocity_basis_finalization"]["required_fields"])
        self.assertIn("RAF", by_item["recirculation_mask_and_section_effective_policy"]["required_fields"])
        self.assertIn("mesh_family", by_item["same_qoi_mesh_time_uncertainty_attachment"]["required_fields"])
        self.assertIn("reset_type", by_item["reset_development_basis_to_Fluid_API_contract"]["required_fields"])

    def test_summary_and_manifest_are_complete(self) -> None:
        out = self.build_tmp()
        summary_rows = self.rows(out / "pressure_readiness_summary.csv")
        categories = {row["category"]: int(row["count"]) for row in summary_rows}
        self.assertEqual(categories["total_named_pressure_rows"], 33)
        self.assertEqual(categories["fit_ready_candidate"], 0)
        self.assertEqual(categories["diagnostic_or_section_effective_only"], 24)
        manifest = self.rows(out / "source_manifest.csv")
        self.assertEqual(len(manifest), 10)
        self.assertTrue(all(row["exists"] == "True" for row in manifest))


if __name__ == "__main__":
    unittest.main()
