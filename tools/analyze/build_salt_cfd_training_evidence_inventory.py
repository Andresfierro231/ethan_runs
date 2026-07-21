#!/usr/bin/env python3
"""Build the salt-only CFD training evidence inventory.

This reducer is deliberately read-only with respect to solver case trees.  It
combines registry rows, corrected Salt-Q campaign records, live-job evidence,
steady/admission gates, mesh-family gates, and boundary-role summaries into the
AGENT-334 work-product package.
"""

from __future__ import annotations

import csv
import json
import re
import subprocess
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional


REPO_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = REPO_ROOT / "work_products/2026-07/2026-07-14/2026-07-14_salt_cfd_training_evidence_inventory"

CASE_REGISTRY = REPO_ROOT / "registry/case_registry.csv"
POSTPROCESSING_RUNS = REPO_ROOT / "registry/_all_postprocessing_runs.csv"
FAMILY_INDEXES = [
    REPO_ROOT / "registry/salt1/_family_index.csv",
    REPO_ROOT / "registry/salt2/_family_index.csv",
    REPO_ROOT / "registry/salt3/_family_index.csv",
    REPO_ROOT / "registry/salt4/_family_index.csv",
]
SPLIT_TABLE = REPO_ROOT / "work_products/2026-07/2026-07-13/2026-07-13_predictive_validation_split/admission_split_table.csv"
PATCH_ROLE_TABLE = REPO_ROOT / "work_products/2026-07/2026-07-13/2026-07-13_thermal_boundary_patch_role_table/thermal_boundary_patch_role_table.csv"
PATCH_ROLE_SUMMARY = REPO_ROOT / "work_products/2026-07/2026-07-13/2026-07-13_thermal_boundary_patch_role_table/patch_role_area_heat_summary.csv"
SALT1_ADMISSION = REPO_ROOT / "work_products/2026-07/2026-07-13/2026-07-13_salt1_terminal_harvest_admission_review/admission_decision_table.csv"
SALT1_FINAL_WINDOW = REPO_ROOT / "work_products/2026-07/2026-07-13/2026-07-13_stopped_sbatch_steady_state_decisions/final_window_metrics.csv"
CORRECTED_MANIFEST = REPO_ROOT / "jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations/corrected_case_manifest.csv"
CORRECTED_STATUS = REPO_ROOT / "work_products/2026-07/2026-07-13/2026-07-13_corrected_q_latest_time_refresh/all_corrected_q_status_table.csv"
CORRECTED_LIVE_GATE = REPO_ROOT / "work_products/2026-07/2026-07-14/2026-07-14_corrected_q_terminal_admission_gate/corrected_q_terminal_gate_rows.csv"
CORRECTED_PREFLIGHT = REPO_ROOT / "jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations/logs/selected_runtime_preflight_3293924.csv"
SELECTED_JOBS = REPO_ROOT / "jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations/selected_submitted_jobs.csv"
SUBMITTED_JOBS = REPO_ROOT / "jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations/submitted_jobs.csv"
CORRECTED_README = REPO_ROOT / "jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations/README.md"
CORRECTED_TODO = REPO_ROOT / "jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations/TODO.md"
SLURM_3293924_OUT = REPO_ROOT / "jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations/slurm-saltq_sel_cont-3293924.out"
SLURM_3293924_ERR = REPO_ROOT / "jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations/slurm-saltq_sel_cont-3293924.err"
THERMAL_MESH_STATUS = REPO_ROOT / "work_products/2026-07/2026-07-14/2026-07-14_thermal_closure_mesh_gate_refresh/refreshed_qoi_mesh_gate_status.csv"
THERMAL_ADMISSION = REPO_ROOT / "work_products/2026-07/2026-07-14/2026-07-14_thermal_closure_mesh_gate_refresh/thermal_admission_table.csv"
PRESSURE_MESH_FIT = REPO_ROOT / "work_products/2026-07/2026-07-13/2026-07-13_salt2_pressure_only_mesh_family_comparison/fit_safety_summary.csv"
UPCOMER_ONSET_CONDITIONS = REPO_ROOT / "work_products/2026-07/2026-07-14/2026-07-14_upcomer_recirculation_internal_nu_admissibility/upcomer_recirculation_onset_conditions.csv"
UPCOMER_BLOCKED_METRICS = REPO_ROOT / "work_products/2026-07/2026-07-14/2026-07-14_upcomer_recirculation_internal_nu_admissibility/blocked_missing_metrics.csv"
UPCOMER_ONSET_REQUIREMENTS = REPO_ROOT / "work_products/2026-07/2026-07-14/2026-07-14_upcomer_onset_blocker_resolution/next_evidence_requirements.csv"
MESH_MAP = REPO_ROOT / "operational_notes/maps/mesh-gci-and-uncertainty.md"
CFD_ADMISSION_MAP = REPO_ROOT / "operational_notes/maps/cfd-runs-and-admission.md"
THERMAL_BOUNDARY_MAP = REPO_ROOT / "operational_notes/maps/thermal-boundary-and-radiation.md"

MAINLINE_ROOTS = {
    "salt1": "jadyn_runs/modern_runs/2026-07-08_salt1_nominal_continuation_candidate/runs/salt1_jin_nominal_continuation_corrected/case_stage/viscosity_screening_salt_test_1_jin_coarse_mesh_continuation",
    "salt2": "jadyn_runs/modern_runs/2026-06-18_convergence_and_jin_envelope_wave/runs/salt2_jin/case_stage/viscosity_screening_salt_test_2_jin_coarse_mesh_continuation",
    "salt3": "jadyn_runs/modern_runs/2026-06-18_convergence_and_jin_envelope_wave/runs/salt3_jin/case_stage/viscosity_screening_salt_test_3_jin_coarse_mesh_continuation",
    "salt4": "jadyn_runs/modern_runs/2026-06-18_convergence_and_jin_envelope_wave/runs/salt4_jin/case_stage/viscosity_screening_salt_test_4_jin_coarse_mesh_continuation",
}
MAINLINE_SOURCE_IDS = {
    "salt1": "viscosity_screening_salt_test_1_jin_coarse_mesh",
    "salt2": "viscosity_screening_salt_test_2_jin_coarse_mesh",
    "salt3": "viscosity_screening_salt_test_3_jin_coarse_mesh",
    "salt4": "viscosity_screening_salt_test_4_jin_coarse_mesh",
}
SHORT_SPLIT_IDS = {"salt2": "salt_2", "salt3": "salt_3", "salt4": "salt_4"}
SPLIT_ASSIGNMENTS = {"salt2": "training", "salt3": "validation", "salt4": "holdout"}
UPCOMER_RE_TARGETS = ["150", "200", "250"]
RADIATION_SEMANTICS = (
    "rcExternalTemperature includes emissivity/Tsur; OpenFOAM wallHeatFlux is the total "
    "wall heat balance with radiation folded in and no separate exported qr term."
)


def _read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, fieldnames: Iterable[str], rows: Iterable[Dict[str, object]]) -> None:
    row_list = list(rows)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fieldnames))
        writer.writeheader()
        writer.writerows(row_list)


def _rel(path_or_text: object) -> str:
    text = str(path_or_text)
    try:
        path = Path(text)
    except TypeError:
        return text
    if path.is_absolute():
        try:
            return str(path.relative_to(REPO_ROOT))
        except ValueError:
            return str(path)
    return text


def _exists_text(path_or_text: str) -> str:
    if not path_or_text:
        return "False"
    path = REPO_ROOT / path_or_text if not Path(path_or_text).is_absolute() else Path(path_or_text)
    return str(path.exists())


