"""Tests for AGENT-262 Salt2 pressure-only mesh comparison."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.analyze.build_salt2_pressure_mesh_family_comparison import (
    build_package,
    friction_verdict,
    momentum_verdict,
)


class Salt2PressureMeshFamilyComparisonTests(unittest.TestCase):
    def test_friction_negative_flag_is_not_fit_safe(self) -> None:
        medium = {
            "apparent_darcy_f": "-0.7",
            "dp_loss_ds_pa_per_m": "-6.0",
            "flags": "mu_from_jin_corr_T_from_rho_eos;negative_f_pressure_recovery_or_noise",
        }
        fine = {
            "apparent_darcy_f": "-0.6",
            "dp_loss_ds_pa_per_m": "-5.0",
            "flags": "mu_from_jin_corr_T_from_rho_eos;negative_f_pressure_recovery_or_noise",
        }

        self.assertEqual(friction_verdict(medium, fine), "not_fit_safe_pressure_recovery_or_noise")

    def test_positive_close_friction_is_fit_safe(self) -> None:
        medium = {"apparent_darcy_f": "1.80", "dp_loss_ds_pa_per_m": "16.6", "flags": ""}
        fine = {"apparent_darcy_f": "1.82", "dp_loss_ds_pa_per_m": "16.7", "flags": ""}

        self.assertEqual(friction_verdict(medium, fine), "fit_safe_pressure_gradient")

    def test_positive_close_momentum_is_fit_safe(self) -> None:
        medium = {"f_corrected": "2.20"}
        fine = {"f_corrected": "2.24"}

        self.assertEqual(momentum_verdict(medium, fine), "fit_safe_momentum_corrected")

    def test_build_package_from_minimal_fixture(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_dir = root / "inputs"
            output_dir = root / "outputs"
            for level in ("medium", "fine"):
                level_dir = input_dir / level
                level_dir.mkdir(parents=True)
                (level_dir / "section_mean_pressure_case.csv").write_text(
                    "label,span,gate,status,section_mean_p_rgh_pa,section_mean_total_pressure_pa,dynamic_head_pa,u_bulk_m_s,flow_alignment\n"
                    "left_lower_leg__s01,left_lower_leg,ok,sampled,-9,-8,0.2,0.014,0.9\n",
                    encoding="utf-8",
                )
                f_value = "1.80" if level == "medium" else "1.82"
                (level_dir / "segment_friction.csv").write_text(
                    "source_id,span,method,n_stations_used,segment_arc_length_m,dp_signed_ds_pa_per_m,dp_loss_ds_pa_per_m,hydraulic_diameter_m,section_mean_rho_kg_m3,u_bulk_m_s,segment_temperature_k,mu_pa_s_used,apparent_darcy_f,reynolds_number,laminar_ref_darcy_f_64_over_Re,excess_loss_factor_fapp_over_flam,flow_alignment_min,flags\n"
                    f"case,left_lower_leg,section_mean_static_gradient,3,0.1,-16,16,0.02,1955,0.014,451,0.0088,{f_value},70,0.9,2.0,0.85,\n",
                    encoding="utf-8",
                )
                m_value = "1.35" if level == "medium" else "1.36"
                (level_dir / "momentum_budget.csv").write_text(
                    "Re,bulk_T_C,bulk_T_K,buoyancy_fraction_of_raw_grad,buoyancy_source_grad_pa_m,d_h_m,f_corrected,f_corrected_noinertia,f_corrected_over_flam,f_lam_64_re,f_raw_buoyancy_embedded,flow_orientation_sigma,friction_grad_corrected_noinertia_pa_m,friction_grad_corrected_pa_m,friction_grad_raw_pa_m,gh_mean_m2_s2,grad_p_rgh_pa_m,grad_rho_kg_m4,grad_u_per_s,inertial_grad_pa_m,n_stations_used,rho_mean_kg_m3,source_id,span,u_along_tangent_mean_m_s,u_bulk_mean_m_s\n"
                    f"70,178,451,0.2,4,0.02,{m_value},{m_value},1.5,0.9,1.8,1,12,12,16,-1,-16,-2,-0.003,-0.08,3,1955,case,left_lower_leg,0.014,0.014\n",
                    encoding="utf-8",
                )

            summary = build_package(input_dir, output_dir)

            self.assertEqual(summary["pressure_station_rows"], 1)
            self.assertIn("left_lower_leg", summary["pressure_gradient_fit_safe_spans"])
            self.assertTrue((output_dir / "fit_safety_summary.csv").is_file())


if __name__ == "__main__":
    unittest.main()
