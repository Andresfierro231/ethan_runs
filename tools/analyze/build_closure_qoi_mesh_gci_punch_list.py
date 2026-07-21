#!/usr/bin/env python3
"""Narrow closure-QOI mesh/GCI into an explicit punch list.

AGENT-450 is a narrowing pass only. It consumes existing GCI, thermal-admission,
and pressure-diagnostic packages, then emits a row-level ledger of what remains
before the blocker can be resolved. It does not edit the blocker register,
registry state, generated indexes, scheduler state, or native solver outputs.
"""

from __future__ import annotations

import csv
import json
import math
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[2]
TASK = "AGENT-450"
DATE = "2026-07-16"
SLUG = "2026-07-16_closure_qoi_mesh_gci_punch_list"
OUT = ROOT / "work_products/2026-07/2026-07-16" / SLUG

REFRESHED_QOI_STATUS = (
    ROOT
    / "work_products/2026-07/2026-07-14/2026-07-14_thermal_closure_mesh_gate_refresh"
    / "refreshed_qoi_mesh_gate_status.csv"
)
THERMAL_ADMISSION = (
    ROOT
    / "work_products/2026-07/2026-07-14/2026-07-14_thermal_closure_mesh_gate_refresh"
    / "thermal_admission_table.csv"
)
GCI_DECISIONS = (
    ROOT
    / "work_products/2026-07/2026-07-13/2026-07-13_salt2_closure_qoi_mesh_gci"
    / "closure_qoi_admission_decisions.csv"
)
GCI_RESULTS = (
    ROOT
    / "work_products/2026-07/2026-07-13/2026-07-13_salt2_closure_qoi_mesh_gci"
    / "closure_qoi_gci_results.csv"
)
RAW_TWO_TAP = (
    ROOT
    / "work_products/2026-07/2026-07-15/2026-07-15_staged_closure_qoi_pressure_sbatch"
    / "raw_pressure_two_tap_harvest.csv"
)
PRESSURE_LADDER_STATIONS = (
    ROOT
    / "work_products/2026-07/2026-07-15/2026-07-15_pressure_ladder_unlock_sbatch"
    / "station_pressure_ladder.csv"
)
PRESSURE_LADDER_ADJACENT = (
    ROOT
    / "work_products/2026-07/2026-07-15/2026-07-15_pressure_ladder_unlock_sbatch"
    / "adjacent_pressure_ladder.csv"
)
EXPANDED_PRESSURE_STATIONS = (
    ROOT
    / "work_products/2026-07/2026-07-15/2026-07-15_expanded_salt_pressure_ladder_8pm_sbatch"
    / "station_pressure_ladder.csv"
)
EXPANDED_PRESSURE_ADJACENT = (
    ROOT
    / "work_products/2026-07/2026-07-15/2026-07-15_expanded_salt_pressure_ladder_8pm_sbatch"
    / "adjacent_pressure_ladder.csv"
)
BLOCKERS_YML = ROOT / ".agent/blockers.yml"

PUNCH_FIELDS = [
    "case_id",
    "source_id",
    "qoi_family",
    "lane",
    "qoi_id",
    "span",
    "segment",
    "method",
    "quantity",
    "classification",
    "primary_bucket",
    "current_publication_ready",
    "current_fit_admissible",
    "complete_triplet",
    "coarse_available",
    "medium_available",
    "fine_available",
    "gci_status",
    "gci_verdict",
    "gci_trustworthy",
    "admission_remaining",
    "extraction_remaining",
    "next_artifact_needed",
    "next_resolution_action",
    "diagnostic_use_allowed",
    "source_paths",
]

ADMITTED_FIELDS = [
    "case_id",
    "qoi_id",
    "lane",
    "span",
    "quantity",
    "gci_status",
    "next_use",
    "source_paths",
]

QUEUE_FIELDS = [
    "case_id",
    "qoi_id",
    "lane",
    "span",
    "quantity",
    "required_mesh_levels",
    "extraction_or_reconciliation_needed",
    "admission_precondition",
    "source_paths",
]

ADMISSION_FIELDS = [
    "case_id",
    "qoi_id",
    "lane",
    "span",
    "quantity",
    "admission_gate",
    "admission_work_remaining",
    "source_paths",
]