def _case_stage_root(case_root: str) -> str:
    return case_root


def _log_path(case_root: str, log_name: str) -> str:
    return f"{case_root}/logs/{log_name}"


def _latest_time_from_log(path_text: str) -> str:
    path = REPO_ROOT / path_text if not Path(path_text).is_absolute() else Path(path_text)
    if not path.exists():
        return ""
    latest = ""
    pattern = re.compile(r"^Time = ([0-9]+(?:\.[0-9]+)?)s?\s*$")
    tail_bytes = 2_000_000
    with path.open("rb") as handle:
        handle.seek(0, 2)
        size = handle.tell()
        handle.seek(max(0, size - tail_bytes))
        text = handle.read().decode("utf-8", errors="ignore")
    for line in text.splitlines():
        match = pattern.match(line.strip())
        if match:
            latest = match.group(1)
    return latest


def _short_corrected_key(case_key: str) -> str:
    return case_key.replace("_jin_", "_").replace("_corrected", "")


def _variant_from_q_ratio(q_ratio: str) -> str:
    mapping = {"0.90": "lo10q", "0.95": "lo5q", "1.05": "hi5q", "1.10": "hi10q"}
    return mapping.get(q_ratio, "corrected_q")


def _salt_number(bucket_or_num: str) -> str:
    text = str(bucket_or_num)
    if text.startswith("salt"):
        return text
    return f"salt{text}"


def _query_job_3293924() -> Dict[str, str]:
    fallback = {
        "job_id": "3293924",
        "job_state": "RUNNING",
        "job_evidence": _rel(SLURM_3293924_OUT),
        "scheduler_checked_at": "",
        "scheduler_detail": "state inferred from prior live gate if sacct is unavailable",
    }

    def query_squeue() -> Dict[str, str]:
        try:
            squeue = subprocess.run(
                ["squeue", "-j", "3293924", "-h", "-o", "%T|%M|%N"],
                check=False,
                capture_output=True,
                encoding="utf-8",
                timeout=5,
            )
        except (OSError, subprocess.SubprocessError):
            return fallback
        squeue_lines = [line for line in squeue.stdout.splitlines() if line.strip()]
        if not squeue_lines:
            return fallback
        state, elapsed, node = (squeue_lines[0].split("|") + ["", ""])[:3]
        return {
            "job_id": "3293924",
            "job_state": "RUNNING" if state == "RUNNING" else state,
            "job_evidence": _rel(SLURM_3293924_OUT),
            "scheduler_checked_at": datetime.now().astimezone().isoformat(timespec="seconds"),
            "scheduler_detail": f"squeue state={state}; elapsed={elapsed}; node={node}",
        }

    try:
        result = subprocess.run(
            ["sacct", "-j", "3293924", "--format", "JobID,JobName%30,State,ExitCode,Elapsed,Start,End", "-P"],
            check=False,
            capture_output=True,
            encoding="utf-8",
            timeout=3,
        )
    except (OSError, subprocess.SubprocessError):
        return query_squeue()
    lines = [line for line in result.stdout.splitlines() if line.strip()]
    if len(lines) < 2:
        return query_squeue()
    top = lines[1].split("|")
    state = top[2] if len(top) > 2 else fallback["job_state"]
    elapsed = top[4] if len(top) > 4 else ""
    start = top[5] if len(top) > 5 else ""
    end = top[6] if len(top) > 6 else ""
    return {
        "job_id": "3293924",
        "job_state": state,
        "job_evidence": _rel(SLURM_3293924_OUT),
        "scheduler_checked_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "scheduler_detail": f"sacct top-level state={state}; elapsed={elapsed}; start={start}; end={end}",
    }


def _load_split_rows() -> Dict[str, Dict[str, str]]:
    return {row["row_id"]: row for row in _read_csv(SPLIT_TABLE)}


def _load_family_rows() -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for path in FAMILY_INDEXES:
        rows.extend(_read_csv(path))
    return rows


def _load_upcomer_metrics() -> Dict[str, Dict[str, str]]:
    metrics: Dict[str, Dict[str, str]] = {}
    for row in _read_csv(UPCOMER_ONSET_CONDITIONS):
        salt = row.get("case_id", "").replace("_", "")
        if not salt:
            continue
        metrics[f"{salt}_jin_nominal_continuation"] = row
    return metrics


def _next_action_to_unlock_onset(row: Dict[str, object]) -> str:
    case_key = str(row["case_key"])
    salt = str(row["salt_number"])
    variant = str(row["variant"])
    if case_key in {
        "salt2_jin_nominal_continuation",
        "salt3_jin_nominal_continuation",
        "salt4_jin_nominal_continuation",
    }:
        return "already mined for coarse diagnostic recirculation metrics; still needs wall-bulk Delta T, Gz, secondary velocity fraction, and uncertainty before internal-Nu/onset admission"
    if case_key == "salt1_jin_nominal_continuation" or salt == "salt1":
        return "define Salt1 admission policy and extract matched recirculation metrics before using as an onset anchor"
    if str(row["part_of_live_job_3293924"]) == "yes":
        return "wait for job 3293924 terminal state; then harvest stdout/stderr/solver logs, run postprocessing, and run steady/admission plus recirculation extraction"
    if salt == "salt4" and variant in {"hi5q", "hi10q"}:
        return "continue or rerun to terminal corrected-Q state, then postprocess for Re_upcomer/backflow/Ri before treating as a near-onset candidate"
    if str(row["classification"]) == "perturbation/sensitivity":
        return "continue only if sensitivity coverage is needed; then run terminal harvest, postprocessing, and steady/admission gate"
    return str(row["action_needed"])


def _candidate_onset_role(row: Dict[str, object]) -> str:
    case_key = str(row["case_key"])
    salt = str(row["salt_number"])
    variant = str(row["variant"])
    if case_key in {
        "salt2_jin_nominal_continuation",
        "salt3_jin_nominal_continuation",
        "salt4_jin_nominal_continuation",
    }:
        return "recirculating_reference"
    if salt == "salt4" and variant in {"hi5q", "hi10q"} and str(row["run_state"]) != "failed":
        return "transition_candidate"
    if str(row["classification"]) == "perturbation/sensitivity":
        return "sensitivity_only"
    return "not_useful"


def _apply_upcomer_onset_fields(inventory_rows: List[Dict[str, object]]) -> None:
    metrics = _load_upcomer_metrics()
    for row in inventory_rows:
        metric = metrics.get(str(row["case_key"]), {})
        row["Re_upcomer"] = metric.get("Re_upcomer", "")
        row["recirculation_evidence_available"] = "yes" if metric else "no"
        row["candidate_onset_role"] = _candidate_onset_role(row)
        row["next_action_to_unlock"] = _next_action_to_unlock_onset(row)


def _load_patch_role_stats() -> Dict[str, Dict[str, Dict[str, object]]]:
    stats: Dict[str, Dict[str, Dict[str, object]]] = defaultdict(lambda: defaultdict(lambda: {
        "patch_count": 0,
        "bc_types": Counter(),
        "emissivity_values": set(),
        "tsur_values": set(),
    }))
    for row in _read_csv(PATCH_ROLE_TABLE):
        case_id = row["case_id"]
        role = row["role"]
        item = stats[case_id][role]
        item["patch_count"] += 1
        item["bc_types"][row["bc_type"]] += 1
        if row.get("emissivity"):
            item["emissivity_values"].add(row["emissivity"])
        if row.get("Tsur_K"):
            item["tsur_values"].add(row["Tsur_K"])
    return stats


