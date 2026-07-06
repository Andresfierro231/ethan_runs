#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[2]
TMP_MPL_ROOT = ROOT / "tmp" / "mplconfig"
TMP_MPL_ROOT.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(TMP_MPL_ROOT))

import matplotlib.pyplot as plt
import numpy as np

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.common import csv_dump, ensure_dir, iso_timestamp, json_dump, safe_float, save_matplotlib_figure  # noqa: E402

try:
    plt.style.use("seaborn-v0_8-whitegrid")
except OSError:
    plt.style.use("ggplot")


DEFAULT_OUTPUT_DIR = ROOT / "reports" / "2026-06-18_ethan_salt_analysis_checkpoint_suite"
DEFAULT_SMOKE_OUTPUT_DIR = ROOT / "tmp" / "2026-06-18_ethan_salt_analysis_checkpoint_suite_smoke"
SALT_PACKAGE_DIR = ROOT / "reports" / "2026-06-18_ethan_salt_closure_correlation_package"
PRESSURE_PACKAGE_DIR = ROOT / "reports" / "2026-06-17_ethan_pressure_htc_boundarylayer_package"

PHASES = (
    "phase1_hydraulic_hardening",
    "phase2_heatloss_enthalpy_closure",
    "phase3_branch_trust_gate",
    "phase4_boundary_layer_context",
    "phase5_fit_ready_handoff",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build a Salt-first checkpoint suite from the existing June 17/18 "
            "Salt closure artifacts without reopening the shared extraction path."
        )
    )
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument(
        "--source-id",
        action="append",
        dest="source_ids",
        help="Optional bounded rebuild of one or more Salt source IDs.",
    )
    return parser.parse_args()


def load_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def finite_float(value: Any, default: float = math.nan) -> float:
    parsed = safe_float(value)
    if parsed is None or not math.isfinite(parsed):
        return default
    return float(parsed)


def is_finite(value: Any) -> bool:
    parsed = safe_float(value)
    return parsed is not None and math.isfinite(parsed)


def safe_mean(values: Iterable[float]) -> float:
    payload = [value for value in values if math.isfinite(value)]
    if not payload:
        return math.nan
    return float(sum(payload) / len(payload))


def safe_abs_max(values: Iterable[float]) -> float:
    payload = [abs(value) for value in values if math.isfinite(value)]
    if not payload:
        return math.nan
    return float(max(payload))


def filter_source_rows(rows: list[dict[str, str]], source_ids: set[str] | None = None) -> list[dict[str, str]]:
    if not source_ids:
        return rows
    return [row for row in rows if row.get("source_id") in source_ids]


def save_phase_figure(fig: plt.Figure, phase_dir: Path, stem: str) -> dict[str, str]:
    return save_matplotlib_figure(fig, phase_dir, stem, dpi=220)


def case_order(rows: list[dict[str, str]]) -> dict[str, int]:
    source_ids = []
    for row in rows:
        source_id = row["source_id"]
        if source_id not in source_ids:
            source_ids.append(source_id)
    return {source_id: index for index, source_id in enumerate(source_ids)}


def heatmap_matrix(
    rows: list[dict[str, Any]],
    row_key: str,
    col_key: str,
    value_key: str,
) -> tuple[list[str], list[str], np.ndarray]:
    row_labels = sorted({str(row[row_key]) for row in rows})
    col_labels = sorted({str(row[col_key]) for row in rows})
    matrix = np.full((len(row_labels), len(col_labels)), np.nan, dtype=float)
    for row in rows:
        ri = row_labels.index(str(row[row_key]))
        ci = col_labels.index(str(row[col_key]))
        matrix[ri, ci] = finite_float(row.get(value_key))
    return row_labels, col_labels, matrix


def read_inputs(source_ids: set[str]) -> dict[str, list[dict[str, str]]]:
    payload = {
        "salt_hydraulic_case_summary": load_csv_rows(SALT_PACKAGE_DIR / "salt_hydraulic_case_summary.csv"),
        "salt_hydraulic_section_closure": load_csv_rows(SALT_PACKAGE_DIR / "salt_hydraulic_section_closure.csv"),
        "salt_feature_keff": load_csv_rows(SALT_PACKAGE_DIR / "salt_feature_keff.csv"),
        "salt_heat_loss_partition_case": load_csv_rows(SALT_PACKAGE_DIR / "salt_heat_loss_partition_case.csv"),
        "salt_leg_enthalpy_summary": load_csv_rows(SALT_PACKAGE_DIR / "salt_leg_enthalpy_summary.csv"),
        "salt_branch_usability": load_csv_rows(SALT_PACKAGE_DIR / "salt_branch_usability.csv"),
        "salt_boundary_layer_summary": load_csv_rows(SALT_PACKAGE_DIR / "salt_boundary_layer_summary.csv"),
        "salt_representative_boundary_profiles": load_csv_rows(SALT_PACKAGE_DIR / "salt_representative_boundary_profiles.csv"),
        "salt_case_correlation_inputs": load_csv_rows(SALT_PACKAGE_DIR / "salt_case_correlation_inputs.csv"),
        "salt_straight_section_correlation_inputs": load_csv_rows(SALT_PACKAGE_DIR / "salt_straight_section_correlation_inputs.csv"),
        "salt_feature_correlation_inputs": load_csv_rows(SALT_PACKAGE_DIR / "salt_feature_correlation_inputs.csv"),
        "salt_fit_exclusion_log": load_csv_rows(SALT_PACKAGE_DIR / "salt_fit_exclusion_log.csv"),
        "bulk_vs_centerline_temperature_correction": load_csv_rows(PRESSURE_PACKAGE_DIR / "bulk_vs_centerline_temperature_correction.csv"),
    }
    for key in list(payload):
        payload[key] = filter_source_rows(payload[key], source_ids or None)
    payload["bulk_vs_centerline_temperature_correction"] = [
        row
        for row in payload["bulk_vs_centerline_temperature_correction"]
        if row.get("source_id") in {item["source_id"] for item in payload["salt_case_correlation_inputs"]}
    ]
    return payload


