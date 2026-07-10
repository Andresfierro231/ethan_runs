#!/usr/bin/env python3
"""build_timeseries_steadystate_report.py — postprocessor time-series + steady-state.

Discovers every Ethan CFD run's OpenFOAM `postProcessing` scalar time series
(jadyn + modern runs), then for each unique case produces:

  * grouped value-vs-time SVGs (mdot legs, temperature probes, wall-temperature
    probes, total heat Q);
  * a last-window (~5 min of simulated time) SVG per group with a linear
    trendline, its equation, and R² in the legend;
  * a SEM-vs-averaging-time convergence SVG (CLT / 1-over-sqrt(t)) for loop mdot;
  * a full per-series statistics table (RMSE, variance, trend, autocorrelation
    time, effective N, standard error of the mean, steady-state verdict).

A cross-case `steady_state_summary.csv`, README, METHODOLOGY, DATA_DISCLOSURE,
inventory, and summary.json tie the package together. Everything is stdlib-only
and never mutates the solver output tree.

Usage:
    python tools/analyze/build_timeseries_steadystate_report.py
    python tools/analyze/build_timeseries_steadystate_report.py --window-seconds 300
    python tools/analyze/build_timeseries_steadystate_report.py --limit 3   # smoke test
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from datetime import datetime
from pathlib import Path

import openfoam_timeseries as ot
import timeseries_stats as ts
from openfoam_timeseries import Series
from svg_timeseries_chart import (
    line_chart,
    sem_convergence_chart,
    trend_window_chart,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = (REPO_ROOT
                  / "work_products/2026-07/2026-07-09/2026-07-09_timeseries_steadystate")
TASK_ID = "AGENT-244"
DEFAULT_WINDOW_S = 300.0   # "last ~5 minutes" of simulated time

GROUP_ORDER = ["mdot", "temperature", "wall_temperature", "heat"]
GROUP_TITLE = {
    "mdot": "Mass flow rate (mdot) vs time",
    "temperature": "Fluid temperature probes vs time",
    "wall_temperature": "Wall temperature probes vs time",
    "heat": "Net loop heat (total_Q) vs time",
}
GROUP_YLABEL = {
    "mdot": "mdot = sum(phi) (kg/s)",
    "temperature": "T (K)",
    "wall_temperature": "T_wall (K)",
    "heat": "Q (W)",
}

# Known scientific caveat carried into the summary (per CLAUDE.md / June work).
QPERT_CAVEAT_RE = re.compile(r"(hi\d*q|lo\d*q|balq)", re.I)


# ---------------------------------------------------------------------------
def mean_series(members: list[Series], name: str, group: str, unit: str) -> Series | None:
    """Mean across series over their common time grid (sign-preserving)."""
    if not members:
        return None
    common = set(members[0].t)
    for s in members[1:]:
        common &= set(s.t)
    if not common:
        return None
    times = sorted(common)
    lut = [{round(t, 6): y for t, y in zip(s.t, s.y)} for s in members]
    ys = []
    for t in times:
        key = round(t, 6)
        ys.append(sum(d[key] for d in lut) / len(lut))
    return Series(name=name, group=group, unit=unit, t=times, y=ys,
                  source_files=[f for s in members for f in s.source_files],
                  meta={"derived": "mean_across_series", "n_members": len(members)})


def fluid_label(slug: str) -> str:
    m = re.search(r"(salt|water)_?test_?(\d)", slug) or re.search(r"(salt|water)(\d)", slug)
    if m:
        return f"{m.group(1)}{m.group(2)}"
    return "unknown"


_CFG_TOKENS = ["optins", "hiins", "loins", "hi10q", "lo10q", "hi5q", "lo5q",
               "hiq", "loq", "balq", "nominal", "corrected", "basecont", "kirst",
               "loH", "hiH"]


def short_case_label(slug: str) -> str:
    """Compact human label for subtitles (full slug stays in provenance/stats)."""
    fluid = fluid_label(slug)
    date = re.search(r"(20\d\d-\d\d-\d\d)", slug)
    cfg = [t for t in _CFG_TOKENS if t.lower() in slug.lower()]
    bits = [fluid]
    if cfg:
        bits.append("/".join(dict.fromkeys(cfg)))
    if date:
        bits.append(date.group(1))
    return "  ·  ".join(bits)


def representative(group: str, members: list[Series]) -> Series | None:
    """The single series used for the windowed trend + CLT analysis of a group."""
    if not members:
        return None
    if group == "mdot":
        # By mass continuity every leg carries the same loop mdot; use the heater leg.
        for s in members:
            if "lower" in s.name or "heater" in s.name:
                return s
        return members[0]
    if group == "temperature":
        return None  # temperature keeps all probes as separate trend entries
    if group == "wall_temperature":
        return mean_series(members, "wall T (spatial mean)", group, members[0].unit)
    if group == "heat":
        return members[0]
    return members[0]


# ---------------------------------------------------------------------------
def process_case(case: ot.CaseInfo, out_dir: Path, window_s: float,
                 provenance: str) -> list[dict]:
    """Emit figures + return per-series stat rows for this case."""
    series = ot.load_case_series(case.postprocessing)
    if not series:
        return []
    by_group: dict[str, list[Series]] = {}
    for s in series:
        by_group.setdefault(s.group, []).append(s)

    case_dir = out_dir / "cases" / case.slug
    fig_dir = case_dir / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)

    stat_rows: list[dict] = []

    def stat_row(s: Series, analysis: ts.SeriesAnalysis | None, is_rep: bool) -> None:
        row = {"case_slug": case.slug, "fluid": fluid_label(case.slug),
               "group": s.group, "series": s.name, "unit": s.unit,
               "representative": is_rep, "n_total": len(s),
               "t_first": s.t[0] if s.t else "", "t_last": s.t[-1] if s.t else ""}
        row.update(analysis.flat() if analysis else {})
        stat_rows.append(row)

    for group in GROUP_ORDER:
        members = by_group.get(group)
        if not members:
            continue
        members = sorted(members, key=lambda s: s.name)
        unit = members[0].unit

        # ---- full time series ----
        line_chart(
            fig_dir / f"{group}_timeseries.svg",
            GROUP_TITLE[group], f"{short_case_label(case.slug)}  ·  full run",
            members, "time (s)", GROUP_YLABEL[group],
            f"Source: postProcessing under {case.postprocessing.relative_to(REPO_ROOT)}. "
            f"{'Ensemble + mean shown (many probes).' if len(members) > 8 else ''}",
            provenance)

        # ---- windowed trend entries ----
        if group == "temperature":
            trend_members = members
        else:
            rep = representative(group, members)
            trend_members = [rep] if rep else []

        entries: list[dict] = []
        for s in trend_members:
            if s is None:
                continue
            tw, yw = ts.window(s.t, s.y, window_s)
            an = ts.analyze(s.t, s.y, window_s)
            if an is None or len(tw) < ts.MIN_WINDOW_POINTS:
                continue
            entries.append({
                "name": s.name, "t": tw, "y": yw,
                "slope": an.fit.slope, "intercept": an.fit.intercept,
                "r2": an.fit.r2, "rmse": an.oscillation.rmse_about_trend,
                "mean": an.oscillation.mean, "sem": an.uncertainty.sem_corrected,
            })

        if entries:
            trend_window_chart(
                fig_dir / f"{group}_last{int(window_s)}s.svg",
                f"{GROUP_TITLE[group]} — last {int(window_s)} s",
                f"{short_case_label(case.slug)}  ·  trend, equation + R² in legend",
                entries, "time (s)", GROUP_YLABEL[group], unit,
                "Dashed = OLS trendline over the window. RMSE/variance/steady-state "
                "verdict and mean±SEM are in stats.csv. Slope units are (series unit)/s.",
                provenance)

        # ---- per-series stats rows (every individual series) ----
        rep_names = {e["name"] for e in entries}
        for s in members:
            an = ts.analyze(s.t, s.y, window_s)
            stat_row(s, an, is_rep=(s.name in rep_names))
        # wall-temperature representative (spatial mean) also gets a row
        if group == "wall_temperature":
            rep = representative(group, members)
            if rep is not None:
                stat_row(rep, ts.analyze(rep.t, rep.y, window_s), is_rep=True)

    # ---- CLT / SEM convergence for loop mdot ----
    mdot_rep = representative("mdot", by_group.get("mdot", []))
    if mdot_rep is not None:
        tw, yw = ts.window(mdot_rep.t, mdot_rep.y, window_s)
        pts = ts.running_sem(tw, yw)
        if pts:
            an = ts.analyze(mdot_rep.t, mdot_rep.y, window_s)
            rel = an.uncertainty.rel_sem_corrected * 100 if an else float("nan")
            sem_convergence_chart(
                fig_dir / "mdot_sem_convergence.svg",
                "Uncertainty of the mean vs averaging time (CLT)",
                f"{short_case_label(case.slug)}  ·  loop mdot (heater leg), last {int(window_s)} s",
                pts, "standard error of the mean (kg/s)",
                f"Observed SEM tracks the 1/√t CLT reference. Autocorrelation-corrected "
                f"relative SEM at full window ≈ {rel:.3g}% of the mean (see stats.csv).",
                provenance)

    # ---- per-case stats files ----
    fields = _stat_fields(stat_rows)
    with (case_dir / "stats.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for r in stat_rows:
            w.writerow({k: r.get(k, "") for k in fields})
    (case_dir / "stats.json").write_text(json.dumps(
        {"case_slug": case.slug, "postprocessing": str(case.postprocessing.relative_to(REPO_ROOT)),
         "window_seconds": window_s, "rows": stat_rows}, indent=2, default=str))
    return stat_rows


def _stat_fields(rows: list[dict]) -> list[str]:
    lead = ["case_slug", "fluid", "group", "series", "unit", "representative",
            "n_total", "t_first", "t_last"]
    seen = list(lead)
    for r in rows:
        for k in r:
            if k not in seen:
                seen.append(k)
    return seen


# ---------------------------------------------------------------------------
def build(out_dir: Path, window_s: float = DEFAULT_WINDOW_S, limit: int | None = None) -> dict:
    cases = ot.discover_cases(REPO_ROOT)
    unique = [c for c in cases if c.duplicate_of is None]
    if limit:
        unique = unique[:limit]
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().isoformat(timespec="seconds")
    provenance = (f"{TASK_ID} · OpenFOAM postProcessing time series · window={int(window_s)}s "
                  f"· generated {stamp} · see DATA_DISCLOSURE.md")

    # inventory (all cases incl. duplicates)
    with (out_dir / "case_inventory.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["slug", "fluid", "postprocessing",
                                           "fingerprint", "duplicate_of"])
        w.writeheader()
        for c in cases:
            w.writerow({"slug": c.slug, "fluid": fluid_label(c.slug),
                        "postprocessing": str(c.postprocessing.relative_to(REPO_ROOT)),
                        "fingerprint": c.fingerprint, "duplicate_of": c.duplicate_of or ""})

    all_rows: list[dict] = []
    for i, c in enumerate(unique, 1):
        print(f"[{i}/{len(unique)}] {c.slug}")
        all_rows += process_case(c, out_dir, window_s, provenance)

    # cross-case summary: representative rows only
    summary_rows = [r for r in all_rows if r.get("representative") and r.get("verdict")]
    _write_summary_csv(out_dir / "steady_state_summary.csv", summary_rows)

    def bucket(v: str) -> str:
        return "steady" if v == "steady" else ("quasi" if v.startswith("quasi") else "not_steady")

    counts = {"steady": 0, "quasi": 0, "not_steady": 0}
    counts_by_group: dict[str, dict[str, int]] = {}
    for r in summary_rows:
        b = bucket(r["verdict"])
        counts[b] += 1
        g = counts_by_group.setdefault(r["group"], {"steady": 0, "quasi": 0, "not_steady": 0})
        g[b] += 1

    write_docs(out_dir, cases, unique, window_s, summary_rows, counts, counts_by_group)

    summary = {
        "generated_at": stamp, "task": TASK_ID, "window_seconds": window_s,
        "cases_total": len(cases), "cases_unique": len(unique),
        "duplicates": len(cases) - len([c for c in cases if c.duplicate_of is None]),
        "series_rows": len(all_rows), "representative_rows": len(summary_rows),
        "verdict_counts": counts, "verdict_counts_by_group": counts_by_group,
        "reusable_modules": [
            "tools/analyze/openfoam_timeseries.py",
            "tools/analyze/timeseries_stats.py",
            "tools/analyze/svg_timeseries_chart.py",
        ],
        "outputs": {
            "per_case_dir": "cases/<slug>/",
            "cross_case_summary": "steady_state_summary.csv",
            "inventory": "case_inventory.csv",
            "methodology": "METHODOLOGY.md",
            "data_disclosure": "DATA_DISCLOSURE.md",
        },
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True))
    print(json.dumps({"cases_unique": len(unique), "verdicts": counts,
                      "out": str(out_dir)}, indent=2))
    return summary


def _write_summary_csv(path: Path, rows: list[dict]) -> None:
    cols = ["case_slug", "fluid", "group", "series", "unit", "n_window",
            "t_start", "t_end", "verdict", "rel_drift_over_window", "drift_ratio",
            "near_zero_mean", "trend_resolved",
            "osc_mean", "osc_rmse_about_mean", "osc_rmse_about_trend",
            "osc_var_about_mean", "osc_peak_to_peak", "osc_cov",
            "fit_slope", "fit_r2", "fit_slope_se", "fit_t_stat",
            "unc_tau_int", "unc_n_eff", "unc_sem_naive", "unc_sem_corrected",
            "unc_rel_sem_corrected"]
    with path.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in cols})


# ---------------------------------------------------------------------------
def write_docs(out_dir: Path, cases, unique, window_s, summary_rows, counts,
               counts_by_group) -> None:
    n_dup = len(cases) - len(unique)
    fluids = sorted({fluid_label(c.slug) for c in unique})
    group_lines = "\n".join(
        f"  - **{g}**: {counts_by_group[g]['steady']} steady, "
        f"{counts_by_group[g]['quasi']} quasi-steady, "
        f"{counts_by_group[g]['not_steady']} not steady"
        for g in GROUP_ORDER if g in counts_by_group)
    _write_methodology(out_dir, window_s)
    _write_disclosure(out_dir, window_s, cases, unique)
    readme = f"""# Postprocessor Time-Series & Steady-State Analysis — {TASK_ID}, 2026-07-09