def _mainline_inventory_rows(split_rows: Dict[str, Dict[str, str]], family_rows: List[Dict[str, str]]) -> List[Dict[str, object]]:
    by_source = {row["source_id"]: row for row in family_rows}
    salt1_decisions = {row["case_id"]: row for row in _read_csv(SALT1_ADMISSION)}
    rows: List[Dict[str, object]] = []
    for salt in ["salt1", "salt2", "salt3", "salt4"]:
        source_id = MAINLINE_SOURCE_IDS[salt]
        root = MAINLINE_ROOTS[salt]
        log_path = _log_path(root, "log.foamRun_continuation")
        family = by_source.get(source_id, {})
        split_id = SHORT_SPLIT_IDS.get(salt)
        split = split_rows.get(split_id, {})
        if salt == "salt1":
            decision = salt1_decisions.get("salt1_nominal", {})
            verdict = "diagnostic-only"
            reason = "Salt1 terminal window is context-only pending an explicit Salt1 admission policy."
            run_state = "stopped"
            assignment = "diagnostic-only"
            steady_path = _rel(SALT1_ADMISSION)
        else:
            verdict = "fit-admissible" if salt == "salt2" else f"{SPLIT_ASSIGNMENTS[salt]}-only"
            reason = split.get("reason", "Mainline Jin continuation in active split.")
            run_state = "completed"
            assignment = SPLIT_ASSIGNMENTS[salt]
            steady_path = split.get("primary_evidence", _rel(SPLIT_TABLE))
        rows.append({
            "case_key": f"{salt}_jin_nominal_continuation",
            "source_id": source_id,
            "salt_number": salt,
            "variant": "nominal",
            "classification": "mainline nominal",
            "source_path": family.get("run_root", ""),
            "run_root": root,
            "case_stage_path": _case_stage_root(root),
            "latest_time_s": _latest_time_from_log(log_path),
            "run_state": run_state,
            "scheduler_job_id": "",
            "terminal_status_evidence_path": steady_path,
            "solver_log_path": log_path,
            "postprocessing_availability": "registry aggregates available" if family.get("normalized_csv") else "mainline case evidence available",
            "steady_state_admission_evidence_path": steady_path,
            "admission_verdict": verdict,
            "reason_for_verdict": reason,
            "part_of_live_job_3293924": "no",
            "action_needed": "none for current split" if salt != "salt1" else "define Salt1 admission/split policy before any training use",
            "split_recommendation": assignment,
            "bc_label_status": "full Salt2/3/4 role audit complete" if salt != "salt1" else "not promoted; BC role reduction still needed before fit use",
        })
    return rows


def _historical_registry_rows(family_rows: List[Dict[str, str]]) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    for row in family_rows:
        variant = row.get("variant_label", "")
        source_id = row.get("source_id", "")
        if variant not in {"kirst", ""}:
            continue
        if "jin" in source_id:
            continue
        salt = row.get("bucket", "")
        case_key = f"{salt}_{variant or 'native'}_historical_reference"
        classification = "historical/Kirst" if variant == "kirst" else "historical/native-reference"
        rows.append({
            "case_key": case_key,
            "source_id": source_id,
            "salt_number": salt,
            "variant": variant or "native_reference",
            "classification": classification,
            "source_path": row.get("run_root", ""),
            "run_root": row.get("run_root", ""),
            "case_stage_path": "",
            "latest_time_s": "",
            "run_state": "completed" if row.get("run_status") == "completed" else "stopped",
            "scheduler_job_id": "",
            "terminal_status_evidence_path": _rel(CFD_ADMISSION_MAP),
            "solver_log_path": "",
            "postprocessing_availability": "registry aggregates available" if row.get("normalized_csv") else "unknown",
            "steady_state_admission_evidence_path": _rel(CFD_ADMISSION_MAP),
            "admission_verdict": "diagnostic-only",
            "reason_for_verdict": "Historical/reference Salt row; not current mainline and not re-admitted for training.",
            "part_of_live_job_3293924": "no",
            "action_needed": "dated re-admission task required before any downstream use",
            "split_recommendation": "excluded",
            "bc_label_status": "not current mainline",
        })
    return rows


def _job_ids_by_case() -> Dict[str, List[str]]:
    mapping: Dict[str, List[str]] = defaultdict(list)
    for table in [_read_csv(SUBMITTED_JOBS), _read_csv(SELECTED_JOBS)]:
        for row in table:
            cases = row.get("cases") or row.get("case_keys", "")
            normalized = cases.replace(",", ";").split(";")
            for case in [item.strip() for item in normalized if item.strip().startswith("salt")]:
                mapping[case].append(row.get("job_id", ""))
    return mapping


def _corrected_rows(job_info: Dict[str, str]) -> List[Dict[str, object]]:
    status_rows = {row["case_key"]: row for row in _read_csv(CORRECTED_STATUS)}
    live_rows = {row["source_key"]: row for row in _read_csv(CORRECTED_LIVE_GATE)}
    preflight_rows = {row["case_key"]: row for row in _read_csv(CORRECTED_PREFLIGHT)}
    job_ids = _job_ids_by_case()
    rows: List[Dict[str, object]] = []
    for manifest in _read_csv(CORRECTED_MANIFEST):
        case_key = manifest["case_key"]
        short_key = _short_corrected_key(case_key)
        salt = _salt_number(manifest["salt"])
        variant = _variant_from_q_ratio(manifest["q_ratio"])
        case_root = _rel(manifest["case_dir"])
        log_path = _log_path(case_root, "log.foamRun_corrected_q")
        status = status_rows.get(case_key, {})
        live = live_rows.get(case_key)
        preflight = preflight_rows.get(case_key, {})
        latest_time = _latest_time_from_log(log_path) or status.get("latest_log_time", "").replace(" s", "")
        if live:
            run_state = "running" if job_info["job_state"] == "RUNNING" else job_info["job_state"].lower()
            verdict = "pending-terminal-harvest"
            reason = f"Selected live continuation job 3293924 is {job_info['job_state']}; terminal steady/admission gate has not run."
            action = "harvest terminal logs and postprocess after Slurm exits, then run operating-point steady/admission gate"
            terminal_evidence = f"{_rel(SLURM_3293924_OUT)}; {_rel(SLURM_3293924_ERR)}; {_rel(CORRECTED_PREFLIGHT)}"
        elif "Not accepted" in status.get("status", ""):
            run_state = "failed"
            verdict = "not-admissible"
            reason = status.get("status", "not accepted by prior corrected-Q gate")
            action = "investigate failed high-Q attempt, document cause, then rebuild/rerun from corrected restart if still needed"
            terminal_evidence = _rel(CORRECTED_STATUS)
        elif salt == "salt1":
            run_state = "stopped"
            verdict = "diagnostic-only"
            reason = "Salt1 corrected-Q rows have context-only terminal evidence pending Salt1 policy."
            action = "define Salt1 policy and verify diagnostic-only convergenceMonitor before any continuation"
            terminal_evidence = _rel(SALT1_ADMISSION)
        else:
            run_state = "stopped"
            verdict = "sensitivity-only"
            reason = status.get("status", "partial or under-advanced corrected-Q row; not admitted")
            action = "continue or re-gate after sufficient perturbed operating-point window; do not fit until split policy is revised"
            terminal_evidence = _rel(CORRECTED_STATUS)
        rows.append({
            "case_key": short_key,
            "source_id": case_key,
            "salt_number": salt,
            "variant": variant,
            "classification": "perturbation/sensitivity" if run_state != "failed" else "failed",
            "source_path": _rel(manifest["parent_case_dir"]),
            "run_root": case_root,
            "case_stage_path": case_root,
            "latest_time_s": latest_time,
            "run_state": run_state,
            "scheduler_job_id": "3293924" if live else ";".join(job_ids.get(case_key, [])),
            "terminal_status_evidence_path": terminal_evidence,
            "solver_log_path": log_path,
            "postprocessing_availability": "pending terminal postprocessing" if live else "prior latest-time/steady review only",
            "steady_state_admission_evidence_path": _rel(CORRECTED_LIVE_GATE) if live else terminal_evidence,
            "admission_verdict": verdict,
            "reason_for_verdict": reason,
            "part_of_live_job_3293924": "yes" if live else "no",
            "action_needed": action,
            "split_recommendation": "perturbation/sensitivity candidates only after terminal admission" if verdict != "not-admissible" else "excluded until rerun",
            "bc_label_status": "runtime preflight OK; row-level BC reduction pending" if preflight else "manifest/root audit available; row-level BC reduction pending",
        })
    return rows


