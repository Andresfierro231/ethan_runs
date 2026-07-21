#!/usr/bin/env python3
"""Assess statistical steadiness ("convergence") of TAMU loop CFD monitors.

WHY THIS EXISTS (action item #2 from the 2026-06-30 inspection)
---------------------------------------------------------------
The cases have NO in-solver `fieldAverage`, and the existing pipeline treats the
mean of the last ~5 instantaneous snapshots as a "time-averaged / steady" value
WITHOUT any test that the flow has actually stopped drifting or oscillating.
For a buoyancy-driven natural-circulation loop that is not a safe assumption.

This tool replaces "assert steady" with "measure steadiness". It reads the
native `postProcessing/` monitor time series (which are written every step, so
they are a far richer record than the handful of retained 3D field snapshots)
and emits, for each monitor, explicit, justified stationarity diagnostics plus a
defensible averaging window and uncertainty band.

It is read-only and never reconstructs fields, so it runs anywhere (no OpenFOAM
runtime needed).

SCIENTIFIC METHOD (every threshold is justified; see THRESHOLDS below)
----------------------------------------------------------------------
For each monitor series y(t) we take a trailing analysis window of fraction
`--window-frac` of the total simulated time (default 0.25, i.e. the last
quarter), and within that window compute:

  * mean, std, and relative std (CV = std/|mean|)
  * normalized drift: a least-squares slope b fit to y(t), expressed as the
    total change across the window (b * window_length) divided by |mean|. This
    is the single most important steadiness number: it asks "does the quantity
    still have a trend?"
  * peak-to-peak amplitude (max-min)/|mean| — captures oscillation/limit cycles
    that a small net slope would hide.
  * a lag-1 autocorrelation estimate, used to deflate the naive standard error
    of the mean (samples in a CFD trace are NOT independent).
  * an effective sample size N_eff = N * (1-r1)/(1+r1) and the autocorrelation-
    corrected standard error SE = std / sqrt(max(N_eff,1)).

A verdict is assigned per series from the drift and amplitude (THRESHOLDS).
The reported "steady value" is mean ± SE over the window; we ALSO report the
last instantaneous value so the reader can see how far the legacy
"last snapshot" choice sits from the windowed mean.

THRESHOLDS (justification)
--------------------------
These are engineering steadiness bands, deliberately conservative, and are
reported alongside every result so a reviewer can re-judge:
  * |drift over window| < 1% of mean   AND amplitude < 2% -> "stationary"
  * |drift over window| < 5% of mean   AND amplitude < 10% -> "quasi_stationary"
  * otherwise -> "drifting_or_oscillatory"
Rationale: 1%/2% is below the coarse-mesh discretization error we already
attribute to these laminar runs (so tighter would be meaningless precision);
5%/10% marks the point past which a single mean is not a faithful summary and a
longer run or explicit transient treatment is required. The bands are tunable
via CLI flags and the chosen values are recorded in the output.

USAGE
  python tools/analyze/assess_time_convergence.py --paper-grade-salt-jin
  python tools/analyze/assess_time_convergence.py --source-id <id> [--case-dir DIR]
  python tools/analyze/assess_time_convergence.py --all-registered
"""
from __future__ import annotations

import argparse
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
    parse_scalar_series,
    read_registry_rows,
    relative_to_workspace,
    safe_float,
)

# Paper-grade Salt Jin subset (user scope decision, 2026-06-30). Salt 1 is kept
# but flagged because its retained window is short (documented caveat).
PAPER_GRADE_SALT_JIN = [
    "viscosity_screening_salt_test_1_jin_coarse_mesh",
    "viscosity_screening_salt_test_2_jin_coarse_mesh",
    "viscosity_screening_salt_test_3_jin_coarse_mesh",
    "viscosity_screening_salt_test_4_jin_coarse_mesh",
]
SALT_1_CAVEAT_ID = "viscosity_screening_salt_test_1_jin_coarse_mesh"

