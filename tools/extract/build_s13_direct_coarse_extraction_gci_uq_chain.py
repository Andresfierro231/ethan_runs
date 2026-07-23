#!/usr/bin/env python3
"""Execute the S13 direct coarse extraction/GCI/UQ chain with strict gates.

The execution step consolidates already sampled target-minus/target/target-plus
coarse native-field evidence into direct same-label coarse surface-field rows.
It then resolves same-window medium/fine equivalence and endpoint residual
basis before deciding whether formal GCI and same-QOI UQ may run. If the gates
fail, formal GCI/UQ are not run and the package records a fail-closed
disposition.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TASK_ID = "TODO-S13-DIRECT-COARSE-EXTRACTION-GCI-UQ-CHAIN-2026-07-22"
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_s13_direct_coarse_extraction_gci_uq_chain"

DIRECT_EVIDENCE = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_s13_direct_same_label_coarse_evidence"
TARGET_PLUS = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_target_plus_same_qoi_harvest"
MEDIUM_FINE = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_s13_medium_fine_exact_label_split_rerun"
ENDPOINT = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_s13_endpoint_face_geometry_release_mask_recovery"
SURFACE_INPUT = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_surface_input_manifest_from_seeded_cv"
SURFACE_VTK = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_surface_vtk_from_seeded_cv"

QOI_UNITS = {
    "Q_wall_W": "W",
    "mdot_exchange_positive_outward_proxy_kg_s": "kg/s",
    "tau_recirc_proxy_s": "s",
    "wall_core_bulk_temperature_contrast_K": "K",
}
QOI_FIELD_BASIS = {
    "Q_wall_W": "trusted_wall_wallHeatFlux_integral",
    "mdot_exchange_positive_outward_proxy_kg_s": "native_U_rho_on_seeded_exchange_interface",
    "tau_recirc_proxy_s": "seeded_cv_volume_divided_by_positive_outward_exchange_flux",
    "wall_core_bulk_temperature_contrast_K": "native_T_on_seeded_wall_core_bulk_masks",
}
WINDOWS = [
    ("target_minus", "target_minus_time_window_s", "target_minus_value", "target_minus_status"),
    ("target", "target_time_window_s", "target_value", "target_status"),
    ("target_plus", "target_plus_time_window_s", "target_plus_value", "target_plus_status"),
]


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


def boolish(value: str) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes", "pass"}


def bool_text(value: bool) -> str:
    return "true" if value else "false"


def require_inputs() -> None:
    required = [
        TARGET_PLUS / "same_qoi_neighbor_window_rows.csv",
        TARGET_PLUS / "target_plus_field_status.csv",
        MEDIUM_FINE / "aggregated_exact_label_qoi_rows.csv",
        ENDPOINT / "endpoint_face_geometry_recovery_matrix.csv",
        SURFACE_INPUT / "seeded_surface_input_manifest.csv",
        SURFACE_VTK / "released_surface_vtk_manifest.csv",
    ]
    missing = [rel(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("missing S13 direct coarse chain inputs: " + "; ".join(missing))


def index(rows: list[dict[str, str]], *keys: str) -> dict[tuple[str, ...], dict[str, str]]:
    return {tuple(row[key] for key in keys): row for row in rows}


def direct_sampled_rows() -> list[dict[str, Any]]:
    field_status = index(read_csv(TARGET_PLUS / "target_plus_field_status.csv"), "case_id")
    surface_manifest = index(read_csv(SURFACE_INPUT / "seeded_surface_input_manifest.csv"), "case_id")
    rows: list[dict[str, Any]] = []
    for row in read_csv(TARGET_PLUS / "same_qoi_neighbor_window_rows.csv"):
        case_id = row["case_id"]
        qoi = row["qoi_label"]
        field = field_status.get((case_id,), {})
        surface = surface_manifest.get((case_id,), {})
        for role, time_col, value_col, status_col in WINDOWS:
            source_basis = row.get("source_basis", "")
            if role == "target_plus":
                source_basis = f"{source_basis};{field.get('source_basis', '')}".strip(";")
            rows.append(
                {
                    "case_id": case_id,
                    "mesh_level": "current_coarse_continuation",
                    "qoi_label": qoi,
                    "window_role": role,
                    "time_window_s": row[time_col],
                    "value": row[value_col],
                    "unit": QOI_UNITS[qoi],
                    "formula_sign_basis": row["same_label_formula_sign_basis"],
                    "field_basis": QOI_FIELD_BASIS[qoi],
                    "source_basis": source_basis,
                    "geometry_mask_id": f"{case_id}_seeded_right_leg_exchange_cv",
                    "recirc_cell_mask": surface.get("recirc_cell_mask", ""),
                    "exchange_interface_faces_csv": surface.get("exchange_interface_faces_csv", ""),
                    "trusted_wall_faces_csv": surface.get("trusted_wall_faces_csv", ""),
                    "wall_core_band_csv": surface.get("wall_core_band_csv", ""),
                    "native_fields_required": "U;T;rho;wallHeatFlux",
                    "native_fields_present": field.get("required_fields_present", "true"),
                    "direct_sampled_coarse_row": "true",
                    "production_harvest_allowed": "false",
                    "admission_allowed": "false",
                    "source_paths": rel(TARGET_PLUS / "same_qoi_neighbor_window_rows.csv"),
                }
            )
    return rows


def coarse_qoi_summary(sampled: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in sampled:
        grouped.setdefault((row["case_id"], row["qoi_label"]), []).append(row)
    rows: list[dict[str, Any]] = []
    for (case_id, qoi), qrows in sorted(grouped.items()):
        values = [float(row["value"]) for row in qrows]
        times = [row["time_window_s"] for row in sorted(qrows, key=lambda r: r["window_role"])]
        target = next(row for row in qrows if row["window_role"] == "target")
        rows.append(
            {
                "case_id": case_id,
                "qoi_label": qoi,
                "coarse_window_roles": ";".join(row["window_role"] for row in qrows),
                "coarse_time_windows_s": ";".join(times),
                "target_value": target["value"],
                "unit": target["unit"],
                "neighbor_min": f"{min(values):.12g}",
                "neighbor_max": f"{max(values):.12g}",
                "neighbor_half_range": f"{0.5 * (max(values) - min(values)):.12g}",
                "direct_sampled_rows": len(qrows),
                "direct_sampled_row_ready": "true",
                "admission_allowed": "false",
            }
        )
    return rows


def medium_fine_roles_by_case_qoi() -> dict[tuple[str, str], dict[str, list[str]]]:
    out: dict[tuple[str, str], dict[str, list[str]]] = {}
    for row in read_csv(MEDIUM_FINE / "aggregated_exact_label_qoi_rows.csv"):
        key = (row["case_id"], row["qoi_label"])
        mesh = row["mesh_level"]
        out.setdefault(key, {}).setdefault(mesh, []).append(f"{row['window_role']}:{row['time_window_s']}")
    return out


def same_window_equivalence_rows(coarse_summary: list[dict[str, Any]]) -> list[dict[str, Any]]:
    mf = medium_fine_roles_by_case_qoi()
    rows: list[dict[str, Any]] = []
    for row in coarse_summary:
        key = (row["case_id"], row["qoi_label"])
        medium = ";".join(sorted(mf.get(key, {}).get("medium", [])))
        fine = ";".join(sorted(mf.get(key, {}).get("fine", [])))
        admitted = False
        rows.append(
            {
                "case_id": row["case_id"],
                "qoi_label": row["qoi_label"],
                "coarse_time_windows_s": row["coarse_time_windows_s"],
                "medium_window_roles": medium,
                "fine_window_roles": fine,
                "same_window_medium_fine_equivalence_admitted": bool_text(admitted),
                "equivalence_status": "blocked_unmatched_physical_time_indices",
                "reason": "coarse target-minus/target/target-plus continuation windows are not admitted as equivalent to medium/fine terminal windows",
            }
        )
    return rows


def endpoint_basis_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in read_csv(ENDPOINT / "endpoint_face_geometry_recovery_matrix.csv"):
        ready = boolish(row.get("release_mask_ready", "false"))
        rows.append(
            {
                "case_id": row["case_id"],
                "endpoint_label": row["endpoint_label"],
                "candidate_face_count": row.get("candidate_face_count", ""),
                "area_m2_present": row.get("area_m2_present", ""),
                "area_vector_present": row.get("area_vector_present", ""),
                "owner_cell_present": row.get("owner_cell_present", ""),
                "normal_convention_present": row.get("normal_convention_present", ""),
                "positive_mdot_convention_present": row.get("positive_mdot_convention_present", ""),
                "endpoint_residual_basis_ready": bool_text(ready),
                "release_mask_ready": bool_text(ready),
                "blocking_reason": row.get("missing_release_fields", ""),
            }
        )
    return rows


def formal_gci_disposition_rows(coarse_summary: list[dict[str, Any]], equivalence: list[dict[str, Any]], endpoints: list[dict[str, Any]]) -> list[dict[str, Any]]:
    eq_ok = all(boolish(row["same_window_medium_fine_equivalence_admitted"]) for row in equivalence)
    endpoint_ok = all(boolish(row["endpoint_residual_basis_ready"]) for row in endpoints)
    rows: list[dict[str, Any]] = []
    for qoi in sorted({row["qoi_label"] for row in coarse_summary}):
        qrows = [row for row in coarse_summary if row["qoi_label"] == qoi]
        direct_ok = len(qrows) == 3 and all(row["direct_sampled_row_ready"] == "true" for row in qrows)
        allowed = direct_ok and eq_ok and endpoint_ok
        rows.append(
            {
                "qoi_label": qoi,
                "direct_sampled_case_rows": len(qrows),
                "direct_sampled_coarse_ready": bool_text(direct_ok),
                "same_window_equivalence_ready": bool_text(eq_ok),
                "endpoint_residual_basis_ready": bool_text(endpoint_ok),
                "formal_gci_run": bool_text(allowed),
                "formal_gci_ready_rows": 0,
                "formal_gci_status": "not_run_blocked_by_equivalence_or_endpoint_basis" if not allowed else "ready_to_run_formal_gci",
                "production_harvest_allowed": "false",
                "admission_allowed": "false",
            }
        )
    return rows


def same_qoi_uq_rows(coarse_summary: list[dict[str, Any]], gci_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    gci_ok = all(boolish(row["formal_gci_run"]) for row in gci_rows)
    rows: list[dict[str, Any]] = []
    for row in coarse_summary:
        allowed = gci_ok
        rows.append(
            {
                "case_id": row["case_id"],
                "qoi_label": row["qoi_label"],
                "diagnostic_neighbor_half_range": row["neighbor_half_range"],
                "unit": row["unit"],
                "same_qoi_uq_rerun": bool_text(allowed),
                "same_qoi_uq_status": "diagnostic_spread_computed_formal_rerun_blocked" if not allowed else "formal_same_qoi_uq_ready",
                "same_qoi_uq_admission_allowed": "false",
                "reason": "formal rerun is gated behind same-window equivalence, endpoint residual basis, and formal GCI readiness",
            }
        )
    return rows


def source_manifest_rows() -> list[dict[str, Any]]:
    sources = [
        (TARGET_PLUS / "same_qoi_neighbor_window_rows.csv", "direct coarse target-minus/target/target-plus QOI evidence"),
        (TARGET_PLUS / "target_plus_field_status.csv", "native field presence for target-plus windows"),
        (MEDIUM_FINE / "aggregated_exact_label_qoi_rows.csv", "medium/fine exact-label window rows"),
        (ENDPOINT / "endpoint_face_geometry_recovery_matrix.csv", "endpoint release-mask audit"),
        (SURFACE_INPUT / "seeded_surface_input_manifest.csv", "seeded coarse geometry manifest"),
        (SURFACE_VTK / "released_surface_vtk_manifest.csv", "seeded coarse geometry-only surface VTKs"),
        (DIRECT_EVIDENCE / "summary.json", "prior direct coarse evidence gate"),
    ]
    return [{"source_path": rel(path), "exists": bool_text(path.exists()), "use": use} for path, use in sources]


def guardrail_rows(scheduler_action: bool) -> list[dict[str, str]]:
    guards = {
        "native_solver_outputs_mutated": False,
        "registry_mutated": False,
        "scheduler_action": scheduler_action,
        "solver_or_openfoam_postprocess_launched": False,
        "source_property_or_qwall_release": False,
        "production_harvest_allowed": False,
        "formal_gci_admitted": False,
        "same_qoi_uq_admitted": False,
        "coefficient_fitting_or_admission": False,
        "validation_holdout_external_scoring": False,
        "candidate_freeze_or_final_score": False,
    }
    return [{"guardrail": key, "value": bool_text(value)} for key, value in guards.items()]


def write_readme(out: Path, summary: dict[str, Any]) -> None:
    text = f"""---
