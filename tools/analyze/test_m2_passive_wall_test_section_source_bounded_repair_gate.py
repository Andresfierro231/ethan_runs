#!/usr/bin/env python3.11
"""Validate the M2 passive wall/test-section repair gate."""

from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BUILDER = ROOT / "tools/analyze/build_m2_passive_wall_test_section_source_bounded_repair_gate.py"
OUT_DIR = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_m2_passive_wall_test_section_source_bounded_repair_gate"
TASK_ID = "TODO-M2-PASSIVE-WALL-TEST-SECTION-SOURCE-BOUNDED-REPAIR-GATE-2026-07-22"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def main() -> int:
    subprocess.run([sys.executable, str(BUILDER)], cwd=ROOT, check=True)
    summary = json.loads((OUT_DIR / "summary.json").read_text(encoding="utf-8"))
    assert summary["task_id"] == TASK_ID
    assert summary["decision"] == "no_m2_passive_repair_now_source_basis_not_released"
    assert summary["source_basis_rows"] >= 3
    assert summary["residual_owner_rows"] >= 5
    assert summary["s11_reviewable_candidates"] == 0
    assert summary["repair_execution_allowed"] is False
    assert summary["source_property_release_allowed"] is False
    assert summary["closure_admission_allowed"] is False
    assert summary["global_passive_half_TW5_improvement_K"] > summary["lower_leg_half_TW5_improvement_K"]
    assert summary["global_to_lower_response_ratio"] > 5.0
    for key in (
        "fluid_solve",
        "native_output_mutation",
        "registry_or_admission_mutation",
        "scheduler_action",
        "solver_postprocessing_sampler_harvest_uq_launch",
        "fluid_or_external_edit",
        "validation_holdout_external_scoring",
        "fitting_tuning_model_selection",
        "global_hA_multiplier_selection",
        "source_property_release",
        "final_score_claim",
        "s11_s12_s13_s15_s6_trigger",
        "runtime_temperature_input_release",
        "residual_internal_nu_absorption",
    ):
        assert summary[key] is False

    source_basis = read_csv(OUT_DIR / "passive_heat_path_source_basis_table.csv")
    assert any(row["candidate_id"] == "PASSIVE-H2-CAND001" and row["decision"] == "plausible_but_not_source_released" for row in source_basis)
    assert any(row["candidate_id"] == "GLOBAL-PASSIVE-HA-0.5" and row["decision"] == "forbidden_as_global_multiplier" for row in source_basis)

    gate = read_csv(OUT_DIR / "repair_no_repair_gate.csv")
    assert len(gate) == 1
    assert gate[0]["decision"] == "no_repair_now_no_s11_candidate"
    assert gate[0]["s11_reviewable"] == "False"
    assert gate[0]["repair_execution_allowed"] == "False"

    runtime = read_csv(OUT_DIR / "runtime_legality_matrix.csv")
    assert any(row["candidate_or_input"] == "global_passive_hA_scale_0.5" and row["runtime_status"] == "forbidden" for row in runtime)
    assert any(row["candidate_or_input"] == "source_geometry_ambient_insulation_literature_basis" and row["allowed_now"] == "True" for row in runtime)

    assert (OUT_DIR / "README.md").exists()
    assert (ROOT / f".agent/status/2026-07-22_{TASK_ID}.md").exists()
    assert (ROOT / ".agent/journal/2026-07-22/m2-passive-wall-test-section-source-bounded-repair-gate.md").exists()
    assert (ROOT / "imports/2026-07-22_m2_passive_wall_test_section_source_bounded_repair_gate.json").exists()
    print("M2 passive wall/test-section source-bounded repair gate package passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