def phase1_hydraulic_hardening(
    output_root: Path,
    inputs: dict[str, list[dict[str, str]]],
) -> dict[str, Any]:
    phase_dir = ensure_dir(output_root / "phase1_hydraulic_hardening")
    sections = inputs["salt_straight_section_correlation_inputs"]
    features = inputs["salt_feature_correlation_inputs"]
    cases = inputs["salt_hydraulic_case_summary"]

    candidate_subset = [row for row in sections if row["fit_status"] == "candidate"]
    buoyancy_subset = [row for row in sections if row["net_section_role"] == "buoyancy_aided_or_net_gain"]
    screening_subset = [row for row in sections if row["fit_status"] != "candidate"]

    span_summary: list[dict[str, Any]] = []
    grouped_by_span: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in sections:
        grouped_by_span[row["span_name"]].append(row)
    for span_name, payload in sorted(grouped_by_span.items()):
        span_summary.append(
            {
                "span_name": span_name,
                "row_count": len(payload),
                "candidate_count": sum(1 for row in payload if row["fit_status"] == "candidate"),
                "screening_count": sum(1 for row in payload if row["fit_status"] == "screening_only"),
                "blocked_count": sum(1 for row in payload if row["fit_status"] == "do_not_fit"),
                "mean_apparent_darcy_f_local": safe_mean(finite_float(row.get("apparent_darcy_f_local")) for row in payload),
                "mean_direct_to_shear_darcy_ratio": safe_mean(
                    finite_float(row.get("direct_to_shear_darcy_ratio")) for row in payload
                ),
                "mean_pressure_loss_to_driving_head_ratio": safe_mean(
                    finite_float(row.get("pressure_loss_to_driving_head_ratio")) for row in payload
                ),
            }
        )

    feature_summary: list[dict[str, Any]] = []
    grouped_by_feature_kind: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in features:
        grouped_by_feature_kind[row["feature_kind"]].append(row)
    for feature_kind, payload in sorted(grouped_by_feature_kind.items()):
        feature_summary.append(
            {
                "feature_kind": feature_kind,
                "row_count": len(payload),
                "candidate_count": sum(1 for row in payload if row["fit_status"] == "candidate"),
                "screening_count": sum(1 for row in payload if row["fit_status"] == "screening_only"),
                "mean_keff_reference": safe_mean(finite_float(row.get("mean_keff_reference")) for row in payload),
                "max_keff_reference": safe_abs_max(finite_float(row.get("mean_keff_reference")) for row in payload),
            }
        )

    buoyancy_table = [
        {
            "source_id": row["source_id"],
            "case_label": row["case_label"],
            "span_name": row["span_name"],
            "pressure_loss_hydro_pa": finite_float(row.get("pressure_loss_hydro_pa")),
            "apparent_darcy_f_local": finite_float(row.get("apparent_darcy_f_local")),
            "direct_to_shear_darcy_ratio": finite_float(row.get("direct_to_shear_darcy_ratio")),
            "fit_reason": row["fit_reason"],
        }
        for row in buoyancy_subset
    ]

    csv_dump(phase_dir / "hydraulic_case_checkpoint.csv", list(cases[0].keys()), cases)
    csv_dump(phase_dir / "hydraulic_screening_matrix.csv", list(sections[0].keys()), sections)
    csv_dump(phase_dir / "hydraulic_fit_candidates.csv", list(candidate_subset[0].keys()) if candidate_subset else list(sections[0].keys()), candidate_subset)
    csv_dump(phase_dir / "hydraulic_screening_remainder.csv", list(screening_subset[0].keys()) if screening_subset else list(sections[0].keys()), screening_subset)
    csv_dump(phase_dir / "hydraulic_span_fit_summary.csv", list(span_summary[0].keys()), span_summary)
    csv_dump(phase_dir / "feature_keff_status.csv", list(features[0].keys()), features)
    csv_dump(phase_dir / "feature_keff_summary_by_kind.csv", list(feature_summary[0].keys()), feature_summary)
    csv_dump(phase_dir / "buoyancy_aided_sections.csv", list(buoyancy_table[0].keys()), buoyancy_table)

    status_map = {"candidate": 2.0, "screening_only": 1.0, "do_not_fit": 0.0}
    status_rows = [
        {"source_id": row["source_id"], "span_name": row["span_name"], "status_value": status_map[row["fit_status"]]}
        for row in sections
    ]
    cases_h, spans_h, matrix_h = heatmap_matrix(status_rows, "source_id", "span_name", "status_value")
    fig1, ax1 = plt.subplots(figsize=(12, 6), constrained_layout=True)
    im = ax1.imshow(matrix_h, aspect="auto", cmap=plt.get_cmap("RdYlGn", 3), vmin=0.0, vmax=2.0)
    ax1.set_title("Phase 1 Hydraulic Fit Status")
    ax1.set_xticks(range(len(spans_h)))
    ax1.set_xticklabels(spans_h, rotation=45, ha="right")
    ax1.set_yticks(range(len(cases_h)))
    ax1.set_yticklabels(cases_h)
    cb = fig1.colorbar(im, ax=ax1, ticks=[0.0, 1.0, 2.0])
    cb.ax.set_yticklabels(["do_not_fit", "screening_only", "candidate"])
    fig_paths1 = save_phase_figure(fig1, phase_dir, "hydraulic_fit_status_heatmap")

    ratio_rows = [
        {"source_id": row["source_id"], "span_name": row["span_name"], "ratio": finite_float(row.get("direct_to_shear_darcy_ratio"))}
        for row in sections
    ]
    cases_r, spans_r, matrix_r = heatmap_matrix(ratio_rows, "source_id", "span_name", "ratio")
    fig2, ax2 = plt.subplots(figsize=(12, 6), constrained_layout=True)
    im2 = ax2.imshow(np.log10(matrix_r), aspect="auto", cmap="coolwarm")
    ax2.set_title("Phase 1 Direct/Shear Darcy Ratio (log10)")
    ax2.set_xticks(range(len(spans_r)))
    ax2.set_xticklabels(spans_r, rotation=45, ha="right")
    ax2.set_yticks(range(len(cases_r)))
    ax2.set_yticklabels(cases_r)
    fig2.colorbar(im2, ax=ax2, label="log10(direct/shear)")
    fig_paths2 = save_phase_figure(fig2, phase_dir, "hydraulic_direct_to_shear_ratio")

    kinds = [row["feature_kind"] for row in feature_summary]
    candidate_counts = [int(row["candidate_count"]) for row in feature_summary]
    screening_counts = [int(row["screening_count"]) for row in feature_summary]
    fig3, ax3 = plt.subplots(figsize=(10, 5), constrained_layout=True)
    x = np.arange(len(kinds))
    ax3.bar(x - 0.18, candidate_counts, 0.36, label="candidate")
    ax3.bar(x + 0.18, screening_counts, 0.36, label="screening_only")
    ax3.set_title("Phase 1 Feature K_eff Status by Feature Kind")
    ax3.set_xticks(x)
    ax3.set_xticklabels(kinds, rotation=30, ha="right")
    ax3.set_ylabel("row count")
    ax3.legend()
    fig_paths3 = save_phase_figure(fig3, phase_dir, "feature_keff_status_by_kind")

    summary = {
        "generated_at": iso_timestamp(),
        "case_count": len(cases),
        "hydraulic_row_count": len(sections),
        "candidate_section_count": len(candidate_subset),
        "screening_section_count": len(screening_subset),
        "feature_row_count": len(features),
        "candidate_feature_count": sum(1 for row in features if row["fit_status"] == "candidate"),
        "buoyancy_aided_section_count": len(buoyancy_subset),
        "figure_paths": {
            "fit_status_heatmap": fig_paths1,
            "direct_to_shear_ratio": fig_paths2,
            "feature_keff_status": fig_paths3,
        },
        "main_findings": [
            "Every Salt case still contains two buoyancy-aided or net-gain straight sections under the signed hydro-corrected closure.",
            "Only lower_leg and test_section_span contribute most of the current straight-section fit candidates.",
            "Many upper_leg rows remain screening-only because direct and shear friction proxies disagree materially in magnitude.",
        ],
    }
    json_dump(phase_dir / "summary.json", summary)
    readme = f"""# Phase 1 Hydraulic Hardening

Generated: `2026-06-18`

This checkpoint hardens the Salt hydraulic interpretation using the June 18
Salt closure package outputs. It does not recompute extraction. It instead
repackages the current straight-section and feature results into a more explicit
fit gate and blocker summary.

## Main findings

- Straight-section candidate rows: `{summary['candidate_section_count']}` of `{summary['hydraulic_row_count']}`
- Buoyancy-aided/net-gain straight sections: `{summary['buoyancy_aided_section_count']}`
- Candidate feature rows: `{summary['candidate_feature_count']}` of `{summary['feature_row_count']}`

## Key outputs

- `hydraulic_case_checkpoint.csv`
- `hydraulic_screening_matrix.csv`
- `hydraulic_fit_candidates.csv`
- `hydraulic_span_fit_summary.csv`
- `feature_keff_status.csv`
- `feature_keff_summary_by_kind.csv`
- `buoyancy_aided_sections.csv`

## Interpretation checkpoint

This phase confirms that the current Salt hydraulic story is usable for
screening and partial fitting, but not yet fully closure-clean. In particular,
negative or net-gain section losses are preserved as physical outcomes, and the
feature `K_eff` family still inherits the residual `p_rgh` feature path from the
June 17 additive pressure package.
"""
    (phase_dir / "README.md").write_text(readme, encoding="utf-8")
    return summary