def _mesh_family_row() -> Dict[str, object]:
    return {
        "case_key": "salt2_mesh_refinement_family_coarse_medium_fine",
        "source_id": "viscosity_screening_salt_test_2_jin_coarse_mesh",
        "salt_number": "salt2",
        "variant": "mesh-level",
        "classification": "mesh refinement family",
        "source_path": _rel(THERMAL_MESH_STATUS),
        "run_root": "Salt2 coarse/medium/fine mesh-family evidence packages",
        "case_stage_path": "",
        "latest_time_s": "",
        "run_state": "completed",
        "scheduler_job_id": "",
        "terminal_status_evidence_path": _rel(MESH_MAP),
        "solver_log_path": "",
        "postprocessing_availability": "pressure and thermal repair-smoke summaries available; closure-QOI GCI not publication-ready",
        "steady_state_admission_evidence_path": f"{_rel(THERMAL_MESH_STATUS)}; {_rel(THERMAL_ADMISSION)}; {_rel(PRESSURE_MESH_FIT)}",
        "admission_verdict": "diagnostic-only",
        "reason_for_verdict": "Mesh family exists and selected Salt2 pressure/thermal outputs are readable, but 0 closure-QOI rows are publication-ready and 0 thermal rows are fit-admissible.",
        "part_of_live_job_3293924": "no",
        "action_needed": "resolve closure-QOI GCI/sign/heat-balance gates before using mesh rows for fit or publication uncertainty",
        "split_recommendation": "diagnostic mesh/GCI evidence only",
        "bc_label_status": "inherits Salt2 mainline roles for coarse; refined row-level BC reduction not promoted",
    }


def _invalid_original_perturbation_row() -> Dict[str, object]:
    return {
        "case_key": "original_q_insulation_perturbation_sweep",
        "source_id": "invalid_14_case_q_insulation_campaign",
        "salt_number": "salt1-salt4",
        "variant": "old_false_steady_q_insulation",
        "classification": "failed",
        "source_path": _rel(CORRECTED_README),
        "run_root": "old invalid roots quarantined/deleted",
        "case_stage_path": "",
        "latest_time_s": "",
        "run_state": "failed",
        "scheduler_job_id": "",
        "terminal_status_evidence_path": _rel(CORRECTED_README),
        "solver_log_path": "",
        "postprocessing_availability": "not usable",
        "steady_state_admission_evidence_path": _rel(CFD_ADMISSION_MAP),
        "admission_verdict": "not-admissible",
        "reason_for_verdict": "Historical Q perturbation roots were false-steady/invalid because live restart fields did not carry the intended perturbation.",
        "part_of_live_job_3293924": "no",
        "action_needed": "none; use corrected Salt-Q campaign only after terminal admission",
        "split_recommendation": "excluded",
        "bc_label_status": "invalid live BC/restart evidence",
    }


def _build_inventory(job_info: Dict[str, str]) -> List[Dict[str, object]]:
    split_rows = _load_split_rows()
    family_rows = _load_family_rows()
    rows = []
    rows.extend(_mainline_inventory_rows(split_rows, family_rows))
    rows.extend(_corrected_rows(job_info))
    rows.append(_mesh_family_row())
    rows.extend(_historical_registry_rows(family_rows))
    rows.append(_invalid_original_perturbation_row())
    return rows


def _build_corrected_status(inventory_rows: List[Dict[str, object]]) -> List[Dict[str, object]]:
    manifest_rows = {row["case_key"]: row for row in _read_csv(CORRECTED_MANIFEST)}
    status_rows = {row["case_key"]: row for row in _read_csv(CORRECTED_STATUS)}
    live_rows = {row["source_key"]: row for row in _read_csv(CORRECTED_LIVE_GATE)}
    preflight_rows = {row["case_key"]: row for row in _read_csv(CORRECTED_PREFLIGHT)}
    by_source = {row["source_id"]: row for row in inventory_rows if row["classification"].startswith("perturbation") or row["classification"] == "failed"}
    output = []
    for case_key, manifest in sorted(manifest_rows.items()):
        inv = by_source[case_key]
        live = live_rows.get(case_key, {})
        preflight = preflight_rows.get(case_key, {})
        output.append({
            "case_key": inv["case_key"],
            "source_id": case_key,
            "salt_number": inv["salt_number"],
            "variant": inv["variant"],
            "q_ratio": manifest["q_ratio"],
            "target_heater_power_W": manifest["target_heater_power_W"],
            "parent_restart_time_s": manifest["parent_restart_time_s"],
            "case_stage_path": inv["case_stage_path"],
            "submitted_job_ids": inv["scheduler_job_id"],
            "part_of_live_selected_job_3293924": inv["part_of_live_job_3293924"],
            "live_slurm_step": live.get("slurm_step", ""),
            "preflight_overall_ok": preflight.get("overall_ok", ""),
            "run_state": inv["run_state"],
            "latest_time_s": inv["latest_time_s"],
            "previous_gate_status": status_rows.get(case_key, {}).get("status", ""),
            "terminal_status_evidence_path": inv["terminal_status_evidence_path"],
            "solver_log_path": inv["solver_log_path"],
            "admission_verdict": inv["admission_verdict"],
            "action_needed": inv["action_needed"],
        })
    return output


def _build_steady_matrix(inventory_rows: List[Dict[str, object]]) -> List[Dict[str, object]]:
    rows = []
    for row in inventory_rows:
        verdict = row["admission_verdict"]
        if verdict in {"fit-admissible", "validation-only", "holdout-only"}:
            can_enter = "yes"
        else:
            can_enter = "no"
        if row["part_of_live_job_3293924"] == "yes":
            steady_class = "pending-terminal-window"
        elif verdict == "diagnostic-only":
            steady_class = "context-or-diagnostic"
        elif verdict == "not-admissible":
            steady_class = "failed-or-invalid"
        elif verdict == "sensitivity-only":
            steady_class = "partial-not-admitted"
        else:
            steady_class = "admitted-baseline"
        rows.append({
            "case_key": row["case_key"],
            "source_id": row["source_id"],
            "salt_number": row["salt_number"],
            "variant": row["variant"],
            "run_state": row["run_state"],
            "latest_time_s": row["latest_time_s"],
            "steady_state_class": steady_class,
            "steady_state_admission_evidence_path": row["steady_state_admission_evidence_path"],
            "admission_verdict": verdict,
            "can_enter_downstream_analysis_now": can_enter,
            "downstream_use_now": row["split_recommendation"],
            "reason": row["reason_for_verdict"],
        })
    return rows


