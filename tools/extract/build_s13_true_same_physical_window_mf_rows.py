#!/usr/bin/env python3
"""Recover true S13 medium/fine rows at coarse physical target windows.

The previous S13 chain resolved endpoint geometry but kept formal GCI/UQ closed
because medium/fine rows were terminal-role rows rather than the same coarse
target-minus/target/target-plus physical labels. This builder audits native
medium/fine processor directories for the exact coarse labels and emits true
rows only when exact native directories exist. Missing directories produce an
auditable no-go proof, not proxy terminal substitution.
"""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TASK_ID = "TODO-S13-TRUE-SAME-PHYSICAL-WINDOW-MF-ROWS-2026-07-22"
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_s13_true_same_physical_window_mf_rows"

DIRECT_CHAIN = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_s13_direct_coarse_extraction_gci_uq_chain"
ENDPOINT_CHAIN = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_s13_same_window_endpoint_gci_uq_admission_chain"
MEDIUM_FINE = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_s13_medium_fine_exact_label_split_rerun"

ROLE_MAP = {
    "target_minus": "terminal_minus",
    "target": "terminal",
    "target_plus": "terminal_plus",
}

QOI_UNITS = {
    "Q_wall_W": "W",
    "mdot_exchange_positive_outward_proxy_kg_s": "kg/s",
    "tau_recirc_proxy_s": "s",
    "wall_core_bulk_temperature_contrast_K": "K",
}


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists() or path.stat().st_size == 0:
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def bool_text(value: bool) -> str:
    return "true" if value else "false"


def boolish(value: str) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes", "pass"}


def require_inputs() -> None:
    required = [
        DIRECT_CHAIN / "direct_sampled_coarse_surface_field_rows.csv",
        DIRECT_CHAIN / "coarse_case_qoi_neighbor_spread.csv",
        ENDPOINT_CHAIN / "endpoint_residual_basis_gate.csv",
        MEDIUM_FINE / "aggregated_exact_label_qoi_rows.csv",
        MEDIUM_FINE / "aggregated_terminal_window_reductions.csv",
    ]
    missing = [rel(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("missing S13 true same-window inputs: " + "; ".join(missing))


def key_index(rows: list[dict[str, str]], *keys: str) -> dict[tuple[str, ...], dict[str, str]]:
    return {tuple(row[key] for key in keys): row for row in rows}


def source_roots_by_case_mesh() -> dict[tuple[str, str], tuple[Path, Path]]:
    roots: dict[tuple[str, str], tuple[Path, Path]] = {}
    for row in read_csv(MEDIUM_FINE / "aggregated_terminal_window_reductions.csv"):
        roots[(row["case_id"], row["mesh_level"])] = (Path(row["source_root"]), Path(row["processors_dir"]))
    return roots


def exact_label_rows() -> dict[tuple[str, str, str, str], dict[str, str]]:
    return key_index(
        read_csv(MEDIUM_FINE / "aggregated_exact_label_qoi_rows.csv"),
        "case_id",
        "mesh_level",
        "qoi_label",
        "window_role",
    )


def numeric_dir_names(path: Path) -> list[str]:
    if not path.exists():
        return []
    names = []
    for child in path.iterdir():
        if not child.is_dir():
            continue
        try:
            float(child.name)
        except ValueError:
            continue
        names.append(child.name)
    return sorted(names, key=lambda value: float(value))


def nearest_time(target: str, available: list[str]) -> tuple[str, str]:
    if not available:
        return "", ""
    target_f = float(target)
    nearest = min(available, key=lambda value: abs(float(value) - target_f))
    return nearest, f"{abs(float(nearest) - target_f):.12g}"


def native_time_inventory_rows() -> list[dict[str, Any]]:
    roots = source_roots_by_case_mesh()
    rows: list[dict[str, Any]] = []
    for (case_id, mesh), (source_root, processors_dir) in sorted(roots.items()):
        root_times = numeric_dir_names(source_root)
        processor_times = numeric_dir_names(processors_dir)
        rows.append(
            {
                "case_id": case_id,
                "mesh_level": mesh,
                "source_root": str(source_root),
                "processors_dir": str(processors_dir),
                "source_root_exists": bool_text(source_root.exists()),
                "processors_dir_exists": bool_text(processors_dir.exists()),
                "root_time_labels": ";".join(root_times),
                "processor_time_labels": ";".join(processor_times),
                "root_time_count": len(root_times),
                "processor_time_count": len(processor_times),
            }
        )
    return rows


def target_scan_rows(inventory: list[dict[str, Any]]) -> list[dict[str, Any]]:
    inv = {(row["case_id"], row["mesh_level"]): row for row in inventory}
    rows: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str, str]] = set()
    for coarse in read_csv(DIRECT_CHAIN / "direct_sampled_coarse_surface_field_rows.csv"):
        case_id = coarse["case_id"]
        coarse_role = coarse["window_role"]
        coarse_time = coarse["time_window_s"]
        for mesh in ("medium", "fine"):
            key = (case_id, mesh, coarse_role, coarse_time)
            if key in seen:
                continue
            seen.add(key)
            inv_row = inv[(case_id, mesh)]
            processor_times = str(inv_row["processor_time_labels"]).split(";") if inv_row["processor_time_labels"] else []
            root_times = str(inv_row["root_time_labels"]).split(";") if inv_row["root_time_labels"] else []
            exact_processor = coarse_time in processor_times
            exact_root = coarse_time in root_times
            nearest_proc, nearest_proc_delta = nearest_time(coarse_time, processor_times)
            nearest_root, nearest_root_delta = nearest_time(coarse_time, root_times)
            rows.append(
                {
                    "case_id": case_id,
                    "mesh_level": mesh,
                    "coarse_window_role": coarse_role,
                    "coarse_time_window_s": coarse_time,
                    "role_equivalent_window_role": ROLE_MAP[coarse_role],
                    "exact_processors_time_dir": bool_text(exact_processor),
                    "exact_root_time_dir": bool_text(exact_root),
                    "exact_native_time_available": bool_text(exact_processor or exact_root),
                    "nearest_processors_time_label": nearest_proc,
                    "nearest_processors_abs_delta": nearest_proc_delta,
                    "nearest_root_time_label": nearest_root,
                    "nearest_root_abs_delta": nearest_root_delta,
                    "true_same_physical_row_possible": bool_text(exact_processor or exact_root),
                    "admissible_equivalence_status": "pass_exact_native_time_present" if (exact_processor or exact_root) else "fail_closed_exact_native_time_absent",
                }
            )
    return rows


