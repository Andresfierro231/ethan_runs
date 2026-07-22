import csv
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools.analyze import build_1d_sensor_projection_operator_tp_tw_wall_bulk as builder


class SensorProjectionOperatorTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.out = Path(cls.tmp.name) / "projection_operator"
        cls.patch = mock.patch.object(builder, "OUT", cls.out)
        cls.patch.start()
        cls.summary = builder.build()

    @classmethod
    def tearDownClass(cls):
        cls.patch.stop()
        cls.tmp.cleanup()

    def read_rows(self, name):
        with (self.out / name).open(newline="", encoding="utf-8") as handle:
            return list(csv.DictReader(handle))

    def test_sensor_operator_counts(self):
        rows = self.read_rows("sensor_projection_operator_table.csv")
        self.assertEqual(len(rows), 17)
        operators = {row["projection_operator"] for row in rows}
        self.assertEqual(operators, {"bulk_fluid_projection", "wall_state_projection", "excluded_no_projection"})
        self.assertEqual(sum(row["projection_operator"] == "bulk_fluid_projection" for row in rows), 6)
        self.assertEqual(sum(row["projection_operator"] == "wall_state_projection" for row in rows), 10)
        self.assertEqual(sum(row["projection_operator"] == "excluded_no_projection" for row in rows), 1)

    def test_runtime_temperature_guardrail(self):
        rows = self.read_rows("sensor_projection_operator_table.csv")
        self.assertEqual({row["runtime_temperature_allowed"] for row in rows}, {"false"})
        gates = {row["gate"]: row for row in self.read_rows("runtime_legality_matrix.csv")}
        self.assertEqual(gates["observed_TP_TW_temperature_as_runtime_input"]["allowed"], "False")
        self.assertEqual(gates["bulk_to_TP_thermal_development_offset_release"]["allowed"], "False")

    def test_tw10_stays_excluded(self):
        rows = {row["sensor"]: row for row in self.read_rows("sensor_projection_operator_table.csv")}
        self.assertEqual(rows["TW10"]["projection_operator"], "excluded_no_projection")
        self.assertEqual(rows["TW10"]["acceptance_class"], "excluded")

    def test_summary_decision(self):
        with (self.out / "summary.json").open(encoding="utf-8") as handle:
            summary = json.load(handle)
        self.assertEqual(summary["decision"], "projection_operator_defined_diagnostic_only_no_runtime_temperature_release")
        self.assertEqual(summary["sensor_rows"], 17)
        self.assertFalse(summary["runtime_temperature_release"])
        self.assertFalse(summary["bulk_to_tp_correction_released"])
        self.assertTrue(summary["thermal_development_path_promising"])


if __name__ == "__main__":
    unittest.main()
