#!/usr/bin/env python3
"""Tests for AGENT-474 Closure-QOI final-use disposition closeout."""

from __future__ import annotations

import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_closure_qoi_final_use_disposition_closeout as builder  # noqa: E402


class ClosureQoiFinalUseDispositionTests(unittest.TestCase):
    def test_builder_resolves_when_all_rows_are_admitted_or_excluded(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            summary = builder.build_package(out)

            self.assertEqual(summary["task"], "AGENT-474")
            self.assertEqual(summary["blocker_decision"], "resolved_by_final_use_disposition")
            self.assertEqual(summary["final_use_rows_reviewed"], 13)
            self.assertEqual(summary["retained_extraction_required_rows"], 0)
            self.assertEqual(summary["admitted_publication_gci_rows"], 0)
            self.assertEqual(summary["excluded_rows"], 13)

            for filename in [
                "README.md",
                "closure_qoi_final_use_disposition.csv",
                "gci_results_admitted_only.csv",
                "extraction_required_rows.csv",
                "blocker_decision.csv",
                "closure_qoi_resolution_decision.md",
                "source_manifest.csv",
                "summary.json",
            ]:
                self.assertTrue((out / filename).exists(), filename)

            written = json.loads((out / "summary.json").read_text(encoding="utf-8"))
            self.assertEqual(written["retained_extraction_required_rows"], 0)

    def test_disposition_rules_preserve_branch_and_boundary_reasons(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            builder.build_package(out)

            with (out / "closure_qoi_final_use_disposition.csv").open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))

            by_leg: dict[str, set[str]] = {}
            for row in rows:
                by_leg.setdefault(row["canonical_leg_id"], set()).add(row["final_use_disposition"])

            self.assertEqual(by_leg["heater_lower_leg"], {"excluded_branch_gate_failed"})
            self.assertEqual(by_leg["downcomer_right_vertical"], {"excluded_branch_gate_failed"})
            self.assertEqual(by_leg["cooler_hx_branch"], {"excluded_boundary_residual"})
            self.assertTrue(all(row["blocks_closure_qoi_mesh_gci"] == "no" for row in rows))

    def test_admitted_only_and_extraction_required_exports_are_header_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            builder.build_package(out)

            for filename in ["gci_results_admitted_only.csv", "extraction_required_rows.csv"]:
                with (out / filename).open(newline="", encoding="utf-8") as handle:
                    rows = list(csv.DictReader(handle))
                self.assertEqual(rows, [], filename)

    def test_unknown_leg_would_keep_blocker_open(self) -> None:
        row = {
            "qoi_id": "unknown::row",
            "canonical_leg_id": "new_leg",
            "reported_span_or_segment": "new",
            "qoi_family": "closure",
            "quantity": "Nu",
            "current_publication_ready": "no",
            "current_fit_admissible": "no",
            "complete_triplet": "no",
            "gci_status": "not_computed",
            "final_use_decision": "unknown",
            "resolution_action": "extract same-QOI triplet",
            "source_paths": "source.csv",
        }
        disposed = builder.dispose_row(row)
        self.assertEqual(disposed["final_use_disposition"], "retain_requires_extraction")
        self.assertEqual(disposed["blocks_closure_qoi_mesh_gci"], True)


if __name__ == "__main__":
    unittest.main()
