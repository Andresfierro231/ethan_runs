#!/usr/bin/env python3
"""Tests for AGENT-521 LitRev gate carryforward ledger."""

from __future__ import annotations

import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_litrev_gate_carryforward_ledger as builder  # noqa: E402


class LitRevGateCarryforwardLedgerTests(unittest.TestCase):
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
            "branch_gate_carryforward_summary.csv",
            "target_package_gate_contract.csv",
            "source_gate_crosswalk.csv",
            "fit_and_runtime_guardrails.csv",
            "source_manifest.csv",
            "summary.json",
        ]:
            self.assertTrue((out / name).exists(), name)
        summary = json.loads((out / "summary.json").read_text(encoding="utf-8"))
        self.assertEqual(summary["task"], "AGENT-521")
        self.assertEqual(summary["scientific_admission_change"], "none")
        self.assertEqual(summary["scheduler_action"], "none")
        self.assertGreaterEqual(summary["branch_gate_rows"], 18)
        self.assertEqual(summary["contract_rows"], 6)
        self.assertEqual(summary["guardrail_rows"], 5)

    def test_branch_summary_carries_required_fields(self) -> None:
        rows = self.rows(self.build_tmp() / "branch_gate_carryforward_summary.csv")
        self.assertTrue(rows)
        required = {
            "property_mode",
            "source_overlap_status",
            "reset_distance",
            "pressure_basis",
            "velocity_basis",
            "heat_path_separation",
            "RAF",
            "RMF",
            "SVF",
            "steady_window",
            "mesh_time_UQ",
        }
        for row in rows:
            fields = set(row["required_next_fields"].split(";"))
            self.assertTrue(required.issubset(fields), row)
            self.assertTrue(row["source_paths"])
            self.assertTrue(row["carryforward_decision"])
        decisions = {row["carryforward_decision"] for row in rows}
        self.assertIn("diagnostic_or_section_effective_only", decisions)
        self.assertIn("single_stream_candidate_but_thermal_fit_blocked", decisions)

    def test_target_contracts_cover_future_consumers(self) -> None:
        rows = self.rows(self.build_tmp() / "target_package_gate_contract.csv")
        packages = {row["target_package"] for row in rows}
        for expected in {
            "terminal_anchor_harvest_and_F6_phi_Re",
            "named_pressure_loss_or_reset_development_extraction",
            "branchwise_internal_HTC_bakeoff",
            "CFD_reduction_validity_diagnostics",
            "wall_test_section_temperature_shape_candidate",
            "final_predictive_scorecard_or_thesis_claim",
        }:
            self.assertIn(expected, packages)
        by_package = {row["target_package"]: row for row in rows}
        self.assertIn("RAF < 0.01", by_package["terminal_anchor_harvest_and_F6_phi_Re"]["acceptance_gate"])
        self.assertIn("pressure basis", by_package["named_pressure_loss_or_reset_development_extraction"]["acceptance_gate"])
        self.assertIn("evidence class", by_package["final_predictive_scorecard_or_thesis_claim"]["acceptance_gate"])

    def test_guardrails_block_known_bad_shortcuts(self) -> None:
        rows = self.rows(self.build_tmp() / "fit_and_runtime_guardrails.csv")
        joined = "\n".join(row["forbidden_label_or_action"] for row in rows)
        self.assertIn("ordinary_F6_fit", joined)
        self.assertIn("universal_K", joined)
        self.assertIn("hidden_global_friction_multiplier", joined)
        self.assertIn("internal_Nu_fit_absorbs_external_heat_loss", joined)
        self.assertIn("ordinary_f_D_K_Nu_from_material_reverse_flow", joined)
        self.assertIn("realized_wallHeatFlux", joined)

    def test_source_crosswalk_has_all_gate_families_and_counts(self) -> None:
        rows = self.rows(self.build_tmp() / "source_gate_crosswalk.csv")
        families = {row["gate_family"] for row in rows}
        self.assertEqual(
            families,
            {
                "source_envelope",
                "property_sensitivity",
                "reset_named_losses",
                "named_pressure_losses",
                "heat_loss",
                "cfd_validity",
            },
        )
        for row in rows:
            self.assertGreater(int(row["rows"]), 0)
            self.assertTrue(row["key_status_counts"])
            self.assertTrue(row["must_not_infer"])


if __name__ == "__main__":
    unittest.main()
