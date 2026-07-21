#!/usr/bin/env python3
"""Tests for AGENT-467 recirculation feature/admission contract."""

from __future__ import annotations

import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_recirc_feature_admission_and_hybrid_contract as builder  # noqa: E402


class RecircFeatureAdmissionHybridContractTests(unittest.TestCase):
    def test_package_counts_and_decision(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            summary = builder.build_package(out)

            self.assertEqual(summary["task"], "AGENT-467")
            self.assertGreaterEqual(summary["feature_rows"], 15)
            self.assertEqual(summary["single_stream_allowed_rows"], 0)
            self.assertGreater(summary["recirculating_lane_rows"], 0)
            self.assertEqual(summary["ordinary_coefficient_claim"], "not_admitted")
            self.assertEqual(summary["hybrid_lane_contract"], "published")

            written = json.loads((out / "summary.json").read_text(encoding="utf-8"))
            self.assertEqual(written["feature_rows"], summary["feature_rows"])

    def test_current_rows_block_single_stream_coefficients(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            builder.build_package(out)

            with (out / "recirculation_feature_admission_table.csv").open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))

            self.assertTrue(rows)
            self.assertEqual({"no"}, {row["single_stream_fit_allowed"] for row in rows})
            self.assertTrue(
                all("f_D" in row["blocked_labels"] for row in rows if row["canonical_lane"] == "recirculating_upcomer_effective")
            )

    def test_contract_preserves_test_section_as_upcomer_subspan(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            builder.build_package(out)

            with (out / "hybrid_1d_model_contract.csv").open(newline="", encoding="utf-8") as handle:
                contract_rows = list(csv.DictReader(handle))
            lanes = {row["model_lane"]: row for row in contract_rows}

            self.assertIn("test_section_upcomer_subspan", lanes)
            self.assertIn("standalone_non_upcomer_Nu_fit", lanes["test_section_upcomer_subspan"]["forbidden_labels"])
            self.assertIn("M3+TS", lanes["test_section_upcomer_subspan"]["solver_facing_behavior"])

    def test_m3ts_candidates_remain_future_queue_items(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            builder.build_package(out)

            with (out / "next_extraction_queue.csv").open(newline="", encoding="utf-8") as handle:
                queue_rows = list(csv.DictReader(handle))
            queue_ids = {row["queue_id"] for row in queue_rows}

            self.assertIn("m3ts_candidate:TS1_salt2_fit_hA_constant_drive_deltaT", queue_ids)
            self.assertIn("m3ts_candidate:TS2_salt2_fit_constant_loss_W", queue_ids)


if __name__ == "__main__":
    unittest.main()
