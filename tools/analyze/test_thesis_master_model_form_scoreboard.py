from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from tools.analyze import build_thesis_master_model_form_scoreboard as builder


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class ThesisMasterModelFormScoreboardTests(unittest.TestCase):
    def test_percent_error_formula_is_signed(self) -> None:
        self.assertAlmostEqual(builder.safe_percent(-10.0, 400.0), -2.5)
        self.assertAlmostEqual(builder.safe_percent(10.0, 400.0), 2.5)
        self.assertIsNone(builder.safe_percent(10.0, 0.0))

    def test_glossary_defines_requested_terms(self) -> None:
        terms = {row["term"] for row in builder.glossary_rows()}
        for term in ["MF", "M", "S13", "two-tap", "TP", "TW", "K", "RMSE"]:
            self.assertIn(term, terms)

    def test_signed_sensor_rows_are_individual_and_signed(self) -> None:
        rows = builder.signed_sensor_error_rows()
        self.assertEqual(len(rows), 204)
        finite = [row for row in rows if row["finite_prediction"] == "true"]
        self.assertTrue(finite)
        sample = next(row for row in rows if row["case_id"] == "salt_2" and row["model_form_id"] == "M1" and row["sensor"] == "TP3")
        self.assertLess(float(sample["signed_error_K"]), 0.0)
        self.assertLess(float(sample["signed_error_percent_of_target"]), 0.0)
        self.assertIn(sample["sensor_kind"], {"TP", "TW"})

    def test_build_outputs_expected_tables(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "pkg"
            summary = builder.build(out)
            self.assertEqual(summary["decision"], "master_scoreboard_refreshed_all_current_scoreable_forms_tried_no_admission")
            self.assertGreaterEqual(summary["master_scoreboard_rows"], 25)
            self.assertEqual(summary["signed_sensor_error_rows"], 204)
            self.assertEqual(summary["diagnostic_tested_model_form_rows"], 6)
            self.assertEqual(summary["final_score_values"], 0)
            for filename in [
                "master_model_form_scoreboard.csv",
                "term_glossary.csv",
                "signed_sensor_errors.csv",
                "signed_sensor_error_summary.csv",
                "figure_ready_signed_sensor_errors.csv",
                "recommended_model_forms_to_try.csv",
                "try_all_model_form_disposition.csv",
                "diagnostic_tested_model_form_scoreboard.csv",
                "diagnostic_tested_sensor_errors.csv",
                "thesis_figure_plan.csv",
                "source_manifest.csv",
                "no_mutation_guardrails.csv",
                "summary.json",
                "README.md",
            ]:
                self.assertTrue((out / filename).exists(), filename)
            master = read_rows(out / "master_model_form_scoreboard.csv")
            ids = {row["scoreboard_id"] for row in master}
            self.assertIn("M5/S13", ids)
            self.assertIn("MF-02/two-tap", ids)
            self.assertIn("D4_M3_segment_offsets_min2_train", ids)
            self.assertIn("PASSIVE-H2-CAND001/latest", ids)


if __name__ == "__main__":
    unittest.main()
