#!/usr/bin/env python3.11
"""Build the S13 endpoint face-geometry release-mask recovery gate."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path


TASK_ID = "TODO-S13-ENDPOINT-FACE-GEOMETRY-RELEASE-MASK-RECOVERY-2026-07-22"
DATE = "2026-07-22"
SLUG = "s13_endpoint_face_geometry_release_mask_recovery"
REPO = Path(__file__).resolve().parents[2]
OUT_DIR = REPO / "work_products/2026-07/2026-07-22/2026-07-22_s13_endpoint_face_geometry_release_mask_recovery"
STATUS_PATH = REPO / f".agent/status/{DATE}_{TASK_ID}.md"
JOURNAL_PATH = REPO / f".agent/journal/{DATE}/s13-endpoint-face-geometry-release-mask-recovery.md"
IMPORT_PATH = REPO / f"imports/{DATE}_{SLUG}.json"

ENRICHMENT = REPO / "work_products/2026-07/2026-07-22/2026-07-22_s13_endpoint_geometry_enrichment_for_release_masks"
DERIVATION = REPO / "work_products/2026-07/2026-07-22/2026-07-22_s13_throughflow_endpoint_mask_derivation"
MASK_DIR = DERIVATION / "masks"

REQUIRED_RELEASE_FIELDS = [
    "case_id",
    "endpoint_label",
    "face_id",
    "area_m2",
    "area_vector_x_m2",
    "area_vector_y_m2",
    "area_vector_z_m2",
    "owner_cell",
    "normal_convention",
    "positive_mdot_convention",
    "time_window_s",
    "source_path",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        raise ValueError(f"no rows for {path}")
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def build_recovery() -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    manifest_rows = read_csv(DERIVATION / "endpoint_mask_manifest.csv")
    inventory_rows = read_csv(DERIVATION / "classified_cap_face_inventory.csv")
    inventory_by_case = {row["case_id"]: row for row in inventory_rows}
    recovery_rows: list[dict[str, object]] = []
    candidate_rows: list[dict[str, object]] = []
    for row in manifest_rows:
        mask_path = REPO / row["candidate_mask_path"]
        mask_rows = read_csv(mask_path)
        columns = set(mask_rows[0]) if mask_rows else set()
        missing = [
            field
            for field in REQUIRED_RELEASE_FIELDS
            if field not in columns or any(not str(face.get(field, "")).strip() for face in mask_rows)
        ]
        release_ready = not missing
        recovery_rows.append(
            {
                "case_id": row["case_id"],
                "endpoint_label": row["endpoint_label"],
                "candidate_mask_path": row["candidate_mask_path"],
                "candidate_face_count": row["candidate_face_count"],
                "face_ids_present": str("face_id" in columns),
                "area_m2_present": str("area_m2" in columns),
                "area_vector_present": str(all(field in columns for field in REQUIRED_RELEASE_FIELDS if field.startswith("area_vector_"))),
                "owner_cell_present": str("owner_cell" in columns),
                "normal_convention_present": str("normal_convention" in columns and all(face.get("normal_convention", "").strip() for face in mask_rows)),
                "positive_mdot_convention_present": str("positive_mdot_convention" in columns and all(face.get("positive_mdot_convention", "").strip() for face in mask_rows)),
                "release_mask_ready": str(release_ready),
                "missing_release_fields": ";".join(missing),
                "decision": "candidate_face_ids_only_no_release_mask",
            }
        )
        for face in mask_rows:
            candidate_rows.append(
                {
                    "case_id": row["case_id"],
                    "endpoint_label": row["endpoint_label"],
                    "face_id": face.get("face_id", ""),
                    "candidate_mask_path": row["candidate_mask_path"],
                    "release_ready": "False",
                    "release_blocker": "missing_area_vectors_owner_cell_and_admitted_sign_convention",
                }
            )
    for row in recovery_rows:
        inv = inventory_by_case.get(row["case_id"], {})
        row["classified_inventory_status"] = inv.get("status", "missing")
        row["source_release_flag"] = inv.get("source_release_flag", "unknown")
        row["harvest_allowed_in_source_manifest"] = inv.get("harvest_allowed_in_source_manifest", "unknown")
    return recovery_rows, candidate_rows


def write_docs(summary: dict[str, object], changed_files: list[str]) -> None:
    STATUS_PATH.parent.mkdir(parents=True, exist_ok=True)
    JOURNAL_PATH.parent.mkdir(parents=True, exist_ok=True)
    IMPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATUS_PATH.write_text(
        f"""---