@dataclass(frozen=True)
class Inputs:
    refreshed_qoi_status: Path = REFRESHED_QOI_STATUS
    thermal_admission: Path = THERMAL_ADMISSION
    gci_decisions: Path = GCI_DECISIONS
    gci_results: Path = GCI_RESULTS
    raw_two_tap: Path = RAW_TWO_TAP
    pressure_ladder_stations: Path = PRESSURE_LADDER_STATIONS
    pressure_ladder_adjacent: Path = PRESSURE_LADDER_ADJACENT
    expanded_pressure_stations: Path = EXPANDED_PRESSURE_STATIONS
    expanded_pressure_adjacent: Path = EXPANDED_PRESSURE_ADJACENT
    blockers_yml: Path = BLOCKERS_YML


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: Iterable[dict[str, object]], fieldnames: list[str]) -> int:
    data = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in data:
            writer.writerow({field: format_value(row.get(field, "")) for field in fieldnames})
    return len(data)


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def format_value(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, float):
        return f"{value:.12g}" if math.isfinite(value) else ""
    return str(value)


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT.resolve()))
    except ValueError:
        return str(path)


def is_yes(value: object) -> bool:
    return str(value).strip().lower() == "yes"


def numeric(value: str | object | None) -> float | None:
    if value in {None, ""}:
        return None
    try:
        parsed = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def missing_levels(row: dict[str, str]) -> list[str]:
    levels = []
    for level in ["coarse", "medium", "fine"]:
        if not is_yes(row.get(f"{level}_available", "")):
            levels.append(level)
    return levels


def bucket_for(row: dict[str, str]) -> str:
    classification = row.get("classification", "")
    if is_yes(row.get("publication_ready")) and is_yes(row.get("fit_admissible")):
        return "admitted_only_candidate"
    if classification == "blocked-sign-review":
        return "thermal_admission_review_required"
    if classification == "blocked-downcomer-policy":
        return "downcomer_policy_blocked"
    if classification == "blocked-missing-triplet" or not is_yes(row.get("complete_triplet")):
        return "missing_triplet_extraction_or_reconciliation_required"
    if classification == "non-monotone/oscillatory":
        return "gci_failed_no_resolution_without_reextract_or_remesh"
    blockers = row.get("blockers", "")
    if "not_fit_safe" in blockers or "pressure" in row.get("lane", ""):
        return "pressure_admission_review_required"
    return "manual_review_required"


def admission_remaining(row: dict[str, str], bucket: str) -> str:
    blockers = row.get("blockers", "")
    if bucket == "admitted_only_candidate":
        return "none"
    if bucket == "thermal_admission_review_required":
        return "resolve thermal sign labels, enthalpy direction, heat-balance residual, source ownership, and internal-Nu residual guardrail"
    if bucket == "downcomer_policy_blocked":
        return "decide downcomer/right-leg thermal policy before extracting or interpreting closure QoI"
    if bucket == "missing_triplet_extraction_or_reconciliation_required":
        if row.get("qoi_family") == "thermal":
            return "admit repaired thermal source rows after sign, enthalpy, heat-balance, downcomer, and internal-Nu policy review"
        return "admit pressure source row and same-QOI mesh-level provenance after missing triplet is reconciled"
    if bucket == "gci_failed_no_resolution_without_reextract_or_remesh":
        parts = ["exclude from final closure set or produce same-QOI monotone/asymptotic triplet"]
        if "not_fit_safe" in blockers:
            parts.append("resolve pressure fit-safety, pressure-recovery/noise, tap orientation, straight-loss subtraction, and recirculation gates")
        return "; ".join(parts)
    if bucket == "pressure_admission_review_required":
        return "resolve pressure definition, tap orientation, straight-loss subtraction, localized-loss isolation, recirculation mask, and source admission"
    return "manual row-level admission review"


def extraction_remaining(row: dict[str, str], bucket: str) -> str:
    missing = missing_levels(row)
    if bucket == "admitted_only_candidate":
        return "none"
    if missing:
        return "missing_or_unreconciled_mesh_levels=" + "|".join(missing)
    if bucket == "gci_failed_no_resolution_without_reextract_or_remesh":
        return "no missing levels; targeted same-plane/same-window re-extraction or conformal-first remesh only if this QoI remains in final closure set"
    return "none until admission gate changes"


