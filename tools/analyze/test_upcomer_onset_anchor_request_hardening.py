#!/usr/bin/env python3
"""Tests for the hardened upcomer-onset CFD/postprocessing request."""

from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools.analyze import build_upcomer_onset_anchor_request_hardening as mod


class UpcomerOnsetAnchorRequestHardeningTest(unittest.TestCase):
    def test_target_matrix_contains_required_anchor_roles(self) -> None:
        rows = mod.build_target_matrix()
        roles = {row["acceptance_role"] for row in rows}
        nonrecirc = [row for row in rows if row["acceptance_role"] == "non_recirculating_anchor"]

        self.assertIn("non_recirculating_anchor", roles)
        self.assertIn("recirculating_anchor", roles)
        self.assertTrue(any("transition" in role for role in roles))
        self.assertTrue(all(row["launch_allowed_in_this_row"] == "false" for row in rows))
        self.assertTrue(any(float(row["target_Re_upcomer_design_min"]) >= 150 for row in nonrecirc))
        self.assertIn("RAF<=0.02", nonrecirc[0]["acceptance_gate"])
        self.assertIn("Ri_median<0.30", nonrecirc[0]["acceptance_gate"])

    def test_same_window_request_covers_wall_bulk_heat_pressure_and_properties(self) -> None:
        rows = {row["field_id"]: row for row in mod.build_same_window_request()}

        for key in [
            "bulk_temperature",
            "wall_temperature",
            "wall_bulk_deltaT",
            "velocity_vector",
            "mass_flux",
            "pressure_static",
            "wall_heat_flux",
            "fluid_properties",
            "heat_balance",
        ]:
            self.assertIn(key, rows)
            self.assertIn("same retained", rows[key]["same_window_requirement"])
        self.assertIn("junction", rows["wall_heat_flux"]["location"])
        self.assertIn("1D", rows["wall_bulk_deltaT"]["one_d_model_mapping"])

    def test_pm5_pm10_request_covers_required_metrics(self) -> None:
        rows = mod.build_pm_request()
        metrics = {row["metric"] for row in rows}

        for metric in [
            "RAF",
            "RMF",
            "SVF",
            "Re_upcomer",
            "Pr",
            "Ri",
            "Gr",
            "Ra",
            "Gz",
            "delta_p_PM5_PM10",
            "wall_bulk_deltaT_PM5_PM10",
            "wallHeatFlux_PM5_PM10_section",
        ]:
            self.assertIn(metric, metrics)
        self.assertTrue(any(row["plane_set"] == "PM5_to_PM10_pair" for row in rows))

    def test_uncertainty_requirements_unlock_needs(self) -> None:
        text = json.dumps(mod.build_uncertainty_requirements())

        self.assertIn("coarse/medium/fine", text)
        self.assertIn("RAF", text)
        self.assertIn("RMF", text)
        self.assertIn("Ri", text)
        self.assertIn("Re", text)
        self.assertIn("wall_bulk_deltaT", text)
        self.assertIn("time-window", text)
        self.assertIn("delta_p", text)

    def test_guardrails_forbid_misuse(self) -> None:
        text = json.dumps(mod.build_guardrails())

        self.assertIn("Nu", text)
        self.assertIn("f_D", text)
        self.assertIn("corner K", text)
        self.assertIn("different time windows", text)
        self.assertIn("design target", text)

    def test_main_writes_complete_nonlaunching_package(self) -> None:
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

                self.assertGreaterEqual(summary["target_matrix_rows"], 12)
                self.assertGreaterEqual(summary["pm5_pm10_request_rows"], 30)
                self.assertGreaterEqual(summary["mesh_time_requirement_rows"], 5)
                self.assertFalse(summary["scheduler_action"])
                self.assertFalse(summary["native_solver_outputs_mutated"])
                self.assertFalse(summary["registry_mutated"])
                self.assertFalse(summary["unblocks_upcomer_onset_data_sparsity"])

                for name in [
                    "target_re_thermal_drive_matrix.csv",
                    "same_window_field_request.csv",
                    "pm5_pm10_extraction_request.csv",
                    "mesh_time_uncertainty_requirements.csv",
                    "launch_gate_checklist.csv",
                    "misuse_guardrails.csv",
                    "blocker_attack_map.csv",
                    "source_manifest.csv",
                    "cfd_postprocessing_request.json",
                    "summary.json",
                    "README.md",
                ]:
                    self.assertTrue((out / name).exists(), name)
                self.assertTrue(status.exists())
                self.assertTrue(journal.exists())
                self.assertTrue(import_manifest.exists())

                with (out / "target_re_thermal_drive_matrix.csv").open(newline="") as f:
                    matrix = list(csv.DictReader(f))
                self.assertTrue(all(row["launch_allowed_in_this_row"] == "false" for row in matrix))

                with import_manifest.open() as f:
                    manifest = json.load(f)
                self.assertEqual(manifest["task"], mod.TASK)
                self.assertFalse(manifest["scheduler_action"])
                self.assertFalse(manifest["native_solver_outputs_mutated"])


if __name__ == "__main__":
    unittest.main()
