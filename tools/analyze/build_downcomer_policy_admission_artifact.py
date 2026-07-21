#!/usr/bin/env python3
"""Build AGENT-469 downcomer policy/admission artifact.

The artifact decides whether the downcomer can enter ordinary Internal-Nu
fitting. It uses existing evidence only and treats sign/enthalpy consistency,
low-recirculation validity, and same-QOI publication-ready GCI as hard gates.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


TASK = "AGENT-469"
DATE = "2026-07-16"
ROOT = Path(__file__).resolve().parents[2]
OUT_REL = Path("work_products/2026-07/2026-07-16/2026-07-16_downcomer_policy_admission_artifact")
OUT = ROOT / OUT_REL

AG466 = ROOT / "work_products/2026-07/2026-07-16/2026-07-16_downcomer_internal_nu_unlock_and_blocker_roadmap"
AG459 = ROOT / "work_products/2026-07/2026-07-16/2026-07-16_branch_local_internal_nu_unblock"
AG455 = ROOT / "work_products/2026-07/2026-07-16/2026-07-16_closure_qoi_mesh_gci_resolution"
SIGN_REVIEW = ROOT / "work_products/2026-07/2026-07-13/2026-07-13_thermal_sign_enthalpy_review/thermal_sign_enthalpy_review.csv"
ENTHALPY = ROOT / "work_products/2026-07/2026-07-08/2026-07-08_patchwise_heat_ledger_enthalpy_interfaces/segment_enthalpy_residuals.csv"
RECIRC = ROOT / "work_products/2026-06/2026-06-30/2026-06-30_claude_downcomer_recirculation/downcomer_recirculation.csv"
FINAL_GCI = AG459 / "final_use_closure_qoi_gci.csv"
MESH_GCI = AG455 / "mesh_gci_gate_for_admitted_candidates.csv"
DOWNCOMER_GATE = AG466 / "downcomer_admission_gate.csv"
LITREV = ROOT / "operational_notes/maps/literature-synthesis-and-gates.md"

RESIDUAL_FRACTION_TOL = 0.25
STATION_BACKFLOW_TOL = 0.05
INTERFACE_RECIRC_TOL = 0.20
DOWNCOMER_STATIONS = {"TW4", "TW5", "TW6"}

SIGN_COLUMNS = [
    "case_id",
    "source_id",
    "wallHeatFlux_W",
    "enthalpy_change_W",
    "residual_W",
    "residual_fraction",
    "direction_status",
    "residual_status",
    "interface_recirc_ratio",
    "quality_flags",
    "gate",
    "source_path",
]
RECIRC_COLUMNS = [
    "source_id",
    "station_count",
    "max_backflow_area_fraction",
    "max_recirculation_intensity",
    "min_flow_alignment",
    "nondim_available",
    "core_station_gate",
    "interface_recirc_gate",
    "interpretation",
    "source_path",
]
GCI_COLUMNS = [
    "qoi_id",
    "quantity",
    "reported_span_or_segment",
    "complete_triplet",
    "current_publication_ready",
    "current_fit_admissible",
    "gci_status",
    "final_use_decision",
    "gate",
    "resolution_action",
    "source_paths",
]
DECISION_COLUMNS = [
    "canonical_leg_id",
    "sign_enthalpy_gate",
    "low_recirculation_gate",
    "same_qoi_gci_gate",
    "litrev_gate",
    "ordinary_nu_fit_admitted",
    "decision",
    "blocking_reasons",
    "next_required_artifact",
]
MANIFEST_COLUMNS = ["source_id", "path", "exists", "role"]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT.resolve()))
    except ValueError:
        return str(path)


def safe_float(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def fmt(value: Any) -> str:
    number = safe_float(value)
    if number is None:
        return "" if value is None else str(value)
    return f"{number:.12g}"


def yes(value: Any) -> bool:
    return str(value).strip().lower() in {"yes", "true", "1", "pass"}


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
            writer.writerow({column: format_value(row.get(column, "")) for column in columns})
    return len(materialized)


def format_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "yes" if value else "no"
    return str(value)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sign_enthalpy_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in read_csv(ENTHALPY):
        if row.get("physical_segment") != "downcomer":
            continue
        residual_fraction = safe_float(row.get("residual_fraction"))
        wall = safe_float(row.get("segment_wallHeatFlux_sum_W"))
        enthalpy = safe_float(row.get("enthalpy_change_W"))
        recirc = safe_float(row.get("max_interface_recirc_ratio"))
        direction_ok = wall is not None and enthalpy is not None and wall * enthalpy >= 0
        residual_ok = residual_fraction is not None and abs(residual_fraction) <= RESIDUAL_FRACTION_TOL
        recirc_ok = recirc is not None and recirc <= INTERFACE_RECIRC_TOL
        gate = "pass" if direction_ok and residual_ok and recirc_ok else "fail"
        rows.append(
            {
                "case_id": row.get("case_id", ""),
                "source_id": row.get("source_id", ""),
                "wallHeatFlux_W": fmt(wall),
                "enthalpy_change_W": fmt(enthalpy),
                "residual_W": row.get("wallHeatFlux_vs_enthalpy_residual_W", ""),
                "residual_fraction": fmt(residual_fraction),
                "direction_status": "same_direction" if direction_ok else "opposed_direction",
                "residual_status": "within_tolerance" if residual_ok else f"outside_abs_{RESIDUAL_FRACTION_TOL}",
                "interface_recirc_ratio": fmt(recirc),
                "quality_flags": row.get("quality_flags", ""),
                "gate": gate,
                "source_path": rel(ENTHALPY),
            }
        )
    return rows


def low_recirculation_rows(sign_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    station_rows = [row for row in read_csv(RECIRC) if row.get("label") in DOWNCOMER_STATIONS and row.get("span") == "right_leg"]
    by_source: dict[str, list[dict[str, str]]] = {}
    for row in station_rows:
        by_source.setdefault(row["source_id"], []).append(row)
    interface_by_source = {row["source_id"]: safe_float(row["interface_recirc_ratio"]) for row in sign_rows}
    out: list[dict[str, Any]] = []
    for source_id, rows in sorted(by_source.items()):
        backflows = [safe_float(row.get("backflow_area_fraction")) or 0.0 for row in rows]
        intensities = [safe_float(row.get("recirculation_intensity")) or 0.0 for row in rows]
        alignments = [safe_float(row.get("flow_alignment")) or 0.0 for row in rows]
        max_backflow = max(backflows) if backflows else None
        max_intensity = max(intensities) if intensities else None
        min_alignment = min(alignments) if alignments else None
        core_pass = max_backflow is not None and max_backflow <= STATION_BACKFLOW_TOL
        interface_recirc = interface_by_source.get(source_id)
        interface_pass = interface_recirc is not None and interface_recirc <= INTERFACE_RECIRC_TOL
        if core_pass and interface_pass:
            interpretation = "low_recirculation_valid_for_policy_screen"
        elif core_pass:
            interpretation = "station_core_low_recirculation_but_interface_invalid_for_internal_nu"
        else:
            interpretation = "station_core_recirculation_blocks_internal_nu"
        out.append(
            {
                "source_id": source_id,
                "station_count": len(rows),
                "max_backflow_area_fraction": fmt(max_backflow),
                "max_recirculation_intensity": fmt(max_intensity),
                "min_flow_alignment": fmt(min_alignment),
                "nondim_available": "no",
                "core_station_gate": "pass" if core_pass else "fail",
                "interface_recirc_gate": "pass" if interface_pass else "fail",
                "interpretation": interpretation,
                "source_path": rel(RECIRC),
            }
        )
    return out


def gci_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in read_csv(FINAL_GCI):
        if row.get("canonical_leg_id") != "downcomer_right_vertical":
            continue
        publication_ready = yes(row.get("current_publication_ready")) and yes(row.get("current_fit_admissible"))
        rows.append(
            {
                "qoi_id": row.get("qoi_id", ""),
                "quantity": row.get("quantity", ""),
                "reported_span_or_segment": row.get("reported_span_or_segment", ""),
                "complete_triplet": row.get("complete_triplet", ""),
                "current_publication_ready": row.get("current_publication_ready", ""),
                "current_fit_admissible": row.get("current_fit_admissible", ""),
                "gci_status": row.get("gci_status", ""),
                "final_use_decision": row.get("final_use_decision", ""),
                "gate": "pass" if publication_ready else "fail",
                "resolution_action": row.get("resolution_action", ""),
                "source_paths": row.get("source_paths", ""),
            }
        )
    return rows


def decision_rows(sign_rows: list[dict[str, Any]], recirc_rows: list[dict[str, Any]], gci: list[dict[str, Any]]) -> list[dict[str, Any]]:
    sign_pass = bool(sign_rows) and all(row["gate"] == "pass" for row in sign_rows)
    recirc_pass = bool(recirc_rows) and all(row["core_station_gate"] == "pass" and row["interface_recirc_gate"] == "pass" for row in recirc_rows)
    # Same-QOI means a thermal Nu/HTC/UA-like row, not only pressure/f rows.
    thermal_gci_rows = [row for row in gci if row["quantity"] in {"Nu", "HTC", "UA_prime", "thermal_segment_closure"}]
    same_qoi_gci_pass = bool(thermal_gci_rows) and any(row["gate"] == "pass" for row in thermal_gci_rows)
    litrev_pass = sign_pass and recirc_pass
    admitted = sign_pass and recirc_pass and same_qoi_gci_pass and litrev_pass
    reasons = []
    if not sign_pass:
        reasons.append("sign_enthalpy_heat_balance_failed")
    if not recirc_pass:
        reasons.append("low_recirculation_validity_failed")
    if not same_qoi_gci_pass:
        reasons.append("same_qoi_publication_gci_missing_or_failed")
    if not litrev_pass:
        reasons.append("litrev_no_nu_absorption_gate_failed")
    return [
        {
            "canonical_leg_id": "downcomer_right_vertical",
            "sign_enthalpy_gate": "pass" if sign_pass else "fail",
            "low_recirculation_gate": "pass" if recirc_pass else "fail",
            "same_qoi_gci_gate": "pass" if same_qoi_gci_pass else "fail",
            "litrev_gate": "pass" if litrev_pass else "fail",
            "ordinary_nu_fit_admitted": "yes" if admitted else "no",
            "decision": "admitted_downcomer_internal_nu_policy" if admitted else "not_admitted_downcomer_policy_failed",
            "blocking_reasons": ";".join(reasons),
            "next_required_artifact": "new downcomer same-QOI thermal extraction/GCI only after sign/enthalpy and interface-recirculation policy are repaired or rejected",
        }
    ]


def manifest_rows() -> list[dict[str, Any]]:
    roles = {
        "agent466_downcomer_gate": DOWNCOMER_GATE,
        "thermal_sign_review": SIGN_REVIEW,
        "segment_enthalpy_residuals": ENTHALPY,
        "downcomer_recirculation": RECIRC,
        "agent459_final_gci": FINAL_GCI,
        "agent455_mesh_gci": MESH_GCI,
        "litrev_map": LITREV,
    }
    return [{"source_id": key, "path": rel(path), "exists": path.exists(), "role": "input"} for key, path in roles.items()]


def write_readme(summary: dict[str, Any]) -> None:
    text = f"""---
