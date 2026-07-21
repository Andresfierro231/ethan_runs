from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from tools.analyze.build_salt1_terminal_bc_and_pm5_upcomer_harvest import (
    build_salt1_terminal_bc_and_pm5_upcomer_harvest,
)


class Salt1TerminalBCHarvestTests(unittest.TestCase):
    def test_salt1_patch_table_and_hi10q_resolution(self) -> None:
        with tempfile.TemporaryDirectory(prefix="salt1-bc-harvest-") as tmpdir:
            out_dir = Path(tmpdir)
            summary = build_salt1_terminal_bc_and_pm5_upcomer_harvest(out_dir)
            self.assertEqual(summary["salt1_case_count"], 3)
            self.assertEqual(summary["salt1_patch_rows"], 207)
            self.assertTrue(summary["salt1_hi10q_conflict_removed"])

            admission = self._rows_by(out_dir / "salt1_training_admission_update.csv", "case_id")
            self.assertEqual(admission["salt1_hi10q"]["use_now_for_training"], "yes")
            self.assertEqual(admission["salt1_hi10q"]["admission_decision"], "training_admissible_perturbed_q")

    def test_role_table_contains_heater_cooler_and_radiative_wall(self) -> None:
        with tempfile.TemporaryDirectory(prefix="salt1-bc-harvest-") as tmpdir:
            out_dir = Path(tmpdir)
            build_salt1_terminal_bc_and_pm5_upcomer_harvest(out_dir)
            rows = self._read_rows(out_dir / "salt1_terminal_patch_bc_role_table.csv")
            roles = {row["thermal_role"] for row in rows}
            self.assertIn("heater_source", roles)
            self.assertIn("heater_source_test_section", roles)
            self.assertIn("cooler_HX_removal", roles)
            self.assertIn("passive_wall_rcExternalTemperature", roles)

    def test_required_outputs_exist(self) -> None:
        with tempfile.TemporaryDirectory(prefix="salt1-bc-harvest-") as tmpdir:
            out_dir = Path(tmpdir)
            summary = build_salt1_terminal_bc_and_pm5_upcomer_harvest(out_dir)
            for filename in summary["required_outputs"]:
                self.assertTrue((out_dir / filename).exists(), filename)

    @staticmethod
    def _read_rows(path: Path) -> list[dict[str, str]]:
        with path.open(encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle))

    @classmethod
    def _rows_by(cls, path: Path, key: str) -> dict[str, dict[str, str]]:
        return {row[key]: row for row in cls._read_rows(path)}


if __name__ == "__main__":
    unittest.main()
