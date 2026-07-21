from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.extract import build_upcomer_exchange_cell_vtk_salt3_salt4_matrix as builder


class UpcomerExchangeCellVtkSalt3Salt4MatrixTests(unittest.TestCase):
    def test_preflight_rows_are_released_for_salt3_and_salt4(self) -> None:
        rows = builder.preflight_rows()
        self.assertEqual([row["case_id"] for row in rows], ["salt_3", "salt_4"])
        for row in rows:
            self.assertEqual(row["release_status"], "released_for_scheduler_cell_vtk_extraction")
            self.assertEqual(str(row["volume_n_cells"]), "2166996")
            self.assertEqual(row["preflight_status"], "ready_for_sbatch_preflight")

    def test_expected_paths_are_case_specific(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "pkg"
            self.assertEqual(builder.expected_vtk_path("salt_3", out).name, "salt_3_cell_fields.vtk")
            self.assertEqual(builder.expected_vtk_path("salt_4", out).name, "salt_4_cell_fields.vtk")

    def test_build_package_writes_matrix_scripts_and_pending_validation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "pkg"
            payload = builder.build_package(out)
            self.assertEqual(payload["summary"]["case_ids"], ["salt_3", "salt_4"])
            self.assertFalse(payload["summary"]["scheduler_action"])
            self.assertEqual(payload["summary"]["vtk_validation_pass_count"], 0)
            self.assertEqual({row["validation_status"] for row in payload["validation"]}, {"pending_not_produced"})
            for name in [
                "preflight.csv",
                "validation_report.csv",
                "submission_record.csv",
                "scheduler_terminal_status.csv",
                "no_mutation_guardrails.csv",
                "source_manifest.csv",
                "summary.json",
                "README.md",
                "scripts/run_salt3_salt4_cell_vtk_matrix.sh",
                "scripts/submit_salt3_salt4_cell_vtk_matrix.sbatch",
                "scripts/validate_salt3_salt4_cell_vtk.py",
            ]:
                self.assertTrue((out / name).exists(), name)
            runner_text = (out / "scripts/run_salt3_salt4_cell_vtk_matrix.sh").read_text(encoding="utf-8")
        self.assertIn("task-local empty functions include", runner_text)
        self.assertIn("-noFaceZones", runner_text)
        self.assertIn("-noPointValues", runner_text)
        self.assertIn("-excludePatches '(\".*\")'", runner_text)
        self.assertIn("--sanitize-boundary-field", runner_text)
        self.assertIn("salt_3_case_stage_7618.vtk", runner_text)
        self.assertIn("salt_4_case_stage_10000.vtk", runner_text)
        self.assertNotIn("-no-boundary", runner_text)

    def test_sanitizer_replaces_boundary_only_and_rejects_internal_nonfinite(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "T"
            path.write_text(
                "\n".join(
                    [
                        "internalField   nonuniform List<scalar>",
                        "3",
                        "(",
                        "450",
                        "451",
                        "452",
                        ")",
                        "boundaryField",
                        "{",
                        "patch0",
                        "{",
                        "value nonuniform List<scalar>",
                        "2",
                        "(",
                        "-nan",
                        "nan",
                        ")",
                        "}",
                        "}",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            result = builder.sanitize_boundary_nonfinite_tokens(path)
            text = path.read_text(encoding="utf-8")
        self.assertEqual(result["declared_internal_values"], 3)
        self.assertEqual(result["boundary_nonfinite_replacements"], 2)
        self.assertNotIn("-nan", text)
        self.assertNotIn("nan", text)

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "T"
            path.write_text("internalField nonuniform List<scalar>\n1\n(\n-nan\n)\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                builder.sanitize_boundary_nonfinite_tokens(path)


if __name__ == "__main__":
    unittest.main()
