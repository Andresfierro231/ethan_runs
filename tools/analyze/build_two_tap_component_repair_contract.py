#!/usr/bin/env python3
"""Build AGENT-525 two-tap component repair contract."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


TASK = "AGENT-525"
DATE = "2026-07-17"
ROOT = Path(__file__).resolve().parents[2]
OUT_REL = Path("work_products/2026-07/2026-07-17/2026-07-17_two_tap_component_repair_contract")
OUT = ROOT / OUT_REL

AG523 = ROOT / "work_products/2026-07/2026-07-17/2026-07-17_named_pressure_extraction_readiness"
MINOR = ROOT / "work_products/2026-07/2026-07-08/2026-07-08_minor_loss_two_tap"
TAP = ROOT / "work_products/2026-07/2026-07-14/2026-07-14_hydraulic_tap_length_admission_refresh"
RAW = ROOT / "work_products/2026-07/2026-07-15/2026-07-15_staged_closure_qoi_pressure_sbatch"
CORNER = ROOT / "work_products/2026-07/2026-07-17/2026-07-17_val_salt2_pressure_evidence_corner_k_diagnosis"

SOURCES = {
    "ag523_readiness": AG523 / "named_pressure_readiness.csv",
    "ag523_queue": AG523 / "next_pressure_extraction_queue.csv",
    "minor_loss_two_tap": MINOR / "minor_loss_two_tap.csv",
    "tap_centerline_lengths": TAP / "tap_centerline_length_table.csv",
    "component_k_recomputed": TAP / "component_cluster_k_recomputed_admission_table.csv",
    "raw_pressure_two_tap_harvest": RAW / "raw_pressure_two_tap_harvest.csv",
    "corner_k_gate_matrix": CORNER / "corner_k_gate_matrix.csv",
    "corner_next_queue": CORNER / "next_pressure_evidence_queue.csv",
}

TARGET_COLUMNS = [
    "target_id",
    "case_id",
    "feature",
    "readiness_status",
    "blocking_fields",
    "centerline_length_status",
    "centerline_tap_length_m",
    "current_centerline_K_local",
    "current_component_admission_status",
    "ordinary_admission_now",
    "immediate_required_repair",
    "future_extractor_priority",
    "source_paths",
]

FIELD_COLUMNS = [
    "field",
    "definition",
    "units",
    "required_for_gate",
    "current_status",
    "acceptance_rule",
    "reject_if_missing_or_ambiguous",
    "source_paths",
]

SCHEMA_COLUMNS = ["table_name", "column", "units", "required", "reason"]
GATE_COLUMNS = ["gate", "target_rows", "required_fields", "pass_rule", "current_status", "forbidden_shortcut"]
SUMMARY_COLUMNS = ["category", "count", "interpretation"]
MANIFEST_COLUMNS = ["source_id", "path", "exists", "role"]


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


def write_csv(path: Path, rows: Iterable[dict[str, Any]], columns: list[str]) -> int:
    materialized = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in materialized:
            writer.writerow({column: "" if row.get(column) is None else str(row.get(column, "")) for column in columns})
    return len(materialized)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def require_sources() -> None:
    missing = [rel(path) for path in SOURCES.values() if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing AGENT-525 source files: " + ", ".join(missing))


def index_by_case_feature(rows: list[dict[str, str]]) -> dict[tuple[str, str], dict[str, str]]:
    return {(row.get("case_id", ""), row.get("feature", "")): row for row in rows}


def build_targets() -> list[dict[str, Any]]:
    readiness = [
        row
        for row in read_csv(SOURCES["ag523_readiness"])
        if row["readiness_status"] == "extraction_required_component_or_cluster"
    ]
    tap_rows = index_by_case_feature(read_csv(SOURCES["tap_centerline_lengths"]))
    component_rows = index_by_case_feature(read_csv(SOURCES["component_k_recomputed"]))
    targets = []
    for row in readiness:
        feature = row["span_or_feature"]
        key = (row["case_id"], feature)
        tap = tap_rows.get(key, {})
        component = component_rows.get(key, {})
        targets.append(
            {
                "target_id": row["row_id"],
                "case_id": row["case_id"],
                "feature": feature,
                "readiness_status": row["readiness_status"],
                "blocking_fields": row["blocking_fields"],
                "centerline_length_status": tap.get("centerline_length_status", "missing"),
                "centerline_tap_length_m": tap.get("centerline_tap_length_m", ""),
                "current_centerline_K_local": component.get("K_local_centerline", ""),
                "current_component_admission_status": component.get("admission_status", "missing"),
                "ordinary_admission_now": "no",
                "immediate_required_repair": "final_pressure_basis;final_velocity_basis;physically_comparable_straight_reference;same_qoi_mesh_time_UQ;component_isolation",
                "future_extractor_priority": 1,
                "source_paths": f"{rel(SOURCES['ag523_readiness'])};{rel(SOURCES['tap_centerline_lengths'])};{rel(SOURCES['component_k_recomputed'])}",
            }
        )
    return targets


def build_field_contract() -> list[dict[str, Any]]:
    common_sources = f"{rel(SOURCES['ag523_queue'])};{rel(SOURCES['corner_next_queue'])}"
    return [
        {
            "field": "final_pressure_basis",
            "definition": "Explicit static/total/p_rgh basis with hydrostatic and kinetic terms stated.",
            "units": "text",
            "required_for_gate": "pressure_basis_resolved",
            "current_status": "missing_or_proxy",
            "acceptance_rule": "basis is reproducible and no pressure term is double-counted",
            "reject_if_missing_or_ambiguous": "yes",
            "source_paths": common_sources,
        },
        {
            "field": "final_velocity_basis",
            "definition": "Local bulk velocity or dynamic pressure basis used to normalize K.",
            "units": "m/s or Pa",
            "required_for_gate": "velocity_basis_resolved",
            "current_status": "mean/proxy",
            "acceptance_rule": "basis tied to the same window, local density, and component section",
            "reject_if_missing_or_ambiguous": "yes",
            "source_paths": common_sources,
        },
        {
            "field": "centerline_tap_length_m",
            "definition": "Centerline distance between upstream and downstream taps.",
            "units": "m",
            "required_for_gate": "geometry_normalization",
            "current_status": "available_for_targets_but_not_sufficient",
            "acceptance_rule": "reported from mesh centerline or raw tap geometry with endpoint labels",
            "reject_if_missing_or_ambiguous": "yes",
            "source_paths": rel(SOURCES["tap_centerline_lengths"]),
        },
        {
            "field": "straight_loss_subtraction_pa",
            "definition": "Straight-pipe pressure loss removed from feature pressure loss.",
            "units": "Pa",
            "required_for_gate": "local_K_nonnegative_after_reference",
            "current_status": "over_subtracts_for_current_centerline_reference",
            "acceptance_rule": "physically comparable straight span; nonnegative local K is possible without hidden clipping",
            "reject_if_missing_or_ambiguous": "yes",
            "source_paths": f"{rel(SOURCES['component_k_recomputed'])};{rel(SOURCES['corner_k_gate_matrix'])}",
        },
        {
            "field": "component_isolation_label",
            "definition": "Whether the row isolates a local component or contains reset/development/branch-apparent loss.",
            "units": "text",
            "required_for_gate": "component_isolated",
            "current_status": "not_isolated",
            "acceptance_rule": "local component K separated from reset, development, and branch-apparent effects",
            "reject_if_missing_or_ambiguous": "yes",
            "source_paths": common_sources,
        },
        {
            "field": "RAF_RMF_SVF",
            "definition": "Reverse area, reverse mass, and secondary-velocity fractions adjacent to taps.",
            "units": "fraction",
            "required_for_gate": "ordinary_non_recirculating_coefficient",
            "current_status": "material_reverse_flow_present_in_related rows",
            "acceptance_rule": "ordinary rows require RAF < 0.01 and RMF < 0.01; otherwise diagnostic/section-effective only",
            "reject_if_missing_or_ambiguous": "yes",
            "source_paths": f"{rel(SOURCES['ag523_queue'])};{rel(SOURCES['raw_pressure_two_tap_harvest'])}",
        },
        {
            "field": "same_qoi_mesh_time_UQ",
            "definition": "Mesh/time uncertainty for the same local pressure-loss QoI.",
            "units": "Pa and/or percent",
            "required_for_gate": "publication_grade_coefficient",
            "current_status": "missing",
            "acceptance_rule": "same QoI over a mesh/time family or explicit non-GCI uncertainty flag",
            "reject_if_missing_or_ambiguous": "yes",
            "source_paths": rel(SOURCES["ag523_queue"]),
        },
    ]


def build_schema() -> list[dict[str, Any]]:
    columns = [
        ("case_id", "text", "join to case/registry evidence"),
        ("feature", "text", "local component or connector name"),
        ("time_window", "s", "same-window pressure/velocity/recirculation basis"),
        ("p_upstream_pa", "Pa", "raw pressure basis endpoint"),
        ("p_downstream_pa", "Pa", "raw pressure basis endpoint"),
        ("pressure_basis", "text", "static/total/p_rgh and corrections"),
        ("hydrostatic_correction_pa", "Pa", "avoid buoyancy double-counting"),
        ("kinetic_correction_pa", "Pa", "avoid dynamic-head double-counting"),
        ("straight_loss_subtraction_pa", "Pa", "local component isolation"),
        ("local_dynamic_pressure_pa", "Pa", "K normalization"),
        ("K_apparent", "dimensionless", "diagnostic apparent feature loss"),
        ("K_local", "dimensionless", "candidate after straight-loss subtraction"),
        ("RAF", "fraction", "ordinary-vs-recirculation gate"),
        ("RMF", "fraction", "ordinary-vs-recirculation gate"),
        ("SVF", "fraction", "secondary-flow diagnostic"),
        ("mesh_time_uncertainty", "text", "same-QOI uncertainty gate"),
        ("admission_status", "text", "explicit admitted/diagnostic/blocked label"),
    ]
    return [
        {
            "table_name": "future_two_tap_component_repair_output",
            "column": column,
            "units": units,
            "required": "yes",
            "reason": reason,
        }
        for column, units, reason in columns
    ]


def build_gate_matrix(targets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    n_targets = len(targets)
    return [
        {
            "gate": "pressure_and_velocity_basis",
            "target_rows": n_targets,
            "required_fields": "final_pressure_basis;final_velocity_basis;density_basis",
            "pass_rule": "all bases explicit and same-window",
            "current_status": "blocked",
            "forbidden_shortcut": "score K from pressure proxy or mean velocity proxy",
        },
        {
            "gate": "straight_reference",
            "target_rows": n_targets,
            "required_fields": "centerline_tap_length_m;straight_loss_subtraction_pa;reference_span_label",
            "pass_rule": "local K remains physically interpretable after straight-loss subtraction",
            "current_status": "blocked_current_centerline_reference_over_subtracts",
            "forbidden_shortcut": "clip negative K to zero or use dz proxy",
        },
        {
            "gate": "component_isolation",
            "target_rows": n_targets,
            "required_fields": "component_isolation_label;reset_development_exclusion",
            "pass_rule": "component loss separated from branch-apparent and reset/development losses",
            "current_status": "blocked",
            "forbidden_shortcut": "name a cluster or branch-apparent loss as universal component K",
        },
        {
            "gate": "recirculation_policy",
            "target_rows": n_targets,
            "required_fields": "RAF;RMF;SVF;steady_window",
            "pass_rule": "ordinary coefficient only if RAF < 0.01 and RMF < 0.01",
            "current_status": "blocked_until_same-window masks exist",
            "forbidden_shortcut": "ordinary f_D/K from material reverse-flow sections",
        },
        {
            "gate": "same_qoi_mesh_time_UQ",
            "target_rows": n_targets,
            "required_fields": "mesh_family;time_window;uncertainty_bound",
            "pass_rule": "same pressure-loss QoI uncertainty attached or row remains diagnostic",
            "current_status": "blocked",
            "forbidden_shortcut": "reuse unrelated mesh/GCI or fabricate monotonicity",
        },
    ]


def build_manifest() -> list[dict[str, Any]]:
    return [{"source_id": key, "path": rel(path), "exists": path.exists(), "role": "read-only contract source"} for key, path in SOURCES.items()]


def build_summary_rows(targets: list[dict[str, Any]], fields: list[dict[str, Any]], gates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    statuses = Counter(row["current_component_admission_status"] for row in targets)
    return [
        {"category": "component_repair_target_rows", "count": len(targets), "interpretation": "AGENT-523 component/cluster rows nearest to repair."},
        {"category": "ordinary_admitted_now", "count": 0, "interpretation": "No target is currently admitted as ordinary K/f_D evidence."},
        {"category": "field_contract_rows", "count": len(fields), "interpretation": "Required fields for the future repair extractor."},
        {"category": "acceptance_gate_rows", "count": len(gates), "interpretation": "Predeclared gates before coefficient use."},
        {"category": "blocked_mesh_gci_after_tap_refresh", "count": statuses.get("blocked_mesh_gci_after_tap_refresh", 0), "interpretation": "Current component table status for the three targets."},
    ]


def write_readme(path: Path, summary: dict[str, Any]) -> None:
    path.write_text(
        f"""---
