#!/usr/bin/env python3
"""Build the Salt training-promotion and legacy perturbation audit package.

This package answers a policy-heavy CFD admission question without mutating
native OpenFOAM outputs.  It joins terminal-harvest evidence, last-window
steady-state detector results, postprocessing aggregate paths, boundary-role
summaries, and user-requested split overrides into reviewable CSVs.
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Iterable


REPO_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = REPO_ROOT / "work_products/2026-07/2026-07-14/2026-07-14_salt_training_promotion_and_legacy_perturbation_audit"

SALT1_REVIEW = REPO_ROOT / "work_products/2026-07/2026-07-13/2026-07-13_salt1_terminal_harvest_admission_review/admission_decision_table.csv"
SALT1_POSTPROCESSING = REPO_ROOT / "work_products/2026-07/2026-07-13/2026-07-13_salt1_terminal_harvest_admission_review/postprocessing_availability.csv"
SALT1_FINAL_WINDOW = REPO_ROOT / "work_products/2026-07/2026-07-13/2026-07-13_salt1_terminal_harvest_admission_review/final_window_admission_review.csv"
STEADY_TABLE = REPO_ROOT / "work_products/2026-07/2026-07-14/2026-07-14_submitted_cfd_run_steady_state_table/submitted_cfd_run_steady_state_table.csv"
COMPACT_TABLE = REPO_ROOT / "work_products/2026-07/2026-07-14/2026-07-14_submitted_cfd_run_steady_state_table/submitted_cfd_run_compact_lineage_table.csv"
PM5_MATRIX = REPO_ROOT / "work_products/2026-07/2026-07-14/2026-07-14_corrected_q_pm5_admission_split_processing/corrected_q_pm5_split_admission_matrix.csv"
PM5_HEAT = REPO_ROOT / "work_products/2026-07/2026-07-14/2026-07-14_corrected_q_pm5_admission_split_processing/corrected_q_pm5_heat_role_reduction.csv"
PM5_QUEUE = REPO_ROOT / "work_products/2026-07/2026-07-14/2026-07-14_corrected_q_pm5_admission_split_processing/corrected_q_pm5_forward_gate_queue.csv"
LEGACY_REQUAL = REPO_ROOT / "work_products/2026-07/2026-07-01/2026-07-01_claude_perturbation_requal/perturbation_requal.csv"
LEGACY_MANIFEST = REPO_ROOT / "jadyn_runs/modern_runs/2026-06-19_ethan_blocker_and_1d_followon_wave/campaign_manifest.csv"
BC_RESPONSE_INVALID = REPO_ROOT / "work_products/2026-07/2026-07-14/2026-07-14_flow_rate_temperature_bc_response_study/invalid_or_diagnostic_runs.csv"
MATCHED_READINESS = REPO_ROOT / "work_products/2026-07/2026-07-14/2026-07-14_upcomer_matched_plane_compute_extraction/candidate_readiness_matrix.csv"
MATCHED_RUNNER = REPO_ROOT / "work_products/2026-07/2026-07-14/2026-07-14_upcomer_matched_plane_compute_extraction/scripts/run_upcomer_matched_plane_compute.sh"
VAL_DOCS = REPO_ROOT / "work_products/2026-07/2026-07-14/2026-07-14_val_salt_test_2_coarse_mesh_documentation/README.md"

SALT1_CASE_MAP = {
    "salt1_nominal": "salt1_jin_nominal_continuation_corrected",
    "salt1_lo10q": "salt1_jin_lo10q_corrected",
    "salt1_hi10q": "salt1_jin_hi10q_corrected",
}

PM5_SPLIT_OVERRIDES = {
    "salt2_lo5q": ("holdout", "user_requested_salt2_pm5_holdout"),
    "salt2_hi5q": ("holdout", "user_requested_salt2_pm5_holdout"),
    "salt4_lo5q": ("training", "user_requested_salt4_pm5_training"),
    "salt4_hi5q": ("training", "user_requested_salt4_pm5_training"),
}

LEGACY_CASES = [
    "salt4_jin_hi5q_balq",
    "salt4_jin_lo5q_balq",
    "salt4_jin_hiq_hiins",
    "salt3_jin_hiq_hiins",
]


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, fieldnames: Iterable[str], rows: Iterable[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fieldnames))
        writer.writeheader()
        writer.writerows(rows)


def _rel(path_or_text: object) -> str:
    text = str(path_or_text)
    if not text:
        return ""
    path = Path(text)
    if path.is_absolute():
        try:
            return str(path.relative_to(REPO_ROOT))
        except ValueError:
            return str(path)
    return text


def _rows_by(path: Path, key: str) -> dict[str, dict[str, str]]:
    return {row.get(key, ""): row for row in _read_csv(path)}


def _source_exists(path_text: str) -> str:
    if not path_text:
        return ""
    path = Path(path_text)
    if not path.is_absolute():
        path = REPO_ROOT / path
    return str(path.exists())


def _salt1_training_package() -> list[dict[str, object]]:
    review = _rows_by(SALT1_REVIEW, "case_id")
    steady = _rows_by(STEADY_TABLE, "run_key")
    post_rows = _read_csv(SALT1_POSTPROCESSING)
    post_status_by_case = {row.get("case_id", ""): row for row in post_rows}
    rows: list[dict[str, object]] = []
    for case_id, run_key in SALT1_CASE_MAP.items():
        review_row = review.get(case_id, {})
        steady_row = steady.get(run_key, {})
        has_terminal = review_row.get("terminal_state_recorded") == "yes"
        has_post = review_row.get("postprocessing_status") == "harvest_inputs_present"
        is_steady = steady_row.get("steady_or_needs_continuation") == "steady"
        if case_id == "salt1_hi10q":
            verdict = "training_candidate_needs_conflict_resolution"
            gate = "terminal review says stationary; older inventory also marked failed/not-admissible, so require one curator signoff before use"
        elif has_terminal and has_post and is_steady:
            verdict = "training_admissible_by_salt1_policy_override"
            gate = "Salt1-specific package assembled and user policy allows Salt1 training use"
        else:
            verdict = "not_admitted"
            gate = "missing terminal, postprocessing, or steady-state evidence"
        rows.append({
            "case_id": case_id,
            "run_key": run_key,
            "terminal_harvest_evidence": _rel(SALT1_REVIEW),
            "terminal_state_recorded": review_row.get("terminal_state_recorded", ""),
            "slurm_job_or_step": review_row.get("slurm_job_or_step", ""),
            "stationarity_label": review_row.get("stationarity_label", ""),
            "steady_detector_label": steady_row.get("steady_or_needs_continuation", ""),
            "final_window_start_s": steady_row.get("last_time_or_window_start_s", ""),
            "final_window_end_s": steady_row.get("last_time_or_window_end_s", ""),
            "postprocessing_status": review_row.get("postprocessing_status", ""),
            "postprocessing_evidence": _rel(SALT1_POSTPROCESSING),
            "bc_role_table_status": "partial_case_level_available",
            "bc_role_evidence": "Salt1 terminal package plus inherited manifest/case-level roles; patch-complete terminal BC table still should be promoted in the next BC refresh",
            "operating_point_gate": "accepted_for_closure_training" if verdict.startswith("training_admissible") else "review_required",
            "split_policy": "Salt1 nominal and Salt1 +/-10Q are allowed as training/correlation-support rows by 2026-07-14 user override; perturbations remain labeled perturbations",
            "admission_verdict": verdict,
            "remaining_caveat": gate,
            "postprocessing_detail_evidence": _rel(post_status_by_case.get(case_id, {}).get("evidence_path", "")),
        })
    return rows


def _pm5_split_override_rows() -> list[dict[str, object]]:
    matrix = _rows_by(PM5_MATRIX, "case_key")
    heat = _rows_by(PM5_HEAT, "case_key")
    rows: list[dict[str, object]] = []
    for case_key, (split_role, policy) in PM5_SPLIT_OVERRIDES.items():
        row = matrix.get(case_key, {})
        heat_row = heat.get(case_key, {})
        fully_harvested = (
            row.get("terminal_harvest_state", "").startswith("COMPLETED")
            and row.get("closure_fit_admissible_terminal_gate") == "yes"
            and row.get("registry_aggregate_available") == "yes"
        )
        rows.append({
            "case_key": case_key,
            "source_case_key": row.get("source_case_key", ""),
            "baseline_case": row.get("baseline_case", ""),
            "salt_number": row.get("salt_number", ""),
            "variant": row.get("variant", ""),
            "q_ratio": row.get("q_ratio", ""),
            "requested_split_role": split_role,
            "split_policy_basis": policy,
            "terminal_harvest_state": row.get("terminal_harvest_state", ""),
            "closure_fit_admissible_terminal_gate": row.get("closure_fit_admissible_terminal_gate", ""),
            "registry_aggregate_available": row.get("registry_aggregate_available", ""),
            "thermal_postprocessing_complete": "yes" if fully_harvested and heat_row else "no",
            "final_window_start_s": heat_row.get("final_window_start_s", ""),
            "final_window_end_s": heat_row.get("final_window_end_s", ""),
            "heater_net_q_mean_W": heat_row.get("section_heater_net_q_mean_W", ""),
            "cooling_branch_total_removal_mean_W": heat_row.get("cooling_branch_total_removal_mean_W", ""),
            "ambient_proxy_mean_W": heat_row.get("ambient_proxy_mean_W", ""),
            "radiation_semantics": heat_row.get("radiation_semantics", ""),
            "runtime_use_guardrail": heat_row.get("runtime_use_guardrail", ""),
            "normalized_csv": _rel(row.get("normalized_csv", "")),
            "wall_heat_flux_grouped_csv": _rel(row.get("wall_heat_flux_grouped_csv", "")),
            "case_summary_csv": _rel(row.get("case_summary_csv", "")),
            "training_or_holdout_admission": "admitted_for_requested_split_role" if fully_harvested else "blocked",
            "remaining_gate": "matched pressure/upcomer metrics still pending; thermal closure rows can proceed with this caveat",
        })
    return rows


def _legacy_label_audit_rows() -> list[dict[str, object]]:
    requal = _rows_by(LEGACY_REQUAL, "run")
    manifest = _rows_by(LEGACY_MANIFEST, "case_key")
    steady = _rows_by(STEADY_TABLE, "run_key")
    bc = _rows_by(BC_RESPONSE_INVALID, "case_key")
    rows: list[dict[str, object]] = []
    for case_key in LEGACY_CASES:
        req = requal.get(case_key, {})
        man = manifest.get(case_key, {})
        steady_row = steady.get(case_key, {})
        bc_row = bc.get(case_key, {})
        if man:
            mutation = man.get("mutation_profile", "")
            insulation_delta = man.get("insulation_delta_in", "")
            stage_dir = man.get("stage_case_dir", "")
            job_id = man.get("job_id", "")
        else:
            mutation = "legacy_balq_q_perturbation"
            insulation_delta = "not_proven_changed"
            stage_dir = steady_row.get("run_root", "")
            job_id = steady_row.get("submitted_job_ids", "")
        if "hiins" in case_key and insulation_delta in {"0.00", "0", "0.0"}:
            trusted_label = "high-Q balanced-cooling baseline-insulation; do not label as high-insulation"
        elif "balq" in case_key:
            trusted_label = "balanced-cooling Q perturbation; no insulation-change claim"
        else:
            trusted_label = "legacy perturbation label requires restored source before stronger claim"
        false_steady = req.get("op_verdict") == "false_steady" or bc_row.get("evidence_class") == "invalid_false_steady"
        terminal_steady = steady_row.get("steady_or_needs_continuation") == "steady"
        if case_key == "salt3_jin_hiq_hiins":
            split = "not_training_needs_continuation"
            decision = "heat still drifting; use only to document failed/false-steady legacy construction"
        elif false_steady:
            split = "sensitivity_only_until_operating_point_gate_override"
            decision = "last-window flatness exists, but operating-point movement gate classified row false-steady"
        else:
            split = "training_candidate_after_bc_source_restore"
            decision = "needs source restoration and BC/provenance recheck"
        rows.append({
            "case_key": case_key,
            "trusted_physics_label": trusted_label,
            "mutation_profile": mutation,
            "heater_scale": man.get("heater_scale", ""),
            "q_ratio": req.get("q_ratio") or bc_row.get("q_ratio", ""),
            "Q_W": req.get("Q_W", ""),
            "nominal_Q_W": req.get("nominal_Q_W", ""),
            "insulation_delta_in": insulation_delta,
            "cooler_or_sink_label": "balanced cooling/removal from legacy manifest or BC response table",
            "thermal_bc_roles_available": bc_row.get("bc_summary_status", ""),
            "heater_power_W": bc_row.get("heater_power_W", ""),
            "cooling_power_W": bc_row.get("cooling_power_W", ""),
            "heater_h_W_m2K": bc_row.get("heater_h_W_m2K", ""),
            "heater_Ta_K": bc_row.get("heater_Ta_K", ""),
            "cooler_h_W_m2K": bc_row.get("cooler_h_W_m2K", ""),
            "cooler_Ta_K": bc_row.get("cooler_Ta_K", ""),
            "test_section_h_W_m2K": bc_row.get("test_section_h_W_m2K", ""),
            "insulated_h_W_m2K": bc_row.get("insulated_h_W_m2K", ""),
            "two_d_radiation_on": bc_row.get("two_d_radiation_on", ""),
            "terminal_steady_label": steady_row.get("steady_or_needs_continuation", ""),
            "steady_state_detection_status": steady_row.get("steady_state_detection_status", ""),
            "op_verdict": req.get("op_verdict", ""),
            "usable_for_correlation_prior_requal": req.get("usable_for_correlation", ""),
            "case_stage_path": _rel(stage_dir),
            "case_stage_path_exists": _source_exists(stage_dir),
            "job_id_or_submitted_jobs": job_id,
            "postprocessing_evidence_status": "derived_rollup_and_bc_response_available" if bc_row else "not_found",
            "split_decision": split,
            "training_use_decision": decision,
            "evidence_paths": ";".join(filter(None, [_rel(LEGACY_REQUAL), _rel(LEGACY_MANIFEST) if man else "", _rel(BC_RESPONSE_INVALID) if bc_row else "", _rel(STEADY_TABLE)])),
        })
        if not terminal_steady and case_key != "salt3_jin_hiq_hiins":
            rows[-1]["training_use_decision"] = "not terminal steady in current joined evidence"
    return rows


def _salt3_hiq_hiins_rows(legacy_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    row = next(item for item in legacy_rows if item["case_key"] == "salt3_jin_hiq_hiins")
    return [
        {
            "topic": "identity",
            "finding": "Name contains hiins, but manifest mutation is high-Q balanced-cooling baseline-insulation.",
            "evidence": row["evidence_paths"],
            "usable_status": "documented_not_training",
        },
        {
            "topic": "steady_state",
            "finding": f"Latest joined detector status is {row['steady_state_detection_status']} with terminal label {row['terminal_steady_label']}.",
            "evidence": _rel(STEADY_TABLE),
            "usable_status": "needs_continuation",
        },
        {
            "topic": "boundary_conditions",
            "finding": "Patch-role summary exists for parent/current BC response table; restored case-stage tree is not present at the manifest path in this checkout.",
            "evidence": row["evidence_paths"],
            "usable_status": "documented_partial_bc_source_restore_needed",
        },
        {
            "topic": "split_role",
            "finding": "Do not use as a training row until a new continuation reaches steady state and a terminal BC table is refreshed from the actual terminal case.",
            "evidence": _rel(LEGACY_REQUAL),
            "usable_status": "sensitivity_or_exclusion_only",
        },
    ]


def _training_split_rows(pm5_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = [
        {
            "case_key": "salt1_jin_nominal_continuation_corrected",
            "requested_split_role": "training",
            "basis": "Salt1-specific package assembled; user wants better closure fits",
            "use_now": "yes_with_caveats",
            "caveat": "patch-complete terminal BC table should be promoted in next BC refresh",
        },
        {
            "case_key": "salt1_jin_lo10q_corrected",
            "requested_split_role": "training_perturbation",
            "basis": "terminal stationary Salt1 perturbation; keep perturbed-Q label",
            "use_now": "yes_with_caveats",
            "caveat": "do not collapse into nominal Salt1",
        },
        {
            "case_key": "salt1_jin_hi10q_corrected",
            "requested_split_role": "training_perturbation_candidate",
            "basis": "terminal harvest review says stationary but older inventory had failed/not-admissible conflict",
            "use_now": "no_pending_conflict_resolution",
            "caveat": "curator must resolve conflict before fit use",
        },
        {
            "case_key": "salt4_jin",
            "requested_split_role": "training",
            "basis": "user explicitly moved Salt4 nominal out of holdout for current closure progress",
            "use_now": "yes",
            "caveat": "future holdout data must be collected; do not report Salt4 as untouched holdout",
        },
    ]
    for row in pm5_rows:
        rows.append({
            "case_key": row["source_case_key"],
            "requested_split_role": row["requested_split_role"],
            "basis": row["split_policy_basis"],
            "use_now": "yes_for_thermal_closure" if row["training_or_holdout_admission"] == "admitted_for_requested_split_role" else "no",
            "caveat": row["remaining_gate"],
        })
    return rows


def _matched_metric_readiness_rows(pm5_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    readiness = _rows_by(MATCHED_READINESS, "case_key")
    runner_text = MATCHED_RUNNER.read_text(encoding="utf-8") if MATCHED_RUNNER.exists() else ""
    rows: list[dict[str, object]] = []
    for row in pm5_rows:
        source_case_key = row["source_case_key"]
        short_key = str(row["case_key"])
        ready = readiness.get(short_key, {})
        runner_includes_case = source_case_key in runner_text or short_key in runner_text
        if runner_includes_case and ready.get("compute_readiness") == "runnable-now":
            status = "ready_to_submit"
            action = "submit matched-plane compute job"
        else:
            status = "not_submitted_blocked"
            action = "extend matched-plane compute case list with harvested +/-5Q case roots and mesh/reconstruction station mapping, then submit"
        rows.append({
            "case_key": short_key,
            "source_case_key": source_case_key,
            "requested_split_role": row["requested_split_role"],
            "terminal_harvest_complete": "yes" if row["terminal_harvest_state"].startswith("COMPLETED") else "no",
            "thermal_postprocessing_complete": row["thermal_postprocessing_complete"],
            "matched_plane_current_readiness": ready.get("compute_readiness", ""),
            "matched_plane_blocking_reason": ready.get("blocking_reason", ""),
            "current_runner_includes_case": str(runner_includes_case),
            "submission_status": status,
            "next_action": action,
            "evidence_path": _rel(MATCHED_READINESS),
        })
    return rows


def _more_training_data_todo_rows() -> list[dict[str, object]]:
    return [
        {
            "priority": 1,
            "candidate_group": "Salt4 nominal plus Salt4 +/-5Q perturbed-Q",
            "why_it_matters": "Immediate training expansion under user split override.",
            "next_action": "Use thermal closure aggregates now; add matched pressure/upcomer metrics after compute workflow is extended.",
            "evidence": f"{_rel(PM5_MATRIX)};{_rel(PM5_HEAT)}",
        },
        {
            "priority": 2,
            "candidate_group": "Salt2 +/-5Q perturbed-Q",
            "why_it_matters": "Requested holdout rows with terminal harvest and thermal aggregates.",
            "next_action": "Freeze as holdout; avoid model selection leakage; add matched pressure/upcomer metrics before hydraulic/upcomer scoring.",
            "evidence": f"{_rel(PM5_MATRIX)};{_rel(PM5_QUEUE)}",
        },
        {
            "priority": 3,
            "candidate_group": "Salt3 nominal and near-steady Salt3 perturbations",
            "why_it_matters": "Additional mid-range salt data with different Re/temperature; useful if heat drift can be removed.",
            "next_action": "Plan continuation for heat-drifting rows with known BC roles rather than admitting false steady rows.",
            "evidence": _rel(STEADY_TABLE),
        },
        {
            "priority": 4,
            "candidate_group": "Corrected/perturbed +/-10Q selected continuation rows",
            "why_it_matters": "Potential broader Q bracket once terminal harvest job 3295438 lands.",
            "next_action": "Wait for terminal harvest/admission evidence; do not launch duplicates.",
            "evidence": _rel(PM5_QUEUE),
        },
        {
            "priority": 5,
            "candidate_group": "New targeted upcomer-onset CFD",
            "why_it_matters": "Existing cases do not cleanly bracket Re_upcomer 150/200/250 onset with admitted metrics.",
            "next_action": "After current harvests, design targeted CFD only for missing onset anchors.",
            "evidence": _rel(MATCHED_READINESS),
        },
    ]


def _write_readme(out_dir: Path, summary: dict[str, object]) -> None:
    text = f"""---