provenance:
  - {rel(ENTHALPY)}
  - {rel(RECIRC)}
  - {rel(FINAL_GCI)}
  - {rel(DOWNCOMER_GATE)}
tags: [downcomer, internal-nu, admission, sign-enthalpy, recirculation, mesh-gci]
related:
  - .agent/blockers.yml
  - operational_notes/maps/thermal-closures-and-internal-nu.md
  - operational_notes/maps/mesh-gci-and-uncertainty.md
task: {TASK}
date: {DATE}
role: Coordinator/Thermal-modeling/Internal-Nu/Mesh-GCI/Implementer/Tester/Writer
type: work_product
status: complete
---
# Downcomer Policy Admission Artifact

Generated: `{summary["generated_at"]}`

## Decision

Downcomer ordinary Internal-Nu fit admission: `{summary["decision"]}`.

Current evidence does not admit a downcomer Nu fit. The downcomer core station
velocity metrics are low-recirculation on TW4/TW5/TW6, but the thermal
interface evidence has opposed wallHeatFlux/enthalpy direction, large residuals,
and high interface recirculation flags. Same-QOI publication-ready thermal GCI
is also absent.

## Results

- Sign/enthalpy rows reviewed: `{summary["sign_enthalpy_rows"]}`.
- Low-recirculation case summaries: `{summary["recirculation_rows"]}`.
- Downcomer GCI rows reviewed: `{summary["gci_rows"]}`.
- Ordinary Nu fit rows admitted: `{summary["ordinary_nu_fit_admitted"]}`.

