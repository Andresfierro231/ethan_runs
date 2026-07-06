from __future__ import annotations

import unittest

from tools.analyze.build_ethan_feature_path_hydro_probe import (
    build_boundary_candidate_lookup,
    classify_case_summary,
    classify_time_row,
    pick_nearest_stations,
)


class FeaturePathHydroProbeTests(unittest.TestCase):
    def test_boundary_lookup_maps_summary_patch_to_geometry_endpoint_labels(self) -> None:
        geometry_rows = [
            {
                "span_name": "upper_leg",
                "s_span_m": "0.0",
                "segment_start_label": "TP6",
                "segment_end_label": "TW11",
            },
            {
                "span_name": "upper_leg",
                "s_span_m": "1.0",
                "segment_start_label": "TW9",
                "segment_end_label": "TP1",
            },
        ]
        summary_rows = [
            {
                "span_name": "upper_leg",
                "start_patch": "ncc_pipeleg_upper_09_straight_end",
                "end_patch": "ncc_pipeleg_upper_01_straight_start",
            }
        ]
        lookup = build_boundary_candidate_lookup(geometry_rows, summary_rows)
        start_candidate = lookup["ncc_pipeleg_upper_09_straight_end"][0]
        end_candidate = lookup["ncc_pipeleg_upper_01_straight_start"][0]
        self.assertEqual(start_candidate.boundary_role, "start")
        self.assertEqual(start_candidate.boundary_labels, ("TP6",))
        self.assertEqual(end_candidate.boundary_role, "end")
        self.assertEqual(end_candidate.boundary_labels, ("TP1",))

    def test_pick_nearest_stations_prefers_closest_unique_s_values(self) -> None:
        picked = pick_nearest_stations([0.0, 0.05, 0.10, 0.15, 0.15], boundary_s_m=0.12, station_count=3)
        self.assertEqual(picked, [0.1, 0.15, 0.05])

    def test_time_row_is_partial_when_station_support_is_incomplete(self) -> None:
        status, reason = classify_time_row(
            {
                "start_window_support_fraction": 1.0,
                "end_window_support_fraction": 2.0 / 3.0,
                "start_window_p_wall_area_avg_pa": 5.0,
                "start_window_p_rgh_wall_area_avg_pa": 1.0,
                "end_window_p_wall_area_avg_pa": 2.0,
                "end_window_p_rgh_wall_area_avg_pa": 0.5,
            }
        )
        self.assertEqual(status, "partial")
        self.assertEqual(reason, "incomplete_window_station_support")

    def test_case_summary_only_becomes_ready_when_all_times_are_ready(self) -> None:
        ready_status, ready_reason = classify_case_summary(
            {
                "probe_ready_fraction": 1.0,
                "probe_any_coverage_fraction": 1.0,
            }
        )
        self.assertEqual(ready_status, "probe_ready_for_downstream_review")
        self.assertEqual(ready_reason, "all_retained_times_have_full_endpoint_window_support")

        partial_status, partial_reason = classify_case_summary(
            {
                "probe_ready_fraction": 0.5,
                "probe_any_coverage_fraction": 1.0,
            }
        )
        self.assertEqual(partial_status, "partial_probe_only")
        self.assertEqual(partial_reason, "some_retained_times_have_endpoint_window_support_but_not_all")


if __name__ == "__main__":
    unittest.main()
