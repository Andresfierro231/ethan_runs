#!/usr/bin/env python3
"""Build the thesis pressure-basis ladder evidence packet."""

from __future__ import annotations

import csv
import json
from decimal import Decimal
from pathlib import Path


TASK_ID = "TODO-THESIS-STUDY-PRESSURE-BASIS-LADDER-EVIDENCE-PACKET-2026-07-22"
DATE = "2026-07-22"
REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "work_products/2026-07/2026-07-22/2026-07-22_thesis_study_pressure_basis_ladder_evidence_packet"

SECTION_SCORECARD = REPO / "work_products/2026-07/2026-07-21/2026-07-21_two_tap_section_effective_hybrid_pressure_scorecard/section_effective_pressure_scorecard.csv"
HYBRID_CONTRACT = REPO / "work_products/2026-07/2026-07-21/2026-07-21_two_tap_section_effective_hybrid_pressure_scorecard/hybrid_pressure_term_contract.csv"
NO_FIT_PERFORMANCE = REPO / "work_products/2026-07/2026-07-21/2026-07-21_hybrid_pressure_no_fit_performance_bakeoff/no_fit_performance_table.csv"
RESIDUAL_OWNERSHIP = REPO / "work_products/2026-07/2026-07-21/2026-07-21_hybrid_pressure_no_fit_performance_bakeoff/residual_ownership_table.csv"
REVIEWABILITY = REPO / "work_products/2026-07/2026-07-21/2026-07-21_hybrid_pressure_no_fit_performance_bakeoff/candidate_reviewability_decision.csv"
S10_S14_GATE = REPO / "work_products/2026-07/2026-07-22/2026-07-22_s10_s14_pressure_f6_cand001_retry_and_uq_gate/timeout_source_ordinary_uq_gate_matrix.csv"
F3_F6_PREREQ = REPO / "work_products/2026-07/2026-07-22/2026-07-22_s10_s14_pressure_f6_cand001_retry_and_uq_gate/f3_vs_f6_comparison_prerequisites.csv"
SOURCE_PROPERTY_PREFLIGHT = REPO / "work_products/2026-07/2026-07-22/2026-07-22_source_property_nominal_train_release_preflight/summary.json"
S14_SUMMARY = REPO / "work_products/2026-07/2026-07-21/2026-07-21_thesis_study_s14_pressure_f6_nonrecirc_anchor_evidence/summary.json"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path) -> dict[str, object]:
    with path.open() as handle:
        return json.load(handle)


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({name: row.get(name, "") for name in fieldnames})


def decimal_list(rows: list[dict[str, str]], field: str) -> list[Decimal]:
    return [Decimal(row[field]) for row in rows]