def _role_flags(role: str, bc_type: str) -> Dict[str, str]:
    return {
        "heater_source": "yes" if role == "heater" else "no",
        "cooler_hx_removal": "yes" if role == "cooler" else "no",
        "passive_wall": "yes" if role in {"ambient_wall", "junction_other", "test_section"} and bc_type != "zeroGradient" else "no",
        "rcExternalTemperature_radiative_wall": "yes" if "rcExternalTemperature" in bc_type else "no",
        "inlet_outlet_other": "yes" if role == "zero_gradient_ncc_connector" else "no",
    }


def _build_bc_roles(inventory_rows: List[Dict[str, object]]) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    stats = _load_patch_role_stats()
    summary_rows = _read_csv(PATCH_ROLE_SUMMARY)
    for row in summary_rows:
        case_id = row["case_id"]
        salt = case_id.replace("_", "")
        role = row["role"]
        role_stats = stats.get(case_id, {}).get(role, {})
        bc_parts = []
        for bc_type, count in sorted(role_stats.get("bc_types", Counter()).items()):
            bc_parts.append(f"{bc_type}:{count}")
        bc_type_summary = ";".join(bc_parts)
        flags = _role_flags(role, bc_type_summary)
        rows.append({
            "case_key": f"{salt}_jin_nominal_continuation",
            "source_id": row["source_id"],
            "salt_number": salt,
            "variant": "nominal",
            "patch_or_role": role,
            "thermal_role": row["role_group"],
            "bc_type": bc_type_summary,
            "patch_count": row["patch_count"],
            "heater_source": flags["heater_source"],
            "cooler_hx_removal": flags["cooler_hx_removal"],
            "passive_wall": flags["passive_wall"],
            "rcExternalTemperature_radiative_wall": flags["rcExternalTemperature_radiative_wall"],
            "inlet_outlet_other": flags["inlet_outlet_other"],
            "imposed_Q_W": row["imposed_Q_W"],
            "realized_wallHeatFlux_W": row["realized_wallHeatFlux_W"],
            "emissivity_values": ";".join(sorted(role_stats.get("emissivity_values", set()))),
            "Tsur_K_values": ";".join(sorted(role_stats.get("tsur_values", set()))),
            "radiation_wallHeatFlux_semantics": RADIATION_SEMANTICS,
            "evidence_path": _rel(PATCH_ROLE_SUMMARY),
            "admission_use": "admitted baseline BC label" if case_id in {"salt_2", "salt_3", "salt_4"} else "diagnostic",
        })
    for row in inventory_rows:
        if row["classification"] != "perturbation/sensitivity":
            continue
        for role, role_group, bc_type, imposed in [
            ("heater", "intended_heater_input", "fixedValue/coded thermal source patches", "manifest target_heater_power_W"),
            ("cooler", "intended_cooler_removal", "fixedValue/coded balanced sink patches", "manifest target_cooler_q04/q05/q06_W"),
            ("ambient_wall", "passive_ambient_wall_exchange", "rcExternalTemperature inherited from parent", ""),
        ]:
            flags = _role_flags(role, bc_type)
            rows.append({
                "case_key": row["case_key"],
                "source_id": row["source_id"],
                "salt_number": row["salt_number"],
                "variant": row["variant"],
                "patch_or_role": role,
                "thermal_role": role_group,
                "bc_type": bc_type,
                "patch_count": "3" if role in {"heater", "cooler"} else "",
                "heater_source": flags["heater_source"],
                "cooler_hx_removal": flags["cooler_hx_removal"],
                "passive_wall": flags["passive_wall"],
                "rcExternalTemperature_radiative_wall": flags["rcExternalTemperature_radiative_wall"],
                "inlet_outlet_other": flags["inlet_outlet_other"],
                "imposed_Q_W": imposed,
                "realized_wallHeatFlux_W": "",
                "emissivity_values": "inherits parent; terminal row reduction pending",
                "Tsur_K_values": "inherits parent; terminal row reduction pending",
                "radiation_wallHeatFlux_semantics": RADIATION_SEMANTICS,
                "evidence_path": _rel(CORRECTED_MANIFEST),
                "admission_use": "not admitted until terminal harvest/admission gate",
            })
    rows.append({
        "case_key": "salt2_mesh_refinement_family_coarse_medium_fine",
        "source_id": "viscosity_screening_salt_test_2_jin_coarse_mesh",
        "salt_number": "salt2",
        "variant": "mesh-level",
        "patch_or_role": "coarse/medium/fine mesh-family BCs",
        "thermal_role": "diagnostic mesh-family inheritance",
        "bc_type": "inherits Salt2 setup; refined BC reduction not separately admitted",
        "patch_count": "",
        "heater_source": "yes",
        "cooler_hx_removal": "yes",
        "passive_wall": "yes",
        "rcExternalTemperature_radiative_wall": "yes",
        "inlet_outlet_other": "yes",
        "imposed_Q_W": "",
        "realized_wallHeatFlux_W": "",
        "emissivity_values": "0.95 on admitted Salt2 mainline rcExternalTemperature patches",
        "Tsur_K_values": "299.19 on admitted Salt2 mainline rcExternalTemperature patches",
        "radiation_wallHeatFlux_semantics": RADIATION_SEMANTICS,
        "evidence_path": _rel(THERMAL_MESH_STATUS),
        "admission_use": "diagnostic mesh/GCI only",
    })
    return rows


def _build_recommended_split(inventory_rows: List[Dict[str, object]]) -> List[Dict[str, object]]:
    rows = []
    for row in inventory_rows:
        case_key = row["case_key"]
        verdict = row["admission_verdict"]
        if case_key == "salt2_jin_nominal_continuation":
            category = "training candidate"
            split = "training"
            can_train = "yes"
            guardrail = "single train baseline; no validation/holdout leakage"
        elif case_key == "salt3_jin_nominal_continuation":
            category = "validation candidate"
            split = "validation"
            can_train = "no"
            guardrail = "do not fit on Salt3 after using it for model choice"
        elif case_key == "salt4_jin_nominal_continuation":
            category = "holdout candidate"
            split = "holdout"
            can_train = "no"
            guardrail = "keep endpoint hidden from fitting/model selection"
        elif row["classification"] == "perturbation/sensitivity":
            category = "perturbation/sensitivity candidate"
            split = "sensitivity-only pending terminal admission"
            can_train = "no"
            guardrail = "perturbations of a baseline are grouped with that baseline; do not treat as independent training rows without a dated split policy"
        elif verdict == "diagnostic-only":
            category = "diagnostic-only/excluded"
            split = "diagnostic-only"
            can_train = "no"
            guardrail = "not current fit evidence"
        else:
            category = "diagnostic-only/excluded"
            split = "excluded"
            can_train = "no"
            guardrail = "failed, false-steady, historical, or mesh-diagnostic evidence cannot train models"
        rows.append({
            "case_key": case_key,
            "source_id": row["source_id"],
            "salt_number": row["salt_number"],
            "variant": row["variant"],
            "category": category,
            "recommended_split": split,
            "can_expand_training_now": can_train,
            "can_enter_validation_now": "yes" if split == "validation" else "no",
            "can_enter_holdout_now": "yes" if split == "holdout" else "no",
            "leakage_guardrail": guardrail,
            "requirements_before_fit": row["action_needed"],
            "reason": row["reason_for_verdict"],
        })
    return rows


