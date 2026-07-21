"""Tests for AGENT-448 Salt1 admission and scorecard package."""

from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.analyze import build_salt1_primary_evidence_admission_and_scorecard as mod


class Salt1PrimaryEvidenceAdmissionAndScorecardTests(unittest.TestCase):
    def test_scorecard_uses_only_admission_statuses_and_admits_salt1(self) -> None:
        summaries = [
            {"case_id": "salt1_nominal", "suspicious_monitor_flag": "no"},
            {"case_id": "salt1_lo10q", "suspicious_monitor_flag": "no"},
            {"case_id": "salt1_hi10q", "suspicious_monitor_flag": "no"},
        ]

        rows = mod.build_scorecard(summaries)
        by_key = {row["case_key"]: row for row in rows}
        allowed = {"admitted", "validation-only", "diagnostic-only", "blocked"}

        self.assertEqual({row["admission_status"] for row in rows} - allowed, set())
        self.assertEqual(by_key["salt1_nominal"]["admission_status"], "admitted")
        self.assertEqual(by_key["salt1_lo10q"]["admission_status"], "admitted")
        self.assertEqual(by_key["salt1_hi10q"]["admission_status"], "admitted")
        self.assertEqual(by_key["salt3_jin_nominal"]["admission_status"], "admitted")
        self.assertEqual(by_key["salt4_nominal"]["admission_status"], "admitted")
        self.assertEqual(by_key["salt4_hi5q"]["admission_status"], "diagnostic-only")
        self.assertEqual(by_key["salt2_hi10q"]["admission_status"], "blocked")

    def test_main_writes_package_and_summary(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            out = Path(tmp)
            product = out / "product"
            journal = out / "journal.md"
            manifest = out / "import.json"
            status = out / "status.md"

            fake_monitor_rows = (
                [{"case_id": "salt1_nominal", "family": "total_Q", "status": "analyzed", "verdict": "steady"}],
                {
                    "case_id": "salt1_nominal",
                    "max_mdot_rel_drift": 1e-7,
                    "max_mdot_rel_span": 1e-7,
                    "max_tp_abs_drift_K": 0.0,
                    "max_tw_abs_drift_K": 0.0,
                    "total_Q_drift_W": 0.0,
                    "all_monitor_verdicts": "steady",
                    "suspicious_monitor_flag": "no",
                },
            )

            with (
                patch.object(mod, "PRODUCT", product),
                patch.object(mod, "JOURNAL", journal),
                patch.object(mod, "IMPORT", manifest),
                patch.object(mod, "STATUS", status),
                patch.object(mod, "monitor_rows", return_value=fake_monitor_rows),
                patch.object(mod, "convergence_audit", return_value={
                    "case_id": "salt1_nominal",
                    "functions_path": "system/functions",
                    "log_paths": "logs/log.foamRun",
                    "has_stopAt_writeNow": "no",
                    "diagnostic_continue_message_in_functions": "yes",
                    "diagnostic_criterion_message_in_functions": "yes",
                    "foam_fatal_in_tail": "no",
                    "cancelled_in_tail": "yes",
                    "latest_time_in_tail_s": "7884.81875",
                    "pimple_criteria_note": "diagnostic",
                    "audit_interpretation": "not_suspicious_diagnostic_only_monitor_operational_cancel",
                }),
            ):
                mod.main()

            self.assertTrue((product / "README.md").is_file())
            self.assertTrue((product / "final_admission_status_scorecard.csv").is_file())
            self.assertTrue(journal.is_file())
            self.assertTrue(manifest.is_file())

            summary = json.loads((product / "summary.json").read_text())
            self.assertTrue(summary["salt1_promoted_to_primary_evidence"])
            self.assertEqual(summary["salt1_cases_reviewed"], 3)
            self.assertGreaterEqual(summary["scorecard_status_counts"]["admitted"], 6)

            with (product / "final_admission_status_scorecard.csv").open(newline="") as f:
                rows = list(csv.DictReader(f))
            self.assertEqual(rows[0]["admission_status"], "admitted")


if __name__ == "__main__":
    unittest.main()
