#!/usr/bin/env python3
"""Curate transient CFD monitor histories as quasi-steady observations with UQ.

This is the paper-grade layer above ``assess_time_convergence.py``. It is
read-only with respect to CFD cases: it reads postProcessing monitor histories,
evaluates multiple late-time windows, and writes an explicit observation ledger.

Scientific contract:

* Raw time samples are not independent closure-training rows.
* A window must carry a state, uncertainty components, and fit-use status.
* Coherent oscillations are not allowed to shrink away as 1/sqrt(N).
* Multiple windows from one relaxation path share an independence group.
* Corrected Salt / special-gate rows remain non-admissible until review.
"""
from __future__ import annotations

import argparse
import math
import sys
from dataclasses import dataclass
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
)
from tools.analyze import assess_time_convergence as atc  # noqa: E402


REGISTRY_PATH = WORKSPACE_ROOT / "registry" / "case_registry.csv"
DEFAULT_OUTPUT_DIR = (
    WORKSPACE_ROOT / "work_products" / "2026-07-07_time_window_quasi_steady_uq"
)

WINDOW_STATES = {
    "stationary",
    "quasi_stationary",
    "moving_not_plateaued",
    "oscillatory_not_steady",
    "short_or_early_terminated",
    "transient_model_only",
}

FIT_USE_STATUSES = {
    "fit_admissible",
    "provisional_sensitivity_only",
    "excluded_drifting",
    "excluded_oscillatory",
    "excluded_short",
    "excluded_gate_pending",
    "transient_model_required",
    "diagnostic_only",
}


@dataclass(frozen=True)
class WindowPolicy:
    stationary_drift: float = 0.01
    stationary_amp: float = 0.02
    quasi_drift: float = 0.05
    quasi_amp: float = 0.10
    min_samples: int = 20
    min_duration_s: float = 60.0
    block_count: int = 5
    min_cycles_for_oscillation: float = 1.5


@dataclass(frozen=True)
class SeriesSpec:
    qoi_name: str
    qoi_units: str
    role: str
    source_path: str
    series: list[dict[str, float]]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--source-id", help="Registered source_id to assess.")
    group.add_argument(
        "--paper-grade-salt-jin",
        action="store_true",
        help="Assess the Salt 1-4 Jin paper subset from the registry.",
    )
    group.add_argument(
        "--case-dir",
        help="Direct case directory containing or nesting postProcessing.",
    )
    parser.add_argument("--case-id", help="Case id used with --case-dir.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument(
        "--window-fracs",
        default="0.50,0.25,0.20,0.10",
        help="Comma-separated trailing fractions to evaluate; longest should be first.",
    )
    parser.add_argument("--min-samples", type=int, default=20)
    parser.add_argument("--min-duration-s", type=float, default=60.0)
    parser.add_argument("--stationary-drift", type=float, default=0.01)
    parser.add_argument("--stationary-amp", type=float, default=0.02)
    parser.add_argument("--quasi-drift", type=float, default=0.05)
    parser.add_argument("--quasi-amp", type=float, default=0.10)
    parser.add_argument("--block-count", type=int, default=5)
    parser.add_argument(
        "--special-gate-source",
        action="append",
        default=[],
        help=(
            "Source id requiring coordinator review before closure-fit admission. "
            "Can be repeated."
        ),
    )
    parser.add_argument(
        "--target-value",
        action="append",
        default=[],
        metavar="QOI=VALUE",
        help=(
            "Optional pass-through target. If a drifting window crosses this value, "
            "it is marked transient_model_required. Repeat per QOI."
        ),
    )
    return parser.parse_args()


def parse_window_fracs(value: str) -> list[float]:
    out: list[float] = []
    for part in value.split(","):
        stripped = part.strip()
        if not stripped:
            continue
        frac = float(stripped)
        if not (0.0 < frac <= 1.0):
            raise ValueError(f"window fraction must be in (0, 1]: {frac}")
        out.append(frac)
    if not out:
        raise ValueError("at least one window fraction is required")
    return sorted(set(out), reverse=True)


