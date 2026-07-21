from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from tools.analyze import build_thermal_mismatch_remedy_deep_dive as builder


class ThermalMismatchRemedyDeepDiveTests(unittest.TestCase):
    def build_temp_package(self) -> Path:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        out = Path(tmp.name) / "deep_dive"
        args = builder.parse_args(["--output-dir", str(out), "--skip-fluid-replays"])
        summary = builder.build_package(args)
        self.assertEqual(3, summary["heater_rows"])
        return out

    def rows(self, path: Path) -> list[dict[str, str]]:
        with path.open(newline="", encoding="utf-8") as f:
            return list(csv.DictReader(f))

    def test_heater_values_are_exact_contract_values(self) -> None:
        out = self.build_temp_package()
        rows = {row["case_id"]: row for row in self.rows(out / "heater_values.csv")}

        self.assertEqual("265.7", rows["salt_2"]["heater_imposed_duty_W"])
        self.assertEqual("243.519", rows["salt_2"]["heater_wallHeatFlux_input_W"])
        self.assertEqual("297.5", rows["salt_3"]["heater_imposed_duty_W"])
        self.assertEqual("273.155", rows["salt_3"]["heater_wallHeatFlux_input_W"])
        self.assertEqual("337.6", rows["salt_4"]["heater_imposed_duty_W"])
        self.assertEqual("310.487", rows["salt_4"]["heater_wallHeatFlux_input_W"])

    def test_energy_budget_identifies_cooler_as_large_defect(self) -> None:
        out = self.build_temp_package()
        rows = self.rows(out / "energy_defect_budget.csv")

        for row in rows:
            self.assertGreater(float(row["cooler_extra_removal_vs_1d_W"]), 85.0)
            self.assertGreater(float(row["known_first_order_correction_W"]), 145.0)
            self.assertGreater(float(row["cfd_test_section_net_sink_W"]), 5.0)

    def test_docs_for_parallel_prompts_and_fixed_mdot_plan_exist(self) -> None:
        out = self.build_temp_package()

        prompts = (out / "parallel_agent_prompts.md").read_text(encoding="utf-8")
        fixed = (out / "fixed_mdot_solver_plan.md").read_text(encoding="utf-8")
        self.assertIn("Agent A: Cooler/HX Duty Audit", prompts)
        self.assertIn("fixed_mdot_kg_s", fixed)
        self.assertIn("Pressure residual is diagnostic", fixed)


if __name__ == "__main__":
    unittest.main()