def phase2_heatloss_enthalpy_closure(
    output_root: Path,
    inputs: dict[str, list[dict[str, str]]],
) -> dict[str, Any]:
    phase_dir = ensure_dir(output_root / "phase2_heatloss_enthalpy_closure")
    heat_cases = inputs["salt_heat_loss_partition_case"]
    enthalpy = inputs["salt_leg_enthalpy_summary"]

    case_enthalpy_summary: list[dict[str, Any]] = []
    grouped_case: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in enthalpy:
        grouped_case[row["source_id"]].append(row)
    for source_id, payload in sorted(grouped_case.items(), key=lambda item: payload[0]["case_order"] if (payload := item[1]) else 999):
        case_enthalpy_summary.append(
            {
                "source_id": source_id,
                "case_label": payload[0]["case_label"],
                "leg_count": len(payload),
                "candidate_leg_count": sum(1 for row in payload if row["fit_status"] == "candidate"),
                "screening_leg_count": sum(1 for row in payload if row["fit_status"] == "screening_only"),
                "blocked_leg_count": sum(1 for row in payload if row["fit_status"] == "do_not_fit"),
                "mean_enthalpy_residual_fraction": safe_mean(
                    finite_float(row.get("enthalpy_residual_fraction_of_wall_heat")) for row in payload
                ),
                "max_enthalpy_residual_fraction": safe_abs_max(
                    finite_float(row.get("enthalpy_residual_fraction_of_wall_heat")) for row in payload
                ),
            }
        )

    residual_ranking = sorted(
        [
            {
                **row,
                "abs_enthalpy_residual_fraction": abs(finite_float(row.get("enthalpy_residual_fraction_of_wall_heat"))),
            }
            for row in enthalpy
        ],
        key=lambda row: finite_float(row.get("abs_enthalpy_residual_fraction")),
        reverse=True,
    )

    case_heat_fractions: list[dict[str, Any]] = []
    for row in heat_cases:
        heater_power = finite_float(row.get("heater_power_w"))
        resolved_fraction = sum(
            abs(finite_float(row.get(key)))
            for key in [
                "cooling_total_fraction_of_heater",
                "ambient_proxy_fraction_of_heater",
                "junction_fraction_of_heater",
            ]
            if is_finite(row.get(key))
        )
        case_heat_fractions.append(
            {
                **row,
                "resolved_partition_fraction": resolved_fraction,
                "unresolved_partition_fraction_proxy": max(
                    0.0,
                    1.0 - abs(finite_float(row.get("cooling_total_fraction_of_heater"))) - abs(finite_float(row.get("ambient_proxy_fraction_of_heater"))),
                )
                if math.isfinite(heater_power) and abs(heater_power) > 0.0
                else math.nan,
            }
        )

    csv_dump(phase_dir / "heat_partition_case_fractions.csv", list(case_heat_fractions[0].keys()), case_heat_fractions)
    csv_dump(phase_dir / "leg_enthalpy_closure_screen.csv", list(enthalpy[0].keys()), enthalpy)
    csv_dump(phase_dir / "enthalpy_case_checkpoint.csv", list(case_enthalpy_summary[0].keys()), case_enthalpy_summary)
    csv_dump(phase_dir / "enthalpy_residual_ranking.csv", list(residual_ranking[0].keys()), residual_ranking)

    labels = [row["case_label"] for row in case_heat_fractions]
    x = np.arange(len(case_heat_fractions))
    fig1, ax1 = plt.subplots(figsize=(12, 6), constrained_layout=True)
    cooling = [finite_float(row.get("cooling_total_fraction_of_heater")) for row in case_heat_fractions]
    ambient = [finite_float(row.get("ambient_proxy_fraction_of_heater")) for row in case_heat_fractions]
    junction = [abs(finite_float(row.get("junction_fraction_of_heater"))) for row in case_heat_fractions]
    residual = [abs(finite_float(row.get("net_total_mean_w"))) / finite_float(row.get("heater_power_w")) if is_finite(row.get("net_total_mean_w")) and abs(finite_float(row.get("heater_power_w"))) > 0.0 else math.nan for row in case_heat_fractions]
    ax1.bar(x, cooling, label="cooling / heater")
    ax1.bar(x, ambient, bottom=cooling, label="ambient / heater")
    ax1.bar(x, junction, bottom=np.array(cooling) + np.array(ambient), label="|junction| / heater")
    ax1.bar(x, residual, bottom=np.array(cooling) + np.array(ambient) + np.array(junction), label="|net residual| / heater")
    ax1.set_title("Phase 2 Salt Case Heat Partition Stack")
    ax1.set_xticks(x)
    ax1.set_xticklabels(labels, rotation=45, ha="right")
    ax1.set_ylabel("fraction of heater power")
    ax1.legend(fontsize=8)
    fig_paths1 = save_phase_figure(fig1, phase_dir, "heat_partition_stack")

    cases_h = sorted({row["source_id"] for row in enthalpy})
    spans_h = sorted({row["span_name"] for row in enthalpy})
    matrix = np.full((len(cases_h), len(spans_h)), np.nan, dtype=float)
    for row in enthalpy:
        ci = cases_h.index(row["source_id"])
        si = spans_h.index(row["span_name"])
        matrix[ci, si] = finite_float(row.get("enthalpy_residual_fraction_of_wall_heat"))
    fig2, ax2 = plt.subplots(figsize=(12, 6), constrained_layout=True)
    im2 = ax2.imshow(matrix, aspect="auto", cmap="magma")
    ax2.set_title("Phase 2 Enthalpy Residual Fraction by Case and Span")
    ax2.set_xticks(range(len(spans_h)))
    ax2.set_xticklabels(spans_h, rotation=45, ha="right")
    ax2.set_yticks(range(len(cases_h)))
    ax2.set_yticklabels(cases_h)
    fig2.colorbar(im2, ax=ax2, label="|DeltaH - Qwall| / |Qwall|")
    fig_paths2 = save_phase_figure(fig2, phase_dir, "enthalpy_residual_heatmap")

    fig3, ax3 = plt.subplots(figsize=(12, 5), constrained_layout=True)
    top_rows = residual_ranking[:18]
    labels3 = [f"{row['case_label']}:{row['span_name']}" for row in top_rows]
    values3 = [finite_float(row.get("abs_enthalpy_residual_fraction")) for row in top_rows]
    ax3.bar(range(len(top_rows)), values3)
    ax3.set_title("Phase 2 Highest Enthalpy Residual Fractions")
    ax3.set_xticks(range(len(top_rows)))
    ax3.set_xticklabels(labels3, rotation=55, ha="right", fontsize=8)
    ax3.set_ylabel("abs residual fraction")
    fig_paths3 = save_phase_figure(fig3, phase_dir, "enthalpy_residual_ranking")

    summary = {
        "generated_at": iso_timestamp(),
        "case_count": len(case_heat_fractions),
        "leg_row_count": len(enthalpy),
        "candidate_leg_count": sum(1 for row in enthalpy if row["fit_status"] == "candidate"),
        "screening_leg_count": sum(1 for row in enthalpy if row["fit_status"] == "screening_only"),
        "blocked_leg_count": sum(1 for row in enthalpy if row["fit_status"] == "do_not_fit"),
        "max_enthalpy_residual_fraction": safe_abs_max(
            finite_float(row.get("enthalpy_residual_fraction_of_wall_heat")) for row in enthalpy
        ),
        "figure_paths": {
            "heat_partition_stack": fig_paths1,
            "enthalpy_residual_heatmap": fig_paths2,
            "enthalpy_residual_ranking": fig_paths3,
        },
        "main_findings": [
            "Current Salt heat-loss separation is still case-level and audit-style rather than a resolved resistance decomposition.",
            "Enthalpy closure is the dominant remaining Salt blocker: almost every span remains screening-only or blocked under the current residual thresholds.",
            "The current package can localize the worst residual spans, but it does not yet explain the residual into physically separated internal, wall, and external channels.",
        ],
    }
    json_dump(phase_dir / "summary.json", summary)
    readme = f"""# Phase 2 Heat-Loss / Enthalpy Closure

Generated: `2026-06-18`

This checkpoint focuses on the current Salt heat-loss partition and enthalpy
closure problem.

## Main findings

- Candidate enthalpy rows: `{summary['candidate_leg_count']}` of `{summary['leg_row_count']}`
- Screening enthalpy rows: `{summary['screening_leg_count']}`
- Blocked enthalpy rows: `{summary['blocked_leg_count']}`
- Maximum enthalpy residual fraction: `{summary['max_enthalpy_residual_fraction']:.3f}`

## Key outputs

- `heat_partition_case_fractions.csv`
- `leg_enthalpy_closure_screen.csv`
- `enthalpy_case_checkpoint.csv`
- `enthalpy_residual_ranking.csv`

## Interpretation checkpoint

This phase confirms that Salt thermal closure is not yet dissertation-clean.
The current audit-style heat partition is useful for locating where heater
power likely leaves the loop, but the dominant next step is still a more
resolved decomposition that keeps internal convection, wall/insulation
conduction, and external loss channels separate.
"""
    (phase_dir / "README.md").write_text(readme, encoding="utf-8")
    return summary


