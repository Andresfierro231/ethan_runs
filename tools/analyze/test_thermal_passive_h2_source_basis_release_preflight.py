#!/usr/bin/env python3
"""Tests for the PASSIVE-H2 source-basis release preflight."""

from __future__ import annotations

import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.analyze import build_thermal_passive_h2_source_basis_release_preflight as builder


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class ThermalPassiveH2SourceBasisReleasePreflightTest(unittest.TestCase):
    def test_build_outputs_no_release_packet(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "packet"
            summary = builder.build(out)
            self.assertEqual(
                summary["decision"],
                "thermal_passive_h2_preflight_complete_no_source_release_no_repair_no_freeze",
            )
            self.assertEqual(summary["passive_source_family_rows"], 5)
            self.assertEqual(summary["source_basis_release_ready_rows"], 0)
            self.assertEqual(summary["repair_ready_rows"], 0)
            self.assertEqual(summary["predictive_wallHeatFlux_runtime_allowed_rows"], 0)
            self.assertEqual(summary["source_property_released_rows"], 0)
            self.assertFalse(summary["candidate_freeze"])
            self.assertFalse(summary["Qwall_or_source_property_release"])

            for name in [
                "passive_source_release_checklist.csv",
                "source_backed_vs_diagnostic_split.csv",
                "exact_missing_provenance_fields.csv",
                "repair_freeze_decision.csv",
                "source_manifest.csv",
                "no_mutation_guardrails.csv",
                "README.md",
                "summary.json",
            ]:
                self.assertTrue((out / name).exists(), name)
            json.loads((out / "summary.json").read_text(encoding="utf-8"))

    def test_each_family_remains_blocked_by_independent_source_basis(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "packet"
            builder.build(out)
            checklist = rows(out / "passive_source_release_checklist.csv")
            self.assertEqual(len(checklist), 5)
            self.assertEqual({row["source_basis_release_ready_now"] for row in checklist}, {"False"})
            self.assertEqual({row["wallHeatFlux_independent"] for row in checklist}, {"False"})
            self.assertTrue(
                all("replace wallHeatFlux-derived" in row["exact_missing_provenance"] for row in checklist)
            )

    def test_repair_freeze_decision_is_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "packet"
            builder.build(out)
            decision = rows(out / "repair_freeze_decision.csv")[0]
            self.assertEqual(decision["decision"], "no_repair_no_freeze_source_basis_not_released")
            self.assertEqual(decision["run_one_train_repair"], "False")
            self.assertEqual(decision["freeze_or_admission_allowed_now"], "False")


if __name__ == "__main__":
    unittest.main()
