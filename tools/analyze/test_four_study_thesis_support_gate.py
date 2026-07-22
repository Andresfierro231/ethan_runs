#!/usr/bin/env python3
"""Regression checks for the four-study thesis-support gate package."""

from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / (
    "work_products/2026-07/2026-07-22/"
    "2026-07-22_four_study_thesis_support_gate"
)


def read_csv(name: str) -> list[dict[str, str]]:
    with (OUT_DIR / name).open(newline="") as f:
        return list(csv.DictReader(f))


def main() -> int:
    subprocess.run(
        [sys.executable, "tools/analyze/build_four_study_thesis_support_gate.py"],
        cwd=ROOT,
        check=True,
        stdout=subprocess.DEVNULL,
    )

    summary = json.loads((OUT_DIR / "summary.json").read_text())
    assert summary["decision"] == "no_freeze_no_single_released_candidate"
    assert summary["study_rows"] == 4
    assert summary["candidate_rows"] == 4
    assert summary["candidate_released_count"] == 0
    assert summary["s15_trigger_allowed"] is False
    assert summary["s13_Q_wall_W_released_rows"] == 3
    assert summary["s13_production_harvest_allowed_rows"] == 0
    assert summary["validation_holdout_external_rows_scored"] == 0
    assert summary["fitting_or_model_selection"] is False
    assert summary["source_property_release"] is False
    assert summary["s11_s12_s13_s15_s6_trigger"] is False
    assert summary["residual_absorbed_into_internal_nu"] is False

    sequence = read_csv("four_study_sequence_status.csv")
    assert {row["study_id"] for row in sequence} == {
        "passive_physical_basis",
        "source_sink_residual_decomposition",
        "s13_sampled_field_qwall_harvest",
        "candidate_freeze_no_freeze",
    }
    assert all(row["s15_eligible_now"] == "false" for row in sequence)

    readiness = read_csv("candidate_freeze_readiness_matrix.csv")
    assert len(readiness) == 4
    assert all(row["candidate_released"] == "false" for row in readiness)
    assert all(row["freeze_decision"] == "no_freeze" for row in readiness)

    gates = read_csv("s15_trigger_gate.csv")
    by_gate = {row["gate"]: row for row in gates}
    assert by_gate["exactly_one_candidate_released"]["status"] == "fail"
    assert by_gate["s15_candidate_freeze"]["status"] == "blocked_no_freeze"
    assert by_gate["protected_split_integrity"]["status"] == "pass"

    manifest = read_csv("source_manifest.csv")
    assert len(manifest) >= 9
    assert {row["mutation_status"] for row in manifest} == {"read_only"}

    print("four-study thesis-support gate checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
