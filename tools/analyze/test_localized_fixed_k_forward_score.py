"""Tests for AGENT-328 localized fixed-K forward scoring."""

from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools.analyze import build_localized_fixed_k_forward_score as score


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


class LocalizedFixedKForwardScoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source_rows = score.localized_source_rows()
        cls.score_rows = [
            {
                "case_id": "salt_2",
                "split_assignment": "train",
                "base_variant_id": "F1_heater_only",
                "localized_variant_id": "F1_heater_only_localized_fixed_K",
                "baseline_mdot_error_vs_cfd_kg_s": 0.004,
                "localized_mdot_error_vs_cfd_kg_s": 0.005,
                "baseline_abs_mdot_error_pct": 30.0,
                "localized_abs_mdot_error_pct": 38.0,
                "mdot_error_reduction_pct": -25.0,
                "movement_direction": "away_from_cfd",
                "thermal_fit_used": "false",
                "runtime_uses_cfd_mdot": "false",
                "runtime_uses_realized_cfd_wallheatflux": "false",
                "runtime_uses_validation_temperatures": "false",
            },
            {
                "case_id": "salt_3",
                "split_assignment": "validation",
                "base_variant_id": "F1_heater_only",
                "localized_variant_id": "F1_heater_only_localized_fixed_K",
                "baseline_mdot_error_vs_cfd_kg_s": 0.005,
                "localized_mdot_error_vs_cfd_kg_s": 0.006,
                "baseline_abs_mdot_error_pct": 34.0,
                "localized_abs_mdot_error_pct": 40.0,
                "mdot_error_reduction_pct": -20.0,
                "movement_direction": "away_from_cfd",
                "thermal_fit_used": "false",
                "runtime_uses_cfd_mdot": "false",
                "runtime_uses_realized_cfd_wallheatflux": "false",
                "runtime_uses_validation_temperatures": "false",
            },
            {
                "case_id": "salt_4",
                "split_assignment": "holdout",
                "base_variant_id": "F1_heater_only",
                "localized_variant_id": "F1_heater_only_localized_fixed_K",
                "baseline_mdot_error_vs_cfd_kg_s": 0.006,
                "localized_mdot_error_vs_cfd_kg_s": 0.007,
                "baseline_abs_mdot_error_pct": 36.0,
                "localized_abs_mdot_error_pct": 42.0,
                "mdot_error_reduction_pct": -16.0,
                "movement_direction": "away_from_cfd",
                "thermal_fit_used": "false",
                "runtime_uses_cfd_mdot": "false",
                "runtime_uses_realized_cfd_wallheatflux": "false",
                "runtime_uses_validation_temperatures": "false",
            },
            {
                "case_id": "salt_2",
                "split_assignment": "train",
                "base_variant_id": "F0_current_fluid_sources",
                "localized_variant_id": "F0_current_fluid_sources_localized_fixed_K",
                "baseline_mdot_error_vs_cfd_kg_s": 0.007,
                "localized_mdot_error_vs_cfd_kg_s": 0.006,
                "baseline_abs_mdot_error_pct": 50.0,
                "localized_abs_mdot_error_pct": 45.0,
                "mdot_error_reduction_pct": 14.0,
                "movement_direction": "toward_cfd",
                "thermal_fit_used": "false",
                "runtime_uses_cfd_mdot": "false",
                "runtime_uses_realized_cfd_wallheatflux": "false",
                "runtime_uses_validation_temperatures": "false",
            },
            {
                "case_id": "salt_3",
                "split_assignment": "validation",
                "base_variant_id": "F0_current_fluid_sources",
                "localized_variant_id": "F0_current_fluid_sources_localized_fixed_K",
                "baseline_mdot_error_vs_cfd_kg_s": 0.008,
                "localized_mdot_error_vs_cfd_kg_s": 0.007,
                "baseline_abs_mdot_error_pct": 55.0,
                "localized_abs_mdot_error_pct": 50.0,
                "mdot_error_reduction_pct": 12.0,
                "movement_direction": "toward_cfd",
                "thermal_fit_used": "false",
                "runtime_uses_cfd_mdot": "false",
                "runtime_uses_realized_cfd_wallheatflux": "false",
                "runtime_uses_validation_temperatures": "false",
            },
            {
                "case_id": "salt_4",
                "split_assignment": "holdout",
                "base_variant_id": "F0_current_fluid_sources",
                "localized_variant_id": "F0_current_fluid_sources_localized_fixed_K",
                "baseline_mdot_error_vs_cfd_kg_s": 0.009,
                "localized_mdot_error_vs_cfd_kg_s": 0.008,
                "baseline_abs_mdot_error_pct": 58.0,
                "localized_abs_mdot_error_pct": 52.0,
                "mdot_error_reduction_pct": 11.0,
                "movement_direction": "toward_cfd",
                "thermal_fit_used": "false",
                "runtime_uses_cfd_mdot": "false",
                "runtime_uses_realized_cfd_wallheatflux": "false",
                "runtime_uses_validation_temperatures": "false",
            },
        ]

    def test_localized_k_map_uses_salt2_fit_target_keys(self) -> None:
        k_map = score.localized_k_map(self.source_rows)
        self.assertEqual(set(k_map), {"lower_leg", "right_leg", "upper_leg"})
        self.assertGreater(sum(k_map.values()), 0.0)

    def test_score_rows_preserve_split_and_input_guardrails(self) -> None:
        rows = self.score_rows
        self.assertEqual(len(rows), 6)
        f1_rows = [row for row in rows if row["base_variant_id"] == "F1_heater_only"]
        self.assertEqual({row["case_id"] for row in f1_rows}, {"salt_2", "salt_3", "salt_4"})
        by_case = {row["case_id"]: row for row in f1_rows}
        self.assertEqual(by_case["salt_2"]["split_assignment"], "train")
        self.assertEqual(by_case["salt_3"]["split_assignment"], "validation")
        self.assertEqual(by_case["salt_4"]["split_assignment"], "holdout")
        self.assertTrue(all(row["thermal_fit_used"] == "false" for row in rows))
        self.assertTrue(all(row["runtime_uses_cfd_mdot"] == "false" for row in rows))
        self.assertTrue(all(row["runtime_uses_realized_cfd_wallheatflux"] == "false" for row in rows))
        self.assertTrue(all(row["runtime_uses_validation_temperatures"] == "false" for row in rows))

    def test_variant_summary_keeps_final_forward_v1_diagnostic_only(self) -> None:
        summary = score.variant_summary_rows(self.score_rows)
        f1 = next(row for row in summary if row["base_variant_id"] == "F1_heater_only")
        self.assertIn("diagnostic_only", f1["forward_v1_scoring_decision"])
        self.assertTrue(abs(float(f1["mean_mdot_error_reduction_pct"])) > 0.0)

    def test_run_package_writes_outputs_and_rigor_audit(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            out_dir = Path(tmp) / "localized"
            with mock.patch.object(
                score,
                "build_score_rows",
                return_value=(self.source_rows, self.score_rows),
            ):
                summary = score.run_package(out_dir)
            self.assertEqual(summary["overall_status"], "localized_fixed_k_score_complete_diagnostic_only")
            self.assertFalse(summary["thermal_fit_used"])
            self.assertFalse(summary["external_fluid_modified"])
            self.assertFalse(summary["native_solver_outputs_mutated"])
            self.assertTrue(summary["runtime_uses_imposed_cooler_duty"])
            self.assertTrue((out_dir / "README.md").exists())
            rigor = read_csv(out_dir / "rigor_gate_audit.csv")
            self.assertEqual({row["gate_id"] for row in rigor if row["status"] == "fail"}, set())
            self.assertIn("FWD", {row["gate_id"] for row in rigor if row["status"] == "blocked"})


if __name__ == "__main__":
    unittest.main()