Value-vs-time plots, last-window trend fits, oscillation/RMSE statistics, and a
central-limit-theorem uncertainty analysis for every Ethan CFD run's OpenFOAM
`postProcessing` scalar output (jadyn + modern runs).

## What is here

- `cases/<slug>/figures/` per case:
  - `<group>_timeseries.svg` — full run, grouped (mdot legs / temperature probes /
    wall-temperature probes / total_Q).
  - `<group>_last{int(window_s)}s.svg` — last {int(window_s)} s with a linear
    trendline, its **equation and R² in the legend**.
  - `mdot_sem_convergence.svg` — standard error of the mean vs averaging time
    with the **1/√t CLT reference**.
- `cases/<slug>/stats.csv` + `stats.json` — every series' full statistics.
- `steady_state_summary.csv` — one representative row per case/group: verdict,
  mean, RMSE (about mean and about trend), variance, CoV, trend slope/R²,
  autocorrelation time, effective N, SEM (naive + corrected), relative SEM.
- `case_inventory.csv` — all {len(cases)} postProcessing dirs with content
  fingerprints and duplicate flags ({n_dup} byte-identical duplicates excluded
  from analysis).
- `METHODOLOGY.md` — exact definitions of every statistic and the steady-state
  criteria. `DATA_DISCLOSURE.md` — inputs, units, sign conventions, exclusions.