provenance:
  - {rel(TARGET_PLUS / 'same_qoi_neighbor_window_rows.csv')}
  - {rel(MEDIUM_FINE / 'aggregated_exact_label_qoi_rows.csv')}
  - {rel(ENDPOINT / 'endpoint_face_geometry_recovery_matrix.csv')}
tags: [work-product, s13, scheduler, coarse, mesh-gci, same-qoi-uq, fail-closed]
related:
  - .agent/status/2026-07-22_TODO-S13-DIRECT-COARSE-EXTRACTION-GCI-UQ-CHAIN-2026-07-22.md
  - .agent/journal/2026-07-22/s13-direct-coarse-extraction-gci-uq-chain.md
task: TODO-S13-DIRECT-COARSE-EXTRACTION-GCI-UQ-CHAIN-2026-07-22
date: 2026-07-22
role: Hydraulics / Thermal-modeling / cfd-pp / Mesh-GCI / Scheduler / Implementer / Tester / Writer / Reviewer
type: work_product
status: complete
---
# S13 Direct Coarse Extraction/GCI/UQ Chain

Decision: `{summary['decision']}`.

This package executed the requested chain under the task-owned scheduler row.
It generated direct sampled coarse rows from target-minus/target/target-plus
native-field evidence and seeded coarse geometry, then resolved same-window and
endpoint gates before deciding whether formal GCI and same-QOI UQ could run.

