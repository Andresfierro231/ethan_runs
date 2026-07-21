#!/usr/bin/env python3
"""Tests for the AGENT-424 setup/BC/model-form synthesis report builder."""

from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from tools.analyze import build_setup_bc_model_error_synthesis_report as builder


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class SetupBcModelErrorSynthesisReportTests(unittest.TestCase):
    def test_builder_writes_expected_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp) / "report"
            builder.build(out_dir)

            expected = [
                "README.md",
                "report.md",
                "case_setup_summary.csv",
                "boundary_model_matrix.csv",
                "mode_error_summary.csv",
                "case_mode_error_matrix.csv",
                "heater_cooler_model_form_errors.csv",
                "setup_predictive_variant_status.csv",
                "assumptions_and_guardrails.csv",
                "source_manifest.csv",
                "summary.json",
            ]
            for name in expected:
                self.assertTrue((out_dir / name).exists(), name)

    def test_headline_error_numbers_are_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp) / "report"
            builder.build(out_dir)
            rows = {row["mode_id"]: row for row in read_csv(out_dir / "mode_error_summary.csv")}

            self.assertEqual(
                rows["M2_cfd_heater_test_section_cooler_pressure_root"][
                    "mean_abs_mdot_error_pct"
                ],
                "10.397",
            )
            self.assertEqual(
                rows["M2_cfd_heater_test_section_cooler_pressure_root"][
                    "mean_all_probe_rmse_K"
                ],
                "26.972",
            )
            self.assertEqual(
                rows["M3_cfd_heater_cooler_pressure_root"]["mean_all_probe_rmse_K"],
                "18.023",
            )

    def test_guardrails_separate_diagnostic_from_predictive_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp) / "report"
            builder.build(out_dir)
            matrix = read_csv(out_dir / "boundary_model_matrix.csv")
            realized_wallflux_modes = [
                row for row in matrix if row["uses_realized_cfd_wallHeatFlux_runtime"] == "yes"
            ]
            self.assertGreaterEqual(len(realized_wallflux_modes), 4)
            for row in realized_wallflux_modes:
                self.assertIn("diagnostic", row["predictivity_class"])

            variant_fields = {
                row["field"] for row in read_csv(out_dir / "setup_predictive_variant_status.csv")
            }
            self.assertIn("external_boundary_coverage_multiplier_by_parent_segment", variant_fields)
            self.assertIn("external_boundary_drive_selector_by_parent_segment", variant_fields)


if __name__ == "__main__":
    unittest.main()