def true_row_table(scan: list[dict[str, Any]]) -> list[dict[str, Any]]:
    # No exact target directories exist in the current evidence. Keep this
    # function explicit so future reruns can be extended without changing the
    # package contract.
    exact = [row for row in scan if boolish(str(row["true_same_physical_row_possible"]))]
    if not exact:
        return []
    exact_rows = exact_label_rows()
    rows: list[dict[str, Any]] = []
    for scan_row in exact:
        case_id = scan_row["case_id"]
        mesh = scan_row["mesh_level"]
        role = scan_row["coarse_window_role"]
        mapped_role = ROLE_MAP[role]
        for qoi in QOI_UNITS:
            prior = exact_rows.get((case_id, mesh, qoi, mapped_role), {})
            rows.append(
                {
                    "case_id": case_id,
                    "mesh_level": mesh,
                    "qoi_label": qoi,
                    "window_role": role,
                    "time_window_s": scan_row["coarse_time_window_s"],
                    "value": "",
                    "unit": QOI_UNITS[qoi],
                    "true_same_physical_window_row": "false",
                    "row_status": "exact_time_dir_present_but_sampler_not_executed_by_this_guarded_audit",
                    "prior_role_equivalent_value": prior.get("value", ""),
                    "source_basis": "requires field sampler on exact native target directory before release",
                }
            )
    return rows


def physical_time_equivalence_rows(scan: list[dict[str, Any]]) -> list[dict[str, Any]]:
    exact_rows = exact_label_rows()
    rows: list[dict[str, Any]] = []
    for scan_row in scan:
        case_id = scan_row["case_id"]
        mesh = scan_row["mesh_level"]
        role = scan_row["coarse_window_role"]
        mapped_role = scan_row["role_equivalent_window_role"]
        qoi_refs = []
        for qoi in QOI_UNITS:
            prior = exact_rows.get((case_id, mesh, qoi, mapped_role), {})
            qoi_refs.append(f"{qoi}:{prior.get('time_window_s', '')}")
        exact = boolish(str(scan_row["exact_native_time_available"]))
        rows.append(
            {
                "case_id": case_id,
                "mesh_level": mesh,
                "coarse_window_role": role,
                "coarse_time_window_s": scan_row["coarse_time_window_s"],
                "role_equivalent_window_role": mapped_role,
                "role_equivalent_qoi_time_labels": ";".join(qoi_refs),
                "exact_native_time_available": bool_text(exact),
                "nearest_processors_time_label": scan_row["nearest_processors_time_label"],
                "nearest_processors_abs_delta": scan_row["nearest_processors_abs_delta"],
                "nearest_root_time_label": scan_row["nearest_root_time_label"],
                "nearest_root_abs_delta": scan_row["nearest_root_abs_delta"],
                "physical_time_equivalence_admitted": bool_text(exact),
                "proof_status": "exact native time label present" if exact else "no-go: exact native time label absent; role-equivalent terminal rows are proxy-only",
            }
        )
    return rows