## Coverage

- {len(unique)} unique cases (of {len(cases)} postProcessing dirs); fluids: {", ".join(fluids)}.
- Window = last {int(window_s)} s of simulated time ("last ~5 minutes").

## Headline (representative series, last-window verdict)

Overall: {counts['steady']} steady · {counts['quasi']} quasi-steady · {counts['not_steady']} not steady.

By quantity group:
{group_lines}

**Read this correctly.** The mass flow and temperatures are steady in almost
every case — the loops reach a stationary (often gently oscillating) state. The
"not steady" rows are dominated by the `heat` group, which is `total_Q`, the
**net heat residual** (heat in − out). That residual is ≈ 0 at steady state
(order 0.1 W against a loop heat scale of hundreds of W), so a small absolute
drift is a large *relative* drift — the verdict flags the residual's noisiness,
not a genuine thermal runaway. The only `mdot` rows flagged not-steady are the
salt3 corrected-Q perturbations (hi5q/hi10q), whose mass flow is still moving —
consistent with the corrected-Salt gate marking them "too short / needs extended
continuation."

See `steady_state_summary.csv` for the numbers behind each verdict (mean,
`drift_ratio`, `rel_drift_over_window`, `near_zero_mean`). Verdicts are advisory
and use the explicit thresholds in `METHODOLOGY.md`.

