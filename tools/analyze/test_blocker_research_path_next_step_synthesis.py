#!/usr/bin/env python3
"""Tests for AGENT-539 blocker/research-path/next-step synthesis."""

from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path

from tools.analyze import build_blocker_research_path_next_step_synthesis as builder


class BlockerResearchPathNextStepSynthesisTests(unittest.TestCase):
    def build_tmp(self) -> Path:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        out = Path(tmp.name)
        builder.build_package(out)
        return out

    def rows(self, path: Path) -> list[dict[str, str]]:
        with path.open(newline="", encoding="utf-8") as handle:
            return list(csv.DictReader(handle))

    def test_outputs_and_summary(self) -> None:
        out = self.build_tmp()
        for name in [
            "README.md",
            "verified_blockers.csv",
            "research_paths.csv",
            "next_steps_queue.csv",
            "source_manifest.csv",
            "summary.json",
        ]:
            self.assertTrue((out / name).exists(), name)

        summary = json.loads((out / "summary.json").read_text(encoding="utf-8"))
        self.assertEqual(summary["task"], "AGENT-539")
        self.assertEqual(summary["verified_open_blockers"], 3)
        self.assertEqual(summary["research_paths"], 6)
        self.assertEqual(summary["next_steps"], 5)
        self.assertEqual(summary["top_next_step"], "NS1_fluid_umx1_api_row")
        self.assertEqual(summary["umx1_grid_status"], "blocked_no_real_hook")
        self.assertEqual(summary["scientific_admission_change"], "none")
        self.assertEqual(summary["scheduler_action"], "none")
        self.assertEqual(summary["generated_index_refresh"], "not_run_synthesis_package_only")

    def test_verified_blockers_are_current_open_only(self) -> None:
        rows = self.rows(self.build_tmp() / "verified_blockers.csv")
        blocker_ids = {row["blocker_id"] for row in rows}
        self.assertEqual(
            blocker_ids,
            {
                "predictive-wall-test-section-submodels",
                "upcomer-onset-data-sparsity",
                "f6-friction-re-correction",
            },
        )
        for resolved_id in [
            "closure-qoi-mesh-gci",
            "refined-mesh-t-reconstruction-corruption",
            "thermal-cfd-1d-parity",
            "predictive-heater-cooler-wall-submodels",
            "fluid-external-boundary-api-gap",
            "of12-reconstructpar-segfault",
            "no-mesh-for-gci",
            "cfd-no-radiation-parity",
        ]:
            self.assertNotIn(resolved_id, blocker_ids)

    def test_umx1_is_api_path_not_scoring_grid(self) -> None:
        rows = self.rows(self.build_tmp() / "research_paths.csv")
        by_id = {row["path_id"]: row for row in rows}
        rp1 = by_id["RP1"]
        self.assertEqual(rp1["priority"], "P0")
        self.assertIn("AGENT-537 decision=no_real_upcomer_mixing_hook_no_solver_api_contract", rp1["evidence_available_now"])
        self.assertIn("real_hook_present=false", rp1["evidence_available_now"])
        self.assertIn("Do not launch a UMX1 scoring grid", rp1["guardrails"])
        self.assertIn("do not fake mixing", rp1["guardrails"])

    def test_source_property_enforcement_remains_a_research_path(self) -> None:
        rows = self.rows(self.build_tmp() / "research_paths.csv")
        by_id = {row["path_id"]: row for row in rows}
        rp5 = by_id["RP5"]
        self.assertEqual(rp5["research_path"], "Closure scorecard label enforcement")
        self.assertIn("source-envelope/property labels", rp5["missing_evidence"])
        self.assertIn("No blank property/source label fields", rp5["acceptance_signal"])
        self.assertIn("Do not treat missing source/property coverage", rp5["guardrails"])

    def test_next_step_queue_has_actionable_guardrails(self) -> None:
        rows = self.rows(self.build_tmp() / "next_steps_queue.csv")
        by_rank = {int(row["rank"]): row for row in rows}
        first = by_rank[1]
        self.assertEqual(first["next_step_id"], "NS1_fluid_umx1_api_row")
        self.assertIn("before any UMX1 score grid", first["action"])
        self.assertEqual(first["scheduler_or_compute_policy"], "no scheduler or solver until API contract exists")
        self.assertEqual(first["fit_model_selection_policy"], "no fitting/model selection")
        self.assertIn("no wall-loss/HTC/friction/source/sensor adjustment", first["runtime_input_guardrail"])

        scoring_grid_actions = [
            row
            for row in rows
            if "UMX1" in row["action"] and "score grid" in row["action"] and "before any UMX1 score grid" not in row["action"]
        ]
        self.assertEqual(scoring_grid_actions, [])

    def test_source_manifest_inputs_exist(self) -> None:
        rows = self.rows(self.build_tmp() / "source_manifest.csv")
        self.assertGreaterEqual(len(rows), 10)
        self.assertTrue(all(row["exists"] == "True" for row in rows))


if __name__ == "__main__":
    unittest.main()