def phase3_branch_trust_gate(
    output_root: Path,
    inputs: dict[str, list[dict[str, str]]],
) -> dict[str, Any]:
    phase_dir = ensure_dir(output_root / "phase3_branch_trust_gate")
    branches = inputs["salt_branch_usability"]

    candidates = [row for row in branches if row["fit_status"] == "candidate"]
    remainder = [row for row in branches if row["fit_status"] != "candidate"]

    reason_summary: list[dict[str, Any]] = []
    counter = Counter((row["branch_name"], row["fit_status"], row["fit_reason"]) for row in branches)
    for (branch_name, fit_status, fit_reason), count in sorted(counter.items()):
        reason_summary.append(
            {
                "branch_name": branch_name,
                "fit_status": fit_status,
                "fit_reason": fit_reason,
                "row_count": count,
            }
        )

    branch_summary: list[dict[str, Any]] = []
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in branches:
        grouped[row["branch_name"]].append(row)
    for branch_name, payload in sorted(grouped.items()):
        branch_summary.append(
            {
                "branch_name": branch_name,
                "row_count": len(payload),
                "candidate_count": sum(1 for row in payload if row["fit_status"] == "candidate"),
                "screening_count": sum(1 for row in payload if row["fit_status"] == "screening_only"),
                "blocked_count": sum(1 for row in payload if row["fit_status"] == "do_not_fit"),
                "mean_effective_htc_w_m2_k": safe_mean(
                    finite_float(row.get("mean_effective_htc_w_m2_k")) for row in payload
                ),
                "mean_min_abs_delta_t_k": safe_mean(
                    finite_float(row.get("min_abs_bulk_minus_wall_temp_k")) for row in payload
                ),
            }
        )

    csv_dump(phase_dir / "branch_promotion_gate.csv", list(branches[0].keys()), branches)
    csv_dump(phase_dir / "branch_candidate_subset.csv", list(candidates[0].keys()) if candidates else list(branches[0].keys()), candidates)
    csv_dump(phase_dir / "branch_screening_remainder.csv", list(remainder[0].keys()) if remainder else list(branches[0].keys()), remainder)
    csv_dump(phase_dir / "branch_reason_summary.csv", list(reason_summary[0].keys()), reason_summary)
    csv_dump(phase_dir / "branch_status_summary.csv", list(branch_summary[0].keys()), branch_summary)

    status_map = {"do_not_fit": 0.0, "screening_only": 1.0, "candidate": 2.0}
    cases = sorted({row["source_id"] for row in branches})
    branch_names = sorted({row["branch_name"] for row in branches})
    matrix = np.full((len(cases), len(branch_names)), np.nan, dtype=float)
    for row in branches:
        ci = cases.index(row["source_id"])
        bi = branch_names.index(row["branch_name"])
        matrix[ci, bi] = status_map[row["fit_status"]]
    fig1, ax1 = plt.subplots(figsize=(12, 6), constrained_layout=True)
    im1 = ax1.imshow(matrix, aspect="auto", cmap=plt.get_cmap("RdYlGn", 3), vmin=0.0, vmax=2.0)
    ax1.set_title("Phase 3 Branch Promotion Gate")
    ax1.set_xticks(range(len(branch_names)))
    ax1.set_xticklabels(branch_names, rotation=45, ha="right")
    ax1.set_yticks(range(len(cases)))
    ax1.set_yticklabels(cases)
    cb1 = fig1.colorbar(im1, ax=ax1, ticks=[0.0, 1.0, 2.0])
    cb1.ax.set_yticklabels(["do_not_fit", "screening_only", "candidate"])
    fig_paths1 = save_phase_figure(fig1, phase_dir, "branch_promotion_gate")

    branch_labels = [row["branch_name"] for row in branch_summary]
    candidate_counts = [int(row["candidate_count"]) for row in branch_summary]
    blocked_counts = [int(row["blocked_count"]) for row in branch_summary]
    screening_counts = [int(row["screening_count"]) for row in branch_summary]
    fig2, ax2 = plt.subplots(figsize=(12, 5), constrained_layout=True)
    x = np.arange(len(branch_summary))
    ax2.bar(x, candidate_counts, label="candidate")
    ax2.bar(x, screening_counts, bottom=candidate_counts, label="screening_only")
    ax2.bar(x, blocked_counts, bottom=np.array(candidate_counts) + np.array(screening_counts), label="do_not_fit")
    ax2.set_title("Phase 3 Branch Status Counts")
    ax2.set_xticks(x)
    ax2.set_xticklabels(branch_labels, rotation=45, ha="right")
    ax2.set_ylabel("row count")
    ax2.legend()
    fig_paths2 = save_phase_figure(fig2, phase_dir, "branch_status_counts")

    fig3, ax3 = plt.subplots(figsize=(10, 5), constrained_layout=True)
    reasons = [row["fit_reason"] for row in reason_summary]
    counts = [int(row["row_count"]) for row in reason_summary]
    ax3.barh(range(len(reason_summary)), counts)
    ax3.set_yticks(range(len(reason_summary)))
    ax3.set_yticklabels([f"{row['branch_name']} | {row['fit_reason']}" for row in reason_summary], fontsize=8)
    ax3.set_title("Phase 3 Branch Blocker and Gate Reasons")
    ax3.set_xlabel("row count")
    fig_paths3 = save_phase_figure(fig3, phase_dir, "branch_reason_counts")

    summary = {
        "generated_at": iso_timestamp(),
        "branch_row_count": len(branches),
        "candidate_branch_row_count": len(candidates),
        "screening_branch_row_count": sum(1 for row in branches if row["fit_status"] == "screening_only"),
        "blocked_branch_row_count": sum(1 for row in branches if row["fit_status"] == "do_not_fit"),
        "candidate_branch_names": sorted({row["branch_name"] for row in candidates}),
        "figure_paths": {
            "promotion_gate": fig_paths1,
            "status_counts": fig_paths2,
            "reason_counts": fig_paths3,
        },
        "main_findings": [
            "left_lower_leg, left_upper_leg, test_section_span, and upcomer form the stable Salt thermal-fit subset under the current support rules.",
            "right_leg is blocked across the whole Salt family under the current branch trust gate.",
            "lower_leg and upper_leg remain screening or blocked because of marginal thermal support and small local driving-temperature differences.",
        ],
    }
    json_dump(phase_dir / "summary.json", summary)
    readme = f"""# Phase 3 Branch Trust Gate

Generated: `2026-06-18`

This checkpoint turns the Salt branch thermal support logic into a durable
promotion gate for later correlation fitting.

## Main findings

- Candidate branch rows: `{summary['candidate_branch_row_count']}` of `{summary['branch_row_count']}`
- Screening branch rows: `{summary['screening_branch_row_count']}`
- Blocked branch rows: `{summary['blocked_branch_row_count']}`
- Candidate branch names: `{", ".join(summary['candidate_branch_names'])}`

## Key outputs

- `branch_promotion_gate.csv`
- `branch_candidate_subset.csv`
- `branch_screening_remainder.csv`
- `branch_reason_summary.csv`
- `branch_status_summary.csv`

## Interpretation checkpoint

This phase formalizes the Salt thermal subset that can move into the final
fit-ready package. It also preserves blocked and marginal branches explicitly so
they remain documented evidence rather than disappearing from view.
"""
    (phase_dir / "README.md").write_text(readme, encoding="utf-8")
    return summary


