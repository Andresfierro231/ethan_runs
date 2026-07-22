import tempfile
import unittest
from pathlib import Path

from tools.analyze import build_wall_thermal_circuit_model as wall


class WallThermalCircuitTests(unittest.TestCase):
    def test_component_rows_cover_test_section_and_junction(self):
        rows = wall.component_rows()
        self.assertIn("test_section_quartz_span", {row["segment_id"] for row in rows})
        self.assertIn("junction_stub_connector", {row["segment_id"] for row in rows})
        self.assertTrue(all(row["runtime_allowed_now"] == "false" for row in rows))

    def test_passive_operator_context_is_not_released(self):
        rows = wall.passive_operator_rows()
        self.assertEqual(len(rows), 3)
        self.assertEqual({row["runtime_use"] for row in rows}, {"diagnostic_context_only_until_same_QOI_and_source_release"})

    def test_package_builds_no_final_score(self):
        old_out = wall.OUT
        with tempfile.TemporaryDirectory() as tmp:
            wall.OUT = Path(tmp)
            try:
                summary = wall.build_package()
                self.assertEqual(summary["final_score_rows"], 0)
                self.assertEqual(summary["numeric_q_loss_release_rows"], 0)
                self.assertGreater(summary["blocked_release_rows"], 0)
            finally:
                wall.OUT = old_out


if __name__ == "__main__":
    unittest.main()
