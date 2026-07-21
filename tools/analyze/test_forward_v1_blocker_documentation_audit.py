"""Tests for forward-v1 blocker documentation audit."""

from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path

from tools.analyze.build_forward_v1_blocker_documentation_audit import build_package


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class ForwardV1BlockerDocumentationAuditTests(unittest.TestCase):
    def test_all_blockers_have_sufficient_docs(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            summary = build_package(Path(tmp))
            self.assertEqual(summary["blocker_count"], 7)
            self.assertEqual(summary["sufficient_rows"], 7)
            self.assertEqual(summary["missing_primary_docs"], 0)
            self.assertEqual(summary["missing_supporting_docs"], 0)
            self.assertTrue(summary["all_blockers_have_plain_language_why"])
            self.assertTrue(summary["all_blockers_have_next_unblock_artifact"])
            self.assertFalse(summary["scientific_admission_state_changed"])

    def test_matrix_covers_expected_blockers(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            out = Path(tmp)
            build_package(out)
            rows = {row["blocker_id"]: row for row in read_csv(out / "blocker_documentation_matrix.csv")}
            self.assertEqual(
                set(rows),
                {
                    "fluid_reset_development_api",
                    "hydraulic_h1_pressure_evidence",
                    "pm5_matched_pressure_upcomer_metrics",
                    "perturbation_split_policy",
                    "thermal_internal_nu",
                    "boundary_hx_wall_radiation",
                    "sensor_map_policy",
                },
            )
            self.assertIn("API support is not pressure evidence", rows["fluid_reset_development_api"]["why_blocked_plain_language"])
            self.assertIn("job_id=3295901", rows["pm5_matched_pressure_upcomer_metrics"]["proof_numbers"])
            self.assertIn("setup_only_boundary_hx_outputs.csv", rows["boundary_hx_wall_radiation"]["next_unblock_artifact"])

    def test_evidence_chain_all_paths_exist(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            out = Path(tmp)
            build_package(out)
            rows = read_csv(out / "blocker_evidence_chain.csv")
            self.assertGreater(len(rows), 7)
            self.assertTrue(all(row["artifact_status"] == "exists" for row in rows))

    def test_outputs_written(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            out = Path(tmp)
            build_package(out)
            for name in {
                "README.md",
                "blocker_documentation_matrix.csv",
                "blocker_evidence_chain.csv",
                "blocker_reading_guide.md",
                "source_manifest.csv",
                "summary.json",
            }:
                self.assertTrue((out / name).exists(), name)
            parsed = json.loads((out / "summary.json").read_text(encoding="utf-8"))
            self.assertEqual(parsed["task"], "AGENT-371")


if __name__ == "__main__":
    unittest.main()
