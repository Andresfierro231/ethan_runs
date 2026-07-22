#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import subprocess
import sys
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
OUT_DIR = REPO / "work_products/2026-07/2026-07-22/2026-07-22_thermal_passive_h2_runtime_operator_smoke_uq_gate"
BUILDER = REPO / "tools/analyze/build_thermal_passive_h2_runtime_operator_smoke_uq_gate.py"


def read_csv(path: Path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class PassiveH2RuntimeOperatorSmokeUQGateTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        subprocess.run([sys.executable, str(BUILDER)], cwd=REPO, check=True, stdout=subprocess.PIPE, text=True)

    def test_summary_is_diagnostic_no_release(self) -> None:
        summary = json.loads((OUT_DIR / "summary.json").read_text(encoding="utf-8"))
        self.assertEqual(summary["candidate_id"], "PASSIVE-H2-CAND001")
        self.assertEqual(summary["train_case_id"], "salt_2")
        self.assertEqual(summary["operator_family_rows"], 5)
        self.assertEqual(summary["wall_state_mapping_rows"], 5)
        self.assertEqual(summary["sensitivity_scenario_rows"], 8)
        self.assertGreater(summary["diagnostic_nominal_q_total_W"], 0.0)
        self.assertGreater(summary["largest_abs_sensitivity_delta_W"], 0.0)
        self.assertGreater(summary["max_abs_delta_mdot_model_kg_s"], 0.0)
        self.assertGreater(summary["max_abs_delta_qambient_total_W"], 0.0)
        self.assertGreater(summary["max_abs_TP_delta_K"], 0.0)
        self.assertGreater(summary["max_abs_TW_delta_K"], 0.0)
        self.assertFalse(summary["numeric_passive_heat_loss_release"])
        self.assertFalse(summary["source_property_release"])
        self.assertFalse(summary["qwall_release"])
        self.assertFalse(summary["repair_execution"])
        self.assertFalse(summary["candidate_freeze"])
        self.assertFalse(summary["protected_scoring"])
        self.assertFalse(summary["final_score_claim"])

    def test_operator_rows_use_no_forbidden_runtime_inputs(self) -> None:
        rows = read_csv(OUT_DIR / "passive_operator_family_smoke.csv")
        self.assertEqual(len(rows), 40)
        self.assertEqual({row["source_family"] for row in rows}, {"cooling_branch", "downcomer", "junction", "lower_leg", "upcomer"})
        for row in rows:
            self.assertEqual(row["numeric_q_loss_release"], "False")
            self.assertEqual(row["runtime_wallHeatFlux_used"], "False")
            self.assertEqual(row["runtime_validation_temperature_used"], "False")
            self.assertEqual(row["runtime_CFD_mdot_used"], "False")
            self.assertEqual(row["runtime_Qwall_used"], "False")
            self.assertEqual(row["runtime_imposed_cooler_duty_used"], "False")

    def test_projection_and_ledger_are_support_only(self) -> None:
        projection = read_csv(OUT_DIR / "tp_tw_projection_sensitivity_summary.csv")
        self.assertTrue(projection)
        self.assertTrue(all(row["fit_allowed"] == "False" for row in projection))
        self.assertTrue(all(row["model_selection_allowed"] == "False" for row in projection))
        ledger = read_csv(OUT_DIR / "heat_ledger_sensitivity_summary.csv")
        self.assertEqual(len(ledger), 8)
        self.assertTrue(all(row["heat_ledger_release"] == "False" for row in ledger))
        self.assertTrue(all(row["residual_absorption_into_internal_Nu"] == "False" for row in ledger))
        combined = read_csv(OUT_DIR / "mdot_tp_tw_heat_operator_sensitivity.csv")
        self.assertEqual(len(combined), 11)
        self.assertTrue(all(row["runtime_wallHeatFlux_used"] == "False" for row in combined))
        self.assertTrue(all(row["runtime_observed_temperature_used"] == "False" for row in combined))
        self.assertTrue(all(row["source_property_release"] == "False" for row in combined))
        self.assertTrue(any(row["passive_operator_local_scenario_id"] == "radiation_off" for row in combined))
        self.assertTrue((OUT_DIR / "scientific_findings_and_caveats.csv").exists())

    def test_decision_gate_manifest_and_guardrails(self) -> None:
        gates = read_csv(OUT_DIR / "decision_gate.csv")
        self.assertEqual({row["gate"] for row in gates}, {"runtime_input_audit", "operator_smoke", "tp_tw_projection_sensitivity", "numeric_q_loss_release", "admission_or_freeze"})
        manifest = read_csv(OUT_DIR / "source_manifest.csv")
        self.assertTrue(all(row["exists"] == "True" for row in manifest))
        self.assertTrue(all(row["mutation_status"] == "read_only" for row in manifest))
        guardrails = read_csv(OUT_DIR / "no_mutation_guardrails.csv")
        self.assertTrue(all(row["status"] == "False" for row in guardrails))
        self.assertTrue((OUT_DIR / "README.md").exists())
        self.assertTrue((OUT_DIR / "passive_h2_runtime_operator_family_scenario.csv").exists())
        self.assertTrue((OUT_DIR / "passive_h2_runtime_operator_scenario_summary.csv").exists())
        self.assertTrue((OUT_DIR / "passive_h2_runtime_operator_uq_sensitivity.csv").exists())


if __name__ == "__main__":
    unittest.main()
