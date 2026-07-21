from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.extract import build_s13_upcomer_exchange_interface_wall_source_recovery as builder


class S13InterfaceWallSourceRecoveryTests(unittest.TestCase):
    def test_release_allowed_only_for_released_topology_cv(self) -> None:
        self.assertTrue(builder.release_allowed({"topology_release_status": "released_topology_cv"}))
        self.assertFalse(builder.release_allowed({"topology_release_status": "blocked_group_release_requires_all_three_cases"}))

    def test_case_reason_preserves_blocker_chain(self) -> None:
        reason = builder.case_reason({"blocking_reason": "a;b;c"})
        self.assertEqual(reason, "a;b;c")
        fallback = builder.case_reason({"blocking_reason": ""})
        self.assertEqual(fallback, "topology_cv_not_released")

    def test_package_builds_fail_closed_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "pkg"
            payload = builder.build_package(out)
            self.assertEqual(payload["summary"]["released_exchange_interface_rows"], 0)
            self.assertEqual(payload["summary"]["released_q_wall_rows"], 0)
            self.assertFalse(payload["summary"]["production_harvest_allowed"])
            self.assertTrue((out / "interface_wall_source_release_gate.csv").exists())
            self.assertTrue((out / "interface_wall_source_recovery_decision.csv").exists())
            self.assertTrue((out / "q_wall_source_release_gate.csv").exists())
            self.assertTrue((out / "downstream_sampler_blocker_chain.csv").exists())
            self.assertTrue((out / "source_evidence_synthesis.csv").exists())
            self.assertTrue((out / "s13_unblock_decision.csv").exists())
            self.assertTrue((out / "next_unblock_sequence.csv").exists())

    def test_default_package_keeps_all_rows_blocked(self) -> None:
        summary = builder.build()
        self.assertEqual(summary["case_rows"], 3)
        self.assertEqual(summary["sampler_ready_rows"], 0)
        self.assertFalse(summary["s13_unblocked"])
        self.assertFalse(summary["sampler_manifest_allowed"])
        gate = builder.read_csv(builder.OUT / "interface_wall_source_release_gate.csv")
        self.assertEqual({row["case_id"] for row in gate}, set(builder.CASE_IDS))
        self.assertTrue(all(row["cell_vtk_ready"] == "true" for row in gate))
        self.assertTrue(all(row["recirc_cv_status"] == "blocked_fragmented_velocity_topology" for row in gate))
        self.assertTrue(all(row["normal_status"] == "blocked_no_trusted_exchange_interface" for row in gate))
        self.assertTrue(all(row["production_harvest_allowed"] == "false" for row in gate))


if __name__ == "__main__":
    unittest.main()
