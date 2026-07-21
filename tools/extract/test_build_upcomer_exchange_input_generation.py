from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from tools.extract import build_upcomer_exchange_input_generation as builder


class UpcomerExchangeInputGenerationTests(unittest.TestCase):
    def test_input_rows_cover_required_inputs_for_all_cases(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            rows = builder.input_rows(Path(tmp), "ready_for_sbatch_generation")
        self.assertEqual({row["case_id"] for row in rows}, {"salt_2", "salt_3", "salt_4"})
        self.assertEqual(
            {row["input_name"] for row in rows},
            {
                "cell_volume_csv",
                "recirc_mask",
                "cell_vtk",
                "exchange_interface_vtk",
                "wall_vtk",
                "source_sink_ledger",
            },
        )
        volume = [row for row in rows if row["input_name"] == "cell_volume_csv"]
        if all(builder.external_volume_ready(row) for row in builder.mesh_rows()):
            self.assertTrue(all(row["blocking_for_sampler_execution"] == "false" for row in volume))
            self.assertTrue(all(row["status"] == "present_external_cell_volume_export_sbatch" for row in volume))
        else:
            self.assertTrue(all(row["blocking_for_sampler_execution"] == "true" for row in volume))

    def test_volume_commands_use_parser_and_task_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "pkg"
            rows = builder.volume_command_rows(out)
        self.assertEqual(len(rows), 3)
        self.assertTrue(all("openfoam_cell_volumes.py" in row["command"] for row in rows))
        self.assertTrue(all("cell_volumes" in row["output_csv"] for row in rows))

    def test_build_package_writes_scripts_and_ledgers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "pkg"
            payload = builder.build_package(out)
            self.assertEqual(payload["summary"]["case_rows"], 3)
            self.assertFalse(payload["summary"]["scheduler_action"])
            for name in [
                "input_generation_ledger.csv",
                "cell_volume_export_validation.csv",
                "cell_volume_export_commands.csv",
                "surface_and_ledger_blockers.csv",
                "submission_record.csv",
                "no_mutation_guardrails.csv",
                "next_agent_handoff.csv",
                "source_manifest.csv",
                "summary.json",
                "README.md",
                "scripts/run_cell_volume_exports.sh",
                "scripts/submit_cell_volume_exports.sbatch",
            ]:
                self.assertTrue((out / name).exists(), name)

    def test_submission_id_writes_running_note(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "pkg"
            payload = builder.build_package(out, submission_id="12345", submit_command="sbatch script")
            self.assertTrue(payload["summary"]["scheduler_action"])
            self.assertTrue((out / "RUNNING.md").exists())
            with (out / "submission_record.csv").open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
        self.assertEqual(rows[0]["submission_id"], "12345")
        self.assertEqual(rows[0]["submitted"], "true")


if __name__ == "__main__":
    unittest.main()
