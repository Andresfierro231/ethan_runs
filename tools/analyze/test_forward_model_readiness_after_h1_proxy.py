"""Tests for build_forward_model_readiness_after_h1_proxy.py."""

from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path

from tools.analyze import build_forward_model_readiness_after_h1_proxy as readiness


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class ForwardModelReadinessAfterH1ProxyTests(unittest.TestCase):
    def build_tmp(self) -> Path:
        tmp = Path(tempfile.mkdtemp(prefix="forward_readiness_h1_"))
        readiness.build_package(tmp)
        return tmp

    def test_summary_is_not_final_forward_v1(self) -> None:
        out = self.build_tmp()
        summary = json.loads((out / "summary.json").read_text(encoding="utf-8"))
        self.assertEqual(summary["final_forward_v1_status"], "blocked_not_final")
        self.assertEqual(summary["h1_proxy_score_status"], "screen_only_not_final_forward_v1")
        self.assertFalse(summary["native_solver_outputs_mutated"])
        self.assertFalse(summary["external_fluid_modified"])

        readme = (out / "README.md").read_text(encoding="utf-8")
        self.assertIn("not a final\nforward-v1 score", readme)

    def test_split_discipline_is_locked_before_scores(self) -> None:
        out = self.build_tmp()
        rows = read_csv(out / "train_validation_holdout_guardrail.csv")
        roles = {row["case_id"]: row["split_role"] for row in rows}
        self.assertEqual(roles, {"salt_2": "train", "salt_3": "validation", "salt_4": "holdout"})
        self.assertEqual({row["fit_allowed"] for row in rows if row["case_id"] != "salt_2"}, {"no"})

    def test_h1_residual_rows_are_screen_only(self) -> None:
        out = self.build_tmp()
        rows = read_csv(out / "residual_attribution_after_h1_proxy.csv")
        self.assertEqual(len(rows), 6)
        self.assertTrue(all(row["score_status"] == "h1_proxy_screen_only_not_final_forward_v1" for row in rows))
        self.assertTrue(all(float(row["mdot_error_vs_cfd_kg_s"]) > 0.0 for row in rows))

    def test_final_forward_v1_blockers_are_explicit(self) -> None:
        out = self.build_tmp()
        blockers = {row["blocker_id"]: row for row in read_csv(out / "blockers_to_final_forward_v1.csv")}
        for blocker_id in {
            "localized_h1_not_implemented",
            "h1_proxy_mdot_still_overpredicts",
            "thermal_mesh_not_admitted",
            "predictive_hx_boundary_not_final",
            "sensor_map_partial",
        }:
            self.assertIn(blocker_id, blockers)
            self.assertIn("yes", blockers[blocker_id]["blocks_final_forward_v1"])

    def test_gate_table_carries_required_evidence(self) -> None:
        out = self.build_tmp()
        gates = {row["gate_id"]: row for row in read_csv(out / "input_contract_gate_readiness.csv")}
        self.assertEqual(gates["predictive_input_contract"]["gate_status"], "pass_0_violations")
        self.assertEqual(gates["train_validation_holdout_split"]["gate_status"], "locked")
        self.assertEqual(gates["solve_case_confirmation"]["gate_status"], "pass")
        self.assertIn("yes", gates["hydraulic_h1_proxy"]["blocks_final_forward_v1"])
        self.assertIn("yes", gates["thermal_mesh_gate"]["blocks_final_forward_v1"])


if __name__ == "__main__":
    unittest.main()
