#!/usr/bin/env python3
"""Compute Salt1 PASSIVE-H2 source-family areas directly from polyMesh."""

from __future__ import annotations

import csv
import json
import math
import re
from pathlib import Path


TASK_ID = "TODO-PASSIVE-H2-SALT1-MESH-AREA-PROVENANCE-REPAIR-PREFLIGHT-2026-07-22"
DATE = "2026-07-22"
REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "work_products/2026-07/2026-07-22/2026-07-22_passive_h2_salt1_mesh_area_provenance_repair_preflight"

CASE_ROOT = REPO / "jadyn_runs/modern_runs/2026-07-08_salt1_nominal_continuation_candidate/runs/salt1_jin_nominal_continuation_corrected/case_stage/viscosity_screening_salt_test_1_jin_coarse_mesh_continuation"
POLYMESH = CASE_ROOT / "constant/polyMesh"
BOUNDARY = POLYMESH / "boundary"
POINTS = POLYMESH / "points"
FACES = POLYMESH / "faces"
T0 = CASE_ROOT / "0/T"

JUNCTION_PACKAGE = REPO / "work_products/2026-07/2026-07-22/2026-07-22_passive_h2_salt1_junction_setup_row_recovery_background"
SOURCE_ENVELOPE_PACKAGE = REPO / "work_products/2026-07/2026-07-22/2026-07-22_salt1_branch_source_envelope_recovery"
PREVIOUS_RECOVERY = REPO / "work_products/2026-07/2026-07-21/2026-07-21_salt1_train_external_bc_recovery_freeze_gate"

OPERATOR_ROWS = JUNCTION_PACKAGE / "salt1_five_family_operator_rows_for_fluid.csv"
JUNCTION_PATCH_ROWS = JUNCTION_PACKAGE / "salt1_junction_patch_inventory.csv"
RECOVERY_ROWS = PREVIOUS_RECOVERY / "salt1_external_bc_recovery_rows.csv"
SOURCE_ENVELOPE_GATE = SOURCE_ENVELOPE_PACKAGE / "salt1_source_envelope_gate_matrix.csv"

AREA_ABS_TOL_M2 = 2.0e-10
AREA_REL_TOL = 2.0e-8


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8", errors="replace") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({name: row.get(name, "") for name in fieldnames})


def parse_boundary(path: Path) -> dict[str, dict[str, int]]:
    text = path.read_text(encoding="utf-8", errors="replace")
    matches = re.finditer(
        r"^\s*(?P<name>[A-Za-z0-9_]+)\s*\{\s*.*?^\s*nFaces\s+(?P<nfaces>\d+);\s*^\s*startFace\s+(?P<start>\d+);",
        text,
        flags=re.M | re.S,
    )
    return {
        match.group("name"): {
            "startFace": int(match.group("start")),
            "nFaces": int(match.group("nfaces")),
        }
        for match in matches
    }


def parse_points(path: Path) -> list[tuple[float, float, float]]:
    points: list[tuple[float, float, float]] = []
    in_list = False
    point_re = re.compile(r"\(([-+0-9.eE]+)\s+([-+0-9.eE]+)\s+([-+0-9.eE]+)\)")
    with path.open(encoding="utf-8", errors="replace") as handle:
        for line in handle:
            stripped = line.strip()
            if stripped == "(":
                in_list = True
                continue
            if not in_list:
                continue
            if stripped == ")":
                break
            match = point_re.match(stripped)
            if match:
                points.append((float(match.group(1)), float(match.group(2)), float(match.group(3))))
    return points


def vector_sub(a: tuple[float, float, float], b: tuple[float, float, float]) -> tuple[float, float, float]:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def cross(a: tuple[float, float, float], b: tuple[float, float, float]) -> tuple[float, float, float]:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def norm(a: tuple[float, float, float]) -> float:
    return math.sqrt(a[0] * a[0] + a[1] * a[1] + a[2] * a[2])


def face_area(indices: list[int], points: list[tuple[float, float, float]]) -> float:
    if len(indices) < 3:
        return 0.0
    p0 = points[indices[0]]
    area = 0.0
    for i in range(1, len(indices) - 1):
        area += 0.5 * norm(cross(vector_sub(points[indices[i]], p0), vector_sub(points[indices[i + 1]], p0)))
    return area