provenance:
  - {rel(SOURCES['ag523_readiness'])}
  - {rel(SOURCES['component_k_recomputed'])}
  - {rel(SOURCES['corner_k_gate_matrix'])}
tags: [pressure-ledger, two-tap, component-k, extraction-contract]
related:
  - .agent/status/2026-07-17_AGENT-525.md
  - .agent/journal/2026-07-17/two-tap-component-repair-contract.md
task: {TASK}
date: {DATE}
role: Hydraulics/Implementer/Tester/Writer
type: work_product
status: complete
---
# Two-Tap Component Repair Contract

Generated: `{summary['generated_at_utc']}`

## Decision

This package implements the first AGENT-523 queue item as a future extraction
contract. It does not admit any component K row.

## Outputs

- `component_repair_targets.csv`
- `repair_field_contract.csv`
- `future_extractor_schema.csv`
- `acceptance_gate_matrix.csv`
- `repair_contract_summary.csv`
- `source_manifest.csv`
- `summary.json`

## Counts

- Component/cluster target rows: `{summary['component_repair_target_rows']}`.
- Ordinary admitted rows now: `{summary['ordinary_admitted_now']}`.
- Required field rows: `{summary['field_contract_rows']}`.
- Acceptance gates: `{summary['acceptance_gate_rows']}`.