## Caveats

- All admitted CFD is `coarse_no_gci`; these are convergence/steadiness
  diagnostics, not mesh-converged results.
- The June Q-perturbation runs were previously flagged "false-steady" (mdot never
  moved). A "steady" verdict here means the *time series* is stationary; it does
  **not** certify the operating point is physically correct. Cross-check the
  corrected-Salt gate before using any perturbation row as evidence.
- `mdot` is `sum(phi)` through an oriented faceZone (kg/s for this compressible
  buoyant solver); by mass continuity all legs carry the same loop mdot, so the
  heater leg is the representative for trend/CLT.

## Reproduce

```bash
cd {REPO_ROOT}
python tools/analyze/build_timeseries_steadystate_report.py --window-seconds {int(window_s)}
python -m pytest tools/analyze/test_openfoam_timeseries.py tools/analyze/test_timeseries_stats.py -q
```
"""
    (out_dir / "README.md").write_text(readme)


def _write_methodology(out_dir: Path, window_s: float) -> None:
    txt = f"""# Methodology — statistics & steady-state criteria ({TASK_ID})

All statistics are computed on the **analysis window**: the samples whose
simulated time is within the last {int(window_s)} s of the run
(`t ≥ t_end − {int(window_s)}`). Implementation: `tools/analyze/timeseries_stats.py`
(pure Python; auditable).

