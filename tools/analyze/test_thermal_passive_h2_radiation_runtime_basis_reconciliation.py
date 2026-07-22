#!/usr/bin/env python3
"""Validate the PASSIVE-H2 radiation/runtime-basis reconciliation package."""
from __future__ import annotations

import csv
import json
from pathlib import Path


TASK_ID = "TODO-THERMAL-PASSIVE-H2-RADIATION-RUNTIME-BASIS-RECONCILIATION-2026-07-22"
REPO = Path(__file__).resolve().parents[2]
OUT_DIR = REPO / "work_products/2026-07/2026-07-22/2026-07-22_thermal_passive_h2_radiation_runtime_basis_reconciliation"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def main() -> int:
    summary = json.loads((OUT_DIR / "summary.json").read_text(encoding="utf-8"))
    assert summary["task_id"] == TASK_ID
    assert summary["decision"] == "passive_h2_radiation_basis_resolved_outer_insulation_surface_same_qoi_gate_diagnostic_no_release"
    assert summary["previous_direct_radiation_W"] > 600.0
    assert summary["recomputed_naive_inner_surface_radiation_W"] > 600.0
    assert summary["corrected_outer_surface_radiation_W"] < 100.0
    assert summary["corrected_radiation_fraction_of_prior_direct"] < 0.15
    assert summary["model_radiation_on_qambient_delta_W"] == 0.0
    assert summary["source_property_release"] is False
    assert summary["numeric_q_loss_release"] is False
    assert summary["qwall_release"] is False
    assert summary["coefficient_admission"] is False
    assert summary["protected_scoring"] is False
    assert summary["solver_or_sampler_launch"] is False
    assert summary["native_solver_outputs_mutated"] is False

    family_rows = read_csv(OUT_DIR / "corrected_outer_surface_passive_operator_family.csv")
    assert len(family_rows) == summary["family_rows"]
    assert len({row["source_family"] for row in family_rows}) == 5
    nominal_family = [row for row in family_rows if row["scenario_id"] == "salt_2__V00__nominal"]
    assert len(nominal_family) == 5
    assert all(float(row["outer_surface_T_K"]) < float(row["inner_wall_state_T_K"]) for row in nominal_family)
    assert all(row["runtime_wallHeatFlux_used"] == "False" for row in family_rows)
    assert all(row["runtime_validation_temperature_used"] == "False" for row in family_rows)
    assert all(row["runtime_CFD_mdot_used"] == "False" for row in family_rows)

    gate_rows = read_csv(OUT_DIR / "train_only_same_qoi_h2_gate.csv")
    assert len(gate_rows) == summary["same_qoi_gate_rows"]
    assert any(row["scenario_id"] == "salt_2__V05__radiation_on" for row in gate_rows)
    rad_row = next(row for row in gate_rows if row["scenario_id"] == "salt_2__V05__radiation_on")
    assert float(rad_row["corrected_passive_operator_delta_vs_nominal_W"]) == 0.0
    assert all(row["protected_scoring"] == "False" for row in gate_rows)
    assert all(row["passive_operator_release"] == "False" for row in gate_rows)

    recon_rows = read_csv(OUT_DIR / "radiation_runtime_basis_reconciliation.csv")
    assert any(row["status"] == "resolved_basis_error" for row in recon_rows)
    assert any(row["status"] == "model_switch_not_admitted" for row in recon_rows)

    decision_rows = read_csv(OUT_DIR / "radiation_runtime_decision.csv")
    assert any(row["decision"] == "not_admitted_zero_output_delta" for row in decision_rows)
    assert all(row["release_allowed"] == "False" for row in decision_rows)

    audit_rows = read_csv(OUT_DIR / "runtime_input_audit.csv")
    assert audit_rows
    assert all(row["pass"] == "True" for row in audit_rows)

    source_rows = read_csv(OUT_DIR / "source_manifest.csv")
    assert source_rows
    assert all(row["exists"] == "True" for row in source_rows)
    assert all(row["native_or_prior_output_mutated"] == "False" for row in source_rows)

    print("PASS: passive_H2 radiation runtime-basis reconciliation package is internally consistent")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
