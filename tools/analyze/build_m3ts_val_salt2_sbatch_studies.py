#!/usr/bin/env python3
"""Build and run AGENT-439 sbatch study wrappers for M3+TS/val_salt2/PM5."""

from __future__ import annotations

import argparse
import csv
import json
import os
import stat
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


TASK = "AGENT-439"
DATE = "2026-07-15"
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "work_products/2026-07/2026-07-15/2026-07-15_m3ts_val_salt2_matched_plane_sbatch_submit"

AG424 = ROOT / "work_products/2026-07/2026-07-15/2026-07-15_setup_bc_model_error_synthesis_report"
AG438 = ROOT / "work_products/2026-07/2026-07-15/2026-07-15_setup_only_hx_cooler_scorecard_unlock"
AG422 = ROOT / "work_products/2026-07/2026-07-15/2026-07-15_val_salt2_postprocessing_admission_unlock"
AG418 = ROOT / "work_products/2026-07/2026-07-15/2026-07-15_setup_predictive_heat_loss_fluid_variant"
AG425 = ROOT / "work_products/2026-07/2026-07-15/2026-07-15_f6_internal_nu_admission_review_and_forward_unblock"
PM5 = ROOT / "work_products/2026-07/2026-07-14/2026-07-14_pm5_corrected_q_matched_plane_unlock"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT.resolve()))
    except ValueError:
        return str(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: Iterable[dict[str, Any]], fieldnames: list[str]) -> int:
    data = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in data:
            writer.writerow({field: row.get(field, "") for field in fieldnames})
    return len(data)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def safe_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def fmt(value: Any, precision: int = 10) -> str:
    number = safe_float(value)
    if number is None:
        return "" if value is None else str(value)
    return f"{number:.{precision}g}"


def m3ts_rows() -> list[dict[str, Any]]:
    case_errors = read_csv(AG424 / "case_mode_error_matrix.csv")
    hx_rows = read_csv(AG438 / "setup_only_hx_boundary_scorecard.csv")
    hx_by_case = {row["case_id"]: row for row in hx_rows if row.get("candidate_id") == "salt2_fit_constant_UA_bulk_drive"}
    by_case_mode = {(row["case_id"], row["mode_id"]): row for row in case_errors}
    cases = ["salt_2", "salt_3", "salt_4"]
    rows: list[dict[str, Any]] = []
    for case_id in cases:
        m2 = by_case_mode.get((case_id, "M2_cfd_heater_test_section_cooler_pressure_root"), {})
        m3 = by_case_mode.get((case_id, "M3_cfd_heater_cooler_pressure_root"), {})
        hx = hx_by_case.get(case_id, {})
        split = m3.get("split", hx.get("split_role", ""))
        rows.append(
            {
                "case_id": case_id,
                "split_role": split,
                "study_id": "M3TS_setup_only_scaffold",
                "runtime_model_inputs": "heater_setup_model;setup_only_hx_constant_UA_bulk_drive;setup_external_boundary_table;explicit_test_section_loss_model_pending",
                "runtime_input_violations": 0,
                "hx_candidate": hx.get("candidate_id", "salt2_fit_constant_UA_bulk_drive"),
                "hx_abs_error_W": hx.get("abs_error_W", ""),
                "diagnostic_M2_mdot_error_pct": m2.get("mdot_error_pct", ""),
                "diagnostic_M2_all_probe_rmse_K": m2.get("all_probe_rmse_K", ""),
                "diagnostic_M3_mdot_error_pct": m3.get("mdot_error_pct", ""),
                "diagnostic_M3_all_probe_rmse_K": m3.get("all_probe_rmse_K", ""),
                "m3_minus_m2_mdot_error_pct": fmt((safe_float(m3.get("mdot_error_pct")) or 0.0) - (safe_float(m2.get("mdot_error_pct")) or 0.0)),
                "m3_minus_m2_all_probe_rmse_K": fmt((safe_float(m3.get("all_probe_rmse_K")) or 0.0) - (safe_float(m2.get("all_probe_rmse_K")) or 0.0)),
                "scorecard_status": "submitted_for_compute_node_rebuild_from_setup_only_inputs",
                "admission_status": "not_final_forward_v1_pending_hydraulic_internal_nu_mesh_gates",
                "guardrail": "diagnostic_M2_M3_values_are_comparators_only_not_runtime_inputs",
                "source_paths": ";".join(
                    [
                        rel(AG424 / "case_mode_error_matrix.csv"),
                        rel(AG438 / "setup_only_hx_boundary_scorecard.csv"),
                        rel(AG418 / "fluid_variant_contract.csv"),
                    ]
                ),
            }
        )
    return rows


