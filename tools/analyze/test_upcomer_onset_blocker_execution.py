from __future__ import annotations

import csv
import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "tools/analyze/build_upcomer_onset_blocker_execution.py"
OUT = ROOT / "work_products/2026-07/2026-07-20/2026-07-20_upcomer_onset_blocker_execution"


class UpcomerOnsetBlockerExecutionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        subprocess.run(["python3.11", str(SCRIPT), "--no-scheduler"], cwd=ROOT, check=True)

    def read_csv(self, name: str) -> list[dict[str, str]]:
        with (OUT / name).open("r", encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle))

    def test_summary_and_outputs_exist(self) -> None:
        summary = json.loads((OUT / "summary.json").read_text(encoding="utf-8"))
        self.assertEqual(summary["ordinary_upcomer_fit_rows_now"], 0)
        for name in summary["outputs"]:
            self.assertTrue((OUT / name).exists(), name)

    def test_pm10_rows_are_extraction_queue_not_fit_rows(self) -> None:
        rows = [row for row in self.read_csv("upcomer_anchor_admission_ledger.csv") if row["evidence_family"].startswith("pm10")]
        self.assertEqual({row["case_key"] for row in rows}, {"salt2_lo10q", "salt2_hi10q", "salt4_lo10q", "salt4_hi10q"})
        self.assertEqual({row["ordinary_Nu_fit_allowed"] for row in rows}, {"no"})
        self.assertEqual({row["classification"] for row in rows}, {"not_admissible_missing_matched_plane_fields"})

    def test_high_heat_rows_are_not_harvested_while_running(self) -> None:
        rows = [row for row in self.read_csv("upcomer_anchor_admission_ledger.csv") if row["evidence_family"] == "high_heat_no_recirc_probe"]
        self.assertEqual(len(rows), 4)
        self.assertTrue(all(row["ordinary_f_D_fit_allowed"] == "no" for row in rows))
        self.assertTrue(all("ordinary_Nu" in row["forbidden_use"] for row in rows))

    def test_current_diagnostics_remain_recirculation_only(self) -> None:
        rows = [
            row
            for row in self.read_csv("upcomer_anchor_admission_ledger.csv")
            if row["evidence_family"] == "current_mainline_recirculation_diagnostic"
        ]
        self.assertEqual(len(rows), 3)
        self.assertEqual({row["classification"] for row in rows}, {"recirculation_diagnostic"})
        self.assertEqual({row["component_K_fit_allowed"] for row in rows}, {"no"})

    def test_launch_queue_prepares_sentinels_without_submission(self) -> None:
        rows = self.read_csv("launch_preflight_queue.csv")
        self.assertGreaterEqual(len(rows), 11)
        sentinel_keys = {row["case_key"] for row in rows if row["priority"] == "1"}
        self.assertIn("salt3_jin_q1500w_hiins_onset_anchor", sentinel_keys)
        self.assertIn("salt3_jin_q0150w_loins_onset_anchor", sentinel_keys)
        self.assertEqual({row["launch_status"] for row in rows}, {"prepared_not_submitted"})


if __name__ == "__main__":
    unittest.main()
