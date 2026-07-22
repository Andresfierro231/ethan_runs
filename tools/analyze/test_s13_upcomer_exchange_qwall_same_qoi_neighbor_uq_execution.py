from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from tools.analyze import build_s13_upcomer_exchange_qwall_same_qoi_neighbor_uq_execution as builder


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class S13QwallSameQoiNeighborUqExecutionTests(unittest.TestCase):
    def test_target_inventory_has_four_qois_for_three_cases(self) -> None:
        rows = builder.target_qoi_evidence_rows()
        self.assertEqual(len(rows), 12)
        self.assertEqual({row["qoi_label"] for row in rows}, set(builder.qoi_labels()))
        qwall_rows = [row for row in rows if row["qoi_label"] == "Q_wall_W"]
        self.assertEqual(len(qwall_rows), 3)
        self.assertTrue(all(row["target_status"] == "released_exact_target_window" for row in qwall_rows))

    def test_neighbor_inventory_fails_closed_for_all_requested_qois(self) -> None:
        rows = builder.neighbor_window_inventory_rows()
        self.assertEqual(len(rows), 12)
        self.assertTrue(all(row["target_evidence_exists"] == "true" for row in rows))
        self.assertTrue(all(row["target_minus_window_evidence_exists"] == "false" for row in rows))
        self.assertTrue(all(row["target_plus_window_evidence_exists"] == "false" for row in rows))
        self.assertTrue(all(row["neighbor_window_uq_ready"] == "false" for row in rows))

    def test_same_qoi_matrix_blocks_mesh_gci_and_production(self) -> None:
        rows = builder.same_qoi_uq_matrix_rows()
        self.assertEqual(len(rows), 4)
        self.assertTrue(all(row["neighbor_window_uq_ready"] == "false" for row in rows))
        self.assertTrue(all(row["move_to_mesh_gci_uq_allowed_now"] == "false" for row in rows))
        self.assertTrue(all(row["production_use_allowed_now"] == "false" for row in rows))

    def test_build_outputs_fail_closed_thesis_result(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "pkg"
            summary = builder.build(out)
            self.assertEqual(summary["decision"], "fail_closed_neighbor_window_uq_missing")
            self.assertEqual(summary["target_window_ready_rows"], 12)
            self.assertEqual(summary["target_minus_ready_rows"], 0)
            self.assertEqual(summary["target_plus_ready_rows"], 0)
            self.assertFalse(summary["move_to_mesh_gci_uq_allowed_now"])
            self.assertFalse(summary["production_harvest_allowed"])
            self.assertTrue((out / "clean_fail_closed_thesis_result.md").exists())
            gates = {row["gate"]: row for row in read_rows(out / "production_readiness_gate.csv")}
            self.assertEqual(gates["production_harvest"]["status"], "do_not_run")
            self.assertEqual(gates["clean_fail_closed_thesis_result"]["status"], "ready")


if __name__ == "__main__":
    unittest.main()
