#!/usr/bin/env python3
"""Tests for the thesis CFD run QoI split chart builder."""

from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from tools.analyze import build_thesis_cfd_run_qoi_split_chart as builder


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class ThesisCfdRunQoiSplitChartTests(unittest.TestCase):
    def test_split_rows_and_no_training_leakage_flags(self) -> None:
        wide_rows, long_rows, coverage_rows = builder.build_rows()
        by_case = {row["case_key"]: row for row in wide_rows}

        self.assertEqual(len(wide_rows), 7)
        self.assertEqual(sum(1 for row in wide_rows if row["split_group"] == "train"), 4)
        self.assertEqual(sum(1 for row in wide_rows if row["split_group"] == "holdout_test"), 3)
        self.assertEqual(by_case["val_salt2"]["split_group"], "holdout_test")
        self.assertEqual(by_case["val_salt2"]["split_subrole"], "external_test")
        self.assertFalse(any(row["coefficient_fit_allowed_now"] for row in wide_rows))
        self.assertFalse(any(row["model_selection_allowed_now"] for row in wide_rows))
        self.assertTrue(all(row["runtime_use_warning"] for row in wide_rows))

        self.assertGreater(len(long_rows), len(wide_rows))
        self.assertEqual(len(coverage_rows), len(wide_rows))
        self.assertEqual(by_case["salt1_nominal"]["tw_sensor_count"], "0")
        self.assertNotEqual(by_case["salt1_nominal"]["TW_mean_K"], "")
        self.assertGreater(float(by_case["salt2_hi5q"]["mdot_abs_mean_kg_s"]), 0.0)
        self.assertGreater(float(by_case["val_salt2"]["TP_mean_K"]), 0.0)

    def test_build_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "chart"
            summary = builder.build(out)

            self.assertEqual(summary["decision"], "cfd_run_qoi_split_chart_complete_no_model_scoring")
            self.assertEqual(summary["wide_rows"], 7)
            self.assertEqual(summary["train_rows"], 4)
            self.assertEqual(summary["holdout_test_rows"], 3)
            self.assertEqual(summary["external_test_rows_grouped_as_holdout_test"], 1)
            self.assertTrue(summary["all_source_paths_exist"])
            self.assertFalse(summary["model_scoring_performed"])
            self.assertFalse(summary["fitting_model_selection_performed"])

            wide = read_csv(out / "cfd_run_qoi_split_chart_wide.csv")
            policy = read_csv(out / "holdout_test_policy_update.csv")
            guardrails = read_csv(out / "no_mutation_guardrails.csv")

            self.assertEqual(len(wide), 7)
            self.assertEqual({row["case_key"] for row in wide if row["split_group"] == "holdout_test"}, {"salt2_lo5q", "salt2_hi5q", "val_salt2"})
            self.assertEqual(next(row for row in policy if row["case_key"] == "val_salt2")["split_subrole"], "external_test")
            self.assertIn({"guardrail": "fitting_tuning_model_selection", "status": "not_performed"}, guardrails)
            self.assertTrue((out / "README.md").exists())


if __name__ == "__main__":
    unittest.main()
