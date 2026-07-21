from __future__ import annotations

import csv
import json
import unittest

from tools.analyze import build_blocker_resolution_wave_implementation as builder


def read_csv(path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class BlockerResolutionWaveImplementationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        builder.main()

    def test_pm5_rows_are_review_ready_not_admitted(self) -> None:
        rows = read_csv(builder.OUT_DIR / "pm5_f6_admission_readiness.csv")
        self.assertGreaterEqual(len(rows), 12)
        self.assertTrue(all(row["has_Re_Pr_Ri_Gr_Ra"] == "true" for row in rows))
        self.assertTrue(all(row["wallHeatFlux_available"] == "true" for row in rows))
        self.assertTrue(all(row["f6_pressure_onset_readiness"] == "review_ready_not_admitted" for row in rows))
        self.assertTrue(all(row["admission_class"] == "review_ready_not_admitted" for row in rows))

    def test_thermal_rows_do_not_promote_internal_nu(self) -> None:
        rows = read_csv(builder.OUT_DIR / "thermal_internal_nu_admission_review.csv")
        self.assertGreater(len(rows), 0)
        self.assertTrue(all(row["guardrail"] == "do_not_fit_boundary_or_storage_residual_into_internal_Nu" for row in rows))
        self.assertEqual(sum(row["internal_nu_fit_allowed"] == "true" for row in rows), 0)

    def test_blocker_refresh_records_fluid_recast(self) -> None:
        rows = read_csv(builder.OUT_DIR / "blocker_register_refresh.csv")
        by_id = {row["blocker_id"]: row for row in rows}
        self.assertEqual(by_id["fluid-external-boundary-api-gap"]["agent413_status"], "partially_resolved_recast")
        self.assertIn("hx_ua_multiplier", by_id["predictive-heater-cooler-wall-submodels"]["evidence_delta"])

    def test_summary_guardrails(self) -> None:
        summary = json.loads((builder.OUT_DIR / "summary.json").read_text(encoding="utf-8"))
        self.assertFalse(summary["native_solver_outputs_mutated"])
        self.assertFalse(summary["scheduler_mutated"])
        self.assertFalse(summary["registry_or_case_admission_mutated"])
        self.assertEqual(summary["final_forward_v1_status"], "blocked_no_go_final_forward_v1_not_admitted")


if __name__ == "__main__":
    unittest.main()
