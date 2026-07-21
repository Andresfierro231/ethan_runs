#!/usr/bin/env python3
"""Tests for AGENT-300 hydraulic correction candidate builder."""

from __future__ import annotations

import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.analyze.build_predictive_hydraulic_correction_candidates import build_package


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


class PredictiveHydraulicCorrectionCandidatesTests(unittest.TestCase):
    def test_build_package_separates_raw_and_diagnostic_lanes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            gate_dir = root / "gate"
            reset_named_dir = root / "reset_named"
            out_dir = root / "out"
            write(
                gate_dir / "hydraulic_fit_safety_gate.csv",
                "lane,span,fit_safety,basis,medium_value,fine_value,delta_pct,gci_admission_decision,gci_verdict,gci_publication_ready,gate_decision,allowed_use\n"
                "pressure_gradient_friction,left_lower_leg,fit_safe_pressure_gradient,positive_loss_both_meshes,1.7,1.8,1.0,blocked,oscillatory,no,fit_safe_but_gci_not_publication_ready,may_screen\n"
                "pressure_gradient_friction,upper_leg,not_fit_safe_pressure_recovery_or_noise,pressure_recovery_or_noise_flagged,-11,-11.2,-1.0,diagnostic,oscillatory,no,not_fit_safe_for_training,diagnostic_only\n"
                "momentum_corrected_friction,left_lower_leg,fit_safe_momentum_corrected,corrected_f_positive_both_meshes,1.3,1.4,1.0,blocked,oscillatory,no,fit_safe_momentum_corrected_diagnostic,may_inform\n"
                "momentum_corrected_friction,upper_leg,fit_safe_momentum_corrected,corrected_f_positive_both_meshes; strong_buoyancy_correction,2.2,2.3,2.0,blocked,oscillatory,no,fit_safe_momentum_corrected_diagnostic,may_inform\n",
            )
            write(
                gate_dir / "forward_v0_hydraulic_residuals.csv",
                "case_id,fluid_case_name,variant_id,engine,accepted_for_validation,mdot_kg_s,cfd_mdot_kg_s,mdot_error_vs_cfd_kg_s,mdot_error_vs_cfd_pct,mdot_error_vs_experimental_kg_s,pressure_residual_Pa,deltaP_buoyancy_Pa,deltaP_losses_Pa,root_status,hydraulic_interpretation\n"
                "salt_2,Salt 2,F1_heater_only,fast_scan,True,0.018,0.012,0.006,50,0.001,1.0,50,51,root,over\n",
            )
            write(
                reset_named_dir / "named_pressure_loss_table.csv",
                "source_id,case_id,name,loss_class,span_or_feature,pressure_basis,velocity_basis,plane_or_tap_span,included_fittings,delta_p_basis_pa,straight_loss_correction_pa,K_local,K_apparent,f_D_delta_p,fit_use_status,coefficient_naming_status,source_status,provenance_author_title,source_path,quality_flags\n"
                "s,salt_2,straight_section:test_section_span,straight_section,test_section_span,basis,q,a->b,straight,1,1,,,1.2,fit_target,candidate,pressure_ledger,source,path,coarse_no_gci\n",
            )
            write(
                reset_named_dir / "reset_distance_map.csv",
                "source_id,case_id,feature_or_span,reset_type,downstream_span,orientation,x_from_reset_m,L_over_D_from_reset,thermal_reset_status,hydraulic_reset_status,provenance_author_title,source_path,quality_flags\n"
                "s,salt_2,lower_leg,section_endpoint_or_recent_feature,lower_leg,mostly_horizontal,0.3,15,unknown,reset_flagged,source,path,coarse_no_gci\n",
            )

            summary = build_package(out_dir, gate_dir, reset_named_dir)

            self.assertFalse(summary["thermal_fit_used"])
            self.assertEqual(summary["raw_fit_safe_spans"], ["left_lower_leg"])
            self.assertEqual(
                summary["diagnostic_momentum_corrected_spans"],
                ["left_lower_leg", "upper_leg"],
            )
            raw_rows = read_csv(out_dir / "fit_safe_raw_pressure_rows.csv")
            diagnostic_rows = read_csv(out_dir / "diagnostic_momentum_corrected_rows.csv")
            self.assertEqual(len(raw_rows), 1)
            self.assertEqual(len(diagnostic_rows), 2)
            scaling = read_csv(out_dir / "mdot_resistance_scaling.csv")
            self.assertAlmostEqual(float(scaling[0]["required_resistance_multiplier"]), 2.25)
            candidates = read_csv(out_dir / "candidate_rankings.csv")
            self.assertEqual(candidates[0]["candidate_id"], "H1_localized_named_loss_and_reset_bundle")
            self.assertEqual(candidates[-1]["admission_status"], "blocked")
            self.assertTrue((out_dir / "README.md").exists())
            self.assertTrue((out_dir / "decision_summary.json").exists())


if __name__ == "__main__":
    unittest.main()
