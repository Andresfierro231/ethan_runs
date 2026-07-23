#!/usr/bin/env python3
"""Tests for the S13 direct coarse extraction/GCI/UQ chain package."""

from __future__ import annotations

import csv
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_s13_direct_coarse_extraction_gci_uq_chain"


def rows(name: str) -> list[dict[str, str]]:
    with (OUT / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class S13DirectCoarseExtractionGCIUQChainTests(unittest.TestCase):
    def test_summary_records_executed_rows_and_blocked_gates(self) -> None:
        with (OUT / "summary.json").open(encoding="utf-8") as handle:
            summary = json.load(handle)
        self.assertEqual(
            summary["decision"],
            "direct_coarse_rows_generated_formal_gci_uq_blocked_by_equivalence_endpoint",
        )
        self.assertEqual(summary["direct_sampled_coarse_rows"], 36)
        self.assertEqual(summary["coarse_case_qoi_summary_rows"], 12)
        self.assertEqual(summary["same_window_equivalence_rows"], 12)
        self.assertEqual(summary["same_window_equivalence_admitted_rows"], 0)
        self.assertEqual(summary["endpoint_basis_rows"], 6)
        self.assertEqual(summary["endpoint_residual_basis_ready_rows"], 0)
        self.assertEqual(summary["formal_gci_rows"], 4)
        self.assertEqual(summary["formal_gci_run_rows"], 0)
        self.assertEqual(summary["same_qoi_uq_rows"], 12)
        self.assertEqual(summary["same_qoi_uq_rerun_rows"], 0)
        self.assertFalse(summary["native_solver_outputs_mutated"])
        self.assertFalse(summary["registry_mutated"])

    def test_direct_sampled_rows_cover_all_cases_qois_windows(self) -> None:
        sampled = rows("direct_sampled_coarse_surface_field_rows.csv")
        self.assertEqual(len(sampled), 36)
        keys = {(row["case_id"], row["qoi_label"], row["window_role"]) for row in sampled}
        for case_id in {"salt_2", "salt_3", "salt_4"}:
            for qoi in {
                "Q_wall_W",
                "mdot_exchange_positive_outward_proxy_kg_s",
                "tau_recirc_proxy_s",
                "wall_core_bulk_temperature_contrast_K",
            }:
                for role in {"target_minus", "target", "target_plus"}:
                    self.assertIn((case_id, qoi, role), keys)
        for row in sampled:
            self.assertEqual(row["mesh_level"], "current_coarse_continuation")
            self.assertEqual(row["formula_sign_basis"], "true")
            self.assertEqual(row["direct_sampled_coarse_row"], "true")
            self.assertEqual(row["production_harvest_allowed"], "false")
            self.assertEqual(row["admission_allowed"], "false")

    def test_same_window_equivalence_is_not_admitted(self) -> None:
        gate = rows("same_window_medium_fine_equivalence_gate.csv")
        self.assertEqual(len(gate), 12)
        for row in gate:
            self.assertEqual(row["same_window_medium_fine_equivalence_admitted"], "false")
            self.assertEqual(row["equivalence_status"], "blocked_unmatched_physical_time_indices")
            self.assertIn("terminal", row["medium_window_roles"])
            self.assertIn("terminal", row["fine_window_roles"])

    def test_endpoint_and_gci_uq_dispositions_fail_closed(self) -> None:
        endpoint = rows("endpoint_residual_basis_gate.csv")
        self.assertEqual(len(endpoint), 6)
        for row in endpoint:
            self.assertEqual(row["endpoint_residual_basis_ready"], "false")
            self.assertEqual(row["release_mask_ready"], "false")
        for row in rows("formal_gci_rerun_disposition.csv"):
            self.assertEqual(row["formal_gci_run"], "false")
            self.assertEqual(row["formal_gci_status"], "not_run_blocked_by_equivalence_or_endpoint_basis")
            self.assertEqual(row["production_harvest_allowed"], "false")
            self.assertEqual(row["admission_allowed"], "false")
        for row in rows("same_qoi_uq_rerun_disposition.csv"):
            self.assertEqual(row["same_qoi_uq_rerun"], "false")
            self.assertEqual(row["same_qoi_uq_status"], "diagnostic_spread_computed_formal_rerun_blocked")
            self.assertEqual(row["same_qoi_uq_admission_allowed"], "false")

    def test_scheduler_record_sources_and_guardrails(self) -> None:
        self.assertEqual(len(rows("scheduler_execution_record.csv")), 1)
        for row in rows("source_manifest.csv"):
            self.assertEqual(row["exists"], "true", row["source_path"])
        guards = {row["guardrail"]: row["value"] for row in rows("no_mutation_guardrails.csv")}
        self.assertEqual(guards["scheduler_action"], "true")
        for guard, value in guards.items():
            if guard != "scheduler_action":
                self.assertEqual(value, "false", guard)


if __name__ == "__main__":
    unittest.main()
