from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.extract import build_upcomer_exchange_three_case_cell_vtk_manifest as builder


class UpcomerExchangeThreeCaseCellVtkManifestTests(unittest.TestCase):
    def test_cell_manifest_releases_all_three_cell_lanes(self) -> None:
        rows = builder.build_cell_manifest_rows()
        self.assertEqual([row["case_id"] for row in rows], ["salt_2", "salt_3", "salt_4"])
        for row in rows:
            self.assertEqual(row["validation_status"], "pass")
            self.assertEqual(row["release_status"], "cell_lane_released_for_manifest")
            self.assertEqual(str(row["expected_cells"]), "2166996")
            self.assertEqual(str(row["observed_cells"]), "2166996")
            self.assertEqual(row["cell_vtk_exists"], "true")
            self.assertTrue(builder.required_fields_present(row["observed_fields"]))

    def test_sampler_manifest_populates_only_cell_vtk_paths(self) -> None:
        rows = builder.build_sampler_manifest_rows(builder.build_cell_manifest_rows())
        self.assertEqual(len(rows), 3)
        for row in rows:
            self.assertNotIn("MISSING_CELL_VTK", row["cell_vtk"])
            self.assertEqual(row["interface_vtk"], "MISSING_EXCHANGE_INTERFACE_VTK")
            self.assertEqual(row["wall_vtk"], "MISSING_WALL_VTK")
            self.assertEqual(row["throughflow_nx"], "")
            self.assertEqual(row["interface_nx"], "")

    def test_package_summary_keeps_sampler_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            payload = builder.build_package(Path(tmp) / "pkg")
        self.assertEqual(payload["summary"]["cell_vtk_pass_rows"], 3)
        self.assertEqual(payload["summary"]["sampler_ready_rows"], 0)
        self.assertGreaterEqual(payload["summary"]["remaining_blocker_rows"], 12)
        self.assertFalse(payload["summary"]["sampler_harvest_launched"])
        self.assertFalse(payload["summary"]["residual_absorbed_into_internal_Nu"])

    def test_blockers_include_interface_wall_source_and_qwall(self) -> None:
        blocked = {(row["case_id"], row["blocked_input"]) for row in builder.build_blocker_rows()}
        for case_id in builder.CASE_IDS:
            self.assertIn((case_id, "exchange_interface_vtk"), blocked)
            self.assertIn((case_id, "wall_vtk"), blocked)
            self.assertIn((case_id, "source_sink_ledger"), blocked)
            self.assertIn((case_id, "Q_wall_W"), blocked)


if __name__ == "__main__":
    unittest.main()
