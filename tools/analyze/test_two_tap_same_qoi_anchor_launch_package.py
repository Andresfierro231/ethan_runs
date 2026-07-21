#!/usr/bin/env python3
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools.analyze import build_two_tap_same_qoi_anchor_launch_package as mod


class TwoTapSameQoiAnchorLaunchPackageTest(unittest.TestCase):
    def test_contract_keeps_exact_endpoint_and_no_clipping(self) -> None:
        rows = mod.build_endpoint_sampling_contract()

        self.assertEqual({row["qoi"] for row in rows}, {"Delta_p", "K_app", "RAF", "RMF"})
        self.assertTrue(all(row["endpoint_pair"] == "lower_leg__s04->right_leg__s00" for row in rows))
        self.assertTrue(all(row["pressure_basis_primary"] == "static_p_pa" for row in rows))
        self.assertTrue(all(row["clipping_policy"] == "reject_nonphysical_no_make_positive_correction" for row in rows))

    def test_launch_is_blocked_and_no_submit_without_source_case(self) -> None:
        staged = mod.build_staged_copy_case_request()[0]
        preflight = mod.build_nonrecirc_gate_preflight()
        launch = mod.build_sbatch_or_manual_launch_plan(preflight)[0]

        self.assertEqual(staged["staged_copy_status"], "blocked")
        self.assertEqual(launch["launch_ready"], "false")
        self.assertEqual(launch["auto_submit"], "false")

    def test_main_writes_launch_package(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            with (
                mock.patch.object(mod, "OUT", base / "out"),
                mock.patch.object(mod, "STATUS", base / "status.md"),
                mock.patch.object(mod, "JOURNAL", base / "journal.md"),
                mock.patch.object(mod, "IMPORT", base / "import.json"),
            ):
                summary = mod.main()

            self.assertFalse(summary["launch_ready"])
            self.assertFalse(summary["auto_submit"])
            self.assertTrue((base / "out/sbatch_or_manual_launch_plan.csv").exists())


if __name__ == "__main__":
    unittest.main()