def val_salt2_rows() -> list[dict[str, Any]]:
    gate = read_csv(AG422 / "refreshed_terminal_steady_state_gate.csv")
    split = read_csv(AG422 / "val_salt2_split_admission_refresh.csv")
    ledger = read_csv(AG422 / "val_salt2_section_heat_loss_ledger.csv")
    gate_row = gate[0] if gate else {}
    split_row = split[0] if split else {}
    total_abs_heat = sum(abs(safe_float(row.get("q_to_fluid_W")) or safe_float(row.get("net_to_fluid_W")) or 0.0) for row in ledger)
    return [
        {
            "case_id": "val_salt2",
            "source_id": "val_salt_test_2_coarse_mesh_laminar",
            "study_id": "val_salt2_external_setup_only_test",
            "split_role": split_row.get("split_role", "external_test_or_validation_candidate"),
            "fit_allowed": "no",
            "runtime_input_violations": 0,
            "steady_state_label": gate_row.get("refreshed_steady_state_label", gate_row.get("steady_state_label", "")),
            "terminal_window_s": f"{gate_row.get('window_start_s', gate_row.get('time_start_s', ''))}-{gate_row.get('window_end_s', gate_row.get('time_end_s', ''))}",
            "section_heat_loss_rows": len(ledger),
            "section_heat_loss_abs_sum_W": fmt(total_abs_heat),
            "scorecard_status": "submitted_for_compute_node_external_test_rebuild",
            "admission_status": split_row.get("admission_decision", "external_test_validation_candidate_unlocked"),
            "guardrail": "do_not_fit_or_tune_on_val_salt2; realized_wallHeatFlux_scoring_only",
            "source_paths": ";".join(
                [
                    rel(AG422 / "refreshed_terminal_steady_state_gate.csv"),
                    rel(AG422 / "val_salt2_section_heat_loss_ledger.csv"),
                    rel(AG422 / "val_salt2_split_admission_refresh.csv"),
                ]
            ),
        }
    ]


def matched_plane_preflight_rows() -> list[dict[str, Any]]:
    case_list = read_csv(PM5 / "pm5_matched_plane_case_list.csv")
    rows: list[dict[str, Any]] = []
    for row in case_list:
        source_case = ROOT / row["source_case_dir"]
        mesh_path = ROOT / row["mesh_stations_path"]
        proc_time = source_case / "processors64" / row["representative_time_s"]
        ok = source_case.exists() and mesh_path.exists() and proc_time.exists()
        rows.append(
            {
                "case_key": row["case_key"],
                "requested_split_role": row.get("requested_split_role", ""),
                "representative_time_s": row["representative_time_s"],
                "source_case_exists": source_case.exists(),
                "mesh_stations_exists": mesh_path.exists(),
                "processor_time_exists": proc_time.exists(),
                "local_field_contract_preflight": "pass" if ok else "fail",
                "compute_action": "submit_compute_node_extraction" if ok else "blocked_do_not_submit",
                "source_case_dir": row["source_case_dir"],
                "mesh_stations_path": row["mesh_stations_path"],
            }
        )
    return rows


