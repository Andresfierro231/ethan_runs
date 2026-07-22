#!/usr/bin/env python3
"""Checks for the MF09 recirculating-upcomer thermal alternatives gate."""

from __future__ import annotations

import csv
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.analyze import build_mf09_recirculating_upcomer_thermal_model_alternatives as builder


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class MF09RecirculatingUpcomerAlternativesTests(unittest.TestCase):
    def test_build_outputs_current_gate_and_docs(self) -> None:
        summary = builder.build()
        self.assertEqual(summary["task_id"], builder.TASK_ID)
        self.assertEqual(summary["decision"], "blocked_missing_mesh_gci_source_basis")
        self.assertEqual(summary["variant_rows"], 4)
        self.assertEqual(summary["heat_flow_case_rows"], 3)
        self.assertEqual(summary["energy_residual_contract_rows"], 3)
        self.assertEqual(summary["best_next_science_lane"], "MF09b_throughflow_plus_recirculation_exchange_cell_with_signed_wall_heat")
        self.assertEqual(summary["smoke_ready_variants"], 0)
        self.assertEqual(summary["admission_allowed_variants"], 0)
        self.assertEqual(summary["accepted_same_label_mesh_gci_qois"], 0)
        self.assertEqual(summary["source_property_conservation_release_ready_rows"], 0)
        self.assertEqual(summary["ordinary_internal_nu_fit_rows"], 0)
        self.assertEqual(summary["exchange_cell_fit_ready_rows"], 0)
        self.assertEqual(summary["onset_anchor_candidate_rows"], 0)
        self.assertFalse(summary["production_harvest_allowed"])
        self.assertFalse(summary["ordinary_upcomer_nu_fd_k_allowed"])
        self.assertFalse(summary["Qwall_or_source_property_release"])
        self.assertFalse(summary["source_side_relabel_as_Q_wall"])
        self.assertFalse(summary["coefficient_admission"])
        self.assertFalse(summary["s11_s12_s13_s15_s6_trigger"])
        self.assertFalse(summary["native_output_mutation"])
        self.assertFalse(summary["registry_or_admission_mutation"])
        self.assertFalse(summary["scheduler_action"])
        self.assertFalse(summary["solver_sampler_harvest_uq_launched"])
        self.assertFalse(summary["Fluid_or_external_repo_mutation"])
        self.assertEqual(summary["validation_holdout_external_rows_scored"], 0)
        self.assertFalse(summary["fitting_or_model_selection"])
        self.assertFalse(summary["residual_absorbed_into_internal_nu"])

        self.assertTrue((builder.OUT_DIR / "README.md").exists())
        self.assertTrue((builder.OUT_DIR / "summary.json").exists())
        self.assertTrue((builder.OUT_DIR / "heat_flow_match_case_diagnostics.csv").exists())
        self.assertTrue((builder.OUT_DIR / "energy_residual_bridge_contract.csv").exists())
        self.assertTrue((ROOT / f".agent/status/2026-07-22_{builder.TASK_ID}.md").exists())
        self.assertTrue((ROOT / ".agent/journal/2026-07-22/mf09-recirculating-upcomer-thermal-model-alternatives.md").exists())
        self.assertTrue((ROOT / "imports/2026-07-22_mf09_recirculating_upcomer_thermal_model_alternatives.json").exists())
        json.loads((builder.OUT_DIR / "summary.json").read_text(encoding="utf-8"))

    def test_variant_table_preserves_required_alternatives_and_blocks_admission(self) -> None:
        builder.build()
        rows = read_rows(builder.OUT_DIR / "variant_comparison_table.csv")
        self.assertEqual(len(rows), 4)
        by_id = {row["variant_id"]: row for row in rows}
        self.assertIn("MF09a_upcomer_excluded_guarded_single_stream_invalid", by_id)
        self.assertIn("MF09b_throughflow_plus_recirculation_exchange_cell_with_signed_wall_heat", by_id)
        self.assertIn("MF09c_two-zone_stratified_mixed-convection_upcomer", by_id)
        self.assertIn("MF09d_source-side_energy_residual_bridge", by_id)
        self.assertEqual(by_id["MF09a_upcomer_excluded_guarded_single_stream_invalid"]["decision"], "required_guardrail")
        self.assertEqual(
            by_id["MF09b_throughflow_plus_recirculation_exchange_cell_with_signed_wall_heat"]["decision"],
            "best_next_science_lane_but_blocked",
        )
        self.assertTrue(all(row["smoke_ready"] == "false" for row in rows))
        self.assertTrue(all(row["admission_allowed"] == "false" for row in rows))

    def test_qoi_and_production_gates_fail_closed(self) -> None:
        builder.build()
        qois = {row["qoi_label"]: row for row in read_rows(builder.OUT_DIR / "qoi_availability_and_uq_status.csv")}
        self.assertEqual(qois["Q_wall_W"]["same_label_mesh_gci_status"], "blocked_missing_same_label_mesh_family")
        self.assertEqual(qois["Q_source_side_net_static_bc_W"]["source_property_or_cp_status"], "blocked_missing_source_property_conservation")
        self.assertEqual(qois["cp_J_kg_K"]["direct_or_proxy_release_status"], "missing")
        self.assertTrue(all(row["production_harvest_allowed_now"] == "false" for row in qois.values()))
        self.assertTrue(all(row["admission_allowed_now"] == "false" for row in qois.values()))

        gates = {row["gate"]: row for row in read_rows(builder.OUT_DIR / "production_and_admission_gate.csv")}
        self.assertEqual(gates["ordinary_upcomer_Nu_fD_K"]["status"], "disabled")
        self.assertEqual(gates["exchange_cell_smoke"]["status"], "blocked_missing_mesh_gci_source_basis")
        self.assertEqual(gates["s11_s12_s13_s15_s6_trigger"]["status"], "not_triggered")
        self.assertTrue(all(row["pass"] == "false" for row in gates.values()))

    def test_heat_flow_match_and_energy_residual_contract_are_fail_closed(self) -> None:
        builder.build()
        heat_rows = read_rows(builder.OUT_DIR / "heat_flow_match_case_diagnostics.csv")
        self.assertEqual(len(heat_rows), 3)
        salt2 = [row for row in heat_rows if row["case_id"] == "salt_2"][0]
        self.assertAlmostEqual(float(salt2["Q_wall_W"]), 23.1161370708, places=10)
        self.assertAlmostEqual(float(salt2["Q_source_side_net_static_bc_W"]), 166.349260094, places=9)
        self.assertGreater(float(salt2["source_minus_qwall_W"]), 100.0)
        self.assertGreater(float(salt2["minimum_cp_required_J_kg_K"]), 1.0e6)
        self.assertTrue(
            all(row["heat_flow_match_status"] == "not_physical_match_with_current_exchange_scale" for row in heat_rows)
        )
        self.assertTrue(
            all(row["admissible_action_now"] == "diagnose_and_define_residual_contract_only" for row in heat_rows)
        )

        contract_rows = read_rows(builder.OUT_DIR / "energy_residual_bridge_contract.csv")
        self.assertEqual(len(contract_rows), 3)
        formulas = {row["residual_label"]: row["formula"] for row in contract_rows}
        self.assertIn("Q_wall_W - mdot_exchange_positive_outward_kg_s", formulas["E_wall_exchange_resid_W"])
        self.assertIn(
            "Q_source_side_net_static_bc_W - mdot_exchange_positive_outward_kg_s",
            formulas["E_source_exchange_resid_W"],
        )
        self.assertTrue(
            all("recirculation cell to main-throughflow cell" in row["normal_convention"] for row in contract_rows)
        )
        self.assertTrue(
            all(
                "not to fit" in row["claim_boundary"]
                or "not coefficient" in row["claim_boundary"]
                or "do not absorb into internal Nu" in row["claim_boundary"]
                for row in contract_rows
            )
        )


if __name__ == "__main__":
    unittest.main()
