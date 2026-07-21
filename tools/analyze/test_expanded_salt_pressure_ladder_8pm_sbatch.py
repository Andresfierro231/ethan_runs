#!/usr/bin/env python3
"""Focused checks for AGENT-447 expanded Salt pressure-ladder package."""

from __future__ import annotations

import csv
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "work_products/2026-07/2026-07-15/2026-07-15_expanded_salt_pressure_ladder_8pm_sbatch"


def rows(name: str) -> list[dict[str, str]]:
    with (OUT / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_preflight() -> None:
    pre = rows("pressure_ladder_preflight.csv")
    assert len(pre) == 8
    assert all(row["preflight_status"] == "pass" for row in pre)
    assert all(row["station_count"] == "30" for row in pre)
    assert {row["case_key"] for row in pre} == {
        "salt1_nominal",
        "salt1_lo10q",
        "salt1_hi10q",
        "salt2_lo5q",
        "salt2_hi5q",
        "salt4_lo5q",
        "salt4_hi5q",
        "val_salt2",
    }
    assert "holdout_perturbation" in {row["split_role"] for row in pre}
    assert "external_validation" in {row["split_role"] for row in pre}


def test_scripts_parse() -> None:
    for row in rows("scripts_manifest.csv"):
        subprocess.run(["bash", "-n", str(ROOT / row["path"])], check=True)


def test_summary_guardrails() -> None:
    summary = json.loads((OUT / "summary.json").read_text(encoding="utf-8"))
    assert summary["task"] == "AGENT-447"
    assert summary["preflight_failures"] == 0
    assert summary["submitted_begin_time"] == "2026-07-15T20:00:00"
    assert summary["native_solver_outputs_mutated"] is False
    assert summary["registry_or_admission_mutated"] is False


if __name__ == "__main__":
    test_preflight()
    test_scripts_parse()
    test_summary_guardrails()
    print("AGENT-447 tests passed")
