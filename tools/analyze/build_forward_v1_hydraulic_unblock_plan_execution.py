#!/usr/bin/env python3
"""Build the July 15 forward-v1/hydraulic unblock execution package."""

from __future__ import annotations

import csv
import json
import subprocess
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


TASK = "AGENT-393"
DATE = "2026-07-15"
OUT_REL = Path("work_products/2026-07/2026-07-15/2026-07-15_forward_v1_hydraulic_unblock_plan_execution")
SCHEDULER_JOB_IDS = ["3293924", "3295438", "3295989", "3295990", "3295991", "3295901", "3295968", "3295120"]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="") as fh:
        return list(csv.DictReader(fh))


def read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    with path.open() as fh:
        return json.load(fh)


def write_csv(path: Path, rows: Iterable[dict[str, object]], fieldnames: list[str]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    materialized = list(rows)
    with path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in materialized:
            writer.writerow({name: row.get(name, "") for name in fieldnames})
    return len(materialized)


def run_command(args: list[str]) -> tuple[int, str, str]:
    try:
        proc = subprocess.run(args, check=False, text=True, capture_output=True, timeout=10)
        return proc.returncode, proc.stdout, proc.stderr
    except FileNotFoundError as exc:
        return 127, "", str(exc)
    except subprocess.TimeoutExpired as exc:
        return 124, exc.stdout or "", f"timed out after {exc.timeout}s"


def parse_squeue(stdout: str) -> list[dict[str, str]]:
    rows = []
    for line in stdout.splitlines():
        if not line.strip():
            continue
        parts = line.split("|")
        if len(parts) != 6:
            continue
        rows.append(
            {
                "job_id": parts[0].strip(),
                "partition": parts[1].strip(),
                "job_name": parts[2].strip(),
                "state": parts[3].strip(),
                "elapsed": parts[4].strip(),
                "node_or_reason": parts[5].strip(),
            }
        )
    return rows


def parse_sacct(stdout: str) -> list[dict[str, str]]:
    rows = []
    for line in stdout.splitlines():
        if not line.strip():
            continue
        parts = line.split("|")
        if len(parts) < 6:
            continue
        rows.append(
            {
                "job_id": parts[0].strip(),
                "job_name": parts[1].strip(),
                "state": parts[2].strip(),
                "exit_code": parts[3].strip(),
                "elapsed": parts[4].strip(),
                "node_or_reason": parts[5].strip(),
            }
        )
    return rows


def scheduler_snapshot() -> tuple[list[dict[str, str]], dict[str, str]]:
    squeue_code, squeue_out, squeue_err = run_command(
        ["squeue", "-u", "andresfierro231", "-h", "-o", "%i|%P|%j|%T|%M|%R"]
    )
    sacct_code, sacct_out, sacct_err = run_command(
        [
            "sacct",
            "-j",
            ",".join(SCHEDULER_JOB_IDS),
            "--format=JobID,JobName,State,ExitCode,Elapsed,NodeList",
            "-n",
            "-P",
        ]
    )
    squeue_rows = parse_squeue(squeue_out)
    sacct_rows = parse_sacct(sacct_out)
    sacct_by_id = {row["job_id"]: row for row in sacct_rows if "." not in row["job_id"]}
    squeue_by_id = {row["job_id"]: row for row in squeue_rows}

    labels = {
        "3293924": "corrected_q_solver_continuation",
        "3295438": "selected_salt2_salt4_pm10q_harvester",
        "3295989": "agent373_test_section_complex_raw_two_tap",
        "3295990": "agent373_f6_ready_to_run_gate",
        "3295991": "agent373_fluid_reset_k_diagnostic_sweep",
        "3295901": "cancelled_pm5_matched_plane_sbatch_original",
        "3295968": "cancelled_pm5_matched_plane_sbatch_replacement",
        "3295120": "interactive_compute_node_allocation",
    }
    rows = []
    for job_id in SCHEDULER_JOB_IDS:
        acct = sacct_by_id.get(job_id, {})
        queue = squeue_by_id.get(job_id, {})
        state = queue.get("state") or acct.get("state") or "not_present"
        reason = queue.get("node_or_reason") or acct.get("node_or_reason") or ""
        next_action = "read_only_monitor"
        if job_id == "3293924" and state == "RUNNING":
            next_action = "wait_for_terminal_then_harvest_corrected_q"
        elif job_id == "3295438" and state in {"PENDING", "PD"}:
            next_action = "wait_for_dependency_after_3293924"
        elif job_id in {"3295989", "3295990", "3295991"} and state in {"PENDING", "PD"}:
            next_action = "wait_for_agent373_dependency_chain"
        elif job_id in {"3295901", "3295968"}:
            next_action = "do_not_relaunch_blindly; replacement_interactive_run_completed_but_parse_incomplete"
        rows.append(
            {
                "job_id": job_id,
                "role": labels[job_id],
                "squeue_state": queue.get("state", ""),
                "sacct_state": acct.get("state", ""),
                "job_name": queue.get("job_name") or acct.get("job_name", ""),
                "elapsed": queue.get("elapsed") or acct.get("elapsed", ""),
                "exit_code": acct.get("exit_code", ""),
                "node_or_reason": reason,
                "current_interpretation": state,
                "next_action": next_action,
            }
        )
    meta = {
        "squeue_returncode": str(squeue_code),
        "squeue_stderr": squeue_err.strip(),
        "sacct_returncode": str(sacct_code),
        "sacct_stderr": sacct_err.strip(),
    }
    return rows, meta


def build_pm5_decision(root: Path) -> list[dict[str, object]]:
    pm5_dir = root / "work_products/2026-07/2026-07-14/2026-07-14_pm5_corrected_q_matched_plane_unlock"
    summary = read_json(pm5_dir / "summary.json")
    status_rows = read_csv(pm5_dir / "submission_status.csv")
    parsed_files = sorted((pm5_dir / "parsed").glob("matched_plane_metrics_*.csv"))
    metric_rows = []
    for path in parsed_files:
        rows = read_csv(path)
        metric_rows.extend(rows)

    incomplete = sum(1 for row in metric_rows if row.get("metric_status") != "complete")
    admitted = sum(1 for row in metric_rows if row.get("admission_status", "").startswith("admitted"))
    parsed_case_count = len({row.get("case_key", "") for row in metric_rows if row.get("case_key")})
    rows = [
        {
            "item": "cancelled_sbatch_jobs",
            "status": "resolved_no_direct_relaunch",
            "evidence": "; ".join(f"{r.get('job_id')}={r.get('state')} exit={r.get('exit_code')}" for r in status_rows if r.get("job_id", "").isdigit()),
            "decision": "do_not_relaunch_cancelled_3295901_or_3295968_blindly",
            "next_action": "use the completed interactive replacement as evidence of runnable staging; fix parse/field gap first",
            "source": str(pm5_dir / "submission_status.csv"),
        },
        {
            "item": "interactive_replacement_run",
            "status": summary.get("interactive_state", "unknown"),
            "evidence": f"run={summary.get('interactive_run_id','')} exit={summary.get('interactive_exit_code','')} parsed_csv_count={summary.get('parsed_csv_count','')}",
            "decision": "runner_path_is_viable_but_metrics_not_admitted",
            "next_action": "repair sampled field extraction/parser contract for U,rho,T,wall T,wallHeatFlux",
            "source": str(pm5_dir / "summary.json"),
        },
        {
            "item": "parsed_metric_admission",
            "status": "blocked_parse_incomplete",
            "evidence": f"cases={parsed_case_count}; metric_rows={len(metric_rows)}; incomplete_rows={incomplete}; admitted_rows={admitted}; quality={summary.get('parsed_quality_flag','')}",
            "decision": "pm5_metrics_unavailable_for_f6_onset_internal_nu",
            "next_action": "after parser/field fix, rerun staged helper or reparse generated VTKs; then refresh F6/onset gate",
            "source": str(pm5_dir / "parsed"),
        },
    ]
    return rows


def build_hydraulic_gate(root: Path, scheduler_rows: list[dict[str, str]]) -> list[dict[str, object]]:
    tap_summary = read_json(root / "work_products/2026-07/2026-07-14/2026-07-14_hydraulic_tap_length_admission_refresh/summary.json")
    gate_summary = read_json(root / "work_products/2026-07/2026-07-14/2026-07-14_forward_v1_gate_refresh_after_fluid_api_and_audits/summary.json")
    pm5_summary = read_json(root / "work_products/2026-07/2026-07-14/2026-07-14_pm5_corrected_q_matched_plane_unlock/summary.json")
    agent373_pending = [row for row in scheduler_rows if row["job_id"] in {"3295989", "3295990", "3295991"} and row["current_interpretation"] in {"PENDING", "PD"}]
    return [
        {
            "gate": "h1_faithful_launch",
            "status": "blocked_no_go",
            "evidence": f"centerline_resolved={tap_summary.get('centerline_resolved_rows')}; centerline_blocked={tap_summary.get('centerline_blocked_rows')}; component_fit_admissible={tap_summary.get('component_fit_admissible_rows')}",
            "separation": "component_K_and_reset_development_not_admitted",
            "next_action": "do not run H1 score as faithful closure until pressure evidence is admitted",
        },
        {
            "gate": "test_section_complex_raw_two_tap",
            "status": "pending_agent373" if agent373_pending else "check_agent373_outputs",
            "evidence": f"AGENT-373 pending jobs={','.join(row['job_id'] for row in agent373_pending)}",
            "separation": "tap_length_evidence_only",
            "next_action": "consume AGENT-373 output when dependency chain runs; raw extraction remains staged/no-native-mutation",
        },
        {
            "gate": "reset_development_pressure_evidence",
            "status": "api_ready_evidence_blocked",
            "evidence": f"fluid_reset_api={gate_summary.get('fluid_reset_development_api_implemented')}; h1_launchable_after_api={gate_summary.get('h1_launchable_after_fluid_api')}",
            "separation": "reset_development_K_separate_from_localized_fixed_K",
            "next_action": "wait for admitted pressure rows before reset/development fitting",
        },
        {
            "gate": "pm5_matched_pressure_upcomer",
            "status": "blocked_parse_incomplete",
            "evidence": f"interactive={pm5_summary.get('interactive_state')}; parsed_rows={pm5_summary.get('parsed_metric_row_count')}; admitted_rows={pm5_summary.get('admitted_metric_row_count')}; quality={pm5_summary.get('parsed_quality_flag')}",
            "separation": "matched_pressure_upcomer_not_mdot_or_thermal_fit",
            "next_action": "repair field/parser gap, then refresh F6/onset gate",
        },
        {
            "gate": "f6_phi_re",
            "status": "blocked_no_go",
            "evidence": f"pm5_independent_training_expansion_rows={gate_summary.get('pm5_independent_training_expansion_rows')}; pm5 metrics admitted=0",
            "separation": "straight_friction_Re_correction_not_global_multiplier",
            "next_action": "define bounded test only after admitted pressure/Re variation rows exist",
        },
    ]


def build_forward_delta(root: Path, scheduler_rows: list[dict[str, str]]) -> list[dict[str, object]]:
    mdot_summary = read_json(root / "work_products/2026-07/2026-07-14/2026-07-14_mdot_temperature_overnight_compute_node_run/summary.json")
    thermal_stage_rows = read_csv(root / "work_products/2026-07/2026-07-14/2026-07-14_thermal_overnight_compute_node_rescue/stage_status.csv")
    cooler_rows = read_csv(root / "work_products/2026-07/2026-07-14/2026-07-14_mdot_temperature_overnight_compute_node_run/setup_only_cooler_closure_bakeoff/cooler_model_scores.csv")
    gate_summary = read_json(root / "work_products/2026-07/2026-07-14/2026-07-14_forward_v1_gate_refresh_after_fluid_api_and_audits/summary.json")
    running_392 = any(row.get("exit_code") not in {"0", ""} for row in thermal_stage_rows)
    corrected = next((row for row in scheduler_rows if row["job_id"] == "3293924"), {})
    harvester = next((row for row in scheduler_rows if row["job_id"] == "3295438"), {})
    return [
        {
            "gate": "final_forward_v1",
            "before_status": gate_summary.get("final_forward_v1_status", "blocked_no_go_final_forward_v1_not_admitted"),
            "new_evidence": "AGENT-391 completed repo-local diagnostics; scheduler CFD-derived gates remain pending",
            "after_status": "blocked_no_go_final_forward_v1_not_admitted",
            "reason": "hydraulic PM5/F6, corrected-Q harvest, setup-only HX admission, and sensor policy gates are not all admitted",
        },
        {
            "gate": "corrected_q_pm10q_harvest",
            "before_status": "pending",
            "new_evidence": f"3293924={corrected.get('current_interpretation','')}; 3295438={harvester.get('current_interpretation','')}",
            "after_status": "blocked_wait_for_terminal_or_dependency",
            "reason": "do not duplicate corrected-Q solver/harvester",
        },
        {
            "gate": "setup_only_cooler_hx",
            "before_status": "missing_setup_only_outputs",
            "new_evidence": f"AGENT-391 cooler bakeoff rows={len(cooler_rows)}",
            "after_status": "diagnostic_available_not_admitted",
            "reason": "consume bakeoff, but do not call imposed CFD duty predictive",
        },
        {
            "gate": "external_bc_thermal_rescue",
            "before_status": "recommended_lightweight_study",
            "new_evidence": f"AGENT-392 stage rows={len(thermal_stage_rows)}; all_recorded_exit0={all(row.get('exit_code') == '0' for row in thermal_stage_rows) if thermal_stage_rows else False}",
            "after_status": "partial_or_in_progress_diagnostic",
            "reason": "use completed stage logs, but keep diagnostic until admitted by gate",
        },
        {
            "gate": "sensor_map_policy",
            "before_status": "blocked_policy_missing",
            "new_evidence": f"AGENT-391 sensor rows={mdot_summary.get('substudies', {}).get('agent360_refresh', {}).get('sensor_error_rows', '')}",
            "after_status": "policy_table_built_by_agent393",
            "reason": "sensor targets remain post-solve only",
        },
    ]


def build_sensor_policy(root: Path) -> list[dict[str, object]]:
    rows = read_csv(root / "work_products/2026-07/2026-07-14/2026-07-14_mdot_temperature_overnight_compute_node_run/agent360_refresh/sensor_level_errors.csv")
    grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[(row.get("sensor", ""), row.get("kind", ""))].append(row)

    out = []
    for (sensor, kind), items in sorted(grouped.items()):
        abs_errors = []
        segments = set()
        classes = set()
        for row in items:
            try:
                abs_errors.append(float(row.get("abs_error_K", "")))
            except ValueError:
                pass
            if row.get("prediction_source_segment"):
                segments.add(row["prediction_source_segment"])
            if row.get("admission_use_class"):
                classes.add(row["admission_use_class"])
        mean_abs = sum(abs_errors) / len(abs_errors) if abs_errors else ""
        max_abs = max(abs_errors) if abs_errors else ""
        policy = "scoreable_post_solve_target_only"
        if not segments:
            policy = "coordinate_upgrade_needed"
        elif max_abs != "" and max_abs > 75:
            policy = "scoreable_large_residual_review"
        out.append(
            {
                "sensor": sensor,
                "kind": kind,
                "observed_rows": len(items),
                "source_segments": ";".join(sorted(segments)),
                "admission_use_classes": ";".join(sorted(classes)),
                "mean_abs_error_K": f"{mean_abs:.6g}" if mean_abs != "" else "",
                "max_abs_error_K": f"{max_abs:.6g}" if max_abs != "" else "",
                "policy": policy,
                "runtime_input_allowed": "false",
                "next_action": "use for validation/scorecard only; do not use TP/TW as model inputs",
            }
        )
    return out


def build_source_manifest(root: Path) -> list[dict[str, object]]:
    sources = [
        "work_products/2026-07/2026-07-14/2026-07-14_hydraulic_tap_length_admission_refresh/summary.json",
        "work_products/2026-07/2026-07-14/2026-07-14_forward_v1_gate_refresh_after_fluid_api_and_audits/summary.json",
        "work_products/2026-07/2026-07-14/2026-07-14_pm5_corrected_q_matched_plane_unlock/summary.json",
        "work_products/2026-07/2026-07-14/2026-07-14_pm5_corrected_q_matched_plane_unlock/submission_status.csv",
        "work_products/2026-07/2026-07-14/2026-07-14_mdot_temperature_overnight_compute_node_run/summary.json",
        "work_products/2026-07/2026-07-14/2026-07-14_mdot_temperature_overnight_compute_node_run/agent360_refresh/sensor_level_errors.csv",
        "work_products/2026-07/2026-07-14/2026-07-14_thermal_overnight_compute_node_rescue/stage_status.csv",
        "work_products/2026-07/2026-07-14/2026-07-14_hydraulic_overnight_dependent_chain/slurm_dependency_tail_manifest.csv",
    ]
    return [{"path": source, "exists": str((root / source).exists()).lower()} for source in sources]


def write_readme(out_dir: Path, counts: dict[str, int]) -> None:
    text = f"""# Forward-v1 Hydraulic Unblock Plan Execution

Date: {DATE}
Task: {TASK}

## Bottom Line

Final forward-v1 remains `blocked_no_go_final_forward_v1_not_admitted`.
The highest-priority unblock is now the PM5 matched pressure/upcomer field/parser
gap: replacement compute completed interactively, but parsed metrics are
incomplete and admitted rows are zero.

## Outputs

- `scheduler_snapshot.csv` ({counts['scheduler']} rows)
- `pm5_matched_pressure_upcomer_relaunch_decision.csv` ({counts['pm5']} rows)
- `hydraulic_gate_refresh.csv` ({counts['hydraulic']} rows)
- `forward_v1_post_overnight_gate_delta.csv` ({counts['forward']} rows)
- `sensor_map_policy_refresh.csv` ({counts['sensor']} rows)
- `source_manifest.csv`
- `summary.json`

## Recommended Next Run/Edit

Do not relaunch cancelled PM5 sbatch jobs `3295901`/`3295968` blindly. The
staged interactive replacement path completed, so the next edit is to repair the
matched-plane field extraction/parser contract for `U`, `rho`, `T`, wall
temperature, and `wallHeatFlux`, then rerun or reparse the staged PM5 helper.
After admitted PM5 pressure/upcomer metrics exist, refresh F6/onset and
internal-Nu gates.

## Guardrails

- No native CFD solver outputs were mutated.
- No external `../cfd-modeling-tools` files were edited.
- No scheduler jobs were launched by this package.
- AGENT-373 hydraulics jobs remain pending dependencies and were not duplicated.
- Sensor temperatures remain post-solve validation targets only.
"""
    (out_dir / "README.md").write_text(text)


def build(root: Path, out_dir: Path) -> dict[str, object]:
    out_dir.mkdir(parents=True, exist_ok=True)
    scheduler_rows, scheduler_meta = scheduler_snapshot()
    pm5_rows = build_pm5_decision(root)
    hydraulic_rows = build_hydraulic_gate(root, scheduler_rows)
    forward_rows = build_forward_delta(root, scheduler_rows)
    sensor_rows = build_sensor_policy(root)
    source_rows = build_source_manifest(root)

    counts = {
        "scheduler": write_csv(out_dir / "scheduler_snapshot.csv", scheduler_rows, ["job_id", "role", "squeue_state", "sacct_state", "job_name", "elapsed", "exit_code", "node_or_reason", "current_interpretation", "next_action"]),
        "pm5": write_csv(out_dir / "pm5_matched_pressure_upcomer_relaunch_decision.csv", pm5_rows, ["item", "status", "evidence", "decision", "next_action", "source"]),
        "hydraulic": write_csv(out_dir / "hydraulic_gate_refresh.csv", hydraulic_rows, ["gate", "status", "evidence", "separation", "next_action"]),
        "forward": write_csv(out_dir / "forward_v1_post_overnight_gate_delta.csv", forward_rows, ["gate", "before_status", "new_evidence", "after_status", "reason"]),
        "sensor": write_csv(out_dir / "sensor_map_policy_refresh.csv", sensor_rows, ["sensor", "kind", "observed_rows", "source_segments", "admission_use_classes", "mean_abs_error_K", "max_abs_error_K", "policy", "runtime_input_allowed", "next_action"]),
        "source": write_csv(out_dir / "source_manifest.csv", source_rows, ["path", "exists"]),
    }
    write_readme(out_dir, counts)
    summary = {
        "task": TASK,
        "date": DATE,
        "created_utc": utc_now(),
        "counts": counts,
        "scheduler_meta": scheduler_meta,
        "final_forward_v1_status": "blocked_no_go_final_forward_v1_not_admitted",
        "recommended_next_action": "repair_pm5_matched_plane_field_extraction_parser_then_refresh_f6_onset_gate",
        "native_solver_outputs_mutated": False,
        "external_fluid_modified": False,
        "scheduler_jobs_launched": False,
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True))
    return summary


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    summary = build(root, root / OUT_REL)
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
