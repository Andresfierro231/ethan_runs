#!/usr/bin/env python3.11
"""Tests for the S12 TP-first upcomer-exchange evidence gate."""

from __future__ import annotations

import csv
import json
import unittest
from pathlib import Path

from tools.analyze.build_s12_tp_first_upcomer_exchange_evidence_gate import OUT, build


def rows(name: str) -> list[dict[str, str]]:
    with (OUT / name).open(newline="") as f:
        return list(csv.DictReader(f))


class S12TpFirstEvidenceGateTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        build()

    def test_summary_is_fail_closed(self) -> None:
        summary = json.loads((OUT / "summary.json").read_text())
        self.assertEqual(summary["decision"], "tp_first_s12_exchange_continuation_diagnostic_only")
        self.assertEqual(summary["production_ready_rows"], 0)
        self.assertFalse(summary["s12_freeze_allowed"])
        self.assertFalse(summary["source_property_or_qwall_release"])
        self.assertFalse(summary["protected_split_scoring"])
        self.assertFalse(summary["residual_absorbed_into_internal_nu"])

    def test_tp_priority_context_uses_m3_and_tp_is_lower_than_tw(self) -> None:
        context = rows("s12_tp_priority_context.csv")
        self.assertEqual(len(context), 3)
        self.assertTrue(all(r["model_form_id"] == "M3" for r in context))
        self.assertTrue(all(float(r["tp_rmse_K"]) < float(r["tw_rmse_K"]) for r in context))
        self.assertTrue(all(r["candidate_use"] == "context_only_not_final_locked_split" for r in context))

    def test_exchange_evidence_remains_diagnostic_only(self) -> None:
        evidence = rows("s12_tp_exchange_evidence_table.csv")
        self.assertEqual(len(evidence), 3)
        self.assertTrue(all(r["release_status"] == "diagnostic_only_no_production_harvest_no_coefficient_admission" for r in evidence))
        self.assertTrue(all(float(r["tau_recirc_proxy_s"]) > 0.0 for r in evidence))

    def test_gate_matrix_names_true_blockers(self) -> None:
        gate_rows = rows("s12_tp_unlock_gate_matrix.csv")
        gates = {r["gate"]: r for r in gate_rows}
        for gate in [
            "source_property_conservation_release",
            "same_qoi_uq",
            "production_harvest",
            "finite_exchange_proxy_rows",
        ]:
            self.assertIn(gate, gates)
        self.assertEqual(gates["source_property_conservation_release"]["status"], "fail")
        self.assertEqual(gates["same_qoi_uq"]["status"], "fail")
        self.assertEqual(gates["validation_holdout_external_scoring"]["status"], "not_consumed")
        self.assertTrue(all(r["production_ready"] == "False" for r in gate_rows))


if __name__ == "__main__":
    unittest.main()
