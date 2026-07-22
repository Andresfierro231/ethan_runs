#!/usr/bin/env python3
"""Build the S8/S12 thermal residual ownership gate package.

This is a read-only synthesis. It does not run Fluid, score protected splits,
fit a physical model, or release S11/S15/S6.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "work_products/2026-07/2026-07-21/2026-07-21_s8_s12_thermal_residual_ownership_gate"

S8 = REPO / "work_products/2026-07/2026-07-21/2026-07-21_thesis_study_s8_wall_test_section_axial_mixing_candidate"
S12 = REPO / "work_products/2026-07/2026-07-21/2026-07-21_thesis_study_s12_thermal_shape_ownership_candidate"
H2 = REPO / "work_products/2026-07/2026-07-21/2026-07-21_fluid_extbc_phase_h2_passive_heat_loss_attribution"
PASSIVE = REPO / "work_products/2026-07/2026-07-21/2026-07-21_passive_h2_cand001_physical_basis"
SOURCE = REPO / "work_products/2026-07/2026-07-21/2026-07-21_fluid_setup_known_heater_source_train_residual_decomp"
EMPIRICAL = REPO / "work_products/2026-07/2026-07-21/2026-07-21_fluid_empirical_leg_bias_correction_diagnostic"
INCLINE = REPO / "work_products/2026-07/2026-07-21/2026-07-21_heated_incline_tw4_tw6_local_audit"
PHASE_E = REPO / "work_products/2026-07/2026-07-21/2026-07-21_fluid_external_bc_phase_e_train_full_solve"
PHASE_FJ = REPO / "work_products/2026-07/2026-07-21/2026-07-21_fluid_extbc_fj_parallel_diagnostics"

TASK = "TODO-S8-S12-THERMAL-RESIDUAL-OWNERSHIP-GATE-2026-07-21"
DECISION = "needs_more_physical_basis"
CLAIM = "read-only thermal residual ownership gate; no Fluid solve; no protected split scoring; no fit/admission"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({name: row.get(name, "") for name in fieldnames})


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def truthy(value: str) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes"}


def residual_owner_matrix() -> list[dict[str, object]]:
    s12_residuals = read_csv(S12 / "residual_quantification.csv")
    s12_gates = read_csv(S12 / "admission_gate_matrix.csv")
    passive_gate = read_csv(PASSIVE / "repair_gate.csv")[0]
    heater_rows = read_csv(SOURCE / "tw4_tw6_focus.csv")
    empirical_summary = load_json(EMPIRICAL / "summary.json")
    s8_summary = load_json(S8 / "summary.json")

    tw5 = next(row for row in s12_residuals if row["sensor"] == "TW5")
    tw6 = next(row for row in s12_residuals if row["sensor"] == "TW6")
    s12_failed_gates = [row["gate"] for row in s12_gates if row["status"].startswith("fail")]
    heater_worsens = [row["sensor"] for row in heater_rows if row["response_class"] == "worsens"]
    heater_improves = [row["sensor"] for row in heater_rows if row["response_class"] == "improves"]

    return [
        {
            "candidate_id": "S12-HIAX1",
            "owner_family": "heated_incline_upcomer_exchange_shape",
            "positive_evidence": "S12 identifies TW5/TW6 residual ownership and runtime-legal contract",
            "blocking_evidence": ";".join(s12_failed_gates),
            "quantitative_signal": f"TW5 prior-family fail_fraction={tw5['fail_fraction']}; TW6 prior-family fail_fraction={tw6['fail_fraction']}",
            "gate_status": "plausible_owner_not_repair_ready",
            "decision": DECISION,
            "claim_boundary": CLAIM,
        },
        {
            "candidate_id": "PASSIVE-H2-CAND001",
            "owner_family": "passive_wall_external_boundary",
            "positive_evidence": "broad passive h and fixed-state q estimates sit inside engineering screens",
            "blocking_evidence": passive_gate["rationale"],
            "quantitative_signal": f"repair_run_allowed_now={passive_gate['repair_run_allowed_now']}",
            "gate_status": "source_basis_not_released",
            "decision": DECISION,
            "claim_boundary": CLAIM,
        },
        {
            "candidate_id": "SETUP-KNOWN-HEATER-SOURCE",
            "owner_family": "lower_leg_setup_heater_source_lane",
            "positive_evidence": "source lane is executable and setup-known for Salt2 train/support",
            "blocking_evidence": f"TW4/TW5 worsen and only {','.join(heater_improves) or 'none'} improves",
            "quantitative_signal": f"worsens={','.join(heater_worsens)}",
            "gate_status": "partial_local_diagnostic_not_candidate",
            "decision": DECISION,
            "claim_boundary": CLAIM,
        },
        {
            "candidate_id": "EMPIRICAL-LEG-BIAS",
            "owner_family": "diagnostic_empirical_residual_layer",
            "positive_evidence": "train-only residual envelope shows large reducible bias",
            "blocking_evidence": "coefficients are empirical and nonphysical; no source/property release",
            "quantitative_signal": f"all_MAE {empirical_summary['baseline_all_mae_K']} -> {empirical_summary['corrected_all_mae_K']}",
            "gate_status": "diagnostic_only_not_physical_candidate",
            "decision": DECISION,
            "claim_boundary": CLAIM,
        },
        {
            "candidate_id": "S8-PRIOR-FAMILIES",
            "owner_family": "prior_wall_test_section_selector_families",
            "positive_evidence": "completed falsification narrows the search",
            "blocking_evidence": f"S8 admitted candidates={s8_summary.get('admitted_candidate_rows', 0)}; S11-ready={s8_summary.get('s11_ready_candidates', 0)}",
            "quantitative_signal": "current prior families do not resolve dominant TW5/TW6 residual",
            "gate_status": "rejected_as_repeat_path",
            "decision": DECISION,
            "claim_boundary": CLAIM,
        },
    ]


def physical_basis_coverage() -> list[dict[str, object]]:
    s12_gates = read_csv(S12 / "admission_gate_matrix.csv")
    passive_gate = read_csv(PASSIVE / "repair_gate.csv")[0]
    incline = read_csv(INCLINE / "failure_classification.csv")
    empirical_coeffs = read_csv(EMPIRICAL / "leg_bias_correction_coefficients.csv")
    source_decision = read_csv(SOURCE / "decision_table.csv")
    h2_gate = read_csv(H2 / "repair_candidate_predeclaration_gate.csv")[0]

    rows: list[dict[str, object]] = []
    for row in s12_gates:
        rows.append(
            {
                "basis_id": f"S12-{row['gate']}",
                "source_family": "S12-HIAX1",
                "status": row["status"],
                "evidence": row["evidence"],
                "blocks_repair": row["blocks_s11"],
                "required_next": row["required_next"],
            }
        )
    rows.append(
        {
            "basis_id": "PASSIVE-H2-source-basis",
            "source_family": "PASSIVE-H2-CAND001",
            "status": passive_gate["gate_decision"],
            "evidence": passive_gate["rationale"],
            "blocks_repair": str(not truthy(passive_gate["repair_run_allowed_now"])),
            "required_next": passive_gate["next_action"],
        }
    )
    rows.append(
        {
            "basis_id": "H2-predeclaration",
            "source_family": "PASSIVE-H2-CAND001",
            "status": h2_gate["execution_status"],
            "evidence": h2_gate["dominant_evidence"],
            "blocks_repair": "true",
            "required_next": h2_gate["required_before_execution"],
        }
    )
    for row in incline:
        rows.append(
            {
                "basis_id": f"heated-incline-{row['candidate_failure_mode']}",
                "source_family": "heated_incline_audit",
                "status": row["classification"],
                "evidence": row["evidence"],
                "blocks_repair": "true" if row["classification"] in {"primary", "secondary_primary_after_source_gate"} else "false",
                "required_next": row["decision"],
            }
        )
    for row in source_decision:
        rows.append(
            {
                "basis_id": f"setup-source-{row.get('decision_id', row.get('case_id', 'decision'))}",
                "source_family": "setup_known_heater_source",
                "status": row.get("decision", row.get("status", "reviewed")),
                "evidence": row.get("rationale", row.get("claim_boundary", "")),
                "blocks_repair": "true",
                "required_next": "new physical form or source-basis release; do not use source lane alone",
            }
        )
    nonphysical = [row["leg"] for row in empirical_coeffs if row["physics_admission_status"] != "admitted"]
    rows.append(
        {
            "basis_id": "empirical-leg-bias-physics",
            "source_family": "empirical_leg_bias",
            "status": "diagnostic_only",
            "evidence": f"not admitted for legs={';'.join(nonphysical)}",
            "blocks_repair": "true",
            "required_next": "translate diagnostic bias into source-backed physical candidate before S11",
        }
    )
    return rows


def candidate_gate_decision(owner_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    return [
        {
            "gate_id": "THERM-G1",
            "gate": "single_physical_candidate_available",
            "status": "fail",
            "evidence": "No candidate has finite train score plus source/property/same-QOI readiness.",
            "decision_effect": DECISION,
        },
        {
            "gate_id": "THERM-G2",
            "gate": "repeat_failed_s8_families_avoided",
            "status": "pass",
            "evidence": "S8 prior wall/test-section selector families remain rejected.",
            "decision_effect": "do_not_expand_failed_families",
        },
        {
            "gate_id": "THERM-G3",
            "gate": "passive_repair_source_basis",
            "status": "fail",
            "evidence": "PASSIVE-H2-CAND001 gate decision is needs_more_source.",
            "decision_effect": DECISION,
        },
        {
            "gate_id": "THERM-G4",
            "gate": "exchange_state_and_uq",
            "status": "fail",
            "evidence": "S12-HIAX1 still lacks exchange-state harvest and same-QOI UQ.",
            "decision_effect": DECISION,
        },
        {
            "gate_id": "THERM-G5",
            "gate": "empirical_correction_physics_admission",
            "status": "fail",
            "evidence": "Empirical leg-bias layer is diagnostic residual ownership only.",
            "decision_effect": "no_physics_admission",
        },
        {
            "gate_id": "THERM-G6",
            "gate": "overall_decision",
            "status": DECISION,
            "evidence": f"{len(owner_rows)} evidence families reviewed; none releases a repair or S11 candidate.",
            "decision_effect": "S11_blocked",
        },
    ]


def runtime_leakage_audit() -> list[dict[str, object]]:
    forbidden = [
        "CFD mdot",
        "realized wallHeatFlux",
        "imposed cooler duty",
        "realized test-section heat",
        "validation temperatures",
        "holdout temperatures",
        "external-test temperatures",
        "train residual fill",
    ]
    return [
        {
            "audit_id": f"RUNTIME-{idx:02d}",
            "runtime_input": item,
            "used_as_runtime_input": False,
            "status": "pass",
            "detail": "forbidden input audit; not used; package is read-only evidence synthesis",
        }
        for idx, item in enumerate(forbidden, start=1)
    ] + [
        {
            "audit_id": "RUNTIME-09",
            "runtime_input": "validation/holdout/external score rows",
            "used_as_runtime_input": False,
            "status": "pass",
            "detail": "forbidden input audit; validation, holdout, and external-test rows scored: 0/0/0",
        }
    ]


def source_property_split_consequence() -> list[dict[str, object]]:
    return [
        {
            "candidate_id": "S12-HIAX1",
            "source_validity": "architecture_supported_not_parameterized",
            "property_sensitivity": "not_run",
            "split_consequence": "train_support_only_until finite candidate and S11 source/property refresh",
            "release_status": "not_released",
            "next_required": "S13 exchange QOIs and same-QOI UQ",
        },
        {
            "candidate_id": "PASSIVE-H2-CAND001",
            "source_validity": "needs_more_source",
            "property_sensitivity": "not_run",
            "split_consequence": "no train repair run allowed",
            "release_status": "not_released",
            "next_required": "independent geometry ambient insulation and literature hA source release",
        },
        {
            "candidate_id": "SETUP-KNOWN-HEATER-SOURCE",
            "source_validity": "setup_known_source_lane_executable",
            "property_sensitivity": "not_run",
            "split_consequence": "diagnostic train-only residual decomposition",
            "release_status": "not_released",
            "next_required": "new physical model form; source lane alone worsens TW4/TW5",
        },
        {
            "candidate_id": "EMPIRICAL-LEG-BIAS",
            "source_validity": "no_physical_source",
            "property_sensitivity": "not_applicable",
            "split_consequence": "diagnostic-only; cannot freeze or score",
            "release_status": "not_released",
            "next_required": "convert diagnostic pattern into source-backed candidate",
        },
    ]


def s11_decision() -> list[dict[str, object]]:
    return [
        {
            "decision_id": "S11-THERMAL-OWNER-GATE",
            "s11_unblocked": False,
            "s15_unblocked": False,
            "s6_unblocked": False,
            "decision": DECISION,
            "candidate_count_released": 0,
            "rationale": "No exactly-one runtime-legal physical candidate passed source/property, split, finite-score, and UQ gates.",
            "next_claimable": "S13 sampled-field/Qwall/UQ unblock or passive source-basis enrichment; do not run Fluid repair from this package",
        }
    ]


def source_manifest() -> list[dict[str, object]]:
    paths = [
        ("s8", S8 / "summary.json", "read-only S8 negative result"),
        ("s12", S12 / "candidate_contract.csv", "read-only S12 candidate contract"),
        ("s12_gates", S12 / "admission_gate_matrix.csv", "read-only S12 gate matrix"),
        ("h2", H2 / "repair_candidate_predeclaration_gate.csv", "read-only Phase H2 predeclaration"),
        ("passive", PASSIVE / "repair_gate.csv", "read-only passive-H2 physical-basis gate"),
        ("source", SOURCE / "tw4_tw6_focus.csv", "read-only setup-known source residual focus"),
        ("empirical", EMPIRICAL / "corrected_train_residual_metrics.csv", "read-only empirical diagnostic"),
        ("incline", INCLINE / "failure_classification.csv", "read-only heated-incline audit"),
        ("phase_e", PHASE_E / "README.md", "read-only external-BC train solve context"),
        ("phase_fj", PHASE_FJ / "README.md", "read-only residual decomposition context"),
    ]
    return [
        {
            "source_id": source_id,
            "path": str(path.relative_to(REPO)),
            "role": role,
            "exists": path.exists(),
            "mutated": False,
        }
        for source_id, path, role in paths
    ]


def write_readme(summary: dict[str, object]) -> None:
    text = f"""---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_study_s12_thermal_shape_ownership_candidate/admission_gate_matrix.csv
  - work_products/2026-07/2026-07-21/2026-07-21_passive_h2_cand001_physical_basis/repair_gate.csv
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_setup_known_heater_source_train_residual_decomp/tw4_tw6_focus.csv
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_empirical_leg_bias_correction_diagnostic/corrected_train_residual_metrics.csv
tags: [s8, s12, thermal-residual, source-property, s11-blocked]
related:
  - .agent/status/2026-07-21_{TASK}.md
