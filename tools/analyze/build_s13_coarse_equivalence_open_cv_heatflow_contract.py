#!/usr/bin/env python3
"""S13 coarse-equivalence, open-CV, and heat-flow contract.

This is a no-launch/no-admission audit. It resolves whether existing
current-coarse S13 rows can be used as the coarse member of the medium/fine
mesh family, and records when open recirculation control volumes and averaged
values are scientifically acceptable.
"""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TASK_ID = "TODO-S13-COARSE-EQUIVALENCE-OPEN-CV-HEATFLOW-CONTRACT-2026-07-22"
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / (
    "work_products/2026-07/2026-07-22/"
    "2026-07-22_s13_coarse_equivalence_open_cv_heatflow_contract"
)

MF_DISPOSITION = ROOT / (
    "work_products/2026-07/2026-07-22/"
    "2026-07-22_s13_medium_fine_mesh_gci_disposition"
)
MESH_FAMILY = ROOT / (
    "work_products/2026-07/2026-07-22/"
    "2026-07-22_s13_upcomer_exchange_same_label_mesh_family_generation"
)
SOURCE_EQ = ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_s13_upcomer_exchange_source_side_heatflow_equivalence_uq_prereq"
)
SAME_QOI_UQ = ROOT / (
    "work_products/2026-07/2026-07-22/"
    "2026-07-22_s13_upcomer_exchange_same_qoi_neighbor_uq_after_target_plus"
)

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
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


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


