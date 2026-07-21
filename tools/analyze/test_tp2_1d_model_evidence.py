import unittest

from tools.analyze.build_tp2_1d_model_evidence import (
    RESTORED_EXCLUDED,
    TP2,
    TP2_CANONICAL_SEGMENT,
    TP2_FLUID_PARENT_SEGMENT,
    TW10,
    aggregate_row,
    finite_tp2_gate,
    gate_rows,
    projected_registry_rows,
    sensor_policy_rows,
)


class Tp2OneDimensionalEvidenceTests(unittest.TestCase):
    def sample_sensor_rows(self):
        rows = []
        for case in ("salt_2", "salt_3"):
            for sensor, kind, pred, target, source in [
                ("TP1", "TP", 440.0, 441.0, "top_horizontal_exit"),
                (TP2, "TP", 445.0, 446.5, TP2_FLUID_PARENT_SEGMENT),
                ("TP3", "TP", 430.0, 431.0, "left_lower_vertical"),
                ("TW1", "TW", 450.0, 452.0, "right_vertical"),
                (TW10, "TW", "", 460.0, ""),
            ]:
                error = pred - target if isinstance(pred, float) else ""
                rows.append(
                    {
                        "case_id": case,
                        "mode_id": "M3_cfd_heater_cooler_pressure_root",
                        "part": "part3",
                        "sensor": sensor,
                        "kind": kind,
                        "predicted_K": pred,
                        "target_K": target,
                        "error_K": error,
                        "abs_error_K": abs(error) if isinstance(error, float) else "",
                        "prediction_source_segment": source,
                        "prediction_source_fraction": "0.0" if sensor == TP2 else "1.0",
                        "target_provenance": "synthetic",
                        "admission_use_class": "validation_candidate",
                        "assumption_ids": "A006;A007",
                        "notes": "synthetic row",
                    }
                )
        return rows

    def test_projected_registry_preserves_original_tp2_coordinate(self):
        rows = projected_registry_rows(
            [
                {
                    "sensor": TP2,
                    "kind": "TP",
                    "x_in": "36.8289343482927",
                    "y_in": "-12.3127251597241",
                    "x_m": "0.91",
                    "y_m": "-0.31274322",
                    "placement_class": "provisional_working_placement",
                    "source_basis": "user approximate registry note",
                    "authoritative_status": "not_exact_measurement",
                    "caveat": "Approximate initial placement only.",
                    "notes": "bottom right downcomer",
                }
            ]
        )
        tp2 = rows[0]
        self.assertEqual(tp2["original_x_in"], "36.8289343482927")
        self.assertEqual(tp2["original_y_in"], "-12.3127251597241")
        self.assertEqual(tp2["x_in"], "35.8289343482927")
        self.assertEqual(tp2["projection_parent_segment"], TP2_FLUID_PARENT_SEGMENT)
        self.assertEqual(tp2["canonical_source_segment"], TP2_CANONICAL_SEGMENT)

    def test_tp2_gate_passes_only_when_all_tp2_rows_are_finite(self):
        status, detail = finite_tp2_gate(self.sample_sensor_rows())
        self.assertEqual(status, "pass")
        self.assertIn("TP2 rows have finite", detail)

        broken = self.sample_sensor_rows()
        broken[1]["predicted_K"] = ""
        broken[1]["error_K"] = ""
        status, detail = finite_tp2_gate(broken)
        self.assertEqual(status, "fail")
        self.assertIn("lack finite", detail)

    def test_restored_aggregate_includes_tp2_and_excludes_tw10(self):
        row = aggregate_row(
            self.sample_sensor_rows(),
            label="restored_policy_includes_tp2_excludes_tw10",
            excluded=RESTORED_EXCLUDED,
            interpretation="synthetic",
        )
        self.assertEqual(row["tp_count"], 3)
        self.assertEqual(row["tw_count"], 1)
        self.assertIn(TP2, row["included_sensors"])
        self.assertNotIn(TW10, row["included_sensors"])

    def test_gate_rows_expose_source_runtime_and_tw10_statuses(self):
        gates = {row["gate"]: row for row in gate_rows(self.sample_sensor_rows())}
        self.assertEqual(gates["TP2_source_segment_named"]["status"], "pass")
        self.assertEqual(gates["TP2_runtime_input_forbidden"]["status"], "pass")
        self.assertEqual(gates["TP2_finite_prediction_before_aggregate"]["status"], "pass")
        self.assertEqual(gates["TW10_excluded_until_active_hx_shell_state"]["status"], "pass")

    def test_policy_rows_keep_tp_tw_validation_only(self):
        rows = {row["sensor"]: row for row in sensor_policy_rows(self.sample_sensor_rows())}
        self.assertEqual(rows[TP2]["runtime_temperature_allowed"], "false")
        self.assertEqual(rows[TP2]["fit_allowed"], "false")
        self.assertEqual(rows[TP2]["aggregate_score_after_tp2_restore"], "yes")
        self.assertEqual(rows[TW10]["aggregate_score_after_tp2_restore"], "no")


if __name__ == "__main__":
    unittest.main()
