#!/usr/bin/env python3.11
"""Build the MF02 pressure-mdot coupling diagnostic package."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path


TASK_ID = "TODO-MF02-PRESSURE-MDOT-COUPLING-DIAGNOSTIC-2026-07-22"
SLUG = "mf02_pressure_mdot_coupling_diagnostic"
ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_mf02_pressure_mdot_coupling_diagnostic"

SECTION_SCORECARD = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_two_tap_section_effective_hybrid_pressure_scorecard/section_effective_pressure_scorecard.csv"
HYBRID_CONTRACT = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_two_tap_section_effective_hybrid_pressure_scorecard/hybrid_pressure_term_contract.csv"
NO_FIT = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_hybrid_pressure_no_fit_performance_bakeoff/no_fit_performance_table.csv"
F6_GATE = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_f6_same_qoi_uq_and_admission_gate/f6_candidate_admission_decision.csv"
S10_GATE = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_s10_s14_pressure_f6_cand001_retry_and_uq_gate/f3_vs_f6_comparison_prerequisites.csv"
S10_SUMMARY = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_s10_s14_pressure_f6_cand001_retry_and_uq_gate/summary.json"
LOWER_RIGHT_NEGATIVE = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_s10_s14_pressure_f6_cand001_retry_and_uq_gate/lower_right_negative_result_classification.csv"
BLOCKERS = ROOT / ".agent/BLOCKERS.md"


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str] | None = None) -> None:
    if fieldnames is None:
        fieldnames = []
        for row in rows:
            for key in row:
                if key not in fieldnames:
                    fieldnames.append(key)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def f(row: dict[str, str], key: str) -> float:
    text = row.get(key, "")
    return float(text) if text not in {"", "nan", "None"} else float("nan")


def build_pressure_residual_basis(rows: list[dict[str, str]]) -> list[dict[str, object]]:
    out: list[dict[str, object]] = []
    for row in rows:
        gross = f(row, "gross_static_pressure_rise_pa")
        residual = f(row, "available_signed_residual_pa")
        hydro = f(row, "hydrostatic_term_pa")
        kinetic = f(row, "kinetic_term_pa")
        q_ref = f(row, "q_ref_pa")
        out.append(
            {
                "case_id": row["case_id"],
                "case_key": row["case_key"],
                "feature": row["feature"],
                "gross_static_pressure_rise_pa": gross,
                "hydrostatic_term_pa": hydro,
                "kinetic_term_pa": kinetic,
                "straight_developing_term_pa": row["straight_developing_term_pa"],
                "available_signed_residual_pa": residual,
                "pressure_recovery_candidate_pa": row["pressure_recovery_candidate_pa"],
                "residual_percent_of_gross_static": abs(residual) / gross * 100.0,
                "q_ref_pa": q_ref,
                "K_eff_recirc_diagnostic": row["K_eff_recirc_diagnostic"],
                "reverse_area_fraction": row["reverse_area_fraction"],
                "reverse_mass_fraction": row["reverse_mass_fraction"],
                "secondary_velocity_fraction": row["secondary_velocity_fraction"],
                "basis_label": "section_effective_pressure_recovery_diagnostic",
                "component_label": row["final_label"],
                "admission_status": row["admission_status"],
            }
        )
    return out


def build_mdot_sensitivity(rows: list[dict[str, str]]) -> list[dict[str, object]]:
    out: list[dict[str, object]] = []
    for row in rows:
        gross = f(row, "gross_static_pressure_rise_pa")
        residual = f(row, "available_signed_residual_pa")
        q_ref = f(row, "q_ref_pa")
        signed_fraction = residual / gross
        # If a closed-loop pressure balance were locally quadratic in mdot,
        # d(mdot)/mdot ~= -0.5 d(loss)/loss. Here the "loss" basis is not
        # admitted, so this is only a scale estimate against gross static rise.
        signed_mdot_fraction = -0.5 * signed_fraction
        out.append(
            {
                "case_id": row["case_id"],
                "case_key": row["case_key"],
                "basis": "gross_static_rise_quadratic_scale_only",
                "available_signed_residual_pa": residual,
                "normalization_pa": gross,
                "signed_pressure_fraction": signed_fraction,
                "signed_pressure_percent": signed_fraction * 100.0,
                "signed_mdot_fraction_estimate": signed_mdot_fraction,
                "signed_mdot_percent_estimate": signed_mdot_fraction * 100.0,
                "interpretation": "tiny gross-scale mdot effect; diagnostic only because residual is not an admitted loop-loss term",
                "use_allowed": "scale_of_effect_discussion",
                "use_forbidden": "mdot_prediction;pressure_closure_fit;component_K_admission",
            }
        )
        out.append(
            {
                "case_id": row["case_id"],
                "case_key": row["case_key"],
                "basis": "local_dynamic_pressure_K_eff_invalid_for_mdot",
                "available_signed_residual_pa": residual,
                "normalization_pa": q_ref,
                "signed_pressure_fraction": residual / q_ref,
                "signed_pressure_percent": residual / q_ref * 100.0,
                "signed_mdot_fraction_estimate": "",
                "signed_mdot_percent_estimate": "",
                "interpretation": "large apparent K_eff magnitude reflects recirculating section-effective basis, not ordinary mdot sensitivity",
                "use_allowed": "nonordinary_basis_warning",
                "use_forbidden": "mdot_prediction;ordinary_K;F6_fit;global_multiplier",
            }
        )
    return out


def build_lower_right_restatement(rows: list[dict[str, str]]) -> list[dict[str, object]]:
    out: list[dict[str, object]] = []
    for row in rows:
        out.append(
            {
                "case_id": row["case_id"],
                "feature": row["feature"],
                "final_label": row["final_label"],
                "component_isolation_gate": row["component_isolation_gate"],
                "same_qoi_uncertainty_gate": row["same_qoi_uncertainty_gate"],
                "ordinary_recirculation_gate": row["ordinary_recirculation_gate"],
                "reverse_area_fraction": row["reverse_area_fraction"],
                "reverse_mass_fraction": row["reverse_mass_fraction"],
                "pressure_finding": "pressure rise is hydrostatic/recovery/section-effective diagnostic, not negative loss",
                "admission_status": "not_component_K_not_F6_not_cluster_K",
                "allowed_use": "pressure_recovery_diagnostic;gross_scale_mdot_coupling_discussion",
                "forbidden_use": "component_K;F6_fit;clipped_K;hidden_global_multiplier;mixed_basis_promotion",
            }
        )
    return out


def build_f3_f6_prereq() -> list[dict[str, object]]:
    f6_rows = read_csv(F6_GATE)
    s10_summary = json.loads(S10_SUMMARY.read_text(encoding="utf-8"))
    return [
        {
            "gate": "terminal_source_success",
            "current_count": s10_summary["terminal_success_cases"],
            "required_status": "greater_than_zero_for_candidate_family",
            "current_status": "fail",
            "reason": "CAND001 terminal source evidence is still pending/retry-only.",
        },
        {
            "gate": "endpoint_fields_ready",
            "current_count": s10_summary["endpoint_fields_ready"],
            "required_status": "pressure_velocity_density_fields_available",
            "current_status": "fail",
            "reason": "No endpoint-field package exists for new low-recirculation pressure candidate.",
        },
        {
            "gate": "ordinary_flow_candidate_pairs",
            "current_count": s10_summary["ordinary_candidate_pairs"],
            "required_status": "RAF/RMF/SVF ordinary-flow gate pass",
            "current_status": "fail",
            "reason": "Existing lower-right rows fail material reverse-flow gate.",
        },
        {
            "gate": "same_qoi_mesh_time_UQ",
            "current_count": s10_summary["same_qoi_mesh_uq_admissible_rows"],
            "required_status": "same-label same-formula UQ admissible",
            "current_status": "fail",
            "reason": "No same-QOI mesh/time UQ family is admitted for F6/component-K.",
        },
        {
            "gate": "F3_comparison",
            "current_count": sum(1 for row in f6_rows if row.get("f3_comparison_status", "").startswith("pass")),
            "required_status": "compare after admitted ordinary F6 row exists",
            "current_status": "not_evaluated",
            "reason": "F3 comparison requires a reviewable F6/component row; none exists.",
        },
    ]


def write_docs(summary: dict[str, object], validation_status: str = "pending") -> None:
    generated_at = str(summary["generated_at_utc"])
    readme = f"""---
