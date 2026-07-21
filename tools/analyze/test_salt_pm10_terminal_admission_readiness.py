from __future__ import annotations

import csv
import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "tools/analyze/build_salt_pm10_terminal_admission_readiness.py"
OUT = ROOT / "work_products/2026-07/2026-07-17/2026-07-17_salt_pm10_terminal_admission_readiness"


class SaltPm10TerminalAdmissionReadinessTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        subprocess.run(["python3.11", str(SCRIPT), "--no-scheduler"], cwd=ROOT, check=True)

    def read_csv(self, name: str) -> list[dict[str, str]]:
        with (OUT / name).open(newline="", encoding="utf-8") as handle:
            return list(csv.DictReader(handle))

    def test_todo_definition_names_pm10_todo(self) -> None:
        rows = self.read_csv("todo_definition.csv")
        self.assertEqual(rows[0]["todo_id"], "TODO-PREDICT-SALT-PM10-TERMINAL-ADMISSION")
        self.assertIn("salt2_lo10q", rows[0]["cases"])
        self.assertIn("3293924", rows[0]["must_wait_for_jobs"])

    def test_four_pm10_cases_indexed(self) -> None:
        rows = self.read_csv("pm10_case_readiness.csv")
        self.assertEqual({row["case_key"] for row in rows}, {"salt2_lo10q", "salt2_hi10q", "salt4_lo10q", "salt4_hi10q"})
        self.assertTrue(all(row["fit_allowed"] == "no" for row in rows))

    def test_scheduler_disabled_does_not_admit(self) -> None:
        rows = self.read_csv("pm10_case_readiness.csv")
        self.assertEqual({row["readiness_state"] for row in rows}, {"blocked_scheduler_unknown"})

    def test_pm5_reference_preserves_repair_lessons(self) -> None:
        rows = self.read_csv("pm5_workflow_reference.csv")
        text = " ".join(row["pm5_action"] + " " + row["pm10_action"] for row in rows)
        self.assertIn("old broken July 14 script was not relaunched", text)
        self.assertIn("scratch", text)

    def test_summary(self) -> None:
        summary = json.loads((OUT / "summary.json").read_text(encoding="utf-8"))
        self.assertEqual(summary["case_count"], 4)
        self.assertEqual(summary["terminal_admission_performed"], "no")
        self.assertEqual(summary["native_output_mutation"], "none")


if __name__ == "__main__":
    unittest.main()
