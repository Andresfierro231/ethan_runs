#!/usr/bin/env python3
"""Regression checks for thesis N1 frozen runtime-legal candidate gate."""

from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_thesis_n1_frozen_runtime_legal_candidate_gate"


def rows(name: str) -> list[dict[str, str]]:
    with (OUT / name).open(newline="") as f:
        return list(csv.DictReader(f))


def main() -> int:
    subprocess.run([sys.executable, "tools/analyze/build_thesis_n1_frozen_runtime_legal_candidate_gate.py"], cwd=ROOT, check=True)
    summary = json.loads((OUT / "summary.json").read_text())
    assert summary["decision"] == "no_frozen_runtime_legal_candidate"
    assert summary["released_candidate_rows"] == 0
    assert summary["s6_final_score_values_published"] == 0
    assert summary["s14_admitted_rows"] == 0
    assert summary["source_property_release"] is False
    assert summary["s11_s12_s13_s15_s6_trigger"] is False
    candidate_rows = rows("candidate_gate_matrix.csv")
    assert len(candidate_rows) == 4
    assert all(row["candidate_released"] == "false" for row in candidate_rows)
    runtime = rows("runtime_input_audit.csv")
    assert any(row["input_or_output"] == "runtime TP/TW temperatures" and row["runtime_input_allowed"] == "false" for row in runtime)
    print("thesis N1 checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
