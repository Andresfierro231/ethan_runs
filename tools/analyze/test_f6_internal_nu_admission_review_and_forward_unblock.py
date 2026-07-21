#!/usr/bin/env python3
"""Tests for AGENT-425 F6/internal-Nu admission review package."""

from __future__ import annotations

import csv
import json
import unittest

from tools.analyze import build_f6_internal_nu_admission_review_and_forward_unblock as build


class F6InternalNuAdmissionReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        build.build()
        cls.package = build.OUT

    def read_csv(self, name: str) -> list[dict[str, str]]:
        with (self.package / name).open(newline="", encoding="utf-8") as handle:
            return list(csv.DictReader(handle))

    def test_material_recirculation_blocks_f6_fit(self) -> None:
        row = {
            "Re": "100",
            "Pr": "20",
            "Ri": "10",
            "Gr": "1000",
            "Ra": "20000",
            "reverse_area_fraction": "0.25",
            "reverse_mass_fraction": "0.50",
            "secondary_velocity_fraction": "0.01",
        }

        status, fit_now, reason = build.f6_admission_decision(row)

        self.assertEqual(status, "diagnostic_onset_only_material_recirculation_not_f6_fit")
        self.assertEqual(fit_now, "no")
        self.assertIn("single-stream", reason)

    def test_positive_h_proxy_stays_section_effective_under_material_reverse_flow(self) -> None:
        row = {
            "wallHeatFlux_available": "true",
            "wallHeatFlux_W_m2": "-300",
            "delta_T_wall_bulk_K": "-5",
            "reverse_area_fraction": "0.30",
            "reverse_mass_fraction": "0.50",
            "Ri": "5",
            "secondary_velocity_fraction": "0.01",
        }

        status, fit_now, reason, h_proxy = build.internal_nu_decision(row)

        self.assertEqual(h_proxy, 60)
        self.assertEqual(status, "diagnostic_section_effective_material_recirculation_not_fit")
        self.assertEqual(fit_now, "no")
        self.assertIn("material reverse flow", reason)

    def test_negative_h_proxy_requires_sign_review(self) -> None:
        row = {
            "wallHeatFlux_available": "true",
            "wallHeatFlux_W_m2": "-300",
            "delta_T_wall_bulk_K": "5",
            "reverse_area_fraction": "0",
            "reverse_mass_fraction": "0",
            "Ri": "0.01",
            "secondary_velocity_fraction": "0.01",
        }

        status, fit_now, _, h_proxy = build.internal_nu_decision(row)

        self.assertEqual(h_proxy, -60)
        self.assertEqual(status, "diagnostic_sign_review_required")
        self.assertEqual(fit_now, "no")

    def test_heat_balance_gate_rejects_large_residual(self) -> None:
        row = {
            "segment": "lower_leg",
            "wall_vs_enthalpy_direction": "same_direction",
            "residual_fraction": "0.18",
            "blockers": "",
            "internal_nu_fit_allowed": "false",
        }

        gate, reason = build.heat_balance_gate_class(row)

        self.assertEqual(gate, "fail_heat_balance_residual")
        self.assertIn("10 percent", reason)

    def test_generated_package_keeps_final_states_blocked(self) -> None:
        summary = json.loads((self.package / "summary.json").read_text(encoding="utf-8"))

        self.assertEqual(summary["task"], "AGENT-425")
        self.assertEqual(summary["pm5_rows"], 12)
        self.assertEqual(summary["pm5_wallHeatFlux_rows"], 12)
        self.assertEqual(summary["f6_fit_admissible_rows"], 0)
        self.assertEqual(summary["internal_nu_fit_admissible_rows"], 0)
        self.assertEqual(summary["segment_heat_balance_pass_rows"], 0)
        self.assertEqual(summary["final_forward_v1_status"], "blocked_no_go_final_forward_v1_not_admitted")
        self.assertEqual(summary["final_hydraulic_residual_status"], "blocked_not_final")
        self.assertFalse(summary["native_solver_outputs_mutated"])

    def test_unblock_requirements_explain_hydraulic_and_internal_nu(self) -> None:
        rows = self.read_csv("final_forward_v1_unblock_requirements.csv")
        by_gate = {row["blocker_or_gate"]: row for row in rows}

        self.assertEqual(by_gate["final_hydraulic_residual"]["current_state"], "blocked_not_final")
        self.assertIn("straight friction", by_gate["final_hydraulic_residual"]["unblock_requirement"])
        self.assertEqual(by_gate["internal_nu"]["current_state"], "unlocked_for_review_not_admitted")
        self.assertEqual(by_gate["move_past_recirculation"]["may_use_current_pm5_rows"], "regime/onset evidence")


if __name__ == "__main__":
    unittest.main()
