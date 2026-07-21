#!/usr/bin/env python3
"""Tests for AGENT-455 closure-QOI / leg-specific Internal-Nu resolution."""

from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from tools.analyze import build_closure_qoi_mesh_gci_resolution as resolution


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class ClosureQoiMeshGciResolutionTests(unittest.TestCase):
    def test_test_section_span_maps_to_upcomer(self) -> None:
        self.assertEqual(resolution.canonical_leg("test_section_span"), "upcomer_left_vertical")
        self.assertEqual(resolution.canonical_leg("test_section"), "upcomer_left_vertical")
        rows = resolution.geometry_taxonomy_rows()
        test_section = next(row for row in rows if row["span_or_segment"] == "test_section_span")
        self.assertEqual(test_section["parent_geometry"], "upcomer")
        self.assertEqual(test_section["upcomer_member"], "yes")

    def test_upcomer_row_cannot_be_single_stream_internal_nu_fit(self) -> None:
        row = {
            "case_id": "salt2",
            "review_admission_class": "fit_admissible",
            "internal_nu_fit_allowed": "true",
            "residual_owner_gate": "pass",
            "reverse_area_fraction": "0.01",
            "reverse_mass_fraction": "0.01",
        }
        evaluated = resolution.evaluate_candidate(
            "candidate",
            "fixture",
            row,
            "test_section_span",
            "Nu",
            "fixture.csv",
        )
        self.assertEqual(evaluated["canonical_leg_id"], "upcomer_left_vertical")
        self.assertEqual(evaluated["internal_nu_fit_allowed_now"], False)
        self.assertEqual(evaluated["admission_class"], "hybrid_recirculation_lane_only")

    def test_non_upcomer_requires_all_gates(self) -> None:
        row = {
            "case_id": "salt2",
            "review_admission_class": "fit_admissible",
            "internal_nu_fit_allowed": "true",
            "residual_owner_gate": "pass",
            "reverse_area_fraction": "0.01",
            "reverse_mass_fraction": "0.01",
        }
        original_mesh_gate = resolution.mesh_gate_for_current
        try:
            resolution.mesh_gate_for_current = lambda: "pass"  # type: ignore[assignment]
            admitted = resolution.evaluate_candidate("ok", "fixture", row, "right_leg", "Nu", "fixture.csv")
            self.assertTrue(admitted["internal_nu_fit_allowed_now"])

            blocked = dict(row)
            blocked["blockers"] = "wallHeatFlux_enthalpy_opposed_direction"
            rejected = resolution.evaluate_candidate("bad", "fixture", blocked, "right_leg", "Nu", "fixture.csv")
            self.assertFalse(rejected["internal_nu_fit_allowed_now"])
            self.assertIn("sign_heat_balance_gate=fail", rejected["reason"])
        finally:
            resolution.mesh_gate_for_current = original_mesh_gate  # type: ignore[assignment]

    def test_current_package_reports_zero_fit_rows_and_correct_parent(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            out = Path(tmp) / "out"
            summary = resolution.build_package(out)

            self.assertEqual(summary["test_section_parent_leg"], "upcomer_left_vertical")
            self.assertEqual(summary["fit_admissible_internal_nu_rows"], 0)
            self.assertEqual(summary["publication_ready_mesh_gci_rows"], 0)
            self.assertGreater(summary["upcomer_single_stream_exclusion_rows"], 0)

            candidate_rows = read_csv(out / "leg_specific_internal_nu_candidate_rows.csv")
            test_section_rows = [
                row
                for row in candidate_rows
                if row["reported_segment_or_span"] in {"test_section", "test_section_span", "test_section_complex"}
            ]
            self.assertTrue(test_section_rows)
            self.assertTrue(all(row["canonical_leg_id"] == "upcomer_left_vertical" for row in test_section_rows))

    def test_model_form_matrix_has_distinct_leg_lanes(self) -> None:
        branch_rows = read_csv(resolution.BRANCH_MASK)
        rows = resolution.model_form_rows(branch_rows)
        legs = {row["canonical_leg_id"] for row in rows}
        self.assertIn("heater_lower_leg", legs)
        self.assertIn("downcomer_right_vertical", legs)
        self.assertIn("cooler_hx_branch", legs)
        self.assertIn("upcomer_left_vertical", legs)
        upcomer = next(row for row in rows if row["canonical_leg_id"] == "upcomer_left_vertical")
        self.assertIn("recirculation", upcomer["future_internal_nu_correlation_lane"])


if __name__ == "__main__":
    unittest.main()
