from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path

from tools.common import csv_dump, ensure_dir
from tools.extract.postprocessing_registry_common import NORMALIZED_COLUMNS, case_context

ROOT = Path(__file__).resolve().parents[2]
SOURCE_ID = "viscosity_screening_salt_test_2_kirst_coarse_mesh"


class PostprocessingPlotScriptsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        context = case_context(SOURCE_ID)
        aggregate_root = ensure_dir(ROOT / "tmp" / "test_postprocessing_plots" / "aggregates")
        cls.aggregate_csv = aggregate_root / "postprocessing_case_long.csv"
        rows = [
            {
                "source_id": SOURCE_ID,
                "source_owner": context["source_owner"],
                "case_id": context["case_id"],
                "bucket": context["bucket"],
                "run_name": context["run_name"],
                "dataset": "temperature_probe",
                "time_s": 0.0,
                "entity_name": "TP1",
                "value_name": "temperature_K",
                "value": 447.0,
                "units": "K",
                "x_m": 0.0,
                "y_m": 0.0,
                "z_m": 0.0,
                "distance_m": "",
                "profile_time_s": "",
                "profile_axis": "",
                "profile_level": "",
                "source_file_relpath": "synthetic",
            },
            {
                "source_id": SOURCE_ID,
                "source_owner": context["source_owner"],
                "case_id": context["case_id"],
                "bucket": context["bucket"],
                "run_name": context["run_name"],
                "dataset": "temperature_probe",
                "time_s": 1.0,
                "entity_name": "TP1",
                "value_name": "temperature_K",
                "value": 448.0,
                "units": "K",
                "x_m": 0.0,
                "y_m": 0.0,
                "z_m": 0.0,
                "distance_m": "",
                "profile_time_s": "",
                "profile_axis": "",
                "profile_level": "",
                "source_file_relpath": "synthetic",
            },
            {
                "source_id": SOURCE_ID,
                "source_owner": context["source_owner"],
                "case_id": context["case_id"],
                "bucket": context["bucket"],
                "run_name": context["run_name"],
                "dataset": "temperature_probe",
                "time_s": 0.0,
                "entity_name": "TP4",
                "value_name": "temperature_K",
                "value": 447.5,
                "units": "K",
                "x_m": 0.0,
                "y_m": 0.0,
                "z_m": 0.0,
                "distance_m": "",
                "profile_time_s": "",
                "profile_axis": "",
                "profile_level": "",
                "source_file_relpath": "synthetic",
            },
            {
                "source_id": SOURCE_ID,
                "source_owner": context["source_owner"],
                "case_id": context["case_id"],
                "bucket": context["bucket"],
                "run_name": context["run_name"],
                "dataset": "temperature_probe",
                "time_s": 1.0,
                "entity_name": "TP4",
                "value_name": "temperature_K",
                "value": 448.5,
                "units": "K",
                "x_m": 0.0,
                "y_m": 0.0,
                "z_m": 0.0,
                "distance_m": "",
                "profile_time_s": "",
                "profile_axis": "",
                "profile_level": "",
                "source_file_relpath": "synthetic",
            },
            {
                "source_id": SOURCE_ID,
                "source_owner": context["source_owner"],
                "case_id": context["case_id"],
                "bucket": context["bucket"],
                "run_name": context["run_name"],
                "dataset": "wall_temperature_station",
                "time_s": 0.0,
                "entity_name": "TW1",
                "value_name": "temperature_K",
                "value": 450.0,
                "units": "K",
                "x_m": 0.0,
                "y_m": 0.0,
                "z_m": 0.0,
                "distance_m": "",
                "profile_time_s": "",
                "profile_axis": "",
                "profile_level": "",
                "source_file_relpath": "synthetic",
            },
            {
                "source_id": SOURCE_ID,
                "source_owner": context["source_owner"],
                "case_id": context["case_id"],
                "bucket": context["bucket"],
                "run_name": context["run_name"],
                "dataset": "wall_temperature_station",
                "time_s": 1.0,
                "entity_name": "TW1",
                "value_name": "temperature_K",
                "value": 451.0,
                "units": "K",
                "x_m": 0.0,
                "y_m": 0.0,
                "z_m": 0.0,
                "distance_m": "",
                "profile_time_s": "",
                "profile_axis": "",
                "profile_level": "",
                "source_file_relpath": "synthetic",
            },
            {
                "source_id": SOURCE_ID,
                "source_owner": context["source_owner"],
                "case_id": context["case_id"],
                "bucket": context["bucket"],
                "run_name": context["run_name"],
                "dataset": "wall_temperature_station",
                "time_s": 0.0,
                "entity_name": "TW5",
                "value_name": "temperature_K",
                "value": 452.0,
                "units": "K",
                "x_m": 0.0,
                "y_m": 0.0,
                "z_m": 0.0,
                "distance_m": "",
                "profile_time_s": "",
                "profile_axis": "",
                "profile_level": "",
                "source_file_relpath": "synthetic",
            },
            {
                "source_id": SOURCE_ID,
                "source_owner": context["source_owner"],
                "case_id": context["case_id"],
                "bucket": context["bucket"],
                "run_name": context["run_name"],
                "dataset": "wall_temperature_station",
                "time_s": 1.0,
                "entity_name": "TW5",
                "value_name": "temperature_K",
                "value": 453.0,
                "units": "K",
                "x_m": 0.0,
                "y_m": 0.0,
                "z_m": 0.0,
                "distance_m": "",
                "profile_time_s": "",
                "profile_axis": "",
                "profile_level": "",
                "source_file_relpath": "synthetic",
            },
        ]
        for profile_time in (586.0, 586.56):
            for axis in ("X", "Z"):
                for level in (0.25, 0.5):
                    for distance, value in ((0.0, 0.0), (0.01, 0.02 + level + profile_time / 10000.0)):
                        rows.append(
                            {
                                "source_id": SOURCE_ID,
                                "source_owner": context["source_owner"],
                                "case_id": context["case_id"],
                                "bucket": context["bucket"],
                                "run_name": context["run_name"],
                                "dataset": "velocity_profile",
                                "time_s": profile_time,
                                "entity_name": f"Y_H_{level:.2f}_{axis}",
                                "value_name": "U_y_m_s",
                                "value": value,
                                "units": "m/s",
                                "x_m": "",
                                "y_m": "",
                                "z_m": "",
                                "distance_m": distance,
                                "profile_time_s": profile_time,
                                "profile_axis": axis,
                                "profile_level": level,
                                "source_file_relpath": "synthetic",
                            }
                        )
        csv_dump(cls.aggregate_csv, NORMALIZED_COLUMNS, rows)

    def test_temperature_probe_plot_cli(self) -> None:
        output_dir = ROOT / "tmp" / "test_postprocessing_plots" / "tp"
        subprocess.run(
            [
                "python3",
                "tools/analyze/plot_temperature_probes.py",
                "--source-id",
                SOURCE_ID,
                "--output-name",
                "tp_smoke",
                "--output-dir",
                str(output_dir),
                "--input-csv",
                str(self.aggregate_csv),
                "--include",
                "TP1",
                "TP4",
            ],
            cwd=ROOT,
            check=True,
        )
        metadata = json.loads((output_dir / "tp_smoke.json").read_text(encoding="utf-8"))
        self.assertEqual(metadata["included_series"], ["TP1", "TP4"])
        self.assertTrue((output_dir / "svg" / "tp_smoke.svg").exists())
        self.assertTrue((output_dir / "png" / "tp_smoke.png").exists())

    def test_wall_temperature_plot_cli(self) -> None:
        output_dir = ROOT / "tmp" / "test_postprocessing_plots" / "tw"
        subprocess.run(
            [
                "python3",
                "tools/analyze/plot_wall_temperature_probes.py",
                "--source-id",
                SOURCE_ID,
                "--output-name",
                "tw_smoke",
                "--output-dir",
                str(output_dir),
                "--input-csv",
                str(self.aggregate_csv),
                "--include",
                "TW1",
                "TW5",
            ],
            cwd=ROOT,
            check=True,
        )
        metadata = json.loads((output_dir / "tw_smoke.json").read_text(encoding="utf-8"))
        self.assertEqual(metadata["included_series"], ["TW1", "TW5"])
        self.assertTrue((output_dir / "svg" / "tw_smoke.svg").exists())
        self.assertTrue((output_dir / "png" / "tw_smoke.png").exists())

    def test_velocity_profile_plot_cli(self) -> None:
        output_dir = ROOT / "tmp" / "test_postprocessing_plots" / "velocity"
        subprocess.run(
            [
                "python3",
                "tools/analyze/plot_velocity_profiles.py",
                "--source-id",
                SOURCE_ID,
                "--output-name",
                "velocity_smoke",
                "--output-dir",
                str(output_dir),
                "--input-csv",
                str(self.aggregate_csv),
                "--times",
                "586.56",
                "--component",
                "Uy",
                "--profile-axis",
                "both",
            ],
            cwd=ROOT,
            check=True,
        )
        metadata = json.loads((output_dir / "velocity_smoke.json").read_text(encoding="utf-8"))
        self.assertEqual(metadata["component"], "Uy")
        self.assertTrue(metadata["matched_times"])
        self.assertTrue((output_dir / "svg" / "velocity_smoke.svg").exists())
        self.assertTrue((output_dir / "png" / "velocity_smoke.png").exists())


if __name__ == "__main__":
    unittest.main()
