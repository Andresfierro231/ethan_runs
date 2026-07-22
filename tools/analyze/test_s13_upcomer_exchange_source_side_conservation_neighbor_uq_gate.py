from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from tools.analyze import build_s13_upcomer_exchange_source_side_conservation_neighbor_uq_gate as builder


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class S13SourceSideConservationNeighborUqGateTests(unittest.TestCase):
    def test_conservation_release_keeps_exact_qoi_and_blocks_release(self) -> None:
        rows = builder.source_property_conservation_release_rows()
        self.assertEqual(len(rows), 3)
        self.assertTrue(all(row["qoi_label"] == builder.QOI_LABEL for row in rows))
        self.assertTrue(all(row["arithmetic_source_sink_status"] == "pass" for row in rows))
        self.assertTrue(all(row["source_property_release_allowed_now"] == "false" for row in rows))
        self.assertTrue(all(row["production_release_allowed_now"] == "false" for row in rows))

    def test_neighbor_inventory_and_uq_fail_closed(self) -> None:
        neighbors = builder.neighbor_window_inventory_rows()
        self.assertGreaterEqual(len(neighbors), 4)
        self.assertTrue(all(row["neighbor_minus_window_status"] == "missing" for row in neighbors))
        self.assertTrue(all(row["neighbor_plus_window_status"] == "missing" for row in neighbors))
        uq = builder.same_qoi_uq_matrix_rows()
        self.assertTrue(all(row["same_qoi_uq_ready"] == "false" for row in uq))

    def test_production_gate_blocks_harvest_and_admission(self) -> None:
        gates = {row["gate"]: row for row in builder.production_readiness_gate_rows()}
        self.assertEqual(gates["production_harvest"]["release_allowed_now"], "false")
        self.assertEqual(gates["coefficient_or_S11_admission"]["release_allowed_now"], "false")
        self.assertEqual(gates["source_side_heat_flow_basis"]["release_allowed_now"], "false")

    def test_build_outputs_all_five_step_tables(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "pkg"
            summary = builder.build(out)
            self.assertEqual(summary["decision"], "source_side_path_executed_fail_closed_production_harvest_not_ready")
            self.assertEqual(summary["conservation_release_ready_rows"], 0)
            self.assertEqual(summary["same_qoi_uq_ready_rows"], 0)
            self.assertFalse(summary["harvest_allowed"])
            steps = read_rows(out / "step_sequence_status.csv")
            self.assertEqual(len(steps), 5)
            self.assertTrue((out / "production_readiness_gate.csv").exists())


if __name__ == "__main__":
    unittest.main()