def write_sbatch_scripts() -> list[dict[str, Any]]:
    scripts = OUT / "scripts"
    scripts.mkdir(parents=True, exist_ok=True)
    script_specs = [
        {
            "study": "m3ts",
            "path": scripts / "run_m3ts_setup_only_scorecard.sbatch",
            "job_name": "m3ts_score",
            "partition": "development",
            "time": "01:00:00",
            "command": "python3.11 tools/analyze/build_m3ts_val_salt2_sbatch_studies.py --study m3ts",
            "compute_requirement": "lightweight Python scorecard rebuild; no OpenFOAM",
        },
        {
            "study": "val_salt2",
            "path": scripts / "run_val_salt2_external_test.sbatch",
            "job_name": "val_s2_ext",
            "partition": "development",
            "time": "01:00:00",
            "command": "python3.11 tools/analyze/build_m3ts_val_salt2_sbatch_studies.py --study val_salt2",
            "compute_requirement": "lightweight Python external-test rebuild; no OpenFOAM",
        },
        {
            "study": "matched_plane_onset",
            "path": scripts / "run_matched_plane_onset_extraction.sbatch",
            "job_name": "pm5_onset",
            "partition": "NuclearEnergy",
            "time": "08:00:00",
            "command": (
                "bash work_products/2026-07/2026-07-14/2026-07-14_pm5_corrected_q_matched_plane_unlock/"
                "scripts/run_pm5_matched_plane_compute.sh preflight\n"
                "bash work_products/2026-07/2026-07-14/2026-07-14_pm5_corrected_q_matched_plane_unlock/"
                "scripts/run_pm5_matched_plane_compute.sh all"
            ),
            "compute_requirement": "OpenFOAM reconstruct/foamPostProcess sampling on compute node",
        },
    ]
    rows: list[dict[str, Any]] = []
    for spec in script_specs:
        log_base = f"{spec['study']}-%j"
        body = f"""#!/usr/bin/env bash
#SBATCH -J {spec['job_name']}
#SBATCH -N 1
#SBATCH -n 1
#SBATCH -t {spec['time']}
#SBATCH -p {spec['partition']}
#SBATCH -A ASC23046
#SBATCH -o {rel(OUT / 'logs' / (log_base + '.out'))}
#SBATCH -e {rel(OUT / 'logs' / (log_base + '.err'))}

set -euo pipefail

cd {ROOT}
mkdir -p {rel(OUT / 'logs')} {rel(OUT / 'job_run_records')}
{spec['command']}
python3.11 tools/analyze/build_m3ts_val_salt2_sbatch_studies.py --study record-run --record-study {spec['study']} --record-job-id "${{SLURM_JOB_ID:-local}}"
"""
        spec["path"].write_text(body, encoding="utf-8")
        spec["path"].chmod(spec["path"].stat().st_mode | stat.S_IXUSR)
        rows.append(
            {
                "study": spec["study"],
                "sbatch_path": rel(spec["path"]),
                "job_name": spec["job_name"],
                "partition": spec["partition"],
                "time_limit": spec["time"],
                "dependency_recommendation": "afterok:3295438",
                "compute_requirement": spec["compute_requirement"],
                "local_validation": "pending",
            }
        )
    return rows


def write_readme(summary: dict[str, Any]) -> None:
    readme = f"""# M3+TS, val_salt2, and Matched-Plane sbatch Submission

Task: {TASK}
Generated: {DATE}

This package prepares and validates three requested overnight jobs:

1. `M3+TS` setup-only study/scorecard scaffold.
2. `val_salt2` setup-only external-test scaffold.
3. PM5 matched-plane/onset extraction after local field-contract preflight.

## Guardrail

The M3+TS and val_salt2 scorecard jobs are setup/preflight rebuilds from
existing evidence and do not use realized CFD wallHeatFlux, CFD mdot, imposed
CFD cooler duty, or validation temperatures as runtime model inputs. The
matched-plane job runs OpenFOAM postprocessing only on a compute node.

## Local Preflight Result

- M3+TS rows: `{summary['m3ts_rows']}`
- val_salt2 rows: `{summary['val_salt2_rows']}`
- matched-plane preflight rows: `{summary['matched_plane_preflight_rows']}`
- matched-plane preflight failures: `{summary['matched_plane_preflight_failures']}`

## sbatch Scripts

- `scripts/run_m3ts_setup_only_scorecard.sbatch`
- `scripts/run_val_salt2_external_test.sbatch`
- `scripts/run_matched_plane_onset_extraction.sbatch`

Submit with dependency on the current corrected-Q harvest unless a later
coordinator changes the scheduler chain:

```bash
sbatch --dependency=afterok:3295438 <script>
```
"""
    (OUT / "README.md").write_text(readme, encoding="utf-8")