## Linear trend (OLS)
Fit `y = a·t + b` by ordinary least squares.
- slope `a`, intercept `b`.
- `R² = 1 − SS_res/SS_tot`.
- slope standard error `se_a = sqrt( (SS_res/(n−2)) / Σ(t−t̄)² )`.
- slope t-statistic `t = a / se_a` (|t| > {ts.TSTAT_SIGNIF} → a statistically
  resolved trend; note the autocorrelation caveat below makes this optimistic).

## Oscillation / RMSE / variance
- `mean` = time-average over the window.
- **RMSE about the mean** = `sqrt( mean( (y−ȳ)² ) )` = the population standard
  deviation = RMS fluctuation amplitude. Its square is the **variance about the
  mean**.
- **RMSE about the trend** = `sqrt( mean( (y − (a·t+b))² ) )` = the *detrended*
  oscillation amplitude (removes any linear drift). Its square is the variance
  about the trend. Comparing the two RMSEs separates drift from oscillation.
- peak-to-peak = max − min; coefficient of variation `CoV = std/|mean|`.

## Autocorrelation & effective sample size
CFD samples are correlated in time, so naive statistics overstate confidence.
- Integrated autocorrelation time `τ_int = 1 + 2 Σ_k ρ_k`, summing the
  autocorrelation of the detrended residuals until the first non-positive ρ_k
  (initial-positive-sequence truncation).
- Effective independent samples `N_eff = N / τ_int`.

## Uncertainty of the mean (Central Limit Theorem)
- **Naive** standard error of the mean `SEM = σ/√N` — the textbook CLT result
  assuming independent samples; scales as 1/√N ∝ 1/√t at fixed sample rate.
- **Autocorrelation-corrected** `SEM = σ/√N_eff = σ·√(τ_int/N)` — the honest
  uncertainty for correlated CFD data.
- **Relative SEM** = SEM/|mean| compares the uncertainty to the average value.
- The `mdot_sem_convergence.svg` figure plots the running `σ(window)/√N` against
  averaging duration on log-log axes with a `σ_full/√t` reference line; a slope
  of −1/2 confirms CLT scaling.

## Steady-state verdict (advisory thresholds)
The verdict uses a **scale-free** primary metric so it stays valid when the mean
is near zero (e.g. net heat oscillating about ~0, where relative-to-mean drift
would explode):

- `drift_ratio = |a·W| / (RMSE about trend)` — the trend's total change across the
  window W = {int(window_s)} s, measured in units of the oscillation amplitude.
- `rel_drift = |a·W| / |mean|` — used only when the mean is well separated from
  zero (`|mean| > {ts.SNR_MEAN:.0f}·std`); otherwise reported as NaN and the row is
  flagged `near_zero_mean`.

Decision — two branches:

