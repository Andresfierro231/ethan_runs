#!/usr/bin/env python3
"""Build the wall thermal-circuit forward-model readiness package."""

from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TASK = "TODO-PREDICT-WALL-THERMAL-CIRCUIT"
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_predict_wall_thermal_circuit"
INVENTORY = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_heat_loss_source_inventory_material_geometry_phases"
MATERIAL_GEOMETRY = INVENTORY / "material_geometry_phase_table.csv"
HEAT_PATHS = INVENTORY / "source_inventory_by_heat_path.csv"
PASSIVE_H2 = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_thermal_passive_h2_multi_train_corrected_radiation_smoke/case_corrected_radiation_summary.csv"
OLD_WALL_STUDY = ROOT / "work_products/2026-07/2026-07-17/2026-07-17_wall_thermal_circuit_study/summary.json"
GEOMETRY = ROOT / "reference/geometry_reference.md"

SEGMENT_COMPONENTS = [
    ("heater_lower_leg", "steel pipe plus heater boundary", "internal convection;steel conduction;insulation;external convection;radiation"),
    ("cooler_hx_branch", "steel pipe plus jacket/HX", "internal convection;steel conduction;cooler jacket UA;external balance"),
    ("downcomer_right_vertical", "insulated steel pipe", "internal convection;steel conduction;insulation;external convection;radiation"),
    ("upcomer_left_vertical", "insulated steel pipe with recirculation caveat", "internal convection;steel conduction;insulation;external convection;radiation;recirculation exchange flag"),
    ("test_section_quartz_span", "bare quartz test section", "internal convection;quartz conduction;external convection;radiation;test-section source/loss"),
    ("junction_stub_connector", "3D connector/stub region", "named loss;contact/conduction;external loss;residual owner"),
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT.resolve()))
    except ValueError:
        return str(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def component_rows() -> list[dict[str, str]]:
    material_by_scope = {row["material_geometry_scope"]: row for row in read_csv(MATERIAL_GEOMETRY)}
    rows = []
    for segment_id, physical_scope, components in SEGMENT_COMPONENTS:
        is_test = segment_id == "test_section_quartz_span"
        for component in components.split(";"):
            key = "quartz_or_bare_test_section" if is_test and component == "quartz conduction" else "wall_conduction"
            basis = material_by_scope.get(key, {})
            status = basis.get("current_status", "unresolved")
            if "recirculation" in component:
                status = "blocked_by_exchange_state"
            if "cooler jacket" in component:
                status = "partial_setup_model_lane"
            if "named loss" in component:
                status = "junction_blocked"
            rows.append(
                {
                    "segment_id": segment_id,
                    "physical_scope": physical_scope,
                    "thermal_component": component,
                    "material_geometry_status": status,
                    "runtime_allowed_now": "false",
                    "required_release_or_handoff": basis.get("next_required_action", "source-bounded release or separate extraction required"),
                    "diagnostic_evidence_allowed": "wallHeatFlux and sampled fields post-prediction only",
                }
            )
    return rows


def passive_operator_rows() -> list[dict[str, Any]]:
    return [
        {
            "case_id": row["case_id"],
            "corrected_outer_surface_convection_W": row["corrected_outer_surface_convection_W"],
            "corrected_outer_surface_radiation_W": row["corrected_outer_surface_radiation_W"],
            "corrected_outer_surface_total_W": row["corrected_outer_surface_total_W"],
            "numeric_q_loss_release": row["numeric_q_loss_release"],
            "admission_or_score": row["admission_or_score"],
            "runtime_use": "diagnostic_context_only_until_same_QOI_and_source_release",
        }
        for row in read_csv(PASSIVE_H2)
    ]


def release_gate_rows() -> list[dict[str, str]]:
    rows = []
    for row in read_csv(HEAT_PATHS):
        blocked = "no release" in row["current_status"] or "partial" in row["current_status"]
        rows.append(
            {
                "heat_path": row["heat_path"],
                "segment_family": row["segment_family"],
                "current_status": row["current_status"],
                "runtime_policy": row["runtime_policy"],
                "release_gate": "blocked" if blocked else "review",
                "not_allowed_as_runtime_input": row["not_allowed_as_runtime_input"],
            }
        )
    return rows


def handoff_rows() -> list[dict[str, str]]:
    return [
        {"handoff_id": "H1", "target": "segment thermal scorecards", "needed_inputs": "segment UA/resistance terms with material provenance", "status": "blocked_until_release"},
        {"handoff_id": "H2", "target": "M3+TS", "needed_inputs": "test-section quartz/source/loss lane and passive operator release", "status": "blocked_until_source_basis"},
        {"handoff_id": "H3", "target": "S12 TP-first thermal development", "needed_inputs": "bulk-to-TP projection plus wall/core exchange UQ", "status": "diagnostic_handoff_ready"},
        {"handoff_id": "H4", "target": "Fluid runtime implementation", "needed_inputs": "external Fluid board row and exact runtime fields", "status": "not_claimed_here"},
    ]


def build_package() -> dict[str, Any]:
    OUT.mkdir(parents=True, exist_ok=True)
    components = component_rows()
    passive = passive_operator_rows()
    gates = release_gate_rows()
    handoff = handoff_rows()
    manifest = [
        {"source_id": "material_geometry", "path": rel(MATERIAL_GEOMETRY), "use": "material/geometry readiness by component"},
        {"source_id": "heat_paths", "path": rel(HEAT_PATHS), "use": "heat-path release policy"},
        {"source_id": "passive_h2", "path": rel(PASSIVE_H2), "use": "outer-surface convection/radiation diagnostic magnitudes"},
        {"source_id": "prior_wall_study", "path": rel(OLD_WALL_STUDY), "use": "prior coupled wall-circuit study context"},
        {"source_id": "geometry_reference", "path": rel(GEOMETRY), "use": "segment/test-section geometry naming"},
    ]
    write_csv(OUT / "segment_wall_circuit_components.csv", components, list(components[0].keys()))
    write_csv(OUT / "passive_operator_context.csv", passive, list(passive[0].keys()))
    write_csv(OUT / "release_gate_matrix.csv", gates, list(gates[0].keys()))
    write_csv(OUT / "handoff_inputs.csv", handoff, list(handoff[0].keys()))
    write_csv(OUT / "source_manifest.csv", manifest, list(manifest[0].keys()))
    status_counts = Counter(row["material_geometry_status"] for row in components)
    summary = {
        "task": TASK,
        "created_utc": utc_now(),
        "decision": "wall_thermal_circuit_contract_ready_no_numeric_release",
        "output_dir": rel(OUT),
        "segment_component_rows": len(components),
        "passive_operator_rows": len(passive),
        "release_gate_rows": len(gates),
        "blocked_release_rows": sum(1 for row in gates if row["release_gate"] == "blocked"),
        "component_status_counts": dict(status_counts),
        "numeric_q_loss_release_rows": sum(1 for row in passive if row["numeric_q_loss_release"] == "True"),
        "final_score_rows": 0,
    }
    write_json(OUT / "summary.json", summary)
    (OUT / "README.md").write_text(
        "# Wall Thermal-Circuit Model\n\n"
        "This package converts the material/geometry and passive-H2 evidence into a segment-local wall-circuit contract. It does not release numeric heat-loss inputs or mutate Fluid.\n\n"
        "Decision: `wall_thermal_circuit_contract_ready_no_numeric_release`.\n",
        encoding="utf-8",
    )
    return summary


def main() -> None:
    print(json.dumps(build_package(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
