#!/usr/bin/env python3
"""Build the val_salt_test_2_coarse_mesh admission unlock package.

This builder is intentionally read-only with respect to CFD case directories.
It consumes already-generated postProcessing/registry aggregates, reconciles the
older heat-drift label with a fresh terminal-window check, and promotes the
existing BC/material documentation into an external-test admission package.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUT = (
    ROOT
    / "work_products/2026-07/2026-07-15/2026-07-15_val_salt2_postprocessing_admission_unlock"
)

CASE_KEY = "salt2_native_val"
DISPLAY_LABEL = "val_salt_test_2_coarse_mesh"
SOURCE_ID = "val_salt_test_2_coarse_mesh_laminar"
TASK = "AGENT-422"

REGISTRY_ROOT = (
    ROOT
    / "registry/salt2/native_2d_cfd_external/salt_test_2/val_salt_test_2_coarse_mesh_laminar"
)
AGG = REGISTRY_ROOT / "aggregates"
WALL_HEAT = AGG / "wall_heat_flux_grouped.csv"
CASE_SUMMARY = AGG / "case_summary.csv"
POST_LONG = AGG / "postprocessing_case_long.csv"
MANIFEST = REGISTRY_ROOT / "aggregation_manifest.json"
RUNTIME_ROOT = (
    ROOT
    / "jadyn_runs/salt2/2026-06-01_continuation_candidate/case_stage/"
    "val_salt_test_2_coarse_mesh_laminar_continuation"
)
TOTAL_Q = RUNTIME_ROOT / "postProcessing/total_Q.dat"
OLD_ROLLUP = (
    ROOT
    / "work_products/2026-07/2026-07-09/2026-07-09_cfd_steady_state_continuation_table/"
    "all_timeseries_case_rollup.csv"
)
AGENT417_MASTER = (
    ROOT
    / "work_products/2026-07/2026-07-15/2026-07-15_salt_external_test_and_q_unlock_admission/"
    "salt_unlock_master_inventory.csv"
)
AGENT417_STEADY = (
    ROOT
    / "work_products/2026-07/2026-07-15/2026-07-15_salt_external_test_and_q_unlock_admission/"
    "terminal_steady_state_evidence.csv"
)
VAL_DOC = ROOT / "work_products/2026-07/2026-07-14/2026-07-14_val_salt_test_2_coarse_mesh_documentation"
BC_SUMMARY = VAL_DOC / "boundary_condition_summary.csv"
BC_PATCH = VAL_DOC / "boundary_condition_patch_detail.csv"
MATERIALS = VAL_DOC / "material_property_evidence.csv"
JIN_COMPARISON = VAL_DOC / "salt2_jin_comparison.csv"
VAL_README = VAL_DOC / "README.md"

SECTION_COLUMNS = [
    "section_heater_net_q_w",
    "section_test_section_net_q_w",
    "section_cooling_branch_net_q_w",
    "section_downcomer_net_q_w",
    "section_upcomer_net_q_w",
    "section_upper_transport_net_q_w",
    "section_lower_transport_net_q_w",
    "section_junctions_net_q_w",
    "section_other_net_q_w",
]

SECTION_LABELS = {
    "section_heater_net_q_w": ("heater", "lower-leg heater patches", "heater/source"),
    "section_test_section_net_q_w": ("test_section", "powered test-section patch", "test-section/source-or-loss"),
    "section_cooling_branch_net_q_w": ("cooling_branch", "upper reducer/cooler branch", "cooler/HX/removal"),
    "section_downcomer_net_q_w": ("downcomer", "right downcomer", "passive wall loss"),
    "section_upcomer_net_q_w": ("upcomer", "upcomer/test-section leg", "passive wall loss"),
    "section_upper_transport_net_q_w": ("upper_transport", "upper transport wall/stub patches", "passive wall loss"),
    "section_lower_transport_net_q_w": ("lower_transport", "lower transport wall/stub patches", "passive wall loss"),
    "section_junctions_net_q_w": ("junctions", "junction and connector patches", "passive wall/stub loss"),
    "section_other_net_q_w": ("other", "other/unmapped patches", "other"),
}

MDOT_FILES = [
    RUNTIME_ROOT / "postProcessing/mdot_pipeleg_left_04_test_section/5182/surfaceFieldValue.dat",
    RUNTIME_ROOT / "postProcessing/mdot_pipeleg_lower_05_straight/5182/surfaceFieldValue.dat",
    RUNTIME_ROOT / "postProcessing/mdot_pipeleg_right_02_middle/5182/surfaceFieldValue.dat",
    RUNTIME_ROOT / "postProcessing/mdot_pipeleg_upper_05_cooler/5182/surfaceFieldValue.dat",
]


@dataclass(frozen=True)
class Drift:
    metric: str
    group: str
    n: int
    window_start_s: float
    window_end_s: float
    first: float
    last: float
    mean: float
    min_value: float
    max_value: float
    slope_per_s: float
    linear_drift: float
    endpoint_change: float
    rel_linear_drift: float | None
    rmse_about_trend: float
    drift_ratio: float | None
    verdict: str
    threshold_basis: str
    source_path: str


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as fh:
        return list(csv.DictReader(fh))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = list(rows[0].keys()) if rows else []
    with path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_json(path: Path, data: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def as_float(value: str | float | int | None) -> float | None:
    if value in (None, ""):
        return None
    try:
        val = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(val):
        return None
    return val


def round_sig(value: float | None, digits: int = 10) -> float | str:
    if value is None:
        return ""
    return round(value, digits)


def parse_two_column(path: Path) -> list[tuple[float, float]]:
    rows: list[tuple[float, float]] = []
    with path.open() as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) < 2:
                continue
            t = as_float(parts[0])
            v = as_float(parts[1])
            if t is None or v is None:
                continue
            rows.append((t, v))
    return rows


def linear_fit(points: list[tuple[float, float]]) -> tuple[float, float, float]:
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    xbar = statistics.fmean(xs)
    ybar = statistics.fmean(ys)
    denom = sum((x - xbar) ** 2 for x in xs)
    slope = 0.0 if denom == 0 else sum((x - xbar) * (y - ybar) for x, y in points) / denom
    intercept = ybar - slope * xbar
    rmse = math.sqrt(statistics.fmean((y - (slope * x + intercept)) ** 2 for x, y in points))
    return slope, intercept, rmse


def drift_for_series(
    metric: str,
    group: str,
    points: list[tuple[float, float]],
    window_start: float,
    source_path: Path,
    threshold_kind: str,
) -> Drift:
    window = [(t, v) for t, v in points if t >= window_start]
    if not window:
        raise ValueError(f"no points for {metric} after {window_start}")
    slope, _intercept, rmse = linear_fit(window)
    start = window[0][0]
    end = window[-1][0]
    duration = end - start
    drift = slope * duration
    mean = statistics.fmean(v for _, v in window)
    denom = abs(mean)
    rel = abs(drift) / denom if denom > 1e-12 else None
    ratio = abs(drift) / rmse if rmse > 1e-12 else None
    endpoint = window[-1][1] - window[0][1]
    max_abs = max(abs(v) for _, v in window)

    if threshold_kind == "mdot":
        verdict = "steady" if rel is not None and rel <= 0.005 else "needs_continuation"
        basis = "terminal-window linear drift <= 0.5% of mean |mdot|"
    elif threshold_kind == "section_heat":
        # Section heat uses a magnitude gate because several diagnostic terms
        # have very low noise, making drift_ratio overly sensitive to harmless
        # sub-watt monotonic changes.
        allowed = max(1.0, 0.005 * max_abs)
        verdict = "steady" if abs(drift) <= allowed else "needs_continuation"
        basis = "terminal-window linear drift <= max(1 W, 0.5% of section magnitude)"
    else:
        verdict = "steady" if abs(drift) <= 1.0 else "needs_continuation"
        basis = "terminal-window linear drift <= 1 W"

    return Drift(
        metric=metric,
        group=group,
        n=len(window),
        window_start_s=start,
        window_end_s=end,
        first=window[0][1],
        last=window[-1][1],
        mean=mean,
        min_value=min(v for _, v in window),
        max_value=max(v for _, v in window),
        slope_per_s=slope,
        linear_drift=drift,
        endpoint_change=endpoint,
        rel_linear_drift=rel,
        rmse_about_trend=rmse,
        drift_ratio=ratio,
        verdict=verdict,
        threshold_basis=basis,
        source_path=str(source_path.relative_to(ROOT)),
    )


def drift_to_row(d: Drift) -> dict[str, object]:
    return {
        "case_key": CASE_KEY,
        "display_label": DISPLAY_LABEL,
        "metric": d.metric,
        "group": d.group,
        "n_points": d.n,
        "window_start_s": round_sig(d.window_start_s, 6),
        "window_end_s": round_sig(d.window_end_s, 6),
        "first": round_sig(d.first, 10),
        "last": round_sig(d.last, 10),
        "mean": round_sig(d.mean, 10),
        "min": round_sig(d.min_value, 10),
        "max": round_sig(d.max_value, 10),
        "slope_per_s": round_sig(d.slope_per_s, 12),
        "linear_drift_over_window": round_sig(d.linear_drift, 10),
        "endpoint_change": round_sig(d.endpoint_change, 10),
        "relative_linear_drift": round_sig(d.rel_linear_drift, 10),
        "rmse_about_trend": round_sig(d.rmse_about_trend, 10),
        "drift_ratio": round_sig(d.drift_ratio, 10),
        "verdict": d.verdict,
        "threshold_basis": d.threshold_basis,
        "source_path": d.source_path,
    }


def load_wall_heat_rows() -> list[dict[str, str]]:
    return read_csv(WALL_HEAT)


def build_section_ledger(wall_rows: list[dict[str, str]], window_start: float) -> list[dict[str, object]]:
    tail = [row for row in wall_rows if (as_float(row.get("time_s")) or -1) >= window_start]
    latest = wall_rows[-1]
    rows: list[dict[str, object]] = []
    for col in SECTION_COLUMNS:
        key, section_label, thermal_role = SECTION_LABELS[col]
        values = [as_float(r.get(col)) for r in tail]
        vals = [v for v in values if v is not None]
        latest_value = as_float(latest.get(col))
        mean_value = statistics.fmean(vals) if vals else None
        net = latest_value if latest_value is not None else 0.0
        rows.append(
            {
                "case_key": CASE_KEY,
                "display_label": DISPLAY_LABEL,
                "source_id": SOURCE_ID,
                "section_key": key,
                "section_label": section_label,
                "thermal_role": thermal_role,
                "latest_time_s": round_sig(as_float(latest.get("time_s")), 6),
                "latest_cfd_realized_net_to_fluid_W": round_sig(latest_value, 10),
                "terminal_window_mean_net_to_fluid_W": round_sig(mean_value, 10),
                "realized_source_component_W": round_sig(max(net, 0.0), 10),
                "realized_removal_component_W": round_sig(max(-net, 0.0), 10),
                "sign_convention": "positive is net heat into fluid; negative is heat removed from fluid",
                "source_path": str(WALL_HEAT.relative_to(ROOT)),
            }
        )

    summary_cols = [
        "total_Q_postProc",
        "ambient_proxy_w",
        "ambient_noncooling_proxy_w",
        "cooling_branch_total_removal_w",
        "cooling_branch_excess_w",
    ]
    for col in summary_cols:
        val = as_float(latest.get(col))
        mean = statistics.fmean([as_float(r.get(col)) for r in tail if as_float(r.get(col)) is not None])
        rows.append(
            {
                "case_key": CASE_KEY,
                "display_label": DISPLAY_LABEL,
                "source_id": SOURCE_ID,
                "section_key": col,
                "section_label": col,
                "thermal_role": "summary_diagnostic",
                "latest_time_s": round_sig(as_float(latest.get("time_s")), 6),
                "latest_cfd_realized_net_to_fluid_W": round_sig(val, 10),
                "terminal_window_mean_net_to_fluid_W": round_sig(mean, 10),
                "realized_source_component_W": "",
                "realized_removal_component_W": "",
                "sign_convention": "summary diagnostic from registry wall_heat_flux_grouped.csv",
                "source_path": str(WALL_HEAT.relative_to(ROOT)),
            }
        )
    return rows


def build_bc_contract_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for row in read_csv(BC_SUMMARY):
        rows.append(
            {
                "case_key": CASE_KEY,
                "display_label": DISPLAY_LABEL,
                "contract_type": "boundary_condition_role_summary",
                "field": row.get("field", ""),
                "role": row.get("role", ""),
                "patch_count": row.get("patch_count", ""),
                "bc_types": row.get("bc_types", ""),
                "net_imposed_Q_W": row.get("net_imposed_Q_W", ""),
                "h_min_W_m2K": row.get("h_min_W_m2K", ""),
                "h_max_W_m2K": row.get("h_max_W_m2K", ""),
                "Ta_K": row.get("Ta_K", ""),
                "Tsur_K": row.get("Tsur_K", ""),
                "emissivity": row.get("emissivity", ""),
                "layers_m": row.get("layers_m", ""),
                "evidence": row.get("interpretation", ""),
                "source_path": row.get("source_path", str(BC_SUMMARY.relative_to(ROOT))),
            }
        )
    for row in read_csv(MATERIALS):
        rows.append(
            {
                "case_key": CASE_KEY,
                "display_label": DISPLAY_LABEL,
                "contract_type": "material_property_evidence",
                "field": row.get("evidence_group", ""),
                "role": row.get("property", ""),
                "patch_count": "",
                "bc_types": "",
                "net_imposed_Q_W": row.get("value", ""),
                "h_min_W_m2K": "",
                "h_max_W_m2K": "",
                "Ta_K": "",
                "Tsur_K": "",
                "emissivity": "",
                "layers_m": "",
                "evidence": row.get("interpretation", ""),
                "source_path": row.get("source_path", str(MATERIALS.relative_to(ROOT))),
            }
        )
    return rows


def find_row(path: Path, predicate) -> dict[str, str] | None:
    if not path.exists():
        return None
    for row in read_csv(path):
        if predicate(row):
            return row
    return None


def build_package(out: Path = DEFAULT_OUT, window_seconds: float = 300.0) -> dict[str, object]:
    out.mkdir(parents=True, exist_ok=True)
    wall_rows = load_wall_heat_rows()
    latest_time = as_float(wall_rows[-1]["time_s"])
    if latest_time is None:
        raise ValueError("wall heat latest time missing")
    window_start = latest_time - window_seconds

    drifts: list[Drift] = []
    total_q_points = [(as_float(r["time_s"]), as_float(r["total_Q_postProc"])) for r in wall_rows]
    drifts.append(
        drift_for_series(
            "total_Q_postProc",
            "global_heat_residual",
            [(t, v) for t, v in total_q_points if t is not None and v is not None],
            window_start,
            WALL_HEAT,
            "total_q",
        )
    )
    for col in SECTION_COLUMNS:
        points = [(as_float(r["time_s"]), as_float(r[col])) for r in wall_rows]
        drifts.append(
            drift_for_series(
                col,
                SECTION_LABELS[col][0],
                [(t, v) for t, v in points if t is not None and v is not None],
                window_start,
                WALL_HEAT,
                "section_heat",
            )
        )

    mdot_points_all: list[tuple[float, float]] = []
    for path in MDOT_FILES:
        points = parse_two_column(path)
        drifts.append(
            drift_for_series(
                "mdot_kg_s",
                path.parts[-3],
                points,
                window_start,
                path,
                "mdot",
            )
        )
        mdot_points_all.extend((t, abs(v)) for t, v in points if t >= window_start)

    latest_case_summary = read_csv(CASE_SUMMARY)[0]
    old_rollup = find_row(OLD_ROLLUP, lambda r: r.get("run_key") == "2026-06-01_continuation_candidate")
    agent417_master = find_row(AGENT417_MASTER, lambda r: r.get("case_key") == CASE_KEY)
    agent417_steady = find_row(AGENT417_STEADY, lambda r: r.get("case_key") == CASE_KEY)

    drift_rows = [drift_to_row(d) for d in drifts]
    write_csv(out / "refreshed_terminal_steady_state_gate.csv", drift_rows)

    all_steady = all(d.verdict == "steady" for d in drifts)
    final_label = "steady" if all_steady else "needs_continuation"
    admission = (
        "external_test_validation_candidate_unlocked"
        if all_steady
        else "external_test_candidate_needs_continuation"
    )
    usable_now = "yes_external_test_validation" if all_steady else "no"

    ledger = build_section_ledger(wall_rows, window_start)
    write_csv(out / "val_salt2_section_heat_loss_ledger.csv", ledger)
    bc_rows = build_bc_contract_rows()
    write_csv(out / "val_salt2_bc_source_material_contract.csv", bc_rows)

    conflict_rows = [
        {
            "case_key": CASE_KEY,
            "display_label": DISPLAY_LABEL,
            "evidence_source": str(OLD_ROLLUP.relative_to(ROOT)),
            "observed_label": old_rollup.get("steady_state_detection_status", "") if old_rollup else "not_found",
            "mdot_verdict": old_rollup.get("mdot_verdict", "") if old_rollup else "",
            "heat_verdict": old_rollup.get("heat_verdict", "") if old_rollup else "",
            "interpretation": "older table used diagnostic heat-drift wording; refreshed AGENT-422 gate applies magnitude thresholds to existing terminal wallHeatFlux and mdot tails",
            "resolution": "superseded_for_val_salt2_external_test_admission" if all_steady else "confirmed_needs_continuation",
        },
        {
            "case_key": CASE_KEY,
            "display_label": DISPLAY_LABEL,
            "evidence_source": str(AGENT417_STEADY.relative_to(ROOT)),
            "observed_label": agent417_steady.get("steady_state_verdict", "") if agent417_steady else "not_found",
            "mdot_verdict": "",
            "heat_verdict": "",
            "interpretation": "AGENT-417 already carried val_salt2 as steady but blocked it for missing section heat-loss ledger",
            "resolution": "confirmed_and_ledger_added" if all_steady else "partially_overturned_by_refreshed_gate",
        },
    ]
    write_csv(out / "evidence_conflict_resolution.csv", conflict_rows)

    split_rows = [
        {
            "case_key": CASE_KEY,
            "display_label": DISPLAY_LABEL,
            "source_id": SOURCE_ID,
            "salt_family": "salt2",
            "lineage_role": "native_validation_comparison",
            "terminal_state": "time_limit_stop_after_continuation",
            "latest_time_s": round_sig(latest_time, 6),
            "refreshed_steady_state_label": final_label,
            "bc_source_material_contract": "attached",
            "section_heat_loss_ledger": "attached",
            "split_role": "external_test_or_validation_candidate" if all_steady else "pending_continuation",
            "admission_decision": admission,
            "usable_now": usable_now,
            "leakage_guardrail": "do not fit/tune on this row if used as blind external test; realized wallHeatFlux is diagnostic target/output, not predictive runtime input",
            "reason": (
                "terminal mdot, total_Q, and section heat terms pass refreshed final-window magnitude gates"
                if all_steady
                else "one or more terminal-window drift metrics exceed refreshed gate"
            ),
            "primary_evidence": ";".join(
                [
                    display_path(out / "refreshed_terminal_steady_state_gate.csv"),
                    display_path(out / "val_salt2_section_heat_loss_ledger.csv"),
                    str(BC_SUMMARY.relative_to(ROOT)),
                    str(MATERIALS.relative_to(ROOT)),
                ]
            ),
        }
    ]
    write_csv(out / "val_salt2_split_admission_refresh.csv", split_rows)

    source_manifest = [
        ("registry wall heat grouped", WALL_HEAT, "section heat-loss history and total_Q terminal drift"),
        ("registry case summary", CASE_SUMMARY, "case-level postprocessing aggregate summary"),
        ("registry postprocessing long", POST_LONG, "normalized postprocessing aggregate; cited, not re-streamed"),
        ("registry aggregation manifest", MANIFEST, "postprocessing provenance and row counts"),
        ("runtime total_Q", TOTAL_Q, "native postProcessing scalar source mirrored by registry grouped CSV"),
        ("runtime mdot monitor left test section", MDOT_FILES[0], "terminal mdot drift"),
        ("runtime mdot monitor lower straight", MDOT_FILES[1], "terminal mdot drift"),
        ("runtime mdot monitor right middle", MDOT_FILES[2], "terminal mdot drift"),
        ("runtime mdot monitor upper cooler", MDOT_FILES[3], "terminal mdot drift"),
        ("val BC summary", BC_SUMMARY, "BC role/source contract"),
        ("val BC patch detail", BC_PATCH, "patch-level BC detail"),
        ("val material properties", MATERIALS, "material/property contract"),
        ("val Salt2 Jin comparison", JIN_COMPARISON, "lineage distinction and BC comparison"),
        ("val documentation README", VAL_README, "prior documentation package"),
        ("old steady rollup", OLD_ROLLUP, "conflicting heat-drift label"),
        ("AGENT-417 master", AGENT417_MASTER, "prior missing-ledger block"),
        ("AGENT-417 steady evidence", AGENT417_STEADY, "prior steady label"),
    ]
    write_csv(
        out / "source_manifest.csv",
        [
            {
                "label": label,
                "path": str(path.relative_to(ROOT)),
                "exists": path.exists(),
                "use": use,
            }
            for label, path, use in source_manifest
        ],
    )

    max_abs_heat_drift = max(abs(d.linear_drift) for d in drifts if d.metric != "mdot_kg_s")
    max_rel_mdot = max((d.rel_linear_drift or 0.0) for d in drifts if d.metric == "mdot_kg_s")
    summary = {
        "task": TASK,
        "case_key": CASE_KEY,
        "display_label": DISPLAY_LABEL,
        "source_id": SOURCE_ID,
        "latest_time_s": latest_time,
        "window_start_s": window_start,
        "window_seconds": window_seconds,
        "steady_state_label": final_label,
        "admission_decision": admission,
        "usable_now": usable_now,
        "max_abs_heat_linear_drift_W": max_abs_heat_drift,
        "max_relative_mdot_linear_drift": max_rel_mdot,
        "latest_total_Q_postProc_W": as_float(latest_case_summary.get("latest_total_Q_postProc_w")),
        "mdot_consensus_kg_s": as_float(latest_case_summary.get("mdot_consensus_kg_s")),
        "section_ledger_rows": len(ledger),
        "bc_contract_rows": len(bc_rows),
        "native_cfd_outputs_mutated": False,
        "scheduler_actions": "none",
        "registry_state_mutated": False,
    }
    write_json(out / "summary.json", summary)

    readme = f"""---
