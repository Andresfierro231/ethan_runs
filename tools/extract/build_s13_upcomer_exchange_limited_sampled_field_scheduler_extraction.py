#!/usr/bin/env python3
"""Run limited S13 sampled-field extraction from existing seeded VTK inputs.

This task samples only interface U/T/rho and wall/core T from already released
whole-mesh cell VTKs and seeded geometry maps. It does not run OpenFOAM,
wallHeatFlux/Q_wall extraction, sampler harvest, UQ, fitting, or admission.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.analyze import build_s13_upcomer_exchange_average_field_thermal_reduction as avg
from tools.common import csv_dump, ensure_dir, iso_timestamp, json_dump, relative_to_workspace

TASK_ID = "TODO-S13-UPCOMER-EXCHANGE-LIMITED-SAMPLED-FIELD-SCHEDULER-EXTRACTION-2026-07-21"
OUT = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_limited_sampled_field_scheduler_extraction"

CONTRACT = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_sampled_field_qwall_contract_from_seeded_vtk"
SURFACE_INPUT = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_surface_input_manifest_from_seeded_cv"
AVERAGE_PROXY = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_average_field_thermal_reduction"


def rel(path: Path) -> str:
    return relative_to_workspace(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def vector(values: tuple[float, float, float]) -> str:
    return ";".join(f"{value:.12g}" for value in values)


def load_trusted_wall_rows(path: Path) -> list[dict[str, Any]]:
    return [
        {
            "face_id": int(row["face_id"]),
            "patch_name": row["patch_name"],
            "owner": int(row["owner"]),
            "area_m2": float(row["area_m2"]),
        }
        for row in read_csv(path)
    ]


def area_weighted_wall_temperature(rows: list[dict[str, Any]], fields: dict[int, dict[str, Any]]) -> dict[str, Any]:
    area = sum(row["area_m2"] for row in rows)
    t_sum = sum(fields[row["owner"]]["T"] * row["area_m2"] for row in rows)
    patch_areas: dict[str, float] = {}
    patch_t: dict[str, float] = {}
    for row in rows:
        patch = row["patch_name"]
        patch_areas[patch] = patch_areas.get(patch, 0.0) + row["area_m2"]
        patch_t[patch] = patch_t.get(patch, 0.0) + fields[row["owner"]]["T"] * row["area_m2"]
    return {
        "area_m2": area,
        "T_area_K": t_sum / area,
        "patch_T": {patch: patch_t[patch] / patch_areas[patch] for patch in sorted(patch_areas)},
    }


def load_case_fields(case: dict[str, str]) -> tuple[set[int], list[dict[str, Any]], list[dict[str, Any]], dict[int, dict[str, Any]]]:
    seed_cells = avg.load_seed_cells(ROOT / case["recirc_cell_mask"])
    interface_rows = avg.load_interface_rows(ROOT / case["exchange_interface_faces_csv"])
    wall_rows = load_trusted_wall_rows(ROOT / case["trusted_wall_faces_csv"])
    selected = set(seed_cells)
    selected.update(row["seed_owner_cell"] for row in interface_rows)
    selected.update(row["adjacent_core_cell"] for row in interface_rows)
    selected.update(row["owner"] for row in wall_rows)
    fields = avg.read_vtk_cell_fields(ROOT / case["cell_vtk"], selected)
    return seed_cells, interface_rows, wall_rows, fields


def sampled_interface_detail(case: dict[str, str], interface_rows: list[dict[str, Any]], fields: dict[int, dict[str, Any]]) -> list[dict[str, Any]]:
    area_vectors = avg.face_area_vectors(case["case_id"], {row["face_id"] for row in interface_rows})
    rows: list[dict[str, Any]] = []
    for row in interface_rows:
        seed = row["seed_owner_cell"]
        core = row["adjacent_core_cell"]
        seed_fields = fields[seed]
        core_fields = fields[core]
        outward_area = area_vectors[row["face_id"]]
        if row["seed_owner_cell"] == row["neighbour"]:
            outward_area = avg.vector_scale(outward_area, -1.0)
        u_face = avg.vector_scale(avg.vector_add(seed_fields["U"], core_fields["U"]), 0.5)
        rho_face = 0.5 * (seed_fields["rho"] + core_fields["rho"])
        t_face = 0.5 * (seed_fields["T"] + core_fields["T"])
        mdot = rho_face * avg.dot(u_face, outward_area)
        rows.append(
            {
                "case_id": case["case_id"],
                "time_window_s": case["time_window_s"],
                "face_id": row["face_id"],
                "seed_owner_cell": seed,
                "adjacent_core_cell": core,
                "area_m2": f"{row['area_m2']:.12g}",
                "seed_T_K": f"{seed_fields['T']:.12g}",
                "core_T_K": f"{core_fields['T']:.12g}",
                "face_T_avg_K": f"{t_face:.12g}",
                "seed_rho_kg_m3": f"{seed_fields['rho']:.12g}",
                "core_rho_kg_m3": f"{core_fields['rho']:.12g}",
                "face_rho_avg_kg_m3": f"{rho_face:.12g}",
                "seed_U_m_s": vector(seed_fields["U"]),
                "core_U_m_s": vector(core_fields["U"]),
                "face_U_avg_m_s": vector(u_face),
                "outward_area_vector_m2": vector(outward_area),
                "mdot_outward_proxy_kg_s": f"{mdot:.12g}",
                "release_status": "limited_sampled_interface_field_nonharvest",
            }
        )
    return rows


def sampled_wall_detail(case: dict[str, str], wall_rows: list[dict[str, Any]], fields: dict[int, dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in wall_rows:
        wall_t = fields[row["owner"]]["T"]
        rows.append(
            {
                "case_id": case["case_id"],
                "time_window_s": case["time_window_s"],
                "face_id": row["face_id"],
                "patch_name": row["patch_name"],
                "owner_cell": row["owner"],
                "area_m2": f"{row['area_m2']:.12g}",
                "wall_owner_T_K": f"{wall_t:.12g}",
                "wallHeatFlux_present": "false",
                "Q_wall_W_released": "false",
                "release_status": "limited_sampled_wall_temperature_nonharvest",
            }
        )
    return rows


def reduce_case(case: dict[str, str]) -> dict[str, Any]:
    seed_cells, interface_rows, wall_rows, fields = load_case_fields(case)
    volumes = avg.load_volumes(ROOT / case["volume_csv"], seed_cells)
    seed_avg = avg.weighted_seed_average(seed_cells, volumes, fields)
    interface = avg.interface_reduction(case["case_id"], interface_rows, fields)
    wall = area_weighted_wall_temperature(wall_rows, fields)
    return {
        "case_id": case["case_id"],
        "time_window_s": case["time_window_s"],
        "interface_face_count": len(interface_rows),
        "interface_area_m2": f"{interface['area_m2']:.12g}",
        "interface_seed_T_area_avg_K": f"{interface['seed_T_area_K']:.12g}",
        "interface_core_T_area_avg_K": f"{interface['core_T_area_K']:.12g}",
        "interface_seed_rho_area_avg_kg_m3": f"{interface['seed_rho_area_kg_m3']:.12g}",
        "interface_core_rho_area_avg_kg_m3": f"{interface['core_rho_area_kg_m3']:.12g}",
        "interface_seed_U_area_avg_m_s": vector(interface["seed_U_area_m_s"]),
        "interface_core_U_area_avg_m_s": vector(interface["core_U_area_m_s"]),
        "mdot_exchange_net_proxy_kg_s": f"{interface['mdot_net_kg_s']:.12g}",
        "mdot_exchange_positive_outward_proxy_kg_s": f"{interface['mdot_positive_outward_kg_s']:.12g}",
        "mdot_exchange_negative_inward_proxy_kg_s": f"{interface['mdot_negative_inward_kg_s']:.12g}",
        "wall_face_count": len(wall_rows),
        "trusted_wall_area_m2": f"{wall['area_m2']:.12g}",
        "trusted_wall_T_area_avg_K": f"{wall['T_area_K']:.12g}",
        "seeded_cv_T_volume_avg_K": f"{seed_avg['T_K']:.12g}",
        "delta_T_wall_minus_core_K": f"{wall['T_area_K'] - interface['core_T_area_K']:.12g}",
        "delta_T_core_minus_seed_K": f"{interface['core_T_area_K'] - seed_avg['T_K']:.12g}",
        "wallHeatFlux_present": "false",
        "Q_wall_W_released": "false",
        "sampler_ready": "false",
        "production_harvest_allowed": "false",
        "same_qoi_uq_ready": "false",
        "admission_allowed": "false",
        "release_status": "limited_sampled_field_nonharvest",
    }


def downstream_rows() -> list[dict[str, str]]:
    return [
        {
            "gate": "limited_sampled_field_extraction",
            "status": "complete_nonharvest",
            "allowed": "true",
            "reason": "interface U/T/rho and wall/core T sampled from released geometry and existing cell VTK fields",
        },
        {
            "gate": "Q_wall_W_release",
            "status": "blocked",
            "allowed": "false",
            "reason": "wallHeatFlux remains absent; wall T is not Q_wall_W",
        },
        {
            "gate": "sampler_manifest_refresh",
            "status": "blocked",
            "allowed": "false",
            "reason": "production sampler readiness still lacks Q_wall_W, pressure, viscosity, cp, and UQ",
        },
        {
            "gate": "production_harvest_uq_admission",
            "status": "blocked",
            "allowed": "false",
            "reason": "this extraction is limited nonharvest evidence only",
        },
    ]


def guardrail_rows(job_id: str = "") -> list[dict[str, str]]:
    return [
        {"guard_id": "native_output_mutation", "changed": "false", "policy": "read-only VTK/package inputs"},
        {"guard_id": "scheduler_action", "changed": "true" if job_id else "false", "policy": "task-owned Slurm job only"},
        {"guard_id": "OpenFOAM_solver_postprocessing", "changed": "false", "policy": "no solver, foamToVTK, or native postprocessing launch"},
        {"guard_id": "wallHeatFlux_Q_wall_W", "changed": "false", "policy": "wallHeatFlux absent and Q_wall_W not released"},
        {"guard_id": "sampler_harvest_uq_admission", "changed": "false", "policy": "no sampler refresh, production harvest, UQ, fit, or admission"},
        {"guard_id": "downstream_trigger", "changed": "false", "policy": "no S11/S12/S13/S15/S6 trigger"},
        {"guard_id": "registry_Fluid_external_blocker_generated_index", "changed": "false", "policy": "no registry, Fluid, external, blocker, or generated index edit"},
    ]


def source_manifest_rows() -> list[dict[str, str]]:
    paths = [
        (CONTRACT / "sampled_field_scheduler_decision.csv", "scheduler extraction permission contract"),
        (AVERAGE_PROXY / "diagnostic_average_exchange_metrics.csv", "read-only completed diagnostic proxy context"),
        (SURFACE_INPUT / "seeded_surface_input_manifest.csv", "case-level geometry/input manifest"),
    ]
    cases = read_csv(SURFACE_INPUT / "seeded_surface_input_manifest.csv")
    for case in cases:
        paths.extend(
            [
                (ROOT / case["cell_vtk"], f"{case['case_id']} whole-mesh cell VTK"),
                (ROOT / case["exchange_interface_faces_csv"], f"{case['case_id']} exchange interface face map"),
                (ROOT / case["trusted_wall_faces_csv"], f"{case['case_id']} trusted wall face map"),
            ]
        )
    return [
        {
            "path": rel(path),
            "role": role,
            "exists": str(path.exists()).lower(),
            "native_solver_output": "false",
            "mutated": "false",
        }
        for path, role in paths
    ]


def write_readme(out: Path, summary: dict[str, Any]) -> None:
    text = f"""---
