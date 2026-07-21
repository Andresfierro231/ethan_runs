#!/usr/bin/env python3
"""Smoke tests for AGENT-245 repair-batch generator."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "tools/analyze/build_salt2_refined_closure_qoi_repair_batch.py"
PKG = ROOT / "work_products/2026-07/2026-07-09/2026-07-09_salt2_refined_closure_qoi_repair_batch"


def test_generator_contract() -> None:
    subprocess.run([sys.executable, str(SCRIPT)], cwd=ROOT, check=True)
    payload = json.loads((PKG / "summary.json").read_text(encoding="utf-8"))
    assert payload["task_id"] == "AGENT-245"
    assert payload["source_cases_read_only"] is True
    assert [c["level"] for c in payload["cases"]] == ["medium", "fine"]
    runner = (PKG / "scripts/run_repair_extraction.sh").read_text(encoding="utf-8")
    assert "assert_sampled_sections" in runner
    assert "no sampled section rows" in runner
    assert "Version: 13" in runner
    assert "assert_thermal_has_cutplane" in runner
