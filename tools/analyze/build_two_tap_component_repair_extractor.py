#!/usr/bin/env python3
"""Build AGENT-530 two-tap component repair extractor outputs."""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


TASK = "AGENT-530"
DATE = "2026-07-17"
ROOT = Path(__file__).resolve().parents[2]
OUT_REL = Path("work_products/2026-07/2026-07-17/2026-07-17_two_tap_component_repair_extractor")
OUT = ROOT / OUT_REL

CONTRACT = ROOT / "work_products/2026-07/2026-07-17/2026-07-17_two_tap_component_repair_contract"
MINOR = ROOT / "work_products/2026-07/2026-07-08/2026-07-08_minor_loss_two_tap"
TAP = ROOT / "work_products/2026-07/2026-07-14/2026-07-14_hydraulic_tap_length_admission_refresh"
RAW = ROOT / "work_products/2026-07/2026-07-15/2026-07-15_staged_closure_qoi_pressure_sbatch"
CORNER = ROOT / "work_products/2026-07/2026-07-17/2026-07-17_val_salt2_pressure_evidence_corner_k_diagnosis"

SOURCES = {
    "component_repair_targets": CONTRACT / "component_repair_targets.csv",
    "future_extractor_schema": CONTRACT / "future_extractor_schema.csv",
    "acceptance_gate_matrix": CONTRACT / "acceptance_gate_matrix.csv",
    "minor_loss_two_tap": MINOR / "minor_loss_two_tap.csv",
    "tap_centerline_lengths": TAP / "tap_centerline_length_table.csv",
    "component_k_recomputed": TAP / "component_cluster_k_recomputed_admission_table.csv",
    "raw_pressure_two_tap_harvest": RAW / "raw_pressure_two_tap_harvest.csv",
    "corner_k_gate_matrix": CORNER / "corner_k_gate_matrix.csv",
}

EXTRACTOR_COLUMNS = [
    "case_id",
    "feature",
    "time_window",
    "p_upstream_pa",
    "p_downstream_pa",
    "pressure_basis",
    "hydrostatic_correction_pa",
    "kinetic_correction_pa",
    "straight_loss_subtraction_pa",
    "local_dynamic_pressure_pa",
    "K_apparent",
    "K_local",
    "RAF",
    "RMF",
    "SVF",
    "mesh_time_uncertainty",
    "admission_status",
]

GATE_COLUMNS = ["case_id", "feature", "gate", "status", "evidence", "blocker", "source_paths"]
QUEUE_COLUMNS = ["priority", "missing_artifact", "target_rows", "why", "required_action", "acceptance_signal", "guardrail", "source_paths"]
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
        raise FileNotFoundError("Missing AGENT-530 source files: " + ", ".join(missing))


