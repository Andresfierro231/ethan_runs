#!/usr/bin/env python3
"""Tests for the thermal passive/source-sink unblock packet."""

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

from tools.analyze import build_thermal_passive_source_sink_unblock_packet as builder


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class ThermalPassiveSourceSinkUnblockPacketTest(unittest.TestCase):
    def test_build_outputs_no_freeze_packet(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "packet"
            summary = builder.build(out)
            self.assertEqual(summary["decision"], "thermal_unblock_packet_ready_no_freeze_no_runtime_leakage")
            self.assertGreaterEqual(summary["source_evidence_gap_rows"], 10)
            self.assertEqual(summary["passive_basis_family_rows"], 5)
            self.assertEqual(summary["source_sink_residual_decomposition_rows"], 12)
            self.assertEqual(summary["released_freeze_candidates"], 0)
            self.assertEqual(summary["passive_repair_allowed_rows"], 0)
            self.assertFalse(summary["runtime_wallHeatFlux_or_validation_temperature_release"])
            self.assertFalse(summary["candidate_freeze"])
            self.assertFalse(summary["Qwall_or_source_property_release"])

            for name in [
                "source_evidence_gap_rank.csv",
                "passive_physical_basis_gate.csv",
                "source_sink_residual_decomposition_refresh.csv",
                "s13_consumption_readiness_boundary.csv",
                "freeze_no_freeze_gate.csv",
                "runtime_forbidden_input_audit.csv",
                "source_manifest.csv",
                "no_mutation_guardrails.csv",
                "README.md",
                "summary.json",
            ]:
                self.assertTrue((out / name).exists(), name)
            json.loads((out / "summary.json").read_text(encoding="utf-8"))

    def test_passive_gate_preserves_source_basis_blocker(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "packet"
            builder.build(out)
            passive = rows(out / "passive_physical_basis_gate.csv")
            self.assertEqual({row["repair_run_allowed_now"] for row in passive}, {"False"})
            self.assertEqual({row["wallHeatFlux_provenance_present"] for row in passive}, {"True"})
            self.assertTrue(all(row["basis_decision"] == "not_independent_physical_basis" for row in passive))

    def test_runtime_forbidden_inputs_remain_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "packet"
            builder.build(out)
            forbidden = {row["forbidden_input"]: row for row in rows(out / "runtime_forbidden_input_audit.csv")}
            self.assertIn("realized CFD wallHeatFlux", forbidden)
            self.assertIn("validation temperatures", forbidden)
            self.assertIn("CFD mdot", forbidden)
            self.assertTrue(all(row["runtime_allowed"] == "False" for row in forbidden.values()))
            self.assertTrue(all(row["fit_allowed"] == "False" for row in forbidden.values()))

    def test_s13_boundary_is_diagnostic_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "packet"
            builder.build(out)
            s13_rows = rows(out / "s13_consumption_readiness_boundary.csv")
            self.assertEqual(len(s13_rows), 2)
            self.assertTrue(all(row["runtime_release_allowed_now"] == "False" for row in s13_rows))
            self.assertTrue(all(row["admission_allowed"] == "False" for row in s13_rows))


if __name__ == "__main__":
    unittest.main()