REGISTRY_PATH = WORKSPACE_ROOT / "registry" / "case_registry.csv"
DEFAULT_OUTPUT_DIR = (
    WORKSPACE_ROOT / "work_products" / "2026-06-30_claude_time_convergence"
)

# Monitors we treat as primary loop QoI. mdot is the buoyancy-balance flow rate
# (the quantity the 1D model ultimately predicts); total_Q is the global heat
# balance. These are the two that most directly gate "is the loop steady".
MDOT_MONITOR_DIRS = [
    "mdot_pipeleg_left_04_test_section",
    "mdot_pipeleg_lower_05_straight",
    "mdot_pipeleg_right_02_middle",
    "mdot_pipeleg_upper_05_cooler",
]

# IMPORTANT thermal-steadiness nuance (justification):
# `total_Q.dat` is the NET signed sum of wall heat (sum of wallHeatFlux*magSf
# over all wall patches). At steady state this net approaches ~0 (heat in ~ heat
# out), so normalizing its drift by its own near-zero mean grossly overstates
# non-stationarity. The physically meaningful thermal QoI for HTC/Nu closures is
# the GROSS duty (total heat actually crossing the walls), which we reconstruct
# from the per-patch `wallHeatFlux.dat`:
#   gross_duty(t)  = sum over wall patches of |Q_patch(t)|
#   heat_in(t)     = sum of positive Q (into fluid)   [heater-dominated]
#   heat_out(t)    = sum of negative Q (out of fluid) [cooler+ambient]
#   net_imbalance(t) = heat_in + heat_out  (== total_Q)
# We assess gross_duty for steadiness (proper scale) and additionally report the
# net imbalance as a FRACTION OF GROSS DUTY, which doubles as a conservation
# (heat-closure) check rather than a misleading steadiness flag.


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--source-id", help="Single registered source id.")
    group.add_argument("--paper-grade-salt-jin", action="store_true", help="Run the Salt Jin paper subset.")
    group.add_argument("--all-registered", action="store_true", help="Run every registered case with postProcessing.")
    parser.add_argument("--case-dir", help="Explicit case dir (overrides registry lookup for --source-id).")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--window-frac", type=float, default=0.25, help="Trailing fraction of time used as the analysis window.")
    parser.add_argument("--stationary-drift", type=float, default=0.01, help="Max |drift/mean| over window for 'stationary'.")
    parser.add_argument("--stationary-amp", type=float, default=0.02, help="Max peak-to-peak/mean for 'stationary'.")
    parser.add_argument("--quasi-drift", type=float, default=0.05, help="Max |drift/mean| over window for 'quasi_stationary'.")
    parser.add_argument("--quasi-amp", type=float, default=0.10, help="Max peak-to-peak/mean for 'quasi_stationary'.")
    # --- operating-point (re-equilibration) gate: T3, see OPERATING_POINT_GATE ---
    parser.add_argument(
        "--require-moved-from",
        type=float,
        default=None,
        metavar="BASELINE_MDOT",
        help=(
            "Enable the operating-point convergence gate. The run must have MOVED its "
            "loop mdot away from this NOMINAL baseline (signed kg/s) by ~the physically "
            "expected fraction AND re-plateaued. Requires --expected-q-ratio (or "
            "--expected-move-frac)."
        ),
    )
    parser.add_argument(
        "--expected-q-ratio",
        type=float,
        default=None,
        help=(
            "Perturbed heater power / nominal heater power (e.g. 1.10 for +10%). The "
            "expected fractional mdot move is |ratio^(1/3) - 1| (laminar natural "
            "convection mdot ~ Q^(1/3)). Used only with --require-moved-from."
        ),
    )
    parser.add_argument(
        "--expected-move-frac",
        type=float,
        default=None,
        help="Override the expected fractional mdot move directly (else derived from --expected-q-ratio).",
    )
    parser.add_argument(
        "--move-tolerance",
        type=float,
        default=0.5,
        help=(
            "Fraction of the expected move the observed move must reach to count as 'moved' "
            "(default 0.5, i.e. at least half of the Q^(1/3) expectation)."
        ),
    )
    parser.add_argument(
        "--tau-thermal",
        type=float,
        default=None,
        help=(
            "Loop thermal relaxation time constant tau [s] (rho*cp*V_loop/UA). If given, "
            "advance-past-restart is reported in units of tau and runs with advance < "
            "--min-tau-advance*tau are flagged too-short."
        ),
    )
    parser.add_argument(
        "--min-tau-advance",
        type=float,
        default=3.0,
        help="Minimum advance/tau required (default 3 tau) when --tau-thermal is supplied.",
    )
    return parser.parse_args()


