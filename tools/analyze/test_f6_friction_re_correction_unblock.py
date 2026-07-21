#!/usr/bin/env python3
"""Tests for AGENT-487 F6 friction/Re-correction unblock package."""

from __future__ import annotations

import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_f6_friction_re_correction_unblock as builder  # noqa: E402


class F6FrictionReCorrectionUnblockTests(unittest.TestCase):
    def test_builder_keeps_blocker_open_and_preserves_f3(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            summary = builder.build_package(out)

            self.assertEqual(summary["task"], "AGENT-487")
            self.assertEqual(summary["f6_blocker_decision"], "keep_open_narrowed")
            self.assertEqual(summary["production_closure"], "F3_shah_apparent")
            self.assertEqual(summary["ordinary_f6_candidate_rows"], 0)
            self.assertEqual(summary["ordinary_f6_scoreable_rows"], 0)
            self.assertGreater(summary["hybrid_candidate_rows"], 0)
            self.assertEqual(summary["hybrid_scoreable_rows"], 0)
            self.assertGreater(summary["queue_rows"], 0)

            written = json.loads((out / "summary.json").read_text(encoding="utf-8"))
            self.assertEqual(written["generated_index_refresh"], "not_run_active_AGENT_482_owns_generated_indexes")

    def test_material_recirculation_rows_are_not_ordinary_f6(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            builder.build_package(out)

            with (out / "f6_candidate_inventory.csv").open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))

            self.assertTrue(rows)
            self.assertEqual({"recirculation_diagnostic"}, {row["primary_classification"] for row in rows})
            self.assertEqual({"blocked_material_recirculation"}, {row["ordinary_f6_admission_status"] for row in rows})
            self.assertTrue(all("ordinary_F6" in row["blocked_labels"] for row in rows))

    def test_f3_scorecard_has_no_promoted_lane(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            builder.build_package(out)

            with (out / "f6_vs_f3_scorecard.csv").open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))

            self.assertEqual({"ordinary_F6_single_stream", "recirculation_modeled_F6_onset"}, {row["model_lane"] for row in rows})
            self.assertEqual({"do_not_promote"}, {row["decision"] for row in rows})
            self.assertEqual({"F3_shah_apparent"}, {row["production_baseline"] for row in rows})


if __name__ == "__main__":
    unittest.main()