provenance:
  task: AGENT-355
  generated_by: tools/analyze/build_salt_training_promotion_and_legacy_perturbation_audit.py
tags: [cfd-pp, salt, training-data, admission, perturbation, boundary-conditions]
related:
  - work_products/2026-07/2026-07-13/2026-07-13_salt1_terminal_harvest_admission_review/README.md
  - work_products/2026-07/2026-07-14/2026-07-14_corrected_q_pm5_admission_split_processing/README.md
  - work_products/2026-07/2026-07-14/2026-07-14_val_salt_test_2_coarse_mesh_documentation/README.md
---
# Salt Training Promotion And Legacy Perturbation Audit

## Observed Facts

- Salt1 nominal, lo10q, and hi10q have terminal harvest evidence in `{_rel(SALT1_REVIEW)}` and final-window steady labels in the submitted-run table.
- Salt2/Salt4 +/-5Q perturbed-Q rows from harvest job `3295437` have completed terminal harvest, registered aggregates, and heat-role reductions in `{_rel(PM5_MATRIX)}` and `{_rel(PM5_HEAT)}`.
- The user-requested split override is encoded here: Salt2 +/-5Q are holdout rows; Salt4 +/-5Q and Salt4 nominal are training rows.
- Legacy `hiins` names are not reliable physics labels. The June 19 manifest records `mutation_profile=hiQ_balQ_baselineIns` and `insulation_delta_in=0.00` for `salt3_jin_hiq_hiins` and `salt4_jin_hiq_hiins`.
- `salt3_jin_hiq_hiins` is not training-ready: it is heat-drifting in the joined steady-state table and failed the older operating-point movement gate.