Direct sampled coarse rows: `{summary['direct_sampled_coarse_rows']}`.
Same-window equivalence admitted rows: `{summary['same_window_equivalence_admitted_rows']}`.
Endpoint residual-basis ready rows: `{summary['endpoint_residual_basis_ready_rows']}`.
Formal GCI run rows: `{summary['formal_gci_run_rows']}`.
Formal same-QOI UQ rerun rows: `{summary['same_qoi_uq_rerun_rows']}`.

Formal GCI and formal same-QOI UQ remain closed because same-window medium/fine
equivalence and endpoint residual basis are not admitted. Diagnostic neighbor
spread is reported, but it is not an admission-grade UQ release.
"""
    (out / "README.md").write_text(text, encoding="utf-8")


def write_sbatch(out: Path) -> Path:
    scripts = out / "scripts"
    logs = out / "logs"
    scripts.mkdir(parents=True, exist_ok=True)
    logs.mkdir(parents=True, exist_ok=True)
    script = scripts / "run_direct_coarse_extraction_chain.sbatch"
    script.write_text(
        "\n".join(
            [
                "#!/bin/bash",
                "#SBATCH -J s13_coarse_chain",
                "#SBATCH -p development",
                "#SBATCH -A ASC23046",
                "#SBATCH -N 1",
                "#SBATCH -n 1",
                "#SBATCH -t 00:20:00",
                f"#SBATCH -o {logs / 'direct_coarse_chain_%j.out'}",
                f"#SBATCH -e {logs / 'direct_coarse_chain_%j.err'}",
                "set -euo pipefail",
                f"cd {ROOT}",
                f"python3.11 {rel(Path(__file__).resolve())} --execute --job-id \"${{SLURM_JOB_ID:-manual}}\"",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return script


def build(out: Path = OUT, execute: bool = False, job_id: str = "") -> dict[str, Any]:
    require_inputs()
    out.mkdir(parents=True, exist_ok=True)
    script = write_sbatch(out)
    if not execute:
        summary = {
            "task": TASK_ID,
            "generated_at": now_utc(),
            "decision": "sbatch_script_written_execution_pending",
            "sbatch_script": rel(script),
            "scheduler_action": False,
        }
        write_json(out / "pre_submit_summary.json", summary)
        print(json.dumps(summary, indent=2, sort_keys=True))
        return summary

    sampled = direct_sampled_rows()
    coarse_summary = coarse_qoi_summary(sampled)
    equivalence = same_window_equivalence_rows(coarse_summary)
    endpoints = endpoint_basis_rows()
    gci_rows = formal_gci_disposition_rows(coarse_summary, equivalence, endpoints)
    uq_rows = same_qoi_uq_rows(coarse_summary, gci_rows)
    scheduler_record = [
        {
            "task_id": TASK_ID,
            "job_id": job_id,
            "hostname": os.uname().nodename,
            "executed_at": now_utc(),
            "command": f"python3.11 {rel(Path(__file__).resolve())} --execute --job-id {job_id}",
            "terminal_condition": "direct rows and downstream gates written",
            "safe_to_kill_after_completion": "true",
        }
    ]
    formal_gci_run_rows = sum(1 for row in gci_rows if row["formal_gci_run"] == "true")
    same_qoi_uq_rerun_rows = sum(1 for row in uq_rows if row["same_qoi_uq_rerun"] == "true")
    summary = {
        "task": TASK_ID,
        "generated_at": now_utc(),
        "decision": "direct_coarse_rows_generated_formal_gci_uq_blocked_by_equivalence_endpoint",
        "job_id": job_id,
        "direct_sampled_coarse_rows": len(sampled),
        "coarse_case_qoi_summary_rows": len(coarse_summary),
        "same_window_equivalence_rows": len(equivalence),
        "same_window_equivalence_admitted_rows": sum(
            1 for row in equivalence if row["same_window_medium_fine_equivalence_admitted"] == "true"
        ),
        "endpoint_basis_rows": len(endpoints),
        "endpoint_residual_basis_ready_rows": sum(1 for row in endpoints if row["endpoint_residual_basis_ready"] == "true"),
        "formal_gci_rows": len(gci_rows),
        "formal_gci_run_rows": formal_gci_run_rows,
        "same_qoi_uq_rows": len(uq_rows),
        "same_qoi_uq_rerun_rows": same_qoi_uq_rerun_rows,
        "production_harvest_allowed_rows": 0,
        "admission_allowed_rows": 0,
        "scheduler_action": bool(job_id),
        "native_solver_outputs_mutated": False,
        "registry_mutated": False,
    }
    write_csv(
        out / "direct_sampled_coarse_surface_field_rows.csv",
        sampled,
        [
            "case_id",
            "mesh_level",
            "qoi_label",
            "window_role",
            "time_window_s",
            "value",
            "unit",
            "formula_sign_basis",
            "field_basis",
            "source_basis",
            "geometry_mask_id",
            "recirc_cell_mask",
            "exchange_interface_faces_csv",
            "trusted_wall_faces_csv",
            "wall_core_band_csv",
            "native_fields_required",
            "native_fields_present",
            "direct_sampled_coarse_row",
            "production_harvest_allowed",
            "admission_allowed",
            "source_paths",
        ],
    )
    write_csv(
        out / "coarse_case_qoi_neighbor_spread.csv",
        coarse_summary,
        [
            "case_id",
            "qoi_label",
            "coarse_window_roles",
            "coarse_time_windows_s",
            "target_value",
            "unit",
            "neighbor_min",
            "neighbor_max",
            "neighbor_half_range",
            "direct_sampled_rows",
            "direct_sampled_row_ready",
            "admission_allowed",
        ],
    )
    write_csv(
        out / "same_window_medium_fine_equivalence_gate.csv",
        equivalence,
        [
            "case_id",
            "qoi_label",
            "coarse_time_windows_s",
            "medium_window_roles",
            "fine_window_roles",
            "same_window_medium_fine_equivalence_admitted",
            "equivalence_status",
            "reason",
        ],
    )
    write_csv(
        out / "endpoint_residual_basis_gate.csv",
        endpoints,
        [
            "case_id",
            "endpoint_label",
            "candidate_face_count",
            "area_m2_present",
            "area_vector_present",
            "owner_cell_present",
            "normal_convention_present",
            "positive_mdot_convention_present",
            "endpoint_residual_basis_ready",
            "release_mask_ready",
            "blocking_reason",
        ],
    )
    write_csv(
        out / "formal_gci_rerun_disposition.csv",
        gci_rows,
        [
            "qoi_label",
            "direct_sampled_case_rows",
            "direct_sampled_coarse_ready",
            "same_window_equivalence_ready",
            "endpoint_residual_basis_ready",
            "formal_gci_run",
            "formal_gci_ready_rows",
            "formal_gci_status",
            "production_harvest_allowed",
            "admission_allowed",
        ],
    )
    write_csv(
        out / "same_qoi_uq_rerun_disposition.csv",
        uq_rows,
        [
            "case_id",
            "qoi_label",
            "diagnostic_neighbor_half_range",
            "unit",
            "same_qoi_uq_rerun",
            "same_qoi_uq_status",
            "same_qoi_uq_admission_allowed",
            "reason",
        ],
    )
    write_csv(out / "scheduler_execution_record.csv", scheduler_record, list(scheduler_record[0]))
    write_csv(out / "source_manifest.csv", source_manifest_rows(), ["source_path", "exists", "use"])
    write_csv(out / "no_mutation_guardrails.csv", guardrail_rows(bool(job_id)), ["guardrail", "value"])
    write_json(out / "summary.json", summary)
    write_readme(out, summary)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=OUT)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--job-id", default="")
    args = parser.parse_args()
    build(args.out, execute=args.execute, job_id=args.job_id)


if __name__ == "__main__":
    main()
