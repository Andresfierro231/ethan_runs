#!/usr/bin/env python3
"""Regression checks for thesis N3 thermal residual-owner ablation."""

from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_thesis_n3_thermal_residual_owner_train_ablation"


def rows(name: str) -> list[dict[str, str]]:
    with (OUT / name).open(newline="") as f:
        return list(csv.DictReader(f))


def main() -> int:
    subprocess.run([sys.executable, "tools/analyze/build_thesis_n3_thermal_residual_owner_train_ablation.py"], cwd=ROOT, check=True)
    summary = json.loads((OUT / "summary.json").read_text())
    assert summary["decision"] == "train_only_residual_owner_ablation_complete_no_candidate_release"
    assert summary["ablation_rows"] == 6
    assert summary["candidate_reviewable_rows"] == 0
    assert summary["source_property_release"] is False
    assert summary["residual_absorbed_into_internal_nu"] is False
    legality = rows("runtime_legality_matrix.csv")
    assert len(legality) == 6
    assert all(row["runtime_legal"] == "false" for row in legality)
    print("thesis N3 checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
