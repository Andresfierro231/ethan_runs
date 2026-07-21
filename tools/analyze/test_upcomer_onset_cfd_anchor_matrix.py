#!/usr/bin/env python3
"""Tests for the upcomer onset CFD anchor matrix."""

from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools.analyze import build_upcomer_onset_cfd_anchor_matrix as mod


class UpcomerOnsetCfdAnchorMatrixTest(unittest.TestCase):
    def test_anchor_matrix_contains_required_study_groups(self) -> None:
        rows = mod.build_anchor_matrix()
        groups = {row["study_group"] for row in rows}

        self.assertIn("sentinel_cell_off", groups)
        self.assertIn("sentinel_cell_max", groups)
        self.assertIn("small_q_x_insulation_matrix", groups)
        self.assertIn("optional_forced_flow_feasibility", groups)
        self.assertTrue(all(row["launch_allowed_in_this_row"] == "false" for row in rows))

    def test_required_outputs_cover_onset_metrics(self) -> None:
        rows = {row["required_output"]: row for row in mod.build_required_output_rows()}

        for key in ["U", "T", "wallHeatFlux", "Re", "Pr", "Ri", "Gr", "Ra", "Gz", "wall_core_deltaT", "reverse_area_fraction", "reverse_mass_fraction", "secondary_velocity_fraction", "steady_window_status", "mesh_time_uncertainty"]:
            self.assertIn(key, rows)
            self.assertEqual(rows[key]["admission_role"], "required_before_hybrid_fit_admission")

    def test_runtime_audit_forbids_launch_side_effects(self) -> None:
        rows = mod.runtime_audit_rows()
        forbidden = {row["forbidden_input"] for row in rows}

        self.assertTrue(all(row["status"] == "pass_forbidden" for row in rows))
        self.assertIn("sbatch/srun/scancel", forbidden)
        self.assertIn("native CFD case outputs", forbidden)
        self.assertIn("registry/admission state", forbidden)

    def test_main_writes_complete_package(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            out = base / "out"
            status = base / "status.md"
            journal = base / "journal.md"
            import_manifest = base / "import.json"
            with (
                mock.patch.object(mod, "OUT", out),
                mock.patch.object(mod, "STATUS", status),
                mock.patch.object(mod, "JOURNAL", journal),
                mock.patch.object(mod, "IMPORT", import_manifest),
            ):
                summary = mod.main()
                self.assertGreaterEqual(summary["anchor_rows"], 12)
                self.assertGreaterEqual(summary["after_high_heat_preflight_rows"], 2)
                self.assertGreaterEqual(summary["future_compute_heavy_rows"], 1)
                self.assertEqual(summary["runtime_audit_pass_rows"], 3)
                self.assertFalse(summary["scheduler_action"])
                self.assertTrue((out / "upcomer_onset_anchor_matrix.csv").exists())
                self.assertTrue(status.exists())
                self.assertTrue(journal.exists())
                self.assertTrue(import_manifest.exists())

                with (out / "upcomer_onset_anchor_matrix.csv").open(newline="") as f:
                    anchors = list(csv.DictReader(f))
                self.assertTrue(all(row["launch_allowed_in_this_row"] == "false" for row in anchors))
                with import_manifest.open() as f:
                    manifest = json.load(f)
                self.assertFalse(manifest["scheduler_action"])
                self.assertFalse(manifest["native_solver_outputs_mutated"])


if __name__ == "__main__":
    unittest.main()
