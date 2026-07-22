#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import subprocess
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = REPO_ROOT / "work_products/2026-07/2026-07-22/2026-07-22_thermal_passive_h2_source_evidence_recovery"
BUILDER = REPO_ROOT / "tools/analyze/build_thermal_passive_h2_source_evidence_recovery.py"


def read_csv(path: Path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class PassiveH2SourceEvidenceRecoveryTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        subprocess.run([sys.executable, str(BUILDER)], cwd=REPO_ROOT, check=True, stdout=subprocess.PIPE, text=True)

    def test_summary_preserves_source_basis_without_release(self) -> None:
        summary = json.loads((OUT_DIR / "summary.json").read_text(encoding="utf-8"))
        self.assertEqual(summary["passive_family_rows"], 5)
        self.assertEqual(summary["source_basis_release_ready_rows"], 5)
        self.assertEqual(summary["runtime_setup_input_allowed_next_row_rows"], 5)
        self.assertEqual(summary["q_loss_operator_admissible_rows"], 5)
        self.assertEqual(summary["source_property_release_allowed_rows"], 0)
        self.assertEqual(summary["Qwall_release_allowed_rows"], 0)
        self.assertEqual(summary["numeric_q_loss_released_rows"], 0)
        self.assertEqual(summary["repair_run_allowed_rows"], 0)
        self.assertEqual(summary["candidate_freeze_allowed_rows"], 0)
        self.assertEqual(summary["forbidden_wallflux_runtime_input_rows"], 0)
        self.assertFalse(summary["source_property_release"])
        self.assertFalse(summary["qwall_release"])
        self.assertFalse(summary["numeric_q_loss_release"])
        self.assertFalse(summary["candidate_freeze"])
        self.assertFalse(summary["protected_scoring"])
        self.assertEqual(summary["setup_uq_smoke_status"], "smoke_complete")
        self.assertEqual(summary["setup_uq_variant_accepted_rows"], 33)
        self.assertEqual(summary["setup_uq_source_property_release_rows"], 0)
        self.assertEqual(summary["setup_uq_protected_scoring_rows"], 0)

    def test_family_matrix_is_setup_backed_and_no_leak(self) -> None:
        rows = read_csv(OUT_DIR / "passive_h2_family_evidence_recovery_matrix.csv")
        self.assertEqual(len(rows), 5)
        self.assertTrue(all(row["source_basis_release_ready_now"] == "True" for row in rows))
        self.assertTrue(all(row["q_loss_operator_admissible_next_use"] == "True" for row in rows))
        self.assertTrue(all(row["area_geometry_source_backed"] == "True" for row in rows))
        self.assertTrue(all(row["ambient_surrounding_source_backed"] == "True" for row in rows))
        self.assertTrue(all(row["layers_kappa_source_backed"] == "True" for row in rows))
        self.assertTrue(all(row["h_setup_dictionary_source_backed"] == "True" for row in rows))
        self.assertTrue(all(row["h_literature_correlation_admitted"] == "False" for row in rows))
        self.assertTrue(all(row["numeric_q_loss_released"] == "False" for row in rows))
        self.assertTrue(all(row["source_property_release_allowed"] == "False" for row in rows))
        self.assertTrue(all(row["Qwall_release_allowed"] == "False" for row in rows))
        self.assertTrue(all(row["realized_wallHeatFlux_runtime_input_allowed"] == "False" for row in rows))
        self.assertTrue(all(row["validation_temperature_runtime_input_allowed"] == "False" for row in rows))
        junction = [row for row in rows if row["source_family"] == "junction"][0]
        self.assertIn("mixed junction/stub wall-layer metadata", junction["remaining_missing_evidence"])

    def test_field_strength_names_numeric_q_as_gap(self) -> None:
        rows = read_csv(OUT_DIR / "source_backing_strength_by_field.csv")
        by_field = {row["field_or_issue"]: row for row in rows}
        self.assertEqual(by_field["geometry_area"]["current_status"], "source_backed_setup_input")
        self.assertEqual(by_field["q_loss_operator"]["current_status"], "operator_released_for_future_runtime_state")
        self.assertEqual(by_field["numeric_passive_heat_loss"]["current_status"], "not_released")
        self.assertEqual(by_field["numeric_passive_heat_loss"]["source_backed_now"], "False")
        self.assertIn("runtime state", by_field["q_loss_operator"]["missing_evidence_or_caveat"])
        self.assertIn("setup-legal", by_field["train_only_setup_uq_smoke"]["allowed_use_now"])

    def test_missing_evidence_and_claim_boundaries_are_publication_safe(self) -> None:
        missing = read_csv(OUT_DIR / "passive_h2_missing_evidence_after_recovery.csv")
        missing_ids = {row["missing_evidence_id"] for row in missing}
        self.assertEqual(missing_ids, {"M01", "M02", "M03", "M04", "M05"})
        claims = read_csv(OUT_DIR / "publication_claim_boundary.csv")
        by_claim = {row["claim"]: row for row in claims}
        self.assertEqual(by_claim["passive_H2 numeric passive heat losses are released"]["status"], "forbidden")
        self.assertEqual(
            by_claim["passive_H2 source/property, Qwall, repair, or candidate freeze is released"]["status"],
            "forbidden",
        )
        self.assertEqual(
            by_claim["passive_H2 has a source-backed setup-dictionary basis for external passive boundaries"]["status"],
            "allowed",
        )
        self.assertIn("operator path released; numeric q_loss not released", by_claim["passive_H2 can define a no-leak external q_loss operator"]["required_wording"])

    def test_source_manifest_exists_and_is_read_only(self) -> None:
        rows = read_csv(OUT_DIR / "source_manifest.csv")
        self.assertGreaterEqual(len(rows), 10)
        self.assertTrue(all(row["exists"] == "True" for row in rows))
        self.assertTrue(all(row["mutation_status"] == "read_only" for row in rows))


if __name__ == "__main__":
    unittest.main()