def next_artifact(row: dict[str, str], bucket: str) -> str:
    if bucket == "admitted_only_candidate":
        return "gci_results_admitted_only.csv"
    if bucket == "missing_triplet_extraction_or_reconciliation_required":
        return "staged same-QOI mesh-level extraction or reconciliation package before admitted-only GCI"
    if bucket == "thermal_admission_review_required":
        return "thermal sign/enthalpy/heat-balance/source-admission decision table"
    if bucket == "downcomer_policy_blocked":
        return "downcomer/right-leg thermal policy decision memo"
    if bucket == "gci_failed_no_resolution_without_reextract_or_remesh":
        return "final closure-set exclusion decision or remeshed/re-extracted monotone triplet package"
    if bucket == "pressure_admission_review_required":
        return "raw-pressure admission package with pressure definition, orientation, straight-loss subtraction, and recirculation masks"
    return "manual admission memo"


def next_action(row: dict[str, str], bucket: str) -> str:
    if bucket == "admitted_only_candidate":
        return "carry into admitted-only GCI resolution pass"
    if bucket == "missing_triplet_extraction_or_reconciliation_required":
        return "reconcile missing mesh-level values first; do not compute publication GCI yet"
    if bucket == "thermal_admission_review_required":
        return "complete admission review before any thermal fitting or publication GCI"
    if bucket == "downcomer_policy_blocked":
        return "block row until policy chooses include/exclude/diagnostic label"
    if bucket == "gci_failed_no_resolution_without_reextract_or_remesh":
        return "either exclude row from final closure set or rerun same-QOI extraction on better mesh/source contract"
    if bucket == "pressure_admission_review_required":
        return "use July 15 pressure diagnostics only as admission evidence; do not fit true f_D/K yet"
    return "manual review"


def source_paths(row: dict[str, str]) -> str:
    paths = [
        row.get("coarse_source_path", ""),
        row.get("medium_source_path", ""),
        row.get("fine_source_path", ""),
        row.get("decision_source_path", ""),
        row.get("gci_source_path", ""),
    ]
    return ";".join(path for path in paths if path)


def pressure_diagnostic_summary(inputs: Inputs) -> dict[str, object]:
    raw = read_csv(inputs.raw_two_tap)
    station_rows = read_csv(inputs.pressure_ladder_stations) + read_csv(inputs.expanded_pressure_stations)
    adjacent_rows = read_csv(inputs.pressure_ladder_adjacent) + read_csv(inputs.expanded_pressure_adjacent)
    raf_values = [
        numeric(row.get("reverse_area_fraction_proxy"))
        for row in station_rows
        if numeric(row.get("reverse_area_fraction_proxy")) is not None
    ]
    return {
        "raw_two_tap_rows": len(raw),
        "station_pressure_rows": len(station_rows),
        "adjacent_pressure_rows": len(adjacent_rows),
        "station_reverse_area_fraction_min": min(raf_values) if raf_values else None,
        "station_reverse_area_fraction_max": max(raf_values) if raf_values else None,
        "station_rows_with_reverse_area_fraction_lt_0p01": sum(1 for value in raf_values if value < 0.01),
        "station_rows_with_reverse_area_fraction_ge_0p20": sum(1 for value in raf_values if value >= 0.20),
        "pressure_admission_note": "July 15 pressure rows are coarse diagnostic evidence; all station rows remain recirculation-contaminated by RAF proxy.",
    }


def build_punch_rows(inputs: Inputs) -> list[dict[str, object]]:
    qoi_rows = read_csv(inputs.refreshed_qoi_status)
    gci_results = {row.get("qoi_id", ""): row for row in read_csv(inputs.gci_results)}
    punch: list[dict[str, object]] = []
    for row in qoi_rows:
        bucket = bucket_for(row)
        gci = gci_results.get(row.get("qoi_id", ""), {})
        punch.append(
            {
                "case_id": row.get("case_id", ""),
                "source_id": row.get("source_id", ""),
                "qoi_family": row.get("qoi_family", ""),
                "lane": row.get("lane", ""),
                "qoi_id": row.get("qoi_id", ""),
                "span": row.get("span", ""),
                "segment": row.get("segment", ""),
                "method": row.get("method", ""),
                "quantity": row.get("quantity", ""),
                "classification": row.get("classification", ""),
                "primary_bucket": bucket,
                "current_publication_ready": row.get("publication_ready", ""),
                "current_fit_admissible": row.get("fit_admissible", ""),
                "complete_triplet": row.get("complete_triplet", ""),
                "coarse_available": row.get("coarse_available", ""),
                "medium_available": row.get("medium_available", ""),
                "fine_available": row.get("fine_available", ""),
                "gci_status": row.get("gci_status", ""),
                "gci_verdict": gci.get("verdict", row.get("convergence_verdict", "")),
                "gci_trustworthy": gci.get("gci_trustworthy", ""),
                "admission_remaining": admission_remaining(row, bucket),
                "extraction_remaining": extraction_remaining(row, bucket),
                "next_artifact_needed": next_artifact(row, bucket),
                "next_resolution_action": next_action(row, bucket),
                "diagnostic_use_allowed": "yes" if bucket != "admitted_only_candidate" else "not_needed",
                "source_paths": source_paths(row),
            }
        )
    return punch


