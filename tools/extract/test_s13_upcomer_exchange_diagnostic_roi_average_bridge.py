from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.extract import build_s13_upcomer_exchange_diagnostic_roi_average_bridge as builder


class S13DiagnosticRoiAverageBridgeTests(unittest.TestCase):
    def test_weighted_mean_uses_cell_volumes(self) -> None:
        values = {1: 10.0, 2: 20.0}
        volumes = {1: 1.0, 2: 3.0}
        self.assertAlmostEqual(builder.weighted_mean(values, volumes), 17.5)

    def test_fmt_hides_nonfinite(self) -> None:
        self.assertEqual(builder.fmt(float("nan")), "")
        self.assertEqual(builder.fmt(1.25), "1.25")

    def test_vtk_scalar_reader_reads_selected_cells(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            vtk = Path(tmp) / "fixture.vtk"
            vtk.write_text(
                "\n".join(
                    [
                        "# vtk DataFile Version 2.0",
                        "fixture",
                        "ASCII",
                        "DATASET UNSTRUCTURED_GRID",
                        "CELL_DATA 3",
                        "FIELD attributes 2",
                        "T 1 3 float",
                        "300 310 320",
                        "rho 1 3 float",
                        "1.0 2.0 3.0",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            fields = builder.read_vtk_scalar_fields(vtk, {0, 2}, {"T", "rho"})
        self.assertEqual(fields["T"], {0: 300.0, 2: 320.0})
        self.assertEqual(fields["rho"], {0: 1.0, 2: 3.0})

    def test_package_summary_is_nonadmissible(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "pkg"
            payload = builder.build_package(out)
            self.assertEqual(payload["summary"]["admission_rows_released"], 0)
            self.assertEqual(payload["summary"]["proxy_support_rows"], 15)
            self.assertFalse(payload["summary"]["sampler_or_harvest_allowed"])
            self.assertTrue((out / "diagnostic_roi_average_bridge.csv").exists())
            self.assertTrue((out / "diagnostic_roi_average_metrics.csv").exists())
            self.assertTrue((out / "proxy_admission_support_matrix.csv").exists())
            self.assertTrue((out / "diagnostic_bridge_decision.csv").exists())


if __name__ == "__main__":
    unittest.main()
