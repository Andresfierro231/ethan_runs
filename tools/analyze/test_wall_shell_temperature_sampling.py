"""Tests for TODO-PRED-WALL-SHELL-SAMPLE wall-shell proxy extraction."""

from __future__ import annotations

import csv
import importlib.util
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "tools/analyze/build_wall_shell_temperature_sampling.py"
OUT = ROOT / "work_products/2026-07/2026-07-13/2026-07-13_wall_shell_temperature_sampling"


def _load_module():
    spec = importlib.util.spec_from_file_location("build_wall_shell_temperature_sampling", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod


builder = _load_module()


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_stats_reports_mean_min_max_std():
    values = [1.0, 2.0, 3.0]
    stat = builder.stats(values)
    assert stat["mean"] == 2.0
    assert stat["min"] == 1.0
    assert stat["max"] == 3.0
    assert round(stat["std"], 6) == round((2.0 / 3.0) ** 0.5, 6)


def test_real_artifact_build_outputs_supported_rows():
    result = subprocess.run([sys.executable, str(SCRIPT)], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    patch_rows = _read_csv(OUT / "patch_wall_shell_temperatures.csv")
    segment_rows = _read_csv(OUT / "segment_wall_shell_temperatures.csv")

    assert len(patch_rows) == 108
    assert len(segment_rows) == 21
    assert {row["case_id"] for row in patch_rows} == {"salt_2", "salt_3", "salt_4"}
    assert all(row["support_status"] == "ok_patch_internal_owner_cell_proxy" for row in patch_rows)
    assert all(row["T_wall_shell_K"] for row in segment_rows)
    assert all(row["proxy_definition"] == "boundary_face_owner_cell_temperature_mean_area_weighted_by_patch" for row in segment_rows)


if __name__ == "__main__":
    test_stats_reports_mean_min_max_std()
    test_real_artifact_build_outputs_supported_rows()
    print("wall_shell_temperature_sampling tests passed")
