#!/usr/bin/env python3
"""Tests for AGENT-530 two-tap component repair extractor."""

from __future__ import annotations

import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_two_tap_component_repair_extractor as builder  # noqa: E402


class TwoTapComponentRepairExtractorTests(unittest.TestCase):
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
            "two_tap_component_repair_output.csv",
            "extractor_gate_results.csv",
            "next_raw_postprocessing_queue.csv",
            "extractor_summary.csv",
            "source_manifest.csv",
            "summary.json",
        ]:
            self.assertTrue((out / name).exists(), name)
        summary = json.loads((out / "summary.json").read_text(encoding="utf-8"))
        self.assertEqual(summary["task"], "AGENT-530")
        self.assertEqual(summary["extractor_rows"], 3)
        self.assertEqual(summary["ordinary_admitted_rows"], 0)
        self.assertEqual(summary["diagnostic_blocked_rows"], 3)
        self.assertEqual(summary["missing_endpoint_pressure_rows"], 3)
        self.assertEqual(summary["negative_K_local_rows"], 3)
        self.assertEqual(summary["gate_fail_rows"], 15)
        self.assertEqual(summary["scientific_admission_change"], "none")
        self.assertEqual(summary["scheduler_action"], "none")

    def test_extractor_schema_preserves_missing_endpoint_fields(self) -> None:
        rows = self.rows(self.build_tmp() / "two_tap_component_repair_output.csv")
        self.assertEqual(len(rows), 3)
        self.assertEqual(list(rows[0]), builder.EXTRACTOR_COLUMNS)
        self.assertEqual({row["feature"] for row in rows}, {"corner_lower_right"})
        self.assertEqual({row["case_id"] for row in rows}, {"salt_2", "salt_3", "salt_4"})
        for row in rows:
            self.assertEqual(row["p_upstream_pa"], "")
            self.assertEqual(row["p_downstream_pa"], "")
            self.assertEqual(row["RAF"], "")
            self.assertEqual(row["RMF"], "")
            self.assertEqual(row["SVF"], "")
            self.assertLess(float(row["K_local"]), 0.0)
            self.assertEqual(row["mesh_time_uncertainty"], "missing_same_qoi_mesh_time_UQ")
            self.assertEqual(row["admission_status"], "diagnostic_blocked_missing_raw_endpoint_pressure_basis_recirculation_UQ")

    def test_gate_results_fail_all_predeclared_gates(self) -> None:
        rows = self.rows(self.build_tmp() / "extractor_gate_results.csv")
        self.assertEqual(len(rows), 15)
        self.assertEqual({row["status"] for row in rows}, {"fail"})
        gates = {row["gate"] for row in rows}
        self.assertEqual(
            gates,
            {
                "pressure_and_velocity_basis",
                "straight_reference",
                "component_isolation",
                "recirculation_policy",
                "same_qoi_mesh_time_UQ",
            },
        )
        straight_rows = [row for row in rows if row["gate"] == "straight_reference"]
        self.assertTrue(all("over_subtracts" in row["blocker"] for row in straight_rows))

    def test_next_queue_names_required_raw_artifacts(self) -> None:
        rows = self.rows(self.build_tmp() / "next_raw_postprocessing_queue.csv")
        artifacts = {row["missing_artifact"] for row in rows}
        self.assertEqual(
            artifacts,
            {
                "raw_feature_endpoint_pressure_surfaces",
                "final_pressure_velocity_basis",
                "physically_comparable_straight_reference",
                "same_window_RAF_RMF_SVF",
                "same_qoi_mesh_time_uncertainty",
            },
        )
        by_artifact = {row["missing_artifact"]: row for row in rows}
        self.assertIn("finite p_upstream_pa", by_artifact["raw_feature_endpoint_pressure_surfaces"]["acceptance_signal"])
        self.assertIn("not clipped", by_artifact["physically_comparable_straight_reference"]["acceptance_signal"])
        self.assertIn("RAF < 0.01", by_artifact["same_window_RAF_RMF_SVF"]["acceptance_signal"])


if __name__ == "__main__":
    unittest.main()
