#!/usr/bin/env python3.11
"""Tests for the MF10 train-only variant bakeoff gate."""

from __future__ import annotations

import csv
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.analyze.build_mf10_entrance_wallflux_train_only_variant_bakeoff import OUT_DIR, build


def rows(name: str) -> list[dict[str, str]]:
    with (OUT_DIR / name).open(newline="") as f:
        return list(csv.DictReader(f))


class MF10EntranceWallfluxTrainOnlyVariantBakeoffTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        build()

    def test_summary_diagnostic_no_new_scoring(self) -> None:
        summary = json.loads((OUT_DIR / "summary.json").read_text())
        self.assertEqual(summary["decision"], "diagnostic_only")
        self.assertEqual(summary["variant_rows"], 6)
        self.assertFalse(summary["new_train_support_scoring_executed"])
        self.assertEqual(summary["smoke_ready_variants"], 0)
        self.assertEqual(summary["candidate_ready_variants"], 0)
        self.assertEqual(summary["validation_holdout_external_rows_scored"], 0)
        self.assertFalse(summary["source_property_release"])
        self.assertFalse(summary["coefficient_admission"])
        self.assertFalse(summary["final_score"])

    def test_required_variants_present_and_blocked(self) -> None:
        variants = {r["variant_id"]: r for r in rows("variant_bakeoff_matrix.csv")}
        self.assertIn("MF10b_hydraulic_development_only", variants)
        self.assertIn("MF10c_signed_thermal_development_only", variants)
        self.assertIn("MF10e_combined_with_mf09_exchange_cell_upcomer", variants)
        self.assertEqual(variants["MF10e_combined_with_mf09_exchange_cell_upcomer"]["primary_blocker"], "blocked_mf09_mesh_gci_source_basis")
        self.assertTrue(all(r["smoke_ready_now"] == "false" for r in variants.values()))
        self.assertTrue(all(r["candidate_ready_now"] == "false" for r in variants.values()))

    def test_metrics_are_existing_context_only(self) -> None:
        metrics = {r["variant_id"]: r for r in rows("train_support_metric_table.csv")}
        self.assertEqual(metrics["MF10a_fully_developed_baseline"]["metric_status"], "existing_scoreboard_numeric_context_not_new_scoring")
        self.assertEqual(metrics["MF10f_no_upcomer_correction_negative_control"]["source_metric_model_form"], "M3")
        self.assertTrue(all(r["support_metric_rows"] == "0" for r in metrics.values()))

    def test_runtime_and_production_gates_fail_closed(self) -> None:
        runtime = {r["guardrail"]: r["pass"] for r in rows("runtime_leakage_audit.csv")}
        self.assertEqual(runtime["validation_holdout_external_rows_used"], "true")
        self.assertEqual(runtime["new_fitting_or_model_selection"], "true")
        gates = {r["gate"]: r for r in rows("production_gate.csv")}
        self.assertEqual(gates["train_only_bakeoff_execution"]["status"], "blocked")
        self.assertEqual(gates["diagnostic_only"]["status"], "selected")
        self.assertEqual(gates["candidate_for_source_property_audit"]["pass"], "false")


if __name__ == "__main__":
    unittest.main()
