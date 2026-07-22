#!/usr/bin/env python3
"""Build a case-by-segment LitRev admission engine package."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


TASK = "TODO-LITREV-FINAL-CASE-BY-SEGMENT-ADMISSION-ENGINE-2026-07-22"
DATE = "2026-07-22"
ROOT = Path(__file__).resolve().parents[2]
OUT_REL = Path("work_products/2026-07/2026-07-22/2026-07-22_litrev_final_case_by_segment_admission_engine")
OUT = ROOT / OUT_REL

REGIME = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_1d_regime_map_nondimensional_closure_eligibility"
SEGMENT_MAP = REGIME / "segment_case_regime_map.csv"
CLOSURE_DECISIONS = REGIME / "closure_eligibility_decisions.csv"
PRESSURE_CONTRACT = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_1d_final_pressure_energy_basis_and_bc_equivalence_contract"
PRESSURE_BASIS = PRESSURE_CONTRACT / "pressure_energy_basis_contract.csv"
HEATLOSS_CONTRACT = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_heat_loss_source_inventory_material_geometry_phases"
HEAT_PATH_LANES = HEATLOSS_CONTRACT / "heat_path_lane_contract.csv"
LITREV_FINAL = (
    ROOT
    / "../papers/UTexas_Research/LitRev-start---Closure-and-Modeling-Decisions-for-Developing-HITEC-Flow-TAMU-MSFL/data/audit_outputs/final_release"
).resolve()

LITREV_FILES = [
    "HITEC_final_source_validity_envelope.csv",
    "HITEC_final_active_equation_gate_matrix.csv",
    "HITEC_final_Nu_correlation_gate_matrix.csv",
    "HITEC_final_property_gate_matrix.csv",
    "HITEC_final_minor_loss_K_gate_matrix.csv",
    "HITEC_final_CFD_coefficient_gate_matrix.csv",
    "HITEC_final_ROM_admission_gate.csv",
    "HITEC_final_model_form_hierarchy.csv",
    "HITEC_final_reverse_flow_taxonomy.csv",
    "HITEC_final_pressure_energy_accounting_rules.csv",
    "HITEC_final_unresolved_claims.csv",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT.resolve()))
    except ValueError:
        return str(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: Iterable[dict[str, Any]], fieldnames: list[str]) -> int:
    materialized = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in materialized:
            writer.writerow({field: row.get(field, "") for field in fieldnames})
    return len(materialized)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def admission_status(row: dict[str, str]) -> tuple[str, str]:
    blockers = row.get("blocking_reasons", "")
    eligibility = row.get("closure_eligibility", "")
    if row.get("coefficient_admission_statuses") != "no_coefficient_admission":
        return "active", "coefficient admission already present"
    if "same_QOI_UQ_missing" in blockers or "coarse_no_gci" in blockers:
        return "unresolved", "same-QOI UQ and/or mesh/GCI missing"
    if "source_envelope_not_fit" in blockers:
        return "source-bounded", "source envelope missing for fit use"
    if "diagnostic" in eligibility:
        return "diagnostic", "diagnostic architecture only"
    return "appendix-only", "precheck evidence only"


def case_segment_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for src in read_csv(SEGMENT_MAP):
        status, reason = admission_status(src)
        rows.append(
            {
                "case_id": src["case_id"],
                "segment_or_span": src["span"],
                "Re_range": src["Re_range"],
                "Pr_range": src["Pr_range"],
                "Gr_range": src["Gr_range"],
                "Gr_star_range": "missing_not_in_current_regime_map",
                "Ri_range": src["Ri_range"],
                "Ra_range": src["Ra_range"],
                "Bo_range": "missing_not_in_current_regime_map",
                "Gz_range": src["Gz_range"],
                "L_over_Dh_range": "missing_not_in_current_regime_map",
                "hydraulic_reset_distance_m_range": src["hydraulic_reset_distance_m_range"],
                "thermal_reset_distance_m_range": "missing_not_in_current_regime_map",
                "pressure_velocity_basis": "blocked_until_pressure_energy_basis_contract_and_endpoint_rows_are_released",
                "boundary_condition_class": "from_heat_path_lane_contract_precheck",
                "property_package": src["property_modes"],
                "topology_flags": src["recirculation_statuses"],
                "closure_status": status,
                "missing_input_reasons": reason + ";" + src.get("blocking_reasons", ""),
                "allowed_use": "regime_evidence_and_model_form_selector_not_fit_or_score",
                "source_path": rel(SEGMENT_MAP),
            }
        )
    return rows


def closure_family_rows() -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for row in read_csv(CLOSURE_DECISIONS):
        out.append(
            {
                "model_family": row["model_family"],
                "evidence_rows_reviewed": row["evidence_rows_reviewed"],
                "eligible_rows": row["eligible_rows"],
                "admitted_rows": row["admitted_rows"],
                "closure_status": row["decision"],
                "reason": row["reason"],
                "next_gate": row["next_gate"],
                "source_path": rel(CLOSURE_DECISIONS),
            }
        )
    return out


def missing_field_rows(case_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    fields = [
        "Gr_star_range",
        "Bo_range",
        "L_over_Dh_range",
        "thermal_reset_distance_m_range",
        "same_QOI_UQ",
        "formal_mesh_GCI",
        "source_property_release",
    ]
    out = []
    for field in fields:
        if field in {"same_QOI_UQ", "formal_mesh_GCI", "source_property_release"}:
            affected = len(case_rows)
            status = "blocked"
            reason = "required by current closure/admission rows"
        else:
            affected = sum(1 for row in case_rows if row.get(field, "").startswith("missing"))
            status = "missing" if affected else "present"
            reason = "not emitted by current regime map"
        out.append(
            {
                "field": field,
                "affected_case_segment_rows": affected,
                "status": status,
                "reason": reason,
                "next_extraction_task": "extend regime map extractor or release source/property/UQ gate before coefficient admission",
            }
        )
    return out


def litrev_source_rows() -> list[dict[str, str]]:
    rows = []
    for name in LITREV_FILES:
        path = LITREV_FINAL / name
        row_count = 0
        columns = ""
        if path.exists():
            with path.open(newline="", encoding="utf-8") as handle:
                reader = csv.reader(handle)
                header = next(reader, [])
                row_count = sum(1 for _ in reader)
                columns = ";".join(header[:12])
        rows.append(
            {
                "source_path": rel(path),
                "exists": str(path.exists()).lower(),
                "row_count": row_count,
                "first_columns": columns,
                "use": "LitRev final-release controlling layer provenance",
            }
        )
    return rows


def source_manifest_rows() -> list[dict[str, str]]:
    paths = [SEGMENT_MAP, CLOSURE_DECISIONS, PRESSURE_BASIS, HEAT_PATH_LANES, *[LITREV_FINAL / name for name in LITREV_FILES]]
    return [{"source_path": rel(path), "exists": str(path.exists()).lower(), "use": "input"} for path in paths]


def build() -> dict[str, Any]:
    OUT.mkdir(parents=True, exist_ok=True)
    case_rows = case_segment_rows()
    closure_rows = closure_family_rows()
    missing_rows = missing_field_rows(case_rows)
    litrev_rows = litrev_source_rows()
    counts = {
        "case_segment_admission_matrix.csv": write_csv(
            OUT / "case_segment_admission_matrix.csv",
            case_rows,
            [
                "case_id",
                "segment_or_span",
                "Re_range",
                "Pr_range",
                "Gr_range",
                "Gr_star_range",
                "Ri_range",
                "Ra_range",
                "Bo_range",
                "Gz_range",
                "L_over_Dh_range",
                "hydraulic_reset_distance_m_range",
                "thermal_reset_distance_m_range",
                "pressure_velocity_basis",
                "boundary_condition_class",
                "property_package",
                "topology_flags",
                "closure_status",
                "missing_input_reasons",
                "allowed_use",
                "source_path",
            ],
        ),
        "closure_family_decisions.csv": write_csv(
            OUT / "closure_family_decisions.csv",
            closure_rows,
            ["model_family", "evidence_rows_reviewed", "eligible_rows", "admitted_rows", "closure_status", "reason", "next_gate", "source_path"],
        ),
        "missing_input_ledger.csv": write_csv(
            OUT / "missing_input_ledger.csv",
            missing_rows,
            ["field", "affected_case_segment_rows", "status", "reason", "next_extraction_task"],
        ),
        "litrev_final_source_register.csv": write_csv(
            OUT / "litrev_final_source_register.csv",
            litrev_rows,
            ["source_path", "exists", "row_count", "first_columns", "use"],
        ),
        "source_manifest.csv": write_csv(
            OUT / "source_manifest.csv",
            source_manifest_rows(),
            ["source_path", "exists", "use"],
        ),
    }
    status_counts: dict[str, int] = {}
    for row in case_rows:
        status_counts[row["closure_status"]] = status_counts.get(row["closure_status"], 0) + 1
    decision = {
        "task": TASK,
        "decision": "case_by_segment_admission_engine_fail_closed_no_coefficients_admitted",
        "case_segment_rows": len(case_rows),
        "closure_status_counts": status_counts,
        "closure_family_admitted_rows": sum(int(row["admitted_rows"]) for row in closure_rows),
        "litrev_sources_recorded": len(litrev_rows),
        "created_utc": utc_now(),
    }
    write_json(OUT / "engine_decision.json", decision)
    summary = {
        "task": TASK,
        "date": DATE,
        "output_dir": rel(OUT),
        "counts": counts,
        **decision,
        "native_output_mutation": False,
        "solver_or_postprocessing_launch": False,
        "source_property_release": False,
        "coefficient_admission": False,
    }
    write_json(OUT / "summary.json", summary)
    (OUT / "README.md").write_text(
        f"""---
provenance:
  - {rel(SEGMENT_MAP)}
  - {rel(CLOSURE_DECISIONS)}
  - {rel(LITREV_FINAL / 'HITEC_final_source_validity_envelope.csv')}
tags: [litrev, admission-engine, regime-map, fail-closed]
task: {TASK}
date: {DATE}
status: complete
---
# LitRev Final Case-By-Segment Admission Engine

Decision: `{decision['decision']}`.

The engine emits one row per current case/span regime-map row and records the
LitRev final-release controlling CSV paths. Current output is fail-closed:
ordinary single-stream, pressure K, internal Nu, and exchange-cell families have
0 admitted closure rows. Missing same-QOI UQ, formal mesh/GCI, source-property
release, and several nondimensional fields block coefficient admission.

Use `case_segment_admission_matrix.csv`, `closure_family_decisions.csv`, and
`missing_input_ledger.csv` as the next admission-control layer. Do not fit,
score, or silently extrapolate from these rows.
""",
        encoding="utf-8",
    )
    return summary


def main() -> None:
    print(json.dumps(build(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