def parse_face_indices(line: str) -> list[int] | None:
    stripped = line.strip()
    match = re.match(r"\d+\(([^)]*)\)", stripped)
    if not match:
        return None
    return [int(item) for item in match.group(1).split()]


def compute_patch_areas(
    faces_path: Path,
    points: list[tuple[float, float, float]],
    patch_ranges: dict[str, dict[str, int]],
    needed_patches: set[str],
) -> dict[str, dict[str, float | int]]:
    face_to_patch: dict[int, str] = {}
    for patch in needed_patches:
        meta = patch_ranges[patch]
        start = meta["startFace"]
        for face_id in range(start, start + meta["nFaces"]):
            face_to_patch[face_id] = patch

    patch_area = {patch: 0.0 for patch in needed_patches}
    patch_face_count = {patch: 0 for patch in needed_patches}
    in_list = False
    face_id = 0
    with faces_path.open(encoding="utf-8", errors="replace") as handle:
        for line in handle:
            stripped = line.strip()
            if stripped == "(":
                in_list = True
                continue
            if not in_list:
                continue
            if stripped == ")":
                break
            patch = face_to_patch.get(face_id)
            if patch:
                indices = parse_face_indices(stripped)
                if indices is None:
                    raise RuntimeError(f"Could not parse face {face_id}: {stripped[:80]}")
                patch_area[patch] += face_area(indices, points)
                patch_face_count[patch] += 1
            face_id += 1

    return {
        patch: {
            "mesh_area_m2": patch_area[patch],
            "mesh_face_count": patch_face_count[patch],
            "boundary_nFaces": patch_ranges[patch]["nFaces"],
            "startFace": patch_ranges[patch]["startFace"],
        }
        for patch in sorted(needed_patches)
    }


def family_patch_map(recovery_rows: list[dict[str, str]], junction_rows: list[dict[str, str]]) -> dict[str, list[str]]:
    mapping: dict[str, list[str]] = {}
    for row in recovery_rows:
        if row.get("case_id") != "salt_1":
            continue
        mapping[row["segment_id"]] = [patch for patch in row["patch_names"].split(";") if patch]
    mapping["junction"] = [row["patch"] for row in junction_rows]
    return mapping


def rel_delta(a: float, b: float) -> float:
    denom = max(abs(b), 1.0e-30)
    return abs(a - b) / denom


