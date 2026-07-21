#!/usr/bin/env python3
"""Build streamwise pressure / 1D maps for harvested CFD pressure ladders.

This is the reusable version of the Salt2-only AGENT-456 builder. It consumes
available post-processed station-pressure ladder CSVs, applies the locked CFD
span-to-1D mapping, and writes station/branch pressure tables with provenance.
"""

from __future__ import annotations

import csv
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any


TASK = "AGENT-457"
DATE = "2026-07-16"
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.analyze.build_salt2_streamwise_pressure_1d_map import BRANCH_METADATA, BRANCH_ORDER

OUT_REL = Path("work_products/2026-07/2026-07-16/2026-07-16_postprocessed_cfd_streamwise_pressure_1d_maps")
OUT = ROOT / OUT_REL

PRESSURE_SOURCES = [
    {
        "harvest_package": "AGENT-445_pressure_ladder_unlock_sbatch",
        "harvest_task": "AGENT-445",
        "harvest_job_id": "3297860",
        "package_path": Path("work_products/2026-07/2026-07-15/2026-07-15_pressure_ladder_unlock_sbatch"),
        "station_csv": Path(
            "work_products/2026-07/2026-07-15/2026-07-15_pressure_ladder_unlock_sbatch/station_pressure_ladder.csv"
        ),
        "source_manifest": Path(
            "work_products/2026-07/2026-07-15/2026-07-15_pressure_ladder_unlock_sbatch/source_manifest.csv"
        ),
        "summary_json": Path("work_products/2026-07/2026-07-15/2026-07-15_pressure_ladder_unlock_sbatch/summary.json"),
        "description": "Mainline Salt2/Salt3/Salt4 pressure ladder harvest.",
    },
    {
        "harvest_package": "AGENT-447_expanded_salt_pressure_ladder_8pm_sbatch",
        "harvest_task": "AGENT-447",
        "harvest_job_id": "3297863",
        "package_path": Path("work_products/2026-07/2026-07-15/2026-07-15_expanded_salt_pressure_ladder_8pm_sbatch"),
        "station_csv": Path(
            "work_products/2026-07/2026-07-15/2026-07-15_expanded_salt_pressure_ladder_8pm_sbatch/station_pressure_ladder.csv"
        ),
        "source_manifest": Path(
            "work_products/2026-07/2026-07-15/2026-07-15_expanded_salt_pressure_ladder_8pm_sbatch/source_manifest.csv"
        ),
        "summary_json": Path(
            "work_products/2026-07/2026-07-15/2026-07-15_expanded_salt_pressure_ladder_8pm_sbatch/summary.json"
        ),
        "description": "Expanded Salt1/Salt2/Salt4 perturbation and validation pressure ladder harvest.",
    },
]

DEFAULT_SPLIT_ROLES = {
    "salt2_mainline": "training",
    "salt3_mainline": "validation_or_training_by_declared_scorecard",
    "salt4_mainline": "holdout_or_training_by_declared_scorecard",
}

DEFAULT_ADMISSION_CAVEATS = {
    "salt2_mainline": "Mainline Salt2 pressure ladder diagnostic until mesh/GCI and pressure gates admit.",
    "salt3_mainline": "Mainline Salt3 pressure ladder diagnostic until mesh/GCI and pressure gates admit.",
    "salt4_mainline": "Mainline Salt4 pressure ladder diagnostic until mesh/GCI and pressure gates admit.",
}

FLUID_SEGMENTS = (
    "../cfd-modeling-tools/tamu_first_order_model/Fluid/outputs_tamu_loop_v2_resumable/geometry/loop_segments.csv"
)
GEOMETRY_REFERENCE = "reference/geometry_reference.md"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def path_resolve(path: Path | str) -> Path:
    path = Path(path)
    return (ROOT / path).resolve() if not path.is_absolute() else path.resolve()


def rel(path: Path | str) -> str:
    resolved = path_resolve(path)
    try:
        return str(resolved.relative_to(ROOT.resolve()))
    except ValueError:
        return str(resolved)


