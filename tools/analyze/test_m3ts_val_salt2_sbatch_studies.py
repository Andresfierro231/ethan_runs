#!/usr/bin/env python3
"""Tests for AGENT-439 sbatch study package builder."""

from __future__ import annotations

import csv
import unittest

from tools.analyze import build_m3ts_val_salt2_sbatch_studies as builder


class M3tsValSalt2SbatchStudiesTests(unittest.TestCase):
    def test_m3ts_rows_preserve_guardrails(self) -> None:
        rows = builder.m3ts_rows()
        self.assertEqual(len(rows), 3)
        self.assertTrue(all(row["runtime_input_violations"] == 0 for row in rows))
        self.assertTrue(all("diagnostic_M2_M3" in row["guardrail"] for row in rows))

    def test_val_salt2_external_test_is_not_fit_row(self) -> None:
        rows = builder.val_salt2_rows()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["fit_allowed"], "no")
        self.assertEqual(rows[0]["runtime_input_violations"], 0)

    def test_matched_plane_preflight_has_no_missing_contract_paths(self) -> None:
        rows = builder.matched_plane_preflight_rows()
        self.assertTrue(rows)
        failures = [row for row in rows if row["local_field_contract_preflight"] != "pass"]
        self.assertEqual(failures, [])

    def test_build_package_writes_sbatch_scripts(self) -> None:
        summary = builder.build_package()
        self.assertEqual(summary["matched_plane_preflight_failures"], 0)
        for name in [
            "run_m3ts_setup_only_scorecard.sbatch",
            "run_val_salt2_external_test.sbatch",
            "run_matched_plane_onset_extraction.sbatch",
        ]:
            self.assertTrue((builder.OUT / "scripts" / name).exists())
        with (builder.OUT / "sbatch_submission_plan.csv").open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(len(rows), 3)
        self.assertTrue(all(row["dependency_recommendation"] == "afterok:3295438" for row in rows))


if __name__ == "__main__":
    unittest.main()
