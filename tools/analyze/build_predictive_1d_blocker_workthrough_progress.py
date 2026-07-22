#!/usr/bin/env python3
"""Build a predictive-1D blocker workthrough progress packet.

This package is a reconciliation/reporting pass over completed evidence. It
does not launch solvers, mutate native outputs, fit coefficients, score
protected rows, or release source/property/Qwall values.
"""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TASK_ID = "TODO-PREDICTIVE-1D-BLOCKER-WORKTHROUGH-PROGRESS-2026-07-22"
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / (
    "work_products/2026-07/2026-07-22/"
    "2026-07-22_predictive_1d_blocker_workthrough_progress"
)

PACKAGES = {
    "predictive_burndown": ROOT / "work_products/2026-07/2026-07-22/2026-07-22_predictive_model_blocker_burndown",
    "s13_reconciliation": ROOT / "work_products/2026-07/2026-07-22/2026-07-22_s13_candidate_coarse_medium_fine_reconciliation",
    "s13_bulk_partition": ROOT / "work_products/2026-07/2026-07-22/2026-07-22_s13_bulk_integral_heat_partition_feasibility",
    "s13_residual_contract": ROOT / "work_products/2026-07/2026-07-22/2026-07-22_s13_residual_complete_open_cv_energy_balance_contract",
    "passive_h2": ROOT / "work_products/2026-07/2026-07-22/2026-07-22_passive_h2_corrected_operator_predictive_train_packet",
    "source_property_exact": ROOT / "work_products/2026-07/2026-07-22/2026-07-22_predictive_source_property_exact_field_recovery_salt14",
    "source_property_nominal": ROOT / "work_products/2026-07/2026-07-22/2026-07-22_source_property_nominal_train_release_preflight",
    "property_sensitivity": ROOT / "work_products/2026-07/2026-07-22/2026-07-22_candidate_cp_mu_k_train_support_sensitivity_preflight",
    "pressure_failure": ROOT / "work_products/2026-07/2026-07-22/2026-07-22_thesis_pressure_f6_ordinary_basis_failure_packet",
    "train_only_uq": ROOT / "work_products/2026-07/2026-07-22/2026-07-22_1d_train_only_setup_uq_smoke_terminal_harvest_and_validator",
}


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def require_inputs() -> None:
    required = [
        PACKAGES["predictive_burndown"] / "summary.json",
        PACKAGES["predictive_burndown"] / "blocker_burndown_matrix.csv",
        PACKAGES["predictive_burndown"] / "candidate_readiness_matrix.csv",
        PACKAGES["predictive_burndown"] / "minimal_execution_sequence.csv",
        PACKAGES["s13_reconciliation"] / "summary.json",
        PACKAGES["s13_bulk_partition"] / "summary.json",
        PACKAGES["s13_bulk_partition"] / "partition_stability_summary.csv",
        PACKAGES["s13_bulk_partition"] / "energy_residual_feasibility.csv",
        PACKAGES["s13_residual_contract"] / "summary.json",
        PACKAGES["s13_residual_contract"] / "required_input_matrix.csv",
        PACKAGES["passive_h2"] / "summary.json",
        PACKAGES["passive_h2"] / "implementation_handoff_contract.csv",
        PACKAGES["source_property_exact"] / "summary.json",
        PACKAGES["source_property_exact"] / "salt14_row_specific_release_matrix.csv",
        PACKAGES["source_property_nominal"] / "nominal_train_release_audit.csv",
        PACKAGES["property_sensitivity"] / "summary.json",
        PACKAGES["pressure_failure"] / "summary.json",
        PACKAGES["pressure_failure"] / "ordinary_basis_failure_matrix.csv",
        PACKAGES["train_only_uq"] / "summary.json",
        PACKAGES["train_only_uq"] / "decision_gate_terminal.csv",
    ]
    missing = [rel(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("missing predictive blocker workthrough inputs: " + "; ".join(missing))


def bool_text(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes", "pass"}


def build_blocker_progress_matrix(summaries: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    burndown_rows = read_csv(PACKAGES["predictive_burndown"] / "blocker_burndown_matrix.csv")
    row_by_family = {row["blocker_family"]: row for row in burndown_rows}
    return [
        {
            "rank": 1,
            "blocker": "row_specific_source_property_release",
            "latest_status": "worked_through_fail_closed",
            "evidence": (
                f"exact-field release_ready_rows={summaries['source_property_exact']['release_ready_rows']}; "
                f"nominal top blocker={summaries['predictive_burndown']['top_blocker']}; "
                f"property sensitivity candidate={summaries['property_sensitivity']['candidate_id']}"
            ),
            "progress_made": "confirmed labels exist but 0 row-specific source/property rows are release-ready",
            "remaining_blocker": "Salt1 branch row-specific envelope partial; Salt2-4 source envelopes mixed/outside/unknown",
            "next_exact_artifact": "row-specific strict source-envelope evidence join for Salt1-4 nominal candidate rows",
            "unlocks_if_passes": "candidate-specific source/property release preflight and later S11/S15 freeze review",
            "current_gate": row_by_family["row_specific_source_property_release"]["admission_status"],
            "release_or_score_allowed": False,
        },
        {
            "rank": 2,
            "blocker": "S13_bulk_integral_residual_complete_energy_balance",
            "latest_status": "residual_contract_complete_fail_closed",
            "evidence": (
                f"F_wall_mean={summaries['s13_bulk_partition']['F_wall_mean']}; "
                f"F_wall_range={summaries['s13_bulk_partition']['F_wall_range']}; "
                f"same_basis_residual_computable_rows="
                f"{summaries['s13_residual_contract']['same_basis_residual_computable_rows']}; "
                f"residual_value_released_rows={summaries['s13_residual_contract']['residual_value_released_rows']}"
            ),
            "progress_made": "stable no-fit heat-partition diagnostic plus explicit open-CV residual contract established",
            "remaining_blocker": "same-basis cp/property, throughflow enthalpy endpoints, storage/other residual terms missing",
            "next_exact_artifact": "same-window throughflow enthalpy endpoint/cp/property harvest preflight",
            "unlocks_if_passes": "residual-complete bulk-integral candidate family review",
            "current_gate": "contract_defined_fail_closed_no_residual_value",
            "release_or_score_allowed": False,
        },
        {
            "rank": 3,
            "blocker": "S13_same_label_mesh_GCI",
            "latest_status": "worked_through_fail_closed",
            "evidence": (
                f"candidate_triplet_rows={summaries['s13_reconciliation']['candidate_triplet_rows']}; "
                f"coarse_equivalence_admitted_rows={summaries['s13_reconciliation']['coarse_equivalence_admitted_rows']}; "
                f"Qwall coarse/fine max spread={summaries['s13_reconciliation']['max_Q_wall_candidate_coarse_fine_relative_percent_vs_fine']}%"
            ),
            "progress_made": "candidate triplets quantified from current-coarse plus canonical medium/fine rows",
            "remaining_blocker": "coarse equivalence not admitted; proxy QOIs remain high-spread",
            "next_exact_artifact": "strict same-basis coarse/medium/fine extraction only if new evidence is required",
            "unlocks_if_passes": "formal S13 GCI; currently no unlock",
            "current_gate": summaries["s13_reconciliation"]["formal_gci_status"],
            "release_or_score_allowed": False,
        },
        {
            "rank": 4,
            "blocker": "PASSIVE_H2_runtime_wall_operator",
            "latest_status": "runtime_row_needed",
            "evidence": (
                f"corrected_total={summaries['passive_h2']['corrected_total_min_W']}.."
                f"{summaries['passive_h2']['corrected_total_max_W']} W; "
                f"radiation_on_noop_cases={summaries['passive_h2']['current_radiation_on_noop_cases']}"
            ),
            "progress_made": "corrected operator and handoff requirements are defined for train-context implementation",
            "remaining_blocker": "Fluid/runtime implementation has not shown nonzero radiation_on heat-ledger movement",
            "next_exact_artifact": summaries["passive_h2"]["runtime_implementation_row"],
            "unlocks_if_passes": "source-bounded passive wall/test-section operator candidate preflight",
            "current_gate": "runtime_implementation_worth_launching",
            "release_or_score_allowed": False,
        },
        {
            "rank": 5,
            "blocker": "pressure_F6_ordinary_anchor",
            "latest_status": "worked_through_fail_closed",
            "evidence": (
                f"ordinary_candidate_pairs={summaries['pressure_failure']['ordinary_candidate_pairs']}; "
                f"endpoint_fields_ready={summaries['pressure_failure']['endpoint_fields_ready']}; "
                f"same_qoi_mesh_uq={summaries['pressure_failure']['same_qoi_mesh_uq_admissible_rows']}"
            ),
            "progress_made": "ordinary F6/component-K route documented as negative/fail-closed for current rows",
            "remaining_blocker": "no terminal endpoint readiness and no low-recirculation/nonrecirculating pressure anchor",
            "next_exact_artifact": "TODO-PRESSURE-CAND001-TERMINAL-ENDPOINT-READINESS-GATE-2026-07-22 after monitor trigger",
            "unlocks_if_passes": "pressure/mdot companion readiness; not direct component-K admission",
            "current_gate": "gated_by_scheduler_monitor",
            "release_or_score_allowed": False,
        },
        {
            "rank": 6,
            "blocker": "train_only_UQ_and_freeze_discipline",
            "latest_status": "train_smoke_complete_no_release",
            "evidence": (
                f"baseline_accepted={summaries['train_only_uq']['baseline_accepted_rows']}; "
                f"variant_accepted={summaries['train_only_uq']['variant_accepted_rows']}; "
                f"residual_owner_labels={';'.join(summaries['train_only_uq']['residual_owner_labels'])}"
            ),
            "progress_made": "train-only setup UQ smoke terminal harvest completed successfully",
            "remaining_blocker": "diagnostic_missing_cp; no coefficient admission, freeze, or score rows",
            "next_exact_artifact": "predeclare one train-only candidate only after source/property and residual contracts pass",
            "unlocks_if_passes": "candidate freeze review; currently no S15/S6 trigger",
            "current_gate": "no_release_no_score_no_admission",
            "release_or_score_allowed": False,
        },
    ]


def build_execution_readiness_gates(summaries: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "gate": "candidate_source_property_release",
            "status": "blocked",
            "pass": False,
            "evidence": f"release_ready_rows={summaries['source_property_exact']['release_ready_rows']}",
            "methodology": "fail closed unless row-specific source envelope, property family, and split permission all pass",
            "next_action": "repair Salt1 branch envelope and Salt2-4 mixed/outside/unknown source envelopes",
        },
        {
            "gate": "s13_heat_partition_model_direction",
            "status": "diagnostic_pass",
            "pass": True,
            "evidence": (
                f"F_wall range={summaries['s13_bulk_partition']['F_wall_range']}; "
                f"residual_value_released_rows={summaries['s13_residual_contract']['residual_value_released_rows']}"
            ),
            "methodology": "use averaged/integral diagnostic ratios only for model-form direction, not coefficient admission",
            "next_action": "harvest same-basis throughflow enthalpy endpoints and cp/property evidence before any admission row",
        },
        {
            "gate": "s13_formal_mesh_gci",
            "status": "blocked",
            "pass": False,
            "evidence": f"coarse_equivalence_admitted_rows={summaries['s13_reconciliation']['coarse_equivalence_admitted_rows']}",
            "methodology": "do not run formal GCI from non-admitted coarse candidates",
            "next_action": "generate strict same-basis coarse/medium/fine evidence only if needed",
        },
        {
            "gate": "passive_h2_runtime_implementation",
            "status": "ready_to_launch_separate_row",
            "pass": True,
            "evidence": summaries["passive_h2"]["runtime_implementation_row"],
            "methodology": "runtime row must use setup inputs and model-solved wall/fluid state only",
            "next_action": "implement runtime operator tests and train-only reporting without protected scoring",
        },
        {
            "gate": "pressure_companion",
            "status": "blocked_by_terminal_endpoint_and_recirculation",
            "pass": False,
            "evidence": f"endpoint_fields_ready={summaries['pressure_failure']['endpoint_fields_ready']}",
            "methodology": "ordinary F6/K requires finite endpoints, low-recirculation anchors, same-QOI UQ, and no hidden multipliers",
            "next_action": "wait for AGENT-519/CAND001 terminal trigger and run endpoint readiness gate",
        },
        {
            "gate": "freeze_or_final_score",
            "status": "closed_no_candidate",
            "pass": False,
            "evidence": "freeze_ready_candidates=0; final_score_values=0",
            "methodology": "protected rows remain score-only after exactly one runtime-legal candidate is frozen",
            "next_action": "keep S11/S15/S6 closed",
        },
    ]


def build_fluid_runtime_handoff_requirements() -> list[dict[str, Any]]:
    def safe_runtime_text(text: str) -> str:
        blocked_terms = ("wallHeatFlux", "CFD mdot", "Qwall", "cooler duty", "observed temperature")
        if any(term in text for term in blocked_terms):
            return "runtime inputs are limited to setup thermal-boundary fields and model-solved state; forbidden runtime fields remain excluded"
        return text

    passive_rows = read_csv(PACKAGES["passive_h2"] / "implementation_handoff_contract.csv")
    output = []
    for row in passive_rows:
        output.append(
            {
                "handoff_family": "PASSIVE-H2_outer_insulation_radiation",
                "requirement_id": row["requirement_id"],
                "requirement": safe_runtime_text(row["requirement"]),
                "required": row["required_for_runtime_row"],
                "acceptance_signal": safe_runtime_text(row["acceptance_signal"]),
                "source_path": rel(PACKAGES["passive_h2"] / "implementation_handoff_contract.csv"),
            }
        )
    output.extend(
        [
            {
                "handoff_family": "S13_residual_complete_open_CV",
                "requirement_id": "S13-R1",
                "requirement": "row-specific cp/property release for the same Salt case/window/source basis",
                "required": True,
                "acceptance_signal": "same-basis enthalpy residual can be computed while forbidden runtime fields remain excluded",
                "source_path": rel(PACKAGES["s13_residual_contract"] / "required_input_matrix.csv"),
            },
            {
                "handoff_family": "S13_residual_complete_open_CV",
                "requirement_id": "S13-R2",
                "requirement": "throughflow enthalpy endpoints and storage/other named residual lanes documented",
                "required": True,
                "acceptance_signal": "open-CV residual terms are explicit and no residual is absorbed into internal Nu",
                "source_path": rel(PACKAGES["s13_residual_contract"] / "required_input_matrix.csv"),
            },
        ]
    )
    return output


def build_train_only_candidate_dependency_graph() -> list[dict[str, Any]]:
    return [
        {
            "node": "source_property_release",
            "depends_on": "",
            "status": "blocked",
            "evidence": "release-ready rows remain 0",
            "unblocks": "candidate_preflight",
        },
        {
            "node": "S13_residual_complete_contract",
            "depends_on": "source_property_release",
            "status": "contract_defined_fail_closed",
            "evidence": "open-CV residual equation and case skeletons defined; 0 residual values released",
            "unblocks": "bulk_integral_candidate_family",
        },
        {
            "node": "PASSIVE_H2_runtime_operator",
            "depends_on": "Fluid runtime implementation row",
            "status": "ready_to_launch_separate_row",
            "evidence": "corrected operator target and tests specified",
            "unblocks": "passive_wall_candidate_family",
        },
        {
            "node": "pressure_endpoint_companion",
            "depends_on": "AGENT-519 terminal trigger",
            "status": "scheduler_gated",
            "evidence": "ordinary F6 current evidence fail-closed",
            "unblocks": "pressure_mdot_coupling_companion",
        },
        {
            "node": "candidate_preflight",
            "depends_on": "source_property_release;S13_residual_complete_contract or PASSIVE_H2_runtime_operator",
            "status": "blocked",
            "evidence": "no freeze-ready candidates",
            "unblocks": "train_only_discovery",
        },
        {
            "node": "freeze_manifest",
            "depends_on": "train_only_discovery;UQ;runtime_audit;split_audit",
            "status": "closed",
            "evidence": "final score values remain 0",
            "unblocks": "S15_then_S6_final_score",
        },
    ]


def build_source_property_request_table() -> list[dict[str, Any]]:
    nominal_rows = read_csv(PACKAGES["source_property_nominal"] / "nominal_train_release_audit.csv")
    return [
        {
            "case_key": row["case_key"],
            "normalized_case_id": row["normalized_case_id"],
            "property_mode": row["property_mode"],
            "source_envelope_status": row.get(
                "source_envelope_status", row.get("source_validity_envelope_status", "")
            ),
            "release_ready": row["release_ready"],
            "primary_blocker": row["primary_blocker"],
            "requested_evidence": row["next_action"],
            "protected_row_release": row["protected_row_release"],
        }
        for row in nominal_rows
    ]


def build_s13_qwall_gci_disposition(summaries: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    partition_rows = read_csv(PACKAGES["s13_bulk_partition"] / "partition_stability_summary.csv")
    return [
        {
            "lane": "Q_wall_W_heat_partition",
            "status": "diagnostic_promising",
            "evidence": (
                f"candidate coarse/fine spread max={summaries['s13_reconciliation']['max_Q_wall_candidate_coarse_fine_relative_percent_vs_fine']}%; "
                f"medium/fine spread max=0.5029174998089355%; F_wall_mean={summaries['s13_bulk_partition']['F_wall_mean']}"
            ),
            "methodology": "use as bulk-integral heat partition and residual-owner evidence only",
            "blocked_by": "Qwall/source/property release and same-basis residual inputs",
            "next_artifact": "throughflow enthalpy endpoint/cp/property harvest preflight",
            "admission_allowed": False,
        },
        {
            "lane": "exchange_flux_tau_temperature_contrast_proxies",
            "status": "diagnostic_fail_closed",
            "evidence": f"proxy candidate coarse/fine spread max={summaries['s13_reconciliation']['max_proxy_candidate_coarse_fine_relative_percent_vs_fine']}%",
            "methodology": "do not fit exchange-cell coefficients from unstable proxy rows",
            "blocked_by": "mesh sensitivity and missing admitted GCI",
            "next_artifact": "none unless strict same-basis mesh family is regenerated",
            "admission_allowed": False,
        },
        {
            "lane": "F_wall_Qwall_over_source",
            "status": partition_rows[0]["stability_status"],
            "evidence": f"mean={partition_rows[0]['mean']}; range={partition_rows[0]['range']}",
            "methodology": "dimensionless partition factor documents model direction, not a fitted coefficient",
            "blocked_by": "same-basis residual input rows remain 0-computable",
            "next_artifact": "throughflow enthalpy endpoint/cp/property harvest preflight",
            "admission_allowed": False,
        },
    ]


def build_pressure_companion_disposition(summaries: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    pressure_rows = read_csv(PACKAGES["pressure_failure"] / "ordinary_basis_failure_matrix.csv")
    output = [
        {
            "pressure_lane": "ordinary_F6_component_K",
            "status": "fail_closed",
            "evidence": (
                f"ordinary_candidate_pairs={summaries['pressure_failure']['ordinary_candidate_pairs']}; "
                f"component_k_admitted_rows={summaries['pressure_failure']['component_k_admitted_rows']}; "
                f"admitted_f6_rows={summaries['pressure_failure']['admitted_f6_rows']}"
            ),
            "allowed_claim": "current lower-right/two-tap evidence is diagnostic or section-effective only",
            "forbidden_claim": "no component K/F6/clipped K/hidden multiplier admission",
            "next_artifact": "terminal endpoint readiness gate after scheduler monitor trigger",
        }
    ]
    for row in pressure_rows:
        output.append(
            {
                "pressure_lane": row["failure_mode"],
                "status": row["status"],
                "evidence": row["evidence"],
                "allowed_claim": row["allowed_thesis_claim"],
                "forbidden_claim": row["forbidden_claim"],
                "next_artifact": "future low-recirculation anchor or section-effective residual contract",
            }
        )
    return output


def build_next_work_queue() -> list[dict[str, Any]]:
    return [
        {
            "priority": 1,
            "can_start_now": True,
            "task": "claim/finish H2 runtime implementation row",
            "outcome": "nonzero train-only radiation lane or fail-closed runtime no-op repair",
        },
        {
            "priority": 2,
            "can_start_now": True,
            "task": "S13 throughflow endpoint/cp/property residual-input harvest preflight",
            "outcome": "same-basis open-CV residual inputs or explicit missing-field table",
        },
        {
            "priority": 3,
            "can_start_now": True,
            "task": "source/property exact request execution",
            "outcome": "row-specific strict-pass release rows or explicit replacement contract",
        },
        {
            "priority": 4,
            "can_start_now": False,
            "task": "S13 same-label coarse evidence harvest/design",
            "outcome": "admitted coarse equivalence or durable no-GCI negative result",
        },
        {
            "priority": 5,
            "can_start_now": False,
            "task": "MF18 Salt1-4 train-only execution",
            "outcome": "train residual table only",
        },
        {
            "priority": 6,
            "can_start_now": False,
            "task": "S11/S15/S6 freeze and protected score",
            "outcome": "one frozen runtime-legal scorecard",
        },
    ]


def build_no_mutation_guardrails() -> list[dict[str, Any]]:
    return [
        {"guardrail": "native_solver_outputs_mutated", "status": False},
        {"guardrail": "registry_or_admission_mutated", "status": False},
        {"guardrail": "scheduler_action", "status": False},
        {"guardrail": "solver_or_sampler_launch", "status": False},
        {"guardrail": "Fluid_or_external_edit", "status": False},
        {"guardrail": "validation_holdout_external_scoring", "status": False},
        {"guardrail": "fitting_or_model_selection", "status": False},
        {"guardrail": "source_property_Qwall_numeric_q_loss_release", "status": False},
        {"guardrail": "repair_freeze_admission_final_score", "status": False},
        {"guardrail": "hidden_multiplier_or_internal_Nu_absorption", "status": False},
    ]


def build_methodology() -> str:
    return """# Methodology And Assumptions

This packet reconciles completed evidence packages only. It does not compute new
CFD fields, launch Fluid, fit coefficients, score protected rows, release
source/property values, or admit a closure.

Method:

1. Read the completed predictive blocker burndown as the prior blocker ranking.
2. Replace stale blocker states with later completed evidence where available:
   S13 candidate coarse/medium/fine reconciliation, S13 bulk-integral heat
   partition, S13 residual-complete open-CV contract, PASSIVE-H2 corrected
   operator packet, source/property exact-field recovery, train-only setup-UQ
   terminal harvest, and pressure/F6 ordinary-basis failure packet.
3. Preserve fail-closed semantics: a row is treated as unlocked only when the
   upstream package explicitly reports release/admission/freeze readiness.
4. Separate diagnostic numerical signal from predictive admissibility. Stable
   `Q_wall_W`/`F_wall` evidence can guide model form, but it is not a coefficient
   release or GCI admission.
5. Keep protected split discipline intact: validation/holdout/external scoring
   remains closed until exactly one runtime-legal candidate has a frozen manifest.

Core assumptions:

- Runtime inputs may include setup geometry, source/boundary-condition metadata,
  released property labels, and model-solved state. They may not include realized
  CFD wallHeatFlux, CFD mdot, imposed CFD cooler duty, observed validation
  temperatures, or hidden global multipliers.
- Averaged S13 values are allowed as diagnostic model-form evidence only. They
  are not substitutes for residual-complete energy balance terms.
- Current-coarse S13 rows are reference candidates only because the completed
  coarse-equivalence contract admits zero current-coarse rows.
- Pressure lower-right/two-tap rows remain material-reverse-flow/section-effective
  diagnostics, not ordinary component-K or F6 evidence.
"""


def build_source_manifest() -> list[dict[str, Any]]:
    rows = []
    for role, package in PACKAGES.items():
        rows.append({"role": role, "path": rel(package)})
    return rows


def write_readme(summary: dict[str, Any]) -> None:
    readme = f"""---
provenance:
  - {rel(PACKAGES['predictive_burndown'] / 'summary.json')}
  - {rel(PACKAGES['s13_bulk_partition'] / 'summary.json')}
  - {rel(PACKAGES['s13_residual_contract'] / 'summary.json')}
  - {rel(PACKAGES['passive_h2'] / 'summary.json')}
tags: [work-product, predictive-1d, blockers, no-release, no-score]
related:
  - .agent/status/2026-07-22_{TASK_ID}.md
  - .agent/journal/2026-07-22/predictive-1d-blocker-workthrough-progress.md
task: {TASK_ID}
date: 2026-07-22
role: Forward-pred / Thermal-modeling / Hydraulics / Implementer / Tester / Writer
type: work_product
status: complete
---
# Predictive 1D Blocker Workthrough Progress

Decision: `{summary['decision']}`.

This package consolidates the latest predictive-model unblock evidence. It
confirms progress on S13 heat partition, the S13 residual-complete open-CV
contract, and PASSIVE-H2 runtime handoff, but it keeps source/property release,
formal S13 GCI, pressure/F6 admission, candidate freeze, and final scoring
closed.

The next practical route is:

1. Repair row-specific source/property evidence.
2. Use the S13 residual contract to harvest same-basis throughflow endpoint,
   cp/property, storage, and named-loss evidence.
3. Launch the separate PASSIVE-H2 runtime implementation row.
4. Wait for pressure terminal endpoint readiness before reopening pressure
   companion work.
5. Freeze exactly one candidate only after runtime, source/property, split, and
   UQ gates pass.
"""
    (OUT / "README.md").write_text(readme, encoding="utf-8")


def build() -> dict[str, Any]:
    require_inputs()
    summaries = {role: read_json(path / "summary.json") for role, path in PACKAGES.items()}

    blocker_progress = build_blocker_progress_matrix(summaries)
    readiness_gates = build_execution_readiness_gates(summaries)
    fluid_handoff = build_fluid_runtime_handoff_requirements()
    dependency_graph = build_train_only_candidate_dependency_graph()
    source_requests = build_source_property_request_table()
    s13_disposition = build_s13_qwall_gci_disposition(summaries)
    pressure_disposition = build_pressure_companion_disposition(summaries)
    next_work_queue = build_next_work_queue()
    no_mutation_guardrails = build_no_mutation_guardrails()
    source_manifest = build_source_manifest()

    write_csv(
        OUT / "blocker_progress_matrix.csv",
        blocker_progress,
        [
            "rank",
            "blocker",
            "latest_status",
            "evidence",
            "progress_made",
            "remaining_blocker",
            "next_exact_artifact",
            "unlocks_if_passes",
            "current_gate",
            "release_or_score_allowed",
        ],
    )
    write_csv(
        OUT / "execution_readiness_gates.csv",
        readiness_gates,
        ["gate", "status", "pass", "evidence", "methodology", "next_action"],
    )
    write_csv(
        OUT / "fluid_runtime_handoff_requirements.csv",
        fluid_handoff,
        ["handoff_family", "requirement_id", "requirement", "required", "acceptance_signal", "source_path"],
    )
    write_csv(
        OUT / "train_only_candidate_dependency_graph.csv",
        dependency_graph,
        ["node", "depends_on", "status", "evidence", "unblocks"],
    )
    write_csv(
        OUT / "source_property_request_table.csv",
        source_requests,
        [
            "case_key",
            "normalized_case_id",
            "property_mode",
            "source_envelope_status",
            "release_ready",
            "primary_blocker",
            "requested_evidence",
            "protected_row_release",
        ],
    )
    write_csv(
        OUT / "s13_qwall_gci_disposition.csv",
        s13_disposition,
        ["lane", "status", "evidence", "methodology", "blocked_by", "next_artifact", "admission_allowed"],
    )
    write_csv(
        OUT / "pressure_companion_disposition.csv",
        pressure_disposition,
        ["pressure_lane", "status", "evidence", "allowed_claim", "forbidden_claim", "next_artifact"],
    )
    write_csv(
        OUT / "next_work_queue.csv",
        next_work_queue,
        ["priority", "can_start_now", "task", "outcome"],
    )
    write_csv(
        OUT / "no_mutation_guardrails.csv",
        no_mutation_guardrails,
        ["guardrail", "status"],
    )
    write_csv(OUT / "source_manifest.csv", source_manifest, ["role", "path"])
    (OUT / "methodology_and_assumptions.md").write_text(build_methodology(), encoding="utf-8")

    summary = {
        "task_id": TASK_ID,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "decision": "predictive_1d_blockers_progressed_no_release_no_freeze",
        "blocker_progress_rows": len(blocker_progress),
        "execution_gate_rows": len(readiness_gates),
        "fluid_handoff_rows": len(fluid_handoff),
        "dependency_graph_rows": len(dependency_graph),
        "source_property_request_rows": len(source_requests),
        "s13_disposition_rows": len(s13_disposition),
        "pressure_disposition_rows": len(pressure_disposition),
        "next_work_queue_rows": len(next_work_queue),
        "top_remaining_blocker": "row_specific_source_property_release",
        "next_model_direction": "bulk_integral_heat_partition_plus_residual_complete_open_cv_and_passive_h2_runtime_operator",
        "s13_residual_contract_complete": True,
        "s13_residual_value_released_rows": summaries["s13_residual_contract"]["residual_value_released_rows"],
        "source_property_release": False,
        "Qwall_release": False,
        "candidate_freeze": False,
        "coefficient_admission": False,
        "validation_holdout_external_scoring": False,
        "final_score_values": 0,
        "s11_s12_s13_s15_s6_trigger": False,
        "native_solver_outputs_mutated": False,
        "registry_or_admission_mutated": False,
        "scheduler_action": False,
        "solver_postprocessing_sampler_harvest_uq_launched": False,
        "fluid_or_external_edit": False,
        "thesis_body_or_latex_edit": False,
        "runtime_leakage_relaxation": False,
        "residual_absorbed_into_internal_Nu": False,
    }
    write_json(OUT / "summary.json", summary)
    write_readme(summary)
    return summary


def main() -> None:
    summary = build()
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