def fnum(value: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return math.nan
    return number if math.isfinite(number) else math.nan


def finite_or_blank(value: Any) -> str:
    number = fnum(str(value))
    return "" if not math.isfinite(number) else f"{number:.12g}"


def by_case_feature(rows: list[dict[str, str]]) -> dict[tuple[str, str], dict[str, str]]:
    return {(row.get("case_id", ""), row.get("feature", "")): row for row in rows}


def raw_time_by_case(rows: list[dict[str, str]]) -> dict[str, str]:
    return {row["case_id"]: row.get("time_s", "") for row in rows if row.get("case_id")}


def build_extractor_rows() -> list[dict[str, Any]]:
    targets = read_csv(SOURCES["component_repair_targets"])
    minor = by_case_feature(read_csv(SOURCES["minor_loss_two_tap"]))
    component = by_case_feature(read_csv(SOURCES["component_k_recomputed"]))
    times = raw_time_by_case(read_csv(SOURCES["raw_pressure_two_tap_harvest"]))
    rows: list[dict[str, Any]] = []
    for target in targets:
        key = (target["case_id"], target["feature"])
        minor_row = minor.get(key, {})
        component_row = component.get(key, {})
        rows.append(
            {
                "case_id": target["case_id"],
                "feature": target["feature"],
                "time_window": times.get(target["case_id"], ""),
                "p_upstream_pa": "",
                "p_downstream_pa": "",
                "pressure_basis": "preserved_feature_total_pressure_loss_with_buoyancy_dynamic_terms;raw_endpoint_pressures_missing",
                "hydrostatic_correction_pa": finite_or_blank(minor_row.get("buoyancy_term_pa", "")),
                "kinetic_correction_pa": finite_or_blank(minor_row.get("delta_q_dyn_pa", "")),
                "straight_loss_subtraction_pa": finite_or_blank(component_row.get("centerline_adjacent_straight_loss_subtracted_pa", "")),
                "local_dynamic_pressure_pa": finite_or_blank(component_row.get("q_ref_local_pa", "")),
                "K_apparent": finite_or_blank(component_row.get("K_apparent", "")),
                "K_local": finite_or_blank(component_row.get("K_local_centerline", "")),
                "RAF": "",
                "RMF": "",
                "SVF": "",
                "mesh_time_uncertainty": "missing_same_qoi_mesh_time_UQ",
                "admission_status": "diagnostic_blocked_missing_raw_endpoint_pressure_basis_recirculation_UQ",
            }
        )
    return rows


def build_gate_rows(extractor_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in extractor_rows:
        case_id = row["case_id"]
        feature = row["feature"]
        k_local = fnum(str(row["K_local"]))
        rows.extend(
            [
                {
                    "case_id": case_id,
                    "feature": feature,
                    "gate": "pressure_and_velocity_basis",
                    "status": "fail",
                    "evidence": "preserved feature loss available; raw endpoint pressure fields blank; velocity basis remains proxy",
                    "blocker": "raw_endpoint_pressure_and_final_velocity_basis_missing",
                    "source_paths": f"{rel(SOURCES['component_repair_targets'])};{rel(SOURCES['minor_loss_two_tap'])}",
                },
                {
                    "case_id": case_id,
                    "feature": feature,
                    "gate": "straight_reference",
                    "status": "fail",
                    "evidence": f"K_local_centerline={finite_or_blank(k_local)} after centerline straight-loss subtraction",
                    "blocker": "current_centerline_reference_over_subtracts_local_loss",
                    "source_paths": rel(SOURCES["component_k_recomputed"]),
                },
                {
                    "case_id": case_id,
                    "feature": feature,
                    "gate": "component_isolation",
                    "status": "fail",
                    "evidence": "component row is still a cluster/component candidate without reset-development exclusion",
                    "blocker": "component_K_not_isolated_from_reset_development_or_branch_apparent_loss",
                    "source_paths": f"{rel(SOURCES['component_repair_targets'])};{rel(SOURCES['corner_k_gate_matrix'])}",
                },
                {
                    "case_id": case_id,
                    "feature": feature,
                    "gate": "recirculation_policy",
                    "status": "fail",
                    "evidence": "same-window RAF/RMF/SVF fields are blank for this feature row",
                    "blocker": "same_window_reverse_and_secondary_flow_metrics_missing",
                    "source_paths": rel(SOURCES["raw_pressure_two_tap_harvest"]),
                },
                {
                    "case_id": case_id,
                    "feature": feature,
                    "gate": "same_qoi_mesh_time_UQ",
                    "status": "fail",
                    "evidence": "same pressure-loss QoI mesh/time uncertainty unavailable",
                    "blocker": "same_qoi_mesh_time_uncertainty_missing",
                    "source_paths": rel(SOURCES["acceptance_gate_matrix"]),
                },
            ]
        )
    return rows


def build_queue(extractor_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    target_rows = len(extractor_rows)
    common_guardrail = "row remains diagnostic until this artifact lands; do not admit K or tune friction from proxy fields"
    return [
        {
            "priority": 1,
            "missing_artifact": "raw_feature_endpoint_pressure_surfaces",
            "target_rows": target_rows,
            "why": "Current target rows lack p_upstream_pa and p_downstream_pa for the local feature.",
            "required_action": "stage or sample upstream/downstream feature taps for corner_lower_right at the same time window",
            "acceptance_signal": "finite p_upstream_pa and p_downstream_pa with labels and pressure basis",
            "guardrail": common_guardrail,
            "source_paths": rel(SOURCES["component_repair_targets"]),
        },
        {
            "priority": 2,
            "missing_artifact": "final_pressure_velocity_basis",
            "target_rows": target_rows,
            "why": "Preserved feature loss uses proxy pressure and velocity bases.",
            "required_action": "emit static/total/p_rgh basis, hydrostatic correction, kinetic correction, local density, and local dynamic pressure",
            "acceptance_signal": "basis fields reproduce feature loss without buoyancy or kinetic double counting",
            "guardrail": common_guardrail,
            "source_paths": rel(SOURCES["minor_loss_two_tap"]),
        },
        {
            "priority": 3,
            "missing_artifact": "physically_comparable_straight_reference",
            "target_rows": target_rows,
            "why": "Current centerline straight-reference subtraction makes all target K_local values negative.",
            "required_action": "select and document a local straight reference or retain apparent/cluster label",
            "acceptance_signal": "straight_loss_subtraction_pa is justified and K_local is not clipped",
            "guardrail": "negative K cannot be clipped; apparent/cluster labels must remain if isolation fails",
            "source_paths": rel(SOURCES["component_k_recomputed"]),
        },
        {
            "priority": 4,
            "missing_artifact": "same_window_RAF_RMF_SVF",
            "target_rows": target_rows,
            "why": "Ordinary K requires non-recirculating adjacent flow metrics.",
            "required_action": "compute RAF, RMF, and SVF on the same feature/tap window",
            "acceptance_signal": "ordinary rows require RAF < 0.01 and RMF < 0.01",
            "guardrail": "material reverse-flow rows remain diagnostic or section-effective only",
            "source_paths": rel(SOURCES["raw_pressure_two_tap_harvest"]),
        },
        {
            "priority": 5,
            "missing_artifact": "same_qoi_mesh_time_uncertainty",
            "target_rows": target_rows,
            "why": "No same-QOI mesh/time uncertainty exists for the target feature K.",
            "required_action": "repeat the same feature pressure-loss extraction over a mesh/time family or flag non-GCI uncertainty",
            "acceptance_signal": "uncertainty bound attached to the same pressure-loss QoI",
            "guardrail": "do not reuse unrelated GCI or fabricate monotonicity",
            "source_paths": rel(SOURCES["acceptance_gate_matrix"]),
        },
    ]


def build_summary_rows(extractor_rows: list[dict[str, Any]], gate_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    statuses = Counter(row["admission_status"] for row in extractor_rows)
    gate_statuses = Counter(row["status"] for row in gate_rows)
    negative_k = sum(fnum(str(row["K_local"])) < 0 for row in extractor_rows)
    endpoint_missing = sum(not row["p_upstream_pa"] or not row["p_downstream_pa"] for row in extractor_rows)
    return [
        {"category": "extractor_rows", "count": len(extractor_rows), "interpretation": "Rows emitted in AGENT-525 future schema."},
        {"category": "ordinary_admitted_rows", "count": 0, "interpretation": "No row passes all gates."},
        {"category": "diagnostic_blocked_rows", "count": statuses.get("diagnostic_blocked_missing_raw_endpoint_pressure_basis_recirculation_UQ", 0), "interpretation": "Rows correctly retained as diagnostic."},
        {"category": "missing_endpoint_pressure_rows", "count": endpoint_missing, "interpretation": "Rows with blank p_upstream_pa or p_downstream_pa."},
        {"category": "negative_K_local_rows", "count": negative_k, "interpretation": "Rows where current centerline straight-reference subtraction over-subtracts."},
        {"category": "gate_fail_rows", "count": gate_statuses.get("fail", 0), "interpretation": "Failed predeclared gate rows."},
    ]


def build_manifest() -> list[dict[str, Any]]:
    return [{"source_id": key, "path": rel(path), "exists": path.exists(), "role": "read-only extractor source"} for key, path in SOURCES.items()]


def write_readme(path: Path, summary: dict[str, Any]) -> None:
    path.write_text(
        f"""---
provenance:
  - {rel(SOURCES['component_repair_targets'])}
  - {rel(SOURCES['future_extractor_schema'])}
  - {rel(SOURCES['component_k_recomputed'])}
tags: [pressure-ledger, two-tap, component-k, extractor]
related:
  - .agent/status/2026-07-17_AGENT-530.md
  - .agent/journal/2026-07-17/two-tap-component-repair-extractor.md
task: {TASK}
date: {DATE}
role: Hydraulics/cfd-pp/Implementer/Tester/Writer
type: work_product
status: complete
---
# Two-Tap Component Repair Extractor

Generated: `{summary['generated_at_utc']}`

## Decision

The extractor emits the AGENT-525 future schema for the three current
`corner_lower_right` targets from existing preserved/staged evidence only.
All rows remain diagnostic because raw endpoint pressures, final bases,
same-window recirculation metrics, component isolation, and same-QOI uncertainty
are still missing or failing.

## Outputs

- `two_tap_component_repair_output.csv`
- `extractor_gate_results.csv`
- `next_raw_postprocessing_queue.csv`
- `extractor_summary.csv`
- `source_manifest.csv`
- `summary.json`

## Counts

- Extractor rows: `{summary['extractor_rows']}`.
- Ordinary admitted rows: `{summary['ordinary_admitted_rows']}`.
- Missing endpoint-pressure rows: `{summary['missing_endpoint_pressure_rows']}`.
- Negative current `K_local` rows: `{summary['negative_K_local_rows']}`.
- Failed gate rows: `{summary['gate_fail_rows']}`.

## Guardrails

No native CFD outputs, registry/admission state, scheduler state, external Fluid
files, generated index files, or active-agent scoped artifacts were mutated.
Blank endpoint-pressure, RAF/RMF/SVF, and uncertainty fields are intentional:
they are blockers, not values to infer.
""",
        encoding="utf-8",
    )


def build_package(out: Path = OUT) -> dict[str, Any]:
    require_sources()
    out.mkdir(parents=True, exist_ok=True)
    extractor_rows = build_extractor_rows()
    gate_rows = build_gate_rows(extractor_rows)
    queue = build_queue(extractor_rows)
    summary_rows = build_summary_rows(extractor_rows, gate_rows)
    manifest = build_manifest()
    counts = {row["category"]: int(row["count"]) for row in summary_rows}
    summary = {
        "task": TASK,
        "date": DATE,
        "generated_at_utc": utc_now(),
        "output_dir": rel(out),
        "extractor_rows": counts["extractor_rows"],
        "ordinary_admitted_rows": counts["ordinary_admitted_rows"],
        "diagnostic_blocked_rows": counts["diagnostic_blocked_rows"],
        "missing_endpoint_pressure_rows": counts["missing_endpoint_pressure_rows"],
        "negative_K_local_rows": counts["negative_K_local_rows"],
        "gate_fail_rows": counts["gate_fail_rows"],
        "queue_rows": len(queue),
        "source_rows": len(manifest),
        "scientific_admission_change": "none",
        "native_output_mutation": "none",
        "registry_mutation": "none",
        "scheduler_action": "none",
        "solver_or_postprocessing_launched": "none",
        "external_fluid_edit": "none",
        "generated_index_refresh": "not_run_active_agents_own_generated_index_paths",
    }
    write_csv(out / "two_tap_component_repair_output.csv", extractor_rows, EXTRACTOR_COLUMNS)
    write_csv(out / "extractor_gate_results.csv", gate_rows, GATE_COLUMNS)
    write_csv(out / "next_raw_postprocessing_queue.csv", queue, QUEUE_COLUMNS)
    write_csv(out / "extractor_summary.csv", summary_rows, SUMMARY_COLUMNS)
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
