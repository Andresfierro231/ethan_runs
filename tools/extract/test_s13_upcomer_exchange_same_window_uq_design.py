#!/usr/bin/env python3
"""Tests for the S13 upcomer exchange same-window UQ design package."""

from __future__ import annotations

import csv
import unittest

from tools.extract import build_s13_upcomer_exchange_same_window_uq_design as design


class S13UpcomerExchangeSameWindowUqDesignTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.summary = design.build()
        cls.acceptance = cls.read_csv("uq_acceptance_contract.csv")
        cls.neighbors = cls.read_csv("neighbor_window_requirements.csv")
        cls.mesh = cls.read_csv("mesh_gci_requirements.csv")
        cls.decisions = cls.read_csv("qoi_release_decision.csv")
        cls.guards = cls.read_csv("no_mutation_guardrails.csv")

    @classmethod
    def read_csv(cls, name: str) -> list[dict[str, str]]:
        with (design.OUT / name).open(newline="", encoding="utf-8") as handle:
            return list(csv.DictReader(handle))

    def test_covers_three_target_exchange_qois(self) -> None:
        self.assertEqual({row["qoi_name"] for row in self.acceptance}, set(design.TARGET_QOIS))
        self.assertEqual(len(self.acceptance), 3)

    def test_all_target_qois_are_fail_closed(self) -> None:
        self.assertTrue(all(row["s13_acceptance_status"] == "blocked" for row in self.acceptance))
        self.assertTrue(all(row["s11_reviewable_now"] == "false" for row in self.acceptance))
        self.assertTrue(all(row["sampler_or_harvest_allowed_now"] == "false" for row in self.acceptance))

    def test_neighbor_and_mesh_requirements_remain_missing(self) -> None:
        self.assertTrue(all("missing" in row["current_neighbor_status"] or "blocked" in row["current_neighbor_status"] for row in self.neighbors))
        self.assertTrue(all(row["status"] == "blocked" for row in self.mesh))
        self.assertTrue(all(row["accepted_gci_rows"] == "0" for row in self.mesh))

    def test_support_gate_decisions_do_not_release_candidates(self) -> None:
        self.assertEqual(len(self.decisions), len(design.TARGET_QOIS) + len(design.SUPPORT_GATES))
        self.assertTrue(all(row["release_allowed_now"] == "false" for row in self.decisions))
        self.assertTrue(all(row["s11_reviewable_candidate_count"] == "0" for row in self.decisions))

    def test_summary_and_guardrails_have_no_side_effects(self) -> None:
        self.assertFalse(self.summary["uq_release_allowed"])
        self.assertFalse(self.summary["sampler_or_harvest_allowed"])
        self.assertEqual(self.summary["s11_reviewable_candidate_count"], 0)
        self.assertTrue(all(row["observed"] == "false" for row in self.guards))


if __name__ == "__main__":
    unittest.main()
