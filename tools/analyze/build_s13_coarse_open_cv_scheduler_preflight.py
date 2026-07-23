#!/usr/bin/env python3.11
"""Build the S13 coarse open-CV scheduler preflight package.

This row turns the current S13 coarse no-go evidence into a concrete extraction
handoff. It consumes only existing contracts and diagnostic S13 outputs. It
does not edit extractors, launch Slurm work, mutate native solver outputs, or
admit formal GCI evidence.
"""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TASK_ID = "TODO-S13-COARSE-OPEN-CV-SCHEDULER-PREFLIGHT-2026-07-22"
DATE = "2026-07-22"
SLUG = "s13_coarse_open_cv_scheduler_preflight"
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_s13_coarse_open_cv_scheduler_preflight"
STATUS_PATH = ROOT / f".agent/status/{DATE}_{TASK_ID}.md"
JOURNAL_PATH = ROOT / f".agent/journal/{DATE}/s13-coarse-open-cv-scheduler-preflight.md"
IMPORT_PATH = ROOT / f"imports/{DATE}_{SLUG}.json"

DIRECT = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_s13_direct_same_label_coarse_evidence"
STRICT = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_s13_strict_coarse_nogo_contract"
GEN = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_same_label_mesh_family_generation"
RESIDUAL = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_s13_residual_complete_open_cv_energy_balance_contract"
SAMPLER = ROOT / "tools/extract/build_s13_upcomer_exchange_medium_fine_exact_label_sampler.py"
SAMPLER_TEST = ROOT / "tools/extract/test_s13_upcomer_exchange_medium_fine_exact_label_sampler.py"

QOIS = [
    "Q_wall_W",
    "mdot_exchange_positive_outward_proxy_kg_s",
    "tau_recirc_proxy_s",
    "wall_core_bulk_temperature_contrast_K",
]


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
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


