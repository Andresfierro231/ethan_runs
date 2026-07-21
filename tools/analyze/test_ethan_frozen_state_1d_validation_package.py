from __future__ import annotations

import unittest

from tools.analyze.build_ethan_frozen_state_1d_validation_package import (
    build_scenario_bundle_alignment_rows,
    build_sensor_reference_rows,
    bundle_alignment_status,
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

    def test_bundle_alignment_helpers(self) -> None:
        self.assertEqual(
            bundle_alignment_status(
                scenario_family_value="baseline",
                profile_descriptor_mode="disabled",
                internal_htc_mode="baseline",
            )[0],
            "full_bundle_alignment",
        )
        rows = build_scenario_bundle_alignment_rows(
            scenario_rows=[
                {
                    "scenario": "baseline_case",
                    "scenario_family": "baseline",
                    "closure_stack_label": "disabled|baseline|ins=1.0|rad=True",
                    "profile_descriptor_mode": "disabled",
                    "internal_htc_mode": "baseline",
                    "all_rows_accepted_for_validation": True,
                    "composite_rank": 1,
                },
                {
                    "scenario": "hybrid_case",
                    "scenario_family": "hybrid",
                    "closure_stack_label": "ethan_cfd_informed_salt_v1|per_parent_multiplier|ins=1.0|rad=True",
                    "profile_descriptor_mode": "ethan_cfd_informed_salt_v1",
                    "internal_htc_mode": "per_parent_multiplier",
                    "all_rows_accepted_for_validation": True,
                    "composite_rank": 2,
                },
            ],
            bundle_payload={
                "distributed_friction": {"closure_name": "f", "target_regions": ["lower_leg", "test_section_span"]},
                "primary_ua_surface": {"closure_name": "ua", "target_regions": ["left_lower_leg"]},
                "direct_nusselt": {"closure_name": "nu", "target_regions": ["left_lower_leg"]},
                "blocked_terms": {"a": {}, "b": {}},
            },
        )
        self.assertEqual(rows[0]["bundle_alignment_status"], "full_bundle_alignment")
        self.assertEqual(rows[1]["bundle_alignment_status"], "hybrid_bundle_extension_undercovered")


if __name__ == "__main__":
    unittest.main()
