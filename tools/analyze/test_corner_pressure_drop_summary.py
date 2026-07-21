#!/usr/bin/env python3
from __future__ import annotations

import csv
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.analyze.summarize_corner_pressure_drops import (
    build_candidate,
    choose_best_candidates,
    summarize_candidate,
)


def write_feature_csv(path: Path, rows: list[dict[str, str]]) -> None:
    fieldnames = list(rows[0].keys())
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


class CornerPressureDropSummaryTest(unittest.TestCase):
    def test_choose_best_candidate_prefers_more_available_times(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            short_csv = root / "pkg_short" / "feature_minor_loss_timeseries.csv"
            long_csv = root / "pkg_long" / "feature_minor_loss_timeseries.csv"
            base_row = {
                "source_id": "viscosity_screening_salt_test_2_jin_coarse_mesh",
                "time_s": "",
                "feature_name": "corner_lower_left",
                "feature_kind": "corner",
                "start_patch": "a",
                "end_patch": "b",
                "start_p_pa": "0",
                "end_p_pa": "0",
                "delta_p_pa": "0",
                "start_p_rgh_pa": "1",
                "end_p_rgh_pa": "0",
                "delta_p_rgh_pa": "-1",
                "abs_delta_p_rgh_pa": "1",
                "profile_dp_pa": "nan",
                "wall_dp_pa": "nan",
                "minor_residual_dp_pa": "nan",
                "minor_k_reference": "nan",
                "warning_flag": "0",
                "note": "",
                "reference_length_m": "1",
                "reference_major_dp_pa": "1",
            }
            rows_short = [dict(base_row, time_s=str(value)) for value in (1, 2, 3)]
            rows_long = [dict(base_row, time_s=str(value)) for value in (1, 2, 3, 4, 5)]
            write_feature_csv(short_csv, rows_short)
            write_feature_csv(long_csv, rows_long)

            selected = choose_best_candidates(
                [build_candidate(short_csv), build_candidate(long_csv)],  # type: ignore[list-item]
                set(),
            )
            self.assertEqual(len(selected), 1)
            self.assertEqual(selected[0].package_dir.name, "pkg_long")

    def test_summary_math_reports_start_end_and_drop_signs(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            feature_csv = root / "pkg" / "feature_minor_loss_timeseries.csv"
            rows = [
                {
                    "source_id": "viscosity_screening_salt_test_2_jin_coarse_mesh",
                    "time_s": "10",
                    "feature_name": "corner_lower_left",
                    "feature_kind": "corner",
                    "start_patch": "start_a",
                    "end_patch": "end_a",
                    "start_p_pa": "100",
                    "end_p_pa": "90",
                    "delta_p_pa": "-10",
                    "start_p_rgh_pa": "5",
                    "end_p_rgh_pa": "3",
                    "delta_p_rgh_pa": "-2",
                    "abs_delta_p_rgh_pa": "2",
                    "profile_dp_pa": "nan",
                    "wall_dp_pa": "nan",
                    "minor_residual_dp_pa": "nan",
                    "minor_k_reference": "nan",
                    "warning_flag": "0",
                    "note": "",
                    "reference_length_m": "1",
                    "reference_major_dp_pa": "1",
                },
                {
                    "source_id": "viscosity_screening_salt_test_2_jin_coarse_mesh",
                    "time_s": "11",
                    "feature_name": "corner_lower_left",
                    "feature_kind": "corner",
                    "start_patch": "start_a",
                    "end_patch": "end_a",
                    "start_p_pa": "120",
                    "end_p_pa": "110",
                    "delta_p_pa": "-10",
                    "start_p_rgh_pa": "7",
                    "end_p_rgh_pa": "4",
                    "delta_p_rgh_pa": "-3",
                    "abs_delta_p_rgh_pa": "3",
                    "profile_dp_pa": "nan",
                    "wall_dp_pa": "nan",
                    "minor_residual_dp_pa": "nan",
                    "minor_k_reference": "nan",
                    "warning_flag": "yes",
                    "note": "",
                    "reference_length_m": "1",
                    "reference_major_dp_pa": "1",
                },
            ]
            write_feature_csv(feature_csv, rows)
            candidate = build_candidate(feature_csv)
            assert candidate is not None

            summary_rows = summarize_candidate(candidate, [2])
            self.assertEqual(len(summary_rows), 1)
            target = next(row for row in summary_rows if row["feature_name"] == "corner_lower_left")
            self.assertAlmostEqual(target["mean_start_p_rgh_pa"], 6.0)
            self.assertAlmostEqual(target["mean_end_p_rgh_pa"], 3.5)
            self.assertAlmostEqual(target["mean_delta_p_rgh_pa"], -2.5)
            self.assertAlmostEqual(target["mean_pressure_drop_start_to_end_rgh_pa"], 2.5)
            self.assertEqual(target["warning_row_count"], 1)


if __name__ == "__main__":
    unittest.main()
