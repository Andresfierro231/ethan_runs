#!/usr/bin/env python3
"""Tests for Phase 2 split heat-loss evidence artifacts."""

from __future__ import annotations

import csv
import unittest

from tools.analyze import build_heatloss_phase2_split_heat_loss_evidence as phase2


class HeatlossPhase2SplitEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.summary = phase2.build()
        cls.split = cls.read_csv("split_junction_stub_heat_rows.csv")
        cls.matrix = cls.read_csv("heat_path_evidence_matrix.csv")
        cls.owners = cls.read_csv("energy_residual_owner_matrix.csv")
        cls.missing = cls.read_csv("missing_field_queue.csv")
        cls.runtime = cls.read_csv("runtime_legality_audit.csv")

    @classmethod
    def read_csv(cls, name: str) -> list[dict[str, str]]:
        with (phase2.OUT / name).open(newline="") as handle:
            return list(csv.DictReader(handle))

    def test_junction_split_has_four_families_per_case(self) -> None:
        self.assertEqual(self.summary["split_junction_rows"], 12)
        self.assertEqual(
            set(self.summary["junction_families"]),
            {"lower_left", "lower_right", "upper_left", "upper_right"},
        )
        for case_id in {row["case_id"] for row in self.split}:
            self.assertEqual(sum(row["case_id"] == case_id for row in self.split), 4)

    def test_junction_split_is_not_admitted_target(self) -> None:
        self.assertTrue(
            all(row["split_status"] == "estimated_from_grouped_junction_row_not_new_sampling" for row in self.split)
        )
        self.assertTrue(all("forbidden predictive" in row["runtime_legality"] for row in self.split))

    def test_heat_path_matrix_keeps_core_lanes(self) -> None:
        lanes = ";".join(row["heat_path"] for row in self.matrix)
        for token in (
            "heater_source_to_fluid",
            "jacket_cooler_removal",
            "junction_stub_heat",
            "insulation_quartz",
            "external_convection",
        ):
            self.assertIn(token, lanes)

    def test_qr_and_storage_absence_are_explicit(self) -> None:
        missing = {row["missing_field_id"]: row for row in self.missing}
        self.assertEqual(missing["qr_separate_radiation_output"]["current_status"], "absent_no_qr_output")
        self.assertEqual(
            missing["solid_storage_or_wall_energy_time_derivative"]["current_status"],
            "absent_no_solid_storage_field",
        )
        self.assertEqual(self.summary["qr_output_rows_admitted"], 0)
        self.assertEqual(self.summary["solid_storage_runtime_rows_admitted"], 0)

    def test_residual_owner_rows_preserve_upcomer_gate(self) -> None:
        upcomer = [row for row in self.owners if row["physical_segment"] == "upcomer"]
        self.assertTrue(upcomer)
        self.assertTrue(
            all(
                row["next_owner"] == "TODO-HEATLOSS-PHASE-4-UPCOMER-EXCHANGE-AND-INTERNAL-NU-GATE"
                for row in upcomer
            )
        )

    def test_runtime_audit_forbids_leakage_and_scoring(self) -> None:
        policies = " ".join(row["policy"] for row in self.runtime)
        self.assertIn("forbidden predictive wallHeatFlux", policies)
        self.assertIn("no fitting/model selection/admission", policies)
        self.assertFalse(self.summary["model_scoring_or_admission"])


if __name__ == "__main__":
    unittest.main()
