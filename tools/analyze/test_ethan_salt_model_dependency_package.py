from __future__ import annotations

import math
import unittest

from tools.analyze.build_ethan_salt_model_dependency_package import (
    HYDRAULIC_AUDIT_COLUMNS,
    THERMAL_DECOMPOSITION_COLUMNS,
    classify_hydraulic_row,
    classify_thermal_row,
    exp_inv_t_eval,
    normalized_residual,
    polynomial_eval,
    sign_token,
)


class SaltModelDependencyPackageTests(unittest.TestCase):
    def test_polynomial_eval(self) -> None:
        self.assertAlmostEqual(polynomial_eval((1.0, 2.0, 3.0), 2.0), 17.0)

    def test_exp_inv_t_eval(self) -> None:
        value = exp_inv_t_eval((1.0, 10.0), 5.0)
        self.assertAlmostEqual(value, math.exp(2.0))

    def test_sign_token(self) -> None:
        self.assertEqual(sign_token(1.0), "positive")
        self.assertEqual(sign_token(-1.0), "negative")
        self.assertEqual(sign_token(0.0), "zero")

    def test_normalized_residual(self) -> None:
        self.assertAlmostEqual(normalized_residual(2.0, 8.0), 0.25)
        self.assertTrue(math.isnan(normalized_residual(1.0, 0.0)))

    def test_right_leg_is_blocked(self) -> None:
        status, reason, reasons, screened, closure = classify_thermal_row(
            branch_name="right_leg",
            is_derived_branch=False,
            branch_fit_status_screened="candidate",
            branch_fit_reason_screened="thermal_support_clean",
            support_fraction=0.95,
            warning_fraction=0.0,
            min_abs_delta_t_k=1.0,
            residual_fraction=0.05,
            direction_consistent=True,
            group_reconstruction_fraction=0.0,
        )
        self.assertEqual(status, "excluded")
        self.assertEqual(reason, "right_leg_blocked_by_policy")
        self.assertIn("right_leg_blocked_by_policy", reasons)
        self.assertTrue(screened)
        self.assertFalse(closure)

    def test_derived_branch_is_sensitivity_only(self) -> None:
        status, reason, reasons, screened, closure = classify_thermal_row(
            branch_name="upcomer",
            is_derived_branch=True,
            branch_fit_status_screened="candidate",
            branch_fit_reason_screened="thermal_support_clean",
            support_fraction=0.95,
            warning_fraction=0.0,
            min_abs_delta_t_k=1.0,
            residual_fraction=0.05,
            direction_consistent=True,
            group_reconstruction_fraction=0.0,
        )
        self.assertEqual(status, "sensitivity_only")
        self.assertEqual(reason, "derived_branch_overlap_double_counting")
        self.assertIn("derived_branch_overlap_double_counting", reasons)
        self.assertTrue(screened)
        self.assertFalse(closure)

    def test_weak_thermal_support_excludes(self) -> None:
        status, reason, reasons, _screened, closure = classify_thermal_row(
            branch_name="left_lower_leg",
            is_derived_branch=False,
            branch_fit_status_screened="candidate",
            branch_fit_reason_screened="thermal_support_clean",
            support_fraction=0.60,
            warning_fraction=0.0,
            min_abs_delta_t_k=1.0,
            residual_fraction=0.05,
            direction_consistent=True,
            group_reconstruction_fraction=0.0,
        )
        self.assertEqual(status, "sensitivity_only")
        self.assertEqual(reason, "support_fraction_below_candidate_gate")
        self.assertIn("support_fraction_below_candidate_gate", reasons)
        self.assertFalse(closure)

    def test_loose_enthalpy_closure_excludes(self) -> None:
        status, reason, reasons, _screened, closure = classify_thermal_row(
            branch_name="left_lower_leg",
            is_derived_branch=False,
            branch_fit_status_screened="candidate",
            branch_fit_reason_screened="thermal_support_clean",
            support_fraction=0.95,
            warning_fraction=0.0,
            min_abs_delta_t_k=1.0,
            residual_fraction=0.40,
            direction_consistent=True,
            group_reconstruction_fraction=0.0,
        )
        self.assertEqual(status, "sensitivity_only")
        self.assertEqual(reason, "enthalpy_wall_heat_balance_loose")
        self.assertIn("enthalpy_wall_heat_balance_loose", reasons)
        self.assertFalse(closure)

    def test_direction_inconsistency_excludes(self) -> None:
        status, reason, reasons, _screened, closure = classify_thermal_row(
            branch_name="left_lower_leg",
            is_derived_branch=False,
            branch_fit_status_screened="candidate",
            branch_fit_reason_screened="thermal_support_clean",
            support_fraction=0.95,
            warning_fraction=0.0,
            min_abs_delta_t_k=1.0,
            residual_fraction=0.05,
            direction_consistent=False,
            group_reconstruction_fraction=0.0,
        )
        self.assertEqual(status, "sensitivity_only")
        self.assertEqual(reason, "enthalpy_wall_direction_inconsistent")
        self.assertIn("enthalpy_wall_direction_inconsistent", reasons)
        self.assertFalse(closure)

    def test_candidate_thermal_row_is_fit_used(self) -> None:
        status, reason, reasons, screened, closure = classify_thermal_row(
            branch_name="left_lower_leg",
            is_derived_branch=False,
            branch_fit_status_screened="candidate",
            branch_fit_reason_screened="thermal_support_clean",
            support_fraction=0.95,
            warning_fraction=0.0,
            min_abs_delta_t_k=1.0,
            residual_fraction=0.05,
            direction_consistent=True,
            group_reconstruction_fraction=0.0,
        )
        self.assertEqual(status, "fit_used")
        self.assertEqual(reason, "closure_supported")
        self.assertEqual(reasons, [])
        self.assertTrue(screened)
        self.assertTrue(closure)

    def test_nonpositive_feature_loss_is_excluded(self) -> None:
        status, reason, reasons, screened, closure = classify_hydraulic_row(
            asset_family="feature_keff",
            fit_status_screened="screening_only",
            fit_reason_screened="nonpositive_residual_feature_loss",
            pressure_method_status="residual_prgh_only",
        )
        self.assertEqual(status, "excluded")
        self.assertEqual(reason, "nonpositive_residual_feature_loss")
        self.assertIn("feature_pressure_method_residual_only", reasons)
        self.assertFalse(screened)
        self.assertFalse(closure)

    def test_buoyancy_aided_hydraulic_section_excluded(self) -> None:
        status, reason, reasons, screened, closure = classify_hydraulic_row(
            asset_family="straight_section_friction",
            fit_status_screened="screening_only",
            fit_reason_screened="buoyancy_aided_or_net_gain_section",
            pressure_method_status="defended_direct_hydro",
        )
        self.assertEqual(status, "excluded")
        self.assertEqual(reason, "buoyancy_aided_or_net_gain_section")
        self.assertFalse(screened)
        self.assertFalse(closure)

    def test_candidate_hydraulic_section_is_fit_used(self) -> None:
        status, reason, reasons, screened, closure = classify_hydraulic_row(
            asset_family="straight_section_friction",
            fit_status_screened="candidate",
            fit_reason_screened="dissipative_with_agreeing_friction_proxies",
            pressure_method_status="defended_direct_hydro",
        )
        self.assertEqual(status, "fit_used")
        self.assertEqual(reason, "closure_supported")
        self.assertEqual(reasons, [])
        self.assertTrue(screened)
        self.assertTrue(closure)

    def test_output_schemas_contain_required_columns(self) -> None:
        self.assertIn("fit_use_status", THERMAL_DECOMPOSITION_COLUMNS)
        self.assertIn("re_effective", THERMAL_DECOMPOSITION_COLUMNS)
        self.assertIn("pressure_method_status", HYDRAULIC_AUDIT_COLUMNS)
        self.assertIn("fit_use_status", HYDRAULIC_AUDIT_COLUMNS)


if __name__ == "__main__":
    unittest.main()