def resolve_case_dir(source_id: str, explicit: str | None) -> Path | None:
    if explicit:
        return Path(explicit)
    rows = read_registry_rows(REGISTRY_PATH)
    for row in rows:
        if row.get("source_id") == source_id:
            for key in ("local_link_path", "source_root"):
                candidate = row.get(key) or ""
                if candidate and Path(candidate).exists():
                    return Path(candidate)
    return None


def find_postprocessing(case_dir: Path) -> Path | None:
    direct = case_dir / "postProcessing"
    if direct.exists():
        return direct
    # Some staged trees nest the case one level down.
    for child in case_dir.iterdir() if case_dir.exists() else []:
        candidate = child / "postProcessing"
        if candidate.is_dir():
            return candidate
    return None


def latest_dat(monitor_dir: Path, filename: str) -> Path | None:
    """Return the highest-start-time copy of a monitor .dat (handles restarts)."""
    if not monitor_dir.exists():
        return None
    candidates: list[tuple[float, Path]] = []
    for sub in monitor_dir.iterdir():
        dat = sub / filename
        if dat.exists():
            try:
                candidates.append((float(sub.name), dat))
            except ValueError:
                candidates.append((-1.0, dat))
    if not candidates:
        return None
    candidates.sort(key=lambda item: item[0])
    return candidates[-1][1]


def merge_restart_series(monitor_dir: Path, filename: str) -> list[dict[str, float]]:
    """Concatenate all restart segments, later segments overriding earlier times."""
    if not monitor_dir.exists():
        return []
    merged: dict[float, float] = {}
    starts = sorted(
        (sub for sub in monitor_dir.iterdir() if (sub / filename).exists()),
        key=lambda sub: (float(sub.name) if sub.name.replace(".", "", 1).isdigit() else -1.0),
    )
    for sub in starts:
        for row in parse_scalar_series(sub / filename):
            merged[row["time"]] = row["value"]
    return [{"time": t, "value": merged[t]} for t in sorted(merged)]


def parse_wallheatflux_duty(dat_path: Path) -> dict[str, list[dict[str, float]]]:
    """Parse per-patch wallHeatFlux.dat into gross/in/out/net duty time series.

    Columns: Time  patch  min[W/m^2]  max[W/m^2]  Q[W]  q[W/m^2].
    We sum the per-patch total power Q[W] (column 5) per time, split by sign.
    Patches with exactly zero Q (e.g. non-conformal interface stubs) drop out
    naturally. Returns series for gross/heat_in/heat_out/net.
    """
    if not dat_path.exists():
        return {}
    per_time: dict[float, dict[str, float]] = {}
    with dat_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            parts = stripped.split()
            if len(parts) < 5:
                continue
            t = safe_float(parts[0])
            q_w = safe_float(parts[4])
            if t is None or q_w is None:
                continue
            bucket = per_time.setdefault(t, {"gross": 0.0, "heat_in": 0.0, "heat_out": 0.0, "net": 0.0})
            bucket["gross"] += abs(q_w)
            bucket["net"] += q_w
            if q_w >= 0.0:
                bucket["heat_in"] += q_w
            else:
                bucket["heat_out"] += q_w
    out: dict[str, list[dict[str, float]]] = {k: [] for k in ("gross", "heat_in", "heat_out", "net")}
    for t in sorted(per_time):
        for key in out:
            out[key].append({"time": t, "value": per_time[t][key]})
    return out


