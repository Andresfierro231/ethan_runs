#!/usr/bin/env python3
"""Build a CFD case admission inventory for cfd-pp.

The builder is intentionally read-only with respect to solver case trees.  It
reduces existing admission/split/boundary evidence into three human-facing CSVs:
case admission, boundary-condition roles, and train/validation/holdout
candidates.
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List


REPO_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = REPO_ROOT / "work_products/2026-07/2026-07-14/2026-07-14_cfd_case_admission_inventory"

SPLIT_TABLE = REPO_ROOT / "work_products/2026-07/2026-07-13/2026-07-13_predictive_validation_split/admission_split_table.csv"
PATCH_ROLE_TABLE = REPO_ROOT / "work_products/2026-07/2026-07-13/2026-07-13_thermal_boundary_patch_role_table/thermal_boundary_patch_role_table.csv"
PATCH_ROLE_SUMMARY = REPO_ROOT / "work_products/2026-07/2026-07-13/2026-07-13_thermal_boundary_patch_role_table/patch_role_area_heat_summary.csv"
SALT1_ADMISSION = REPO_ROOT / "work_products/2026-07/2026-07-13/2026-07-13_salt1_terminal_harvest_admission_review/admission_decision_table.csv"
SALT1_FINAL_WINDOW = REPO_ROOT / "work_products/2026-07/2026-07-13/2026-07-13_stopped_sbatch_steady_state_decisions/final_window_metrics.csv"
CORRECTED_STATUS = REPO_ROOT / "work_products/2026-07/2026-07-13/2026-07-13_corrected_q_latest_time_refresh/all_corrected_q_status_table.csv"
CORRECTED_LIVE_GATE = REPO_ROOT / "work_products/2026-07/2026-07-14/2026-07-14_corrected_q_terminal_admission_gate/corrected_q_terminal_gate_rows.csv"
CORRECTED_LIVE_SUMMARY = REPO_ROOT / "work_products/2026-07/2026-07-14/2026-07-14_corrected_q_terminal_admission_gate/summary.json"
CORRECTED_PREFLIGHT = REPO_ROOT / "jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations/logs/selected_runtime_preflight_3293924.csv"
CORRECTED_MANIFEST = REPO_ROOT / "jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations/corrected_case_manifest.csv"

MAINLINE_CASE_ROOTS = {
    "salt_2": "jadyn_runs/modern_runs/2026-06-18_convergence_and_jin_envelope_wave/runs/salt2_jin/case_stage/viscosity_screening_salt_test_2_jin_coarse_mesh_continuation",
    "salt_3": "jadyn_runs/modern_runs/2026-06-18_convergence_and_jin_envelope_wave/runs/salt3_jin/case_stage/viscosity_screening_salt_test_3_jin_coarse_mesh_continuation",
    "salt_4": "jadyn_runs/modern_runs/2026-06-18_convergence_and_jin_envelope_wave/runs/salt4_jin/case_stage/viscosity_screening_salt_test_4_jin_coarse_mesh_continuation",
}
MAINLINE_SOURCE_IDS = {
    "salt_2": "viscosity_screening_salt_test_2_jin_coarse_mesh",
    "salt_3": "viscosity_screening_salt_test_3_jin_coarse_mesh",
    "salt_4": "viscosity_screening_salt_test_4_jin_coarse_mesh",
}
SALT1_CASE_ROOTS = {
    "salt1_nominal": "jadyn_runs/modern_runs/2026-07-08_salt1_nominal_continuation_candidate/runs/salt1_jin_nominal_continuation_corrected/case_stage/viscosity_screening_salt_test_1_jin_coarse_mesh_continuation",
    "salt1_lo10q": "jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations/runs/salt1_jin_lo10q_corrected/case_stage/viscosity_screening_salt_test_1_jin_coarse_mesh_continuation",
    "salt1_hi10q": "jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations/runs/salt1_jin_hi10q_corrected/case_stage/viscosity_screening_salt_test_1_jin_coarse_mesh_continuation",
}
KIRST_ROOT = "jadyn_runs/salt1/2026-06-05_targeted_campaign/kirst_continuation_candidate/case_stage/viscosity_screening_salt_test_1_kirst_coarse_mesh_continuation"


def _read_csv(path: Path) -> List[Dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, fieldnames: Iterable[str], rows: Iterable[Dict[str, object]]) -> None:
    row_list = list(rows)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fieldnames))
        writer.writeheader()
        writer.writerows(row_list)


def _rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def _log_path(case_root: str, log_name: str = "log.foamRun_continuation") -> str:
    return f"{case_root}/logs/{log_name}"


def _short_corrected_id(case_key: str) -> str:
    return case_key.replace("_jin_", "_").replace("_corrected", "")


def _load_patch_case_summary() -> Dict[str, Dict[str, object]]:
    rows = _read_csv(PATCH_ROLE_TABLE)
    summary: Dict[str, Dict[str, object]] = {}
    for row in rows:
        case_id = row["case_id"]
        item = summary.setdefault(
            case_id,
            {
                "patch_rows": 0,
                "rc_external_temperature_count": 0,
                "external_temperature_count": 0,
                "zero_gradient_count": 0,
                "rc_tsur_values": set(),
                "rc_emissivity_values": set(),
                "case_root": row["case_root"],
                "boundary_dictionary_path": row["boundary_dictionary_path"],
            },
        )
        item["patch_rows"] += 1
        if row["bc_type"] == "rcExternalTemperature":
            item["rc_external_temperature_count"] += 1
            if row["Tsur_K"]:
                item["rc_tsur_values"].add(row["Tsur_K"])
            if row["emissivity"]:
                item["rc_emissivity_values"].add(row["emissivity"])
        elif row["bc_type"] == "externalTemperature":
            item["external_temperature_count"] += 1
        elif row["bc_type"] == "zeroGradient":
            item["zero_gradient_count"] += 1
    for item in summary.values():
        item["rc_tsur_values"] = ";".join(sorted(item["rc_tsur_values"]))
        item["rc_emissivity_values"] = ";".join(sorted(item["rc_emissivity_values"]))
    return summary


def _build_case_inventory() -> List[Dict[str, object]]:
    split_rows = {row["row_id"]: row for row in _read_csv(SPLIT_TABLE)}
    salt1_rows = {row["case_id"]: row for row in _read_csv(SALT1_ADMISSION)}
    corrected_rows = {row["case_key"]: row for row in _read_csv(CORRECTED_STATUS)}
    live_rows = {row["source_key"]: row for row in _read_csv(CORRECTED_LIVE_GATE)}
    patch_summary = _load_patch_case_summary()

    rows: List[Dict[str, object]] = []

    for case_id in ["salt_2", "salt_3", "salt_4"]:
        split = split_rows[case_id]
        patch = patch_summary[case_id]
        assignment = split["current_assignment"]
        rows.append(
            {
                "case_id": case_id,
                "source_key": MAINLINE_SOURCE_IDS[case_id],
                "run_family": "mainline_jin_continuation",
                "case_classification": "mainline_nominal",
                "case_root": MAINLINE_CASE_ROOTS[case_id],
                "primary_log_path": _log_path(MAINLINE_CASE_ROOTS[case_id]),
                "scheduler_or_terminal_state": "terminal_or_stationary_baseline",
                "admission_status": split["current_admission_state"],
                "evidence_use_class": f"{assignment}_candidate",
                "current_split_assignment": assignment,
                "training_eligible_now": "yes" if assignment == "train" else "no",
                "validation_eligible_now": "yes" if assignment == "validation" else "no",
                "holdout_eligible_now": "yes" if assignment == "holdout" else "no",
                "boundary_label_status": "full_patch_role_audit_complete",
                "radiation_semantics": (
                    "rcExternalTemperature includes emissivity/Tsur; radiation is folded into total wallHeatFlux, "
                    "not separately exported as qr"
                ),
                "rcExternalTemperature_patches": patch["rc_external_temperature_count"],
                "reason": split["reason"],
                "next_required_postprocessing": split["next_admission_gate"],
                "primary_evidence": split["primary_evidence"],
            }
        )

    for case_id in ["salt1_nominal", "salt1_lo10q", "salt1_hi10q"]:
        decision = salt1_rows[case_id]
        rows.append(
            {
                "case_id": case_id,
                "source_key": case_id,
                "run_family": "mainline_salt1" if case_id == "salt1_nominal" else "corrected_q_salt1",
                "case_classification": "diagnostic-only" if case_id == "salt1_nominal" else "perturbation_sensitivity",
                "case_root": SALT1_CASE_ROOTS[case_id],
                "primary_log_path": _log_path(SALT1_CASE_ROOTS[case_id], "log.foamRun_corrected_q" if case_id != "salt1_nominal" else "log.foamRun_continuation"),
                "scheduler_or_terminal_state": decision["stationarity_label"],
                "admission_status": decision["admission_decision"],
                "evidence_use_class": "diagnostic_context_only",
                "current_split_assignment": "diagnostic-only",
                "training_eligible_now": "no",
                "validation_eligible_now": "no",
                "holdout_eligible_now": "no",
                "boundary_label_status": "salt1_policy_not_promoted",
                "radiation_semantics": "not promoted to current thermal closure split; use only as context until Salt1 policy admits it",
                "rcExternalTemperature_patches": "",
                "reason": decision["recommended_use"],
                "next_required_postprocessing": "explicit Salt1 admission policy plus predictive input-contract row",
                "primary_evidence": _rel(SALT1_ADMISSION),
            }
        )

    for case_key, status in sorted(corrected_rows.items()):
        if case_key.startswith("salt1_jin_"):
            continue
        case_id = _short_corrected_id(case_key)
        live = live_rows.get(case_key)
        is_live = live is not None
        case_root = status["registry_source_root"].replace(str(REPO_ROOT) + "/", "")
        if is_live:
            scheduler_state = live["scheduler_state"]
            admission_status = live["classification"]
            evidence_use = "blocked_pending_terminal_gate"
            primary_evidence = live["evidence_path"]
            next_gate = "wait for terminal Slurm state, then run terminal harvest and operating-point convergence gate"
        else:
            scheduler_state = "not_live_in_job_3293924"
            admission_status = status["status"]
            if "Not accepted" in status["status"]:
                evidence_use = "failed_or_requires_investigation"
                next_gate = "document launch/BC/log cause, rebuild or rerun from corrected restart, then terminal gate"
            else:
                evidence_use = "blocked_not_admitted"
                next_gate = "terminal/latest-time corrected-Q convergence gate; then add a dated split revision before any fitting"
            primary_evidence = _rel(CORRECTED_STATUS)
        rows.append(
            {
                "case_id": case_id,
                "source_key": case_key,
                "run_family": "corrected_q_perturbation",
                "case_classification": "perturbation_sensitivity" if evidence_use != "failed_or_requires_investigation" else "failed",
                "case_root": case_root,
                "primary_log_path": _log_path(case_root, "log.foamRun_corrected_q"),
                "scheduler_or_terminal_state": scheduler_state,
                "admission_status": admission_status,
                "evidence_use_class": evidence_use,
                "current_split_assignment": "blocked",
                "training_eligible_now": "no",
                "validation_eligible_now": "no",
                "holdout_eligible_now": "no",
                "boundary_label_status": "runtime_preflight_ok_but_terminal_patch_role_reduction_pending" if is_live else "corrected_manifest_available_boundary_reduction_pending",
                "radiation_semantics": (
                    "corrected rows inherit rcExternalTemperature semantics, but remain pending until terminal harvest and row-specific boundary reduction"
                ),
                "rcExternalTemperature_patches": "",
                "reason": "live selected continuation still running" if is_live else status["status"],
                "next_required_postprocessing": next_gate,
                "primary_evidence": primary_evidence,
            }
        )

    rows.append(
        {
            "case_id": "salt1_kirst_continuation_candidate",
            "source_key": "kirst_continuation_candidate",
            "run_family": "historical_kirst",
            "case_classification": "historical/Kirst",
            "case_root": KIRST_ROOT,
            "primary_log_path": _log_path(KIRST_ROOT),
            "scheduler_or_terminal_state": "historical",
            "admission_status": "excluded_by_run_classification_policy",
            "evidence_use_class": "historical_context_only",
            "current_split_assignment": "excluded",
            "training_eligible_now": "no",
            "validation_eligible_now": "no",
            "holdout_eligible_now": "no",
            "boundary_label_status": "not_current_mainline",
            "radiation_semantics": "do not use as current mainline unless a later dated note explicitly re-admits it",
            "rcExternalTemperature_patches": "",
            "reason": "Kirst runs are historical and not current mainline when continuation-derived Jin evidence exists.",
            "next_required_postprocessing": "new dated re-admission task would be required before any use",
            "primary_evidence": "operational_notes/06-26/30/2026-06-30_run_classification_policy.md",
        }
    )
    rows.append(
        {
            "case_id": "original_q_insulation_perturbation_sweep",
            "source_key": "invalid_14_case_q_insulation_campaign",
            "run_family": "invalid_perturbation_campaign",
            "case_classification": "failed",
            "case_root": "old invalid staged roots deleted; see salt-q quarantine/admission notes",
            "primary_log_path": "",
            "scheduler_or_terminal_state": "quarantined",
            "admission_status": "false_steady_quarantined",
            "evidence_use_class": "not_usable",
            "current_split_assignment": "excluded",
            "training_eligible_now": "no",
            "validation_eligible_now": "no",
            "holdout_eligible_now": "no",
            "boundary_label_status": "invalid_bc_restart_evidence",
            "radiation_semantics": "do not use for regression, validation, or closure evidence",
            "rcExternalTemperature_patches": "",
            "reason": "mdot pinned at nominal and insulation knob did not reliably change live BC; old roots were deleted after quarantine.",
            "next_required_postprocessing": "none; use corrected Salt-Q campaign instead after terminal admission",
            "primary_evidence": "operational_notes/07-26/04/2026-07-04_salt_perturbation_quarantine_and_relaunch.md",
        }
    )
    return rows


def _build_boundary_table() -> List[Dict[str, object]]:
    role_rows = _read_csv(PATCH_ROLE_SUMMARY)
    patch_summary = _load_patch_case_summary()
    output: List[Dict[str, object]] = []
    for row in role_rows:
        case_id = row["case_id"]
        patch = patch_summary[case_id]
        output.append(
            {
                "case_id": case_id,
                "source_id": row["source_id"],
                "case_classification": "mainline_nominal",
                "role": row["role"],
                "role_group": row["role_group"],
                "patch_count": row["patch_count"],
                "area_m2": row["area_m2"],
                "imposed_Q_W": row["imposed_Q_W"],
                "realized_wallHeatFlux_W": row["realized_wallHeatFlux_W"],
                "rcExternalTemperature_count": row["rcExternalTemperature_count"],
                "externalTemperature_count": row["externalTemperature_count"],
                "zeroGradient_count": row["zeroGradient_count"],
                "Tsur_K_values": patch["rc_tsur_values"],
                "emissivity_values": patch["rc_emissivity_values"],
                "radiation_semantics": (
                    "if rcExternalTemperature_count>0, emissivity/Tsur radiation is active and folded into total wallHeatFlux; "
                    "no separate qr term is exported"
                ),
                "boundary_dictionary_path": patch["boundary_dictionary_path"],
                "wallHeatFlux_source_status": "available_in_patch_role_table",
                "admission_use": "boundary_label_evidence_for_admitted_mainline_rows",
            }
        )

    preflight_rows = _read_csv(CORRECTED_PREFLIGHT)
    manifest_rows = {row["case_key"]: row for row in _read_csv(CORRECTED_MANIFEST)}
    for row in preflight_rows:
        case_id = _short_corrected_id(row["case_key"])
        manifest = manifest_rows[row["case_key"]]
        for role, q_value, role_group in [
            ("heater", manifest["target_heater_power_W"], "intended_heater_input"),
            ("heater_patch_each_lower_straight", row["target_heater_patch_Q_W"], "intended_heater_input"),
            ("cooler_upper_reducer_04", manifest["target_cooler_q04_W"], "intended_cooler_removal"),
            ("cooler_upper_05", manifest["target_cooler_q05_W"], "intended_cooler_removal"),
            ("cooler_upper_reducer_06", manifest["target_cooler_q06_W"], "intended_cooler_removal"),
        ]:
            output.append(
                {
                    "case_id": case_id,
                    "source_id": row["case_key"],
                    "case_classification": "perturbation_sensitivity_pending_terminal",
                    "role": role,
                    "role_group": role_group,
                    "patch_count": "",
                    "area_m2": "",
                    "imposed_Q_W": q_value,
                    "realized_wallHeatFlux_W": "",
                    "rcExternalTemperature_count": "",
                    "externalTemperature_count": "",
                    "zeroGradient_count": "",
                    "Tsur_K_values": "",
                    "emissivity_values": "",
                    "radiation_semantics": "runtime preflight confirms corrected heater/cooler values; full terminal wallHeatFlux/radiation role reduction still pending",
                    "boundary_dictionary_path": f"{row['case_dir']}/0/T",
                    "wallHeatFlux_source_status": "pending_terminal_harvest",
                    "admission_use": "not_admitted_until_terminal_gate",
                }
            )
    return output


def _build_candidate_table(case_rows: List[Dict[str, object]]) -> List[Dict[str, object]]:
    out: List[Dict[str, object]] = []
    for row in case_rows:
        can_add_training = "no"
        if row["case_id"] == "salt_2" and row["current_split_assignment"] == "train":
            can_add_training = "already_the_only_training_row_for_current_split"
        elif row["case_id"] in {"salt_3", "salt_4"}:
            can_add_training = "no_split_locked_validation_or_holdout"
        elif row["run_family"] == "corrected_q_perturbation":
            can_add_training = "no_pending_terminal_admission_and_split_revision"
        out.append(
            {
                "case_id": row["case_id"],
                "run_family": row["run_family"],
                "current_split_assignment": row["current_split_assignment"],
                "candidate_label": row["evidence_use_class"],
                "can_add_training_without_split_violation": can_add_training,
                "can_score_validation_now": row["validation_eligible_now"],
                "can_score_holdout_now": row["holdout_eligible_now"],
                "admission_status": row["admission_status"],
                "allowed_downstream_use_now": _allowed_use(row),
                "blocked_or_guardrail": row["next_required_postprocessing"],
                "evidence_path": row["primary_evidence"],
            }
        )
    return out


def _allowed_use(row: Dict[str, object]) -> str:
    if row["training_eligible_now"] == "yes":
        return "training for predeclared one-scalar/pilot or existing admitted training response only"
    if row["validation_eligible_now"] == "yes":
        return "validation scoring only; no fitting"
    if row["holdout_eligible_now"] == "yes":
        return "held-out final score only after model is frozen"
    if row["evidence_use_class"] == "diagnostic_context_only":
        return "diagnostic/context only"
    return "not admitted for downstream fitting or scoring"


def _build_source_manifest() -> List[Dict[str, object]]:
    sources = [
        ("predictive_validation_split", SPLIT_TABLE, "split/admission policy for Salt2 train, Salt3 validation, Salt4 holdout"),
        ("thermal_boundary_patch_role_table", PATCH_ROLE_TABLE, "mainline patch-level BC roles, h/Ta/Tsur/emissivity, wallHeatFlux provenance"),
        ("thermal_boundary_role_summary", PATCH_ROLE_SUMMARY, "role-level boundary summary for mainline cases"),
        ("salt1_terminal_harvest_admission", SALT1_ADMISSION, "Salt1 terminal context-only admission decision"),
        ("salt1_final_window_metrics", SALT1_FINAL_WINDOW, "Salt1/Salt4 final-window stationarity metrics"),
        ("corrected_q_latest_time_status", CORRECTED_STATUS, "all corrected-Q latest-time admission status before live continuation"),
        ("corrected_q_live_terminal_gate", CORRECTED_LIVE_GATE, "live job 3293924 case-level pending terminal rows"),
        ("corrected_q_live_summary", CORRECTED_LIVE_SUMMARY, "live job 3293924 top-level scheduler/admission summary"),
        ("corrected_q_runtime_preflight", CORRECTED_PREFLIGHT, "selected job 3293924 runtime preflight and corrected heater values"),
        ("corrected_q_manifest", CORRECTED_MANIFEST, "corrected-Q target heater/cooler values and case paths"),
        ("cfd_runs_admission_map", REPO_ROOT / "operational_notes/maps/cfd-runs-and-admission.md", "current CFD run admission policy"),
        ("thermal_boundary_radiation_map", REPO_ROOT / "operational_notes/maps/thermal-boundary-and-radiation.md", "radiation semantics for rcExternalTemperature"),
        ("run_classification_policy", REPO_ROOT / "operational_notes/06-26/30/2026-06-30_run_classification_policy.md", "Kirst/mainline/perturbation classification policy"),
        ("corrected_q_live_journal", REPO_ROOT / ".agent/journal/2026-07-14/corrected-salt-q-live-job-admission.md", "live corrected-Q monitoring caveats"),
    ]
    rows: List[Dict[str, object]] = []
    for source_id, path, role in sources:
        rows.append(
            {
                "source_id": source_id,
                "path": _rel(path),
                "read_or_generated": "read_only_input",
                "role": role,
                "exists": path.exists(),
            }
        )
    for case_id, case_root in {**MAINLINE_CASE_ROOTS, **SALT1_CASE_ROOTS, "salt1_kirst_continuation_candidate": KIRST_ROOT}.items():
        rows.append(
            {
                "source_id": f"{case_id}_case_root",
                "path": case_root,
                "read_or_generated": "native_solver_output_read_only",
                "role": "case root / solver output tree; not mutated",
                "exists": (REPO_ROOT / case_root).exists(),
            }
        )
    return rows


def build_cfd_case_admission_inventory(output_dir: Path = OUT_DIR) -> Dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    cases = _build_case_inventory()
    boundary = _build_boundary_table()
    candidates = _build_candidate_table(cases)
    sources = _build_source_manifest()

    _write_csv(
        output_dir / "cfd_case_admission_inventory.csv",
        [
            "case_id",
            "source_key",
            "run_family",
            "case_classification",
            "case_root",
            "primary_log_path",
            "scheduler_or_terminal_state",
            "admission_status",
            "evidence_use_class",
            "current_split_assignment",
            "training_eligible_now",
            "validation_eligible_now",
            "holdout_eligible_now",
            "boundary_label_status",
            "radiation_semantics",
            "rcExternalTemperature_patches",
            "reason",
            "next_required_postprocessing",
            "primary_evidence",
        ],
        cases,
    )
    _write_csv(
        output_dir / "boundary_condition_role_table.csv",
        [
            "case_id",
            "source_id",
            "case_classification",
            "role",
            "role_group",
            "patch_count",
            "area_m2",
            "imposed_Q_W",
            "realized_wallHeatFlux_W",
            "rcExternalTemperature_count",
            "externalTemperature_count",
            "zeroGradient_count",
            "Tsur_K_values",
            "emissivity_values",
            "radiation_semantics",
            "boundary_dictionary_path",
            "wallHeatFlux_source_status",
            "admission_use",
        ],
        boundary,
    )
    _write_csv(
        output_dir / "training_validation_holdout_candidate_table.csv",
        [
            "case_id",
            "run_family",
            "current_split_assignment",
            "candidate_label",
            "can_add_training_without_split_violation",
            "can_score_validation_now",
            "can_score_holdout_now",
            "admission_status",
            "allowed_downstream_use_now",
            "blocked_or_guardrail",
            "evidence_path",
        ],
        candidates,
    )
    _write_csv(output_dir / "source_manifest.csv", ["source_id", "path", "read_or_generated", "role", "exists"], sources)

    class_counts = Counter(row["case_classification"] for row in cases)
    evidence_counts = Counter(row["evidence_use_class"] for row in cases)
    summary = {
        "task": "AGENT-331",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "case_rows": len(cases),
        "boundary_rows": len(boundary),
        "candidate_rows": len(candidates),
        "class_counts": dict(sorted(class_counts.items())),
        "evidence_use_counts": dict(sorted(evidence_counts.items())),
        "training_rows_now": [row["case_id"] for row in cases if row["training_eligible_now"] == "yes"],
        "validation_rows_now": [row["case_id"] for row in cases if row["validation_eligible_now"] == "yes"],
        "holdout_rows_now": [row["case_id"] for row in cases if row["holdout_eligible_now"] == "yes"],
        "corrected_q_rows_admitted": 0,
        "native_solver_outputs_mutated": False,
        "outputs": [
            "cfd_case_admission_inventory.csv",
            "boundary_condition_role_table.csv",
            "training_validation_holdout_candidate_table.csv",
            "source_manifest.csv",
            "summary.json",
            "README.md",
        ],
    }
    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output_dir / "README.md").write_text(_readme(summary), encoding="utf-8")
    return summary


def _readme(summary: Dict[str, object]) -> str:
    return f"""---
