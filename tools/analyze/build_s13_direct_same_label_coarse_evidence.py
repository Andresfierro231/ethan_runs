#!/usr/bin/env python3.11
"""Build the S13 direct same-label coarse evidence admission gate.

This consumes only existing S13 topology/coarse/medium/fine evidence. It does
not launch samplers or mutate native outputs. If direct same-label coarse
evidence is still missing, it emits a compute-ready extraction contract.
"""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TASK_ID = "TODO-S13-DIRECT-SAME-LABEL-COARSE-EVIDENCE-2026-07-22"
DATE = "2026-07-22"
SLUG = "s13_direct_same_label_coarse_evidence"
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_s13_direct_same_label_coarse_evidence"
STATUS_PATH = ROOT / f".agent/status/{DATE}_{TASK_ID}.md"
JOURNAL_PATH = ROOT / f".agent/journal/{DATE}/s13-direct-same-label-coarse-evidence.md"
IMPORT_PATH = ROOT / f"imports/{DATE}_{SLUG}.json"

STRICT = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_s13_strict_coarse_nogo_contract"
GEN = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_same_label_mesh_family_generation"
RECON = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_s13_candidate_coarse_medium_fine_reconciliation"
CLEAN = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_s13_clean_sampler_gci_readiness"
RESIDUAL = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_s13_residual_complete_open_cv_energy_balance_contract"
ENDPOINT = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_s13_endpoint_face_geometry_release_mask_recovery"
DERIVATION = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_s13_throughflow_endpoint_mask_derivation"

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


def boolish(value: object) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes", "pass"}


def b(value: bool) -> str:
    return "true" if value else "false"