provenance:
  generated_by: tools/analyze/build_mf02_pressure_mdot_coupling_diagnostic.py
  task_id: {TASK_ID}
  generated_at_utc: {generated_at}
task: {TASK_ID}
tags:
  - MF02
  - pressure
  - mdot
  - diagnostic
related:
  - {rel(SECTION_SCORECARD)}
  - {rel(NO_FIT)}
  - {rel(S10_SUMMARY)}
---

# MF02 Pressure-Mdot Coupling Diagnostic

## Decision

MF02 is useful as a diagnostic scale estimate only. The lower-right pressure
rise is hydrostatic/recovery/section-effective evidence, not negative loss and
not component-K/F6 evidence.

Across the three available lower-right rows, the signed residual magnitude is
`{summary['min_residual_percent_gross']}%` to `{summary['max_residual_percent_gross']}%`
of gross static pressure rise. A gross-scale quadratic mdot estimate would be
only `{summary['max_abs_mdot_percent_estimate']}%` at most, but this is not a
predictive mdot correction because the residual is not an admitted loop-loss
term.

## Guardrails

No F6 fit, component K, cluster K, clipped K, hidden/global multiplier, mixed
basis promotion, solver/sampler launch, fitting, model selection, source/property
release, admission, registry mutation, native-output mutation, or S11/S15/S6
trigger was performed.
"""
    write_text(OUT_DIR / "README.md", readme)

    status = f"""---
