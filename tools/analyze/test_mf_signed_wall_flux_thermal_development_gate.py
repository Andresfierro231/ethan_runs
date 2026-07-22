#!/usr/bin/env python3.11
"""Tests for the integrated signed wall-flux thermal-development gate."""

from __future__ import annotations

import csv
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.analyze.build_mf_signed_wall_flux_thermal_development_gate import OUT, build


def rows(name: str) -> list[dict[str, str]]:
    with (OUT / name).open(newline="") as f:
        return list(csv.DictReader(f))


class SignedWallFluxThermalDevelopmentGateTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        build()

    def test_summary_is_diagnostic_only(self) -> None:
        summary = json.loads((OUT / "summary.json").read_text())
        self.assertEqual(summary["decision"], "diagnostic_only_no_candidate_reviewable")
        self.assertEqual(summary["candidate_reviewable_rows"], 0)
        self.assertEqual(summary["release_gates_passed"], 0)
        self.assertFalse(summary["source_property_release"])
        self.assertFalse(summary["coefficient_admission"])
        self.assertFalse(summary["final_score"])
        self.assertFalse(summary["residual_absorbed_into_internal_nu"])

    def test_residual_owner_layers_are_separated(self) -> None:
        owner_rows = rows("residual_owner_decomposition_table.csv")
        owners = {row["owner_layer"] for row in owner_rows}
        self.assertIn("bulk_to_TP_projection_thermal_development", owners)
        self.assertIn("signed_wall_or_source_heat_path", owners)
        self.assertIn("recirculating_upcomer_exchange", owners)
        self.assertIn("TP_to_TW_wall_shape_axial_mixing", owners)
        self.assertIn("segment_source_placement", owners)
        self.assertIn("empirical_bias_or_hidden_fit", owners)
        self.assertTrue(all(row["candidate_review_status"] != "reviewable" for row in owner_rows))

    def test_release_gate_blocks_every_release(self) -> None:
        gates = rows("source_property_release_gate.csv")
        self.assertGreaterEqual(len(gates), 7)
        self.assertTrue(all(row["passed"] == "False" for row in gates))
        self.assertTrue(all(row["release_allowed"] == "False" for row in gates))

    def test_runtime_forbids_wallheatflux_and_targets(self) -> None:
        runtime = {row["item"]: row for row in rows("runtime_legality_audit.csv")}
        self.assertEqual(runtime["realized CFD wallHeatFlux"]["runtime_allowed"], "False")
        self.assertEqual(runtime["TP/TW target temperatures"]["fit_allowed"], "False")
        self.assertEqual(runtime["empirical bias offsets"]["runtime_allowed"], "False")

    def test_next_sequence_prioritizes_mesh_and_source_basis(self) -> None:
        plan = rows("next_analysis_sequence.csv")
        self.assertEqual(plan[0]["next_analysis"], "same-label S13 mesh-family generation/GCI or explicit fail-close")
        self.assertEqual(plan[1]["next_analysis"], "signed source/property heat-path release preflight")
        self.assertEqual(plan[2]["next_analysis"], "bulk-to-TP formula gate")


if __name__ == "__main__":
    unittest.main()