def require_inputs() -> None:
    required = [
        MF_DISPOSITION / "summary.json",
        MF_DISPOSITION / "qoi_mesh_disposition_summary.csv",
        MESH_FAMILY / "same_label_mesh_family_generated_rows.csv",
        MESH_FAMILY / "qoi_mesh_level_preflight_matrix.csv",
        SOURCE_EQ / "source_side_qoi_contract.csv",
        SOURCE_EQ / "case_heatflow_equivalence_basis.csv",
        SAME_QOI_UQ / "same_qoi_temporal_uq_case_rows.csv",
        SAME_QOI_UQ / "heat_flow_match_diagnostics.csv",
    ]
    missing = [rel(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("missing S13 contract inputs: " + "; ".join(missing))


def build_coarse_basis_resolution(
    coarse_rows: list[dict[str, str]], preflight_rows: list[dict[str, str]]
) -> list[dict[str, Any]]:
    coarse_by_case_qoi = {
        (row["case_id"], row["qoi_label"]): row
        for row in coarse_rows
        if row["mesh_level"] == "current_coarse_continuation"
        and row["row_generation_status"] == "generated_current_coarse_only_not_gci"
    }
    preflight_by_qoi_mesh = {
        (row["qoi_label"], row["mesh_level"]): row
        for row in preflight_rows
        if row["mesh_level"] in {"coarse", "medium", "fine"}
    }
    output: list[dict[str, Any]] = []
    for case_id in sorted({case for case, _qoi in coarse_by_case_qoi}):
        for qoi in QOI_LABELS:
            coarse = coarse_by_case_qoi[(case_id, qoi)]
            strict_cells_ready = [
                preflight_by_qoi_mesh[(qoi, mesh)]["strict_same_label_mesh_rows"] for mesh in ["coarse", "medium", "fine"]
            ]
            output.append(
                {
                    "case_id": case_id,
                    "qoi_label": qoi,
                    "current_coarse_candidate_exists": True,
                    "current_coarse_time_window_s": coarse["target_time_window_s"],
                    "current_coarse_target_value": coarse["target_value"],
                    "current_coarse_formula_sign_basis": coarse["same_label_formula_sign_basis"],
                    "strict_same_label_mesh_rows_coarse_medium_fine": ";".join(strict_cells_ready),
                    "direct_same_label_coarse_admitted": False,
                    "coarse_equivalence_admitted": False,
                    "formal_gci_unlocked": False,
                    "resolution": "current_coarse_reference_candidate_only_not_equivalent_yet",
                    "reason": (
                        "current-coarse reconstructed target rows exist, but the strict "
                        "same-label mesh-level preflight has zero admitted coarse/medium/fine "
                        "cells and medium/fine sampler rows come from a separate exact-label "
                        "runtime family"
                    ),
                }
            )
    return output


def build_equivalence_contract() -> list[dict[str, Any]]:
    criteria = [
        (
            "qoi_label_formula_sign_units",
            "required",
            "same formula, units, positive direction, clipping convention, and no source-side/Qwall relabel",
            "not_admitted_currently",
            "current rows state formula/sign basis, but no audited joined triplet contract exists",
        ),
        (
            "geometry_mask_provenance",
            "required",
            "same topology-derived CV, exchange interface, wall/core band, face areas, and normals at each mesh",
            "not_admitted_currently",
            "medium/fine masks are mesh-level sampler masks; current coarse is reconstructed from prior topology packages",
        ),
        (
            "time_window_equivalence",
            "required",
            "same physical window role or documented terminal-equivalence map with source roots and sampled fields",
            "not_admitted_currently",
            "coarse windows are continuation retained windows; medium/fine terminal windows are not strict same-time companions",
        ),
        (
            "field_source_property_basis",
            "required",
            "same OpenFOAM field source basis, property basis, and pressure/velocity basis for the QOI",
            "not_admitted_currently",
            "source/property and cp/viscosity releases remain separate gates",
        ),
        (
            "closed_or_residual_accounted_cv",
            "required_for_admission",
            "all open-boundary advective, exchange, wall, source/sink, storage, and residual terms explicit",
            "not_admitted_currently",
            "open-CV diagnostics exist, but no production energy residual is closed on the same basis",
        ),
        (
            "same_qoi_uq_and_mesh_disposition",
            "required",
            "same-QOI temporal UQ plus mesh/GCI or accepted mesh-spread disposition on the exact labels",
            "partially_available_diagnostic",
            "temporal UQ exists and Q_wall_W medium/fine spread is low; formal GCI and proxy stability fail closed",
        ),
    ]
    return [
        {
            "criterion": name,
            "necessity": necessity,
            "auditable_acceptance_text": acceptance,
            "current_status": status,
            "current_evidence_or_gap": gap,
            "admission_effect_if_satisfied": "can consider coarse-equivalent triplet only after all required criteria pass",
        }
        for name, necessity, acceptance, status, gap in criteria
    ]


def build_open_cv_policy() -> list[dict[str, Any]]:
    return [
        {
            "use_case": "diagnostic_exchange_or_heat_accounting",
            "open_cv_allowed": True,
            "closed_cv_required": False,
            "conditions": "all cut surfaces named; normal convention explicit; storage/advective/source/wall terms reported; residual not hidden",
            "allowed_outputs": "diagnostic Q_wall_W, source-side heat-flow comparison, averaged states, provisional residual support",
            "forbidden_outputs": "coefficient admission; formal conservation claim; ordinary one-stream Nu/f_D/K substitution",
        },
        {
            "use_case": "formal_energy_or_pressure_residual",
            "open_cv_allowed": True,
            "closed_cv_required": False,
            "conditions": "open CV is acceptable only if every boundary flux term is included in the residual equation with sign convention",
            "allowed_outputs": "explicit residual with uncertainty and named unclosed terms",
            "forbidden_outputs": "claiming residual is a closure coefficient or absorbing it into internal Nu",
        },
        {
            "use_case": "throughflow_plus_recirc_exchange_cell_admission",
            "open_cv_allowed": False,
            "closed_cv_required": True,
            "conditions": "defensible recirculation CV, exchange interface, wall/core band, same-QOI UQ, mesh/GCI, source/property basis, and bounded residual",
            "allowed_outputs": "candidate coefficient review only after all gates pass",
            "forbidden_outputs": "coefficient fitting from open/proxy-only CV evidence",
        },
    ]


def build_averaging_policy() -> list[dict[str, Any]]:
    return [
        {
            "quantity_type": "intensive_state",
            "examples": "T_recirc, T_core, rho, mu, cp",
            "averaged_values_allowed": True,
            "required_weighting": "volume-, mass-, or area-weighted basis stated per QOI",
            "admission_limit": "usable as reduced-model state only with same-mask UQ and property provenance",
        },
        {
            "quantity_type": "flux_or_integral",
            "examples": "Q_wall_W, mdot_exchange, source-side heat flow",
            "averaged_values_allowed": False,
            "required_weighting": "integrate signed face/cell contributions first; averages may be secondary diagnostics only",
            "admission_limit": "do not replace integrals with area-average fields times approximate area unless equivalence is proved",
        },
        {
            "quantity_type": "residual",
            "examples": "energy residual, pressure residual",
            "averaged_values_allowed": False,
            "required_weighting": "compute from conserved/integral terms with sign convention",
            "admission_limit": "average residual indicators are screening metrics only",
        },
    ]


def build_heatflow_focus(
    qwall_summary_rows: list[dict[str, str]], heat_rows: list[dict[str, str]]
) -> list[dict[str, Any]]:
    qwall_summary = {row["qoi_label"]: row for row in qwall_summary_rows}
    qwall = qwall_summary["Q_wall_W"]
    output: list[dict[str, Any]] = []
    for row in heat_rows:
        output.append(
            {
                "case_id": row["case_id"],
                "target_time_window_s": row["target_time_window_s"],
                "Q_wall_W": row["Q_wall_W"],
                "Q_source_side_net_static_bc_W": row["Q_source_side_net_static_bc_W"],
                "qwall_to_source_side_ratio": row["qwall_to_source_side_ratio"],
                "cp_required_to_match_Q_wall_J_kg_K": row["cp_required_to_match_Q_wall_J_kg_K"],
                "cp_required_to_match_source_side_J_kg_K": row["cp_required_to_match_source_side_J_kg_K"],
                "heat_flow_match_status": row["heat_flow_match_status"],
                "medium_fine_Q_wall_max_spread_percent": qwall["max_medium_fine_relative_percent_vs_fine"],
                "production_focus": "focus_on_source_side_equivalence_and_energy_residual_not_coefficient_fit",
                "admission_allowed_now": False,
                "reason": "Q_wall_W mesh spread is low, but source-side heat is a distinct QOI and current mdot*DeltaT scale is not a physical match",
            }
        )
    return output


def build_production_gate() -> list[dict[str, Any]]:
    return [
        {
            "gate": "current_coarse_reference_rows",
            "status": "diagnostic_available",
            "pass": True,
            "evidence": "12 current-coarse reconstructed target rows exist for four QOIs and three cases",
            "consequence": "can be audited as coarse-reference candidates",
        },
        {
            "gate": "same_label_coarse_equivalence",
            "status": "fail_closed_not_admitted",
            "pass": False,
            "evidence": "no joined contract proves geometry/time/source/property equivalence to medium/fine sampler rows",
            "consequence": "formal GCI remains blocked",
        },
        {
            "gate": "open_cv_for_diagnostics",
            "status": "allowed_with_explicit_residual",
            "pass": True,
            "evidence": "diagnostic use allowed when all open-boundary terms and residual are labeled",
            "consequence": "can continue heat-flow and exchange diagnostics",
        },
        {
            "gate": "closed_cv_for_exchange_cell_admission",
            "status": "required_not_satisfied",
            "pass": False,
            "evidence": "no same-basis bounded energy residual, source/property release, or formal mesh/GCI",
            "consequence": "no exchange-cell coefficient fitting or admission",
        },
    ]


def build_source_manifest() -> list[dict[str, Any]]:
    return [
        {"artifact": "medium_fine_mesh_gci_disposition", "path": rel(MF_DISPOSITION / "summary.json"), "role": "controls medium/fine diagnostic result", "mutation_status": "read_only"},
        {"artifact": "current_coarse_generated_rows", "path": rel(MESH_FAMILY / "same_label_mesh_family_generated_rows.csv"), "role": "candidate current-coarse rows and formulas", "mutation_status": "read_only"},
        {"artifact": "mesh_level_preflight", "path": rel(MESH_FAMILY / "qoi_mesh_level_preflight_matrix.csv"), "role": "strict same-label mesh-level admission status", "mutation_status": "read_only"},
        {"artifact": "source_side_qoi_contract", "path": rel(SOURCE_EQ / "source_side_qoi_contract.csv"), "role": "distinct source-side heat-flow label contract", "mutation_status": "read_only"},
        {"artifact": "heat_flow_match_diagnostics", "path": rel(SAME_QOI_UQ / "heat_flow_match_diagnostics.csv"), "role": "Qwall/source-side mismatch and cp-scale diagnostics", "mutation_status": "read_only"},
    ]


def build_readme(summary: dict[str, Any]) -> str:
    return f"""---
provenance:
  - {rel(MF_DISPOSITION / "summary.json")}
  - {rel(MESH_FAMILY / "same_label_mesh_family_generated_rows.csv")}
  - {rel(MESH_FAMILY / "qoi_mesh_level_preflight_matrix.csv")}
  - {rel(SAME_QOI_UQ / "heat_flow_match_diagnostics.csv")}
tags: [work-product, s13, recirculation, open-cv, coarse-equivalence, source-side-heat-flow]
related:
  - .agent/status/2026-07-22_{TASK_ID}.md
  - .agent/journal/2026-07-22/s13-coarse-equivalence-open-cv-heatflow-contract.md
task: {TASK_ID}
date: 2026-07-22
role: Hydraulics / Thermal-modeling / cfd-pp / Mesh-GCI / Implementer / Tester / Writer
type: work_product
status: complete
---
# S13 Coarse-Equivalence / Open-CV / Heat-Flow Contract

Decision: `{summary["decision"]}`.

Current-coarse reconstructed rows exist and are useful as reference candidates,
but they are not admitted as same-label coarse evidence for formal GCI. The
contract in this package states the criteria required to admit them later.

Open recirculation CVs are allowed for diagnostics if all open-boundary terms,
signs, and residuals are explicit. A closed or residual-complete CV is required
before exchange-cell coefficient fitting or admission.

`Q_wall_W` is the only S13 exchange QOI with low medium/fine spread, so heat-flow
matching should focus on source-side heat-flow equivalence and the same-basis
energy residual. Source-side heat flow remains a distinct QOI and must not be
relabeled as `Q_wall_W`.
"""


def build() -> dict[str, Any]:
    require_inputs()
    OUT.mkdir(parents=True, exist_ok=True)

    mf_summary = read_json(MF_DISPOSITION / "summary.json")
    qwall_summary_rows = read_csv(MF_DISPOSITION / "qoi_mesh_disposition_summary.csv")
    coarse_rows = read_csv(MESH_FAMILY / "same_label_mesh_family_generated_rows.csv")
    preflight_rows = read_csv(MESH_FAMILY / "qoi_mesh_level_preflight_matrix.csv")
    heat_rows = read_csv(SAME_QOI_UQ / "heat_flow_match_diagnostics.csv")

    coarse_basis = build_coarse_basis_resolution(coarse_rows, preflight_rows)
    equivalence_contract = build_equivalence_contract()
    open_cv_policy = build_open_cv_policy()
    averaging_policy = build_averaging_policy()
    heatflow_focus = build_heatflow_focus(qwall_summary_rows, heat_rows)
    production_gate = build_production_gate()
    source_manifest = build_source_manifest()

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "decision": "coarse_reference_candidate_only_equivalence_contract_defined_no_gci_no_admission",
        "source_medium_fine_decision": mf_summary["decision"],
        "qoi_count": len(QOI_LABELS),
        "current_coarse_candidate_rows": len(coarse_basis),
        "coarse_equivalence_admitted_rows": 0,
        "formal_gci_unlocked": False,
        "open_cv_diagnostic_allowed": True,
        "closed_or_residual_complete_cv_required_for_admission": True,
        "averaged_intensive_values_allowed_with_weights": True,
        "averaged_flux_substitution_allowed": False,
        "source_side_heatflow_focus_rows": len(heatflow_focus),
        "production_harvest_allowed": False,
        "admission_allowed": False,
        "coefficient_admission": False,
        "source_property_release": False,
        "Qwall_release": False,
        "scheduler_action": False,
        "native_solver_outputs_mutated": False,
        "registry_or_admission_mutated": False,
        "validation_holdout_external_scoring": False,
        "s11_s12_s13_s15_s6_trigger": False,
        "generated_docs_index_refreshed": False,
    }

    write_csv(
        OUT / "coarse_basis_resolution.csv",
        coarse_basis,
        [
            "qoi_label",
            "case_id",
            "current_coarse_candidate_exists",
            "current_coarse_time_window_s",
            "current_coarse_target_value",
            "current_coarse_formula_sign_basis",
            "strict_same_label_mesh_rows_coarse_medium_fine",
            "direct_same_label_coarse_admitted",
            "coarse_equivalence_admitted",
            "formal_gci_unlocked",
            "resolution",
            "reason",
        ],
    )
    write_csv(
        OUT / "auditable_coarse_equivalence_contract.csv",
        equivalence_contract,
        [
            "criterion",
            "necessity",
            "auditable_acceptance_text",
            "current_status",
            "current_evidence_or_gap",
            "admission_effect_if_satisfied",
        ],
    )
    write_csv(
        OUT / "open_cv_use_policy.csv",
        open_cv_policy,
        ["use_case", "open_cv_allowed", "closed_cv_required", "conditions", "allowed_outputs", "forbidden_outputs"],
    )
    write_csv(
        OUT / "averaged_value_policy.csv",
        averaging_policy,
        ["quantity_type", "examples", "averaged_values_allowed", "required_weighting", "admission_limit"],
    )
    write_csv(
        OUT / "source_side_heatflow_focus.csv",
        heatflow_focus,
        [
            "case_id",
            "target_time_window_s",
            "Q_wall_W",
            "Q_source_side_net_static_bc_W",
            "qwall_to_source_side_ratio",
            "cp_required_to_match_Q_wall_J_kg_K",
            "cp_required_to_match_source_side_J_kg_K",
            "heat_flow_match_status",
            "medium_fine_Q_wall_max_spread_percent",
            "production_focus",
            "admission_allowed_now",
            "reason",
        ],
    )
    write_csv(
        OUT / "production_admission_gate.csv",
        production_gate,
        ["gate", "status", "pass", "evidence", "consequence"],
    )
    write_csv(
        OUT / "source_manifest.csv",
        source_manifest,
        ["artifact", "path", "role", "mutation_status"],
    )
    write_json(OUT / "summary.json", summary)
    (OUT / "README.md").write_text(build_readme(summary), encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=None)
    args = parser.parse_args()
    global OUT
    if args.output_dir is not None:
        OUT = args.output_dir
    print(json.dumps(build(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
