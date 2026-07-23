#!/usr/bin/env python3
"""Tests for Salt1 PASSIVE-H2 junction patchset reconciliation."""

from __future__ import annotations

import csv
import unittest

from tools.analyze import build_passive_h2_salt1_junction_patchset_reconciliation as builder


def read_rows(path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class Salt1JunctionPatchsetReconciliationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.summary = builder.build()

    def test_all_junction_patches_checked(self) -> None:
        rows = read_rows(builder.OUT / "junction_patch_delta_table.csv")
        self.assertEqual(len(rows), 18)
        self.assertEqual({row["source_family"] for row in rows}, {"junction"})

    def test_mismatch_localizes_to_core_body(self) -> None:
        rows = read_rows(builder.OUT / "junction_patch_delta_table.csv")
        failed = [row for row in rows if row["area_tolerance_pass"] == "False"]
        self.assertEqual(len(failed), 4)
        self.assertEqual({row["junction_subgroup"] for row in failed}, {"core_junction_body"})

    def test_corrected_candidate_remains_diagnostic_only(self) -> None:
        rows = read_rows(builder.OUT / "five_family_mesh_area_candidate_diagnostic_only.csv")
        self.assertEqual(len(rows), 5)
        junction = next(row for row in rows if row["source_family"] == "junction")
        self.assertEqual(junction["setup_recovery_status"], "mesh_area_reconciled_same_patchset")
        self.assertEqual(junction["source_property_release"], "false")
        self.assertEqual(junction["admission_or_score"], "false")
        self.assertEqual(junction["runtime_wallHeatFlux_used"], "false")

    def test_release_gates_stay_closed(self) -> None:
        gates = {row["gate"]: row for row in read_rows(builder.OUT / "release_gate.csv")}
        self.assertEqual(gates["junction_patch_coverage"]["status"], "pass")
        self.assertEqual(gates["recovered_operator_area_reconciliation"]["status"], "fail_closed")
        self.assertEqual(gates["same_patchset_direct_mesh_area_replacement"]["status"], "pass_area_only_no_release")
        self.assertEqual(gates["source_property_release"]["status"], "fail_closed")
        self.assertEqual(gates["candidate_freeze_or_score"]["status"], "closed_not_run")
        self.assertFalse(self.summary["source_property_release"])
        self.assertFalse(self.summary["candidate_freeze"])
        self.assertEqual(self.summary["score_values_emitted"], 0)


if __name__ == "__main__":
    unittest.main()
