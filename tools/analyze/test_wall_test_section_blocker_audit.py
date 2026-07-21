#!/usr/bin/env python3
"""Tests for AGENT-531 wall/test-section blocker audit."""

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

from tools.analyze import build_wall_test_section_blocker_audit as mod


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class WallTestSectionBlockerAuditTests(unittest.TestCase):
    def test_cross_candidate_matrix_includes_final_agent511_and_agent522(self) -> None:
        rows = mod.build_cross_candidate_residual_matrix()
        packages = {row["source_package"] for row in rows}
        families = {row["candidate_family"] for row in rows}

        self.assertIn("AGENT-511_heater_source_redistribution", packages)
        self.assertIn("AGENT-522_wall_thermal_circuit", packages)
        self.assertIn("HS1_heater_source_redistribution", families)
        self.assertIn("HIW1_heated_incline_pipe_wall_drive", families)
        self.assertGreaterEqual(len(rows), 34)
        self.assertTrue(all(row["score_gate"] == "fail" for row in rows))

    def test_sensor_audit_keeps_tw5_tw6_scoreable_and_tp2_tw10_excluded(self) -> None:
        probes = mod.build_probe_residual_atlas()
        sensor_rows = mod.build_sensor_map_candidate_audit(probes)

        tw5 = [row for row in sensor_rows if row["sensor"] == "TW5"]
        tw6 = [row for row in sensor_rows if row["sensor"] == "TW6"]
        tp2 = [row for row in sensor_rows if row["sensor"] == "TP2"]
        tw10 = [row for row in sensor_rows if row["sensor"] == "TW10"]

        self.assertTrue(tw5)
        self.assertTrue(tw6)
        self.assertTrue(any(row["policy_source_segment"] == "heated_incline" for row in tw5))
        self.assertTrue(any(row["audit_status"] == "scoreable_residual_failure" for row in tw5))
        self.assertTrue(any(row["audit_status"] == "scoreable_residual_failure" for row in tw6))
        self.assertTrue(all(row["audit_status"] == "policy_excluded_junction_or_restore_target" for row in tp2))
        self.assertTrue(all(row["audit_status"] == "policy_excluded_active_hx_shell_state" for row in tw10))

    def test_invariant_failures_include_heated_incline_tw(self) -> None:
        probes = mod.build_probe_residual_atlas()
        roles = mod.build_role_segment_residual_atlas()
        failures = mod.build_invariant_failure_modes(probes, roles)

        self.assertTrue(failures)
        heated_tw = [
            row for row in failures
            if row["kind"] == "TW" and row["prediction_source_segment"] == "heated_incline"
        ]
        self.assertTrue(heated_tw)
        self.assertTrue(any("TW5" in row["sensor_scope"] or "role_rmse" in row["failure_mode_id"] for row in heated_tw))

    def test_admission_sanity_preserves_zero_admission(self) -> None:
        matrix = mod.build_cross_candidate_residual_matrix()
        sanity = mod.build_admission_gate_sanity(matrix)

        self.assertGreaterEqual(len(sanity), 17)
        self.assertTrue(all(row["admission_decision"] == "not_admitted" for row in sanity))
        self.assertTrue(any(row["candidate_family"] == "HS1_heater_source_redistribution" for row in sanity))
        self.assertTrue(any(row["tw_gate"] == "fail" for row in sanity))
        self.assertTrue(any(row["all_probe_gate"] == "fail" for row in sanity))

    def test_next_lane_decision_defers_solver_overlap_and_keeps_blocker_open(self) -> None:
        probes = mod.build_probe_residual_atlas()
        sensors = mod.build_sensor_map_candidate_audit(probes)
        matrix = mod.build_cross_candidate_residual_matrix()
        failures = mod.build_invariant_failure_modes(probes, mod.build_role_segment_residual_atlas())
        decision = mod.build_next_lane_decision(sensors, matrix, failures)[0]

        self.assertEqual(decision["decision"], "axial_mixing_candidate_next_after_AGENTS526")
        self.assertEqual(decision["blocker_status_after_audit"], "open")
        self.assertIn("AGENT-526", decision["active_collision"])
        self.assertEqual(decision["scientific_admission_change"], "none")

    def test_main_writes_complete_package_to_tempdir(self) -> None:
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
                summary = mod.main(["--parallel-workers", "8", "--timeout-seconds", "273"])

                self.assertEqual(summary["admitted_candidates"], 0)
                self.assertEqual(summary["blocker_status_after_audit"], "open")
                self.assertEqual(summary["next_lane_decision"], "axial_mixing_candidate_next_after_AGENTS526")
                for name in [
                    "cross_candidate_residual_matrix.csv",
                    "probe_residual_atlas.csv",
                    "sensor_map_candidate_audit.csv",
                    "role_segment_residual_atlas.csv",
                    "invariant_failure_modes.csv",
                    "admission_gate_sanity.csv",
                    "next_lane_decision.csv",
                    "runtime_request_audit.csv",
                    "source_manifest.csv",
                    "summary.json",
                    "README.md",
                ]:
                    self.assertTrue((out / name).exists(), name)
                self.assertTrue(status.exists())
                self.assertTrue(journal.exists())
                self.assertTrue(import_manifest.exists())

                matrix = read_csv(out / "cross_candidate_residual_matrix.csv")
                self.assertTrue(any(row["source_package"] == "AGENT-522_wall_thermal_circuit" for row in matrix))

                with import_manifest.open(encoding="utf-8") as handle:
                    manifest = json.load(handle)
                self.assertEqual(manifest["task"], mod.TASK)
                self.assertFalse(manifest["scheduler_action"])
                self.assertFalse(manifest["solver_or_postprocessing_launched"])
                self.assertEqual(manifest["scientific_admission_change"], "none")


if __name__ == "__main__":
    unittest.main()
