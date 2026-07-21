#!/usr/bin/env python3
"""Tests for AGENT-248 pressure-only package generator."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "tools/analyze/build_salt2_refined_pressure_smoke_and_8pm_batch.py"
PKG = ROOT / "work_products/2026-07/2026-07-10/2026-07-10_salt2_refined_pressure_smoke_and_8pm_batch"


def test_generator_contract() -> None:
    subprocess.run([sys.executable, str(SCRIPT)], cwd=ROOT, check=True)
    payload = json.loads((PKG / "summary.json").read_text(encoding="utf-8"))
    assert payload["task_id"] == "AGENT-248"
    assert payload["scheduled_start"] == "2026-07-10T20:00:00"
    assert payload["source_cases_read_only"] is True
    runner = (PKG / "scripts/run_pressure_extraction.sh").read_text(encoding="utf-8")
    assert "--dump-temperature" not in runner
    assert "fields '(p_rgh U rho wallShearStress yPlus)'" in runner
    assert "assert_sampled_sections" in runner
    assert "thermal_status" in runner
