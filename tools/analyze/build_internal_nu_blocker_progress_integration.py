#!/usr/bin/env python3
"""Build the internal-Nu blocker/progress integration package."""
from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[2]
TASK = "AGENT-345"
DATE = "2026-07-14"
SLUG = "internal_nu_blocker_progress_integration"
OUT = ROOT / "work_products/2026-07/2026-07-14/2026-07-14_internal_nu_blocker_progress_integration"

SOURCES = {
    "blockers": ROOT / ".agent/BLOCKERS.md",
    "extraction_contract": ROOT / "work_products/2026-07/2026-07-14/2026-07-14_upcomer_internal_nu_extraction_contract/README.md",
    "extraction_contract_csv": ROOT / "work_products/2026-07/2026-07-14/2026-07-14_upcomer_internal_nu_extraction_contract/upcomer_extraction_contract.csv",
    "admission_criteria": ROOT / "work_products/2026-07/2026-07-14/2026-07-14_upcomer_internal_nu_extraction_contract/upcomer_nu_admission_criteria.csv",
    "matched_plane_plan": ROOT / "work_products/2026-07/2026-07-14/2026-07-14_upcomer_matched_plane_extraction_plan/README.md",
    "matched_plane_targets": ROOT / "work_products/2026-07/2026-07-14/2026-07-14_upcomer_matched_plane_extraction_plan/upcomer_matched_plane_extraction_plan.csv",
    "salt_inventory": ROOT / "work_products/2026-07/2026-07-14/2026-07-14_salt_cfd_training_evidence_inventory/upcomer_onset_candidate_cases.csv",
    "residual_guardrails": ROOT / "work_products/2026-07/2026-07-14/2026-07-14_boundary_internal_nu_residual_guardrails/README.md",
    "forward_gate": ROOT / "work_products/2026-07/2026-07-14/2026-07-14_final_forward_v1_scorecard_gate/README.md",
    "hydraulic_contract": ROOT / "work_products/2026-07/2026-07-14/2026-07-14_hydraulic_reset_k_admission_contract/README.md",
    "submitted_runs": ROOT / "work_products/2026-07/2026-07-14/2026-07-14_submitted_cfd_run_steady_state_table/README.md",
}


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def write_csv(path: Path, rows: Iterable[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def source_manifest_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for source_id, path in SOURCES.items():
        rows.append(
            {
                "source_id": source_id,
                "path": rel(path),
                "exists": "yes" if path.exists() else "no",
                "use": {
                    "blockers": "authoritative current open/resolved blocker state",
                    "extraction_contract": "current zero-fit Nu decision and reopen evidence",
                    "extraction_contract_csv": "exact metric fields and formulas",
                    "admission_criteria": "classification gates and forbidden labels",
                    "matched_plane_plan": "existing proxy limitation and compute-node requirement",
                    "matched_plane_targets": "candidate plane/case extraction plan",
                    "salt_inventory": "candidate onset cases and corrected-Q/target-Re status",
                    "residual_guardrails": "physical residual ownership lanes",
                    "forward_gate": "forward-v1 restriction against fitted internal-Nu consumption",
                    "hydraulic_contract": "F6/K readiness dependency on admitted Re-variation rows",
                    "submitted_runs": "submitted CFD run readiness context",
                }[source_id],
            }
        )
    return rows


def assumptions_rows() -> list[dict[str, str]]:
    return [
        {
            "assumption_id": "zero_fit_internal_nu",
            "workstream": "internal-Nu admission",
            "assumption": "Current fit-admissible internal-Nu row count is zero.",
            "method": "Carry the AGENT-319/330/339 admission decision forward; do not infer fit eligibility from diagnostic Nu, HTC, UA, or section-effective rows.",
            "source_path": rel(SOURCES["extraction_contract"]),
            "process_step": "Before any model fit, read the admission table and confirm a later dated gate has explicitly admitted rows.",
            "validation_check": "README and admission tables must state current fit-admissible upcomer/internal-Nu rows remain 0.",
            "risk_if_wrong": "A forward model can silently absorb boundary, heater, cooler, storage, radiation, or recirculation residuals into Nu.",
            "owner_lane": "internal-Nu",
            "status": "active_assumption",
        },
        {
            "assumption_id": "section_effective_only_under_recirculation",
            "workstream": "coefficient naming",
            "assumption": "Recirculating upcomer rows may use section-effective diagnostic labels, not true single-stream Nu/f_D/K labels.",
            "method": "Classify rows with reverse-flow, Ri, or recirculation evidence as invalid single-stream coefficients unless all fit gates pass.",
            "source_path": rel(SOURCES["admission_criteria"]),
            "process_step": "Apply naming policy before exporting coefficients to downstream fitting or reporting tables.",
            "validation_check": "`Nu_section_effective_upcomer_diagnostic` is allowed only for diagnostic/validation use and forbidden for fit.",
            "risk_if_wrong": "A mixed-convection cell is mislabeled as ordinary pipe convection and contaminates correlations.",
            "owner_lane": "internal-Nu; therm-reconstr",
            "status": "active_assumption",
        },
        {
            "assumption_id": "geometric_plane_normal",
            "workstream": "matched-plane extraction",
            "assumption": "The plane normal for upcomer extraction must be geometric and oriented nominal inlet-to-outlet, not mean-velocity based.",
            "method": "Use mesh station tangent and fixed plane definitions; carry sign and reverse-flow metrics separately.",
            "source_path": rel(SOURCES["extraction_contract_csv"]),
            "process_step": "Reject admission-grade extraction rows that used mean-velocity normals.",
            "validation_check": "Extractor metadata records geometric normal and plane location for inlet/mid/outlet.",
            "risk_if_wrong": "The sampling normal can rotate with the cell and hide reverse flow.",
            "owner_lane": "therm-reconstr",
            "status": "active_assumption",
        },
        {
            "assumption_id": "existing_proxies_diagnostic_only",
            "workstream": "matched-plane extraction",
            "assumption": "Existing upcomer plane proxies are diagnostic because they lack face areas and matched wall-band wall T plus wallHeatFlux.",
            "method": "Treat AGENT-341 parsed values as planning/proxy rows until compute-node OpenFOAM sampling supplies the required fields.",
            "source_path": rel(SOURCES["matched_plane_plan"]),
            "process_step": "Keep proxy rows out of fit and validation admission tables.",
            "validation_check": "Matched-plane package states admission-grade extraction still requires compute-node sampling.",
            "risk_if_wrong": "A partial proxy row is promoted to an admission row without required thermal and vector metrics.",
            "owner_lane": "therm-reconstr",
            "status": "active_assumption",
        },
        {
            "assumption_id": "corrected_q_pending_terminal_harvest",
            "workstream": "cfd-pp",
            "assumption": "Corrected-Q rows are not admitted until terminal harvest, steady/admission review, and recirculation extraction complete.",
            "method": "Use corrected-Q candidate rows only as pending transition evidence until their terminal package is available.",
            "source_path": rel(SOURCES["salt_inventory"]),
            "process_step": "Monitor/harvest submitted jobs, then rerun steady-state and admission gates before Nu use.",
            "validation_check": "Candidate inventory marks selected corrected-Q rows as pending-terminal-harvest, running, stopped, or sensitivity-only.",
            "risk_if_wrong": "Transient or under-advanced rows can falsely bracket recirculation onset.",
            "owner_lane": "cfd-pp",
            "status": "active_assumption",
        },
        {
            "assumption_id": "smoke_repair_rows_diagnostic_until_admitted",
            "workstream": "mesh/GCI",
            "assumption": "Repaired or smoke thermal outputs remain diagnostic until an explicit gate admits them.",
            "method": "Do not convert readable repaired outputs into fit or publication GCI rows without sign, heat-balance, triplet, and uncertainty gates.",
            "source_path": rel(SOURCES["blockers"]),
            "process_step": "Keep closure-QOI mesh/GCI as the active trust limiter, not stale reconstruction blockers.",
            "validation_check": "Blocker ledger says refined-T corruption is resolved and closure-qoi-mesh-gci remains open.",
            "risk_if_wrong": "Thermal mesh uncertainty is claimed before row-level admission is complete.",
            "owner_lane": "mesh/GCI; internal-Nu",
            "status": "active_assumption",
        },
        {
            "assumption_id": "radiation_embedded_no_qr",
            "workstream": "thermal boundary semantics",
            "assumption": "CFD rcExternalTemperature wallHeatFlux includes radiation; no separate exported qr term exists for current rows.",
            "method": "Carry radiation as embedded wallHeatFlux semantics and forbid an extra Nu or wall residual for qr unless a future source explicitly exports qr.",
            "source_path": rel(SOURCES["residual_guardrails"]),
            "process_step": "Check thermal sign/boundary semantics before any heat-balance or Nu admission.",
            "validation_check": "No downstream row adds separate radiation on top of CFD wallHeatFlux.",
            "risk_if_wrong": "Radiation is double-counted or incorrectly assigned to internal Nu.",
            "owner_lane": "BC-modeling; internal-Nu",
            "status": "active_assumption",
        },
        {
            "assumption_id": "no_realized_cfd_inputs_for_forward_runtime",
            "workstream": "forward predictive model",
            "assumption": "Forward models must not consume realized CFD mdot, wallHeatFlux, or validation temperatures as runtime inputs.",
            "method": "Use extracted CFD quantities as diagnostics/admission evidence only, not predictive inputs.",
            "source_path": rel(SOURCES["forward_gate"]),
            "process_step": "Audit every proposed forward run input against setup/calibrated/validation/diagnostic classifications.",
            "validation_check": "Forward-v1 gate rejects fitted internal Nu consumption and preserves train/validation/holdout separation.",
            "risk_if_wrong": "The model becomes a replay or leakage exercise rather than a predictive model.",
            "owner_lane": "forward-pred; internal-Nu",
            "status": "active_assumption",
        },
        {
            "assumption_id": "f6_waits_admitted_re_variation",
            "workstream": "hydraulics",
            "assumption": "F6 friction/Re correction is a hydraulics candidate, but it waits for admitted Re-variation rows.",
            "method": "Keep pressure-loss validation primary and do not let thermal Nu evidence backfill hydraulic K/f gaps.",
            "source_path": rel(SOURCES["hydraulic_contract"]),
            "process_step": "After corrected-Q/target-Re admission, rebuild F6 pressure-loss scorecards.",
            "validation_check": "Hydraulic contract reports 0 component/cluster K fit-admissible rows and F6 blocked pending admitted Re variation.",
            "risk_if_wrong": "Hydraulic error is hidden in thermal coefficients.",
            "owner_lane": "hydraulics; cfd-pp",
            "status": "active_assumption",
        },
        {
            "assumption_id": "residual_ownership_before_nu_fit",
            "workstream": "thermal residual ownership",
            "assumption": "Heater, cooler, passive loss, wall storage, radiation, and branch mixing residuals must be assigned before Nu fitting reopens.",
            "method": "Use residual ownership lanes as a prefit ledger; Nu can receive only its physically admissible internal-convection residual.",
            "source_path": rel(SOURCES["residual_guardrails"]),
            "process_step": "Run residual ownership audit after extraction and before any fit decision.",
            "validation_check": "Every residual row has an owner lane and an explicit `do not fit into Nu` disposition where applicable.",
            "risk_if_wrong": "Internal Nu becomes a compensating knob for missing boundary physics.",
            "owner_lane": "BC-modeling; internal-Nu; forward-pred",
            "status": "active_assumption",
        },
    ]


def blocker_rows() -> list[dict[str, str]]:
    return [
        {
            "blocker_id": "closure-qoi-mesh-gci",
            "severity": "high",
            "current_state": "Mesh families and repaired thermal outputs exist, but 0 publication-ready closure-QOI GCI rows and 0 fit-admissible thermal rows are available.",
            "progress_made": "Resolved stale no-mesh/reconstruction blockers into a row-level GCI/sign/heat-balance admission problem.",
            "remaining_gate": "Publication-ready mesh triplets plus sign, heat-balance, lower-leg Nu, and downcomer policy checks.",
            "next_executable_action": "Build row-by-row closure-QOI mesh/GCI failed-gate matrix from refreshed thermal mesh package and current repaired/smoke status.",
            "owner_lane": "mesh/GCI; therm-reconstr; internal-Nu",
            "evidence_path": rel(SOURCES["blockers"]),
            "admission_impact": "Blocks thermal fit rows and publication uncertainty claims.",
            "status": "open_progress_possible_now",
        },
        {
            "blocker_id": "thermal-cfd-1d-parity",
            "severity": "high",
            "current_state": "The 7-study parity ladder and internal wall-adjacent-T problem remain unexecuted/open.",
            "progress_made": "Residual ownership guardrails and internal-Nu extraction contract prevent parity residuals from being absorbed into Nu.",
            "remaining_gate": "Execute parity ladder with matched wall/bulk/heat-flux evidence and residual ownership ledger.",
            "next_executable_action": "After matched-plane extraction lands, build thermal residual ledger separating heater, cooler/HX, passive loss, wall/storage, radiation semantics, and branch mixing.",
            "owner_lane": "BC-modeling; forward-pred; internal-Nu",
            "evidence_path": rel(SOURCES["residual_guardrails"]),
            "admission_impact": "Blocks predictive thermal claims and internal-Nu admission beyond diagnostics.",
            "status": "open_progress_possible_now",
        },
        {
            "blocker_id": "predictive-heater-cooler-wall-submodels",
            "severity": "high",
            "current_state": "Predictive thermal errors still require setup-side heater, cooler/HX, wall/layer, and external boundary submodels.",
            "progress_made": "Forward gate and residual guardrails identify which residuals are not Nu-owned.",
            "remaining_gate": "Implement or contract first-class HX/heater/wall-layer inputs without realized CFD wallHeatFlux or validation-temperature leakage.",
            "next_executable_action": "Create a boundary-model task matrix for HX UA/effectiveness, heater realized fraction/source split, wall-layer drive, and external boundary dictionary API.",
            "owner_lane": "BC-modeling; forward-pred",
            "evidence_path": rel(SOURCES["forward_gate"]),
            "admission_impact": "Blocks end-to-end predictive thermal scorecards; Nu fit remains closed.",
            "status": "open_progress_possible_now",
        },
        {
            "blocker_id": "upcomer-onset-data-sparsity",
            "severity": "medium",
            "current_state": "Available mainline Salt2/3/4 onset rows are all recirculating and below Re 150; onset is not bracketed by admitted non-recirculating evidence.",
            "progress_made": "AGENT-340 built candidate inventory; AGENT-341 defined matched-plane extraction; AGENT-342 submitted corrected-Q harvest jobs.",
            "remaining_gate": "Terminal corrected-Q harvest plus matched-plane Re/Pr/Ri/Ra/Gr/Gz, wall-bulk Delta T, reverse-flow, and uncertainty metrics; targeted Re 150/200/250 if onset remains unbracketed.",
            "next_executable_action": "Monitor/harvest corrected-Q jobs, run admission gate, then sample admitted candidates with matched-plane extractor.",
            "owner_lane": "cfd-pp; therm-reconstr; internal-Nu",
            "evidence_path": rel(SOURCES["salt_inventory"]),
            "admission_impact": "Keeps upcomer Nu single-stream fitting closed and labels section-effective diagnostics only.",
            "status": "open_progress_possible_now",
        },
        {
            "blocker_id": "fluid-external-boundary-api-gap",
            "severity": "medium",
            "current_state": "Fluid lacks first-class external boundary dictionaries for h/Ta/Tsur/emissivity/layers and drive-temperature selectors.",
            "progress_made": "Boundary/radiation semantics are now documented, including embedded radiation in CFD wallHeatFlux.",
            "remaining_gate": "Fluid-owned API for external boundary dictionaries and wall/layer semantics, with no double-counted radiation.",
            "next_executable_action": "Claim a Fluid API row before editing external ../cfd-modeling-tools, then implement setup-side external boundary dictionary support and repo-local parity tests.",
            "owner_lane": "Fluid; BC-modeling; forward-pred",
            "evidence_path": rel(SOURCES["residual_guardrails"]),
            "admission_impact": "Blocks physically faithful passive-loss replay and predictive wall-layer drives.",
            "status": "open_progress_requires_claim",
        },
        {
            "blocker_id": "f6-friction-re-correction",
            "severity": "medium",
            "current_state": "Current component/cluster K has 0 fit-admissible rows; F6 phi(Re) waits for admitted Re-variation pressure evidence.",
            "progress_made": "Hydraulic reset/K admission contract separates hydraulic readiness from thermal fitting.",
            "remaining_gate": "Admitted corrected-Q or targeted-Re rows with pressure-loss and mdot guardrails.",
            "next_executable_action": "After cfd-pp admits Re-variation rows, rerun F6 pressure-loss scorecards and keep thermal Nu out of hydraulic residuals.",
            "owner_lane": "hydraulics; cfd-pp",
            "evidence_path": rel(SOURCES["hydraulic_contract"]),
            "admission_impact": "Blocks hydraulic closure upgrade but should not block internal-Nu extraction documentation.",
            "status": "open_waiting_on_admitted_re_variation",
        },
    ]


def admission_decision_rows() -> list[dict[str, str]]:
    return [
        {
            "decision_id": "current_salt2_4_upcomer_internal_nu",
            "subject": "Salt2/Salt3/Salt4 current upcomer Nu/HTC/UA rows",
            "current_classification": "diagnostic_or_validation_only",
            "allowed_use": "regime interpretation, recirculation evidence, validation context with explicit caveat",
            "forbidden_use": "fit_admissible_Nu; universal single-stream Nu correlation fitting",
            "failed_gates": "reverse-flow evidence; Ri>=1 in current diagnostics; missing matched wall-bulk Delta T; missing Gz; missing secondary velocity fraction; missing wall-band wallHeatFlux; missing row-level uncertainty/residual ownership",
            "next_evidence_required": "Compute-node matched-plane extraction across inlet/mid/outlet plus terminal/admitted candidate cases.",
            "source_path": rel(SOURCES["extraction_contract"]),
        },
        {
            "decision_id": "nu_section_effective_upcomer_diagnostic",
            "subject": "Nu_section_effective_upcomer_diagnostic",
            "current_classification": "diagnostic_only",
            "allowed_use": "section heat-transfer diagnostic under recirculation or mixed-convection conditions",
            "forbidden_use": "fit_admissible_Nu; single-stream internal convection coefficient; forward runtime fitted Nu",
            "failed_gates": "recirculation invalidates single-stream interpretation unless all reverse-flow/Ri/secondary-flow gates pass",
            "next_evidence_required": "Separate non-recirculating single-stream anchor rows before any true Nu fit label is used.",
            "source_path": rel(SOURCES["admission_criteria"]),
        },
        {
            "decision_id": "matched_plane_proxy_rows",
            "subject": "Existing matched-plane proxy values from current postprocessing",
            "current_classification": "diagnostic_only",
            "allowed_use": "planning, sanity checks, station/case prioritization",
            "forbidden_use": "admission-grade Nu, validation-only Nu, fit Nu",
            "failed_gates": "no face areas; no matched wall-band area-weighted wall T and wallHeatFlux; legacy mean-velocity normal risk",
            "next_evidence_required": "Compute-node OpenFOAM sampling with geometric normals and matched wall/fluid station bands.",
            "source_path": rel(SOURCES["matched_plane_plan"]),
        },
        {
            "decision_id": "salt4_high_q_transition_candidates",
            "subject": "Salt4 high-Q corrected rows and other corrected-Q candidates",
            "current_classification": "pending_terminal_harvest_or_sensitivity_only",
            "allowed_use": "candidate onset planning after terminal status is known",
            "forbidden_use": "onset bracket, fit Nu, validation Nu before admission",
            "failed_gates": "terminal harvest/admission incomplete; matched recirculation metrics absent",
            "next_evidence_required": "Harvest jobs, run steady/admission review, extract matched Re/Pr/Ri/Ra/Gr/Gz/reverse-flow/wall-bulk metrics.",
            "source_path": rel(SOURCES["salt_inventory"]),
        },
        {
            "decision_id": "salt2_mesh_family_thermal_rows",
            "subject": "Salt2 coarse/medium/fine thermal mesh-family rows",
            "current_classification": "diagnostic_only_until_mesh_gate",
            "allowed_use": "mesh/GCI planning and diagnostic trend review",
            "forbidden_use": "publication-ready uncertainty; fit-admissible thermal Nu",
            "failed_gates": "0 publication-ready closure-QOI GCI rows; sign/heat-balance/lower-leg/downcomer policy gates open",
            "next_evidence_required": "Closure-QOI GCI failed-gate matrix and admitted thermal mesh triplets.",
            "source_path": rel(SOURCES["blockers"]),
        },
        {
            "decision_id": "forward_v1_internal_nu_consumption",
            "subject": "Forward-v1 use of internal Nu",
            "current_classification": "blocked_no_go_for_fitted_internal_nu",
            "allowed_use": "baseline/literature/default internal Nu behavior",
            "forbidden_use": "fitted internal Nu from current CFD diagnostic rows; realized CFD inputs at runtime",
            "failed_gates": "zero fit-admissible Nu rows; residual ownership incomplete; predictive input leakage risk",
            "next_evidence_required": "At least three admitted single-stream Nu rows plus residual ownership and train/validation split enforcement.",
            "source_path": rel(SOURCES["forward_gate"]),
        },
        {
            "decision_id": "thermal_residual_ownership",
            "subject": "Heater/cooler/passive wall/radiation/storage/branch residuals",
            "current_classification": "not_nu_owned",
            "allowed_use": "assign residuals to their physical model lanes before Nu fitting",
            "forbidden_use": "burying residuals in internal Nu, HTC, UA, or wallHeatFlux sign choices",
            "failed_gates": "residual lane not yet resolved for predictive model",
            "next_evidence_required": "Residual ledger after matched extraction and parity study execution.",
            "source_path": rel(SOURCES["residual_guardrails"]),
        },
        {
            "decision_id": "f6_hydraulic_re_correction",
            "subject": "F6_phi_re hydraulic correction",
            "current_classification": "hydraulic_candidate_waiting_on_admitted_re_variation",
            "allowed_use": "future pressure-loss scorecard after admitted Re-variation rows",
            "forbidden_use": "thermal Nu substitution for hydraulic residual",
            "failed_gates": "no admitted Re-variation rows; 0 component/cluster K fit-admissible rows",
            "next_evidence_required": "Admitted corrected-Q/target-Re pressure-loss rows.",
            "source_path": rel(SOURCES["hydraulic_contract"]),
        },
    ]


def next_action_rows() -> list[dict[str, str]]:
    return [
        {
            "priority": "P1",
            "owner_lane": "therm-reconstr",
            "action_id": "run_compute_node_matched_plane_sampling",
            "action": "Execute or finish the compute-node matched upcomer inlet/mid/outlet sampling workflow from AGENT-341/344.",
            "inputs": "AGENT-339 extraction contract; AGENT-341 sampling targets; admitted terminal case paths",
            "outputs": "Admission-grade reverse area/mass fractions, secondary velocity fraction, bulk T, wall T, wallHeatFlux, Re/Pr/Ri/Ra/Gr/Gz, plane/time metadata",
            "acceptance": "Every row uses geometric normals, face areas, matched wall/fluid station bands, and exact time windows; proxy-only rows remain marked diagnostic.",
            "blocked_by": "compute-node sampling not terminal in this package; active AGENT-344 owns implementation",
            "can_start_now": "yes_active_elsewhere",
        },
        {
            "priority": "P2",
            "owner_lane": "cfd-pp",
            "action_id": "harvest_corrected_q_terminal_rows",
            "action": "Monitor and harvest corrected-Q jobs, then run terminal steady/admission and recirculation extraction gates.",
            "inputs": "AGENT-342 job submissions; corrected-Q solver logs; AGENT-343 run steady-state table",
            "outputs": "Admitted or rejected corrected-Q candidate rows with terminal status and onset metrics",
            "acceptance": "No row is used for onset/Nu until terminal harvest and admission verdict are recorded.",
            "blocked_by": "scheduler terminal state and postprocessing completion",
            "can_start_now": "yes",
        },
        {
            "priority": "P3",
            "owner_lane": "internal-Nu",
            "action_id": "rebuild_nu_admission_from_extracted_metrics",
            "action": "Re-run the Nu admission decision after matched-plane metrics and corrected-Q admission land.",
            "inputs": "Matched-plane metric table; corrected-Q/target-Re admission table; residual ownership ledger",
            "outputs": "Updated diagnostic/validation/fit-admissible Nu decision table",
            "acceptance": "Fit reopens only with at least three admitted single-stream rows including a non-recirculating ordinary-pipe anchor and near-transition or higher-Re row.",
            "blocked_by": "P1 and usually P2",
            "can_start_now": "no",
        },
        {
            "priority": "P4",
            "owner_lane": "mesh/GCI",
            "action_id": "build_closure_qoi_gci_failed_gate_matrix",
            "action": "Convert closure-QOI mesh/GCI blocker into per-QOI failed gates and next evidence rows.",
            "inputs": "Thermal mesh gate refresh; repaired/smoke outputs; blocker ledger",
            "outputs": "QOI-by-QOI mesh/GCI admission matrix",
            "acceptance": "No smoke row is admitted unless sign, heat balance, triplet, monotonicity/oscillation, and policy gates pass.",
            "blocked_by": "none for diagnostic matrix; fit/publication rows need future evidence",
            "can_start_now": "yes",
        },
        {
            "priority": "P5",
            "owner_lane": "BC-modeling",
            "action_id": "define_boundary_model_task_matrix",
            "action": "Build setup-side task matrix for HX/cooler, heater/source, wall-layer/passive loss, storage, and radiation semantics.",
            "inputs": "Boundary residual guardrails; forward-v1 gate; thermal parity roadmap",
            "outputs": "Boundary model tasks with required inputs, forbidden runtime leakage, and acceptance tests",
            "acceptance": "Every thermal residual lane has an owner, setup/calibration/validation classification, and Nu exclusion rule.",
            "blocked_by": "none for contract; Fluid implementation needs separate claim",
            "can_start_now": "yes",
        },
        {
            "priority": "P6",
            "owner_lane": "Fluid; BC-modeling",
            "action_id": "implement_external_boundary_dictionary_api",
            "action": "Add first-class Fluid support for external h/Ta/Tsur/emissivity/layer dictionaries and drive-temperature selectors.",
            "inputs": "Fluid external boundary API task; boundary/radiation semantics",
            "outputs": "Fluid API and tests for external boundary replay/prediction without double-counted radiation",
            "acceptance": "Requires explicit board claim over external ../cfd-modeling-tools before edits.",
            "blocked_by": "external repo ownership claim",
            "can_start_now": "claim_required",
        },
        {
            "priority": "P7",
            "owner_lane": "hydraulics",
            "action_id": "rerun_f6_after_admitted_re_variation",
            "action": "Evaluate F6_phi_re only after admitted Re-variation pressure-loss rows exist.",
            "inputs": "Admitted corrected-Q/target-Re rows; hydraulic reset/K contract",
            "outputs": "F6 pressure-loss scorecard with mdot guardrails",
            "acceptance": "Thermal Nu is not used to compensate hydraulic residuals.",
            "blocked_by": "P2 or targeted-Re CFD admission",
            "can_start_now": "no",
        },
    ]


def readme_text(summary: dict[str, Any]) -> str:
    return f"""---
provenance:
  - {rel(SOURCES['blockers'])}
  - {rel(SOURCES['extraction_contract'])}
  - {rel(SOURCES['matched_plane_plan'])}
  - {rel(SOURCES['salt_inventory'])}
  - {rel(SOURCES['residual_guardrails'])}
tags: [internal-nu, blockers, admission, coordinator]
related:
  - operational_notes/maps/thermal-closures-and-internal-nu.md
task: {TASK}
date: {DATE}
role: Coordinator/Implementer/Tester/Writer
type: work_product
status: complete
---
# Internal-Nu Blocker Progress Integration

## Current Decision

Internal-Nu fitting remains closed. Current fit-admissible internal-Nu rows remain `0`.

The progress since the zero-fit decision is not a fit reopening. It is a conversion
of vague blockers into executable gates: matched-plane extraction, corrected-Q
terminal harvest, closure-QOI mesh/GCI failed-gate accounting, boundary residual
ownership, Fluid external boundary API work, and hydraulic Re-variation gating.

## What Can Move Now

1. Run or finish compute-node matched upcomer inlet/mid/outlet extraction under the
   active therm-reconstr workflow. Existing postprocessing proxies stay diagnostic.
2. Harvest corrected-Q terminal rows and run admission before using them as onset
   or Nu evidence.
3. Build the closure-QOI mesh/GCI failed-gate matrix; repaired and smoke thermal
   outputs are diagnostic until admitted.
4. Build the boundary-model task matrix so heater, cooler, wall/layer, storage,
   radiation, and branch-mixing residuals are not assigned to Nu.

## Major Blockers

- `closure-qoi-mesh-gci`: mesh families exist, but publication-ready thermal GCI
  and fit-admissible thermal rows do not.
- `thermal-cfd-1d-parity`: parity and wall-adjacent-T residual ownership remain
  unresolved.
- `predictive-heater-cooler-wall-submodels`: setup-side boundary submodels are
  still needed before predictive thermal claims.
- `upcomer-onset-data-sparsity`: all current mainline Salt upcomer points are
  recirculating; onset is not bracketed by admitted non-recirculating evidence.
- `fluid-external-boundary-api-gap`: Fluid needs first-class external boundary
  dictionaries before faithful passive-loss prediction.
- `f6-friction-re-correction`: hydraulic F6 waits for admitted Re-variation rows.

## Assumptions

This package assumes the authoritative blocker ledger is current as of
{summary['generated_at']}. It deliberately does not reopen stale blockers:
OF13 reconstruction works, mesh families exist, and CFD `rcExternalTemperature`
wallHeatFlux includes radiation. No separate exported `qr` term exists in the
current evidence stack.

It also assumes that current CFD diagnostics are evidence for admission decisions,
not forward-model runtime inputs. Forward models may use baseline/literature/default
internal Nu behavior today, but not fitted internal Nu from current rows.

## Methods

The builder reads the current blocker ledger and the July 14 internal-Nu,
matched-plane, onset-candidate, residual-guardrail, forward-gate, hydraulic, and
submitted-run packages. It writes:

- `assumptions_methods_process.csv`
- `blocker_progress_matrix.csv`
- `admission_decision_table.csv`
- `next_workstream_actions.csv`
- `source_manifest.csv`
- `summary.json`

No native CFD solver outputs, registry/admission state, scheduler state,
generated repo indexes, or external `../cfd-modeling-tools` files were mutated.
Generated index refresh is intentionally left untouched because active `AGENT-344`
currently owns that scope.

## Process

1. Claimed board row `{TASK}` before edits.
2. Read current blocker and internal-Nu source packages.
3. Encoded assumptions, blockers, admission decisions, and next actions in a
   reproducible builder.
4. Added focused tests that enforce zero-fit status, diagnostic naming, open
   blocker coverage, radiation semantics, and executable next actions.
5. Wrote dated status, journal, import, and work-product closeout artifacts.

## Reopen Evidence

Internal-Nu fitting can reopen only if a later dated gate admits at least three
single-stream upcomer rows, including an ordinary-pipe non-recirculating anchor
and a near-transition or higher-Re row, with matched reverse-flow, secondary-flow,
wall/bulk, heat-flux, nondimensional, mesh/time, residual-ownership, and
sign/radiation checks passing.
"""


def status_text(summary: dict[str, Any]) -> str:
    return f"""# {DATE} {TASK} Status

Status: COMPLETE

Built `work_products/2026-07/2026-07-14/2026-07-14_internal_nu_blocker_progress_integration/`.

Current decision remains unchanged: fit-admissible internal-Nu rows = `0`.

Outputs:
- `assumptions_methods_process.csv`
- `blocker_progress_matrix.csv`
- `admission_decision_table.csv`
- `next_workstream_actions.csv`
- `source_manifest.csv`
- `summary.json`

Generated at: `{summary['generated_at']}`

Notes:
- Did not mutate native CFD outputs, registry/admission state, scheduler state,
  generated repo indexes, or external `../cfd-modeling-tools`.
- Did not edit `.agent/BLOCKERS.md` because active `AGENT-344` owns generated
  index/blocker refresh scope.
"""


def journal_text(summary: dict[str, Any]) -> str:
    return f"""# Internal-Nu Blocker Progress Integration

Task: `{TASK}`
Date: `{DATE}`

## Assumptions

- Current fit-admissible internal-Nu row count remains `0`.
- Existing upcomer matched-plane proxies are diagnostic only.
- Corrected-Q rows require terminal harvest and admission before onset or Nu use.
- CFD `rcExternalTemperature` wallHeatFlux includes radiation; no separate
  exported `qr` residual is available.
- Repaired/smoke thermal rows remain diagnostic until admitted.

## Method

Read the current blocker ledger plus July 14 internal-Nu, matched-plane,
candidate-onset, residual-guardrail, forward-gate, hydraulic, and submitted-run
packages. Encoded the result in reproducible CSV tables and tests rather than a
free-form memo only.

## Result

The major open blockers now have executable next actions and owner lanes. This
does not reopen internal-Nu fitting; it documents the evidence required to make
that future decision without guessing scientific criteria.

Generated at: `{summary['generated_at']}`
"""


def build() -> dict[str, Any]:
    OUT.mkdir(parents=True, exist_ok=True)

    assumptions = assumptions_rows()
    blockers = blocker_rows()
    decisions = admission_decision_rows()
    actions = next_action_rows()
    manifest = source_manifest_rows()

    write_csv(
        OUT / "assumptions_methods_process.csv",
        assumptions,
        [
            "assumption_id",
            "workstream",
            "assumption",
            "method",
            "source_path",
            "process_step",
            "validation_check",
            "risk_if_wrong",
            "owner_lane",
            "status",
        ],
    )
    write_csv(
        OUT / "blocker_progress_matrix.csv",
        blockers,
        [
            "blocker_id",
            "severity",
            "current_state",
            "progress_made",
            "remaining_gate",
            "next_executable_action",
            "owner_lane",
            "evidence_path",
            "admission_impact",
            "status",
        ],
    )
    write_csv(
        OUT / "admission_decision_table.csv",
        decisions,
        [
            "decision_id",
            "subject",
            "current_classification",
            "allowed_use",
            "forbidden_use",
            "failed_gates",
            "next_evidence_required",
            "source_path",
        ],
    )
    write_csv(
        OUT / "next_workstream_actions.csv",
        actions,
        [
            "priority",
            "owner_lane",
            "action_id",
            "action",
            "inputs",
            "outputs",
            "acceptance",
            "blocked_by",
            "can_start_now",
        ],
    )
    write_csv(OUT / "source_manifest.csv", manifest, ["source_id", "path", "exists", "use"])

    summary: dict[str, Any] = {
        "task": TASK,
        "date": DATE,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "decision": "current_fit_admissible_internal_Nu_rows_remain_zero",
        "fit_admissible_internal_nu_rows": 0,
        "assumption_rows": len(assumptions),
        "blocker_rows": len(blockers),
        "admission_decision_rows": len(decisions),
        "next_action_rows": len(actions),
        "open_blockers_covered": [row["blocker_id"] for row in blockers],
        "outputs": [
            "README.md",
            "assumptions_methods_process.csv",
            "blocker_progress_matrix.csv",
            "admission_decision_table.csv",
            "next_workstream_actions.csv",
            "source_manifest.csv",
            "summary.json",
        ],
    }

    write_json(OUT / "summary.json", summary)
    (OUT / "README.md").write_text(readme_text(summary), encoding="utf-8")

    status = ROOT / ".agent/status/2026-07-14_AGENT-345.md"
    journal = ROOT / ".agent/journal/2026-07-14/internal-nu-blocker-progress-integration.md"
    import_path = ROOT / "imports/2026-07-14_internal_nu_blocker_progress_integration.json"
    status.write_text(status_text(summary), encoding="utf-8")
    journal.parent.mkdir(parents=True, exist_ok=True)
    journal.write_text(journal_text(summary), encoding="utf-8")
    write_json(
        import_path,
        {
            "task": TASK,
            "date": DATE,
            "kind": "work_product_import",
            "work_product": rel(OUT),
            "summary": rel(OUT / "summary.json"),
            "status": rel(status),
            "journal": rel(journal),
            "decision": summary["decision"],
            "fit_admissible_internal_nu_rows": 0,
            "generated_index_refresh": "not_run_active_AGENT_344_owns_generated_index_scope",
            "native_cfd_outputs_mutated": False,
            "external_cfd_modeling_tools_mutated": False,
        },
    )

    return summary


if __name__ == "__main__":
    print(json.dumps(build(), indent=2, sort_keys=True))
