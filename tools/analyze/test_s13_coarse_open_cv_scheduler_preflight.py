#!/usr/bin/env python3.11
"""Tests for the S13 coarse open-CV scheduler preflight package."""

from __future__ import annotations

import csv
import json
import unittest

from tools.analyze import build_s13_coarse_open_cv_scheduler_preflight as builder


def rows(name: str) -> list[dict[str, str]]:
    with (builder.OUT / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class S13CoarseOpenCvSchedulerPreflightTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        builder.main()

    def test_summary_is_preflight_only(self) -> None:
        summary = json.loads((builder.OUT / "summary.json").read_text())
        self.assertEqual(
            summary["decision"],
            "s13_coarse_open_cv_scheduler_preflight_source_staging_repair_needed_no_execution",
        )
        self.assertEqual(summary["case_rows"], 3)
        self.assertEqual(summary["qoi_rows_required"], 12)
        self.assertEqual(summary["required_artifact_rows"], 4)
        self.assertEqual(summary["source_staging_repair_rows"], 12)
        self.assertEqual(summary["source_staging_repair_source_fields_present"], 12)
        self.assertFalse(summary["scheduler_action"])
        self.assertFalse(summary["native_solver_outputs_mutated"])
        self.assertFalse(summary["extractor_source_edited"])
        self.assertTrue(summary["next_board_row_ready"])

    def test_case_window_contract_covers_salt234(self) -> None:
        contract = rows("coarse_case_window_contract.csv")
        self.assertEqual({row["case_id"] for row in contract}, {"salt_2", "salt_3", "salt_4"})
        self.assertTrue(all(row["mesh_label"] == "current_coarse_continuation" for row in contract))
        for row in contract:
            windows = row["strict_contract_windows_s"].split(";")
            self.assertEqual(len(windows), 3)
            self.assertEqual(windows[1], row["target_time_window_s"])
            self.assertEqual(row["native_solver_output_mutated"], "false")

    def test_source_repair_contract_points_to_existing_original_fields(self) -> None:
        repair = rows("coarse_source_staging_repair_contract.csv")
        self.assertEqual(len(repair), 12)
        self.assertEqual({row["field"] for row in repair}, {"T", "rho", "U", "wallHeatFlux"})
        self.assertEqual({row["window_s"] for row in repair}, {"7914", "7617", "9999"})
        for row in repair:
            self.assertEqual(row["source_processors_note_exists"], "true")
            self.assertEqual(row["source_field_exists"], "true")
            self.assertEqual(row["destination_field_exists"], "false")
            self.assertEqual(row["repair_allowed_in_this_row"], "false")
            self.assertEqual(row["native_solver_output_mutated"], "false")

    def test_required_schema_preserves_admission_columns(self) -> None:
        schema = {row["artifact"]: row for row in rows("required_output_schema_contract.csv")}
        self.assertIn("area_vector_x_m2", schema["s13_same_label_coarse_open_cv_face_contract.csv"]["required_columns"])
        self.assertIn("owner_cell", schema["s13_same_label_coarse_open_cv_face_contract.csv"]["required_columns"])
        self.assertIn(
            "direct_same_label_coarse_admitted",
            schema["s13_same_label_coarse_open_cv_qoi_rows.csv"]["required_columns"],
        )
        self.assertIn("residual_accounted", schema["s13_same_label_coarse_open_cv_residual_ledger.csv"]["required_columns"])
        self.assertIn("formal_gci_ready", schema["s13_same_label_coarse_triplet_admission_gate.csv"]["required_columns"])

    def test_sampler_capability_map_identifies_reuse_and_delta(self) -> None:
        capabilities = {row["capability"]: row for row in rows("existing_sampler_capability_map.csv")}
        self.assertEqual(capabilities["face_area_vectors_and_owner_cells"]["present_in_existing_sampler"], "true")
        self.assertIn("area_vector", capabilities["face_area_vectors_and_owner_cells"]["coarse_delta"])
        self.assertEqual(capabilities["runtime_parameterization"]["present_in_existing_sampler"], "true")
        self.assertEqual(capabilities["runtime_parameterization"]["reuse_for_coarse"], "blocked_until_adapter_or_parameterization")
        self.assertIn("contract-csv", capabilities["runtime_parameterization"]["coarse_delta"])

    def test_scheduler_handoff_does_not_submit(self) -> None:
        handoff = rows("scheduler_handoff.csv")
        self.assertEqual(len(handoff), 1)
        self.assertEqual(handoff[0]["submit_performed"], "false")
        self.assertEqual(handoff[0]["scheduler_action_allowed_in_this_row"], "false")
        self.assertEqual(handoff[0]["source_staging_repair_required_before_submit"], "true")
        self.assertIn("build_s13_coarse_open_cv_extraction.py", handoff[0]["exact_command_after_next_row_claim"])
        self.assertTrue((builder.OUT / "run_s13_coarse_open_cv_extraction.sbatch").exists())

    def test_next_row_and_guardrails_are_explicit(self) -> None:
        next_rows = rows("next_board_row.csv")
        self.assertEqual(next_rows[0]["task_id"], "TODO-S13-COARSE-OPEN-CV-EXTRACTION-SCHEDULER-2026-07-22")
        self.assertIn("tools/extract/build_s13_coarse_open_cv_extraction.py", next_rows[0]["allowed_edit_paths"])
        for row in rows("no_mutation_guardrails.csv"):
            self.assertEqual(row["value"], "false", row["guardrail"])
        for row in rows("source_manifest.csv"):
            self.assertEqual(row["exists"], "true", row["source_path"])
            self.assertEqual(row["mutated"], "false", row["source_path"])


if __name__ == "__main__":
    unittest.main()
