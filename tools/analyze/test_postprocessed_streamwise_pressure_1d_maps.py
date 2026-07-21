import unittest

from tools.analyze.build_postprocessed_streamwise_pressure_1d_maps import (
    BRANCH_ORDER,
    build_branch_averages,
    build_case_provenance,
    build_station_map_for_case,
    load_harvest_rows,
)


class PostprocessedStreamwisePressure1DMapsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source_rows = load_harvest_rows()
        cls.by_case = {}
        for row in cls.source_rows:
            cls.by_case.setdefault(row["case_key"], []).append(row)
        cls.station_rows = []
        for case_key in sorted(cls.by_case):
            cls.station_rows.extend(build_station_map_for_case(case_key, cls.by_case[case_key]))
        cls.branch_rows = build_branch_averages(cls.station_rows)
        cls.provenance = build_case_provenance(cls.source_rows, cls.station_rows)

    def test_all_available_harvested_cases_are_mapped(self):
        self.assertEqual(len(self.by_case), 11)
        self.assertEqual(len(self.source_rows), 330)
        self.assertEqual(len(self.station_rows), 330)
        self.assertEqual(len(self.branch_rows), 66)
        self.assertEqual(len(self.provenance), 11)

    def test_each_case_has_30_station_rows_and_6_branch_rows(self):
        for case_key, rows in self.by_case.items():
            self.assertEqual(len(rows), 30, case_key)
            mapped = [row for row in self.station_rows if row["case_key"] == case_key]
            branches = [row for row in self.branch_rows if row["case_key"] == case_key]
            self.assertEqual(len(mapped), 30, case_key)
            self.assertEqual(len(branches), len(BRANCH_ORDER), case_key)

    def test_lower_leg_and_right_leg_mapping_guardrails_hold_for_all_cases(self):
        for case_key in self.by_case:
            mapped = [row for row in self.station_rows if row["case_key"] == case_key]
            self.assertEqual(mapped[0]["station_label"], "lower_leg__s04", case_key)
            self.assertEqual(mapped[0]["one_d_parent_segment"], "heated_incline", case_key)
            right = next(row for row in self.branch_rows if row["case_key"] == case_key and row["cfd_span"] == "right_leg")
            self.assertEqual(right["physical_location_label"], "right downcomer / cold vertical return", case_key)
            self.assertEqual(right["one_d_parent_segment"], "right_vertical", case_key)
            self.assertEqual(right["flow_start_station_label"], "right_leg__s00", case_key)
            self.assertEqual(right["flow_end_station_label"], "right_leg__s04", case_key)

    def test_upper_leg_maps_to_hx_composite_for_all_cases(self):
        for case_key in self.by_case:
            upper = next(row for row in self.branch_rows if row["case_key"] == case_key and row["cfd_span"] == "upper_leg")
            self.assertEqual(upper["one_d_parent_segment"], "cooled_incline_composite", case_key)
            self.assertIn("cooled_incline_hx_active", upper["one_d_component_segments"], case_key)

    def test_provenance_keeps_harvest_job_and_native_case_path(self):
        jobs = {row["harvest_job_id"] for row in self.provenance}
        self.assertEqual(jobs, {"3297860", "3297863"})
        val = next(row for row in self.provenance if row["case_key"] == "val_salt2")
        self.assertEqual(val["split_role"], "external_validation")
        self.assertIn("val_salt_test_2_coarse_mesh_laminar_continuation", val["native_case_path"])
        salt2 = next(row for row in self.provenance if row["case_key"] == "salt2_mainline")
        self.assertEqual(salt2["harvest_job_id"], "3297860")


if __name__ == "__main__":
    unittest.main()
