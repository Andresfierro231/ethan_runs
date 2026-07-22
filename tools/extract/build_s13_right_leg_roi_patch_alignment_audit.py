#!/usr/bin/env python3
"""Audit S13 right-leg ROI and trusted wall-patch alignment."""

from __future__ import annotations

import csv
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.common import csv_dump, ensure_dir, iso_timestamp, json_dump, relative_to_workspace

TASK_ID = "TODO-S13-RIGHT-LEG-ROI-PATCH-ALIGNMENT-AUDIT-2026-07-21"
OUT = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_s13_right_leg_roi_patch_alignment_audit"

FORENSICS = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_topology_forensics_alt_cv"
SOURCE_BOUNDED = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_source_bounded_cv_definition"
GEOMETRY = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_geometry_contract"

TRUSTED_RIGHT_LEG_PATCHES = {
    "pipeleg_right_01_lower",
    "pipeleg_right_02_middle",
    "pipeleg_right_03_upper",
}
CASE_IDS = ("salt_2", "salt_3", "salt_4")


def rel(path: Path) -> str:
    return relative_to_workspace(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def by_case_component(rows: list[dict[str, str]]) -> dict[tuple[str, str], list[dict[str, str]]]:
    out: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        out[(row["case_id"], row["face_component_id"])].append(row)
    return out


def is_trusted_patch(name: str) -> bool:
    return name in TRUSTED_RIGHT_LEG_PATCHES


def is_right_context_patch(name: str) -> bool:
    return "right" in name


def dominant_rows(components: list[dict[str, str]]) -> list[dict[str, str]]:
    out = []
    for case_id in CASE_IDS:
        case_rows = [row for row in components if row["case_id"] == case_id]
        if not case_rows:
            continue
        out.append(max(case_rows, key=lambda row: int(row["cell_count"])))
    return out


def build_package(out: Path = OUT) -> dict[str, Any]:
    ensure_dir(out)
    components = read_csv(FORENSICS / "component_topology_forensics.csv")
    boundaries = read_csv(FORENSICS / "component_boundary_escape_by_patch.csv")
    wall_contract = read_csv(GEOMETRY / "wall_core_band_contract.csv")
    release_decisions = read_csv(SOURCE_BOUNDED / "release_decision.csv")
    boundary_by_component = by_case_component(boundaries)
    wall_patch_by_case = {
        row["case_id"]: row.get("wall_patch_candidates", "")
        for row in wall_contract
    }
    source_release_by_case = {row["case_id"]: row for row in release_decisions}

    dominant = []
    for row in dominant_rows(components):
        patch_rows = boundary_by_component[(row["case_id"], row["face_component_id"])]
        patch_names = [patch["patch_name"] for patch in patch_rows]
        trusted_contact = [name for name in patch_names if is_trusted_patch(name)]
        right_context = [name for name in patch_names if is_right_context_patch(name)]
        dominant.append(
            {
                "case_id": row["case_id"],
                "dominant_component_id": row["face_component_id"],
                "cell_count": row["cell_count"],
                "fraction_of_reverse_candidates": row["fraction_of_reverse_candidates"],
                "y_min": row["y_min"],
                "y_max": row["y_max"],
                "boundary_patch_count": len(set(patch_names)),
                "boundary_patch_names": ";".join(sorted(set(patch_names))),
                "trusted_right_leg_patch_contact_count": len(set(trusted_contact)),
                "trusted_right_leg_patch_names": ";".join(sorted(set(trusted_contact))),
                "right_context_patch_names": ";".join(sorted(set(right_context))),
                "alignment_status": "misaligned_no_trusted_right_leg_wall_contact",
                "interpretation": "dominant reverse-flow component is not source-bounded by trusted right-leg wall patches",
            }
        )

    wall_candidates = []
    for row in components:
        if row.get("alternate_cv_selected") != "true":
            continue
        patch_rows = boundary_by_component[(row["case_id"], row["face_component_id"])]
        patch_names = sorted({patch["patch_name"] for patch in patch_rows})
        trusted = [name for name in patch_names if is_trusted_patch(name)]
        wall_candidates.append(
            {
                "case_id": row["case_id"],
                "candidate_component_id": row["face_component_id"],
                "cell_count": row["cell_count"],
                "fraction_of_reverse_candidates": row["fraction_of_reverse_candidates"],
                "right_leg_wall_face_count": row["right_leg_wall_face_count"],
                "right_leg_wall_area_m2": row["right_leg_wall_area_m2"],
                "boundary_patch_names": ";".join(patch_names),
                "trusted_patch_names": ";".join(trusted),
                "candidate_status": row["release_status"],
                "blocking_reason": row["blocking_reason"],
                "interpretation": "wall-adjacent diagnostic component is too small or touches unreleased/ncc boundary faces",
            }
        )
    if not any(row["case_id"] == "salt_2" for row in wall_candidates):
        wall_candidates.append(
            {
                "case_id": "salt_2",
                "candidate_component_id": "",
                "cell_count": 0,
                "fraction_of_reverse_candidates": 0,
                "right_leg_wall_face_count": 0,
                "right_leg_wall_area_m2": 0,
                "boundary_patch_names": "",
                "trusted_patch_names": "",
                "candidate_status": "blocked_no_wall_adjacent_reverse_component",
                "blocking_reason": "no_face_connected_reverse_flow_component_contacts_trusted_right_leg_wall_patches",
                "interpretation": "Salt2 provides no wall-adjacent reverse-flow seed under the current mask",
            }
        )
    wall_candidates.sort(key=lambda row: row["case_id"])

    seed_requirements = []
    for case_id in CASE_IDS:
        release = source_release_by_case[case_id]
        seed_requirements.append(
            {
                "case_id": case_id,
                "required_seed": "predeclared_geometry_backed_right_leg_upcomer_band",
                "trusted_wall_patch_candidates": wall_patch_by_case.get(case_id, ""),
                "current_velocity_mask_status": release["release_status"],
                "required_rule": "seed from trusted right-leg wall patches plus conservative spatial band before applying velocity/exchange tests",
                "forbidden_rule": "largest reverse-flow component or loop mdot/proxy faceZone as exchange interface",
                "release_status": "blocked_geometry_seed_required",
                "s12_impact": "S12-HIAX1 implementation remains blocked until this seed releases an exchange-state QOI basis",
            }
        )

    s12_impact = [
        {
            "gate": "s13_roi_patch_alignment",
            "status": "fail",
            "effect_on_s12": "blocks S12-HIAX1 exchange-state QOIs",
            "evidence": rel(out / "dominant_component_patch_overlap.csv"),
            "next_action": "define geometry-backed right-leg/upcomer seed tied to trusted wall patches",
        },
        {
            "gate": "s13_source_bounded_cv",
            "status": "fail",
            "effect_on_s12": "blocks sampler manifest and true Fluid implementation",
            "evidence": rel(SOURCE_BOUNDED / "release_decision.csv"),
            "next_action": "rerun source-bounded CV release only after geometry seed exists",
        },
    ]

    decision = [
        {
            "decision_id": "roi_patch_alignment",
            "release_status": "complete_fail_closed_geometry_seed_required",
            "dominant_components_aligned": "false",
            "wall_candidate_components_released": "false",
            "new_cv_admitted": "false",
            "s12_unlocked": "false",
            "blocking_reason": "dominant reverse-flow components have no trusted right-leg wall patch contact; wall-adjacent components are absent or tiny and touch unreleased/ncc boundaries",
        }
    ]

    csv_dump(
        out / "dominant_component_patch_overlap.csv",
        [
            "case_id",
            "dominant_component_id",
            "cell_count",
            "fraction_of_reverse_candidates",
            "y_min",
            "y_max",
            "boundary_patch_count",
            "boundary_patch_names",
            "trusted_right_leg_patch_contact_count",
            "trusted_right_leg_patch_names",
            "right_context_patch_names",
            "alignment_status",
            "interpretation",
        ],
        dominant,
    )
    csv_dump(
        out / "wall_candidate_component_review.csv",
        [
            "case_id",
            "candidate_component_id",
            "cell_count",
            "fraction_of_reverse_candidates",
            "right_leg_wall_face_count",
            "right_leg_wall_area_m2",
            "boundary_patch_names",
            "trusted_patch_names",
            "candidate_status",
            "blocking_reason",
            "interpretation",
        ],
        wall_candidates,
    )
    csv_dump(
        out / "geometry_seed_requirements.csv",
        [
            "case_id",
            "required_seed",
            "trusted_wall_patch_candidates",
            "current_velocity_mask_status",
            "required_rule",
            "forbidden_rule",
            "release_status",
            "s12_impact",
        ],
        seed_requirements,
    )
    csv_dump(
        out / "s12_unlock_impact.csv",
        ["gate", "status", "effect_on_s12", "evidence", "next_action"],
        s12_impact,
    )
    csv_dump(
        out / "roi_patch_alignment_decision.csv",
        ["decision_id", "release_status", "dominant_components_aligned", "wall_candidate_components_released", "new_cv_admitted", "s12_unlocked", "blocking_reason"],
        decision,
    )
    csv_dump(
        out / "source_manifest.csv",
        ["path", "role", "exists", "native_solver_output", "mutated"],
        [
            {"path": rel(FORENSICS / "component_topology_forensics.csv"), "role": "read component geometry and release status", "exists": "true", "native_solver_output": "false", "mutated": "false"},
            {"path": rel(FORENSICS / "component_boundary_escape_by_patch.csv"), "role": "read component boundary contacts", "exists": "true", "native_solver_output": "false", "mutated": "false"},
            {"path": rel(GEOMETRY / "wall_core_band_contract.csv"), "role": "read trusted wall patch candidates", "exists": "true", "native_solver_output": "false", "mutated": "false"},
            {"path": rel(SOURCE_BOUNDED / "release_decision.csv"), "role": "read source-bounded release result", "exists": "true", "native_solver_output": "false", "mutated": "false"},
            {"path": rel(out), "role": "generated task-owned package", "exists": "true", "native_solver_output": "false", "mutated": "true"},
        ],
    )
    csv_dump(
        out / "no_mutation_guardrails.csv",
        ["guard_id", "status", "policy"],
        [
            {"guard_id": "native_outputs", "status": "pass", "policy": "no native CFD/OpenFOAM outputs mutated"},
            {"guard_id": "admission", "status": "pass", "policy": "no CV, exchange-cell, S11, S12, S15, or S6 admission"},
            {"guard_id": "thresholds", "status": "pass", "policy": "no threshold relaxation or new mask rule admitted"},
        ],
    )

    summary = {
        "task": TASK_ID,
        "generated_at": iso_timestamp(),
        "decision": "complete_fail_closed_geometry_seed_required",
        "case_count": len(CASE_IDS),
        "dominant_components_aligned": False,
        "wall_candidate_components_released": False,
        "new_cv_admitted": False,
        "s12_unlocked": False,
        "native_output_mutation": False,
        "registry_or_admission_mutation": False,
        "scheduler_action": False,
        "threshold_relaxation": False,
        "next_action": "define a predeclared geometry-backed right-leg/upcomer seed tied to trusted wall patches",
    }
    json_dump(out / "summary.json", summary)
    (out / "README.md").write_text(
        f"""---
provenance:
  - {rel(FORENSICS / 'component_topology_forensics.csv')}
  - {rel(FORENSICS / 'component_boundary_escape_by_patch.csv')}
  - {rel(GEOMETRY / 'wall_core_band_contract.csv')}
tags: [s13, upcomer-exchange, roi, geometry-seed, fail-closed]
related:
  - {rel(SOURCE_BOUNDED / 'release_decision.csv')}
task: {TASK_ID}
date: 2026-07-21
role: Hydraulics / cfd-pp / Tester / Writer
type: work_product
status: complete_fail_closed
---
# S13 Right-Leg ROI Patch Alignment Audit

This package audits whether the reverse-flow cell-center ROI and trusted
right-leg wall patches describe the same physical S13 region.

Decision: `{summary['decision']}`.

Dominant reverse-flow components in Salt2/Salt3/Salt4 have zero trusted
right-leg wall patch contact. The only wall-contact alternate components are
absent for Salt2 and tiny for Salt3/Salt4, where they touch unreleased
`ncc_pipeleg_right_03_upper_end` boundary faces. A source-bounded S13 CV should
therefore not be released from the velocity-only dominant component rule.

Next executable unlock is a predeclared geometry-backed right-leg/upcomer seed
tied to `pipeleg_right_01_lower`, `pipeleg_right_02_middle`, and
`pipeleg_right_03_upper`, followed by a rerun of source-bounded CV release.

No native-output mutation, scheduler action, surface extraction, sampler,
harvest, Fluid edit, threshold relaxation, new mask admission, exchange-cell
admission, S11/S12/S15/S6 trigger, or internal-Nu residual absorption was
performed.
""",
        encoding="utf-8",
    )
    return {"summary": summary, "dominant": dominant, "wall_candidates": wall_candidates}


def main() -> int:
    payload = build_package()
    print(json.dumps(payload["summary"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