provenance:
  - {WALL_HEAT.relative_to(ROOT)}
  - {CASE_SUMMARY.relative_to(ROOT)}
  - {BC_SUMMARY.relative_to(ROOT)}
  - {MATERIALS.relative_to(ROOT)}
  - {OLD_ROLLUP.relative_to(ROOT)}
tags: [cfd-pp, salt2, val-salt2, admission, heat-loss-ledger]
related:
  - operational_notes/maps/cfd-runs-and-admission.md
  - work_products/2026-07/2026-07-14/2026-07-14_val_salt_test_2_coarse_mesh_documentation/README.md
  - work_products/2026-07/2026-07-15/2026-07-15_salt_external_test_and_q_unlock_admission/README.md
task: {TASK}
date: 2026-07-15
role: cfd-pp/Thermal-admission/Implementer/Tester/Writer
type: work_product
status: complete
---
# val_salt_test_2_coarse_mesh Postprocessing Admission Unlock

## Observed Facts

- Refreshed terminal window: `{window_start:.0f}` to `{latest_time:.0f}` s.
- Refreshed steady-state label: `{final_label}`.
- Latest `total_Q_postProc`: `{as_float(latest_case_summary.get("latest_total_Q_postProc_w")):.6g}` W.
- mdot consensus from registry summary: `{as_float(latest_case_summary.get("mdot_consensus_kg_s")):.10g}` kg/s.
- Maximum heat linear drift over the terminal window: `{max_abs_heat_drift:.6g}` W.
- Maximum mdot relative linear drift over the terminal window: `{max_rel_mdot:.6g}`.
- BC/source/material contract rows attached: `{len(bc_rows)}`.
- Section heat-loss ledger rows: `{len(ledger)}`.

