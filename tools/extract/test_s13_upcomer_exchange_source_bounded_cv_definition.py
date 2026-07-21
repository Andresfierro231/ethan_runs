from __future__ import annotations

import unittest

from tools.extract import build_s13_upcomer_exchange_source_bounded_cv_definition as builder


class S13SourceBoundedCvDefinitionTests(unittest.TestCase):
    def test_boundary_class_accepts_only_trusted_right_leg_wall(self) -> None:
        classification, trusted, role, reason = builder.boundary_class("pipeleg_right_02_middle")
        self.assertEqual(classification, "trusted_right_leg_wall")
        self.assertTrue(trusted)
        self.assertEqual(role, "wall_heat_boundary")
        self.assertEqual(reason, "")

        classification, trusted, role, reason = builder.boundary_class("outlet")
        self.assertEqual(classification, "untrusted_boundary_escape")
        self.assertFalse(trusted)
        self.assertEqual(role, "unreleased_source_or_sink_boundary")
        self.assertIn("unreleased_boundary", reason)

    def test_outward_normal_flips_when_selected_cell_is_neighbour(self) -> None:
        normal = builder.outward_normal((2.0, 0.0, 0.0), owner_selected=True, neighbour_selected=False)
        self.assertEqual(normal, (1.0, 0.0, 0.0))

        normal = builder.outward_normal((2.0, 0.0, 0.0), owner_selected=False, neighbour_selected=True)
        self.assertEqual(normal, (-1.0, -0.0, -0.0))

    def test_decision_requires_interface_wall_and_no_boundary_escape(self) -> None:
        accum = builder.CaseAccum(interface_faces=[{"face_id": 1}], wall_faces=[], boundary_by_patch={})
        accum.interface_area_m2 = 1.0
        row = builder.decision_for_case("salt_2", {1, 2}, accum)
        self.assertEqual(row["release_status"], "blocked_source_bounded_cv_not_released")
        self.assertIn("missing_positive_trusted_right_leg_wall", row["blocking_reason"])

        accum.wall_faces.append({"face_id": 2})
        accum.wall_area_m2 = 0.5
        accum.untrusted_boundary_faces = 3
        row = builder.decision_for_case("salt_2", {1, 2}, accum)
        self.assertIn("selected_cv_touches_non_wall_or_unreleased_boundary_faces", row["blocking_reason"])

        accum.untrusted_boundary_faces = 0
        accum.untrusted_boundary_area_m2 = 0.0
        row = builder.decision_for_case("salt_2", {1, 2}, accum)
        self.assertEqual(row["release_status"], "released_source_bounded_cv")
        self.assertEqual(row["blocking_reason"], "")

    def test_next_rows_block_sampler_when_group_not_released(self) -> None:
        rows = builder.next_rows(group_released=False)
        self.assertIn("Do not rerun sampler", rows[0]["next_step"])
        self.assertIn("no surface extraction", rows[0]["guardrail"])


if __name__ == "__main__":
    unittest.main()
