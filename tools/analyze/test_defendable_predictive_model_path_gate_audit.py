#!/usr/bin/env python3
"""Tests for the defendable predictive-model path gate audit."""

from __future__ import annotations

import csv
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.analyze import build_defendable_predictive_model_path_gate_audit as builder  # noqa: E402


class DefendablePredictiveModelPathGateAuditTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        builder.main()
        cls.out = builder.OUT
        with (cls.out / "summary.json").open(encoding="utf-8") as handle:
            cls.summary = json.load(handle)

    def read_csv(self, name: str) -> list[dict[str, str]]:
        with (self.out / name).open(newline="", encoding="utf-8") as handle:
            return list(csv.DictReader(handle))

    def test_summary_distinguishes_prototype_from_defendable_prediction(self) -> None:
        self.assertEqual(
            self.summary["decision"],
            "defendable_predictive_model_not_yet_available_path_now_explicit",
        )
        self.assertIs(self.summary["working_prototype_exists_now"], True)
        self.assertIs(self.summary["defendable_predictive_model_exists_now"], False)
        self.assertEqual(self.summary["candidate_to_carry_forward"], "P1D-BULK-CV-H2-CAND001")
        self.assertGreaterEqual(self.summary["blocking_gates"], 3)
        self.assertEqual(
            self.summary["shortest_path_next_action"],
            "claim PASSIVE-H2 Salt3/Salt4 diagnostic runtime-smoke row",
        )

    def test_release_score_and_freeze_guardrails_are_closed(self) -> None:
        for key in [
            "source_property_release",
            "Qwall_release",
            "numeric_q_loss_release",
            "validation_holdout_external_scoring",
            "protected_scoring",
            "fitting_or_model_selection",
            "coefficient_admission",
            "candidate_freeze",
            "final_score_claim",
            "hidden_multiplier",
            "residual_absorbed_into_internal_Nu",
            "endpoint_proxy_substitution",
            "runtime_leakage_relaxation",
        ]:
            self.assertIs(self.summary[key], False, key)

    def test_gate_matrix_has_passes_and_blockers(self) -> None:
        rows = self.read_csv("defendability_gate_matrix.csv")
        gates = {row["gate"]: row for row in rows}
        self.assertEqual(gates["working_no_fit_prototype"]["pass_now"], "True")
        self.assertEqual(gates["PASSIVE_H2_runtime_support"]["pass_now"], "True")
        self.assertEqual(gates["candidate_source_property_release"]["pass_now"], "False")
        self.assertEqual(gates["S13_endpoint_masks_and_open_CV_residual"]["pass_now"], "False")
        self.assertEqual(gates["freeze_exactly_one_candidate"]["pass_now"], "False")
        self.assertIn("15/15", gates["PASSIVE_H2_subspan_and_same_QOI_UQ"]["evidence"])
        self.assertIn("6/6", gates["PASSIVE_H2_subspan_and_same_QOI_UQ"]["evidence"])

    def test_minimum_evidence_chain_and_action_queue_are_ordered(self) -> None:
        chain = self.read_csv("minimum_evidence_chain.csv")
        self.assertEqual([row["rank"] for row in chain], ["1", "2", "3", "4", "5"])
        actions = self.read_csv("next_action_queue.csv")
        self.assertGreaterEqual(len(actions), 5)
        self.assertEqual(actions[0]["action"], "claim PASSIVE-H2 Salt3/Salt4 diagnostic runtime-smoke row")
        self.assertEqual(actions[1]["action"], "claim exact same-QOI runtime UQ rows for PASSIVE-H2")
        self.assertTrue(all(row["can_launch_from_audit"] == "False" for row in actions))

    def test_split_claim_contract_keeps_protected_rows_unused(self) -> None:
        rows = self.read_csv("split_claim_contract.csv")
        by_split = {row["split"]: row for row in rows}
        self.assertEqual(by_split["train_support"]["used_by_this_audit"], "True")
        for split in ["validation", "holdout", "external_test"]:
            self.assertEqual(by_split[split]["used_by_this_audit"], "False")
            self.assertIn("none", by_split[split]["claim_allowed_now"])
        self.assertIs(self.summary["validation_claims_used"], False)
        self.assertIs(self.summary["holdout_claims_used"], False)
        self.assertIs(self.summary["external_test_claims_used"], False)

    def test_freeze_protocol_is_pre_then_freeze_then_score(self) -> None:
        rows = self.read_csv("freeze_and_score_protocol.csv")
        self.assertEqual([row["phase"] for row in rows], ["pre_freeze", "freeze", "post_freeze_score"])
        self.assertIn("exactly one candidate", rows[0]["required"])
        self.assertIn("frozen candidate manifest", rows[1]["required"])
        self.assertIn("protected score", rows[2]["required"])


if __name__ == "__main__":
    unittest.main()