def phase4_boundary_layer_context(
    output_root: Path,
    inputs: dict[str, list[dict[str, str]]],
) -> dict[str, Any]:
    phase_dir = ensure_dir(output_root / "phase4_boundary_layer_context")
    boundary = inputs["salt_boundary_layer_summary"]
    representative = inputs["salt_representative_boundary_profiles"]
    bulk_centerline = inputs["bulk_vs_centerline_temperature_correction"]

    bulk_centerline_salt = [row for row in bulk_centerline if "water" not in row["source_id"]]
    grouped_case: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in bulk_centerline_salt:
        grouped_case[row["source_id"]].append(row)
    case_context: list[dict[str, Any]] = []
    for source_id, payload in sorted(grouped_case.items()):
        case_context.append(
            {
                "source_id": source_id,
                "case_label": payload[0]["case_label"],
                "sample_count": len(payload),
                "mean_bulk_minus_centerline_temp_k": safe_mean(
                    finite_float(row.get("bulk_minus_centerline_temp_k")) for row in payload
                ),
                "max_abs_bulk_minus_centerline_temp_k": safe_abs_max(
                    finite_float(row.get("bulk_minus_centerline_temp_k")) for row in payload
                ),
                "mean_centerline_temp_k": safe_mean(finite_float(row.get("centerline_temp_k")) for row in payload),
                "mean_bulk_temp_k": safe_mean(finite_float(row.get("bulk_temp_k")) for row in payload),
            }
        )

    csv_dump(phase_dir / "boundary_layer_span_context.csv", list(boundary[0].keys()), boundary)
    csv_dump(phase_dir / "representative_profile_context.csv", list(representative[0].keys()), representative)
    csv_dump(
        phase_dir / "bulk_centerline_salt_context.csv",
        list(bulk_centerline_salt[0].keys()) if bulk_centerline_salt else ["source_id"],
        bulk_centerline_salt,
    )
    csv_dump(
        phase_dir / "boundary_layer_case_context.csv",
        list(case_context[0].keys()) if case_context else ["source_id"],
        case_context,
    )

    spans = sorted({row["span_name"] for row in boundary})
    grouped_span: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in boundary:
        grouped_span[row["span_name"]].append(row)
    fig1, axes1 = plt.subplots(2, 1, figsize=(12, 8), constrained_layout=True)
    axes1[0].boxplot(
        [[finite_float(row.get("mean_delta99_u_over_dh")) for row in grouped_span[span]] for span in spans],
        labels=spans,
    )
    axes1[0].set_title("Phase 4 Hydraulic Boundary Thickness Proxy")
    axes1[0].set_ylabel("delta99_u / D_h")
    axes1[0].tick_params(axis="x", rotation=45)
    axes1[1].boxplot(
        [[finite_float(row.get("mean_delta99_t_over_delta99_u")) for row in grouped_span[span]] for span in spans],
        labels=spans,
    )
    axes1[1].set_title("Phase 4 Thermal/Hydraulic Thickness Ratio")
    axes1[1].set_ylabel("delta99_t / delta99_u")
    axes1[1].tick_params(axis="x", rotation=45)
    fig_paths1 = save_phase_figure(fig1, phase_dir, "boundary_layer_context_boxplots")

    salt2_profiles = [row for row in representative if row["source_id"] == "val_salt_test_2_coarse_mesh_laminar"]
    fig2, axes2 = plt.subplots(1, 2, figsize=(12, 5), constrained_layout=True)
    span_names = sorted({row["span_name"] for row in salt2_profiles})
    colors = plt.cm.tab10(np.linspace(0.0, 1.0, max(len(span_names), 1)))
    for color, span_name in zip(colors, span_names):
        payload = [row for row in salt2_profiles if row["span_name"] == span_name]
        x = [finite_float(row.get("distance_over_dh")) for row in payload]
        axes2[0].plot(x, [finite_float(row.get("u_over_ucore")) for row in payload], color=color, lw=1.0, label=span_name)
        axes2[1].plot(x, [finite_float(row.get("theta_norm")) for row in payload], color=color, lw=1.0, label=span_name)
    axes2[0].set_title("Phase 4 Salt 2 Representative Velocity Profiles")
    axes2[0].set_xlabel("distance / D_h")
    axes2[0].set_ylabel("u / u_core")
    axes2[1].set_title("Phase 4 Salt 2 Representative Thermal Profiles")
    axes2[1].set_xlabel("distance / D_h")
    axes2[1].set_ylabel("theta_norm")
    axes2[1].legend(fontsize=7)
    fig_paths2 = save_phase_figure(fig2, phase_dir, "salt2_representative_profiles")

    grouped_bc_span: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in bulk_centerline_salt:
        grouped_bc_span[row["span_name"]].append(row)
    bc_spans = sorted(grouped_bc_span)
    fig3, ax3 = plt.subplots(figsize=(12, 5), constrained_layout=True)
    ax3.boxplot(
        [[finite_float(row.get("bulk_minus_centerline_temp_k")) for row in grouped_bc_span[span]] for span in bc_spans],
        labels=bc_spans,
    )
    ax3.set_title("Phase 4 Bulk vs Centerline Temperature Correction")
    ax3.set_ylabel("T_bulk - T_centerline [K]")
    ax3.tick_params(axis="x", rotation=45)
    fig_paths3 = save_phase_figure(fig3, phase_dir, "bulk_centerline_correction")

    summary = {
        "generated_at": iso_timestamp(),
        "boundary_span_row_count": len(boundary),
        "representative_profile_row_count": len(representative),
        "bulk_centerline_row_count": len(bulk_centerline_salt),
        "case_context_count": len(case_context),
        "figure_paths": {
            "boundary_context": fig_paths1,
            "salt2_profiles": fig_paths2,
            "bulk_centerline": fig_paths3,
        },
        "main_findings": [
            "All-case Salt boundary-layer context remains landmark-first and should stay that way in the current interpretation stack.",
            "The currently available representative profile context is dominated by the preserved Salt 2 profile set.",
            "Bulk-vs-centerline temperature correction is already available and should be carried forward as context whenever thermal profile claims are made.",
        ],
    }
    json_dump(phase_dir / "summary.json", summary)
    readme = f"""# Phase 4 Boundary-Layer Context

Generated: `2026-06-18`

This checkpoint collects the currently available Salt boundary-layer evidence
without pretending it is a new extraction or a full circumferential field map.

## Main findings

- Boundary summary rows: `{summary['boundary_span_row_count']}`
- Representative profile rows: `{summary['representative_profile_row_count']}`
- Bulk-vs-centerline rows: `{summary['bulk_centerline_row_count']}`

## Key outputs

- `boundary_layer_span_context.csv`
- `representative_profile_context.csv`
- `bulk_centerline_salt_context.csv`
- `boundary_layer_case_context.csv`

## Interpretation checkpoint

This phase is intentionally conservative. It packages the current landmark and
representative-profile context so later dissertation writing can cite it
correctly, while keeping explicit that richer boundary-layer maps would require
upstream extraction work.
"""
    (phase_dir / "README.md").write_text(readme, encoding="utf-8")
    return summary


