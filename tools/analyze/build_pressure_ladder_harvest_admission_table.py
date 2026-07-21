#!/usr/bin/env python3
"""Build AGENT-449 pressure-ladder harvest admission tables.

The July 15 pressure-ladder jobs already harvested adjacent station deltas.
This builder integrates those harvested CSVs into screening/admission tables
for branch orientation, straight-loss subtraction readiness, and recirculation
masks. It does not launch jobs, mutate native CFD outputs, or fit coefficients.
"""

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any, Iterable


TASK = "AGENT-449"
DATE = "2026-07-16"
ROOT = Path(__file__).resolve().parents[2]
OUT_REL = Path("work_products/2026-07/2026-07-16/2026-07-16_pressure_ladder_harvest_admission_table")
OUT = ROOT / OUT_REL

AGENT445 = ROOT / "work_products/2026-07/2026-07-15/2026-07-15_pressure_ladder_unlock_sbatch"
AGENT447 = ROOT / "work_products/2026-07/2026-07-15/2026-07-15_expanded_salt_pressure_ladder_8pm_sbatch"
RECIRCULATION = (
    ROOT
    / "work_products/2026-07/2026-07-15/2026-07-15_recirculation_policy_forward_hydraulic_unblock_plan"
    / "current_evidence_recirculation_classification.csv"
)
BRANCH_SCORECARD = (
    ROOT / "work_products/2026-07/2026-07-15/2026-07-15_branch_specific_ordinary_pipe_scorecard"
)
RAW_TWO_TAP = (
    ROOT / "work_products/2026-07/2026-07-15/2026-07-15_staged_closure_qoi_pressure_sbatch"
)

LADDER_SOURCES = [
    {
        "harvest_package": "AGENT-445_nominal_salt2_salt3_salt4",
        "job_id": "3297860",
        "package": AGENT445,
        "adjacent": AGENT445 / "adjacent_pressure_ladder.csv",
        "station": AGENT445 / "station_pressure_ladder.csv",
    },
    {
        "harvest_package": "AGENT-447_expanded_salt1_pm5_val",
        "job_id": "3297863",
        "package": AGENT447,
        "adjacent": AGENT447 / "adjacent_pressure_ladder.csv",
        "station": AGENT447 / "station_pressure_ladder.csv",
    },
]

DEFAULT_SPLIT_ROLES = {
    "salt2_mainline": "training",
    "salt3_mainline": "validation_or_training_by_declared_scorecard",
    "salt4_mainline": "holdout_or_training_by_declared_scorecard",
}

UPCOMER_HYBRID_BRANCHES = {"left_lower_leg", "test_section_span", "left_upper_leg"}
LOW_RECIRC_THRESHOLD = 0.01
MATERIAL_RECIRC_THRESHOLD = 0.20


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


def as_float(value: str | None, default: float = 0.0) -> float:
    if value is None or value == "":
        return default
    try:
        return float(value)
    except ValueError:
        return default


def sign(value: float, eps: float = 1.0e-12) -> int:
    if value > eps:
        return 1
    if value < -eps:
        return -1
    return 0


def sign_label(value: float) -> str:
    return {1: "positive", -1: "negative", 0: "near_zero"}[sign(value)]


def majority_sign_fraction(values: list[float]) -> tuple[str, float]:
    nonzero = [sign(value) for value in values if sign(value) != 0]
    if not nonzero:
        return "near_zero", 0.0
    counts = Counter(nonzero)
    dominant, count = counts.most_common(1)[0]
    return sign_label(float(dominant)), count / len(nonzero)


def recirculation_band(max_reverse_area_fraction: float) -> str:
    if max_reverse_area_fraction < LOW_RECIRC_THRESHOLD:
        return "low_recirc_mask_pass"
    if max_reverse_area_fraction >= MATERIAL_RECIRC_THRESHOLD:
        return "material_recirc_mask_fail"
    return "recirc_caution_not_fit_admitted"