provenance:
  generated_by: tools/analyze/build_mf02_pressure_mdot_coupling_diagnostic.py
  task_id: {TASK_ID}
  generated_at_utc: {generated_at}
task: {TASK_ID}
tags:
  - status
  - MF02
  - pressure
related:
  - {rel(OUT_DIR)}
---

# {TASK_ID}

## Objective

Quantify pressure/mdot coupling as a diagnostic model-form study while preserving
the lower-right non-admission result.

## Outcome

Decision: `{summary['decision']}`. The package reports `{summary['pressure_rows']}`
pressure rows and `{summary['mdot_sensitivity_rows']}` mdot-sensitivity rows.
The largest gross-scale mdot estimate is `{summary['max_abs_mdot_percent_estimate']}%`,
but all estimates are diagnostic only.

## Changes Made

- Wrote pressure residual basis, mdot sensitivity, lower-right non-admission,
  F3/F6 prerequisite, candidate gate, guardrail, README, summary, status,
  journal, and import artifacts under `{rel(OUT_DIR)}`.

## Validation

{validation_status}

## Guardrails

- Native-output mutation: false.
- Registry/admission mutation: false.
- Scheduler/solver/sampler launch: false.
- Fluid/external edit: false.
- Validation/holdout/external-test scoring: false.
- Fitting/tuning/model selection: false.
- Component-K/F6/cluster-K/clipped-K/hidden multiplier: false.
- S11/S15/S6 trigger: false.
- Mixed-basis promotion or residual-internal-Nu absorption: false.
"""
    write_text(ROOT / f".agent/status/2026-07-22_{TASK_ID}.md", status)

    journal = f"""---
provenance:
  generated_by: tools/analyze/build_mf02_pressure_mdot_coupling_diagnostic.py
  task_id: {TASK_ID}
  generated_at_utc: {generated_at}
task: {TASK_ID}
tags:
  - journal
  - MF02
  - pressure-mdot
related:
  - {rel(OUT_DIR)}
