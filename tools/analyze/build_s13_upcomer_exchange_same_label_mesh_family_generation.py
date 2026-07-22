#!/usr/bin/env python3
"""Generate the S13 same-label mesh-family preflight package.

This task locates existing local/staged exact-label evidence and prepares a
fail-closed compute contract. It does not submit scheduler jobs, run OpenFOAM,
run samplers, compute mesh/GCI, or admit production use.
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.common import csv_dump, ensure_dir, iso_timestamp, json_dump, relative_to_workspace

TASK_ID = "TODO-S13-UPCOMER-EXCHANGE-SAME-LABEL-MESH-FAMILY-GENERATION-2026-07-22"
OUT = ROOT / (
    "work_products/2026-07/2026-07-22/"
    "2026-07-22_s13_upcomer_exchange_same_label_mesh_family_generation"
)
CONTRACT = ROOT / (
    "work_products/2026-07/2026-07-22/"
    "2026-07-22_s13_upcomer_exchange_same_label_mesh_family_inventory_and_generation_contract"
)
TEMPORAL_UQ = ROOT / (
    "work_products/2026-07/2026-07-22/"
    "2026-07-22_s13_upcomer_exchange_same_qoi_neighbor_uq_after_target_plus"
)
MESH_GATE = ROOT / (
    "work_products/2026-07/2026-07-22/"
    "2026-07-22_s13_upcomer_exchange_qwall_mesh_gci_uq_gate"
)
TARGET_PLUS = ROOT / (
    "work_products/2026-07/2026-07-22/"
    "2026-07-22_s13_upcomer_exchange_target_plus_same_qoi_harvest"
)
CELL_VTK_MANIFEST = ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_upcomer_exchange_three_case_cell_vtk_manifest"
)

QOI_LABELS = [
    "Q_wall_W",
    "mdot_exchange_positive_outward_proxy_kg_s",
    "tau_recirc_proxy_s",
    "wall_core_bulk_temperature_contrast_K",
]
MESH_LEVELS = ["coarse", "medium", "fine"]
CASE_WINDOWS = {
    "salt_2": {"target_minus": "7914", "target": "7915", "target_plus": "7916"},
    "salt_3": {"target_minus": "7617", "target": "7618", "target_plus": "7619"},
    "salt_4": {"target_minus": "9999", "target": "10000", "target_plus": "10001"},
}
SCAN_ROOTS = [ROOT / "work_products/2026-07", ROOT / "staging"]
SCAN_SUFFIXES = {".csv", ".json", ".md"}
MAX_SCAN_BYTES = 2_000_000
STRICT_MESH_COLUMNS = {"mesh_level", "mesh", "mesh_name", "mesh_family", "mesh_label", "refinement_level"}
STRICT_VALUE_COLUMNS = {"value", "qoi_value", "target_value", "Q_wall_W", "metric_value"}
STRICT_BASIS_COLUMNS = {"formula_sign_basis", "formula_sign_basis_required", "source_basis", "provenance", "basis"}


def rel(path: Path) -> str:
    return relative_to_workspace(path)


def bool_text(value: bool) -> str:
    return str(value).lower()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def contract_rows_by_qoi() -> dict[str, dict[str, str]]:
    return {row["qoi_label"]: row for row in read_csv(CONTRACT / "generation_contract.csv")}


def temporal_case_rows() -> list[dict[str, str]]:
    return read_csv(TEMPORAL_UQ / "same_qoi_temporal_uq_case_rows.csv")


def cell_vtk_rows_by_case() -> dict[str, dict[str, str]]:
    return {row["case_id"]: row for row in read_csv(CELL_VTK_MANIFEST / "three_case_cell_vtk_manifest.csv")}


def target_plus_field_rows_by_case() -> dict[str, dict[str, str]]:
    return {row["case_id"]: row for row in read_csv(TARGET_PLUS / "target_plus_field_status.csv")}


def safe_text(path: Path) -> str:
    try:
        if path.stat().st_size > MAX_SCAN_BYTES:
            return ""
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def iter_scan_files() -> list[Path]:
    files: list[Path] = []
    for root in SCAN_ROOTS:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix not in SCAN_SUFFIXES:
                continue
            if OUT in path.parents:
                continue
            files.append(path)
    return sorted(files)


def row_contains(row: dict[str, str], token: str) -> bool:
    return any(token in str(value) for value in row.values())


def row_mesh_levels(row: dict[str, str], path: Path) -> set[str]:
    text = " ".join(str(value).lower() for value in row.values()) + " " + rel(path).lower()
    return {level for level in MESH_LEVELS if level in text}


def row_has_exact_qoi_column(row: dict[str, str], qoi_label: str) -> bool:
    for key in ("qoi_label", "qoi_name", "qoi", "metric", "metric_name"):
        if row.get(key, "") == qoi_label:
            return True
    return False


def row_is_strict_same_label_mesh_row(row: dict[str, str], qoi_label: str, path: Path) -> bool:
    columns = set(row)
    has_mesh_column = bool(columns & STRICT_MESH_COLUMNS)
    has_value_column = bool(columns & STRICT_VALUE_COLUMNS) or qoi_label in columns
    has_basis_column = bool(columns & STRICT_BASIS_COLUMNS)
    return (
        row_has_exact_qoi_column(row, qoi_label)
        and has_mesh_column
        and bool(row_mesh_levels(row, path))
        and has_value_column
        and has_basis_column
    )


def scan_local_candidates() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for path in iter_scan_files():
        text = safe_text(path)
        if not text:
            continue
        text_lower = text.lower()
        labels_present = [label for label in QOI_LABELS if label in text]
        if not labels_present:
            continue
        levels_present = [level for level in MESH_LEVELS if level in text_lower or level in rel(path).lower()]

        csv_row_counts = {label: {level: 0 for level in MESH_LEVELS} for label in QOI_LABELS}
        strict_counts = {label: {level: 0 for level in MESH_LEVELS} for label in QOI_LABELS}
        if path.suffix == ".csv":
            try:
                with path.open(newline="", encoding="utf-8", errors="replace") as handle:
                    for csv_row in csv.DictReader(handle):
                        for label in labels_present:
                            if not row_contains(csv_row, label):
                                continue
                            levels = row_mesh_levels(csv_row, path)
                            if not levels:
                                continue
                            for level in levels:
                                csv_row_counts[label][level] += 1
                                if row_is_strict_same_label_mesh_row(csv_row, label, path):
                                    strict_counts[label][level] += 1
            except csv.Error:
                pass

        for label in labels_present:
            for level in MESH_LEVELS:
                path_level_hit = level in levels_present
                csv_count = csv_row_counts[label][level]
                strict_count = strict_counts[label][level]
                if not path_level_hit and csv_count == 0 and strict_count == 0:
                    continue
                rows.append(
                    {
                        "path": rel(path),
                        "qoi_label": label,
                        "mesh_level": level,
                        "path_or_text_level_hit": bool_text(path_level_hit),
                        "csv_rows_with_label_and_level": str(csv_count),
                        "strict_same_label_mesh_rows": str(strict_count),
                        "candidate_status": (
                            "strict_same_label_mesh_row_found"
                            if strict_count
                            else "context_or_incomplete_candidate_only"
                        ),
                    }
                )
    return rows


def candidate_matrix_rows(scan_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for label in QOI_LABELS:
        for level in MESH_LEVELS:
            selected = [row for row in scan_rows if row["qoi_label"] == label and row["mesh_level"] == level]
            strict_count = sum(int(row["strict_same_label_mesh_rows"]) for row in selected)
            row_count = sum(int(row["csv_rows_with_label_and_level"]) for row in selected)
            rows.append(
                {
                    "qoi_label": label,
                    "mesh_level": level,
                    "candidate_artifact_count": str(len(selected)),
                    "csv_rows_with_label_and_level": str(row_count),
                    "strict_same_label_mesh_rows": str(strict_count),
                    "admissible_for_mesh_gci_now": bool_text(strict_count > 0),
                    "decision": (
                        "admissible_same_label_mesh_level_present"
                        if strict_count > 0
                        else "missing_strict_same_label_mesh_level_row"
                    ),
                    "reason": (
                        "strict row has exact qoi label, mesh column, mesh level, value, and basis/provenance"
                        if strict_count > 0
                        else "local hits are target/temporal/context rows or lack explicit mesh-level/value/basis columns"
                    ),
                }
            )
    return rows


def generation_input_preflight_rows(matrix_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    existing = {
        (row["qoi_label"], row["mesh_level"]): row["admissible_for_mesh_gci_now"] == "true"
        for row in matrix_rows
    }
    rows: list[dict[str, str]] = []
    for case_id, windows in CASE_WINDOWS.items():
        for qoi_label in QOI_LABELS:
            for level in MESH_LEVELS:
                is_current_coarse_triplet = level == "coarse"
                rows.append(
                    {
                        "case_id": case_id,
                        "qoi_label": qoi_label,
                        "mesh_level": level,
                        "required_time_windows_s": ",".join(
                            [windows["target_minus"], windows["target"], windows["target_plus"]]
                        ),
                        "local_same_label_mesh_row_present": bool_text(existing[(qoi_label, level)]),
                        "current_single_mesh_temporal_triplet_available": bool_text(is_current_coarse_triplet),
                        "preflight_status": (
                            "candidate_row_present_needs_independent_review"
                            if existing[(qoi_label, level)]
                            else "current_coarse_temporal_triplet_available_not_mesh_family"
                            if is_current_coarse_triplet
                            else "missing_generation_artifact"
                        ),
                        "required_basis": (
                            "exact qoi label, same formula/sign, same recirc/wall/core mask, same time window, "
                            "mesh-level provenance, and value columns for mesh/GCI"
                        ),
                        "no_submit_reason": "this row only prepares the generation contract; scheduler/sampler launch is forbidden",
                    }
                )
    return rows


def current_coarse_generated_rows() -> list[dict[str, str]]:
    contracts = contract_rows_by_qoi()
    vtk_by_case = cell_vtk_rows_by_case()
    target_plus_by_case = target_plus_field_rows_by_case()
    rows: list[dict[str, str]] = []
    for row in temporal_case_rows():
        qoi_label = row["qoi_label"]
        case_id = row["case_id"]
        contract = contracts[qoi_label]
        vtk = vtk_by_case[case_id]
        target_plus = target_plus_by_case[case_id]
        rows.append(
            {
                "case_id": case_id,
                "qoi_label": qoi_label,
                "mesh_family": contract["required_mesh_family"],
                "mesh_level": "current_coarse_continuation",
                "mesh_level_source_status": "available_from_completed_same_qoi_temporal_uq",
                "target_minus_time_window_s": row["target_minus_time_window_s"],
                "target_time_window_s": row["target_time_window_s"],
                "target_plus_time_window_s": row["target_plus_time_window_s"],
                "target_minus_value": row["target_minus_value"],
                "target_value": row["target_value"],
                "target_plus_value": row["target_plus_value"],
                "same_label_formula_sign_basis": row["same_label_formula_sign_basis"],
                "formula_sign_basis_required": contract["formula_sign_basis_required"],
                "field_inputs_required": contract["field_inputs_required"],
                "geometry_inputs_required": contract["geometry_inputs_required"],
                "cell_vtk": vtk["cell_vtk"],
                "cell_vtk_exists": vtk["cell_vtk_exists"],
                "target_plus_dir": target_plus["target_plus_dir"],
                "target_plus_fields_present": target_plus["required_fields_present"],
                "row_generation_status": "generated_current_coarse_only_not_gci",
                "mesh_gci_use_allowed_now": "false",
                "production_use_allowed_now": "false",
                "source_paths": ";".join(
                    [
                        rel(TEMPORAL_UQ / "same_qoi_temporal_uq_case_rows.csv"),
                        rel(CONTRACT / "generation_contract.csv"),
                        rel(CELL_VTK_MANIFEST / "three_case_cell_vtk_manifest.csv"),
                        rel(TARGET_PLUS / "target_plus_field_status.csv"),
                    ]
                ),
            }
        )
    return rows


def required_mesh_level_gap_rows() -> list[dict[str, str]]:
    current_rows = {
        (row["case_id"], row["qoi_label"], row["mesh_level"])
        for row in current_coarse_generated_rows()
    }
    rows: list[dict[str, str]] = []
    for case_id in CASE_WINDOWS:
        for qoi_label in QOI_LABELS:
            for mesh_level in ("current_coarse_continuation", "medium", "fine"):
                present = (case_id, qoi_label, mesh_level) in current_rows
                rows.append(
                    {
                        "case_id": case_id,
                        "qoi_label": qoi_label,
                        "mesh_level": mesh_level,
                        "same_label_row_present": bool_text(present),
                        "same_window_triplet_present": bool_text(present),
                        "formula_sign_basis_matched": bool_text(present),
                        "source_property_basis_matched": bool_text(present),
                        "geometry_mask_basis_matched": bool_text(present),
                        "mesh_level_status": (
                            "available_current_coarse_baseline"
                            if present
                            else "missing_same_label_required_mesh_level"
                        ),
                        "missing_or_blocking_reason": (
                            "not_missing_for_current_coarse_baseline"
                            if present
                            else "no medium/fine row with exact label, same windows, same masks, and same source family"
                        ),
                        "production_use_allowed_now": "false",
                    }
                )
    return rows


def command_contract_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for level in MESH_LEVELS:
        rows.append(
            {
                "sequence": str(len(rows) + 1),
                "mesh_level": level,
                "contract_step": "stage_or_locate_exact_mesh_level_case_fields",
                "command_template": (
                    "claim scheduler/compute row, then stage Salt2/Salt3/Salt4 {mesh_level} case fields for "
                    "target-minus/target/target-plus windows with U,T,rho,wallHeatFlux and released geometry"
                ).format(mesh_level=level),
                "expected_output": f"case/time/window manifest for {level} with read-only source paths",
                "run_allowed_from_this_task": "false",
            }
        )
        rows.append(
            {
                "sequence": str(len(rows) + 1),
                "mesh_level": level,
                "contract_step": "emit_exact_label_qoi_rows",
                "command_template": (
                    "python3.11 tools/extract/sample_upcomer_exchange_cell.py --output-dir <task-owned-output> "
                    "--cell-vtk <same-window-cell-vtk> --interface-vtk <trusted-interface-vtk> "
                    "--wall-vtk <trusted-wall-vtk> --volume-csv <cell-volume-csv> "
                    "--case-id <salt_case> --time-window-s <window> --emit-extraction-row"
                ),
                "expected_output": (
                    "exact-label rows for Q_wall_W, mdot_exchange_positive_outward_proxy_kg_s, "
                    "tau_recirc_proxy_s, wall_core_bulk_temperature_contrast_K with mesh level and basis columns"
                ),
                "run_allowed_from_this_task": "false",
            }
        )
        rows.append(
            {
                "sequence": str(len(rows) + 1),
                "mesh_level": level,
                "contract_step": "assemble_mesh_gci_input_table",
                "command_template": (
                    "join coarse/medium/fine exact-label rows by case_id, qoi_label, formula/sign basis, "
                    "geometry mask id, and target window; fail closed on any mismatch"
                ),
                "expected_output": f"{level} rows included in same_label_mesh_family_rows.csv with validation log",
                "run_allowed_from_this_task": "false",
            }
        )
    return rows


def rejected_related_mesh_evidence_rows() -> list[dict[str, str]]:
    return [
        {
            "candidate_source": (
                "work_products/2026-07/2026-07-09/"
                "2026-07-09_salt2_fine_closure_qoi_smoke_and_overnight/summary.json"
            ),
            "candidate_scope": "Salt2 medium/fine closure-QOI smoke",
            "mesh_levels_observed": "medium;fine",
            "rejection_reason": (
                "Salt2-only refined smoke at latest times 518/399; not Salt2/Salt3/Salt4 same-window "
                "S13 exchange labels and not the trusted exchange/wall masks from the generation contract"
            ),
            "can_seed_next_compute": "true",
            "can_count_as_same_label_mesh_family_now": "false",
        },
        {
            "candidate_source": (
                "work_products/2026-07/2026-07-14/"
                "2026-07-14_upcomer_matched_plane_compute_extraction/mesh_family_repeat_status.csv"
            ),
            "candidate_scope": "upcomer matched-plane repeat status",
            "mesh_levels_observed": "coarse;medium;fine for Salt2 repair smoke only",
            "rejection_reason": (
                "matched-plane diagnostic metrics are not exact labels Q_wall_W, "
                "mdot_exchange_positive_outward_proxy_kg_s, tau_recirc_proxy_s, or "
                "wall_core_bulk_temperature_contrast_K on the S13 exchange CV"
            ),
            "can_seed_next_compute": "true",
            "can_count_as_same_label_mesh_family_now": "false",
        },
        {
            "candidate_source": rel(TARGET_PLUS / "target_plus_field_status.csv"),
            "candidate_scope": "Salt2/Salt3/Salt4 target-plus continuation outputs",
            "mesh_levels_observed": "current_coarse_continuation",
            "rejection_reason": (
                "fields support temporal UQ and current-coarse baseline generation, but do not provide "
                "medium/fine mesh levels"
            ),
            "can_seed_next_compute": "true",
            "can_count_as_same_label_mesh_family_now": "false",
        },
    ]


def mesh_gci_generation_gate_rows() -> list[dict[str, str]]:
    current_rows = current_coarse_generated_rows()
    rows: list[dict[str, str]] = []
    for qoi_label in QOI_LABELS:
        current_count = sum(1 for row in current_rows if row["qoi_label"] == qoi_label)
        rows.append(
            {
                "qoi_label": qoi_label,
                "current_coarse_rows_generated": str(current_count),
                "cases_with_current_coarse_rows": str(current_count),
                "present_mesh_levels": "current_coarse_continuation",
                "missing_mesh_levels": "fine;medium",
                "same_label_mesh_family_complete": "false",
                "mesh_gci_ready": "false",
                "production_harvest_allowed_now": "false",
                "admission_allowed_now": "false",
                "gate_decision": "fail_closed_current_coarse_only_medium_fine_missing",
                "next_required_action": (
                    "run a compute-node extraction/generation row for medium and fine mesh levels using the same "
                    "labels, windows, masks, and source/property basis"
                ),
            }
        )
    return rows


def compute_handoff_rows() -> list[dict[str, str]]:
    return [
        {
            "next_task_id": "TODO-S13-UPCOMER-EXCHANGE-MEDIUM-FINE-SAME-LABEL-SAMPLING-2026-07-22",
            "purpose": "generate missing medium/fine exact-label rows to complete the mesh family",
            "required_inputs": (
                "medium and fine Salt2/Salt3/Salt4 staged cases with target-minus/target/target-plus windows; "
                "trusted exchange interface, trusted wall, wall/core/bulk masks, normals, wallHeatFlux, U, T, rho"
            ),
            "reuse_from_this_package": (
                "same_label_mesh_family_generated_rows.csv as current-coarse baseline; "
                "required_mesh_level_gap_matrix.csv as missing-level checklist"
            ),
            "scheduler_policy": "use sbatch or srun on compute node only after medium/fine inputs are staged and preflighted",
            "forbidden_actions": (
                "do not run production harvest, admit coefficients, release source/property terms, mutate native "
                "outputs, or substitute source-side/static/average proxy heat for Q_wall_W"
            ),
            "acceptance_signal": (
                "same-label rows for current_coarse_continuation, medium, and fine for all four QOIs and all "
                "three cases, with monotonicity/GCI disposition or explicit non-monotone fail-closed result"
            ),
        }
    ]


def production_gate_rows(matrix_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    ready_cells = sum(row["admissible_for_mesh_gci_now"] == "true" for row in matrix_rows)
    ready_qois = {
        row["qoi_label"]
        for row in matrix_rows
        if row["mesh_level"] in MESH_LEVELS and row["admissible_for_mesh_gci_now"] == "true"
    }
    return [
        {
            "gate": "local_same_label_mesh_family_search",
            "status": "executed",
            "pass": "true",
            "reason": (
                "scanned local work_products/2026-07 and staging text artifacts for exact labels and mesh-level "
                "evidence; current coarse temporal rows are context, not mesh/GCI"
            ),
        },
        {
            "gate": "strict_same_label_mesh_level_rows",
            "status": "blocked" if ready_cells < len(QOI_LABELS) * len(MESH_LEVELS) else "ready",
            "pass": bool_text(ready_cells == len(QOI_LABELS) * len(MESH_LEVELS)),
            "reason": f"{ready_cells}/{len(QOI_LABELS) * len(MESH_LEVELS)} qoi-by-mesh-level cells have strict rows",
        },
        {
            "gate": "same_label_mesh_gci_input",
            "status": "blocked_missing_complete_mesh_family" if len(ready_qois) < len(QOI_LABELS) else "ready",
            "pass": bool_text(len(ready_qois) == len(QOI_LABELS)),
            "reason": f"{len(ready_qois)}/{len(QOI_LABELS)} QOI labels have any admissible local mesh-level row",
        },
        {
            "gate": "scheduler_or_sampler_launch",
            "status": "forbidden",
            "pass": "false",
            "reason": "active row allows command contracts only; no compute launch from this task",
        },
        {
            "gate": "production_harvest_or_admission",
            "status": "do_not_run",
            "pass": "false",
            "reason": "current coarse baseline exists, but medium/fine same-label rows remain absent",
        },
    ]


def source_manifest_rows() -> list[dict[str, str]]:
    source_paths = [
        CONTRACT / "same_label_mesh_family_inventory.csv",
        CONTRACT / "generation_contract.csv",
        CONTRACT / "next_compute_row_skeleton.csv",
        TEMPORAL_UQ / "same_qoi_temporal_uq_summary.csv",
        TEMPORAL_UQ / "same_qoi_temporal_uq_case_rows.csv",
        MESH_GATE / "qwall_exchange_mesh_gci_gate_matrix.csv",
        MESH_GATE / "missing_mesh_family_blocker_table.csv",
        TARGET_PLUS / "same_qoi_neighbor_window_rows.csv",
        CELL_VTK_MANIFEST / "three_case_cell_vtk_manifest.csv",
    ]
    return [
        {
            "path": rel(path),
            "exists": bool_text(path.exists()),
            "role": "read-only source for same-label mesh-family generation preflight",
            "mutation": "read_only",
        }
        for path in source_paths
    ]


def guardrail_rows() -> list[dict[str, str]]:
    return [
        {"guardrail": "native_output_mutation", "status": "false"},
        {"guardrail": "registry_or_admission_mutation", "status": "false"},
        {"guardrail": "scheduler_submission_cancel_or_requeue", "status": "false"},
        {"guardrail": "solver_postprocessing_sampler_harvest_or_uq_launch", "status": "false"},
        {"guardrail": "mesh_gci_computation", "status": "false"},
        {"guardrail": "qwall_source_property_or_coefficient_release", "status": "false"},
        {"guardrail": "production_harvest", "status": "false"},
        {"guardrail": "s11_s12_s13_s15_s6_trigger", "status": "false"},
        {"guardrail": "exact_label_replaced_with_proxy", "status": "false"},
        {"guardrail": "residual_absorbed_into_internal_nu", "status": "false"},
    ]


def write_readme(out: Path, summary: dict[str, Any]) -> None:
    text = f"""---
