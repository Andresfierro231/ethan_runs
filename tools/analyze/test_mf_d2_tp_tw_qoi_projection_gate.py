#!/usr/bin/env python3.11
"""Tests for the MF-D2 TP/TW QOI projection gate."""

from __future__ import annotations

import csv
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.analyze.build_mf_d2_tp_tw_qoi_projection_gate import OUT, build


def rows(name: str) -> list[dict[str, str]]:
    with (OUT / name).open(newline="") as f:
        return list(csv.DictReader(f))


class MfD2TpTwQoiProjectionGateTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        build()

    def test_summary_promising_but_fail_closed(self) -> None:
        summary = json.loads((OUT / "summary.json").read_text())
        self.assertEqual(summary["decision"], "thermal_development_path_promising_diagnostic_only_no_correction_release")
        self.assertTrue(summary["thermal_development_path_promising"])
        self.assertFalse(summary["released_bulk_to_tp_correction_exists"])
        self.assertFalse(summary["runtime_temperature_release"])
        self.assertFalse(summary["source_property_release"])
        self.assertFalse(summary["coefficient_admission"])
        self.assertEqual(summary["final_score_values"], 0)

    def test_d2_improves_tp_and_tw_transfer_vs_m3(self) -> None:
        primary = rows("d2_score_improvement_summary.csv")[0]
        self.assertEqual(primary["comparison"], "D2_vs_M3_transfer")
        self.assertLess(float(primary["d2_transfer_tp_rmse_K"]), float(primary["m3_transfer_tp_rmse_K"]))
        self.assertLess(float(primary["d2_transfer_tw_rmse_K"]), float(primary["m3_transfer_tw_rmse_K"]))
        self.assertGreater(float(primary["tp_rmse_reduction_K"]), float(primary["tw_rmse_reduction_K"]))
        self.assertEqual(primary["status"], "promising_diagnostic_not_admitted")

    def test_bulk_to_tp_correction_not_released(self) -> None:
        audit = {r["layer"]: r for r in rows("bulk_to_tp_correction_existence_audit.csv")}
        self.assertEqual(audit["bulk_to_TP_thermal_development_offset"]["exists_now"], "False")
        self.assertEqual(audit["bulk_to_TP_thermal_development_offset"]["status"], "not_released")
        self.assertEqual(audit["empirical_D2_TP_TW_offsets"]["status"], "diagnostic_only")

    def test_next_plan_orders_tp_before_tw(self) -> None:
        plan = rows("next_analysis_plan.csv")
        self.assertEqual(plan[0]["analysis"], "bulk-to-TP existence proof")
        self.assertEqual(plan[-1]["analysis"], "TW residual after TP projection")
        claims = {r["claim"]: r["status"] for r in rows("publication_claim_boundary.csv")}
        self.assertEqual(claims["D2 proves a released correction."], "forbidden")
        self.assertEqual(claims["Thermal development is worth the next analysis."], "allowed")


if __name__ == "__main__":
    unittest.main()
