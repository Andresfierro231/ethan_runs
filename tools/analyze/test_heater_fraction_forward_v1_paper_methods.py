"""Tests for the heater fraction / forward-v1 paper-methods package."""

from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path

from tools.analyze.build_heater_fraction_forward_v1_paper_methods import build_package


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class HeaterFractionForwardV1PaperMethodsTests(unittest.TestCase):
    def test_summary_fails_closed_and_preserves_runtime_hygiene(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            summary = build_package(Path(tmp))

            self.assertEqual(summary["task"], "AGENT-390")
            self.assertEqual(summary["final_forward_v1_status"], "blocked_no_go_final_forward_v1_not_admitted")
            self.assertFalse(summary["final_forward_v1_admitted"])
            self.assertEqual(summary["runtime_input_audit_violations"], 0)
            self.assertFalse(summary["native_solver_outputs_mutated"])
            self.assertFalse(summary["registry_mutated"])
            self.assertFalse(summary["scheduler_action_taken"])
            self.assertFalse(summary["external_fluid_modified_by_this_task"])

    def test_only_salt2_is_fit_row_for_scalar_candidates(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            out = Path(tmp)
            build_package(out)
            rows = read_csv(out / "heater_fraction_split_scores.csv")

            scalar_fit_rows = [
                row
                for row in rows
                if row["model_id"] in {"H1_eta_heater_fit_salt2", "H2_test_section_external_loss_fit_salt2"}
                and row["score_role"] == "fit_row"
            ]
            self.assertEqual({row["case_id"] for row in scalar_fit_rows}, {"salt_2"})
            heldout_scalar_rows = [
                row
                for row in rows
                if row["model_id"] in {"H1_eta_heater_fit_salt2", "H2_test_section_external_loss_fit_salt2"}
                and row["case_id"] in {"salt_3", "salt_4"}
            ]
            self.assertTrue(heldout_scalar_rows)
            self.assertTrue(all(row["score_role"] == "score_only" for row in heldout_scalar_rows))

    def test_salt2_scalar_fits_zero_train_error_by_construction(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            out = Path(tmp)
            build_package(out)
            rows = read_csv(out / "heater_fraction_split_scores.csv")
            fit_rows = {
                row["model_id"]: row
                for row in rows
                if row["case_id"] == "salt_2"
                and row["model_id"] in {"H1_eta_heater_fit_salt2", "H2_test_section_external_loss_fit_salt2"}
            }

            for row in fit_rows.values():
                self.assertAlmostEqual(float(row["predicted_Tmean_error_K"]), 0.0, places=9)
                self.assertEqual(row["runtime_input_audit"], "no_cfd_mdot_no_wallHeatFlux_no_validation_temperature_runtime_input")

    def test_heater_only_beats_rejected_37w_on_heldout(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            out = Path(tmp)
            build_package(out)
            summaries = {row["model_id"]: row for row in read_csv(out / "heater_fraction_model_summary.csv")}

            heater_only = float(summaries["H0_heater_only_unfitted"]["heldout_mean_abs_Tmean_error_K"])
            legacy = float(summaries["H3_test_section_37W_rejected"]["heldout_mean_abs_Tmean_error_K"])
            self.assertLess(heater_only, legacy)

    def test_required_paper_artifacts_written(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            out = Path(tmp)
            build_package(out)
            expected = {
                "README.md",
                "methods_process.md",
                "heater_fraction_scalar_candidates.csv",
                "heater_fraction_split_scores.csv",
                "heater_fraction_model_summary.csv",
                "heater_fraction_decision_table.csv",
                "runtime_input_audit.csv",
                "result_intake_table.csv",
                "claim_limitations_table.csv",
                "figure_table_index.csv",
                "source_manifest.csv",
                "summary.json",
            }
            for name in expected:
                self.assertTrue((out / name).exists(), name)

            parsed = json.loads((out / "summary.json").read_text(encoding="utf-8"))
            self.assertEqual(parsed["task"], "AGENT-390")


if __name__ == "__main__":
    unittest.main()