def merge_wallheatflux_duty(monitor_dir: Path) -> dict[str, list[dict[str, float]]]:
    """Concatenate wallHeatFlux.dat across restart segments."""
    if not monitor_dir.exists():
        return {}
    merged: dict[str, dict[float, float]] = {}
    starts = sorted(
        (sub for sub in monitor_dir.iterdir() if (sub / "wallHeatFlux.dat").exists()),
        key=lambda sub: (float(sub.name) if sub.name.replace(".", "", 1).isdigit() else -1.0),
    )
    for sub in starts:
        seg = parse_wallheatflux_duty(sub / "wallHeatFlux.dat")
        for key, series in seg.items():
            tgt = merged.setdefault(key, {})
            for row in series:
                tgt[row["time"]] = row["value"]
    return {key: [{"time": t, "value": vals[t]} for t in sorted(vals)] for key, vals in merged.items()}


def lag1_autocorr(values: np.ndarray) -> float:
    if values.size < 3:
        return 0.0
    centered = values - values.mean()
    denom = float(np.dot(centered, centered))
    if denom <= 0.0:
        return 0.0
    return float(np.dot(centered[:-1], centered[1:]) / denom)


def assess_series(
    name: str,
    series: list[dict[str, float]],
    args: argparse.Namespace,
    norm_scale: float | None = None,
    role: str = "primary",
) -> dict[str, Any]:
    """Assess one monitor series.

    norm_scale: if given (and finite, >0), drift/amp/CV/SE are normalized by this
      PHYSICAL scale instead of the series' own |mean|. Used for near-zero
      residual monitors (e.g. net heat imbalance normalized by gross duty).
    role: free-text tag ("hydraulic", "thermal_duty", "conservation", ...) used
      to roll up case-level verdicts correctly.
    """
    if len(series) < 4:
        return {"monitor": name, "status": "insufficient_data", "n_total": len(series), "role": role}
    times = np.array([row["time"] for row in series], dtype=float)
    values = np.array([row["value"] for row in series], dtype=float)
    t_end = float(times[-1])
    t_start = float(times[0])
    span = t_end - t_start
    win_start = t_end - args.window_frac * span
    mask = times >= win_start
    if mask.sum() < 4:
        mask = np.ones_like(times, dtype=bool)
    w_t = times[mask]
    w_v = values[mask]
    mean = float(np.mean(w_v))
    std = float(np.std(w_v, ddof=1)) if w_v.size > 1 else 0.0
    own_abs_mean = abs(mean) if abs(mean) > 1e-30 else float("nan")
    if norm_scale is not None and math.isfinite(norm_scale) and norm_scale > 1e-30:
        abs_mean = norm_scale
        norm_basis = "physical_scale"
    else:
        abs_mean = own_abs_mean
        norm_basis = "own_mean"
    # least-squares slope across the window
    slope = float(np.polyfit(w_t, w_v, 1)[0]) if w_v.size > 1 else 0.0
    window_len = float(w_t[-1] - w_t[0]) if w_v.size > 1 else 0.0
    drift_over_window = slope * window_len
    drift_frac = abs(drift_over_window) / abs_mean if math.isfinite(abs_mean) else float("nan")
    amp = float(np.max(w_v) - np.min(w_v))
    amp_frac = amp / abs_mean if math.isfinite(abs_mean) else float("nan")
    cv = (std / abs_mean) if math.isfinite(abs_mean) else float("nan")
    r1 = lag1_autocorr(w_v)
    n = int(w_v.size)
    n_eff = n * (1.0 - r1) / (1.0 + r1) if (1.0 + r1) > 0 else float(n)
    n_eff = max(1.0, n_eff)
    se = std / math.sqrt(n_eff)
    se_frac = (se / abs_mean) if math.isfinite(abs_mean) else float("nan")

    if math.isfinite(drift_frac) and math.isfinite(amp_frac) and drift_frac < args.stationary_drift and amp_frac < args.stationary_amp:
        verdict = "stationary"
    elif math.isfinite(drift_frac) and math.isfinite(amp_frac) and drift_frac < args.quasi_drift and amp_frac < args.quasi_amp:
        verdict = "quasi_stationary"
    else:
        verdict = "drifting_or_oscillatory"

    return {
        "monitor": name,
        "status": "assessed",
        "role": role,
        "norm_basis": norm_basis,
        "norm_scale": abs_mean,
        "n_total": len(series),
        "t_start_s": t_start,
        "t_end_s": t_end,
        "window_start_s": float(w_t[0]),
        "window_end_s": float(w_t[-1]),
        "n_window": n,
        "window_mean": mean,
        "window_std": std,
        "window_cv": cv,
        "drift_slope_per_s": slope,
        "drift_over_window": drift_over_window,
        "drift_frac_of_mean": drift_frac,
        "peak_to_peak": amp,
        "amp_frac_of_mean": amp_frac,
        "lag1_autocorr": r1,
        "n_eff": n_eff,
        "stderr_autocorr_corrected": se,
        "stderr_frac_of_mean": se_frac,
        "last_instantaneous_value": float(values[-1]),
        "last_minus_windowmean_frac": (float(values[-1]) - mean) / abs_mean if math.isfinite(abs_mean) else float("nan"),
        "verdict": verdict,
    }