def phase5_fit_ready_handoff(
    output_root: Path,
    inputs: dict[str, list[dict[str, str]]],
) -> dict[str, Any]:
    phase_dir = ensure_dir(output_root / "phase5_fit_ready_handoff")
    cases = inputs["salt_case_correlation_inputs"]
    hydraulic = inputs["salt_straight_section_correlation_inputs"]
    features = inputs["salt_feature_correlation_inputs"]
    branches = inputs["salt_branch_usability"]
    exclusions = inputs["salt_fit_exclusion_log"]

    hydraulic_fit = [row for row in hydraulic if row["fit_status"] == "candidate"]
    feature_fit = [row for row in features if row["fit_status"] == "candidate"]
    branch_fit = [row for row in branches if row["fit_status"] == "candidate"]

    case_fit_summary: list[dict[str, Any]] = []
    hydraulic_by_case: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in hydraulic_fit:
        hydraulic_by_case[row["source_id"]].append(row)
    feature_by_case: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in feature_fit:
        feature_by_case[row["source_id"]].append(row)
    branch_by_case: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in branch_fit:
        branch_by_case[row["source_id"]].append(row)
    exclusion_by_case: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in exclusions:
        exclusion_by_case[row["source_id"]].append(row)

    for row in cases:
        source_id = row["source_id"]
        case_fit_summary.append(
            {
                **row,
                "fit_ready_hydraulic_section_count": len(hydraulic_by_case[source_id]),
                "fit_ready_feature_count": len(feature_by_case[source_id]),
                "fit_ready_branch_count": len(branch_by_case[source_id]),
                "excluded_asset_count": len(exclusion_by_case[source_id]),
            }
        )

    exclusion_summary: list[dict[str, Any]] = []
    counter = Counter((row["asset_family"], row["fit_reason"]) for row in exclusions)
    for (asset_family, fit_reason), count in sorted(counter.items()):
        exclusion_summary.append(
            {
                "asset_family": asset_family,
                "fit_reason": fit_reason,
                "row_count": count,
            }
        )

    csv_dump(phase_dir / "fit_ready_case_table.csv", list(case_fit_summary[0].keys()), case_fit_summary)
    csv_dump(phase_dir / "fit_ready_hydraulic_sections.csv", list(hydraulic_fit[0].keys()) if hydraulic_fit else list(hydraulic[0].keys()), hydraulic_fit)
    csv_dump(phase_dir / "fit_ready_features.csv", list(feature_fit[0].keys()) if feature_fit else list(features[0].keys()), feature_fit)
    csv_dump(phase_dir / "fit_ready_thermal_branches.csv", list(branch_fit[0].keys()) if branch_fit else list(branches[0].keys()), branch_fit)
    csv_dump(phase_dir / "fit_ready_exclusion_audit.csv", list(exclusions[0].keys()), exclusions)
    csv_dump(phase_dir / "fit_ready_exclusion_summary.csv", list(exclusion_summary[0].keys()), exclusion_summary)

    labels = [row["display_label"] for row in case_fit_summary]
    x = np.arange(len(case_fit_summary))
    h_counts = [int(row["fit_ready_hydraulic_section_count"]) for row in case_fit_summary]
    f_counts = [int(row["fit_ready_feature_count"]) for row in case_fit_summary]
    b_counts = [int(row["fit_ready_branch_count"]) for row in case_fit_summary]
    fig1, ax1 = plt.subplots(figsize=(12, 6), constrained_layout=True)
    ax1.bar(x, h_counts, label="hydraulic sections")
    ax1.bar(x, f_counts, bottom=h_counts, label="features")
    ax1.bar(x, b_counts, bottom=np.array(h_counts) + np.array(f_counts), label="thermal branches")
    ax1.set_title("Phase 5 Fit-Ready Asset Counts by Salt Case")
    ax1.set_xticks(x)
    ax1.set_xticklabels(labels, rotation=45, ha="right")
    ax1.set_ylabel("fit-ready asset count")
    ax1.legend(fontsize=8)
    fig_paths1 = save_phase_figure(fig1, phase_dir, "fit_ready_asset_counts")

    labels2 = [f"{row['asset_family']} | {row['fit_reason']}" for row in exclusion_summary]
    counts2 = [int(row["row_count"]) for row in exclusion_summary]
    fig2, ax2 = plt.subplots(figsize=(12, 6), constrained_layout=True)
    ax2.barh(range(len(exclusion_summary)), counts2)
    ax2.set_yticks(range(len(exclusion_summary)))
    ax2.set_yticklabels(labels2, fontsize=8)
    ax2.set_title("Phase 5 Exclusion Audit Counts")
    ax2.set_xlabel("row count")
    fig_paths2 = save_phase_figure(fig2, phase_dir, "fit_ready_exclusion_audit")

    summary = {
        "generated_at": iso_timestamp(),
        "case_count": len(case_fit_summary),
        "fit_ready_hydraulic_count": len(hydraulic_fit),
        "fit_ready_feature_count": len(feature_fit),
        "fit_ready_branch_count": len(branch_fit),
        "exclusion_row_count": len(exclusions),
        "figure_paths": {
            "fit_ready_asset_counts": fig_paths1,
            "exclusion_audit": fig_paths2,
        },
        "main_findings": [
            "The final fit-ready subset is much narrower than the full Salt artifact set and remains intentionally so.",
            "Hydraulic, feature, and branch candidates can now be consumed without manual triage because exclusions are explicit.",
            "Enthalpy and boundary-layer context remain documented alongside the fit tables but are not automatically promoted as fit-ready regression families.",
        ],
    }
    json_dump(phase_dir / "summary.json", summary)
    readme = f"""# Phase 5 Fit-Ready Handoff

Generated: `2026-06-18`

This checkpoint assembles the final Salt fit-ready subset from the prior
checkpoint phases.

## Main findings

- Fit-ready hydraulic section rows: `{summary['fit_ready_hydraulic_count']}`
- Fit-ready feature rows: `{summary['fit_ready_feature_count']}`
- Fit-ready thermal branch rows: `{summary['fit_ready_branch_count']}`
- Exclusion audit rows: `{summary['exclusion_row_count']}`

## Key outputs

- `fit_ready_case_table.csv`
- `fit_ready_hydraulic_sections.csv`
- `fit_ready_features.csv`
- `fit_ready_thermal_branches.csv`
- `fit_ready_exclusion_audit.csv`
- `fit_ready_exclusion_summary.csv`

## Interpretation checkpoint

This phase is the Salt handoff subset for later fitting. It is deliberately
narrower than the full June 18 Salt closure package, and it should remain that
way until upstream hydraulic or thermal closure work clears more rows into the
candidate set.
"""
    (phase_dir / "README.md").write_text(readme, encoding="utf-8")
    return summary


