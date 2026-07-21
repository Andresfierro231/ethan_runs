#!/usr/bin/env python3
"""Tests for the Phase 1 external-boundary/radiation package."""

from __future__ import annotations

import csv
import unittest

from tools.analyze import build_heatloss_phase1_external_bc_radiation_integration as phase1


class HeatlossPhase1ExternalBcRadiationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.summary = phase1.build()
        cls.schema = cls.read_csv("external_bc_dictionary_contract.csv")
        cls.boundary = cls.read_csv("external_bc_segment_role_audit.csv")
        cls.runtime = cls.read_csv("runtime_mode_matrix.csv")
        cls.radiation = cls.read_csv("radiation_semantics_audit.csv")
        cls.tests = cls.read_csv("radiation_analytic_tests.csv")
        cls.handoff = cls.read_csv("fluid_handoff_contract.csv")

    @classmethod
    def read_csv(cls, name: str) -> list[dict[str, str]]:
        with (phase1.OUT / name).open(newline="") as handle:
            return list(csv.DictReader(handle))

    def test_schema_has_required_contract_fields(self) -> None:
        fields = {row["field_name"] for row in self.schema}
        for field in {
            "case_id",
            "segment_id",
            "patch_group",
            "h_W_m2_K",
            "Ta_K",
            "Tsur_K",
            "emissivity",
            "area_m2",
            "coverage_factor",
            "drive_temperature_selector",
            "radiation_policy",
            "wallHeatFlux_runtime_allowed",
        }:
            self.assertIn(field, fields)

    def test_segment_role_coverage_is_explicit(self) -> None:
        self.assertEqual(self.summary["segment_role_rows"], 24)
        self.assertEqual(self.summary["case_count"], 3)
        self.assertTrue(all(row["boundary_field_availability_status"] for row in self.boundary))
        self.assertTrue(
            any(
                row["boundary_field_availability_status"]
                == "explicit_unavailable_active_cooler_sink_not_passive_external_bc"
                for row in self.boundary
            )
        )

    def test_predictive_mode_forbids_wallheatflux_runtime(self) -> None:
        self.assertTrue(
            all(row["wallHeatFlux_runtime_allowed_predictive"] == "false" for row in self.boundary)
        )
        predictive = next(row for row in self.runtime if row["mode"] == "predictive")
        self.assertEqual(predictive["wallHeatFlux_runtime_allowed"], "false")
        self.assertIn("realized CFD wallHeatFlux", predictive["forbidden_runtime_inputs"])

    def test_replay_mode_disables_extra_boundary_terms(self) -> None:
        replay = next(row for row in self.runtime if row["mode"] == "replay")
        self.assertEqual(replay["wallHeatFlux_runtime_allowed"], "true")
        self.assertEqual(replay["external_convection_term_allowed"], "false")
        self.assertEqual(replay["radiation_term_allowed"], "false")

    def test_radiation_off_is_sensitivity_only(self) -> None:
        sensitivity = next(row for row in self.runtime if row["mode"] == "diagnostic_sensitivity")
        self.assertEqual(sensitivity["radiation_policy"], "radiation_off_sensitivity")
        self.assertEqual(sensitivity["consumer_status"], "sensitivity_only")
        self.assertIn("calling radiation-off CFD parity", sensitivity["forbidden_runtime_inputs"])

    def test_analytic_radiation_contract_passes(self) -> None:
        self.assertEqual(self.summary["analytic_tests_failed"], 0)
        self.assertTrue(all(row["pass_fail"] == "pass" for row in self.tests))

    def test_handoff_keeps_external_mutations_separate(self) -> None:
        owners = {row["future_owner"] for row in self.handoff}
        self.assertIn("TODO-FLUID-EXTERNAL-BC-DICT", owners)
        self.assertIn("TODO-1D-RADIATION-CAPABILITY", owners)
        self.assertFalse(self.summary["fluid_edit"])
        self.assertFalse(self.summary["model_scoring_or_admission"])


if __name__ == "__main__":
    unittest.main()
