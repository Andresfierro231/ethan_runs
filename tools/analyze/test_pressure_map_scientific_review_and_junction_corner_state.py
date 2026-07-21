import unittest

from tools.analyze.build_pressure_map_scientific_review_and_junction_corner_state import (
    aggregate_corner_summary,
    build_corner_review,
    build_junction_heat_review,
    build_pressure_branch_review,
    build_pressure_case_review,
    read_csv,
    PRESSURE_ADMISSION,
    PRESSURE_BRANCH,
    PRESSURE_STATION,
    CASE_PROVENANCE,
    HEAT_ROLE,
    HEAT_SEGMENT,
    MINOR_LOSS,
    MINOR_LOSS_SEPARATION,
)


class PressureMapScientificReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.branch_review = build_pressure_branch_review(read_csv(PRESSURE_BRANCH), read_csv(PRESSURE_ADMISSION))
        cls.case_review = build_pressure_case_review(
            cls.branch_review,
            read_csv(PRESSURE_STATION),
            read_csv(CASE_PROVENANCE),
        )
        cls.junction_review = build_junction_heat_review(read_csv(HEAT_ROLE), read_csv(HEAT_SEGMENT))
        cls.corner_review = build_corner_review(read_csv(MINOR_LOSS), read_csv(MINOR_LOSS_SEPARATION))
        cls.corner_summary = aggregate_corner_summary(cls.corner_review)

    def test_pressure_reviews_cover_all_cases_and_branches(self):
        self.assertEqual(len(self.case_review), 11)
        self.assertEqual(len(self.branch_review), 66)

    def test_no_pressure_branch_is_fit_admitted(self):
        self.assertEqual(sum(row["true_f_D_or_K_fit_admitted"] == "yes" for row in self.branch_review), 0)
        self.assertEqual(
            sum(row["recirculation_mask_status"] == "blocked_material_recirculation_mask" for row in self.branch_review),
            66,
        )

    def test_labeling_guardrail_survives_review(self):
        lower = next(row for row in self.branch_review if row["case_key"] == "salt2_mainline" and row["cfd_span"] == "lower_leg")
        right = next(row for row in self.branch_review if row["case_key"] == "salt2_mainline" and row["cfd_span"] == "right_leg")
        self.assertEqual(lower["one_d_component_segments"], "heated_incline")
        self.assertEqual(right["one_d_component_segments"], "right_vertical")

    def test_junction_heat_loss_has_diagnostic_rows(self):
        junction_rows = [row for row in self.junction_review if row["role_or_lane"] == "junction_other"]
        self.assertEqual(len(junction_rows), 3)
        self.assertTrue(all(row["heat_direction"] == "from_fluid" for row in junction_rows))

    def test_corner_k_rows_are_diagnostic_upper_bounds(self):
        self.assertEqual(len(self.corner_review), 12)
        self.assertEqual(len(self.corner_summary), 4)
        self.assertTrue(all(row["scientific_status"] == "diagnostic_upper_bound_not_fit_admitted" for row in self.corner_summary))


if __name__ == "__main__":
    unittest.main()
