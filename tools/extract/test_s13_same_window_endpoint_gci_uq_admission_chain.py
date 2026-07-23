#!/usr/bin/env python3
"""Tests for the S13 same-window/endpoint GCI/UQ chain package."""

from __future__ import annotations

import csv
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_s13_same_window_endpoint_gci_uq_admission_chain"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def truth(value: str) -> bool:
    return str(value).strip().lower() == "true"


class S13SameWindowEndpointChainTest(unittest.TestCase):
    def test_summary_counts_and_decision(self) -> None:
        summary = json.loads((OUT / "summary.json").read_text(encoding="utf-8"))
        self.assertEqual(summary["decision"], "endpoint_basis_resolved_formal_gci_uq_blocked_by_same_window_equivalence")
        self.assertEqual(summary["same_window_mapping_rows"], 72)
        self.assertEqual(summary["same_window_equivalence_admitted_rows"], 0)
        self.assertEqual(summary["endpoint_geometry_rows"], 288)
        self.assertEqual(summary["released_endpoint_masks"], 6)
        self.assertEqual(summary["endpoint_residual_basis_ready_rows"], 6)
        self.assertEqual(summary["formal_gci_run_rows"], 0)
        self.assertEqual(summary["same_qoi_uq_rerun_rows"], 0)
        self.assertFalse(summary["native_solver_outputs_mutated"])
        self.assertFalse(summary["registry_mutated"])

    def test_endpoint_geometry_is_release_ready(self) -> None:
        rows = read_csv(OUT / "endpoint_geometry_enriched_face_rows.csv")
        self.assertEqual(len(rows), 288)
        for row in rows:
            self.assertTrue(truth(row["release_ready"]))
            self.assertGreater(float(row["area_m2"]), 0.0)
            vector = (
                float(row["area_vector_x_m2"]),
                float(row["area_vector_y_m2"]),
                float(row["area_vector_z_m2"]),
            )
            self.assertGreater(sum(component * component for component in vector), 0.0)
            self.assertNotEqual(row["owner_cell"], "")
            self.assertIn("OpenFOAM boundary face area vector", row["normal_convention"])
            self.assertIn("rho*U dot Sf", row["positive_mdot_convention"])

    def test_same_window_mapping_fails_closed_not_role_proxy(self) -> None:
        rows = read_csv(OUT / "medium_fine_same_window_mapping_attempt.csv")
        self.assertEqual(len(rows), 72)
        self.assertTrue(any(truth(row["role_equivalent_row_found"]) for row in rows))
        self.assertTrue(all(not truth(row["same_physical_window_mapping_admitted"]) for row in rows))
        self.assertTrue(all(row["mapping_status"] == "blocked_missing_native_target_time_directory" for row in rows))

    def test_formal_gci_and_uq_not_run_without_same_window(self) -> None:
        gci = read_csv(OUT / "formal_gci_rerun_disposition.csv")
        uq = read_csv(OUT / "same_qoi_uq_rerun_disposition.csv")
        self.assertEqual(len(gci), 4)
        self.assertEqual(len(uq), 12)
        self.assertTrue(all(truth(row["endpoint_residual_basis_ready"]) for row in gci))
        self.assertTrue(all(not truth(row["same_window_equivalence_ready"]) for row in gci))
        self.assertTrue(all(not truth(row["formal_gci_run"]) for row in gci))
        self.assertTrue(all(not truth(row["same_qoi_uq_rerun"]) for row in uq))

    def test_guardrails(self) -> None:
        guardrails = {row["guardrail"]: row["value"] for row in read_csv(OUT / "no_mutation_guardrails.csv")}
        self.assertEqual(guardrails["native_solver_outputs_mutated"], "false")
        self.assertEqual(guardrails["registry_mutated"], "false")
        self.assertEqual(guardrails["solver_or_openfoam_postprocess_launched"], "false")
        self.assertEqual(guardrails["source_property_or_qwall_release"], "false")
        self.assertEqual(guardrails["coefficient_fitting_or_admission"], "false")
        self.assertEqual(guardrails["candidate_freeze_or_final_score"], "false")


if __name__ == "__main__":
    unittest.main()
