#!/usr/bin/env python3
"""Build Salt external-test and perturbed-Q unlock admission tables.

This is a consolidation pass. It consumes existing postprocessing/admission
packages and does not inspect or mutate native OpenFOAM case outputs.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


DEFAULT_OUT = Path(
    "work_products/2026-07/2026-07-15/"
    "2026-07-15_salt_external_test_and_q_unlock_admission"
)

OSC = Path(
    "work_products/2026-07/2026-07-15/"
    "2026-07-15_salt_oscillation_expanded_case_set"
)
SALT_INV = Path(
    "work_products/2026-07/2026-07-14/"
    "2026-07-14_salt_cfd_training_evidence_inventory"
)
SALT_ROLLUP = Path(
    "work_products/2026-07/2026-07-14/"
    "2026-07-14_salt_training_testing_evidence_rollup"
)
VAL_DOC = Path(
    "work_products/2026-07/2026-07-14/"
    "2026-07-14_val_salt_test_2_coarse_mesh_documentation"
)
SALT1_BC = Path(
    "work_products/2026-07/2026-07-14/"
    "2026-07-14_salt1_terminal_bc_and_pm5_upcomer_harvest"
)
EXT_BC = Path(
    "work_products/2026-07/2026-07-14/"
    "2026-07-14_external_bc_thermal_profile_parity_study"
)
PM5_REFRESH = Path(
    "work_products/2026-07/2026-07-15/"
    "2026-07-15_downstream_pm5_final_state_refresh"
)
BLOCKER_WAVE = Path(
    "work_products/2026-07/2026-07-15/"
    "2026-07-15_blocker_resolution_wave_implementation"
)
AGENT410 = Path(
    "work_products/2026-07/2026-07-15/"
    "2026-07-15_diagnostic_cfd_heat_loss_replay_and_predictive_loss_plan"
)
AGENT408 = Path(
    "work_products/2026-07/2026-07-15/"
    "2026-07-15_corrected_q_live_terminal_gate_followup"
)


@dataclass(frozen=True)
class RequestedRow:
    case_key: str
    display_label: str
    salt_family: str
    variant: str
    requested_group: str
    focus_reason: str


REQUESTED_ROWS = [
    RequestedRow("salt1_nominal", "salt1_jin_nominal_continuation_corrected", "salt1", "nominal", "salt1", "Salt1 user-training row with lower-Re caveat."),
    RequestedRow("salt1_lo10q", "salt1_jin_lo10q_corrected", "salt1", "lo10q", "salt1_perturbed_q", "Salt1 low-Q training perturbation candidate."),
    RequestedRow("salt1_hi10q", "salt1_jin_hi10q_corrected", "salt1", "hi10q", "salt1_perturbed_q", "Salt1 high-Q training perturbation candidate; old conflict superseded in later rollout."),
    RequestedRow("salt3_jin_nominal", "viscosity_screening_salt_test_3_jin_coarse_mesh", "salt3", "nominal", "salt3", "Canonical Salt3 row for validation/training-policy discussion."),
    RequestedRow("salt3_lo5q", "salt3_jin_lo5q_corrected", "salt3", "lo5q", "salt3_perturbed_q", "Salt3 low-Q sensitivity candidate."),
    RequestedRow("salt3_lo10q", "salt3_jin_lo10q_corrected", "salt3", "lo10q", "salt3_perturbed_q", "Salt3 low-Q sensitivity candidate."),
    RequestedRow("salt3_hi5q", "salt3_jin_hi5q_corrected", "salt3", "hi5q", "salt3_perturbed_q", "Salt3 high-Q failed candidate."),
    RequestedRow("salt3_hi10q", "salt3_jin_hi10q_corrected", "salt3", "hi10q", "salt3_perturbed_q", "Salt3 high-Q failed candidate."),
    RequestedRow("salt2_native_val", "val_salt_test_2_coarse_mesh", "salt2", "native_validation_comparison", "external_test_candidate", "First external-test candidate, not admitted until ledgers match."),
    RequestedRow("salt2_lo5q", "salt2_jin_lo5q_corrected", "salt2", "lo5q", "holdout_perturbed_q", "Salt2 +/-5Q holdout/testing perturbation."),
    RequestedRow("salt2_hi5q", "salt2_jin_hi5q_corrected", "salt2", "hi5q", "holdout_perturbed_q", "Salt2 +/-5Q holdout/testing perturbation."),
    RequestedRow("salt4_lo5q", "salt4_jin_lo5q_corrected", "salt4", "lo5q", "training_perturbed_q", "Salt4 +/-5Q user-policy training perturbation."),
    RequestedRow("salt4_hi5q", "salt4_jin_hi5q_corrected", "salt4", "hi5q", "training_perturbed_q", "Salt4 +/-5Q user-policy training perturbation."),
    RequestedRow("salt2_lo10q", "salt2_jin_lo10q_corrected", "salt2", "lo10q", "live_perturbed_q", "Live selected +/-10Q continuation row."),
    RequestedRow("salt2_hi10q", "salt2_jin_hi10q_corrected", "salt2", "hi10q", "live_perturbed_q", "Live selected +/-10Q continuation row."),
    RequestedRow("salt4_lo10q", "salt4_jin_lo10q_corrected", "salt4", "lo10q", "live_perturbed_q", "Live selected +/-10Q continuation row."),
    RequestedRow("salt4_hi10q", "salt4_jin_hi10q_corrected", "salt4", "hi10q", "live_perturbed_q", "Live selected +/-10Q continuation row."),
    RequestedRow("salt3_hiq_hiins_legacy", "salt3_jin_hiq_hiins", "salt3", "legacy_hiq_hiins", "legacy_boundary_mutation", "Legacy Salt3 high-Q/high-insulation label audit context only."),
]


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="") as fh:
        return list(csv.DictReader(fh))


def write_csv(path: Path, rows: Iterable[dict[str, object]], fields: list[str]) -> int:
    materialized = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for row in materialized:
            writer.writerow({field: row.get(field, "") for field in fields})
    return len(materialized)


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as fh:
        json.dump(payload, fh, indent=2, sort_keys=True)
        fh.write("\n")


def by_key(rows: list[dict[str, str]], key: str) -> dict[str, dict[str, str]]:
    return {row.get(key, ""): row for row in rows if row.get(key)}


def exists_text(path: Path) -> str:
    return "yes" if path.exists() else "no"


def make_indexes() -> dict[str, object]:
    selected = by_key(read_csv(OSC / "selected_cases.csv"), "case_key")
    osc_summary = by_key(read_csv(OSC / "case_summary.csv"), "case_key")
    salt_candidates = by_key(read_csv(SALT_INV / "salt_cfd_candidate_inventory.csv"), "case_key")
    corrected_q = by_key(read_csv(SALT_INV / "corrected_q_perturbation_status.csv"), "case_key")
    rollout = by_key(read_csv(SALT_ROLLUP / "salt_training_testing_case_use_table.csv"), "case_key")
    pm5 = read_csv(PM5_REFRESH / "downstream_pm5_refresh_matrix.csv")
    f6 = read_csv(PM5_REFRESH / "f6_pm5_row_readiness.csv")
    inu = read_csv(PM5_REFRESH / "internal_nu_pm5_row_readiness.csv")
    thermal = read_csv(BLOCKER_WAVE / "thermal_internal_nu_admission_review.csv")
    heat_loss = read_csv(EXT_BC / "section_heat_loss_comparison.csv")
    ext_patch = read_csv(EXT_BC / "external_bc_patch_contract.csv")
    val_bc = read_csv(VAL_DOC / "boundary_condition_summary.csv")
    val_mat = read_csv(VAL_DOC / "material_property_evidence.csv")
    salt1_bc = read_csv(SALT1_BC / "salt1_terminal_bc_role_summary.csv")
    salt1_patch = read_csv(SALT1_BC / "salt1_terminal_patch_bc_role_table.csv")
    return {
        "selected": selected,
        "osc_summary": osc_summary,
        "salt_candidates": salt_candidates,
        "corrected_q": corrected_q,
        "rollout": rollout,
        "pm5": pm5,
        "f6": f6,
        "inu": inu,
        "thermal": thermal,
        "heat_loss": heat_loss,
        "ext_patch": ext_patch,
        "val_bc": val_bc,
        "val_mat": val_mat,
        "salt1_bc": salt1_bc,
        "salt1_patch": salt1_patch,
    }


def candidate_for(row: RequestedRow, idx: dict[str, object]) -> dict[str, str]:
    candidates = idx["salt_candidates"]  # type: ignore[index]
    corrected = idx["corrected_q"]  # type: ignore[index]
    selected = idx["selected"]  # type: ignore[index]
    rollout = idx["rollout"]  # type: ignore[index]
    key = {
        "salt1_nominal": "salt1_jin_nominal_continuation",
        "salt3_jin_nominal": "salt3_jin_nominal_continuation",
    }.get(row.case_key, row.case_key)
    base = {}
    if isinstance(candidates, dict):
        base.update(candidates.get(key, {}))
    if isinstance(corrected, dict):
        base.update(corrected.get(row.case_key, {}))
    if isinstance(selected, dict):
        base.update(selected.get(row.case_key, {}))
    if isinstance(rollout, dict):
        base.update(rollout.get(row.case_key, {}))
    return base


def steady_for(row: RequestedRow, idx: dict[str, object]) -> dict[str, str]:
    osc = idx["osc_summary"]  # type: ignore[index]
    if isinstance(osc, dict):
        return osc.get(row.case_key, {})
    return {}


def bc_status(row: RequestedRow, idx: dict[str, object]) -> tuple[str, str, str]:
    if row.case_key.startswith("salt1_"):
        n_summary = len(idx["salt1_bc"])  # type: ignore[arg-type]
        n_patch = len(idx["salt1_patch"])  # type: ignore[arg-type]
        if n_summary or n_patch:
            return (
                "patch_complete_salt1_terminal_bc_available",
                f"{n_summary} role-summary rows; {n_patch} patch rows",
                str(SALT1_BC / "salt1_terminal_patch_bc_role_table.csv"),
            )
    if row.case_key == "salt2_native_val":
        n_bc = len(idx["val_bc"])  # type: ignore[arg-type]
        n_mat = len(idx["val_mat"])  # type: ignore[arg-type]
        if n_bc:
            return (
                "val_salt2_bc_and_material_contract_available",
                f"{n_bc} BC summary rows; {n_mat} material/property rows",
                str(VAL_DOC / "boundary_condition_summary.csv"),
            )
    if row.salt_family in {"salt2", "salt3", "salt4"} and row.variant == "nominal":
        matching = [r for r in idx["ext_patch"] if r.get("case_id") == row.salt_family.replace("salt", "salt_")]  # type: ignore[index]
        if matching:
            return (
                "salt2_3_4_external_bc_contract_available",
                f"{len(matching)} patch contract rows",
                str(EXT_BC / "external_bc_patch_contract.csv"),
            )
    if "q" in row.variant:
        q = idx["corrected_q"].get(row.case_key, {}) if isinstance(idx["corrected_q"], dict) else {}  # type: ignore[index]
        if q:
            return (
                "corrected_q_manifest_and_preflight_available_pending_full_role_reduction",
                "corrected-Q manifest/preflight provenance exists; per-row BC role reduction still needed for final thesis-strength use",
                q.get("terminal_status_evidence_path", str(SALT_INV / "corrected_q_perturbation_status.csv")),
            )
    if row.case_key == "salt3_hiq_hiins_legacy":
        return (
            "legacy_label_audit_available_not_current_mainline",
            "legacy Salt3 hiq_hiins documentation exists; use as historical/sensitivity only unless re-admitted",
            str(Path("work_products/2026-07/2026-07-14/2026-07-14_salt_training_promotion_and_legacy_perturbation_audit/salt3_hiq_hiins_documentation.csv")),
        )
    return ("missing_or_not_promoted", "No promoted patch-complete BC contract found in scoped evidence", "")


def heat_loss_status(row: RequestedRow, idx: dict[str, object]) -> tuple[str, str, str]:
    if row.case_key == "salt2_native_val":
        return (
            "missing_current_section_heat_loss_ledger",
            "val_salt2 has BC/material documentation and steady traces, but no AGENT-350/365-style section heat-loss replay/admission package was found",
            str(VAL_DOC / "README.md"),
        )
    if row.salt_family in {"salt2", "salt3", "salt4"} and row.variant == "nominal":
        case_id = row.salt_family.replace("salt", "salt_")
        matches = [r for r in idx["heat_loss"] if r.get("case_id") == case_id]  # type: ignore[index]
        if matches:
            return (
                "section_heat_loss_ledger_available_diagnostic",
                f"{len(matches)} section heat-loss comparison rows; diagnostic/model-form evidence",
                str(EXT_BC / "section_heat_loss_comparison.csv"),
            )
    if row.case_key in {"salt2_lo5q", "salt2_hi5q", "salt4_lo5q", "salt4_hi5q"}:
        q = idx["corrected_q"].get(row.case_key, {}) if isinstance(idx["corrected_q"], dict) else {}  # type: ignore[index]
        if q.get("wall_heat_flux_grouped_csv"):
            return (
                "registry_wall_heat_flux_aggregate_available_needs_role_reduction",
                "Corrected-Q harvest wrote wall_heat_flux_grouped.csv, but thesis-strength heat-loss ledger still needs role reduction and split-aware admission",
                q["wall_heat_flux_grouped_csv"],
            )
    if row.case_key.startswith("salt1_"):
        return (
            "salt1_terminal_bc_available_heat_loss_ledger_not_promoted",
            "Salt1 terminal BC package exists; full section heat-loss ledger comparable to Salt2-4 not promoted in scoped evidence",
            str(SALT1_BC / "README.md"),
        )
    if row.case_key in {"salt2_lo10q", "salt2_hi10q", "salt4_lo10q", "salt4_hi10q"}:
        return (
            "pending_terminal_harvest",
            "Live +/-10Q rows cannot receive heat-loss ledger until job 3293924 exits and harvester 3295438 runs",
            str(AGENT408 / "README.md"),
        )
    return ("not_available_or_diagnostic_only", "No comparable heat-loss ledger found", "")


def closure_gate(row: RequestedRow, idx: dict[str, object]) -> dict[str, str]:
    f6_rows = [r for r in idx["f6"] if r.get("case_key") == row.case_key]  # type: ignore[index]
    inu_rows = [r for r in idx["inu"] if r.get("case_key") == row.case_key]  # type: ignore[index]
    pm5_rows = [r for r in idx["pm5"] if r.get("case_key") == row.case_key]  # type: ignore[index]
    thermal_rows = [r for r in idx["thermal"] if row.display_label in r.get("source_id", "") or row.salt_family.replace("salt", "salt_") == r.get("case_id", "")]  # type: ignore[index]

    def summarize(rows: list[dict[str, str]], field: str, default: str) -> str:
        if not rows:
            return default
        values = sorted(set(r.get(field, "") for r in rows if r.get(field, "")))
        return ";".join(values) if values else default

    return {
        "pm5_status": summarize(pm5_rows, "metric_status", "not_available"),
        "f6_status": summarize(f6_rows, "f6_review_status", "not_available_or_not_applicable"),
        "internal_nu_status": summarize(inu_rows, "internal_nu_review_status", summarize(thermal_rows, "review_admission_class", "not_available_or_not_applicable")),
        "upcomer_status": summarize(f6_rows, "f6_review_status", "not_available_or_not_applicable"),
        "mesh_gci_status": "diagnostic_only_zero_publication_ready_rows" if row.case_key == "salt3_jin_nominal" else "not_reviewed_in_this_row",
        "fit_admissible_closure_now": "no" if (f6_rows or inu_rows or thermal_rows or row.case_key in {"salt2_lo5q", "salt2_hi5q", "salt4_lo5q", "salt4_hi5q"}) else "not_applicable",
        "closure_gate_reason": (
            "PM5/F6/internal-Nu evidence exists but reverse-flow/sign/admission policy keeps fit rows at zero"
            if f6_rows or inu_rows
            else "No admitted closure-gate evidence in scoped sources"
        ),
    }


def final_decision(row: RequestedRow, base: dict[str, str], steady: dict[str, str], heat: tuple[str, str, str]) -> tuple[str, str, str, str]:
    heat_status = heat[0]
    if row.case_key in {"salt2_lo10q", "salt2_hi10q", "salt4_lo10q", "salt4_hi10q"}:
        return (
            "pending_terminal_harvest",
            "no",
            "Wait for 3293924 terminal state, let 3295438 run, then run terminal steady/admission, BC role reduction, heat-loss ledger, and PM5/F6/internal-Nu review.",
            "Live selected +/-10Q rows are still running and cannot be used downstream.",
        )
    if row.case_key in {"salt3_hi5q", "salt3_hi10q"}:
        return (
            "not_admissible_failed",
            "no",
            "Investigate failure/log cause before any future rebuild; no continuation submission in this pass.",
            "Salt3 high-Q corrected rows failed/not accepted.",
        )
    if row.case_key in {"salt3_lo5q", "salt3_lo10q"}:
        return (
            "sensitivity_only_needs_continuation_or_regate",
            "no",
            "Do not use for thesis training/testing now; if needed later, continue or re-gate after sufficient perturbed operating-point window.",
            "Salt3 low-Q rows are stopped/under-advanced under older gates.",
        )
    if row.case_key == "salt2_native_val":
        if heat_status.startswith("missing"):
            return (
                "external_test_candidate_blocked_heat_loss_ledger",
                "no",
                "Build val_salt2 section heat-loss ledger and admission package matching Salt2-4 external-BC/heat-loss contract before blind scoring.",
                "Steady and BC/material evidence exists, but matching heat-loss ledger is missing.",
            )
    if row.case_key in {"salt2_lo5q", "salt2_hi5q"}:
        return (
            "holdout_thermal_candidate_closure_diagnostic_only",
            "yes_for_thermal_holdout_only",
            "Use only as declared holdout/testing thermal rows; do not fit or tune on these rows; keep F6/internal-Nu diagnostic because recirculation/sign gates fail.",
            "Terminal harvest and aggregates exist; PM5 closure review remains not fit-admissible.",
        )
    if row.case_key in {"salt4_lo5q", "salt4_hi5q"}:
        return (
            "training_thermal_candidate_closure_diagnostic_only",
            "yes_for_user_policy_thermal_training_only",
            "Use only under explicit user-policy perturbed-Q training; keep labels perturbed and do not claim independent nominal baselines; F6/internal-Nu diagnostic only.",
            "Terminal harvest and aggregates exist; PM5 closure review remains not fit-admissible.",
        )
    if row.case_key.startswith("salt1_"):
        return (
            "training_thermal_candidate_salt1_caveats",
            "yes_for_user_policy_thermal_training_only",
            "Use for thermal training only with Salt1 lower-Re and perturbation-label caveats; do not use for F6/internal-Nu/onset fit without matched metrics.",
            "Later Salt1 package supersedes older context-only label for thermal training, but closure gates are not admitted.",
        )
    if row.case_key == "salt3_jin_nominal":
        return (
            "validation_or_user_training_candidate",
            "yes_after_split_policy_freeze",
            "Keep as canonical validation under older Salt2/Salt3/Salt4 split or user-requested training row only if that split is frozen before scoring.",
            "Nominal Salt3 is steady with Salt2-4 BC/heat-loss diagnostic ledgers available.",
        )
    if row.case_key == "salt3_hiq_hiins_legacy":
        return (
            "diagnostic_only_legacy_label_audit",
            "no",
            "Use as historical/label-correctness evidence only unless a separate re-admission contract proves mutation, terminal state, BCs, and postprocessing.",
            "Legacy hiins/hiq labels are not current mainline perturbed-Q evidence.",
        )
    return ("diagnostic_only", "no", "No admitted use assigned.", "Conservative default.")


def build_tables(out: Path) -> dict[str, int]:
    idx = make_indexes()
    master_rows: list[dict[str, object]] = []
    steady_rows: list[dict[str, object]] = []
    bc_rows: list[dict[str, object]] = []
    heat_rows: list[dict[str, object]] = []
    closure_rows: list[dict[str, object]] = []
    split_rows: list[dict[str, object]] = []
    blocked_rows: list[dict[str, object]] = []

    for row in REQUESTED_ROWS:
        base = candidate_for(row, idx)
        steady = steady_for(row, idx)
        bc = bc_status(row, idx)
        heat = heat_loss_status(row, idx)
        gate = closure_gate(row, idx)
        verdict, usable_now, next_action, reason = final_decision(row, base, steady, heat)

        master_rows.append(
            {
                "case_key": row.case_key,
                "display_label": row.display_label,
                "salt_family": row.salt_family,
                "variant": row.variant,
                "requested_group": row.requested_group,
                "run_state": base.get("run_state", "historical_or_unknown"),
                "latest_time_s": base.get("latest_time_s", ""),
                "postprocessing_available": base.get("postprocessing_exists", base.get("postprocessing_availability", "")),
                "steady_state_verdict": steady.get("verdicts", base.get("steady_state_class", "")),
                "bc_contract_status": bc[0],
                "heat_loss_ledger_status": heat[0],
                "closure_gate_status": gate["fit_admissible_closure_now"],
                "final_admission_decision": verdict,
                "usable_now": usable_now,
                "next_action": next_action,
                "reason": reason,
                "primary_evidence": base.get("primary_evidence", base.get("steady_state_admission_evidence_path", base.get("terminal_status_evidence_path", ""))),
            }
        )

        steady_rows.append(
            {
                "case_key": row.case_key,
                "display_label": row.display_label,
                "steady_state_verdict": steady.get("verdicts", base.get("steady_state_class", "")),
                "representative_groups": steady.get("representative_groups", ""),
                "steady_representative_groups": steady.get("steady_representative_groups", ""),
                "max_rel_sem_corrected": steady.get("max_rel_sem_corrected", ""),
                "max_drift_ratio": steady.get("max_drift_ratio", ""),
                "run_state": base.get("run_state", ""),
                "latest_time_s": base.get("latest_time_s", ""),
                "evidence_path": str(OSC / "case_summary.csv") if steady else base.get("steady_state_admission_evidence_path", ""),
            }
        )
        bc_rows.append(
            {
                "case_key": row.case_key,
                "display_label": row.display_label,
                "bc_contract_status": bc[0],
                "bc_contract_summary": bc[1],
                "bc_evidence_path": bc[2],
                "radiation_policy": "rcExternalTemperature emissivity/Tsur is setup metadata; realized wallHeatFlux already includes radiation and must not be double-counted",
            }
        )
        heat_rows.append(
            {
                "case_key": row.case_key,
                "display_label": row.display_label,
                "heat_loss_ledger_status": heat[0],
                "heat_loss_summary": heat[1],
                "heat_loss_evidence_path": heat[2],
                "predictive_runtime_policy": "realized CFD wallHeatFlux is diagnostic target/output, not predictive runtime input",
            }
        )
        closure_rows.append(
            {
                "case_key": row.case_key,
                "display_label": row.display_label,
                **gate,
                "source_metric_path": str(PM5_REFRESH / "f6_pm5_row_readiness.csv") if row.case_key in {"salt2_lo5q", "salt2_hi5q", "salt4_lo5q", "salt4_hi5q"} else "",
            }
        )
        split_rows.append(
            {
                "case_key": row.case_key,
                "display_label": row.display_label,
                "requested_group": row.requested_group,
                "final_admission_decision": verdict,
                "usable_now": usable_now,
                "split_guardrail": reason,
                "next_action": next_action,
            }
        )
        if usable_now == "no" or "diagnostic" in verdict or "pending" in verdict or "blocked" in verdict or "not_admissible" in verdict:
            blocked_rows.append(
                {
                    "case_key": row.case_key,
                    "display_label": row.display_label,
                    "blocker_or_caveat": verdict,
                    "next_action": next_action,
                    "blocking_evidence": heat[2] or bc[2] or base.get("terminal_status_evidence_path", ""),
                    "priority": "high" if row.case_key in {"salt2_native_val", "salt2_lo10q", "salt2_hi10q", "salt4_lo10q", "salt4_hi10q"} else "medium",
                }
            )

    counts = {
        "master": write_csv(
            out / "salt_unlock_master_inventory.csv",
            master_rows,
            [
                "case_key",
                "display_label",
                "salt_family",
                "variant",
                "requested_group",
                "run_state",
                "latest_time_s",
                "postprocessing_available",
                "steady_state_verdict",
                "bc_contract_status",
                "heat_loss_ledger_status",
                "closure_gate_status",
                "final_admission_decision",
                "usable_now",
                "next_action",
                "reason",
                "primary_evidence",
            ],
        ),
        "steady": write_csv(
            out / "terminal_steady_state_evidence.csv",
            steady_rows,
            [
                "case_key",
                "display_label",
                "steady_state_verdict",
                "representative_groups",
                "steady_representative_groups",
                "max_rel_sem_corrected",
                "max_drift_ratio",
                "run_state",
                "latest_time_s",
                "evidence_path",
            ],
        ),
        "bc": write_csv(
            out / "bc_source_contracts.csv",
            bc_rows,
            [
                "case_key",
                "display_label",
                "bc_contract_status",
                "bc_contract_summary",
                "bc_evidence_path",
                "radiation_policy",
            ],
        ),
        "heat": write_csv(
            out / "heat_loss_ledger_status.csv",
            heat_rows,
            [
                "case_key",
                "display_label",
                "heat_loss_ledger_status",
                "heat_loss_summary",
                "heat_loss_evidence_path",
                "predictive_runtime_policy",
            ],
        ),
        "closure": write_csv(
            out / "closure_gate_matrix.csv",
            closure_rows,
            [
                "case_key",
                "display_label",
                "pm5_status",
                "f6_status",
                "internal_nu_status",
                "upcomer_status",
                "mesh_gci_status",
                "fit_admissible_closure_now",
                "closure_gate_reason",
                "source_metric_path",
            ],
        ),
        "split": write_csv(
            out / "split_admission_decisions.csv",
            split_rows,
            [
                "case_key",
                "display_label",
                "requested_group",
                "final_admission_decision",
                "usable_now",
                "split_guardrail",
                "next_action",
            ],
        ),
        "blocked": write_csv(
            out / "pending_or_blocked_actions.csv",
            blocked_rows,
            ["case_key", "display_label", "blocker_or_caveat", "next_action", "blocking_evidence", "priority"],
        ),
    }

    manifest_rows = [
        {"source": str(OSC / "selected_cases.csv"), "used_for": "postProcessing paths and steady selected rows", "exists": exists_text(OSC / "selected_cases.csv")},
        {"source": str(OSC / "case_summary.csv"), "used_for": "TP/TW/mdot steady evidence", "exists": exists_text(OSC / "case_summary.csv")},
        {"source": str(SALT_INV / "salt_cfd_candidate_inventory.csv"), "used_for": "run status/admission/action base inventory", "exists": exists_text(SALT_INV / "salt_cfd_candidate_inventory.csv")},
        {"source": str(SALT_INV / "corrected_q_perturbation_status.csv"), "used_for": "corrected-Q run states and solver/log paths", "exists": exists_text(SALT_INV / "corrected_q_perturbation_status.csv")},
        {"source": str(SALT_ROLLUP / "salt_training_testing_case_use_table.csv"), "used_for": "user-policy split/admission labels", "exists": exists_text(SALT_ROLLUP / "salt_training_testing_case_use_table.csv")},
        {"source": str(VAL_DOC / "boundary_condition_summary.csv"), "used_for": "val_salt2 BC/source contract", "exists": exists_text(VAL_DOC / "boundary_condition_summary.csv")},
        {"source": str(SALT1_BC / "salt1_terminal_patch_bc_role_table.csv"), "used_for": "Salt1 patch-complete terminal BC roles", "exists": exists_text(SALT1_BC / "salt1_terminal_patch_bc_role_table.csv")},
        {"source": str(EXT_BC / "section_heat_loss_comparison.csv"), "used_for": "Salt2-4 nominal section heat-loss ledger status", "exists": exists_text(EXT_BC / "section_heat_loss_comparison.csv")},
        {"source": str(PM5_REFRESH / "f6_pm5_row_readiness.csv"), "used_for": "+/-5Q F6/upcomer review status", "exists": exists_text(PM5_REFRESH / "f6_pm5_row_readiness.csv")},
        {"source": str(PM5_REFRESH / "internal_nu_pm5_row_readiness.csv"), "used_for": "+/-5Q internal-Nu review status", "exists": exists_text(PM5_REFRESH / "internal_nu_pm5_row_readiness.csv")},
        {"source": str(AGENT408 / "scheduler_snapshot.csv"), "used_for": "live +/-10Q terminal-harvest blocker", "exists": exists_text(AGENT408 / "scheduler_snapshot.csv")},
    ]
    counts["manifest"] = write_csv(out / "source_manifest.csv", manifest_rows, ["source", "used_for", "exists"])

    decision_counts = Counter(row["final_admission_decision"] for row in split_rows)
    usable_counts = Counter(row["usable_now"] for row in split_rows)
    summary = {
        "task": "AGENT-417",
        "requested_rows": len(REQUESTED_ROWS),
        "output_counts": counts,
        "decision_counts": dict(sorted(decision_counts.items())),
        "usable_counts": dict(sorted(usable_counts.items())),
        "live_3293924_rows_blocked": sum(1 for row in split_rows if row["final_admission_decision"] == "pending_terminal_harvest"),
        "external_test_candidates_blocked": sum(1 for row in split_rows if row["final_admission_decision"] == "external_test_candidate_blocked_heat_loss_ledger"),
        "native_cfd_outputs_mutated": False,
        "scheduler_actions": "read_only_or_none",
    }
    write_json(out / "summary.json", summary)
    write_readme(out, summary)
    return counts


def write_readme(out: Path, summary: dict[str, object]) -> None:
    readme = f"""---
