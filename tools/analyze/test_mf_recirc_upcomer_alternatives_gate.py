#!/usr/bin/env python3
"""Checks for the recirculating-upcomer alternatives gate."""

from __future__ import annotations

import csv
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.analyze import build_mf_recirc_upcomer_alternatives_gate as builder


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


class RecirculatingUpcomerAlternativesGateTests(unittest.TestCase):
    def test_summary_is_fail_closed(self) -> None:
        summary = builder.build()
        self.assertEqual(summary["decision"], "diagnostic_only_no_admission")
        self.assertEqual(summary["alternative_rows"], 4)
        self.assertEqual(summary["candidate_reviewable_rows"], 0)
        self.assertEqual(summary["admission_allowed_rows"], 0)
        self.assertEqual(summary["same_qoi_temporal_uq_complete_qois"], 4)
        self.assertEqual(summary["accepted_same_label_mesh_gci_qois"], 0)
        self.assertEqual(summary["onset_anchor_candidate_rows"], 0)
        self.assertEqual(summary["ordinary_internal_nu_fit_rows"], 0)
        self.assertEqual(summary["mf09_smoke_ready_variants"], 0)
        self.assertFalse(summary["mf10_new_scoring_executed"])
        self.assertFalse(summary["production_harvest_allowed"])
        self.assertFalse(summary["source_property_or_qwall_release"])
        self.assertFalse(summary["coefficient_admission"])
        self.assertFalse(summary["s11_s12_s13_s15_s6_trigger"])
        self.assertFalse(summary["native_output_mutation"])
        self.assertFalse(summary["registry_or_admission_mutation"])
        self.assertFalse(summary["scheduler_action"])
        self.assertFalse(summary["solver_sampler_harvest_uq_launched"])
        self.assertFalse(summary["Fluid_or_external_repo_mutation"])
        self.assertEqual(summary["validation_holdout_external_rows_scored"], 0)
        self.assertFalse(summary["fitting_or_model_selection"])
        self.assertFalse(summary["residual_absorbed_into_internal_nu"])

    def test_tables_keep_ordinaries_disabled_and_exchange_blocked(self) -> None:
        builder.build()
        alternatives = {row["alternative"]: row for row in rows(builder.OUT_DIR / "alternatives_matrix.csv")}
        self.assertEqual(alternatives["ordinary_upcomer_single_stream_disabled"]["status"], "required_guardrail")
        self.assertEqual(
            alternatives["throughflow_plus_recirculation_exchange_cell"]["status"],
            "preferred_science_lane_blocked",
        )
        self.assertTrue(all(row["candidate_reviewable"] == "false" for row in alternatives.values()))
        self.assertTrue(all(row["admission_allowed"] == "false" for row in alternatives.values()))

        prereqs = rows(builder.OUT_DIR / "production_harvest_prerequisites.csv")
        self.assertEqual(len(prereqs), 6)
        self.assertEqual(sum(1 for row in prereqs if row["pass"] == "true"), 1)
        self.assertIn("same_label_mesh_gci", {row["prerequisite"] for row in prereqs if row["pass"] == "false"})

    def test_no_admission_and_manifest(self) -> None:
        builder.build()
        gates = rows(builder.OUT_DIR / "no_admission_gate.csv")
        self.assertEqual(len(gates), 4)
        self.assertTrue(all(row["allowed"] == "false" for row in gates))
        manifest = rows(builder.OUT_DIR / "source_manifest.csv")
        self.assertEqual(len(manifest), 6)
        self.assertEqual({row["mutation_status"] for row in manifest}, {"read_only"})
        json.loads((builder.OUT_DIR / "summary.json").read_text())


if __name__ == "__main__":
    unittest.main()
