from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from tools.analyze import build_s13_upcomer_exchange_same_qoi_neighbor_uq_after_target_plus as builder


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class S13SameQoiNeighborUqAfterTargetPlusTests(unittest.TestCase):
    def test_temporal_uq_rows_cover_four_qois_three_cases(self) -> None:
        rows = builder.temporal_uq_rows()
        self.assertEqual(len(rows), 12)
        self.assertEqual(
            set(builder.qoi_labels(rows)),
            {
                "Q_wall_W",
                "mdot_exchange_positive_outward_proxy_kg_s",
                "tau_recirc_proxy_s",
                "wall_core_bulk_temperature_contrast_K",
            },
        )
        self.assertTrue(all(row["neighbor_window_uq_executed"] == "true" for row in rows))

    def test_temporal_uq_formula_for_qwall_salt2(self) -> None:
        rows = builder.temporal_uq_rows()
        selected = [
            row for row in rows if row["case_id"] == "salt_2" and row["qoi_label"] == "Q_wall_W"
        ][0]
        self.assertAlmostEqual(float(selected["delta_target_minus_to_target"]), 6.64561e-05, places=10)
        self.assertAlmostEqual(float(selected["delta_target_to_plus"]), -2.46022e-05, places=10)
        self.assertAlmostEqual(float(selected["max_abs_neighbor_delta"]), 6.64561e-05, places=10)

    def test_qoi_summary_unblocks_mesh_gate_but_not_production(self) -> None:
        summary_rows = builder.qoi_summary_rows(builder.temporal_uq_rows())
        self.assertEqual(len(summary_rows), 4)
        self.assertTrue(all(row["mesh_gci_gate_input_ready"] == "true" for row in summary_rows))
        self.assertTrue(all(row["production_use_allowed_now"] == "false" for row in summary_rows))

    def test_heat_flow_match_diagnostic_quantifies_gap_and_blocks_match(self) -> None:
        rows = builder.heat_flow_match_rows(builder.temporal_uq_rows())
        self.assertEqual(len(rows), 3)
        salt2 = [row for row in rows if row["case_id"] == "salt_2"][0]
        self.assertAlmostEqual(float(salt2["Q_wall_W"]), 23.1161370708, places=10)
        self.assertAlmostEqual(float(salt2["Q_source_side_net_static_bc_W"]), 166.349260094, places=9)
        self.assertGreater(float(salt2["source_minus_qwall_W"]), 100.0)
        self.assertGreater(float(salt2["cp_required_to_match_Q_wall_J_kg_K"]), 1.0e6)
        self.assertTrue(
            all(row["heat_flow_match_status"] == "not_physical_match_with_current_exchange_scale" for row in rows)
        )

    def test_build_outputs_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "pkg"
            summary = builder.build(out)
            self.assertEqual(
                summary["decision"],
                "same_qoi_neighbor_temporal_uq_executed_mesh_gci_ready_to_claim",
            )
            self.assertEqual(summary["case_temporal_uq_rows"], 12)
            self.assertEqual(summary["same_qoi_temporal_uq_executed_qois"], 4)
            self.assertEqual(summary["heat_flow_match_rows"], 3)
            self.assertEqual(summary["heat_flow_match_ready_rows"], 0)
            self.assertTrue(summary["mesh_gci_gate_input_ready"])
            self.assertFalse(summary["production_harvest_allowed"])
            self.assertTrue((out / "heat_flow_match_diagnostics.csv").exists())
            gates = {row["gate"]: row for row in read_rows(out / "production_readiness_gate.csv")}
            self.assertEqual(gates["mesh_gci_uq"]["status"], "ready_to_claim")
            self.assertEqual(gates["production_harvest"]["status"], "do_not_run")


if __name__ == "__main__":
    unittest.main()
