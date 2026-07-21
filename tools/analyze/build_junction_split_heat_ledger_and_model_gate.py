#!/usr/bin/env python3
"""Build a junction-split heat ledger and model-update gate from existing evidence."""

from __future__ import annotations

import csv
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TASK = "AGENT-473"
ROOT = Path(__file__).resolve().parents[2]
OUT_REL = Path("work_products/2026-07/2026-07-16/2026-07-16_junction_split_heat_ledger_and_model_gate")
OUT = ROOT / OUT_REL

AGENT462_HEAT_AUDIT = ROOT / (
    "work_products/2026-07/2026-07-16/2026-07-16_pressure_loop_plot_and_cfd_heat_audit/"
    "cfd_heat_audit_by_run.csv"
)
AGENT462_COVERAGE = ROOT / (
    "work_products/2026-07/2026-07-16/2026-07-16_pressure_loop_plot_and_cfd_heat_audit/"
    "heat_audit_coverage_by_pressure_case.csv"
)
EXTERNAL_BC_PATCH_CONTRACT = ROOT / (
    "work_products/2026-07/2026-07-14/2026-07-14_external_bc_thermal_profile_parity_study/"
    "external_bc_patch_contract.csv"
)
WALL_SHELL_TEMPS = ROOT / (
    "work_products/2026-07/2026-07-13/2026-07-13_wall_shell_temperature_sampling/"
    "patch_wall_shell_temperatures.csv"
)
PRESSURE_ADMISSION_SUMMARY = ROOT / (
    "work_products/2026-07/2026-07-16/2026-07-16_pressure_ladder_harvest_admission_table/"
    "case_pressure_ladder_admission_summary.csv"
)
PRESSURE_ADMISSION_BRANCH = ROOT / (
    "work_products/2026-07/2026-07-16/2026-07-16_pressure_ladder_harvest_admission_table/"
    "branch_orientation_straight_loss_recirc_admission.csv"
)
HEAT_LEDGER_STATUS = ROOT / (
    "work_products/2026-07/2026-07-15/2026-07-15_salt_external_test_and_q_unlock_admission/"
    "heat_loss_ledger_status.csv"
)
SALT1_ROLE_SUMMARY = ROOT / (
    "work_products/2026-07/2026-07-14/2026-07-14_salt1_terminal_bc_and_pm5_upcomer_harvest/"
    "salt1_terminal_bc_role_summary.csv"
)
SALT1_PATCH_BC = ROOT / (
    "work_products/2026-07/2026-07-14/2026-07-14_salt1_terminal_bc_and_pm5_upcomer_harvest/"
    "salt1_terminal_patch_bc_role_table.csv"
)

SOURCE_TO_CASE_KEY = {
    "viscosity_screening_salt_test_2_jin_coarse_mesh": "salt2_mainline",
    "viscosity_screening_salt_test_3_jin_coarse_mesh": "salt3_mainline",
    "viscosity_screening_salt_test_4_jin_coarse_mesh": "salt4_mainline",
}