provenance:
  - {OSC / "case_summary.csv"}
  - {SALT_INV / "salt_cfd_candidate_inventory.csv"}
  - {VAL_DOC / "README.md"}
  - {PM5_REFRESH / "README.md"}
tags: [salt-cfd, admission, external-test, perturbed-q, heat-loss-ledger]
related:
  - operational_notes/maps/cfd-runs-and-admission.md
  - operational_notes/maps/forward-predictive-model.md
task: AGENT-417
date: 2026-07-15
role: cfd-pp/Thermal-admission/Hydraulics/Writer/Tester
type: work_product
status: complete
supersedes: []
superseded_by:
---
# Salt External-Test And Perturbed-Q Unlock Admission

## Observed Facts

- Requested rows consolidated: `{summary["requested_rows"]}`.
- Live selected +/-10Q rows remain blocked pending terminal harvest: `{summary["live_3293924_rows_blocked"]}`.
- `val_salt_test_2_coarse_mesh` has steady traces plus BC/material documentation, but no matching section heat-loss ledger in scoped evidence.
- Salt2/Salt4 +/-5Q PM5 rows now have wallHeatFlux and nondimensional fields, but F6/internal-Nu fit admission remains zero because recirculation/sign/admission gates fail.
- Salt3 nominal is steady and has Salt2-4 style BC/heat-loss diagnostic evidence; Salt3 corrected-Q high rows failed and low rows remain sensitivity/continuation candidates only.