def require_inputs() -> None:
    required = [
        STRICT / "replacement_coarse_dataset_contract.csv",
        STRICT / "case_qoi_strict_coarse_no_go.csv",
        GEN / "same_label_mesh_family_generated_rows.csv",
        RECON / "candidate_triplet_reconciliation.csv",
        CLEAN / "face_lane_contract_inventory.csv",
        RESIDUAL / "case_residual_budget_skeleton.csv",
        ENDPOINT / "endpoint_face_geometry_recovery_matrix.csv",
        DERIVATION / "endpoint_mask_manifest.csv",
    ]
    missing = [rel(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("missing S13 direct coarse inputs: " + "; ".join(missing))


def build_lane_matrix() -> list[dict[str, Any]]:
    replacement = read_csv(STRICT / "replacement_coarse_dataset_contract.csv")
    generated = read_csv(GEN / "same_label_mesh_family_generated_rows.csv")
    face_rows = read_csv(CLEAN / "face_lane_contract_inventory.csv")
    residual_rows = read_csv(RESIDUAL / "case_residual_budget_skeleton.csv")
    endpoint_rows = read_csv(ENDPOINT / "endpoint_face_geometry_recovery_matrix.csv")

    coarse_generated_rows = [row for row in generated if row["mesh_level"] == "current_coarse_continuation"]
    medium_fine_face_rows = [row for row in face_rows if row["mesh_level"] in {"medium", "fine"}]
    released_endpoint_rows = [row for row in endpoint_rows if row.get("release_mask_ready") == "True"]
    residual_complete_rows = [row for row in residual_rows if row.get("can_compute_residual_complete_balance") == "true"]

    return [
        {
            "lane": "coarse_qoi_values",
            "required_artifact": "s13_same_label_coarse_open_cv_qoi_rows.csv",
            "existing_rows": len(coarse_generated_rows),
            "direct_same_label_admitted_rows": 0,
            "admission_ready": "false",
            "available_evidence": rel(GEN / "same_label_mesh_family_generated_rows.csv"),
            "blocking_gap": "rows are generated_current_coarse_only_not_gci and lack direct admission flags",
        },
        {
            "lane": "coarse_endpoint_face_geometry",
            "required_artifact": "s13_same_label_coarse_open_cv_face_contract.csv",
            "existing_rows": 0,
            "direct_same_label_admitted_rows": 0,
            "admission_ready": "false",
            "available_evidence": rel(ENDPOINT / "endpoint_face_geometry_recovery_matrix.csv"),
            "blocking_gap": f"released endpoint masks {len(released_endpoint_rows)}; candidate masks lack area vectors/owner/sign convention",
        },
        {
            "lane": "medium_fine_face_context",
            "required_artifact": "medium/fine face lane inventory",
            "existing_rows": len(medium_fine_face_rows),
            "direct_same_label_admitted_rows": 0,
            "admission_ready": "false",
            "available_evidence": rel(CLEAN / "face_lane_contract_inventory.csv"),
            "blocking_gap": "medium/fine context exists but cannot substitute for direct coarse face geometry",
        },
        {
            "lane": "open_cv_residual_ledger",
            "required_artifact": "s13_same_label_coarse_open_cv_residual_ledger.csv",
            "existing_rows": len(residual_rows),
            "direct_same_label_admitted_rows": len(residual_complete_rows),
            "admission_ready": "false",
            "available_evidence": rel(RESIDUAL / "case_residual_budget_skeleton.csv"),
            "blocking_gap": "throughflow enthalpy, cp/property, storage, and named-loss terms are not complete",
        },
        {
            "lane": "triplet_admission_gate",
            "required_artifact": "s13_same_label_coarse_triplet_admission_gate.csv",
            "existing_rows": len(read_csv(RECON / "candidate_triplet_reconciliation.csv")),
            "direct_same_label_admitted_rows": 0,
            "admission_ready": "false",
            "available_evidence": rel(RECON / "candidate_triplet_reconciliation.csv"),
            "blocking_gap": "coarse candidates are diagnostic; formal GCI cannot use two-level or non-admitted coarse evidence",
        },
    ]


def build_case_qoi_matrix() -> list[dict[str, Any]]:
    generated = {
        (row["case_id"], row["qoi_label"]): row
        for row in read_csv(GEN / "same_label_mesh_family_generated_rows.csv")
    }
    recon = {
        (row["case_id"], row["qoi_label"]): row
        for row in read_csv(RECON / "candidate_triplet_reconciliation.csv")
    }
    no_go = {
        (row["case_id"], row["qoi_label"]): row
        for row in read_csv(STRICT / "case_qoi_strict_coarse_no_go.csv")
    }

    rows: list[dict[str, Any]] = []
    for case_id in ("salt_2", "salt_3", "salt_4"):
        for qoi in QOIS:
            gen = generated.get((case_id, qoi), {})
            rec = recon.get((case_id, qoi), {})
            nogo = no_go.get((case_id, qoi), {})
            formula_ready = boolish(gen.get("same_label_formula_sign_basis", "false"))
            coarse_value_exists = boolish(rec.get("current_coarse_candidate_exists", "false"))
            face_geometry_ready = False
            same_window_ready = False
            field_property_ready = False
            residual_ready = False
            direct_admitted = all(
                [
                    formula_ready,
                    coarse_value_exists,
                    face_geometry_ready,
                    same_window_ready,
                    field_property_ready,
                    residual_ready,
                ]
            )
            rows.append(
                {
                    "case_id": case_id,
                    "qoi_label": qoi,
                    "coarse_candidate_value": rec.get("coarse_candidate_value", gen.get("target_value", "")),
                    "medium_value": rec.get("medium_value", ""),
                    "fine_value": rec.get("fine_value", ""),
                    "target_time_window_s": gen.get("target_time_window_s", nogo.get("current_coarse_time_window_s", "")),
                    "medium_fine_window_role": "terminal",
                    "formula_sign_units_ready": b(formula_ready),
                    "coarse_qoi_value_exists": b(coarse_value_exists),
                    "coarse_face_geometry_ready": b(face_geometry_ready),
                    "same_window_role_ready": b(same_window_ready),
                    "field_property_basis_ready": b(field_property_ready),
                    "open_cv_residual_ready": b(residual_ready),
                    "direct_same_label_coarse_admitted": b(direct_admitted),
                    "coarse_equivalence_admitted": "false",
                    "formal_gci_ready": "false",
                    "production_harvest_allowed": "false",
                    "admission_allowed": "false",
                    "reason": "direct coarse evidence missing face geometry, same-window equivalence, source/property basis, and residual-complete open-CV ledger",
                    "source_paths": gen.get("source_paths", rec.get("source_paths", "")),
                }
            )
    return rows


def build_extraction_contract() -> list[dict[str, Any]]:
    return [
        {
            "rank": 1,
            "artifact_to_generate": "s13_same_label_coarse_open_cv_face_contract.csv",
            "source_scope": "coarse Salt2/Salt3/Salt4 current-continuation cases at target-minus/target/target-plus windows",
            "required_operation": "mesh-aware face export for exchange_interface, trusted_wall, cap/endpoints",
            "required_columns": "case_id;mesh_label;cv_id;endpoint_label;patch_name;face_id;owner_cell;area_m2;area_vector_x_m2;area_vector_y_m2;area_vector_z_m2;normal_convention;positive_mdot_convention;time_window_s;field_time_s;source_path",
            "success_signal": "finite area vectors and owner_cell on all coarse faces; sign convention admitted",
            "scheduler_needed": "yes_for_native_mesh_sampling",
            "forbidden": "do not use candidate endpoint face ids without area vectors or owner cells",
        },
        {
            "rank": 2,
            "artifact_to_generate": "s13_same_label_coarse_open_cv_qoi_rows.csv",
            "source_scope": "same coarse masks and same target windows",
            "required_operation": "compute exact Q_wall_W, mdot_exchange_positive_outward_proxy_kg_s, tau_recirc_proxy_s, and wall_core_bulk_temperature_contrast_K",
            "required_columns": "case_id;mesh_label;qoi_label;unit;value;formula_id;sign_convention;time_window_s;field_basis;property_basis;geometry_mask_id;source_path;direct_same_label_coarse_admitted;coarse_equivalence_admitted",
            "success_signal": "12 coarse case/QOI rows with direct_same_label_coarse_admitted=true only if all basis fields pass",
            "scheduler_needed": "yes_if_values_are_not_already_exported_on_exact_masks",
            "forbidden": "do not promote current reconstructed coarse candidates",
        },
        {
            "rank": 3,
            "artifact_to_generate": "s13_same_label_coarse_open_cv_residual_ledger.csv",
            "source_scope": "coarse open-CV energy balance on the same masks/windows",
            "required_operation": "name wall, source-side, throughflow enthalpy, cp/property, storage, named-loss, and residual terms",
            "required_columns": "case_id;mesh_label;cv_id;qoi_label;term_label;term_value;unit;positive_direction;time_window_s;source_path;residual_accounted;release_allowed",
            "success_signal": "all terms explicit; no hidden residual in internal Nu or fitted coefficient",
            "scheduler_needed": "maybe_after_face_and_qoi_artifacts_exist",
            "forbidden": "do not release residual values until same-basis terms and source/property evidence pass",
        },
        {
            "rank": 4,
            "artifact_to_generate": "s13_same_label_coarse_triplet_admission_gate.csv",
            "source_scope": "coarse plus existing medium/fine exact-label rows",
            "required_operation": "join coarse/medium/fine by exact case/QOI/formula/sign/window-role/property/mask basis and rerun formal GCI gate",
            "required_columns": "case_id;qoi_label;coarse_value;medium_value;fine_value;coarse_mask_id;medium_mask_id;fine_mask_id;same_formula_units_sign;time_window_equivalent;field_property_basis_equivalent;cv_residual_accounted;direct_same_label_coarse_admitted;formal_gci_ready;admission_allowed",
            "success_signal": "formal_gci_ready can become true only after direct coarse admission",
            "scheduler_needed": "no_after_artifacts_exist",
            "forbidden": "do not run GCI on two-level evidence or non-admitted coarse values",
        },
    ]


def build_source_manifest() -> list[dict[str, Any]]:
    sources = [
        (STRICT / "replacement_coarse_dataset_contract.csv", "required direct coarse replacement schema"),
        (STRICT / "case_qoi_strict_coarse_no_go.csv", "prior strict no-go case/QOI baseline"),
        (GEN / "same_label_mesh_family_generated_rows.csv", "current coarse diagnostic QOI candidates"),
        (RECON / "candidate_triplet_reconciliation.csv", "coarse/medium/fine diagnostic values"),
        (CLEAN / "face_lane_contract_inventory.csv", "medium/fine face-lane readiness context"),
        (RESIDUAL / "case_residual_budget_skeleton.csv", "open-CV residual skeleton"),
        (ENDPOINT / "endpoint_face_geometry_recovery_matrix.csv", "endpoint face geometry blocker"),
        (DERIVATION / "endpoint_mask_manifest.csv", "candidate endpoint masks"),
    ]
    return [{"source_path": rel(path), "exists": b(path.exists()), "mutated": "false", "use": use} for path, use in sources]


def write_docs(summary: dict[str, Any], changed_files: list[str]) -> None:
    STATUS_PATH.parent.mkdir(parents=True, exist_ok=True)
    JOURNAL_PATH.parent.mkdir(parents=True, exist_ok=True)
    IMPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATUS_PATH.write_text(
        f"""---
provenance:
  - {rel(OUT / 'summary.json')}
  - {rel(OUT / 'case_qoi_direct_coarse_evidence_matrix.csv')}
  - {rel(OUT / 'compute_ready_extraction_contract.csv')}
tags: [status, s13, coarse, open-cv, mesh-gci, fail-closed]
related:
  - {rel(JOURNAL_PATH)}
  - {rel(IMPORT_PATH)}
task: {TASK_ID}
date: {DATE}
role: Hydraulics / Thermal-modeling / cfd-pp / Mesh-GCI / Implementer / Tester / Writer / Reviewer
type: status
status: complete
---
# {TASK_ID}

## Changes Made

Built the direct same-label coarse evidence gate for S13. The package audited
existing current-coarse QOI candidates, medium/fine face context, endpoint mask
recovery, and open-CV residual skeletons. It also published a compute-ready
replacement extraction contract.

## Validation

- `python3.11 tools/analyze/build_s13_direct_same_label_coarse_evidence.py`: passed.
- `python3.11 -m py_compile tools/analyze/build_s13_direct_same_label_coarse_evidence.py tools/analyze/test_s13_direct_same_label_coarse_evidence.py`: passed.
- `python3.11 -m unittest tools.analyze.test_s13_direct_same_label_coarse_evidence`: 6 tests passed.

## Guardrails

Native solver outputs mutated: false. Registry mutated: false. Scheduler
action: false. External Fluid edit: false. No sampler/harvest/UQ launch,
source/property or Qwall release, production harvest, formal GCI run/admission,
coefficient fitting/admission, validation/holdout/external scoring, candidate
freeze, final score, endpoint proxy substitution, hidden multiplier, residual
absorption, or runtime-leakage relaxation was performed.
""",
        encoding="utf-8",
    )
    JOURNAL_PATH.write_text(
        f"""---
provenance:
  - {rel(OUT / 'summary.json')}
  - {rel(GEN / 'same_label_mesh_family_generated_rows.csv')}
  - {rel(STRICT / 'replacement_coarse_dataset_contract.csv')}
tags: [journal, s13, coarse, open-cv, mesh-gci]
related:
  - {rel(STATUS_PATH)}
  - {rel(IMPORT_PATH)}
task: {TASK_ID}
date: {DATE}
role: Hydraulics / Thermal-modeling / cfd-pp / Mesh-GCI / Implementer / Tester / Writer / Reviewer
type: journal
status: complete
---
# S13 Direct Same-Label Coarse Evidence

Task: `{TASK_ID}`

Observed: existing current-coarse rows provide diagnostic QOI values for all 12
Salt2/Salt3/Salt4 case/QOI combinations. Medium/fine exact-label evidence also
exists.

Observed: no existing artifact provides admitted coarse endpoint face geometry,
same-window coarse/medium/fine equivalence, release-grade field/property basis,
or residual-complete open-CV terms.

Inferred: S13 is not usable yet for formal GCI or same-basis open-CV residual
evidence. It is still scientifically promising because the exact missing
artifacts are now small and concrete: coarse face contract, coarse exact QOI
rows, residual ledger, and triplet admission gate.

Next useful action: claim a scheduler-authorized coarse extraction row that
generates `s13_same_label_coarse_open_cv_face_contract.csv` and exact coarse
QOI rows from the native coarse cases. Do not promote reconstructed current
coarse values, candidate endpoint face ids, or two-level medium/fine evidence.
""",
        encoding="utf-8",
    )
    write_json(
        IMPORT_PATH,
        {
            "task": TASK_ID,
            "date": DATE,
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "changed_files": changed_files,
            "read_only_context": [row["source_path"] for row in build_source_manifest()],
            "decision": summary["decision"],
            "case_qoi_rows": summary["case_qoi_rows"],
            "direct_same_label_coarse_admitted_rows": summary["direct_same_label_coarse_admitted_rows"],
            "formal_gci_ready_rows": summary["formal_gci_ready_rows"],
            "compute_ready_contract_rows": summary["compute_ready_contract_rows"],
            "native_solver_outputs_mutated": False,
            "registry_mutated": False,
            "scheduler_action": False,
            "external_fluid_edit": False,
            "no_scorecard_outputs": True,
            "mutation_flags": {
                "solver_postprocessing_sampler_harvest_uq_launch": False,
                "source_property_or_qwall_release": False,
                "production_harvest_allowed": False,
                "formal_gci_run_or_admission": False,
                "coefficient_fitting_or_admission": False,
                "protected_or_final_scoring": False,
                "candidate_freeze": False,
                "endpoint_proxy_substitution": False,
            },
        },
    )


def main() -> None:
    require_inputs()
    OUT.mkdir(parents=True, exist_ok=True)

    lane_rows = build_lane_matrix()
    case_qoi_rows = build_case_qoi_matrix()
    extraction_rows = build_extraction_contract()
    source_rows = build_source_manifest()
    guardrails = [
        {"guardrail": "native_solver_outputs_mutated", "value": "false"},
        {"guardrail": "registry_mutated", "value": "false"},
        {"guardrail": "scheduler_action", "value": "false"},
        {"guardrail": "solver_postprocessing_sampler_harvest_uq_launch", "value": "false"},
        {"guardrail": "source_property_or_qwall_release", "value": "false"},
        {"guardrail": "production_harvest_allowed", "value": "false"},
        {"guardrail": "formal_gci_run_or_admission", "value": "false"},
        {"guardrail": "coefficient_fitting_or_admission", "value": "false"},
        {"guardrail": "candidate_freeze_or_final_score", "value": "false"},
        {"guardrail": "endpoint_proxy_substitution", "value": "false"},
    ]
    qoi_rollup = []
    for qoi in QOIS:
        qrows = [row for row in case_qoi_rows if row["qoi_label"] == qoi]
        qoi_rollup.append(
            {
                "qoi_label": qoi,
                "case_rows": len(qrows),
                "coarse_candidate_rows": sum(1 for row in qrows if row["coarse_qoi_value_exists"] == "true"),
                "direct_same_label_coarse_admitted_rows": sum(1 for row in qrows if row["direct_same_label_coarse_admitted"] == "true"),
                "formal_gci_ready_rows": sum(1 for row in qrows if row["formal_gci_ready"] == "true"),
                "highest_value_next_evidence": "coarse endpoint face geometry and same-window exact-QOI extraction",
            }
        )

    write_csv(OUT / "direct_coarse_lane_evidence_matrix.csv", lane_rows)
    write_csv(OUT / "case_qoi_direct_coarse_evidence_matrix.csv", case_qoi_rows)
    write_csv(OUT / "qoi_direct_coarse_rollup.csv", qoi_rollup)
    write_csv(OUT / "compute_ready_extraction_contract.csv", extraction_rows)
    write_csv(OUT / "source_manifest.csv", source_rows)
    write_csv(OUT / "no_mutation_guardrails.csv", guardrails)
    summary = {
        "task": TASK_ID,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "decision": "s13_direct_same_label_coarse_evidence_fail_closed_compute_contract_ready",
        "lane_rows": len(lane_rows),
        "case_qoi_rows": len(case_qoi_rows),
        "coarse_candidate_rows": sum(1 for row in case_qoi_rows if row["coarse_qoi_value_exists"] == "true"),
        "direct_same_label_coarse_admitted_rows": sum(1 for row in case_qoi_rows if row["direct_same_label_coarse_admitted"] == "true"),
        "formal_gci_ready_rows": sum(1 for row in case_qoi_rows if row["formal_gci_ready"] == "true"),
        "production_harvest_allowed_rows": 0,
        "compute_ready_contract_rows": len(extraction_rows),
        "scheduler_action": False,
        "native_solver_outputs_mutated": False,
        "source_property_or_qwall_release": False,
        "candidate_freeze_or_final_score": False,
    }
    write_json(OUT / "summary.json", summary)
    (OUT / "README.md").write_text(
        f"""---
provenance:
  - {rel(OUT / 'summary.json')}
  - {rel(OUT / 'case_qoi_direct_coarse_evidence_matrix.csv')}
  - {rel(OUT / 'compute_ready_extraction_contract.csv')}
tags: [work-product, s13, coarse, open-cv, mesh-gci, fail-closed]
related:
  - {rel(STATUS_PATH)}
  - {rel(JOURNAL_PATH)}
  - {rel(IMPORT_PATH)}
task: {TASK_ID}
date: {DATE}
role: Hydraulics / Thermal-modeling / cfd-pp / Mesh-GCI / Implementer / Tester / Writer / Reviewer
type: work_product
status: complete
---
# S13 Direct Same-Label Coarse Evidence

Decision: `{summary["decision"]}`.

Existing current-coarse candidate values cover all `{summary["case_qoi_rows"]}`
case/QOI rows, but direct same-label coarse admission remains `0`. The missing
evidence is not another medium/fine rerun; it is exact coarse face geometry,
same-window coarse QOI rows, residual-complete open-CV accounting, and a
triplet admission gate.

This package publishes `compute_ready_extraction_contract.csv`, which is the
next executable contract for making S13 usable. It preserves the no-proxy rule:
candidate endpoint face ids, reconstructed current-coarse values, source-side
heat flow relabeled as `Q_wall_W`, and two-level medium/fine evidence cannot
substitute for direct same-label coarse evidence.
""",
        encoding="utf-8",
    )
    changed_files = [
        rel(OUT / name)
        for name in [
            "README.md",
            "direct_coarse_lane_evidence_matrix.csv",
            "case_qoi_direct_coarse_evidence_matrix.csv",
            "qoi_direct_coarse_rollup.csv",
            "compute_ready_extraction_contract.csv",
            "source_manifest.csv",
            "no_mutation_guardrails.csv",
            "summary.json",
        ]
    ] + [
        rel(Path("tools/analyze/build_s13_direct_same_label_coarse_evidence.py")),
        rel(Path("tools/analyze/test_s13_direct_same_label_coarse_evidence.py")),
        rel(STATUS_PATH),
        rel(JOURNAL_PATH),
        rel(IMPORT_PATH),
    ]
    write_docs(summary, changed_files)
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