---

# MF02 pressure-mdot coupling diagnostic

## Attempted

Built a read-only diagnostic package from the section-effective lower-right
pressure scorecard, hybrid no-fit bakeoff, F6 admission gates, and CAND001
retry/UQ gate.

## Observed

The lower-right rows have finite pressure residuals, but they also fail
component isolation, same-QOI UQ, and ordinary recirculation gates. Their
gross-scale residuals are small relative to hydrostatic pressure rise, while
local dynamic-pressure normalization produces large nonordinary apparent
`K_eff` values.

## Inferred

The pressure residual can be discussed as a possible mdot coupling scale, but
only as a diagnostic. It does not justify changing a 1D pressure closure, fitting
F6, clipping K, or applying a hidden global multiplier.

## Contradictions or Caveats

The gross-scale mdot estimate assumes a quadratic balance only to estimate order
of magnitude. It is not a validated loop sensitivity, and the sign convention is
not a component-loss sign convention.

## Next Useful Actions

Keep pressure work separated: wait for CAND001 terminal evidence or another
ordinary-flow source family before any endpoint/F3/F6 review. Use this MF02
package as a thesis-safe diagnostic of how small the section-effective residual
is against gross hydrostatic pressure.
"""
    write_text(ROOT / ".agent/journal/2026-07-22/mf02-pressure-mdot-coupling-diagnostic.md", journal)


def build() -> dict[str, object]:
    generated_at = now_utc()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    section_rows = read_csv(SECTION_SCORECARD)
    pressure_rows = build_pressure_residual_basis(section_rows)
    mdot_rows = build_mdot_sensitivity(section_rows)
    lower_rows = build_lower_right_restatement(section_rows)
    prereq_rows = build_f3_f6_prereq()
    no_fit_rows = read_csv(NO_FIT)

    candidate_gate_rows = [
        {
            "candidate_id": "MF02_pressure_mdot_coupling",
            "candidate_status": "diagnostic_only_not_admission_candidate",
            "pressure_rows": len(pressure_rows),
            "same_qoi_uq_pass": False,
            "ordinary_flow_pass": False,
            "endpoint_field_gate_pass": False,
            "source_property_gate_pass": False,
            "f3_comparison_ready": False,
            "s11_reviewable": False,
            "reason": "Pressure residual basis is section-effective/recovery diagnostic; lower-right rows fail ordinary-flow, same-QOI UQ, and component-isolation gates.",
        }
    ]
    guardrails = [
        {"guardrail": "component_K_admission", "allowed": False},
        {"guardrail": "F6_fit_or_scoring", "allowed": False},
        {"guardrail": "cluster_K_or_clipped_K", "allowed": False},
        {"guardrail": "hidden_global_multiplier", "allowed": False},
        {"guardrail": "mixed_basis_promotion", "allowed": False},
        {"guardrail": "mdot_prediction_from_pressure_residual", "allowed": False},
        {"guardrail": "solver_scheduler_sampler_launch", "allowed": False},
        {"guardrail": "source_property_release_or_admission", "allowed": False},
    ]

    write_csv(OUT_DIR / "pressure_residual_basis_table.csv", pressure_rows)
    write_csv(OUT_DIR / "mdot_sensitivity_coupling_estimate.csv", mdot_rows)
    write_csv(OUT_DIR / "lower_right_non_admission_restatement.csv", lower_rows)
    write_csv(OUT_DIR / "f3_f6_prerequisite_table.csv", prereq_rows)
    write_csv(OUT_DIR / "candidate_gate.csv", candidate_gate_rows)
    write_csv(OUT_DIR / "no_admission_guardrails.csv", guardrails)
    write_csv(OUT_DIR / "no_fit_performance_context.csv", no_fit_rows)

    gross_mdot_estimates = [
        abs(float(row["signed_mdot_percent_estimate"]))
        for row in mdot_rows
        if row["basis"] == "gross_static_rise_quadratic_scale_only"
    ]
    residual_pcts = [float(row["residual_percent_of_gross_static"]) for row in pressure_rows]
    summary = {
        "task_id": TASK_ID,
        "generated_at_utc": generated_at,
        "decision": "diagnostic_pressure_mdot_coupling_scale_only_no_candidate",
        "pressure_rows": len(pressure_rows),
        "mdot_sensitivity_rows": len(mdot_rows),
        "max_abs_mdot_percent_estimate": max(gross_mdot_estimates),
        "min_residual_percent_gross": min(residual_pcts),
        "max_residual_percent_gross": max(residual_pcts),
        "component_k_admitted": False,
        "cluster_k_admitted": False,
        "f6_fit_performed": False,
        "f6_scoring_allowed_now": False,
        "clipped_k": False,
        "hidden_global_multiplier": False,
        "mixed_basis_promotion": False,
        "mdot_prediction_claim": False,
        "same_qoi_uq_pass": False,
        "ordinary_flow_pass": False,
        "endpoint_field_gate_pass": False,
        "source_property_release": False,
        "s11_s15_s6_trigger": False,
        "native_output_mutation": False,
        "registry_or_admission_mutation": False,
        "solver_scheduler_sampler_launch": False,
        "fluid_or_external_edit": False,
        "validation_holdout_external_scoring": False,
        "fitting_tuning_model_selection": False,
        "source_context": [
            rel(SECTION_SCORECARD),
            rel(HYBRID_CONTRACT),
            rel(NO_FIT),
            rel(F6_GATE),
            rel(S10_GATE),
            rel(S10_SUMMARY),
            rel(LOWER_RIGHT_NEGATIVE),
            rel(BLOCKERS),
        ],
    }
    write_text(OUT_DIR / "summary.json", json.dumps(summary, indent=2, sort_keys=True) + "\n")
    write_docs(summary)

    manifest = {
        "task": TASK_ID,
        "generated_at_utc": generated_at,
        "changed_files": [
            rel(OUT_DIR / "README.md"),
            rel(OUT_DIR / "summary.json"),
            rel(OUT_DIR / "pressure_residual_basis_table.csv"),
            rel(OUT_DIR / "mdot_sensitivity_coupling_estimate.csv"),
            rel(OUT_DIR / "lower_right_non_admission_restatement.csv"),
            rel(OUT_DIR / "f3_f6_prerequisite_table.csv"),
            rel(OUT_DIR / "candidate_gate.csv"),
            rel(OUT_DIR / "no_admission_guardrails.csv"),
            rel(OUT_DIR / "no_fit_performance_context.csv"),
            f".agent/status/2026-07-22_{TASK_ID}.md",
            ".agent/journal/2026-07-22/mf02-pressure-mdot-coupling-diagnostic.md",
            f"imports/2026-07-22_{SLUG}.json",
            "tools/analyze/build_mf02_pressure_mdot_coupling_diagnostic.py",
            "tools/analyze/test_mf02_pressure_mdot_coupling_diagnostic.py",
            ".agent/BOARD.md",
        ],
        "read_only_context": summary["source_context"]
        + [
            "native CFD/OpenFOAM outputs",
            "registry/admission state",
            "scheduler state",
            "Fluid source tree",
            "external repos",
            "blocker register",
            "generated docs index files",
            "thesis current/LaTeX files",
        ],
        "native_solver_outputs_mutated": False,
        "registry_mutated": False,
        "scheduler_action": "none",
        "external_fluid_edit": False,
        "mutation_flags": {
            "component_k_or_f6_admission": False,
            "fitting_tuning_model_selection": False,
            "source_property_release": False,
            "solver_scheduler_sampler_launch": False,
            "native_output_mutation": False,
            "registry_or_admission_mutation": False,
            "fluid_or_external_edit": False,
        },
    }
    write_text(ROOT / f"imports/2026-07-22_{SLUG}.json", json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return summary


if __name__ == "__main__":
    print(json.dumps(build(), indent=2, sort_keys=True))
