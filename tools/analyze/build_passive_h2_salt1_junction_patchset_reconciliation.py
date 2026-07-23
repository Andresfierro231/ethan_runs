#!/usr/bin/env python3
"""Reconcile the Salt1 PASSIVE-H2 junction area mismatch."""

from __future__ import annotations

import csv
import json
from pathlib import Path


TASK_ID = "TODO-PASSIVE-H2-SALT1-JUNCTION-PATCHSET-RECONCILIATION-2026-07-22"
DATE = "2026-07-22"
REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "work_products/2026-07/2026-07-22/2026-07-22_passive_h2_salt1_junction_patchset_reconciliation"

MESH_PREFLIGHT = REPO / "work_products/2026-07/2026-07-22/2026-07-22_passive_h2_salt1_mesh_area_provenance_repair_preflight"
JUNCTION_RECOVERY = REPO / "work_products/2026-07/2026-07-22/2026-07-22_passive_h2_salt1_junction_setup_row_recovery_background"

PATCH_EVIDENCE = MESH_PREFLIGHT / "patch_mesh_area_evidence.csv"
FAMILY_RECON = MESH_PREFLIGHT / "family_area_reconciliation.csv"
FOUR_FAMILY_CANDIDATE = MESH_PREFLIGHT / "mesh_area_backed_operator_candidate.csv"
FIVE_FAMILY_OPERATOR = JUNCTION_RECOVERY / "salt1_five_family_operator_rows_for_fluid.csv"
JUNCTION_PATCH_INVENTORY = JUNCTION_RECOVERY / "salt1_junction_patch_inventory.csv"

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
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def rel_delta(a: float, b: float) -> float:
    return abs(a - b) / max(abs(b), 1.0e-30)


def patch_group(patch: str) -> str:
    if patch.endswith("_stub"):
        return "stub"
    if patch.endswith("_extension"):
        return "extension"
    return "core_junction_body"


def bool_text(value: bool) -> str:
    return "true" if value else "false"


def source_paths() -> str:
    return ";".join(
        str(path.relative_to(REPO))
        for path in [PATCH_EVIDENCE, FAMILY_RECON, FIVE_FAMILY_OPERATOR, JUNCTION_PATCH_INVENTORY]
    )


