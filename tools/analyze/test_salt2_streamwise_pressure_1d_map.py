import unittest

from tools.analyze.build_salt2_streamwise_pressure_1d_map import (
    BRANCH_METADATA,
    build_branch_averages,
    build_station_map,
    load_salt2_station_rows,
)


class Salt2StreamwisePressure1DMapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source_rows = load_salt2_station_rows()
        cls.station_rows = build_station_map(cls.source_rows)
        cls.branch_rows = build_branch_averages(cls.station_rows)

    def test_all_salt2_station_rows_present(self):
        self.assertEqual(len(self.source_rows), 30)
        self.assertEqual(len(self.station_rows), 30)
        self.assertEqual(len(self.branch_rows), 6)

    def test_lower_leg_is_heater_and_reversed_to_flow_order(self):
        self.assertEqual(self.station_rows[0]["station_label"], "lower_leg__s04")
        self.assertEqual(self.station_rows[0]["cfd_span"], "lower_leg")
        self.assertEqual(self.station_rows[0]["physical_location_label"], "heater / bottom heated incline")
        self.assertEqual(self.station_rows[0]["one_d_parent_segment"], "heated_incline")
        lower = next(row for row in self.branch_rows if row["cfd_span"] == "lower_leg")
        self.assertEqual(lower["flow_start_station_label"], "lower_leg__s04")
        self.assertEqual(lower["flow_end_station_label"], "lower_leg__s00")

    def test_right_leg_is_downcomer_not_heater(self):
        right = next(row for row in self.branch_rows if row["cfd_span"] == "right_leg")
        self.assertEqual(right["physical_location_label"], "right downcomer / cold vertical return")
        self.assertEqual(right["one_d_parent_segment"], "right_vertical")
        self.assertEqual(right["flow_start_station_label"], "right_leg__s00")
        self.assertEqual(right["flow_end_station_label"], "right_leg__s04")

    def test_upper_leg_maps_to_cooled_fluid_composite(self):
        upper = next(row for row in self.branch_rows if row["cfd_span"] == "upper_leg")
        self.assertEqual(upper["one_d_parent_segment"], "cooled_incline_composite")
        self.assertIn("cooled_incline_hx_active", upper["one_d_component_segments"])
        self.assertEqual(BRANCH_METADATA["upper_leg"]["one_d_role"], "cooler_hx_path")

    def test_pressure_values_follow_source(self):
        first = self.station_rows[0]
        self.assertAlmostEqual(float(first["mean_p_Pa"]), -450.9593084)
        self.assertAlmostEqual(float(first["mean_p_rgh_Pa"]), -0.6814987012)
        salt2_lower_s00 = next(row for row in self.station_rows if row["station_label"] == "lower_leg__s00")
        self.assertAlmostEqual(float(salt2_lower_s00["mean_p_Pa"]), -7536.547239)


if __name__ == "__main__":
    unittest.main()
