from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from tools.extract.postprocessing_registry_common import (
    WALL_HEAT_GROUPED_COLUMNS,
    bucket_for_case,
    build_wall_heat_grouped_rows,
    load_velocity_profile_rows_from_runtime,
    write_case_aggregation,
)


class PostprocessingRegistryCommonTest(unittest.TestCase):
    def test_bucket_for_case(self) -> None:
        self.assertEqual(bucket_for_case("salt_test_2_jin", "hitec_salt_jin"), "salt2")
        self.assertEqual(bucket_for_case("water_test_4", "water"), "water4")
        self.assertEqual(bucket_for_case("mystery_case", "water"), "extended_water")

    def test_wall_heat_grouped_columns_keep_total_q_first(self) -> None:
        context = {
            "source_root": Path("/tmp/nonexistent_case"),
            "meta_row": {"cooling_power_W": "10.0"},
        }
        wall_heat_rows = [
            {"time_s": 1.0, "patch": "pipeleg_upper_05_cooler", "q_net_w": -12.0},
            {"time_s": 1.0, "patch": "pipeleg_lower_05_straight", "q_net_w": 5.0},
            {"time_s": 1.0, "patch": "junction_lower_left", "q_net_w": -2.0},
        ]
        grouped = build_wall_heat_grouped_rows(context, wall_heat_rows, [{"time": 1.0, "value": -9.0}])
        self.assertEqual(list(grouped[0].keys()), WALL_HEAT_GROUPED_COLUMNS)
        self.assertEqual(grouped[0]["total_Q_postProc"], -9.0)

    def test_write_case_aggregation_smoke(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            run_root = Path(tmpdir) / "salt2" / "owner" / "salt_test_2_kirst" / "demo_run"
            payload = {
                "run_root": run_root,
                "aggregate_root": run_root / "aggregates",
                "normalized_rows": [
                    {
                        "source_id": "demo",
                        "source_owner": "owner",
                        "case_id": "salt_test_2_kirst",
                        "bucket": "salt2",
                        "run_name": "demo_run",
                        "dataset": "temperature_probe",
                        "time_s": 1.0,
                        "entity_name": "TP1",
                        "value_name": "temperature_K",
                        "value": 450.0,
                        "units": "K",
                        "x_m": 0.0,
                        "y_m": 0.0,
                        "z_m": 0.0,
                        "distance_m": None,
                        "profile_time_s": None,
                        "profile_axis": "",
                        "profile_level": None,
                        "source_file_relpath": "postProcessing/temperature_probes/0/T",
                    }
                ],
                "grouped_heat_rows": [
                    {
                        "total_Q_postProc": -10.0,
                        "time_s": 1.0,
                        "ambient_proxy_w": 2.0,
                        "ambient_noncooling_proxy_w": 1.0,
                        "cooling_branch_total_removal_w": 5.0,
                        "cooling_branch_excess_w": 0.0,
                        "section_downcomer_net_q_w": 0.0,
                        "section_heater_net_q_w": 4.0,
                        "section_upcomer_net_q_w": 0.0,
                        "section_test_section_net_q_w": 0.0,
                        "section_cooling_branch_net_q_w": -5.0,
                        "section_upper_transport_net_q_w": 0.0,
                        "section_lower_transport_net_q_w": 0.0,
                        "section_junctions_net_q_w": -1.0,
                        "section_other_net_q_w": 0.0,
                    }
                ],
                "summary_row": {
                    "generated_at": "2026-06-25T12:00:00-05:00",
                    "source_id": "demo",
                    "source_owner": "owner",
                    "case_id": "salt_test_2_kirst",
                    "bucket": "salt2",
                    "run_name": "demo_run",
                    "fluid": "hitec_salt_kirst",
                    "variant_label": "kirst",
                    "source_root": "/tmp/source",
                    "runtime_root": "/tmp/source",
                    "mdot_monitor_count": 4,
                    "mdot_all_same": 1,
                    "mdot_consensus_kg_s": 0.01,
                    "mdot_mean_abs_kg_s": 0.01,
                    "mdot_abs_min_kg_s": 0.01,
                    "mdot_abs_max_kg_s": 0.01,
                    "mdot_abs_spread_kg_s": 0.0,
                    "mdot_discrepancy_note": "",
                    "latest_total_Q_postProc_w": -10.0,
                    "latest_piv_magU_m_s": 0.1,
                    "latest_tp_avg_k": 450.0,
                    "latest_tw_station_count": 11,
                    "latest_velocity_profile_time_s": 100.0,
                    "latest_yplus_time_s": 100.0,
                    "latest_wall_shear_time_s": 100.0,
                    "comparison_ready": "comparison_candidate",
                    "run_status": "completed",
                    "disposition_note": "synthetic",
                },
                "manifest": {
                    "generated_at": "2026-06-25T12:00:00-05:00",
                    "source_id": "demo",
                    "storage_format": "sqlite",
                },
            }
            outputs = write_case_aggregation(payload)
            sqlite_path = Path(outputs["sqlite_db"])
            self.assertTrue(sqlite_path.exists())
            with sqlite3.connect(sqlite_path) as connection:
                tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            self.assertEqual(tables, {"postprocessing_case_long", "wall_heat_flux_grouped", "case_summary"})

    def test_load_velocity_profile_rows_from_runtime(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            runtime_root = Path(tmpdir)
            profile_dir = runtime_root / "postProcessing" / "velocity_profiles" / "10.0"
            profile_dir.mkdir(parents=True, exist_ok=True)
            (profile_dir / "Y_H_0.50_X.xy").write_text(
                "# synthetic\n0.0 1.0 2.0 3.0\n0.1 1.5 2.5 3.5\n",
                encoding="utf-8",
            )
            context = {
                "source_id": "demo",
                "source_owner": "owner",
                "case_id": "salt_test_2_kirst",
                "bucket": "salt2",
                "run_name": "demo_run",
                "runtime_root": runtime_root,
            }
            rows = load_velocity_profile_rows_from_runtime(context)
            self.assertEqual(len(rows), 6)
            self.assertEqual({row["dataset"] for row in rows}, {"velocity_profile"})
            self.assertEqual({row["profile_axis"] for row in rows}, {"X"})
            self.assertEqual({row["profile_level"] for row in rows}, {0.5})
            self.assertEqual({row["profile_time_s"] for row in rows}, {10.0})


if __name__ == "__main__":
    unittest.main()
