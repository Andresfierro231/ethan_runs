from __future__ import annotations

import unittest
from pathlib import Path

from tools.analyze.build_ethan_paper_case_inventory import (
    PAPER_CLASS_RULES,
    build_claim_rows,
    build_summary_rows,
    paper_class_for_source_id,
    retained_window_status,
)


class EthanPaperCaseInventoryTests(unittest.TestCase):
    def test_paper_class_rules_cover_expected_salt2_kirst_role(self) -> None:
        paper_class, reason = paper_class_for_source_id("viscosity_screening_salt_test_2_kirst_coarse_mesh")
        self.assertEqual(paper_class, "exploratory")
        self.assertIn("Representative Salt 2 mechanism", reason)

    def test_retained_window_status_marks_short_checkpoint_family(self) -> None:
        status, note = retained_window_status(
            "viscosity_screening_salt_test_1_jin_coarse_mesh",
            {"representative_time_count": "18"},
        )
        self.assertEqual(status, "checkpoint_short_window_18")
        self.assertIn("shorter than the nominal 20-step target", note)

    def test_retained_window_status_marks_non_checkpoint_case(self) -> None:
        status, note = retained_window_status("viscosity_screening_salt_test_2_kirst_coarse_mesh", None)
        self.assertEqual(status, "not_in_nominal_checkpoint_family")
        self.assertIn("outside the nominal June 23 latest-window", note)

    def test_build_claim_rows_uses_one_d_contract_only_when_requested(self) -> None:
        inventory_rows = [
            {
                "source_id": "viscosity_screening_salt_test_1_jin_coarse_mesh",
                "paper_class": PAPER_CLASS_RULES["viscosity_screening_salt_test_1_jin_coarse_mesh"][0],
            },
            {
                "source_id": "viscosity_screening_salt_test_2_kirst_coarse_mesh",
                "paper_class": PAPER_CLASS_RULES["viscosity_screening_salt_test_2_kirst_coarse_mesh"][0],
            },
            {
                "source_id": "val_salt_test_2_coarse_mesh_laminar",
                "paper_class": PAPER_CLASS_RULES["val_salt_test_2_coarse_mesh_laminar"][0],
            },
            {
                "source_id": "viscosity_screening_salt_test_4_jin_coarse_mesh",
                "paper_class": PAPER_CLASS_RULES["viscosity_screening_salt_test_4_jin_coarse_mesh"][0],
            },
            {
                "source_id": "viscosity_screening_salt_test_4_kirst_coarse_mesh",
                "paper_class": PAPER_CLASS_RULES["viscosity_screening_salt_test_4_kirst_coarse_mesh"][0],
            },
        ]
        claim_rows = build_claim_rows(
            inventory_rows=inventory_rows,
            alignment_row={
                "straight_friction_closure_name": "straight_demo",
                "straight_friction_target_regions": "lower_leg|test_section_span",
                "primary_ua_closure_name": "ua_demo",
                "primary_ua_target_regions": "left_lower_leg|upcomer",
                "direct_nu_closure_name": "nu_demo",
                "direct_nu_target_regions": "left_lower_leg",
            },
            queue_path=Path("queue.md"),
            paper_safe_asset_map=Path("asset_map.csv"),
            promotion_candidate_index=Path("promotion.csv"),
            validation_dir=Path("validation"),
            bakeoff_dir=Path("bakeoff"),
            presentation_figure_manifest=Path("figures.csv"),
        )
        one_d_claim = next(row for row in claim_rows if row["claim_id"] == "latest_window_nominal_salt_jin")
        support_claim = next(row for row in claim_rows if row["claim_id"] == "representative_salt2_mechanism")
        self.assertEqual(one_d_claim["one_d_straight_friction_input"], "straight_demo:lower_leg|test_section_span")
        self.assertEqual(support_claim["one_d_straight_friction_input"], "n/a")

    def test_build_summary_rows_counts_each_class(self) -> None:
        rows = build_summary_rows(
            [
                {"paper_class": "paper-grade"},
                {"paper_class": "paper-grade"},
                {"paper_class": "blocked"},
            ]
        )
        self.assertEqual(rows, [{"paper_class": "blocked", "case_count": 1}, {"paper_class": "paper-grade", "case_count": 2}])


if __name__ == "__main__":
    unittest.main()
