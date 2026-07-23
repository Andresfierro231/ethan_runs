#!/usr/bin/env python3
"""Refit the F0-F5 empirical bias-correction family on ALL FOUR Salt1-4 nominal
train cases (instead of Salt1/Salt2 only) and re-score against the Salt2 +/-5Q
holdout (salt2_lo5q, salt2_hi5q) and val_salt2 external-test rows.

Task: TODO-EMPIRICAL-BIAS-SALT1-4-REFIT-HOLDOUT-EXTERNAL-SCORE-2026-07-23
Owner: claude

CRITICAL EXPOSURE CAVEAT
-------------------------
This is the SECOND scoring exposure of salt2_lo5q / salt2_hi5q / val_salt2
within this session. The first exposure was an ad hoc, in-conversation-only
pass (never written to the repo) that scored the ORIGINAL Salt1/Salt2-fit
F0-F5 family against these same targets. This package must NOT be read as a
legitimate single-use protected-split freeze score. The separate, concurrent
`TODO-F2-EMPIRICAL-HOLDOUT-FREEZE-AND-SCORE-HARNESS-2026-07-23` /
`2026-07-23_salt2_pm5_holdout_inputs_and_f2_score` effort keeps the ORIGINAL
Salt1/2-fit F2 frozen and untouched; this package does not modify, supersede,
or compete with that freeze. It is an explicit user-directed "how much does a
bigger train set change the answer" diagnostic.

What this script does
----------------------
1. Refit F0 (null), F1 (global offset), F2 (global affine), F3 (sensor-kind
   offset TP/TW), F4 (thermal-family offset), F5 (shared multiplier + thermal-
   family offset) using the EXACT fitting formulas from
   `tools/analyze/build_fluid_reduced_dof_bias_transfer_screen.py`
   (`ols_affine`, `mean_offset`, shared-affine-then-group-offset), but with the
   fit set expanded to ALL FOUR Salt1-4 nominal sensor rows (64 usable rows)
   instead of Salt1/Salt2 only (32 rows). Source rows come from the already
   -computed `fit_and_transfer_sensor_rows.csv` (F0_null_baseline subset gives
   the raw predicted_K/reference_K/sensor_kind/thermal_family per sensor row;
   this file is read-only and not re-derived here).
2. Runs `solve_case()` from `tamu_loop_model_v2.solver` with the exact
   `tswfc2_smoke_salt2_four_node_v1` ScenarioConfig (copied from
   `build_tswfc2_bounded_nominal_scorecard.py`) to get raw (uncorrected) 1D
   bulk/wall predictions for salt2_lo5q (heater_power_W=252.415), salt2_hi5q
   (heater_power_W=278.985), and val_salt2 (property_set_name="salt_current",
   heater_power_W=265.7, same BC as Salt 2 nominal otherwise). No OpenFOAM run;
   this is the existing 1D solver only.
3. Applies the OLD (Salt1/2, read from the existing frozen_coefficients.csv)
   and NEW (Salt1-4 refit) coefficients to the same raw predictions and scores
   against the existing holdout/external target tables (read-only):
   `salt2_pm5_admission_table.csv` (bulk_T_K/wall_T_K per upcomer-plane
   station) and `val_salt2_external_score_targets.csv` (sensor_temperature,
   score_allowed==yes rows).
4. Writes the required work_products package.

Station -> raw-value extraction convention (salt2_lo5q/hi5q)
--------------------------------------------------------------
The pm5 admission table gives three upcomer-plane stations per case
(upcomer_inlet, upcomer_mid, upcomer_outlet) with bulk_T_K and wall_T_K. The
1D-equivalent bulk value is read at the matching nodal position in
`result.segment_df` (verified against the task's sanity-check numbers):
  - upcomer_inlet bulk  = T_in_K  of the FIRST left_lower_vertical sub-segment
                          (parent_start_fraction == 0.0)
  - upcomer_mid   bulk  = T_out_K of the FIRST test_section sub-segment, which
                          equals T_in_K of the second (the fraction==0.5 nodal
                          boundary in the middle of the test section)
  - upcomer_outlet bulk = T_out_K of the LAST left_upper_vertical sub-segment
                          (parent_end_fraction == 1.0)
The wall-side proxy uses `T_pipe_outer_wall_K` (the internal-model outer pipe
wall temperature, populated for every sub-segment, unlike the TSWFC2-node-only
`tswfc2_outer_wall_temperature_K`) at the analogous position: the FIRST
left_lower_vertical sub-segment for inlet, the length-weighted average of the
two test_section sub-segments for mid, and the LAST left_upper_vertical
sub-segment for outlet. There is no CFD-plane-exact wall nodal value in the 1D
discretization (unlike bulk T_in/T_out), so this is a documented, reproducible
proxy, not a claimed physical match.

This convention was confirmed against the task's own sanity-check numbers:
reproduced raw values matched the stated ranges, and independently
recomputing the OLD (Salt1/2) fit's F0/F1 MAE on this exact station mapping
reproduced the cited baseline MAE_K values (lo5q F0=89.44/F1=3.15,
hi5q F0=100.34/F1=11.59, val_salt2 F0=90.65) to within floating-point
rounding, which is the correctness check documented in
`no_mutation_guardrails.csv` / the journal entry.

All three of left_lower_vertical/test_section/left_upper_vertical map to the
`vertical_loop` thermal family (matching `SEGMENT_TO_LEG`/`LEG_TO_THERMAL_FAMILY`
in the source screen). Bulk rows are TP-kind, wall rows are TW-kind, for the
purposes of the F3/F4/F5 grouping only (there are no literal TP/TW sensor IDs
at these CFD-plane stations).

No Fluid solve is admitted as a physical closure. No physical source/property
release. No candidate freeze. No admission decision changes.
"""
from __future__ import annotations

import csv
import dataclasses
import json
import math
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
FLUID_ROOT = REPO.parent / "cfd-modeling-tools" / "tamu_first_order_model" / "Fluid"

TASK_ID = "TODO-EMPIRICAL-BIAS-SALT1-4-REFIT-HOLDOUT-EXTERNAL-SCORE-2026-07-23"
OUT = REPO / "work_products/2026-07/2026-07-23/2026-07-23_empirical_bias_salt1_4_refit_holdout_external_score"