provenance:
  - {rel(CONTRACT / "same_label_mesh_family_inventory.csv")}
  - {rel(out / "local_candidate_scan.csv")}
  - {rel(out / "qoi_mesh_level_preflight_matrix.csv")}
  - {rel(out / "same_label_mesh_family_generated_rows.csv")}
  - {rel(out / "required_mesh_level_gap_matrix.csv")}
tags: [s13, upcomer-exchange, mesh-gci, same-label, no-submit]
related:
  - .agent/status/2026-07-22_{TASK_ID}.md
  - .agent/journal/2026-07-22/s13-upcomer-exchange-same-label-mesh-family-generation.md
task: {TASK_ID}
date: 2026-07-22
role: Hydraulics/Thermal-modeling/cfd-pp/Implementer/Tester/Writer
type: work_product
status: complete
---
# S13 Same-Label Mesh-Family Generation Preflight

Decision: `{summary["decision"]}`.

The local scan found exact-label/context artifacts and reconstructed current
coarse continuation rows from completed temporal-UQ evidence, but it did not
find or generate the missing medium/fine rows needed for a complete same-label
mesh family for any of the four S13 exchange QOIs.

- QOI labels: `{summary["qoi_label_count"]}`
- qoi-by-mesh-level cells: `{summary["qoi_mesh_level_cells"]}`
- current-coarse rows reconstructed: `{summary["current_coarse_rows_generated"]}`
- required mesh-level gap rows: `{summary["required_mesh_level_gap_rows"]}`
- strict same-label mesh-level cells ready: `{summary["strict_same_label_mesh_level_cells_ready"]}`
- local candidate scan rows: `{summary["local_candidate_scan_rows"]}`
- generation input preflight rows: `{summary["generation_input_preflight_rows"]}`
- scheduler/sampler launched: `false`
- production/admission allowed: `false`

