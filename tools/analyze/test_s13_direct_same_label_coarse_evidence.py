#!/usr/bin/env python3.11
"""Tests for the S13 direct same-label coarse evidence gate."""

from __future__ import annotations

import csv
import json
import unittest

from tools.analyze import build_s13_direct_same_label_coarse_evidence as builder


def rows(name: str) -> list[dict[str, str]]:
    with (builder.OUT / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class S13DirectSameLabelCoarseEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        builder.main()

    def test_summary_is_compute_contract_ready_no_admission(self) -> None:
        summary = json.loads((builder.OUT / "summary.json").read_text())
        self.assertEqual(
            summary["decision"],
            "s13_direct_same_label_coarse_evidence_fail_closed_compute_contract_ready",
        )
        self.assertEqual(summary["case_qoi_rows"], 12)
        self.assertEqual(summary["coarse_candidate_rows"], 12)
        self.assertEqual(summary["direct_same_label_coarse_admitted_rows"], 0)
        self.assertEqual(summary["formal_gci_ready_rows"], 0)
        self.assertEqual(summary["compute_ready_contract_rows"], 4)

    def test_lane_matrix_names_missing_lanes(self) -> None:
        matrix = {row["lane"]: row for row in rows("direct_coarse_lane_evidence_matrix.csv")}
        self.assertEqual(len(matrix), 5)
        self.assertEqual(matrix["coarse_qoi_values"]["existing_rows"], "12")
        self.assertEqual(matrix["coarse_endpoint_face_geometry"]["admission_ready"], "false")
        self.assertIn("area vectors", matrix["coarse_endpoint_face_geometry"]["blocking_gap"])
        self.assertEqual(matrix["open_cv_residual_ledger"]["admission_ready"], "false")

    def test_case_qoi_matrix_blocks_every_qoi(self) -> None:
        audit = rows("case_qoi_direct_coarse_evidence_matrix.csv")
        self.assertEqual(len(audit), 12)
        for row in audit:
            self.assertEqual(row["formula_sign_units_ready"], "true")
            self.assertEqual(row["coarse_qoi_value_exists"], "true")
            self.assertEqual(row["coarse_face_geometry_ready"], "false")
            self.assertEqual(row["open_cv_residual_ready"], "false")
            self.assertEqual(row["direct_same_label_coarse_admitted"], "false")
            self.assertEqual(row["formal_gci_ready"], "false")

    def test_compute_contract_is_executable_and_strict(self) -> None:
        contract = rows("compute_ready_extraction_contract.csv")
        self.assertEqual([row["rank"] for row in contract], ["1", "2", "3", "4"])
        self.assertIn("area_vector_x_m2", contract[0]["required_columns"])
        self.assertIn("owner_cell", contract[0]["required_columns"])
        self.assertIn("direct_same_label_coarse_admitted", contract[1]["required_columns"])
        self.assertIn("do not promote current reconstructed coarse candidates", contract[1]["forbidden"])
        self.assertIn("residual_accounted", contract[2]["required_columns"])
        self.assertIn("formal_gci_ready", contract[3]["required_columns"])

    def test_qwall_rollup_does_not_admit_even_low_spread_lane(self) -> None:
        rollup = {row["qoi_label"]: row for row in rows("qoi_direct_coarse_rollup.csv")}
        self.assertEqual(rollup["Q_wall_W"]["coarse_candidate_rows"], "3")
        self.assertEqual(rollup["Q_wall_W"]["direct_same_label_coarse_admitted_rows"], "0")

    def test_sources_and_guardrails(self) -> None:
        for row in rows("source_manifest.csv"):
            self.assertEqual(row["exists"], "true", row["source_path"])
            self.assertEqual(row["mutated"], "false")
        for row in rows("no_mutation_guardrails.csv"):
            self.assertEqual(row["value"], "false", row["guardrail"])


if __name__ == "__main__":
    unittest.main()