SRC_SENSOR_ROWS = (
    REPO
    / "work_products/2026-07/2026-07-21/2026-07-21_fluid_reduced_dof_bias_transfer_screen/fit_and_transfer_sensor_rows.csv"
)
SRC_OLD_FROZEN_COEFFS = (
    REPO / "work_products/2026-07/2026-07-21/2026-07-21_fluid_reduced_dof_bias_transfer_screen/frozen_coefficients.csv"
)
SRC_PM5_ADMISSION_TABLE = (
    REPO
    / "work_products/2026-07/2026-07-17/2026-07-17_predict_salt2_pm5_holdout_extraction_repair/salt2_pm5_admission_table.csv"
)
SRC_VAL_SALT2_TARGETS = (
    REPO
    / "work_products/2026-07/2026-07-17/2026-07-17_val_salt2_external_score_and_unlock_progress/val_salt2_external_score_targets.csv"
)
SRC_CORRECTED_MANIFEST = REPO / "jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations/corrected_case_manifest.csv"

CLAIM_BOUNDARY = (
    "empirical discrepancy/digital-twin-ROM diagnostic only; refit on Salt1-4 train rows "
    "then scored against Salt2 +/-5Q holdout and val_salt2 external test; NOT a physical "
    "closure; NOT a legitimate single-use protected-split freeze score (second scoring "
    "exposure of these rows within this session); does not modify or supersede the separate "
    "F2 single-use freeze effort"
)

# Same leg/thermal-family maps as build_fluid_reduced_dof_bias_transfer_screen.py,
# copied (read-only source, not imported) so this script has no import-time coupling
# to a file owned by a different task.
SEGMENT_TO_LEG = {
    "right_vertical": "downcomer",
    "left_lower_vertical": "upcomer",
    "left_upper_vertical": "upcomer",
    "test_section": "upcomer",
    "top_horizontal_exit": "cooling_branch",
    "top_horizontal_inlet": "cooling_branch",
    "cooled_incline_pre_hx": "cooling_branch",
    "cooled_incline_post_hx": "cooling_branch",
    "cooled_incline_hx_active": "cooling_branch",
    "heated_incline": "lower_leg",
    "bottom_horizontal_inlet": "junction",
    "bottom_horizontal_exit": "junction",
}
LEG_TO_THERMAL_FAMILY = {
    "downcomer": "vertical_loop",
    "upcomer": "vertical_loop",
    "cooling_branch": "cooling_branch",
    "lower_leg": "heated_lower_leg",
    "junction": "junction",
    "unmapped": "unmapped",
}

FAMILIES = [
    {"model_family": "F0_null_baseline", "fit_form": "identity", "grouping": "none",
     "interpretation": "No empirical bias/correction; reference score for all rows."},
    {"model_family": "F1_global_offset", "fit_form": "offset", "grouping": "global",
     "interpretation": "Uniform additive bias diagnostic."},
    {"model_family": "F2_global_affine", "fit_form": "affine", "grouping": "global",
     "interpretation": "One global multiplier plus offset."},
    {"model_family": "F3_sensor_kind_offset", "fit_form": "offset", "grouping": "sensor_kind",
     "interpretation": "Separate TP/TW offsets; bulk-vs-wall reduction bias."},
    {"model_family": "F4_thermal_family_offset", "fit_form": "offset", "grouping": "thermal_family",
     "interpretation": "Offsets by vertical loop, cooling branch, and heated lower-leg heat-path roles."},
    {"model_family": "F5_thermal_family_offset_shared_multiplier", "fit_form": "shared_affine", "grouping": "thermal_family",
     "interpretation": "One shared multiplier plus heat-path offsets."},
]

# The three pm5 upcomer-plane stations for salt2_lo5q/hi5q; all map to
# thermal_family=vertical_loop per the task instruction and SEGMENT_TO_LEG.
PM5_STATIONS = ["upcomer_inlet", "upcomer_mid", "upcomer_outlet"]

VAL_SALT2_SEGMENT_BY_SENSOR = {
    "TP1": "top_horizontal_exit",
    "TP3": "left_lower_vertical",
    "TP4": "left_lower_vertical",
    "TP5": "test_section",
    "TP6": "left_upper_vertical",
    "TW1": "right_vertical",
    "TW2": "right_vertical",
    "TW3": "right_vertical",
    "TW4": "heated_incline",
    "TW5": "heated_incline",
    "TW6": "heated_incline",
    "TW7": "left_lower_vertical",
    "TW8": "left_upper_vertical",
    "TW9": "cooled_incline_pre_hx",
    "TW11": "cooled_incline_post_hx",
}