provenance:
  - {SPLIT_TABLE.relative_to(REPO_ROOT)}
  - {PATCH_ROLE_TABLE.relative_to(REPO_ROOT)}
  - {CORRECTED_LIVE_GATE.relative_to(REPO_ROOT)}
tags: [cfd-pp, admission, boundary-conditions, validation-split, corrected-q]
related:
  - operational_notes/maps/cfd-runs-and-admission.md
  - operational_notes/maps/thermal-boundary-and-radiation.md
  - reports/thesis_dossier/master_thesis_bullet_outline.md
task: AGENT-331
date: 2026-07-14
role: Implementer/Tester/Writer
type: work_product
status: complete
---
# CFD Case Admission Inventory

This package turns current CFD run/admission evidence into case-level and
boundary-role tables for downstream training, validation, and holdout use.

## Result

- Admitted now under the current split: `salt_2` as training, `salt_3` as
  validation, and `salt_4` as holdout.
- Diagnostic/context only: Salt1 nominal and Salt1 corrected-Q terminal harvest
  rows; these still need an explicit Salt1 admission policy before closure use.
- Blocked/pending: all corrected Salt-Q rows. Job `3293924` selected four rows
  for continuation, but the terminal gate package still reports zero admitted
  corrected-Q rows.
- Excluded: Kirst rows are historical, and the original Q/insulation sweep is
  false-steady/quarantined.

## Boundary Semantics

Mainline Salt2/3/4 boundary labels come from the July 13 patch-role audit.
`rcExternalTemperature` rows include emissivity/Tsur radiation, and radiation is
folded into total OpenFOAM `wallHeatFlux`; there is no separate exported `qr`
term. Corrected-Q selected live rows have clean runtime preflight evidence for
heater/cooler values, but still need terminal patch/heat-flux reduction before
admission.

## Outputs

- `cfd_case_admission_inventory.csv`
- `boundary_condition_role_table.csv`
- `training_validation_holdout_candidate_table.csv`
- `source_manifest.csv`
- `summary.json`

## Counts

- Case rows: {summary["case_rows"]}
- Boundary rows: {summary["boundary_rows"]}
- Training rows now: {", ".join(summary["training_rows_now"])}
- Validation rows now: {", ".join(summary["validation_rows_now"])}
- Holdout rows now: {", ".join(summary["holdout_rows_now"])}

No native CFD solver outputs were modified.
"""


def main() -> None:
    build_cfd_case_admission_inventory()


if __name__ == "__main__":
    main()
