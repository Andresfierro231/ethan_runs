from __future__ import annotations

import unittest

from tools.analyze.build_ethan_salt_model_dependency_package_v4 import choose_feature_status


class ClosureModelingV4Tests(unittest.TestCase):
    def test_feature_status_requires_multiple_stable_feature_families(self) -> None:
        rows = [
            {"source_id": "case_a", "category_name": "corner_upper_right"},
            {"source_id": "case_b", "category_name": "corner_upper_right"},
            {"source_id": "case_c", "category_name": "corner_upper_right"},
            {"source_id": "case_d", "category_name": "corner_upper_right"},
        ]
        status, model, reason = choose_feature_status(
            rows,
            {
                "status": "fit",
                "model_type": "feature_name_aware_re_power_law",
                "bootstrap_ci95": {"log_re": [0.2, 0.6]},
            },
        )
        self.assertEqual(status, "not_defensible_yet")
        self.assertEqual(model, "exploratory_screened_only_model")
        self.assertEqual(reason, "single_feature_family_only")

    def test_feature_status_promotes_stable_multi_feature_fit(self) -> None:
        rows = [
            {"source_id": "case_a", "category_name": "corner_upper_right"},
            {"source_id": "case_b", "category_name": "corner_upper_right"},
            {"source_id": "case_c", "category_name": "test_section_complex"},
            {"source_id": "case_d", "category_name": "test_section_complex"},
        ]
        status, model, reason = choose_feature_status(
            rows,
            {
                "status": "fit",
                "model_type": "feature_name_aware_re_power_law",
                "bootstrap_ci95": {"log_re": [0.2, 0.6]},
            },
        )
        self.assertEqual(status, "provisional_defended")
        self.assertEqual(model, "feature_name_aware_re_power_law")
        self.assertEqual(reason, "stable_patch_endpoint_prgh_local_boundary_reference")


if __name__ == "__main__":
    unittest.main()