def write_root_readme(output_root: Path, phase_summaries: dict[str, dict[str, Any]]) -> None:
    text = f"""# Ethan Salt Analysis Checkpoint Suite

Generated: `2026-06-18`

This suite implements the Salt-first, closure-first roadmap as a sequence of
durable documented checkpoints built from the existing June 17 and June 18
Salt analysis artifacts. It does not reopen the shared June 15/17 extraction
path.

## Checkpoints

- `phase1_hydraulic_hardening/`
  Hydraulic fit gates, feature status, and buoyancy-aided section inventory.
- `phase2_heatloss_enthalpy_closure/`
  Heat-partition and enthalpy-closure checkpoint.
- `phase3_branch_trust_gate/`
  Thermal promotion gate for Salt branches and spans.
- `phase4_boundary_layer_context/`
  Boundary-layer and bulk-vs-centerline context package.
- `phase5_fit_ready_handoff/`
  Final fit-ready Salt subset and exclusion audit.

## High-level counts

- Phase 1 candidate hydraulic rows: `{phase_summaries['phase1_hydraulic_hardening']['candidate_section_count']}`
- Phase 2 candidate enthalpy rows: `{phase_summaries['phase2_heatloss_enthalpy_closure']['candidate_leg_count']}`
- Phase 3 candidate branch rows: `{phase_summaries['phase3_branch_trust_gate']['candidate_branch_row_count']}`
- Phase 5 fit-ready hydraulic rows: `{phase_summaries['phase5_fit_ready_handoff']['fit_ready_hydraulic_count']}`
- Phase 5 fit-ready thermal rows: `{phase_summaries['phase5_fit_ready_handoff']['fit_ready_branch_count']}`

## Interpretation

This suite gives you the requested explanations and checkpoints along the way.
The packages are ordered so each later phase depends on earlier closure or
trust work rather than bypassing it.

The main unresolved blockers remain:

1. feature `K_eff` still inherits the residual `p_rgh` feature path
2. enthalpy closure remains weak for most Salt spans
3. representative boundary-layer evidence is still limited to the currently
   preserved landmark/profile context
"""
    (output_root / "README.md").write_text(text, encoding="utf-8")


