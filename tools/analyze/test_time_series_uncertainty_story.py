#!/usr/bin/env python3
"""Tests for build_time_series_uncertainty_story.py."""

from __future__ import annotations

import csv
import sys
import tempfile
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.analyze import build_time_series_uncertainty_story as builder


def sample_row(case_slug: str, verdict: str = "steady", group: str = "mdot") -> dict[str, str]:
    series = "lower (heater)"
    unit = "kg/s"
    if group == "temperature":
        series = "probe 1 (0.887519 -0.245426 0)"
        unit = "K"
    elif group == "wall_temperature":
        series = "wall T (spatial mean)"
        unit = "K"
    elif group == "heat":
        series = "total_Q"
        unit = "W"
    return {
        "case_slug": case_slug,
        "fluid": "salt2",
        "group": group,
        "series": series,
        "unit": unit,
        "n_window": "11",
        "t_start": "100.0",
        "t_end": "200.0",
        "verdict": verdict,
        "rel_drift_over_window": "0.001",
        "drift_ratio": "0.5",
        "near_zero_mean": "False",
        "trend_resolved": "False",
        "osc_mean": "10.0",
        "osc_rmse_about_mean": "0.5",
        "osc_rmse_about_trend": "0.4",
        "osc_var_about_mean": "0.25",
        "osc_peak_to_peak": "1.0",
        "osc_cov": "0.05",
        "fit_slope": "0.002",
        "fit_r2": "0.1",
        "fit_slope_se": "0.001",
        "fit_t_stat": "2.0",
        "unc_tau_int": "1.0",
        "unc_n_eff": "11.0",
        "unc_sem_naive": "0.02",
        "unc_sem_corrected": "0.1",
        "unc_rel_sem_corrected": "0.01",
    }


class TimeSeriesUncertaintyStoryTests(unittest.TestCase):
    def test_screening_excludes_live_and_not_steady_rows(self) -> None:
        rows = [
            sample_row("steady_case"),
            sample_row("not_steady_case", verdict="not steady (drifting)"),
            sample_row("salt1_jin_hi10q_corrected_case"),
        ]
        components, screened = builder.split_components(rows)
        self.assertEqual(len(components), 1)
        self.assertEqual(len(screened), 2)
        self.assertEqual(screened[0]["screen_reason"], "not_uncertainty_usable_verdict:not steady (drifting)")
        self.assertTrue(screened[1]["screen_reason"].startswith("live_or_active_case:"))

    def test_component_row_preserves_metrics_and_adds_envelope(self) -> None:
        row = builder.component_row(sample_row("steady_case"))
        self.assertEqual(row["osc_mean"], "10.0")
        self.assertEqual(row["osc_rmse_about_trend"], "0.4")
        self.assertEqual(row["fit_slope"], "0.002")
        self.assertEqual(row["unc_sem_corrected"], "0.1")
        self.assertEqual(row["unc_rel_sem_corrected"], "0.01")
        self.assertAlmostEqual(float(row["drift_over_window"]), 0.2)
        self.assertAlmostEqual(float(row["paper_envelope_abs"]), 0.696)

    def test_build_writes_main_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_csv = root / "steady.csv"
            case_slug = "modern_runs__2026-06-18_convergence_and_jin_envelope_wave__salt2_jin__case"
            rows = [
                sample_row(case_slug, group="mdot"),
                sample_row(case_slug, group="temperature"),
                sample_row(case_slug, group="wall_temperature"),
                sample_row(case_slug, verdict="not steady (drifting)", group="heat"),
            ]
            with input_csv.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
                writer.writeheader()
                writer.writerows(rows)

            out = root / "out"
            summary = builder.build(input_csv, out)
            self.assertEqual(summary["usable_rows"], 3)
            self.assertEqual(summary["screened_rows"], 1)
            self.assertEqual(summary["presentation_salt234_rows"], 4)
            self.assertTrue((out / "uncertainty_components_steady_or_quasi.csv").is_file())
            compact = (out / "paper_uncertainty_bounds_salt234.csv").read_text(encoding="utf-8")
            self.assertIn("total_Q_screen_note", compact)
            self.assertIn("not steady (drifting) screened out", compact)
            presentation = (out / "presentation_salt234_timeseries_uncertainty.csv").read_text(encoding="utf-8")
            self.assertIn("total_Q residual", presentation)
            self.assertIn("Absolute W residual", presentation)
            self.assertNotIn("relative", presentation.splitlines()[0])


if __name__ == "__main__":
    unittest.main()