def read_csv(path: Path | str) -> list[dict[str, str]]:
    with path_resolve(path).open(newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = list(rows[0].keys()) if rows else []
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def f(row: dict[str, Any], key: str) -> float:
    return float(row[key])


def station_suffix(label: str) -> str:
    return label.split("__", 1)[1]


def load_source_manifest(source: dict[str, Any]) -> dict[str, dict[str, str]]:
    rows = read_csv(source["source_manifest"])
    by_case: dict[str, dict[str, str]] = {}
    for row in rows:
        case_key = row.get("case_key") or row.get("role")
        if case_key and case_key != "OpenFOAM 13 env":
            by_case[case_key] = row
    return by_case


def load_harvest_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for source in PRESSURE_SOURCES:
        manifest = load_source_manifest(source)
        for row in read_csv(source["station_csv"]):
            case_key = row["case_key"]
            manifest_row = manifest.get(case_key, {})
            enriched = dict(row)
            enriched["harvest_package"] = source["harvest_package"]
            enriched["harvest_task"] = source["harvest_task"]
            enriched["harvest_job_id"] = source["harvest_job_id"]
            enriched["harvest_package_path"] = rel(source["package_path"])
            enriched["harvest_station_csv"] = rel(source["station_csv"])
            enriched["harvest_summary_json"] = rel(source["summary_json"])
            enriched["native_case_path"] = manifest_row.get("path", "")
            enriched["native_case_exists_at_harvest"] = manifest_row.get("exists", "")
            enriched["split_role"] = row.get("split_role") or manifest_row.get("split_role") or DEFAULT_SPLIT_ROLES.get(case_key, "not_declared")
            enriched["time_window_s"] = row.get("time_window_s") or manifest_row.get("time_window_s", "")
            enriched["admission_caveat"] = row.get("admission_caveat") or DEFAULT_ADMISSION_CAVEATS.get(
                case_key, "Pressure ladder diagnostic until mesh/GCI and pressure gates admit."
            )
            rows.append(enriched)
    return rows


def expected_labels() -> set[str]:
    return {label for meta in BRANCH_METADATA.values() for label in meta["flow_station_order"]}


def validate_case_rows(case_key: str, rows: list[dict[str, Any]]) -> None:
    if len(rows) != 30:
        raise ValueError(f"{case_key}: expected 30 station rows, found {len(rows)}")
    labels = {row["station_label"] for row in rows}
    missing = sorted(expected_labels() - labels)
    extra = sorted(labels - expected_labels())
    if missing or extra:
        raise ValueError(f"{case_key}: station label mismatch, missing={missing}, extra={extra}")


def build_station_map_for_case(case_key: str, source_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    validate_case_rows(case_key, source_rows)
    by_label = {row["station_label"]: row for row in source_rows}
    start = by_label[BRANCH_METADATA["lower_leg"]["flow_station_order"][0]]
    start_p = f(start, "mean_p_Pa")
    start_p_rgh = f(start, "mean_p_rgh_Pa")

    mapped: list[dict[str, Any]] = []
    loop_index = 0
    for branch in BRANCH_ORDER:
        meta = BRANCH_METADATA[branch]
        branch_start_p: float | None = None
        branch_start_p_rgh: float | None = None
        for branch_flow_index, station_label in enumerate(meta["flow_station_order"]):
            source = by_label[station_label]
            mean_p = f(source, "mean_p_Pa")
            mean_p_rgh = f(source, "mean_p_rgh_Pa")
            if branch_flow_index == 0:
                branch_start_p = mean_p
                branch_start_p_rgh = mean_p_rgh
            previous = mapped[-1] if mapped else None
            mapped.append(
                {
                    "case_id": source["case_id"],
                    "case_key": source["case_key"],
                    "split_role": source["split_role"],
                    "time_window_s": source["time_window_s"],
                    "admission_caveat": source["admission_caveat"],
                    "source_id": source["source_id"],
                    "time_s": source["time_s"],
                    "harvest_package": source["harvest_package"],
                    "harvest_task": source["harvest_task"],
                    "harvest_job_id": source["harvest_job_id"],
                    "harvest_package_path": source["harvest_package_path"],
                    "harvest_station_csv": source["harvest_station_csv"],
                    "harvest_summary_json": source["harvest_summary_json"],
                    "native_case_path": source["native_case_path"],
                    "native_case_exists_at_harvest": source["native_case_exists_at_harvest"],
                    "loop_order_index": loop_index,
                    "branch_flow_index": branch_flow_index,
                    "station_label": station_label,
                    "station_suffix": station_suffix(station_label),
                    "source_station_index": source["station_index"],
                    "cfd_span": branch,
                    "physical_location_label": meta["physical_location_label"],
                    "loop_region": meta["loop_region"],
                    "one_d_parent_segment": meta["one_d_parent_segment"],
                    "one_d_component_segments": ";".join(meta["one_d_component_segments"]),
                    "one_d_role": meta["one_d_role"],
                    "flow_order_note": meta["flow_order_note"],
                    "cfd_span_length_m_reference": meta["cfd_span_length_m_reference"],
                    "one_d_component_length_m": meta["one_d_component_length_m"],
                    "length_basis_note": meta["length_basis_note"],
                    "face_count": source["face_count"],
                    "mean_p_Pa": mean_p,
                    "mean_p_rgh_Pa": mean_p_rgh,
                    "mean_un_m_s": f(source, "mean_un_m_s"),
                    "mean_rho_kg_m3": f(source, "mean_rho_kg_m3"),
                    "reverse_area_fraction_proxy": f(source, "reverse_area_fraction_proxy"),
                    "relative_p_from_case_loop_start_Pa": mean_p - start_p,
                    "relative_p_rgh_from_case_loop_start_Pa": mean_p_rgh - start_p_rgh,
                    "relative_p_from_branch_start_Pa": mean_p - float(branch_start_p),
                    "relative_p_rgh_from_branch_start_Pa": mean_p_rgh - float(branch_start_p_rgh),
                    "delta_from_previous_case_loop_p_Pa": "" if previous is None else mean_p - float(previous["mean_p_Pa"]),
                    "delta_from_previous_case_loop_p_rgh_Pa": ""
                    if previous is None
                    else mean_p_rgh - float(previous["mean_p_rgh_Pa"]),
                    "admission_status": source["admission_status"],
                    "fit_eligible": source["fit_eligible"],
                    "blockers": source["blockers"],
                    "mapping_status": "label_locked_reference_mapping",
                    "plane_file": source["plane_file"],
                    "source_path": source["harvest_station_csv"],
                }
            )
            loop_index += 1
    return mapped


def weighted_average(rows: list[dict[str, Any]], value_key: str, weight_key: str) -> float:
    weights = [float(row[weight_key]) for row in rows]
    return sum(float(row[value_key]) * weight for row, weight in zip(rows, weights)) / sum(weights)


def build_branch_averages(station_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in station_rows:
        grouped[(str(row["case_key"]), str(row["cfd_span"]))].append(row)

    rows: list[dict[str, Any]] = []
    for case_key in sorted({row["case_key"] for row in station_rows}):
        for branch in BRANCH_ORDER:
            branch_rows = sorted(grouped[(case_key, branch)], key=lambda row: int(row["branch_flow_index"]))
            start = branch_rows[0]
            end = branch_rows[-1]
            meta = BRANCH_METADATA[branch]
            p_values = [float(row["mean_p_Pa"]) for row in branch_rows]
            p_rgh_values = [float(row["mean_p_rgh_Pa"]) for row in branch_rows]
            rows.append(
                {
                    "case_key": case_key,
                    "case_id": start["case_id"],
                    "split_role": start["split_role"],
                    "time_s": start["time_s"],
                    "time_window_s": start["time_window_s"],
                    "harvest_package": start["harvest_package"],
                    "harvest_task": start["harvest_task"],
                    "harvest_job_id": start["harvest_job_id"],
                    "native_case_path": start["native_case_path"],
                    "loop_branch_order_index": BRANCH_ORDER.index(branch),
                    "cfd_span": branch,
                    "physical_location_label": meta["physical_location_label"],
                    "loop_region": meta["loop_region"],
                    "one_d_parent_segment": meta["one_d_parent_segment"],
                    "one_d_component_segments": ";".join(meta["one_d_component_segments"]),
                    "one_d_role": meta["one_d_role"],
                    "station_count": len(branch_rows),
                    "flow_start_station_label": start["station_label"],
                    "flow_end_station_label": end["station_label"],
                    "arithmetic_mean_p_Pa": mean(p_values),
                    "face_count_weighted_mean_p_Pa": weighted_average(branch_rows, "mean_p_Pa", "face_count"),
                    "min_mean_p_Pa": min(p_values),
                    "max_mean_p_Pa": max(p_values),
                    "flow_end_minus_start_p_Pa": float(end["mean_p_Pa"]) - float(start["mean_p_Pa"]),
                    "arithmetic_mean_p_rgh_Pa": mean(p_rgh_values),
                    "face_count_weighted_mean_p_rgh_Pa": weighted_average(branch_rows, "mean_p_rgh_Pa", "face_count"),
                    "min_mean_p_rgh_Pa": min(p_rgh_values),
                    "max_mean_p_rgh_Pa": max(p_rgh_values),
                    "flow_end_minus_start_p_rgh_Pa": float(end["mean_p_rgh_Pa"]) - float(start["mean_p_rgh_Pa"]),
                    "max_reverse_area_fraction_proxy": max(float(row["reverse_area_fraction_proxy"]) for row in branch_rows),
                    "mean_reverse_area_fraction_proxy": mean(float(row["reverse_area_fraction_proxy"]) for row in branch_rows),
                    "flow_order_note": meta["flow_order_note"],
                    "length_basis_note": meta["length_basis_note"],
                    "admission_caveat": start["admission_caveat"],
                    "admission_status": "diagnostic_station_pressure_ladder_not_fit_admitted",
                    "fit_eligible": "no",
                    "mapping_status": "label_locked_reference_mapping",
                    "source_path": start["source_path"],
                }
            )
    return rows


def build_case_provenance(source_rows: list[dict[str, Any]], station_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for case_key in sorted({row["case_key"] for row in source_rows}):
        raw = [row for row in source_rows if row["case_key"] == case_key]
        mapped = [row for row in station_rows if row["case_key"] == case_key]
        first = raw[0]
        rows.append(
            {
                "case_key": case_key,
                "case_id": first["case_id"],
                "split_role": first["split_role"],
                "source_id": first["source_id"],
                "time_s": first["time_s"],
                "time_window_s": first["time_window_s"],
                "harvest_package": first["harvest_package"],
                "harvest_task": first["harvest_task"],
                "harvest_job_id": first["harvest_job_id"],
                "harvest_station_csv": first["harvest_station_csv"],
                "harvest_summary_json": first["harvest_summary_json"],
                "native_case_path": first["native_case_path"],
                "native_case_exists_at_harvest": first["native_case_exists_at_harvest"],
                "station_rows_in_source": len(raw),
                "station_rows_mapped": len(mapped),
                "branch_rows_expected": len(BRANCH_ORDER),
                "admission_status": first["admission_status"],
                "fit_eligible": first["fit_eligible"],
                "admission_caveat": first["admission_caveat"],
                "blockers": first["blockers"],
            }
        )
    return rows


def fmt(value: Any, digits: int = 3) -> str:
    if isinstance(value, float):
        return f"{value:.{digits}f}"
    return str(value)


def write_case_markdowns(branch_rows: list[dict[str, Any]], case_provenance: list[dict[str, Any]]) -> None:
    by_case: dict[str, list[dict[str, Any]]] = defaultdict(list)
    provenance_by_case = {row["case_key"]: row for row in case_provenance}
    for row in branch_rows:
        by_case[str(row["case_key"])].append(row)
    per_case = OUT / "per_case"
    per_case.mkdir(parents=True, exist_ok=True)
    for case_key in sorted(by_case):
        provenance = provenance_by_case[case_key]
        rows = sorted(by_case[case_key], key=lambda row: int(row["loop_branch_order_index"]))
        lines = [
            f"# {case_key} Streamwise Pressure / 1D Map",
            "",
            "## Provenance",
            "",
            f"- Source case: `{provenance['native_case_path']}`",
            f"- Harvest package: `{provenance['harvest_package']}`",
            f"- Harvest job ID: `{provenance['harvest_job_id']}`",
            f"- Station CSV: `{provenance['harvest_station_csv']}`",
            f"- Source ID: `{provenance['source_id']}`",
            f"- Time: `{provenance['time_s']}` s",
            f"- Window: `{provenance['time_window_s'] or 'not declared in source CSV'}`",
            f"- Split role: `{provenance['split_role']}`",
            f"- Admission caveat: {provenance['admission_caveat']}",
            "",
            "## Branch Average Pressures",
            "",
            "| CFD span | Physical location | 1D segment(s) | flow stations | avg p [Pa] | avg p_rgh [Pa] | end-start p [Pa] | max reverse proxy |",
            "|---|---|---|---|---:|---:|---:|---:|",
        ]
        for row in rows:
            lines.append(
                "| {span} | {loc} | `{segments}` | {start} -> {end} | {p} | {prgh} | {dp} | {rev} |".format(
                    span=row["cfd_span"],
                    loc=row["physical_location_label"],
                    segments=row["one_d_component_segments"],
                    start=row["flow_start_station_label"],
                    end=row["flow_end_station_label"],
                    p=fmt(row["arithmetic_mean_p_Pa"]),
                    prgh=fmt(row["arithmetic_mean_p_rgh_Pa"]),
                    dp=fmt(row["flow_end_minus_start_p_Pa"]),
                    rev=fmt(row["max_reverse_area_fraction_proxy"], 4),
                )
            )
        lines.extend(
            [
                "",
                "## Labeling Guardrails",
                "",
                "- `lower_leg` = heater = 1D `heated_incline`; loop-flow order `s04 -> s00`.",
                "- `right_leg` = downcomer = 1D `right_vertical`; loop-flow order `s00 -> s04`.",
                "- `upper_leg` = cooled top leg = Fluid top/HX composite including `cooled_incline_hx_active`.",
                "- These rows are diagnostic harvested pressure averages, not admitted `f_D` or component-`K` coefficients.",
            ]
        )
        (per_case / f"{case_key}.md").write_text("\n".join(lines) + "\n")


def write_summary_markdown(branch_rows: list[dict[str, Any]], case_provenance: list[dict[str, Any]], summary: dict[str, Any]) -> None:
    lines = [
        "# Postprocessed CFD Streamwise Pressure / 1D Maps",
        "",
        "This package generalizes the Salt2 pressure/1D map across all currently available harvested station-pressure ladder outputs.",
        "No solver outputs were mutated and no scheduler jobs were submitted.",
        "",
        "## Scope",
        "",
        f"- Cases mapped: `{summary['case_count']}`",
        f"- Station rows: `{summary['station_rows']}`",
        f"- Branch-average rows: `{summary['branch_rows']}`",
        "- Sources: AGENT-445 job `3297860` and AGENT-447 job `3297863`.",
        "",
        "## Provenance By Case",
        "",
        "| case_key | split role | harvest job | time s | source case |",
        "|---|---|---:|---:|---|",
    ]
    for row in case_provenance:
        lines.append(
            f"| `{row['case_key']}` | `{row['split_role']}` | `{row['harvest_job_id']}` | {row['time_s']} | `{row['native_case_path']}` |"
        )
    lines.extend(
        [
            "",
            "## Branch Mean Static Pressure By Case",
            "",
            "| case_key | lower_leg heater | left_lower upcomer | test_section | left_upper upcomer | upper_leg cooler | right_leg downcomer |",
            "|---|---:|---:|---:|---:|---:|---:|",
        ]
    )
    by_case: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in branch_rows:
        by_case[str(row["case_key"])][str(row["cfd_span"])] = row
    for case_key in sorted(by_case):
        lines.append(
            "| `{case}` | {lower} | {ll} | {ts} | {lu} | {upper} | {right} |".format(
                case=case_key,
                lower=fmt(by_case[case_key]["lower_leg"]["arithmetic_mean_p_Pa"]),
                ll=fmt(by_case[case_key]["left_lower_leg"]["arithmetic_mean_p_Pa"]),
                ts=fmt(by_case[case_key]["test_section_span"]["arithmetic_mean_p_Pa"]),
                lu=fmt(by_case[case_key]["left_upper_leg"]["arithmetic_mean_p_Pa"]),
                upper=fmt(by_case[case_key]["upper_leg"]["arithmetic_mean_p_Pa"]),
                right=fmt(by_case[case_key]["right_leg"]["arithmetic_mean_p_Pa"]),
            )
        )
    lines.extend(
        [
            "",
            "## Mapping Guardrails",
            "",
            "- `lower_leg` is the physical heater and maps to Fluid `heated_incline`; use station order `s04 -> s00`.",
            "- `right_leg` is the physical downcomer and maps to Fluid `right_vertical`; use station order `s00 -> s04`.",
            "- `upper_leg` is the cooled top leg and maps to `top_horizontal_inlet;cooled_incline_pre_hx;cooled_incline_hx_active;cooled_incline_post_hx;top_horizontal_exit`.",
            "- `left_lower_leg -> test_section_span -> left_upper_leg` maps to `left_lower_vertical -> test_section -> left_upper_vertical`.",
            "- Use `mean_p_Pa` for the static pressure value and preserve `mean_p_rgh_Pa` as the OpenFOAM gravity-adjusted diagnostic.",
            "- All rows remain diagnostic pressure-map evidence until pressure definition, straight-loss subtraction, recirculation masking, and mesh/GCI gates are satisfied together.",
        ]
    )
    (OUT / "README.md").write_text("\n".join(lines) + "\n")


def build() -> dict[str, Any]:
    OUT.mkdir(parents=True, exist_ok=True)
    source_rows = load_harvest_rows()
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in source_rows:
        grouped[str(row["case_key"])].append(row)

    station_rows: list[dict[str, Any]] = []
    for case_key in sorted(grouped):
        station_rows.extend(build_station_map_for_case(case_key, grouped[case_key]))
    branch_rows = build_branch_averages(station_rows)
    case_provenance = build_case_provenance(source_rows, station_rows)

    station_fields = list(station_rows[0].keys())
    branch_fields = list(branch_rows[0].keys())
    provenance_fields = list(case_provenance[0].keys())
    write_csv(OUT / "all_streamwise_pressure_1d_map.csv", station_rows, station_fields)
    write_csv(OUT / "all_branch_average_pressure_map.csv", branch_rows, branch_fields)
    write_csv(OUT / "case_provenance_manifest.csv", case_provenance, provenance_fields)
    write_csv(
        OUT / "source_manifest.csv",
        [
            {
                "source_type": "station_pressure_ladder",
                "path": rel(source["station_csv"]),
                "harvest_package": source["harvest_package"],
                "harvest_task": source["harvest_task"],
                "harvest_job_id": source["harvest_job_id"],
                "description": source["description"],
            }
            for source in PRESSURE_SOURCES
        ]
        + [
            {
                "source_type": "geometry_label_reference",
                "path": rel(GEOMETRY_REFERENCE),
                "harvest_package": "",
                "harvest_task": "",
                "harvest_job_id": "",
                "description": "Authoritative CFD span labels, physical locations, and flow-order guardrails.",
            },
            {
                "source_type": "fluid_1d_geometry",
                "path": rel(FLUID_SEGMENTS),
                "harvest_package": "",
                "harvest_task": "",
                "harvest_job_id": "",
                "description": "Fluid 1D segment names and lengths used for mapping labels.",
            },
        ],
        ["source_type", "path", "harvest_package", "harvest_task", "harvest_job_id", "description"],
    )

    summary = {
        "task": TASK,
        "created_utc": utc_now(),
        "case_count": len(grouped),
        "case_keys": sorted(grouped),
        "source_station_rows": len(source_rows),
        "station_rows": len(station_rows),
        "branch_rows": len(branch_rows),
        "source_packages": [
            {
                "harvest_package": source["harvest_package"],
                "harvest_task": source["harvest_task"],
                "harvest_job_id": source["harvest_job_id"],
                "station_csv": rel(source["station_csv"]),
                "summary_json": rel(source["summary_json"]),
            }
            for source in PRESSURE_SOURCES
        ],
        "station_output": rel(OUT / "all_streamwise_pressure_1d_map.csv"),
        "branch_average_output": rel(OUT / "all_branch_average_pressure_map.csv"),
        "case_provenance_output": rel(OUT / "case_provenance_manifest.csv"),
        "admission_status": "diagnostic_station_pressure_ladder_not_fit_admitted",
        "mapping_guardrails": {
            "lower_leg": "heater / Fluid heated_incline / station order s04 -> s00",
            "right_leg": "downcomer / Fluid right_vertical / station order s00 -> s04",
            "upper_leg": "cooled top leg / Fluid top-HX composite",
        },
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    write_case_markdowns(branch_rows, case_provenance)
    write_summary_markdown(branch_rows, case_provenance, summary)
    return summary


def main() -> None:
    print(json.dumps(build(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