## Inferred Interpretation

- Salt1 can now be used for training/correlation support under the dated Salt1 policy override captured in `salt1_training_admission_package.csv`, but `salt1_jin_hi10q_corrected` still needs curator signoff because older inventory evidence conflicts with the terminal-harvest review.
- Salt4 nominal is no longer holdout in this package. It is a training row by user policy; future holdout data must be collected separately.
- Salt4 legacy `balq`/`hiins` rows are useful sensitivity evidence, but the trustworthy label is Q/cooling perturbation with baseline insulation unless an actual terminal case dictionary proves otherwise. Last-window flatness alone does not erase the prior false-steady operating-point gate.

## Math And Gate Assumptions

- Perturbed-Q labels use `q_ratio = Q_case / Q_nominal`.
- A row can be terminal-harvested and still not fully admitted: admission also requires boundary-condition labels, registered postprocessing aggregates, an operating-point/steady-state gate, and split-policy assignment.
- `wallHeatFlux` for `rcExternalTemperature` patches includes the radiation semantics available to OpenFOAM in the total heat flux; no separate predictive `qr` runtime target is created here.

## Usable Now

- Training: Salt4 nominal, Salt4 +/-5Q perturbed-Q thermal closure rows, Salt1 nominal and Salt1 lo10q under caveats.
- Holdout: Salt2 +/-5Q perturbed-Q thermal closure rows, with leakage guardrails.
- Not yet fit-use: Salt1 hi10q until the failed/not-admissible conflict is resolved; Salt3 hiq/hiins; legacy Salt4 balq/hiins unless the operating-point gate is explicitly overridden.

