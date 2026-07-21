#!/usr/bin/env python3
"""Tests for the dry upcomer exchange-cell sampler design."""

from __future__ import annotations

import csv
import math
import tempfile
import unittest
from pathlib import Path

import numpy as np

from tools.extract import sample_upcomer_exchange_cell as sampler


CELL_VTK = """# vtk DataFile Version 3.0
cells
ASCII
DATASET POLYDATA
POINTS 12 float
0 0 0  1 0 0  1 1 0  0 1 0
0 0 1  1 0 1  1 1 1  0 1 1
0 0 2  1 0 2  1 1 2  0 1 2
POLYGONS 3 15
4 0 1 2 3
4 4 5 6 7
4 8 9 10 11
CELL_DATA 3
SCALARS cellVolume float 1
LOOKUP_TABLE default
1
2
3
SCALARS recircMask float 1
LOOKUP_TABLE default
1
0
1
SCALARS rho float 1
LOOKUP_TABLE default
2
4
3
SCALARS mu float 1
LOOKUP_TABLE default
10
20
15
SCALARS T float 1
LOOKUP_TABLE default
300
400
330
"""


INTERFACE_VTK = """# vtk DataFile Version 3.0
interface
ASCII
DATASET POLYDATA
POINTS 8 float
0 0 0  1 0 0  1 1 0  0 1 0
2 0 0  3 0 0  3 1 0  2 1 0
POLYGONS 2 10
4 0 1 2 3
4 4 5 6 7
CELL_DATA 2
VECTORS U float
1 0 0
-1 0 0
SCALARS rho float 1
LOOKUP_TABLE default
2
2
"""


WALL_VTK = """# vtk DataFile Version 3.0
wall
ASCII
DATASET POLYDATA
POINTS 8 float
0 0 0  1 0 0  1 1 0  0 1 0
2 0 0  3 0 0  3 1 0  2 1 0
POLYGONS 2 10
4 0 1 2 3
4 4 5 6 7
CELL_DATA 2
SCALARS T float 1
LOOKUP_TABLE default
350
370
SCALARS wallHeatFlux float 1
LOOKUP_TABLE default
100
200
"""