def _build_actions(inventory_rows: List[Dict[str, object]], job_info: Dict[str, str]) -> List[Dict[str, object]]:
    return [
        {
            "action_group": "live_corrected_q_job_3293924",
            "affected_cases": "salt2_lo10q;salt2_hi10q;salt4_lo10q;salt4_hi10q",
            "current_state": job_info["job_state"],
            "action_needed": "Wait for terminal scheduler state; do not launch an immediate duplicate harvest while the solver job is running. After exit, harvest stdout/stderr and solver logs, run operating-point steady/admission gate, and only then classify rows for fit/sensitivity use.",
            "priority": "high",
            "evidence_path": f"{_rel(SLURM_3293924_OUT)}; {_rel(SLURM_3293924_ERR)}; {_rel(CORRECTED_PREFLIGHT)}",
            "unlocks": "potential corrected-Q sensitivity/correlation rows; no downstream use until admitted",
        },
        {
            "action_group": "deferred_corrected_q_partial_rows",
            "affected_cases": ";".join(row["case_key"] for row in inventory_rows if row["admission_verdict"] == "sensitivity-only"),
            "current_state": "stopped/under-advanced",
            "action_needed": "Continue or re-gate rows after sufficient perturbed operating-point window; retain as sensitivity-only unless split policy admits perturbations.",
            "priority": "medium",
            "evidence_path": _rel(CORRECTED_STATUS),
            "unlocks": "possible Q-response diagnostics after terminal harvest",
        },
        {
            "action_group": "failed_corrected_q_high_rows",
            "affected_cases": ";".join(row["case_key"] for row in inventory_rows if row["run_state"] == "failed" and "salt3" in row["case_key"]),
            "current_state": "failed/not accepted",
            "action_needed": "Investigate cancelled high-Q attempt before rebuild/rerun; document launcher/BC/log cause.",
            "priority": "medium",
            "evidence_path": _rel(CORRECTED_STATUS),
            "unlocks": "Salt3 high-Q sensitivity rows only after corrected rerun and terminal gate",
        },
        {
            "action_group": "salt1_policy",
            "affected_cases": "salt1_jin_nominal_continuation;salt1_lo10q;salt1_hi10q",
            "current_state": "terminal/context-only",
            "action_needed": "Write and approve Salt1 admission/split policy; verify corrected-Q convergenceMonitor cannot stop on weak diagnostic criteria before any continuation.",
            "priority": "medium",
            "evidence_path": _rel(SALT1_ADMISSION),
            "unlocks": "Salt1 diagnostic context only unless policy changes",
        },
        {
            "action_group": "mesh_family_closure_qoi_gci",
            "affected_cases": "salt2_mesh_refinement_family_coarse_medium_fine",
            "current_state": "diagnostic only",
            "action_needed": "Resolve non-monotone/missing-triplet/sign/heat-balance blockers before any closure-fit or publication uncertainty use.",
            "priority": "high",
            "evidence_path": _rel(THERMAL_MESH_STATUS),
            "unlocks": "publication-strength mesh uncertainty and thermal/closure admission",
        },
        {
            "action_group": "bc_labeling_for_pending_rows",
            "affected_cases": "all corrected-Q rows after terminal harvest",
            "current_state": "manifest/preflight labels only",
            "action_needed": "Reduce row-level boundary patch roles and heat ledgers after terminal postprocessing; preserve rcExternalTemperature radiation semantics.",
            "priority": "medium",
            "evidence_path": f"{_rel(CORRECTED_MANIFEST)}; {_rel(THERMAL_BOUNDARY_MAP)}",
            "unlocks": "correctly labeled sensitivity rows for downstream tables",
        },
        {
            "action_group": "upcomer_onset_bracketing",
            "affected_cases": "salt2_jin_nominal_continuation;salt3_jin_nominal_continuation;salt4_jin_nominal_continuation;salt4_hi5q;salt4_hi10q;new_targeted_re150;new_targeted_re200;new_targeted_re250",
            "current_state": "existing admitted diagnostics reach Re_upcomer=134.883 and all are recirculating",
            "action_needed": "Mine terminal Salt4 high-Q corrected rows after job 3293924 exits; if no admitted row reaches a transition/non-recirculating state, design targeted Salt CFD at Re_upcomer 150, 200, and 250 with matched recirculation, wall-bulk Delta T, Gz, secondary-velocity, and uncertainty extraction.",
            "priority": "high",
            "evidence_path": f"{_rel(UPCOMER_ONSET_CONDITIONS)}; {_rel(UPCOMER_ONSET_REQUIREMENTS)}; {_rel(UPCOMER_BLOCKED_METRICS)}",
            "unlocks": "bounded upcomer recirculation onset and ordinary-pipe anchor evidence",
        },
    ]


def _onset_availability(row: Dict[str, object]) -> str:
    if row["recirculation_evidence_available"] == "yes":
        return "available now"
    if row["part_of_live_job_3293924"] == "yes":
        return "running"
    if row["run_state"] == "failed":
        return "would require a new run"
    if row["classification"] == "perturbation/sensitivity":
        return "needs continuation"
    if row["run_state"] in {"completed", "stopped"}:
        return "terminal but needs postprocessing"
    return "would require a new run"


def _re_target_bucket(re_upcomer: str) -> str:
    if not re_upcomer:
        return ""
    try:
        value = float(re_upcomer)
    except ValueError:
        return ""
    targets = [150.0, 200.0, 250.0]
    nearest = min(targets, key=lambda target: abs(target - value))
    if value < 150.0:
        return "highest_available_below_150" if value > 130.0 else f"below_Re{int(nearest)}"
    return f"near_Re{int(nearest)}"


def _build_upcomer_onset_candidates(inventory_rows: List[Dict[str, object]]) -> List[Dict[str, object]]:
    metrics = _load_upcomer_metrics()
    rows: List[Dict[str, object]] = []
    for row in inventory_rows:
        include = (
            row["classification"] in {"mainline nominal", "perturbation/sensitivity", "failed"}
            or row["case_key"] == "salt2_mesh_refinement_family_coarse_medium_fine"
        )
        if not include:
            continue
        metric = metrics.get(str(row["case_key"]), {})
        re_upcomer = str(row.get("Re_upcomer", ""))
        rows.append({
            "case_key": row["case_key"],
            "source_id": row["source_id"],
            "salt_number": row["salt_number"],
            "variant": row["variant"],
            "availability_status": _onset_availability(row),
            "run_state": row["run_state"],
            "admission_verdict": row["admission_verdict"],
            "Re_upcomer": re_upcomer,
            "Re_target_bucket": _re_target_bucket(re_upcomer),
            "recirculation_evidence_available": row["recirculation_evidence_available"],
            "candidate_onset_role": row["candidate_onset_role"],
            "recirculation_observed": metric.get("recirculation_observed", ""),
            "backflow_fraction": metric.get("backflow_fraction", ""),
            "Ri_median": metric.get("Ri_median", ""),
            "recirculation_intensity": metric.get("recirculation_intensity", ""),
            "source_path": row["source_path"],
            "case_stage_path": row["case_stage_path"],
            "solver_log_path": row["solver_log_path"],
            "evidence_path": metric.get("source_paths", row["steady_state_admission_evidence_path"]),
            "next_action_to_unlock": row["next_action_to_unlock"],
            "reason": row["reason_for_verdict"],
        })
    for target in UPCOMER_RE_TARGETS:
        role = "ordinary_pipe_anchor" if target == "250" else "transition_candidate"
        rows.append({
            "case_key": f"new_targeted_re{target}",
            "source_id": f"planned_salt_target_re{target}",
            "salt_number": "salt_targeted",
            "variant": f"target_re{target}",
            "availability_status": "would require a new run",
            "run_state": "not_launched",
            "admission_verdict": "not-admissible",
            "Re_upcomer": target,
            "Re_target_bucket": f"target_Re{target}",
            "recirculation_evidence_available": "no",
            "candidate_onset_role": role,
            "recirculation_observed": "",
            "backflow_fraction": "",
            "Ri_median": "",
            "recirculation_intensity": "",
            "source_path": "planned targeted CFD design; no case directory yet",
            "case_stage_path": "",
            "solver_log_path": "",
            "evidence_path": _rel(UPCOMER_ONSET_REQUIREMENTS),
            "next_action_to_unlock": "create a separate board row, design/run targeted Salt CFD, then extract matched Re_upcomer/backflow/Ri/wall-bulk Delta T/Gz/secondary velocity and uncertainty before admission",
            "reason": "Current admitted CFD reaches only Re_upcomer=134.883 and all available rows are recirculating; this target is needed to bracket onset.",
        })
    return rows