## Perturbed +/-5Q Full Workflow Status

The +/-5Q rows have terminal harvest and thermal postprocessing. They have **not** completed matched pressure/upcomer metric extraction. The current matched-plane runner does not include the harvested +/-5Q cases, so this package does not submit a misleading job. The exact blocker and next command/workflow action are in `matched_pressure_upcomer_workflow_readiness.csv`.

## val_salt_test_2_coarse_mesh

Documentation is ready at `{_rel(VAL_DOCS)}` and includes alias migration, BC/property evidence, and the Salt2 Jin comparison.

## Files

- `salt1_training_admission_package.csv`
- `pm5_perturbed_q_split_override.csv`
- `salt_training_split_override.csv`
- `legacy_perturbation_label_audit.csv`
- `salt3_hiq_hiins_documentation.csv`
- `matched_pressure_upcomer_workflow_readiness.csv`
- `more_training_data_todo.csv`
- `source_manifest.csv`
- `summary.json`

## Summary

- Rows generated: `{summary["total_rows"]}`
- Training rows now allowed by this package: `{summary["training_now_count"]}`
- Holdout rows now allowed by this package: `{summary["holdout_now_count"]}`
- Native CFD outputs mutated: `false`
"""
    (out_dir / "README.md").write_text(text, encoding="utf-8")


def _source_manifest(generated: list[Path]) -> list[dict[str, object]]:
    sources = [
        SALT1_REVIEW,
        SALT1_POSTPROCESSING,
        SALT1_FINAL_WINDOW,
        STEADY_TABLE,
        COMPACT_TABLE,
        PM5_MATRIX,
        PM5_HEAT,
        PM5_QUEUE,
        LEGACY_REQUAL,
        LEGACY_MANIFEST,
        BC_RESPONSE_INVALID,
        MATCHED_READINESS,
        MATCHED_RUNNER,
        VAL_DOCS,
    ]
    rows = [
        {"artifact": path.name, "role": "read_only_input", "path": _rel(path), "exists": path.exists(), "notes": "input evidence; not mutated"}
        for path in sources
    ]
    rows.extend(
        {"artifact": path.name, "role": "generated_output", "path": _rel(path), "exists": path.exists(), "notes": "generated by AGENT-355 builder"}
        for path in generated
    )
    return rows


def build_salt_training_promotion_and_legacy_perturbation_audit(out_dir: Path | None = None) -> dict[str, object]:
    out_dir = out_dir or OUT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    salt1_rows = _salt1_training_package()
    pm5_rows = _pm5_split_override_rows()
    legacy_rows = _legacy_label_audit_rows()
    split_rows = _training_split_rows(pm5_rows)
    matched_rows = _matched_metric_readiness_rows(pm5_rows)
    todo_rows = _more_training_data_todo_rows()
    salt3_rows = _salt3_hiq_hiins_rows(legacy_rows)

    outputs: list[tuple[str, list[str], list[dict[str, object]]]] = [
        ("salt1_training_admission_package.csv", list(salt1_rows[0]), salt1_rows),
        ("pm5_perturbed_q_split_override.csv", list(pm5_rows[0]), pm5_rows),
        ("salt_training_split_override.csv", list(split_rows[0]), split_rows),
        ("legacy_perturbation_label_audit.csv", list(legacy_rows[0]), legacy_rows),
        ("salt3_hiq_hiins_documentation.csv", list(salt3_rows[0]), salt3_rows),
        ("matched_pressure_upcomer_workflow_readiness.csv", list(matched_rows[0]), matched_rows),
        ("more_training_data_todo.csv", list(todo_rows[0]), todo_rows),
    ]
    generated: list[Path] = []
    for filename, fields, rows in outputs:
        path = out_dir / filename
        _write_csv(path, fields, rows)
        generated.append(path)

    manifest_path = out_dir / "source_manifest.csv"
    _write_csv(manifest_path, ["artifact", "role", "path", "exists", "notes"], _source_manifest(generated))
    generated.append(manifest_path)

    role_counts = Counter(row["requested_split_role"] for row in split_rows)
    summary = {
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "task": "AGENT-355",
        "total_rows": sum(len(rows) for _, _, rows in outputs),
        "salt1_training_rows_admitted_or_conditional": sum(1 for row in salt1_rows if "training" in str(row["admission_verdict"])),
        "training_now_count": sum(1 for row in split_rows if str(row["requested_split_role"]).startswith("training") and str(row["use_now"]).startswith("yes")),
        "holdout_now_count": sum(1 for row in split_rows if row["requested_split_role"] == "holdout" and str(row["use_now"]).startswith("yes")),
        "matched_pressure_upcomer_pm5_submitted": False,
        "matched_pressure_upcomer_pm5_blocker": "current matched-plane runner does not include harvested +/-5Q case roots and readiness table does not mark them runnable-now",
        "split_role_counts": dict(sorted(role_counts.items())),
        "native_solver_outputs_mutated": False,
        "required_outputs": [item[0] for item in outputs] + ["source_manifest.csv", "summary.json", "README.md"],
    }
    summary_path = out_dir / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    generated.append(summary_path)
    _write_readme(out_dir, summary)
    return summary


def main() -> None:
    print(json.dumps(build_salt_training_promotion_and_legacy_perturbation_audit(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
