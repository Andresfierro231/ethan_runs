#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import subprocess
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = REPO_ROOT / "work_products/2026-07/2026-07-22/2026-07-22_thermal_passive_h2_one_train_repair_preflight"
BUILDER = REPO_ROOT / "tools/analyze/build_thermal_passive_h2_one_train_repair_preflight.py"


def read_csv(path: Path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class PassiveH2OneTrainRepairPreflightTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        subprocess.run([sys.executable, str(BUILDER)], cwd=REPO_ROOT, check=True, stdout=subprocess.PIPE, text=True)

    def test_summary_is_dry_single_candidate_single_train(self) -> None:
        summary = json.loads((OUT_DIR / "summary.json").read_text(encoding="utf-8"))
        self.assertEqual(summary["candidate_id"], "PASSIVE-H2-CAND001")
        self.assertEqual(summary["train_case_id"], "salt_2")
        self.assertEqual(summary["scenario_id"], "salt_2__V00__nominal")
        self.assertTrue(summary["exactly_one_candidate_named"])
        self.assertTrue(summary["exactly_one_train_case_declared"])
        self.assertEqual(summary["passive_operator_family_rows"], 5)
        self.assertEqual(summary["source_backed_operator_rows"], 5)
        self.assertEqual(summary["runtime_setup_input_allowed_rows"], 5)
        self.assertEqual(summary["q_loss_operator_admissible_rows"], 5)
        self.assertEqual(summary["dry_preflight_gate_pass_rows"], summary["dry_preflight_gate_total_rows"])
        self.assertFalse(summary["scheduler_action"])
        self.assertFalse(summary["solver_or_sampler_launch"])
        self.assertFalse(summary["source_property_release"])
        self.assertFalse(summary["qwall_release"])
        self.assertFalse(summary["numeric_q_loss_release"])
        self.assertFalse(summary["repair_run"])
        self.assertFalse(summary["candidate_freeze"])
        self.assertFalse(summary["final_score_claim"])

    def test_candidate_case_contract_locks_protected_rows(self) -> None:
        rows = read_csv(OUT_DIR / "predeclared_candidate_case_contract.csv")
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row["candidate_id"], "PASSIVE-H2-CAND001")
        self.assertEqual(row["train_case_id"], "salt_2")
        self.assertEqual(row["split_role"], "train")
        self.assertEqual(row["dry_preflight_only"], "True")
        self.assertEqual(row["execute_solve_this_row"], "False")
        self.assertEqual(row["scheduler_action_allowed_this_row"], "False")
        self.assertEqual(row["validation_rows_locked"], "True")
        self.assertEqual(row["holdout_rows_locked"], "True")
        self.assertEqual(row["external_test_rows_locked"], "True")

    def test_operator_terms_are_source_backed_without_releases(self) -> None:
        rows = read_csv(OUT_DIR / "passive_operator_term_contract.csv")
        self.assertEqual(len(rows), 5)
        self.assertTrue(all(row["source_basis_release_ready_now"] == "True" for row in rows))
        self.assertTrue(all(row["runtime_setup_input_allowed"] == "True" for row in rows))
        self.assertTrue(all(row["q_loss_operator_admissible"] == "True" for row in rows))
        self.assertTrue(all(row["numeric_q_loss_released"] == "False" for row in rows))
        self.assertTrue(all(row["source_property_release_allowed"] == "False" for row in rows))
        self.assertTrue(all(row["Qwall_release_allowed"] == "False" for row in rows))
        self.assertTrue(all(row["uses_realized_wallHeatFlux"] == "False" for row in rows))
        self.assertTrue(all(row["uses_validation_temperature"] == "False" for row in rows))
        self.assertTrue(all(row["uses_CFD_mdot"] == "False" for row in rows))
        self.assertTrue(all(row["uses_Qwall"] == "False" for row in rows))

    def test_runtime_audit_and_next_contract_preserve_no_fit_no_score(self) -> None:
        runtime_rows = read_csv(OUT_DIR / "runtime_input_legality_audit.csv")
        self.assertTrue(any(row["audit_item"] == "forbidden_runtime_fields" and row["status"] == "pass" for row in runtime_rows))
        self.assertTrue(any(row["audit_item"] == "global_multiplier" and "forbidden" in row["status"] for row in runtime_rows))
        next_rows = read_csv(OUT_DIR / "next_execution_contract.csv")
        joined = " ".join(row["contract"] for row in next_rows)
        self.assertIn("separate execution row", joined)
        self.assertIn("may not freeze", joined)
        self.assertIn("may not", joined)

    def test_source_manifest_and_guardrails_are_clean(self) -> None:
        manifest = read_csv(OUT_DIR / "source_manifest.csv")
        self.assertGreaterEqual(len(manifest), 12)
        self.assertTrue(all(row["exists"] == "True" for row in manifest))
        self.assertTrue(all(row["mutation_status"] == "read_only" for row in manifest))
        guardrails = read_csv(OUT_DIR / "no_mutation_guardrails.csv")
        self.assertTrue(all(row["status"] == "False" for row in guardrails))


if __name__ == "__main__":
    unittest.main()
