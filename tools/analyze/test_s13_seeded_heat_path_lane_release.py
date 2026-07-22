from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from tools.analyze import build_s13_seeded_heat_path_lane_release as builder


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class S13SeededHeatPathLaneReleaseTests(unittest.TestCase):
    def test_field_inventory_finds_partial_cell_field_support(self) -> None:
        rows = builder.build_field_inventory(builder.case_rows())
        self.assertEqual(len(rows), 3)
        for row in rows:
            self.assertEqual(row["has_cellID"], "true")
            self.assertEqual(row["has_U"], "true")
            self.assertEqual(row["has_T"], "true")
            self.assertEqual(row["has_rho"], "true")
            self.assertEqual(row["has_pressure_basis"], "false")
            self.assertEqual(row["has_mu_basis"], "false")
            self.assertEqual(row["has_wallHeatFlux"], "false")

    def test_qwall_contract_uses_geometry_but_releases_no_qwall(self) -> None:
        cases = builder.case_rows()
        surface_rows = builder.read_csv(builder.SURFACE_VTK / "surface_vtk_validation.csv")
        source_rows = builder.read_csv(builder.SOURCE_SINK / "source_sink_summary.csv")
        rows = builder.build_qwall_contract(cases, surface_rows, source_rows)
        self.assertEqual(len(rows), 3)
        for row in rows:
            self.assertEqual(row["trusted_wall_geometry_ready"], "true")
            self.assertEqual(row["wallHeatFlux_source_exists"], "false")
            self.assertEqual(row["Q_wall_W_released"], "false")
            self.assertIn("not a substitute", row["blocking_reason"])

    def test_sampled_field_contract_blocks_pressure_qwall_and_cp(self) -> None:
        cases = builder.case_rows()
        inventory = builder.build_field_inventory(cases)
        surface_rows = builder.read_csv(builder.SURFACE_VTK / "surface_vtk_validation.csv")
        rows = builder.build_sampled_field_contract(cases, inventory, surface_rows)
        status_by_lane = {(row["case_id"], row["lane"]): row["status"] for row in rows}
        for case in ("salt_2", "salt_3", "salt_4"):
            self.assertEqual(
                status_by_lane[(case, "interface_U")],
                "geometry_ready_whole_mesh_field_present_surface_sampling_not_run",
            )
            self.assertEqual(status_by_lane[(case, "interface_pressure")], "blocked_missing_pressure_basis")
            self.assertEqual(status_by_lane[(case, "wallHeatFlux")], "blocked_missing_wallHeatFlux_Q_wall")
            self.assertEqual(status_by_lane[(case, "cp_J_kg_K")], "blocked_missing_cp_property_contract")

    def test_build_package_writes_contract_and_keeps_gates_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "pkg"
            payload = builder.build_package(out)
            summary = payload["summary"]
            self.assertEqual(summary["case_count"], 3)
            self.assertEqual(summary["geometry_surface_vtk_rows"], 6)
            self.assertEqual(summary["validated_geometry_surface_vtk_rows"], 6)
            self.assertEqual(summary["whole_mesh_cell_fields_U_T_rho_ready_rows"], 3)
            self.assertEqual(summary["pressure_basis_ready_rows"], 0)
            self.assertEqual(summary["mu_basis_ready_rows"], 0)
            self.assertEqual(summary["wallHeatFlux_ready_rows"], 0)
            self.assertEqual(summary["Q_wall_W_released_rows"], 0)
            self.assertEqual(summary["sampler_ready_rows"], 0)
            self.assertEqual(summary["harvest_ready_rows"], 0)
            self.assertFalse(summary["exchange_cell_admission_allowed"])
            self.assertFalse(summary["s11_s12_s13_s15_s6_trigger"])
            self.assertFalse(summary["residual_absorbed_into_internal_nu"])

            for name in [
                "README.md",
                "summary.json",
                "field_inventory.csv",
                "sampled_field_lane_table.csv",
                "qwall_contract.csv",
                "q_wall_source_contract.csv",
                "heat_path_lane_table.csv",
                "heat_path_lane_release.csv",
                "same_window_thermal_field_contract.csv",
                "same_window_thermal_pressure_field_contract.csv",
                "sampler_manifest_delta.csv",
                "harvest_readiness_gate.csv",
                "downstream_gate.csv",
                "sampler_refresh_gate.csv",
                "no_mutation_guardrails.csv",
                "source_manifest.csv",
            ]:
                self.assertTrue((out / name).exists(), name)

            qois = {row["qoi"] for row in read_rows(out / "harvest_readiness_gate.csv")}
            self.assertIn("V_recirc", qois)
            self.assertIn("mdot_exchange", qois)
            self.assertIn("T_recirc", qois)
            self.assertIn("pressure_residual", qois)
            self.assertIn("energy_residual", qois)
            self.assertIn("R_mu", qois)
            self.assertIn("R_rho", qois)

            gates = read_rows(out / "downstream_gate.csv")
            admission = [row for row in gates if row["gate"] == "coefficient_or_model_admission"][0]
            self.assertEqual(admission["allowed"], "false")


if __name__ == "__main__":
    unittest.main()
