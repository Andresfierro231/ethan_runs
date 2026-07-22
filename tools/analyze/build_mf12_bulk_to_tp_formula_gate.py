#!/usr/bin/env python3
"""Build MF12 bulk-to-TP formula gate from completed diagnostic evidence.

This is deliberately a gate, not a fitter. It asks whether the D2/MF07 signal
can be written as a source-bounded model form before any train-only smoke run.
"""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_mf12_bulk_to_tp_formula_gate"

MF07 = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_mf07_entrance_development_and_reset_source_basis"
MF08 = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_mf08_signed_wall_flux_developing_thermal_branches"
D2 = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_mf_d2_tp_tw_qoi_projection_gate"
D3 = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_mf_d3_wall_shape_axial_mixing_gate"
D4 = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_mf_d4_segment_source_placement_evidence_gate"
MF11 = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_mf11_empirical_f2_f5_physical_attribution_gate"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def ffloat(value: str | None) -> float | None:
    if value in (None, ""):
        return None
    return float(value)


def mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    tp_rows = read_csv(MF07 / "tp_residual_reset_graetz_join.csv")
    bulk_gate = read_csv(MF07 / "bulk_to_tp_existence_proof_gate.csv")
    formula_provenance = read_csv(MF07 / "formula_provenance_table.csv")
    source_rows = read_csv(MF08 / "runtime_legal_source_table.csv")
    mf08_variants = read_csv(MF08 / "candidate_gate.csv")
    d2_summary = json.loads((D2 / "summary.json").read_text())
    d3_summary = json.loads((D3 / "summary.json").read_text())
    d4_summary = json.loads((D4 / "summary.json").read_text())
    mf11_summary = json.loads((MF11 / "summary.json").read_text())

    m3_tp = [r for r in tp_rows if r["tested_model_form_id"] == "M3_as_is"]
    d2_tp = [r for r in tp_rows if r["tested_model_form_id"].startswith("D2_")]
    m3_errors = [ffloat(r["signed_error_K"]) for r in m3_tp]
    d2_errors = [ffloat(r["signed_error_K"]) for r in d2_tp]
    m3_errors = [v for v in m3_errors if v is not None]
    d2_errors = [v for v in d2_errors if v is not None]

    sensor_rows: list[dict[str, object]] = []
    for row in tp_rows:
        signed_error = ffloat(row["signed_error_K"])
        sensor_rows.append(
            {
                "tested_model_form_id": row["tested_model_form_id"],
                "case_id": row["case_id"],
                "split_group": row["split_group"],
                "sensor": row["sensor"],
                "prediction_source_segment": row["prediction_source_segment"],
                "mapped_span": row["mapped_span"],
                "signed_error_K": signed_error,
                "mean_Gz": ffloat(row["mean_Gz"]),
                "L_over_D_from_reset": ffloat(row["L_over_D_from_reset"]),
                "heating_cooling_signs": row["heating_cooling_signs"],
                "single_stream_allowed_rows": row["single_stream_allowed_rows"],
                "recirculation_blocked_rows": row["recirculation_blocked_rows"],
                "expected_thermal_development_direction": row["expected_thermal_development_direction"],
                "direction_match_to_signed_residual": row["direction_match_to_signed_residual"],
                "formula_gate_interpretation": interpret_sensor(row),
            }
        )

    source_ready_count = sum(r["runtime_allowed_now"].lower() == "true" for r in source_rows)
    source_release_count = sum(r["source_property_released_now"].lower() == "true" for r in source_rows)
    source_basis_needed = sum("needs_source_basis" in r["gate_decision"] for r in mf08_variants)

    candidate_rows = [
        {
            "candidate_id": "MF12a_signed_graetz_probe_offset",
            "symbolic_form": "T_TP = T_bulk + sigma_q * A_source * Phi(Gz, x/D, reset, BC)",
            "missing_physics_targeted": "source-signed thermal development and bulk-to-probe projection",
            "required_runtime_inputs": "segment bulk temperature; setup-known source/sink sign; source-bounded A_source; Re; Pr; Gz; reset distance; sensor map",
            "current_support": "MF07 shows M3 train TP residuals are uniformly cold and reset/Graetz coordinates exist; MF08 provides setup-side heat signs",
            "blocking_gap": "A_source formula, thermal reset labels, source/property release, and same-QOI TP projection UQ are missing",
            "ready_for_train_only_smoke": False,
            "decision": "diagnostic_only_needs_source_basis",
        },
        {
            "candidate_id": "MF12b_piecewise_signed_source_integral",
            "symbolic_form": "T_TP = T_bulk + integral_upstream W(reset,x) * q_setup(s)/(mdot cp) dx",
            "missing_physics_targeted": "axial source placement and reset-memory from cooler/heater/passive branches",
            "required_runtime_inputs": "runtime-legal q_setup by source family; mdot predicted by model; cp source/property release; axial source placement; reset kernel",
            "current_support": "D4 segment offsets reduce transfer RMSE by about 54 percent and MF08 signs are physically plausible",
            "blocking_gap": "source/property and cp release are absent; no reset kernel is admitted",
            "ready_for_train_only_smoke": False,
            "decision": "diagnostic_only_needs_source_basis",
        },
        {
            "candidate_id": "MF12c_wall_profile_projection",
            "symbolic_form": "T_TP = T_bulk + B_profile * (T_wall_inner - T_bulk) * Psi(y_probe/R, Gz, BC)",
            "missing_physics_targeted": "wall/core profile and TP probe localization",
            "required_runtime_inputs": "inner-wall temperature prediction or source-bounded wall profile; probe position; Gz; boundary condition",
            "current_support": "D3 wall-shape gate reduces transfer RMSE by about 52 percent",
            "blocking_gap": "runtime wall-profile model and same-QOI projection UQ are not released",
            "ready_for_train_only_smoke": False,
            "decision": "diagnostic_only_needs_wall_profile_basis",
        },
        {
            "candidate_id": "MF12d_empirical_projection_prior_for_diagnostic_only",
            "symbolic_form": "Use F2/F5 coefficients only as residual-shape priors, not runtime correction",
            "missing_physics_targeted": "non-unique low-dimensional discrepancy attribution",
            "required_runtime_inputs": "none for prediction; diagnostic comparison only",
            "current_support": "MF11 says F2/F5 strongly reduce transfer error but attribution is non-unique",
            "blocking_gap": "empirical coefficients are not source-bounded physical closures",
            "ready_for_train_only_smoke": False,
            "decision": "forbidden_as_empirical_projection_fit",
        },
    ]

    release_rows = [
        {
            "gate": "reset_graetz_coordinates",
            "status": "pass_diagnostic",
            "evidence": "MF07 has 33 segment-classification rows and TP reset/Graetz joins",
            "release_allowed": False,
        },
        {
            "gate": "train_tp_direction_signal",
            "status": "pass_diagnostic",
            "evidence": f"{sum(v < 0 for v in m3_errors)}/{len(m3_errors)} M3 train TP rows are cold relative to targets; mean signed error {mean(m3_errors):.6f} K",
            "release_allowed": False,
        },
        {
            "gate": "d2_projection_signal",
            "status": "pass_diagnostic",
            "evidence": f"D2 TP RMSE {d2_summary['d2_transfer_tp_rmse_K']} K versus M3 TP RMSE {d2_summary['m3_transfer_tp_rmse_K']} K",
            "release_allowed": False,
        },
        {
            "gate": "signed_source_runtime_release",
            "status": "fail_closed",
            "evidence": f"MF08 runtime-allowed source rows {source_ready_count}; source/property released rows {source_release_count}; variants needing source basis {source_basis_needed}",
            "release_allowed": False,
        },
        {
            "gate": "wall_profile_or_tp_projection_uq",
            "status": "fail_closed",
            "evidence": "Same-QOI TP projection UQ and runtime wall-profile source basis are not released",
            "release_allowed": False,
        },
        {
            "gate": "admission_or_final_score",
            "status": "fail_closed",
            "evidence": "No coefficient admission, source/property release, validation/holdout/external score, or final score is authorized",
            "release_allowed": False,
        },
    ]

    next_rows = [
        {
            "priority": 1,
            "next_study": "signed_source_property_heat_path_release_preflight",
            "why": "MF12a/MF12b cannot be written as runtime formulas until q_setup, cp, source placement, and sign conventions are released",
            "success_signal": "source/property rows for cooler, heater, test-section, and passive/downcomer families are released or fail closed with exact missing fields",
        },
        {
            "priority": 2,
            "next_study": "same_qoi_tp_projection_uq",
            "why": "D2 improves TP strongly, but the TP projection itself is still a post-solve target comparison, not a released runtime observable",
            "success_signal": "TP projection uncertainty table with same-QOI labels and runtime-legality status",
        },
        {
            "priority": 3,
            "next_study": "runtime_wall_profile_basis_for_tp_projection",
            "why": "D3 wall-shape signal suggests a wall/core profile contribution to TP/TW residuals",
            "success_signal": "source-bounded wall-profile model or explicit fail-closed wall-profile gap table",
        },
        {
            "priority": 4,
            "next_study": "train_only_mf12_formula_smoke_after_release",
            "why": "Only after the source and projection gates pass should a train/support smoke run compare MF12 formulas",
            "success_signal": "train/support metrics and runtime-leakage audit; validation/holdout/external rows not used",
        },
        {
            "priority": 5,
            "next_study": "tw_after_tp_residual_ownership",
            "why": "Once TP projection is separated, TW residual can be attributed to wall/source/axial mixing rather than bulk thermal error",
            "success_signal": "TW residual-owner table after subtracting released or diagnostic TP projection",
        },
    ]

    thesis_insert = build_thesis_insert(
        m3_errors=m3_errors,
        d2_errors=d2_errors,
        d2_summary=d2_summary,
        d3_summary=d3_summary,
        d4_summary=d4_summary,
        mf11_summary=mf11_summary,
    )

    summary = {
        "task_id": "TODO-MF12-BULK-TO-TP-FORMULA-GATE-2026-07-22",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "decision": "diagnostic_only_needs_source_basis",
        "candidate_formula_rows": len(candidate_rows),
        "sensor_evidence_rows": len(sensor_rows),
        "release_gate_rows": len(release_rows),
        "next_study_rows": len(next_rows),
        "m3_train_tp_rows": len(m3_errors),
        "m3_train_tp_mean_signed_error_K": mean(m3_errors),
        "d2_train_tp_mean_signed_error_K": mean(d2_errors),
        "d2_transfer_tp_rmse_K": d2_summary["d2_transfer_tp_rmse_K"],
        "m3_transfer_tp_rmse_K": d2_summary["m3_transfer_tp_rmse_K"],
        "ready_for_train_only_smoke": False,
        "source_property_release": False,
        "coefficient_admission": False,
        "validation_holdout_external_scoring": False,
        "residual_absorbed_into_internal_nu": False,
    }

    write_csv(
        OUT_DIR / "sensor_formula_evidence.csv",
        sensor_rows,
        [
            "tested_model_form_id",
            "case_id",
            "split_group",
            "sensor",
            "prediction_source_segment",
            "mapped_span",
            "signed_error_K",
            "mean_Gz",
            "L_over_D_from_reset",
            "heating_cooling_signs",
            "single_stream_allowed_rows",
            "recirculation_blocked_rows",
            "expected_thermal_development_direction",
            "direction_match_to_signed_residual",
            "formula_gate_interpretation",
        ],
    )
    write_csv(
        OUT_DIR / "candidate_bulk_to_tp_formulas.csv",
        candidate_rows,
        [
            "candidate_id",
            "symbolic_form",
            "missing_physics_targeted",
            "required_runtime_inputs",
            "current_support",
            "blocking_gap",
            "ready_for_train_only_smoke",
            "decision",
        ],
    )
    write_csv(
        OUT_DIR / "formula_release_gap_matrix.csv",
        release_rows,
        ["gate", "status", "evidence", "release_allowed"],
    )
    write_csv(
        OUT_DIR / "next_study_queue.csv",
        next_rows,
        ["priority", "next_study", "why", "success_signal"],
    )
    write_csv(
        OUT_DIR / "source_manifest.csv",
        [
            {"path": str(MF07 / "tp_residual_reset_graetz_join.csv"), "use": "TP residual/development evidence"},
            {"path": str(MF07 / "bulk_to_tp_existence_proof_gate.csv"), "use": "MF07 release gates"},
            {"path": str(MF07 / "formula_provenance_table.csv"), "use": "formula provenance"},
            {"path": str(MF08 / "runtime_legal_source_table.csv"), "use": "signed heat source runtime gate"},
            {"path": str(D2 / "summary.json"), "use": "D2 TP projection result"},
            {"path": str(D3 / "summary.json"), "use": "D3 wall-shape context"},
            {"path": str(D4 / "summary.json"), "use": "D4 source-placement context"},
            {"path": str(MF11 / "summary.json"), "use": "F2/F5 attribution context"},
        ],
        ["path", "use"],
    )
    write_csv(
        OUT_DIR / "no_mutation_guardrails.csv",
        [
            {"guardrail": "native_outputs_mutated", "value": False},
            {"guardrail": "registry_admission_mutated", "value": False},
            {"guardrail": "scheduler_action", "value": False},
            {"guardrail": "solver_sampler_harvest_uq_launched", "value": False},
            {"guardrail": "validation_holdout_external_scoring", "value": False},
            {"guardrail": "fitting_tuning_model_selection", "value": False},
            {"guardrail": "source_property_or_coefficient_release", "value": False},
            {"guardrail": "residual_absorbed_into_internal_nu", "value": False},
        ],
        ["guardrail", "value"],
    )

    (OUT_DIR / "thesis_model_form_insert.md").write_text(thesis_insert)
    (OUT_DIR / "README.md").write_text(build_readme(summary))
    (OUT_DIR / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")

    # Preserve provenance table in compact form for the thesis package.
    write_csv(
        OUT_DIR / "formula_provenance_compact.csv",
        formula_provenance,
        list(formula_provenance[0].keys()) if formula_provenance else ["formula_or_basis"],
    )


def interpret_sensor(row: dict[str, str]) -> str:
    if row["tested_model_form_id"] == "M3_as_is":
        if row["direction_match_to_signed_residual"].startswith("consistent"):
            return "supports positive source-bounded projection sign for M3 cold residual"
        return "M3 cold residual opposes local signed-source expectation; needs piecewise/source-placement model"
    if row["tested_model_form_id"].startswith("D2_"):
        if abs(float(row["signed_error_K"])) < 2.0:
            return "D2 nearly closes this TP row; useful existence proof but not a formula"
        return "D2 leaves residual; projection formula must be local/segment-aware"
    return "context"


def build_thesis_insert(
    *,
    m3_errors: list[float],
    d2_errors: list[float],
    d2_summary: dict[str, object],
    d3_summary: dict[str, object],
    d4_summary: dict[str, object],
    mf11_summary: dict[str, object],
) -> str:
    return f"""---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_mf12_bulk_to_tp_formula_gate/summary.json
tags: [mf12, bulk-to-tp, model-form, diagnostic-only]
status: draft_insert
---
# MF12 Bulk-to-TP Projection Formula Gate

The corrected model-form scoreboard indicates that part of the thermal
discrepancy is not a loop-energy error alone. For the M3 comparator, the
Salt2 train TP rows are uniformly cold relative to the TP targets
(`{sum(v < 0 for v in m3_errors)}/{len(m3_errors)}` rows; mean signed error
`{mean(m3_errors):.3f} K`). A sensor-kind projection correction reduces
transfer TP RMSE from `{d2_summary['m3_transfer_tp_rmse_K']} K` to
`{d2_summary['d2_transfer_tp_rmse_K']} K`, which is an existence proof that a
bulk-to-probe layer can matter.

The physically admissible form is therefore not an arbitrary offset, but a
source-bounded projection term:

```text
T_TP,j = T_bulk,s(j)(x_j) + Delta T_proj,j
Delta T_proj,j = sigma_q,j A_source,j Phi(Gz_j, x_j/D_h, reset_j, BC_j)
```

Here `sigma_q,j` is the sign of the local setup heat exchange, `A_source,j`
must come from a released source/property basis, and `Phi` is a developing-flow
or reset-memory shape function. This form is not admitted yet. The current
evidence supports the model-form direction but fails the release gate because
the source/property basis, TP projection UQ, and runtime wall/profile basis are
not released.

The same result explains why empirical corrections worked. D3 wall-shape
diagnostics reduced transfer RMSE by `{d3_summary['d3_transfer_rmse_reduction_pct']}%`,
and D4 segment source-placement diagnostics reduced transfer RMSE by
`{d4_summary['d4_transfer_rmse_reduction_pct']}%`. MF11 concluded that F2/F5
are useful discrepancy diagnostics but are non-unique and not physical
closures. MF12 converts that lesson into a source-basis requirement: before a
new scorecard is credible, the projection term must be tied to setup heat
sign, development coordinate, source placement, and same-QOI uncertainty.

Claim boundary: MF12 is diagnostic-only. It supports a missing-physics
explanation and a next-study sequence, but it does not release a correction,
coefficient, source/property label, validation score, holdout score, external
score, or final predictive model.
"""


def build_readme(summary: dict[str, object]) -> str:
    return f"""---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_mf07_entrance_development_and_reset_source_basis/README.md
  - work_products/2026-07/2026-07-22/2026-07-22_mf08_signed_wall_flux_developing_thermal_branches/README.md
  - work_products/2026-07/2026-07-22/2026-07-22_mf_d2_tp_tw_qoi_projection_gate/summary.json
tags: [mf12, bulk-to-tp, formula-gate, diagnostic-only]
task: TODO-MF12-BULK-TO-TP-FORMULA-GATE-2026-07-22
date: 2026-07-22
role: Thermal-modeling / Forward-pred / Implementer / Tester / Writer / Reviewer
type: work_product
status: complete
---
# MF12 Bulk-to-TP Formula Gate

Decision: `{summary['decision']}`.

MF12 tests whether the D2/MF07 bulk-to-TP signal can be converted into a
source-bounded model form. The answer is: not yet. A formula family can be
written, and the direction is scientifically plausible, but the release gates
fail closed because source/property labels, same-QOI TP projection UQ, and a
runtime wall/profile basis are missing.

Key results:

- candidate formula rows: `{summary['candidate_formula_rows']}`
- sensor evidence rows: `{summary['sensor_evidence_rows']}`
- release gate rows: `{summary['release_gate_rows']}`
- M3 train TP mean signed error: `{summary['m3_train_tp_mean_signed_error_K']:.6f} K`
- M3 transfer TP RMSE: `{summary['m3_transfer_tp_rmse_K']} K`
- D2 transfer TP RMSE: `{summary['d2_transfer_tp_rmse_K']} K`
- train-only smoke ready: `{summary['ready_for_train_only_smoke']}`

## Files

- `candidate_bulk_to_tp_formulas.csv`
- `sensor_formula_evidence.csv`
- `formula_release_gap_matrix.csv`
- `next_study_queue.csv`
- `thesis_model_form_insert.md`
- `formula_provenance_compact.csv`
- `source_manifest.csv`
- `no_mutation_guardrails.csv`
- `summary.json`

No fitting, protected scoring, source/property release, coefficient admission,
Fluid solve, scheduler action, native-output mutation, or residual absorption
into internal Nu was performed.
"""


if __name__ == "__main__":
    main()
