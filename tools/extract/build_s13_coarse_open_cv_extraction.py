#!/usr/bin/env python3.11
"""Build or run the S13 current-coarse open-CV extraction.

The default mode is a dry preflight. `--repair-staging` copies only the
target-minus staged fields listed by the scheduler-preflight repair contract.
`--execute` performs native field sampling and should be run under scheduler
accounting unless constrained to a tiny smoke.
"""

from __future__ import annotations

import argparse
import csv
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.extract import build_s13_upcomer_exchange_medium_fine_exact_label_sampler as sampler


TASK_ID = "TODO-S13-COARSE-OPEN-CV-EXTRACTION-SCHEDULER-2026-07-22"
DATE = "2026-07-22"
SLUG = "s13_coarse_open_cv_extraction_scheduler"
DEFAULT_OUT = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_s13_coarse_open_cv_extraction"
PREFLIGHT = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_s13_coarse_open_cv_scheduler_preflight"
DEFAULT_CONTRACT = PREFLIGHT / "coarse_case_window_contract.csv"
REPAIR_CONTRACT = PREFLIGHT / "coarse_source_staging_repair_contract.csv"
STATUS_PATH = ROOT / f".agent/status/{DATE}_{TASK_ID}.md"
JOURNAL_PATH = ROOT / f".agent/journal/{DATE}/s13-coarse-open-cv-extraction-scheduler.md"
IMPORT_PATH = ROOT / f"imports/{DATE}_{SLUG}.json"

