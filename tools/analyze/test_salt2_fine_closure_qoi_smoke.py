#!/usr/bin/env python3
"""Lightweight assertions for the Salt2 refined closure-QOI runner generator."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "tools/analyze/build_salt2_fine_closure_qoi_smoke.py"
PACKAGE = ROOT / "work_products/2026-07/2026-07-09/2026-07-09_salt2_fine_closure_qoi_smoke_and_overnight"


def test_generator_outputs_expected_contract() -> None:
    subprocess.run([sys.executable, str(SCRIPT)], cwd=ROOT, check=True)
    summary = json.loads((PACKAGE / "summary.json").read_text(encoding="utf-8"))

    assert summary["task"] == "AGENT-239"
    assert summary["profile_source_id"] == "viscosity_screening_salt_test_2_jin_coarse_mesh"
    assert summary["policy"]["source_cases_read_only"] is True
    assert summary["policy"]["closure_observations_updated"] is False
    assert [case["mesh_level"] for case in summary["source_cases"]] == ["medium", "fine"]
    assert summary["source_cases"][1]["processor_dir"] == "processors128"


def test_generated_runner_keeps_source_case_read_only() -> None:
    subprocess.run([sys.executable, str(SCRIPT)], cwd=ROOT, check=True)
    runner = (PACKAGE / "scripts/run_refined_closure_qoi.sh").read_text(encoding="utf-8")

    assert "reconstructPar -case '$recon_dir'" in runner
    assert "ln -s \"$case_dir/$proc_dir\" \"$recon_dir/$proc_dir\"" in runner
    assert "sample_section_mean_pressure.py" in runner
    assert "--mesh-stations \"$MESH_STATIONS\"" in runner
    assert "closure_observations" not in runner
