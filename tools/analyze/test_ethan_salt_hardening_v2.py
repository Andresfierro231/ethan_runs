from __future__ import annotations

import math
import unittest

from tools.analyze.build_ethan_salt_feature_hydraulic_hardening import classify_feature_case_row
from tools.analyze.build_ethan_salt_model_dependency_package_v2 import (
    direct_thermal_fit_rows,
    normalize_feature_case_rows,
    stable_feature_fit_rows,
    summarize_exclusions,
)
from tools.analyze.build_ethan_salt_thermal_closure_hardening import classify_case_row, classify_time_row
from tools.analyze.ethan_salt_hardening_common import local_side_support_mean, normalized_residual


class SaltHardeningV2Tests(unittest.TestCase):
    def test_normalized_residual_uses_absolute_ratio(self) -> None:
        self.assertAlmostEqual(normalized_residual(-5.0, 20.0), 0.25)
        self.assertTrue(math.isnan(normalized_residual(1.0, 0.0)))

    def test_local_side_support_mean_handles_direction_and_missing(self) -> None:
        rows = [
            {"value": "nan"},
            {"value": "2.0"},
            {"value": "4.0"},
            {"value": "6.0"},
        ]
        mean_start, count_start, selected_start = local_side_support_mean(rows, from_start=True, value_key="value", count=2)
        mean_end, count_end, selected_end = local_side_support_mean(rows, from_start=False, value_key="value", count=2)
        self.assertEqual(count_start, 2)
        self.assertEqual(count_end, 2)
        self.assertAlmostEqual(mean_start, 3.0)
        self.assertAlmostEqual(mean_end, 5.0)
        self.assertEqual(selected_start[0]["value"], "2.0")
        self.assertEqual(selected_end[0]["value"], "6.0")

    def test_classify_feature_case_row_excludes_nonpositive_feature_loss(self) -> None:
        status, primary, reasons = classify_feature_case_row(
            {
                "mean_dynamic_head_local_pa": 10.0,
                "mean_re_effective": 500.0,
                "local_support_fraction_min": 1.0,
                "positive_time_fraction": 0.40,
                "mean_feature_excess_dp_local_pa": -1.0,
            }
        )
        self.assertEqual(status, "excluded")
        self.assertEqual(primary, "nonpositive_local_feature_excess_loss")
        self.assertIn("nonpositive_local_feature_excess_loss", reasons)

    def test_stable_feature_fit_rows_requires_stability_and_count(self) -> None:
        rows = []
        for index in range(4):
            rows.append(
                {
                    "source_id": f"salt{index}",
                    "case_label": f"Case {index}",
                    "feature_name": "corner_upper_right",
                    "feature_class": "bend",
                    "fit_use_status": "fit_used",
                    "mean_re_effective": 1000.0 + index,
                    "mean_keff_effective_local": 0.5 + 0.1 * index,
                    "local_support_fraction_min": 1.0,
                    "positive_time_fraction": 1.0,
                }
            )
        rows.append(
            {
                "source_id": "salt4",
                "case_label": "Case 4",
                "feature_name": "corner_upper_right",
                "feature_class": "bend",
                "fit_use_status": "excluded",
                "mean_re_effective": 1005.0,
                "mean_keff_effective_local": 0.9,
                "local_support_fraction_min": 1.0,
                "positive_time_fraction": 0.2,
            }
        )
        stable_rows, stability = stable_feature_fit_rows(rows)
        self.assertEqual(len(stable_rows), 4)
        self.assertAlmostEqual(stability["corner_upper_right"], 0.8)

    def test_classify_time_row_enforces_right_leg_policy(self) -> None:
        status, reason = classify_time_row(
            branch_name="right_leg",
            branch_fit_status="candidate",
            support_fraction=1.0,
            delta_t_wall_bulk_mean_k=2.0,
            residual_fraction=0.01,
            thermal_direction_consistent=True,
            grouped_reconstruction_fraction=0.01,
        )
        self.assertEqual(status, "excluded")
        self.assertEqual(reason, "right_leg_blocked_by_policy")

    def test_classify_time_row_enforces_weak_thermal_support(self) -> None:
        status, reason = classify_time_row(
            branch_name="left_lower_leg",
            branch_fit_status="candidate",
            support_fraction=1.0,
            delta_t_wall_bulk_mean_k=0.05,
            residual_fraction=0.01,
            thermal_direction_consistent=True,
            grouped_reconstruction_fraction=0.01,
        )
        self.assertEqual(status, "sensitivity_only")
        self.assertEqual(reason, "weak_twall_minus_tbulk_support")

    def test_classify_case_row_returns_sensitivity_only_for_derived_branch(self) -> None:
        status, primary, reasons = classify_case_row(
            {
                "branch_name": "upcomer",
                "branch_fit_status": "candidate",
                "branch_fit_reason": "thermal_support_clean",
                "mean_support_fraction": 1.0,
                "min_delta_t_wall_bulk_mean_k": 1.0,
                "mean_residual_fraction_of_wall_heat": 0.05,
                "max_residual_fraction_of_wall_heat": 0.05,
                "pass_time_fraction": 1.0,
                "direction_consistent_all_times": True,
                "mean_grouped_reconstruction_fraction": 0.01,
                "mean_nu_effective": 5.0,
            }
        )
        self.assertEqual(status, "sensitivity_only")
        self.assertEqual(primary, "derived_branch_overlap_double_counting")
        self.assertIn("derived_branch_overlap_double_counting", reasons)

    def test_direct_thermal_fit_rows_excludes_blocked_and_derived(self) -> None:
        rows = [
            {"branch_name": "right_leg", "fit_use_status": "fit_used", "branch_fit_status": "candidate", "mean_nu_effective": "10", "mean_re_effective": "100"},
            {"branch_name": "upcomer", "fit_use_status": "fit_used", "branch_fit_status": "candidate", "mean_nu_effective": "10", "mean_re_effective": "100"},
            {"branch_name": "left_lower_leg", "fit_use_status": "fit_used", "branch_fit_status": "candidate", "mean_nu_effective": "10", "mean_re_effective": "100"},
            {"branch_name": "left_upper_leg", "fit_use_status": "sensitivity_only", "branch_fit_status": "candidate", "mean_nu_effective": "11", "mean_re_effective": "101"},
        ]
        defended, exploratory = direct_thermal_fit_rows(rows)
        self.assertEqual([row["branch_name"] for row in defended], ["left_lower_leg"])
        self.assertEqual({row["branch_name"] for row in exploratory}, {"left_lower_leg", "left_upper_leg"})

    def test_normalize_feature_case_rows_uses_fallback_keff_column(self) -> None:
        rows = normalize_feature_case_rows(
            [
                {
                    "source_id": "salt1",
                    "feature_name": "corner_upper_right",
                    "fit_use_status": "fit_used",
                    "mean_keff_local": "1.25",
                }
            ]
        )
        self.assertAlmostEqual(rows[0]["mean_keff_effective_local"], 1.25)

    def test_summarize_exclusions_aggregates_counts(self) -> None:
        summary = summarize_exclusions(
            [
                {"asset_family": "thermal_branch", "fit_use_status": "sensitivity_only", "exclusion_reason_primary": "enthalpy_wall_heat_balance_loose"},
                {"asset_family": "thermal_branch", "fit_use_status": "sensitivity_only", "exclusion_reason_primary": "enthalpy_wall_heat_balance_loose"},
                {"asset_family": "thermal_branch", "fit_use_status": "excluded", "exclusion_reason_primary": "right_leg_blocked_by_policy"},
                {"asset_family": "thermal_branch", "fit_use_status": "fit_used", "exclusion_reason_primary": "closure_supported"},
            ],
            "asset_family",
        )
        self.assertEqual(len(summary), 2)
        count_map = {(row["fit_use_status"], row["exclusion_reason_primary"]): row["row_count"] for row in summary}
        self.assertEqual(count_map[("sensitivity_only", "enthalpy_wall_heat_balance_loose")], 2)
        self.assertEqual(count_map[("excluded", "right_leg_blocked_by_policy")], 1)


if __name__ == "__main__":
    unittest.main()
