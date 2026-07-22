#!/usr/bin/env python3
"""Tests for the pressure low-recirculation anchor inventory packet."""

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

from tools.analyze import build_pressure_low_recirc_nonrecirc_anchor_inventory as builder


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class PressureLowRecircAnchorInventoryTest(unittest.TestCase):
    def test_build_outputs_fail_closed_anchor_inventory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "packet"
            summary = builder.build(out)
            self.assertEqual(summary["decision"], "pressure_anchor_inventory_ready_no_f6_revisit_yet")
            self.assertEqual(summary["candidate_rows_reviewed"], 36)
            self.assertEqual(summary["preferred_future_anchor_rows"], 6)
            self.assertEqual(summary["sampled_endpoint_ordinary_flow_pass_rows"], 0)
            self.assertEqual(summary["f6_fit_ready_rows"], 0)
            self.assertEqual(summary["component_k_admitted_rows"], 0)
            self.assertFalse(summary["f3_f6_shah_numeric_comparison_released"])

            for name in [
                "anchor_inventory_gate.csv",
                "sampled_endpoint_ordinary_flow_gate.csv",
                "f3_f6_shah_revisit_gate.csv",
                "next_unblock_queue.csv",
                "source_manifest.csv",
                "no_mutation_guardrails.csv",
                "README.md",
                "summary.json",
            ]:
                self.assertTrue((out / name).exists(), name)
            json.loads((out / "summary.json").read_text(encoding="utf-8"))

    def test_lower_right_not_promoted_and_future_anchors_are_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "packet"
            builder.build(out)
            inventory = rows(out / "anchor_inventory_gate.csv")
            preferred = [row for row in inventory if row["preferred_future_anchor"] == "True"]
            self.assertEqual(len(preferred), 6)
            self.assertTrue(all(row["f6_fit_ready_now"] == "False" for row in preferred))
            self.assertTrue(all("same_qoi_mesh_time_uq" in row["primary_blockers"] for row in preferred))
            self.assertTrue(all(row["claim_boundary"].startswith("no F6") for row in inventory))

    def test_revisit_gate_remains_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "packet"
            builder.build(out)
            gates = {row["gate"]: row for row in rows(out / "f3_f6_shah_revisit_gate.csv")}
            self.assertEqual(gates["F3_F6_Shah_numeric_comparison"]["status"], "closed")
            self.assertEqual(gates["ordinary_low_recirc_anchor"]["status"], "blocked")
            self.assertTrue(all(row["release_allowed"] == "False" for row in gates.values()))


if __name__ == "__main__":
    unittest.main()