task: {TASK}
date: 2026-07-21
role: Forward-pred / Thermal-modeling / Implementer / Tester / Writer / Reviewer
type: work_product
status: complete
---
# S8/S12 Thermal Residual Ownership Gate

## Decision

Decision: `{summary["decision"]}`.

The gate reviewed `{summary["evidence_families_reviewed"]}` evidence families
and released `{summary["candidate_count_released"]}` S11-ready candidates.
S11, S15, and S6 remain blocked.

## What This Establishes

- S12-HIAX1 remains the best physical owner hypothesis, but it still lacks
  finite exchange-state QOIs, same-QOI UQ, and source/property release.
- PASSIVE-H2-CAND001 still needs independent geometry, ambient, insulation, and
  literature/source basis before any train repair run.
- The setup-known heater source lane is executable but does not solve the
  heated-incline residual by itself.
- The empirical leg-bias diagnostic quantifies reducible train residual but is
  not a physical closure.

## Files

| File | Use |
| --- | --- |
| `residual_owner_matrix.csv` | Candidate-family evidence and blocker summary. |
| `physical_basis_coverage.csv` | Source-basis coverage by gate. |
| `candidate_gate_decision.csv` | Machine-readable overall gate decision. |
| `runtime_leakage_audit.csv` | Forbidden runtime input audit. |
| `source_property_split_consequence.csv` | S11/S15/S6 source-property consequences. |
| `s11_decision.csv` | Current S11 decision. |
| `source_manifest.csv` | Source paths and mutation flags. |
| `summary.json` | Machine-readable summary. |

