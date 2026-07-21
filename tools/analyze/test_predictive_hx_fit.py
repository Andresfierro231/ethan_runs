#!/usr/bin/env python3
"""Tests for build_predictive_hx_fit.py."""

from __future__ import annotations

import math
import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.analyze import build_predictive_hx_fit as hx  # noqa: E402


class PredictiveHxFitTests(unittest.TestCase):
    def test_primary_split_holds_out_salt3_without_overlap(self) -> None:
        splits = hx.split_rows()
        primary = {row["split_id"]: row for row in splits}[hx.PRIMARY_SPLIT_ID]
        self.assertEqual(hx.parse_cases(primary["train_cases"]), ("salt_2",))
        self.assertEqual(hx.parse_cases(primary["validation_cases"]), ("salt_3",))
        self.assertEqual(hx.parse_cases(primary["holdout_cases"]), ("salt_4",))
        self.assertEqual(hx.validate_split_rows(splits), [])

    def test_validate_split_rows_rejects_overlap(self) -> None:
        violations = hx.validate_split_rows(
            [
                {
                    "split_id": "bad",
                    "train_cases": "salt_2;salt_3",
                    "validation_cases": "salt_3",
                    "holdout_cases": "",
                }
            ]
        )
        self.assertEqual(violations[0]["violation"], "split_role_overlap")

    def test_fit_multiplier_is_zero_intercept_least_squares(self) -> None:
        baseline = [
            {"case_id": "salt_2", "variant_id": "v", "baseline_qhx_total_W": 10.0, "target_cooler_removed_W": 20.0},
            {"case_id": "salt_4", "variant_id": "v", "baseline_qhx_total_W": 30.0, "target_cooler_removed_W": 60.0},
        ]
        fit = hx.fit_multiplier(baseline, ("salt_2", "salt_4"), "v")
        self.assertAlmostEqual(fit["fitted_global_qhx_multiplier"], 2.0)
        self.assertAlmostEqual(fit["train_rmse_qhx_W"], 0.0)

    def test_duty_score_marks_validation_without_runtime_target_use(self) -> None:
        baseline = [
            {"case_id": "salt_2", "variant_id": "v", "baseline_qhx_total_W": 10.0, "target_cooler_removed_W": 20.0},
            {"case_id": "salt_3", "variant_id": "v", "baseline_qhx_total_W": 15.0, "target_cooler_removed_W": 33.0},
        ]
        splits = [
            {
                "split_id": "s",
                "train_cases": "salt_2",
                "validation_cases": "salt_3",
            }
        ]
        params = [
            {
                "split_id": "s",
                "variant_id": "v",
                "model_form_id": "HX1_global_qhx_multiplier_on_fluid_airside",
                "fitted_global_qhx_multiplier": 2.0,
            }
        ]
        rows = hx.duty_score_rows(baseline, params, splits)
        validation = [row for row in rows if row["case_id"] == "salt_3"][0]
        self.assertEqual(validation["fit_role"], "validation")
        self.assertEqual(validation["target_cooler_used_at_runtime"], "false")
        self.assertAlmostEqual(validation["predicted_qhx_total_W"], 30.0)
        self.assertAlmostEqual(validation["qhx_error_W"], -3.0)

    def test_model_forms_include_direct_ua_as_blocked_future_path(self) -> None:
        forms = {row["model_form_id"]: row for row in hx.model_form_rows()}
        self.assertEqual(forms["HX2_direct_UA_multiplier_in_solver"]["status"], "blocked_not_implemented")
        self.assertIn("external Fluid source edits", forms["HX2_direct_UA_multiplier_in_solver"]["blocked_or_limit_reason"])

    def test_target_cooler_by_case_uses_abs_removed_duty(self) -> None:
        targets = hx.target_cooler_by_case([{"case_id": "salt_2", "cooler_removed_duty_W": "-136.5"}])
        self.assertTrue(math.isclose(targets["salt_2"], 136.5))


if __name__ == "__main__":
    unittest.main()