def admitted_candidates(punch: list[dict[str, object]]) -> list[dict[str, object]]:
    rows = []
    for row in punch:
        if row["primary_bucket"] != "admitted_only_candidate":
            continue
        rows.append(
            {
                "case_id": row["case_id"],
                "qoi_id": row["qoi_id"],
                "lane": row["lane"],
                "span": row["span"],
                "quantity": row["quantity"],
                "gci_status": row["gci_status"],
                "next_use": "input_to_later_gci_results_admitted_only_csv",
                "source_paths": row["source_paths"],
            }
        )
    return rows


def extraction_queue(punch: list[dict[str, object]]) -> list[dict[str, object]]:
    rows = []
    for row in punch:
        bucket = row["primary_bucket"]
        if bucket not in {
            "missing_triplet_extraction_or_reconciliation_required",
            "gci_failed_no_resolution_without_reextract_or_remesh",
        }:
            continue
        rows.append(
            {
                "case_id": row["case_id"],
                "qoi_id": row["qoi_id"],
                "lane": row["lane"],
                "span": row["span"],
                "quantity": row["quantity"],
                "required_mesh_levels": row["extraction_remaining"],
                "extraction_or_reconciliation_needed": row["next_resolution_action"],
                "admission_precondition": row["admission_remaining"],
                "source_paths": row["source_paths"],
            }
        )
    return rows


def admission_only_rows(punch: list[dict[str, object]]) -> list[dict[str, object]]:
    rows = []
    for row in punch:
        bucket = row["primary_bucket"]
        if bucket not in {
            "thermal_admission_review_required",
            "downcomer_policy_blocked",
            "pressure_admission_review_required",
        }:
            continue
        rows.append(
            {
                "case_id": row["case_id"],
                "qoi_id": row["qoi_id"],
                "lane": row["lane"],
                "span": row["span"],
                "quantity": row["quantity"],
                "admission_gate": bucket,
                "admission_work_remaining": row["admission_remaining"],
                "source_paths": row["source_paths"],
            }
        )
    return rows


def source_manifest(inputs: Inputs) -> list[dict[str, object]]:
    paths = [
        inputs.refreshed_qoi_status,
        inputs.thermal_admission,
        inputs.gci_decisions,
        inputs.gci_results,
        inputs.raw_two_tap,
        inputs.pressure_ladder_stations,
        inputs.pressure_ladder_adjacent,
        inputs.expanded_pressure_stations,
        inputs.expanded_pressure_adjacent,
        inputs.blockers_yml,
    ]
    rows = []
    for path in paths:
        row_count = len(read_csv(path)) if path.suffix == ".csv" else ""
        rows.append({"path": rel(path), "exists": path.exists(), "row_count": row_count})
    return rows


def make_readme(summary: dict[str, object]) -> str:
    bucket_counts = summary["bucket_counts"]
    return f"""---
provenance:
  - work_products/2026-07/2026-07-14/2026-07-14_thermal_closure_mesh_gate_refresh/refreshed_qoi_mesh_gate_status.csv
  - work_products/2026-07/2026-07-13/2026-07-13_salt2_closure_qoi_mesh_gci/closure_qoi_admission_decisions.csv
  - work_products/2026-07/2026-07-15/2026-07-15_pressure_ladder_unlock_sbatch/station_pressure_ladder.csv
tags: [mesh-gci, closure-qoi, blocker-narrowing]
related:
  - .agent/blockers.yml
  - operational_notes/maps/mesh-gci-and-uncertainty.md
task: {TASK}
date: {DATE}
role: Coordinator/cfd-pp/Implementer/Tester/Writer
type: work_product
status: complete
---
# Closure-QOI Mesh-GCI Punch List

Generated: `{summary['generated_at']}`

## Result

This package narrows `closure-qoi-mesh-gci`; it does not resolve it.

- QOI rows reviewed: `{summary['qoi_row_count']}`
- Admitted-only candidates now: `{summary['admitted_only_candidate_count']}`
- Extraction/reconciliation queue rows: `{summary['extraction_queue_count']}`
- Admission-only queue rows: `{summary['admission_only_count']}`
- Bucket counts: `{bucket_counts}`

## Pressure Diagnostic Context

July 15 pressure diagnostics are available, but remain coarse diagnostic
evidence. Station pressure rows with reverse-area proxy below `0.01`:
`{summary['pressure_diagnostics']['station_rows_with_reverse_area_fraction_lt_0p01']}`;
rows at or above `0.20`:
`{summary['pressure_diagnostics']['station_rows_with_reverse_area_fraction_ge_0p20']}`.

## Outputs

- `closure_qoi_blocker_punch_list.csv`
- `admitted_only_candidate_matrix.csv`
- `extraction_queue_candidates.csv`
- `admission_only_candidates.csv`
- `closure_qoi_narrowing_decision.md`
- `source_manifest.csv`
- `summary.json`
"""


