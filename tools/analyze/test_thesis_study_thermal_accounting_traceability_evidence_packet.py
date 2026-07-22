#!/usr/bin/env python3
"""Tests for the thermal accounting traceability evidence packet."""

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

from tools.analyze import build_thesis_study_thermal_accounting_traceability_evidence_packet as builder


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class ThermalAccountingTraceabilityPacketTest(unittest.TestCase):
    def test_build_outputs_core_tables_and_guardrails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "packet"
            summary = builder.build(out)
            self.assertEqual(
                summary["decision"],
                "thermal_accounting_traceability_packet_ready_no_fit_no_runtime_leakage",
            )
            self.assertEqual(summary["heat_path_ledger_rows"], 10)
            self.assertEqual(summary["setup_source_sink_rows"], 12)
            self.assertEqual(summary["missing_setup_field_rows"], 5)
            self.assertGreaterEqual(summary["diagnostic_heat_value_rows"], 15)
            self.assertFalse(summary["runtime_wallHeatFlux_or_validation_temperature_release"])
            self.assertFalse(summary["source_property_release"])
            self.assertFalse(summary["coefficient_admission"])
            self.assertFalse(summary["residual_absorbed_into_internal_nu"])
            self.assertEqual(summary["validation_holdout_external_rows_scored"], 0)

            for name in [
                "thermal_accounting_traceability_ledger.csv",
                "setup_source_sink_values.csv",
                "diagnostic_heat_values_by_case_role.csv",
                "passive_wall_segment_response.csv",
                "junction_stub_traceability_rows.csv",
                "missing_setup_fields.csv",
                "residual_owner_gate_matrix.csv",
                "runtime_forbidden_input_audit.csv",
                "figure_table_caption_targets.csv",
                "source_manifest.csv",
                "no_mutation_guardrails.csv",
                "README.md",
                "summary.json",
            ]:
                self.assertTrue((out / name).exists(), name)
            json.loads((out / "summary.json").read_text(encoding="utf-8"))

    def test_forbidden_inputs_are_explicit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "packet"
            builder.build(out)
            forbidden = {row["forbidden_input"]: row for row in rows(out / "runtime_forbidden_input_audit.csv")}
            self.assertIn("realized CFD wallHeatFlux", forbidden)
            self.assertIn("validation temperatures", forbidden)
            self.assertIn("imposed CFD cooler duty", forbidden)
            self.assertIn("internal Nu residual absorption", forbidden)
            self.assertTrue(all(row["runtime_allowed"] == "False" for row in forbidden.values()))
            self.assertTrue(all(row["fit_allowed"] == "False" for row in forbidden.values()))

    def test_owner_matrix_keeps_accounting_before_fitting(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "packet"
            builder.build(out)
            owner_rows = rows(out / "residual_owner_gate_matrix.csv")
            owners = {row["owner_family"]: row for row in owner_rows}
            self.assertIn("passive_wall_and_external_boundary", owners)
            self.assertIn("test_section_source_or_loss", owners)
            self.assertIn("junction_stub_heat", owners)
            self.assertIn("radiation", owners)
            self.assertIn("upcomer_exchange_and_internal_Nu", owners)
            self.assertTrue(all(row["admission_allowed"] == "False" for row in owner_rows))
            self.assertTrue(all(row["runtime_release_allowed"] == "False" for row in owner_rows))

    def test_setup_values_are_traceable_not_runtime_released(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "packet"
            builder.build(out)
            source_rows = rows(out / "setup_source_sink_values.csv")
            self.assertEqual(len(source_rows), 12)
            roles = {row["physical_role"] for row in source_rows}
            self.assertEqual(roles, {"heater", "cooler", "test_section"})
            self.assertTrue(all(row["runtime_allowed_now"] in {"false", "False"} for row in source_rows))


if __name__ == "__main__":
    unittest.main()
