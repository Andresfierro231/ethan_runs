from __future__ import annotations

import unittest

from tools.analyze.build_ethan_feature_path_hydro_decomposition import classify_case_row


class EthanFeaturePathHydroDecompositionTests(unittest.TestCase):
    def test_fit_used_case_requires_full_support_and_positive_feature_excess(self) -> None:
        status, reason, reasons = classify_case_row(
            {
                "defended_time_fraction": 1.0,
                "support_fraction_min": 1.0,
                "positive_time_fraction": 1.0,
                "mean_feature_excess_path_pa": 2.0,
                "mean_dynamic_head_local_pa": 1.5,
                "mean_re_effective": 100.0,
            }
        )
        self.assertEqual(status, "fit_used")
        self.assertEqual(reason, "closure_supported")
        self.assertEqual(reasons, [])

    def test_case_blocks_when_patch_support_is_incomplete(self) -> None:
        status, reason, reasons = classify_case_row(
            {
                "defended_time_fraction": 0.8,
                "support_fraction_min": 1.0,
                "positive_time_fraction": 1.0,
                "mean_feature_excess_path_pa": 2.0,
                "mean_dynamic_head_local_pa": 1.5,
                "mean_re_effective": 100.0,
            }
        )
        self.assertEqual(status, "excluded")
        self.assertEqual(reason, "missing_patch_endpoint_pair_or_reference")
        self.assertIn("missing_patch_endpoint_pair_or_reference", reasons)

    def test_case_blocks_when_feature_excess_is_nonpositive(self) -> None:
        status, reason, reasons = classify_case_row(
            {
                "defended_time_fraction": 1.0,
                "support_fraction_min": 1.0,
                "positive_time_fraction": 0.4,
                "mean_feature_excess_path_pa": -0.2,
                "mean_dynamic_head_local_pa": 1.5,
                "mean_re_effective": 100.0,
            }
        )
        self.assertEqual(status, "excluded")
        self.assertEqual(reason, "nonpositive_path_feature_excess_loss")
        self.assertIn("nonpositive_path_feature_excess_loss", reasons)


if __name__ == "__main__":
    unittest.main()
