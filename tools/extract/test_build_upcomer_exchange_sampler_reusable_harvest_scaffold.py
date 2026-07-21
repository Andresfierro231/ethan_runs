from __future__ import annotations

import csv
import subprocess
import tempfile
import unittest
from pathlib import Path

from tools.extract import build_upcomer_exchange_sampler_reusable_harvest_scaffold as builder


class UpcomerExchangeReusableHarvestScaffoldTests(unittest.TestCase):
    def test_case_volume_map_uses_ready_input_generation_csvs(self) -> None:
        rows = builder.case_volume_map_rows()
        self.assertEqual({row["case_id"] for row in rows}, {"salt_2", "salt_3", "salt_4"})
        self.assertTrue(all(row["volume_status"] == "ready" for row in rows))
        self.assertTrue(all(int(row["n_cells"]) > 0 for row in rows))
        self.assertTrue(all(row["sampler_ready_now"] == "false" for row in rows))

    def test_contract_rows_fail_closed_for_missing_geometry_and_sources(self) -> None:
        rows = builder.vtk_input_contract_rows()
        self.assertEqual(len(rows), 12)
        self.assertEqual(
            {row["input_role"] for row in rows},
            {"cell_vtk", "exchange_interface_vtk", "wall_vtk", "source_sink_ledger"},
        )
        self.assertTrue(all(row["blocking_for_harvest"] == "true" for row in rows))

    def test_build_package_writes_reusable_scripts_and_templates(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            out = Path(raw_tmp) / "pkg"
            payload = builder.build_package(out)
            self.assertEqual(payload["summary"]["case_volume_rows"], 3)
            self.assertEqual(payload["summary"]["ready_volume_csvs"], 3)
            self.assertFalse(payload["summary"]["sampler_harvest_launched"])
            self.assertFalse(payload["summary"]["scheduler_action"])
            for name in [
                "case_volume_input_map.csv",
                "required_vtk_input_contract.csv",
                "case_vtk_input_manifest.template.csv",
                "geometry_source_blockers.csv",
                "reusable_script_index.csv",
                "no_mutation_guardrails.csv",
                "source_manifest.csv",
                "summary.json",
                "README.md",
                "scripts/harvest_one_exchange_case.sh",
                "scripts/harvest_exchange_case_matrix.sh",
                "scripts/validate_exchange_case_inputs.py",
                "scripts/check_exchange_outputs.py",
            ]:
                self.assertTrue((out / name).exists(), name)
            with (out / "case_vtk_input_manifest.template.csv").open(newline="", encoding="utf-8") as handle:
                template = list(csv.DictReader(handle))
        self.assertEqual(len(template), 3)
        self.assertTrue(all(row["cell_vtk"].startswith("MISSING_") for row in template))

    def test_validator_rejects_template_and_accepts_populated_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            root = Path(raw_tmp)
            out = root / "pkg"
            builder.build_package(out)
            validator = out / "scripts/validate_exchange_case_inputs.py"
            template = out / "case_vtk_input_manifest.template.csv"
            rejected = subprocess.run(
                ["python3.11", str(validator), str(template)],
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self.assertNotEqual(rejected.returncode, 0)
            self.assertIn("missing cell_vtk", rejected.stderr)

            for name in ("cell.vtk", "interface.vtk", "wall.vtk", "volumes.csv"):
                (root / name).write_text("placeholder\n", encoding="utf-8")
            manifest = root / "manifest.csv"
            with manifest.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=builder.TEMPLATE_FIELDS)
                writer.writeheader()
                writer.writerow(
                    {
                        "case_id": "fixture",
                        "time_window_s": "1",
                        "cell_vtk": str(root / "cell.vtk"),
                        "interface_vtk": str(root / "interface.vtk"),
                        "wall_vtk": str(root / "wall.vtk"),
                        "volume_csv": str(root / "volumes.csv"),
                        "throughflow_nx": "0",
                        "throughflow_ny": "0",
                        "throughflow_nz": "1",
                        "interface_nx": "1",
                        "interface_ny": "0",
                        "interface_nz": "0",
                        "output_dir": str(root / "sampled"),
                        "cp_J_kg_K": "",
                    }
                )
            accepted = subprocess.run(
                ["python3.11", str(validator), str(manifest)],
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        self.assertEqual(accepted.returncode, 0, accepted.stderr)
        self.assertIn("validated_exchange_input_rows=1", accepted.stdout)


if __name__ == "__main__":
    unittest.main()
