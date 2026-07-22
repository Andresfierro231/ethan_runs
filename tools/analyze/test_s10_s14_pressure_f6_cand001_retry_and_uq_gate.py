#!/usr/bin/env python3
"""Regression checks for the S10/S14 CAND-001 retry/UQ gate package."""

from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_s10_s14_pressure_f6_cand001_retry_and_uq_gate"


def rows(name: str) -> list[dict[str, str]]:
    with (OUT / name).open(newline="") as f:
        return list(csv.DictReader(f))


def main() -> int:
    subprocess.run(
        [sys.executable, "tools/analyze/build_s10_s14_pressure_f6_cand001_retry_and_uq_gate.py"],
        cwd=ROOT,
        check=True,
        stdout=subprocess.DEVNULL,
    )
    summary = json.loads((OUT / "summary.json").read_text())
    assert summary["decision"] == "cand001_retry_runbook_recommended_no_launch_no_f6_scoring"
    assert summary["retry_row_recommended"] is True
    assert summary["launch_allowed_in_this_task"] is False
    assert summary["sampler_allowed_now"] is False
    assert summary["f6_scoring_allowed_now"] is False
    assert summary["terminal_success_cases"] == 0
    assert summary["endpoint_fields_ready"] == 0
    assert summary["ordinary_candidate_pairs"] == 0
    assert summary["same_qoi_mesh_uq_admissible_rows"] == 0
    assert summary["lower_right_section_effective_rows"] == 3
    assert summary["lower_right_component_k_or_f6_rows"] == 0
    assert summary["f6_fit_performed"] is False
    assert summary["component_k_admitted"] is False
    assert summary["cluster_k_admitted"] is False
    assert summary["clipped_k"] is False
    assert summary["hidden_global_multiplier"] is False
    assert summary["s11_unblocked"] is False

    gates = {row["gate"]: row for row in rows("timeout_source_ordinary_uq_gate_matrix.csv")}
    assert gates["CAND001_terminal_success"]["status"] == "fail"
    assert gates["ordinary_flow"]["status"] == "fail"
    assert gates["same_qoi_mesh_time_uq"]["status"] == "fail"
    assert gates["lower_right_component_interpretation"]["status"] == "negative_result"

    retry = rows("retry_decision.csv")
    assert retry[0]["retry_row_recommended"] == "true"
    assert retry[0]["launch_allowed_in_this_task"] == "false"

    lower_right = rows("lower_right_negative_result_classification.csv")
    assert len(lower_right) == 3
    assert all(row["final_label"] == "section_effective" for row in lower_right)
    assert all(row["use_in_this_gate"] == "negative_section_effective_context_only" for row in lower_right)

    s11 = rows("s11_decision.csv")
    assert s11[0]["s11_unblocked"] == "false"
    assert s11[0]["s15_or_s6_trigger"] == "false"
    print("S10/S14 CAND-001 retry/UQ gate checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
