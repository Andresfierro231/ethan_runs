#!/usr/bin/env python3
"""Tests for hydraulic tap-length admission refresh."""

from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path

from tools.analyze.build_hydraulic_tap_length_admission_refresh import build_package


def _read_csv(path: Path):
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


class HydraulicTapLengthAdmissionRefreshTests(unittest.TestCase):
    def test_summary_guardrails_and_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            summary = build_package(out)

            expected = {
                "README.md",
                "summary.json",
                "source_manifest.csv",
                "tap_centerline_length_table.csv",
                "component_cluster_k_recomputed_admission_table.csv",
                "h1_faithful_readiness_after_tap_refresh.csv",
            }
            self.assertEqual(expected, {path.name for path in out.iterdir()})
            self.assertFalse(summary["native_solver_outputs_mutated"])
            self.assertFalse(summary["thermal_fit_used"])
            self.assertFalse(summary["global_multiplier_exported"])
            self.assertFalse(summary["external_fluid_code_edited"])

            persisted = json.loads((out / "summary.json").read_text(encoding="utf-8"))
            self.assertEqual(summary["centerline_resolved_rows"], persisted["centerline_resolved_rows"])

    def test_existing_centerlines_resolve_preserved_corner_rows_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            summary = build_package(out)
            rows = _read_csv(out / "tap_centerline_length_table.csv")

            self.assertEqual(15, len(rows))
            self.assertEqual(12, summary["centerline_resolved_rows"])
            self.assertEqual(3, summary["centerline_blocked_rows"])
            blocked = [row for row in rows if row["centerline_length_status"] != "resolved_from_existing_mesh_centerline"]
            self.assertEqual({"test_section_complex"}, {row["feature"] for row in blocked})
            self.assertTrue(
                all(float(row["centerline_tap_length_m"]) > float(row["current_tap_length_proxy_m"]) for row in rows if row["centerline_tap_length_m"])
            )

    def test_recomputed_k_admission_remains_not_fit_admissible(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            summary = build_package(out)
            rows = _read_csv(out / "component_cluster_k_recomputed_admission_table.csv")

            self.assertEqual(0, summary["component_fit_admissible_rows"])
            self.assertFalse(any(row["admission_status"] == "candidate_fit_admissible" for row in rows))
            self.assertTrue(any(row["admission_status"] == "blocked_mesh_gci_after_tap_refresh" for row in rows))
            self.assertTrue(any(row["admission_status"] == "diagnostic_only_recirculation_adjacent" for row in rows))
            self.assertTrue(all(row["coefficient_name_allowed"] == "no_universal_K_yet" for row in rows))

    def test_h1_readiness_gate_blocks_launch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            summary = build_package(out)
            rows = _read_csv(out / "h1_faithful_readiness_after_tap_refresh.csv")

            self.assertFalse(summary["h1_faithful_launchable"])
            gate = {row["gate_id"]: row for row in rows}
            self.assertEqual("not_launchable", gate["H1_faithful_rerun"]["current_status"])
            self.assertIn("not admitted", gate["H1_faithful_rerun"]["blocking_gap"])


if __name__ == "__main__":
    unittest.main()