# =====================================================================================
# OPERATING_POINT_GATE (T3): re-equilibration test for perturbation runs
# -------------------------------------------------------------------------------------
# WHY: a flat monitor is NECESSARY but NOT SUFFICIENT for a perturbation run to be at
# its NEW steady state. A run that restarts from the nominal converged field and is
# advanced only a fraction of the loop thermal relaxation time will sit, flat, at the
# OLD (nominal) fixed point -- "false-steady". See
# .agent/journal/2026-06-30/perturbation-run-convergence-audit.md.
#
# PHYSICS: for a laminar natural-circulation loop the buoyancy/friction balance gives
# mdot ~ Q^(1/3) (Grashof-driven flow, laminar friction ~ mdot). So a Q change by a
# ratio r should move mdot by |r^(1/3) - 1|:  +/-10% Q -> ~3.2% ; +/-5% Q -> ~1.6%.
# A run whose mdot has NOT moved by ~this much (within --move-tolerance) after a real
# Q perturbation has NOT re-equilibrated, regardless of how flat it looks.
#
# We ALSO report the advance-past-restart (sim time elapsed since the perturbation
# restart) and, when a thermal time constant tau is supplied, advance/tau. The restart
# time is detected from the monitor restart segments (see restart_time_from_segments).
# =====================================================================================


def restart_time_from_segments(monitor_dir: Path) -> float | None:
    """Detect the perturbation restart time from a monitor's restart segment dirs.

    Perturbation runs are staged from a nominal converged field. Their postProcessing
    contains restart segments named by their start time. Some staged trees also carry
    an inherited 't=0' (nominal warmup/continuation) segment; the perturbation proper
    begins at the smallest NON-zero segment start when such a zero segment coexists
    with later ones, else at the smallest segment start.
    """
    if not monitor_dir.exists():
        return None
    starts: list[float] = []
    for sub in monitor_dir.iterdir():
        if not sub.is_dir():
            continue
        try:
            starts.append(float(sub.name))
        except ValueError:
            continue
    if not starts:
        return None
    starts.sort()
    nonzero = [s for s in starts if s > 1e-9]
    if len(starts) > 1 and starts[0] <= 1e-9 and nonzero:
        return nonzero[0]
    return starts[0]


def expected_move_frac(args: argparse.Namespace) -> float | None:
    """Expected fractional mdot move from the Q perturbation (Q^(1/3) scaling)."""
    if args.expected_move_frac is not None:
        return abs(args.expected_move_frac)
    if args.expected_q_ratio is not None and args.expected_q_ratio > 0:
        return abs(args.expected_q_ratio ** (1.0 / 3.0) - 1.0)
    return None