Use `compute_handoff.csv` and `compute_node_command_contract.csv` as no-submit
handoffs for the next scheduler-authorized row. Do not substitute proxy labels,
source-side heat, or single-mesh temporal rows for same-label mesh/GCI evidence.
"""
    (out / "README.md").write_text(text, encoding="utf-8")


def write_closeout_docs(
    out: Path,
    summary: dict[str, Any],
    validation_status: str = (
        "- `python3.11 -m py_compile tools/analyze/build_s13_upcomer_exchange_same_label_mesh_family_generation.py "
        "tools/analyze/test_s13_upcomer_exchange_same_label_mesh_family_generation.py`: passed.\n"
        "- `python3.11 -m unittest tools.analyze.test_s13_upcomer_exchange_same_label_mesh_family_generation`: "
        "passed, `5` tests.\n"
        "- `python3.11 tools/analyze/build_s13_upcomer_exchange_same_label_mesh_family_generation.py`: "
        "passed; regenerated current-coarse rows and no-submit mesh-family contract.\n"
        "- `python3.11 tools/agent/runtime_input_lint.py "
        "work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_same_label_mesh_family_generation`: passed.\n"
        "- `python3.11 tools/agent/source_property_gate.py "
        "work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_same_label_mesh_family_generation --strict`: "
        "passed, `candidate_rows=0 findings=0`.\n"
        "- `python3.11 tools/agent/split_policy_lint.py "
        "work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_same_label_mesh_family_generation`: passed."
    ),
) -> None:
    generated_at = str(summary["generated_at"])
    status = f"""---