*When the mean is well separated from zero* (`|mean| > {ts.SNR_MEAN:.0f}·std`,
the usual case for mdot, temperature, and non-zero heat) judge drift by physical
significance relative to the mean:
- **not steady**: `rel_drift > {ts.DRIFT_QUASI:.3g}`.
- **steady**: `rel_drift < {ts.DRIFT_STEADY:.3g}` and `CoV < {ts.COV_STEADY:.3g}`.
- **quasi-steady**: in between.

*When the mean is near zero* (`near_zero_mean`, e.g. net heat about ~0, where
relative-to-mean drift is meaningless) judge by the scale-free `drift_ratio`:
- **not steady**: `drift_ratio > {ts.DRIFT_RATIO_DRIFT:.0f}`.
- **steady**: `drift_ratio < {ts.DRIFT_RATIO_STEADY:.0f}`.
- **quasi-steady**: in between.

`trend_resolved` (= `drift_ratio > {ts.DRIFT_RATIO_DRIFT:.0f}`) marks a drift that
stands clear of the oscillation band — note a drift can be statistically resolved
yet physically tiny (small vs a large mean), which correctly reads "quasi-steady".
Thresholds are explicit constants in `timeseries_stats.py`; the verdict is a
screening aid, not a physical certification.
"""
    (out_dir / "METHODOLOGY.md").write_text(txt)


def _write_disclosure(out_dir: Path, window_s: float, cases, unique) -> None:
    txt = f"""# Data Disclosure — Postprocessor Time-Series Analysis ({TASK_ID})

## Sources (READ-ONLY; never mutated)

Native OpenFOAM `postProcessing` outputs under `jadyn_runs/**`:

| Quantity group | Path pattern | Column used | Unit |
|---|---|---|---|
| mdot | `postProcessing/mdot_<leg>/<startTime>/surfaceFieldValue.dat` | `sum(phi)` | kg/s |
| temperature | `postProcessing/temperature_probes/<startTime>/T` | per-probe columns | K |
| wall_temperature | `postProcessing/wall_temperature_probes/<startTime>/T` | per-probe columns | K |
| heat | `postProcessing/total_Q.dat` | column 2 | W |

## Handling

- **Continuations**: each functionObject may have several `<startTime>`
  subdirectories; they are concatenated and de-duplicated on the time column
  (later/higher start wins at overlaps).
- **Duplicates**: {len(cases)} postProcessing dirs found; byte-identical copies
  (e.g. `failed_stage_preserved` and staging mirrors) are detected by content
  fingerprint and excluded from analysis, leaving {len(unique)} unique cases.
  All are listed with their fingerprint in `case_inventory.csv`.
- **Representatives** (for the windowed trend + CLT): loop `mdot` uses the heater
  leg (all legs carry the same mass flow by continuity); `wall_temperature` uses
  the spatial mean across probes; `temperature` keeps all probes; `heat` uses
  `total_Q`. Every *individual* series still gets a full stats row in the
  per-case `stats.csv`.

## Units / sign conventions

- `sum(phi)` is the surfaceFieldValue flux integral through an oriented faceZone;
  for this compressible buoyant solver it is a mass flow in kg/s and its sign
  reflects the faceZone orientation (legs may differ in sign; magnitudes agree).
- Temperatures are in kelvin; `total_Q` is in watts (sign per the solver's
  convention — net loop heat).

## What is NOT done here

- No mesh/GCI convergence (all cases `coarse_no_gci`).
- No field-sample (velocity/PIV/wallHeatFlux field) processing — only scalar time
  series. Per-patch heat accounting lives in the patchwise heat ledger.
- A "steady" verdict describes time-series stationarity only; it does not certify
  the operating point (see the false-steady Q-perturbation caveat in README).

Window = last {int(window_s)} s of simulated time. Every plotted value is
reproducible from the sources above via the reusable modules
`openfoam_timeseries.py`, `timeseries_stats.py`, `svg_timeseries_chart.py`.
"""
    (out_dir / "DATA_DISCLOSURE.md").write_text(txt)


# ---------------------------------------------------------------------------
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    ap.add_argument("--window-seconds", type=float, default=DEFAULT_WINDOW_S)
    ap.add_argument("--limit", type=int, default=None, help="process only first N cases")
    args = ap.parse_args(argv)
    build(args.output_dir, args.window_seconds, args.limit)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
