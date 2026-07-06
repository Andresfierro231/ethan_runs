from __future__ import annotations

import unittest

from tools.analyze.build_ethan_frozen_state_1d_validation_package import (
    build_sensor_reference_rows,
    case_family_from_label,
    safe_mae,
    safe_rmse,
)


class EthanFrozenState1DValidationPackageTests(unittest.TestCase):
    def test_case_family_from_label_trims_variant(self) -> None:
        self.assertEqual(case_family_from_label("Salt 2 Kirst"), "Salt 2")
        self.assertEqual(case_family_from_label("Salt 4 Val"), "Salt 4")

    def test_safe_error_helpers(self) -> None:
        self.assertAlmostEqual(safe_mae([1.0, -2.0, 3.0]), 2.0)
        self.assertAlmostEqual(safe_rmse([3.0, 4.0]), (12.5) ** 0.5)

    def test_build_sensor_reference_rows_uses_tp_core_and_tw_wall(self) -> None:
        sensor_rows, lookup = build_sensor_reference_rows(
            frozen_case_label="Salt 2 Kirst",
            source_id="salt2",
            boundary_rows=[
                {
                    "landmark_label": "TP4",
                    "t_core_k": "450.0",
                    "t_wall_area_avg_k": "460.0",
                    "bulk_temp_fluid_area_avg_k": "455.0",
                },
                {
                    "landmark_label": "TP4",
                    "t_core_k": "452.0",
                    "t_wall_area_avg_k": "462.0",
                    "bulk_temp_fluid_area_avg_k": "457.0",
                },
                {
                    "landmark_label": "TW7",
                    "t_core_k": "449.0",
                    "t_wall_area_avg_k": "470.0",
                    "bulk_temp_fluid_area_avg_k": "456.0",
                },
                {
                    "landmark_label": "TW7",
                    "t_core_k": "451.0",
                    "t_wall_area_avg_k": "472.0",
                    "bulk_temp_fluid_area_avg_k": "458.0",
                },
            ],
        )
        self.assertEqual(len(sensor_rows), 2)
        self.assertAlmostEqual(lookup["TP4"]["reference_k"], 451.0)
        self.assertEqual(lookup["TP4"]["reference_source_field"], "t_core_k")
        self.assertAlmostEqual(lookup["TW7"]["reference_k"], 471.0)
        self.assertEqual(lookup["TW7"]["reference_source_field"], "t_wall_area_avg_k")


if __name__ == "__main__":
    unittest.main()
