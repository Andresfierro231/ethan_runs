#!/usr/bin/env python3
"""Tests for the upcomer exchange terminal/source readiness package."""

from __future__ import annotations

import csv
import unittest

from tools.analyze import build_upcomer_exchange_terminal_source_readiness as readiness


class UpcomerExchangeTerminalSourceReadinessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.summary = readiness.build()
        cls.sources = cls.read_csv("terminal_source_family_matrix.csv")
        cls.qois = cls.read_csv("required_exchange_qoi_coverage.csv")
        cls.decisions = cls.read_csv("harvest_vs_sampler_decision.csv")
        cls.guards = cls.read_csv("duplicate_sampler_guard.csv")
        cls.scheduler = cls.read_csv("read_only_scheduler_observation.csv")

    @classmethod
    def read_csv(cls, name: str) -> list[dict[str, str]]:
        with (readiness.OUT / name).open(newline="", encoding="utf-8") as handle:
            return list(csv.DictReader(handle))

    def test_summary_keeps_all_launch_and_release_gates_closed(self) -> None:
        self.assertFalse(self.summary["terminal_harvest_ready_now"])
        self.assertFalse(self.summary["scoped_sampler_needed_now"])
        self.assertFalse(self.summary["phase4b_ready"])
        self.assertEqual(self.summary["phase5_trigger"], "not_triggered")
        self.assertFalse(self.summary["phase4b_rescore"])

    def test_expected_source_families_are_present(self) -> None:
        families = {row["source_family"] for row in self.sources}
        self.assertEqual(
            families,
            {
                "latest_corrected_Q_live_continuation",
                "high_heat_terminal_gated",
                "pm10_pressure_only_target",
                "two_tap_endpoint_recirc",
                "upcomer_matched_plane_diagnostic_proxy",
            },
        )

    def test_live_sources_are_wait_terminal_not_harvest_ready(self) -> None:
        by_family = {row["source_family"]: row for row in self.sources}
        for family in ("latest_corrected_Q_live_continuation", "high_heat_terminal_gated"):
            self.assertEqual(by_family[family]["source_decision"], "wait_terminal_no_duplicate_sampler")
            self.assertEqual(by_family[family]["can_provide_full_exchange_qois_now"], "false")
            self.assertIn("live_running", by_family[family]["current_terminal_state"])

    def test_required_qois_are_not_phase4b_usable(self) -> None:
        self.assertEqual(len(self.qois), len(readiness.REQUIRED_QOIS) * len(self.sources))
        self.assertTrue(all(row["usable_for_phase4b_now"] == "false" for row in self.qois))
        corrected = [
            row
            for row in self.qois
            if row["source_family"] == "latest_corrected_Q_live_continuation"
            and row["required_qoi"] in {"V_recirc", "mdot_exchange", "tau_recirc"}
        ]
        self.assertTrue(all(row["requires_sampler_or_harvest"] == "true" for row in corrected))

    def test_diagnostic_proxy_keeps_only_diagnostic_qois(self) -> None:
        diagnostic = {
            row["required_qoi"]: row
            for row in self.qois
            if row["source_family"] == "upcomer_matched_plane_diagnostic_proxy"
        }
        self.assertEqual(diagnostic["RAF_RMF_SVF"]["current_coverage_status"], "available_existing_diagnostic")
        self.assertEqual(diagnostic["energy_residual"]["current_coverage_status"], "available_existing_diagnostic")
        self.assertEqual(diagnostic["V_recirc"]["current_coverage_status"], "missing_exchange_state")

    def test_harvest_sampler_phase4b_and_phase5_decisions_are_closed(self) -> None:
        decisions = {row["decision_id"]: row for row in self.decisions}
        self.assertEqual(decisions["terminal_harvest_ready_now"]["status"], "false")
        self.assertEqual(decisions["scoped_sampler_needed_now"]["status"], "false")
        self.assertEqual(decisions["phase4b_rescore_ready"]["status"], "false")
        self.assertEqual(decisions["phase5_trigger"]["status"], "not_triggered")
        for row in self.decisions:
            self.assertEqual(row["admission_change"], "none")

    def test_duplicate_guards_cover_live_and_proxy_paths(self) -> None:
        guard_ids = {row["guard_id"] for row in self.guards}
        self.assertEqual(
            guard_ids,
            {
                "corrected_q_duplicate_sampler",
                "high_heat_duplicate_sampler",
                "diagnostic_proxy_refit_guard",
            },
        )

    def test_scheduler_observation_has_expected_live_and_superseded_jobs(self) -> None:
        by_job = {row["job_id"]: row for row in self.scheduler}
        self.assertEqual(by_job["3307441"]["observed_state"], "RUNNING")
        self.assertEqual(by_job["3299610"]["observed_state"], "RUNNING")
        self.assertEqual(by_job["3299620"]["observed_state"], "RUNNING")
        self.assertEqual(by_job["3295438"]["observed_state"], "COMPLETED")
        self.assertIn("superseded", by_job["3295438"]["readiness_effect"])

    def test_no_side_effect_claims(self) -> None:
        for key in (
            "native_output_mutation",
            "registry_mutation",
            "scheduler_mutation",
            "solver_or_postprocessing_or_sampler_or_harvest_launched",
            "fluid_edit",
            "external_repo_edit",
            "fitting_or_model_selection",
            "closure_admission_change",
            "blocker_register_change",
        ):
            self.assertFalse(self.summary[key])


if __name__ == "__main__":
    unittest.main()