## Guardrails

No Fluid solve, native-output mutation, registry/admission mutation, scheduler
action, solver/postprocessing/sampler/harvest launch, Fluid/external edit,
validation/holdout/external-test scoring, fitting/model selection, global hA
multiplier selection, source/property release, S11/S15/S6 trigger,
blocker-register change, generated-index write, thesis edit, or residual
absorption into internal Nu was performed.
"""
    (OUT / "README.md").write_text(text, encoding="utf-8")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    owner_rows = residual_owner_matrix()
    basis_rows = physical_basis_coverage()
    gate_rows = candidate_gate_decision(owner_rows)
    runtime_rows = runtime_leakage_audit()
    split_rows = source_property_split_consequence()
    s11_rows = s11_decision()
    manifest_rows = source_manifest()

    write_csv(
        OUT / "residual_owner_matrix.csv",
        owner_rows,
        ["candidate_id", "owner_family", "positive_evidence", "blocking_evidence", "quantitative_signal", "gate_status", "decision", "claim_boundary"],
    )
    write_csv(
        OUT / "physical_basis_coverage.csv",
        basis_rows,
        ["basis_id", "source_family", "status", "evidence", "blocks_repair", "required_next"],
    )
    write_csv(OUT / "candidate_gate_decision.csv", gate_rows, ["gate_id", "gate", "status", "evidence", "decision_effect"])
    write_csv(OUT / "runtime_leakage_audit.csv", runtime_rows, ["audit_id", "runtime_input", "used_as_runtime_input", "status", "detail"])
    write_csv(
        OUT / "source_property_split_consequence.csv",
        split_rows,
        ["candidate_id", "source_validity", "property_sensitivity", "split_consequence", "release_status", "next_required"],
    )
    write_csv(OUT / "s11_decision.csv", s11_rows, ["decision_id", "s11_unblocked", "s15_unblocked", "s6_unblocked", "decision", "candidate_count_released", "rationale", "next_claimable"])
    write_csv(OUT / "source_manifest.csv", manifest_rows, ["source_id", "path", "role", "exists", "mutated"])

    summary = {
        "task": TASK,
        "status": "complete",
        "decision": DECISION,
        "evidence_families_reviewed": len(owner_rows),
        "basis_rows": len(basis_rows),
        "candidate_count_released": 0,
        "s11_unblocked": False,
        "s15_unblocked": False,
        "s6_unblocked": False,
        "fluid_solve_run": False,
        "validation_rows_scored": 0,
        "holdout_rows_scored": 0,
        "external_test_rows_scored": 0,
        "fit_or_model_selection": False,
        "source_property_release": False,
        "native_solver_outputs_mutated": False,
        "registry_mutated": False,
        "scheduler_action": False,
        "external_fluid_edit": False,
        "residual_absorbed_into_internal_nu": False,
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    write_readme(summary)


if __name__ == "__main__":
    main()
