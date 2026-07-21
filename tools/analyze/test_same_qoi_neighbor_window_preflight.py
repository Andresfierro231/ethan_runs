from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.analyze import build_same_qoi_neighbor_window_preflight as builder


class SameQoiNeighborWindowPreflightTests(unittest.TestCase):
    def test_preflight_carries_all_phase_c_rows_and_admits_none(self) -> None:
        rows = builder.preflight_rows()
        self.assertEqual(len(rows), 12)
        self.assertTrue(all(row["accepted_after_preflight"] == "false" for row in rows))
        self.assertTrue(any(row["compute_priority"].startswith("P1") for row in rows))

    def test_compute_queue_preserves_no_admission_guard(self) -> None:
        queue = builder.compute_queue_rows(builder.preflight_rows())
        self.assertGreater(len(queue), 0)
        self.assertTrue(all("do not admit" in row["forbidden_action"] for row in queue))
        self.assertEqual(queue[0]["priority"], 1)

    def test_build_package_writes_expected_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "pkg"
            payload = builder.build_package(out)
            self.assertEqual(payload["summary"]["qoi_rows"], 12)
            self.assertEqual(payload["summary"]["accepted_rows"], 0)
            self.assertFalse(payload["summary"]["scheduler_action"])
            for name in [
                "neighbor_window_preflight.csv",
                "compute_needed_queue.csv",
                "admission_guardrails.csv",
                "source_manifest.csv",
                "summary.json",
                "README.md",
            ]:
                self.assertTrue((out / name).exists(), name)


if __name__ == "__main__":
    unittest.main()