class UpcomerExchangeCellSamplerDesignTests(unittest.TestCase):
    def write_fixture(self, directory: Path, name: str, text: str) -> Path:
        path = directory / name
        path.write_text(text, encoding="utf-8")
        return path

    def test_cell_state_computes_volume_ratios_and_temperature(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            root = Path(raw_tmp)
            path = self.write_fixture(root, "cells.vtk", CELL_VTK)
            state = sampler.compute_cell_state(path, np.array([1.0, 0.0, 0.0]))
        self.assertEqual(state["recirc_mask_basis"], "recircMask")
        self.assertEqual(state["volume_basis"], "vtk_cellVolume")
        self.assertAlmostEqual(state["V_recirc_m3"], 4.0)
        self.assertAlmostEqual(state["R_rho"], 2.75 / 4.0)
        self.assertAlmostEqual(state["R_mu"], 13.75 / 20.0)
        self.assertAlmostEqual(state["T_recirc_K"], 324.54545454545456)
        self.assertAlmostEqual(state["T_main_K"], 400.0)

    def test_cell_state_uses_volume_csv_by_cell_id_when_vtk_lacks_cell_volume(self) -> None:
        no_volume = CELL_VTK.replace(
            "SCALARS cellVolume float 1\nLOOKUP_TABLE default\n1\n2\n3\n",
            "SCALARS cellId float 1\nLOOKUP_TABLE default\n2\n0\n1\n",
        )
        with tempfile.TemporaryDirectory() as raw_tmp:
            root = Path(raw_tmp)
            cell_path = self.write_fixture(root, "cells_no_volume.vtk", no_volume)
            volume_path = root / "volumes.csv"
            volume_path.write_text("cell_id,cellVolume_m3\n0,2\n1,3\n2,1\n", encoding="utf-8")
            state = sampler.compute_cell_state(
                cell_path,
                np.array([1.0, 0.0, 0.0]),
                volume_csv=volume_path,
            )
        self.assertEqual(state["volume_basis"], "mesh_volume_csv_by_cell_id")
        self.assertAlmostEqual(state["V_recirc_m3"], 4.0)
        self.assertAlmostEqual(state["V_main_m3"], 2.0)

    def test_interface_exchange_uses_balanced_bidirectional_flux(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            root = Path(raw_tmp)
            path = self.write_fixture(root, "interface.vtk", INTERFACE_VTK)
            exchange = sampler.compute_interface_exchange(path, np.array([1.0, 0.0, 0.0]))
        self.assertAlmostEqual(exchange["positive_mdot_main_to_cell_kg_s"], 2.0)
        self.assertAlmostEqual(exchange["negative_mdot_cell_to_main_kg_s"], 2.0)
        self.assertAlmostEqual(exchange["mdot_exchange_kg_s"], 2.0)
        self.assertAlmostEqual(exchange["exchange_flux_imbalance_kg_s"], 0.0)

    def test_assembled_row_carries_residuals_and_tau(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            root = Path(raw_tmp)
            cell = sampler.compute_cell_state(self.write_fixture(root, "cells.vtk", CELL_VTK), np.array([1.0, 0.0, 0.0]))
            interface = sampler.compute_interface_exchange(
                self.write_fixture(root, "interface.vtk", INTERFACE_VTK),
                np.array([1.0, 0.0, 0.0]),
            )
            wall = sampler.compute_wall_state(self.write_fixture(root, "wall.vtk", WALL_VTK))
            row = sampler.assemble_exchange_row(
                "fixture_case",
                "10",
                cell,
                interface,
                wall,
                pressure_terms={
                    "delta_p_observed_pa": 100.0,
                    "delta_p_straight_pa": 30.0,
                    "delta_p_hydrostatic_pa": 20.0,
                    "delta_p_minor_pa": 5.0,
                },
                energy_terms={"Q_wall_W": 300.0, "Q_source_W": 50.0, "Q_sink_W": 20.0, "cp_J_kg_K": 1.0},
            )
        self.assertAlmostEqual(row["tau_recirc_s"], 5.5)
        self.assertAlmostEqual(row["pressure_residual_Pa"], 45.0)
        expected_energy = 300.0 + 50.0 - 20.0 - 2.0 * (cell["T_recirc_K"] - cell["T_main_K"])
        self.assertAlmostEqual(row["energy_residual_W"], expected_energy)
        self.assertAlmostEqual(row["wall_core_delta_T_K"], 360.0 - cell["T_recirc_K"])
        self.assertEqual(row["admission_use"], "diagnostic_only_until_same_qoi_uq_and_phase4b_rescore")
        self.assertEqual(row["fit_allowed_now"], "false")
        self.assertEqual(row["score_allowed_now"], "false")
        self.assertEqual(row["residual_policy"], "do_not_hide_heat_residual_in_internal_Nu")

    def test_missing_mu_is_explicitly_unavailable(self) -> None:
        no_mu = CELL_VTK.replace("SCALARS mu float 1\nLOOKUP_TABLE default\n10\n20\n15\n", "")
        with tempfile.TemporaryDirectory() as raw_tmp:
            root = Path(raw_tmp)
            state = sampler.compute_cell_state(
                self.write_fixture(root, "cells_no_mu.vtk", no_mu),
                np.array([1.0, 0.0, 0.0]),
            )
        self.assertTrue(math.isnan(state["R_mu"]))
        self.assertEqual(state["R_mu_status"], "not_available_with_reason:missing_mu")

    def test_pressure_and_energy_residuals_fail_closed_when_missing(self) -> None:
        pressure, pressure_status = sampler.pressure_residual_pa(None, 1.0)
        energy, energy_status = sampler.energy_residual_w(1.0, 0.0, 0.0, None, 1.0, 1.0, 2.0)
        self.assertTrue(math.isnan(pressure))
        self.assertEqual(pressure_status, "not_available_with_reason:missing_pressure_basis")
        self.assertTrue(math.isnan(energy))
        self.assertEqual(energy_status, "not_available_with_reason:missing_energy_or_exchange_basis")

    def test_build_package_writes_schema_and_plan_without_launch(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            out = Path(raw_tmp) / "pkg"
            payload = sampler.build_package(out)
            self.assertEqual(payload["summary"]["required_schema_fields"], 10)
            self.assertEqual(payload["summary"]["dry_plan_rows"], 3)
            self.assertFalse(payload["summary"]["solver_or_postprocessing_or_sampler_launched"])
            self.assertTrue((out / "exchange_sampler_required_schema.csv").exists())
            self.assertTrue((out / "exchange_sampler_dry_extraction_plan.csv").exists())
            self.assertTrue((out / "README.md").exists())
            with (out / "exchange_sampler_required_schema.csv").open(newline="", encoding="utf-8") as handle:
                schema = list(csv.DictReader(handle))
        self.assertEqual(
            {row["field_name"] for row in schema},
            {
                "R_mu",
                "R_rho",
                "V_recirc",
                "mdot_exchange",
                "tau_recirc",
                "T_main",
                "T_recirc",
                "wall_core_delta_T",
                "pressure_residual",
                "energy_residual",
            },
        )

    def test_unavailable_row_fails_closed_and_writes_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            out = Path(raw_tmp) / "pkg"
            out.mkdir()
            row = sampler.unavailable_exchange_row(
                "salt_2",
                "7915",
                ["cell_vtk", "interface_vtk"],
                "missing_required_vtk_inputs",
            )
            sampler.write_extraction_rows(out, [row])
            with (out / "exchange_sampler_rows.csv").open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
        self.assertEqual(rows[0]["extraction_status"], "not_available_with_reason:missing_required_vtk_inputs")
        self.assertEqual(rows[0]["missing_inputs"], "cell_vtk;interface_vtk")
        self.assertEqual(rows[0]["fit_allowed_now"], "false")
        self.assertEqual(rows[0]["score_allowed_now"], "false")
        self.assertEqual(rows[0]["V_recirc_m3"], "")

    def test_write_extraction_rows_persists_computed_guard_columns(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            root = Path(raw_tmp)
            cell = sampler.compute_cell_state(
                self.write_fixture(root, "cells.vtk", CELL_VTK),
                np.array([1.0, 0.0, 0.0]),
            )
            interface = sampler.compute_interface_exchange(
                self.write_fixture(root, "interface.vtk", INTERFACE_VTK),
                np.array([1.0, 0.0, 0.0]),
            )
            row = sampler.assemble_exchange_row("fixture_case", "10", cell, interface)
            sampler.write_extraction_rows(root, [row])
            with (root / "exchange_sampler_rows.csv").open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
        self.assertEqual(rows[0]["extraction_status"], "computed_from_supplied_inputs")
        self.assertEqual(rows[0]["fit_allowed_now"], "false")
        self.assertEqual(rows[0]["score_allowed_now"], "false")
        self.assertEqual(rows[0]["runtime_policy"], "not_a_predictive_runtime_input")
        self.assertEqual(rows[0]["volume_basis"], "vtk_cellVolume")


if __name__ == "__main__":
    unittest.main()