def main() -> None:
    args = parse_args()
    source_ids = set(args.source_ids or [])
    output_root = ensure_dir(Path(args.output_dir))
    inputs = read_inputs(source_ids)

    phase_summaries: dict[str, dict[str, Any]] = {}
    phase_summaries["phase1_hydraulic_hardening"] = phase1_hydraulic_hardening(output_root, inputs)
    phase_summaries["phase2_heatloss_enthalpy_closure"] = phase2_heatloss_enthalpy_closure(output_root, inputs)
    phase_summaries["phase3_branch_trust_gate"] = phase3_branch_trust_gate(output_root, inputs)
    phase_summaries["phase4_boundary_layer_context"] = phase4_boundary_layer_context(output_root, inputs)
    phase_summaries["phase5_fit_ready_handoff"] = phase5_fit_ready_handoff(output_root, inputs)

    root_summary = {
        "generated_at": iso_timestamp(),
        "phase_names": list(PHASES),
        "phase_summaries": {
            phase_name: {
                key: value
                for key, value in summary.items()
                if key not in {"figure_paths", "main_findings"}
            }
            for phase_name, summary in phase_summaries.items()
        },
    }
    json_dump(output_root / "summary.json", root_summary)
    write_root_readme(output_root, phase_summaries)


if __name__ == "__main__":
    main()
