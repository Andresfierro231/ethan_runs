from __future__ import annotations

import json
import math
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools.analyze.build_ethan_latest_window_frozen_state_stack import (
    CASE_ANALYSIS_MODULE_CHECK,
    DEFAULT_FREEZE_WINDOWS_CSV,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_REPRESENTATIVE_TIMESTEPS_CSV,
    TARGET_REPRESENTATIVE_COUNT,
    branch_drift_rollup,
    canonical_time_token,
    frozen_state_contract_rows,
    load_representative_times,
    resolve_case_analysis_python,
    write_import_manifest,
)


class EthanLatestWindowFrozenStateStackTests(unittest.TestCase):
    def test_canonical_time_token_matches_processor_labels(self) -> None:
        self.assertEqual(canonical_time_token("5378.0"), "5378")
        self.assertEqual(canonical_time_token("3617.6625"), "3617.6625")
        self.assertEqual(canonical_time_token("3398.45"), "3398.45")

    def test_frozen_state_contract_flags_short_window_but_keeps_case_candidate(self) -> None:
        rows = frozen_state_contract_rows(
            [
                {
                    "source_id": "src",
                    "case_label": "Salt 1 Jin",
                    "representative_time_count": TARGET_REPRESENTATIVE_COUNT - 2,
                    "late_window_time_start_s": 0.0,
                    "late_window_time_end_s": 10.0,
                    "latest_retained_time_s": 10.0,
                    "window_status": "window_shortfall",
                    "window_status_note": "short",
                    "package_root": "/tmp/pkg",
                    "runtime_root": "/tmp/run",
                    "profile_name": "demo",
                    "branch_rows": [
                        {"branch_name": "right_leg", "mean_bulk_temp_fluid_area_avg_k": "452.0"},
                        {"branch_name": "upcomer", "mean_bulk_temp_fluid_area_avg_k": "454.5"},
                        {"branch_name": "lower_leg", "mean_bulk_temp_fluid_area_avg_k": "447.0"},
                        {"branch_name": "upper_leg", "mean_bulk_temp_fluid_area_avg_k": "450.0"},
                    ],
                }
            ]
        )
        self.assertEqual(rows[0]["comparison_ready"], "comparison_candidate")
        self.assertEqual(rows[0]["window_status"], "window_shortfall")
        self.assertAlmostEqual(rows[0]["downcomer_to_upcomer_bulk_delta_k"], -2.5)
        self.assertAlmostEqual(rows[0]["heater_to_cooler_bulk_delta_k"], -3.0)

    def test_branch_drift_rollup_averages_only_finite_values(self) -> None:
        rows = branch_drift_rollup(
            [
                {
                    "branch_name": "left_lower_leg",
                    "bulk_latest_vs_mean_fraction": 0.1,
                    "wall_latest_vs_mean_fraction": 0.2,
                    "htc_latest_vs_mean_fraction": 0.3,
                },
                {
                    "branch_name": "left_lower_leg",
                    "bulk_latest_vs_mean_fraction": math.nan,
                    "wall_latest_vs_mean_fraction": 0.4,
                    "htc_latest_vs_mean_fraction": 0.5,
                },
            ]
        )
        self.assertEqual(len(rows), 1)
        self.assertAlmostEqual(rows[0]["mean_bulk_latest_vs_mean_fraction"], 0.1)
        self.assertAlmostEqual(rows[0]["mean_wall_latest_vs_mean_fraction"], 0.3)
        self.assertAlmostEqual(rows[0]["mean_htc_latest_vs_mean_fraction"], 0.4)
        self.assertAlmostEqual(rows[0]["max_htc_latest_vs_mean_fraction"], 0.5)

    def test_default_paths_use_nested_june_23_report_tree(self) -> None:
        self.assertEqual(
            DEFAULT_FREEZE_WINDOWS_CSV,
            DEFAULT_FREEZE_WINDOWS_CSV.parents[1] / "2026-06-23_ethan_cfd_freeze_checkpoint" / "freeze_case_windows.csv",
        )
        self.assertEqual(
            DEFAULT_REPRESENTATIVE_TIMESTEPS_CSV,
            DEFAULT_REPRESENTATIVE_TIMESTEPS_CSV.parents[1]
            / "2026-06-23_ethan_cfd_freeze_checkpoint"
            / "representative_timesteps.csv",
        )
        self.assertEqual(
            DEFAULT_OUTPUT_DIR,
            DEFAULT_OUTPUT_DIR.parent / "2026-06-23_ethan_frozen_state_results_latest_window",
        )
        self.assertEqual(DEFAULT_OUTPUT_DIR.parent.name, "2026-06-23")
        self.assertEqual(DEFAULT_OUTPUT_DIR.parent.parent.name, "2026-06")

    def test_import_manifest_records_requested_checkpoint_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            manifest_path = root / "import.json"
            checkpoint_root = root / "checkpoint"
            output_dir = root / "output"
            output_dir.mkdir()
            write_import_manifest(
                freeze_windows_csv=root / "freeze_case_windows.csv",
                representative_timesteps_csv=root / "representative_timesteps.csv",
                checkpoint_root=checkpoint_root,
                output_dir=output_dir,
                case_refresh_rows=[],
                import_manifest_path=manifest_path,
            )
            payload = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["inputs"]["checkpoint_root"], str(checkpoint_root.resolve()))

    def test_resolve_case_analysis_python_falls_back_to_plain_python(self) -> None:
        def fake_run(command: list[str], **_kwargs: object) -> mock.Mock:
            executable = command[0]
            self.assertEqual(command[1:], ["-c", CASE_ANALYSIS_MODULE_CHECK])
            result = mock.Mock()
            result.returncode = 1 if executable.endswith("python3.11") else 0
            return result

        with mock.patch(
            "tools.analyze.build_ethan_latest_window_frozen_state_stack.sys.executable",
            "/usr/bin/python3.11",
        ):
            with mock.patch(
                "tools.analyze.build_ethan_latest_window_frozen_state_stack.subprocess.run",
                side_effect=fake_run,
            ) as run_mock:
                self.assertEqual(resolve_case_analysis_python(), "python")
        self.assertEqual(run_mock.call_count, 2)


if __name__ == "__main__":
    unittest.main()