provenance:
  - {rel(CONTRACT / 'sampled_field_scheduler_decision.csv')}
  - {rel(SURFACE_INPUT / 'seeded_surface_input_manifest.csv')}
tags: [s13, upcomer-exchange, limited-sampled-field, scheduler]
related:
  - .agent/status/2026-07-21_{TASK_ID}.md
task: {TASK_ID}
date: 2026-07-21
role: Hydraulics / Thermal-modeling / cfd-pp / Scheduler / Implementer / Tester / Writer
type: work_product
status: complete_nonharvest
---
# S13 Limited Sampled-Field Scheduler Extraction

This package is the scheduler-run limited extraction for interface `U/T/rho`
and wall/core `T` from existing cell VTK fields and released seeded geometry.
It is nonharvest evidence only.

- cases processed: `{summary['case_count']}`
- interface detail rows: `{summary['sampled_interface_detail_rows']}`
- wall detail rows: `{summary['sampled_wall_detail_rows']}`
- summary rows: `{summary['sampled_summary_rows']}`
- Slurm job id: `{summary.get('slurm_job_id', '')}`
- `Q_wall_W` released rows: `{summary['Q_wall_W_released_rows']}`
- production harvest allowed rows: `{summary['production_harvest_allowed_rows']}`
- admission allowed rows: `{summary['admission_allowed_rows']}`

