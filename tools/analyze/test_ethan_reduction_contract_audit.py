from __future__ import annotations

import unittest

from tools.analyze.build_ethan_reduction_contract_audit import (
    build_branch_map_rows,
    build_reduction_choice_rows,
    build_station_map_rows,
    select_paper_grade_inventory_rows,
)


class EthanReductionContractAuditTests(unittest.TestCase):
    def test_select_paper_grade_inventory_rows_uses_nominal_order(self) -> None:
        rows = [
            {"source_id": "viscosity_screening_salt_test_4_jin_coarse_mesh", "paper_class": "paper-grade"},
            {"source_id": "viscosity_screening_salt_test_2_jin_coarse_mesh", "paper_class": "paper-grade"},
            {"source_id": "viscosity_screening_salt_test_1_jin_coarse_mesh", "paper_class": "paper-grade"},
            {"source_id": "viscosity_screening_salt_test_3_jin_coarse_mesh", "paper_class": "paper-grade"},
            {"source_id": "viscosity_screening_salt_test_2_kirst_coarse_mesh", "paper_class": "exploratory"},
        ]
        ordered = select_paper_grade_inventory_rows(rows)
        self.assertEqual(
            [row["source_id"] for row in ordered],
            [
                "viscosity_screening_salt_test_1_jin_coarse_mesh",
                "viscosity_screening_salt_test_2_jin_coarse_mesh",
                "viscosity_screening_salt_test_3_jin_coarse_mesh",
                "viscosity_screening_salt_test_4_jin_coarse_mesh",
            ],
        )

    def test_build_station_map_rows_tracks_matching_cases(self) -> None:
        case_contexts = [
            {
                "source_id": "viscosity_screening_salt_test_1_jin_coarse_mesh",
                "station_rows": [
                    {
                        "span_name": "left_lower_leg",
                        "span_kind": "main_loop_leg",
                        "bin_index": "0",
                        "target_ds_m": "0.01",
                        "s_start_m": "0.0",
                        "s_end_m": "0.01",
                        "s_mid_m": "0.0",
                        "segment_start_label": "TP3",
                        "segment_end_label": "TW7",
                        "sample_index": "0",
                        "s_m": "0.0",
                    }
                ],
            },
            {
                "source_id": "viscosity_screening_salt_test_2_jin_coarse_mesh",
                "station_rows": [
                    {
                        "span_name": "left_lower_leg",
                        "span_kind": "main_loop_leg",
                        "bin_index": "0",
                        "target_ds_m": "0.01",
                        "s_start_m": "0.0",
                        "s_end_m": "0.01",
                        "s_mid_m": "0.0",
                        "segment_start_label": "TP3",
                        "segment_end_label": "TW7",
                        "sample_index": "0",
                        "s_m": "0.0",
                    }
                ],
            },
        ]
        rows = build_station_map_rows(case_contexts)
        self.assertEqual(rows[0]["matching_source_case_count"], 2)
        self.assertEqual(rows[0]["matching_source_ids"], "viscosity_screening_salt_test_1_jin_coarse_mesh|viscosity_screening_salt_test_2_jin_coarse_mesh")

    def test_build_branch_map_rows_merges_policy(self) -> None:
        case_contexts = [
            {
                "source_id": "viscosity_screening_salt_test_1_jin_coarse_mesh",
                "branch_rows": [
                    {
                        "branch_name": "left_lower_leg",
                        "branch_type": "span_section",
                        "component_spans": "left_lower_leg",
                        "component_span_count": "1",
                        "branch_total_length_m": "0.32",
                        "usable_row_count": "95",
                        "total_row_count": "100",
                        "mean_abs_bulk_minus_wall_temp_k": "5.0",
                    }
                ],
            },
            {
                "source_id": "viscosity_screening_salt_test_2_jin_coarse_mesh",
                "branch_rows": [
                    {
                        "branch_name": "left_lower_leg",
                        "branch_type": "span_section",
                        "component_spans": "left_lower_leg",
                        "component_span_count": "1",
                        "branch_total_length_m": "0.34",
                        "usable_row_count": "85",
                        "total_row_count": "100",
                        "mean_abs_bulk_minus_wall_temp_k": "7.0",
                    }
                ],
            },
        ]
        policy_rows = [
            {
                "branch_name": "left_lower_leg",
                "branch_role": "direct_defended",
                "primary_model_mode": "primary_ua_and_direct_nu",
                "direct_nu_allowed": "True",
                "direct_nu_status": "provisional_defended_limited_domain",
                "primary_ua_allowed": "True",
                "secondary_htc_allowed": "True",
                "dominant_fit_status": "fit_used",
                "domain_note": "demo_domain",
                "modeling_note": "demo_note",
            }
        ]
        rows = build_branch_map_rows(case_contexts, policy_rows)
        self.assertEqual(rows[0]["branch_role"], "direct_defended")
        self.assertAlmostEqual(rows[0]["mean_branch_total_length_m"], 0.33)
        self.assertAlmostEqual(rows[0]["mean_support_fraction"], 0.9)

    def test_build_reduction_choice_rows_emits_manifest_details(self) -> None:
        case_contexts = [
            {
                "source_id": "viscosity_screening_salt_test_1_jin_coarse_mesh",
                "case_label": "Salt 1 Jin",
                "requested_times": ["0", "1"],
                "analysis_manifest": {
                    "target_ds_m": 0.01,
                    "required_fields": ["T", "U"],
                    "pressure_fields": ["p_rgh"],
                    "wall_fields": ["wallShearStress"],
                    "sign_conventions": {"feature_pressure_delta": "end_minus_start"},
                    "flow_direction_hints": {
                        "status": "manual_profile_assumption_not_auto_validated",
                        "meaning": "demo",
                        "hints_by_span": {"left_lower_leg": 1.0},
                    },
                    "deferred_terms": ["deferred demo"],
                    "raw_extraction_provenance": {"kind": "demo"},
                },
                "package_summary": {
                    "streamwise_thermal": {
                        "thermal_bulk_method": "bulk method",
                        "thermal_support_flagged_bin_count": 5,
                    },
                    "branch_thermal": {"branch_order": ["left_lower_leg"], "derived_branch_names": ["upcomer"]},
                    "major_loss": {"loop_span_order": ["left_lower_leg"]},
                    "azimuthal_transport": {"matched_transport_row_count": 10},
                },
                "paths": {
                    "analysis_manifest": __import__("pathlib").Path("tmp/manifest.json"),
                    "summary": __import__("pathlib").Path("tmp/summary.json"),
                },
            }
        ]
        rows = build_reduction_choice_rows(case_contexts)
        keys = {(row["choice_group"], row["choice_key"]) for row in rows}
        self.assertIn(("sign_convention", "feature_pressure_delta"), keys)
        self.assertIn(("deferred_term", "deferred_term_1"), keys)
        self.assertIn(("flow_direction", "hints_by_span_json"), keys)


if __name__ == "__main__":
    unittest.main()