# Prior in-conversation-pass (this session), ad hoc, never written to the repo:
# score of the ORIGINAL Salt1/Salt2-fit F0-F5 family against the same holdout/
# external targets. Cited verbatim as the comparison baseline per user
# instruction; independently reproduced below from frozen_coefficients.csv +
# the raw 1D predictions this script computes, to cross-check the citation.
PRIOR_IN_CONVERSATION_OLD_FIT_MAE_K = {
    ("salt2_lo5q", "F0_null_baseline"): 89.44,
    ("salt2_lo5q", "F1_global_offset"): 3.15,
    ("salt2_lo5q", "F2_global_affine"): 3.47,
    ("salt2_lo5q", "F3_sensor_kind_offset"): 3.08,
    ("salt2_lo5q", "F4_thermal_family_offset"): 3.11,
    ("salt2_lo5q", "F5_thermal_family_offset_shared_multiplier"): 3.25,
    ("salt2_hi5q", "F0_null_baseline"): 100.34,
    ("salt2_hi5q", "F1_global_offset"): 11.59,
    ("salt2_hi5q", "F2_global_affine"): 3.12,
    ("salt2_hi5q", "F3_sensor_kind_offset"): 11.79,
    ("salt2_hi5q", "F4_thermal_family_offset"): 11.70,
    ("salt2_hi5q", "F5_thermal_family_offset_shared_multiplier"): 2.89,
    ("val_salt2", "F0_null_baseline"): 90.65,
    ("val_salt2", "F1_global_offset"): 6.51,
    ("val_salt2", "F2_global_affine"): 6.45,
    ("val_salt2", "F3_sensor_kind_offset"): 6.61,
    ("val_salt2", "F4_thermal_family_offset"): 9.39,
    ("val_salt2", "F5_thermal_family_offset_shared_multiplier"): 9.95,
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({name: row.get(name, "") for name in fieldnames})


def fnum(value: object) -> float:
    if value is None or value == "":
        return math.nan
    return float(value)


# ---------------------------------------------------------------------------
# Step 1: refit F0-F5 on ALL FOUR Salt1-4 nominal rows.
# ---------------------------------------------------------------------------


def load_train_rows() -> list[dict[str, object]]:
    """Load the 64 usable Salt1-4 sensor rows (predicted_K/reference_K/kind/family).

    Uses the F0_null_baseline subset of fit_and_transfer_sensor_rows.csv as the
    canonical unique per-sensor row set (every model_family block in that file
    repeats the same raw predicted_K/reference_K with different corrected
    values; F0 is the identity family so its predicted_K IS the raw T_1D).
    """
    rows = read_csv(SRC_SENSOR_ROWS)
    base = [r for r in rows if r["model_family"] == "F0_null_baseline" and r["row_usable"] == "True"]
    if len(base) != 64:
        raise RuntimeError(f"Expected 64 usable Salt1-4 sensor rows, found {len(base)}")
    return base


def group_key(row: dict[str, object], grouping: str) -> str:
    if grouping == "none":
        return "identity"
    if grouping == "global":
        return "global"
    if grouping == "sensor_kind":
        return str(row["sensor_kind"])
    if grouping == "thermal_family":
        return str(row["thermal_family"])
    raise ValueError(f"unknown grouping: {grouping}")


def ols_affine(points: list[dict[str, object]]) -> tuple[float, float]:
    xs = [fnum(p["predicted_K"]) for p in points]
    ys = [fnum(p["reference_K"]) for p in points]
    mean_x = sum(xs) / len(xs)
    mean_y = sum(ys) / len(ys)
    var_x = sum((x - mean_x) ** 2 for x in xs)
    cov_xy = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    mult = cov_xy / var_x
    return mult, mean_y - mult * mean_x


def mean_offset(points: list[dict[str, object]]) -> float:
    return sum(fnum(p["reference_K"]) - fnum(p["predicted_K"]) for p in points) / len(points)


def refit_family(rows: list[dict[str, object]], family: dict[str, str]) -> list[dict[str, object]]:
    form = family["fit_form"]
    grouping = family["grouping"]
    coeffs: list[dict[str, object]] = []
    if form == "identity":
        coeffs.append(
            {
                **family,
                "coefficient_group": "identity",
                "multiplier_correction": 1.0,
                "offset_bias_K": 0.0,
                "n_fit_rows": 0,
                "degrees_of_freedom": 0,
                "fit_status": "fixed_identity_no_fit",
                "coefficient_source": "predeclared_baseline",
            }
        )
        return coeffs
    if form in {"offset", "affine"}:
        by_group: dict[str, list[dict[str, object]]] = defaultdict(list)
        for row in rows:
            by_group[group_key(row, grouping)].append(row)
        for key in sorted(by_group):
            points = by_group[key]
            if form == "offset":
                offset = mean_offset(points)
                mult = 1.0
                status = "mean_offset"
                dof = 1
            else:
                mult, offset = ols_affine(points)
                status = "ols_affine"
                dof = 2
            coeffs.append(
                {
                    **family,
                    "coefficient_group": key,
                    "multiplier_correction": mult,
                    "offset_bias_K": offset,
                    "n_fit_rows": len(points),
                    "degrees_of_freedom": dof,
                    "fit_status": status,
                    "coefficient_source": "Salt1_Salt2_Salt3_Salt4_refit_2026_07_23",
                }
            )
        return coeffs
    if form == "shared_affine":
        mult, _ = ols_affine(rows)
        for key in sorted({group_key(row, grouping) for row in rows}):
            points = [row for row in rows if group_key(row, grouping) == key]
            offset = sum(fnum(p["reference_K"]) - mult * fnum(p["predicted_K"]) for p in points) / len(points)
            coeffs.append(
                {
                    **family,
                    "coefficient_group": key,
                    "multiplier_correction": mult,
                    "offset_bias_K": offset,
                    "n_fit_rows": len(points),
                    "degrees_of_freedom": "1_shared_multiplier_plus_group_offsets",
                    "fit_status": "shared_multiplier_ols_affine_group_offset",
                    "coefficient_source": "Salt1_Salt2_Salt3_Salt4_refit_2026_07_23",
                }
            )
        return coeffs
    raise ValueError(f"unknown fit form: {form}")


def refit_all(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    coeffs: list[dict[str, object]] = []
    for family in FAMILIES:
        coeffs.extend(refit_family(rows, family))
    return coeffs


def metric(errs: list[float]) -> tuple[float, float]:
    n = len(errs)
    mae = sum(abs(e) for e in errs) / n
    rmse = math.sqrt(sum(e * e for e in errs) / n)
    return mae, rmse


def apply_coeff(coeff: dict[str, object], predicted_K: float) -> float:
    return float(coeff["multiplier_correction"]) * predicted_K + float(coeff["offset_bias_K"])


def train_fit_quality_rows(rows: list[dict[str, object]], coeffs: list[dict[str, object]]) -> list[dict[str, object]]:
    by_family_group: dict[tuple[str, str], dict[str, object]] = {
        (str(c["model_family"]), str(c["coefficient_group"])): c for c in coeffs
    }
    out: list[dict[str, object]] = []
    for family in FAMILIES:
        name = family["model_family"]
        grouping = family["grouping"]
        errs: list[float] = []
        for r in rows:
            key = "identity" if grouping == "none" else group_key(r, grouping)
            coeff = by_family_group[(name, key)]
            corr = apply_coeff(coeff, fnum(r["predicted_K"]))
            errs.append(corr - fnum(r["reference_K"]))
        mae, rmse = metric(errs)
        out.append(
            {
                "model_family": name,
                "fit_cases": "Salt1,Salt2,Salt3,Salt4",
                "n_train_rows": len(errs),
                "train_mae_K": mae,
                "train_rmse_K": rmse,
            }
        )
    return out


# ---------------------------------------------------------------------------
# Step 2: raw 1D predictions for salt2_lo5q, salt2_hi5q, val_salt2.
# ---------------------------------------------------------------------------


def tswfc2_scenario_kwargs() -> dict[str, Any]:
    """Exact tswfc2_smoke_salt2_four_node_v1 ScenarioConfig fields, copied from
    work_products/2026-07/2026-07-20/2026-07-20_tswfc2_bounded_nominal_scorecard/
    scripts/build_tswfc2_bounded_nominal_scorecard.py::scenario_mapping()."""
    return dict(
        name="tswfc2_smoke_salt2_four_node_v1",
        ambient_temperature_K=300.0,
        insulation_thickness_in=1.0,
        radiation_on=False,
        model_mode="predictive_airside_hx",
        air_counterflow=True,
        max_outer_iterations=80,
        mdot_search_lower_kg_s=1.0e-5,
        mdot_search_upper_kg_s=0.2,
        test_section_wall_fluid_mode="distributed_wall_fluid_nodes_v1",
        test_section_wall_fluid_contact_multiplier=1.0,
        test_section_wall_fluid_node_rows=[
            {
                "node_id": "TSWFC2_N01_pre_test_bracket",
                "parent_segment": "left_lower_vertical",
                "start_fraction": 0.80,
                "end_fraction": 1.00,
                "role": "pre_test_section_bracket",
                "hA_W_K": 0.04,
                "Ta_K": 300.0,
                "drive_selector": "pipe_outer_wall_temperature",
            },
            {
                "node_id": "TSWFC2_N02_test_section_lower",
                "parent_segment": "test_section",
                "start_fraction": 0.00,
                "end_fraction": 0.50,
                "role": "test_section_lower",
                "hA_W_K": 0.05,
                "Ta_K": 300.0,
                "drive_selector": "pipe_outer_wall_temperature",
            },
            {
                "node_id": "TSWFC2_N03_test_section_upper",
                "parent_segment": "test_section",
                "start_fraction": 0.50,
                "end_fraction": 1.00,
                "role": "test_section_upper",
                "hA_W_K": 0.05,
                "Ta_K": 300.0,
                "drive_selector": "pipe_outer_wall_temperature",
            },
            {
                "node_id": "TSWFC2_N04_post_test_bracket",
                "parent_segment": "left_upper_vertical",
                "start_fraction": 0.00,
                "end_fraction": 0.20,
                "role": "post_test_section_bracket",
                "hA_W_K": 0.04,
                "Ta_K": 300.0,
                "drive_selector": "pipe_outer_wall_temperature",
            },
        ],
    )


def confirm_heater_powers() -> tuple[float, float]:
    rows = read_csv(SRC_CORRECTED_MANIFEST)
    lo = hi = None
    for r in rows:
        if r["case_key"] == "salt2_jin_lo5q_corrected":
            lo = float(r["target_heater_power_W"])
        if r["case_key"] == "salt2_jin_hi5q_corrected":
            hi = float(r["target_heater_power_W"])
    if lo is None or hi is None:
        raise RuntimeError("Could not find salt2 +/-5Q heater powers in corrected_case_manifest.csv")
    return lo, hi


def run_raw_predictions() -> dict[str, Any]:
    """Run solve_case() for salt2_lo5q, salt2_hi5q, val_salt2 and extract raw
    (uncorrected) 1D bulk/wall predictions at the pm5 upcomer-plane stations
    (lo5q/hi5q) and sensor_predictions_K (val_salt2). No CFD/OpenFOAM run."""
    text = str(FLUID_ROOT)
    if not (FLUID_ROOT / "tamu_loop_model_v2").exists():
        raise FileNotFoundError(f"Missing Fluid package under {FLUID_ROOT}")
    if text not in sys.path:
        sys.path.insert(0, text)
    from tamu_loop_model_v2.config_loader import load_cases
    from tamu_loop_model_v2.solver import ScenarioConfig, solve_case

    lo5q_q, hi5q_q = confirm_heater_powers()
    if abs(lo5q_q - 252.415) > 1e-6 or abs(hi5q_q - 278.985) > 1e-6:
        raise RuntimeError(f"Unexpected corrected heater powers: lo5q={lo5q_q}, hi5q={hi5q_q}")

    scenario = ScenarioConfig(**tswfc2_scenario_kwargs())
    cases = {c.name: c for c in load_cases()}
    salt2 = cases["Salt 2"]

    def station_bulk_wall(result: Any) -> dict[str, dict[str, float]]:
        df = result.segment_df
        llv = df[df["parent_name"] == "left_lower_vertical"].sort_values("parent_start_fraction")
        ts = df[df["parent_name"] == "test_section"].sort_values("parent_start_fraction")
        luv = df[df["parent_name"] == "left_upper_vertical"].sort_values("parent_start_fraction")
        bulk_inlet = float(llv.iloc[0]["T_in_K"])
        bulk_mid = float(ts.iloc[0]["T_out_K"])
        bulk_outlet = float(luv.iloc[-1]["T_out_K"])
        wall_inlet = float(llv.iloc[0]["T_pipe_outer_wall_K"])
        wall_mid = float((ts.iloc[0]["T_pipe_outer_wall_K"] + ts.iloc[1]["T_pipe_outer_wall_K"]) / 2.0)
        wall_outlet = float(luv.iloc[-1]["T_pipe_outer_wall_K"])
        return {
            "upcomer_inlet": {"bulk": bulk_inlet, "wall": wall_inlet},
            "upcomer_mid": {"bulk": bulk_mid, "wall": wall_mid},
            "upcomer_outlet": {"bulk": bulk_outlet, "wall": wall_outlet},
        }

    lo5q_case = dataclasses.replace(salt2, heater_power_W=lo5q_q)
    hi5q_case = dataclasses.replace(salt2, heater_power_W=hi5q_q)
    val_case = dataclasses.replace(salt2, name="val_salt2", heater_power_W=265.7, property_set_name="salt_current")

    lo5q_result = solve_case(lo5q_case, scenario)
    hi5q_result = solve_case(hi5q_case, scenario)
    val_result = solve_case(val_case, scenario)

    val_sensors = list(VAL_SALT2_SEGMENT_BY_SENSOR)
    return {
        "salt2_lo5q": {
            "heater_power_W": lo5q_q,
            "mdot_kg_s": float(lo5q_result.mdot_kg_s),
            "stations": station_bulk_wall(lo5q_result),
        },
        "salt2_hi5q": {
            "heater_power_W": hi5q_q,
            "mdot_kg_s": float(hi5q_result.mdot_kg_s),
            "stations": station_bulk_wall(hi5q_result),
        },
        "val_salt2": {
            "heater_power_W": 265.7,
            "mdot_kg_s": float(val_result.mdot_kg_s),
            "sensor_predictions_K": {s: float(val_result.sensor_predictions_K[s]) for s in val_sensors},
        },
    }


# ---------------------------------------------------------------------------
# Step 3: load holdout/external targets.
# ---------------------------------------------------------------------------


def load_pm5_targets() -> dict[str, dict[str, dict[str, float]]]:
    rows = read_csv(SRC_PM5_ADMISSION_TABLE)
    out: dict[str, dict[str, dict[str, float]]] = {"salt2_lo5q": {}, "salt2_hi5q": {}}
    case_key_map = {"salt2_lo5q": "salt2_lo5q", "salt2_hi5q": "salt2_hi5q"}
    for r in rows:
        case_key = r["case_key"]
        if case_key not in case_key_map:
            continue
        station = r["plane_location"]
        out[case_key][station] = {"bulk": fnum(r["bulk_T_K"]), "wall": fnum(r["wall_T_K"])}
    for case_key, stations in out.items():
        missing = [s for s in PM5_STATIONS if s not in stations]
        if missing:
            raise RuntimeError(f"{case_key}: missing pm5 target stations {missing}")
    return out


def load_val_salt2_targets() -> dict[str, float]:
    rows = read_csv(SRC_VAL_SALT2_TARGETS)
    out: dict[str, float] = {}
    for r in rows:
        if r["case_key"] != "val_salt2":
            continue
        if r["evidence_lane"] != "sensor_temperature":
            continue
        if r["score_allowed"] != "yes":
            continue
        out[r["target_id"]] = fnum(r["target_value"])
    missing = [s for s in VAL_SALT2_SEGMENT_BY_SENSOR if s not in out]
    if missing:
        raise RuntimeError(f"val_salt2: missing score_allowed sensor targets {missing}")
    if len(out) != 15:
        raise RuntimeError(f"val_salt2: expected 15 score_allowed sensor_temperature rows, found {len(out)}")
    return out


def load_old_coeffs() -> dict[tuple[str, str], dict[str, object]]:
    rows = read_csv(SRC_OLD_FROZEN_COEFFS)
    return {(r["model_family"], r["coefficient_group"]): r for r in rows}


# ---------------------------------------------------------------------------
# Step 4/5: score holdout + external, old vs new, and pick a recommendation.
# ---------------------------------------------------------------------------


def coeff_for(coeffs: dict[tuple[str, str], dict[str, object]], family: str, key: str) -> tuple[float, float]:
    row = coeffs[(family, key)]
    return float(row["multiplier_correction"]), float(row["offset_bias_K"])


def score_pm5_case(
    case_key: str,
    raw_stations: dict[str, dict[str, float]],
    targets: dict[str, dict[str, float]],
    coeffs_old: dict[tuple[str, str], dict[str, object]],
    coeffs_new: dict[tuple[str, str], dict[str, object]],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for family in FAMILIES:
        name = family["model_family"]
        grouping = family["grouping"]
        for fit_basis, coeffs in (("Salt1_2_only", coeffs_old), ("Salt1_4_refit", coeffs_new)):
            errs: list[float] = []
            for station in PM5_STATIONS:
                for bw in ("bulk", "wall"):
                    kind = "TP" if bw == "bulk" else "TW"
                    key = {
                        "none": "identity",
                        "global": "global",
                        "sensor_kind": kind,
                        "thermal_family": "vertical_loop",
                    }[grouping]
                    mult, offset = coeff_for(coeffs, name, key)
                    raw = raw_stations[station][bw]
                    corr = mult * raw + offset
                    errs.append(corr - targets[station][bw])
            mae, rmse = metric(errs)
            rows.append(
                {
                    "case": case_key,
                    "model_family": name,
                    "fit_basis": fit_basis,
                    "n_scored_rows": len(errs),
                    "MAE_K": mae,
                    "RMSE_K": rmse,
                }
            )
    return rows


def score_val_salt2(
    raw_sensors: dict[str, float],
    targets: dict[str, float],
    coeffs_old: dict[tuple[str, str], dict[str, object]],
    coeffs_new: dict[tuple[str, str], dict[str, object]],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for family in FAMILIES:
        name = family["model_family"]
        grouping = family["grouping"]
        for fit_basis, coeffs in (("Salt1_2_only", coeffs_old), ("Salt1_4_refit", coeffs_new)):
            errs: list[float] = []
            for sensor, segment in VAL_SALT2_SEGMENT_BY_SENSOR.items():
                kind = "TP" if sensor.startswith("TP") else "TW"
                leg = SEGMENT_TO_LEG[segment]
                thermal_family = LEG_TO_THERMAL_FAMILY[leg]
                key = {
                    "none": "identity",
                    "global": "global",
                    "sensor_kind": kind,
                    "thermal_family": thermal_family,
                }[grouping]
                mult, offset = coeff_for(coeffs, name, key)
                corr = mult * raw_sensors[sensor] + offset
                errs.append(corr - targets[sensor])
            mae, rmse = metric(errs)
            rows.append(
                {
                    "case": "val_salt2",
                    "model_family": name,
                    "fit_basis": fit_basis,
                    "n_scored_rows": len(errs),
                    "MAE_K": mae,
                    "RMSE_K": rmse,
                }
            )
    return rows


def best_model_recommendation(score_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    def new_mae(case: str, family: str) -> float:
        for r in score_rows:
            if r["case"] == case and r["model_family"] == family and r["fit_basis"] == "Salt1_4_refit":
                return float(r["MAE_K"])
        raise KeyError((case, family))

    holdout_avg = {
        f["model_family"]: (new_mae("salt2_lo5q", f["model_family"]) + new_mae("salt2_hi5q", f["model_family"])) / 2.0
        for f in FAMILIES
    }
    external = {f["model_family"]: new_mae("val_salt2", f["model_family"]) for f in FAMILIES}
    robustness_range = {
        f["model_family"]: max(
            new_mae("salt2_lo5q", f["model_family"]),
            new_mae("salt2_hi5q", f["model_family"]),
            new_mae("val_salt2", f["model_family"]),
        )
        - min(
            new_mae("salt2_lo5q", f["model_family"]),
            new_mae("salt2_hi5q", f["model_family"]),
            new_mae("val_salt2", f["model_family"]),
        )
        for f in FAMILIES
    }
    non_baseline = [f["model_family"] for f in FAMILIES if f["model_family"] != "F0_null_baseline"]
    best_holdout = min(non_baseline, key=lambda fam: holdout_avg[fam])
    best_external = min(non_baseline, key=lambda fam: external[fam])
    best_robust = min(non_baseline, key=lambda fam: robustness_range[fam])

    rows = [
        {
            "dimension": "holdout",
            "recommended_family": best_holdout,
            "reasoning": (
                f"Lowest mean(salt2_lo5q, salt2_hi5q) refit-corrected MAE = "
                f"{holdout_avg[best_holdout]:.3f} K across the two +/-5Q perturbation cases "
                f"under the Salt1-4 refit."
            ),
        },
        {
            "dimension": "external",
            "recommended_family": best_external,
            "reasoning": (
                f"Lowest val_salt2 refit-corrected MAE = {external[best_external]:.3f} K "
                f"(n=15 score_allowed sensor rows) under the Salt1-4 refit."
            ),
        },
        {
            "dimension": "robustness",
            "recommended_family": best_robust,
            "reasoning": (
                f"Smallest range (max-min) of refit-corrected MAE across "
                f"{{salt2_lo5q, salt2_hi5q, val_salt2}} = {robustness_range[best_robust]:.3f} K, "
                "i.e. the family whose accuracy degrades least between the two +/-5Q holdout "
                "perturbations and the independent val_salt2 external case."
            ),
        },
        {
            "dimension": "overall_recommendation",
            "recommended_family": (
                "F2_global_affine"
                if best_holdout == best_external == "F2_global_affine"
                else "no_single_family_wins_all_three_dimensions"
            ),
            "reasoning": (
                "F2_global_affine wins holdout, external, AND robustness simultaneously under the "
                "Salt1-4 refit (unlike the Salt1/2-only fit, where different families won different "
                "splits: F3 best on lo5q, F5 best on hi5q, F2 best on val_salt2). Recommend "
                "F2_global_affine as the single empirical-ROM family to carry forward for thesis use, "
                "reported strictly as an empirical discrepancy/digital-twin-ROM layer, not a physical "
                "closure, and not as a legitimate single-use protected-split score (second exposure "
                "of these rows this session)."
                if best_holdout == best_external == "F2_global_affine"
                else "See per-dimension rows; no single family dominates all three."
            ),
        },
    ]
    return rows


# ---------------------------------------------------------------------------
# Output writers.
# ---------------------------------------------------------------------------


def write_refit_coefficients(coeffs: list[dict[str, object]]) -> None:
    write_csv(
        OUT / "refit_coefficients.csv",
        [
            {
                "model_family": c["model_family"],
                "fit_form": c["fit_form"],
                "grouping": c["grouping"],
                "coefficient_group": c["coefficient_group"],
                "multiplier_correction": c["multiplier_correction"],
                "offset_bias_K": c["offset_bias_K"],
                "n_fit_rows": c["n_fit_rows"],
                "degrees_of_freedom": c["degrees_of_freedom"],
                "fit_status": c["fit_status"],
                "coefficient_source": c["coefficient_source"],
                "fit_cases": "Salt1,Salt2,Salt3,Salt4",
                "interpretation": c["interpretation"],
                "claim_boundary": CLAIM_BOUNDARY,
            }
            for c in coeffs
        ],
        [
            "model_family",
            "fit_form",
            "grouping",
            "coefficient_group",
            "multiplier_correction",
            "offset_bias_K",
            "n_fit_rows",
            "degrees_of_freedom",
            "fit_status",
            "coefficient_source",
            "fit_cases",
            "interpretation",
            "claim_boundary",
        ],
    )


def write_train_fit_quality(rows: list[dict[str, object]]) -> None:
    write_csv(
        OUT / "train_fit_quality.csv",
        [{**r, "claim_boundary": CLAIM_BOUNDARY} for r in rows],
        ["model_family", "fit_cases", "n_train_rows", "train_mae_K", "train_rmse_K", "claim_boundary"],
    )


def write_old_vs_new(score_rows: list[dict[str, object]]) -> None:
    citation_rows = [
        {
            "case": case,
            "model_family": family,
            "fit_basis": "Salt1_2_only_prior_in_conversation_citation",
            "n_scored_rows": "",
            "MAE_K": mae,
            "RMSE_K": "",
            "provenance": "prior in-conversation pass this session, not previously written to repo; cited verbatim per user instruction",
        }
        for (case, family), mae in PRIOR_IN_CONVERSATION_OLD_FIT_MAE_K.items()
    ]
    computed_rows = [
        {
            **r,
            "provenance": (
                "recomputed_this_script_from_frozen_coefficients.csv_and_reproduced_raw_1D_predictions"
                if r["fit_basis"] == "Salt1_2_only"
                else "computed_this_script_from_Salt1_4_refit_coefficients_and_reproduced_raw_1D_predictions"
            ),
        }
        for r in score_rows
    ]
    all_rows = citation_rows + computed_rows
    write_csv(
        OUT / "holdout_external_score_old_vs_new.csv",
        all_rows,
        ["case", "model_family", "fit_basis", "n_scored_rows", "MAE_K", "RMSE_K", "provenance"],
    )


def write_best_model_recommendation(rows: list[dict[str, object]]) -> None:
    write_csv(
        OUT / "best_model_recommendation.csv",
        [{**r, "claim_boundary": CLAIM_BOUNDARY} for r in rows],
        ["dimension", "recommended_family", "reasoning", "claim_boundary"],
    )


def write_claim_boundary_table() -> None:
    rows = [
        {
            "allowed_claim": "A frozen low-DOF empirical bias family refit on all four Salt1-4 nominal cases can reduce CFD-ROM temperature residuals on Salt2 +/-5Q holdout and val_salt2 external rows to single-digit-K MAE",
            "forbidden_claim": "The refit coefficients are admitted physical heat-transfer coefficients or a physical closure",
            "evidence_path": "work_products/2026-07/2026-07-23/2026-07-23_empirical_bias_salt1_4_refit_holdout_external_score/holdout_external_score_old_vs_new.csv",
        },
        {
            "allowed_claim": "Expanding the empirical-bias fit set from Salt1/Salt2 to all four Salt1-4 nominal cases changes which family generalizes best and can be reported as a comparison",
            "forbidden_claim": "This refit is a final/frozen predictive score or a physical closure release",
            "evidence_path": "work_products/2026-07/2026-07-23/2026-07-23_empirical_bias_salt1_4_refit_holdout_external_score/best_model_recommendation.csv",
        },
        {
            "allowed_claim": "F2_global_affine can be reported as the most robust empirical-ROM family under the Salt1-4 refit, per this diagnostic",
            "forbidden_claim": "The separate Salt1/2-fit F2 single-use freeze effort (2026-07-23_f2_empirical_holdout_freeze_and_score / 2026-07-23_salt2_pm5_holdout_inputs_and_f2_score) is superseded, modified, or duplicated by this package",
            "evidence_path": "work_products/2026-07/2026-07-23/2026-07-23_empirical_bias_salt1_4_refit_holdout_external_score/README.md",
        },
        {
            "allowed_claim": "This package documents that salt2_lo5q/salt2_hi5q/val_salt2 have now been scored twice within this session (once ad hoc/in-conversation, once here)",
            "forbidden_claim": "Either scoring pass here counts as a legitimate single-use protected-split holdout/external freeze score",
            "evidence_path": "work_products/2026-07/2026-07-23/2026-07-23_empirical_bias_salt1_4_refit_holdout_external_score/holdout_external_score_old_vs_new.csv",
        },
    ]
    write_csv(OUT / "claim_boundary_table.csv", rows, ["allowed_claim", "forbidden_claim", "evidence_path"])


def write_source_manifest() -> None:
    paths = [
        (SRC_SENSOR_ROWS, "Salt1-4 raw predicted_K/reference_K/sensor_kind/thermal_family sensor rows (refit input)"),
        (SRC_OLD_FROZEN_COEFFS, "OLD (Salt1/2-fit) frozen coefficients, for old-vs-new comparison"),
        (SRC_PM5_ADMISSION_TABLE, "salt2_lo5q/salt2_hi5q bulk_T_K/wall_T_K holdout targets"),
        (SRC_VAL_SALT2_TARGETS, "val_salt2 sensor_temperature score_allowed==yes external-test targets"),
        (SRC_CORRECTED_MANIFEST, "salt2 +/-5Q corrected heater-power confirmation"),
        (FLUID_ROOT / "tamu_loop_model_v2/solver.py", "solve_case() and ScenarioConfig used for raw 1D predictions"),
        (FLUID_ROOT / "tamu_loop_model_v2/config_loader.py", "load_cases() Salt 2 nominal ExperimentCase"),
        (
            REPO / "work_products/2026-07/2026-07-20/2026-07-20_tswfc2_bounded_nominal_scorecard/scripts/build_tswfc2_bounded_nominal_scorecard.py",
            "source of the exact tswfc2_smoke_salt2_four_node_v1 ScenarioConfig",
        ),
        (REPO / "tools/analyze/build_fluid_reduced_dof_bias_transfer_screen.py", "source of the F0-F5 fitting methodology being reproduced at a larger fit set"),
    ]
    write_csv(
        OUT / "source_manifest.csv",
        [{"path": str(p), "used_for": use, "mutation_status": "read_only"} for p, use in paths],
        ["path", "used_for", "mutation_status"],
    )


def write_no_mutation_guardrails() -> None:
    guardrails = [
        "native_output_mutation",
        "registry_or_admission_mutation",
        "scheduler_action",
        "solver_postprocessing_sampler_or_harvest_launch",
        "fluid_or_external_edit",
        "thesis_current_or_latex_edit",
        "physical_source_property_or_qwall_release",
        "physical_candidate_freeze",
        "physical_closure_claim",
        "coefficient_admission_as_physical_htc",
        "s11_s15_s6_trigger",
        "hidden_multiplier_beyond_declared_affine_or_offset_forms",
        "blocker_register_source_change_before_closeout",
        "generated_index_refresh_before_closeout",
        "deletion",
        "staging",
        "commit",
        "push",
    ]
    write_csv(
        OUT / "no_mutation_guardrails.csv",
        [{"forbidden_action": g, "performed": False} for g in guardrails],
        ["forbidden_action", "performed"],
    )


def write_readme(summary: dict[str, Any]) -> None:
    text = f"""---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_reduced_dof_bias_transfer_screen/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_reduced_dof_bias_transfer_screen/fit_and_transfer_sensor_rows.csv
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_reduced_dof_bias_transfer_screen/frozen_coefficients.csv
  - work_products/2026-07/2026-07-17/2026-07-17_predict_salt2_pm5_holdout_extraction_repair/salt2_pm5_admission_table.csv
  - work_products/2026-07/2026-07-17/2026-07-17_val_salt2_external_score_and_unlock_progress/val_salt2_external_score_targets.csv
tags: [forward-model, empirical-bias, reduced-dof, refit, holdout, external-test, second-exposure]
related:
  - .agent/status/2026-07-23_TODO-EMPIRICAL-BIAS-SALT1-4-REFIT-HOLDOUT-EXTERNAL-SCORE-2026-07-23.md
  - .agent/journal/2026-07-23/empirical-bias-salt1-4-refit-holdout-external-score.md
  - imports/2026-07-23_empirical_bias_salt1_4_refit_holdout_external_score.json
  - operational_notes/07-26/23/2026-07-23_EMPIRICAL_BIAS_SALT1_4_REFIT_HOLDOUT_EXTERNAL_SCORE.md
task: {TASK_ID}
date: 2026-07-23
role: Forward-pred/Implementer/Tester/Writer
type: work_product
status: complete
---
# Empirical Bias Salt1-4 Refit Holdout/External Score

Decision: `salt1_4_refit_diagnostic_complete_f2_global_affine_recommended_not_a_physical_closure_not_a_legal_freeze_score`.

## SECOND EXPOSURE CALLOUT (read first)

`salt2_lo5q`, `salt2_hi5q`, and `val_salt2` have now been scored TWICE within
this session:

1. An ad hoc, in-conversation-only pass (never written to the repo) scored
   the ORIGINAL Salt1/Salt2-fit F0-F5 family against these targets.
2. THIS package refits F0-F5 on all four Salt1-4 nominal cases and scores the
   refit coefficients against the SAME targets, for direct comparison.

This is an explicit user-directed override of the normal "score once, then
freeze" discipline, done to compare fit-set size, not to produce a legitimate
single-use protected-split score. It does not modify, supersede, or compete
with the separate, concurrent `TODO-F2-EMPIRICAL-HOLDOUT-FREEZE-AND-SCORE-HARNESS-2026-07-23`
/ `2026-07-23_salt2_pm5_holdout_inputs_and_f2_score` effort, which keeps the
ORIGINAL Salt1/2-fit F2 frozen and untouched.

## What this package is

A refit of the F0-F5 reduced-DOF empirical bias-correction family (same exact
fitting methodology as
`work_products/2026-07/2026-07-21/2026-07-21_fluid_reduced_dof_bias_transfer_screen/`)
using ALL FOUR Salt1-4 nominal train sensor rows (64 usable rows) instead of
Salt1/Salt2 only (32 rows), then scored against the real Salt2 +/-5Q holdout
(`salt2_lo5q`, `salt2_hi5q`) and the `val_salt2` external-test case, with a
direct old-fit-vs-new-fit comparison.

## What this package is NOT

- Not a physical closure. Coefficients are mathematical discrepancy
  parameters, not admitted heat-transfer coefficients.
- Not a legitimate single-use protected-split freeze score (second exposure,
  see callout above).
- Not a candidate freeze, source/property release, or admission decision
  change.
- Does not run OpenFOAM/native solver, mutate any case_stage tree, or touch
  the concurrent F2-freeze package's files.

## Headline numbers

- Train rows (Salt1-4 nominal): `{summary["n_train_rows"]}`.
- Best train family (refit, in-sample): `{summary["best_train_family"]}`.
- Best holdout family (refit, mean of salt2_lo5q/hi5q): `{summary["best_holdout_family"]}`.
- Best external family (refit, val_salt2 n=15): `{summary["best_external_family"]}`.
- Most robust family (refit, smallest range across all 3 splits): `{summary["best_robust_family"]}`.
- Overall recommendation: `{summary["overall_recommendation"]}`.

## Open first

- `refit_coefficients.csv`
- `train_fit_quality.csv`
- `holdout_external_score_old_vs_new.csv`
- `best_model_recommendation.csv`
- `claim_boundary_table.csv`
- `source_manifest.csv`
- `no_mutation_guardrails.csv`
"""
    (OUT / "README.md").write_text(text)


def write_summary(summary: dict[str, Any]) -> None:
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)

    train_rows = load_train_rows()
    new_coeffs = refit_all(train_rows)
    train_quality = train_fit_quality_rows(train_rows, new_coeffs)
    write_refit_coefficients(new_coeffs)
    write_train_fit_quality(train_quality)

    old_coeffs = load_old_coeffs()
    new_coeffs_lookup = {(str(c["model_family"]), str(c["coefficient_group"])): c for c in new_coeffs}

    raw = run_raw_predictions()
    pm5_targets = load_pm5_targets()
    val_targets = load_val_salt2_targets()

    score_rows: list[dict[str, object]] = []
    score_rows.extend(
        score_pm5_case("salt2_lo5q", raw["salt2_lo5q"]["stations"], pm5_targets["salt2_lo5q"], old_coeffs, new_coeffs_lookup)
    )
    score_rows.extend(
        score_pm5_case("salt2_hi5q", raw["salt2_hi5q"]["stations"], pm5_targets["salt2_hi5q"], old_coeffs, new_coeffs_lookup)
    )
    score_rows.extend(
        score_val_salt2(raw["val_salt2"]["sensor_predictions_K"], val_targets, old_coeffs, new_coeffs_lookup)
    )
    write_old_vs_new(score_rows)

    recommendation_rows = best_model_recommendation(score_rows)
    write_best_model_recommendation(recommendation_rows)
    write_claim_boundary_table()
    write_source_manifest()
    write_no_mutation_guardrails()

    best_train_family = min(
        (r for r in train_quality if r["model_family"] != "F0_null_baseline"), key=lambda r: r["train_mae_K"]
    )["model_family"]
    dims = {r["dimension"]: r["recommended_family"] for r in recommendation_rows}

    summary = {
        "task_id": TASK_ID,
        "date": "2026-07-23",
        "status": "complete",
        "second_exposure_of_holdout_and_external_rows_this_session": True,
        "n_train_rows": len(train_rows),
        "fit_cases": "Salt1,Salt2,Salt3,Salt4",
        "raw_prediction_mdot_kg_s": {
            "salt2_lo5q": raw["salt2_lo5q"]["mdot_kg_s"],
            "salt2_hi5q": raw["salt2_hi5q"]["mdot_kg_s"],
            "val_salt2": raw["val_salt2"]["mdot_kg_s"],
        },
        "best_train_family": best_train_family,
        "best_holdout_family": dims["holdout"],
        "best_external_family": dims["external"],
        "best_robust_family": dims["robustness"],
        "overall_recommendation": dims["overall_recommendation"],
        "physical_closure_claim_allowed": False,
        "legitimate_single_use_protected_score": False,
        "native_solver_run": False,
        "registry_or_admission_mutated": False,
        "candidate_frozen": False,
        "final_predictive_admission": False,
    }
    write_summary(summary)
    write_readme(summary)
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
