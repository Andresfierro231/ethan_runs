#!/usr/bin/env python3
"""Tests for the two-tap raw endpoint sampling contract."""

from __future__ import annotations

import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_two_tap_component_raw_endpoint_plan as builder  # noqa: E402


class TwoTapComponentRawEndpointPlanTests(unittest.TestCase):
    def build_tmp(self) -> Path:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        out = Path(tmp.name)
        builder.build_package(out)
        return out

    def rows(self, path: Path) -> list[dict[str, str]]:
        with path.open(newline="", encoding="utf-8") as handle:
            return list(csv.DictReader(handle))

    def test_outputs_and_summary(self) -> None:
        out = self.build_tmp()
        for name in [
            "README.md",
            "target_feature_taps.csv",
            "pressure_surface_sampling_contract.csv",
            "basis_field_contract.csv",
            "recirculation_metric_contract.csv",
            "same_qoi_uncertainty_contract.csv",
            "launch_readiness_gate.csv",
            "raw_endpoint_plan_summary.csv",
            "source_manifest.csv",
            "summary.json",
        ]:
            self.assertTrue((out / name).exists(), name)
        summary = json.loads((out / "summary.json").read_text(encoding="utf-8"))
        self.assertEqual(summary["task"], "TODO-TWO-TAP-COMPONENT-RAW-ENDPOINTS")
        self.assertEqual(summary["target_rows"], 3)
        self.assertEqual(summary["endpoint_surface_rows"], 6)
        self.assertEqual(summary["basis_field_rows"], 8)
        self.assertEqual(summary["recirculation_contract_rows"], 3)
        self.assertEqual(summary["same_qoi_uncertainty_rows"], 3)
        self.assertEqual(summary["sampling_jobs_launched"], 0)
        self.assertEqual(summary["ordinary_admissions"], 0)
        self.assertEqual(summary["scientific_admission_change"], "none")
        self.assertEqual(summary["scheduler_action"], "none")

    def test_target_taps_are_exact_corner_lower_right_endpoints(self) -> None:
        rows = self.rows(self.build_tmp() / "target_feature_taps.csv")
        self.assertEqual({row["case_id"] for row in rows}, {"salt_2", "salt_3", "salt_4"})
        self.assertEqual({row["feature"] for row in rows}, {"corner_lower_right"})
        self.assertEqual(
            {row["time_window_s"] for row in rows},
            {"7915", "7618", "10000"},
        )
        for row in rows:
            self.assertEqual(row["upstream_patch"], "ncc_pipeleg_lower_09_fitting_end")
            self.assertEqual(row["downstream_patch"], "ncc_pipeleg_right_01_lower_start")
            self.assertEqual(row["upstream_station_label"], "lower_leg__s04")
            self.assertEqual(row["downstream_station_label"], "right_leg__s00")
            self.assertEqual(row["upstream_output_label"], "corner_lower_right__upstream_lower_leg__s04")
            self.assertEqual(row["downstream_output_label"], "corner_lower_right__downstream_right_leg__s00")
            self.assertAlmostEqual(float(row["centerline_tap_length_m"]), 0.15020855004)
            self.assertIn("p;p_rgh;U", row["required_endpoint_fields"])
            self.assertIn("do not mutate", row["guardrail"])

    def test_pressure_contract_requires_p_prgh_u_and_no_double_counting(self) -> None:
        rows = self.rows(self.build_tmp() / "pressure_surface_sampling_contract.csv")
        self.assertEqual(len(rows), 6)
        labels = {row["surface_label"] for row in rows}
        self.assertIn("corner_lower_right__upstream_lower_leg__s04", labels)
        self.assertIn("corner_lower_right__downstream_right_leg__s00", labels)
        for row in rows:
            self.assertIn("p,p_rgh,U,T_or_rho", row["sampled_fields"])
            self.assertIn("do not add it again", row["hydrostatic_policy"])
            self.assertIn("do not double count", row["kinetic_policy"])
            self.assertIn("finite endpoint p and p_rgh", row["acceptance_signal"])
            self.assertNotIn("{role}", row["output_fields"])
            self.assertIn(f"p_{row['tap_role']}_pa", row["output_fields"])

    def test_basis_contract_has_required_future_schema_fields(self) -> None:
        rows = self.rows(self.build_tmp() / "basis_field_contract.csv")
        fields = {row["field"] for row in rows}
        self.assertEqual(
            fields,
            {
                "p_upstream_pa",
                "p_downstream_pa",
                "hydrostatic_correction_pa",
                "kinetic_correction_pa",
                "local_dynamic_pressure_pa",
                "straight_loss_subtraction_pa",
                "K_apparent",
                "K_local",
            },
        )
        k_local = next(row for row in rows if row["field"] == "K_local")
        self.assertIn("nonnegative without clipping", k_local["acceptance_rule"])
        straight = next(row for row in rows if row["field"] == "straight_loss_subtraction_pa")
        self.assertIn("current centerline subtraction is not admissible", straight["formula_or_source"])

    def test_recirculation_and_uq_gates_preserve_diagnostic_fallback(self) -> None:
        recirc = self.rows(self.build_tmp() / "recirculation_metric_contract.csv")
        self.assertEqual(len(recirc), 3)
        for row in recirc:
            self.assertIn("RAF < 0.01", row["ordinary_acceptance_rule"])
            self.assertIn("RMF < 0.01", row["ordinary_acceptance_rule"])
            self.assertIn("do not fit F6 or component K", row["diagnostic_fallback"])
        uq = self.rows(self.build_tmp() / "same_qoi_uncertainty_contract.csv")
        self.assertEqual({row["current_status"] for row in uq}, {"missing_same_qoi_mesh_time_UQ"})
        for row in uq:
            self.assertIn("same pressure-loss QoI", row["acceptance_signal"])
            self.assertIn("do not fabricate GCI", row["guardrail"])

    def test_launch_gates_keep_work_separate_from_sampling_and_f6(self) -> None:
        rows = self.rows(self.build_tmp() / "launch_readiness_gate.csv")
        gates = {row["gate"]: row for row in rows}
        self.assertIn("F6_separation", gates)
        self.assertIn("does not fit F6", gates["F6_separation"]["guardrail"])
        self.assertIn("claim separate staged-copy postprocessing row", gates["task_scope"]["required_before_sampling_launch"])
        self.assertIn("do not substitute left_lower_leg__s00", gates["target_taps_resolved"]["guardrail"])


if __name__ == "__main__":
    unittest.main()
