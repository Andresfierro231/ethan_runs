#!/usr/bin/env python3
"""Regression checks for the five best thesis-support analyses package."""

from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / (
    "work_products/2026-07/2026-07-22/"
    "2026-07-22_five_best_thesis_support_analyses"
)


def read_csv(name: str) -> list[dict[str, str]]:
    with (OUT_DIR / name).open(newline="") as f:
        return list(csv.DictReader(f))


def main() -> int:
    subprocess.run(
        [sys.executable, "tools/analyze/build_five_best_thesis_support_analyses.py"],
        cwd=ROOT,
        check=True,
        stdout=subprocess.DEVNULL,
    )

    summary = json.loads((OUT_DIR / "summary.json").read_text())
    assert summary["decision"] == "five_support_analyses_prioritized_no_admission_no_freeze"
    assert summary["analysis_rows"] == 5
    assert summary["gate_rows"] == 5
    assert summary["figure_table_rows"] == 5
    assert summary["all_sources_present"] is True
    assert summary["candidate_released_count"] == 0
    assert summary["s11_s12_s13_s15_s6_trigger"] is False
    assert summary["source_property_release"] is False
    assert summary["Q_wall_W_release"] is False
    assert summary["production_harvest_allowed_now"] is False
    assert summary["final_score_values_claimed"] == 0
    assert summary["runtime_temperature_inputs_allowed"] == 0
    assert summary["native_output_mutation"] is False
    assert summary["registry_or_admission_mutation"] is False
    assert summary["scheduler_action"] is False
    assert summary["solver_sampler_harvest_uq_launched"] is False
    assert summary["fitting_or_model_selection"] is False
    assert summary["residual_absorbed_into_internal_nu"] is False

    priority = read_csv("support_analysis_priority_matrix.csv")
    assert [row["analysis_id"] for row in priority] == [
        "S13_EXCHANGE_QWALL_UQ_GATE",
        "REDUCED_DOF_TRANSFER_INTERPRETATION",
        "PASSIVE_BOUNDARY_SOURCE_FINALIZATION",
        "PRESSURE_F6_CAND001_RETRY_UQ_GATE",
        "PUBLICATION_SYNTHESIS_SENSOR_RUNTIME_NEGATIVE_RESULTS",
    ]
    assert all(row["admission_or_freeze_now"] == "no" for row in priority)

    gates = read_csv("support_analysis_gate_matrix.csv")
    assert all(row["candidate_released"] == "no" for row in gates)
    assert all(row["s11_or_s15_trigger"] == "no" for row in gates)

    queue = read_csv("board_action_queue.csv")
    assert queue[0]["recommended_task"] == "do_not_duplicate_active_S13_rows"
    assert queue[-1]["recommended_task"] == "TODO-S10-S14-PRESSURE-F6-CAND001-RETRY-AND-UQ-GATE-2026-07-21"

    manifest = read_csv("source_manifest.csv")
    assert len(manifest) >= 10
    assert {row["exists"] for row in manifest} == {"True"}
    assert {row["mutation_status"] for row in manifest} == {"read_only"}

    guardrails = read_csv("no_mutation_guardrails.csv")
    assert {row["status"] for row in guardrails} == {"false"}

    print("five best thesis-support analyses checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