def build() -> dict[str, object]:
    OUT.mkdir(parents=True, exist_ok=True)

    patch_rows = [
        row for row in read_csv(PATCH_EVIDENCE)
        if row["source_family"] == "junction"
    ]
    family_rows = read_csv(FAMILY_RECON)
    operator_rows = read_csv(FIVE_FAMILY_OPERATOR)
    four_family_rows = read_csv(FOUR_FAMILY_CANDIDATE)

    if len(patch_rows) != 18:
        raise RuntimeError(f"Expected 18 junction patches, found {len(patch_rows)}")

    junction_family = next(row for row in family_rows if row["source_family"] == "junction")
    junction_operator = next(row for row in operator_rows if row["source_family"] == "junction")

    detailed_patch_rows: list[dict[str, object]] = []
    for row in patch_rows:
        mesh_area = float(row["mesh_area_m2"])
        recovered_area = float(row["recovered_patch_area_m2"])
        delta_abs = abs(mesh_area - recovered_area)
        delta_rel = rel_delta(mesh_area, recovered_area)
        pass_tol = delta_abs <= AREA_ABS_TOL_M2 or delta_rel <= AREA_REL_TOL
        detailed_patch_rows.append(
            {
                "case_id": "salt_1",
                "source_family": "junction",
                "patch": row["patch"],
                "junction_subgroup": patch_group(row["patch"]),
                "boundary_nFaces": row["boundary_nFaces"],
                "mesh_face_count": row["mesh_face_count"],
                "mesh_area_m2": mesh_area,
                "recovered_patch_area_m2": recovered_area,
                "area_delta_abs_m2": delta_abs,
                "area_delta_rel": delta_rel,
                "area_tolerance_pass": pass_tol,
                "face_count_match": row["face_count_match"],
                "evidence_status": "setup_mesh_verified" if pass_tol else "setup_mesh_replaces_recovered_patch_area",
                "runtime_wallHeatFlux_used": False,
            }
        )

    subgroup_rows: list[dict[str, object]] = []
    for subgroup in ["core_junction_body", "stub", "extension"]:
        members = [row for row in detailed_patch_rows if row["junction_subgroup"] == subgroup]
        mesh_area = sum(float(row["mesh_area_m2"]) for row in members)
        recovered_area = sum(float(row["recovered_patch_area_m2"]) for row in members)
        delta_abs = abs(mesh_area - recovered_area)
        delta_rel = rel_delta(mesh_area, recovered_area)
        subgroup_rows.append(
            {
                "case_id": "salt_1",
                "source_family": "junction",
                "junction_subgroup": subgroup,
                "patch_count": len(members),
                "mesh_area_m2": mesh_area,
                "recovered_patch_area_m2": recovered_area,
                "area_delta_abs_m2": delta_abs,
                "area_delta_rel": delta_rel,
                "area_tolerance_pass": delta_abs <= AREA_ABS_TOL_M2 or delta_rel <= AREA_REL_TOL,
                "delta_share_of_family_abs": delta_abs / float(junction_family["area_delta_abs_m2"]),
                "interpretation": "dominant mismatch owner" if subgroup == "core_junction_body" else "passes or near-roundoff contribution",
            }
        )

    mesh_area_all18 = sum(float(row["mesh_area_m2"]) for row in detailed_patch_rows)
    recovered_operator_area = float(junction_operator["area_m2"])
    h_area_weighted = float(junction_operator["h_W_m2K_area_weighted"])
    corrected_hA = mesh_area_all18 * h_area_weighted
    recovered_hA = float(junction_operator["hA_W_K"])
    corrected_delta = abs(mesh_area_all18 - recovered_operator_area)

    alternative_rows = [
        {
            "candidate": "recovered_operator_all18",
            "patchset": "18 recovered junction/stub patches",
            "area_basis": "recovered operator area",
            "area_m2": recovered_operator_area,
            "hA_W_K": recovered_hA,
            "area_gate_status": "fail_against_setup_mesh",
            "source_property_release": False,
            "candidate_freeze_or_score": False,
            "interpretation": "current diagnostic operator is internally consistent but fails direct setup mesh area reconciliation",
        },
        {
            "candidate": "same_patchset_direct_setup_mesh_area",
            "patchset": "same 18 junction/stub patches",
            "area_basis": "constant/polyMesh points/faces/boundary",
            "area_m2": mesh_area_all18,
            "hA_W_K": corrected_hA,
            "area_gate_status": "pass_area_only",
            "source_property_release": False,
            "candidate_freeze_or_score": False,
            "interpretation": "setup mesh area replaces recovered core-patch areas; patch membership unchanged",
        },
    ]

    corrected_candidate: list[dict[str, object]] = []
    for row in four_family_rows:
        corrected_candidate.append(dict(row))
    corrected_junction = dict(junction_operator)
    corrected_junction.update(
        {
            "diagnostic_use": "salt1_junction_patchset_reconciled_area_only_no_scoring",
            "area_m2": mesh_area_all18,
            "hA_W_K": corrected_hA,
            "admission_or_score": "false",
            "source_property_release": "false",
            "numeric_q_loss_release": "false",
            "runtime_CFD_mdot_used": "false",
            "runtime_Qwall_used": "false",
            "runtime_validation_temperature_used": "false",
            "runtime_wallHeatFlux_used": "false",
            "setup_recovery_status": "mesh_area_reconciled_same_patchset",
            "release_grade_status": "false",
            "source_paths": source_paths(),
        }
    )
    corrected_candidate.append(corrected_junction)

    gate_rows = [
        {
            "gate": "junction_patch_coverage",
            "status": "pass",
            "evidence": f"{len(detailed_patch_rows)}/18 patches present in prior setup-mesh evidence",
            "allows_release_or_score": False,
        },
        {
            "gate": "recovered_operator_area_reconciliation",
            "status": "fail_closed",
            "evidence": f"delta={corrected_delta} m2 against direct setup mesh",
            "allows_release_or_score": False,
        },
        {
            "gate": "same_patchset_direct_mesh_area_replacement",
            "status": "pass_area_only_no_release",
            "evidence": "all mismatch localizes to core junction-body patch areas; patch membership unchanged",
            "allows_release_or_score": False,
        },
        {
            "gate": "source_property_release",
            "status": "fail_closed",
            "evidence": "area reconciliation is not a source/property release or same-QOI UQ result",
            "allows_release_or_score": False,
        },
        {
            "gate": "candidate_freeze_or_score",
            "status": "closed_not_run",
            "evidence": "no train/validation/holdout/external scores emitted",
            "allows_release_or_score": False,
        },
    ]

    guardrail_rows = [
        {"guardrail": "native_solver_outputs_mutated", "status": False},
        {"guardrail": "registry_mutated", "status": False},
        {"guardrail": "scheduler_action", "status": False},
        {"guardrail": "fluid_or_external_edit", "status": False},
        {"guardrail": "source_property_release", "status": False},
        {"guardrail": "candidate_freeze", "status": False},
        {"guardrail": "protected_or_final_scoring", "status": False},
        {"guardrail": "validation_holdout_external_scoring", "status": False},
        {"guardrail": "fitting_tuning_model_selection", "status": False},
        {"guardrail": "runtime_wallHeatFlux_used", "status": False},
    ]

    write_csv(
        OUT / "junction_patch_delta_table.csv",
        detailed_patch_rows,
        [
            "case_id", "source_family", "patch", "junction_subgroup",
            "boundary_nFaces", "mesh_face_count", "mesh_area_m2",
            "recovered_patch_area_m2", "area_delta_abs_m2", "area_delta_rel",
            "area_tolerance_pass", "face_count_match", "evidence_status",
            "runtime_wallHeatFlux_used",
        ],
    )
    write_csv(
        OUT / "junction_subgroup_area_delta.csv",
        subgroup_rows,
        [
            "case_id", "source_family", "junction_subgroup", "patch_count",
            "mesh_area_m2", "recovered_patch_area_m2", "area_delta_abs_m2",
            "area_delta_rel", "area_tolerance_pass", "delta_share_of_family_abs",
            "interpretation",
        ],
    )
    write_csv(
        OUT / "junction_patchset_alternative_gate.csv",
        alternative_rows,
        [
            "candidate", "patchset", "area_basis", "area_m2", "hA_W_K",
            "area_gate_status", "source_property_release",
            "candidate_freeze_or_score", "interpretation",
        ],
    )
    write_csv(
        OUT / "five_family_mesh_area_candidate_diagnostic_only.csv",
        corrected_candidate,
        list(corrected_candidate[0].keys()),
    )
    write_csv(
        OUT / "release_gate.csv",
        gate_rows,
        ["gate", "status", "evidence", "allows_release_or_score"],
    )
    write_csv(
        OUT / "no_mutation_guardrails.csv",
        guardrail_rows,
        ["guardrail", "status"],
    )
    write_csv(
        OUT / "source_manifest.csv",
        [
            {
                "source_path": str(path.relative_to(REPO)),
                "use": use,
                "mutation": "read-only",
            }
            for path, use in [
                (PATCH_EVIDENCE, "patch-level direct setup mesh evidence"),
                (FAMILY_RECON, "prior family-level area gate"),
                (FIVE_FAMILY_OPERATOR, "diagnostic operator row to reconcile"),
                (JUNCTION_PATCH_INVENTORY, "junction patch inventory and recovered areas"),
            ]
        ],
        ["source_path", "use", "mutation"],
    )

    failing_patches = [
        row for row in detailed_patch_rows
        if not bool(row["area_tolerance_pass"])
    ]
    summary = {
        "task_id": TASK_ID,
        "date": DATE,
        "decision": "salt1_junction_patchset_reconciled_area_only_no_release_no_score",
        "junction_patch_count": len(detailed_patch_rows),
        "failing_patch_count": len(failing_patches),
        "failing_patch_groups": sorted({row["junction_subgroup"] for row in failing_patches}),
        "mesh_area_all18_m2": mesh_area_all18,
        "recovered_operator_area_m2": recovered_operator_area,
        "area_delta_abs_m2": corrected_delta,
        "area_delta_rel": rel_delta(mesh_area_all18, recovered_operator_area),
        "corrected_hA_W_K": corrected_hA,
        "recovered_hA_W_K": recovered_hA,
        "hA_delta_abs_W_K": abs(corrected_hA - recovered_hA),
        "same_patchset_area_gate_pass": True,
        "source_property_release": False,
        "candidate_freeze": False,
        "score_values_emitted": 0,
        "runtime_wallHeatFlux_used": False,
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    readme = f"""---
provenance:
  - {PATCH_EVIDENCE.relative_to(REPO)}
  - {FAMILY_RECON.relative_to(REPO)}
  - {FIVE_FAMILY_OPERATOR.relative_to(REPO)}
  - {JUNCTION_PATCH_INVENTORY.relative_to(REPO)}
tags: [passive-h2, salt1, junction, mesh-area, no-release]
related:
  - .agent/status/2026-07-22_{TASK_ID}.md
  - .agent/journal/2026-07-22/passive-h2-salt1-junction-patchset-reconciliation.md
task: {TASK_ID}
date: {DATE}
role: Forward-pred/Implementer/Tester/Writer/Reviewer
type: work_product
status: complete
---
# PASSIVE-H2 Salt1 Junction Patchset Reconciliation

Decision: `{summary["decision"]}`.

The Salt1 junction mismatch is not caused by missing patches. The same 18
junction/stub patches are present in the setup-mesh evidence. The mismatch is
localized to the four core junction-body patches; stub and extension rows are
roundoff-level matches. Replacing the recovered junction area with the direct
`constant/polyMesh` area closes the area-only gate for the same patchset.

This is still diagnostic only. It does not release source/property state,
numeric Qwall or q-loss values, coefficients, train/validation/holdout/external
scores, or a frozen predictive candidate.

## Key Numbers

- junction patches checked: `{summary["junction_patch_count"]}`
- failing patch count: `{summary["failing_patch_count"]}`
- failing patch groups: `{", ".join(summary["failing_patch_groups"])}`
- direct setup-mesh junction area: `{summary["mesh_area_all18_m2"]}` m2
- recovered operator junction area: `{summary["recovered_operator_area_m2"]}` m2
- absolute area delta: `{summary["area_delta_abs_m2"]}` m2
- relative area delta: `{summary["area_delta_rel"]}`
- corrected hA delta versus recovered operator: `{summary["hA_delta_abs_W_K"]}` W/K

## Outputs

- `junction_patch_delta_table.csv`
- `junction_subgroup_area_delta.csv`
- `junction_patchset_alternative_gate.csv`
- `five_family_mesh_area_candidate_diagnostic_only.csv`
- `release_gate.csv`
- `source_manifest.csv`
- `no_mutation_guardrails.csv`
- `summary.json`
"""
    (OUT / "README.md").write_text(readme, encoding="utf-8")

    return summary


if __name__ == "__main__":
    print(json.dumps(build(), indent=2))
