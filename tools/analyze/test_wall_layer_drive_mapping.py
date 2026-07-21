"""Tests for TODO-PRED-WALL-LAYER wall-layer drive mapping."""

from __future__ import annotations

import csv
import importlib.util
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "tools/analyze/build_wall_layer_drive_mapping.py"
OUT = ROOT / "work_products/2026-07/2026-07-13/2026-07-13_wall_layer_drive_mapping"


def _load_module():
    spec = importlib.util.spec_from_file_location("build_wall_layer_drive_mapping", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod


builder = _load_module()


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_inverse_drive_uses_wallheatflux_into_fluid_sign():
    signed, loss_pos = builder.inverse_drive_from_wallheatflux(
        q_into_fluid_w=-20.0,
        hA_w_k=2.0,
        ta_k=300.0,
    )
    assert signed == 310.0
    assert loss_pos == 310.0

    signed_gain, loss_pos_gain = builder.inverse_drive_from_wallheatflux(
        q_into_fluid_w=20.0,
        hA_w_k=2.0,
        ta_k=300.0,
    )
    assert signed_gain == 290.0
    assert loss_pos_gain == 300.0


def test_radiation_and_convection_zero_when_drive_equals_ambient_and_surroundings():
    conv, rad, total = builder.heat_loss_from_drive(
        area_m2=2.0,
        h_w_m2k=5.0,
        ta_k=300.0,
        tsur_k=300.0,
        emissivity=0.95,
        drive_k=300.0,
    )
    assert conv == 0.0
    assert rad == 0.0
    assert total == 0.0


def test_radiation_positive_for_hot_drive():
    conv, rad, total = builder.heat_loss_from_drive(
        area_m2=1.0,
        h_w_m2k=4.0,
        ta_k=300.0,
        tsur_k=300.0,
        emissivity=0.95,
        drive_k=350.0,
    )
    assert conv and conv > 0.0
    assert rad and rad > 0.0
    assert total and total > conv


def test_real_artifact_build_outputs_expected_rows():
    result = subprocess.run([sys.executable, str(SCRIPT)], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr

    drive_rows = _read_csv(OUT / "external_bc_drive_table.csv")
    replay_rows = _read_csv(OUT / "external_bc_replay_modes.csv")
    block_rows = _read_csv(OUT / "blocked_rows.csv")
    parity_rows = _read_csv(OUT / "section_heat_parity.csv")

    assert len(drive_rows) == 24
    assert len(replay_rows) == 72
    assert len(parity_rows) == 51
    assert len(block_rows) == 21
    assert {row["case_id"] for row in drive_rows} == {"salt_2", "salt_3", "salt_4"}
    assert any(row["T_fwd_bulk_K"] for row in drive_rows)
    assert any(row["T_wall_shell_K"] for row in drive_rows)
    assert any("high_recirculation" in row["recirculation_status"] for row in drive_rows)
    assert all(
        "wallHeatFlux is total" in row["radiation_policy"]
        for row in drive_rows
        if row["radiation_policy"]
    )


def test_wall_shell_and_beta_modes_execute_where_supported():
    subprocess.run([sys.executable, str(SCRIPT)], cwd=ROOT, check=True, capture_output=True, text=True)
    replay_rows = _read_csv(OUT / "external_bc_replay_modes.csv")

    counts = Counter((row["mode"], row["executable"]) for row in replay_rows)
    assert counts[("E0_bulk", "yes")] == 18
    assert counts[("E1_wall_shell", "yes")] == 21
    assert counts[("E2_low_dimensional_blend", "yes")] == 12
    assert counts[("E2_low_dimensional_blend", "no")] == 12

    e2_executable = [
        row
        for row in replay_rows
        if row["mode"] == "E2_low_dimensional_blend" and row["executable"] == "yes"
    ]
    assert {row["role"] for row in e2_executable} == {"ambient_wall"}
    assert all(row["beta_family_id"] for row in e2_executable)
    assert all(row["beta_value"] in {"0", "1"} for row in e2_executable)
    assert all(
        row["beta_fit_status"] == "diagnostic_same_case_family_fit_no_validation_split"
        for row in e2_executable
    )


if __name__ == "__main__":
    test_inverse_drive_uses_wallheatflux_into_fluid_sign()
    test_radiation_and_convection_zero_when_drive_equals_ambient_and_surroundings()
    test_radiation_positive_for_hot_drive()
    test_real_artifact_build_outputs_expected_rows()
    test_wall_shell_and_beta_modes_execute_where_supported()
    print("wall_layer_drive_mapping tests passed")