def require_inputs() -> None:
    required = [
        DIRECT / "summary.json",
        DIRECT / "compute_ready_extraction_contract.csv",
        STRICT / "replacement_coarse_dataset_contract.csv",
        GEN / "same_label_mesh_family_generated_rows.csv",
        RESIDUAL / "residual_equation_contract.csv",
        RESIDUAL / "case_residual_budget_skeleton.csv",
        SAMPLER,
        SAMPLER_TEST,
    ]
    missing = [rel(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("missing S13 preflight inputs: " + "; ".join(missing))


def boolish(value: object) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes", "pass"}


def case_window_rows() -> list[dict[str, Any]]:
    generated = read_csv(GEN / "same_label_mesh_family_generated_rows.csv")
    by_case: dict[str, dict[str, str]] = {}
    for row in generated:
        if row.get("mesh_level") != "current_coarse_continuation":
            continue
        by_case.setdefault(row["case_id"], row)

    rows: list[dict[str, Any]] = []
    for case_id in sorted(by_case):
        row = by_case[case_id]
        target_plus_dir = ROOT / row["target_plus_dir"]
        processors_dir = target_plus_dir.parent
        source_root = processors_dir.parent
        windows = [
            row["target_minus_time_window_s"],
            row["target_time_window_s"],
            row["target_plus_time_window_s"],
        ]
        required_fields: list[str] = []
        missing_fields: list[str] = []
        for window in windows:
            for field in ("T", "rho", "U", "wallHeatFlux"):
                field_path = processors_dir / window / field
                required_fields.append(rel(field_path))
                if not field_path.exists():
                    missing_fields.append(rel(field_path))
        required_paths = [
            source_root / "constant/polyMesh/points",
            source_root / "constant/polyMesh/faces",
            source_root / "constant/polyMesh/owner",
            source_root / "constant/polyMesh/neighbour",
            source_root / "constant/polyMesh/boundary",
            processors_dir / "constant/polyMesh/cellProcAddressing",
            processors_dir / "constant/polyMesh/faceProcAddressing",
            processors_dir / "constant/polyMesh/boundary",
        ]
        missing_paths = [rel(path) for path in required_paths if not path.exists()]
        cell_vtk = ROOT / row["cell_vtk"]
        ready = (
            target_plus_dir.exists()
            and processors_dir.exists()
            and cell_vtk.exists()
            and not missing_paths
            and not missing_fields
        )
        rows.append(
            {
                "case_id": case_id,
                "mesh_label": "current_coarse_continuation",
                "source_root": rel(source_root),
                "processors_dir": rel(processors_dir),
                "target_minus_time_window_s": row["target_minus_time_window_s"],
                "target_time_window_s": row["target_time_window_s"],
                "target_plus_time_window_s": row["target_plus_time_window_s"],
                "strict_contract_windows_s": ";".join(windows),
                "fallback_terminal_candidate_windows_s": ";".join(windows),
                "target_plus_dir": row["target_plus_dir"],
                "target_plus_dir_exists": b(target_plus_dir.exists()),
                "cell_vtk": row["cell_vtk"],
                "cell_vtk_exists": b(cell_vtk.exists()),
                "required_native_path_missing_count": len(missing_paths),
                "required_native_field_missing_count": len(missing_fields),
                "required_native_path_missing": ";".join(missing_paths[:12]),
                "required_native_field_missing": ";".join(missing_fields[:12]),
                "coarse_contract_ready_for_scheduler": b(ready),
                "preflight_status": "ready_for_scheduler_authorized_extraction" if ready else "blocked_missing_required_native_path",
                "native_solver_output_mutated": "false",
            }
        )
    return rows


def source_repair_contract(case_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for case_row in case_rows:
        source_processors_note = ROOT / case_row["source_root"] / "SOURCE_PROCESSORS64.txt"
        original_processors = ""
        if source_processors_note.exists():
            original_processors = source_processors_note.read_text(encoding="utf-8", errors="replace").strip()
        missing_fields = [field for field in case_row["required_native_field_missing"].split(";") if field]
        for destination in missing_fields:
            destination_path = ROOT / destination
            field = destination_path.name
            window = destination_path.parent.name
            original_field_path = Path(original_processors) / window / field if original_processors else Path()
            rows.append(
                {
                    "case_id": case_row["case_id"],
                    "mesh_label": case_row["mesh_label"],
                    "window_s": window,
                    "field": field,
                    "source_processors_note": rel(source_processors_note),
                    "source_processors_note_exists": b(source_processors_note.exists()),
                    "source_field_path": rel(original_field_path) if original_processors else "",
                    "source_field_exists": b(original_field_path.exists()) if original_processors else "false",
                    "destination_field_path": destination,
                    "destination_field_exists": b(destination_path.exists()),
                    "repair_operation": "stage_missing_target_minus_field_from_recorded_source_processors",
                    "scheduler_required": "false_if_copy_only_true_if_sampling_verification_runs",
                    "repair_allowed_in_this_row": "false",
                    "native_solver_output_mutated": "false",
                    "staging_mutation_required_before_extraction": "true",
                }
            )
    if rows:
        return rows
    return [
        {
            "case_id": "none",
            "mesh_label": "current_coarse_continuation",
            "window_s": "",
            "field": "",
            "source_processors_note": "",
            "source_processors_note_exists": "false",
            "source_field_path": "",
            "source_field_exists": "false",
            "destination_field_path": "",
            "destination_field_exists": "true",
            "repair_operation": "none_required",
            "scheduler_required": "false",
            "repair_allowed_in_this_row": "false",
            "native_solver_output_mutated": "false",
            "staging_mutation_required_before_extraction": "false",
        }
    ]


def required_output_schema_contract() -> list[dict[str, Any]]:
    replacement = read_csv(STRICT / "replacement_coarse_dataset_contract.csv")
    direct = {
        row["artifact_to_generate"]: row
        for row in read_csv(DIRECT / "compute_ready_extraction_contract.csv")
    }
    rows: list[dict[str, Any]] = []
    for row in replacement:
        action = direct.get(row["artifact"], {})
        rows.append(
            {
                "artifact": row["artifact"],
                "row_unit": row["row_unit"],
                "required_cases": row["required_cases"],
                "required_qois": row["required_qois"],
                "required_columns": row["required_columns"],
                "acceptance": row["acceptance"],
                "scheduler_needed": action.get("scheduler_needed", ""),
                "required_operation": action.get("required_operation", ""),
                "forbidden_substitution": row["forbidden_substitution"],
            }
        )
    return rows


def sampler_capability_map() -> list[dict[str, Any]]:
    source = SAMPLER.read_text(encoding="utf-8", errors="replace")

    def has(name: str) -> bool:
        return name in source

    return [
        {
            "capability": "source_preflight",
            "current_symbol_or_file": "source_preflight_rows",
            "present_in_existing_sampler": b(has("def source_preflight_rows")),
            "reuse_for_coarse": "yes_after_contract_adapter",
            "coarse_delta": "feed current-coarse source_root/processors_dir/windows instead of medium/fine sampling_command_contract.csv",
        },
        {
            "capability": "mesh_geometry_and_seeded_cv",
            "current_symbol_or_file": "build_mesh_geometry",
            "present_in_existing_sampler": b(has("def build_mesh_geometry")),
            "reuse_for_coarse": "yes",
            "coarse_delta": "run on current_coarse_continuation source roots and preserve coarse mesh_mask_id",
        },
        {
            "capability": "face_area_vectors_and_owner_cells",
            "current_symbol_or_file": "add_area_vector_columns;selected_face_area_vectors",
            "present_in_existing_sampler": b(has("def add_area_vector_columns") and has("def selected_face_area_vectors")),
            "reuse_for_coarse": "yes",
            "coarse_delta": "emit replacement face-contract columns including owner_cell and area_vector_* for coarse endpoints",
        },
        {
            "capability": "same-window_qoi_reduction",
            "current_symbol_or_file": "interface_reduction;qoi_rows;sample_window",
            "present_in_existing_sampler": b(
                has("def interface_reduction") and has("def qoi_rows") and has("def sample_window")
            ),
            "reuse_for_coarse": "yes_after_output_schema_mapping",
            "coarse_delta": "write s13_same_label_coarse_open_cv_qoi_rows.csv, not medium/fine diagnostic filenames",
        },
        {
            "capability": "residual_complete_open_cv_ledger",
            "current_symbol_or_file": "residual_equation_contract.csv",
            "present_in_existing_sampler": "false",
            "reuse_for_coarse": "no_new_join_stage_required",
            "coarse_delta": "join coarse Q_wall/exchange/throughflow/source/storage/named-loss terms after sampled QOI rows exist",
        },
        {
            "capability": "runtime_parameterization",
            "current_symbol_or_file": "CONTRACT_PACKAGE constant",
            "present_in_existing_sampler": b("CONTRACT_PACKAGE =" in source),
            "reuse_for_coarse": "blocked_until_adapter_or_parameterization",
            "coarse_delta": "add a coarse wrapper or parameterized --contract-csv/--output-root runner under a scheduler-authorized row",
        },
    ]


def implementation_delta() -> list[dict[str, Any]]:
    return [
        {
            "rank": 1,
            "delta": "create_coarse_sampling_command_contract",
            "owned_by_next_row": "TODO-S13-COARSE-OPEN-CV-EXTRACTION-SCHEDULER-2026-07-22",
            "detail": "materialize one row per Salt2/Salt3/Salt4 current-coarse case with source_root, processors_dir, strict_contract_windows_s, fallback_terminal_candidate_windows_s, case_id, mesh_level; first repair missing target-minus staged fields from SOURCE_PROCESSORS64 paths",
            "acceptance_signal": "coarse_case_window_contract.csv has 3 rows and all target-minus/target/target-plus T/rho/U/wallHeatFlux fields exist in the staged processors tree",
            "scheduler_required": "false",
        },
        {
            "rank": 2,
            "delta": "parameterize_or_wrap_existing_sampler",
            "owned_by_next_row": "TODO-S13-COARSE-OPEN-CV-EXTRACTION-SCHEDULER-2026-07-22",
            "detail": "reuse source_preflight_rows, build_mesh_geometry, add_area_vector_columns, interface_reduction, qoi_rows, and sample_window without changing medium/fine outputs",
            "acceptance_signal": "dry-run smoke for salt_2 max_windows=1 writes no native data and emits empty/no-admission gates",
            "scheduler_required": "false",
        },
        {
            "rank": 3,
            "delta": "run_scheduler_authorized_coarse_sampling",
            "owned_by_next_row": "TODO-S13-COARSE-OPEN-CV-EXTRACTION-SCHEDULER-2026-07-22",
            "detail": "sample T/rho/U/wallHeatFlux on target-minus, target, target-plus windows for Salt2/Salt3/Salt4 current coarse",
            "acceptance_signal": "face contract and 12 exact coarse QOI rows exist with finite values and direct-admission flags still governed by basis tests",
            "scheduler_required": "true",
        },
        {
            "rank": 4,
            "delta": "build_residual_ledger_after_sampling",
            "owned_by_next_row": "later residual-ledger row after coarse sampled outputs exist",
            "detail": "apply S13_OPEN_CV_RESIDUAL to same coarse masks/windows and keep release_allowed=false until all source/property/storage/named-loss terms pass",
            "acceptance_signal": "residual ledger rows name every term and expose missing lanes instead of hiding residual in internal Nu",
            "scheduler_required": "maybe",
        },
        {
            "rank": 5,
            "delta": "rerun_triplet_admission_gate",
            "owned_by_next_row": "later admission-gate row after coarse and residual artifacts exist",
            "detail": "join direct coarse rows to existing medium/fine exact-label rows by case, QOI, formula, sign, window role, property basis, and mask id",
            "acceptance_signal": "formal_gci_ready can become true only when every equivalence flag passes",
            "scheduler_required": "false",
        },
    ]


def scheduler_handoff(case_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ready_rows = sum(1 for row in case_rows if row["coarse_contract_ready_for_scheduler"] == "true")
    staging_first = "true" if ready_rows < len(case_rows) else "false"
    return [
        {
            "handoff_id": "s13_coarse_open_cv_extraction",
            "next_task_id": "TODO-S13-COARSE-OPEN-CV-EXTRACTION-SCHEDULER-2026-07-22",
            "submit_performed": "false",
            "scheduler_action_allowed_in_this_row": "false",
            "source_staging_repair_required_before_submit": staging_first,
            "case_rows_ready": ready_rows,
            "case_rows_total": len(case_rows),
            "recommended_accounting_mode": "sbatch_from_login_node",
            "expected_output_root": "work_products/2026-07/2026-07-22/2026-07-22_s13_coarse_open_cv_extraction",
            "exact_command_after_next_row_claim": (
                "cd /scratch/09748/andresfierro231/projects_scratch/ethan_runs && "
                "python3.11 tools/extract/build_s13_coarse_open_cv_extraction.py "
                "--execute --contract-csv "
                "work_products/2026-07/2026-07-22/2026-07-22_s13_coarse_open_cv_scheduler_preflight/"
                "coarse_case_window_contract.csv "
                "--output-root work_products/2026-07/2026-07-22/2026-07-22_s13_coarse_open_cv_extraction"
            ),
            "forbidden_until_next_row": "staging copy, sbatch submission, native mutation, extractor edit, production harvest, formal GCI, source/property release",
        }
    ]


def next_board_row() -> list[dict[str, Any]]:
    return [
        {
            "task_id": "TODO-S13-COARSE-OPEN-CV-EXTRACTION-SCHEDULER-2026-07-22",
            "role": "Hydraulics / Thermal-modeling / cfd-pp / Mesh-GCI / Implementer / Tester / Writer",
            "owner": "open",
            "allowed_edit_paths": (
                ".agent/BOARD.md own row; .agent/status/2026-07-22_TODO-S13-COARSE-OPEN-CV-EXTRACTION-SCHEDULER-2026-07-22.md; "
                ".agent/journal/2026-07-22/s13-coarse-open-cv-extraction-scheduler.md; "
                "imports/2026-07-22_s13_coarse_open_cv_extraction_scheduler.json; "
                "tools/extract/build_s13_coarse_open_cv_extraction.py; "
                "tools/extract/test_s13_coarse_open_cv_extraction.py; "
                "work_products/2026-07/2026-07-22/2026-07-22_s13_coarse_open_cv_extraction/**"
            ),
            "read_only_context": (
                "this preflight package; medium/fine exact-label sampler source/tests; strict coarse no-go contract; "
                "direct same-label coarse evidence; residual open-CV contract; native CFD/OpenFOAM outputs"
            ),
            "objective": "create/parameterize the coarse sampler, run scheduler-authorized coarse open-CV extraction, and emit direct coarse face/QOI artifacts without admission",
            "acceptance_signal": "first repair target-minus staging if needed; then finite coarse face vectors/owner cells and 12 direct coarse QOI rows exist; scheduler/job handoff documented; no formal GCI or release",
            "guardrails": "no native mutation, no registry mutation, no production harvest, no formal GCI/admission, no source/property or Qwall release, no residual absorption",
        }
    ]


def guardrails() -> list[dict[str, str]]:
    return [
        {"guardrail": "native_solver_outputs_mutated", "value": "false"},
        {"guardrail": "registry_mutated", "value": "false"},
        {"guardrail": "scheduler_action_performed", "value": "false"},
        {"guardrail": "solver_postprocessing_sampler_harvest_uq_launched", "value": "false"},
        {"guardrail": "extractor_source_edited", "value": "false"},
        {"guardrail": "fluid_or_external_repo_edited", "value": "false"},
        {"guardrail": "thesis_current_or_latex_edited", "value": "false"},
        {"guardrail": "source_property_or_qwall_release", "value": "false"},
        {"guardrail": "production_harvest_allowed", "value": "false"},
        {"guardrail": "formal_gci_run_or_admitted", "value": "false"},
        {"guardrail": "candidate_freeze_or_final_score", "value": "false"},
        {"guardrail": "residual_absorbed_into_internal_nu", "value": "false"},
    ]


def source_manifest() -> list[dict[str, Any]]:
    paths = [
        (DIRECT / "summary.json", "read-only direct coarse decision"),
        (DIRECT / "compute_ready_extraction_contract.csv", "read-only compute-ready coarse artifact contract"),
        (STRICT / "replacement_coarse_dataset_contract.csv", "read-only replacement schema contract"),
        (GEN / "same_label_mesh_family_generated_rows.csv", "read-only current coarse case/window/QOI rows"),
        (RESIDUAL / "residual_equation_contract.csv", "read-only open-CV residual formula"),
        (RESIDUAL / "case_residual_budget_skeleton.csv", "read-only residual completeness status"),
        (SAMPLER, "read-only medium/fine sampler capability source"),
        (SAMPLER_TEST, "read-only medium/fine sampler tests"),
    ]
    return [
        {
            "source_path": rel(path),
            "exists": b(path.exists()),
            "mutated": "false",
            "use": use,
        }
        for path, use in paths
    ]


def write_sbatch_handoff() -> None:
    script = """#!/bin/bash
#SBATCH -J s13_coarse_open_cv
#SBATCH -o work_products/2026-07/2026-07-22/2026-07-22_s13_coarse_open_cv_extraction/slurm-%j.out
#SBATCH -e work_products/2026-07/2026-07-22/2026-07-22_s13_coarse_open_cv_extraction/slurm-%j.err
#SBATCH -N 1
#SBATCH -n 1
#SBATCH -t 04:00:00

set -euo pipefail
cd /scratch/09748/andresfierro231/projects_scratch/ethan_runs
python3.11 tools/extract/build_s13_coarse_open_cv_extraction.py \
  --execute \
  --contract-csv work_products/2026-07/2026-07-22/2026-07-22_s13_coarse_open_cv_scheduler_preflight/coarse_case_window_contract.csv \
  --output-root work_products/2026-07/2026-07-22/2026-07-22_s13_coarse_open_cv_extraction
"""
    (OUT / "run_s13_coarse_open_cv_extraction.sbatch").write_text(script, encoding="utf-8")


def write_readme(summary: dict[str, Any]) -> None:
    readiness_sentence = (
        "The July staging bundle is ready for scheduler extraction."
        if summary["scheduler_ready_case_rows"] == summary["case_rows"]
        else "The July staging bundle needs the missing target-minus fields repaired from the recorded SOURCE_PROCESSORS64 paths before scheduler extraction."
    )
    text = f"""---
provenance:
  - {rel(DIRECT / "compute_ready_extraction_contract.csv")}
  - {rel(STRICT / "replacement_coarse_dataset_contract.csv")}
  - {rel(GEN / "same_label_mesh_family_generated_rows.csv")}
  - {rel(RESIDUAL / "residual_equation_contract.csv")}
tags: [s13, coarse, open-cv, scheduler-preflight, mesh-gci]
related:
  - {rel(DIRECT / "README.md")}
  - {rel(STRICT / "README.md")}
task: {TASK_ID}
date: {DATE}
role: Implementer/Tester/Writer
type: work_product
status: complete
---
# S13 Coarse Open-CV Scheduler Preflight

This package makes the next S13 unlock executable without admitting anything.
The current coarse rows are still diagnostic because direct same-label coarse
face geometry, exact coarse QOI rows, residual ledger rows, and a triplet
admission gate do not yet exist on the same basis.

Decision: `{summary["decision"]}`.

{readiness_sentence}

Open first:

- `coarse_case_window_preflight.csv`
- `coarse_case_window_contract.csv`
- `coarse_source_staging_repair_contract.csv`
- `required_output_schema_contract.csv`
- `existing_sampler_capability_map.csv`
- `implementation_delta.csv`
- `scheduler_handoff.csv`
- `next_board_row.csv`

Next task sequence:

1. Claim `TODO-S13-COARSE-OPEN-CV-EXTRACTION-SCHEDULER-2026-07-22`.
2. If `coarse_source_staging_repair_contract.csv` has rows, stage those missing
   target-minus fields from the recorded source processors paths.
3. Create or parameterize a coarse extractor using the existing medium/fine
   sampler capabilities.
4. Submit the scheduler-authorized extraction only after the extractor dry-run
   smoke passes.
5. Emit direct coarse face/QOI artifacts, still with no formal GCI or release.
6. Then build the residual ledger and triplet admission gate.

Do not do:

- Do not submit the bundled `sbatch` script from this preflight row.
- Do not perform the staging repair from this preflight row.
- Do not mutate native OpenFOAM outputs.
- Do not promote current reconstructed coarse candidates.
- Do not run formal GCI, production harvest, source/property release, or final
  scoring from this package.
- Do not hide an open-CV residual inside internal Nu or a fitted multiplier.
"""
    (OUT / "README.md").write_text(text, encoding="utf-8")


def write_closeout(summary: dict[str, Any], changed: list[Path]) -> None:
    STATUS_PATH.parent.mkdir(parents=True, exist_ok=True)
    JOURNAL_PATH.parent.mkdir(parents=True, exist_ok=True)
    IMPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    status = f"""---
provenance:
  - {rel(OUT / "summary.json")}
  - {rel(OUT / "coarse_case_window_preflight.csv")}
  - {rel(OUT / "scheduler_handoff.csv")}
tags: [s13, coarse, open-cv, scheduler-preflight]
related:
  - {rel(OUT / "README.md")}
task: {TASK_ID}
date: {DATE}
role: Implementer/Tester/Writer
type: status
status: complete
---
# {TASK_ID}

## Objective

Objective: prepare the next scheduler-authorized S13 coarse open-CV extraction
row by mapping current coarse cases/windows, required output schemas, reusable
sampler capabilities, implementation delta, and exact run handoff.

## Outcome

Outcome: `{summary["decision"]}`. Case preflight rows: `{summary["case_rows"]}`;
ready case rows: `{summary["scheduler_ready_case_rows"]}`; required output
artifacts: `{summary["required_artifact_rows"]}`; source-staging repair rows:
`{summary["source_staging_repair_rows"]}`; implementation deltas:
`{summary["implementation_delta_rows"]}`.

## Changes Made

Changed artifacts:

- {rel(OUT / "README.md")}
- {rel(OUT / "coarse_case_window_preflight.csv")}
- {rel(OUT / "coarse_case_window_contract.csv")}
- {rel(OUT / "coarse_source_staging_repair_contract.csv")}
- {rel(OUT / "required_output_schema_contract.csv")}
- {rel(OUT / "existing_sampler_capability_map.csv")}
- {rel(OUT / "implementation_delta.csv")}
- {rel(OUT / "scheduler_handoff.csv")}
- {rel(OUT / "next_board_row.csv")}
- {rel(OUT / "summary.json")}

## Validation

Validation run by closeout:

- `python3.11 tools/analyze/build_s13_coarse_open_cv_scheduler_preflight.py`
- `python3.11 -m py_compile tools/analyze/build_s13_coarse_open_cv_scheduler_preflight.py tools/analyze/test_s13_coarse_open_cv_scheduler_preflight.py`
- `python3.11 -m unittest tools.analyze.test_s13_coarse_open_cv_scheduler_preflight`
- `python3.11 tools/agent/finish_task.py --task-id {TASK_ID} --json`

## Remaining Blockers

Unresolved blockers:

- S13 remains unusable for formal GCI until direct same-label coarse face/QOI
  extraction is run under the next scheduler-authorized row.
- The immediate executable blocker is staging, not science: target-minus native
  fields are absent from the July staging tree but present in the recorded June
  source processors paths.
- Residual-complete open-CV evidence and same-QOI admission gates are still
  downstream of the coarse extraction.
- A broad open S11 trigger-gated board row claims optional `tools/analyze/`
  filenames only after exact filenames are claimed; this row used only its
  explicitly assigned S13 filenames.

## Guardrails

Guardrails: no native-output mutation, no registry mutation, no scheduler
action, no staging repair, no extractor-source edit, no Fluid/external/thesis edit, no
source/property or Qwall release, no production harvest, no formal GCI or
admission, no scoring/freeze, and no residual absorption into internal Nu.
"""
    STATUS_PATH.write_text(status, encoding="utf-8")

    journal = f"""---
provenance:
  - {rel(DIRECT / "compute_ready_extraction_contract.csv")}
  - {rel(STRICT / "replacement_coarse_dataset_contract.csv")}
  - {rel(GEN / "same_label_mesh_family_generated_rows.csv")}
  - {rel(OUT / "summary.json")}
tags: [s13, coarse, open-cv, scheduler-preflight]
related:
  - {rel(STATUS_PATH)}
  - {rel(OUT / "README.md")}
task: {TASK_ID}
date: {DATE}
role: Implementer/Tester/Writer
type: journal
status: complete
---
# S13 Coarse Open-CV Scheduler Preflight

Attempted: converted the completed S13 strict no-go and direct coarse evidence
packages into a concrete scheduler handoff for direct same-label coarse
sampling.

Observed: current coarse case/QOI values exist for Salt2, Salt3, and Salt4,
but they are reconstructed diagnostic rows. The next usable evidence must
produce direct coarse face area vectors/owner cells, exact coarse QOI rows,
an open-CV residual ledger, and a triplet gate.

Also observed: the July staged current-coarse processors contain target and
target-plus windows, but the target-minus windows are missing. The recorded
June source processors paths contain those target-minus field files, so the
next row can repair staging before launching extraction.

Inferred: the highest-value unlock is not another admission argument. It is a
scheduler-authorized coarse extraction that reuses the existing medium/fine
sampler's geometry, area-vector, and QOI-reduction logic on a coarse contract.

Caveats: this preflight did not execute the sampler, did not inspect heavy
native fields beyond path existence checks, and did not release any source,
property, Qwall, residual, GCI, or scoring value.

Next useful actions: claim
`TODO-S13-COARSE-OPEN-CV-EXTRACTION-SCHEDULER-2026-07-22`, create the coarse
extractor/wrapper, stage the target-minus fields listed in
`coarse_source_staging_repair_contract.csv`, run a dry smoke for `salt_2` with
one window, then submit the extraction by `sbatch` only after the smoke passes.
"""
    JOURNAL_PATH.write_text(journal, encoding="utf-8")

    manifest = {
        "task": TASK_ID,
        "task_id": TASK_ID,
        "date": DATE,
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "changed_files": [rel(path) for path in changed],
        "read_only_context": [row["source_path"] for row in source_manifest()],
        "native_solver_outputs_mutated": False,
        "registry_mutated": False,
        "scheduler_action": False,
        "scheduler_action_performed": False,
        "staging_repair_performed": False,
        "extractor_source_edited": False,
        "external_fluid_edit": False,
        "fluid_or_external_repo_edited": False,
        "thesis_current_or_latex_edited": False,
        "source_property_or_qwall_release": False,
        "production_harvest_allowed": False,
        "formal_gci_run_or_admitted": False,
        "candidate_freeze_or_final_score": False,
        "notes": (
            "Preflight-only S13 package. The bundled sbatch script is a handoff "
            "artifact for the next claimed row and was not submitted."
        ),
    }
    write_json(IMPORT_PATH, manifest)


def build() -> dict[str, Any]:
    require_inputs()
    OUT.mkdir(parents=True, exist_ok=True)

    case_rows = case_window_rows()
    schema_rows = required_output_schema_contract()
    capability_rows = sampler_capability_map()
    delta_rows = implementation_delta()
    repair_rows = source_repair_contract(case_rows)
    handoff_rows = scheduler_handoff(case_rows)
    next_rows = next_board_row()
    guardrail_rows = guardrails()
    manifest_rows = source_manifest()

    write_csv(OUT / "coarse_case_window_preflight.csv", case_rows)
    write_csv(OUT / "coarse_case_window_contract.csv", case_rows)
    write_csv(OUT / "coarse_source_staging_repair_contract.csv", repair_rows)
    write_csv(OUT / "required_output_schema_contract.csv", schema_rows)
    write_csv(OUT / "existing_sampler_capability_map.csv", capability_rows)
    write_csv(OUT / "implementation_delta.csv", delta_rows)
    write_csv(OUT / "scheduler_handoff.csv", handoff_rows)
    write_csv(OUT / "next_board_row.csv", next_rows)
    write_csv(OUT / "no_mutation_guardrails.csv", guardrail_rows)
    write_csv(OUT / "source_manifest.csv", manifest_rows)
    write_sbatch_handoff()

    summary = {
        "task": TASK_ID,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "decision": (
            "s13_coarse_open_cv_scheduler_preflight_ready_no_execution"
            if sum(row["coarse_contract_ready_for_scheduler"] == "true" for row in case_rows) == len(case_rows)
            else "s13_coarse_open_cv_scheduler_preflight_source_staging_repair_needed_no_execution"
        ),
        "case_rows": len(case_rows),
        "scheduler_ready_case_rows": sum(row["coarse_contract_ready_for_scheduler"] == "true" for row in case_rows),
        "qoi_rows_required": len(QOIS) * len(case_rows),
        "required_artifact_rows": len(schema_rows),
        "source_staging_repair_rows": len([row for row in repair_rows if row["repair_operation"] != "none_required"]),
        "source_staging_repair_source_fields_present": sum(row["source_field_exists"] == "true" for row in repair_rows),
        "sampler_reusable_capability_rows": len(capability_rows),
        "implementation_delta_rows": len(delta_rows),
        "scheduler_handoff_rows": len(handoff_rows),
        "next_board_row_ready": True,
        "scheduler_action": False,
        "native_solver_outputs_mutated": False,
        "extractor_source_edited": False,
        "source_property_or_qwall_release": False,
        "production_harvest_allowed": False,
        "formal_gci_run_or_admitted": False,
        "candidate_freeze_or_final_score": False,
    }
    write_json(OUT / "summary.json", summary)
    write_readme(summary)

    changed = [
        Path(__file__),
        ROOT / "tools/analyze/test_s13_coarse_open_cv_scheduler_preflight.py",
        OUT / "README.md",
        OUT / "coarse_case_window_preflight.csv",
        OUT / "coarse_case_window_contract.csv",
        OUT / "coarse_source_staging_repair_contract.csv",
        OUT / "required_output_schema_contract.csv",
        OUT / "existing_sampler_capability_map.csv",
        OUT / "implementation_delta.csv",
        OUT / "scheduler_handoff.csv",
        OUT / "next_board_row.csv",
        OUT / "no_mutation_guardrails.csv",
        OUT / "source_manifest.csv",
        OUT / "run_s13_coarse_open_cv_extraction.sbatch",
        OUT / "summary.json",
        STATUS_PATH,
        JOURNAL_PATH,
        IMPORT_PATH,
    ]
    write_closeout(summary, changed)
    return summary


def main() -> dict[str, Any]:
    summary = build()
    print(json.dumps(summary, indent=2, sort_keys=True))
    return summary


if __name__ == "__main__":
    main()
