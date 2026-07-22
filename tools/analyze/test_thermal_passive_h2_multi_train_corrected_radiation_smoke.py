#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import subprocess
import sys
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
BUILDER = REPO / "tools/analyze/build_thermal_passive_h2_multi_train_corrected_radiation_smoke.py"
OUT_DIR = REPO / "work_products/2026-07/2026-07-22/2026-07-22_thermal_passive_h2_multi_train_corrected_radiation_smoke"


def rows(path: Path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class PassiveH2MultiTrainCorrectedRadiationSmokeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        subprocess.run([sys.executable, str(BUILDER)], cwd=REPO, check=True, stdout=subprocess.PIPE, text=True)

    def test_summary_multi_case_no_admission(self) -> None:
        summary = json.loads((OUT_DIR / "summary.json").read_text(encoding="utf-8"))
        self.assertEqual(summary["case_rows"], 3)
        self.assertEqual(summary["case_family_rows"], 15)
        self.assertEqual(summary["setup_uq_train_labeled_cases"], 3)
        self.assertGreaterEqual(summary["external_bc_split_conflict_cases"], 1)
        self.assertGreater(summary["corrected_total_max_W"], 0.0)
        self.assertLess(summary["max_corrected_radiation_fraction_of_naive"], 0.1)
        self.assertEqual(summary["runtime_forbidden_inputs_released"], 0)
        for key in [
            "protected_scoring",
            "fitting_or_model_selection",
            "source_property_release",
            "qwall_release",
            "numeric_q_loss_release",
            "repair_execution",
            "candidate_freeze",
            "final_score_claim",
        ]:
            self.assertFalse(summary[key])

    def test_case_family_rows_cover_all_cases_and_families(self) -> None:
        data = rows(OUT_DIR / "case_family_corrected_radiation_operator.csv")
        self.assertEqual(len(data), 15)
        self.assertEqual({row["case_id"] for row in data}, {"salt_2", "salt_3", "salt_4"})
        self.assertEqual({row["source_family"] for row in data}, {"cooling_branch", "downcomer", "junction", "lower_leg", "upcomer"})
        for row in data:
            self.assertEqual(row["runtime_wallHeatFlux_used"], "False")
            self.assertEqual(row["runtime_validation_temperature_used"], "False")
            self.assertEqual(row["runtime_CFD_mdot_used"], "False")
            self.assertEqual(row["runtime_Qwall_used"], "False")
            self.assertEqual(row["numeric_q_loss_release"], "False")
            self.assertLess(float(row["corrected_q_rad_W"]), float(row["naive_inner_surface_q_rad_W"]))

    def test_split_and_potential_tables_are_guarded(self) -> None:
        split = rows(OUT_DIR / "split_scope_audit.csv")
        self.assertEqual(len(split), 3)
        self.assertTrue(all(row["setup_uq_train_only_label"] == "True" for row in split))
        self.assertTrue(all(row["protected_scoring_allowed"] == "False" for row in split))
        potential = rows(OUT_DIR / "training_potential_diagnostic.csv")
        self.assertEqual(len(potential), 3)
        self.assertTrue(any(row["assessment"] == "radiation_high_concern" for row in potential))
        self.assertTrue(all("no" in row["admission_status"].lower() or "closed" in row["admission_status"].lower() or "diagnostic" in row["admission_status"].lower() for row in potential))

    def test_manifest_and_guardrails(self) -> None:
        manifest = rows(OUT_DIR / "source_manifest.csv")
        self.assertTrue(manifest)
        self.assertTrue(all(row["exists"] == "True" for row in manifest))
        guardrails = rows(OUT_DIR / "no_mutation_guardrails.csv")
        self.assertTrue(all(row["status"] == "False" for row in guardrails))
        audit = rows(OUT_DIR / "runtime_input_audit.csv")
        self.assertEqual(len([row for row in audit if row["forbidden_input"] == "True" and row["released_to_runtime"] == "True"]), 0)


if __name__ == "__main__":
    unittest.main()
