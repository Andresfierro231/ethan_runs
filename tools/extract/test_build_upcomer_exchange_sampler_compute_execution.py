from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.extract import build_upcomer_exchange_sampler_compute_execution as builder


class UpcomerExchangeSamplerComputeExecutionTests(unittest.TestCase):
    def test_readiness_has_three_primary_ready_source_windows(self) -> None:
        rows = builder.readiness_rows()
        self.assertEqual(len(rows), 3)
        self.assertEqual({row["case_id"] for row in rows}, {"salt_2", "salt_3", "salt_4"})
        self.assertTrue(all(row["missing_primary_fields"] == "" for row in rows))
        self.assertTrue(all(row["source_case_exists"] == "true" for row in rows))
        self.assertTrue(all(row["existing_recon_time_dir_exists"] == "true" for row in rows))

    def test_cell_volume_gap_blocks_submission_but_optional_mu_does_not(self) -> None:
        readiness = builder.readiness_rows()
        gaps = builder.gap_rows(readiness)
        cell_volume = [row for row in gaps if row["field_or_diagnostic"] == "cellVolume"]
        mu = [row for row in gaps if row["field_or_diagnostic"] == "mu"]
        self.assertEqual(len(cell_volume), 3)
        self.assertTrue(all(row["current_status"] == "missing" for row in cell_volume))
        self.assertTrue(all(row["blocking_for_compute_sample"] == "true" for row in cell_volume))
        self.assertEqual(len(mu), 3)
        self.assertTrue(all(row["current_status"] == "optional_missing" for row in mu))
        self.assertTrue(all(row["blocking_for_compute_sample"] == "false" for row in mu))

    def test_submission_decision_is_no_submit(self) -> None:
        decision = builder.decision_rows(builder.readiness_rows())[0]
        self.assertEqual(decision["submitted"], "false")
        self.assertEqual(decision["scheduler_action"], "false")
        self.assertIn("cellVolume", decision["reason"])

    def test_build_package_writes_expected_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "pkg"
            payload = builder.build_package(out)
            self.assertEqual(payload["summary"]["case_rows"], 3)
            self.assertEqual(payload["summary"]["primary_ready_rows"], 3)
            self.assertEqual(payload["summary"]["decision_status"], "not_submitted_blocked")
            for name in [
                "source_case_readiness.csv",
                "required_field_gap.csv",
                "compute_submission_decision.csv",
                "execution_script_plan.csv",
                "no_mutation_guardrails.csv",
                "next_agent_handoff.csv",
                "source_manifest.csv",
                "summary.json",
                "README.md",
                "scripts/run_upcomer_exchange_sampler_compute.sh",
                "scripts/submit_upcomer_exchange_sampler_compute.sbatch",
            ]:
                self.assertTrue((out / name).exists(), name)


if __name__ == "__main__":
    unittest.main()
