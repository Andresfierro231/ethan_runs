from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.extract import build_s13_upcomer_exchange_limited_sampled_field_scheduler_extraction as builder


class S13LimitedSampledFieldSchedulerExtractionTests(unittest.TestCase):
    def test_area_weighted_wall_temperature(self) -> None:
        rows = [
            {"patch_name": "a", "owner": 1, "area_m2": 2.0},
            {"patch_name": "a", "owner": 2, "area_m2": 1.0},
            {"patch_name": "b", "owner": 3, "area_m2": 3.0},
        ]
        fields = {1: {"T": 300.0}, 2: {"T": 330.0}, 3: {"T": 360.0}}
        result = builder.area_weighted_wall_temperature(rows, fields)
        self.assertAlmostEqual(result["area_m2"], 6.0)
        self.assertAlmostEqual(result["T_area_K"], 335.0)
        self.assertAlmostEqual(result["patch_T"]["a"], 310.0)
        self.assertAlmostEqual(result["patch_T"]["b"], 360.0)

    def test_downstream_gates_keep_production_paths_closed(self) -> None:
        gates = {row["gate"]: row for row in builder.downstream_rows()}
        self.assertEqual(gates["limited_sampled_field_extraction"]["allowed"], "true")
        self.assertEqual(gates["Q_wall_W_release"]["allowed"], "false")
        self.assertEqual(gates["sampler_manifest_refresh"]["allowed"], "false")
        self.assertEqual(gates["production_harvest_uq_admission"]["allowed"], "false")

    def test_guardrails_record_scheduler_only_when_job_id_present(self) -> None:
        no_job = {row["guard_id"]: row for row in builder.guardrail_rows("")}
        with_job = {row["guard_id"]: row for row in builder.guardrail_rows("12345")}
        self.assertEqual(no_job["scheduler_action"]["changed"], "false")
        self.assertEqual(with_job["scheduler_action"]["changed"], "true")
        self.assertEqual(with_job["sampler_harvest_uq_admission"]["changed"], "false")

    def test_write_sbatch_uses_execute_mode_and_task_log(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "pkg"
            script = builder.write_sbatch(out)
            text = script.read_text(encoding="utf-8")
            self.assertIn("#SBATCH -J s13_limsamp", text)
            self.assertIn("--execute", text)
            self.assertIn("--slurm-job-id", text)
            self.assertTrue((out / "logs").is_dir())


if __name__ == "__main__":
    unittest.main()
