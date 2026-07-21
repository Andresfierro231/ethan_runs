#!/usr/bin/env python3
"""Tests for build_heater_test_section_contract.py."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.analyze import build_heater_test_section_contract as contract  # noqa: E402


class HeaterTestSectionContractTests(unittest.TestCase):
    def test_heat_ledger_keeps_roles_separate_and_wallflux_diagnostic(self) -> None:
        rows = contract.heat_ledger_rows(
            [
                base_section("salt_x", "heater", imposed_source_W="100", realized_source_W="90"),
                base_section("salt_x", "test_section", imposed_source_W="37", realized_loss_W="5"),
                base_section("salt_x", "cooler", realized_loss_W="80"),
                base_section("salt_x", "ambient_wall", realized_loss_W="2"),
                base_section("salt_x", "junction_other", realized_loss_W="3"),
            ]
        )

        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertAlmostEqual(row["heater_realized_efficiency_diagnostic"], 0.9)
        self.assertEqual(row["test_section_setup_power_W"], 37.0)
        self.assertEqual(row["test_section_realized_external_loss_W"], 5.0)
        self.assertEqual(row["cooler_imposed_or_realized_loss_W"], 80.0)
        self.assertEqual(row["passive_external_realized_loss_W"], 5.0)
        self.assertEqual(row["wallHeatFlux_runtime_use"], "diagnostic_only_not_forward_runtime_input")

    def test_interpretation_requires_negative_added_heat_when_heater_only_is_hot(self) -> None:
        ledger = [
            {
                "case_id": "salt_x",
                "source_id": "source",
                "heater_setup_power_W": 100.0,
                "test_section_setup_power_W": 37.0,
            }
        ]
        forward = [
            base_forward("salt_x", "F0_current_fluid_sources", model_Tmean_proxy_K="487", cfd_Tmean_K="450"),
            base_forward("salt_x", "F1_heater_only", model_Tmean_proxy_K="457", cfd_Tmean_K="450"),
        ]

        rows = contract.interpretation_rows(forward, ledger)

        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertAlmostEqual(row["test_source_sensitivity_K_per_W"], 30.0 / 37.0)
        self.assertLess(row["equivalent_delta_Q_needed_vs_heater_only_W"], 0.0)
        self.assertLess(row["equivalent_test_section_fluid_fraction_fit"], 0.0)
        self.assertGreater(row["equivalent_test_section_external_loss_fit_W"], 0.0)

    def test_candidate_table_recommends_unfitted_heater_only_and_blocks_wallflux_runtime(self) -> None:
        variant_summary = [
            {
                "variant_id": "F0_current_fluid_sources",
                "mean_abs_Tmean_error_vs_cfd_K": "34.374",
                "mean_mdot_error_vs_cfd_kg_s": "0.00808",
            },
            {
                "variant_id": "F1_heater_only",
                "mean_abs_Tmean_error_vs_cfd_K": "4.609",
                "mean_mdot_error_vs_cfd_kg_s": "0.00548",
            },
        ]
        interpretation = [
            {
                "equivalent_delta_Q_needed_vs_heater_only_W": -5.0,
                "equivalent_eta_heater_fit": 0.98,
                "equivalent_test_section_external_loss_fit_W": 5.0,
                "equivalent_test_section_fluid_fraction_fit": -0.135,
            }
        ]
        ledger = [
            {
                "heater_realized_efficiency_diagnostic": 0.92,
                "test_section_realized_external_loss_W": 10.0,
            }
        ]

        rows = contract.candidate_rows(variant_summary, interpretation, ledger)
        recommended = [row for row in rows if row["recommendation_status"] == "recommend_next_admissible_model"]
        diagnostic = [row for row in rows if row["runtime_class"] == "diagnostic_only_cfd_evidence"]

        self.assertEqual([row["candidate_id"] for row in recommended], ["C1_heater_only_predictive_setup"])
        self.assertEqual(recommended[0]["test_section_fluid_fraction"], "0.0")
        self.assertEqual(diagnostic[0]["wallHeatFlux_runtime_use"], "diagnostic_only_not_forward_runtime_input")
        self.assertIn("reject", next(row for row in rows if row["candidate_id"] == "C4_test_section_fluid_fraction_fit")["admissibility"])


def base_section(case_id: str, role: str, **overrides: str) -> dict[str, str]:
    row = {
        "case_id": case_id,
        "source_id": f"{case_id}_source",
        "role": role,
        "imposed_source_W": "0",
        "realized_source_W": "0",
        "realized_loss_W": "0",
    }
    row.update(overrides)
    return row


def base_forward(case_id: str, variant_id: str, **overrides: str) -> dict[str, str]:
    row = {
        "case_id": case_id,
        "variant_id": variant_id,
        "model_Tmean_proxy_K": "0",
        "cfd_Tmean_K": "0",
        "Tmean_error_vs_cfd_K": "0",
    }
    row.update(overrides)
    return row


if __name__ == "__main__":
    unittest.main()
