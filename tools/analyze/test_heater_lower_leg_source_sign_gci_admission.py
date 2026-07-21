#!/usr/bin/env python3
"""Tests for AGENT-468 heater lower-leg source/sign/GCI admission."""

from __future__ import annotations

import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_heater_lower_leg_source_sign_gci_admission as builder  # noqa: E402


class HeaterLowerLegAdmissionTests(unittest.TestCase):
    def test_builder_outputs_expected_blocked_heater_decision(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            summary = builder.build_package(out)

            self.assertEqual(summary["task"], "AGENT-468")
            self.assertEqual(summary["blocker_decision"], "not_resolved_heater_narrowed")
            self.assertEqual(summary["heater_candidate_rows"], 7)
            self.assertEqual(summary["heater_nu_candidate_rows"], 2)
            self.assertEqual(summary["heater_fit_admissible_rows"], 0)
            self.assertEqual(summary["heater_publication_ready_gci_rows"], 0)

            for filename in summary["outputs"]:
                self.assertTrue((out / filename).exists(), filename)

            written = json.loads((out / "summary.json").read_text(encoding="utf-8"))
            self.assertEqual(written["heater_fit_admissible_rows"], 0)

    def test_no_candidate_is_admitted_without_all_hard_gates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            builder.build_package(out)

            with (out / "heater_internal_nu_candidate_admission.csv").open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))

            self.assertEqual(len(rows), 2)
            for row in rows:
                self.assertEqual(row["admission_decision"], "not_admitted")
                self.assertEqual(row["fit_admissible"], "no")
                self.assertIn("source_allows_fit", row["failure_reasons"])
                self.assertIn("sign_heat_balance", row["failure_reasons"])
                self.assertIn("recirculation", row["failure_reasons"])
                self.assertIn("mesh_gci", row["failure_reasons"])

    def test_heater_gci_rows_preserve_sign_and_triplet_blockers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            builder.build_package(out)

            with (out / "heater_same_qoi_mesh_gci_gate.csv").open(newline="", encoding="utf-8") as handle:
                rows = {row["qoi_id"]: row for row in csv.DictReader(handle)}

            self.assertEqual(len(rows), 6)
            self.assertEqual(rows["thermal_segment_closure::lower_leg::HTC"]["gci_status"], "not_publication_gci_sign_review_required")
            self.assertEqual(rows["thermal_segment_closure::lower_leg::UA_prime"]["gci_status"], "not_publication_gci_sign_review_required")
            self.assertEqual(rows["thermal_segment_closure::lower_leg::Nu"]["gci_status"], "not_computed_missing_triplet")
            self.assertTrue(all(row["same_qoi_gate"] == "no" for row in rows.values()))

    def test_admitted_only_gci_export_is_empty_header_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            builder.build_package(out)

            with (out / "gci_results_admitted_only.csv").open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(rows, [])

    def test_next_queue_is_precise_heater_punch_list(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            builder.build_package(out)

            with (out / "next_extraction_queue.csv").open(newline="", encoding="utf-8") as handle:
                rows = {row["queue_id"]: row for row in csv.DictReader(handle)}

            self.assertEqual(set(rows), {
                "heater_source_enthalpy_sign_heat_balance_admission",
                "heater_same_qoi_nu_or_htc_ua_gci_reconciliation",
                "heater_branch_recirculation_metric",
                "heater_hydraulic_final_use_exclude_or_reextract",
            })
            self.assertEqual(rows["heater_source_enthalpy_sign_heat_balance_admission"]["priority"], "P0")
            self.assertEqual(rows["heater_same_qoi_nu_or_htc_ua_gci_reconciliation"]["priority"], "P0")


if __name__ == "__main__":
    unittest.main()
