from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.extract import build_upcomer_exchange_cell_vtk_salt2_smoke as builder


class UpcomerExchangeCellVtkSalt2SmokeTests(unittest.TestCase):
    def test_preflight_row_is_salt2_only_and_released(self) -> None:
        rows = builder.preflight_rows()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["case_id"], "salt_2")
        self.assertEqual(rows[0]["release_status"], "released_for_scheduler_cell_vtk_extraction")
        self.assertEqual(str(rows[0]["volume_n_cells"]), "2166996")

    def test_inspect_legacy_vtk_detects_cell_data_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "cells.vtk"
            path.write_text(
                "\n".join(
                    [
                        "# vtk DataFile Version 3.0",
                        "fixture",
                        "ASCII",
                        "DATASET UNSTRUCTURED_GRID",
                        "CELL_DATA 3",
                        "VECTORS U float",
                        "1 0 0",
                        "0 1 0",
                        "0 0 1",
                        "SCALARS T float 1",
                        "LOOKUP_TABLE default",
                        "300",
                        "301",
                        "302",
                        "SCALARS rho float 1",
                        "LOOKUP_TABLE default",
                        "1",
                        "1",
                        "1",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            count, fields = builder.inspect_legacy_vtk(path)
        self.assertEqual(count, 3)
        self.assertEqual(fields, ["T", "U", "rho"])

    def test_build_package_writes_preflight_scripts_and_pending_validation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "pkg"
            payload = builder.build_package(out)
            self.assertEqual(payload["summary"]["case_id"], "salt_2")
            self.assertFalse(payload["summary"]["scheduler_action"])
            self.assertEqual(payload["summary"]["vtk_validation_state"], "pending_not_produced")
            for name in [
                "preflight.csv",
                "validation_report.csv",
                "submission_record.csv",
                "no_mutation_guardrails.csv",
                "source_manifest.csv",
                "summary.json",
                "README.md",
                "scripts/run_salt2_cell_vtk_smoke.sh",
                "scripts/submit_salt2_cell_vtk_smoke.sbatch",
                "scripts/validate_salt2_cell_vtk.py",
            ]:
                self.assertTrue((out / name).exists(), name)
            runner_text = (out / "scripts/run_salt2_cell_vtk_smoke.sh").read_text(encoding="utf-8")
        self.assertIn("task-local empty functions include", runner_text)
        self.assertIn("-noFaceZones", runner_text)
        self.assertIn("--harvest --submission-id", runner_text)
        self.assertNotIn("-no-boundary", runner_text)


if __name__ == "__main__":
    unittest.main()