## Guardrails

No native CFD outputs, registry/admission state, scheduler state, external Fluid
files, generated index files, or active-agent scoped artifacts were mutated. The
contract forbids universal K, hidden global friction multipliers, clipping
negative K, and ordinary pressure coefficients from reverse-flow sections.
""",
        encoding="utf-8",
    )


def build_package(out: Path = OUT) -> dict[str, Any]:
    require_sources()
    out.mkdir(parents=True, exist_ok=True)
    targets = build_targets()
    fields = build_field_contract()
    schema = build_schema()
    gates = build_gate_matrix(targets)
    summary_rows = build_summary_rows(targets, fields, gates)
    manifest = build_manifest()
    summary = {
        "task": TASK,
        "date": DATE,
        "generated_at_utc": utc_now(),
        "output_dir": rel(out),
        "component_repair_target_rows": len(targets),
        "ordinary_admitted_now": 0,
        "field_contract_rows": len(fields),
        "future_schema_rows": len(schema),
        "acceptance_gate_rows": len(gates),
        "summary_rows": len(summary_rows),
        "source_rows": len(manifest),
        "scientific_admission_change": "none",
        "native_output_mutation": "none",
        "registry_mutation": "none",
        "scheduler_action": "none",
        "external_fluid_edit": "none",
        "generated_index_refresh": "not_run_active_agents_own_generated_index_paths",
    }
    write_csv(out / "component_repair_targets.csv", targets, TARGET_COLUMNS)
    write_csv(out / "repair_field_contract.csv", fields, FIELD_COLUMNS)
    write_csv(out / "future_extractor_schema.csv", schema, SCHEMA_COLUMNS)
    write_csv(out / "acceptance_gate_matrix.csv", gates, GATE_COLUMNS)
    write_csv(out / "repair_contract_summary.csv", summary_rows, SUMMARY_COLUMNS)
    write_csv(out / "source_manifest.csv", manifest, MANIFEST_COLUMNS)
    write_readme(out / "README.md", summary)
    write_json(out / "summary.json", summary)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args()
    print(json.dumps(build_package(args.out), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
