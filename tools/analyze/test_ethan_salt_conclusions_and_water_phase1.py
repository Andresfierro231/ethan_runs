from __future__ import annotations

import unittest

from tools.analyze.build_ethan_salt_conclusions_package import scientific_use_label, sensitivity_class
from tools.analyze.build_ethan_water_phase1_starter_package import classify_thermal_phase1


class SaltConclusionsAndWaterPhase1Tests(unittest.TestCase):
    def test_scientific_use_label_for_provisional_dependency(self) -> None:
        self.assertEqual(scientific_use_label("provisional_defended"), "usable_with_explicit_caveats")
        self.assertEqual(scientific_use_label("not_defensible_yet"), "do_not_use_for_final_modeling")

    def test_sensitivity_classification(self) -> None:
        self.assertEqual(
            sensitivity_class({"status": "run", "qualitative_conclusion_changed": "no"}),
            "robust",
        )
        self.assertEqual(
            sensitivity_class({"status": "run", "qualitative_conclusion_changed": "yes"}),
            "fragile",
        )
        self.assertEqual(
            sensitivity_class({"status": "not_run", "qualitative_conclusion_changed": "unknown"}),
            "not_run",
        )

    def test_water_thermal_phase1_blocks_hydraulic_exclusion(self) -> None:
        classification, reason = classify_thermal_phase1(
            "left_lower_leg",
            "excluded",
            0.99,
            0.25,
            0.10,
            1.0,
        )
        self.assertEqual(classification, "blocked_hydraulic_exclusion")
        self.assertIn("hydraulic branch", reason)

    def test_water_thermal_phase1_priority_when_support_is_strong_but_sign_is_bad(self) -> None:
        classification, _ = classify_thermal_phase1(
            "test_section_span",
            "water_family_candidate",
            1.0,
            0.21,
            2.4,
            0.0,
        )
        self.assertEqual(classification, "closure_rebuild_priority")

    def test_water_thermal_phase1_candidate_when_support_and_closure_are_reasonable(self) -> None:
        classification, _ = classify_thermal_phase1(
            "left_upper_leg",
            "contextual_only",
            0.99,
            0.14,
            0.50,
            1.0,
        )
        self.assertEqual(classification, "closure_rebuild_candidate")


if __name__ == "__main__":
    unittest.main()
