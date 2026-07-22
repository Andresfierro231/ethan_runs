#!/usr/bin/env python3.11
"""Build the MF11 empirical F2/F5 physical-attribution gate."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path


TASK_ID = "TODO-MF11-EMPIRICAL-F2-F5-PHYSICAL-ATTRIBUTION-GATE-2026-07-22"
SLUG = "mf11_empirical_f2_f5_physical_attribution_gate"
ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_mf11_empirical_f2_f5_physical_attribution_gate"

EMPIRICAL_REPORT = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_fluid_empirical_bias_models_publication_report"
REDUCED_DOF = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_fluid_reduced_dof_bias_transfer_screen"
D2 = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_mf_d2_tp_tw_qoi_projection_gate"
D3 = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_mf_d3_wall_shape_axial_mixing_gate"
D4 = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_mf_d4_segment_source_placement_evidence_gate"
MF07 = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_mf07_entrance_development_and_reset_source_basis"
MF08 = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_mf08_signed_wall_flux_developing_thermal_branches"
MF09 = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_mf09_recirculating_upcomer_thermal_model_alternatives"
N4 = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_thesis_n4_sensor_qoi_projection_uncertainty_table"


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str] | None = None) -> None:
    if fieldnames is None:
        fieldnames = []
        for row in rows:
            for key in row:
                if key not in fieldnames:
                    fieldnames.append(key)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def empirical_summary_rows() -> list[dict[str, object]]:
    rows = read_csv(EMPIRICAL_REPORT / "model_family_publication_table.csv")
    out: list[dict[str, object]] = []
    for row in rows:
        baseline = float(row["transfer_baseline_mae_K"])
        corrected = float(row["transfer_corrected_mae_K"])
        out.append(
            {
                "model_family": row["model_family"],
                "form": row["form"],
                "dof": row["dof"],
                "transfer_baseline_mae_K": baseline,
                "transfer_corrected_mae_K": corrected,
                "transfer_mae_reduction_K": baseline - corrected,
                "transfer_mae_reduction_pct": 100.0 * (baseline - corrected) / baseline,
                "publication_role": row["publication_role"],
                "physical_closure_claim_allowed": False,
            }
        )
    return out


def build_attribution_matrix() -> list[dict[str, object]]:
    d2 = read_json(D2 / "summary.json")
    d3 = read_json(D3 / "summary.json")
    d4 = read_json(D4 / "summary.json")
    mf07 = read_json(MF07 / "summary.json")
    mf08 = read_json(MF08 / "summary.json")
    mf09 = read_json(MF09 / "summary.json")
    n4 = read_json(N4 / "summary.json")
    return [
        {
            "candidate_physics": "MF07_entrance_development_reset",
            "f2_global_affine_explanation": "plausible broad global/axial development bias source",
            "f5_family_offset_explanation": "weak family-specific support because recirculation blocks many single-stream spans",
            "supporting_evidence": f"D2 thermal path promising; MF07 decision {mf07['decision']}; thermal-development rows {mf07['thermal_development_indicated_rows']}",
            "blocking_evidence": f"MF07 smoke-ready {mf07['ready_for_train_only_smoke']}; recirculation-blocked rows {mf07['recirculation_blocked_rows']}; source/property release {mf07['source_property_release']}",
            "attribution_strength": "plausible_diagnostic_not_released",
            "admissible_as_physical_closure": False,
        },
        {
            "candidate_physics": "MF08_signed_wall_flux_development",
            "f2_global_affine_explanation": "plausible because loop-wide heating/cooling sign errors can create global affine temperature bias",
            "f5_family_offset_explanation": "stronger shape match because F5 has thermal-family offsets and signed branch heat is family-specific",
            "supporting_evidence": f"MF08 decision {mf08['decision']}; sign-envelope rows {mf08['sign_envelope_rows']}; needs-source-basis rows {mf08['needs_source_basis_rows']}",
            "blocking_evidence": "setup Q signs are not source/property release; realized wallHeatFlux runtime input is forbidden",
            "attribution_strength": "strongest_physical_hypothesis_diagnostic_only",
            "admissible_as_physical_closure": False,
        },
        {
            "candidate_physics": "MF09_recirculating_upcomer_exchange_stratification",
            "f2_global_affine_explanation": "partial support for global bias through unresolved exchange/storage in recirculating upcomer",
            "f5_family_offset_explanation": "plausible upcomer/family-specific support but not smoke-ready",
            "supporting_evidence": f"MF09 best lane {mf09['best_next_science_lane']}; variants {mf09['variant_rows']}",
            "blocking_evidence": f"MF09 decision {mf09['decision']}; smoke-ready {mf09['smoke_ready_variants']}; accepted mesh/GCI QOIs {mf09['accepted_same_label_mesh_gci_qois']}",
            "attribution_strength": "plausible_but_blocked_missing_mesh_gci_source_basis",
            "admissible_as_physical_closure": False,
        },
        {
            "candidate_physics": "D3_wall_shape_axial_mixing",
            "f2_global_affine_explanation": "limited because F2 is global and cannot represent local wall shape after bias",
            "f5_family_offset_explanation": "plausible contributor to F5 thermal-family offsets",
            "supporting_evidence": f"D3 transfer RMSE reduction {d3['d3_transfer_rmse_reduction_pct']}%; local-shape RMSE {d3['d3_transfer_local_shape_rmse_after_bias_K']} K",
            "blocking_evidence": f"D3 candidate-ready rows {d3['candidate_ready_rows']}; same-QOI UQ executed {d3['same_qoi_uq_executed']}",
            "attribution_strength": "diagnostic_shape_support_only",
            "admissible_as_physical_closure": False,
        },
        {
            "candidate_physics": "D4_segment_source_placement",
            "f2_global_affine_explanation": "partial support if source placement creates global cold bias",
            "f5_family_offset_explanation": "strong support for family/segment offset interpretation",
            "supporting_evidence": f"D4 transfer RMSE reduction {d4['d4_transfer_rmse_reduction_pct']}%; target segments {d4['target_segments']}",
            "blocking_evidence": f"D4 source-bounded candidate-ready rows {d4['source_bounded_candidate_ready_rows']}; admission {d4['admission_status']}",
            "attribution_strength": "strong_empirical_upper_bound_not_source_bounded",
            "admissible_as_physical_closure": False,
        },
        {
            "candidate_physics": "sensor_QOI_projection",
            "f2_global_affine_explanation": "possible offset/scale contributor if mapped sensors/QOIs are not one-to-one runtime observables",
            "f5_family_offset_explanation": "weak to moderate support because sensor families can imitate thermal-family offsets",
            "supporting_evidence": f"N4 bounded rows {n4['bounded_rows']}; sensor rows {n4['sensor_rows']}",
            "blocking_evidence": f"N4 runtime temperature allowed rows {n4['runtime_temperature_allowed_rows']}; source/property release {n4['source_property_release']}",
            "attribution_strength": "projection_uncertainty_context_only",
            "admissible_as_physical_closure": False,
        },
    ]


def build_coefficient_plausibility(empirical_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    by_family = {row["model_family"]: row for row in empirical_rows}
    f2 = by_family["F2_global_affine"]
    f5 = by_family["F5_thermal_family_offset_shared_multiplier"]
    return [
        {
            "empirical_model": "F2_global_affine",
            "observed_transfer_corrected_mae_K": f2["transfer_corrected_mae_K"],
            "observed_transfer_reduction_pct": f2["transfer_mae_reduction_pct"],
            "plausible_physics": "global source/heat-loss magnitude, broad thermal development, sensor/QOI projection scale",
            "contradiction": "too few parameters to identify branch physics; could fit several missing-physics families equally well",
            "allowed_interpretation": "publication diagnostic discrepancy coordinate",
            "forbidden_interpretation": "released temperature-scale closure or source/property coefficient",
            "gate": "empirical_diagnostic_only",
        },
        {
            "empirical_model": "F5_thermal_family_offset_shared_multiplier",
            "observed_transfer_corrected_mae_K": f5["transfer_corrected_mae_K"],
            "observed_transfer_reduction_pct": f5["transfer_mae_reduction_pct"],
            "plausible_physics": "thermal-family source placement, signed wall/source heat, wall-shape/axial mixing, recirculating upcomer exchange",
            "contradiction": "higher DOF can hide multiple residual owners; MF08/MF09/D4 all block source/property or mesh/GCI release",
            "allowed_interpretation": "upper reduced-DOF diagnostic bound on missing thermal structure",
            "forbidden_interpretation": "admitted physical model, hidden fit, internal Nu absorption, or final score",
            "gate": "empirical_diagnostic_only",
        },
    ]


def build_assumptions() -> list[dict[str, object]]:
    return [
        {
            "item_id": "no_new_fit",
            "statement": "MF11 reads frozen empirical tables and completed gates only; it performs no fitting, tuning, or model selection.",
            "impact": "keeps F2/F5 attribution separate from coefficient admission",
        },
        {
            "item_id": "diagnostic_not_closure",
            "statement": "F2/F5 coefficients are discrepancy coordinates, not physical closures.",
            "impact": "prevents using empirical transfer performance as publication evidence of a released model",
        },
        {
            "item_id": "multiple_physics_nonidentifiability",
            "statement": "F2/F5 can be explained by several unresolved physics families at once.",
            "impact": "supports physical hypotheses but not unique attribution",
        },
        {
            "item_id": "protected_scoring_boundary",
            "statement": "No validation, holdout, or external-test rows are newly scored here.",
            "impact": "MF11 is a read-only synthesis gate",
        },
        {
            "item_id": "residual_policy",
            "statement": "Thermal residuals remain explicitly named and are not absorbed into internal Nu.",
            "impact": "keeps future source/property and exchange-cell tests scientifically auditable",
        },
    ]


def build_contradictions() -> list[dict[str, object]]:
    return [
        {
            "contradiction_id": "F2_transfers_but_not_physical",
            "observation": "F2 global affine reduces transfer MAE strongly with only two degrees of freedom.",
            "why_it_does_not_admit": "global scale/offset is not a source-bounded heat-transfer law or runtime-legal source property",
            "resolution": "use as discrepancy coordinate and motivate source-basis tests",
        },
        {
            "contradiction_id": "F5_best_transfer_but_high_DOF",
            "observation": "F5 has the lowest transfer MAE among reduced-DOF empirical models.",
            "why_it_does_not_admit": "thermal-family offsets plus multiplier can hide source placement, wall flux, mixing, and sensor projection simultaneously",
            "resolution": "treat as upper diagnostic bound; forbid hidden-fit interpretation",
        },
        {
            "contradiction_id": "D3_D4_transfer_reductions_are_large",
            "observation": "D3/D4 diagnostic gates reduce transfer RMSE by roughly half.",
            "why_it_does_not_admit": "both remain diagnostic and have zero candidate/source-bounded release rows",
            "resolution": "use them to rank physical owner tests, not as corrections",
        },
        {
            "contradiction_id": "MF08_signs_exist_but_no_source_release",
            "observation": "Setup-known signed heat exchange is physically meaningful.",
            "why_it_does_not_admit": "source/property release is blocked and realized wallHeatFlux is forbidden as runtime input",
            "resolution": "assemble source-basis evidence before train-only smoke",
        },
        {
            "contradiction_id": "MF09_exchange_cell_best_lane_but_blocked",
            "observation": "Exchange-cell model is the most physical recirculating-upcomer alternative.",
            "why_it_does_not_admit": "same-label mesh/GCI, source/property, cp, and production same-window harvest are missing",
            "resolution": "complete same-label mesh-family generation and source-property gate",
        },
    ]


def build_guardrails() -> list[dict[str, object]]:
    return [
        {"guardrail": "new_fitting_tuning_model_selection", "performed": False},
        {"guardrail": "validation_holdout_external_test_scoring", "performed": False},
        {"guardrail": "source_property_release", "performed": False},
        {"guardrail": "coefficient_admission", "performed": False},
        {"guardrail": "final_score_claim", "performed": False},
        {"guardrail": "scheduler_solver_sampler_harvest_uq_launch", "performed": False},
        {"guardrail": "fluid_or_external_edit", "performed": False},
        {"guardrail": "native_output_mutation", "performed": False},
        {"guardrail": "registry_or_admission_mutation", "performed": False},
        {"guardrail": "blocker_register_change", "performed": False},
        {"guardrail": "generated_index_refresh_before_closeout", "performed": False},
        {"guardrail": "residual_internal_nu_absorption", "performed": False},
    ]


def write_docs(summary: dict[str, object], validation_status: str = "pending") -> None:
    generated_at = str(summary["generated_at_utc"])
    readme = f"""---
