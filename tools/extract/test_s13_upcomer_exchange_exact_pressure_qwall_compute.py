from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from tools.extract import build_s13_upcomer_exchange_exact_pressure_qwall_compute as builder


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class S13ExactPressureQwallComputeTests(unittest.TestCase):
    def test_parse_processor_blocks_and_number_list(self) -> None:
        text = """
// Processor0

12
(header
3
(
10
20
30
)
)
// Processor1

12
(header
2
(
40
50
)
)
"""
        blocks = builder.processor_blocks(text)
        self.assertEqual([proc for proc, _ in blocks], [0, 1])
        self.assertEqual(builder.parse_number_list(blocks[0][1], int), [10, 20, 30])
        self.assertEqual(builder.parse_number_list(blocks[1][1], int), [40, 50])

    def test_decode_negative_face_addressing(self) -> None:
        self.assertEqual(builder.decode_face_address(42), (42, False))
        self.assertEqual(builder.decode_face_address(-43), (42, True))

    def test_patch_scalar_values_handle_empty_and_nonuniform(self) -> None:
        empty = "type calculated;\nvalue nonuniform List<scalar> 0();"
        nonuniform = "type calculated;\nvalue nonuniform List<scalar> \n3\n(\n-1.0\n2.5\n4\n)\n;"
        self.assertEqual(builder.parse_patch_scalar_values(empty), [])
        self.assertEqual(builder.parse_patch_scalar_values(nonuniform), [-1.0, 2.5, 4.0])

    def test_downstream_gate_keeps_sampler_and_uq_separate(self) -> None:
        pressure = [{"pressure_basis_released": "true"} for _ in range(3)]
        qwall = [{"Q_wall_W_released": "true"} for _ in range(3)]
        rows = builder.downstream_gate_rows(qwall, pressure)
        by_gate = {row["gate"]: row for row in rows}
        self.assertEqual(by_gate["exact_pressure_basis"]["status"], "released")
        self.assertEqual(by_gate["Q_wall_W"]["status"], "released")
        self.assertEqual(by_gate["production_sampler_manifest_refresh"]["allowed"], "false")
        self.assertEqual(by_gate["same_qoi_uq"]["status"], "blocked")
        self.assertEqual(by_gate["internal_Nu_residual_absorption"]["status"], "forbidden")

    def test_build_outputs_exact_release_tables(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "pkg"
            summary = builder.build(out)
            self.assertEqual(summary["case_count"], 3)
            self.assertEqual(summary["pressure_basis_released_rows"], 3)
            self.assertEqual(summary["Q_wall_W_released_rows"], 3)
            self.assertFalse(summary["production_harvest_allowed_now"])
            qwall = read_rows(out / "trusted_wall_Q_wall_summary.csv")
            self.assertEqual(len(qwall), 3)
            self.assertTrue(all(row["Q_wall_W_released"] == "true" for row in qwall))
            pressure = read_rows(out / "pressure_reduction_summary.csv")
            self.assertEqual(len(pressure), 3)
            self.assertTrue(all(row["pressure_basis_released"] == "true" for row in pressure))


if __name__ == "__main__":
    unittest.main()
