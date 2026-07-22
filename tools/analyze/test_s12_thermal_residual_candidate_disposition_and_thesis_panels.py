from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from tools.analyze import build_s12_thermal_residual_candidate_disposition_and_thesis_panels as builder


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class S12ThermalResidualDispositionTests(unittest.TestCase):
    def test_candidate_disposition_is_fail_closed(self) -> None:
        rows = builder.candidate_disposition_rows()
        self.assertEqual(len(rows), 5)
        dispositions = {row["candidate_or_lane"]: row["disposition"] for row in rows}
        self.assertEqual(dispositions["S12-HIAX1"], "not_frozen")
        self.assertEqual(dispositions["passive_wall"], "evidence_only")
        self.assertEqual(dispositions["test_section_source"], "evidence_only")
        self.assertEqual(dispositions["empirical_correction"], "diagnostic_only")
        self.assertEqual(dispositions["junction_stub"], "blocked")
        self.assertTrue(all(row["source_property_release"] == "false" for row in rows))
        self.assertTrue(all(row["final_score_released"] == "false" for row in rows))

    def test_runtime_legality_keeps_all_lanes_unreleased(self) -> None:
        rows = builder.runtime_legality_rows()
        self.assertEqual(len(rows), 5)
        self.assertTrue(all(row["runtime_legal"] == "false" for row in rows))
        self.assertTrue(all(row["validation_holdout_external_scored"] == "false" for row in rows))
        self.assertTrue(all(row["residual_absorbed_into_internal_Nu"] == "false" for row in rows))

    def test_train_metric_context_preserves_train_only_s12_metrics(self) -> None:
        rows = builder.train_metric_context_rows()
        by_metric = {row["metric_family"]: row for row in rows}
        self.assertEqual(by_metric["all_probe"]["rmse_K"], "83.36187927489736")
        self.assertEqual(by_metric["TW"]["rmse_K"], "84.64865165641251")
        self.assertEqual(by_metric["mdot"]["residual_mdot_kg_s"], "-0.010534324976562249")
        self.assertTrue(all(row["metric_use"] == "train_only_context_not_freeze_or_final_score" for row in rows))

    def test_build_outputs_thesis_package_without_release(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "pkg"
            summary = builder.build(out)
            self.assertEqual(summary["decision"], "s12_attempted_rigorously_no_candidate_freeze_allowed")
            self.assertEqual(summary["candidate_disposition_rows"], 5)
            self.assertEqual(summary["candidate_reviewable_rows"], 0)
            self.assertEqual(summary["validation_holdout_external_rows_scored"], 0)
            self.assertEqual(summary["source_property_release_rows"], 0)
            self.assertEqual(summary["final_score_values"], 0)
            self.assertFalse(summary["candidate_freeze_allowed"])
            self.assertTrue((out / "thesis_panel_handoff.md").exists())
            self.assertTrue((out / "figures" / "svg" / "s12_residual_owner_waterfall.svg").exists())
            claims = read_rows(out / "s12_thesis_claim_boundary.csv")
            self.assertIn("S12-X3", {row["claim_id"] for row in claims})


if __name__ == "__main__":
    unittest.main()