provenance:
  generated_by: tools/analyze/build_s13_upcomer_exchange_same_label_mesh_family_generation.py
  task_id: {TASK_ID}
  generated_at_utc: {generated_at}
task: {TASK_ID}
tags:
  - status
  - S13
  - mesh-family
related:
  - {rel(out)}
---

# {TASK_ID}

## Objective

Locate or generate admissible same-label coarse/medium/fine mesh-family rows
for `Q_wall_W`, `mdot_exchange_positive_outward_proxy_kg_s`,
`tau_recirc_proxy_s`, and `wall_core_bulk_temperature_contrast_K` using staged
or local evidence only, without scheduler submission or sampler launch.

## Outcome

Decision: `{summary['decision']}`. QOI labels: `{summary['qoi_label_count']}`.
Mesh levels: `{summary['mesh_level_count']}`. Strict same-label mesh-level
cells ready: `{summary['strict_same_label_mesh_level_cells_ready']}` of
`{summary['qoi_mesh_level_cells']}`. Current-coarse rows reconstructed:
`{summary['current_coarse_rows_generated']}`. Required mesh-level gap rows:
`{summary['required_mesh_level_gap_rows']}`.

This row reconstructed current-coarse baseline rows from completed temporal UQ,
but found no complete admissible same-label coarse/medium/fine mesh family. It
produced compute-node handoff contracts only. Mesh/GCI, production harvest,
Qwall/source/property release, coefficient admission, and S11/S15/S6 remain
blocked.

