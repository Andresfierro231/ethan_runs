#!/usr/bin/env python3
"""Tests for TODO-PRED-HYDRAULIC-GATE builder."""

from __future__ import annotations

import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.analyze.build_predictive_hydraulic_gate import build_package


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


class PredictiveHydraulicGateTests(unittest.TestCase):
    def test_build_package_separates_fit_safe_rows_and_mdot_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pressure_dir = root / "pressure"
            gci_dir = root / "gci"
            forward_dir = root / "forward"
            out_dir = root / "out"
            write(
                pressure_dir / "summary.json",
                json.dumps(
                    {
                        "thermal_closure_status": "blocked",
                        "pressure_gradient_fit_safe_spans": ["left_lower_leg"],
                        "momentum_corrected_fit_safe_spans": ["left_lower_leg", "upper_leg"],
                    }
                ),
            )
            write(
                pressure_dir / "fit_safety_summary.csv",
                "lane,span,fit_safety,basis,medium_f,fine_f,delta_pct\n"
                "pressure_gradient_friction,left_lower_leg,fit_safe_pressure_gradient,positive_loss_both_meshes,1.8,1.81,0.5\n"
                "pressure_gradient_friction,upper_leg,not_fit_safe_pressure_recovery_or_noise,pressure_recovery_or_noise_flagged,-11,-11.2,-1.8\n"
                "momentum_corrected_friction,left_lower_leg,fit_safe_momentum_corrected,corrected_f_positive_both_meshes,1.35,1.36,0.7\n"
                "momentum_corrected_friction,upper_leg,fit_safe_momentum_corrected,corrected_f_positive_both_meshes; strong_buoyancy_correction,2.2,2.24,2.0\n",
            )
            write(
                gci_dir / "summary.json",
                json.dumps({"thermal_status": "blocked_missing_fine_thermal_extraction"}),
            )
            write(
                gci_dir / "closure_qoi_admission_decisions.csv",
                "case_id,qoi_id,lane,span,method,quantity,numeric_triplet_complete,source_gate,gci_verdict,gci_trustworthy,publication_ready,admission_decision,blocker,recommended_use\n"
                "salt_2,q1,pressure_gradient_friction,left_lower_leg,section_mean_static_gradient,apparent_darcy_f,yes,medium_fine_source_rows_admitted,oscillatory,no,no,blocked_gci_not_trustworthy,gci failed,diagnostic\n"
                "salt_2,q2,momentum_corrected_friction,left_lower_leg,streamwise_momentum_budget_debuoyed,f_corrected,yes,medium_fine_source_rows_admitted,oscillatory,no,no,blocked_gci_not_trustworthy,gci failed,diagnostic\n",
            )
            write(
                forward_dir / "forward_v0_results.csv",
                "case_id,fluid_case_name,source_id,variant_id,engine,root_status,accepted_for_validation,mdot_kg_s,cfd_mdot_kg_s,mdot_error_vs_cfd_kg_s,mdot_error_vs_experimental_kg_s,velocity_main_m_s,reynolds_main,pressure_residual_Pa,deltaP_buoyancy_Pa,deltaP_losses_Pa\n"
                "salt_2,Salt 2,source,F0_current_fluid_sources,fast_scan,root,True,0.020,0.013,0.007,0.003,0.02,100,1.1,43,44\n"
                "salt_2,Salt 2,source,F1_heater_only,fast_scan,root,True,0.018,0.013,0.005,0.001,0.02,100,1.0,52,53\n",
            )

            summary = build_package(out_dir, pressure_dir, gci_dir, forward_dir)

            self.assertEqual(summary["pressure_gradient_fit_safe_spans"], ["left_lower_leg"])
            self.assertEqual(
                summary["hydraulic_gate_status"],
                "blocked_for_thermal_claim_mdot_overpredicted",
            )
            self.assertEqual(summary["thermal_closure_status"], "blocked")
            fit_rows = read_csv(out_dir / "hydraulic_fit_safety_gate.csv")
            upper = next(
                row
                for row in fit_rows
                if row["lane"] == "pressure_gradient_friction" and row["span"] == "upper_leg"
            )
            self.assertEqual(upper["gate_decision"], "not_fit_safe_for_training")
            residuals = read_csv(out_dir / "forward_v0_hydraulic_residuals.csv")
            self.assertTrue(
                all(
                    row["hydraulic_interpretation"]
                    == "pressure_root_converged_but_mdot_overpredicted"
                    for row in residuals
                )
            )
            decisions = read_csv(out_dir / "hydraulic_gate_decisions.csv")
            self.assertTrue(any(row["gate_item"] == "thermal_closure" for row in decisions))


if __name__ == "__main__":
    unittest.main()
