from __future__ import annotations

import unittest

from tools.analyze.build_ethan_salt_feature_path_hydraulic_hardening import classify_case_row
from tools.analyze.build_ethan_salt_model_dependency_package_v3 import choose_nu_status
from tools.analyze.build_ethan_salt_straight_hydraulic_sensitivity import (
    build_late_window_sensitivity_row,
    classify_retained_time_row,
    parse_package_root_overrides,
)
from tools.analyze.build_ethan_water_feature_hydraulic_readiness import classify_feature_row
from tools.analyze.build_ethan_water_phase1_starter_package import classify_thermal_phase1


class ClosureModelingV3Tests(unittest.TestCase):
    def test_feature_case_row_requires_full_path_integral_even_when_proxy_positive(self) -> None:
        status, reason, reasons = classify_case_row(
            {
                "proxy_support_fraction_min": 1.0,
                "positive_proxy_time_fraction": 1.0,
            }
        )
        self.assertEqual(status, "sensitivity_only")
        self.assertEqual(reason, "missing_full_path_density_integral")
        self.assertIn("missing_full_path_density_integral", reasons)

    def test_feature_case_row_blocks_nonpositive_proxy(self) -> None:
        status, reason, _ = classify_case_row(
            {
                "proxy_support_fraction_min": 1.0,
                "positive_proxy_time_fraction": 0.0,
            }
        )
        self.assertEqual(status, "excluded")
        self.assertEqual(reason, "nonpositive_local_feature_proxy_excess")

    def test_water_feature_readiness_candidate_requires_positive_proxy_and_low_warning(self) -> None:
        status, _ = classify_feature_row(0.80, 0.20)
        self.assertEqual(status, "candidate_for_future_dependency_fit")

    def test_water_thermal_priority_when_sign_consistency_is_poor(self) -> None:
        status, _ = classify_thermal_phase1("test_section_span", "candidate", 1.0, 0.30, 0.20, 0.25)
        self.assertEqual(status, "closure_rebuild_priority")

    def test_nu_status_requires_multiple_cases_and_nonzero_slope_ci(self) -> None:
        rows = [
            {"source_id": "case_a"},
            {"source_id": "case_b"},
            {"source_id": "case_c"},
            {"source_id": "case_d"},
        ]
        status, model, reason = choose_nu_status(
            rows,
            {
                "status": "fit",
                "model_type": "branch_aware_re_power_law",
                "bootstrap_ci95": {"log_re": [0.1, 0.4]},
            },
        )
        self.assertEqual(status, "provisional_defended")
        self.assertEqual(model, "branch_aware_re_power_law")
        self.assertEqual(reason, "limited_direct_branch_domain")

    def test_nu_status_refuses_when_ci_crosses_zero(self) -> None:
        rows = [
            {"source_id": "case_a"},
            {"source_id": "case_b"},
            {"source_id": "case_c"},
            {"source_id": "case_d"},
        ]
        status, model, reason = choose_nu_status(
            rows,
            {
                "status": "fit",
                "model_type": "branch_aware_re_power_law",
                "bootstrap_ci95": {"log_re": [-0.1, 0.2]},
            },
        )
        self.assertEqual(status, "not_defensible_yet")
        self.assertEqual(model, "exploratory_screened_only_model")
        self.assertEqual(reason, "re_slope_ci_crosses_zero")

    def test_retained_time_straight_row_needs_positive_hydro_loss_and_ratio_agreement(self) -> None:
        status, reason = classify_retained_time_row(1.0, 12.0, 0.8, 0.9)
        self.assertEqual(status, "fit_used")
        self.assertEqual(reason, "")

        blocked_status, blocked_reason = classify_retained_time_row(1.0, -2.0, 0.8, 0.9)
        self.assertEqual(blocked_status, "excluded")
        self.assertEqual(blocked_reason, "buoyancy_aided_or_net_gain_section")

    def test_late_window_sensitivity_stays_blocked_when_preserved_tail_is_short(self) -> None:
        row = build_late_window_sensitivity_row(
            [{"source_id": "case_a", "scope_name": "lower_leg"}],
            [
                {
                    "source_id": "case_a",
                    "section_name": "lower_leg",
                    "fit_use_status": "fit_used",
                    "window_span_s": 4.0,
                }
            ],
        )
        self.assertEqual(row["status"], "not_run")
        self.assertIn("4.0-4.0 s", row["note"])

    def test_late_window_sensitivity_runs_once_window_is_long_enough(self) -> None:
        row = build_late_window_sensitivity_row(
            [{"source_id": "case_a", "scope_name": "lower_leg"}],
            [
                {
                    "source_id": "case_a",
                    "section_name": "lower_leg",
                    "fit_use_status": "fit_used",
                    "window_span_s": 20.0,
                }
            ],
        )
        self.assertEqual(row["status"], "run")
        self.assertEqual(row["qualitative_conclusion_changed"], "no")

    def test_package_root_override_parser_requires_source_id_equals_path(self) -> None:
        overrides = parse_package_root_overrides(["case_a=tmp/report_root"])
        self.assertIn("case_a", overrides)
        self.assertTrue(str(overrides["case_a"]).endswith("tmp/report_root"))

        with self.assertRaises(ValueError):
            parse_package_root_overrides(["broken_override"])


if __name__ == "__main__":
    unittest.main()
