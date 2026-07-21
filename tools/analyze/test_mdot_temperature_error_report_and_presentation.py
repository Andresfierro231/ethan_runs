#!/usr/bin/env python3
"""Tests for AGENT-420 mdot/temperature report and presentation package."""

from __future__ import annotations

import csv
import json
import unittest

from tools.analyze import build_mdot_temperature_error_report_and_presentation as build


class MdotTemperatureReportPresentationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        build.build()
        cls.out = build.OUT

    def read_csv(self, name: str) -> list[dict[str, str]]:
        with (self.out / name).open(newline="", encoding="utf-8") as handle:
            return list(csv.DictReader(handle))

    def test_summary_counts_and_guardrails(self) -> None:
        summary = json.loads((self.out / "summary.json").read_text(encoding="utf-8"))
        self.assertEqual(summary["task"], "AGENT-420")
        self.assertEqual(summary["boundary_mode_rows"], 4)
        self.assertEqual(summary["case_mode_rows"], 9)
        self.assertEqual(summary["slide_count"], 12)
        self.assertFalse(summary["native_cfd_outputs_mutated"])
        self.assertFalse(summary["external_cfd_modeling_tools_mutated"])

    def test_report_contains_core_conclusions(self) -> None:
        report = (self.out / "mdot_temperature_error_report.md").read_text(encoding="utf-8")
        self.assertIn("M2 has mean absolute mdot", report)
        self.assertIn("test section cannot simply be", report)
        self.assertIn("Pearson r=", report)
        self.assertIn("setup-only", report)

    def test_presentation_has_speaker_notes_and_figures(self) -> None:
        deck = (self.out / "presentation_outline.md").read_text(encoding="utf-8")
        self.assertEqual(deck.count("## Slide "), 12)
        self.assertEqual(deck.count("Speaker notes:"), 12)
        self.assertEqual(deck.count("Suggested figure:"), 12)

    def test_boundary_mode_table_preserves_diagnostic_labels(self) -> None:
        rows = {row["mode_id"]: row for row in self.read_csv("boundary_mode_performance_summary.csv")}
        self.assertEqual(rows["M1_full_cfd_segment_heat_flux_pressure_root"]["predictivity_class"], "diagnostic_cfd_informed_upper_bound")
        self.assertEqual(rows["M1b_full_cfd_segment_heat_flux_fixed_mdot"]["uses_cfd_mdot_runtime"], "yes")
        self.assertEqual(rows["M2_cfd_heater_test_section_cooler_pressure_root"]["uses_realized_cfd_wallHeatFlux_runtime"], "yes")

    def test_figure_plan_points_to_existing_correlation_figure(self) -> None:
        rows = self.read_csv("suggested_figure_plan.csv")
        first = rows[0]
        self.assertEqual(first["status"], "available_existing")
        self.assertIn("mdot_error_vs_probe_rmse.svg", first["source_or_creation_note"])


if __name__ == "__main__":
    unittest.main()
