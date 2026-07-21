#!/usr/bin/env python3
"""Tests for build_heater_source_split_screen.py."""

from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path

from tools.analyze import build_heater_source_split_screen as screen


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class HeaterSourceSplitScreenTests(unittest.TestCase):
    def test_candidate_specs_fit_only_salt2(self) -> None:
        rows = screen.case_rows()
        specs = {row["model_id"]: row for row in screen.candidate_specs(rows)}

        self.assertEqual(specs["C2_eta_heater_fit_salt2"]["fit_case_id"], "salt_2")
        self.assertEqual(specs["C3_test_section_external_loss_fit_salt2"]["fit_case_id"], "salt_2")
        self.assertAlmostEqual(
            specs["C2_eta_heater_fit_salt2"]["eta_heater"],
            next(row for row in rows if row["case_id"] == "salt_2")["equivalent_eta_heater_fit"],
        )
        self.assertAlmostEqual(
            specs["C3_test_section_external_loss_fit_salt2"]["test_section_external_loss_W"],
            next(row for row in rows if row["case_id"] == "salt_2")["equivalent_test_section_external_loss_fit_W"],
        )

    def test_score_rows_exclude_forbidden_runtime_inputs(self) -> None:
        rows = screen.case_rows()
        scores = screen.score_rows(rows, screen.candidate_specs(rows))

        self.assertEqual(len(scores), 12)
        self.assertEqual({row["forbidden_runtime_inputs_used"] for row in scores}, {"false"})
        self.assertEqual(
            {
                row["cfd_target_use"]
                for row in scores
                if row["model_id"] == "C2_eta_heater_fit_salt2" and row["case_id"] == "salt_2"
            },
            {"fit_target_train_only"},
        )
        self.assertEqual(
            {
                row["cfd_target_use"]
                for row in scores
                if row["model_id"] == "C2_eta_heater_fit_salt2" and row["case_id"] in {"salt_3", "salt_4"}
            },
            {"score_target_only"},
        )

    def test_one_scalar_candidates_improve_validation_holdout_proxy(self) -> None:
        rows = screen.case_rows()
        scores = screen.score_rows(rows, screen.candidate_specs(rows))
        params = {row["model_id"]: row for row in screen.parameter_rows(scores, screen.candidate_specs(rows))}

        self.assertEqual(
            params["C1_heater_only_unfitted"]["runtime_admissibility"],
            "recommended_split_scored_unfitted_source_contract",
        )
        self.assertLess(
            float(params["C2_eta_heater_fit_salt2"]["validation_plus_holdout_delta_vs_C1_K"]),
            0.0,
        )
        self.assertLess(
            float(params["C3_test_section_external_loss_fit_salt2"]["validation_plus_holdout_delta_vs_C1_K"]),
            0.0,
        )
        self.assertEqual(
            params["C2_eta_heater_fit_salt2"]["runtime_admissibility"],
            "passes_locked_split_Tmean_proxy_screen_not_final_admission",
        )

    def test_build_package_writes_requested_artifacts(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            out = Path(tmp)
            summary = screen.build_package(out)

            self.assertEqual(summary["task"], "AGENT-332")
            self.assertTrue(summary["runtime_guardrail_passed"])
            self.assertFalse(summary["final_forward_v1_admitted"])
            self.assertFalse(summary["native_solver_outputs_mutated"])
            self.assertFalse(summary["external_fluid_modified"])
            self.assertEqual(summary["next_default_source_contract"], "C1_heater_only_unfitted")

            for name in {
                "heater_source_split_score_rows.csv",
                "heater_source_parameter_screen.csv",
                "heater_source_gate_decision.csv",
                "source_manifest.csv",
                "summary.json",
                "README.md",
            }:
                self.assertTrue((out / name).exists(), name)

            parsed = json.loads((out / "summary.json").read_text(encoding="utf-8"))
            self.assertEqual(parsed["split"], "salt_2=train;salt_3=validation;salt_4=holdout")
            self.assertEqual(len(read_csv(out / "heater_source_split_score_rows.csv")), 12)


if __name__ == "__main__":
    unittest.main()
