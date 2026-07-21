#!/usr/bin/env python3
"""Tests for run_cfd_bc_no_radiation_1d_parity.py."""

from __future__ import annotations

import csv
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.analyze import run_cfd_bc_no_radiation_1d_parity as parity  # noqa: E402


class CfdBcNoRadiationParityTests(unittest.TestCase):
    def read_rows(self, path: Path) -> list[dict[str, str]]:
        with path.open(newline="", encoding="utf-8") as handle:
            return list(csv.DictReader(handle))

    def build_plan_only(self) -> Path:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        out = Path(tmp.name) / "pkg"
        args = parity.parse_args(["--output-dir", str(out), "--plan-only", "--strict"])
        metadata = parity.build_package(args)
        self.assertEqual(24, metadata["boundary_contract_rows"])
        self.assertEqual(12, metadata["run_plan_rows"])
        self.assertEqual(0, metadata["result_rows"])
        return out

    def test_boundary_contract_preserves_heater_and_cooler_setup_terms(self) -> None:
        out = self.build_plan_only()
        rows = self.read_rows(out / "cfd_boundary_condition_contract_no_radiation.csv")
        salt2_heater = next(row for row in rows if row["case_id"] == "salt_2" and row["role"] == "heater")
        salt2_cooler = next(row for row in rows if row["case_id"] == "salt_2" and row["role"] == "cooler")

        self.assertEqual("heated_incline", salt2_heater["fluid_parent_segment"])
        self.assertAlmostEqual(265.7, float(salt2_heater["imposed_source_W"]), places=6)
        self.assertAlmostEqual(243.51909758, float(salt2_heater["realized_source_W"]), places=6)
        self.assertEqual("cooled_incline_hx_active", salt2_cooler["fluid_parent_segment"])
        self.assertAlmostEqual(136.350739906, float(salt2_cooler["imposed_loss_W"]), places=6)

    def test_run_plan_forces_radiation_off_for_all_primary_modes(self) -> None:
        out = self.build_plan_only()
        rows = self.read_rows(out / "run_plan.csv")
        self.assertEqual({"False"}, {row["radiation_on"] for row in rows})
        self.assertEqual(
            {
                "N0_current_fluid_rad_off",
                "N1_heater_cooler_imposed_rad_off",
                "N2_cfd_setup_bc_plus_passive_conv_rad_off",
                "N3_realized_wallflux_diagnostic_rad_off",
            },
            {row["path_id"] for row in rows},
        )

    def test_case_maps_include_heater_test_cooler_and_external_hA(self) -> None:
        patch_rows = parity.read_csv(parity.DEFAULT_PATCH_TABLE)
        contract = parity.build_boundary_contract(patch_rows)
        maps = parity.case_maps(contract, "salt_2")

        self.assertAlmostEqual(265.7, maps["heater_sources"]["heated_incline"], places=6)
        self.assertAlmostEqual(265.7, maps["heater_test_sources"]["heated_incline"], places=6)
        self.assertAlmostEqual(37.0, maps["heater_test_sources"]["test_section"], places=6)
        self.assertAlmostEqual(136.350739906, maps["cooler_imposed_loss"], places=6)
        self.assertGreater(maps["hA_map"]["heated_incline"], 0.0)
        self.assertGreater(maps["hA_map"]["test_section"], 0.0)
        self.assertNotIn("cooled_incline_hx_active", {k for k, v in maps["hA_map"].items() if v <= 0.0})

    def test_external_hA_loss_uses_positive_bulk_to_ambient_delta_only(self) -> None:
        class Segment:
            name = "heated_incline"
            resolved_parent_name = "heated_incline"
            parent_start_fraction = 0.0
            parent_end_fraction = 1.0

        self.assertAlmostEqual(
            20.0,
            parity.external_hA_loss_for_segment(Segment(), 310.0, {"heated_incline": 2.0}, {"heated_incline": 300.0}),
        )
        self.assertAlmostEqual(
            0.0,
            parity.external_hA_loss_for_segment(Segment(), 295.0, {"heated_incline": 2.0}, {"heated_incline": 300.0}),
        )

    def test_section_merge_computes_model_minus_cfd_residuals(self) -> None:
        section_rows = [
            {
                "case_id": "salt_x",
                "source_id": "src",
                "path_id": "N",
                "one_d_segment": "lower_leg",
                "model_source_W": 10.0,
                "model_cooler_loss_W": 1.0,
                "model_external_loss_W": 2.0,
                "model_net_to_fluid_W": 7.0,
            }
        ]
        contract_rows = [
            {
                "case_id": "salt_x",
                "one_d_segment": "lower_leg",
                "imposed_source_W": 12.0,
                "imposed_loss_W": 3.0,
                "realized_source_W": 9.0,
                "realized_loss_W": 4.0,
            }
        ]
        merged = parity.merge_section_comparison(section_rows, contract_rows)
        self.assertAlmostEqual(2.0, merged[0]["model_minus_cfd_realized_net_W"])
        self.assertAlmostEqual(-2.0, merged[0]["model_minus_cfd_imposed_net_W"])


if __name__ == "__main__":
    unittest.main()
