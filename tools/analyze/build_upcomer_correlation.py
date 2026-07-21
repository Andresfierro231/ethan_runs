#!/usr/bin/env python3
"""Build the 3-point upcomer recirculation correlation from Salt 2/3/4 Jin nominal data.

WHY THIS EXISTS  (AGENT-196, 2026-07-07)
-----------------------------------------
The upcomer (pipeleg_left = left_lower_leg + test_section_span + left_upper_leg) shows
a real buoyancy-driven recirculation cell: 15-33% of the cross-section flows backward,
falling monotonically as Re increases (Salt 2 → Salt 3 → Salt 4).  This tool compiles
the 3-point dataset, fits a simple correlation with honest uncertainty bounds, and
documents the physical mechanism and data-needs statement.

PHYSICAL MECHANISM
------------------
The heater outlet (lower_leg, inclined ~21 deg from horizontal) delivers buoyant,
high-temperature salt to the bottom of the vertical test section (pipeleg_left).
The quartz test section is nearly adiabatic (high insulation); fluid near the wall
does not cool.  A density inversion forms between the hot buoyant fluid and the cooler
fluid above, driving a Rayleigh-Benard-like convective instability — the recirculation
cell.  The cell weakens with increasing Re (inertia suppresses the buoyant recirculation).

Onset extrapolation (LitRev ch.14 mixed-convection criterion):
  Route A (from Nu / backflow trend extrapolation): Re_crit ~ 240-260
  Route B (from Ri criterion Ri=Gr/Re^2 ~ O(1)):   Re_crit ~ 100-235
  Both routes agree to ~factor 2.  Current data range: Re 68-135.

DATA NEEDS STATEMENT
--------------------
Corrected Q perturbation jobs (SLURM 3275448-3275451, Salt 2/3/4 hi/lo heater power)
are required to expand the Re range beyond the nominal S2/S3/S4 operating points
(Re ~68-135).  Until those runs qualify under the T2 gate, the correlation is
extrapolated beyond its calibration range for all onset-Re predictions.

CONFIDENCE BOUNDARIES
---------------------
* 3 data points -> parameter uncertainty is O(1) if 2 parameters are fit.  OLS
  produces 1 residual DOF; jackknife leave-1-out gives correlated but informative
  resamples.  Both are reported; treat as indicative, not precise.
* Coarse mesh, laminar, single time per case (mainline continuation).
* The linear model bf = a + b/Re predicts an asymptote of bf -> a as Re -> infinity,
  NOT a zero-crossing.  The onset Re from Route A/B is SEPARATE analysis (extrapolation
  assuming the cell turns off, not from this fit's zero-crossing).
* Ri_median, Ra_median, Pr_median from section-MEDIAN of solver-written fields.
  Use MEDIAN not mean (mean Ri is ~100x larger, dominated by near-zero-velocity cells).
* Re_upcomer from momentum budget (left_lower_leg bulk Re), not section-median Re.

USAGE
  python tools/analyze/build_upcomer_correlation.py
  python tools/analyze/build_upcomer_correlation.py --out-dir work_products/my_out/
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.common import (  # noqa: E402
    WORKSPACE_ROOT,
    csv_dump,
    ensure_dir,
    iso_timestamp,
    json_dump,
    relative_to_workspace,
)

# ---------------------------------------------------------------------------
# Source data paths (READ-ONLY: claimed by prior agents)
# ---------------------------------------------------------------------------
_UPCOMER_CELL_DIR = (
    WORKSPACE_ROOT / "work_products" / "2026-06-30_claude_upcomer_convection_cell"
)
_MOMENTUM_BUDGET_CSV = (
    WORKSPACE_ROOT / "work_products" / "2026-07-01_claude_momentum_budget" / "momentum_budget.csv"
)
_HTC_DIR = WORKSPACE_ROOT / "work_products" / "2026-06-30_claude_thermal_htc"

# Case IDs and short labels
CASES = [
    {
        "source_id": "viscosity_screening_salt_test_2_jin_coarse_mesh",
        "label": "salt_2_jin",
    },
    {
        "source_id": "viscosity_screening_salt_test_3_jin_coarse_mesh",
        "label": "salt_3_jin",
    },
    {
        "source_id": "viscosity_screening_salt_test_4_jin_coarse_mesh",
        "label": "salt_4_jin",
    },
]

# Representative station: first row in left_lower_leg with label TW7
_UPCOMER_SPAN = "left_lower_leg"
_STATION_LABEL = "TW7"
_MOMENTUM_SPAN = "left_lower_leg"
_HTC_SEGMENT = "upcomer"

# Onset-Re extrapolation from prior analysis (Route A and B)
ONSET_RE_ROUTE_A_LOW = 240.0
ONSET_RE_ROUTE_A_HIGH = 260.0
ONSET_RE_ROUTE_B_LOW = 100.0
ONSET_RE_ROUTE_B_HIGH = 235.0


# ---------------------------------------------------------------------------
# Pure functions (unit-testable, side-effect free)
# ---------------------------------------------------------------------------

def load_upcomer_cell_row(
    csv_path: Path,
    span: str = _UPCOMER_SPAN,
    station_label: str = _STATION_LABEL,
) -> dict[str, float]:
    """Return the first matching row from a upcomer convection cell CSV.

    Parameters
    ----------
    csv_path:       Path to the upcomer convection cell CSV for one case.
    span:           Span name to filter on (e.g. "left_lower_leg").
    station_label:  Station label to match (e.g. "TW7").

    Returns
    -------
    dict with float-valued fields from the matched row.
    Raises ValueError if no matching row is found.
    """
    with csv_path.open() as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            if row.get("span") == span and row.get("label") == station_label:
                return {k: _to_float(v) for k, v in row.items() if v != ""}
    raise ValueError(
        f"No row found with span={span!r}, label={station_label!r} in {csv_path}"
    )


def load_momentum_budget_row(
    csv_path: Path,
    source_id: str,
    span: str = _MOMENTUM_SPAN,
) -> dict[str, float]:
    """Return the momentum budget row for (source_id, span).

    Parameters
    ----------
    csv_path:   Path to the momentum_budget.csv.
    source_id:  Case source ID to match.
    span:       Span name to match (e.g. "left_lower_leg").

    Returns
    -------
    dict with float-valued fields from the matched row.
    Raises ValueError if no matching row is found.
    """
    with csv_path.open() as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            if row.get("source_id") == source_id and row.get("span") == span:
                return {k: _to_float(v) for k, v in row.items() if v != ""}
    raise ValueError(
        f"No row found with source_id={source_id!r}, span={span!r} in {csv_path}"
    )


def load_htc_row(
    csv_path: Path,
    segment: str = _HTC_SEGMENT,
) -> dict[str, float | str]:
    """Return the HTC row for the given segment (e.g. 'upcomer').

    Parameters
    ----------
    csv_path:  Path to a segment_htc_uaprime_*.csv.
    segment:   Segment name to match.

    Returns
    -------
    dict with mixed float/str fields.
    Raises ValueError if no matching row is found.
    """
    with csv_path.open() as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            if row.get("segment") == segment:
                result: dict[str, float | str] = {}
                for k, v in row.items():
                    if v == "" or v is None:
                        continue
                    result[k] = _to_float_or_str(v)
                return result
    raise ValueError(f"No row found with segment={segment!r} in {csv_path}")


def _to_float(v: str) -> float:
    """Convert string to float; return NaN on failure."""
    try:
        return float(v)
    except (ValueError, TypeError):
        return float("nan")


def _to_float_or_str(v: str) -> float | str:
    """Try float conversion; fall back to string."""
    try:
        return float(v)
    except (ValueError, TypeError):
        return v


def compile_dataset(
    cases: list[dict[str, str]],
    upcomer_cell_dir: Path,
    momentum_csv: Path,
    htc_dir: Path,
) -> list[dict[str, Any]]:
    """Compile the 3-row dataset from existing work products.

    Returns list of dicts with one entry per case:
      label, source_id,
      Re_upcomer (momentum budget, left_lower_leg),
      Re_section_median (from convection cell CSV),
      Ri_median, Ra_median, Pr_median (from convection cell, MEDIAN not mean),
      backflow_fraction (from convection cell, TW7/left_lower_leg),
      recirculation_intensity (from convection cell),
      Nu_upcomer (from HTC),
      htc_wm2k (from HTC),
      T_bulk_K (from HTC upcomer segment)
    """
    rows: list[dict[str, Any]] = []
    for case in cases:
        sid = case["source_id"]
        label = case["label"]

        # --- upcomer convection cell ---
        cell_csv = upcomer_cell_dir / f"upcomer_convection_cell_{sid}.csv"
        cell = load_upcomer_cell_row(cell_csv)

        # --- momentum budget ---
        mom = load_momentum_budget_row(momentum_csv, sid)

        # --- HTC ---
        htc_csv = htc_dir / f"segment_htc_uaprime_{sid}.csv"
        htc = load_htc_row(htc_csv)

        nu_val = htc.get("Nu")
        nu_upcomer = float(nu_val) if isinstance(nu_val, (int, float)) and not (isinstance(nu_val, float) and math.isnan(nu_val)) else float("nan")

        rows.append({
            "label": label,
            "source_id": sid,
            "Re_upcomer": mom["Re"],               # bulk Re from momentum budget
            "Re_section_median": cell["Re_section_median"],
            "Ri_median": cell["Ri_section_median"],
            "Ra_median": cell["Ra_section_median"],
            "Pr_median": cell["Pr_section_median"],
            "backflow_fraction": cell["backflow_area_fraction"],
            "recirculation_intensity": cell["recirculation_intensity"],
            "Nu_upcomer": nu_upcomer,
            "htc_wm2k": float(htc.get("htc_wm2k", float("nan"))),
            "T_bulk_K": float(htc.get("T_bulk_k", float("nan"))),
            "u_bulk_m_s": mom.get("u_bulk_mean_m_s", float("nan")),
            "inclination_from_vertical_deg": cell.get("inclination_from_vertical_deg", float("nan")),
        })
    return rows


def fit_backflow_linear(
    dataset: list[dict[str, Any]],
) -> dict[str, float]:
    """Fit backflow_fraction = a + b/Re using OLS.

    With only 3 points and 2 parameters (1 DOF), the fit is nearly exact.
    We report:
      a, b: OLS estimates
      a_se, b_se: standard errors from OLS covariance matrix
      a_jk_std, b_jk_std: jackknife leave-1-out standard deviations
      residual_sse, sigma_hat: sum-of-squared residuals, estimated std deviation

    Parameters
    ----------
    dataset: list of 3 dicts, each with 'Re_upcomer' and 'backflow_fraction'.

    Returns
    -------
    dict with all fit parameters and uncertainty estimates.
    Raises ValueError if dataset has fewer than 2 rows (underdetermined).
    """
    n = len(dataset)
    if n < 2:
        raise ValueError(f"Need at least 2 data points to fit; got {n}")

    re_vals = np.array([d["Re_upcomer"] for d in dataset])
    bf_vals = np.array([d["backflow_fraction"] for d in dataset])

    # Design matrix: [1, 1/Re]
    X = np.column_stack([np.ones(n), 1.0 / re_vals])
    y = bf_vals

    # OLS solution via least-squares
    coeffs, sse_arr, rank, sv = np.linalg.lstsq(X, y, rcond=None)
    a, b = float(coeffs[0]), float(coeffs[1])

    # Residuals
    y_hat = X @ coeffs
    residuals = y - y_hat
    sse = float(np.sum(residuals**2))

    # Estimated variance (n - 2 DOF for 2-parameter fit)
    dof = n - 2
    sigma_hat = math.sqrt(sse / dof) if dof > 0 else float("nan")

    # Standard errors from OLS covariance matrix
    if dof > 0 and not math.isnan(sigma_hat):
        try:
            XtXinv = np.linalg.inv(X.T @ X)
            cov = (sigma_hat**2) * XtXinv
            a_se = float(math.sqrt(max(cov[0, 0], 0.0)))
            b_se = float(math.sqrt(max(cov[1, 1], 0.0)))
        except np.linalg.LinAlgError:
            a_se = float("nan")
            b_se = float("nan")
    else:
        a_se = float("nan")
        b_se = float("nan")

    # Jackknife leave-1-out (informative with 3 points)
    jk_a: list[float] = []
    jk_b: list[float] = []
    for i in range(n):
        idx = [j for j in range(n) if j != i]
        X_jk = X[idx]
        y_jk = y[idx]
        c_jk, _, _, _ = np.linalg.lstsq(X_jk, y_jk, rcond=None)
        jk_a.append(float(c_jk[0]))
        jk_b.append(float(c_jk[1]))

    a_jk_std = float(np.std(jk_a, ddof=0)) if len(jk_a) > 1 else float("nan")
    b_jk_std = float(np.std(jk_b, ddof=0)) if len(jk_b) > 1 else float("nan")

    # Onset Re extrapolation from Route A and B (documented, not from fit)
    onset_re_route_a_mid = (ONSET_RE_ROUTE_A_LOW + ONSET_RE_ROUTE_A_HIGH) / 2.0
    onset_re_route_b_mid = (ONSET_RE_ROUTE_B_LOW + ONSET_RE_ROUTE_B_HIGH) / 2.0

    return {
        "model": "bf = a + b / Re",
        "a": a,
        "b": b,
        "a_se_ols": a_se,
        "b_se_ols": b_se,
        "a_jk_std": a_jk_std,
        "b_jk_std": b_jk_std,
        "residual_sse": sse,
        "sigma_hat": sigma_hat,
        "n_points": n,
        "dof": dof,
        "Re_min_calibration": float(np.min(re_vals)),
        "Re_max_calibration": float(np.max(re_vals)),
        "bf_asymptote_high_Re": a,  # bf -> a as Re -> inf
        "onset_Re_route_A_low": ONSET_RE_ROUTE_A_LOW,
        "onset_Re_route_A_high": ONSET_RE_ROUTE_A_HIGH,
        "onset_Re_route_A_mid": onset_re_route_a_mid,
        "onset_Re_route_B_low": ONSET_RE_ROUTE_B_LOW,
        "onset_Re_route_B_high": ONSET_RE_ROUTE_B_HIGH,
        "onset_Re_route_B_mid": onset_re_route_b_mid,
        "note_onset_re": (
            "Onset Re (cell turns off) is from Route A/B extrapolation, NOT from "
            "the linear fit zero-crossing (the fit predicts an asymptote bf->a>0, "
            "not bf=0). Route A ~240-260 (Nu/backflow trend). Route B ~100-235 "
            "(Ri criterion). Both bracketed from LitRev ch.14."
        ),
        "note_extrapolation": (
            "Calibration range Re=68-135. All onset-Re predictions are extrapolated "
            "beyond calibration range. Corrected Q jobs (SLURM 3275448-3275451) "
            "required for in-range validation."
        ),
    }


def predict_backflow(a: float, b: float, Re: float) -> float:
    """Evaluate bf = a + b/Re at the given Re.

    Returns NaN if Re is non-positive.
    """
    if Re <= 0:
        return float("nan")
    return a + b / Re


def check_monotone_bf_decreasing(dataset: list[dict[str, Any]]) -> bool:
    """Return True if backflow_fraction decreases strictly as Re increases.

    Expects dataset rows ordered by ascending Re_upcomer.
    """
    sorted_rows = sorted(dataset, key=lambda d: d["Re_upcomer"])
    bf_vals = [r["backflow_fraction"] for r in sorted_rows]
    return all(bf_vals[i] > bf_vals[i + 1] for i in range(len(bf_vals) - 1))


def check_monotone_nu_increasing(dataset: list[dict[str, Any]]) -> bool:
    """Return True if Nu_upcomer increases strictly as Re increases."""
    sorted_rows = sorted(dataset, key=lambda d: d["Re_upcomer"])
    nu_vals = [r["Nu_upcomer"] for r in sorted_rows]
    return all(nu_vals[i] < nu_vals[i + 1] for i in range(len(nu_vals) - 1))


# ---------------------------------------------------------------------------
# Output builders
# ---------------------------------------------------------------------------

_DATASET_FIELDS = [
    "label",
    "source_id",
    "Re_upcomer",
    "Re_section_median",
    "Ri_median",
    "Ra_median",
    "Pr_median",
    "backflow_fraction",
    "recirculation_intensity",
    "Nu_upcomer",
    "htc_wm2k",
    "T_bulk_K",
    "u_bulk_m_s",
    "inclination_from_vertical_deg",
]

_FIT_FIELDS = [
    "model",
    "a",
    "b",
    "a_se_ols",
    "b_se_ols",
    "a_jk_std",
    "b_jk_std",
    "residual_sse",
    "sigma_hat",
    "n_points",
    "dof",
    "Re_min_calibration",
    "Re_max_calibration",
    "bf_asymptote_high_Re",
    "onset_Re_route_A_low",
    "onset_Re_route_A_high",
    "onset_Re_route_A_mid",
    "onset_Re_route_B_low",
    "onset_Re_route_B_high",
    "onset_Re_route_B_mid",
    "note_onset_re",
    "note_extrapolation",
]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build upcomer recirculation correlation (AGENT-196)"
    )
    parser.add_argument(
        "--out-dir",
        default=str(
            WORKSPACE_ROOT / "work_products" / "2026-07-07_upcomer_correlation_v2"
        ),
        help="Output directory",
    )
    parser.add_argument(
        "--upcomer-cell-dir",
        default=str(_UPCOMER_CELL_DIR),
    )
    parser.add_argument(
        "--momentum-csv",
        default=str(_MOMENTUM_BUDGET_CSV),
    )
    parser.add_argument(
        "--htc-dir",
        default=str(_HTC_DIR),
    )
    args = parser.parse_args(argv)

    out_dir = ensure_dir(Path(args.out_dir))
    upcomer_cell_dir = Path(args.upcomer_cell_dir)
    momentum_csv = Path(args.momentum_csv)
    htc_dir = Path(args.htc_dir)

    # --- Compile dataset ---
    print("Compiling 3-point dataset...")
    dataset = compile_dataset(CASES, upcomer_cell_dir, momentum_csv, htc_dir)
    print(f"  {len(dataset)} cases loaded")
    for row in dataset:
        print(
            f"  {row['label']}: Re={row['Re_upcomer']:.1f}, "
            f"bf={row['backflow_fraction']:.4f}, Nu={row['Nu_upcomer']:.3f}"
        )

    # --- Sanity checks ---
    if not check_monotone_bf_decreasing(dataset):
        print("WARNING: backflow_fraction is NOT monotone decreasing with Re")
    else:
        print("  CHECK PASS: backflow_fraction decreases with Re")

    if not check_monotone_nu_increasing(dataset):
        print("WARNING: Nu_upcomer is NOT monotone increasing with Re")
    else:
        print("  CHECK PASS: Nu_upcomer increases with Re")

    # --- Fit correlation ---
    print("Fitting backflow_fraction = a + b/Re ...")
    fit = fit_backflow_linear(dataset)
    print(
        f"  a = {fit['a']:.5f} +/- {fit['a_se_ols']:.5f} (OLS SE), "
        f"+/- {fit['a_jk_std']:.5f} (jackknife std)"
    )
    print(
        f"  b = {fit['b']:.4f} +/- {fit['b_se_ols']:.4f} (OLS SE), "
        f"+/- {fit['b_jk_std']:.4f} (jackknife std)"
    )
    print(f"  sigma_hat = {fit['sigma_hat']:.6f}  (1 DOF)")
    print(f"  bf asymptote (Re->inf): {fit['bf_asymptote_high_Re']:.4f}")
    print(
        f"  Onset Re Route A: {fit['onset_Re_route_A_low']:.0f}-"
        f"{fit['onset_Re_route_A_high']:.0f}  "
        f"Route B: {fit['onset_Re_route_B_low']:.0f}-"
        f"{fit['onset_Re_route_B_high']:.0f}"
    )

    # --- Write outputs ---
    dataset_path = out_dir / "upcomer_dataset.csv"
    csv_dump(dataset_path, _DATASET_FIELDS, dataset)
    print(f"  Wrote dataset -> {relative_to_workspace(dataset_path)}")

    fit_path = out_dir / "upcomer_correlation_fit.csv"
    csv_dump(fit_path, _FIT_FIELDS, [fit])
    print(f"  Wrote fit    -> {relative_to_workspace(fit_path)}")

    # --- Summary JSON ---
    summary = {
        "generated_at": iso_timestamp(),
        "task": "AGENT-196",
        "inputs": {
            "upcomer_cell_dir": str(relative_to_workspace(upcomer_cell_dir)),
            "momentum_budget_csv": str(relative_to_workspace(momentum_csv)),
            "htc_dir": str(relative_to_workspace(htc_dir)),
        },
        "outputs": {
            "upcomer_dataset_csv": str(relative_to_workspace(dataset_path)),
            "upcomer_correlation_fit_csv": str(relative_to_workspace(fit_path)),
        },
        "counts": {
            "n_cases": len(dataset),
            "n_fit_params": 2,
            "fit_dof": fit["dof"],
        },
        "fit": {
            "model": fit["model"],
            "a": fit["a"],
            "b": fit["b"],
            "a_se_ols": fit["a_se_ols"],
            "b_se_ols": fit["b_se_ols"],
            "a_jk_std": fit["a_jk_std"],
            "b_jk_std": fit["b_jk_std"],
            "sigma_hat": fit["sigma_hat"],
            "Re_range": [fit["Re_min_calibration"], fit["Re_max_calibration"]],
            "bf_asymptote_high_Re": fit["bf_asymptote_high_Re"],
        },
        "onset_Re": {
            "route_A": [fit["onset_Re_route_A_low"], fit["onset_Re_route_A_high"]],
            "route_B": [fit["onset_Re_route_B_low"], fit["onset_Re_route_B_high"]],
            "note": fit["note_onset_re"],
        },
        "monotone_checks": {
            "bf_decreasing_with_Re": check_monotone_bf_decreasing(dataset),
            "Nu_increasing_with_Re": check_monotone_nu_increasing(dataset),
        },
        "limitations": [
            "3 data points only: parameter uncertainty is O(1) at 1 DOF",
            "Coarse mesh, laminar, single time per case",
            "Onset Re predictions are extrapolated beyond Re calibration range (68-135)",
            "Ri_median, Ra_median from section-median of solver fields (exact Lc/DeltaT "
            "definition not audited against case setup)",
            "All perturbation runs (3275448-3275451) still under T2 qualification gate; "
            "not admitted to correlation",
            "Upcomer recirculation cell in UPPER upcomer (TP5/TW8/TP6) is not well "
            "captured by this single-station fit; a 2-region model may be needed",
        ],
    }
    json_dump(out_dir / "summary.json", summary)
    print(f"  Wrote summary -> {relative_to_workspace(out_dir / 'summary.json')}")

    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