## Inferred Interpretation

The best immediate thesis-safe use is thermal training/testing under explicit split policy. Closure-fit use is narrower: current PM5/F6/internal-Nu evidence is review-ready but not fit-admissible. `val_salt_test_2_coarse_mesh` is the right first external-test target, but it is blocked from thesis-strength external scoring until a matching heat-loss ledger and admission package exists.

## Usable Now

Use `split_admission_decisions.csv` as the authoritative table for this pass. In short:

- Salt1 nominal and Salt1 +/-10Q: user-policy thermal training candidates with Salt1 caveats; closure gates not admitted.
- Salt3 nominal: validation or user-training candidate only after the split policy is frozen.
- Salt2 +/-5Q: thermal holdout/testing candidates; not fit rows.
- Salt4 +/-5Q: user-policy thermal training candidates; not independent nominal baselines.

## Blocked Or Diagnostic

- `val_salt_test_2_coarse_mesh`: external-test candidate blocked by missing matching section heat-loss ledger.
- Salt3 low-Q corrected rows: sensitivity-only until continued or re-gated.
- Salt3 high-Q corrected rows: not admissible until failure cause is documented and a future rerun lands.
- Salt2/Salt4 +/-10Q: pending terminal harvest from live job `3293924` and dependent harvester `3295438`.
- F6/internal-Nu/upcomer closure rows: diagnostic/review-ready only; no fit-admissible rows in this pass.

## Files

- `salt_unlock_master_inventory.csv`
- `terminal_steady_state_evidence.csv`
- `bc_source_contracts.csv`
- `heat_loss_ledger_status.csv`
- `closure_gate_matrix.csv`
- `split_admission_decisions.csv`
- `pending_or_blocked_actions.csv`
- `source_manifest.csv`
- `summary.json`

## Guardrails

No native CFD outputs, scheduler state, registry/admission state, generated indexes, or external Fluid files were mutated. Realized CFD `wallHeatFlux` is treated as diagnostic target/output, not predictive runtime input.
"""
    (out / "README.md").write_text(readme)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    build_tables(args.output_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
