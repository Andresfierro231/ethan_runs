#!/usr/bin/env python3
"""Tests for Salt1 final predictive schema promotion artifacts."""

from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools.analyze import build_salt1_schema_promotion as mod


class Salt1SchemaPromotionTest(unittest.TestCase):
    def test_split_manifest_promotes_admitted_salt1_rows(self) -> None:
        rows = mod.build_split_manifest()
        by_case = {row["case_key"]: row for row in rows}

        self.assertEqual(set(by_case), set(mod.SALT1_CASES))
        self.assertEqual(by_case["salt1_nominal"]["canonical_split_role"], "final_training")
        self.assertEqual(by_case["salt1_lo10q"]["canonical_split_role"], "training_support")
        self.assertEqual(by_case["salt1_hi10q"]["canonical_split_role"], "training_support")
        for row in rows:
            self.assertEqual(row["schema_promotion_status"], "promoted")
            self.assertEqual(row["admission_status"], "admitted")
            self.assertEqual(row["do_not_collapse_q_ratio"], "true")
            self.assertEqual(
                row["operational_provenance"],
                "operational_stop_or_cancel_not_clean_endTime_completion",
            )

    def test_heat_ledger_has_source_sink_buckets_and_runtime_guardrails(self) -> None:
        rows = mod.build_patchwise_heat_ledger()
        by_key = {(row["case_key"], row["section_bucket"]): row for row in rows}

        self.assertEqual(len(rows), len(mod.SALT1_CASES) * len(mod.BUCKET_ORDER))
        for case in mod.SALT1_CASES:
            self.assertEqual(
                {row["section_bucket"] for row in rows if row["case_key"] == case},
                set(mod.BUCKET_ORDER),
            )

        nominal_heater = by_key[("salt1_nominal", "heater")]
        nominal_cooler = by_key[("salt1_nominal", "cooler_HX")]
        nominal_test_section = by_key[("salt1_nominal", "test_section")]
        self.assertAlmostEqual(float(nominal_heater["setup_imposed_net_to_fluid_W"]), 232.3)
        self.assertAlmostEqual(float(nominal_test_section["setup_imposed_net_to_fluid_W"]), 37.0)
        self.assertAlmostEqual(
            float(nominal_cooler["setup_imposed_net_to_fluid_W"]),
            -135.6031778466,
        )
        self.assertEqual(
            nominal_heater["runtime_model_use"],
            "setup_boundary_metadata_allowed_realized_heat_scoring_only",
        )
        self.assertEqual(nominal_heater["realized_wallHeatFlux_status"], "not_reduced_in_this_package")
        self.assertEqual(nominal_heater["admission_status"], "admitted_setup_source_sink_schema")
        self.assertEqual(
            by_key[("salt1_nominal", "passive_wall")]["admission_status"],
            "diagnostic_setup_metadata_realized_heat_not_reduced",
        )

    def test_pressure_sensor_and_runtime_rows_are_target_only(self) -> None:
        streamwise, branch = mod.build_pressure_rows()
        sensors = mod.build_sensor_target_rows()
        audit = mod.build_runtime_input_audit()

        self.assertEqual(len(streamwise), 90)
        self.assertEqual(len(branch), 18)
        self.assertTrue(all(row["runtime_pressure_allowed"] == "false" for row in streamwise))
        self.assertTrue(all(row["pressure_model_use"] == "diagnostic_target_only_not_fit_admitted" for row in branch))

        self.assertEqual(len(sensors), 51)
        tp2_rows = [row for row in sensors if row["sensor"] == "TP2"]
        self.assertEqual(len(tp2_rows), 3)
        self.assertTrue(all(row["runtime_temperature_allowed"] == "false" for row in sensors))
        self.assertTrue(all(row["fit_allowed"] == "false" for row in sensors))
        self.assertEqual(
            {row["source_segment"] for row in tp2_rows},
            {"right_downcomer_bottom_horizontal_junction"},
        )

        self.assertEqual(len(audit), 5)
        self.assertTrue(all(row["gate"] == "pass" for row in audit))
        forbidden = {row["forbidden_runtime_input"] for row in audit}
        self.assertIn("CFD mdot", forbidden)
        self.assertIn("realized CFD wallHeatFlux", forbidden)
        self.assertIn("imposed CFD cooler duty", forbidden)
        self.assertIn("validation temperatures", forbidden)

    def test_main_writes_complete_promotion_package(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            out = base / "out"
            status = base / "status.md"
            journal = base / "journal.md"
            import_manifest = base / "import.json"
            with (
                mock.patch.object(mod, "OUT", out),
                mock.patch.object(mod, "STATUS", status),
                mock.patch.object(mod, "JOURNAL", journal),
                mock.patch.object(mod, "IMPORT", import_manifest),
            ):
                summary = mod.main()
            self.assertEqual(summary["promoted_cases"], 3)
            self.assertEqual(summary["streamwise_pressure_rows"], 90)
            self.assertEqual(summary["branch_pressure_rows"], 18)
            self.assertEqual(summary["runtime_audit_pass_rows"], 5)
            self.assertTrue(summary["all_sources_present"])
            self.assertTrue((out / "salt1_split_ready_manifest.csv").exists())
            self.assertTrue((out / "runtime_input_audit.csv").exists())
            self.assertTrue(status.exists())
            self.assertTrue(journal.exists())
            self.assertTrue(import_manifest.exists())

            with (out / "salt1_split_ready_manifest.csv").open(newline="") as f:
                split_rows = list(csv.DictReader(f))
            self.assertEqual(len(split_rows), 3)
            with import_manifest.open() as f:
                manifest = json.load(f)
            self.assertFalse(manifest["native_solver_outputs_mutated"])
            self.assertFalse(manifest["generated_index_refreshed"])


if __name__ == "__main__":
    unittest.main()