def parse_targets(values: list[str]) -> dict[str, float]:
    targets: dict[str, float] = {}
    for item in values:
        if "=" not in item:
            raise ValueError(f"--target-value must be QOI=VALUE, got {item!r}")
        name, raw = item.split("=", 1)
        targets[name.strip()] = float(raw)
    return targets


def resolve_case_dir(source_id: str, explicit: str | None = None) -> Path | None:
    if explicit:
        return Path(explicit)
    rows = read_registry_rows(REGISTRY_PATH)
    for row in rows:
        if row.get("source_id") != source_id:
            continue
        for key in ("local_link_path", "source_root"):
            raw = row.get(key) or ""
            if raw and Path(raw).exists():
                return Path(raw)
    return None


def resolve_targets(args: argparse.Namespace) -> list[dict[str, Any]]:
    if args.paper_grade_salt_jin:
        return [
            {"source_id": source_id, "case_dir": resolve_case_dir(source_id)}
            for source_id in atc.PAPER_GRADE_SALT_JIN
        ]
    if args.source_id:
        return [{"source_id": args.source_id, "case_dir": resolve_case_dir(args.source_id)}]
    case_dir = Path(args.case_dir)
    case_id = args.case_id or case_dir.name
    return [{"source_id": case_id, "case_dir": case_dir}]


def find_postprocessing(case_dir: Path) -> Path | None:
    return atc.find_postprocessing(case_dir)


def finite_scale(mean: float, values: np.ndarray) -> float:
    candidates = [abs(mean)]
    if values.size:
        candidates.append(float(np.nanmax(np.abs(values))))
        candidates.append(float(np.nanpercentile(np.abs(values), 95)))
    scale = max(c for c in candidates if math.isfinite(c)) if candidates else float("nan")
    return scale if scale > 1e-30 else float("nan")


def linear_fit(times: np.ndarray, values: np.ndarray) -> tuple[float, np.ndarray]:
    if values.size < 2:
        return 0.0, values - values
    slope, intercept = np.polyfit(times, values, 1)
    fitted = slope * times + intercept
    return float(slope), fitted


def lag1_autocorr(values: np.ndarray) -> float:
    if values.size < 3:
        return 0.0
    centered = values - np.mean(values)
    denom = float(np.dot(centered, centered))
    if denom <= 0.0:
        return 0.0
    return float(np.dot(centered[:-1], centered[1:]) / denom)


