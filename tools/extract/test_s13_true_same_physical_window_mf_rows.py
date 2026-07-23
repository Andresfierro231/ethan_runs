#!/usr/bin/env python3
"""Tests for the S13 true same-physical-window medium/fine package."""

from __future__ import annotations

import csv
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_s13_true_same_physical_window_mf_rows"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def truth(value: str) -> bool:
    return str(value).strip().lower() == "true"


class S13TrueSamePhysicalWindowRowsTest(unittest.TestCase):
    def test_summary_fail_closed_counts(self) -> None:
        summary = json.loads((OUT / "summary.json").read_text(encoding="utf-8"))
        self.assertEqual(summary["decision"], "true_same_physical_medium_fine_rows_blocked_exact_native_times_absent")
        self.assertEqual(summary["scheduler_partition"], "NuclearEnergy-dev")
        self.assertFalse(summary["development_partition_used"])
        self.assertEqual(summary["native_time_inventory_rows"], 6)
        self.assertEqual(summary["target_window_scan_rows"], 18)
        self.assertEqual(summary["exact_native_target_rows"], 0)
        self.assertEqual(summary["true_medium_fine_rows"], 0)
        self.assertEqual(summary["physical_time_equivalence_admitted_rows"], 0)
        self.assertEqual(summary["endpoint_residual_basis_ready_rows"], 6)
        self.assertEqual(summary["formal_gci_run_rows"], 0)
        self.assertEqual(summary["same_qoi_uq_rerun_rows"], 0)

    def test_physical_time_proof_is_no_go_not_proxy(self) -> None:
        proof = read_csv(OUT / "physical_time_equivalence_proof.csv")
        self.assertEqual(len(proof), 18)
        self.assertTrue(all(not truth(row["physical_time_equivalence_admitted"]) for row in proof))
        self.assertTrue(all("proxy-only" in row["proof_status"] for row in proof))
        self.assertTrue(all(row["nearest_processors_time_label"] for row in proof))

    def test_true_rows_empty_with_header(self) -> None:
        rows = read_csv(OUT / "true_medium_fine_same_physical_rows.csv")
        self.assertEqual(rows, [])
        header = (OUT / "true_medium_fine_same_physical_rows.csv").read_text(encoding="utf-8").splitlines()[0]
        self.assertIn("true_same_physical_window_row", header)

    def test_downstream_gates_do_not_run(self) -> None:
        gci = read_csv(OUT / "formal_gci_rerun_disposition.csv")
        uq = read_csv(OUT / "same_qoi_uq_rerun_disposition.csv")
        self.assertEqual(len(gci), 4)
        self.assertEqual(len(uq), 12)
        self.assertTrue(all(truth(row["endpoint_residual_basis_ready"]) for row in gci))
        self.assertTrue(all(not truth(row["true_same_physical_window_rows_ready"]) for row in gci))
        self.assertTrue(all(not truth(row["formal_gci_run"]) for row in gci))
        self.assertTrue(all(not truth(row["same_qoi_uq_rerun"]) for row in uq))

    def test_guardrails_partition_and_no_mutation(self) -> None:
        guards = {row["guardrail"]: row["value"] for row in read_csv(OUT / "no_mutation_guardrails.csv")}
        self.assertEqual(guards["scheduler_partition"], "NuclearEnergy-dev")
        self.assertEqual(guards["development_partition_used"], "false")
        self.assertEqual(guards["native_solver_outputs_mutated"], "false")
        self.assertEqual(guards["registry_mutated"], "false")
        self.assertEqual(guards["solver_or_openfoam_postprocess_launched"], "false")
        self.assertEqual(guards["proxy_terminal_window_substitution"], "false")


if __name__ == "__main__":
    unittest.main()