provenance:
  generated_by: tools/analyze/build_mf11_empirical_f2_f5_physical_attribution_gate.py
  task_id: {TASK_ID}
  generated_at_utc: {generated_at}
task: {TASK_ID}
tags:
  - MF11
  - empirical-bias
  - attribution
related:
  - {rel(EMPIRICAL_REPORT)}
  - {rel(MF07)}
  - {rel(MF08)}
  - {rel(MF09)}
---

# MF11 Empirical F2/F5 Physical Attribution Gate

## Decision

Decision: `{summary['decision']}`.

F2 and F5 are scientifically useful because they locate the thermal discrepancy:
F2 shows that a low-DOF global affine correction explains much of the transfer
error, while F5 shows that thermal-family structure can explain slightly more.
They are not physical closures. The candidate physics are plausible but
non-unique and still blocked by source/property, mesh/GCI, runtime-input, or
admission gates.

## Use In Publication

Use this package to write that empirical discrepancy models motivate the next
physical studies: entrance/development, signed wall/source heat, recirculating
upcomer exchange, wall-shape/axial mixing, source placement, and sensor/QOI
projection. Do not cite F2/F5 as admitted coefficients, final scores, source
properties, or hidden internal-Nu corrections.
"""
    write_text(OUT_DIR / "README.md", readme)

    status = f"""---
