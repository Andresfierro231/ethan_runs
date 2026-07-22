#!/usr/bin/env python3
"""Validate Phase H2 passive heat-loss attribution package."""

from __future__ import annotations

import csv
import json
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "work_products/2026-07/2026-07-21/2026-07-21_fluid_extbc_phase_h2_passive_heat_loss_attribution"


REQUIRED = [
    "README.md",
    "passive_hA_family_contribution.csv",
    "segment_heat_loss_sweep.csv",
    "hA_area_unit_audit.csv",
    "sign_and_drive_audit.csv",
    "tw5_response_waterfall.csv",
    "physical_plausibility_matrix.csv",
    "source_sink_coupling_matrix.csv",
    "repair_candidate_predeclaration_gate.csv",
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
    assert summary["validation_rows_scored"] == 0
    assert summary["holdout_rows_scored"] == 0
    assert summary["external_test_rows_scored"] == 0
    assert summary["fit_or_model_selection"] is False
    assert summary["repair_candidates_executed"] == 0
    assert summary["repair_candidates_admitted"] == 0
    assert summary["native_output_mutation"] is False
    assert summary["registry_or_admission_mutation"] is False
    assert summary["scheduler_action"] is False
    assert summary["external_fluid_edit"] is False

    family = read_csv("passive_hA_family_contribution.csv")
    assert len(family) >= 4
    lower = next(row for row in family if row["source_family"] == "lower_leg")
    assert lower["contribution_basis"] == "observed_one_at_a_time_lower_leg_scale_0.5"
    assert float(lower["tw5_abs_improvement_K"]) < float(summary["global_tw5_improvement_K"]) * 0.2
    assert any(row["contribution_basis"] == "allocated_global_remainder_by_non_lower_hA_share" for row in family)

    h_audit = read_csv("hA_area_unit_audit.csv")
    assert len(h_audit) == summary["passive_role_rows"]
    assert all(row["h_area_unit_check"] == "pass" for row in h_audit)

    sign = read_csv("sign_and_drive_audit.csv")
    assert len(sign) == summary["heat_ledger_rows"]
    assert all(row["sign_check"] == "pass" for row in sign)

    plaus = read_csv("physical_plausibility_matrix.csv")
    statuses = {row["admissibility_status"] for row in plaus}
    assert "blocked" in statuses
    assert "needs_independent_source" in statuses

    source_sink = read_csv("source_sink_coupling_matrix.csv")
    assert source_sink
    assert all("scored" in row["protected_split_scoring_status"] for row in source_sink)
    assert any(row["case_id"] == "salt_2" and row["source_segment_id"] == "lower_leg" for row in source_sink)

    repair = read_csv("repair_candidate_predeclaration_gate.csv")
    assert len(repair) == 1
    assert repair[0]["execution_status"] == "not_executed"
    assert repair[0]["admission_status"] == "not_admitted"
    assert "global_passive_hA_scale_0.5" in repair[0]["forbidden_shortcut"]

    for name in REQUIRED:
        if name.endswith(".csv"):
            rows = read_csv(name)
            assert rows, f"{name} has no rows"
            assert "claim_boundary" in rows[0] or name == "source_manifest.csv"

    print("Phase H2 passive heat-loss attribution checks passed.")


if __name__ == "__main__":
    main()