def assess_operating_point(
    monitors: list[dict[str, Any]],
    hydraulic_verdict: str,
    pp: Path,
    args: argparse.Namespace,
) -> dict[str, Any]:
    """Apply the re-equilibration gate to the hydraulic (mdot) operating point.

    verdict values:
      * requalified          - moved by ~the expected amount AND plateaued (usable)
      * false_steady         - flat but NOT moved from nominal (restarted near old FP)
      * moving_not_plateaued - moved but hydraulic monitors not yet stationary
      * too_short            - advance < min_tau_advance*tau (insufficient runtime)
      * insufficient_move    - moved some, but below tolerance of expected
    """
    out: dict[str, Any] = {"applied": True, "baseline_mdot": args.require_moved_from}
    # Representative mdot: the test-section monitor if present, else first hydraulic.
    hyd = [m for m in monitors if m.get("role") == "hydraulic" and m.get("status") == "assessed"]
    ref = None
    for m in hyd:
        if "left_04_test_section" in m.get("monitor", ""):
            ref = m
            break
    if ref is None and hyd:
        ref = hyd[0]
    if ref is None:
        out.update({"verdict": "no_mdot_monitor", "note": "no assessable hydraulic monitor"})
        return out

    baseline = args.require_moved_from
    mdot_now = ref.get("window_mean", float("nan"))
    out["mdot_monitor"] = ref.get("monitor")
    out["mdot_window_mean"] = mdot_now
    out["nominal_mdot"] = baseline
    pct_moved = float("nan")
    if baseline is not None and abs(baseline) > 1e-30 and math.isfinite(mdot_now):
        pct_moved = (mdot_now - baseline) / abs(baseline)
    out["pct_moved"] = pct_moved

    exp_frac = expected_move_frac(args)
    out["expected_move_frac"] = exp_frac
    out["move_tolerance"] = args.move_tolerance

    # advance-past-restart
    restart_t = None
    for mon in MDOT_MONITOR_DIRS:
        rt = restart_time_from_segments(pp / mon)
        if rt is not None:
            restart_t = rt if restart_t is None else min(restart_t, rt)
    t_end = ref.get("t_end_s", float("nan"))
    advance = (t_end - restart_t) if (restart_t is not None and math.isfinite(t_end)) else float("nan")
    out["restart_time_s"] = restart_t
    out["t_end_s"] = t_end
    out["advance_s"] = advance
    out["tau_thermal_s"] = args.tau_thermal
    advance_over_tau = float("nan")
    if args.tau_thermal is not None and args.tau_thermal > 0 and math.isfinite(advance):
        advance_over_tau = advance / args.tau_thermal
    out["advance_over_tau"] = advance_over_tau

    plateaued = hydraulic_verdict in ("stationary", "quasi_stationary")
    out["plateaued"] = plateaued

    moved_enough = (
        exp_frac is not None
        and math.isfinite(pct_moved)
        and abs(pct_moved) >= args.move_tolerance * exp_frac
    )
    out["moved_enough"] = moved_enough

    too_short = (
        math.isfinite(advance_over_tau) and advance_over_tau < args.min_tau_advance
    )
    out["too_short"] = too_short

    # Verdict precedence: a not-moved run is false-steady even if it also is too short;
    # both are reported, but the headline is the most decision-relevant failure.
    if not moved_enough:
        if exp_frac is not None and math.isfinite(pct_moved) and abs(pct_moved) < 0.25 * exp_frac:
            verdict = "false_steady"
        else:
            verdict = "insufficient_move"
    elif not plateaued:
        verdict = "moving_not_plateaued"
    elif too_short:
        verdict = "too_short"
    else:
        verdict = "requalified"
    out["verdict"] = verdict
    out["usable_for_correlation"] = verdict == "requalified"
    return out


