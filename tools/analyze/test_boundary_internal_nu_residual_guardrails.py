#!/usr/bin/env python3
"""Tests for build_boundary_internal_nu_residual_guardrails.py."""

from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path

from tools.analyze import build_boundary_internal_nu_residual_guardrails as guardrails


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class BoundaryInternalNuResidualGuardrailTests(unittest.TestCase):
    def test_residual_rows_cover_required_owners_and_exclude_internal_nu(self) -> None:
        rows = guardrails.residual_rows()
        residual_ids = {row["residual_id"] for row in rows}

        self.assertTrue(
            {
                "heater_realized_fraction",
                "cooler_hx_removal",
                "wall_layer_external_convection",
                "radiation_metadata",
                "wall_storage_transient",
                "branch_mixing_recirculation",
                "internal_convection_development",
            }
            <= residual_ids
        )
        for row in rows:
            joined = " ".join(
                [
                    row["internal_nu_guardrail"],
                    row["excluded_internal_nu_use"],
                    row["allowed_use"],
                ]
            ).lower()
            self.assertIn("nu", joined)
            self.assertRegex(joined, r"do not|0 fit-admissible|closed today|keep rows out")

    def test_field_rows_include_boundary_and_upcomer_overlap_metrics(self) -> None:
        rows = guardrails.field_rows()
        field_ids = {row["field_id"] for row in rows}

        self.assertTrue(
            {
                "bulk_temperature",
                "wall_inner_temperature",
                "wall_shell_temperature",
                "wall_heat_flux",
                "external_radiation_metadata",
                "recirculation_vector_metrics",
                "thermal_development_groups",
            }
            <= field_ids
        )
        for row in rows:
            self.assertNotEqual(row["window_and_plane_rule"], "")
            self.assertNotEqual(row["source_path_or_owner_to_preserve"], "")
            self.assertNotEqual(row["double_count_guardrail"], "")

    def test_radiation_row_preserves_no_double_count_semantics(self) -> None:
        row = next(row for row in guardrails.residual_rows() if row["residual_id"] == "radiation_metadata")

        self.assertIn("embedded", row["boundary_model_form_or_ledger"])
        self.assertIn("no exported qr", row["diagnostic_cfd_quantities"])
        self.assertIn("Do not create a radiation residual inside internal Nu", row["excluded_internal_nu_use"])

    def test_build_package_writes_acceptance_artifacts(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            out = Path(tmp)
            summary = guardrails.build_package(out)

            self.assertEqual(summary["task"], "AGENT-336")
            self.assertEqual(summary["internal_nu_fit_admissible_rows_today"], 0)
            self.assertFalse(summary["native_solver_outputs_mutated"])
            self.assertFalse(summary["external_fluid_modified"])
            self.assertTrue((out / "thermal_residual_ownership_guardrails.csv").exists())
            self.assertTrue((out / "boundary_fields_needed_for_upcomer_extraction.csv").exists())
            self.assertTrue((out / "README.md").exists())

            residuals = read_csv(out / "thermal_residual_ownership_guardrails.csv")
            fields = read_csv(out / "boundary_fields_needed_for_upcomer_extraction.csv")
            parsed = json.loads((out / "summary.json").read_text(encoding="utf-8"))
            self.assertEqual(parsed["residual_guardrail_rows"], len(residuals))
            self.assertEqual(parsed["boundary_field_rows"], len(fields))


if __name__ == "__main__":
    unittest.main()