`wall_owner_T_K` is mapped from the owner cell of trusted wall faces. It is not
wallHeatFlux, and it does not release `Q_wall_W`.
"""
    (out / "README.md").write_text(text, encoding="utf-8")


def write_sbatch(out: Path) -> Path:
    scripts = ensure_dir(out / "scripts")
    logs = ensure_dir(out / "logs")
    script = scripts / "submit_limited_sampled_field_extraction.sbatch"
    script.write_text(
        "\n".join(
            [
                "#!/bin/bash",
                "#SBATCH -J s13_limsamp",
                "#SBATCH -p development",
                "#SBATCH -A ASC23046",
                "#SBATCH -N 1",
                "#SBATCH -n 1",
                "#SBATCH -t 00:30:00",
                f"#SBATCH -o {logs / 'limited_sampled_field_%j.out'}",
                f"#SBATCH -e {logs / 'limited_sampled_field_%j.err'}",
                "set -euo pipefail",
                f"cd {ROOT}",
                f"python3.11 {rel(Path(__file__).resolve())} --execute --slurm-job-id \"${{SLURM_JOB_ID:-manual}}\"",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return script


def build(out: Path = OUT, slurm_job_id: str = "", write_script: bool = True) -> dict[str, Any]:
    ensure_dir(out)
    if write_script:
        write_sbatch(out)
    cases = read_csv(SURFACE_INPUT / "seeded_surface_input_manifest.csv")
    summary_rows: list[dict[str, Any]] = []
    interface_detail: list[dict[str, Any]] = []
    wall_detail: list[dict[str, Any]] = []
    for case in cases:
        _, interface_rows, wall_rows, fields = load_case_fields(case)
        summary_rows.append(reduce_case(case))
        interface_detail.extend(sampled_interface_detail(case, interface_rows, fields))
        wall_detail.extend(sampled_wall_detail(case, wall_rows, fields))

    log_id = slurm_job_id.split(".")[0] if slurm_job_id else "%j"
    log_paths = (
        f"{rel(out / 'logs' / f'limited_sampled_field_srun_{log_id}.out')};"
        f"{rel(out / 'logs' / f'limited_sampled_field_srun_{log_id}.err')}"
        if ".srun" in slurm_job_id
        else f"{rel(out / 'logs' / 'limited_sampled_field_%j.out')};{rel(out / 'logs' / 'limited_sampled_field_%j.err')}"
    )
    scheduler_record = [
        {
            "task_id": TASK_ID,
            "slurm_job_id": slurm_job_id,
            "hostname": os.uname().nodename,
            "executed_at": iso_timestamp(),
            "command": f"python3.11 {rel(Path(__file__).resolve())} --execute --slurm-job-id {slurm_job_id or '<unset>'}",
            "log_paths": log_paths,
            "terminal_condition": "summary/detail CSVs written and policy gates remain closed",
            "safe_to_kill_after_completion": "true",
        }
    ]
    downstream = downstream_rows()
    guards = guardrail_rows(slurm_job_id)
    sources = source_manifest_rows()
    summary = {
        "task_id": TASK_ID,
        "generated_at": iso_timestamp(),
        "decision": "limited_sampled_field_extraction_complete_nonharvest",
        "case_count": len(cases),
        "sampled_summary_rows": len(summary_rows),
        "sampled_interface_detail_rows": len(interface_detail),
        "sampled_wall_detail_rows": len(wall_detail),
        "slurm_job_id": slurm_job_id,
        "Q_wall_W_released_rows": sum(1 for row in summary_rows if row["Q_wall_W_released"] == "true"),
        "sampler_ready_rows": sum(1 for row in summary_rows if row["sampler_ready"] == "true"),
        "production_harvest_allowed_rows": sum(1 for row in summary_rows if row["production_harvest_allowed"] == "true"),
        "same_qoi_uq_ready_rows": sum(1 for row in summary_rows if row["same_qoi_uq_ready"] == "true"),
        "admission_allowed_rows": sum(1 for row in summary_rows if row["admission_allowed"] == "true"),
        "native_output_mutation": False,
        "registry_or_admission_mutation": False,
        "scheduler_action": bool(slurm_job_id),
        "OpenFOAM_solver_or_postprocessing_launched": False,
        "sampler_or_harvest_launched": False,
        "Fluid_or_external_repo_mutation": False,
        "fitting_or_model_selection": False,
        "source_property_release": False,
        "s11_s12_s13_s15_s6_trigger": False,
        "blocker_register_change": False,
        "generated_index_refresh": False,
        "residual_absorbed_into_internal_nu": False,
    }
    csv_dump(out / "sampled_field_summary.csv", list(summary_rows[0]), summary_rows)
    csv_dump(out / "sampled_interface_fields.csv", list(interface_detail[0]), interface_detail)
    csv_dump(out / "sampled_wall_core_temperature.csv", list(wall_detail[0]), wall_detail)
    csv_dump(out / "scheduler_execution_record.csv", list(scheduler_record[0]), scheduler_record)
    csv_dump(out / "downstream_gate.csv", list(downstream[0]), downstream)
    csv_dump(out / "no_mutation_guardrails.csv", list(guards[0]), guards)
    csv_dump(out / "source_manifest.csv", list(sources[0]), sources)
    json_dump(out / "summary.json", summary)
    write_readme(out, summary)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=OUT)
    parser.add_argument("--execute", action="store_true", help="perform extraction instead of writing only the sbatch script")
    parser.add_argument("--slurm-job-id", default="")
    args = parser.parse_args()
    if args.execute:
        summary = build(args.out_dir, slurm_job_id=args.slurm_job_id, write_script=True)
    else:
        ensure_dir(args.out_dir)
        script = write_sbatch(args.out_dir)
        summary = {
            "task_id": TASK_ID,
            "generated_at": iso_timestamp(),
            "decision": "sbatch_script_written_extraction_not_run",
            "sbatch_script": rel(script),
        }
        json_dump(args.out_dir / "pre_submit_summary.json", summary)
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
