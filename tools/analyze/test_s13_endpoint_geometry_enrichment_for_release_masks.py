#!/usr/bin/env python3
"""Tests for the S13 endpoint geometry enrichment gate."""

from __future__ import annotations

import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.analyze import build_s13_endpoint_geometry_enrichment_for_release_masks as builder  # noqa: E402


class S13EndpointGeometryEnrichmentTest(unittest.TestCase):
    @staticmethod
    def rows(path: Path) -> list[dict[str, str]]:
        with path.open(newline="", encoding="utf-8") as handle:
            return list(csv.DictReader(handle))

    def build_tmp(self) -> tuple[Path, dict[str, object]]:
        out = Path(tempfile.mkdtemp())
        with mock.patch.object(builder, "OUT", out):
            summary = builder.build()
        with (out / "summary.json").open(encoding="utf-8") as handle:
            summary_from_disk = json.load(handle)
        self.assertEqual(summary, summary_from_disk)
        return out, summary

    def test_endpoint_rows_fail_closed_without_release_masks(self) -> None:
        out, summary = self.build_tmp()
        self.assertEqual(summary["decision"], "s13_endpoint_geometry_enrichment_fail_closed_release_masks_zero")
        self.assertEqual(summary["candidate_endpoint_rows"], 6)
        self.assertEqual(summary["released_endpoint_masks"], 0)
        self.assertEqual(summary["harvest_ready_cases"], 0)
        rows = self.rows(out / "endpoint_geometry_enrichment_gate.csv")
        self.assertEqual(len(rows), 6)
        self.assertEqual({row["release_mask_ready"] for row in rows}, {"False"})
        self.assertEqual({row["residual_value_release_allowed"] for row in rows}, {"False"})

    def test_missing_fields_are_exact_geometry_blockers(self) -> None:
        out, summary = self.build_tmp()
        self.assertEqual(summary["missing_release_fields"], ["area_m2", "area_vector_x_m2", "area_vector_y_m2", "area_vector_z_m2", "owner_cell"])
        matrix = self.rows(out / "mandatory_release_field_matrix.csv")
        missing = {row["mandatory_field"] for row in matrix if row["ready_for_release_mask"] == "False"}
        self.assertEqual(missing, set(summary["missing_release_fields"]))

    def test_harvest_and_claim_ledgers_do_not_release_residuals(self) -> None:
        out, _summary = self.build_tmp()
        harvest = self.rows(out / "residual_harvest_release_gate.csv")
        self.assertEqual(len(harvest), 3)
        self.assertEqual({row["harvest_ready"] for row in harvest}, {"False"})
        self.assertEqual({row["residual_value_release_allowed"] for row in harvest}, {"False"})
        claims = self.rows(out / "thesis_claim_ledger.csv")
        claim_map = {row["claim"]: row["allowed"] for row in claims}
        self.assertEqual(claim_map["S13 candidate cap masks exist and are useful for next geometry regeneration"], "True")
        self.assertEqual(claim_map["S13 residual values can be computed now"], "False")
        self.assertEqual(claim_map["Missing heat residual can be absorbed into internal Nu"], "False")

    def test_guardrails_and_manifest_are_clean(self) -> None:
        out, summary = self.build_tmp()
        for key in [
            "native_solver_outputs_mutated",
            "scheduler_action",
            "source_property_release",
            "Qwall_release",
            "residual_value_release",
            "endpoint_proxy_substitution",
            "residual_absorbed_into_internal_Nu",
        ]:
            self.assertIs(summary[key], False, key)
        manifest = self.rows(out / "source_manifest.csv")
        self.assertTrue(manifest)
        self.assertEqual({row["exists"] for row in manifest}, {"True"})
        self.assertEqual({row["read_only"] for row in manifest}, {"True"})


if __name__ == "__main__":
    unittest.main()
