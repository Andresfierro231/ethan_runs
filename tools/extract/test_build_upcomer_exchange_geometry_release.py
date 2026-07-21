from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.extract import build_upcomer_exchange_geometry_release as builder


class UpcomerExchangeGeometryReleaseTests(unittest.TestCase):
    def test_parse_toposet_planes_extracts_name_point_normal(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "topoSetDict"
            path.write_text(
                """
actions
(
    {
        name    mdot_pipeleg_right_02_middle;
        type    faceZoneSet;
        action  new;
        source  planeToFaceZone;
        point   (0.1 0.2 0.3);
        normal  (0 1 0);
        include closest;
    }
);
""",
                encoding="utf-8",
            )
            rows = builder.parse_toposet_planes(path)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["facezone"], "mdot_pipeleg_right_02_middle")
        self.assertEqual(rows[0]["point"], "0.1 0.2 0.3")
        self.assertEqual(rows[0]["normal"], "0 1 0")

    def test_geometry_decision_releases_only_cell_vtk(self) -> None:
        rows = builder.geometry_decision_rows()
        by_lane = {row["geometry_lane"]: row for row in rows}
        self.assertEqual(by_lane["cell_vtk"]["decision"], "released_whole_mesh_same_order")
        self.assertEqual(by_lane["exchange_interface_vtk"]["launch_allowed_after_this_row"], "false")
        self.assertEqual(by_lane["wall_vtk"]["launch_allowed_after_this_row"], "false")

    def test_build_package_writes_expected_ledgers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "pkg"
            payload = builder.build_package(out)
            summary = payload["summary"]
            self.assertEqual(summary["case_rows"], 3)
            self.assertEqual(summary["released_cell_vtk_rows"], 3)
            self.assertEqual(summary["released_exchange_interface_rows"], 0)
            self.assertEqual(summary["released_wall_core_rows"], 0)
            self.assertFalse(summary["scheduler_action"])
            for name in [
                "geometry_release_decision.csv",
                "cell_vtk_contract.csv",
                "facezone_candidate_audit.csv",
                "wall_core_candidate_audit.csv",
                "planned_extraction_commands.csv",
                "README.md",
            ]:
                self.assertTrue((out / name).exists(), name)


if __name__ == "__main__":
    unittest.main()