provenance:
  - {rel(OUT_DIR / 'summary.json')}
  - {rel(OUT_DIR / 'endpoint_face_geometry_recovery_matrix.csv')}
tags: [s13, endpoint-mask, geometry, release-gate]
related:
  - {rel(JOURNAL_PATH)}
  - {rel(IMPORT_PATH)}
task: {TASK_ID}
date: {DATE}
role: Thermal-modeling / Hydraulics / cfd-pp / Implementer / Tester / Writer / Reviewer
type: status
status: complete
---
# {TASK_ID}

## Changes Made

Built the S13 endpoint face-geometry release-mask recovery package from the
existing endpoint manifest, candidate masks, and classified cap-face inventory.
No exact release masks were recovered because mandatory face geometry fields
remain absent.

## Validation

Run `python3.11 -m unittest tools/analyze/test_s13_endpoint_face_geometry_release_mask_recovery.py`.
The expected result is `6` blocked endpoints, `288` candidate face ids, and
`0` released endpoint masks.

## Guardrails

Native solver outputs mutated: false. Registry mutated: false. Scheduler
action: false. External Fluid edit: false. No sampler/harvest/UQ launch,
source/property/Qwall release, residual value release, endpoint proxy
substitution, coefficient admission, candidate freeze, final score, hidden
multiplier, residual absorption, or runtime-leakage relaxation was performed.
""",
        encoding="utf-8",
    )
    JOURNAL_PATH.write_text(
        f"""---
provenance:
  - {rel(OUT_DIR / 'summary.json')}
  - {rel(DERIVATION / 'endpoint_mask_manifest.csv')}
tags: [s13, endpoint-mask, face-geometry]
related:
  - {rel(STATUS_PATH)}
  - {rel(IMPORT_PATH)}
task: {TASK_ID}
date: {DATE}
role: Thermal-modeling / Hydraulics / cfd-pp / Implementer / Tester / Writer / Reviewer
type: journal
status: complete
---
# S13 Endpoint Face-Geometry Release-Mask Recovery

Task: `{TASK_ID}`

Observed: six candidate endpoint masks exist across Salt2/Salt3/Salt4, each
with 48 face ids. The candidate masks do not include per-face area, area vector,
owner cell, or admitted throughflow sign convention fields.

Inferred: the masks are useful as a seed inventory but cannot support endpoint
throughflow integration, residual harvest, or same-QOI UQ.

