#!/usr/bin/env python3
"""Tests for the heat-loss upcomer source-field audit package."""

from __future__ import annotations

import csv
import unittest

from tools.analyze import build_heatloss_upcomer_source_field_audit as audit


class HeatlossUpcomerSourceFieldAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.summary = audit.build()
        cls.case_rows = cls.read_csv("case_window_source_audit.csv")
        cls.field_rows = cls.read_csv("required_field_availability.csv")
        cls.blockers = cls.read_csv("missing_field_blockers.csv")
        cls.decisions = cls.read_csv("extraction_readiness_decision.csv")
        cls.sbatch = cls.read_csv("sbatch_recommendation.csv")

    @classmethod
    def read_csv(cls, name: str) -> list[dict[str, str]]:
        with (audit.OUT / name).open(newline="", encoding="utf-8") as handle:
            return list(csv.DictReader(handle))

    def test_three_mainline_windows_are_audited(self) -> None:
        self.assertEqual({row["case_id"] for row in self.case_rows}, {"salt_2", "salt_3", "salt_4"})
        self.assertEqual({row["time_window_s"] for row in self.case_rows}, {"7915", "7618", "10000"})
        self.assertTrue(all(row["processors64_time_dir_exists"] == "true" for row in self.case_rows))

    def test_primary_native_fields_are_present(self) -> None:
        primary = {"U", "T", "p", "p_rgh", "rho"}
        for case_id in {"salt_2", "salt_3", "salt_4"}:
            rows = [
                row
                for row in self.field_rows
                if row["case_id"] == case_id and row["required_field_or_artifact"] in primary
            ]
            self.assertEqual({row["required_field_or_artifact"] for row in rows}, primary)
            self.assertTrue(all(row["availability_status"] == "present" for row in rows))
            self.assertTrue(all(int(row["bytes"]) > 0 for row in rows))

    def test_exchange_artifact_blockers_are_explicit(self) -> None:
        blocked = {row["blocked_field_or_artifact"] for row in self.blockers}
        for field in {"mu", "cellVolume", "recircMask", "exchange_interface_vtk", "source_sink_ledger"}:
            self.assertIn(field, blocked)
        self.assertTrue(all(row["fit_allowed_now"] == "false" for row in self.blockers))
        self.assertTrue(all(row["score_allowed_now"] == "false" for row in self.blockers))

    def test_decisions_block_production_extraction_but_allow_next_design_work(self) -> None:
        self.assertFalse(self.summary["production_exchange_extraction_ready"])
        self.assertTrue(self.summary["all_primary_native_fields_present"])
        self.assertEqual(
            self.summary["recommended_next_task"],
            "TODO-HEATLOSS-UPCOMER-EXCHANGE-SAMPLER-IMPLEMENTATION",
        )
        self.assertTrue(all(row["production_exchange_extraction_ready"] == "false" for row in self.decisions))

    def test_sbatch_policy_routes_heavy_work_out_of_this_audit(self) -> None:
        by_item = {row["work_item"]: row for row in self.sbatch}
        self.assertEqual(by_item["source_field_audit"]["where_to_run"], "current_compute_node")
        self.assertIn("sbatch", by_item["production_exchange_surface_generation"]["where_to_run"])

    def test_no_side_effect_claims(self) -> None:
        for key in (
            "scheduler_action",
            "native_output_mutation",
            "registry_mutation",
            "solver_or_postprocessing_or_sampler_launched",
            "tools_extract_edit",
            "fluid_edit",
            "external_repo_edit",
            "fitting_or_model_selection",
            "closure_admission_change",
            "blocker_register_change",
            "generated_index_refresh",
            "residual_absorbed_into_internal_Nu",
        ):
            self.assertFalse(self.summary[key])


if __name__ == "__main__":
    unittest.main()