def build() -> dict[str, object]:
    OUT.mkdir(parents=True, exist_ok=True)
    operator_rows = read_csv(OPERATOR_ROWS)
    recovery_rows = read_csv(RECOVERY_ROWS)
    junction_rows = read_csv(JUNCTION_PATCH_ROWS)
    family_patches = family_patch_map(recovery_rows, junction_rows)
    needed_patches = {patch for patches in family_patches.values() for patch in patches}

    boundary_ranges = parse_boundary(BOUNDARY)
    missing_boundary = sorted(patch for patch in needed_patches if patch not in boundary_ranges)
    if missing_boundary:
        raise RuntimeError(f"Missing patches in boundary file: {missing_boundary}")

    points = parse_points(POINTS)
    patch_areas = compute_patch_areas(FACES, points, boundary_ranges, needed_patches)

    patch_rows: list[dict[str, object]] = []
    for family, patches in sorted(family_patches.items()):
        junction_by_patch = {row["patch"]: row for row in junction_rows}
        for patch in patches:
            meta = patch_areas[patch]
            recovered_patch_area = junction_by_patch.get(patch, {}).get("area_m2", "")
            delta_abs = ""
            delta_rel = ""
            if recovered_patch_area:
                recovered_float = float(recovered_patch_area)
                delta_abs = abs(float(meta["mesh_area_m2"]) - recovered_float)
                delta_rel = rel_delta(float(meta["mesh_area_m2"]), recovered_float)
            patch_rows.append(
                {
                    "source_family": family,
                    "patch": patch,
                    "startFace": meta["startFace"],
                    "boundary_nFaces": meta["boundary_nFaces"],
                    "mesh_face_count": meta["mesh_face_count"],
                    "mesh_area_m2": meta["mesh_area_m2"],
                    "recovered_patch_area_m2": recovered_patch_area,
                    "area_delta_abs_m2": delta_abs,
                    "area_delta_rel": delta_rel,
                    "face_count_match": int(meta["mesh_face_count"]) == int(meta["boundary_nFaces"]),
                    "area_source": "constant/polyMesh points/faces/boundary",
                    "runtime_wallHeatFlux_used": False,
                }
            )

    operator_by_family = {row["source_family"]: row for row in operator_rows}
    family_rows: list[dict[str, object]] = []
    candidate_rows: list[dict[str, object]] = []
    all_family_pass = True
    for family, patches in sorted(family_patches.items()):
        mesh_area = sum(float(patch_areas[patch]["mesh_area_m2"]) for patch in patches)
        operator = operator_by_family[family]
        recovered_area = float(operator["area_m2"])
        delta_abs = abs(mesh_area - recovered_area)
        delta_rel = rel_delta(mesh_area, recovered_area)
        face_count_match = all(
            int(patch_areas[patch]["mesh_face_count"]) == int(patch_areas[patch]["boundary_nFaces"])
            for patch in patches
        )
        area_pass = face_count_match and (delta_abs <= AREA_ABS_TOL_M2 or delta_rel <= AREA_REL_TOL)
        all_family_pass = all_family_pass and area_pass
        h = float(operator["h_W_m2K_area_weighted"])
        hA = h * mesh_area
        source_paths = ";".join(
            str(path.relative_to(REPO))
            for path in [T0, BOUNDARY, FACES, POINTS]
        )
        family_rows.append(
            {
                "case_id": "salt_1",
                "source_family": family,
                "patch_count": len(patches),
                "boundary_face_count": sum(int(patch_areas[patch]["boundary_nFaces"]) for patch in patches),
                "mesh_face_count": sum(int(patch_areas[patch]["mesh_face_count"]) for patch in patches),
                "mesh_area_m2": mesh_area,
                "recovered_operator_area_m2": recovered_area,
                "area_delta_abs_m2": delta_abs,
                "area_delta_rel": delta_rel,
                "area_tolerance_pass": area_pass,
                "area_provenance_status": "mesh_area_verified" if area_pass else "mesh_area_mismatch_fail_closed",
                "h_W_m2K_area_weighted": h,
                "mesh_area_hA_W_K": hA,
                "recovered_operator_hA_W_K": operator["hA_W_K"],
                "hA_delta_abs_W_K": abs(hA - float(operator["hA_W_K"])),
                "source_paths": source_paths,
            }
        )
        if area_pass:
            candidate_rows.append(
                {
                    **operator,
                    "area_m2": mesh_area,
                    "hA_W_K": hA,
                    "area_provenance_status": "mesh_area_verified",
                    "release_grade_status": False,
                    "source_property_release": False,
                    "numeric_q_loss_release": False,
                    "admission_or_score": False,
                    "runtime_wallHeatFlux_used": False,
                    "source_paths": source_paths,
                }
            )

    gate_rows = [
        {
            "gate": "polyMesh_patch_coverage",
            "status": "pass" if not missing_boundary else "fail_closed",
            "count_or_value": f"{len(needed_patches) - len(missing_boundary)}/{len(needed_patches)}",
            "release_allowed": False,
            "reason": "all requested patches found in setup boundary file" if not missing_boundary else "missing setup boundary patches",
        },
        {
            "gate": "family_area_reconciliation",
            "status": "pass_preflight" if all_family_pass else "fail_closed",
            "count_or_value": f"{sum(1 for row in family_rows if row['area_tolerance_pass'])}/5",
            "release_allowed": False,
            "reason": "mesh-derived family areas must match recovered operator areas within predeclared tolerance; any mismatch blocks a five-family candidate",
        },
        {
            "gate": "mesh_area_backed_operator_completeness",
            "status": "pass_preflight" if len(candidate_rows) == 5 else "fail_closed",
            "count_or_value": f"{len(candidate_rows)}/5",
            "release_allowed": False,
            "reason": "mesh-area-backed operator rows are emitted only for families passing the area tolerance gate",
        },
        {
            "gate": "runtime_wallHeatFlux_exclusion",
            "status": "pass",
            "count_or_value": 0,
            "release_allowed": False,
            "reason": "forbidden: mesh area candidate source paths use 0/T and polyMesh only; wallHeatFlux remains excluded as runtime input",
        },
        {
            "gate": "source_property_release",
            "status": "fail_closed",
            "count_or_value": 0,
            "release_allowed": False,
            "reason": "this row repairs area provenance only; S11/S15 source/property release remains required",
        },
        {
            "gate": "candidate_freeze_or_score",
            "status": "closed_not_run",
            "count_or_value": 0,
            "release_allowed": False,
            "reason": "no freeze, fit, validation, holdout, external-test, or final score action is authorized",
        },
    ]

    source_manifest = [
        {"source_id": "polyMesh_boundary", "path": str(BOUNDARY.relative_to(REPO)), "use": "patch startFace/nFaces", "mutation_status": "read_only"},
        {"source_id": "polyMesh_faces", "path": str(FACES.relative_to(REPO)), "use": "face vertex indices for mesh-area calculation", "mutation_status": "read_only"},
        {"source_id": "polyMesh_points", "path": str(POINTS.relative_to(REPO)), "use": "point coordinates for mesh-area calculation", "mutation_status": "read_only"},
        {"source_id": "salt1_boundary_T", "path": str(T0.relative_to(REPO)), "use": "setup h/Ta/Tsur/emissivity provenance path", "mutation_status": "read_only"},
        {"source_id": "junction_recovery_operator", "path": str(OPERATOR_ROWS.relative_to(REPO)), "use": "five-family operator comparison", "mutation_status": "read_only"},
        {"source_id": "junction_patch_inventory", "path": str(JUNCTION_PATCH_ROWS.relative_to(REPO)), "use": "junction patch family definition", "mutation_status": "read_only"},
        {"source_id": "prior_nonjunction_recovery", "path": str(RECOVERY_ROWS.relative_to(REPO)), "use": "non-junction patch family definitions", "mutation_status": "read_only"},
        {"source_id": "source_envelope_gate", "path": str(SOURCE_ENVELOPE_GATE.relative_to(REPO)), "use": "prior release blocker context", "mutation_status": "read_only"},
    ]

    no_mutation_rows = [
        {"guardrail": "native_solver_outputs_mutated", "value": False},
        {"guardrail": "registry_or_admission_mutated", "value": False},
        {"guardrail": "scheduler_action", "value": False},
        {"guardrail": "fluid_or_external_edit", "value": False},
        {"guardrail": "source_property_release", "value": False},
        {"guardrail": "candidate_freeze", "value": False},
        {"guardrail": "validation_holdout_external_scoring", "value": False},
        {"guardrail": "fitting_or_model_selection_performed", "value": False},
        {"guardrail": "runtime_wallHeatFlux_used", "value": False},
        {"guardrail": "qwall_or_numeric_q_loss_release", "value": False},
        {"guardrail": "residual_absorbed_into_internal_nu", "value": False},
    ]

    write_csv(
        OUT / "patch_mesh_area_evidence.csv",
        patch_rows,
        [
            "source_family",
            "patch",
            "startFace",
            "boundary_nFaces",
            "mesh_face_count",
            "mesh_area_m2",
            "recovered_patch_area_m2",
            "area_delta_abs_m2",
            "area_delta_rel",
            "face_count_match",
            "area_source",
            "runtime_wallHeatFlux_used",
        ],
    )
    write_csv(
        OUT / "family_area_reconciliation.csv",
        family_rows,
        [
            "case_id",
            "source_family",
            "patch_count",
            "boundary_face_count",
            "mesh_face_count",
            "mesh_area_m2",
            "recovered_operator_area_m2",
            "area_delta_abs_m2",
            "area_delta_rel",
            "area_tolerance_pass",
            "area_provenance_status",
            "h_W_m2K_area_weighted",
            "mesh_area_hA_W_K",
            "recovered_operator_hA_W_K",
            "hA_delta_abs_W_K",
            "source_paths",
        ],
    )
    candidate_fieldnames = list(operator_rows[0].keys()) + ["area_provenance_status"]
    write_csv(OUT / "mesh_area_backed_operator_candidate.csv", candidate_rows, candidate_fieldnames)
    write_csv(OUT / "release_preflight_gate.csv", gate_rows, ["gate", "status", "count_or_value", "release_allowed", "reason"])
    write_csv(OUT / "source_manifest.csv", source_manifest, ["source_id", "path", "use", "mutation_status"])
    write_csv(OUT / "no_mutation_guardrails.csv", no_mutation_rows, ["guardrail", "value"])

    summary = {
        "task_id": TASK_ID,
        "date": DATE,
        "decision": "salt1_mesh_area_provenance_repaired_preflight_no_release_no_score" if all_family_pass else "salt1_mesh_area_provenance_fail_closed_no_release_no_score",
        "needed_patches": len(needed_patches),
        "missing_boundary_patches": len(missing_boundary),
        "points_read": len(points),
        "family_rows": len(family_rows),
        "family_area_tolerance_pass_rows": sum(1 for row in family_rows if row["area_tolerance_pass"]),
        "mesh_area_backed_operator_rows": len(candidate_rows),
        "five_family_mesh_area_backed_operator_ready": len(candidate_rows) == 5,
        "max_area_delta_abs_m2": max(float(row["area_delta_abs_m2"]) for row in family_rows),
        "max_area_delta_rel": max(float(row["area_delta_rel"]) for row in family_rows),
        "source_property_release": False,
        "candidate_freeze": False,
        "score_values_emitted": 0,
        "validation_holdout_external_scoring": False,
        "fitting_or_model_selection_performed": False,
        "native_output_mutation": False,
        "registry_or_admission_mutation": False,
        "scheduler_action": False,
        "fluid_or_external_edit": False,
        "runtime_wallHeatFlux_used": False,
        "runtime_leakage_relaxation": False,
        "residual_absorbed_into_internal_nu": False,
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (OUT / "README.md").write_text(readme(summary), encoding="utf-8")
    return summary


def readme(summary: dict[str, object]) -> str:
    return f"""---
provenance:
  - {BOUNDARY.relative_to(REPO)}
  - {FACES.relative_to(REPO)}
  - {POINTS.relative_to(REPO)}
  - {OPERATOR_ROWS.relative_to(REPO)}
tags: [passive-h2, salt1, mesh-area, source-envelope, no-release]
related:
  - .agent/status/2026-07-22_{TASK_ID}.md
  - .agent/journal/2026-07-22/passive-h2-salt1-mesh-area-provenance-repair-preflight.md
  - imports/2026-07-22_passive_h2_salt1_mesh_area_provenance_repair_preflight.json
task: {TASK_ID}
date: {DATE}
role: Forward-pred/Implementer/Tester/Writer/Reviewer
type: work_product
status: complete
---
# PASSIVE-H2 Salt1 Mesh-Area Provenance Repair Preflight

## Result

Decision: `{summary["decision"]}`.

This package computes Salt1 PASSIVE-H2 source-family areas directly from
`constant/polyMesh/points`, `faces`, and `boundary`. It compares those setup
mesh areas against the recovered five-family operator rows and emits a
mesh-area-backed diagnostic operator candidate. It does not release
source/property state, freeze coefficients, fit, score, run Fluid, or use
forbidden wallHeatFlux at runtime.

- needed patches: `{summary["needed_patches"]}`
- missing boundary patches: `{summary["missing_boundary_patches"]}`
- family rows: `{summary["family_rows"]}`
- family area tolerance pass rows: `{summary["family_area_tolerance_pass_rows"]}`
- mesh-area-backed operator rows: `{summary["mesh_area_backed_operator_rows"]}`
- five-family mesh-area-backed operator ready: `{summary["five_family_mesh_area_backed_operator_ready"]}`
- max absolute area delta: `{summary["max_area_delta_abs_m2"]}` m2
- final score values: `{summary["score_values_emitted"]}`

## Interpretation

Area provenance can now be separated from wallHeatFlux diagnostics. If all
family rows pass the tolerance gate, the area part of the Salt1 PASSIVE-H2
operator can be cited as setup-mesh backed. This still does not admit the
candidate: source/property release, same-QOI release-UQ, and S11/S15 freeze
gates remain closed.

## Outputs

- `patch_mesh_area_evidence.csv`
- `family_area_reconciliation.csv`
- `mesh_area_backed_operator_candidate.csv`
- `release_preflight_gate.csv`
- `source_manifest.csv`
- `no_mutation_guardrails.csv`
- `summary.json`

## Guardrails

No native CFD/OpenFOAM outputs, registry/admission state, scheduler state, Fluid
source, external repository, thesis current/LaTeX file, validation/holdout/
external-test score, fitting, tuning, model selection, source/property release,
protected-row release, candidate freeze, coefficient admission, runtime
forbidden wallHeatFlux use, Qwall release, hidden multiplier, runtime-leakage relaxation,
or residual absorption into internal Nu was changed.
"""


def main() -> None:
    print(json.dumps(build(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
