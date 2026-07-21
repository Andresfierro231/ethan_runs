"""Tests for AGENT-284 Salt2 Closure-QOI mesh GCI builder."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.analyze.build_salt2_closure_qoi_mesh_gci import (
    build_package,
)


class Salt2ClosureQoiMeshGciTests(unittest.TestCase):
    def test_build_package_with_analytic_pressure_triplet_and_blocked_thermal(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            root = Path(tmp)
            pressure_dir = root / "pressure"
            pressure_dir.mkdir()
            closure = root / "closure_observations.csv"
            thermal = root / "thermal_medium.csv"
            output = root / "out"

            # f(h) = 10 + 0.1*h^2 at h = 1.0, 1.5, 2.25.
            closure.write_text(
                "observation_id,source_id,case_id,observable_family,quantity,span,pressure_method,value,source_path,admission_status\n"
                "obs,viscosity_screening_salt_test_2_jin_coarse_mesh,salt_2,pressure,apparent_darcy_f,left_lower_leg,section_mean_static_gradient,10.50625,coarse.csv,admitted_mainline\n"
                "obs2,viscosity_screening_salt_test_2_jin_coarse_mesh,salt_2,pressure,f_corrected,left_lower_leg,,10.50625,coarse.csv,admitted_mainline\n",
                encoding="utf-8",
            )
            (pressure_dir / "friction_mesh_comparison.csv").write_text(
                "span,method,medium_apparent_darcy_f,fine_apparent_darcy_f,delta_apparent_darcy_f,delta_pct_apparent_darcy_f,mesh_agreement,medium_dp_loss_ds_pa_per_m,fine_dp_loss_ds_pa_per_m,medium_reynolds_number,fine_reynolds_number,medium_flags,fine_flags,sign_review,fit_safety\n"
                "left_lower_leg,section_mean_static_gradient,10.225,10.1,-0.125,-1,strong_medium_fine_agreement,1,1,70,70,,,positive_loss_both_meshes,fit_safe_pressure_gradient\n",
                encoding="utf-8",
            )
            (pressure_dir / "momentum_mesh_comparison.csv").write_text(
                "span,medium_f_corrected,fine_f_corrected,delta_f_corrected,delta_pct_f_corrected,mesh_agreement,medium_f_corrected_over_flam,fine_f_corrected_over_flam,medium_f_raw_buoyancy_embedded,fine_f_raw_buoyancy_embedded,medium_buoyancy_fraction_of_raw_grad,fine_buoyancy_fraction_of_raw_grad,medium_inertial_grad_pa_m,fine_inertial_grad_pa_m,medium_Re,fine_Re,sign_review,buoyancy_review,fit_safety\n"
                "left_lower_leg,10.225,10.1,-0.125,-1,strong_medium_fine_agreement,1,1,1,1,0,0,0,0,70,70,corrected_f_positive_both_meshes,moderate_buoyancy_correction,fit_safe_momentum_corrected\n",
                encoding="utf-8",
            )
            thermal.write_text(
                "segment,status,htc_wm2k,uaprime_wmk,Nu\n"
                "lower_leg,computed,100,10,5\n"
                "downcomer,thermally_blocked_segment_right_leg,,,\n",
                encoding="utf-8",
            )

            summary = build_package(closure, pressure_dir, thermal, output)

            self.assertEqual(summary["numeric_triplet_complete_count"], 2)
            self.assertGreaterEqual(summary["publication_ready_count"], 1)
            decisions = (output / "closure_qoi_admission_decisions.csv").read_text(encoding="utf-8")
            self.assertIn("publication_ready", decisions)
            self.assertIn("blocked_missing_triplet_qoi", decisions)


if __name__ == "__main__":
    unittest.main()
