#!/usr/bin/env python3
"""Tests for the S13 strict same-label coarse no-go contract."""

from __future__ import annotations

import csv
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_s13_strict_coarse_nogo_contract"


def rows(name: str) -> list[dict[str, str]]:
    with (OUT / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class S13StrictCoarseNoGoContractTests(unittest.TestCase):
    def test_summary_blocks_formal_gci_and_harvest(self) -> None:
        with (OUT / "summary.json").open(encoding="utf-8") as handle:
            summary = json.load(handle)
        self.assertEqual(summary["decision"], "s13_strict_same_label_coarse_no_go_formal_gci_blocked")
        self.assertEqual(summary["criteria_rows"], 6)
        self.assertEqual(summary["criteria_pass_rows"], 0)
        self.assertEqual(summary["case_qoi_rows"], 12)
        self.assertEqual(summary["current_coarse_candidate_rows"], 12)
        self.assertEqual(summary["admitted_same_label_coarse_rows"], 0)
        self.assertEqual(summary["strict_coarse_no_go_rows"], 12)
        self.assertEqual(summary["formal_gci_ready_rows"], 0)
        self.assertEqual(summary["production_harvest_allowed_rows"], 0)
        self.assertEqual(summary["medium_fine_exact_label_rows"], 72)
        self.assertEqual(summary["replacement_contract_rows"], 4)
        for value in summary["guardrails"].values():
            self.assertFalse(value)

    def test_all_required_criteria_fail_closed(self) -> None:
        criteria = rows("strict_coarse_equivalence_criteria.csv")
        self.assertEqual(len(criteria), 6)
        required = {row["criterion"] for row in criteria}
        self.assertEqual(
            required,
            {
                "qoi_label_formula_sign_units",
                "geometry_mask_provenance",
                "time_window_equivalence",
                "field_source_property_basis",
                "closed_or_residual_accounted_cv",
                "same_qoi_uq_and_mesh_disposition",
            },
        )
        for row in criteria:
            self.assertEqual(row["strict_coarse_equivalence_pass"], "false")
            self.assertIn("blocks same-label coarse admission", row["no_go_effect_now"])

    def test_case_qoi_rows_are_diagnostic_only(self) -> None:
        audit = rows("case_qoi_strict_coarse_no_go.csv")
        self.assertEqual(len(audit), 12)
        keys = {(row["case_id"], row["qoi_label"]) for row in audit}
        for case_id in {"salt_2", "salt_3", "salt_4"}:
            for qoi in {
                "Q_wall_W",
                "mdot_exchange_positive_outward_proxy_kg_s",
                "tau_recirc_proxy_s",
                "wall_core_bulk_temperature_contrast_K",
            }:
                self.assertIn((case_id, qoi), keys)
        for row in audit:
            self.assertEqual(row["current_coarse_candidate_exists"], "true")
            self.assertEqual(row["direct_same_label_coarse_admitted"], "false")
            self.assertEqual(row["coarse_equivalence_admitted"], "false")
            self.assertEqual(row["strict_coarse_no_go"], "true")
            self.assertEqual(row["formal_gci_status"], "blocked_strict_same_label_coarse_not_admitted")
            self.assertEqual(row["production_harvest_allowed"], "false")
            self.assertEqual(row["admission_allowed"], "false")
            self.assertEqual(row["coefficient_fit_allowed"], "false")
            self.assertIn("current-coarse reconstructed target rows exist", row["no_go_reason"])

    def test_qoi_matrix_preserves_qwall_diagnostic_boundary(self) -> None:
        matrix = rows("qoi_formal_gci_no_go_matrix.csv")
        self.assertEqual(len(matrix), 4)
        by_qoi = {row["qoi_label"]: row for row in matrix}
        self.assertEqual(by_qoi["Q_wall_W"]["qoi_disposition"], "diagnostic_low_spread_but_no_formal_gci")
        for qoi, row in by_qoi.items():
            self.assertEqual(row["case_count"], "3", qoi)
            self.assertEqual(row["current_coarse_candidate_rows"], "3", qoi)
            self.assertEqual(row["admitted_same_label_coarse_rows"], "0", qoi)
            self.assertEqual(row["strict_coarse_no_go_rows"], "3", qoi)
            self.assertEqual(row["medium_fine_exact_label_status"], "complete_diagnostic", qoi)
            self.assertEqual(row["formal_gci_status"], "blocked_strict_same_label_coarse_not_admitted", qoi)
            self.assertEqual(row["production_harvest_allowed"], "false", qoi)
            self.assertEqual(row["admission_allowed"], "false", qoi)
            self.assertEqual(row["coefficient_fit_allowed"], "false", qoi)

    def test_unlock_contract_requires_direct_same_label_coarse_rows(self) -> None:
        contract = rows("coarse_unlock_action_contract.csv")
        self.assertEqual([row["step"] for row in contract], [
            "preserve_current_no_go",
            "generate_or_admit_direct_same_label_coarse_rows",
            "rerun_formal_gci_gate",
            "same_qoi_uq_before_harvest_or_admission",
        ])
        self.assertEqual(contract[0]["scheduler_required"], "false")
        self.assertIn("direct_same_label_coarse_admitted=true", contract[1]["success_criterion"])
        self.assertIn("two-level evidence", contract[2]["forbidden"])
        self.assertIn("same-QOI UQ", contract[3]["forbidden"])

    def test_replacement_contract_is_exact_and_not_a_proxy(self) -> None:
        contract = rows("replacement_coarse_dataset_contract.csv")
        self.assertEqual(len(contract), 4)
        artifacts = {row["artifact"]: row for row in contract}
        face = artifacts["s13_same_label_coarse_open_cv_face_contract.csv"]
        self.assertIn("area_vector_x_m2", face["required_columns"])
        self.assertIn("owner_cell", face["required_columns"])
        self.assertIn("positive_mdot_convention", face["required_columns"])
        qoi = artifacts["s13_same_label_coarse_open_cv_qoi_rows.csv"]
        self.assertIn("direct_same_label_coarse_admitted", qoi["required_columns"])
        self.assertIn("current reconstructed coarse candidates", qoi["forbidden_substitution"])
        triplet = artifacts["s13_same_label_coarse_triplet_admission_gate.csv"]
        self.assertIn("formal_gci_ready", triplet["required_columns"])
        self.assertIn("two-level evidence", triplet["forbidden_substitution"])

    def test_sources_exist_and_guardrails_are_false(self) -> None:
        for row in rows("source_manifest.csv"):
            self.assertEqual(row["exists"], "true", row["source_path"])
        for row in rows("no_mutation_guardrails.csv"):
            self.assertEqual(row["value"], "false", row["guardrail"])


if __name__ == "__main__":
    unittest.main()
