#!/usr/bin/env python3
"""Tests for the heat-loss upcomer exchange evidence-extraction contract."""

from __future__ import annotations

import csv
import unittest

from tools.analyze import build_heatloss_upcomer_exchange_evidence_extraction as build_contract


class HeatlossUpcomerExchangeEvidenceExtractionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.summary = build_contract.build()
        cls.contract = cls.read_csv("upcomer_exchange_extraction_contract.csv")
        cls.field_map = cls.read_csv("sampler_field_map.csv")
        cls.queue = cls.read_csv("case_time_window_queue.csv")
        cls.guards = cls.read_csv("no_admission_guardrail.csv")
        cls.handoff = cls.read_csv("next_agent_handoff.csv")

    @classmethod
    def read_csv(cls, name: str) -> list[dict[str, str]]:
        with (build_contract.OUT / name).open(newline="", encoding="utf-8") as handle:
            return list(csv.DictReader(handle))

    def test_mainline_case_time_queue_is_complete(self) -> None:
        self.assertEqual({row["case_id"] for row in self.queue}, {"salt_2", "salt_3", "salt_4"})
        self.assertEqual({row["time_window_s"] for row in self.queue}, {"7915", "7618", "10000"})
        self.assertTrue(all(row["launch_allowed_from_this_package"] == "false" for row in self.queue))

    def test_contract_has_every_required_group_for_each_case(self) -> None:
        expected_groups = {
            "local_reverse_flow",
            "recirculation_volume",
            "exchange_rate",
            "thermal_state",
            "pressure_basis",
            "wall_source_terms",
            "same_qoi_uq",
        }
        self.assertEqual({row["field_group"] for row in self.field_map}, expected_groups)
        self.assertEqual(len(self.contract), 3 * len(expected_groups))
        for case_id in {"salt_2", "salt_3", "salt_4"}:
            self.assertEqual(
                {row["required_field_group"] for row in self.contract if row["case_id"] == case_id},
                expected_groups,
            )

    def test_no_fit_score_or_internal_nu_residual_absorption(self) -> None:
        self.assertTrue(all(row["fit_allowed_now"] == "false" for row in self.contract))
        self.assertTrue(all(row["score_allowed_now"] == "false" for row in self.contract))
        self.assertTrue(
            all(row["residual_policy"] == "do_not_hide_heat_residual_in_internal_Nu" for row in self.contract)
        )
        self.assertFalse(self.summary["residual_absorbed_into_internal_Nu"])

    def test_sampler_gaps_are_explicit(self) -> None:
        by_group = {row["field_group"]: row for row in self.field_map}
        self.assertIn("partial_existing_tool_support", by_group["local_reverse_flow"]["existing_tool_support"])
        for group in ("recirculation_volume", "exchange_rate", "thermal_state", "pressure_basis", "same_qoi_uq"):
            self.assertIn("not_implemented", by_group[group]["existing_tool_support"])
            self.assertNotEqual(by_group[group]["sampler_gap"], "")

    def test_wall_source_terms_do_not_open_internal_nu(self) -> None:
        by_group = {row["field_group"]: row for row in self.field_map}
        self.assertIn("do not absorb residual into internal Nu", by_group["wall_source_terms"]["blocked_behavior"])
        rows = [row for row in self.contract if row["required_field_group"] == "wall_source_terms"]
        self.assertTrue(all(row["admission_use"] == "diagnostic_only" for row in rows))

    def test_guardrails_and_summary_have_no_side_effect_claims(self) -> None:
        guard_ids = {row["guard_id"] for row in self.guards}
        self.assertIn("internal_Nu_residual", guard_ids)
        for key in (
            "native_output_mutation",
            "registry_mutation",
            "scheduler_mutation",
            "solver_or_postprocessing_or_sampler_launched",
            "fluid_edit",
            "external_repo_edit",
            "fitting_or_model_selection",
            "closure_admission_change",
            "blocker_register_change",
            "generated_index_refresh",
        ):
            self.assertFalse(self.summary[key])

    def test_handoff_is_ordered_to_sampler_then_uq_then_rescore(self) -> None:
        self.assertEqual(
            [row["work_package"] for row in self.handoff],
            [
                "extend_upcomer_sampler_contract",
                "compute_node_sampler_execution",
                "same_qoi_uq_pairing",
                "phase4b_exchange_readiness_rescore",
            ],
        )


if __name__ == "__main__":
    unittest.main()
