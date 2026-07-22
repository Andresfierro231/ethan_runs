#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import subprocess
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = REPO_ROOT / "work_products/2026-07/2026-07-22/2026-07-22_thermal_passive_h2_source_backed_basis_table"
BUILDER = REPO_ROOT / "tools/analyze/build_thermal_passive_h2_source_backed_basis_table.py"


def read_csv(path: Path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class PassiveH2SourceBackedBasisTableTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        subprocess.run([sys.executable, str(BUILDER)], cwd=REPO_ROOT, check=True, stdout=subprocess.PIPE, text=True)

    def test_summary_releases_setup_basis_only(self) -> None:
        summary = json.loads((OUT_DIR / "summary.json").read_text(encoding="utf-8"))
        self.assertEqual(summary["passive_family_rows"], 5)
        self.assertGreater(summary["source_basis_release_ready_rows"], 0)
        self.assertEqual(summary["source_basis_release_ready_rows"], 5)
        self.assertEqual(summary["runtime_setup_input_allowed_next_row_rows"], 5)
        self.assertEqual(summary["source_property_release_allowed_rows"], 0)
        self.assertEqual(summary["Qwall_release_allowed_rows"], 0)
        self.assertEqual(summary["numeric_q_loss_release_allowed_rows"], 0)
        self.assertEqual(summary["repair_run_allowed_rows_this_task"], 0)
        self.assertEqual(summary["candidate_freeze_allowed_rows"], 0)
        self.assertEqual(summary["forbidden_runtime_inputs_released_rows"], 0)
        self.assertFalse(summary["source_property_release"])
        self.assertFalse(summary["qwall_release"])
        self.assertFalse(summary["repair_run"])
        self.assertFalse(summary["candidate_freeze"])
        self.assertFalse(summary["protected_scoring"])

    def test_family_rows_have_source_backed_setup_evidence(self) -> None:
        rows = read_csv(OUT_DIR / "source_backed_passive_h2_basis_table.csv")
        self.assertEqual(len(rows), 5)
        self.assertTrue(all(row["basis_class"] == "setup_dictionary_passive_external_boundary_basis" for row in rows))
        self.assertTrue(all(row["source_basis_release_ready_now"] == "True" for row in rows))
        self.assertTrue(all(row["runtime_forbidden_inputs_released"] == "False" for row in rows))
        self.assertTrue(all("source_backed_by_boundary_dictionary" in row["geometry_area_trace_status"] for row in rows))
        self.assertTrue(all("source_backed_by_rcExternalTemperature" in row["room_surroundings_ambient_source_status"] for row in rows))
        self.assertTrue(all("source_backed_by_thicknessLayers" in row["insulation_exposure_status"] for row in rows))
        self.assertTrue(all("setup_dictionary_h_ext_replaces" in row["h_correlation_literature_provenance_status"] for row in rows))
        self.assertTrue(all("replaced_by_setup" in row["wallHeatFlux_derived_passive_h_replacement_status"] for row in rows))

    def test_q_loss_and_forbidden_inputs_stay_closed(self) -> None:
        q_rows = read_csv(OUT_DIR / "q_loss_operator_contract.csv")
        self.assertEqual(len(q_rows), 5)
        self.assertTrue(all(row["numeric_q_loss_released"] == "False" for row in q_rows))
        self.assertTrue(all(row["phase_e_diagnostic_state_used"] == "False" for row in q_rows))
        self.assertTrue(all(row["realized_wallHeatFlux_used"] == "False" for row in q_rows))
        audit = {row["input_or_claim"]: row["released_to_runtime"] for row in read_csv(OUT_DIR / "forbidden_runtime_input_audit.csv")}
        for key in ["wallHeatFlux", "validation_temperature", "CFD_mdot", "Qwall", "source_property"]:
            self.assertEqual(audit[key], "False")

    def test_repair_preflight_is_next_row_only(self) -> None:
        rows = read_csv(OUT_DIR / "candidate_repair_freeze_preflight.csv")
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row["one_train_passive_h2_repair_preflight_claimable_next"], "True")
        self.assertEqual(row["repair_run_allowed_this_row"], "False")
        self.assertEqual(row["candidate_freeze_allowed_now"], "False")
        self.assertEqual(row["global_fitted_multiplier_allowed"], "False")
        self.assertEqual(row["residual_absorption_into_internal_Nu_allowed"], "False")
        self.assertEqual(row["validation_or_holdout_scoring_before_freeze_allowed"], "False")


if __name__ == "__main__":
    unittest.main()
