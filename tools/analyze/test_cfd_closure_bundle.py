from __future__ import annotations

import json
import math
import tempfile
import unittest
from pathlib import Path

from tools.analyze.cfd_closure_bundle import (
    BLOCKED_REQUIREMENTS,
    BRANCH_DEVELOPMENT_SUMMARY,
    CLOSURE_TERM_RECOMMENDATIONS,
    STALE_AND_DATA_NEEDS,
    build_bundle,
    evaluate_left_lower_leg_nusselt,
    evaluate_straight_friction_factor,
    load_csv_rows,
    load_power_law_closure,
    parse_coefficients,
    parse_re_domain,
)


class ClosureBundleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.closure_rows = load_csv_rows(CLOSURE_TERM_RECOMMENDATIONS)
        self.friction = load_power_law_closure(self.closure_rows, "straight_friction_class_aware_re_power_law")
        self.nu = load_power_law_closure(self.closure_rows, "left_lower_leg_nu_branch_aware_re_power_law")

    def test_parse_coefficients(self) -> None:
        self.assertEqual(
            parse_coefficients("a=1.0|b=-2.5|c=3"),
            {"a": 1.0, "b": -2.5, "c": 3.0},
        )

    def test_parse_re_domain(self) -> None:
        self.assertEqual(parse_re_domain("Approximate defended fit domain 80.35 <= Re <= 173.74"), (80.35, 173.74))

    def test_friction_evaluation_differs_by_region(self) -> None:
        lower = evaluate_straight_friction_factor(100.0, "lower_leg", self.friction)
        test_section = evaluate_straight_friction_factor(100.0, "test_section_span", self.friction)
        self.assertTrue(lower["within_defended_re_domain"])
        self.assertGreater(test_section["darcy_friction_factor"], lower["darcy_friction_factor"])

    def test_nusselt_evaluation_matches_expected_scale(self) -> None:
        evaluation = evaluate_left_lower_leg_nusselt(100.0, self.nu)
        self.assertTrue(evaluation["within_defended_re_domain"])
        self.assertTrue(math.isclose(evaluation["nusselt_number"], 4.137957536818851, rel_tol=1e-12))

    def test_bundle_build_outputs_expected_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "bundle"
            manifest_path = Path(tmpdir) / "bundle_manifest.json"
            summary = build_bundle(output_dir, manifest_path)
            self.assertEqual(summary["straight_friction_status"], "provisional_defended")
            self.assertEqual(summary["direct_nu_status"], "provisional_defended_limited_domain")
            self.assertTrue((output_dir / "salt_closure_bundle.json").exists())
            self.assertTrue((output_dir / "branch_state_surface_policy.csv").exists())
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(manifest["task_id"], "AGENT-138")

    def test_source_tables_exist(self) -> None:
        for path in (CLOSURE_TERM_RECOMMENDATIONS, BRANCH_DEVELOPMENT_SUMMARY, STALE_AND_DATA_NEEDS, BLOCKED_REQUIREMENTS):
            self.assertTrue(path.exists(), str(path))


if __name__ == "__main__":
    unittest.main()
