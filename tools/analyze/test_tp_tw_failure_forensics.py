#!/usr/bin/env python3
"""Tests for AGENT-536 TP/TW failure-forensics matrices."""

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

from tools.analyze import build_tp_tw_failure_forensics as mod


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class TpTwFailureForensicsTests(unittest.TestCase):
    def test_sensor_rank_surfaces_scoreable_tw_failures(self) -> None:
        rows = mod.rank_sensor_failures()
        sensors = {row["sensor"]: row for row in rows}

        self.assertIn("TW5", sensors)
        self.assertIn("TW6", sensors)
        self.assertEqual(sensors["TW5"]["prediction_source_segment"], "heated_incline")
        self.assertIn("scoreable heated-incline", sensors["TW5"]["evidence_read"])
        self.assertIn("upcomer", sensors["TW5"]["required_physics"])
        self.assertGreater(float(sensors["TW5"]["worst_abs_error_delta_vs_m3_K"]), 70.0)
        self.assertLessEqual(int(sensors["TW5"]["rank"]), 3)

    def test_role_segment_rank_identifies_heated_incline_tw(self) -> None:
        rows = mod.rank_role_segment_failures()
        top = rows[0]

        self.assertEqual(top["kind"], "TW")
        self.assertEqual(top["prediction_source_segment"], "heated_incline")
        self.assertGreaterEqual(int(top["candidate_families_failed"]), 8)
        self.assertIn("upcomer", top["required_physics"])

    def test_family_matrix_keeps_all_families_not_admitted_and_blocks_tswfc1(self) -> None:
        rows = mod.candidate_family_gate_matrix()
        by_family = {row["candidate_family"]: row for row in rows}

        self.assertIn("TSWFC1_bulk_to_ambient_series_resistance", by_family)
        self.assertIn("HS1_heater_source_redistribution", by_family)
        self.assertTrue(all(row["admission_status"] == "not_admitted" for row in rows))
        self.assertEqual(
            by_family["TSWFC1_bulk_to_ambient_series_resistance"]["family_gate"],
            "blocked_do_not_duplicate_single_node_wall_fluid_fallback",
        )
        self.assertIn("do not rerun AGENT-526", by_family["TSWFC1_bulk_to_ambient_series_resistance"]["do_not_repeat"])
        self.assertIn("tw", by_family["TSWFC1_bulk_to_ambient_series_resistance"]["failed_dimensions"])

    def test_requirements_and_contract_put_umx1_before_tswfc2(self) -> None:
        sensor_rows = mod.rank_sensor_failures()
        role_rows = mod.rank_role_segment_failures()
        requirements = mod.physics_requirement_matrix(sensor_rows, role_rows)
        contracts = mod.next_model_contract()

        requirement_ids = [row["requirement_id"] for row in requirements]
        self.assertEqual(requirement_ids[0], "R1_upcomer_exchange_stratification")
        self.assertIn("CFD mdot", requirements[0]["runtime_forbidden_inputs"])
        self.assertEqual(contracts[0]["model_family"], "UMX1_energy_conserving_upcomer_exchange")
        self.assertEqual(contracts[2]["model_family"], "TSWFC2_distributed_test_section_wall_fluid_nodes")
        self.assertIn("missing Fluid hook", contracts[0]["hard_no_go"])

    def test_build_writes_requested_outputs_and_manifest(self) -> None:
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
                summary = mod.build()

            self.assertEqual(summary["decision"], "contract_first_no_grid")
            self.assertEqual(summary["admitted_candidate_families"], 0)
            self.assertEqual(summary["scientific_admission_change"], "none")
            for name in [
                "sensor_failure_rank.csv",
                "role_segment_failure_rank.csv",
                "candidate_family_gate_matrix.csv",
                "physics_requirement_matrix.csv",
                "next_model_contract.csv",
                "runtime_request_audit.csv",
                "source_manifest.csv",
                "summary.json",
                "README.md",
            ]:
                self.assertTrue((out / name).exists(), name)
            self.assertTrue(status.exists())
            self.assertTrue(journal.exists())
            self.assertTrue(import_manifest.exists())

            families = read_csv(out / "candidate_family_gate_matrix.csv")
            self.assertTrue(
                any(row["candidate_family"] == "TSWFC1_bulk_to_ambient_series_resistance" for row in families)
            )
            contracts = read_csv(out / "next_model_contract.csv")
            self.assertEqual(contracts[0]["contract_id"], "UMX1_static_api_audit")
            with (out / "summary.json").open(encoding="utf-8") as handle:
                on_disk = json.load(handle)
            self.assertEqual(on_disk["recommended_next_model"], "UMX1_energy_conserving_upcomer_exchange")
            with import_manifest.open(encoding="utf-8") as handle:
                manifest = json.load(handle)
            self.assertFalse(manifest["scheduler_action"])
            self.assertFalse(manifest["solver_or_postprocessing_launched"])
            self.assertEqual(manifest["scientific_admission_change"], "none")


if __name__ == "__main__":
    unittest.main()
