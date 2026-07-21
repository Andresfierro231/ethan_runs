"""Tests for the blocker-resolution plan builder."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.analyze.build_blocker_resolution_plan import (
    OPEN_BLOCKERS,
    RIGOR_GATES,
    STALE_BLOCKERS,
    WORK_PACKETS,
    build_package,
    blocker_coverage_rows,
)


class BlockerResolutionPlanTests(unittest.TestCase):
    def test_every_open_blocker_has_packet_coverage(self) -> None:
        coverage = blocker_coverage_rows()
        covered = {row["blocker_id"] for row in coverage if row["covered"] is True}
        self.assertEqual(set(OPEN_BLOCKERS), covered)

    def test_stale_blockers_are_not_active_packet_targets(self) -> None:
        packet_blob = "\n".join(str(packet) for packet in WORK_PACKETS)
        for blocker in STALE_BLOCKERS:
            self.assertNotIn(blocker, packet_blob)

    def test_rigor_gates_include_gci_and_predictive_input_discipline(self) -> None:
        gate_text = "\n".join(gate["rule"] for gate in RIGOR_GATES)
        self.assertIn("No GCI for two-level", gate_text)
        self.assertIn("cannot use CFD mdot", gate_text)
        self.assertIn("wallHeatFlux includes rcExternalTemperature radiation", gate_text)

    def test_build_package_writes_valid_summary(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            summary = build_package(Path(tmp))
            self.assertEqual(summary["area_count"], 3)
            self.assertEqual(summary["open_blocker_count"], len(OPEN_BLOCKERS))
            self.assertEqual(summary["open_blockers_covered"], len(OPEN_BLOCKERS))
            self.assertEqual(summary["validation_error_count"], 0)
            self.assertTrue((Path(tmp) / "work_packets.csv").exists())
            self.assertTrue((Path(tmp) / "README.md").exists())


if __name__ == "__main__":
    unittest.main()
