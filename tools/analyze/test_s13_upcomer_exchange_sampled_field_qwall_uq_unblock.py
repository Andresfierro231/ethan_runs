from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from tools.analyze import build_s13_upcomer_exchange_sampled_field_qwall_uq_unblock as builder


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class S13SampledFieldQwallUqUnblockTests(unittest.TestCase):
    def test_readiness_rows_keep_production_blocked(self) -> None:
        rows = builder.production_readiness_rows()
        self.assertEqual(len(rows), 3)
        self.assertTrue(all(row["source_side_equivalent_ready_for_contract"] == "true" for row in rows))
        self.assertTrue(all(row["Q_wall_W_ready"] == "false" for row in rows))
        self.assertTrue(all(row["same_qoi_uq_ready"] == "false" for row in rows))
        self.assertTrue(all(row["production_harvest_ready"] == "false" for row in rows))

    def test_path_decision_prefers_source_side_contract_without_relabeling(self) -> None:
        paths = {row["path_id"]: row for row in builder.path_decision_rows()}
        self.assertEqual(paths["distinct_source_side_heat_flow_Q_source_side_W"]["rank"], "1")
        self.assertEqual(paths["direct_Q_wall_W"]["decision"], "blocked_longer_path")
        self.assertEqual(
            paths["distinct_source_side_heat_flow_Q_source_side_W"]["production_release_allowed_now"],
            "false",
        )

    def test_uq_prerequisites_require_neighbors_and_mesh(self) -> None:
        rows = builder.same_qoi_uq_prerequisite_rows()
        self.assertTrue(all(row["uq_release_allowed_now"] == "false" for row in rows))
        self.assertTrue(all(row["neighbor_minus_status"] == "missing" for row in rows))
        self.assertTrue(all(row["mesh_or_gci_status"] == "missing" for row in rows))

    def test_build_outputs_gate_tables(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "pkg"
            summary = builder.build(out)
            self.assertEqual(summary["source_side_contract_ready_rows"], 3)
            self.assertEqual(summary["Q_wall_W_ready_rows"], 0)
            self.assertEqual(summary["production_harvest_ready_rows"], 0)
            readiness = read_rows(out / "production_readiness_table.csv")
            self.assertEqual(len(readiness), 3)
            blockers = read_rows(out / "blocker_unlock_matrix.csv")
            self.assertIn("Q_wall_W", {row["gate"] for row in blockers})


if __name__ == "__main__":
    unittest.main()