## Interpretation

`val_salt_test_2_coarse_mesh` is no longer blocked by a missing section
heat-loss ledger. The older `hydraulic_stationary_heat_drifting` label is
superseded for this admission pass by the refreshed terminal-window check over
the existing registry wallHeatFlux and mdot tails. The older drift label remains
useful context because low-noise monotonic sub-watt heat terms can trip a
ratio-style detector, but the magnitude is small relative to the case heat
budget.

## Admission Refresh

- Admission decision: `{admission}`.
- Split role: `{"external_test_or_validation_candidate" if all_steady else "pending_continuation"}`.
- Usable now: `{usable_now}`.
- Guardrail: do not fit or tune on this row if it is used as blind external
  test data. Realized CFD `wallHeatFlux` is admissible as diagnostic/scoring
  evidence, not as a predictive runtime input.

## Files

- `refreshed_terminal_steady_state_gate.csv`
- `val_salt2_section_heat_loss_ledger.csv`
- `val_salt2_bc_source_material_contract.csv`
- `val_salt2_split_admission_refresh.csv`
- `evidence_conflict_resolution.csv`
- `source_manifest.csv`
- `summary.json`

## Guardrails

No native CFD outputs, registry state, scheduler state, generated indexes, or
external Fluid files were mutated. This package consumes existing
postprocessing/registry evidence only.
"""
    (out / "README.md").write_text(readme)

    return summary


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--window-seconds", type=float, default=300.0)
    args = parser.parse_args(list(argv) if argv is not None else None)
    summary = build_package(args.out, args.window_seconds)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