def assess_case(source_id: str, case_dir: Path, args: argparse.Namespace) -> dict[str, Any]:
    pp = find_postprocessing(case_dir)
    result: dict[str, Any] = {
        "source_id": source_id,
        "case_dir": relative_to_workspace(case_dir),
        "postprocessing_found": pp is not None,
        "monitors": [],
    }
    if pp is None:
        result["note"] = "no postProcessing directory found"
        return result
    # --- hydraulic monitors: loop mass flow rate (role -> 1D mdot prediction) ---
    for mon in MDOT_MONITOR_DIRS:
        series = merge_restart_series(pp / mon, "surfaceFieldValue.dat")
        if series:
            result["monitors"].append(assess_series(f"mdot::{mon}", series, args, role="hydraulic"))

    # --- thermal monitors: GROSS wall duty from per-patch wallHeatFlux.dat ---
    # This is the physically meaningful thermal steadiness QoI for HTC/Nu (see
    # the long justification comment near MDOT_MONITOR_DIRS).
    duty = merge_wallheatflux_duty(pp / "wallHeatFlux")
    gross_scale = float("nan")
    if duty.get("gross"):
        gross_assess = assess_series("wall_duty::gross", duty["gross"], args, role="thermal_duty")
        result["monitors"].append(gross_assess)
        gross_scale = gross_assess.get("window_mean", float("nan"))
        if duty.get("heat_in"):
            result["monitors"].append(assess_series("wall_duty::heat_in", duty["heat_in"], args, role="thermal_duty"))
        if duty.get("heat_out"):
            result["monitors"].append(assess_series("wall_duty::heat_out", duty["heat_out"], args, role="thermal_duty"))
        # net imbalance normalized by gross duty -> conservation/closure check,
        # NOT a steadiness flag. Excluded from the steadiness roll-up.
        if duty.get("net"):
            result["monitors"].append(
                assess_series("wall_duty::net_imbalance", duty["net"], args, norm_scale=abs(gross_scale), role="conservation")
            )

    # total_Q.dat (legacy net monitor): keep it but normalize by gross duty and
    # tag as conservation so it no longer pollutes the steadiness verdict.
    total_q = pp / "total_Q.dat"
    if total_q.exists():
        result["monitors"].append(
            assess_series("total_Q_net", parse_scalar_series(total_q), args, norm_scale=abs(gross_scale), role="conservation")
        )

    # Roll up SEPARATE hydraulic and thermal verdicts (conservation excluded).
    def rollup(roles: tuple[str, ...]) -> str:
        vs = [m.get("verdict") for m in result["monitors"] if m.get("status") == "assessed" and m.get("role") in roles]
        if not vs:
            return "no_assessable_monitors"
        if all(v == "stationary" for v in vs):
            return "stationary"
        if any(v == "drifting_or_oscillatory" for v in vs):
            return "drifting_or_oscillatory"
        return "quasi_stationary"

    result["hydraulic_verdict"] = rollup(("hydraulic",))
    result["thermal_verdict"] = rollup(("thermal_duty",))
    # Overall = worse of hydraulic/thermal (conservation reported separately).
    order = {"stationary": 0, "quasi_stationary": 1, "drifting_or_oscillatory": 2, "no_assessable_monitors": 3}
    result["case_verdict"] = max(
        (result["hydraulic_verdict"], result["thermal_verdict"]), key=lambda v: order.get(v, 3)
    )
    # Conservation headline: net imbalance as fraction of gross duty.
    cons = [m for m in result["monitors"] if m.get("role") == "conservation" and m.get("monitor") == "wall_duty::net_imbalance"]
    if cons:
        result["heat_closure_net_over_gross"] = cons[0].get("window_mean", float("nan")) / abs(gross_scale) if math.isfinite(gross_scale) and abs(gross_scale) > 0 else float("nan")
    result["gross_wall_duty_w"] = gross_scale
    # --- operating-point (re-equilibration) gate: T3 ---
    if args.require_moved_from is not None:
        result["operating_point"] = assess_operating_point(
            result["monitors"], result["hydraulic_verdict"], pp, args
        )
    if source_id == SALT_1_CAVEAT_ID:
        result["caveat"] = "Salt 1 Jin retained window is short; treat any steady claim as weaker."
    return result


def build_target_list(args: argparse.Namespace) -> list[str]:
    if args.paper_grade_salt_jin:
        return list(PAPER_GRADE_SALT_JIN)
    if args.source_id:
        return [args.source_id]
    rows = read_registry_rows(REGISTRY_PATH)
    return [r["source_id"] for r in rows if r.get("source_id") and r.get("status") != "inventory_only"]