def recirculation_gate_from_pairs(pair_rows: list[dict[str, Any]]) -> str:
    if not pair_rows:
        return "no_pairs"
    bands = {row["pair_recirc_band"] for row in pair_rows}
    if "material_recirc_mask_fail" in bands:
        return "blocked_material_recirculation_mask"
    if bands == {"low_recirc_mask_pass"}:
        return "passes_low_recirc_mask_pending_other_gates"
    return "blocked_or_caution_reverse_area_fraction"


def split_role(row: dict[str, str]) -> str:
    return row.get("split_role") or DEFAULT_SPLIT_ROLES.get(row.get("case_key", ""), "unspecified_diagnostic")


def load_adjacent_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for source in LADDER_SOURCES:
        for row in read_csv(source["adjacent"]):
            from_raf = as_float(row.get("from_reverse_area_fraction_proxy"))
            to_raf = as_float(row.get("to_reverse_area_fraction_proxy"))
            max_raf = max(from_raf, to_raf)
            branch = row["branch"]
            rows.append(
                {
                    **row,
                    "split_role": split_role(row),
                    "harvest_package": source["harvest_package"],
                    "harvest_job_id": source["job_id"],
                    "source_path": rel(source["adjacent"]),
                    "delta_p_to_minus_from_Pa_float": as_float(row.get("delta_p_to_minus_from_Pa")),
                    "delta_p_rgh_to_minus_from_Pa_float": as_float(row.get("delta_p_rgh_to_minus_from_Pa")),
                    "max_reverse_area_fraction_proxy": max_raf,
                    "pair_recirc_band": recirculation_band(max_raf),
                    "upcomer_hybrid_lane": "yes" if branch in UPCOMER_HYBRID_BRANCHES else "no",
                }
            )
    return rows


def load_station_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for source in LADDER_SOURCES:
        for row in read_csv(source["station"]):
            rows.append(
                {
                    **row,
                    "split_role": split_role(row),
                    "harvest_package": source["harvest_package"],
                    "harvest_job_id": source["job_id"],
                    "source_path": rel(source["station"]),
                }
            )
    return rows


def recirculation_evidence_lookup() -> dict[tuple[str, str], list[dict[str, str]]]:
    lookup: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in read_csv(RECIRCULATION):
        evidence_id = row.get("evidence_id", "")
        branch = evidence_id.split(":")[-1] if ":" in evidence_id else row.get("location", "")
        if branch:
            lookup[(row.get("case_key", ""), branch)].append(row)
    return lookup


def trimmed_mean_abs_outlier(values: list[float]) -> float:
    if not values:
        return 0.0
    if len(values) <= 2:
        return mean(values)
    indexed = list(enumerate(values))
    largest_abs_index, _ = max(indexed, key=lambda item: abs(item[1]))
    kept = [value for index, value in indexed if index != largest_abs_index]
    return mean(kept)


def orientation_status(net_rgh: float, sign_fraction_rgh: float, pair_rows: list[dict[str, Any]]) -> str:
    recirc_gate = recirculation_gate_from_pairs(pair_rows)
    if sign(net_rgh) == 0 or sign_fraction_rgh < 0.75:
        return "orientation_unresolved_mixed_adjacent_p_rgh"
    if recirc_gate == "blocked_material_recirculation_mask":
        return "orientation_screen_only_material_recirc"
    return "diagnostic_orientation_candidate_pending_pressure_definition"


def pressure_definition_status(net_p: float, net_rgh: float) -> str:
    if sign(net_p) == 0 or sign(net_rgh) == 0:
        return "pressure_definition_near_zero_review"
    if sign(net_p) != sign(net_rgh):
        return "static_p_vs_p_rgh_net_sign_conflict_review"
    return "static_p_and_p_rgh_net_sign_agree"


def straight_loss_status(row: dict[str, Any]) -> str:
    if row["recirculation_mask_status"] != "passes_low_recirc_mask_pending_other_gates":
        return "screen_only_no_straight_loss_subtraction_due_recirc_mask"
    if not row["orientation_status"].startswith("diagnostic_orientation_candidate"):
        return "screen_only_no_straight_loss_subtraction_due_orientation"
    return "candidate_estimate_only_needs_geometry_pressure_definition_mesh_gci"


