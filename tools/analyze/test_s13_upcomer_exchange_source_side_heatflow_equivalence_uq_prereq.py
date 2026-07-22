from __future__ import annotations

import csv
import json
import unittest
from pathlib import Path

from tools.analyze import build_s13_upcomer_exchange_source_side_heatflow_equivalence_uq_prereq as builder


class S13SourceSideHeatflowEquivalenceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        builder.main()
        cls.out = builder.OUT

    def read_csv(self, name: str) -> list[dict[str, str]]:
        with (self.out / name).open(newline="", encoding="utf-8") as handle:
            return list(csv.DictReader(handle))

    def test_summary_is_fail_closed_prerequisite(self) -> None:
        summary = json.loads((self.out / "summary.json").read_text(encoding="utf-8"))
        self.assertEqual(summary["decision"], builder.DECISION)
        self.assertTrue(summary["Q_source_side_net_static_bc_W_defined"])
        self.assertFalse(summary["Q_wall_W_released"])
        self.assertFalse(summary["source_side_relabel_as_Q_wall"])
        self.assertFalse(summary["same_qoi_uq_executed"])
        self.assertFalse(summary["production_harvest_allowed"])

    def test_all_three_cases_have_source_side_context_but_no_release(self) -> None:
        rows = self.read_csv("case_heatflow_equivalence_basis.csv")
        self.assertEqual(len(rows), 3)
        self.assertTrue(all(row["source_side_context_ready"] == "true" for row in rows))
        self.assertTrue(all(float(row["Q_source_side_net_static_bc_W"]) > 0.0 for row in rows))
        self.assertTrue(all(row["production_release_allowed_now"] == "false" for row in rows))

    def test_same_qoi_matrix_keeps_uq_blocked(self) -> None:
        rows = self.read_csv("same_qoi_uq_requirement_matrix.csv")
        self.assertIn("Q_source_side_net_static_bc_W", {row["qoi_name"] for row in rows})
        self.assertTrue(all(row["neighbor_minus_status"] == "missing" for row in rows))
        self.assertTrue(all(row["uq_release_allowed_now"] == "false" for row in rows))

    def test_admission_gate_has_no_trigger(self) -> None:
        rows = self.read_csv("s11_s15_s6_consequence.csv")
        self.assertEqual(rows[0]["s11_unblocked"], "false")
        self.assertEqual(rows[0]["s15_unblocked"], "false")
        self.assertEqual(rows[0]["s6_unblocked"], "false")
        self.assertEqual(rows[0]["candidate_count_released"], "0")


if __name__ == "__main__":
    unittest.main()