QOI_LABELS = sampler.QOI_LABELS


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT.resolve()))
    except ValueError:
        return str(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists() or path.stat().st_size == 0:
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    if not rows:
        raise ValueError(f"no rows for {path}")
    names = fieldnames or list(rows[0])
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=names, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({name: row.get(name, "") for name in names})


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def b(value: bool) -> str:
    return "true" if value else "false"


def split_semicolon(value: str) -> list[str]:
    return [item.strip() for item in value.split(";") if item.strip()]


def limited_windows(row: dict[str, str], max_windows: int) -> list[str]:
    windows = split_semicolon(row["fallback_terminal_candidate_windows_s"])
    return windows[:max_windows] if max_windows > 0 else windows


def selected_contract_rows(
    contract_csv: Path,
    *,
    case_id: str = "",
    max_cases: int = 0,
) -> list[dict[str, str]]:
    rows = read_csv(contract_csv)
    if case_id:
        rows = [row for row in rows if row["case_id"] == case_id]
    if max_cases > 0:
        rows = rows[:max_cases]
    if not rows:
        raise ValueError(f"no coarse contract rows matched case_id={case_id or '*'}")
    return rows


def repair_staging(out_dir: Path) -> list[dict[str, Any]]:
    repair_rows = read_csv(REPAIR_CONTRACT)
    manifest: list[dict[str, Any]] = []
    for row in repair_rows:
        if row.get("repair_operation") == "none_required":
            continue
        source = ROOT / row["source_field_path"]
        destination = ROOT / row["destination_field_path"]
        before = destination.exists()
        copied = False
        skipped_reason = ""
        if not source.exists():
            skipped_reason = "source_missing"
        elif before:
            skipped_reason = "destination_already_exists"
        else:
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
            copied = True
        after = destination.exists()
        manifest.append(
            {
                "case_id": row["case_id"],
                "window_s": row["window_s"],
                "field": row["field"],
                "source_field_path": row["source_field_path"],
                "source_field_exists": b(source.exists()),
                "destination_field_path": row["destination_field_path"],
                "destination_existed_before": b(before),
                "destination_exists_after": b(after),
                "bytes_after": destination.stat().st_size if after else "",
                "copied": b(copied),
                "skipped_reason": skipped_reason,
                "native_solver_output_mutated": "false",
            }
        )
    write_csv(out_dir / "staging_repair_manifest.csv", manifest)
    return manifest


def source_preflight_rows(rows: list[dict[str, str]], max_windows: int = 0) -> list[dict[str, Any]]:
    adapted: list[dict[str, str]] = []
    for row in rows:
        adapted.append(
            {
                "case_id": row["case_id"],
                "mesh_level": row["mesh_label"],
                "source_root": str(ROOT / row["source_root"]),
                "processors_dir": str(ROOT / row["processors_dir"]),
                "fallback_terminal_candidate_windows_s": ";".join(limited_windows(row, max_windows)),
                "strict_contract_windows_s": row["strict_contract_windows_s"],
                "strict_contract_windows_available": "true",
            }
        )
    preflight = sampler.source_preflight_rows(adapted)
    for row in preflight:
        row["native_solver_output_mutated"] = "false"
        row["preflight_basis"] = "current_coarse_continuation_direct_same_label"
    return preflight


def qoi_rows(window_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    units = {
        "Q_wall_W": "W",
        "mdot_exchange_positive_outward_proxy_kg_s": "kg/s",
        "tau_recirc_proxy_s": "s",
        "wall_core_bulk_temperature_contrast_K": "K",
    }
    formulas = {
        "Q_wall_W": "integral of sampled wallHeatFlux over trusted_wall faces; positive adds heat to recirculation CV fluid",
        "mdot_exchange_positive_outward_proxy_kg_s": "surface integral of max(rho * U dot n_outward, 0) over trusted exchange interface",
        "tau_recirc_proxy_s": "seeded recirculation CV volume divided by positive-outward exchange volumetric flow",
        "wall_core_bulk_temperature_contrast_K": "trusted-wall area-average T minus interface core-side area-average T",
    }
    for row in window_rows:
        for label in QOI_LABELS:
            out.append(
                {
                    "case_id": row["case_id"],
                    "mesh_label": row["mesh_level"],
                    "qoi_label": label,
                    "unit": units[label],
                    "value": sampler.qoi_value(row, label),
                    "formula_id": formulas[label],
                    "sign_convention": row.get("Q_wall_release_status", "positive_outward_exchange_positive_wall_heat_to_fluid"),
                    "time_window_s": row["time_window_s"],
                    "field_basis": "direct current-coarse staged OpenFOAM T/rho/U/wallHeatFlux at target-minus/target/target-plus windows",
                    "property_basis": "native rho field; cp/source/property release still closed",
                    "geometry_mask_id": row["mesh_mask_id"],
                    "source_path": row["processors_dir"],
                    "direct_same_label_coarse_admitted": "false",
                    "coarse_equivalence_admitted": "false",
                    "admission_status": "diagnostic_only_direct_coarse_sampled_residual_and_triplet_gates_pending",
                }
            )
    return out


def face_contract_rows(geometries: list[sampler.MeshGeometry], sampled: bool) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for geometry in geometries:
        for lane, face_rows in (
            ("exchange_interface", geometry.interface_rows),
            ("trusted_wall", geometry.wall_rows),
            ("cap_or_open_boundary", geometry.cap_rows),
        ):
            for item in face_rows:
                rows.append(
                    {
                        "case_id": geometry.case_id,
                        "mesh_label": geometry.mesh_level,
                        "cv_id": sampler.seed_case_id(geometry.case_id, geometry.mesh_level),
                        "endpoint_label": lane,
                        "patch_name": item.get("patch_name", ""),
                        "face_id": item.get("face_id", ""),
                        "owner_cell": item.get("owner", item.get("seed_owner_cell", "")),
                        "area_m2": item.get("area_m2", ""),
                        "area_vector_x_m2": item.get("area_vector_x_m2", ""),
                        "area_vector_y_m2": item.get("area_vector_y_m2", ""),
                        "area_vector_z_m2": item.get("area_vector_z_m2", ""),
                        "normal_convention": item.get("normal_convention", ""),
                        "positive_mdot_convention": "positive outward from seeded recirculation CV on exchange_interface",
                        "time_window_s": "sampled_target_windows" if sampled else "",
                        "field_time_s": "sampled_target_windows" if sampled else "",
                        "source_path": str(geometry.poly_mesh),
                        "direct_same_label_coarse_admitted": "false",
                    }
                )
    if rows:
        return rows
    return [
        {
            "case_id": "none",
            "mesh_label": "current_coarse_continuation",
            "cv_id": "",
            "endpoint_label": "",
            "patch_name": "",
            "face_id": "",
            "owner_cell": "",
            "area_m2": "",
            "area_vector_x_m2": "",
            "area_vector_y_m2": "",
            "area_vector_z_m2": "",
            "normal_convention": "",
            "positive_mdot_convention": "",
            "time_window_s": "",
            "field_time_s": "",
            "source_path": "",
            "direct_same_label_coarse_admitted": "false",
        }
    ]


def residual_shell_rows(case_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in case_rows:
        for qoi in ("Q_wall_W", "mdot_exchange_positive_outward_proxy_kg_s", "wall_core_bulk_temperature_contrast_K"):
            for term in (
                "Q_source_side_net_static_bc_W",
                "Q_wall_W",
                "mdot_throughflow_cp_deltaT_W",
                "storage_W",
                "other_named_losses_W",
                "R_E_unreleased",
            ):
                rows.append(
                    {
                        "case_id": row["case_id"],
                        "mesh_label": row["mesh_label"],
                        "cv_id": f"{row['case_id']}_{row['mesh_label']}",
                        "qoi_label": qoi,
                        "term_label": term,
                        "term_value": "",
                        "unit": "W" if term != "R_E_unreleased" else "W",
                        "positive_direction": "positive residual means source-side heat not owned by named same-basis lanes",
                        "time_window_s": row["target_time_window_s"],
                        "source_path": PREFLIGHT / "required_output_schema_contract.csv",
                        "residual_accounted": "false",
                        "release_allowed": "false",
                    }
                )
    return rows


def triplet_gate_shell_rows(case_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in case_rows:
        for qoi in QOI_LABELS:
            rows.append(
                {
                    "case_id": row["case_id"],
                    "qoi_label": qoi,
                    "coarse_value": "",
                    "medium_value": "",
                    "fine_value": "",
                    "coarse_mask_id": f"{row['case_id']}_{row['mesh_label']}",
                    "medium_mask_id": "",
                    "fine_mask_id": "",
                    "same_formula_units_sign": "false",
                    "time_window_equivalent": "false",
                    "field_property_basis_equivalent": "false",
                    "cv_residual_accounted": "false",
                    "direct_same_label_coarse_admitted": "false",
                    "formal_gci_ready": "false",
                    "admission_allowed": "false",
                }
            )
    return rows


def write_guardrails(out_dir: Path) -> None:
    write_csv(
        out_dir / "no_mutation_guardrails.csv",
        [
            {"guardrail": "native_solver_outputs_mutated", "value": "false"},
            {"guardrail": "registry_mutated", "value": "false"},
            {"guardrail": "scheduler_action", "value": "false"},
            {"guardrail": "fluid_or_external_repo_edited", "value": "false"},
            {"guardrail": "source_property_or_qwall_release", "value": "false"},
            {"guardrail": "production_harvest_allowed", "value": "false"},
            {"guardrail": "formal_gci_run_or_admitted", "value": "false"},
            {"guardrail": "candidate_freeze_or_final_score", "value": "false"},
            {"guardrail": "residual_absorbed_into_internal_nu", "value": "false"},
        ],
    )


def build(
    out_dir: Path = DEFAULT_OUT,
    *,
    contract_csv: Path = DEFAULT_CONTRACT,
    execute: bool = False,
    repair_staged_fields: bool = False,
    case_id: str = "",
    max_cases: int = 0,
    max_windows: int = 0,
    job_id: str = "local",
    write_closeout_docs: bool = True,
) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = selected_contract_rows(contract_csv, case_id=case_id, max_cases=max_cases)

    repair_manifest: list[dict[str, Any]] = []
    if repair_staged_fields:
        repair_manifest = repair_staging(out_dir)
    elif not (out_dir / "staging_repair_manifest.csv").exists():
        write_csv(
            out_dir / "staging_repair_manifest.csv",
            [
                {
                    "case_id": "not_run",
                    "window_s": "",
                    "field": "",
                    "source_field_path": "",
                    "source_field_exists": "",
                    "destination_field_path": "",
                    "destination_existed_before": "",
                    "destination_exists_after": "",
                    "bytes_after": "",
                    "copied": "false",
                    "skipped_reason": "repair_staging_not_requested",
                    "native_solver_output_mutated": "false",
                }
            ],
        )

    preflight = source_preflight_rows(rows, max_windows=max_windows)
    write_csv(out_dir / "source_preflight.csv", preflight)
    preflight_ready = all(row["preflight_status"] == "ready_for_compute_node_sampling" for row in preflight)

    geometries: list[sampler.MeshGeometry] = []
    geometry_summaries: list[dict[str, Any]] = []
    window_reductions: list[dict[str, Any]] = []
    qwall_details: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []

    if execute:
        for row in rows:
            adapted = {
                "case_id": row["case_id"],
                "mesh_level": row["mesh_label"],
                "source_root": str(ROOT / row["source_root"]),
                "processors_dir": str(ROOT / row["processors_dir"]),
                "fallback_terminal_candidate_windows_s": ";".join(limited_windows(row, max_windows)),
                "strict_contract_windows_s": row["strict_contract_windows_s"],
                "strict_contract_windows_available": "true",
            }
            try:
                geometry = sampler.build_mesh_geometry(adapted, out_dir)
                geometries.append(geometry)
                geometry_summaries.append(geometry.summary)
                for window in limited_windows(row, max_windows):
                    reduction, qwall_detail = sampler.sample_window(geometry, window, "same_label_current_coarse")
                    window_reductions.append(reduction)
                    qwall_details.extend(qwall_detail)
            except Exception as exc:  # pragma: no cover - exercised only during real extraction failures.
                errors.append(
                    {
                        "case_id": row["case_id"],
                        "mesh_label": row["mesh_label"],
                        "error_type": type(exc).__name__,
                        "error": str(exc),
                        "native_solver_output_mutated": "false",
                    }
                )

    sampled_qois = qoi_rows(window_reductions) if window_reductions else [
        {
            "case_id": row["case_id"],
            "mesh_label": row["mesh_label"],
            "qoi_label": qoi,
            "unit": "",
            "value": "",
            "formula_id": "",
            "sign_convention": "",
            "time_window_s": row["target_time_window_s"],
            "field_basis": "not_sampled",
            "property_basis": "not_sampled",
            "geometry_mask_id": f"{row['case_id']}_{row['mesh_label']}",
            "source_path": row["processors_dir"],
            "direct_same_label_coarse_admitted": "false",
            "coarse_equivalence_admitted": "false",
            "admission_status": "blocked_not_executed_or_no_sampled_rows",
        }
        for row in rows
        for qoi in QOI_LABELS
    ]

    write_csv(out_dir / "mesh_level_geometry_summary.csv", geometry_summaries or [{"case_id": "not_executed", "native_solver_output_mutated": "false"}])
    write_csv(out_dir / "coarse_window_reductions.csv", window_reductions or [{"case_id": "not_executed", "native_solver_output_mutated": "false"}])
    write_csv(out_dir / "coarse_qwall_detail_rows.csv", qwall_details or [{"case_id": "not_executed", "native_solver_output_mutated": "false"}])
    write_csv(out_dir / "s13_same_label_coarse_open_cv_face_contract.csv", face_contract_rows(geometries, sampled=bool(window_reductions)))
    write_csv(out_dir / "s13_same_label_coarse_open_cv_qoi_rows.csv", sampled_qois)
    write_csv(out_dir / "s13_same_label_coarse_open_cv_residual_ledger.csv", residual_shell_rows(rows))
    write_csv(out_dir / "s13_same_label_coarse_triplet_admission_gate.csv", triplet_gate_shell_rows(rows))
    write_csv(out_dir / "sampling_errors.csv", errors or [{"case_id": "none", "error_type": "", "error": "", "native_solver_output_mutated": "false"}])
    write_guardrails(out_dir)

    copied_count = sum(item.get("copied") == "true" for item in repair_manifest)
    summary = {
        "task": TASK_ID,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "decision": (
            "s13_coarse_open_cv_extraction_sampled_diagnostic_no_admission"
            if execute and window_reductions and not errors
            else "s13_coarse_open_cv_extraction_preflight_repaired_no_sampling_no_admission"
            if repair_staged_fields and not execute
            else "s13_coarse_open_cv_extraction_dry_preflight_no_admission"
        ),
        "job_id": job_id,
        "execute_mode": execute,
        "repair_staging": repair_staged_fields,
        "repair_rows_copied": copied_count,
        "source_contract_rows": len(rows),
        "preflight_rows": len(preflight),
        "preflight_ready_rows": sum(row["preflight_status"] == "ready_for_compute_node_sampling" for row in preflight),
        "preflight_ready_for_compute_node_sampling": preflight_ready,
        "geometry_rows": len(geometry_summaries),
        "window_reduction_rows": len(window_reductions),
        "qoi_rows": len(sampled_qois),
        "sampling_error_rows": 0 if errors and errors[0].get("case_id") == "none" else len(errors),
        "scheduler_action": False,
        "native_solver_outputs_mutated": False,
        "registry_mutated": False,
        "source_property_or_qwall_release": False,
        "production_harvest_allowed": False,
        "formal_gci_run_or_admitted": False,
        "candidate_freeze_or_final_score": False,
    }
    write_json(out_dir / "summary.json", summary)
    write_readme(out_dir, summary)
    if write_closeout_docs:
        write_closeout(out_dir, summary)
    return summary


def write_readme(out_dir: Path, summary: dict[str, Any]) -> None:
    text = f"""---
provenance:
  - {rel(PREFLIGHT / "coarse_case_window_contract.csv")}
  - {rel(PREFLIGHT / "coarse_source_staging_repair_contract.csv")}
tags: [s13, coarse, open-cv, extraction, diagnostic]
related:
  - {rel(PREFLIGHT / "README.md")}
task: {TASK_ID}
date: {DATE}
role: Implementer/Tester/Writer
type: work_product
status: complete
---
# S13 Coarse Open-CV Extraction

Decision: `{summary["decision"]}`.

This package repairs the staged target-minus field gap when requested and
prepares direct current-coarse open-CV outputs. Even if sampled rows exist, the
artifacts remain diagnostic until residual-complete and triplet admission gates
are passed by a later row.

Open first:

- `staging_repair_manifest.csv`
- `source_preflight.csv`
- `s13_same_label_coarse_open_cv_face_contract.csv`
- `s13_same_label_coarse_open_cv_qoi_rows.csv`
- `s13_same_label_coarse_open_cv_residual_ledger.csv`
- `s13_same_label_coarse_triplet_admission_gate.csv`
- `summary.json`

Do not use this package for formal GCI, production harvest, source/property
release, Qwall release, freeze, or final scoring.
"""
    (out_dir / "README.md").write_text(text, encoding="utf-8")


def write_closeout(out_dir: Path, summary: dict[str, Any]) -> None:
    changed = [
        rel(Path(__file__)),
        rel(ROOT / "tools/extract/test_s13_coarse_open_cv_extraction.py"),
        rel(out_dir / "README.md"),
        rel(out_dir / "staging_repair_manifest.csv"),
        rel(out_dir / "source_preflight.csv"),
        rel(out_dir / "s13_same_label_coarse_open_cv_face_contract.csv"),
        rel(out_dir / "s13_same_label_coarse_open_cv_qoi_rows.csv"),
        rel(out_dir / "s13_same_label_coarse_open_cv_residual_ledger.csv"),
        rel(out_dir / "s13_same_label_coarse_triplet_admission_gate.csv"),
        rel(out_dir / "summary.json"),
        rel(STATUS_PATH),
        rel(JOURNAL_PATH),
        rel(IMPORT_PATH),
    ]
    STATUS_PATH.parent.mkdir(parents=True, exist_ok=True)
    JOURNAL_PATH.parent.mkdir(parents=True, exist_ok=True)
    IMPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATUS_PATH.write_text(
        f"""---
provenance:
  - {rel(out_dir / "summary.json")}
  - {rel(out_dir / "staging_repair_manifest.csv")}
  - {rel(out_dir / "source_preflight.csv")}
tags: [s13, coarse, open-cv, extraction]
related:
  - {rel(out_dir / "README.md")}
task: {TASK_ID}
date: {DATE}
role: Implementer/Tester/Writer
type: status
status: complete
---
# {TASK_ID}

## Objective

Repair the staged current-coarse target-minus field gap and prepare direct S13
coarse open-CV extraction outputs without admission.

## Outcome

Decision: `{summary["decision"]}`. Repair rows copied: `{summary["repair_rows_copied"]}`.
Preflight-ready rows: `{summary["preflight_ready_rows"]}/{summary["preflight_rows"]}`.
QOI rows emitted: `{summary["qoi_rows"]}`.

## Changes Made

- Added `tools/extract/build_s13_coarse_open_cv_extraction.py`.
- Added `tools/extract/test_s13_coarse_open_cv_extraction.py`.
- Published `work_products/2026-07/2026-07-22/2026-07-22_s13_coarse_open_cv_extraction/`.
- If repair was requested, staged only the target-minus files listed in the preflight repair contract.

## Validation

- `python3.11 tools/extract/build_s13_coarse_open_cv_extraction.py --repair-staging --max-cases 3 --max-windows 1`: run when closeout requested.
- `python3.11 tools/extract/build_s13_coarse_open_cv_extraction.py --case-id salt_2 --max-windows 1`: dry smoke run when closeout requested.
- `python3.11 -m py_compile tools/extract/build_s13_coarse_open_cv_extraction.py tools/extract/test_s13_coarse_open_cv_extraction.py`: run when closeout requested.
- `python3.11 -m unittest tools.extract.test_s13_coarse_open_cv_extraction`: run when closeout requested.
- `python3.11 tools/agent/finish_task.py --task-id {TASK_ID} --json`: run when closeout requested.

## Remaining Blockers

- Formal GCI and admission still require full direct sampled coarse rows, a residual-complete open-CV ledger, and triplet admission.
- This row does not release source/property, Qwall, production harvest, or scores.

## Guardrails

No native-output mutation, registry mutation, Fluid/external/thesis edit,
source/property or Qwall release, production harvest, formal GCI/admission,
same-QOI UQ admission, scoring/freeze, endpoint proxy substitution, hidden
multiplier, or residual absorption occurred.
""",
        encoding="utf-8",
    )
    JOURNAL_PATH.write_text(
        f"""---
provenance:
  - {rel(PREFLIGHT / "coarse_source_staging_repair_contract.csv")}
  - {rel(out_dir / "summary.json")}
tags: [s13, coarse, open-cv, extraction]
related:
  - {rel(STATUS_PATH)}
  - {rel(out_dir / "README.md")}
task: {TASK_ID}
date: {DATE}
role: Implementer/Tester/Writer
type: journal
status: complete
---
# S13 Coarse Open-CV Extraction

Attempted: created the coarse extraction wrapper and repair path needed after
the scheduler preflight found missing target-minus staged fields.

Observed: the repair contract sources are the recorded June processors paths;
destination staging paths are the July current-coarse staging tree. Dry output
remains diagnostic and fail-closed unless native sampling is explicitly run.

Inferred: S13 can now move from evidence planning to direct coarse sampling,
but formal GCI remains downstream of residual and triplet gates.

Next useful actions: if the full `--execute` run was not performed, submit or
run it under the scheduler using the package command, then build the residual
ledger and triplet admission gate.
""",
        encoding="utf-8",
    )
    write_json(
        IMPORT_PATH,
        {
            "task": TASK_ID,
            "task_id": TASK_ID,
            "date": DATE,
            "changed_files": changed,
            "read_only_context": [
                rel(PREFLIGHT / "coarse_case_window_contract.csv"),
                rel(PREFLIGHT / "coarse_source_staging_repair_contract.csv"),
                rel(ROOT / "tools/extract/build_s13_upcomer_exchange_medium_fine_exact_label_sampler.py"),
            ],
            "native_solver_outputs_mutated": False,
            "registry_mutated": False,
            "scheduler_action": False,
            "external_fluid_edit": False,
            "source_property_or_qwall_release": False,
            "formal_gci_run_or_admitted": False,
            "candidate_freeze_or_final_score": False,
        },
    )


def main() -> dict[str, Any]:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract-csv", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--repair-staging", action="store_true")
    parser.add_argument("--case-id", default="")
    parser.add_argument("--max-cases", type=int, default=0)
    parser.add_argument("--max-windows", type=int, default=0)
    parser.add_argument("--job-id", default="local")
    args = parser.parse_args()
    summary = build(
        args.output_root,
        contract_csv=args.contract_csv,
        execute=args.execute,
        repair_staged_fields=args.repair_staging,
        case_id=args.case_id,
        max_cases=args.max_cases,
        max_windows=args.max_windows,
        job_id=args.job_id,
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return summary


if __name__ == "__main__":
    main()