def build() -> dict[str, object]:
    OUT.mkdir(parents=True, exist_ok=True)
    section_rows = read_csv(SECTION_SCORECARD)
    hybrid_rows = read_csv(HYBRID_CONTRACT)
    performance_rows = read_csv(NO_FIT_PERFORMANCE)
    ownership_rows = read_csv(RESIDUAL_OWNERSHIP)
    review_rows = read_csv(REVIEWABILITY)
    s10_s14_rows = read_csv(S10_S14_GATE)
    f3_rows = read_csv(F3_F6_PREREQ)
    source_property = read_json(SOURCE_PROPERTY_PREFLIGHT)
    s14_summary = read_json(S14_SUMMARY)

    if len(section_rows) != 3:
        raise RuntimeError(f"Expected three section-effective pressure rows, found {len(section_rows)}")

    pressure_basis_rows = [
        {
            "basis_step": "gross_static_pressure_rise",
            "definition": "Endpoint static pressure rise across lower_leg__s04 to right_leg__s00",
            "formula_or_extraction": "Delta_p_static = p_static_downstream - p_static_upstream",
            "current_evidence": "Salt2/Salt3/Salt4 gross rises are about 3 kPa",
            "allowed_use": "context for hydrostatic dominance",
            "forbidden_use": "local loss coefficient target",
            "status": "available_context",
        },
        {
            "basis_step": "hydrostatic_head",
            "definition": "Gravity head across the two-tap elevation span",
            "formula_or_extraction": "Delta_p_hydrostatic = rho * g * Delta_z on the same endpoint basis",
            "current_evidence": "hydrostatic fraction of gross is approximately 1.0 for all rows",
            "allowed_use": "dominant pressure owner in thesis pressure ladder",
            "forbidden_use": "hide residual in component K",
            "status": "dominant_owner",
        },
        {
            "basis_step": "kinetic_correction",
            "definition": "Same-endpoint dynamic pressure correction",
            "formula_or_extraction": "Delta_p_kin retained separately from residual",
            "current_evidence": "finite small negative kinetic terms exist for all rows",
            "allowed_use": "basis decomposition",
            "forbidden_use": "absorb into K or F6 coefficient",
            "status": "available_separate_term",
        },
        {
            "basis_step": "straight_developing_reference",
            "definition": "Straight/reference and development subtraction needed before component isolation",
            "formula_or_extraction": "same-QOI same-basis straight/development reference minus endpoint pair",
            "current_evidence": "blocked_missing_same_basis_reference",
            "allowed_use": "admission blocker",
            "forbidden_use": "infer irreversible component loss",
            "status": "missing_blocks_component_k",
        },
        {
            "basis_step": "section_effective_residual",
            "definition": "Signed lower-right residual after hydrostatic and kinetic correction",
            "formula_or_extraction": "Delta_p_recirc_section = Delta_p_rgh - Delta_p_kin - Delta_p_straight - Delta_p_dev",
            "current_evidence": "Salt2/Salt3/Salt4 residuals are negative and small relative to gross pressure rise",
            "allowed_use": "thesis evidence for throughflow-plus-recirculation pressure modeling",
            "forbidden_use": "component K, cluster K, F6 fit, clipped K, or hidden multiplier",
            "status": "diagnostic_section_effective_only",
        },
    ]

    residual_rows: list[dict[str, object]] = []
    for row in section_rows:
        residual_rows.append(
            {
                "case_id": row["case_id"],
                "endpoint_pair": row["endpoint_pair"],
                "gross_static_pressure_rise_pa": row["gross_static_pressure_rise_pa"],
                "hydrostatic_term_pa": row["hydrostatic_term_pa"],
                "hydrostatic_fraction_of_gross": row["hydrostatic_fraction_of_gross"],
                "kinetic_term_pa": row["kinetic_term_pa"],
                "available_signed_residual_pa": row["available_signed_residual_pa"],
                "available_residual_percent_of_gross": row["available_residual_percent_of_gross"],
                "K_eff_recirc_diagnostic": row["K_eff_recirc_diagnostic"],
                "reverse_area_fraction": row["reverse_area_fraction"],
                "reverse_mass_fraction": row["reverse_mass_fraction"],
                "component_isolation_gate": row["component_isolation_gate"],
                "same_qoi_uncertainty_gate": row["same_qoi_uncertainty_gate"],
                "ordinary_recirculation_gate": row["ordinary_recirculation_gate"],
                "final_label": row["final_label"],
                "admission_status": row["admission_status"],
            }
        )

    gate_rows = [
        {
            "gate": row["gate"],
            "status": row["status"],
            "observed": row["observed"],
            "blocks": row["blocks"],
            "next_action": row["next_action"],
            "source": row["source"],
        }
        for row in s10_s14_rows
    ]
    gate_rows.append(
        {
            "gate": "source_property_nominal_train_release",
            "status": "fail",
            "observed": f"release_ready_rows={source_property['release_ready_rows']}; fit_allowed_rows={source_property['fit_allowed_rows']}",
            "blocks": "S11/S15/S6 source-property release",
            "next_action": "candidate-specific strict-pass source-envelope evidence before any release",
            "source": str(SOURCE_PROPERTY_PREFLIGHT.relative_to(REPO)),
        }
    )

    f3_f6_rows = [
        {
            "comparison": f3_rows[0]["comparison_id"],
            "baseline": f3_rows[0]["baseline"],
            "candidate": f3_rows[0]["candidate"],
            "status": f3_rows[0]["status_now"],
            "admitted_f6_rows": f3_rows[0]["admitted_f6_rows"],
            "numeric_score_released": False,
            "reason": f3_rows[0]["reason"],
        }
    ]
    for row in performance_rows:
        if row["comparison_id"] == "HPB-002":
            f3_f6_rows.append(
                {
                    "comparison": "Salt2_frozen_section_effective_transfer",
                    "baseline": "observed_section_effective_residual",
                    "candidate": "Delta_p_recirc_section with Salt2 diagnostic K_eff",
                    "status": row["numeric_status"],
                    "admitted_f6_rows": 0,
                    "numeric_score_released": True,
                    "reason": f"diagnostic no-fit transfer max_abs_error_pa={row['transfer_max_abs_error_pa']}",
                }
            )

    claim_rows = [
        {
            "claim_id": "PRESSURE-ALLOW-001",
            "claim": "The lower-right two-tap gross pressure rise is hydrostatic dominated.",
            "allowed": True,
            "required_citation": str(SECTION_SCORECARD.relative_to(REPO)),
            "forbidden_extension": "Treat gross pressure rise as local irreversible loss.",
        },
        {
            "claim_id": "PRESSURE-ALLOW-002",
            "claim": "After hydrostatic and kinetic correction, the available residual is small and negative for Salt2/Salt3/Salt4.",
            "allowed": True,
            "required_citation": str(SECTION_SCORECARD.relative_to(REPO)),
            "forbidden_extension": "Clip, sign-flip, or force the residual into a positive component K.",
        },
        {
            "claim_id": "PRESSURE-ALLOW-003",
            "claim": "The section-effective residual motivates a throughflow-plus-recirculation pressure term.",
            "allowed": True,
            "required_citation": str(HYBRID_CONTRACT.relative_to(REPO)),
            "forbidden_extension": "Claim candidate freeze, validation score, holdout score, or external generalization.",
        },
        {
            "claim_id": "PRESSURE-FORBID-001",
            "claim": "Current lower-right rows admit component K, cluster K, F6, clipped K, or a hidden multiplier.",
            "allowed": False,
            "required_citation": str(REVIEWABILITY.relative_to(REPO)),
            "forbidden_extension": "Use lower-right rows as fit evidence.",
        },
        {
            "claim_id": "PRESSURE-FORBID-002",
            "claim": "F3/Shah has been numerically beaten by F6 on the current pressure evidence.",
            "allowed": False,
            "required_citation": str(F3_F6_PREREQ.relative_to(REPO)),
            "forbidden_extension": "Publish F3-vs-F6 numeric comparison before ordinary-flow, endpoint, UQ, and source/property gates pass.",
        },
    ]

    figure_table_rows = [
        {
            "target": "Chapter 6 pressure admission methods table",
            "artifact": "pressure_basis_ladder.csv",
            "use": "Define pressure-basis terms and gate status.",
        },
        {
            "target": "Chapter 7 negative-result table",
            "artifact": "section_effective_residual_values.csv",
            "use": "Show exact signed residuals and failed component-K gates.",
        },
        {
            "target": "Appendix pressure claim boundary",
            "artifact": "thesis_pressure_claim_boundary.csv",
            "use": "Prevent external prose from promoting diagnostic rows to closures.",
        },
        {
            "target": "Appendix pressure gate matrix",
            "artifact": "pressure_non_admission_gate_matrix.csv",
            "use": "List endpoint, ordinary-flow, UQ, F3/F6, and source/property blockers.",
        },
    ]

    source_manifest = [
        {"source_id": "SRC-001", "path": str(SECTION_SCORECARD.relative_to(REPO)), "use": "section-effective values and failed gates", "mutation_status": "read_only"},
        {"source_id": "SRC-002", "path": str(HYBRID_CONTRACT.relative_to(REPO)), "use": "Delta_p_recirc_section term contract", "mutation_status": "read_only"},
        {"source_id": "SRC-003", "path": str(NO_FIT_PERFORMANCE.relative_to(REPO)), "use": "no-fit diagnostic transfer result", "mutation_status": "read_only"},
        {"source_id": "SRC-004", "path": str(RESIDUAL_OWNERSHIP.relative_to(REPO)), "use": "residual owner wording", "mutation_status": "read_only"},
        {"source_id": "SRC-005", "path": str(REVIEWABILITY.relative_to(REPO)), "use": "candidate reviewability boundary", "mutation_status": "read_only"},
        {"source_id": "SRC-006", "path": str(S10_S14_GATE.relative_to(REPO)), "use": "F6 non-admission gates", "mutation_status": "read_only"},
        {"source_id": "SRC-007", "path": str(F3_F6_PREREQ.relative_to(REPO)), "use": "F3/F6 comparison status", "mutation_status": "read_only"},
        {"source_id": "SRC-008", "path": str(SOURCE_PROPERTY_PREFLIGHT.relative_to(REPO)), "use": "source/property release blocker", "mutation_status": "read_only"},
        {"source_id": "SRC-009", "path": str(S14_SUMMARY.relative_to(REPO)), "use": "S14 pressure use-map counts", "mutation_status": "read_only"},
    ]

    no_mutation_rows = [
        {"guardrail": "native_solver_outputs_mutated", "value": False},
        {"guardrail": "registry_mutated", "value": False},
        {"guardrail": "scheduler_action", "value": False},
        {"guardrail": "solver_postprocessing_sampler_harvest_or_uq_launched", "value": False},
        {"guardrail": "fluid_or_external_edit", "value": False},
        {"guardrail": "validation_holdout_external_scoring", "value": False},
        {"guardrail": "fitting_or_model_selection_performed", "value": False},
        {"guardrail": "component_k_f6_or_clipped_k_admission", "value": False},
        {"guardrail": "hidden_multiplier_admission", "value": False},
        {"guardrail": "candidate_freeze", "value": False},
        {"guardrail": "source_property_release", "value": False},
        {"guardrail": "s11_s12_s13_s15_s6_trigger", "value": False},
        {"guardrail": "blocker_register_change", "value": False},
        {"guardrail": "generated_index_refresh", "value": False},
        {"guardrail": "residual_absorbed_into_internal_nu", "value": False},
    ]

    write_csv(OUT / "pressure_basis_ladder.csv", pressure_basis_rows, ["basis_step", "definition", "formula_or_extraction", "current_evidence", "allowed_use", "forbidden_use", "status"])
    write_csv(OUT / "section_effective_residual_values.csv", residual_rows, ["case_id", "endpoint_pair", "gross_static_pressure_rise_pa", "hydrostatic_term_pa", "hydrostatic_fraction_of_gross", "kinetic_term_pa", "available_signed_residual_pa", "available_residual_percent_of_gross", "K_eff_recirc_diagnostic", "reverse_area_fraction", "reverse_mass_fraction", "component_isolation_gate", "same_qoi_uncertainty_gate", "ordinary_recirculation_gate", "final_label", "admission_status"])
    write_csv(OUT / "pressure_non_admission_gate_matrix.csv", gate_rows, ["gate", "status", "observed", "blocks", "next_action", "source"])
    write_csv(OUT / "f3_f6_and_hybrid_comparison_status.csv", f3_f6_rows, ["comparison", "baseline", "candidate", "status", "admitted_f6_rows", "numeric_score_released", "reason"])
    write_csv(OUT / "thesis_pressure_claim_boundary.csv", claim_rows, ["claim_id", "claim", "allowed", "required_citation", "forbidden_extension"])
    write_csv(OUT / "figure_table_targets.csv", figure_table_rows, ["target", "artifact", "use"])
    write_csv(OUT / "source_manifest.csv", source_manifest, ["source_id", "path", "use", "mutation_status"])
    write_csv(OUT / "no_mutation_guardrails.csv", no_mutation_rows, ["guardrail", "value"])

    residuals = decimal_list(section_rows, "available_signed_residual_pa")
    salt2_transfer = next(row for row in performance_rows if row["comparison_id"] == "HPB-002")
    summary = {
        "task_id": TASK_ID,
        "date": DATE,
        "decision": "pressure_basis_ladder_packet_ready_thesis_evidence_only",
        "section_effective_rows": len(residual_rows),
        "negative_signed_residual_rows": sum(1 for value in residuals if value < 0),
        "component_k_admitted_rows": 0,
        "f6_fit_rows": 0,
        "clipped_k_rows": 0,
        "hidden_multiplier_rows": 0,
        "admitted_f6_rows": int(f3_rows[0]["admitted_f6_rows"]),
        "f3_f6_numeric_comparison_released": False,
        "salt2_frozen_transfer_max_abs_error_pa": salt2_transfer["transfer_max_abs_error_pa"],
        "low_recirc_anchor_rows": s14_summary.get("low_recirc_anchor_rows", 0),
        "source_property_release_ready_rows": source_property["release_ready_rows"],
        "validation_holdout_external_scoring": False,
        "fitting_or_model_selection_performed": False,
        "native_output_mutation": False,
        "registry_or_admission_mutation": False,
        "scheduler_action": False,
        "fluid_or_external_edit": False,
        "source_property_release": False,
        "candidate_freeze": False,
        "s11_s12_s13_s15_s6_trigger": False,
        "blocker_register_change": False,
        "generated_index_refresh": False,
        "residual_absorbed_into_internal_nu": False,
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    (OUT / "README.md").write_text(readme(summary), encoding="utf-8")
    return summary


def readme(summary: dict[str, object]) -> str:
    return f"""---
provenance:
  - {SECTION_SCORECARD.relative_to(REPO)}
  - {NO_FIT_PERFORMANCE.relative_to(REPO)}
  - {S10_S14_GATE.relative_to(REPO)}
tags: [thesis, pressure, f6, section-effective, negative-result]
related:
  - .agent/status/2026-07-22_TODO-THESIS-STUDY-PRESSURE-BASIS-LADDER-EVIDENCE-PACKET-2026-07-22.md
  - .agent/journal/2026-07-22/thesis-study-pressure-basis-ladder-evidence-packet.md
  - imports/2026-07-22_thesis_study_pressure_basis_ladder_evidence_packet.json
task: {TASK_ID}
date: {DATE}
role: Hydraulics/Writer/Reviewer/Tester
type: work_product
status: complete
---
# Thesis Pressure Basis Ladder Evidence Packet

## Result

Decision: `{summary["decision"]}`.

This package prepares pressure negative-result evidence for external thesis
writing. It does not admit component `K`, cluster `K`, F6, clipped `K`, a hidden
multiplier, or a frozen candidate.

- section-effective rows: `{summary["section_effective_rows"]}`
- negative signed residual rows: `{summary["negative_signed_residual_rows"]}`
- component-K admitted rows: `{summary["component_k_admitted_rows"]}`
- F6 fit rows: `{summary["f6_fit_rows"]}`
- F3/F6 numeric comparison released: `{summary["f3_f6_numeric_comparison_released"]}`
- Salt2-frozen diagnostic transfer max absolute error:
  `{summary["salt2_frozen_transfer_max_abs_error_pa"]} Pa`

## Interpretation

The current lower-right two-tap rows are useful because they quantify the
failure mode. Gross static pressure rise is hydrostatic dominated. After
hydrostatic and kinetic correction, Salt2/Salt3/Salt4 have small negative
section-effective residuals. Those residuals motivate a
throughflow-plus-recirculation term, `Delta_p_recirc_section`, but they do not
support ordinary component-K or F6 admission.

F3/Shah-vs-F6 remains not evaluated numerically. The current F6 path lacks an
ordinary-flow candidate, finite endpoint evidence, same-QOI UQ, source/property
release, and a frozen split-safe candidate.

## Outputs

- `pressure_basis_ladder.csv`
- `section_effective_residual_values.csv`
- `pressure_non_admission_gate_matrix.csv`
- `f3_f6_and_hybrid_comparison_status.csv`
- `thesis_pressure_claim_boundary.csv`
- `figure_table_targets.csv`
- `source_manifest.csv`
- `no_mutation_guardrails.csv`
- `summary.json`

## Thesis Claim Boundary

Allowed: the pressure basis ladder and signed residuals are thesis evidence for
why the hybrid pressure model is needed.

Forbidden: do not force a component `K`, clip negative residuals, infer an
ordinary single-stream loss, claim F6 admission, claim F3/Shah was beaten
numerically, or use these rows as validation/holdout/external-test evidence.
"""


def main() -> None:
    print(json.dumps(build(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