def final_admission_status(row: dict[str, Any]) -> str:
    blockers = row["blockers"]
    if row["recirculation_mask_status"].startswith("blocked"):
        return "not_admitted_recirc_mask"
    if row["orientation_status"].startswith("orientation_unresolved"):
        return "not_admitted_orientation"
    if "pressure_definition_conflict" in blockers:
        return "not_admitted_pressure_definition"
    return "not_admitted_pending_straight_loss_mesh_gci"


def build_branch_admission_table(
    adjacent_rows: list[dict[str, Any]], station_rows: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    recirc_lookup = recirculation_evidence_lookup()
    station_counts = Counter((row["case_key"], row["branch"]) for row in station_rows)
    groups: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in adjacent_rows:
        groups[(row["case_key"], row["branch"], row["harvest_package"])].append(row)

    output: list[dict[str, Any]] = []
    for (case_key, branch, harvest_package), pair_rows in sorted(groups.items()):
        delta_p = [row["delta_p_to_minus_from_Pa_float"] for row in pair_rows]
        delta_p_rgh = [row["delta_p_rgh_to_minus_from_Pa_float"] for row in pair_rows]
        net_p = sum(delta_p)
        net_rgh = sum(delta_p_rgh)
        dominant_p, sign_fraction_p = majority_sign_fraction(delta_p)
        dominant_rgh, sign_fraction_rgh = majority_sign_fraction(delta_p_rgh)
        max_raf = max(row["max_reverse_area_fraction_proxy"] for row in pair_rows)
        recirc_gate = recirculation_gate_from_pairs(pair_rows)
        evidence_rows = recirc_lookup.get((case_key, branch), [])
        evidence_gate = "none"
        if evidence_rows:
            evidence_gate = "recirculation_policy_evidence_present"
        if branch in UPCOMER_HYBRID_BRANCHES:
            evidence_gate = "upcomer_hybrid_lane_by_policy"

        row: dict[str, Any] = {
            "case_key": case_key,
            "case_id": pair_rows[0].get("case_id", ""),
            "split_role": pair_rows[0].get("split_role", ""),
            "harvest_package": harvest_package,
            "harvest_job_id": pair_rows[0].get("harvest_job_id", ""),
            "branch": branch,
            "station_count": station_counts.get((case_key, branch), ""),
            "adjacent_pair_count": len(pair_rows),
            "net_delta_p_to_minus_from_Pa": net_p,
            "net_delta_p_rgh_to_minus_from_Pa": net_rgh,
            "dominant_adjacent_delta_p_sign": dominant_p,
            "dominant_adjacent_delta_p_fraction": sign_fraction_p,
            "dominant_adjacent_delta_p_rgh_sign": dominant_rgh,
            "dominant_adjacent_delta_p_rgh_fraction": sign_fraction_rgh,
            "mean_adjacent_delta_p_rgh_Pa": mean(delta_p_rgh),
            "trimmed_mean_adjacent_delta_p_rgh_Pa": trimmed_mean_abs_outlier(delta_p_rgh),
            "max_pair_reverse_area_fraction_proxy": max_raf,
            "low_recirc_pair_count": sum(1 for pair in pair_rows if pair["pair_recirc_band"] == "low_recirc_mask_pass"),
            "material_recirc_pair_count": sum(
                1 for pair in pair_rows if pair["pair_recirc_band"] == "material_recirc_mask_fail"
            ),
            "upcomer_hybrid_lane": "yes" if branch in UPCOMER_HYBRID_BRANCHES else "no",
            "recirculation_policy_evidence_rows": len(evidence_rows),
            "recirculation_policy_context": evidence_gate,
            "recirculation_mask_status": recirc_gate,
            "pressure_definition_status": pressure_definition_status(net_p, net_rgh),
            "source_paths": ";".join(sorted({row["source_path"] for row in pair_rows})),
        }
        row["orientation_status"] = orientation_status(net_rgh, sign_fraction_rgh, pair_rows)
        blockers = [
            "coarse_only_no_mesh_gci",
            "no_geometry_distance_normalization",
            "component_K_not_isolated",
        ]
        if row["pressure_definition_status"] != "static_p_and_p_rgh_net_sign_agree":
            blockers.append("pressure_definition_conflict")
        if row["orientation_status"].startswith("orientation_unresolved"):
            blockers.append("orientation_unresolved")
        if row["recirculation_mask_status"].startswith("blocked"):
            blockers.append("recirculation_mask")
        if row["upcomer_hybrid_lane"] == "yes":
            blockers.append("upcomer_hybrid_lane_not_ordinary_pipe_fit")
        row["blockers"] = ";".join(blockers)
        row["straight_loss_subtraction_status"] = straight_loss_status(row)
        row["admission_status"] = final_admission_status(row)
        row["true_f_D_or_K_fit_admitted"] = "no"
        row["next_use"] = (
            "orientation_and_straight_loss_screen_only; do_not_submit_duplicate_pressure_ladder_jobs"
        )
        output.append(row)
    return output


def build_adjacent_pair_screen(adjacent_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for row in adjacent_rows:
        rows.append(
            {
                "case_key": row["case_key"],
                "split_role": row.get("split_role", ""),
                "harvest_package": row["harvest_package"],
                "branch": row["branch"],
                "from_station": row["from_station"],
                "to_station": row["to_station"],
                "delta_p_to_minus_from_Pa": row["delta_p_to_minus_from_Pa"],
                "delta_p_rgh_to_minus_from_Pa": row["delta_p_rgh_to_minus_from_Pa"],
                "delta_p_rgh_sign": sign_label(row["delta_p_rgh_to_minus_from_Pa_float"]),
                "from_reverse_area_fraction_proxy": row["from_reverse_area_fraction_proxy"],
                "to_reverse_area_fraction_proxy": row["to_reverse_area_fraction_proxy"],
                "max_reverse_area_fraction_proxy": row["max_reverse_area_fraction_proxy"],
                "pair_recirc_band": row["pair_recirc_band"],
                "upcomer_hybrid_lane": row["upcomer_hybrid_lane"],
                "admission_status": "diagnostic_pair_only_not_fit_admitted",
                "source_path": row["source_path"],
            }
        )
    return rows


def build_case_summary(branch_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in branch_rows:
        groups[row["case_key"]].append(row)
    output = []
    for case_key, rows in sorted(groups.items()):
        admitted = sum(1 for row in rows if row["true_f_D_or_K_fit_admitted"] == "yes")
        output.append(
            {
                "case_key": case_key,
                "split_role": rows[0]["split_role"],
                "branch_rows": len(rows),
                "orientation_candidate_rows": sum(
                    1 for row in rows if row["orientation_status"].startswith("diagnostic_orientation_candidate")
                ),
                "recirc_mask_blocked_rows": sum(
                    1 for row in rows if row["recirculation_mask_status"].startswith("blocked")
                ),
                "pressure_definition_conflict_rows": sum(
                    1 for row in rows if "pressure_definition_conflict" in row["blockers"]
                ),
                "true_f_D_or_K_fit_admitted_rows": admitted,
                "case_admission_status": "no_true_fit_rows_admitted" if admitted == 0 else "review_required",
                "next_use": "use harvested ladders for admission screening; do not launch duplicate ladder jobs",
            }
        )
    return output


def write_source_manifest() -> None:
    rows = [
        {
            "source_role": "nominal Salt2/Salt3/Salt4 pressure ladder harvest",
            "path": rel(AGENT445 / "adjacent_pressure_ladder.csv"),
            "job_id": "3297860",
            "use": "read-only branch orientation and straight-loss screen",
        },
        {
            "source_role": "expanded Salt1/Salt2+/-5Q/Salt4+/-5Q/val_salt2 pressure ladder harvest",
            "path": rel(AGENT447 / "adjacent_pressure_ladder.csv"),
            "job_id": "3297863",
            "use": "read-only branch orientation and straight-loss screen",
        },
        {
            "source_role": "recirculation policy evidence",
            "path": rel(RECIRCULATION),
            "job_id": "",
            "use": "recirculation mask policy and upcomer hybrid lane context",
        },
        {
            "source_role": "prior branch ordinary-pipe scorecard",
            "path": rel(BRANCH_SCORECARD / "branch_specific_fit_mask.csv"),
            "job_id": "",
            "use": "ordinary-pipe/upcomer exclusion continuity",
        },
        {
            "source_role": "raw two-tap pressure harvest context",
            "path": rel(RAW_TWO_TAP / "raw_pressure_two_tap_harvest.csv"),
            "job_id": "3297845",
            "use": "context only; pressure ladder supersedes two isolated taps for orientation screening",
        },
    ]
    write_csv(
        OUT / "source_manifest.csv",
        rows,
        ["source_role", "path", "job_id", "use"],
    )


def write_readme(summary: dict[str, Any]) -> None:
    text = f"""---
provenance:
  - {rel(AGENT445 / "adjacent_pressure_ladder.csv")}
  - {rel(AGENT447 / "adjacent_pressure_ladder.csv")}
  - {rel(RECIRCULATION)}
  - {rel(BRANCH_SCORECARD / "branch_specific_fit_mask.csv")}
tags: [pressure-ladder, hydraulics, recirculation-mask, branch-orientation]
related:
  - {rel(AGENT445 / "README.md")}
  - {rel(AGENT447 / "README.md")}
  - {rel(RAW_TWO_TAP / "README.md")}
task: {TASK}
date: {DATE}
role: Hydraulics/Implementer/Tester/Writer
type: work_product
status: complete
---
# Pressure Ladder Harvest Admission Table

## Purpose

This package integrates the completed July 15 pressure-ladder harvests into the
branch orientation, straight-loss subtraction, and recirculation-mask admission
screen requested for the next hydraulic step. It consumes existing harvested
CSV outputs only. No duplicate pressure-ladder, closure-QOI, or OpenFOAM jobs
were submitted.

## Outputs

- `branch_orientation_straight_loss_recirc_admission.csv`: one row per
  `case_key` plus branch, with adjacent `p_rgh` orientation screening,
  straight-loss subtraction readiness, pressure-definition conflicts, and
  recirculation-mask status.
- `adjacent_pair_recirc_screen.csv`: one row per adjacent station pair from the
  harvested ladders with reverse-area mask classification.
- `case_pressure_ladder_admission_summary.csv`: case-level rollup.
- `source_manifest.csv`: exact source packages and job IDs.

## Result

Harvested ladder inputs are available and parsed:

- AGENT-445 job `3297860`: {summary["agent445_adjacent_rows"]} adjacent rows.
- AGENT-447 job `3297863`: {summary["agent447_adjacent_rows"]} adjacent rows.
- Integrated branch rows: {summary["branch_rows"]}.
- True `f_D` or component `K` fit-admitted branch rows: {summary["true_fit_rows"]}.

Every branch remains diagnostic for coefficient fitting. The most common
blocking reasons are recirculation masks, unresolved or screen-only orientation,
static-`p` versus `p_rgh` pressure-definition conflicts, missing geometry
distance normalization, missing mesh/GCI, and absent component isolation. The
upcomer-related branches (`left_lower_leg`, `test_section_span`, and
`left_upper_leg`) stay in the hybrid/onset lane, not ordinary single-stream
`Nu`, `f_D`, or `K` fitting.

## Admission Contract

Use these tables to decide what to analyze next, not as final coefficients.
Before any localized `K` or distributed `f_D` fit, a future package must admit
pressure definition, tap orientation, straight-loss subtraction, low
recirculation (`RAF < 0.01` for true single-stream fits), mesh/GCI, and
time-window/source provenance together.
"""
    (OUT / "README.md").write_text(text, encoding="utf-8")


def build() -> dict[str, Any]:
    adjacent_rows = load_adjacent_rows()
    station_rows = load_station_rows()
    branch_rows = build_branch_admission_table(adjacent_rows, station_rows)
    pair_rows = build_adjacent_pair_screen(adjacent_rows)
    case_rows = build_case_summary(branch_rows)

    branch_fields = [
        "case_key",
        "case_id",
        "split_role",
        "harvest_package",
        "harvest_job_id",
        "branch",
        "station_count",
        "adjacent_pair_count",
        "net_delta_p_to_minus_from_Pa",
        "net_delta_p_rgh_to_minus_from_Pa",
        "dominant_adjacent_delta_p_sign",
        "dominant_adjacent_delta_p_fraction",
        "dominant_adjacent_delta_p_rgh_sign",
        "dominant_adjacent_delta_p_rgh_fraction",
        "mean_adjacent_delta_p_rgh_Pa",
        "trimmed_mean_adjacent_delta_p_rgh_Pa",
        "max_pair_reverse_area_fraction_proxy",
        "low_recirc_pair_count",
        "material_recirc_pair_count",
        "upcomer_hybrid_lane",
        "recirculation_policy_evidence_rows",
        "recirculation_policy_context",
        "recirculation_mask_status",
        "pressure_definition_status",
        "orientation_status",
        "straight_loss_subtraction_status",
        "admission_status",
        "true_f_D_or_K_fit_admitted",
        "blockers",
        "next_use",
        "source_paths",
    ]
    pair_fields = [
        "case_key",
        "split_role",
        "harvest_package",
        "branch",
        "from_station",
        "to_station",
        "delta_p_to_minus_from_Pa",
        "delta_p_rgh_to_minus_from_Pa",
        "delta_p_rgh_sign",
        "from_reverse_area_fraction_proxy",
        "to_reverse_area_fraction_proxy",
        "max_reverse_area_fraction_proxy",
        "pair_recirc_band",
        "upcomer_hybrid_lane",
        "admission_status",
        "source_path",
    ]
    case_fields = [
        "case_key",
        "split_role",
        "branch_rows",
        "orientation_candidate_rows",
        "recirc_mask_blocked_rows",
        "pressure_definition_conflict_rows",
        "true_f_D_or_K_fit_admitted_rows",
        "case_admission_status",
        "next_use",
    ]

    write_csv(OUT / "branch_orientation_straight_loss_recirc_admission.csv", branch_rows, branch_fields)
    write_csv(OUT / "adjacent_pair_recirc_screen.csv", pair_rows, pair_fields)
    write_csv(OUT / "case_pressure_ladder_admission_summary.csv", case_rows, case_fields)
    write_source_manifest()

    package_counts = Counter(row["harvest_package"] for row in adjacent_rows)
    summary = {
        "task": TASK,
        "generated_at_utc": utc_now(),
        "agent445_adjacent_rows": package_counts["AGENT-445_nominal_salt2_salt3_salt4"],
        "agent447_adjacent_rows": package_counts["AGENT-447_expanded_salt1_pm5_val"],
        "adjacent_pair_rows": len(pair_rows),
        "station_rows": len(station_rows),
        "branch_rows": len(branch_rows),
        "case_rows": len(case_rows),
        "orientation_candidate_branch_rows": sum(
            1 for row in branch_rows if row["orientation_status"].startswith("diagnostic_orientation_candidate")
        ),
        "recirc_mask_blocked_branch_rows": sum(
            1 for row in branch_rows if row["recirculation_mask_status"].startswith("blocked")
        ),
        "pressure_definition_conflict_branch_rows": sum(
            1 for row in branch_rows if "pressure_definition_conflict" in row["blockers"]
        ),
        "true_fit_rows": sum(1 for row in branch_rows if row["true_f_D_or_K_fit_admitted"] == "yes"),
        "final_decision": "pressure_ladders_harvested_integrated_no_true_fd_or_k_fit_admitted",
        "no_duplicate_jobs": True,
    }
    write_json(OUT / "summary.json", summary)
    write_readme(summary)
    return summary


def main() -> None:
    summary = build()
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
