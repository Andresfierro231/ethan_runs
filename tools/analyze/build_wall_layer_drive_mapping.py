#!/usr/bin/env python3
"""Assemble CFD wall-layer drive diagnostics for 1D external-boundary parity.

This TODO-PRED-WALL-LAYER pass consumes already-published repo artifacts.  It
does not sample OpenFOAM fields or modify native solver outputs.  Positive CFD
``wallHeatFlux`` means heat enters the fluid; positive external loss in this
script means heat leaves the fluid.
"""

from __future__ import annotations

import csv
import json
import math
import platform
import socket
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]

TASK_ID = "TODO-PRED-WALL-LAYER"
OUT = ROOT / "work_products/2026-07/2026-07-13/2026-07-13_wall_layer_drive_mapping"
PATCH_TABLE = (
    ROOT
    / "work_products/2026-07/2026-07-13/2026-07-13_thermal_boundary_patch_role_table/thermal_boundary_patch_role_table.csv"
)
SEGMENT_REDUCTIONS = (
    ROOT
    / "work_products/2026-07/2026-07-13/2026-07-13_thermal_boundary_patch_role_table/segment_reduction_inputs.csv"
)
RADIATION_GUIDANCE = (
    ROOT / "work_products/2026-07/2026-07-13/2026-07-13_cfd_radiative_boundary_guidance"
)
THERMAL_CONTRACT = (
    ROOT / "work_products/2026-07/2026-07-08/2026-07-08_thermal_boundary_contract/cfd_thermal_boundary_contract.csv"
)
SPAN_HEAT = (
    ROOT / "work_products/2026-07/2026-07-08/2026-07-08_thermal_boundary_contract/span_heat_residuals.csv"
)
INTERFACE_TEMPERATURES = (
    ROOT
    / "work_products/2026-07/2026-07-08/2026-07-08_patchwise_heat_ledger_enthalpy_interfaces/interface_temperature_samples.csv"
)
WALL_SHELL_TEMPERATURES = (
    ROOT
    / "work_products/2026-07/2026-07-13/2026-07-13_wall_shell_temperature_sampling/segment_wall_shell_temperatures.csv"
)

SIGMA = 5.670374419e-8
SOURCE_ROLES = {"heater", "cooler", "test_section"}
FIT_PASSIVE_ROLES = {"ambient_wall", "junction_other"}

DRIVE_COLUMNS = [
    "source_id",
    "case_id",
    "one_d_segment",
    "role",
    "patch_count",
    "area_m2",
    "hA_W_K",
    "area_weighted_h_W_m2K",
    "Ta_K",
    "Tsur_K",
    "emissivity",
    "realized_wallHeatFlux_W",
    "external_loss_realized_W",
    "imposed_Q_W",
    "T_mix_signed_K",
    "T_fwd_bulk_K",
    "T_path_bulk_K",
    "T_wall_inner_K",
    "T_wall_shell_K",
    "recirculation_ratio_max",
    "recirculation_status",
    "T_ext_drive_signed_inverse_K",
    "T_ext_drive_loss_positive_K",
    "bulk_temperature_status",
    "wall_inner_status",
    "wall_shell_status",
    "radiation_policy",
    "fit_use_status",
    "source_paths",
]

REPLAY_COLUMNS = [
    "source_id",
    "case_id",
    "one_d_segment",
    "role",
    "mode",
    "drive_temperature_selector",
    "beta_family_id",
    "beta_value",
    "beta_fit_status",
    "drive_temperature_K",
    "executable",
    "block_reason",
    "hA_W_K",
    "convective_loss_positive_W",
    "radiative_loss_positive_W",
    "total_external_loss_positive_W",
    "wallHeatFlux_equivalent_W",
    "realized_wallHeatFlux_W",
    "residual_wallHeatFlux_equiv_minus_cfd_W",
    "radiation_policy",
]

