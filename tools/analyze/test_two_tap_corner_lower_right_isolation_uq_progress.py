#!/usr/bin/env python3
"""Tests for two-tap corner_lower_right isolation and same-QOI UQ progress."""

from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools.analyze import build_two_tap_corner_lower_right_isolation_uq_progress as mod


class TwoTapCornerLowerRightIsolationUqProgressTest(unittest.TestCase):
    def test_component_basis_uses_exact_endpoint_labels_and_static_pressure(self) -> None:
        rows = mod.build_component_isolation_basis()

        self.assertEqual(len(rows), 3)
        self.assertTrue(all(row["endpoint_pair"] == "lower_leg__s04->right_leg__s00" for row in rows))
        self.assertTrue(all(row["pressure_basis_primary"] == "static_p_pa" for row in rows))
        self.assertTrue(all(row["delta_p_sign_convention"] == "p_upstream_minus_p_downstream" for row in rows))
        self.assertTrue(all(float(row["delta_p_static_Pa"]) < 0 for row in rows))
        self.assertTrue(
            all(row["p_rgh_conversion_status"] == "not_reconstructed_missing_exact_hydrostatic_term" for row in rows)
        )
        self.assertTrue(all(row["reverse_flow_gate"] == "fail_material_reverse_flow" for row in rows))

    def test_straight_development_subtraction_is_blocked_same_basis(self) -> None:
        rows = mod.build_straight_development_subtraction_ledger()

        self.assertEqual(len(rows), 3)
        self.assertTrue(all(row["subtraction_status"] == "blocked_missing_same_basis_reference" for row in rows))
        self.assertTrue(all(row["same_window_re_status"] == "missing_not_in_endpoint_sampler" for row in rows))
        self.assertTrue(all(row["same_window_mu_status"] == "missing_not_in_endpoint_sampler" for row in rows))
        self.assertTrue(all(row["clipping_policy"] == "no_clipping_no_make_positive_correction" for row in rows))

    def test_apparent_cluster_allowed_but_component_k_blocked(self) -> None:
        apparent = mod.build_apparent_cluster_loss()
        component = mod.build_component_k_decision()

        self.assertEqual(len(apparent), 3)
        self.assertTrue(all(row["decision"] == "apparent_cluster_loss_diagnostic" for row in apparent))
        self.assertTrue(all(row["fit_use"] == "not_fit_not_model_selection" for row in apparent))
        self.assertEqual(len(component), 3)
        self.assertTrue(
            all(row["component_k_status"] == "component_K_blocked_apparent_cluster_only" for row in component)
        )
        self.assertTrue(all(row["component_k_admitted"] == "false" for row in component))
        self.assertTrue(all(row["f6_fit_performed"] == "false" for row in component))

    def test_same_qoi_time_and_mesh_uq_remain_missing(self) -> None:
        time_rows = mod.build_same_qoi_time_uq()
        mesh_rows = mod.build_same_qoi_mesh_uq()

        self.assertEqual(len(time_rows), 3)
        self.assertTrue(all(row["time_uq_status"] == "missing_no_same_window_neighbors" for row in time_rows))
        self.assertTrue(all(row["time_family_member_count"] == 1 for row in time_rows))
        self.assertEqual(len(mesh_rows), 3)
        self.assertTrue(all(row["mesh_uq_status"] == "missing_no_GCI_not_same_qoi" for row in mesh_rows))
        self.assertTrue(all(row["eligible_same_qoi_mesh_members"] == 0 for row in mesh_rows))

    def test_main_writes_progress_package(self) -> None:
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

            self.assertEqual(summary["case_count"], 3)
            self.assertEqual(summary["component_k_admitted_rows"], 0)
            self.assertEqual(summary["same_qoi_time_uq_pass_rows"], 0)
            self.assertEqual(summary["same_qoi_mesh_uq_pass_rows"], 0)
            self.assertFalse(summary["f6_fit_performed"])
            for filename in (
                "component_isolation_basis.csv",
                "straight_development_subtraction_ledger.csv",
                "apparent_cluster_loss.csv",
                "component_k_decision.csv",
                "same_qoi_time_uq.csv",
                "same_qoi_mesh_uq.csv",
                "split_decision.csv",
            ):
                self.assertTrue((out / filename).exists())
                with (out / filename).open(newline="") as handle:
                    self.assertEqual(len(list(csv.DictReader(handle))), 3)
            with import_manifest.open() as handle:
                manifest = json.load(handle)
            self.assertFalse(manifest["native_solver_outputs_mutated"])


if __name__ == "__main__":
    unittest.main()