def build_package() -> dict[str, Any]:
    OUT.mkdir(parents=True, exist_ok=True)
    m3ts = m3ts_rows()
    val = val_salt2_rows()
    matched = matched_plane_preflight_rows()
    sbatches = write_sbatch_scripts()
    write_csv(
        OUT / "m3ts_setup_only_scorecard_preflight.csv",
        m3ts,
        [
            "case_id",
            "split_role",
            "study_id",
            "runtime_model_inputs",
            "runtime_input_violations",
            "hx_candidate",
            "hx_abs_error_W",
            "diagnostic_M2_mdot_error_pct",
            "diagnostic_M2_all_probe_rmse_K",
            "diagnostic_M3_mdot_error_pct",
            "diagnostic_M3_all_probe_rmse_K",
            "m3_minus_m2_mdot_error_pct",
            "m3_minus_m2_all_probe_rmse_K",
            "scorecard_status",
            "admission_status",
            "guardrail",
            "source_paths",
        ],
    )
    write_csv(
        OUT / "val_salt2_external_test_preflight.csv",
        val,
        [
            "case_id",
            "source_id",
            "study_id",
            "split_role",
            "fit_allowed",
            "runtime_input_violations",
            "steady_state_label",
            "terminal_window_s",
            "section_heat_loss_rows",
            "section_heat_loss_abs_sum_W",
            "scorecard_status",
            "admission_status",
            "guardrail",
            "source_paths",
        ],
    )
    write_csv(
        OUT / "matched_plane_field_contract_preflight.csv",
        matched,
        [
            "case_key",
            "requested_split_role",
            "representative_time_s",
            "source_case_exists",
            "mesh_stations_exists",
            "processor_time_exists",
            "local_field_contract_preflight",
            "compute_action",
            "source_case_dir",
            "mesh_stations_path",
        ],
    )
    write_csv(
        OUT / "sbatch_submission_plan.csv",
        sbatches,
        [
            "study",
            "sbatch_path",
            "job_name",
            "partition",
            "time_limit",
            "dependency_recommendation",
            "compute_requirement",
            "local_validation",
        ],
    )
    write_csv(
        OUT / "source_manifest.csv",
        [
            {"label": "setup_bc_model_error_report", "path": rel(AG424), "role": "M2/M3 diagnostic comparators"},
            {"label": "setup_only_hx_scorecard", "path": rel(AG438), "role": "setup-only HX candidate"},
            {"label": "val_salt2_unlock", "path": rel(AG422), "role": "external-test evidence"},
            {"label": "fluid_setup_variant", "path": rel(AG418), "role": "setup-only Fluid hooks"},
            {"label": "pm5_matched_plane_unlock", "path": rel(PM5), "role": "matched-plane extraction script and case list"},
        ],
        ["label", "path", "role"],
    )
    summary = {
        "task": TASK,
        "generated_at": utc_now(),
        "m3ts_rows": len(m3ts),
        "val_salt2_rows": len(val),
        "matched_plane_preflight_rows": len(matched),
        "matched_plane_preflight_failures": sum(1 for row in matched if row["local_field_contract_preflight"] != "pass"),
        "sbatch_scripts": len(sbatches),
        "recommended_dependency": "afterok:3295438",
    }
    write_json(OUT / "summary.json", summary)
    write_readme(summary)
    return summary


def record_run(study: str, job_id: str) -> None:
    payload = {"task": TASK, "study": study, "job_id": job_id, "completed_at": utc_now(), "cwd": os.getcwd()}
    write_json(OUT / "job_run_records" / f"{study}_{job_id}.json", payload)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--study", choices=["all", "m3ts", "val_salt2", "matched_preflight", "record-run"], default="all")
    parser.add_argument("--record-study", default="")
    parser.add_argument("--record-job-id", default="")
    args = parser.parse_args()
    if args.study == "record-run":
        record_run(args.record_study, args.record_job_id)
        return
    summary = build_package()
    if args.study == "m3ts":
        write_json(OUT / "job_run_records" / "m3ts_local_or_batch_summary.json", {"study": "m3ts", **summary})
    elif args.study == "val_salt2":
        write_json(OUT / "job_run_records" / "val_salt2_local_or_batch_summary.json", {"study": "val_salt2", **summary})
    elif args.study == "matched_preflight":
        write_json(OUT / "job_run_records" / "matched_preflight_local_or_batch_summary.json", {"study": "matched_preflight", **summary})


if __name__ == "__main__":
    main()
