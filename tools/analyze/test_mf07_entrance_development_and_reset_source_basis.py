#!/usr/bin/env python3.11
"""Tests for the MF07 entrance/development/reset source-basis gate."""

from __future__ import annotations

import csv
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.analyze.build_mf07_entrance_development_and_reset_source_basis import OUT, build


def rows(name: str) -> list[dict[str, str]]:
    with (OUT / name).open(newline="") as f:
        return list(csv.DictReader(f))


class Mf07EntranceDevelopmentResetSourceBasisTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        build()

    def test_summary_is_diagnostic_only(self) -> None:
        summary = json.loads((OUT / "summary.json").read_text())
        self.assertEqual(summary["decision"], "diagnostic_only")
        self.assertFalse(summary["ready_for_train_only_smoke"])
        self.assertFalse(summary["coefficient_admission"])
        self.assertFalse(summary["source_property_release"])
        self.assertFalse(summary["final_score"])
        self.assertGreater(summary["tp_residual_join_rows"], 0)
        self.assertGreater(summary["thermal_development_indicated_rows"], 0)
        self.assertGreater(summary["single_stream_precheck_rows"], 0)
        self.assertLess(summary["max_abs_wall_core_over_D2_train_TP_offset"], 0.05)
        self.assertEqual(summary["bulk_to_tp_gate_rows"], 5)
        self.assertEqual(summary["next_analysis_plan_rows"], 4)

    def test_predeclared_variants_present_and_not_smoke_ready(self) -> None:
        variants = {r["variant_id"]: r for r in rows("variant_direction_of_effect.csv")}
        self.assertIn("MF07a_hydraulic_reset_development_only", variants)
        self.assertIn("MF07b_thermal_graetz_development_only", variants)
        self.assertIn("MF07c_combined_reset_plus_thermal_graetz_with_recirc_guard", variants)
        self.assertTrue(all(r["train_only_smoke_ready"] == "False" for r in variants.values()))

    def test_tp_join_carries_reset_graetz_and_direction_labels(self) -> None:
        joined = rows("tp_residual_reset_graetz_join.csv")
        self.assertEqual({r["split_group"] for r in joined}, {"train"})
        self.assertTrue(any(r["tested_model_form_id"] == "M3_as_is" for r in joined))
        self.assertTrue(any(r["tested_model_form_id"].startswith("D2_") for r in joined))
        self.assertTrue(any(r["mean_Gz"] for r in joined))
        self.assertTrue(any(r["L_over_D_from_reset"] for r in joined))
        self.assertTrue(all(r["use_boundary"] == "diagnostic_residual_shape_only_no_fit_no_protected_scoring" for r in joined))
        m3_rows = [r for r in joined if r["tested_model_form_id"] == "M3_as_is"]
        self.assertTrue(all(float(r["signed_error_K"]) < 0 for r in m3_rows))

    def test_s13_bridge_is_diagnostic_not_admitted(self) -> None:
        bridge = rows("s13_wall_core_tp_bridge_matrix.csv")
        self.assertTrue(any(r["bridge_item"] == "Q_wall_W" for r in bridge))
        self.assertTrue(any(r["bridge_item"] == "wall_core_bulk_temperature_contrast_K" for r in bridge))
        self.assertTrue(all(r["admission_allowed_now"] in {"false", "False"} for r in bridge))
        ratios = [float(r["abs_wall_core_over_D2_train_TP_offset"]) for r in bridge if r["abs_wall_core_over_D2_train_TP_offset"]]
        self.assertTrue(ratios)
        self.assertLess(max(ratios), 0.05)

    def test_bulk_to_tp_gate_and_next_plan_are_fail_closed(self) -> None:
        gates = rows("bulk_to_tp_existence_proof_gate.csv")
        self.assertEqual(len(gates), 5)
        self.assertTrue(all(r["release_allowed"] == "False" for r in gates))
        self.assertTrue(any(r["status"] == "fail_full_ownership" for r in gates))
        plan = rows("next_analysis_plan.csv")
        self.assertEqual(plan[0]["task"], "MF08 signed heat-path thermal-development source basis")
        self.assertEqual(plan[1]["task"], "MF09 recirculating upcomer thermal alternatives")
        self.assertEqual(plan[2]["task"], "MF10 train/support-only predeclared bakeoff")

    def test_no_mutation_guardrails(self) -> None:
        guardrails = {r["guardrail"]: r["value"] for r in rows("no_mutation_guardrails.csv")}
        self.assertEqual(guardrails["native_output_mutation"], "False")
        self.assertEqual(guardrails["scheduler_action"], "False")
        self.assertEqual(guardrails["fitting_or_model_selection"], "False")
        self.assertEqual(guardrails["residual_absorbed_into_internal_nu"], "False")


if __name__ == "__main__":
    unittest.main()
