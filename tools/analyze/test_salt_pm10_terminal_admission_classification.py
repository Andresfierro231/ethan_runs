from __future__ import annotations

import csv
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from tools.analyze import build_salt_pm10_terminal_admission_classification as mod


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "tools/analyze/build_salt_pm10_terminal_admission_classification.py"
OUT = ROOT / "work_products/2026-07/2026-07-20/2026-07-20_salt_pm10_terminal_admission_classification"


class SaltPm10TerminalAdmissionClassificationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        subprocess.run(["python3.11", str(SCRIPT), "--no-scheduler"], cwd=ROOT, check=True)

    def read_csv(self, name: str) -> list[dict[str, str]]:
        with (OUT / name).open(newline="", encoding="utf-8") as handle:
            return list(csv.DictReader(handle))

    def test_scheduler_evidence_records_timeout_and_completed_harvest(self) -> None:
        rows = {row["job_id"]: row for row in self.read_csv("scheduler_evidence.csv")}
        self.assertEqual(rows["3293924"]["scheduler_state"], "TIMEOUT")
        self.assertEqual(rows["3295438"]["scheduler_state"], "COMPLETED")
        self.assertIn("slurm-saltq_sel_cont-3293924.err", rows["3293924"]["evidence_source"])

    def test_four_pm10_rows_classified_without_fit_permissions(self) -> None:
        rows = self.read_csv("pm10_split_decisions.csv")
        self.assertEqual({row["case_key"] for row in rows}, {"salt2_lo10q", "salt2_hi10q", "salt4_lo10q", "salt4_hi10q"})
        self.assertTrue(all(row["fit_allowed"] == "no" for row in rows))
        self.assertTrue(all(row["model_selection_allowed"] == "no" for row in rows))
        self.assertTrue(all(row["runtime_input_allowed"] == "no" for row in rows))

    def test_terminal_rows_are_holdout_scoring_not_fit_admitted(self) -> None:
        rows = self.read_csv("pm10_terminal_admission_rows.csv")
        self.assertEqual(len(rows), 4)
        self.assertTrue(all(row["terminal_holdout_classification"] == "admitted_for_future_holdout_scoring_after_final_freeze" for row in rows))
        self.assertTrue(all(row["fit_admission"] == "not_fit_admitted" for row in rows))

    def test_pressure_upcomer_remains_diagnostic(self) -> None:
        rows = self.read_csv("pm10_pressure_upcomer_review.csv")
        self.assertTrue(all(row["fit_eligible"] == "no" for row in rows))
        self.assertTrue(all(row["matched_plane_metric_rows"] == "0" for row in rows))
        self.assertTrue(all("pm10_matched_plane_metrics_absent" in row["blockers"] for row in rows))

    def test_strict_log_scanner_ignores_mesh_error_and_timeout_text(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "log.foamRun"
            path.write_text(
                "\n".join(
                    [
                        "Source average openness/error/depth/angle = 1e-16/1e-14/0/0",
                        "slurmstepd: error: *** STEP 3293924.1 CANCELLED DUE TO TIME LIMIT ***",
                        "srun: error: task 3: Terminated",
                    ]
                ),
                encoding="utf-8",
            )
            result = mod.strict_log_markers(path)
        self.assertEqual(result["strict_fatal_count"], 0)

    def test_summary_guardrails(self) -> None:
        summary = json.loads((OUT / "summary.json").read_text(encoding="utf-8"))
        self.assertEqual(summary["case_count"], 4)
        self.assertEqual(summary["solver_job_state"], "TIMEOUT")
        self.assertEqual(summary["harvest_job_state"], "COMPLETED")
        self.assertEqual(summary["fit_admitted_rows"], 0)
        self.assertEqual(summary["model_fitting_performed"], "no")
        self.assertEqual(summary["native_output_mutation"], "none")


if __name__ == "__main__":
    unittest.main()
