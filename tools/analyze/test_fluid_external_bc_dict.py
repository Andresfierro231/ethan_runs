#!/usr/bin/env python3
"""Tests for the Fluid external-boundary dictionary contract package."""

from __future__ import annotations

import csv
import unittest

from tools.analyze import build_fluid_external_bc_dict as extbc


class FluidExternalBcDictTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.summary = extbc.build()
        cls.schema = cls.read_csv("fluid_external_boundary_schema.csv")
        cls.runtime = cls.read_csv("fluid_external_boundary_runtime_dictionary.csv")
        cls.modes = cls.read_csv("allowed_runtime_mode_table.csv")
        cls.validation = cls.read_csv("validation_cases.csv")
        cls.handoff = cls.read_csv("fluid_handoff_stubs.csv")
        cls.audit = cls.read_csv("runtime_leakage_audit.csv")

    @classmethod
    def read_csv(cls, name: str) -> list[dict[str, str]]:
        with (extbc.OUT / name).open(newline="", encoding="utf-8") as handle:
            return list(csv.DictReader(handle))

    def test_schema_contains_required_runtime_fields(self) -> None:
        fields = {row["field_name"] for row in self.schema}
        for field in extbc.REQUIRED_RUNTIME_FIELDS:
            self.assertIn(field, fields)
        self.assertGreaterEqual(self.summary["schema_rows"], len(extbc.REQUIRED_RUNTIME_FIELDS))

    def test_runtime_dictionary_covers_phase1_rows(self) -> None:
        phase1_rows = extbc.read_csv(extbc.PHASE1_SEGMENTS)
        self.assertEqual(len(self.runtime), len(phase1_rows))
        self.assertEqual(self.summary["runtime_dictionary_rows"], len(phase1_rows))
        self.assertGreater(self.summary["predictive_passive_external_rows"], 0)
        self.assertGreater(self.summary["document_only_source_sink_rows"], 0)

    def test_predictive_rows_use_setup_fields_only(self) -> None:
        predictive = [row for row in self.runtime if row["mode"] == "predictive"]
        self.assertTrue(predictive)
        for row in predictive:
            self.assertEqual(row["runtime_heat_flux_policy"], "forbidden: realized wall heat flux is diagnostic only")
            self.assertIn(row["convection_active"], {"true", "false"})
            self.assertIn(row["radiation_active"], {"true", "false"})
            self.assertNotIn("wallHeatFlux", row)

    def test_modes_keep_replay_and_predictive_radiation_separate(self) -> None:
        modes = {row["mode"]: row for row in self.modes}
        self.assertIn("predictive", modes)
        self.assertIn("replay", modes)
        self.assertIn("external_convection", modes["predictive"]["computed_terms"])
        self.assertIn("separate predictive convection or radiation", modes["replay"]["forbidden_runtime_inputs"])

    def test_validation_and_handoff_are_complete(self) -> None:
        self.assertEqual(self.summary["validation_case_rows"], 5)
        self.assertEqual(self.summary["fluid_handoff_stub_rows"], 3)
        self.assertTrue(all(row["expected_status"] == "pass" for row in self.validation))
        stub_ids = {row["stub_id"] for row in self.handoff}
        self.assertEqual(
            stub_ids,
            {"ExternalBoundaryRecord", "ExternalBoundaryModePolicy", "ExternalBoundaryHeatPathLedger"},
        )

    def test_guardrails_record_no_mutating_work(self) -> None:
        self.assertTrue(all(row["status"] == "pass" for row in self.audit))
        self.assertFalse(self.summary["external_fluid_edit"])
        self.assertFalse(self.summary["native_solver_outputs_mutated"])
        self.assertFalse(self.summary["registry_or_admission_mutated"])
        self.assertFalse(self.summary["scheduler_action"])
        self.assertFalse(self.summary["solver_or_postprocessing_launched"])
        self.assertFalse(self.summary["fitting_or_model_selection_performed"])


if __name__ == "__main__":
    unittest.main()