PARITY_COLUMNS = [
    "source_id",
    "case_id",
    "one_d_segment",
    "role",
    "mode",
    "fit_use_status",
    "realized_external_loss_W",
    "mode_external_loss_W",
    "loss_residual_mode_minus_cfd_W",
    "wallHeatFlux_residual_mode_minus_cfd_W",
    "absolute_loss_residual_W",
    "notes",
]

SELECTOR_COLUMNS = [
    "source_id",
    "case_id",
    "one_d_segment",
    "role",
    "T_path_bulk_K",
    "T_wall_inner_K",
    "T_wall_shell_K",
    "T_ext_drive_loss_positive_K",
    "bulk_minus_inverse_K",
    "wall_inner_minus_inverse_K",
    "required_beta_bulk_to_wall_shell",
    "recommended_selector",
    "selector_status",
]

BLOCK_COLUMNS = [
    "source_id",
    "case_id",
    "one_d_segment",
    "role",
    "mode",
    "block_reason",
    "next_evidence_needed",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def fnum(value: Any, default: float | None = None) -> float | None:
    if value is None:
        return default
    text = str(value).strip()
    if text in {"", "nan", "NaN", "None"}:
        return default
    try:
        parsed = float(text)
    except (TypeError, ValueError):
        return default
    return parsed if math.isfinite(parsed) else default


def csv_value(value: Any) -> Any:
    if value is None:
        return ""
    if isinstance(value, float):
        if not math.isfinite(value):
            return ""
        return f"{value:.9f}".rstrip("0").rstrip(".")
    return value


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({column: csv_value(row.get(column, "")) for column in columns})


def area_weighted(rows: list[dict[str, Any]], value_key: str, area_key: str = "area_m2") -> float | None:
    num = 0.0
    den = 0.0
    for row in rows:
        value = fnum(row.get(value_key))
        area = fnum(row.get(area_key))
        if value is None or area is None or area <= 0:
            continue
        num += value * area
        den += area
    return num / den if den > 0 else None


def sum_float(rows: list[dict[str, Any]], key: str) -> float:
    return sum(fnum(row.get(key), 0.0) or 0.0 for row in rows)


def heat_loss_from_drive(
    *,
    area_m2: float | None,
    h_w_m2k: float | None,
    ta_k: float | None,
    tsur_k: float | None,
    emissivity: float | None,
    drive_k: float | None,
) -> tuple[float | None, float | None, float | None]:
    """Return positive external convective, radiative, and total loss."""
    if area_m2 is None or h_w_m2k is None or ta_k is None or drive_k is None:
        return None, None, None
    conv = area_m2 * h_w_m2k * (drive_k - ta_k)
    rad: float | None = None
    if tsur_k is not None and emissivity is not None:
        rad = area_m2 * emissivity * SIGMA * (drive_k**4 - tsur_k**4)
    total = conv + (rad or 0.0)
    return conv, rad, total


def inverse_drive_from_wallheatflux(
    q_into_fluid_w: float | None,
    hA_w_k: float | None,
    ta_k: float | None,
) -> tuple[float | None, float | None]:
    """Return signed and loss-positive inverse drive temperatures.

    The signed convention assumes ``q_into_fluid = hA * (Ta - Tdrive)``.  The
    loss-positive value ignores heat gains from source rows and is intended only
    as a passive-loss diagnostic.
    """
    if q_into_fluid_w is None or hA_w_k is None or hA_w_k <= 0 or ta_k is None:
        return None, None
    signed = ta_k - q_into_fluid_w / hA_w_k
    loss_positive = ta_k + max(-q_into_fluid_w, 0.0) / hA_w_k
    return signed, loss_positive


def load_span_temperatures(rows: list[dict[str, str]]) -> dict[tuple[str, str, str], dict[str, Any]]:
    out: dict[tuple[str, str, str], dict[str, Any]] = {}
    for row in rows:
        key = (row["source_id"], row["case_id"], row["span"])
        bulk = fnum(row.get("T_bulk_span_K"))
        out[key] = {
            "T_mix_signed_K": bulk,
            "T_path_bulk_K": bulk,
            "bulk_temperature_status": row.get("enthalpy_change_status", ""),
        }
    return out


def load_wall_temperatures(rows: list[dict[str, str]]) -> dict[tuple[str, str, str, str], dict[str, Any]]:
    grouped: dict[tuple[str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        key = (row["source_id"], row["case_id"], row["span"], row["patch_group"])
        grouped[key].append(row)
    out: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    for key, group_rows in grouped.items():
        out[key] = {
            "T_wall_inner_K": area_weighted(group_rows, "wall_T_mean_K", "patch_area_m2"),
            "wall_inner_status": "area_weighted_wall_T_mean_from_july8_contract",
        }
    return out


def load_interface_temperatures(rows: list[dict[str, str]]) -> dict[tuple[str, str, str], dict[str, Any]]:
    grouped: dict[tuple[str, str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        if row.get("interface_role") not in {"physical_segment_inlet", "physical_segment_outlet"}:
            continue
        key = (row["source_id"], row["case_id"], row["physical_segment"])
        grouped[key].append(row)

    out: dict[tuple[str, str, str], dict[str, Any]] = {}
    for key, group_rows in grouped.items():
        fwd_values = [fnum(row.get("T_fwd_bulk_K")) for row in group_rows]
        fwd_values = [value for value in fwd_values if value is not None]
        recirc_values = [fnum(row.get("recirculation_ratio")) for row in group_rows]
        recirc_values = [value for value in recirc_values if value is not None]
        flags = sorted(
            {
                flag
                for row in group_rows
                for flag in str(row.get("quality_flags", "")).split(";")
                if flag
            }
        )
        recirc_max = max(recirc_values) if recirc_values else None
        if recirc_max is None:
            recirc_status = "missing_recirculation_ratio"
        elif recirc_max >= 0.5:
            recirc_status = "high_recirculation_forward_bulk_diagnostic"
        elif recirc_max >= 0.1:
            recirc_status = "moderate_recirculation_report_bulk_and_forward"
        else:
            recirc_status = "low_recirculation"
        if flags:
            recirc_status = recirc_status + ";" + ";".join(flags)
        out[key] = {
            "T_fwd_bulk_K": sum(fwd_values) / len(fwd_values) if fwd_values else None,
            "recirculation_ratio_max": recirc_max,
            "recirculation_status": recirc_status,
        }
    return out


def load_wall_shell_temperatures(rows: list[dict[str, str]]) -> dict[tuple[str, str, str, str], dict[str, Any]]:
    out: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    for row in rows:
        key = (row["source_id"], row["case_id"], row["one_d_segment"], row["role"])
        out[key] = {
            "T_wall_shell_K": fnum(row.get("T_wall_shell_K")),
            "wall_shell_status": row.get("support_status", "missing_wall_shell_support_status"),
        }
    return out


def aggregate_patch_rows(patch_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str, str], list[dict[str, str]]] = defaultdict(list)
    for row in patch_rows:
        if row.get("fit_use_status") == "connector_not_fit_target":
            continue
        segment = row.get("one_d_segment", "")
        role = row.get("role", "")
        if not segment or not role or role == "zero_gradient_ncc_connector":
            continue
        grouped[(row["source_id"], row["case_id"], segment, role)].append(row)

    out: list[dict[str, Any]] = []
    for (source_id, case_id, segment, role), rows in sorted(grouped.items()):
        area = sum_float(rows, "area_m2")
        hA = sum(
            (fnum(row.get("area_m2"), 0.0) or 0.0) * (fnum(row.get("h_W_m2K"), 0.0) or 0.0)
            for row in rows
        )
        out.append(
            {
                "source_id": source_id,
                "case_id": case_id,
                "one_d_segment": segment,
                "role": role,
                "patch_count": len(rows),
                "area_m2": area,
                "hA_W_K": hA if hA > 0 else None,
                "area_weighted_h_W_m2K": hA / area if hA > 0 and area > 0 else None,
                "Ta_K": area_weighted(rows, "Ta_K"),
                "Tsur_K": area_weighted(rows, "Tsur_K"),
                "emissivity": area_weighted(rows, "emissivity"),
                "realized_wallHeatFlux_W": sum_float(rows, "realized_wallHeatFlux_W"),
                "imposed_Q_W": sum_float(rows, "imposed_Q_W"),
                "source_paths": ";".join(sorted({row.get("wallHeatFlux_source_path", "") for row in rows if row.get("wallHeatFlux_source_path")})),
            }
        )
    return out


def build_drive_table(
    patch_rows: list[dict[str, str]],
    span_rows: list[dict[str, str]],
    contract_rows: list[dict[str, str]],
    interface_rows: list[dict[str, str]],
    shell_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    span_temps = load_span_temperatures(span_rows)
    wall_temps = load_wall_temperatures(contract_rows)
    interface_temps = load_interface_temperatures(interface_rows)
    shell_temps = load_wall_shell_temperatures(shell_rows)
    rows = aggregate_patch_rows(patch_rows)

    for row in rows:
        key3 = (row["source_id"], row["case_id"], row["one_d_segment"])
        key4 = (row["source_id"], row["case_id"], row["one_d_segment"], row["role"])
        span = span_temps.get(key3, {})
        wall = wall_temps.get(key4, {})
        interface = interface_temps.get(key3, {})
        shell = shell_temps.get(key4, {})
        row.update(span)
        row.update(interface)
        row.update(wall)
        row.update(shell)
        row.setdefault("T_fwd_bulk_K", None)
        row.setdefault("recirculation_ratio_max", None)
        row.setdefault("recirculation_status", "missing_interface_temperature_sample")
        row.setdefault("T_wall_shell_K", None)
        row.setdefault("wall_shell_status", "missing_near_wall_shell_temperature_no_existing_artifact")
        row["T_ext_drive_signed_inverse_K"], row["T_ext_drive_loss_positive_K"] = inverse_drive_from_wallheatflux(
            fnum(row.get("realized_wallHeatFlux_W")),
            fnum(row.get("hA_W_K")),
            fnum(row.get("Ta_K")),
        )
        row["external_loss_realized_W"] = max(-(fnum(row.get("realized_wallHeatFlux_W"), 0.0) or 0.0), 0.0)
        row["radiation_policy"] = (
            "CFD rcExternalTemperature uses emissivity/Tsur; wallHeatFlux is total and radiation is inseparable"
        )
        row["fit_use_status"] = fit_status(row)
        row.setdefault("bulk_temperature_status", "missing_segment_bulk_temperature")
        row.setdefault("wall_inner_status", "missing_wall_inner_temperature")
    return rows


def fit_status(row: dict[str, Any]) -> str:
    role = row.get("role", "")
    if role in SOURCE_ROLES:
        return "source_or_sink_role_document_only_keep_separate_from_passive_hA_fit"
    if role not in FIT_PASSIVE_ROLES:
        return "diagnostic_role_not_admitted_for_hA_fit"
    if fnum(row.get("hA_W_K")) is None:
        return "blocked_missing_hA"
    if fnum(row.get("T_path_bulk_K")) is None:
        return "blocked_missing_path_bulk_temperature"
    return "diagnostic_passive_external_hA_candidate"


def beta_family_id(row: dict[str, Any]) -> str:
    return f"{row.get('role', '')}:{row.get('one_d_segment', '')}"


def fit_beta_families(drive_rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in drive_rows:
        if row.get("role") not in FIT_PASSIVE_ROLES:
            continue
        if fnum(row.get("T_path_bulk_K")) is None or fnum(row.get("T_wall_shell_K")) is None:
            continue
        if fnum(row.get("hA_W_K")) is None:
            continue
        grouped[beta_family_id(row)].append(row)

    fits: dict[str, dict[str, Any]] = {}
    for family, rows in grouped.items():
        if len(rows) < 2:
            fits[family] = {"beta": None, "status": "blocked_less_than_two_rows_for_family_beta"}
            continue
        best_beta = 0.0
        best_sse = float("inf")
        for i in range(1001):
            beta = i / 1000.0
            sse = 0.0
            valid = 0
            for row in rows:
                t_bulk = fnum(row.get("T_path_bulk_K"))
                t_shell = fnum(row.get("T_wall_shell_K"))
                realized_loss = fnum(row.get("external_loss_realized_W"))
                if t_bulk is None or t_shell is None or realized_loss is None:
                    continue
                t_drive = t_bulk + beta * (t_shell - t_bulk)
                _conv, _rad, total = heat_loss_from_drive(
                    area_m2=fnum(row.get("area_m2")),
                    h_w_m2k=fnum(row.get("area_weighted_h_W_m2K")),
                    ta_k=fnum(row.get("Ta_K")),
                    tsur_k=fnum(row.get("Tsur_K")),
                    emissivity=fnum(row.get("emissivity")),
                    drive_k=t_drive,
                )
                if total is None:
                    continue
                sse += (total - realized_loss) ** 2
                valid += 1
            if valid and sse < best_sse:
                best_sse = sse
                best_beta = beta
        fits[family] = {
            "beta": best_beta,
            "status": "diagnostic_same_case_family_fit_no_validation_split",
            "rows": len(rows),
            "sse": best_sse,
        }
    return fits


def build_replay_rows(drive_rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    blocks: list[dict[str, Any]] = []
    beta_fits = fit_beta_families(drive_rows)
    for drive in drive_rows:
        for mode in ("E0_bulk", "E1_wall_shell", "E2_low_dimensional_blend"):
            family = beta_family_id(drive) if mode == "E2_low_dimensional_blend" else ""
            beta_fit = beta_fits.get(family, {}) if family else {}
            beta_value = beta_fit.get("beta")
            beta_status = beta_fit.get("status", "")
            if mode == "E0_bulk":
                selector = "T_path_bulk_K"
                next_evidence = "existing segment bulk from July 8 thermal contract"
                drive_temp = fnum(drive.get(selector))
            elif mode == "E1_wall_shell":
                selector = "T_wall_shell_K"
                next_evidence = "near-wall shell samples adjacent to heat-transfer patches"
                drive_temp = fnum(drive.get(selector))
            else:
                selector = "T_path_bulk_K_plus_beta_family_times_T_wall_shell_minus_T_path_bulk"
                next_evidence = "family-level beta fit using at least two passive rows"
                t_bulk = fnum(drive.get("T_path_bulk_K"))
                t_shell = fnum(drive.get("T_wall_shell_K"))
                drive_temp = (
                    t_bulk + float(beta_value) * (t_shell - t_bulk)
                    if t_bulk is not None and t_shell is not None and beta_value is not None
                    else None
                )
            hA = fnum(drive.get("hA_W_K"))
            executable = drive_temp is not None and hA is not None and hA > 0
            if mode == "E2_low_dimensional_blend" and drive.get("role") not in FIT_PASSIVE_ROLES:
                executable = False
                beta_status = "blocked_source_or_nonpassive_role_not_used_for_beta_fit"
            block_reason = ""
            if not executable:
                missing = []
                if drive_temp is None:
                    missing.append(selector)
                if hA is None or hA <= 0:
                    missing.append("hA_W_K")
                if mode == "E2_low_dimensional_blend" and drive.get("role") not in FIT_PASSIVE_ROLES:
                    missing.append("passive_fit_role")
                if mode == "E2_low_dimensional_blend" and beta_value is None and drive.get("role") in FIT_PASSIVE_ROLES:
                    missing.append("beta_family_fit")
                block_reason = "missing_" + "_and_".join(missing)
                blocks.append(
                    {
                        "source_id": drive["source_id"],
                        "case_id": drive["case_id"],
                        "one_d_segment": drive["one_d_segment"],
                        "role": drive["role"],
                        "mode": mode,
                        "block_reason": block_reason,
                        "next_evidence_needed": next_evidence,
                    }
                )
            conv, rad, total = heat_loss_from_drive(
                area_m2=fnum(drive.get("area_m2")),
                h_w_m2k=fnum(drive.get("area_weighted_h_W_m2K")),
                ta_k=fnum(drive.get("Ta_K")),
                tsur_k=fnum(drive.get("Tsur_K")),
                emissivity=fnum(drive.get("emissivity")),
                drive_k=drive_temp,
            )
            wall_equiv = -total if total is not None else None
            cfd_q = fnum(drive.get("realized_wallHeatFlux_W"))
            residual = wall_equiv - cfd_q if wall_equiv is not None and cfd_q is not None else None
            rows.append(
                {
                    "source_id": drive["source_id"],
                    "case_id": drive["case_id"],
                    "one_d_segment": drive["one_d_segment"],
                    "role": drive["role"],
                    "mode": mode,
                    "drive_temperature_selector": selector,
                    "beta_family_id": family,
                    "beta_value": beta_value,
                    "beta_fit_status": beta_status,
                    "drive_temperature_K": drive_temp,
                    "executable": "yes" if executable else "no",
                    "block_reason": block_reason,
                    "hA_W_K": hA,
                    "convective_loss_positive_W": conv,
                    "radiative_loss_positive_W": rad,
                    "total_external_loss_positive_W": total,
                    "wallHeatFlux_equivalent_W": wall_equiv,
                    "realized_wallHeatFlux_W": cfd_q,
                    "residual_wallHeatFlux_equiv_minus_cfd_W": residual,
                    "radiation_policy": "approximate convection+radiation replay; not exact rcExternalTemperature source formula",
                }
            )
    return rows, blocks


def build_parity_rows(drive_rows: list[dict[str, Any]], replay_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    drive_by_key = {
        (row["source_id"], row["case_id"], row["one_d_segment"], row["role"]): row for row in drive_rows
    }
    rows: list[dict[str, Any]] = []
    for replay in replay_rows:
        if replay.get("executable") != "yes":
            continue
        key = (replay["source_id"], replay["case_id"], replay["one_d_segment"], replay["role"])
        drive = drive_by_key[key]
        realized_loss = fnum(drive.get("external_loss_realized_W"))
        mode_loss = fnum(replay.get("total_external_loss_positive_W"))
        q_residual = fnum(replay.get("residual_wallHeatFlux_equiv_minus_cfd_W"))
        loss_residual = mode_loss - realized_loss if mode_loss is not None and realized_loss is not None else None
        rows.append(
            {
                "source_id": replay["source_id"],
                "case_id": replay["case_id"],
                "one_d_segment": replay["one_d_segment"],
                "role": replay["role"],
                "mode": replay["mode"],
                "fit_use_status": drive["fit_use_status"],
                "realized_external_loss_W": realized_loss,
                "mode_external_loss_W": mode_loss,
                "loss_residual_mode_minus_cfd_W": loss_residual,
                "wallHeatFlux_residual_mode_minus_cfd_W": q_residual,
                "absolute_loss_residual_W": abs(loss_residual) if loss_residual is not None else None,
                "notes": parity_note(drive),
            }
        )
    return rows


def parity_note(row: dict[str, Any]) -> str:
    role = row.get("role")
    if role in SOURCE_ROLES:
        return "source_or_sink_role; do not fit passive hA to absorb this residual"
    if fnum(row.get("T_wall_shell_K")) is None:
        return "E0 uses bulk drive only; E1/E2 require near-wall shell extraction"
    return "passive external hA diagnostic"


def build_selector_rows(drive_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in drive_rows:
        t_bulk = fnum(row.get("T_path_bulk_K"))
        t_inner = fnum(row.get("T_wall_inner_K"))
        t_shell = fnum(row.get("T_wall_shell_K"))
        t_inv = fnum(row.get("T_ext_drive_loss_positive_K"))
        required_beta = None
        if t_bulk is not None and t_shell is not None and t_inv is not None and abs(t_shell - t_bulk) > 1e-9:
            required_beta = (t_inv - t_bulk) / (t_shell - t_bulk)
        if t_shell is None:
            selector = "E0_bulk_only_available"
            status = "blocked_for_E1_E2_missing_T_wall_shell"
        elif required_beta is None:
            selector = "E1_wall_shell"
            status = "wall_shell_available_beta_not_identifiable"
        else:
            selector = "E2_low_dimensional_blend_candidate"
            status = "candidate_requires_family_level_beta_gate"
        rows.append(
            {
                "source_id": row["source_id"],
                "case_id": row["case_id"],
                "one_d_segment": row["one_d_segment"],
                "role": row["role"],
                "T_path_bulk_K": t_bulk,
                "T_wall_inner_K": t_inner,
                "T_wall_shell_K": t_shell,
                "T_ext_drive_loss_positive_K": t_inv,
                "bulk_minus_inverse_K": t_bulk - t_inv if t_bulk is not None and t_inv is not None else None,
                "wall_inner_minus_inverse_K": t_inner - t_inv if t_inner is not None and t_inv is not None else None,
                "required_beta_bulk_to_wall_shell": required_beta,
                "recommended_selector": selector,
                "selector_status": status,
            }
        )
    return rows


def write_readme(summary: dict[str, Any]) -> None:
    readme = f"""# Wall-Layer Drive Mapping

Generated: `{summary['generated_at']}`
Task: `{TASK_ID}`

## Purpose

This package advances the CFD-to-1D external-boundary parity ladder after the
AGENT-263 patch-role table and AGENT-287 radiation correction. It assembles the
available segment bulk and wall-temperature evidence, computes an E0 bulk-drive
external-loss diagnostic, and records why E1/E2 wall-shell modes are not yet
publication-ready.

## Radiation Policy

Ethan CFD should be described as radiation-capable. The admitted Salt
`rcExternalTemperature` rows use emissivity and `Tsur`, and AGENT-277/287 show
those inputs affect total `wallHeatFlux`. The available CFD output has no
separate `qr` ledger, so realized `wallHeatFlux` is a total heat flux. This
package therefore never adds a separate radiation term on top of realized CFD
`wallHeatFlux`.

For the approximate E0 external-BC replay, the table reports convection plus a
Stefan-Boltzmann radiation term using AGENT-263 `h`, `Ta`, `Tsur`, emissivity,
and area. That replay is explicitly marked approximate because the exact
`rcExternalTemperature` source formula is not encoded in the current Fluid API.

## Outputs

- `external_bc_drive_table.csv`: role-level CFD boundary rows joined to
  available bulk, forward-bulk, recirculation, and wall drive temperatures.
- `external_bc_replay_modes.csv`: E0/E1/E2 replay rows with executable/block
  status.
- `section_heat_parity.csv`: E0 loss residuals against realized CFD total
  `wallHeatFlux`.
- `wall_layer_selector_candidates.csv`: inverse-drive and selector diagnostics.
- `blocked_rows.csv`: missing evidence or fit-status blockers for E1/E2 parity.
- `run_metadata.json`: provenance, source paths, command, and row counts.

## Key Counts

- Drive rows: `{summary['drive_rows']}`
- Replay rows: `{summary['replay_rows']}`
- E0 executable rows: `{summary['e0_executable_rows']}`
- Blocked rows: `{summary['blocked_rows']}`

## Scientific Reading Order

Read `external_bc_drive_table.csv` first to confirm the CFD boundary role,
`hA`, ambient/surroundings temperature, emissivity, realized flux, imposed heat,
and available drive temperatures. Then read `section_heat_parity.csv` for the
bulk-drive residual. E1 rows use the available wall-shell proxy when present.
E2 rows use diagnostic same-family beta fits only for passive rows and remain
blocked for source/sink rows.

## Interpretation

The current forward progress is enough to document the parity boundary:

- patch/role/segment external inputs are assembled from authoritative CFD
  artifacts;
- radiation is treated as present and inseparable in realized CFD flux;
- E0 bulk-drive replay is quantified with paired forward-bulk/recirculation
  metadata where existing interface samples support it;
- E1 wall-shell replay is executable where `T_wall_shell_K` is present;
- E2 blend replay is diagnostic and restricted to low-dimensional passive
  section-family beta fits.

Do not use source/sink roles (`heater`, `cooler`, `test_section`) to fit passive
external `hA`. Keep those terms separated from ambient-wall parity.
"""
    (OUT / "README.md").write_text(readme, encoding="utf-8")


def git_rev() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return "unavailable"
    return result.stdout.strip() if result.returncode == 0 else "unavailable"


def build() -> dict[str, Any]:
    patch_rows = read_csv(PATCH_TABLE)
    _segment_rows = read_csv(SEGMENT_REDUCTIONS)
    span_rows = read_csv(SPAN_HEAT)
    contract_rows = read_csv(THERMAL_CONTRACT)
    interface_rows = read_csv(INTERFACE_TEMPERATURES)
    shell_rows = read_csv(WALL_SHELL_TEMPERATURES) if WALL_SHELL_TEMPERATURES.exists() else []

    drive_rows = build_drive_table(patch_rows, span_rows, contract_rows, interface_rows, shell_rows)
    replay_rows, block_rows = build_replay_rows(drive_rows)
    parity_rows = build_parity_rows(drive_rows, replay_rows)
    selector_rows = build_selector_rows(drive_rows)

    write_csv(OUT / "external_bc_drive_table.csv", drive_rows, DRIVE_COLUMNS)
    write_csv(OUT / "external_bc_replay_modes.csv", replay_rows, REPLAY_COLUMNS)
    write_csv(OUT / "section_heat_parity.csv", parity_rows, PARITY_COLUMNS)
    write_csv(OUT / "wall_layer_selector_candidates.csv", selector_rows, SELECTOR_COLUMNS)
    write_csv(OUT / "blocked_rows.csv", block_rows, BLOCK_COLUMNS)

    summary = {
        "task_id": TASK_ID,
        "generated_at": utc_now(),
        "host": socket.gethostname(),
        "platform": platform.platform(),
        "git_rev": git_rev(),
        "source_paths": {
            "patch_table": rel(PATCH_TABLE),
            "segment_reductions": rel(SEGMENT_REDUCTIONS),
            "radiation_guidance": rel(RADIATION_GUIDANCE),
            "thermal_contract": rel(THERMAL_CONTRACT),
            "span_heat_residuals": rel(SPAN_HEAT),
            "interface_temperature_samples": rel(INTERFACE_TEMPERATURES),
            "wall_shell_temperatures": rel(WALL_SHELL_TEMPERATURES),
        },
        "drive_rows": len(drive_rows),
        "replay_rows": len(replay_rows),
        "e0_executable_rows": sum(
            1 for row in replay_rows if row["mode"] == "E0_bulk" and row["executable"] == "yes"
        ),
        "blocked_rows": len(block_rows),
        "radiation_conclusion": (
            "emissivity and Tsur affect CFD wallHeatFlux; radiation is embedded/inseparable in total wallHeatFlux"
        ),
    }
    (OUT / "run_metadata.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    write_readme(summary)
    return summary


def main() -> int:
    summary = build()
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
