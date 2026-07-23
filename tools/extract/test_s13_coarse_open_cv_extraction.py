#!/usr/bin/env python3.11
"""Tests for the S13 current-coarse open-CV extraction wrapper."""

from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path

from tools.extract import build_s13_coarse_open_cv_extraction as builder


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class S13CoarseOpenCvExtractionTests(unittest.TestCase):
    def test_contract_selects_three_current_coarse_cases(self) -> None:
        contract = builder.selected_contract_rows(builder.DEFAULT_CONTRACT)
        self.assertEqual({row["case_id"] for row in contract}, {"salt_2", "salt_3", "salt_4"})
        self.assertTrue(all(row["mesh_label"] == "current_coarse_continuation" for row in contract))

    def test_dry_build_is_fail_closed_and_no_sampling(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "dry"
            summary = builder.build(out, case_id="salt_2", max_windows=1, write_closeout_docs=False)
            self.assertEqual(summary["decision"], "s13_coarse_open_cv_extraction_dry_preflight_no_admission")
            self.assertFalse(summary["execute_mode"])
            self.assertFalse(summary["scheduler_action"])
            self.assertEqual(summary["source_contract_rows"], 1)
            self.assertEqual(summary["qoi_rows"], 4)
            qois = rows(out / "s13_same_label_coarse_open_cv_qoi_rows.csv")
            self.assertEqual({row["direct_same_label_coarse_admitted"] for row in qois}, {"false"})
            self.assertEqual({row["admission_status"] for row in qois}, {"blocked_not_executed_or_no_sampled_rows"})
            json.loads((out / "summary.json").read_text())

    def test_repair_manifest_schema_is_written_without_native_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "dry"
            summary = builder.build(out, case_id="salt_2", max_windows=1, write_closeout_docs=False)
            self.assertFalse(summary["native_solver_outputs_mutated"])
            repair = rows(out / "staging_repair_manifest.csv")
            self.assertEqual(repair[0]["copied"], "false")
            self.assertEqual(repair[0]["native_solver_output_mutated"], "false")

    def test_shell_artifacts_have_required_columns(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "dry"
            builder.build(out, case_id="salt_2", max_windows=1, write_closeout_docs=False)
            face_header = rows(out / "s13_same_label_coarse_open_cv_face_contract.csv")[0].keys()
            self.assertIn("area_vector_x_m2", face_header)
            self.assertIn("owner_cell", face_header)
            residual_header = rows(out / "s13_same_label_coarse_open_cv_residual_ledger.csv")[0].keys()
            self.assertIn("residual_accounted", residual_header)
            gate_header = rows(out / "s13_same_label_coarse_triplet_admission_gate.csv")[0].keys()
            self.assertIn("formal_gci_ready", gate_header)


if __name__ == "__main__":
    unittest.main()