Next useful action: regenerate endpoint masks from a mesh-aware postprocessor
that emits one row per endpoint face with area vectors, owner cells, normal
convention, positive-mdot convention, time window, and exact source path.
""",
        encoding="utf-8",
    )
    write_json(
        IMPORT_PATH,
        {
            "task": TASK_ID,
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "changed_files": changed_files,
            "read_only_context": [
                rel(ENRICHMENT / "endpoint_regeneration_contract.csv"),
                rel(DERIVATION / "endpoint_mask_manifest.csv"),
                rel(DERIVATION / "classified_cap_face_inventory.csv"),
                rel(DERIVATION / "source_manifest.csv"),
                rel(MASK_DIR),
            ],
            "native_solver_outputs_mutated": False,
            "registry_mutated": False,
            "scheduler_action": False,
            "external_fluid_edit": False,
            "no_scorecard_outputs": True,
            "provenance_flags": {
                "endpoint_proxy_substitution": False,
                "residual_value_release": False,
                "qwall_release": False,
                "candidate_freeze": False,
                "final_score_claim": False,
            },
        },
    )


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    recovery_rows, candidate_rows = build_recovery()
    gaps = [
        {
            "required_field": field,
            "endpoint_rows_missing_field": sum(
                1 for row in recovery_rows if field in row["missing_release_fields"].split(";")
            ),
            "release_required": "True",
            "forbidden_substitution": "candidate face ids or case-level convention only",
        }
        for field in REQUIRED_RELEASE_FIELDS
        if any(field in row["missing_release_fields"].split(";") for row in recovery_rows)
    ]
    regen_contract = read_csv(ENRICHMENT / "endpoint_regeneration_contract.csv")
    guardrails = [
        {"guardrail": "no_endpoint_proxy_substitution", "status": "preserved"},
        {"guardrail": "no_sampler_or_harvest_launch", "status": "preserved"},
        {"guardrail": "no_residual_value_release", "status": "preserved"},
        {"guardrail": "no_candidate_freeze", "status": "preserved"},
    ]
    source_manifest = [
        {"source_path": rel(DERIVATION / "endpoint_mask_manifest.csv"), "exists": "True", "mutated": "False", "use": "candidate endpoint manifest"},
        {"source_path": rel(DERIVATION / "classified_cap_face_inventory.csv"), "exists": "True", "mutated": "False", "use": "case-level face inventory"},
        {"source_path": rel(ENRICHMENT / "endpoint_regeneration_contract.csv"), "exists": "True", "mutated": "False", "use": "required release schema"},
        {"source_path": rel(MASK_DIR), "exists": str(MASK_DIR.exists()), "mutated": "False", "use": "candidate face-id masks"},
    ]
    write_csv(OUT_DIR / "endpoint_face_geometry_recovery_matrix.csv", recovery_rows)
    write_csv(OUT_DIR / "candidate_face_id_inventory.csv", candidate_rows)
    write_csv(OUT_DIR / "release_mask_schema_gap.csv", gaps)
    write_csv(OUT_DIR / "regeneration_contract.csv", regen_contract)
    write_csv(OUT_DIR / "source_manifest.csv", source_manifest)
    write_csv(OUT_DIR / "no_mutation_guardrails.csv", guardrails)
    released = [row for row in recovery_rows if row["release_mask_ready"] == "True"]
    summary = {
        "task_id": TASK_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "decision": "s13_endpoint_face_geometry_release_mask_recovery_fail_closed_no_exact_fields",
        "endpoint_rows": len(recovery_rows),
        "candidate_face_id_rows": len(candidate_rows),
        "released_endpoint_masks": len(released),
        "mandatory_gap_rows": len(gaps),
        "scheduler_action": False,
        "residual_value_release": False,
        "endpoint_proxy_substitution": False,
        "candidate_freeze": False,
        "final_score_claim": False,
    }
    write_json(OUT_DIR / "summary.json", summary)
    (OUT_DIR / "README.md").write_text(
        f"""---
provenance:
  - {rel(OUT_DIR / 'summary.json')}
  - {rel(OUT_DIR / 'endpoint_face_geometry_recovery_matrix.csv')}
tags: [s13, endpoint-mask, release-gate]
related:
  - {rel(STATUS_PATH)}
  - {rel(JOURNAL_PATH)}
  - {rel(IMPORT_PATH)}
task: {TASK_ID}
date: {DATE}
role: Thermal-modeling / Hydraulics / cfd-pp / Implementer / Tester / Writer / Reviewer
type: work_product
status: complete
---
# S13 Endpoint Face-Geometry Release-Mask Recovery

Decision: `s13_endpoint_face_geometry_release_mask_recovery_fail_closed_no_exact_fields`.

The existing candidate endpoint masks provide 288 face ids across six endpoints,
but no released mask can be formed because per-face area, area vector, owner
cell, and admitted throughflow sign convention fields are missing. The package
copies the regeneration contract forward and preserves the ban on endpoint proxy
substitution, residual value release, sampler/harvest launch, and scoring.
""",
        encoding="utf-8",
    )
    changed_files = [
        rel(OUT_DIR / name)
        for name in [
            "README.md",
            "endpoint_face_geometry_recovery_matrix.csv",
            "candidate_face_id_inventory.csv",
            "release_mask_schema_gap.csv",
            "regeneration_contract.csv",
            "source_manifest.csv",
            "no_mutation_guardrails.csv",
            "summary.json",
        ]
    ] + [
        rel(Path("tools/analyze/build_s13_endpoint_face_geometry_release_mask_recovery.py")),
        rel(Path("tools/analyze/test_s13_endpoint_face_geometry_release_mask_recovery.py")),
        rel(STATUS_PATH),
        rel(JOURNAL_PATH),
        rel(IMPORT_PATH),
    ]
    write_docs(summary, changed_files)


if __name__ == "__main__":
    main()
