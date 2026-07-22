#!/usr/bin/env python3
"""Validate the S8/S12 thermal residual ownership gate package."""

from __future__ import annotations

import csv
import json
import unittest
from pathlib import Path

from tools.analyze import build_s8_s12_thermal_residual_ownership_gate as builder


OUT = builder.OUT
REQUIRED = [
    "README.md",
    "residual_owner_matrix.csv",
    "physical_basis_coverage.csv",
    "candidate_gate_decision.csv",
    "runtime_leakage_audit.csv",
    "source_property_split_consequence.csv",
    "s11_decision.csv",
    "source_manifest.csv",
    "summary.json",
]


def read_csv(name: str) -> list[dict[str, str]]:
    with (OUT / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class ThermalResidualOwnershipGateTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        builder.main()

    def test_outputs_and_summary_are_fail_closed(self) -> None:
        missing = [name for name in REQUIRED if not (OUT / name).exists()]
        self.assertEqual(missing, [])
        summary = json.loads((OUT / "summary.json").read_text(encoding="utf-8"))
        self.assertEqual(summary["decision"], "needs_more_physical_basis")
        self.assertFalse(summary["s11_unblocked"])
        self.assertFalse(summary["s15_unblocked"])
        self.assertFalse(summary["s6_unblocked"])
        self.assertEqual(summary["candidate_count_released"], 0)
        self.assertFalse(summary["fluid_solve_run"])
        self.assertFalse(summary["fit_or_model_selection"])
        self.assertEqual(summary["validation_rows_scored"], 0)
        self.assertEqual(summary["holdout_rows_scored"], 0)
        self.assertEqual(summary["external_test_rows_scored"], 0)

    def test_gate_tables_preserve_runtime_and_source_guardrails(self) -> None:
        owners = read_csv("residual_owner_matrix.csv")
        self.assertGreaterEqual(len(owners), 5)
        self.assertIn("S12-HIAX1", {row["candidate_id"] for row in owners})
        self.assertIn("PASSIVE-H2-CAND001", {row["candidate_id"] for row in owners})
        self.assertTrue(all(row["decision"] == "needs_more_physical_basis" for row in owners))

        runtime = read_csv("runtime_leakage_audit.csv")
        self.assertTrue(all(row["status"] == "pass" for row in runtime))
        self.assertTrue(all(row["used_as_runtime_input"] == "False" for row in runtime))
        self.assertTrue(any("validation, holdout, and external-test rows scored: 0/0/0" in row["detail"] for row in runtime))

        split = read_csv("source_property_split_consequence.csv")
        self.assertTrue(all(row["release_status"] == "not_released" for row in split))

        s11 = read_csv("s11_decision.csv")
        self.assertEqual(s11[0]["s11_unblocked"], "False")
        self.assertEqual(s11[0]["candidate_count_released"], "0")

    def test_source_manifest_is_read_only(self) -> None:
        manifest = read_csv("source_manifest.csv")
        self.assertTrue(manifest)
        self.assertTrue(all(row["exists"] == "True" for row in manifest))
        self.assertTrue(all(row["mutated"] == "False" for row in manifest))


if __name__ == "__main__":
    unittest.main()
