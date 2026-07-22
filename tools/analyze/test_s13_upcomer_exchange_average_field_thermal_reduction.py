from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from tools.analyze import build_s13_upcomer_exchange_average_field_thermal_reduction as builder


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class S13AverageFieldThermalReductionTests(unittest.TestCase):
    def test_vector_helpers(self) -> None:
        self.assertEqual(builder.vector_add((1, 2, 3), (4, 5, 6)), (5, 7, 9))
        self.assertEqual(builder.vector_scale((1, -2, 3), 2), (2, -4, 6))
        self.assertEqual(builder.dot((1, 2, 3), (4, 5, 6)), 32)

    def test_missing_gates_keep_admission_blocked(self) -> None:
        rows = builder.missing_gate_rows()
        gates = {row["gate"]: row for row in rows}
        self.assertEqual(gates["wallHeatFlux_Q_wall_W"]["status"], "blocked")
        self.assertEqual(gates["same_qoi_uq"]["status"], "blocked")
        self.assertEqual(gates["coefficient_admission"]["diagnostic_average_proxy_allows_progress"], "false")

    def test_downstream_keeps_harvest_blocked(self) -> None:
        gates = {row["gate"]: row for row in builder.downstream_rows()}
        self.assertEqual(gates["sampler_manifest_refresh"]["allowed"], "false")
        self.assertEqual(gates["production_harvest"]["allowed"], "false")
        self.assertEqual(gates["s12_evidence_use"]["allowed"], "true")

    def test_vtk_reader_uses_explicit_cell_ids(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            vtk = Path(tmp) / "cells.vtk"
            vtk.write_text(
                "\n".join(
                    [
                        "# vtk DataFile Version 3.0",
                        "synthetic",
                        "ASCII",
                        "DATASET UNSTRUCTURED_GRID",
                        "CELL_DATA 3",
                        "FIELD attributes 4",
                        "cellID 1 3 int",
                        "30 10 20",
                        "T 1 3 float",
                        "330 310 320",
                        "rho 1 3 float",
                        "3.3 3.1 3.2",
                        "U 3 3 float",
                        "3 0 0 1 0 0 2 0 0",
                    ]
                ),
                encoding="utf-8",
            )
            fields = builder.read_vtk_cell_fields(vtk, {10, 20})
            self.assertEqual(fields[10]["T"], 310.0)
            self.assertEqual(fields[20]["rho"], 3.2)
            self.assertEqual(fields[20]["U"], (2.0, 0.0, 0.0))

    def test_build_writes_diagnostic_package(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "pkg"
            summary = builder.build(out)
            self.assertEqual(summary["case_count"], 3)
            self.assertEqual(summary["diagnostic_metric_rows"], 3)
            self.assertEqual(summary["average_field_rows"], 3)
            self.assertEqual(summary["interface_proxy_rows"], 3)
            self.assertEqual(summary["thermal_proxy_rows"], 3)
            self.assertEqual(summary["sampler_ready_rows"], 0)
            self.assertEqual(summary["admission_ready_rows"], 0)
            rows = read_rows(out / "diagnostic_average_exchange_metrics.csv")
            self.assertEqual(len(rows), 3)
            self.assertTrue(all(row["release_status"] == "diagnostic_average_proxy_only" for row in rows))
            self.assertTrue(all(float(row["seeded_cv_volume_m3"]) > 0.0 for row in rows))
            self.assertTrue(all(float(row["interface_area_m2"]) > 0.0 for row in rows))
            for name in [
                "diagnostic_average_exchange_metrics.csv",
                "average_field_reduction.csv",
                "interface_proxy_reduction.csv",
                "thermal_proxy_reduction.csv",
                "missing_gate_matrix.csv",
                "downstream_gate.csv",
                "no_mutation_guardrails.csv",
                "source_manifest.csv",
                "summary.json",
                "README.md",
            ]:
                self.assertTrue((out / name).exists(), name)


if __name__ == "__main__":
    unittest.main()