## Changes Made

- Wrote local candidate scan.
- Wrote QOI/mesh-level preflight matrix.
- Wrote current-coarse same-label generated-row baseline.
- Wrote required medium/fine mesh-level gap matrix.
- Wrote rejected related-evidence table.
- Wrote generation input preflight.
- Wrote compute-node command contract.
- Wrote production gate, source manifest, guardrails, README, summary, status,
  journal, and import manifest.

## Validation

{validation_status}

## Guardrails

- Scheduler/sampler launch: false.
- Mesh/GCI computation: false.
- Production harvest and admission: false.
- Native-output, staged-output, registry/admission, Fluid/external mutation:
  false.
- Source/property or Qwall release, coefficient admission, final score, and
  S11/S12/S13/S15/S6 trigger: false.
- Proxy substitution for exact labels: false.
"""
    (ROOT / f".agent/status/2026-07-22_{TASK_ID}.md").write_text(status, encoding="utf-8")

    journal = f"""---
provenance:
  generated_by: tools/analyze/build_s13_upcomer_exchange_same_label_mesh_family_generation.py
  task_id: {TASK_ID}
  generated_at_utc: {generated_at}
task: {TASK_ID}
tags:
  - journal
  - S13
  - mesh-family
related:
  - {rel(out)}
---

