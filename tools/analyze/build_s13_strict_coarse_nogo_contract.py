#!/usr/bin/env python3
"""Build the S13 strict same-label coarse no-go contract.

This package turns the existing S13 coarse-candidate evidence into an
auditable disposition: candidate coarse rows may be reported as diagnostics,
but they are not admitted as same-label coarse evidence for formal GCI until
the coarse-equivalence contract criteria pass. This script does not launch
jobs, harvest fields, mutate native outputs, release Qwall/source properties,
or admit coefficients.
"""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TASK_ID = "TODO-S13-STRICT-COARSE-NOGO-CONTRACT-2026-07-22"
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_s13_strict_coarse_nogo_contract"

CONTRACT = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_s13_coarse_equivalence_open_cv_heatflow_contract"
COARSE_UNLOCK = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_s13_same_label_coarse_gci_unlock"
RECONCILIATION = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_s13_candidate_coarse_medium_fine_reconciliation"
CLEAN_READINESS = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_s13_clean_sampler_gci_readiness"
SPLIT_RERUN = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_s13_medium_fine_exact_label_split_rerun"
MESH_UNCERTAINTY = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_mesh_uncertainty"

QOI_LABELS = [
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


def count_data_rows(path: Path) -> int:
    if not path.exists() or path.stat().st_size == 0:
        return 0
    with path.open(encoding="utf-8") as handle:
        return max(sum(1 for _ in handle) - 1, 0)


def require_inputs() -> None:
    required = [
        CONTRACT / "auditable_coarse_equivalence_contract.csv",
        CONTRACT / "coarse_basis_resolution.csv",
        COARSE_UNLOCK / "coarse_same_label_unlock_matrix.csv",
        COARSE_UNLOCK / "s13_qoi_coarse_disposition.csv",
        RECONCILIATION / "candidate_triplet_reconciliation.csv",
        RECONCILIATION / "qoi_reconciliation_summary.csv",
        CLEAN_READINESS / "latest_sampler_success_gate.csv",
        CLEAN_READINESS / "gci_go_no_go_matrix.csv",
        SPLIT_RERUN / "aggregated_exact_label_qoi_rows.csv",
    ]
    missing = [rel(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("missing strict coarse no-go inputs: " + "; ".join(missing))


def build_criterion_rows() -> list[dict[str, Any]]:
    contract_rows = read_csv(CONTRACT / "auditable_coarse_equivalence_contract.csv")
    unlock_rows = {row["criterion"]: row for row in read_csv(COARSE_UNLOCK / "coarse_same_label_unlock_matrix.csv")}
    rows: list[dict[str, Any]] = []
    for row in contract_rows:
        criterion = row["criterion"]
        unlock = unlock_rows.get(criterion, {})
        current_pass = boolish(unlock.get("coarse_same_label_pass", "false"))
        rows.append(
            {
                "criterion": criterion,
                "necessity": row.get("necessity", unlock.get("necessity", "")),
                "auditable_acceptance_text": row.get("auditable_acceptance_text", ""),
                "current_status": unlock.get("current_status", row.get("current_status", "")),
                "current_evidence_or_gap": unlock.get("current_evidence_or_gap", row.get("current_evidence_or_gap", "")),
                "strict_coarse_equivalence_pass": bool_text(current_pass),
                "admission_effect_if_satisfied": row.get("admission_effect_if_satisfied", unlock.get("admission_effect_if_satisfied", "")),
                "no_go_effect_now": "blocks same-label coarse admission, formal GCI, production harvest, and coefficient admission",
            }
        )
    return rows


def basis_by_case_qoi() -> dict[tuple[str, str], dict[str, str]]:
    basis = {}
    for row in read_csv(CONTRACT / "coarse_basis_resolution.csv"):
        basis[(row["case_id"], row["qoi_label"])] = row
    return basis


def build_case_qoi_rows() -> list[dict[str, Any]]:
    basis = basis_by_case_qoi()
    rows: list[dict[str, Any]] = []
    for row in read_csv(RECONCILIATION / "candidate_triplet_reconciliation.csv"):
        key = (row["case_id"], row["qoi_label"])
        basis_row = basis.get(key, {})
        coarse_admitted = boolish(row.get("coarse_equivalence_admitted", "false")) and boolish(
            row.get("direct_same_label_coarse_admitted", "false")
        )
        no_go_reason = basis_row.get("reason") or "same-label coarse equivalence is not admitted"
        rows.append(
            {
                "case_id": row["case_id"],
                "qoi_label": row["qoi_label"],
                "unit": row["unit"],
                "current_coarse_candidate_exists": bool_text(boolish(row.get("current_coarse_candidate_exists", "false"))),
                "current_coarse_candidate_value": row["coarse_candidate_value"],
                "medium_value": row["medium_value"],
                "fine_value": row["fine_value"],
                "current_coarse_time_window_s": basis_row.get("current_coarse_time_window_s", ""),
                "current_coarse_formula_sign_basis": basis_row.get("current_coarse_formula_sign_basis", ""),
                "strict_same_label_mesh_rows_coarse_medium_fine": basis_row.get("strict_same_label_mesh_rows_coarse_medium_fine", ""),
                "direct_same_label_coarse_admitted": bool_text(boolish(row.get("direct_same_label_coarse_admitted", "false"))),
                "coarse_equivalence_admitted": bool_text(boolish(row.get("coarse_equivalence_admitted", "false"))),
                "strict_coarse_no_go": bool_text(not coarse_admitted),
                "formal_gci_status": "blocked_strict_same_label_coarse_not_admitted",
                "diagnostic_use_allowed": row.get("diagnostic_use_allowed", "True"),
                "production_harvest_allowed": "false",
                "admission_allowed": "false",
                "coefficient_fit_allowed": "false",
                "no_go_reason": no_go_reason,
                "source_paths": row.get("source_paths", ""),
            }
        )
    return rows


def build_qoi_rows(case_qoi_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    recon_summary = {row["qoi_label"]: row for row in read_csv(RECONCILIATION / "qoi_reconciliation_summary.csv")}
    gci_gate = {row["qoi_label"]: row for row in read_csv(CLEAN_READINESS / "gci_go_no_go_matrix.csv")}
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in case_qoi_rows:
        grouped[row["qoi_label"]].append(row)

    rows: list[dict[str, Any]] = []
    for qoi in QOI_LABELS:
        qrows = grouped.get(qoi, [])
        admitted = [row for row in qrows if row["coarse_equivalence_admitted"] == "true"]
        summary = recon_summary.get(qoi, {})
        gate = gci_gate.get(qoi, {})
        rows.append(
            {
                "qoi_label": qoi,
                "case_count": len(qrows),
                "current_coarse_candidate_rows": len([row for row in qrows if row["current_coarse_candidate_exists"] == "true"]),
                "admitted_same_label_coarse_rows": len(admitted),
                "strict_coarse_no_go_rows": len([row for row in qrows if row["strict_coarse_no_go"] == "true"]),
                "max_coarse_fine_relative_percent_vs_fine": summary.get("max_coarse_fine_relative_percent_vs_fine", ""),
                "max_medium_fine_relative_percent_vs_fine": summary.get("max_medium_fine_relative_percent_vs_fine", ""),
                "medium_fine_exact_label_status": "complete_diagnostic",
                "required_face_lane": gate.get("required_face_lane", ""),
                "face_contract_ready_all_case_meshes": gate.get("face_contract_ready_all_case_meshes", ""),
                "formal_gci_status": "blocked_strict_same_label_coarse_not_admitted",
                "production_harvest_allowed": "false",
                "admission_allowed": "false",
                "coefficient_fit_allowed": "false",
                "qoi_disposition": (
                    "diagnostic_low_spread_but_no_formal_gci"
                    if qoi == "Q_wall_W"
                    else "diagnostic_proxy_mesh_sensitive_no_formal_gci"
                ),
            }
        )
    return rows


def build_unlock_contract(criteria_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    failed = [row["criterion"] for row in criteria_rows if row["strict_coarse_equivalence_pass"] != "true"]
    failed_text = ";".join(failed)
    return [
        {
            "rank": 1,
            "step": "preserve_current_no_go",
            "required_evidence": "current coarse candidates remain diagnostic reference rows only",
            "success_criterion": f"formal GCI and production harvest stay blocked while failed criteria exist: {failed_text}",
            "scheduler_required": "false",
            "forbidden": "do not relabel source-side heat flow as Q_wall_W; do not borrow unrelated coarse or GCI rows",
        },
        {
            "rank": 2,
            "step": "generate_or_admit_direct_same_label_coarse_rows",
            "required_evidence": "topology-derived coarse CV, exchange interface, wall/core band, face areas/normals, field/property basis, and same window role matching medium/fine exact labels",
            "success_criterion": "each case/QOI has direct_same_label_coarse_admitted=true and coarse_equivalence_admitted=true",
            "scheduler_required": "maybe_only_if_new_coarse_sampling_needed",
            "forbidden": "do not use reconstructed current-coarse candidates as admitted evidence without the criteria audit",
        },
        {
            "rank": 3,
            "step": "rerun_formal_gci_gate",
            "required_evidence": "medium/fine exact-label rows plus admitted same-label coarse rows for the same QOI/case",
            "success_criterion": "formal GCI-ready rows are produced only for admitted triplets",
            "scheduler_required": "false_for_gate_after_rows_exist",
            "forbidden": "do not run formal GCI on two-level evidence or diagnostic coarse candidates",
        },
        {
            "rank": 4,
            "step": "same_qoi_uq_before_harvest_or_admission",
            "required_evidence": "same-window UQ on exact S13 exchange QOIs and source/property validity for heat-flow terms",
            "success_criterion": "production harvest/admission only after exact-label UQ and mesh disposition are both closed",
            "scheduler_required": "maybe_for_uq_execution",
            "forbidden": "do not fit exchange-cell coefficients or admit residual support before same-QOI UQ",
        },
    ]


def build_replacement_dataset_contract() -> list[dict[str, Any]]:
    required_cases = "salt_2;salt_3;salt_4"
    required_qois = ";".join(QOI_LABELS)
    return [
        {
            "artifact": "s13_same_label_coarse_open_cv_face_contract.csv",
            "row_unit": "one row per coarse case/endpoint face",
            "required_cases": required_cases,
            "required_qois": "mdot_exchange_positive_outward_proxy_kg_s;Q_wall_W;source_side_heat_flow_W_if_used",
            "required_columns": "case_id;mesh_label;cv_id;endpoint_label;patch_name;face_id;owner_cell;area_m2;area_vector_x_m2;area_vector_y_m2;area_vector_z_m2;normal_convention;positive_mdot_convention;time_window_s;field_time_s;source_path",
            "acceptance": "all coarse endpoint faces have finite area vectors, owner cells, source paths, and an admitted sign convention matching medium/fine exact labels",
            "forbidden_substitution": "seed/candidate face ids without geometry; source-side heat flow relabeled as wall Q_wall_W",
        },
        {
            "artifact": "s13_same_label_coarse_open_cv_qoi_rows.csv",
            "row_unit": "one row per coarse case/QOI",
            "required_cases": required_cases,
            "required_qois": required_qois,
            "required_columns": "case_id;mesh_label;qoi_label;unit;value;formula_id;sign_convention;time_window_s;field_basis;property_basis;geometry_mask_id;source_path;direct_same_label_coarse_admitted;coarse_equivalence_admitted",
            "acceptance": "12 case/QOI rows have the same formula, units, sign convention, time-window role, field basis, property basis, and mask provenance as medium/fine rows",
            "forbidden_substitution": "current reconstructed coarse candidates; two-level medium/fine rows; proxy QOI renamed to exact QOI",
        },
        {
            "artifact": "s13_same_label_coarse_open_cv_residual_ledger.csv",
            "row_unit": "one row per coarse case/CV/QOI residual term",
            "required_cases": required_cases,
            "required_qois": "Q_wall_W;mdot_exchange_positive_outward_proxy_kg_s;wall_core_bulk_temperature_contrast_K",
            "required_columns": "case_id;mesh_label;cv_id;qoi_label;term_label;term_value;unit;positive_direction;time_window_s;source_path;residual_accounted;release_allowed",
            "acceptance": "open-CV boundary, exchange, wall, source/sink, storage, and residual terms are explicit before production harvest",
            "forbidden_substitution": "unclosed residuals hidden in coefficients or internal Nu corrections",
        },
        {
            "artifact": "s13_same_label_coarse_triplet_admission_gate.csv",
            "row_unit": "one row per case/QOI coarse-medium-fine triplet",
            "required_cases": required_cases,
            "required_qois": required_qois,
            "required_columns": "case_id;qoi_label;coarse_value;medium_value;fine_value;coarse_mask_id;medium_mask_id;fine_mask_id;same_formula_units_sign;time_window_equivalent;field_property_basis_equivalent;cv_residual_accounted;direct_same_label_coarse_admitted;formal_gci_ready;admission_allowed",
            "acceptance": "formal_gci_ready may be true only when every equivalence flag and direct_same_label_coarse_admitted are true",
            "forbidden_substitution": "formal GCI on two-level evidence or diagnostic coarse candidates",
        },
    ]


def build_source_manifest() -> list[dict[str, Any]]:
    sources = [
        (CONTRACT / "README.md", "read-only coarse/open-CV contract"),
        (CONTRACT / "auditable_coarse_equivalence_contract.csv", "read-only required criteria"),
        (CONTRACT / "coarse_basis_resolution.csv", "read-only case/QOI basis disposition"),
        (COARSE_UNLOCK / "coarse_same_label_unlock_matrix.csv", "read-only prior unlock matrix"),
        (COARSE_UNLOCK / "s13_qoi_coarse_disposition.csv", "read-only prior QOI disposition"),
        (RECONCILIATION / "candidate_triplet_reconciliation.csv", "read-only candidate triplets"),
        (RECONCILIATION / "qoi_reconciliation_summary.csv", "read-only QOI spread summary"),
        (CLEAN_READINESS / "latest_sampler_success_gate.csv", "read-only sampler completion gate"),
        (CLEAN_READINESS / "gci_go_no_go_matrix.csv", "read-only latest GCI go/no-go"),
        (SPLIT_RERUN / "aggregated_exact_label_qoi_rows.csv", "read-only medium/fine exact-label rows"),
        (MESH_UNCERTAINTY / "README.md", "read-only mesh uncertainty context"),
    ]
    return [{"source_path": rel(path), "exists": bool_text(path.exists()), "use": use} for path, use in sources]


def build_readme(summary: dict[str, Any]) -> str:
    return f"""---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_s13_coarse_equivalence_open_cv_heatflow_contract/auditable_coarse_equivalence_contract.csv
  - work_products/2026-07/2026-07-22/2026-07-22_s13_coarse_equivalence_open_cv_heatflow_contract/coarse_basis_resolution.csv
  - work_products/2026-07/2026-07-22/2026-07-22_s13_candidate_coarse_medium_fine_reconciliation/candidate_triplet_reconciliation.csv
  - work_products/2026-07/2026-07-22/2026-07-22_s13_clean_sampler_gci_readiness/latest_sampler_success_gate.csv
tags: [work-product, s13, recirculation, mesh-gci, coarse-equivalence, fail-closed]
related:
  - .agent/status/2026-07-22_TODO-S13-STRICT-COARSE-NOGO-CONTRACT-2026-07-22.md
  - .agent/journal/2026-07-22/s13-strict-coarse-nogo-contract.md
task: TODO-S13-STRICT-COARSE-NOGO-CONTRACT-2026-07-22
date: 2026-07-22
role: Hydraulics / Thermal-modeling / cfd-pp / Mesh-GCI / Implementer / Tester / Writer / Reviewer
type: work_product
status: complete
---
# S13 Strict Coarse No-Go Contract

Decision: `{summary["decision"]}`.

This package resolves the strict same-label coarse disposition for the current
S13 exchange-cell evidence. Current coarse candidate rows exist for all
`{summary["case_qoi_rows"]}` case/QOI combinations, but admitted same-label
coarse rows remain `{summary["admitted_same_label_coarse_rows"]}`. Therefore
formal GCI, production harvest, Qwall/source-property release, and coefficient
admission remain blocked.

The latest medium/fine exact-label split rerun is complete and should not be
duplicated unless the input contract changes. The remaining blocker is not
medium/fine sampling; it is direct same-label coarse equivalence.

`Q_wall_W` remains the only low-spread diagnostic heat-flow lane, but low spread
does not waive the coarse-equivalence contract. Source-side heat-flow
equivalence must remain a separate same-basis QOI and must not be relabeled as
wall `Q_wall_W`.

Outputs:

- `strict_coarse_equivalence_criteria.csv`: required criteria and current pass/fail.
- `case_qoi_strict_coarse_no_go.csv`: per-case/QOI coarse no-go audit.
- `qoi_formal_gci_no_go_matrix.csv`: per-QOI GCI/harvest/admission disposition.
- `coarse_unlock_action_contract.csv`: exact evidence needed to reopen GCI.
- `replacement_coarse_dataset_contract.csv`: exact replacement artifact schema
  required if current coarse remains no-go.

Guardrails preserved: no native solver output mutation, registry/admission
mutation, scheduler action, solver/postprocessing/sampler/harvest/UQ launch,
Fluid/external edit, thesis edit, source/property or Qwall release, formal GCI
run/admission, production harvest, coefficient fitting, protected scoring,
candidate freeze, or final-score claim.
"""


def main() -> None:
    require_inputs()
    OUT.mkdir(parents=True, exist_ok=True)

    criteria_rows = build_criterion_rows()
    case_qoi_rows = build_case_qoi_rows()
    qoi_rows = build_qoi_rows(case_qoi_rows)
    unlock_rows = build_unlock_contract(criteria_rows)
    replacement_rows = build_replacement_dataset_contract()
    source_rows = build_source_manifest()
    guardrails = {
        "native_solver_outputs_mutated": False,
        "registry_mutated": False,
        "scheduler_action": False,
        "solver_postprocessing_sampler_harvest_uq_launch": False,
        "fluid_or_external_repo_edited": False,
        "thesis_current_latex_edited": False,
        "source_property_or_qwall_release": False,
        "formal_gci_run_or_admission": False,
        "production_harvest_allowed": False,
        "coefficient_fitting_or_admission": False,
        "validation_holdout_external_scoring": False,
        "candidate_freeze_or_final_score": False,
    }

    summary = {
        "task": TASK_ID,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "decision": "s13_strict_same_label_coarse_no_go_formal_gci_blocked",
        "criteria_rows": len(criteria_rows),
        "criteria_pass_rows": sum(1 for row in criteria_rows if row["strict_coarse_equivalence_pass"] == "true"),
        "case_qoi_rows": len(case_qoi_rows),
        "current_coarse_candidate_rows": sum(1 for row in case_qoi_rows if row["current_coarse_candidate_exists"] == "true"),
        "admitted_same_label_coarse_rows": sum(1 for row in case_qoi_rows if row["coarse_equivalence_admitted"] == "true"),
        "strict_coarse_no_go_rows": sum(1 for row in case_qoi_rows if row["strict_coarse_no_go"] == "true"),
        "qoi_rows": len(qoi_rows),
        "formal_gci_ready_rows": 0,
        "production_harvest_allowed_rows": 0,
        "medium_fine_exact_label_rows": count_data_rows(SPLIT_RERUN / "aggregated_exact_label_qoi_rows.csv"),
        "replacement_contract_rows": len(replacement_rows),
        "guardrails": guardrails,
    }

    write_csv(
        OUT / "strict_coarse_equivalence_criteria.csv",
        criteria_rows,
        [
            "criterion",
            "necessity",
            "auditable_acceptance_text",
            "current_status",
            "current_evidence_or_gap",
            "strict_coarse_equivalence_pass",
            "admission_effect_if_satisfied",
            "no_go_effect_now",
        ],
    )
    write_csv(
        OUT / "case_qoi_strict_coarse_no_go.csv",
        case_qoi_rows,
        [
            "case_id",
            "qoi_label",
            "unit",
            "current_coarse_candidate_exists",
            "current_coarse_candidate_value",
            "medium_value",
            "fine_value",
            "current_coarse_time_window_s",
            "current_coarse_formula_sign_basis",
            "strict_same_label_mesh_rows_coarse_medium_fine",
            "direct_same_label_coarse_admitted",
            "coarse_equivalence_admitted",
            "strict_coarse_no_go",
            "formal_gci_status",
            "diagnostic_use_allowed",
            "production_harvest_allowed",
            "admission_allowed",
            "coefficient_fit_allowed",
            "no_go_reason",
            "source_paths",
        ],
    )
    write_csv(
        OUT / "qoi_formal_gci_no_go_matrix.csv",
        qoi_rows,
        [
            "qoi_label",
            "case_count",
            "current_coarse_candidate_rows",
            "admitted_same_label_coarse_rows",
            "strict_coarse_no_go_rows",
            "max_coarse_fine_relative_percent_vs_fine",
            "max_medium_fine_relative_percent_vs_fine",
            "medium_fine_exact_label_status",
            "required_face_lane",
            "face_contract_ready_all_case_meshes",
            "formal_gci_status",
            "production_harvest_allowed",
            "admission_allowed",
            "coefficient_fit_allowed",
            "qoi_disposition",
        ],
    )
    write_csv(
        OUT / "coarse_unlock_action_contract.csv",
        unlock_rows,
        ["rank", "step", "required_evidence", "success_criterion", "scheduler_required", "forbidden"],
    )
    write_csv(
        OUT / "replacement_coarse_dataset_contract.csv",
        replacement_rows,
        [
            "artifact",
            "row_unit",
            "required_cases",
            "required_qois",
            "required_columns",
            "acceptance",
            "forbidden_substitution",
        ],
    )
    write_csv(OUT / "source_manifest.csv", source_rows, ["source_path", "exists", "use"])
    write_csv(OUT / "no_mutation_guardrails.csv", [{"guardrail": key, "value": bool_text(value)} for key, value in guardrails.items()], ["guardrail", "value"])
    write_json(OUT / "summary.json", summary)
    (OUT / "README.md").write_text(build_readme(summary), encoding="utf-8")

    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