def main() -> int:
    args = parse_args()
    targets = build_target_list(args)
    output_dir = Path(args.output_dir)
    ensure_dir(output_dir)

    thresholds = {
        "window_frac": args.window_frac,
        "stationary_drift": args.stationary_drift,
        "stationary_amp": args.stationary_amp,
        "quasi_drift": args.quasi_drift,
        "quasi_amp": args.quasi_amp,
    }
    case_results: list[dict[str, Any]] = []
    flat_rows: list[dict[str, Any]] = []
    for source_id in targets:
        case_dir = resolve_case_dir(source_id, args.case_dir if args.source_id else None)
        if case_dir is None or not case_dir.exists():
            case_results.append({"source_id": source_id, "postprocessing_found": False, "note": "case dir not resolved"})
            continue
        res = assess_case(source_id, case_dir, args)
        case_results.append(res)
        for mon in res.get("monitors", []):
            if mon.get("status") == "assessed":
                flat_rows.append({"source_id": source_id, **mon})

    payload = {
        "generated_at": iso_timestamp(),
        "method": "trailing-window stationarity (drift, peak-to-peak, autocorr-corrected SE)",
        "thresholds": thresholds,
        "targets": targets,
        "cases": case_results,
    }
    json_dump(output_dir / "time_convergence.json", payload)
    if flat_rows:
        fieldnames = list(flat_rows[0].keys())
        csv_dump(output_dir / "time_convergence_monitors.csv", fieldnames, flat_rows)

    # Console summary (so a human gets the headline without opening files).
    print(f"# Time-convergence assessment  ({iso_timestamp()})")
    print(f"# thresholds: {thresholds}")
    for res in case_results:
        verdict = res.get("case_verdict", "n/a")
        hyd = res.get("hydraulic_verdict", "n/a")
        thm = res.get("thermal_verdict", "n/a")
        print(f"\n## {res['source_id']}  ->  overall={verdict}  (hydraulic={hyd}, thermal={thm})")
        if math.isfinite(res.get("gross_wall_duty_w", float("nan"))):
            closure = res.get("heat_closure_net_over_gross", float("nan"))
            print(f"   gross wall duty ~ {res['gross_wall_duty_w']:.1f} W; net heat imbalance = {closure*100:+.2f}% of gross (closure check)")
        op = res.get("operating_point")
        if op and op.get("applied"):
            pm = op.get("pct_moved", float("nan"))
            ef = op.get("expected_move_frac")
            adv = op.get("advance_s", float("nan"))
            aot = op.get("advance_over_tau", float("nan"))
            aot_s = f" ({aot:.1f} tau)" if math.isfinite(aot) else ""
            ef_s = f"{ef*100:.2f}%" if ef is not None else "n/a"
            print(
                f"   OP-GATE: {op.get('verdict').upper()}  "
                f"mdot={op.get('mdot_window_mean'):.5g} vs nominal={op.get('nominal_mdot')}  "
                f"moved={pm*100:+.2f}% (expected~{ef_s}, plateaued={op.get('plateaued')})  "
                f"advance={adv:.0f}s{aot_s}"
            )
        if res.get("caveat"):
            print(f"   caveat: {res['caveat']}")
        for mon in res.get("monitors", []):
            if mon.get("status") != "assessed":
                print(f"   - {mon['monitor']}: {mon.get('status')}")
                continue
            print(
                f"   - {mon['monitor']:42s} {mon['verdict']:24s} "
                f"mean={mon['window_mean']:.4g} drift={mon['drift_frac_of_mean']*100:.2f}% "
                f"amp={mon['amp_frac_of_mean']*100:.2f}% SE={mon['stderr_frac_of_mean']*100:.2f}% "
                f"last-vs-mean={mon['last_minus_windowmean_frac']*100:+.2f}%"
            )
    print(f"\nWrote {relative_to_workspace(output_dir / 'time_convergence.json')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
