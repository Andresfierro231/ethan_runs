#!/usr/bin/env python3
"""Tests for two-tap nonrecirculating same-QOI anchor request refresh."""

from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools.analyze import build_two_tap_nonrecirculating_same_qoi_anchor_request_refresh as mod


class TwoTapNonrecirculatingSameQoiAnchorRequestRefreshTest(unittest.TestCase):
    def test_anchor_request_locks_exact_endpoint_and_no_submit(self) -> None:
        row = mod.build_anchor_request()[0]

        self.assertEqual(row["required_endpoint_pair"], "lower_leg__s04->right_leg__s00")
        self.assertEqual(row["pressure_basis_primary"], "static_p_pa")
        self.assertEqual(row["pressure_basis_cross_check"], "p_rgh_with_documented_hydrostatic_conversion")
        self.assertEqual(row["auto_submit"], "false")
        self.assertEqual(row["current_rows_use"], "diagnostic_apparent_cluster_loss_only")

    def test_sampling_contract_has_same_qoi_formulas_and_no_clipping(self) -> None:
        rows = mod.build_sampling_contract()
        by_qoi = {row["qoi"]: row for row in rows}

        self.assertEqual(set(by_qoi), {"Delta_p", "K_app", "RAF", "RMF"})
        self.assertTrue(all(row["endpoint_pair"] == "lower_leg__s04->right_leg__s00" for row in rows))
        self.assertTrue(all(row["sign_convention"] == "p_upstream_minus_p_downstream" for row in rows))
        self.assertTrue(all(row["clipping_policy"] == "reject_nonphysical_no_make_positive_correction" for row in rows))

    def test_main_writes_anchor_refresh_package(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            with (
                mock.patch.object(mod, "OUT", base / "out"),
                mock.patch.object(mod, "STATUS", base / "status.md"),
                mock.patch.object(mod, "JOURNAL", base / "journal.md"),
                mock.patch.object(mod, "IMPORT", base / "import.json"),
            ):
                summary = mod.main()

            self.assertFalse(summary["auto_submit"])
            self.assertEqual(summary["component_k_current_status"], "blocked_current_rows_diagnostic_only")
            with (base / "out/uq_requirements.csv").open(newline="") as handle:
                self.assertEqual(len(list(csv.DictReader(handle))), 3)
            with (base / "import.json").open() as handle:
                manifest = json.load(handle)
            self.assertFalse(manifest["native_solver_outputs_mutated"])


if __name__ == "__main__":
    unittest.main()