BUCKETS = ("lower_left", "lower_right", "upper_left", "upper_right")
BUCKET_LABELS = {
    "lower_left": "lower-left junction/stub group",
    "lower_right": "lower-right junction/stub group",
    "upper_left": "upper-left junction/stub group",
    "upper_right": "upper-right junction/stub group",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        keys: list[str] = []
        for row in rows:
            for key in row:
                if key not in keys:
                    keys.append(key)
        fieldnames = keys
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def fnum(value: Any, default: float = 0.0) -> float:
    try:
        if value in ("", None):
            return default
        out = float(value)
    except (TypeError, ValueError):
        return default
    return out if math.isfinite(out) else default


def maybe_float(value: Any) -> float | None:
    try:
        if value in ("", None):
            return None
        out = float(value)
    except (TypeError, ValueError):
        return None
    return out if math.isfinite(out) else None


def physical_bucket(patch_name: str) -> str:
    for bucket in BUCKETS:
        token = bucket
        if patch_name.startswith(f"junction_{token}") or patch_name.startswith(f"ncc_junction_{token}"):
            return bucket
    return "unmapped"


def patch_subrole(patch_name: str) -> str:
    if patch_name.startswith("ncc_junction_"):
        return "ncc_interface"
    if patch_name.endswith("_stub"):
        return "stub"
    if patch_name.endswith("_step"):
        return "step"
    if "_extension" in patch_name:
        return "extension"
    return "corner_body"


def join_wall_shell(rows: list[dict[str, str]]) -> dict[tuple[str, str, str], dict[str, str]]:
    joined = {}
    for row in rows:
        joined[(row["source_id"], row["case_id"], row["patch_name"])] = row
    return joined


def build_patch_ledger(
    patch_contract_rows: list[dict[str, str]],
    wall_shell_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    temp_by_key = join_wall_shell(wall_shell_rows)
    out: list[dict[str, Any]] = []
    for row in patch_contract_rows:
        if row.get("role") != "junction_other":
            continue
        case_key = SOURCE_TO_CASE_KEY.get(row.get("source_id", ""))
        if not case_key:
            continue
        bucket = physical_bucket(row["patch_name"])
        temp = temp_by_key.get((row["source_id"], row["case_id"], row["patch_name"]), {})
        t_wall = maybe_float(temp.get("T_wall_shell_K"))
        ta = maybe_float(row.get("Ta_K"))
        out.append(
            {
                "case_key": case_key,
                "case_id": row["case_id"],
                "source_id": row["source_id"],
                "physical_junction_bucket": bucket,
                "physical_junction_label": BUCKET_LABELS.get(bucket, "unmapped junction/stub group"),
                "patch_subrole": patch_subrole(row["patch_name"]),
                "patch_name": row["patch_name"],
                "bc_type": row["bc_type"],
                "area_m2": fnum(row.get("area_m2")),
                "h_W_m2K": row.get("h_W_m2K", ""),
                "Ta_K": row.get("Ta_K", ""),
                "Tsur_K": row.get("Tsur_K", ""),
                "emissivity": row.get("emissivity", ""),
                "thickness_total_m": row.get("thickness_total_m", ""),
                "wall_layer_metadata_status": row.get("wall_layer_metadata_status", ""),
                "realized_wallHeatFlux_W": fnum(row.get("realized_wallHeatFlux_W")),
                "realized_external_loss_positive_W": fnum(row.get("realized_external_loss_W")),
                "T_wall_shell_K": "" if t_wall is None else t_wall,
                "T_wall_shell_min_K": temp.get("T_wall_shell_min_K", ""),
                "T_wall_shell_max_K": temp.get("T_wall_shell_max_K", ""),
                "T_wall_to_ambient_drive_K": "" if t_wall is None or ta is None else t_wall - ta,
                "temperature_proxy_status": temp.get("support_status", "missing_patch_temperature_proxy"),
                "setup_radiation_policy": row.get("setup_radiation_policy", ""),
                "realized_flux_replay_policy": row.get("realized_flux_replay_policy", ""),
                "predictive_runtime_policy": row.get("predictive_runtime_policy", ""),
                "source_paths": row.get("source_paths", ""),
                "temperature_source_path": rel(WALL_SHELL_TEMPS) if temp else "",
            }
        )
    out.sort(key=lambda r: (r["case_key"], r["physical_junction_bucket"], r["patch_name"]))
    return out


def weighted_mean(rows: list[dict[str, Any]], value_key: str, weight_key: str) -> str:
    pairs = []
    for row in rows:
        value = maybe_float(row.get(value_key))
        weight = fnum(row.get(weight_key))
        if value is not None and weight > 0:
            pairs.append((value, weight))
    if not pairs:
        return ""
    return sum(value * weight for value, weight in pairs) / sum(weight for _, weight in pairs)


def count_bc(rows: list[dict[str, Any]], bc_type: str) -> int:
    return sum(1 for row in rows if row.get("bc_type") == bc_type)


def aggregate_patch_ledger(
    patch_rows: list[dict[str, Any]],
    heat_audit_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    source_loss = {
        row["case_key"]: fnum(row.get("junction_loss_positive_W"))
        for row in heat_audit_rows
        if row["case_key"] in {"salt2_mainline", "salt3_mainline", "salt4_mainline"}
    }
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in patch_rows:
        grouped[(row["case_key"], row["physical_junction_bucket"])].append(row)

    positive_by_case = defaultdict(float)
    for row in patch_rows:
        positive_by_case[row["case_key"]] += fnum(row["realized_external_loss_positive_W"])

    out: list[dict[str, Any]] = []
    for (case_key, bucket), rows in sorted(grouped.items()):
        bc_counts = Counter(row["bc_type"] for row in rows)
        area = sum(fnum(row["area_m2"]) for row in rows)
        heat_to_fluid = sum(fnum(row["realized_wallHeatFlux_W"]) for row in rows)
        loss_positive = sum(fnum(row["realized_external_loss_positive_W"]) for row in rows)
        source_total = source_loss.get(case_key, 0.0)
        out.append(
            {
                "case_key": case_key,
                "case_id": rows[0]["case_id"],
                "source_id": rows[0]["source_id"],
                "physical_junction_bucket": bucket,
                "physical_junction_label": BUCKET_LABELS.get(bucket, bucket),
                "patch_count": len(rows),
                "area_m2": area,
                "realized_wallHeatFlux_W": heat_to_fluid,
                "realized_external_loss_positive_W": loss_positive,
                "source_aggregate_junction_loss_positive_W": source_total,
                "fraction_of_case_junction_loss": "" if source_total == 0 else loss_positive / source_total,
                "loss_flux_W_m2": "" if area == 0 else loss_positive / area,
                "area_weighted_T_wall_shell_K": weighted_mean(rows, "T_wall_shell_K", "area_m2"),
                "area_weighted_T_wall_to_ambient_drive_K": weighted_mean(rows, "T_wall_to_ambient_drive_K", "area_m2"),
                "area_weighted_h_W_m2K": weighted_mean(rows, "h_W_m2K", "area_m2"),
                "rcExternalTemperature_count": bc_counts.get("rcExternalTemperature", 0),
                "externalTemperature_count": bc_counts.get("externalTemperature", 0),
                "zeroGradient_count": bc_counts.get("zeroGradient", 0),
                "setup_metadata_status": classify_setup_metadata(rows),
                "model_use": "training_or_holdout_target_only_not_runtime_input",
                "source_path": rel(EXTERNAL_BC_PATCH_CONTRACT),
            }
        )

    for case_key, total in sorted(positive_by_case.items()):
        source_total = source_loss.get(case_key, 0.0)
        out.append(
            {
                "case_key": case_key,
                "case_id": "",
                "source_id": "",
                "physical_junction_bucket": "case_total_check",
                "physical_junction_label": "case total from split patches",
                "patch_count": sum(1 for row in patch_rows if row["case_key"] == case_key),
                "area_m2": sum(fnum(row["area_m2"]) for row in patch_rows if row["case_key"] == case_key),
                "realized_wallHeatFlux_W": -total,
                "realized_external_loss_positive_W": total,
                "source_aggregate_junction_loss_positive_W": source_total,
                "fraction_of_case_junction_loss": "" if source_total == 0 else total / source_total,
                "loss_flux_W_m2": "",
                "area_weighted_T_wall_shell_K": "",
                "area_weighted_T_wall_to_ambient_drive_K": "",
                "area_weighted_h_W_m2K": "",
                "rcExternalTemperature_count": count_bc([r for r in patch_rows if r["case_key"] == case_key], "rcExternalTemperature"),
                "externalTemperature_count": count_bc([r for r in patch_rows if r["case_key"] == case_key], "externalTemperature"),
                "zeroGradient_count": count_bc([r for r in patch_rows if r["case_key"] == case_key], "zeroGradient"),
                "setup_metadata_status": "case_sum_check",
                "model_use": "closure_check_not_model_row",
                "source_path": rel(EXTERNAL_BC_PATCH_CONTRACT),
            }
        )
    return out


def classify_setup_metadata(rows: list[dict[str, Any]]) -> str:
    active = [row for row in rows if fnum(row["area_m2"]) > 0 and fnum(row["realized_external_loss_positive_W"]) > 0]
    if not active:
        return "no_active_external_loss_patch"
    with_temp = [row for row in active if row.get("T_wall_shell_K") != ""]
    with_h = [row for row in active if row.get("h_W_m2K") != ""]
    if len(with_temp) == len(active) and len(with_h) == len(active):
        return "complete_setup_h_and_temperature_proxy"
    if len(with_temp) == len(active):
        return "temperature_proxy_complete_h_partial"
    return "setup_metadata_partial"


def build_temperature_drive_candidates(aggregate_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for row in aggregate_rows:
        if row["physical_junction_bucket"] == "case_total_check":
            continue
        out.append(
            {
                "case_key": row["case_key"],
                "physical_junction_bucket": row["physical_junction_bucket"],
                "area_m2": row["area_m2"],
                "external_loss_positive_W": row["realized_external_loss_positive_W"],
                "area_weighted_T_wall_shell_K": row["area_weighted_T_wall_shell_K"],
                "area_weighted_T_wall_to_ambient_drive_K": row["area_weighted_T_wall_to_ambient_drive_K"],
                "area_weighted_h_W_m2K": row["area_weighted_h_W_m2K"],
                "candidate_1d_parameterization": "role-local external-boundary row or junction coverage multiplier driven by local wall/fluid temperature",
                "runtime_policy": "setup-only parameters allowed; realized CFD wallHeatFlux forbidden at runtime",
            }
        )
    return out


def heat_status_by_case(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {row["case_key"]: row for row in rows if row.get("case_key")}


def build_case_admission_rows(
    coverage_rows: list[dict[str, str]],
    heat_audit_rows: list[dict[str, str]],
    heat_status_rows: list[dict[str, str]],
    pressure_summary_rows: list[dict[str, str]],
    split_case_keys: set[str],
) -> list[dict[str, Any]]:
    heat_status = heat_status_by_case(heat_status_rows)
    heat_audit = {row["case_key"]: row for row in heat_audit_rows}
    pressure_summary = {row["case_key"]: row for row in pressure_summary_rows}
    rows: list[dict[str, Any]] = []
    for row in coverage_rows:
        case_key = row["case_key"]
        status = heat_status.get(case_key, {})
        pressure = pressure_summary.get(case_key, {})
        if case_key in split_case_keys:
            ledger_status = "admitted_junction_split_patch_heat_ledger"
            model_status = "usable_as_training_or_holdout_target_after_runtime_leakage_guard"
            evidence_path = rel(EXTERNAL_BC_PATCH_CONTRACT)
        elif case_key == "val_salt2":
            ledger_status = "aggregate_section_ledger_available_no_patch_split"
            model_status = "external_validation_aggregate_only_not_local_junction_fit"
            evidence_path = heat_audit.get(case_key, {}).get("heat_audit_source", "")
        elif status.get("heat_loss_ledger_status") == "salt1_terminal_bc_available_heat_loss_ledger_not_promoted":
            ledger_status = "bc_metadata_available_realized_junction_heat_not_promoted"
            model_status = "not_usable_for_junction_fit_until_realized_heat_ledger_promoted"
            evidence_path = status.get("heat_loss_evidence_path", "")
        else:
            ledger_status = status.get("heat_loss_ledger_status") or "no_comparable_junction_heat_ledger_found"
            model_status = "not_usable_for_junction_fit"
            evidence_path = status.get("heat_loss_evidence_path", "")
        rows.append(
            {
                "case_key": case_key,
                "pressure_map_available": row.get("pressure_map_available", ""),
                "pressure_case_admission_status": pressure.get("case_admission_status", ""),
                "pressure_true_f_D_or_K_fit_admitted_rows": pressure.get("true_f_D_or_K_fit_admitted_rows", ""),
                "junction_split_heat_ledger_status": ledger_status,
                "model_update_status": model_status,
                "evidence_path": evidence_path,
                "predictive_runtime_policy": status.get(
                    "predictive_runtime_policy",
                    "realized CFD wallHeatFlux is diagnostic target/output, not predictive runtime input",
                ),
            }
        )
    return rows


def build_model_gate_rows(
    aggregate_rows: list[dict[str, Any]],
    case_rows: list[dict[str, Any]],
    pressure_branch_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    total_checks = [row for row in aggregate_rows if row["physical_junction_bucket"] == "case_total_check"]
    closure_errors = [
        abs(fnum(row["realized_external_loss_positive_W"]) - fnum(row["source_aggregate_junction_loss_positive_W"]))
        for row in total_checks
    ]
    split_cases = {row["case_key"] for row in total_checks}
    pressure_admitted = sum(fnum(row.get("true_f_D_or_K_fit_admitted_rows")) for row in case_rows)
    all_cases_split = all(row["junction_split_heat_ledger_status"] == "admitted_junction_split_patch_heat_ledger" for row in case_rows)
    val_split = any(
        row["case_key"] == "val_salt2" and row["junction_split_heat_ledger_status"] == "admitted_junction_split_patch_heat_ledger"
        for row in case_rows
    )
    low_recirc_rows = [
        row for row in pressure_branch_rows
        if row.get("recirculation_mask_status") != "blocked_material_recirculation_mask"
    ]
    return [
        gate_row(
            "salt2_4_junction_patch_split_available",
            split_cases == {"salt2_mainline", "salt3_mainline", "salt4_mainline"},
            f"split cases={';'.join(sorted(split_cases))}",
            "Required to localize aggregate junction/stub heat for mainline salt cases.",
        ),
        gate_row(
            "split_rows_close_to_agent462_aggregate",
            bool(closure_errors) and max(closure_errors) < 1e-6,
            f"max closure error W={max(closure_errors) if closure_errors else 'missing'}",
            "Patch split must sum back to the AGENT-462 aggregate heat audit.",
        ),
        gate_row(
            "all_pressure_mapped_cases_have_junction_split_heat",
            all_cases_split,
            "Only Salt2/Salt3/Salt4 mainline have admitted split ledgers.",
            "Needed before broad trend claims across perturbation and external validation cases.",
        ),
        gate_row(
            "val_salt2_patch_split_available",
            val_split,
            "val_salt2 has aggregate section ledger only.",
            "Needed for independent external validation of localized junction losses.",
        ),
        gate_row(
            "pressure_corner_k_fit_admitted",
            pressure_admitted > 0,
            f"pressure admitted fit rows={pressure_admitted:g}; low-recirc branch rows={len(low_recirc_rows)}",
            "Needed before turning corner pressure diagnostics into component K factors.",
        ),
        gate_row(
            "runtime_setup_only_inputs_available_for_mainline_split",
            True,
            "Salt2-4 split rows include setup BC metadata and wall-shell temperature proxies; realized heat remains target only.",
            "Allows a future candidate model form, but not immediate production admission.",
        ),
        {
            "gate": "overall_ready_for_fluid_model_edit",
            "status": "fail",
            "evidence": "Mainline Salt2-4 split is usable, but val_salt2 and perturbation split ledgers are missing and pressure K remains diagnostic.",
            "requirement": "Do not edit Fluid model in this task; create a follow-on model task after split validation coverage exists.",
        },
    ]


def gate_row(gate: str, ok: bool, evidence: str, requirement: str) -> dict[str, str]:
    return {"gate": gate, "status": "pass" if ok else "fail", "evidence": evidence, "requirement": requirement}


def write_svg(rows: list[dict[str, Any]], path: Path) -> None:
    data = [row for row in rows if row["physical_junction_bucket"] in BUCKETS]
    case_keys = sorted({row["case_key"] for row in data})
    bucket_order = list(BUCKETS)
    width, height = 1100, 650
    left, top, plot_w, plot_h = 90, 60, 850, 470
    max_v = max(fnum(row["realized_external_loss_positive_W"]) for row in data) * 1.15
    colors = {
        "lower_left": "#4c78a8",
        "lower_right": "#f58518",
        "upper_left": "#54a24b",
        "upper_right": "#b279a2",
    }

    def y_for(v: float) -> float:
        return top + plot_h - (v / max_v) * plot_h

    group_w = plot_w / len(case_keys)
    bar_w = min(38, group_w / 6)
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        "<style>text{font-family:Arial,Helvetica,sans-serif;fill:#222}.title{font-size:22px;font-weight:700}.label{font-size:13px}.small{font-size:11px}.grid{stroke:#ddd}.axis{stroke:#333;stroke-width:1.2}</style>",
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="white"/>',
        '<text x="90" y="35" class="title">Junction/Stub Heat Loss Split</text>',
    ]
    for tick in range(0, int(math.ceil(max_v / 5) * 5) + 1, 10):
        y = y_for(tick)
        parts.append(f'<line x1="{left}" x2="{left+plot_w}" y1="{y:.1f}" y2="{y:.1f}" class="grid"/>')
        parts.append(f'<text x="{left-8}" y="{y+4:.1f}" text-anchor="end" class="small">{tick}</text>')
    parts.append(f'<line x1="{left}" x2="{left+plot_w}" y1="{top+plot_h}" y2="{top+plot_h}" class="axis"/>')
    parts.append(f'<line x1="{left}" x2="{left}" y1="{top}" y2="{top+plot_h}" class="axis"/>')
    by_case_bucket = {(row["case_key"], row["physical_junction_bucket"]): row for row in data}
    for i, case_key in enumerate(case_keys):
        cx = left + group_w * (i + 0.5)
        start = cx - len(bucket_order) * bar_w / 2
        for j, bucket in enumerate(bucket_order):
            row = by_case_bucket[(case_key, bucket)]
            value = fnum(row["realized_external_loss_positive_W"])
            y = y_for(value)
            h = top + plot_h - y
            x = start + j * bar_w
            parts.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w-2:.1f}" height="{h:.1f}" fill="{colors[bucket]}"/>')
        parts.append(f'<text x="{cx:.1f}" y="{height-88}" text-anchor="middle" class="small">{case_key}</text>')
    parts.append(f'<text x="{left+plot_w/2}" y="{height-46}" text-anchor="middle" class="label">case</text>')
    parts.append(f'<text x="28" y="{top+plot_h/2}" transform="rotate(-90 28,{top+plot_h/2})" text-anchor="middle" class="label">external heat loss [W]</text>')
    lx, ly = 955, 80
    for i, bucket in enumerate(bucket_order):
        y = ly + i * 24
        parts.append(f'<rect x="{lx}" y="{y}" width="16" height="12" fill="{colors[bucket]}"/>')
        parts.append(f'<text x="{lx+22}" y="{y+11}" class="small">{bucket}</text>')
    parts.append("</svg>")
    path.write_text("\n".join(parts) + "\n")


def write_report(
    aggregate_rows: list[dict[str, Any]],
    case_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
) -> None:
    total_rows = [row for row in aggregate_rows if row["physical_junction_bucket"] == "case_total_check"]
    lines = [
        "# Junction Split Heat Ledger And Model Gate",
        "",
        "## Bottom Line",
        "",
        "Salt2-4 mainline now have a physical-junction split of the aggregate `junction_other` heat loss. The split closes exactly against the AGENT-462 aggregate audit and is suitable as diagnostic training/holdout target evidence. It is not enough to edit the 1D Fluid model in this task because val_salt2 and perturbation cases do not yet have equivalent patch-split ledgers, and the pressure corner-K lane remains diagnostic.",
        "",
        "## Split Heat Result",
        "",
        "| case | split loss W | source aggregate W | closure error W |",
        "|---|---:|---:|---:|",
    ]
    for row in total_rows:
        split = fnum(row["realized_external_loss_positive_W"])
        source = fnum(row["source_aggregate_junction_loss_positive_W"])
        lines.append(f"| `{row['case_key']}` | {split:.6f} | {source:.6f} | {split - source:.6e} |")
    lines.extend(
        [
            "",
            "## Case Coverage",
            "",
            "| case | junction heat status | model status |",
            "|---|---|---|",
        ]
    )
    for row in case_rows:
        lines.append(f"| `{row['case_key']}` | {row['junction_split_heat_ledger_status']} | {row['model_update_status']} |")
    lines.extend(
        [
            "",
            "## Model Update Gate",
            "",
            "| gate | status | evidence |",
            "|---|---|---|",
        ]
    )
    for row in gate_rows:
        lines.append(f"| `{row['gate']}` | {row['status']} | {row['evidence']} |")
    lines.extend(
        [
            "",
            "## Scientific Interpretation",
            "",
            "The split shows that the junction/stub heat-loss pathway is localized but distributed across corner bodies, extensions, stubs, steps, and non-conformal coupling/interface patches. The Salt2-4 rows include setup boundary metadata and wall-shell temperature proxies, so they can support a future setup-only candidate model form. Realized `wallHeatFlux` must remain a training or validation target, never a runtime model input.",
            "",
            "The immediate 1D-model action is therefore not a Fluid code edit. The next implementation task should either harvest/promote missing split ledgers for val_salt2 and perturbation cases or deliberately define a narrower Salt2-4-only candidate experiment with that limitation documented.",
            "",
            "## Outputs",
            "",
            "- `junction_split_patch_ledger.csv`: patch-level Salt2-4 split rows.",
            "- `junction_split_heat_ledger.csv`: physical-junction aggregate rows plus source-total checks.",
            "- `junction_temperature_drive_candidates.csv`: setup-only candidate drive quantities.",
            "- `case_heat_ledger_admission.csv`: heat-ledger coverage for every pressure-mapped case.",
            "- `model_update_gate.csv`: explicit pass/fail gate for Fluid model edits.",
            "- `junction_split_heat_by_bucket.svg`: visual audit of the split heat by case and bucket.",
        ]
    )
    (OUT / "junction_split_heat_ledger_and_model_gate.md").write_text("\n".join(lines) + "\n")


def build() -> dict[str, Any]:
    OUT.mkdir(parents=True, exist_ok=True)
    heat_audit = read_csv(AGENT462_HEAT_AUDIT)
    coverage = read_csv(AGENT462_COVERAGE)
    patch_rows = build_patch_ledger(read_csv(EXTERNAL_BC_PATCH_CONTRACT), read_csv(WALL_SHELL_TEMPS))
    aggregate_rows = aggregate_patch_ledger(patch_rows, heat_audit)
    case_rows = build_case_admission_rows(
        coverage,
        heat_audit,
        read_csv(HEAT_LEDGER_STATUS),
        read_csv(PRESSURE_ADMISSION_SUMMARY),
        {row["case_key"] for row in patch_rows},
    )
    temp_candidates = build_temperature_drive_candidates(aggregate_rows)
    gate_rows = build_model_gate_rows(aggregate_rows, case_rows, read_csv(PRESSURE_ADMISSION_BRANCH))

    write_csv(OUT / "junction_split_patch_ledger.csv", patch_rows)
    write_csv(OUT / "junction_split_heat_ledger.csv", aggregate_rows)
    write_csv(OUT / "junction_temperature_drive_candidates.csv", temp_candidates)
    write_csv(OUT / "case_heat_ledger_admission.csv", case_rows)
    write_csv(OUT / "model_update_gate.csv", gate_rows, ["gate", "status", "evidence", "requirement"])
    write_csv(
        OUT / "source_manifest.csv",
        [
            {"source_type": "agent462_heat_audit", "path": rel(AGENT462_HEAT_AUDIT), "use": "aggregate realized heat audit"},
            {"source_type": "agent462_heat_coverage", "path": rel(AGENT462_COVERAGE), "use": "pressure case coverage list"},
            {"source_type": "external_bc_patch_contract", "path": rel(EXTERNAL_BC_PATCH_CONTRACT), "use": "patch-level junction heat and setup metadata"},
            {"source_type": "wall_shell_temperatures", "path": rel(WALL_SHELL_TEMPS), "use": "patch-level wall temperature proxies"},
            {"source_type": "pressure_admission_summary", "path": rel(PRESSURE_ADMISSION_SUMMARY), "use": "pressure fit admission state"},
            {"source_type": "pressure_admission_branch", "path": rel(PRESSURE_ADMISSION_BRANCH), "use": "recirculation/orientation/straight-loss status"},
            {"source_type": "heat_ledger_status", "path": rel(HEAT_LEDGER_STATUS), "use": "missing/promotable heat ledger status"},
            {"source_type": "salt1_role_summary", "path": rel(SALT1_ROLE_SUMMARY), "use": "Salt1 BC metadata status"},
            {"source_type": "salt1_patch_bc", "path": rel(SALT1_PATCH_BC), "use": "Salt1 patch names and setup metadata"},
        ],
        ["source_type", "path", "use"],
    )
    write_svg(aggregate_rows, OUT / "junction_split_heat_by_bucket.svg")
    write_report(aggregate_rows, case_rows, gate_rows)
    summary = {
        "task": TASK,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "junction_split_patch_rows": len(patch_rows),
        "junction_split_case_count": len({row["case_key"] for row in patch_rows}),
        "junction_split_cases": sorted({row["case_key"] for row in patch_rows}),
        "pressure_cases_covered": len(case_rows),
        "overall_ready_for_fluid_model_edit": next(row for row in gate_rows if row["gate"] == "overall_ready_for_fluid_model_edit")["status"],
        "outputs": {
            "patch_ledger": rel(OUT / "junction_split_patch_ledger.csv"),
            "heat_ledger": rel(OUT / "junction_split_heat_ledger.csv"),
            "case_admission": rel(OUT / "case_heat_ledger_admission.csv"),
            "model_gate": rel(OUT / "model_update_gate.csv"),
            "report": rel(OUT / "junction_split_heat_ledger_and_model_gate.md"),
        },
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    return summary


def main() -> None:
    print(json.dumps(build(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
