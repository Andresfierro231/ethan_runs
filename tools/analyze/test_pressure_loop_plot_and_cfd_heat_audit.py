import unittest

from tools.analyze.build_pressure_loop_plot_and_cfd_heat_audit import (
    PATCH_ROLE_HEAT,
    PRESSURE_CASE_REVIEW,
    PRESSURE_STATION,
    VAL_SALT2_HEAT,
    build_heat_coverage_table,
    build_mainline_heat_audit,
    build_trend_rows,
    build_val_salt2_heat_audit,
    group_pressure_rows,
    read_csv,
)


class PressureLoopPlotAndCfdHeatAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pressure_rows = read_csv(PRESSURE_STATION)
        cls.grouped = group_pressure_rows(cls.pressure_rows)
        cls.heat_rows = build_mainline_heat_audit(read_csv(PATCH_ROLE_HEAT)) + build_val_salt2_heat_audit(
            read_csv(VAL_SALT2_HEAT)
        )
        cls.coverage = build_heat_coverage_table(read_csv(PRESSURE_CASE_REVIEW), cls.heat_rows)

    def test_pressure_plot_source_has_expected_cases_and_rows(self):
        self.assertEqual(len(self.grouped), 11)
        self.assertEqual(len(self.pressure_rows), 330)
        self.assertEqual(len(self.grouped["salt2_mainline"]), 30)

    def test_heat_audit_has_mainline_and_val_salt2_rows(self):
        keys = {row["case_key"] for row in self.heat_rows}
        self.assertEqual(keys, {"salt2_mainline", "salt3_mainline", "salt4_mainline", "val_salt2"})

    def test_mainline_junction_loss_increases_with_power(self):
        mainline = [row for row in self.heat_rows if row["case_key"] in {"salt2_mainline", "salt3_mainline", "salt4_mainline"}]
        mainline.sort(key=lambda row: row["case_key"])
        losses = [float(row["junction_loss_positive_W"]) for row in mainline]
        self.assertLess(losses[0], losses[1])
        self.assertLess(losses[1], losses[2])

    def test_missing_heat_audit_coverage_is_explicit(self):
        missing = [row["case_key"] for row in self.coverage if row["heat_audit_available"] == "no"]
        self.assertIn("salt1_nominal", missing)
        self.assertIn("salt2_hi5q", missing)
        self.assertEqual(len(missing), 7)

    def test_trend_rows_are_generated(self):
        trends = build_trend_rows(self.heat_rows)
        self.assertEqual(len(trends), 3)
        self.assertTrue(any(row["trend"] == "junction_fraction_of_heater" for row in trends))


if __name__ == "__main__":
    unittest.main()