def integrated_autocorr(values: np.ndarray, max_lag: int | None = None) -> tuple[float, float]:
    """Return integrated autocorrelation time in samples and effective N."""
    n = int(values.size)
    if n < 3:
        return 1.0, float(max(n, 1))
    centered = values - np.mean(values)
    denom = float(np.dot(centered, centered))
    if denom <= 0.0:
        return 1.0, float(n)
    lag_cap = max_lag if max_lag is not None else min(max(n // 3, 1), 200)
    positive_rhos: list[float] = []
    for lag in range(1, lag_cap + 1):
        rho = float(np.dot(centered[:-lag], centered[lag:]) / denom)
        if not math.isfinite(rho) or rho <= 0.0:
            break
        positive_rhos.append(rho)
    tau = max(1.0, 1.0 + 2.0 * sum(positive_rhos))
    return tau, max(1.0, n / tau)


def dominant_period(times: np.ndarray, residual: np.ndarray) -> tuple[float, float]:
    if times.size < 8:
        return float("nan"), float("nan")
    duration = float(times[-1] - times[0])
    if duration <= 0.0:
        return float("nan"), float("nan")
    dt = float(np.median(np.diff(times)))
    if not math.isfinite(dt) or dt <= 0.0:
        return float("nan"), float("nan")
    centered = residual - np.mean(residual)
    if float(np.std(centered)) <= 0.0:
        return float("nan"), float("nan")
    spectrum = np.fft.rfft(centered)
    freqs = np.fft.rfftfreq(centered.size, d=dt)
    if freqs.size <= 1:
        return float("nan"), float("nan")
    amplitudes = np.abs(spectrum)
    amplitudes[0] = 0.0
    idx = int(np.argmax(amplitudes))
    freq = float(freqs[idx])
    if freq <= 0.0 or not math.isfinite(freq):
        return float("nan"), float("nan")
    period = 1.0 / freq
    return period, duration / period


def block_statistics(values: np.ndarray, block_count: int) -> tuple[int, float, float]:
    n = int(values.size)
    count = max(1, min(block_count, n))
    blocks = [block for block in np.array_split(values, count) if block.size]
    means = np.array([float(np.mean(block)) for block in blocks], dtype=float)
    if means.size <= 1:
        return int(means.size), 0.0, 0.0
    std = float(np.std(means, ddof=1))
    return int(means.size), std, std / math.sqrt(float(means.size))


def window_slice(
    series: list[dict[str, float]], window_frac: float
) -> tuple[np.ndarray, np.ndarray]:
    times = np.array([row["time"] for row in series], dtype=float)
    values = np.array([row["value"] for row in series], dtype=float)
    order = np.argsort(times)
    times = times[order]
    values = values[order]
    if times.size == 0:
        return times, values
    span = float(times[-1] - times[0])
    if span <= 0.0:
        return times, values
    start = float(times[-1] - window_frac * span)
    mask = times >= start
    return times[mask], values[mask]


def crosses_target(values: np.ndarray, target: float | None) -> bool:
    if target is None or values.size == 0:
        return False
    lo = float(np.min(values))
    hi = float(np.max(values))
    return lo <= target <= hi


def fit_status_for_state(
    state: str,
    needs_special_gate_scrutiny: bool,
    pass_through: bool,
    role: str = "",
) -> str:
    if role == "conservation":
        return "diagnostic_only"
    if needs_special_gate_scrutiny:
        return "excluded_gate_pending"
    if pass_through:
        return "transient_model_required"
    if state == "stationary":
        return "fit_admissible"
    if state == "quasi_stationary":
        return "provisional_sensitivity_only"
    if state == "short_or_early_terminated":
        return "excluded_short"
    if state == "oscillatory_not_steady":
        return "excluded_oscillatory"
    if state == "moving_not_plateaued":
        return "excluded_drifting"
    return "transient_model_required"


def assess_window(
    *,
    source_id: str,
    case_dir: Path,
    spec: SeriesSpec,
    window_frac: float,
    policy: WindowPolicy,
    target_value: float | None = None,
    needs_special_gate_scrutiny: bool = False,
) -> dict[str, Any]:
    w_t, w_v = window_slice(spec.series, window_frac)
    if w_t.size:
        window_duration = float(w_t[-1] - w_t[0])
        window_start = float(w_t[0])
        window_end = float(w_t[-1])
    else:
        window_duration = 0.0
        window_start = float("nan")
        window_end = float("nan")

    independence_group_id = f"{source_id}::{spec.qoi_name}::relaxation_path"
    window_id = f"{source_id}::{spec.qoi_name}::last_{window_frac:.2f}"
    base: dict[str, Any] = {
        "case_id": source_id,
        "source_id": source_id,
        "run_class": infer_run_class(source_id),
        "job_id": "",
        "campaign": "",
        "fluid": infer_fluid(source_id),
        "condition": "",
        "source_path": relative_to_workspace(case_dir),
        "qoi_source_path": spec.source_path,
        "window_id": window_id,
        "window_fraction": window_frac,
        "window_start_s": window_start,
        "window_end_s": window_end,
        "window_duration_s": window_duration,
        "n_samples": int(w_v.size),
        "qoi_name": spec.qoi_name,
        "qoi_units": spec.qoi_units,
        "role": spec.role,
        "independence_group_id": independence_group_id,
        "needs_special_gate_scrutiny": bool(needs_special_gate_scrutiny),
        "gate_status": "coordinator_review_required" if needs_special_gate_scrutiny else "not_flagged",
        "raw_observation": "",
        "interpretation": "",
    }
    if w_v.size < policy.min_samples or window_duration < policy.min_duration_s:
        return {
            **base,
            **empty_numeric_metrics(),
            "window_state": "short_or_early_terminated",
            "fit_use_status": fit_status_for_state(
                "short_or_early_terminated",
                needs_special_gate_scrutiny,
                False,
                spec.role,
            ),
            "uncertainty_method": "not_computed_short_window",
            "notes": (
                f"Window has {w_v.size} samples over {window_duration:.6g} s; "
                f"requires >= {policy.min_samples} samples and >= "
                f"{policy.min_duration_s:.6g} s."
            ),
        }

    mean = float(np.mean(w_v))
    std = float(np.std(w_v, ddof=1)) if w_v.size > 1 else 0.0
    min_v = float(np.min(w_v))
    max_v = float(np.max(w_v))
    p05 = float(np.percentile(w_v, 5))
    p95 = float(np.percentile(w_v, 95))
    scale = finite_scale(mean, w_v)
    cv = std / scale if math.isfinite(scale) else float("nan")
    slope, fitted = linear_fit(w_t, w_v)
    drift_abs = abs(slope * window_duration)
    drift_rel = drift_abs / scale if math.isfinite(scale) else float("nan")
    peak_to_peak_abs = max_v - min_v
    peak_to_peak_rel = peak_to_peak_abs / scale if math.isfinite(scale) else float("nan")
    residual = w_v - fitted
    rms_fluctuation = float(math.sqrt(np.mean(residual * residual)))
    lag1 = lag1_autocorr(residual)
    tau_samples, n_eff = integrated_autocorr(residual)
    dt = float(np.median(np.diff(w_t))) if w_t.size > 1 else float("nan")
    tau_s = tau_samples * dt if math.isfinite(dt) else float("nan")
    block_count, block_mean_std, block_mean_se = block_statistics(w_v, policy.block_count)
    period_s, cycles = dominant_period(w_t, residual)
    oscillation_envelope_abs = 0.5 * (p95 - p05)
    oscillation_envelope_rel = (
        oscillation_envelope_abs / scale if math.isfinite(scale) else float("nan")
    )
    uncertainty_random = std / math.sqrt(max(n_eff, 1.0))
    uncertainty_block = block_mean_se
    uncertainty_oscillation = max(oscillation_envelope_abs, block_mean_std)
    uncertainty_drift = 0.5 * drift_abs
    uncertainty_total = math.sqrt(
        uncertainty_random**2
        + max(uncertainty_block, uncertainty_oscillation) ** 2
        + uncertainty_drift**2
    )

    pass_through = crosses_target(w_v, target_value) and (
        math.isfinite(drift_rel) and drift_rel >= policy.quasi_drift
    )
    state = classify_window_state(
        drift_rel=drift_rel,
        peak_to_peak_rel=peak_to_peak_rel,
        oscillation_envelope_rel=oscillation_envelope_rel,
        cycles=cycles,
        pass_through=pass_through,
        policy=policy,
    )
    fit_use_status = fit_status_for_state(
        state, needs_special_gate_scrutiny, pass_through, spec.role
    )

    raw = (
        f"{spec.qoi_name} last {window_frac:.2f} window: mean={mean:.6g}, "
        f"drift_rel={drift_rel:.6g}, peak_to_peak_rel={peak_to_peak_rel:.6g}, "
        f"n_eff={n_eff:.6g}, uncertainty_total={uncertainty_total:.6g}."
    )
    interp = (
        "Closure-fit admissibility follows state, special gate, and pass-through "
        "rules; raw time samples are correlated and not independent training rows."
    )
    if pass_through:
        interp = (
            "Window crosses the supplied target while drifting; treat as passing "
            "through a state, not a new equilibrium."
        )

    return {
        **base,
        "mean": mean,
        "std": std,
        "min": min_v,
        "max": max_v,
        "p05": p05,
        "p95": p95,
        "peak_to_peak_abs": peak_to_peak_abs,
        "peak_to_peak_rel": peak_to_peak_rel,
        "rms_fluctuation": rms_fluctuation,
        "coefficient_of_variation": cv,
        "linear_slope": slope,
        "drift_abs": drift_abs,
        "drift_rel": drift_rel,
        "lag1_autocorr": lag1,
        "integrated_autocorr_time_samples": tau_samples,
        "integrated_autocorr_time_s": tau_s,
        "effective_sample_size": n_eff,
        "autocorr_corrected_standard_error": uncertainty_random,
        "block_count": block_count,
        "block_mean_std": block_mean_std,
        "block_mean_standard_error": block_mean_se,
        "dominant_period_s": period_s,
        "cycles_in_window": cycles,
        "oscillation_envelope_abs": oscillation_envelope_abs,
        "oscillation_envelope_rel": oscillation_envelope_rel,
        "uncertainty_random": uncertainty_random,
        "uncertainty_block": uncertainty_block,
        "uncertainty_oscillation": uncertainty_oscillation,
        "uncertainty_drift": uncertainty_drift,
        "uncertainty_total": uncertainty_total,
        "uncertainty_method": (
            "sqrt(random_autocorr^2 + max(block_se, oscillation_envelope)^2 "
            "+ drift_halfspan^2); coherent oscillation is a non-shrinking floor"
        ),
        "window_state": state,
        "fit_use_status": fit_use_status,
        "pass_through_target": target_value if target_value is not None else "",
        "pass_through_risk": bool(pass_through),
        "notes": "",
        "raw_observation": raw,
        "interpretation": interp,
    }


def empty_numeric_metrics() -> dict[str, Any]:
    keys = [
        "mean",
        "std",
        "min",
        "max",
        "p05",
        "p95",
        "peak_to_peak_abs",
        "peak_to_peak_rel",
        "rms_fluctuation",
        "coefficient_of_variation",
        "linear_slope",
        "drift_abs",
        "drift_rel",
        "lag1_autocorr",
        "integrated_autocorr_time_samples",
        "integrated_autocorr_time_s",
        "effective_sample_size",
        "autocorr_corrected_standard_error",
        "block_count",
        "block_mean_std",
        "block_mean_standard_error",
        "dominant_period_s",
        "cycles_in_window",
        "oscillation_envelope_abs",
        "oscillation_envelope_rel",
        "uncertainty_random",
        "uncertainty_block",
        "uncertainty_oscillation",
        "uncertainty_drift",
        "uncertainty_total",
        "pass_through_target",
        "pass_through_risk",
    ]
    return {key: "" for key in keys}


def classify_window_state(
    *,
    drift_rel: float,
    peak_to_peak_rel: float,
    oscillation_envelope_rel: float,
    cycles: float,
    pass_through: bool,
    policy: WindowPolicy,
) -> str:
    if pass_through:
        return "transient_model_only"
    if (
        math.isfinite(drift_rel)
        and math.isfinite(peak_to_peak_rel)
        and drift_rel < policy.stationary_drift
        and peak_to_peak_rel < policy.stationary_amp
    ):
        return "stationary"
    if (
        math.isfinite(drift_rel)
        and math.isfinite(peak_to_peak_rel)
        and drift_rel < policy.quasi_drift
        and peak_to_peak_rel < policy.quasi_amp
    ):
        return "quasi_stationary"
    if (
        math.isfinite(oscillation_envelope_rel)
        and math.isfinite(cycles)
        and oscillation_envelope_rel >= 0.5 * policy.quasi_amp
        and cycles >= policy.min_cycles_for_oscillation
    ):
        return "oscillatory_not_steady"
    if (
        math.isfinite(peak_to_peak_rel)
        and peak_to_peak_rel >= policy.quasi_amp
        and math.isfinite(drift_rel)
        and drift_rel < policy.quasi_drift
    ):
        return "oscillatory_not_steady"
    return "moving_not_plateaued"


def infer_fluid(source_id: str) -> str:
    lowered = source_id.lower()
    if "salt" in lowered:
        return "salt"
    if "water" in lowered:
        return "water"
    return ""


def infer_run_class(source_id: str) -> str:
    lowered = source_id.lower()
    if "corrected" in lowered or "hi" in lowered or "lo" in lowered:
        return "corrected_or_perturbation"
    if "jin" in lowered:
        return "jin_mainline"
    if "kirst" in lowered:
        return "kirst_historical"
    return ""


def discover_series(pp: Path) -> list[SeriesSpec]:
    specs: list[SeriesSpec] = []
    for monitor in atc.MDOT_MONITOR_DIRS:
        dat = pp / monitor / "surfaceFieldValue.dat"
        source_path = ""
        series = atc.merge_restart_series(pp / monitor, "surfaceFieldValue.dat")
        if series:
            latest = atc.latest_dat(pp / monitor, "surfaceFieldValue.dat")
            source_path = relative_to_workspace(latest) if latest else relative_to_workspace(dat)
            specs.append(
                SeriesSpec(
                    qoi_name=f"mdot::{monitor}",
                    qoi_units="kg/s",
                    role="hydraulic",
                    source_path=source_path,
                    series=series,
                )
            )
    duty = atc.merge_wallheatflux_duty(pp / "wallHeatFlux")
    for name, units, role in [
        ("gross", "W", "thermal_duty"),
        ("heat_in", "W", "thermal_duty"),
        ("heat_out", "W", "thermal_duty"),
        ("net", "W", "conservation"),
    ]:
        if duty.get(name):
            specs.append(
                SeriesSpec(
                    qoi_name=f"wall_duty::{name}",
                    qoi_units=units,
                    role=role,
                    source_path=relative_to_workspace(pp / "wallHeatFlux"),
                    series=duty[name],
                )
            )
    total_q = pp / "total_Q.dat"
    if total_q.exists():
        specs.append(
            SeriesSpec(
                qoi_name="total_Q_net",
                qoi_units="W",
                role="conservation",
                source_path=relative_to_workspace(total_q),
                series=parse_scalar_series(total_q),
            )
        )
    return specs


def is_special_gate_source(source_id: str, explicit: set[str]) -> bool:
    lowered = source_id.lower()
    return (
        source_id in explicit
        or "corrected" in lowered
        or "salt1_jin_hi10q_corrected" in lowered
    )


def select_primary(rows: list[dict[str, Any]]) -> None:
    by_group: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in rows:
        row["is_primary_window"] = False
        by_group.setdefault((row["source_id"], row["qoi_name"]), []).append(row)
    status_rank = {
        "fit_admissible": 0,
        "provisional_sensitivity_only": 1,
        "excluded_gate_pending": 2,
        "excluded_oscillatory": 3,
        "excluded_drifting": 4,
        "transient_model_required": 5,
        "excluded_short": 6,
        "diagnostic_only": 7,
    }
    for group_rows in by_group.values():
        best = min(
            group_rows,
            key=lambda row: (
                status_rank.get(row.get("fit_use_status", ""), 99),
                -float(row.get("window_duration_s") or 0.0),
                -float(row.get("n_samples") or 0.0),
            ),
        )
        best["is_primary_window"] = True


def fieldnames(rows: list[dict[str, Any]]) -> list[str]:
    preferred = [
        "case_id",
        "source_id",
        "run_class",
        "job_id",
        "campaign",
        "fluid",
        "condition",
        "qoi_name",
        "qoi_units",
        "role",
        "window_id",
        "is_primary_window",
        "window_fraction",
        "window_start_s",
        "window_end_s",
        "window_duration_s",
        "n_samples",
        "mean",
        "std",
        "min",
        "max",
        "p05",
        "p95",
        "peak_to_peak_abs",
        "peak_to_peak_rel",
        "rms_fluctuation",
        "coefficient_of_variation",
        "linear_slope",
        "drift_abs",
        "drift_rel",
        "lag1_autocorr",
        "integrated_autocorr_time_samples",
        "integrated_autocorr_time_s",
        "effective_sample_size",
        "autocorr_corrected_standard_error",
        "block_count",
        "block_mean_std",
        "block_mean_standard_error",
        "dominant_period_s",
        "cycles_in_window",
        "oscillation_envelope_abs",
        "oscillation_envelope_rel",
        "uncertainty_random",
        "uncertainty_block",
        "uncertainty_oscillation",
        "uncertainty_drift",
        "uncertainty_total",
        "uncertainty_method",
        "window_state",
        "fit_use_status",
        "independence_group_id",
        "gate_status",
        "needs_special_gate_scrutiny",
        "pass_through_target",
        "pass_through_risk",
        "source_path",
        "qoi_source_path",
        "raw_observation",
        "interpretation",
        "notes",
    ]
    keys = set()
    for row in rows:
        keys.update(row.keys())
    return [key for key in preferred if key in keys] + sorted(keys - set(preferred))


def summarize(rows: list[dict[str, Any]], targets: list[dict[str, Any]]) -> dict[str, Any]:
    primary = [row for row in rows if row.get("is_primary_window")]
    counts_by_state: dict[str, int] = {}
    counts_by_fit: dict[str, int] = {}
    for row in primary:
        counts_by_state[row["window_state"]] = counts_by_state.get(row["window_state"], 0) + 1
        counts_by_fit[row["fit_use_status"]] = counts_by_fit.get(row["fit_use_status"], 0) + 1
    return {
        "generated_at": iso_timestamp(),
        "method": (
            "multi-window quasi-steady curation with drift, autocorrelation, "
            "block means, oscillation envelope, and conservative temporal UQ"
        ),
        "targets": [
            {
                "source_id": target["source_id"],
                "case_dir": relative_to_workspace(target["case_dir"])
                if target.get("case_dir")
                else "",
                "case_dir_found": bool(target.get("case_dir")),
            }
            for target in targets
        ],
        "primary_window_count": len(primary),
        "candidate_window_count": len(rows),
        "counts_by_primary_state": counts_by_state,
        "counts_by_primary_fit_use_status": counts_by_fit,
        "recommendation": recommendation(primary),
        "window_states": sorted(WINDOW_STATES),
        "fit_use_statuses": sorted(FIT_USE_STATUSES),
    }


def recommendation(primary_rows: list[dict[str, Any]]) -> str:
    if not primary_rows:
        return "investigate: no primary windows were produced"
    admitted = [r for r in primary_rows if r.get("fit_use_status") == "fit_admissible"]
    gated = [r for r in primary_rows if r.get("fit_use_status") == "excluded_gate_pending"]
    excluded = [r for r in primary_rows if str(r.get("fit_use_status", "")).startswith("excluded")]
    transient = [r for r in primary_rows if r.get("fit_use_status") == "transient_model_required"]
    closure_rows = [r for r in primary_rows if r.get("fit_use_status") != "diagnostic_only"]
    if gated:
        return "hold/investigate: coordinator review required for special-gate rows"
    if excluded or transient:
        return "investigate: at least one primary window is not closure-fit admissible"
    if closure_rows and len(admitted) == len(closure_rows):
        return "admit admitted rows only; preserve independence_group_id during fitting"
    return "hold for sensitivity-only treatment unless coordinator admits quasi-stationary rows"


def write_readme(output_dir: Path, summary_payload: dict[str, Any]) -> None:
    lines = [
        "# Time-Window Quasi-Steady UQ",
        "",
        f"Generated: `{summary_payload['generated_at']}`",
        "",
        "## Objective",
        "",
        "Curate time-dependent CFD monitor histories into quasi-steady observations "
        "with explicit uncertainty, window-state labels, fit-use controls, and "
        "independence groups. Raw transient samples are not independent closure "
        "training rows.",
        "",
        "## Method",
        "",
        "- Candidate trailing windows are evaluated for each QOI.",
        "- Drift is measured by a linear fit over the window.",
        "- Random uncertainty uses an autocorrelation-corrected effective sample size.",
        "- Block means and a robust oscillation envelope are reported separately.",
        "- The total temporal uncertainty is conservative: random, drift, and the "
        "larger of block or oscillation components are combined by root-sum-square.",
        "- Persistent oscillation is treated as a non-shrinking uncertainty floor.",
        "- Multiple windows from the same relaxation path share one "
        "`independence_group_id`.",
        "- Corrected Salt / special-gate rows are not closure-fit admissible until "
        "coordinator review.",
        "",
        "## Outputs",
        "",
        "- `quasi_steady_observations.csv`: primary window per case/QOI.",
        "- `window_diagnostics.csv`: all evaluated candidate windows.",
        "- `excluded_or_provisional_windows.csv`: non-admitted primary rows.",
        "- `run_window_summary.json`: machine-readable summary and recommendation.",
        "",
        "## Recommendation",
        "",
        summary_payload["recommendation"],
        "",
        "## Raw Observations vs Interpretation",
        "",
        "Raw observations are the computed window statistics in the CSV/JSON outputs. "
        "Interpretation is limited to the explicit `window_state`, `fit_use_status`, "
        "`needs_special_gate_scrutiny`, and recommendation fields. Passing through a "
        "target while drifting is not treated as equilibrium evidence.",
    ]
    (output_dir / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    output_dir = ensure_dir(Path(args.output_dir))
    window_fracs = parse_window_fracs(args.window_fracs)
    target_values = parse_targets(args.target_value)
    policy = WindowPolicy(
        stationary_drift=args.stationary_drift,
        stationary_amp=args.stationary_amp,
        quasi_drift=args.quasi_drift,
        quasi_amp=args.quasi_amp,
        min_samples=args.min_samples,
        min_duration_s=args.min_duration_s,
        block_count=args.block_count,
    )
    targets = resolve_targets(args)
    special_sources = set(args.special_gate_source)

    diagnostics: list[dict[str, Any]] = []
    missing: list[dict[str, str]] = []
    for target in targets:
        source_id = target["source_id"]
        case_dir = target.get("case_dir")
        if case_dir is None or not Path(case_dir).exists():
            missing.append({"source_id": source_id, "reason": "case_dir_not_found"})
            continue
        pp = find_postprocessing(Path(case_dir))
        if pp is None:
            missing.append({"source_id": source_id, "reason": "postProcessing_not_found"})
            continue
        specs = discover_series(pp)
        if not specs:
            missing.append({"source_id": source_id, "reason": "no_supported_monitor_series"})
            continue
        needs_gate = is_special_gate_source(source_id, special_sources)
        for spec in specs:
            for frac in window_fracs:
                diagnostics.append(
                    assess_window(
                        source_id=source_id,
                        case_dir=Path(case_dir),
                        spec=spec,
                        window_frac=frac,
                        policy=policy,
                        target_value=target_values.get(spec.qoi_name),
                        needs_special_gate_scrutiny=needs_gate,
                    )
                )

    select_primary(diagnostics)
    primary_rows = [row for row in diagnostics if row.get("is_primary_window")]
    non_admitted = [
        row
        for row in primary_rows
        if row.get("fit_use_status") not in ("fit_admissible",)
    ]
    summary_payload = summarize(diagnostics, targets)
    if missing:
        summary_payload["missing_targets"] = missing

    if diagnostics:
        csv_dump(output_dir / "window_diagnostics.csv", fieldnames(diagnostics), diagnostics)
    if primary_rows:
        csv_dump(
            output_dir / "quasi_steady_observations.csv",
            fieldnames(primary_rows),
            primary_rows,
        )
    if non_admitted:
        csv_dump(
            output_dir / "excluded_or_provisional_windows.csv",
            fieldnames(non_admitted),
            non_admitted,
        )
    json_dump(output_dir / "run_window_summary.json", summary_payload)
    write_readme(output_dir, summary_payload)

    print("# Time-window quasi-steady UQ")
    print(f"# output_dir: {relative_to_workspace(output_dir)}")
    print(f"# candidate windows: {len(diagnostics)}")
    print(f"# primary observations: {len(primary_rows)}")
    print(f"# recommendation: {summary_payload['recommendation']}")
    if missing:
        print(f"# missing targets: {len(missing)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
