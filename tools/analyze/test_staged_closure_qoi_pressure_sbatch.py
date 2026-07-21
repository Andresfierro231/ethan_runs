#!/usr/bin/env python3
"""Focused checks for AGENT-440 staged closure-QOI/pressure sbatch package."""

from __future__ import annotations

import csv
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "work_products/2026-07/2026-07-15/2026-07-15_staged_closure_qoi_pressure_sbatch"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_package_contract() -> None:
    summary = json.loads((OUT / "summary.json").read_text(encoding="utf-8"))
    submitted = json.loads((OUT / "submitted_job.json").read_text(encoding="utf-8"))
    assert summary["task"] == "AGENT-440"
    assert summary["native_solver_outputs_mutated"] is False
    assert summary["registry_or_admission_mutated"] is False
    assert summary["preflight_failures"] == 0
    assert summary["preflight_rows"] == 3
    assert submitted["job_id"] == "3297845"


def test_preflight_table() -> None:
    rows = read_csv(OUT / "raw_pressure_preflight.csv")
    assert len(rows) == 3
    assert {row["case_key"] for row in rows} == {"salt2_mainline", "salt3_mainline", "salt4_mainline"}
    assert all(row["preflight_status"] == "pass" for row in rows)
    assert all(row["processor_time_exists"] == "true" for row in rows)
    assert all(row["native_solver_outputs_mutated"] == "false" for row in rows)


def test_shell_scripts_parse() -> None:
    for rel in [
        "scripts/run_staged_closure_qoi_raw_pressure.sh",
        "scripts/submit_staged_closure_qoi_raw_pressure.sbatch",
    ]:
        subprocess.run(["bash", "-n", str(OUT / rel)], check=True)


def test_harvest_table_parses_submitted_surface_output() -> None:
    rows = read_csv(OUT / "raw_pressure_two_tap_harvest.csv")
    assert len(rows) == 3
    assert {row["case_key"] for row in rows} == {"salt2_mainline", "salt3_mainline", "salt4_mainline"}
    assert {row["surface_function"] for row in rows} <= {
        "agent440RawPressureSurfaces",
        "agent440ClosurePressureSurfaces",
    }
    assert all(row["admission_status"] == "diagnostic_staged_copy_raw_pressure_not_fit_admitted" for row in rows)
    assert all(row["fit_eligible"] == "no" for row in rows)
    assert all(int(row["lower_face_count"]) > 0 for row in rows)
    assert all(int(row["upper_face_count"]) > 0 for row in rows)


if __name__ == "__main__":
    test_package_contract()
    test_preflight_table()
    test_shell_scripts_parse()
    test_harvest_table_parses_submitted_surface_output()
    print("AGENT-440 tests passed")
