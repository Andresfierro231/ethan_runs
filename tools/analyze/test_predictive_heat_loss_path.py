#!/usr/bin/env python3
"""Tests for build_predictive_heat_loss_path.py."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.analyze import build_predictive_heat_loss_path as builder  # noqa: E402


class PredictiveHeatLossPathTests(unittest.TestCase):
    def test_cooler_error_reduction_uses_absolute_errors(self) -> None:
        reduction, pct = builder.cooler_error_reduction(62.226, -6.219)
        self.assertAlmostEqual(reduction, 56.007)
        self.assertAlmostEqual(pct, 90.0058, places=3)

    def test_mesh_unestablished_htc_is_validation_only(self) -> None:
        htc_row = {
            "status": "computed",
            "mesh_independence": "UNESTABLISHED",
            "nu_direct_admitted": "True",
            "thermally_blocked": "False",
        }
        self.assertEqual(
            builder.classify_effective_thermal_status(htc_row),
            "validation_only_mesh_unestablished",
        )

    def test_thermal_blocker_overrides_computed_status(self) -> None:
        htc_row = {
            "status": "computed",
            "mesh_independence": "ESTABLISHED",
            "nu_direct_admitted": "True",
            "thermally_blocked": "True",
        }
        self.assertEqual(
            builder.classify_effective_thermal_status(htc_row),
            "blocked_by_source_segment_htc_flag",
        )

    def test_control_volume_table_computes_external_hA_and_gates_fit(self) -> None:
        segment_rows = [
            {
                "source_id": "viscosity_screening_salt_test_2_jin_coarse_mesh",
                "case_id": "salt_2",
                "one_d_segment": "lower_leg",
                "component_parent_spans": "lower_leg",
                "area_m2": "2.0",
                "area_weighted_h_W_m2K": "4.5",
                "area_weighted_Ta_K": "299.19",
                "area_weighted_Tsur_K": "299.19",
                "area_weighted_emissivity": "0.95",
                "realized_wallHeatFlux_W": "236.0",
                "imposed_Q_W": "265.0",
            }
        ]
        enthalpy_rows = [
            {
                "case_id": "salt_2",
                "physical_segment": "lower_leg",
                "enthalpy_change_W": "288.0",
                "wallHeatFlux_vs_enthalpy_residual_W": "-52.0",
                "residual_fraction": "-0.18",
                "bracket_status": "bracketed_full_span_interfaces",
                "max_interface_recirc_ratio": "0.28",
                "quality_flags": "",
                "T_bulk_inlet_K": "444.0",
                "T_bulk_outlet_K": "459.0",
                "delta_T_K": "15.0",
                "mdot_kg_s": "0.013",
                "cp_jkgk": "1423.47",
            }
        ]
        htc_rows = {
            ("salt_2", "lower_leg"): {
                "status": "computed",
                "mesh_independence": "UNESTABLISHED",
                "nu_direct_admitted": "False",
                "thermally_blocked": "False",
                "htc_wm2k": "252.0",
                "Nu": "",
                "uaprime_wmk": "22.0",
                "T_wall_k": "459.0",
                "T_bulk_k": "444.0",
                "delta_T_k": "15.0",
                "mesh": "coarse",
            }
        }
        rows = builder.build_control_volume_effective_table(
            segment_rows, enthalpy_rows, htc_rows
        )
        self.assertEqual(len(rows), 1)
        self.assertAlmostEqual(rows[0]["external_hA_W_per_K"], 9.0)
        self.assertEqual(
            rows[0]["thermal_effective_status"], "validation_only_mesh_unestablished"
        )
        self.assertEqual(
            rows[0]["fit_use_status"], "validation_only_effective_thermal_not_fit_safe"
        )

    def test_cooler_hx_table_separates_cfd_and_baseline_duty(self) -> None:
        role_rows = [
            {
                "case_id": "salt_2",
                "role": "cooler",
                "imposed_Q_W": "-136.35",
                "realized_wallHeatFlux_W": "-136.35",
            }
        ]
        replay_rows = [
            {
                "case_id": "salt_2",
                "path_id": "P0_fixed_mdot_current_1d_contract",
                "Tmean_error_K": "62.226",
                "qhx_total_W": "46.292",
            },
            {
                "case_id": "salt_2",
                "path_id": "P1_cfd_cooler_duty_only",
                "Tmean_error_K": "6.219",
                "qhx_total_W": "136.35",
            },
        ]
        rows = builder.build_cooler_hx_duty_table(role_rows, replay_rows)
        self.assertEqual(len(rows), 1)
        self.assertAlmostEqual(rows[0]["cooler_extra_removal_vs_baseline_1d_W"], 90.058)
        self.assertEqual(
            rows[0]["cooler_duty_mismatch_class"],
            "first_order_external_hx_boundary_error",
        )


if __name__ == "__main__":
    unittest.main()