def _build_exclusions(inventory_rows: List[Dict[str, object]]) -> List[Dict[str, object]]:
    rows = []
    for row in inventory_rows:
        if row["admission_verdict"] in {"fit-admissible", "validation-only", "holdout-only", "pending-terminal-harvest", "sensitivity-only"}:
            continue
        if row["case_key"] == "salt1_jin_nominal_continuation":
            exclusion = "diagnostic-only Salt1"
        elif "kirst" in row["variant"] or "historical" in row["classification"]:
            exclusion = "historical/reference"
        elif row["classification"] == "failed":
            exclusion = "failed/not-admissible"
        elif row["variant"] == "mesh-level":
            exclusion = "mesh diagnostic"
        else:
            exclusion = "diagnostic-only"
        rows.append({
            "case_key": row["case_key"],
            "source_id": row["source_id"],
            "salt_number": row["salt_number"],
            "variant": row["variant"],
            "exclusion_class": exclusion,
            "reason": row["reason_for_verdict"],
            "evidence_path": row["steady_state_admission_evidence_path"],
            "reentry_condition": row["action_needed"],
        })
    return rows


def _build_source_manifest(generated_files: List[Path]) -> List[Dict[str, object]]:
    read_only_sources = [
        CASE_REGISTRY,
        POSTPROCESSING_RUNS,
        *FAMILY_INDEXES,
        SPLIT_TABLE,
        PATCH_ROLE_TABLE,
        PATCH_ROLE_SUMMARY,
        SALT1_ADMISSION,
        SALT1_FINAL_WINDOW,
        CORRECTED_MANIFEST,
        CORRECTED_STATUS,
        CORRECTED_LIVE_GATE,
        CORRECTED_PREFLIGHT,
        SELECTED_JOBS,
        SUBMITTED_JOBS,
        CORRECTED_README,
        CORRECTED_TODO,
        SLURM_3293924_OUT,
        SLURM_3293924_ERR,
        THERMAL_MESH_STATUS,
        THERMAL_ADMISSION,
        PRESSURE_MESH_FIT,
        UPCOMER_ONSET_CONDITIONS,
        UPCOMER_BLOCKED_METRICS,
        UPCOMER_ONSET_REQUIREMENTS,
        MESH_MAP,
        CFD_ADMISSION_MAP,
        THERMAL_BOUNDARY_MAP,
    ]
    rows = []
    for path in read_only_sources:
        rows.append({
            "artifact": path.name,
            "role": "read_only_input",
            "path": _rel(path),
            "exists": path.exists(),
            "notes": "input evidence; not mutated",
        })
    for path in generated_files:
        rows.append({
            "artifact": path.name,
            "role": "generated_output",
            "path": _rel(path),
            "exists": path.exists(),
            "notes": "generated by tools/analyze/build_salt_cfd_training_evidence_inventory.py",
        })
    return rows


def _write_readme(out_dir: Path, summary: Dict[str, object], job_info: Dict[str, str]) -> None:
    text = f"""---
provenance:
  task: AGENT-334/AGENT-340
  generated_by: tools/analyze/build_salt_cfd_training_evidence_inventory.py
tags: [cfd-pp, salt-cfd, admission, training-split, corrected-q, upcomer-onset]
related:
  - operational_notes/maps/cfd-runs-and-admission.md
  - operational_notes/maps/thermal-boundary-and-radiation.md
  - operational_notes/maps/forward-predictive-model.md
---
# Salt CFD Training Evidence Inventory

## Observed Facts

- Salt-only candidate rows inventoried: `{summary["candidate_rows"]}`; water rows are excluded from this package.
- Current usable split remains Salt2 training, Salt3 validation, Salt4 holdout.
- Corrected Salt-Q rows admitted now: `0`.
- Live corrected-Q job `3293924` scheduler state at build time: `{job_info["job_state"]}` (`{job_info["scheduler_detail"]}`).
- Live selected continuation rows are `salt2_lo10q`, `salt2_hi10q`, `salt4_lo10q`, and `salt4_hi10q`; all remain pending terminal harvest.
- Salt2 mesh-family evidence exists, but current mesh/GCI gates admit `0` publication-ready closure-QOI rows and `0` fit-admissible thermal rows.
- Upcomer recirculation evidence currently available for admitted nominal diagnostics spans Re_upcomer `{summary["onset_current_re_min"]}` to `{summary["onset_current_re_max"]}`; all available rows remain recirculating.

## Inferred Interpretation

Slurm completion and solver advancement are runtime facts, not admission. A salt row can enter model training/validation/holdout only after terminal operating-point and steady-state evidence exists and the split policy allows that use. Corrected-Q perturbations are useful sensitivity candidates, but they are not independent training rows under the current split discipline.

`rcExternalTemperature` wall patches include emissivity/Tsur radiation, and `wallHeatFlux` already folds radiation into the total wall heat balance. Do not add a separate radiation residual when consuming CFD wallHeatFlux.

## Math And Assumptions

- Re_upcomer is consumed from the upstream onset package as the section Reynolds number, interpreted under the standard form `Re = rho U D / mu` for the upcomer section/window already defined there.
- Recirculation evidence is not inferred from runtime completion. It requires extracted flow metrics such as backflow fraction, reverse-flow area/mass fraction, Ri_median, and recirculation intensity on a matched retained window.
- The current non-recirculating/ordinary-pipe anchor criterion is the one stated in `next_evidence_requirements.csv`: backflow_fraction <= 0.02 and Ri_median < 0.30, or a bounded transition pair straddling backflow_fraction 0.02-0.10.
- Perturbed-Q rows may move thermal/buoyancy state, but their Re_upcomer/backflow/Ri are blank here until terminal postprocessing extracts them from the actual fields.

## Usable Now

- `salt2_jin_nominal_continuation`: training candidate.
- `salt3_jin_nominal_continuation`: validation candidate.
- `salt4_jin_nominal_continuation`: holdout candidate.

No corrected-Q row can expand training now.

## Running

- Job `3293924` (`saltq_sel_cont`) is tracked through `{_rel(SLURM_3293924_OUT)}`, `{_rel(SLURM_3293924_ERR)}`, and live solver logs listed in `corrected_q_perturbation_status.csv`.
- Rows in that job: `salt2_lo10q`, `salt2_hi10q`, `salt4_lo10q`, `salt4_hi10q`.

## Could Still Be Continued

- Partial/deferred corrected-Q rows outside job `3293924` can be continued only if they are re-gated after a sufficient perturbed operating-point window.
- Failed Salt3 high-Q rows need cause documentation before rebuild/rerun.
- Salt1 rows need an explicit Salt1 admission/split policy before any training use.

## Need Postprocessing Or Admission Review

- Live corrected-Q selected rows need terminal harvest, postprocessing, steady-state/admission gate, and BC role reduction.
- Salt2 mesh family needs closure-QOI GCI/sign/heat-balance gates before fit or publication use.
- Corrected-Q rows need a dated split policy before any admitted perturbation is used as training rather than sensitivity/correlation support.

## Can Existing CFD Bracket Upcomer Recirculation Onset?

Not yet. Existing mined Salt2/Salt3/Salt4 diagnostics are useful recirculating references, but the highest available admitted diagnostic is `salt4_jin_nominal_continuation` at Re_upcomer `{summary["onset_current_re_max"]}`, and it still has observed recirculation. There is no ordinary-pipe/non-recirculating anchor and no admitted transition pair straddling the backflow threshold.

The nearest existing candidates are Salt4 corrected-Q rows, especially `salt4_hi10q` from live job `3293924` and stopped `salt4_hi5q`, but they are availability candidates only until terminal harvest, postprocessing, and admission evidence exist. If those rows do not naturally land near/above Re_upcomer 150 with bounded recirculation metrics, the next step is new targeted Salt CFD at Re_upcomer 150, 200, and 250.

See `upcomer_onset_candidate_cases.csv` for availability, Re_upcomer, recirculation evidence, onset role, and next action per case.

## Recommended Next Actions

See `run_actions_needed.csv` for grouped blockers and concrete unlocks. The highest-value cfd-pp action remains terminal harvest of job `3293924` after it exits.
"""
    (out_dir / "README.md").write_text(text, encoding="utf-8")


