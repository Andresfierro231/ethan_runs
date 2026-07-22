#!/usr/bin/env python3
"""Focused checks for MF13 signed source/property heat-path preflight."""

from __future__ import annotations

import csv
import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "tools/analyze/build_mf13_signed_source_property_heat_path_release_preflight.py"
OUT_DIR = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_mf13_signed_source_property_heat_path_release_preflight"


class TestMF13SignedSourcePropertyPreflight(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        subprocess.run([sys.executable, str(SCRIPT)], cwd=ROOT, check=True)

    def read_csv(self, name: str) -> list[dict[str, str]]:
        with (OUT_DIR / name).open(newline="") as f:
            return list(csv.DictReader(f))

    def test_summary_fails_closed_without_release(self) -> None:
        summary = json.loads((OUT_DIR / "summary.json").read_text())
        self.assertEqual(summary["decision"], "signed_source_property_release_preflight_fail_closed")
        self.assertEqual(summary["source_family_rows"], 4)
        self.assertEqual(summary["setup_known_active_source_rows"], 3)
        self.assertEqual(summary["release_ready_rows"], 0)
        self.assertFalse(summary["source_property_release"])
        self.assertFalse(summary["validation_used"])
        self.assertFalse(summary["holdout_used"])
        self.assertFalse(summary["external_test_used"])
        self.assertFalse(summary["mf12_formula_smoke_unblocked"])
        self.assertFalse(summary["residual_absorbed_into_internal_nu"])

    def test_all_expected_heat_path_families_are_represented(self) -> None:
        rows = self.read_csv("signed_heat_path_release_preflight.csv")
        families = {(row["source_segment_id"], row["physical_role"]) for row in rows}
        self.assertEqual(
            families,
            {
                ("cooling_branch", "cooler"),
                ("lower_leg", "heater"),
                ("upcomer", "test_section"),
                ("downcomer_or_passive_wall", "passive_loss"),
            },
        )
        self.assertTrue(all(row["release_ready"] == "False" for row in rows))
        passive = [row for row in rows if row["physical_role"] == "passive_loss"][0]
        self.assertIn("independent_source_basis", passive["blocking_gap"])

    def test_release_gate_never_allows_release(self) -> None:
        rows = self.read_csv("source_property_release_gate.csv")
        self.assertGreaterEqual(len(rows), 8)
        self.assertTrue(all(row["release_allowed"] == "False" for row in rows))
        statuses = {row["status"] for row in rows}
        self.assertIn("fail_closed", statuses)
        gates = {row["gate"] for row in rows}
        self.assertIn("source_property_labels_released", gates)
        self.assertIn("same_qoi_projection_uq", gates)

    def test_split_boundaries_and_guardrails_are_explicit(self) -> None:
        case_rows = self.read_csv("case_split_source_values.csv")
        protected = [row for row in case_rows if row["split_role"] in {"validation", "holdout"}]
        self.assertGreater(len(protected), 0)
        self.assertTrue(all(row["claim_use_in_this_study"] == "protected_metadata_not_used" for row in protected))
        self.assertTrue(all(row["scoring_use_in_this_study"] == "not_scored" for row in case_rows))

        guardrails = self.read_csv("no_mutation_guardrails.csv")
        self.assertTrue(all(row["occurred"] == "False" for row in guardrails))

    def test_thesis_insert_preserves_claim_boundary(self) -> None:
        text = (OUT_DIR / "thesis_heat_path_preflight_insert.md").read_text()
        self.assertIn("fail closed preflight", text)
        self.assertIn("not a source/property release", text)
        self.assertIn("validation, holdout, and external-test rows are metadata-only", text)

    def test_next_queue_keeps_projection_uq_first(self) -> None:
        rows = self.read_csv("next_study_queue.csv")
        self.assertEqual(rows[0]["next_study"], "same_qoi_tp_projection_uq")
        self.assertEqual(rows[0]["current_status_after_mf13"], "next")
        self.assertIn("train_only_mf12_formula_smoke_after_release", {row["next_study"] for row in rows})


if __name__ == "__main__":
    unittest.main()
