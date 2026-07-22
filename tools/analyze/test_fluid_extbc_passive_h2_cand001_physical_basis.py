#!/usr/bin/env python3
"""Validate PASSIVE-H2-CAND001 physical-basis package."""

from __future__ import annotations

import csv
import json
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "work_products/2026-07/2026-07-21/2026-07-21_passive_h2_cand001_physical_basis"
FAMILIES = ["junction", "downcomer", "upcomer", "cooling_branch", "lower_leg"]
REQUIRED = [
    "README.md",
    "current_hA_basis_and_provenance_risk.csv",
    "independent_h_estimate_range.csv",
    "area_coverage_basis.csv",
    "ambient_surroundings_basis.csv",
    "expected_q_loss_envelope.csv",
    "source_sink_interaction_update.csv",
    "repair_gate.csv",
    "source_manifest.csv",
    "summary.json",
]


def read_csv(name: str) -> list[dict[str, str]]:
    with (OUT / name).open(newline="") as f:
        return list(csv.DictReader(f))


def main() -> None:
    missing = [name for name in REQUIRED if not (OUT / name).exists()]
    assert not missing, f"missing outputs: {missing}"
    summary = json.loads((OUT / "summary.json").read_text())
    assert summary["status"] == "complete"
    assert summary["gate_decision"] in {"run_one_train_repair", "needs_more_source", "forbidden_as_fit"}
    assert summary["gate_decision"] == "needs_more_source"
    assert summary["fluid_solve_run"] is False
    assert summary["validation_rows_scored"] == 0
    assert summary["holdout_rows_scored"] == 0
    assert summary["external_test_rows_scored"] == 0
    assert summary["fit_or_model_selection"] is False
    assert summary["global_multiplier_admitted"] is False
    assert summary["repair_executed"] is False
    assert summary["freeze_or_admission_decision"] is False
    assert summary["source_property_release"] is False
    assert summary["native_output_mutation"] is False
    assert summary["registry_or_admission_mutation"] is False
    assert summary["scheduler_action"] is False
    assert summary["external_fluid_edit"] is False

    for name in [
        "current_hA_basis_and_provenance_risk.csv",
        "independent_h_estimate_range.csv",
        "area_coverage_basis.csv",
        "ambient_surroundings_basis.csv",
        "expected_q_loss_envelope.csv",
    ]:
        rows = read_csv(name)
        assert [row["source_family"] for row in rows] == FAMILIES, name
        assert all(row["claim_boundary"] for row in rows), name

    current = read_csv("current_hA_basis_and_provenance_risk.csv")
    assert all(row["wallHeatFlux_provenance_present"] == "True" for row in current)
    assert all(row["provenance_risk"] == "high_wallHeatFlux_derived" for row in current)

    h_range = read_csv("independent_h_estimate_range.csv")
    assert all(row["current_h_inside_independent_range"] == "True" for row in h_range)
    assert all(row["repair_justified_by_this_row"] == "False" for row in h_range)

    q_env = read_csv("expected_q_loss_envelope.csv")
    assert all(row["current_q_inside_envelope"] == "True" for row in q_env)
    assert all(row["material_q_basis_for_repair"] == "False" for row in q_env)

    ambient = read_csv("ambient_surroundings_basis.csv")
    assert all(row["ambient_basis_status"] == "provisional_envelope_only_needs_setup_room_source" for row in ambient)

    source_update = read_csv("source_sink_interaction_update.csv")
    assert len(source_update) == 2
    assert any(row["decision"] == "source_lane_partial_improvement_model_form_still_needed" for row in source_update)

    gate = read_csv("repair_gate.csv")
    assert len(gate) == 1
    assert gate[0]["candidate_id"] == "PASSIVE-H2-CAND001"
    assert gate[0]["gate_decision"] == "needs_more_source"
    assert gate[0]["repair_run_allowed_now"] == "False"
    assert "global_passive_hA_scale_0.5" in gate[0]["forbidden_shortcut"]

    manifest = read_csv("source_manifest.csv")
    assert len(manifest) >= 6
    assert all(row["mutation"] == "read_only" for row in manifest)

    print("PASSIVE-H2-CAND001 physical-basis checks passed.")


if __name__ == "__main__":
    main()