provenance:
  generated_by: tools/analyze/build_mf11_empirical_f2_f5_physical_attribution_gate.py
  task_id: {TASK_ID}
  generated_at_utc: {generated_at}
task: {TASK_ID}
tags:
  - status
  - MF11
  - empirical-bias
related:
  - {rel(OUT_DIR)}
---

# {TASK_ID}

## Objective

Connect the strong F2/F5 empirical correction result to candidate physics
without treating empirical coefficients as closures.

## Outcome

Decision: `{summary['decision']}`. Attribution rows: `{summary['attribution_rows']}`.
Coefficient plausibility rows: `{summary['coefficient_plausibility_rows']}`.
Forbidden-as-physical-closure rows: `{summary['forbidden_physical_closure_rows']}`.

## Changes Made

- Wrote empirical F2/F5 summary table.
- Wrote physical attribution matrix.
- Wrote coefficient-to-physics plausibility table.
- Wrote assumptions/caveats ledger and contradiction log.
- Wrote no-mutation guardrails, README, summary, status, journal, and import manifest.

## Validation

{validation_status}

## Guardrails

- New fitting/tuning/model selection: false.
- Validation/holdout/external-test scoring: false.
- Source/property release, coefficient admission, final score: false.
- Scheduler/solver/sampler/harvest/UQ launch: false.
- Fluid/external edit, native-output mutation, registry/admission mutation:
  false.
