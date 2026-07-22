#!/usr/bin/env python3.11
"""Validate the MF08 signed wall-flux developing thermal branch gate."""

from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BUILDER = ROOT / "tools/analyze/build_mf08_signed_wall_flux_developing_thermal_branches.py"
OUT_DIR = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_mf08_signed_wall_flux_developing_thermal_branches"
TASK_ID = "TODO-MF08-SIGNED-WALL-FLUX-DEVELOPING-THERMAL-BRANCHES-2026-07-22"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def main() -> int:
    subprocess.run([sys.executable, str(BUILDER)], cwd=ROOT, check=True)
    summary = json.loads((OUT_DIR / "summary.json").read_text(encoding="utf-8"))
    assert summary["task_id"] == TASK_ID
    assert summary["decision"] == "needs_source_basis_sign_aware_development_promising_diagnostic_only"
    assert summary["required_variant_rows"] == 4
    assert summary["ready_for_train_only_smoke_rows"] == 0
    assert summary["needs_source_basis_rows"] == 4
    assert summary["forbidden_wallHeatFlux_fit_rows"] == 1
    assert summary["source_property_release_allowed"] is False
    assert summary["coefficient_admission_allowed"] is False
    assert summary["realized_wallHeatFlux_runtime_input_allowed"] is False
    for key in (
        "fluid_solve",
        "native_output_mutation",
        "registry_or_admission_mutation",
        "scheduler_action",
        "solver_postprocessing_sampler_harvest_uq_launch",
        "fluid_or_external_edit",
        "validation_holdout_external_scoring",
        "fitting_tuning_model_selection",
        "final_score_claim",
        "residual_internal_nu_absorption",
    ):
        assert summary[key] is False

    expected_ids = {
        "MF08a_cooler_negative_wall_flux_strong_development",
        "MF08b_downcomer_negative_wall_flux_weak_passive_cooling",
        "MF08c_heater_positive_wall_flux_development",
        "MF08d_piecewise_signed_wall_flux_reset_memory",
    }
    gate = read_csv(OUT_DIR / "candidate_gate.csv")
    gate_ids = {row["variant_id"] for row in gate}
    assert expected_ids.issubset(gate_ids)
    for row in gate:
        if row["variant_id"] in expected_ids:
            assert row["gate_decision"] == "needs_source_basis"
            assert row["ready_for_train_only_smoke"] == "False"
            assert row["source_basis_ready"] == "False"
            assert row["wallHeatFlux_fit_forbidden"] == "True"
    assert any(row["gate_decision"] == "forbidden_as_wallHeatFlux_fit" for row in gate)

    sign_rows = read_csv(OUT_DIR / "branch_wall_flux_sign_magnitude_envelope.csv")
    signs = {(row["branch_id"], row["physical_role"]): row["fluid_energy_sign"] for row in sign_rows}
    assert signs[("cooling_branch", "cooler_or_HX")] == "negative"
    assert signs[("lower_leg", "heater")] == "positive"
    assert signs[("upcomer", "test_section")] == "positive"
    assert signs[("downcomer_or_passive_wall", "passive_loss")] == "negative_expected"

    runtime = read_csv(OUT_DIR / "runtime_legal_source_table.csv")
    assert all(row["runtime_allowed_now"] == "False" for row in runtime)
    assert all(row["realized_wallHeatFlux_runtime_input_allowed"] == "False" for row in runtime)

    guardrails = read_csv(OUT_DIR / "no_mutation_guardrails.csv")
    assert all(row["performed"] == "False" for row in guardrails)

    assert (OUT_DIR / "README.md").exists()
    assert (ROOT / f".agent/status/2026-07-22_{TASK_ID}.md").exists()
    assert (ROOT / ".agent/journal/2026-07-22/mf08-signed-wall-flux-developing-thermal-branches.md").exists()
    assert (ROOT / "imports/2026-07-22_mf08_signed_wall_flux_developing_thermal_branches.json").exists()
    print("MF08 signed wall-flux developing thermal branch gate package passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
