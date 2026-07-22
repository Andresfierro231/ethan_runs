import csv
import json
import unittest

from tools.analyze import build_fluid_setup_known_heater_source_train_residual_decomp as builder


class HeaterSourceResidualDecompTests(unittest.TestCase):
    def test_response_class_thresholds(self) -> None:
        self.assertEqual(builder.response_class(-2.0), "improves")
        self.assertEqual(builder.response_class(2.0), "worsens")
        self.assertEqual(builder.response_class(0.0), "insensitive")

    def test_decision_table_blocks_downstream_triggers_after_build(self) -> None:
        summary = builder.build(timeout_seconds=builder.TIMEOUT_SECONDS)
        self.assertEqual(summary["validation_rows_consumed"], 0)
        self.assertFalse(summary["freeze_or_admission_decision"])
        with (builder.PACKAGE / "decision_table.csv").open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["s11_trigger"], "False")
        with (builder.PACKAGE / "runtime_leakage_audit.csv").open(newline="", encoding="utf-8") as handle:
            runtime = list(csv.DictReader(handle))
        self.assertEqual({row["runtime_used"] for row in runtime}, {"False"})
        parsed = json.loads((builder.PACKAGE / "summary.json").read_text())
        self.assertIn(parsed["decision"], {
            "source_lane_improves_and_candidate_ready_for_source_property_review",
            "source_lane_partial_improvement_model_form_still_needed",
            "source_lane_no_material_improvement_fail_closed",
        })


if __name__ == "__main__":
    unittest.main()