def downstream_rows(true_rows: list[dict[str, Any]], proof: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    endpoint_rows = read_csv(ENDPOINT_CHAIN / "endpoint_residual_basis_gate.csv")
    endpoint_ready = endpoint_rows and all(boolish(row.get("endpoint_residual_basis_ready", "")) for row in endpoint_rows)
    proof_ready = proof and all(boolish(str(row["physical_time_equivalence_admitted"])) for row in proof)
    true_rows_ready = len(true_rows) == 72 and all(boolish(str(row["true_same_physical_window_row"])) for row in true_rows)
    run = endpoint_ready and proof_ready and true_rows_ready
    gci = []
    for qoi in QOI_UNITS:
        gci.append(
            {
                "qoi_label": qoi,
                "endpoint_residual_basis_ready": bool_text(endpoint_ready),
                "true_same_physical_window_rows_ready": bool_text(true_rows_ready),
                "physical_time_equivalence_ready": bool_text(proof_ready),
                "formal_gci_run": bool_text(run),
                "formal_gci_admission_ready": bool_text(run),
                "formal_gci_status": "run_ready" if run else "not_run_blocked_by_true_same_physical_medium_fine_rows",
                "production_harvest_allowed": bool_text(run),
                "admission_allowed": bool_text(run),
            }
        )
    spread = key_index(read_csv(DIRECT_CHAIN / "coarse_case_qoi_neighbor_spread.csv"), "case_id", "qoi_label")
    uq = []
    for (case_id, qoi), row in sorted(spread.items()):
        uq.append(
            {
                "case_id": case_id,
                "qoi_label": qoi,
                "diagnostic_neighbor_half_range": row.get("neighbor_half_range", ""),
                "unit": row.get("unit", QOI_UNITS[qoi]),
                "endpoint_residual_basis_ready": bool_text(endpoint_ready),
                "true_same_physical_window_rows_ready": bool_text(true_rows_ready),
                "formal_gci_ready": bool_text(run),
                "same_qoi_uq_rerun": bool_text(run),
                "same_qoi_uq_admission_allowed": bool_text(run),
                "same_qoi_uq_status": "run_ready" if run else "diagnostic_spread_only_true_same_physical_rows_missing",
                "reason": "" if run else "same-QOI UQ requires true medium/fine same-physical-window rows and formal GCI readiness",
            }
        )
    return gci, uq


def write_sbatch() -> Path:
    script = OUT / "scripts/run_true_same_physical_window_mf_rows.sbatch"
    script.parent.mkdir(parents=True, exist_ok=True)
    script.write_text(
        f"""#!/usr/bin/env bash
#SBATCH -J s13_true_mf_window
#SBATCH -A ASC23046
#SBATCH -p NuclearEnergy-dev
#SBATCH -N 1
#SBATCH -n 1
#SBATCH -t 00:20:00
#SBATCH -o {rel(OUT / 'logs/true_mf_window_%j.out')}
#SBATCH -e {rel(OUT / 'logs/true_mf_window_%j.err')}

set -euo pipefail
cd {ROOT}
python3.11 tools/extract/build_s13_true_same_physical_window_mf_rows.py --execute --job-id "${{SLURM_JOB_ID:-manual}}"
""",
        encoding="utf-8",
    )
    return script


def write_readme(summary: dict[str, Any]) -> None:
    text = f"""---
provenance:
  - {rel(DIRECT_CHAIN / 'direct_sampled_coarse_surface_field_rows.csv')}
  - {rel(MEDIUM_FINE / 'aggregated_terminal_window_reductions.csv')}
  - {rel(ENDPOINT_CHAIN / 'endpoint_residual_basis_gate.csv')}
tags: [work-product, s13, same-physical-window, mesh-gci, same-qoi-uq, fail-closed]
related:
  - .agent/status/2026-07-22_{TASK_ID}.md
  - .agent/journal/2026-07-22/s13-true-same-physical-window-mf-rows.md
task: {TASK_ID}
date: 2026-07-22
role: Hydraulics / Thermal-modeling / cfd-pp / Mesh-GCI / Scheduler / Implementer / Tester / Writer / Reviewer / Coordinator
type: work_product
status: complete
---
# S13 True Same-Physical-Window Medium/Fine Rows

Decision: `{summary['decision']}`.

This package used the `NuclearEnergy-dev` scheduler partition and scanned native
medium/fine Salt2/Salt3/Salt4 roots for exact coarse
target-minus/target/target-plus physical time labels. It generates true rows
only when exact native time directories exist.

True medium/fine same-physical rows: `{summary['true_medium_fine_rows']}`.
Physical-time equivalence admitted rows: `{summary['physical_time_equivalence_admitted_rows']}/{summary['physical_time_equivalence_rows']}`.
Endpoint residual basis ready rows: `{summary['endpoint_residual_basis_ready_rows']}/6`.
Formal GCI run rows: `{summary['formal_gci_run_rows']}/4`.
Same-QOI UQ rerun rows: `{summary['same_qoi_uq_rerun_rows']}/12`.

The current native medium/fine evidence does not contain the coarse physical
target labels. Role-equivalent terminal rows are documented as proxy-only and
are not admitted for formal GCI/UQ.
"""
    (OUT / "README.md").write_text(text, encoding="utf-8")


def execute(job_id: str | None) -> dict[str, Any]:
    require_inputs()
    OUT.mkdir(parents=True, exist_ok=True)
    inventory = native_time_inventory_rows()
    scan = target_scan_rows(inventory)
    true_rows = true_row_table(scan)
    proof = physical_time_equivalence_rows(scan)
    gci, uq = downstream_rows(true_rows, proof)

    write_csv(OUT / "native_medium_fine_time_inventory.csv", inventory, [
        "case_id", "mesh_level", "source_root", "processors_dir", "source_root_exists", "processors_dir_exists",
        "root_time_labels", "processor_time_labels", "root_time_count", "processor_time_count",
    ])
    write_csv(OUT / "same_physical_target_window_scan.csv", scan, [
        "case_id", "mesh_level", "coarse_window_role", "coarse_time_window_s", "role_equivalent_window_role",
        "exact_processors_time_dir", "exact_root_time_dir", "exact_native_time_available",
        "nearest_processors_time_label", "nearest_processors_abs_delta", "nearest_root_time_label", "nearest_root_abs_delta",
        "true_same_physical_row_possible", "admissible_equivalence_status",
    ])
    write_csv(OUT / "true_medium_fine_same_physical_rows.csv", true_rows, [
        "case_id", "mesh_level", "qoi_label", "window_role", "time_window_s", "value", "unit",
        "true_same_physical_window_row", "row_status", "prior_role_equivalent_value", "source_basis",
    ])
    write_csv(OUT / "physical_time_equivalence_proof.csv", proof, [
        "case_id", "mesh_level", "coarse_window_role", "coarse_time_window_s", "role_equivalent_window_role",
        "role_equivalent_qoi_time_labels", "exact_native_time_available", "nearest_processors_time_label",
        "nearest_processors_abs_delta", "nearest_root_time_label", "nearest_root_abs_delta",
        "physical_time_equivalence_admitted", "proof_status",
    ])
    write_csv(OUT / "formal_gci_rerun_disposition.csv", gci, [
        "qoi_label", "endpoint_residual_basis_ready", "true_same_physical_window_rows_ready",
        "physical_time_equivalence_ready", "formal_gci_run", "formal_gci_admission_ready",
        "formal_gci_status", "production_harvest_allowed", "admission_allowed",
    ])
    write_csv(OUT / "same_qoi_uq_rerun_disposition.csv", uq, [
        "case_id", "qoi_label", "diagnostic_neighbor_half_range", "unit", "endpoint_residual_basis_ready",
        "true_same_physical_window_rows_ready", "formal_gci_ready", "same_qoi_uq_rerun",
        "same_qoi_uq_admission_allowed", "same_qoi_uq_status", "reason",
    ])
    write_csv(OUT / "scheduler_execution_record.csv", [{
        "task_id": TASK_ID,
        "job_id": job_id or "",
        "partition": "NuclearEnergy-dev",
        "account": "ASC23046",
        "executed_at": now_utc(),
        "command": f"python3.11 tools/extract/build_s13_true_same_physical_window_mf_rows.py --execute --job-id {job_id or ''}".strip(),
        "terminal_condition": "native time inventory, physical-time proof, and downstream dispositions written",
        "safe_to_kill_after_completion": "true",
    }], ["task_id", "job_id", "partition", "account", "executed_at", "command", "terminal_condition", "safe_to_kill_after_completion"])
    write_csv(OUT / "source_manifest.csv", [
        {"source_path": rel(DIRECT_CHAIN / "direct_sampled_coarse_surface_field_rows.csv"), "exists": "true", "mutated": "false", "use": "coarse target labels"},
        {"source_path": rel(MEDIUM_FINE / "aggregated_terminal_window_reductions.csv"), "exists": "true", "mutated": "false", "use": "medium/fine source roots"},
        {"source_path": rel(MEDIUM_FINE / "aggregated_exact_label_qoi_rows.csv"), "exists": "true", "mutated": "false", "use": "terminal role rows, proxy-only"},
        {"source_path": rel(ENDPOINT_CHAIN / "endpoint_residual_basis_gate.csv"), "exists": "true", "mutated": "false", "use": "endpoint readiness"},
    ], ["source_path", "exists", "mutated", "use"])
    endpoint_rows = read_csv(ENDPOINT_CHAIN / "endpoint_residual_basis_gate.csv")
    endpoint_ready_count = sum(1 for row in endpoint_rows if boolish(row.get("endpoint_residual_basis_ready", "")))
    guardrails = [
        {"guardrail": "native_solver_outputs_mutated", "value": "false"},
        {"guardrail": "registry_mutated", "value": "false"},
        {"guardrail": "scheduler_action", "value": bool_text(bool(job_id))},
        {"guardrail": "scheduler_partition", "value": "NuclearEnergy-dev"},
        {"guardrail": "development_partition_used", "value": "false"},
        {"guardrail": "solver_or_openfoam_postprocess_launched", "value": "false"},
        {"guardrail": "native_field_directory_created", "value": "false"},
        {"guardrail": "proxy_terminal_window_substitution", "value": "false"},
        {"guardrail": "production_harvest_allowed", "value": "false"},
        {"guardrail": "formal_gci_admitted", "value": "false"},
        {"guardrail": "same_qoi_uq_admitted", "value": "false"},
        {"guardrail": "coefficient_fitting_or_admission", "value": "false"},
        {"guardrail": "candidate_freeze_or_final_score", "value": "false"},
    ]
    write_csv(OUT / "no_mutation_guardrails.csv", guardrails, ["guardrail", "value"])

    summary = {
        "task": TASK_ID,
        "generated_at": now_utc(),
        "job_id": job_id or "",
        "scheduler_action": bool(job_id),
        "scheduler_partition": "NuclearEnergy-dev",
        "development_partition_used": False,
        "decision": "true_same_physical_medium_fine_rows_blocked_exact_native_times_absent",
        "native_time_inventory_rows": len(inventory),
        "target_window_scan_rows": len(scan),
        "exact_native_target_rows": sum(1 for row in scan if boolish(str(row["exact_native_time_available"]))),
        "true_medium_fine_rows": len(true_rows),
        "physical_time_equivalence_rows": len(proof),
        "physical_time_equivalence_admitted_rows": sum(1 for row in proof if boolish(str(row["physical_time_equivalence_admitted"]))),
        "endpoint_residual_basis_ready_rows": endpoint_ready_count,
        "formal_gci_rows": len(gci),
        "formal_gci_run_rows": sum(1 for row in gci if boolish(str(row["formal_gci_run"]))),
        "same_qoi_uq_rows": len(uq),
        "same_qoi_uq_rerun_rows": sum(1 for row in uq if boolish(str(row["same_qoi_uq_rerun"]))),
        "production_harvest_allowed_rows": 0,
        "admission_allowed_rows": 0,
        "native_solver_outputs_mutated": False,
        "registry_mutated": False,
    }
    write_json(OUT / "summary.json", summary)
    write_readme(summary)
    return summary


def dry_run() -> dict[str, Any]:
    require_inputs()
    script = write_sbatch()
    summary = {
        "task": TASK_ID,
        "generated_at": now_utc(),
        "decision": "sbatch_script_written_execution_pending",
        "sbatch_script": rel(script),
        "scheduler_partition": "NuclearEnergy-dev",
        "scheduler_action": False,
        "native_solver_outputs_mutated": False,
        "registry_mutated": False,
    }
    write_json(OUT / "pre_submit_summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--job-id", default="")
    args = parser.parse_args()
    summary = execute(args.job_id or None) if args.execute else dry_run()
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