- Blocker-register change and generated-index refresh before closeout: false.
- Residual-internal-Nu absorption: false.
"""
    write_text(ROOT / f".agent/status/2026-07-22_{TASK_ID}.md", status)

    journal = f"""---
provenance:
  generated_by: tools/analyze/build_mf11_empirical_f2_f5_physical_attribution_gate.py
  task_id: {TASK_ID}
  generated_at_utc: {generated_at}
task: {TASK_ID}
tags:
  - journal
  - MF11
  - empirical-bias
related:
  - {rel(OUT_DIR)}
---

# MF11 empirical F2/F5 physical attribution gate

## Attempted

Joined the empirical F2/F5 publication package to completed D2/D3/D4 and
MF07/MF08/MF09 source-basis gates, then classified whether the empirical
coefficients can be tied to physical residual owners.

## Observed

F2 and F5 both reduce transfer error strongly, but every candidate physics lane
that could explain those coefficients is still diagnostic-only, source-basis
blocked, mesh/GCI blocked, or runtime-input blocked.

## Inferred

The correct claim is empirical diagnostic attribution. The coefficients help
rank physical hypotheses, but no unique physical attribution or closure release
is supportable.

## Contradictions or Caveats

F5 being numerically best does not make it the best scientific model; its extra
degrees of freedom can absorb several unresolved mechanisms at once. F2 being
low-DOF and transferable makes it useful for publication, not admissible as a
temperature-scale law.

## Next Useful Actions

