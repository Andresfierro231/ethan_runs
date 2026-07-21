from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.extract import build_s13_upcomer_exchange_geometry_contract as builder


class S13UpcomerExchangeGeometryContractTests(unittest.TestCase):
    def test_interface_contract_fails_closed_for_all_cases(self) -> None:
        rows = builder.interface_contract_rows()
        self.assertEqual([row["case_id"] for row in rows], ["salt_2", "salt_3", "salt_4"])
        for row in rows:
            self.assertEqual(row["release_status"], "blocked_no_trusted_exchange_interface")
            self.assertEqual(row["mdot_exchange_ready"], "false")
            self.assertIn("recirculation cell toward main throughflow", row["normal_vector_convention"])

    def test_wall_core_contract_blocks_q_wall_without_region_link(self) -> None:
        rows = builder.wall_core_contract_rows()
        self.assertEqual(len(rows), 3)
        for row in rows:
            self.assertEqual(row["release_status"], "blocked_no_recirc_region_wall_band_link")
            self.assertEqual(row["q_wall_w_ready"], "false")
            self.assertIn("pipeleg_right", row["wall_patch_candidates"])

    def test_downstream_matrix_blocks_harvest_until_surface_lanes_exist(self) -> None:
        rows = builder.downstream_input_rows()
        harvest_rows = [row for row in rows if row["input_lane"] == "exchange_cell_harvest"]
        self.assertEqual(len(harvest_rows), 3)
        for row in harvest_rows:
            self.assertEqual(row["status"], "blocked")
            self.assertIn("interface/wall/Q_wall", row["blocking_reason"])

    def test_build_package_writes_fail_closed_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "pkg"
            payload = builder.build_package(out)
            summary = payload["summary"]
            self.assertEqual(summary["released_interface_rows"], 0)
            self.assertEqual(summary["released_wall_core_rows"], 0)
            self.assertEqual(summary["released_q_wall_rows"], 0)
            self.assertEqual(summary["harvest_ready_rows"], 0)
            self.assertFalse(summary["surface_vtk_extraction_allowed"])
            for name in [
                "geometry_source_ledger.csv",
                "interface_geometry_contract.csv",
                "wall_core_band_contract.csv",
                "downstream_surface_vtk_inputs.csv",
                "no_mutation_guardrails.csv",
                "source_manifest.csv",
                "summary.json",
                "README.md",
            ]:
                self.assertTrue((out / name).exists(), name)


if __name__ == "__main__":
    unittest.main()