def make_decision(summary: dict[str, object]) -> str:
    return f"""---
provenance:
  - work_products/2026-07/2026-07-16/2026-07-16_closure_qoi_mesh_gci_punch_list/closure_qoi_blocker_punch_list.csv
tags: [mesh-gci, closure-qoi, blockers]
related:
  - .agent/blockers.yml
  - .agent/BLOCKERS.md
task: {TASK}
date: {DATE}
role: Coordinator/cfd-pp/Writer
type: work_product
status: complete
---
# Closure-QOI Mesh-GCI Narrowing Decision

## Decision

`closure-qoi-mesh-gci` remains open after this narrowing pass. The blocker is
now reduced to the explicit rows in `closure_qoi_blocker_punch_list.csv`.

## Current Counts

- QOI rows reviewed: `{summary['qoi_row_count']}`
- Admitted-only candidates: `{summary['admitted_only_candidate_count']}`
- Publication-ready rows promoted by this task: `0`
- Extraction/reconciliation queue rows: `{summary['extraction_queue_count']}`
- Admission-only queue rows: `{summary['admission_only_count']}`

## Next Resolution Step

The next task may resolve the blocker only if it first consumes this package,
builds `gci_results_admitted_only.csv` from admitted rows only, writes
`closure_qoi_resolution_decision.md`, updates `.agent/blockers.yml`, and
regenerates `.agent/BLOCKERS.md`. If `admitted_only_candidate_matrix.csv` is
empty, the resolution task must either produce new admitted evidence or keep the
blocker open with the narrowed punch list.
"""


def build_package(output: Path = OUT, inputs: Inputs = Inputs()) -> dict[str, object]:
    punch = build_punch_rows(inputs)
    admitted = admitted_candidates(punch)
    extraction = extraction_queue(punch)
    admission = admission_only_rows(punch)
    pressure = pressure_diagnostic_summary(inputs)
    buckets = Counter(str(row["primary_bucket"]) for row in punch)
    classifications = Counter(str(row["classification"]) for row in punch)

    summary: dict[str, object] = {
        "task": TASK,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "qoi_row_count": len(punch),
        "admitted_only_candidate_count": len(admitted),
        "extraction_queue_count": len(extraction),
        "admission_only_count": len(admission),
        "bucket_counts": dict(sorted(buckets.items())),
        "classification_counts": dict(sorted(classifications.items())),
        "pressure_diagnostics": pressure,
        "blocker_register_mutated": False,
        "generated_indexes_refreshed": False,
        "native_solver_outputs_mutated": False,
    }

    write_csv(output / "closure_qoi_blocker_punch_list.csv", punch, PUNCH_FIELDS)
    write_csv(output / "admitted_only_candidate_matrix.csv", admitted, ADMITTED_FIELDS)
    write_csv(output / "extraction_queue_candidates.csv", extraction, QUEUE_FIELDS)
    write_csv(output / "admission_only_candidates.csv", admission, ADMISSION_FIELDS)
    write_csv(output / "source_manifest.csv", source_manifest(inputs), ["path", "exists", "row_count"])
    write_json(output / "summary.json", summary)
    (output / "README.md").write_text(make_readme(summary), encoding="utf-8")
    (output / "closure_qoi_narrowing_decision.md").write_text(make_decision(summary), encoding="utf-8")
    return summary


def main() -> None:
    summary = build_package()
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
