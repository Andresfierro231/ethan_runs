import csv
import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_passive_h2_salt1_junction_setup_row_recovery_background"
SCRIPT = ROOT / "tools/analyze/build_passive_h2_salt1_junction_setup_row_recovery_background.py"


def rows(name: str) -> list[dict[str, str]]:
    with (OUT / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class PassiveH2Salt1JunctionRecoveryTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        subprocess.run([sys.executable, str(SCRIPT)], cwd=ROOT, check=True, stdout=subprocess.PIPE, text=True)

    def test_summary_recovers_setup_but_does_not_release(self) -> None:
        summary = json.loads((OUT / "summary.json").read_text(encoding="utf-8"))
        self.assertEqual(summary["decision"], "salt1_junction_setup_row_recovered_background_runtime_smoke_prepared_no_release")
        self.assertEqual(summary["junction_required_patch_rows"], 18)
        self.assertEqual(summary["junction_setup_patch_rows"], 18)
        self.assertEqual(summary["junction_area_patch_rows"], 18)
        self.assertEqual(summary["operator_rows"], 5)
        self.assertTrue(summary["five_family_operator_ready"])
        self.assertIn(
            summary["runtime_status"],
            {
                "not_submitted",
                "submitted_pending_or_running",
                "replacement_submitted_pending_or_running_after_failed_partial_output",
                "partial_outputs_present_no_fluid_summary",
                "failed_after_partial_outputs_schema_mismatch",
                "runtime_radiation_smoke_complete_no_release_no_score",
            },
        )
        self.assertEqual(summary["source_property_release_rows"], 0)
        self.assertEqual(summary["freeze_allowed_rows"], 0)
        self.assertFalse(summary["candidate_freeze"])

    def test_junction_patch_inventory_is_complete_setup_geometry(self) -> None:
        inventory = rows("salt1_junction_patch_inventory.csv")
        self.assertEqual(len(inventory), 18)
        self.assertTrue(all(row["setup_boundary_present"] == "true" for row in inventory))
        self.assertTrue(all(row["area_basis_present"] == "true" for row in inventory))
        self.assertTrue(all(row["h_present"] == "true" for row in inventory))
        self.assertTrue(all(float(row["area_m2"]) > 0.0 for row in inventory))
        self.assertTrue(all(row["admissibility_role"] == "setup_geometry_inventory_only" for row in inventory))

    def test_operator_csv_has_five_train_families_and_runtime_guard_columns(self) -> None:
        operators = rows("salt1_five_family_operator_rows_for_fluid.csv")
        self.assertEqual({row["source_family"] for row in operators}, {"cooling_branch", "downcomer", "junction", "lower_leg", "upcomer"})
        self.assertTrue(all(row["external_bc_split_role"] == "train" for row in operators))
        self.assertTrue(all(row["setup_recovery_status"] == "recovered_setup_candidate" for row in operators))
        self.assertTrue(all(float(row["area_m2"]) > 0.0 for row in operators))
        self.assertTrue(all(float(row["hA_W_K"]) > 0.0 for row in operators))
        self.assertTrue(all(row["runtime_wallHeatFlux_used"] == "false" for row in operators))
        self.assertTrue(all(row["source_property_release"] == "false" for row in operators))

    def test_recovery_gate_allows_only_diagnostic_smoke(self) -> None:
        gates = {row["gate"]: row for row in rows("salt1_junction_recovery_gate.csv")}
        self.assertEqual(gates["salt1_junction_patch_setup_inventory"]["status"], "pass")
        self.assertEqual(gates["salt1_junction_area_basis_inventory"]["status"], "pass")
        self.assertEqual(gates["five_family_operator_csv_candidate"]["status"], "pass_diagnostic")
        self.assertEqual(gates["five_family_operator_csv_candidate"]["runtime_smoke_allowed"], "true")
        self.assertEqual(gates["source_property_release"]["status"], "fail_closed")
        self.assertEqual(gates["source_property_release"]["runtime_smoke_allowed"], "false")

    def test_command_manifest_and_guardrails_are_non_release(self) -> None:
        commands = rows("command_manifest.csv")
        self.assertEqual(len(commands), 1)
        self.assertIn(commands[0]["status"], {"prepared_not_submitted", "submitted"})
        self.assertIn("passive_h2_radiation_runtime_smoke", commands[0]["command"])
        guardrails = rows("no_mutation_guardrails.csv")
        self.assertTrue(guardrails)
        self.assertTrue(all(row["value"] == "false" for row in guardrails))

    def test_partial_runtime_outputs_are_diagnostic_only_when_present(self) -> None:
        artifact_rows = rows("runtime_artifact_status.csv")
        self.assertEqual({row["artifact"] for row in artifact_rows}, {
            "runtime_smoke_summary.csv",
            "source_operator_rows_train_only.csv",
            "heat_ledger_delta.csv",
            "sensor_prediction_delta.csv",
            "segment_heat_ledger.csv",
            "runtime_input_audit.csv",
            "summary.json",
        })
        summary = json.loads((OUT / "summary.json").read_text(encoding="utf-8"))
        if summary["partial_runtime_summary_rows"]:
            partial = rows("partial_runtime_smoke_summary.csv")
            self.assertEqual(len(partial), summary["partial_runtime_summary_rows"])
            self.assertTrue(all(row["protected_target_used"] == "False" for row in partial))
            self.assertTrue(all(row["diagnostic_status"] == "partial_runtime_summary_retained_no_release_no_score" for row in partial))
        if summary["partial_heat_delta_rows"]:
            deltas = rows("partial_heat_delta_from_runtime_summary.csv")
            self.assertEqual(len(deltas), summary["partial_heat_delta_rows"])
            self.assertTrue(all(row["protected_target_used"] == "false" for row in deltas))
            self.assertTrue(all(row["target_basis"] == "no protected target available; target intentionally not used" for row in deltas))


if __name__ == "__main__":
    unittest.main()
