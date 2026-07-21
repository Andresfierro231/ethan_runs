#!/usr/bin/env python3
"""Tests for pressure/upcomer post-3305547 harvest wrapper."""

from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools.analyze import build_pressure_upcomer_post_3305547_harvest_wrapper as mod


class PressureUpcomerPost3305547HarvestWrapperTest(unittest.TestCase):
    def fake_job(self, state: str = "PENDING") -> list[dict[str, str]]:
        return [
            {
                "job_id": mod.JOB_ID,
                "job_name": "upc_nominal",
                "scheduler_state": state,
                "elapsed": "0:00",
                "nodes": "1",
                "nodelist_or_reason": "Priority",
                "scheduler_source": "test",
                "stdout_exists": "true",
                "stderr_exists": "true",
                "stdout_tail_has_sampling": "false",
                "stderr_tail_has_error": "false",
                "stdout_path": "stdout",
                "stderr_path": "stderr",
                "terminal_state": str(state in mod.TERMINAL_STATES).lower(),
                "completed_successfully": str(state in mod.SUCCESS_STATES).lower(),
                "wrapper_action": "wait_for_terminal_job_state_or_use_existing_local_outputs_as_diagnostic",
                "submission_log": "submission",
            }
        ]

    def test_pending_job_does_not_release_fit_candidates(self) -> None:
        with mock.patch.object(mod, "build_job_status", return_value=self.fake_job("PENDING")):
            parse = mod.build_matched_plane_parse_status(mod.build_job_status())
            rollup = mod.build_pressure_upcomer_admission_rollup(parse)
            decision = mod.build_fit_candidate_decision(rollup)[0]

        self.assertEqual(decision["decision"], "no_fit_candidate_released")
        self.assertEqual(decision["fit_or_model_selection_changed"], "false")
        self.assertTrue(all(row["fit_candidate"] == "false" for row in rollup))

    def test_completed_job_with_parser_inputs_still_requires_rollup(self) -> None:
        with mock.patch.object(mod, "build_job_status", return_value=self.fake_job("COMPLETED")):
            parse = mod.build_matched_plane_parse_status(mod.build_job_status())

        self.assertTrue(parse)
        self.assertTrue(all(row["next_action"] in {"run matched-plane parser and refresh admission rollup", "wait for 3305547 or rerun compute wrapper"} for row in parse))

    def test_main_writes_wrapper_package(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            with (
                mock.patch.object(mod, "OUT", base / "out"),
                mock.patch.object(mod, "STATUS", base / "status.md"),
                mock.patch.object(mod, "JOURNAL", base / "journal.md"),
                mock.patch.object(mod, "IMPORT", base / "import.json"),
                mock.patch.object(mod, "build_job_status", return_value=self.fake_job("PENDING")),
            ):
                summary = mod.main()

            self.assertEqual(summary["fit_admitted_rows"], 0)
            self.assertTrue((base / "out/job_status.csv").exists())
            with (base / "out/pressure_upcomer_admission_rollup.csv").open(newline="") as handle:
                self.assertTrue(list(csv.DictReader(handle)))
            with (base / "import.json").open() as handle:
                manifest = json.load(handle)
            self.assertFalse(manifest["native_solver_outputs_mutated"])


if __name__ == "__main__":
    unittest.main()
