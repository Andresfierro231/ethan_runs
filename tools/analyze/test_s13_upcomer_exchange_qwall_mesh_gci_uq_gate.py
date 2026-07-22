from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from tools.analyze import build_s13_upcomer_exchange_qwall_mesh_gci_uq_gate as builder


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class S13QwallMeshGciUqGateTests(unittest.TestCase):
    def test_mesh_gate_matrix_reviews_four_labels(self) -> None:
        rows = builder.mesh_gate_matrix_rows()
        self.assertEqual(len(rows), 4)
        self.assertEqual(set(row["qoi_label"] for row in rows), set(builder.MESH_FAMILY_MAP))
        self.assertTrue(all(row["temporal_uq_status"] == "executed" for row in rows))

    def test_mesh_gate_fails_closed_without_same_label_mesh_family(self) -> None:
        rows = builder.mesh_gate_matrix_rows()
        self.assertTrue(all(row["mesh_gci_gate_executed"] == "true" for row in rows))
        self.assertTrue(all(row["same_label_mesh_gci_ready"] == "false" for row in rows))
        self.assertTrue(all(row["mesh_gci_uq_status"] == "blocked_missing_same_label_mesh_family" for row in rows))
        self.assertTrue(all(row["move_to_production_harvest_allowed_now"] == "false" for row in rows))

    def test_missing_mesh_family_blocker_has_one_row_per_qoi(self) -> None:
        blockers = builder.missing_mesh_family_rows(builder.mesh_gate_matrix_rows())
        self.assertEqual(len(blockers), 4)
        self.assertTrue(all(row["temporal_uq_available"] == "true" for row in blockers))
        self.assertTrue(all(row["production_consequence"] == "blocks_production_harvest_and_admission" for row in blockers))

    def test_build_outputs_production_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "pkg"
            summary = builder.build(out)
            self.assertEqual(summary["decision"], "fail_closed_missing_same_label_mesh_gci_family_after_temporal_uq")
            self.assertEqual(summary["temporal_uq_complete_qois"], 4)
            self.assertEqual(summary["accepted_same_label_mesh_gci_qois"], 0)
            self.assertFalse(summary["production_harvest_allowed"])
            gates = {row["gate"]: row for row in read_rows(out / "production_harvest_consequence.csv")}
            self.assertEqual(gates["same_label_mesh_gci_uq"]["status"], "blocked_missing_same_label_mesh_family")
            self.assertEqual(gates["production_harvest"]["status"], "do_not_run")


if __name__ == "__main__":
    unittest.main()
