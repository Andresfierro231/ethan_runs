#!/usr/bin/env python3
"""Tests for AGENT-409 closure-QOI/hydraulic postprocess artifacts."""

from __future__ import annotations

import csv
import json
import unittest

from tools.analyze import build_lead_closure_qoi_hydraulic_postprocess as build


class LeadClosureQoiHydraulicPostprocessTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        build.build()
        cls.package = build.PACKAGE

    def read_csv(self, name: str) -> list[dict[str, str]]:
        with (self.package / name).open(newline="", encoding="utf-8") as handle:
            return list(csv.DictReader(handle))

    def test_summary_contract(self) -> None:
        summary = json.loads((self.package / "summary.json").read_text(encoding="utf-8"))
        self.assertEqual(summary["task"], "AGENT-409")
        self.assertFalse(summary["native_solver_outputs_mutated"])
        self.assertFalse(summary["registry_or_admission_mutated"])
        self.assertEqual(summary["final_forward_v1_status"], "blocked_no_go_final_forward_v1_not_admitted")
        self.assertEqual(summary["internal_nu_fit_admissible_rows_today"], 0)
        self.assertGreaterEqual(summary["pm5_rows"], 9)

    def test_closure_gate_matrix_has_no_publication_admission(self) -> None:
        rows = self.read_csv("closure_qoi_failed_gate_matrix.csv")
        self.assertGreater(len(rows), 0)
        self.assertFalse(any(row["gate_status"] == "admitted_publication_ready" for row in rows))
        statuses = {row["gate_status"] for row in rows}
        self.assertIn("blocked_missing_triplet", statuses)
        self.assertIn("blocked_non_monotone_or_oscillatory", statuses)

    def test_raw_two_tap_rows_are_diagnostic_only(self) -> None:
        rows = self.read_csv("raw_two_tap_test_section_complex.csv")
        self.assertEqual(len(rows), 3)
        for row in rows:
            self.assertEqual(row["fit_eligible"], "no")
            self.assertIn("diagnostic", row["admission_status"])
            self.assertIn("coarse_only_no_mesh_gci", row["blockers"])
            self.assertTrue(row["delta_p_rgh_upper_minus_lower_Pa"])

    def test_runner_and_manifest_are_scratch_only(self) -> None:
        runner = self.package / "scripts/run_staged_raw_two_tap.sh"
        self.assertTrue(runner.exists())
        text = runner.read_text(encoding="utf-8")
        self.assertIn(str(build.TMP_REL), text)
        self.assertIn('TMP="$ROOT/', text)
        manifest = self.read_csv("raw_two_tap_postprocess_manifest.csv")
        self.assertEqual(len(manifest), 3)
        self.assertTrue(all(row["native_solver_outputs_mutated"] == "false" for row in manifest))


if __name__ == "__main__":
    unittest.main()
