#!/usr/bin/env python3
"""Tests for thesis diagnostic-evidence integration package."""

from __future__ import annotations

import csv
import json
import unittest
from pathlib import Path

import build_thesis_diagnostic_evidence_integration as builder


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / builder.OUT_REL


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class ThesisDiagnosticEvidenceIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        builder.build()

    def test_claim_matrix_has_all_required_themes_and_boundaries(self) -> None:
        rows = read_csv(OUT / "diagnostic_claim_matrix.csv")
        claim_ids = {row["claim_id"] for row in rows}
        self.assertEqual(
            claim_ids,
            {
                "recirculation_guard",
                "energy_residual_attribution",
                "ordinary_upcomer_closure_exclusion",
                "pressure_residual_ownership",
                "thermal_residual_ownership",
            },
        )
        for row in rows:
            self.assertTrue(row["source_paths"])
            self.assertIn("not_admitted", row["admission_status"])
            self.assertIn("Do not", row["forbidden_claim"])
            self.assertIn("Diagnostic evidence", row["claim_boundary"])

    def test_s4_negative_admission_counts_are_preserved(self) -> None:
        summary = json.loads((OUT / "summary.json").read_text(encoding="utf-8"))
        self.assertEqual(summary["ordinary_candidate_rows_reviewed"], 90)
        self.assertEqual(summary["ordinary_closure_admitted_rows"], 0)
        self.assertEqual(summary["ordinary_upcomer_Nu_fD_K_admitted_rows"], 0)
        self.assertEqual(summary["exchange_cell_coefficient_admitted_rows"], 0)
        self.assertEqual(summary["scoreable_now_rows"], 0)

    def test_no_runtime_or_admission_side_effects_are_claimed(self) -> None:
        summary = json.loads((OUT / "summary.json").read_text(encoding="utf-8"))
        self.assertFalse(summary["phase4b_ready"])
        self.assertEqual(summary["phase5_trigger"], "not_triggered")
        self.assertFalse(summary["final_predictive_score_claim"])
        for key in [
            "native_solver_outputs_mutated",
            "registry_mutated",
            "admission_state_mutated",
            "scheduler_action",
            "fluid_or_external_edit",
            "fit_or_model_selection_performed",
            "sampler_or_harvest_launched",
            "blocker_register_mutated",
        ]:
            self.assertFalse(summary[key], key)

    def test_residual_ownership_matrix_covers_pressure_and_thermal_lanes(self) -> None:
        rows = read_csv(OUT / "residual_ownership_matrix.csv")
        families = {row["residual_family"] for row in rows}
        self.assertIn("pressure_corner_residual", families)
        self.assertIn("thermal_energy_residual", families)
        self.assertIn("thermal_wall_test_section", families)
        self.assertIn("upcomer_exchange_or_internal_Nu", families)
        for row in rows:
            self.assertTrue(row["forbidden_use"])
            self.assertTrue(row["next_evidence_needed"])

    def test_figure_table_ledger_includes_integration_and_s4_tables(self) -> None:
        rows = read_csv(OUT / "figure_table_ledger_update.csv")
        artifacts = {row["artifact"] for row in rows}
        self.assertIn(str(builder.OUT_REL / "ordinary_closure_exclusion_table.csv"), artifacts)
        self.assertIn(str(builder.OUT_REL / "residual_ownership_matrix.csv"), artifacts)
        self.assertIn(str(builder.S4.relative_to(ROOT) / "ordinary_closure_disable_table.csv"), artifacts)
        self.assertIn(str(builder.S4.relative_to(ROOT) / "reverse_flow_onset_evidence_ledger.csv"), artifacts)


if __name__ == "__main__":
    unittest.main()
