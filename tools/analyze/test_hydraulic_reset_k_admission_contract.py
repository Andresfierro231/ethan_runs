#!/usr/bin/env python3
"""Tests for the hydraulic reset/K admission contract builder."""

from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path

from tools.analyze.build_hydraulic_reset_k_admission_contract import build_package


def _read_csv(path: Path):
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


class HydraulicResetKAdmissionContractTests(unittest.TestCase):
    def test_outputs_and_summary_guardrails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            summary = build_package(out)

            expected_files = {
                "README.md",
                "summary.json",
                "source_manifest.csv",
                "hydraulic_reset_development_contract.csv",
                "component_cluster_k_admission_table.csv",
                "tap_length_gap_table.csv",
                "f6_readiness_handoff.csv",
            }
            self.assertEqual(expected_files, {path.name for path in out.iterdir()})
            self.assertFalse(summary["native_solver_outputs_mutated"])
            self.assertFalse(summary["thermal_fit_used"])
            self.assertFalse(summary["global_multiplier_exported"])
            self.assertGreater(summary["reset_contract_rows"], 0)
            self.assertGreater(summary["component_k_rows"], 0)
            self.assertGreater(summary["tap_length_gap_rows"], 0)

            persisted = json.loads((out / "summary.json").read_text(encoding="utf-8"))
            self.assertEqual(summary["component_fit_admissible_rows"], persisted["component_fit_admissible_rows"])

    def test_component_k_current_rows_are_not_fit_admitted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            summary = build_package(out)
            rows = _read_csv(out / "component_cluster_k_admission_table.csv")

            self.assertEqual(0, summary["component_fit_admissible_rows"])
            self.assertFalse(any(row["admission_status"] == "candidate_fit_admissible" for row in rows))
            self.assertTrue(any(row["coefficient_name_allowed"] == "no_universal_K_yet" for row in rows))
            self.assertTrue(
                any(row["admission_status"] == "diagnostic_only_recirculation_adjacent" for row in rows)
            )

    def test_reset_contract_requires_first_class_api(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            summary = build_package(out)
            rows = _read_csv(out / "hydraulic_reset_development_contract.csv")

            self.assertGreater(summary["reset_candidate_blocked_rows"], 0)
            self.assertTrue(all(row["fluid_api_requirement"] == "first_class_reset_development_term" for row in rows))
            self.assertTrue(
                any(row["admission_status"] == "candidate_blocked_api_and_mesh_admission" for row in rows)
            )

    def test_f6_handoff_blocks_until_corrected_q_admitted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            summary = build_package(out)
            rows = _read_csv(out / "f6_readiness_handoff.csv")

            self.assertEqual(1, len(rows))
            self.assertFalse(summary["f6_ready_for_bounded_test"])
            self.assertEqual("no", rows[0]["ready_for_bounded_test"])
            self.assertEqual("0", rows[0]["corrected_q_admitted_rows"])
            self.assertIn("terminal/admitted corrected-Q", rows[0]["blocking_gap"])


if __name__ == "__main__":
    unittest.main()
