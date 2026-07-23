#!/usr/bin/env python3
"""Tests for Salt1 mesh-area provenance repair preflight."""

from __future__ import annotations

import csv
import unittest

from tools.analyze import build_passive_h2_salt1_mesh_area_provenance_repair_preflight as builder


def read_rows(path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class PassiveH2Salt1MeshAreaProvenanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.summary = builder.build()

    def test_all_five_families_present(self) -> None:
        rows = read_rows(builder.OUT / "family_area_reconciliation.csv")
        self.assertEqual(len(rows), 5)
        self.assertEqual({row["source_family"] for row in rows}, {"cooling_branch", "downcomer", "junction", "lower_leg", "upcomer"})

    def test_mesh_area_tolerance_fails_only_junction(self) -> None:
        rows = read_rows(builder.OUT / "family_area_reconciliation.csv")
        failed = [row for row in rows if row["area_tolerance_pass"] == "False"]
        self.assertEqual([row["source_family"] for row in failed], ["junction"])
        self.assertEqual(self.summary["family_area_tolerance_pass_rows"], 4)

    def test_candidate_has_no_release_or_wallheatflux_runtime_use(self) -> None:
        rows = read_rows(builder.OUT / "mesh_area_backed_operator_candidate.csv")
        self.assertEqual(len(rows), 4)
        self.assertNotIn("junction", {row["source_family"] for row in rows})
        self.assertTrue(all(row["source_property_release"] == "False" for row in rows))
        self.assertTrue(all(row["admission_or_score"] == "False" for row in rows))
        self.assertTrue(all(row["runtime_wallHeatFlux_used"] == "False" for row in rows))
        self.assertTrue(all("postProcessing" not in row["source_paths"] for row in rows))

    def test_release_gates_remain_closed(self) -> None:
        gates = {row["gate"]: row for row in read_rows(builder.OUT / "release_preflight_gate.csv")}
        self.assertEqual(gates["family_area_reconciliation"]["status"], "fail_closed")
        self.assertEqual(gates["mesh_area_backed_operator_completeness"]["status"], "fail_closed")
        self.assertEqual(gates["source_property_release"]["status"], "fail_closed")
        self.assertEqual(gates["candidate_freeze_or_score"]["status"], "closed_not_run")
        self.assertFalse(self.summary["source_property_release"])
        self.assertFalse(self.summary["candidate_freeze"])
        self.assertEqual(self.summary["score_values_emitted"], 0)


if __name__ == "__main__":
    unittest.main()