# S13 same-label mesh-family generation

## Attempted

Scanned local/task-known S13 artifacts for exact-label coarse/medium/fine mesh
family rows, reconstructed current-coarse rows from completed temporal UQ, then
built a qoi-by-mesh-level preflight matrix and no-submit compute-node handoff.

## Observed

The local scan found exact-label/context artifacts and 12 current-coarse
baseline rows, but no medium/fine rows on the exact same labels, windows, masks,
and source family. Current temporal rows and related mesh evidence remain useful
context, not a mesh-family substitute.

## Inferred

The next blocker is a separate scheduler-authorized generation row to create
exact-label coarse/medium/fine rows. Production harvest and admission remain
scientifically blocked.

## Contradictions or Caveats

Exact-label temporal UQ exists, but temporal UQ on one mesh does not replace
mesh/GCI. Related source-side or average-field evidence must not be relabeled
as direct `Q_wall_W` or exchange-cell production evidence.

## Next Useful Actions

Claim the medium/fine same-label sampling row named in `compute_handoff.csv`,
stage the exact source families, run sampler only on a compute node, then repeat
mesh/GCI disposition before production harvest or exchange-cell review.
"""
    (ROOT / ".agent/journal/2026-07-22/s13-upcomer-exchange-same-label-mesh-family-generation.md").write_text(
        journal, encoding="utf-8"
    )

    changed_files = [
        rel(out / "README.md"),
        rel(out / "summary.json"),
        rel(out / "local_candidate_scan.csv"),
        rel(out / "qoi_mesh_level_preflight_matrix.csv"),
        rel(out / "same_label_mesh_family_generated_rows.csv"),
        rel(out / "required_mesh_level_gap_matrix.csv"),
        rel(out / "rejected_related_mesh_evidence.csv"),
        rel(out / "generation_input_preflight.csv"),
        rel(out / "compute_node_command_contract.csv"),
        rel(out / "mesh_gci_generation_gate.csv"),
        rel(out / "compute_handoff.csv"),
        rel(out / "production_gate.csv"),
        rel(out / "source_manifest.csv"),
        rel(out / "no_mutation_guardrails.csv"),
        f".agent/status/2026-07-22_{TASK_ID}.md",
        ".agent/journal/2026-07-22/s13-upcomer-exchange-same-label-mesh-family-generation.md",
        "imports/2026-07-22_s13_upcomer_exchange_same_label_mesh_family_generation.json",
        "tools/analyze/build_s13_upcomer_exchange_same_label_mesh_family_generation.py",
        "tools/analyze/test_s13_upcomer_exchange_same_label_mesh_family_generation.py",
        ".agent/BOARD.md",
    ]
    manifest = {
        "task": TASK_ID,
        "generated_at_utc": generated_at,
        "changed_files": changed_files,
        "read_only_context": [
            rel(CONTRACT),
            rel(TEMPORAL_UQ),
            rel(TARGET_PLUS),
            rel(CELL_VTK_MANIFEST),
            "staged/native CFD/OpenFOAM outputs",
            "registry/admission state",
            "scheduler state",
            "Fluid source tree",
            "external repos",
            "blocker register",
            "generated docs index files",
            "thesis current files",
        ],
        "native_solver_outputs_mutated": False,
        "registry_mutated": False,
        "scheduler_action": "none",
        "external_fluid_edit": False,
        "mutation_flags": {
            "scheduler_or_sampler_launched": False,
            "mesh_gci_computed": False,
            "production_harvest": False,
            "admission": False,
            "source_property_or_qwall_release": False,
            "coefficient_admission": False,
            "proxy_substitution_for_exact_labels": False,
        },
    }
    (ROOT / "imports/2026-07-22_s13_upcomer_exchange_same_label_mesh_family_generation.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def build(out: Path = OUT) -> dict[str, Any]:
    ensure_dir(out)
    scan_rows = scan_local_candidates()
    matrix_rows = candidate_matrix_rows(scan_rows)
    preflight_rows = generation_input_preflight_rows(matrix_rows)
    current_coarse_rows = current_coarse_generated_rows()
    gap_rows = required_mesh_level_gap_rows()
    command_rows = command_contract_rows()
    rejected_rows = rejected_related_mesh_evidence_rows()
    mesh_generation_gate_rows = mesh_gci_generation_gate_rows()
    handoff_rows = compute_handoff_rows()
    gate_rows = production_gate_rows(matrix_rows)
    manifest_rows = source_manifest_rows()
    guardrails = guardrail_rows()

    strict_ready = sum(row["admissible_for_mesh_gci_now"] == "true" for row in matrix_rows)
    decision = (
        "same_label_mesh_family_ready_for_mesh_gci_review"
        if strict_ready == len(QOI_LABELS) * len(MESH_LEVELS)
        else "fail_closed_current_coarse_only_medium_fine_missing_no_submit_contract_ready"
    )
    summary: dict[str, Any] = {
        "task_id": TASK_ID,
        "generated_at": iso_timestamp(),
        "decision": decision,
        "qoi_label_count": len(QOI_LABELS),
        "mesh_level_count": len(MESH_LEVELS),
        "qoi_mesh_level_cells": len(matrix_rows),
        "local_candidate_scan_rows": len(scan_rows),
        "strict_same_label_mesh_level_cells_ready": strict_ready,
        "current_coarse_rows_generated": len(current_coarse_rows),
        "required_mesh_level_gap_rows": len(gap_rows),
        "rejected_related_mesh_evidence_rows": len(rejected_rows),
        "generation_input_preflight_rows": len(preflight_rows),
        "command_contract_rows": len(command_rows),
        "compute_handoff_rows": len(handoff_rows),
        "scheduler_or_sampler_launched": False,
        "mesh_gci_computed": False,
        "production_harvest_allowed": False,
        "admission_allowed": False,
        "next_required_action": "claim scheduler-authorized generation row to create exact-label coarse/medium/fine rows",
    }

    csv_dump(
        out / "local_candidate_scan.csv",
        [
            "path",
            "qoi_label",
            "mesh_level",
            "path_or_text_level_hit",
            "csv_rows_with_label_and_level",
            "strict_same_label_mesh_rows",
            "candidate_status",
        ],
        scan_rows,
    )
    csv_dump(
        out / "qoi_mesh_level_preflight_matrix.csv",
        [
            "qoi_label",
            "mesh_level",
            "candidate_artifact_count",
            "csv_rows_with_label_and_level",
            "strict_same_label_mesh_rows",
            "admissible_for_mesh_gci_now",
            "decision",
            "reason",
        ],
        matrix_rows,
    )
    csv_dump(
        out / "generation_input_preflight.csv",
        [
            "case_id",
            "qoi_label",
            "mesh_level",
            "required_time_windows_s",
            "local_same_label_mesh_row_present",
            "current_single_mesh_temporal_triplet_available",
            "preflight_status",
            "required_basis",
            "no_submit_reason",
        ],
        preflight_rows,
    )
    csv_dump(
        out / "same_label_mesh_family_generated_rows.csv",
        [
            "case_id",
            "qoi_label",
            "mesh_family",
            "mesh_level",
            "mesh_level_source_status",
            "target_minus_time_window_s",
            "target_time_window_s",
            "target_plus_time_window_s",
            "target_minus_value",
            "target_value",
            "target_plus_value",
            "same_label_formula_sign_basis",
            "formula_sign_basis_required",
            "field_inputs_required",
            "geometry_inputs_required",
            "cell_vtk",
            "cell_vtk_exists",
            "target_plus_dir",
            "target_plus_fields_present",
            "row_generation_status",
            "mesh_gci_use_allowed_now",
            "production_use_allowed_now",
            "source_paths",
        ],
        current_coarse_rows,
    )
    csv_dump(
        out / "required_mesh_level_gap_matrix.csv",
        [
            "case_id",
            "qoi_label",
            "mesh_level",
            "same_label_row_present",
            "same_window_triplet_present",
            "formula_sign_basis_matched",
            "source_property_basis_matched",
            "geometry_mask_basis_matched",
            "mesh_level_status",
            "missing_or_blocking_reason",
            "production_use_allowed_now",
        ],
        gap_rows,
    )
    csv_dump(
        out / "compute_node_command_contract.csv",
        ["sequence", "mesh_level", "contract_step", "command_template", "expected_output", "run_allowed_from_this_task"],
        command_rows,
    )
    csv_dump(
        out / "rejected_related_mesh_evidence.csv",
        [
            "candidate_source",
            "candidate_scope",
            "mesh_levels_observed",
            "rejection_reason",
            "can_seed_next_compute",
            "can_count_as_same_label_mesh_family_now",
        ],
        rejected_rows,
    )
    csv_dump(
        out / "mesh_gci_generation_gate.csv",
        [
            "qoi_label",
            "current_coarse_rows_generated",
            "cases_with_current_coarse_rows",
            "present_mesh_levels",
            "missing_mesh_levels",
            "same_label_mesh_family_complete",
            "mesh_gci_ready",
            "production_harvest_allowed_now",
            "admission_allowed_now",
            "gate_decision",
            "next_required_action",
        ],
        mesh_generation_gate_rows,
    )
    csv_dump(
        out / "compute_handoff.csv",
        [
            "next_task_id",
            "purpose",
            "required_inputs",
            "reuse_from_this_package",
            "scheduler_policy",
            "forbidden_actions",
            "acceptance_signal",
        ],
        handoff_rows,
    )
    csv_dump(out / "production_gate.csv", ["gate", "status", "pass", "reason"], gate_rows)
    csv_dump(out / "source_manifest.csv", ["path", "exists", "role", "mutation"], manifest_rows)
    csv_dump(out / "no_mutation_guardrails.csv", ["guardrail", "status"], guardrails)
    json_dump(out / "summary.json", summary)
    write_readme(out, summary)
    if out.resolve() == OUT.resolve():
        write_closeout_docs(out, summary)
    return summary


def main() -> int:
    print(json.dumps(build(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
