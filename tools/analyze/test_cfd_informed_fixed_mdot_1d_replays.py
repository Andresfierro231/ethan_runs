from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from tools.analyze import run_cfd_informed_fixed_mdot_1d_replays as runner


class CfdInformedFixedMdotReplayTests(unittest.TestCase):
    def build_plan_only_package(self) -> Path:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        out = Path(tmp.name) / "runs"
        args = runner.parse_args(["--output-dir", str(out), "--plan-only"])
        metadata = runner.build_package(args)
        self.assertEqual(21, metadata["run_plan_rows"])
        self.assertEqual(0, metadata["result_rows"])
        return out

    def rows(self, path: Path) -> list[dict[str, str]]:
        with path.open(newline="", encoding="utf-8") as f:
            return list(csv.DictReader(f))

    def test_run_plan_has_seven_paths_per_salt_case(self) -> None:
        out = self.build_plan_only_package()
        rows = self.rows(out / "run_plan.csv")

        self.assertEqual(21, len(rows))
        for case_id in {"salt_2", "salt_3", "salt_4"}:
            paths = {row["path_id"] for row in rows if row["case_id"] == case_id}
            self.assertEqual(
                {
                    "P0_fixed_mdot_current_1d_contract",
                    "P1_cfd_cooler_duty_only",
                    "P2_heater_wallflux_no_test_source",
                    "P3_source_plus_test_section_sink",
                    "P4_cfd_cooler_plus_heater_wallflux",
                    "P5_cfd_cooler_source_plus_test_sink",
                    "P6_full_patch_ledger_prescribed",
                },
                paths,
            )

    def test_run_plan_separates_thermal_replay_from_pressure_scoring(self) -> None:
        out = self.build_plan_only_package()
        rows = self.rows(out / "run_plan.csv")

        for row in rows:
            self.assertIn("hold mdot at CFD observation", row["hydraulic_policy"])
            self.assertIn("pressure_residual_diagnostic", row["score_partition"])

    def test_result_schema_contains_diagnostic_pressure_columns(self) -> None:
        self.assertIn("pressure_residual_Pa", runner.RESULT_COLUMNS)
        self.assertIn("pressure_root_policy", runner.RESULT_COLUMNS)
        self.assertIn("deltaP_buoyancy_Pa", runner.RESULT_COLUMNS)
        self.assertIn("deltaP_losses_Pa", runner.RESULT_COLUMNS)


if __name__ == "__main__":
    unittest.main()