Use MF11 to prioritize MF10 only after source-basis gates are released; otherwise
continue same-label mesh-family/source-property work for S13 and signed source
basis for MF08.
"""
    write_text(ROOT / ".agent/journal/2026-07-22/mf11-empirical-f2-f5-physical-attribution-gate.md", journal)


def build() -> dict[str, object]:
    generated_at = now_utc()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    empirical_rows = empirical_summary_rows()
    attribution = build_attribution_matrix()
    plausibility = build_coefficient_plausibility(empirical_rows)
    assumptions = build_assumptions()
    contradictions = build_contradictions()
    guardrails = build_guardrails()

    write_csv(OUT_DIR / "empirical_f2_f5_summary.csv", empirical_rows)
    write_csv(OUT_DIR / "physical_attribution_matrix.csv", attribution)
    write_csv(OUT_DIR / "coefficient_to_physics_plausibility.csv", plausibility)
    write_csv(OUT_DIR / "assumptions_caveats_ledger.csv", assumptions)
    write_csv(OUT_DIR / "contradiction_log.csv", contradictions)
    write_csv(OUT_DIR / "no_mutation_guardrails.csv", guardrails)

    f2 = next(row for row in empirical_rows if row["model_family"] == "F2_global_affine")
    f5 = next(row for row in empirical_rows if row["model_family"] == "F5_thermal_family_offset_shared_multiplier")
    summary = {
        "task_id": TASK_ID,
        "generated_at_utc": generated_at,
        "decision": "empirical_diagnostic_only",
        "empirical_model_rows": len(empirical_rows),
        "attribution_rows": len(attribution),
        "coefficient_plausibility_rows": len(plausibility),
        "assumption_caveat_rows": len(assumptions),
        "contradiction_rows": len(contradictions),
        "forbidden_physical_closure_rows": sum(1 for row in plausibility if "closure" in row["forbidden_interpretation"]),
        "f2_transfer_corrected_mae_K": f2["transfer_corrected_mae_K"],
        "f2_transfer_reduction_pct": f2["transfer_mae_reduction_pct"],
        "f5_transfer_corrected_mae_K": f5["transfer_corrected_mae_K"],
        "f5_transfer_reduction_pct": f5["transfer_mae_reduction_pct"],
        "physical_attribution_unique": False,
        "physical_closure_admitted": False,
        "source_property_release": False,
        "coefficient_admission": False,
        "final_score_claim": False,
        "new_fitting_tuning_model_selection": False,
        "validation_holdout_external_test_scoring": False,
        "scheduler_solver_sampler_harvest_uq_launch": False,
        "fluid_or_external_edit": False,
        "native_output_mutation": False,
        "registry_or_admission_mutation": False,
        "blocker_register_change": False,
        "generated_index_refresh_before_closeout": False,
        "residual_internal_nu_absorption": False,
        "source_context": [
            rel(EMPIRICAL_REPORT / "model_family_publication_table.csv"),
            rel(EMPIRICAL_REPORT / "claim_boundary_table.csv"),
            rel(REDUCED_DOF / "summary.json"),
            rel(REDUCED_DOF / "transfer_summary.csv"),
            rel(D2 / "summary.json"),
            rel(D3 / "summary.json"),
            rel(D4 / "summary.json"),
            rel(MF07 / "summary.json"),
            rel(MF08 / "summary.json"),
            rel(MF09 / "summary.json"),
            rel(N4 / "summary.json"),
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
            rel(OUT_DIR / "empirical_f2_f5_summary.csv"),
            rel(OUT_DIR / "physical_attribution_matrix.csv"),
            rel(OUT_DIR / "coefficient_to_physics_plausibility.csv"),
            rel(OUT_DIR / "assumptions_caveats_ledger.csv"),
            rel(OUT_DIR / "contradiction_log.csv"),
            rel(OUT_DIR / "no_mutation_guardrails.csv"),
            f".agent/status/2026-07-22_{TASK_ID}.md",
            ".agent/journal/2026-07-22/mf11-empirical-f2-f5-physical-attribution-gate.md",
            f"imports/2026-07-22_{SLUG}.json",
            "tools/analyze/build_mf11_empirical_f2_f5_physical_attribution_gate.py",
            "tools/analyze/test_mf11_empirical_f2_f5_physical_attribution_gate.py",
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
            "new_fitting_tuning_model_selection": False,
            "protected_scoring": False,
            "source_property_release": False,
            "coefficient_admission": False,
            "final_score_claim": False,
            "residual_internal_nu_absorption": False,
        },
    }
    write_text(ROOT / f"imports/2026-07-22_{SLUG}.json", json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return summary


if __name__ == "__main__":
    print(json.dumps(build(), indent=2, sort_keys=True))
