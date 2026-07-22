#!/usr/bin/env python3.11
"""Validate the MF02 pressure-mdot coupling diagnostic package."""

from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BUILDER = ROOT / "tools/analyze/build_mf02_pressure_mdot_coupling_diagnostic.py"
OUT_DIR = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_mf02_pressure_mdot_coupling_diagnostic"
TASK_ID = "TODO-MF02-PRESSURE-MDOT-COUPLING-DIAGNOSTIC-2026-07-22"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def main() -> int:
    subprocess.run([sys.executable, str(BUILDER)], cwd=ROOT, check=True)
    summary = json.loads((OUT_DIR / "summary.json").read_text(encoding="utf-8"))
    assert summary["task_id"] == TASK_ID
    assert summary["decision"] == "diagnostic_pressure_mdot_coupling_scale_only_no_candidate"
    assert summary["pressure_rows"] == 3
    assert summary["mdot_sensitivity_rows"] == 6
    assert summary["max_abs_mdot_percent_estimate"] < 0.04
    assert summary["component_k_admitted"] is False
    assert summary["cluster_k_admitted"] is False
    assert summary["f6_fit_performed"] is False
    assert summary["f6_scoring_allowed_now"] is False
    assert summary["clipped_k"] is False
    assert summary["hidden_global_multiplier"] is False
    assert summary["mixed_basis_promotion"] is False
    assert summary["mdot_prediction_claim"] is False
    assert summary["same_qoi_uq_pass"] is False
    assert summary["ordinary_flow_pass"] is False
    assert summary["endpoint_field_gate_pass"] is False
    assert summary["source_property_release"] is False
    assert summary["s11_s15_s6_trigger"] is False
    assert summary["native_output_mutation"] is False
    assert summary["registry_or_admission_mutation"] is False
    assert summary["solver_scheduler_sampler_launch"] is False

    basis = read_csv(OUT_DIR / "pressure_residual_basis_table.csv")
    assert len(basis) == 3
    assert {row["basis_label"] for row in basis} == {"section_effective_pressure_recovery_diagnostic"}
    assert all(float(row["reverse_area_fraction"]) > 0.7 for row in basis)
    assert all(float(row["reverse_mass_fraction"]) > 0.49 for row in basis)

    mdot = read_csv(OUT_DIR / "mdot_sensitivity_coupling_estimate.csv")
    assert len(mdot) == 6
    assert any(row["basis"] == "gross_static_rise_quadratic_scale_only" for row in mdot)
    assert any(row["basis"] == "local_dynamic_pressure_K_eff_invalid_for_mdot" for row in mdot)
    invalid = [row for row in mdot if row["basis"] == "local_dynamic_pressure_K_eff_invalid_for_mdot"]
    assert all(row["signed_mdot_percent_estimate"] == "" for row in invalid)

    gates = read_csv(OUT_DIR / "candidate_gate.csv")
    assert gates[0]["candidate_status"] == "diagnostic_only_not_admission_candidate"
    assert gates[0]["s11_reviewable"] == "False"

    guardrails = {row["guardrail"]: row["allowed"] for row in read_csv(OUT_DIR / "no_admission_guardrails.csv")}
    assert guardrails["component_K_admission"] == "False"
    assert guardrails["F6_fit_or_scoring"] == "False"
    assert guardrails["mdot_prediction_from_pressure_residual"] == "False"

    prereq = read_csv(OUT_DIR / "f3_f6_prerequisite_table.csv")
    assert len(prereq) == 5
    assert all(row["current_status"] in {"fail", "not_evaluated"} for row in prereq)

    assert (OUT_DIR / "README.md").exists()
    assert (ROOT / f".agent/status/2026-07-22_{TASK_ID}.md").exists()
    assert (ROOT / ".agent/journal/2026-07-22/mf02-pressure-mdot-coupling-diagnostic.md").exists()
    assert (ROOT / "imports/2026-07-22_mf02_pressure_mdot_coupling_diagnostic.json").exists()
    print("MF02 pressure-mdot coupling diagnostic package passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
