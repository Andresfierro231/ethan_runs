from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path

from tools.analyze import build_mdot_temperature_probe_error_audit as audit


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


class MdotTemperatureProbeErrorAuditTests(unittest.TestCase):
    def test_builds_expected_outputs_without_fluid_execution(self) -> None:
        with tempfile.TemporaryDirectory(prefix="mdot-tp-audit-") as tmp:
            out = Path(tmp)
            summary = audit.build(out, execute_fluid=False)
            self.assertEqual(summary["task"], "AGENT-360")
            self.assertFalse(summary["native_cfd_outputs_mutated"])
            self.assertFalse(summary["external_cfd_modeling_tools_mutated"])
            for name in [
                "README.md",
                "paper_ready_report.md",
                "study_assumption_register.csv",
                "case_admission_and_use_table.csv",
                "model_mode_matrix.csv",
                "mdot_error_summary.csv",
                "model_result_ledger.csv",
                "sensor_level_errors.csv",
                "temperature_probe_error_summary.csv",
                "part1_full_cfd_flux_mdot_sensor_errors.csv",
                "part2_heater_test_cooler_errors.csv",
                "part3_heater_cooler_only_errors.csv",
                "part3_test_section_error_increment.csv",
                "part4_cooling_leg_heat_removed_scores.csv",
                "part4_cooling_rmse_summary.csv",
                "part5_heating_leg_heat_added_scores.csv",
                "part5_heating_rmse_summary.csv",
                "mdot_temperature_error_correlation.csv",
                "trend_conclusion_register.csv",
                "source_manifest.csv",
                "summary.json",
            ]:
                self.assertTrue((out / name).exists(), name)
            self.assertTrue((out / "model_config_appendix" / "cases.yaml").exists())
            parsed = json.loads((out / "summary.json").read_text(encoding="utf-8"))
            self.assertEqual(parsed["salt1_policy"], "diagnostic_context_only_blocked_for_cfd_heat_flux_modes")
            report = (out / "paper_ready_report.md").read_text(encoding="utf-8")
            self.assertIn("## Assumptions", report)
            self.assertIn("## Trends and Conclusions", report)

    def test_case_split_and_salt1_policy_are_explicit(self) -> None:
        with tempfile.TemporaryDirectory(prefix="mdot-tp-audit-") as tmp:
            out = Path(tmp)
            audit.build(out, execute_fluid=False)
            by_case = {row["case_id"]: row for row in rows(out / "case_admission_and_use_table.csv")}
            self.assertEqual(by_case["salt_1"]["admission_use_class"], "diagnostic_context_only")
            self.assertEqual(by_case["salt_1"]["fit_use"], "no")
            self.assertEqual(by_case["salt_2"]["split"], "train")
            self.assertEqual(by_case["salt_3"]["split"], "validation")
            self.assertEqual(by_case["salt_4"]["split"], "holdout")

    def test_modes_label_cfd_informed_and_fixed_mdot_correctly(self) -> None:
        matrix = {row["mode_id"]: row for row in audit.mode_rows()}
        self.assertEqual(matrix["M1_full_cfd_segment_heat_flux_pressure_root"]["uses_cfd_mdot_runtime"], "no")
        self.assertEqual(matrix["M1_full_cfd_segment_heat_flux_pressure_root"]["uses_realized_cfd_wallHeatFlux_runtime"], "yes")
        self.assertEqual(matrix["M1b_full_cfd_segment_heat_flux_fixed_mdot"]["uses_cfd_mdot_runtime"], "yes")
        self.assertIn("diagnostic", matrix["M1b_full_cfd_segment_heat_flux_fixed_mdot"]["predictivity_class"])

    def test_salt1_rows_are_blocked_when_fluid_execution_disabled_or_heat_missing(self) -> None:
        with tempfile.TemporaryDirectory(prefix="mdot-tp-audit-") as tmp:
            out = Path(tmp)
            audit.build(out, execute_fluid=False)
            result_rows = rows(out / "model_result_ledger.csv")
            salt1 = [row for row in result_rows if row["case_id"] == "salt_1"]
            self.assertGreater(len(salt1), 0)
            self.assertTrue(all(row["result_status"] == "blocked_missing_inputs" for row in salt1))
            self.assertTrue(any("patch heat ledger" in row["blocked_reason"] for row in salt1))

    def test_sensor_reference_loader_prefers_jin_labels(self) -> None:
        refs = audit.load_sensor_refs()
        self.assertIn(("salt_1", "TP1"), refs)
        self.assertIn("Salt 1 Jin", refs[("salt_1", "TP1")]["frozen_case_label"])
        self.assertIn(("salt_4", "TW11"), refs)

    def test_assumption_register_contains_radiation_and_runtime_discipline(self) -> None:
        assumptions = {row["assumption_id"]: row for row in audit.assumption_rows()}
        self.assertIn("no separate qr", assumptions["A002"]["statement"])
        self.assertIn("Realized CFD wallHeatFlux", assumptions["A003"]["statement"])
        self.assertIn("Salt2", assumptions["A007"]["statement"])


if __name__ == "__main__":
    unittest.main()