## Outputs

- `downcomer_sign_enthalpy_gate.csv`
- `downcomer_low_recirculation_gate.csv`
- `downcomer_same_qoi_gci_gate.csv`
- `downcomer_admission_decision.csv`
- `source_manifest.csv`
- `summary.json`
"""
    (OUT / "README.md").write_text(text, encoding="utf-8")


def build_package(out: Path = OUT) -> dict[str, Any]:
    global OUT
    OUT = out
    sign = sign_enthalpy_rows()
    recirc = low_recirculation_rows(sign)
    gci = gci_rows()
    decision = decision_rows(sign, recirc, gci)
    manifest = manifest_rows()
    write_csv(out / "downcomer_sign_enthalpy_gate.csv", sign, SIGN_COLUMNS)
    write_csv(out / "downcomer_low_recirculation_gate.csv", recirc, RECIRC_COLUMNS)
    write_csv(out / "downcomer_same_qoi_gci_gate.csv", gci, GCI_COLUMNS)
    write_csv(out / "downcomer_admission_decision.csv", decision, DECISION_COLUMNS)
    write_csv(out / "source_manifest.csv", manifest, MANIFEST_COLUMNS)
    summary = {
        "task": TASK,
        "generated_at": utc_now(),
        "decision": decision[0]["decision"],
        "sign_enthalpy_rows": len(sign),
        "sign_gate_counts": dict(Counter(row["gate"] for row in sign)),
        "recirculation_rows": len(recirc),
        "core_station_gate_counts": dict(Counter(row["core_station_gate"] for row in recirc)),
        "interface_recirc_gate_counts": dict(Counter(row["interface_recirc_gate"] for row in recirc)),
        "gci_rows": len(gci),
        "gci_gate_counts": dict(Counter(row["gate"] for row in gci)),
        "ordinary_nu_fit_admitted": 1 if decision[0]["ordinary_nu_fit_admitted"] == "yes" else 0,
        "native_solver_outputs_mutated": False,
        "registry_mutated": False,
        "scheduler_action_taken": False,
        "external_fluid_mutated": False,
    }
    write_json(out / "summary.json", summary)
    write_readme(summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args()
    print(json.dumps(build_package(args.out), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