def build_salt_cfd_training_evidence_inventory(out_dir: Optional[Path] = None, query_scheduler: bool = True) -> Dict[str, object]:
    out_dir = out_dir or OUT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    job_info = _query_job_3293924() if query_scheduler else {
        "job_id": "3293924",
        "job_state": "RUNNING",
        "job_evidence": _rel(SLURM_3293924_OUT),
        "scheduler_checked_at": "",
        "scheduler_detail": "scheduler query skipped by test harness; live gate evidence still marks job pending",
    }
    inventory = _build_inventory(job_info)
    _apply_upcomer_onset_fields(inventory)
    corrected = _build_corrected_status(inventory)
    steady = _build_steady_matrix(inventory)
    bc_roles = _build_bc_roles(inventory)
    split = _build_recommended_split(inventory)
    actions = _build_actions(inventory, job_info)
    exclusions = _build_exclusions(inventory)
    upcomer_onset = _build_upcomer_onset_candidates(inventory)

    output_specs = [
        ("salt_cfd_candidate_inventory.csv", [
            "case_key", "source_id", "salt_number", "variant", "classification", "source_path", "run_root",
            "case_stage_path", "latest_time_s", "run_state", "scheduler_job_id", "terminal_status_evidence_path",
            "solver_log_path", "postprocessing_availability", "steady_state_admission_evidence_path",
            "admission_verdict", "reason_for_verdict", "part_of_live_job_3293924", "action_needed",
            "split_recommendation", "bc_label_status", "Re_upcomer", "recirculation_evidence_available",
            "candidate_onset_role", "next_action_to_unlock",
        ], inventory),
        ("corrected_q_perturbation_status.csv", [
            "case_key", "source_id", "salt_number", "variant", "q_ratio", "target_heater_power_W",
            "parent_restart_time_s", "case_stage_path", "submitted_job_ids", "part_of_live_selected_job_3293924",
            "live_slurm_step", "preflight_overall_ok", "run_state", "latest_time_s", "previous_gate_status",
            "terminal_status_evidence_path", "solver_log_path", "admission_verdict", "action_needed",
        ], corrected),
        ("steady_state_admission_matrix.csv", [
            "case_key", "source_id", "salt_number", "variant", "run_state", "latest_time_s",
            "steady_state_class", "steady_state_admission_evidence_path", "admission_verdict",
            "can_enter_downstream_analysis_now", "downstream_use_now", "reason",
        ], steady),
        ("bc_role_label_inventory.csv", [
            "case_key", "source_id", "salt_number", "variant", "patch_or_role", "thermal_role", "bc_type",
            "patch_count", "heater_source", "cooler_hx_removal", "passive_wall",
            "rcExternalTemperature_radiative_wall", "inlet_outlet_other", "imposed_Q_W",
            "realized_wallHeatFlux_W", "emissivity_values", "Tsur_K_values",
            "radiation_wallHeatFlux_semantics", "evidence_path", "admission_use",
        ], bc_roles),
        ("recommended_salt_split.csv", [
            "case_key", "source_id", "salt_number", "variant", "category", "recommended_split",
            "can_expand_training_now", "can_enter_validation_now", "can_enter_holdout_now",
            "leakage_guardrail", "requirements_before_fit", "reason",
        ], split),
        ("run_actions_needed.csv", [
            "action_group", "affected_cases", "current_state", "action_needed", "priority", "evidence_path", "unlocks",
        ], actions),
        ("upcomer_onset_candidate_cases.csv", [
            "case_key", "source_id", "salt_number", "variant", "availability_status", "run_state",
            "admission_verdict", "Re_upcomer", "Re_target_bucket", "recirculation_evidence_available",
            "candidate_onset_role", "recirculation_observed", "backflow_fraction", "Ri_median",
            "recirculation_intensity", "source_path", "case_stage_path", "solver_log_path",
            "evidence_path", "next_action_to_unlock", "reason",
        ], upcomer_onset),
        ("excluded_or_diagnostic_salt_runs.csv", [
            "case_key", "source_id", "salt_number", "variant", "exclusion_class", "reason", "evidence_path",
            "reentry_condition",
        ], exclusions),
    ]

    generated_files: List[Path] = []
    for filename, fields, rows in output_specs:
        path = out_dir / filename
        _write_csv(path, fields, rows)
        generated_files.append(path)

    source_manifest_path = out_dir / "source_manifest.csv"
    _write_csv(source_manifest_path, ["artifact", "role", "path", "exists", "notes"], _build_source_manifest(generated_files))
    generated_files.append(source_manifest_path)

    verdict_counts = Counter(row["admission_verdict"] for row in inventory)
    run_state_counts = Counter(row["run_state"] for row in inventory)
    split_rows = {row["case_key"]: row for row in split}
    onset_re_values = sorted(
        float(row["Re_upcomer"])
        for row in upcomer_onset
        if row["recirculation_evidence_available"] == "yes" and row["Re_upcomer"]
    )
    summary = {
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "task": "AGENT-334/AGENT-340",
        "native_solver_outputs_mutated": False,
        "water_rows_included": 0,
        "candidate_rows": len(inventory),
        "corrected_q_rows": len(corrected),
        "bc_role_rows": len(bc_roles),
        "upcomer_onset_candidate_rows": len(upcomer_onset),
        "onset_existing_bracket_available": False,
        "onset_re_targets": [150, 200, 250],
        "onset_current_re_min": f"{min(onset_re_values):.3f}" if onset_re_values else "",
        "onset_current_re_max": f"{max(onset_re_values):.3f}" if onset_re_values else "",
        "actions_needed_rows": len(actions),
        "excluded_or_diagnostic_rows": len(exclusions),
        "admission_verdict_counts": dict(sorted(verdict_counts.items())),
        "run_state_counts": dict(sorted(run_state_counts.items())),
        "usable_training_now": [key for key, row in split_rows.items() if row["can_expand_training_now"] == "yes"],
        "usable_validation_now": [key for key, row in split_rows.items() if row["can_enter_validation_now"] == "yes"],
        "usable_holdout_now": [key for key, row in split_rows.items() if row["can_enter_holdout_now"] == "yes"],
        "corrected_q_rows_admitted_now": 0,
        "live_corrected_q_job": job_info,
        "required_outputs": [spec[0] for spec in output_specs] + ["source_manifest.csv", "summary.json", "README.md"],
    }

    summary_path = out_dir / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _write_readme(out_dir, summary, job_info)
    return summary


def main() -> None:
    summary = build_salt_cfd_training_evidence_inventory()
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
