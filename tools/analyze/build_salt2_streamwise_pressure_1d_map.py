#!/usr/bin/env python3
"""Build the Salt2 streamwise pressure map against the 1D loop segments."""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any


TASK = "AGENT-456"
DATE = "2026-07-16"
ROOT = Path(__file__).resolve().parents[2]
OUT_REL = Path("work_products/2026-07/2026-07-16/2026-07-16_salt2_streamwise_pressure_1d_map")
OUT = ROOT / OUT_REL
SOURCE_REL = Path(
    "work_products/2026-07/2026-07-15/2026-07-15_pressure_ladder_unlock_sbatch/station_pressure_ladder.csv"
)
SOURCE = ROOT / SOURCE_REL
FLUID_SEGMENTS_REL = Path(
    "../cfd-modeling-tools/tamu_first_order_model/Fluid/outputs_tamu_loop_v2_resumable/geometry/loop_segments.csv"
)
GEOMETRY_REF_REL = Path("reference/geometry_reference.md")


BRANCH_ORDER = [
    "lower_leg",
    "left_lower_leg",
    "test_section_span",
    "left_upper_leg",
    "upper_leg",
    "right_leg",
]

BRANCH_METADATA: dict[str, dict[str, Any]] = {
    "lower_leg": {
        "physical_location_label": "heater / bottom heated incline",
        "loop_region": "heater",
        "one_d_parent_segment": "heated_incline",
        "one_d_component_segments": ["heated_incline"],
        "one_d_role": "heater",
        "flow_station_order": ["lower_leg__s04", "lower_leg__s03", "lower_leg__s02", "lower_leg__s01", "lower_leg__s00"],
        "flow_order_note": "CFD span lower_leg is the heater; actual flow is s04 -> s00.",
        "cfd_span_length_m_reference": 0.357,
        "one_d_component_length_m": 0.9144,
        "length_basis_note": "CFD mesh PCA span length differs from Fluid 1D physical 36 in heated_incline length.",
    },
    "left_lower_leg": {
        "physical_location_label": "lower upcomer below test section",
        "loop_region": "upcomer",
        "one_d_parent_segment": "left_lower_vertical",
        "one_d_component_segments": ["left_lower_vertical"],
        "one_d_role": "upcomer",
        "flow_station_order": [
            "left_lower_leg__s00",
            "left_lower_leg__s01",
            "left_lower_leg__s02",
            "left_lower_leg__s03",
            "left_lower_leg__s04",
        ],
        "flow_order_note": "Upcomer-side ladder is reported in increasing station order along the loop path.",
        "cfd_span_length_m_reference": 0.121,
        "one_d_component_length_m": 0.364236,
        "length_basis_note": "CFD mesh PCA span and Fluid 1D left_lower_vertical lengths use different geometric bases.",
    },
    "test_section_span": {
        "physical_location_label": "test section / middle upcomer",
        "loop_region": "upcomer_test_section",
        "one_d_parent_segment": "test_section",
        "one_d_component_segments": ["test_section"],
        "one_d_role": "test_section",
        "flow_station_order": [
            "test_section_span__s00",
            "test_section_span__s01",
            "test_section_span__s02",
            "test_section_span__s03",
            "test_section_span__s04",
        ],
        "flow_order_note": "Test-section span is the 1D quartz test_section in the upcomer path.",
        "cfd_span_length_m_reference": 0.082,
        "one_d_component_length_m": 0.185928,
        "length_basis_note": "CFD extracted span length differs from Fluid 1D test_section length.",
    },
    "left_upper_leg": {
        "physical_location_label": "upper upcomer above test section",
        "loop_region": "upcomer",
        "one_d_parent_segment": "left_upper_vertical",
        "one_d_component_segments": ["left_upper_vertical"],
        "one_d_role": "upcomer",
        "flow_station_order": [
            "left_upper_leg__s00",
            "left_upper_leg__s01",
            "left_upper_leg__s02",
            "left_upper_leg__s03",
            "left_upper_leg__s04",
        ],
        "flow_order_note": "Upper upcomer ladder is reported in increasing station order along the loop path.",
        "cfd_span_length_m_reference": 0.145,
        "one_d_component_length_m": 0.364236,
        "length_basis_note": "CFD mesh PCA span and Fluid 1D left_upper_vertical lengths use different geometric bases.",
    },
    "upper_leg": {
        "physical_location_label": "cooled leg / top cooled incline",
        "loop_region": "cooler",
        "one_d_parent_segment": "cooled_incline_composite",
        "one_d_component_segments": [
            "top_horizontal_inlet",
            "cooled_incline_pre_hx",
            "cooled_incline_hx_active",
            "cooled_incline_post_hx",
            "top_horizontal_exit",
        ],
        "one_d_role": "cooler_hx_path",
        "flow_station_order": ["upper_leg__s00", "upper_leg__s01", "upper_leg__s02", "upper_leg__s03", "upper_leg__s04"],
        "flow_order_note": "CFD upper_leg is the cooled top path and maps to the Fluid top/HX composite.",
        "cfd_span_length_m_reference": 0.357,
        "one_d_component_length_m": 0.9652,
        "length_basis_note": "Composite Fluid length is top inlet + three 12 in cooled/HX segments + top exit.",
    },
    "right_leg": {
        "physical_location_label": "right downcomer / cold vertical return",
        "loop_region": "downcomer",
        "one_d_parent_segment": "right_vertical",
        "one_d_component_segments": ["right_vertical"],
        "one_d_role": "downcomer",
        "flow_station_order": ["right_leg__s00", "right_leg__s01", "right_leg__s02", "right_leg__s03", "right_leg__s04"],
        "flow_order_note": "CFD span right_leg is the downcomer; actual flow is top-to-bottom s00 -> s04.",
        "cfd_span_length_m_reference": 0.366,
        "one_d_component_length_m": 0.9144,
        "length_basis_note": "CFD mesh PCA span length differs from Fluid 1D physical 36 in right_vertical length.",
    },
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT.resolve()))
    except ValueError:
        return str(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = list(rows[0].keys()) if rows else []
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def f(row: dict[str, str], key: str) -> float:
    return float(row[key])


def station_suffix(label: str) -> str:
    return label.split("__", 1)[1]


def load_salt2_station_rows(path: Path = SOURCE) -> list[dict[str, str]]:
    rows = [row for row in read_csv(path) if row["case_key"] == "salt2_mainline"]
    if len(rows) != 30:
        raise ValueError(f"Expected 30 salt2_mainline station rows, found {len(rows)}")
    labels = {row["station_label"] for row in rows}
    expected = {label for meta in BRANCH_METADATA.values() for label in meta["flow_station_order"]}
    missing = sorted(expected - labels)
    extra = sorted(labels - expected)
    if missing or extra:
        raise ValueError(f"Salt2 station label mismatch, missing={missing}, extra={extra}")
    return rows


def build_station_map(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    by_label = {row["station_label"]: row for row in rows}
    start_p = f(by_label[BRANCH_METADATA["lower_leg"]["flow_station_order"][0]], "mean_p_Pa")
    start_p_rgh = f(by_label[BRANCH_METADATA["lower_leg"]["flow_station_order"][0]], "mean_p_rgh_Pa")

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
            row = {
                "case_id": source["case_id"],
                "case_key": source["case_key"],
                "source_id": source["source_id"],
                "time_s": source["time_s"],
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
                "relative_p_from_loop_start_Pa": mean_p - start_p,
                "relative_p_rgh_from_loop_start_Pa": mean_p_rgh - start_p_rgh,
                "relative_p_from_branch_start_Pa": mean_p - float(branch_start_p),
                "relative_p_rgh_from_branch_start_Pa": mean_p_rgh - float(branch_start_p_rgh),
                "delta_from_previous_loop_p_Pa": "" if previous is None else mean_p - float(previous["mean_p_Pa"]),
                "delta_from_previous_loop_p_rgh_Pa": "" if previous is None else mean_p_rgh - float(previous["mean_p_rgh_Pa"]),
                "admission_status": source["admission_status"],
                "fit_eligible": source["fit_eligible"],
                "blockers": source["blockers"],
                "mapping_status": "label_locked_reference_mapping",
                "plane_file": source["plane_file"],
                "source_path": rel(path_resolve(SOURCE_REL)),
            }
            mapped.append(row)
            loop_index += 1
    return mapped


def path_resolve(path: Path) -> Path:
    return (ROOT / path).resolve() if not path.is_absolute() else path.resolve()


def weighted_average(rows: list[dict[str, Any]], value_key: str, weight_key: str) -> float:
    weights = [float(row[weight_key]) for row in rows]
    return sum(float(row[value_key]) * weight for row, weight in zip(rows, weights)) / sum(weights)


def build_branch_averages(station_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in station_rows:
        grouped[str(row["cfd_span"])].append(row)

    rows: list[dict[str, Any]] = []
    for branch in BRANCH_ORDER:
        branch_rows = sorted(grouped[branch], key=lambda row: int(row["branch_flow_index"]))
        start = branch_rows[0]
        end = branch_rows[-1]
        meta = BRANCH_METADATA[branch]
        p_values = [float(row["mean_p_Pa"]) for row in branch_rows]
        p_rgh_values = [float(row["mean_p_rgh_Pa"]) for row in branch_rows]
        rows.append(
            {
                "case_key": start["case_key"],
                "time_s": start["time_s"],
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
                "admission_status": "diagnostic_station_pressure_ladder_not_fit_admitted",
                "fit_eligible": "no",
                "mapping_status": "label_locked_reference_mapping",
                "source_path": rel(path_resolve(SOURCE_REL)),
            }
        )
    return rows


def format_value(value: Any, digits: int = 3) -> str:
    if isinstance(value, float):
        return f"{value:.{digits}f}"
    return str(value)


def write_markdown(station_rows: list[dict[str, Any]], branch_rows: list[dict[str, Any]]) -> None:
    lines = [
        "# Salt2 Streamwise Pressure / 1D Segment Map",
        "",
        "This package filters the July 15 station pressure ladder to `salt2_mainline` and orders it by physical loop flow.",
        "The station values are diagnostic harvested averages, not fit-admitted `f_D` or component `K` evidence.",
        "",
        "## Branch Averages In Loop Order",
        "",
        "| CFD span | Physical location | 1D segment(s) | flow stations | mean p [Pa] | mean p_rgh [Pa] | end-start p [Pa] | max reverse proxy |",
        "|---|---|---|---|---:|---:|---:|---:|",
    ]
    for row in branch_rows:
        lines.append(
            "| {cfd_span} | {physical_location_label} | `{one_d_component_segments}` | {flow_start_station_label} -> {flow_end_station_label} | {p} | {prgh} | {dp} | {rev} |".format(
                cfd_span=row["cfd_span"],
                physical_location_label=row["physical_location_label"],
                one_d_component_segments=row["one_d_component_segments"],
                flow_start_station_label=row["flow_start_station_label"],
                flow_end_station_label=row["flow_end_station_label"],
                p=format_value(row["arithmetic_mean_p_Pa"]),
                prgh=format_value(row["arithmetic_mean_p_rgh_Pa"]),
                dp=format_value(row["flow_end_minus_start_p_Pa"]),
                rev=format_value(row["max_reverse_area_fraction_proxy"], 4),
            )
        )
    lines.extend(
        [
            "",
            "## Labeling Guardrails",
            "",
            "- `lower_leg` is the physical heater and maps to 1D `heated_incline`; traverse `lower_leg__s04 -> lower_leg__s00`.",
            "- `right_leg` is the physical downcomer and maps to 1D `right_vertical`; traverse `right_leg__s00 -> right_leg__s04`.",
            "- `upper_leg` is the cooled top leg and maps to the Fluid top/HX composite: `top_horizontal_inlet`, `cooled_incline_pre_hx`, `cooled_incline_hx_active`, `cooled_incline_post_hx`, `top_horizontal_exit`.",
            "- `left_lower_leg`, `test_section_span`, and `left_upper_leg` map to the upcomer/test-section path.",
            "",
            "## Station-Level Sequence",
            "",
            "| loop index | station | CFD span | physical location | 1D parent | mean p [Pa] | mean p_rgh [Pa] |",
            "|---:|---|---|---|---|---:|---:|",
        ]
    )
    for row in station_rows:
        lines.append(
            "| {loop_order_index} | {station_label} | {cfd_span} | {physical_location_label} | `{one_d_parent_segment}` | {p} | {prgh} |".format(
                loop_order_index=row["loop_order_index"],
                station_label=row["station_label"],
                cfd_span=row["cfd_span"],
                physical_location_label=row["physical_location_label"],
                one_d_parent_segment=row["one_d_parent_segment"],
                p=format_value(row["mean_p_Pa"]),
                prgh=format_value(row["mean_p_rgh_Pa"]),
            )
        )
    (OUT / "salt2_loop_pressure_sequence.md").write_text("\n".join(lines) + "\n")


def write_readme(summary: dict[str, Any]) -> None:
    lines = [
        "# AGENT-456 Salt2 Streamwise Pressure / 1D Map",
        "",
        "## Purpose",
        "",
        "Identify Salt2 average pressure values through the loop, label each CFD station by physical location, and map the CFD spans to the Fluid 1D model segments.",
        "",
        "## Outputs",
        "",
        "- `salt2_streamwise_pressure_1d_map.csv`: 30 station rows in loop-flow order.",
        "- `salt2_branch_average_pressure_map.csv`: 6 CFD branch averages in loop-flow order.",
        "- `salt2_loop_pressure_sequence.md`: readable branch and station tables.",
        "- `source_manifest.csv`: source and guardrail references.",
        "- `summary.json`: row counts and key labels.",
        "",
        "## Key Mapping",
        "",
        "- `lower_leg` = heater = Fluid `heated_incline`; flow order `s04 -> s00`.",
        "- `right_leg` = downcomer = Fluid `right_vertical`; flow order `s00 -> s04`.",
        "- `upper_leg` = cooled top leg = Fluid top/HX composite.",
        "- Upcomer path = `left_lower_leg -> test_section_span -> left_upper_leg`.",
        "",
        "## Admission",
        "",
        "These are harvested station averages. They are diagnostic pressure-map values and remain `fit_eligible=no` for friction/minor-loss fitting.",
        "",
        "## Summary",
        "",
        f"- Station rows: `{summary['station_rows']}`",
        f"- Branch average rows: `{summary['branch_rows']}`",
        f"- Case key: `{summary['case_key']}`",
        f"- Time: `{summary['time_s']}` s",
    ]
    (OUT / "README.md").write_text("\n".join(lines) + "\n")


def build() -> dict[str, Any]:
    OUT.mkdir(parents=True, exist_ok=True)
    source_rows = load_salt2_station_rows()
    station_rows = build_station_map(source_rows)
    branch_rows = build_branch_averages(station_rows)

    station_fields = [
        "case_id",
        "case_key",
        "source_id",
        "time_s",
        "loop_order_index",
        "branch_flow_index",
        "station_label",
        "station_suffix",
        "source_station_index",
        "cfd_span",
        "physical_location_label",
        "loop_region",
        "one_d_parent_segment",
        "one_d_component_segments",
        "one_d_role",
        "flow_order_note",
        "cfd_span_length_m_reference",
        "one_d_component_length_m",
        "length_basis_note",
        "face_count",
        "mean_p_Pa",
        "mean_p_rgh_Pa",
        "mean_un_m_s",
        "mean_rho_kg_m3",
        "reverse_area_fraction_proxy",
        "relative_p_from_loop_start_Pa",
        "relative_p_rgh_from_loop_start_Pa",
        "relative_p_from_branch_start_Pa",
        "relative_p_rgh_from_branch_start_Pa",
        "delta_from_previous_loop_p_Pa",
        "delta_from_previous_loop_p_rgh_Pa",
        "admission_status",
        "fit_eligible",
        "blockers",
        "mapping_status",
        "plane_file",
        "source_path",
    ]
    branch_fields = list(branch_rows[0].keys())
    write_csv(OUT / "salt2_streamwise_pressure_1d_map.csv", station_rows, station_fields)
    write_csv(OUT / "salt2_branch_average_pressure_map.csv", branch_rows, branch_fields)
    write_csv(
        OUT / "source_manifest.csv",
        [
            {
                "source_type": "pressure_ladder_station_values",
                "path": rel(path_resolve(SOURCE_REL)),
                "use": "Salt2 mean p and p_rgh station values at time 7915 s",
            },
            {
                "source_type": "1d_fluid_segment_geometry",
                "path": rel(path_resolve(FLUID_SEGMENTS_REL)),
                "use": "Authoritative Fluid 1D segment names and lengths",
            },
            {
                "source_type": "geometry_label_reference",
                "path": rel(path_resolve(GEOMETRY_REF_REL)),
                "use": "CFD span labels, physical locations, and lower/right leg flow-order guardrails",
            },
        ],
        ["source_type", "path", "use"],
    )

    summary = {
        "task": TASK,
        "created_utc": utc_now(),
        "case_key": "salt2_mainline",
        "time_s": source_rows[0]["time_s"],
        "station_rows": len(station_rows),
        "branch_rows": len(branch_rows),
        "source": rel(path_resolve(SOURCE_REL)),
        "station_output": rel(OUT / "salt2_streamwise_pressure_1d_map.csv"),
        "branch_average_output": rel(OUT / "salt2_branch_average_pressure_map.csv"),
        "lower_leg_mapping": {
            "cfd_span": "lower_leg",
            "physical_location": "heater",
            "flow_order": "lower_leg__s04 -> lower_leg__s00",
            "one_d_segment": "heated_incline",
        },
        "right_leg_mapping": {
            "cfd_span": "right_leg",
            "physical_location": "downcomer",
            "flow_order": "right_leg__s00 -> right_leg__s04",
            "one_d_segment": "right_vertical",
        },
        "upper_leg_mapping": {
            "cfd_span": "upper_leg",
            "physical_location": "cooled leg",
            "one_d_segments": BRANCH_METADATA["upper_leg"]["one_d_component_segments"],
        },
        "admission_status": "diagnostic_station_pressure_ladder_not_fit_admitted",
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    write_markdown(station_rows, branch_rows)
    write_readme(summary)
    return summary


def main() -> None:
    summary = build()
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
