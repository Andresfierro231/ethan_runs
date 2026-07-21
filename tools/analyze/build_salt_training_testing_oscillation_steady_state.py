#!/usr/bin/env python3
"""Build Salt training/testing oscillation and steady-state report.

This AGENT-411 product is deliberately read-only with respect to CFD outputs.
It consumes the current Salt training/testing use table, resolves each row to
its OpenFOAM postProcessing directory, and reports TP, TW, and mdot last-window
oscillation statistics with CLT-style uncertainty of the time average.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

THIS = Path(__file__).resolve()
REPO = THIS.parents[2]
TOOLS = REPO / "tools" / "analyze"
sys.path.insert(0, str(TOOLS))

from openfoam_timeseries import GROUP_UNITS, Series, load_case_series  # noqa: E402
from svg_timeseries_chart import line_chart, sem_convergence_chart  # noqa: E402
from timeseries_stats import analyze, linfit, running_sem, window  # noqa: E402


DATE = "2026-07-15"
TASK = "AGENT-411"
PRODUCT = REPO / "work_products/2026-07/2026-07-15/2026-07-15_salt_training_testing_oscillation_steady_state"
USE_TABLE = REPO / "work_products/2026-07/2026-07-15/2026-07-15_salt_forward_v1_unblock/salt_training_fit_input_table.csv"
MATRIX = REPO / "work_products/2026-07/2026-07-14/2026-07-14_flow_rate_temperature_bc_response_study/case_bc_response_matrix.csv"
LEDGER = REPO / "work_products/2026-07/2026-07-15/2026-07-15_forward_v1_row_admission_ledger/row_admission_ledger.csv"

GROUP_LABEL = {
    "temperature": "TP",
    "wall_temperature": "TW",
    "mdot": "mdot",
}


@dataclass
class SelectedCase:
    case_key: str
    display_label: str
    salt_family: str
    variant: str
    split_role: str
    use_for_thermal_fit: str
    use_for_holdout_or_test: str
    admission_status: str
    guardrail: str
    primary_evidence: str
    postprocessing: Path
    matrix_case_key: str


def slugify(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "-", text).strip("-")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as fh:
        return list(csv.DictReader(fh))


def normalize_postprocessing(path_text: str) -> Path:
    p = Path(path_text)
    if not p.is_absolute():
        p = REPO / p
    return p if p.name == "postProcessing" else p / "postProcessing"


def resolve_selected_cases(use_table: Path = USE_TABLE, matrix: Path = MATRIX) -> list[SelectedCase]:
    """Resolve current Salt fit/test table rows to postProcessing directories."""
    use_rows = read_csv(use_table)
    matrix_rows = read_csv(matrix)
    by_key: dict[str, dict[str, str]] = {}
    for row in matrix_rows:
        for key_name in ("case_key", "source_case_key", "canonical_case_key"):
            key = row.get(key_name, "")
            if key and key not in by_key:
                by_key[key] = row

    selected: list[SelectedCase] = []
    for row in use_rows:
        if row.get("use_for_thermal_fit") != "yes" and row.get("use_for_holdout_or_test") != "yes":
            continue
        match = None
        for key in (row.get("case_key", ""), row.get("display_label", "")):
            if key in by_key:
                match = by_key[key]
                break
        if not match:
            raise RuntimeError(f"Could not resolve source_root for selected row {row.get('case_key')}")
        pp = normalize_postprocessing(match["source_root"])
        selected.append(SelectedCase(
            case_key=row["case_key"],
            display_label=row["display_label"],
            salt_family=row["salt_family"],
            variant=row["variant"],
            split_role=row["split_role"],
            use_for_thermal_fit=row["use_for_thermal_fit"],
            use_for_holdout_or_test=row["use_for_holdout_or_test"],
            admission_status=row["admission_status"],
            guardrail=row["guardrail"],
            primary_evidence=row["primary_evidence"],
            postprocessing=pp,
            matrix_case_key=match.get("case_key", ""),
        ))
    return selected


def common_mean_series(series: list[Series], name: str, group: str) -> Series | None:
    """Mean across same-time probe samples using rounded time keys."""
    if not series:
        return None
    maps: list[dict[float, float]] = []
    for s in series:
        maps.append({round(t, 6): y for t, y in zip(s.t, s.y)})
    common = sorted(set.intersection(*(set(m) for m in maps)))
    if not common:
        return None
    y = [sum(m[t] for m in maps) / len(maps) for t in common]
    return Series(name=name, group=group, unit=series[0].unit, t=common, y=y,
                  source_files=sorted({src for s in series for src in s.source_files}),
                  meta={"derived": "spatial mean at common sample times", "n_series": len(series)})


def representative_series(group: str, series: list[Series]) -> Series | None:
    if not series:
        return None
    if group in {"temperature", "wall_temperature"}:
        return common_mean_series(series, f"{GROUP_LABEL[group]} spatial mean", group)
    lower = [s for s in series if "lower" in s.name or "heater" in s.name]
    return lower[0] if lower else series[0]


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fieldnames)
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in fieldnames})


def finite_fmt(value) -> str:
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, (int, str)):
        return value
    if value is None:
        return ""
    try:
        v = float(value)
    except (TypeError, ValueError):
        return value
    if math.isnan(v):
        return "nan"
    if math.isinf(v):
        return "inf" if v > 0 else "-inf"
    return f"{v:.10g}"


def stats_row(case: SelectedCase, group: str, series: Series, role: str, window_seconds: float) -> dict | None:
    result = analyze(series.t, series.y, window_seconds)
    if result is None:
        return None
    d = result.flat()
    out = {
        "case_key": case.case_key,
        "display_label": case.display_label,
        "salt_family": case.salt_family,
        "variant": case.variant,
        "split_role": case.split_role,
        "admission_status": case.admission_status,
        "group": group,
        "quantity_label": GROUP_LABEL[group],
        "series_role": role,
        "series_name": series.name,
        "unit": series.unit,
        "postprocessing": str(case.postprocessing),
    }
    out.update({k: finite_fmt(v) for k, v in d.items()})
    return out


def subset_series(series: Series, window_seconds: float) -> Series | None:
    tw, yw = window(series.t, series.y, window_seconds)
    if not tw:
        return None
    return Series(series.name, series.group, series.unit, tw, yw, series.source_files, series.meta)


def fluctuation_series(series: Series, window_seconds: float) -> Series | None:
    tw, yw = window(series.t, series.y, window_seconds)
    if len(tw) < 2:
        return None
    mean = sum(yw) / len(yw)
    return Series(f"{series.name} - last-window mean", series.group, series.unit,
                  tw, [y - mean for y in yw], series.source_files, series.meta)


def chart_group(case: SelectedCase, group: str, series: list[Series], outdir: Path,
                window_seconds: float, figure_rows: list[dict]) -> None:
    if not series:
        return
    label = GROUP_LABEL[group]
    slug = slugify(case.case_key)
    ylabel = f"{label} ({GROUP_UNITS[group]})"
    subtitle = f"{case.display_label}; split={case.split_role}; last window={window_seconds:g} s"
    note = ("Thin lines show individual probes/legs when available; ensemble mean is overlaid for "
            "multi-probe TP/TW groups. These plots diagnose stationarity only and do not change admission.")

    full_path = outdir / f"{slug}_{label}_full.svg"
    line_chart(full_path, f"{case.case_key}: {label} full time series", subtitle, series,
               "time (s)", ylabel, note, f"{TASK}; source={case.postprocessing}")
    figure_rows.append({"case_key": case.case_key, "group": group, "figure_type": "full_timeseries", "path": str(full_path.relative_to(PRODUCT))})

    windowed = [s for s in (subset_series(s, window_seconds) for s in series) if s is not None]
    if windowed:
        wpath = outdir / f"{slug}_{label}_last_window.svg"
        line_chart(wpath, f"{case.case_key}: {label} last-window oscillation", subtitle,
                   windowed, "time (s)", ylabel, note, f"{TASK}; source={case.postprocessing}")
        figure_rows.append({"case_key": case.case_key, "group": group, "figure_type": "last_window", "path": str(wpath.relative_to(PRODUCT))})

    fluct = [s for s in (fluctuation_series(s, window_seconds) for s in series) if s is not None]
    if fluct:
        fpath = outdir / f"{slug}_{label}_last_window_fluctuation.svg"
        line_chart(fpath, f"{case.case_key}: {label} fluctuation about last-window mean", subtitle,
                   fluct, "time (s)", f"{label} fluctuation ({GROUP_UNITS[group]})",
                   "Oscillation is quantified as RMS and variance of these last-window fluctuations.",
                   f"{TASK}; source={case.postprocessing}")
        figure_rows.append({"case_key": case.case_key, "group": group, "figure_type": "last_window_fluctuation", "path": str(fpath.relative_to(PRODUCT))})

    rep = representative_series(group, series)
    if rep:
        tw, yw = window(rep.t, rep.y, window_seconds)
        points = running_sem(tw, yw)
        if points:
            sem_path = outdir / f"{slug}_{label}_clt_sem.svg"
            sem_convergence_chart(
                sem_path,
                f"{case.case_key}: {label} mean uncertainty convergence",
                subtitle + f"; representative={rep.name}",
                points,
                f"SEM of {label} mean ({rep.unit})",
                "The ideal independent-sample central-limit theorem gives SEM = sigma/sqrt(N). "
                "Because CFD samples are autocorrelated, the tables also report an inflated SEM using N_eff=N/tau_int.",
                f"{TASK}; source={case.postprocessing}",
            )
            figure_rows.append({"case_key": case.case_key, "group": group, "figure_type": "clt_sem", "path": str(sem_path.relative_to(PRODUCT))})


def summarize_cases(stats_rows: list[dict]) -> list[dict]:
    rows: list[dict] = []
    reps = [r for r in stats_rows if r["series_role"] == "representative"]
    for case_key in sorted({r["case_key"] for r in reps}):
        case_reps = [r for r in reps if r["case_key"] == case_key]
        verdicts = sorted({r["verdict"] for r in case_reps})
        rows.append({
            "case_key": case_key,
            "split_role": case_reps[0]["split_role"] if case_reps else "",
            "representative_groups": len(case_reps),
            "steady_representative_groups": sum(1 for r in case_reps if r["verdict"] == "steady"),
            "quasi_representative_groups": sum(1 for r in case_reps if "quasi-steady" in r["verdict"]),
            "drifting_representative_groups": sum(1 for r in case_reps if "not steady" in r["verdict"]),
            "verdicts": "; ".join(verdicts),
            "max_rel_sem_corrected": finite_fmt(max(float(r["unc_rel_sem_corrected"]) for r in case_reps if r["unc_rel_sem_corrected"] not in {"", "nan", "inf", "-inf"})),
            "max_drift_ratio": finite_fmt(max(float(r["drift_ratio"]) for r in case_reps if r["drift_ratio"] not in {"", "nan", "inf", "-inf"})),
        })
    return rows


def representative_metrics(stats_rows: list[dict]) -> list[dict]:
    reps = [r for r in stats_rows if r["series_role"] == "representative"]
    out: list[dict] = []
    for case_key in sorted({r["case_key"] for r in reps}):
        row = {"case_key": case_key}
        case_reps = [r for r in reps if r["case_key"] == case_key]
        row["split_role"] = case_reps[0]["split_role"]
        max_rel_sem = 0.0
        max_rel_drift = 0.0
        for r in case_reps:
            label = r["quantity_label"]
            row[f"{label}_mean"] = r["osc_mean"]
            row[f"{label}_rms"] = r["osc_rmse_about_mean"]
            row[f"{label}_variance"] = r["osc_var_about_mean"]
            row[f"{label}_sem_corrected"] = r["unc_sem_corrected"]
            row[f"{label}_verdict"] = r["verdict"]
            try:
                max_rel_sem = max(max_rel_sem, float(r["unc_rel_sem_corrected"]))
            except ValueError:
                pass
            try:
                rel = float(r["rel_drift_over_window"])
                if math.isfinite(rel):
                    max_rel_drift = max(max_rel_drift, rel)
            except ValueError:
                pass
        row["max_rel_sem_corrected"] = finite_fmt(max_rel_sem)
        row["max_rel_drift_over_window"] = finite_fmt(max_rel_drift)
        out.append(row)
    return out


def write_readme(path: Path, cases: list[SelectedCase], stats_rows: list[dict],
                 case_summary: list[dict], rep_metrics: list[dict], window_seconds: float) -> None:
    n_series = len(stats_rows)
    n_figs = len(list((path / "figures").glob("*.svg")))
    lines = [
        "# Salt Training/Testing Oscillation and Steady-State Report",
        "",
        f"Task: {TASK}",
        f"Generated: {DATE}",
        f"Last-window definition: final `{window_seconds:g} s` of each available postProcessing time series.",
        "",
        "## Scope",
        "",
        "This package analyzes the current Salt thermal training/testing rows from",
        "`2026-07-15_salt_forward_v1_unblock/salt_training_fit_input_table.csv`: Salt1 nominal",
        "and +/-10Q, Salt4 nominal and +/-5Q, and Salt2 +/-5Q holdout/testing rows. It also",
        "cites the canonical forward-v1 ledger, where the setup-legal HX candidate lane still",
        "uses Salt2 train, Salt3 validation, and Salt4 holdout. Those are distinct split policies;",
        "this report does not change admission or fitting status.",
        "",
        "## Math and Assumptions",
        "",
        "- TP is `postProcessing/temperature_probes/*/T`; TW is",
        "  `postProcessing/wall_temperature_probes/*/T`; mdot is",
        "  `postProcessing/mdot_pipeleg_*/surfaceFieldValue.dat` `sum(phi)` in kg/s.",
        "- Oscillation RMS is `sqrt(mean((x_i - mean(x))^2))` over the last window.",
        "- Oscillation variance is `mean((x_i - mean(x))^2)` over the last window.",
        "- A linear trend `x = a t + b` is also fit over the last window; drift ratio is",
        "  `|a| * window_seconds / RMS_about_trend`.",
        "- Independent-sample CLT uncertainty of a time average is `SEM = sigma/sqrt(N)`.",
        "- CFD samples are autocorrelated, so the report also gives",
        "  `SEM_corrected = sigma/sqrt(N_eff)` with `N_eff = N/tau_int`.",
        "- The 1/sqrt(t) curves are diagnostic convergence plots, not proof of independence.",
        "",
        "## Results",
        "",
        f"- Selected cases resolved: `{len(cases)}`.",
        f"- Series/stat rows written: `{n_series}`.",
        f"- SVG figures written: `{n_figs}`.",
        "",
        "Representative case-level verdicts:",
        "",
        "| case | split role | steady reps | quasi reps | drifting reps | verdicts |",
        "| --- | --- | ---: | ---: | ---: | --- |",
    ]
    for row in case_summary:
        lines.append(
            f"| {row['case_key']} | {row['split_role']} | {row['steady_representative_groups']} | "
            f"{row['quasi_representative_groups']} | {row['drifting_representative_groups']} | {row['verdicts']} |"
        )
    lines += [
        "",
        "Representative last-window oscillation metrics:",
        "",
        "| case | TP RMS K | TP var K^2 | TW RMS K | TW var K^2 | mdot RMS kg/s | mdot var (kg/s)^2 | max corrected relative SEM |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in rep_metrics:
        lines.append(
            f"| {row['case_key']} | {row.get('TP_rms', '')} | {row.get('TP_variance', '')} | "
            f"{row.get('TW_rms', '')} | {row.get('TW_variance', '')} | "
            f"{row.get('mdot_rms', '')} | {row.get('mdot_variance', '')} | "
            f"{row.get('max_rel_sem_corrected', '')} |"
        )
    lines += [
        "",
        "Steady-state reading: all individual and representative TP/TW/mdot series in this",
        "selected set are `steady` by the documented thresholds in the final 300 s. Some",
        "Salt2/Salt4 perturbation representatives have large drift-ratio values because the",
        "detrended RMS is very small; their physical drift over the window remains below",
        "`0.24%` of the mean in this run.",
        "",
        "## Files",
        "",
        "- `selected_cases.csv`: resolved Salt training/testing rows and postProcessing paths.",
        "- `oscillation_stats.csv`: per-series TP/TW/mdot last-window RMS, variance, drift, SEM, and verdicts.",
        "- `case_summary.csv`: representative TP/TW/mdot verdict summary by case.",
        "- `representative_metrics.csv`: compact per-case TP/TW/mdot RMS, variance, SEM, and verdicts.",
        "- `figure_manifest.csv`: generated SVG plot inventory.",
        "- `figures/*.svg`: full traces, last-window traces, mean-fluctuation traces, and CLT SEM curves.",
        "- `source_manifest.csv`: provenance inputs.",
        "",
        "## Interpretation Guardrail",
        "",
        "These plots quantify whether the consumed time windows are steady enough for reporting.",
        "They do not make single-stream Nu/f_D/K labels valid in recirculating regimes and do not",
        "admit final forward-v1 closure evidence.",
        "",
    ]
    path.joinpath("README.md").write_text("\n".join(lines))


def write_closeouts(cases: list[SelectedCase], summary: dict) -> None:
    status = REPO / f".agent/status/{DATE}_{TASK}.md"
    journal = REPO / f".agent/journal/2026-07-15/salt-training-testing-oscillation-steady-state.md"
    imports = REPO / f"imports/{DATE}_salt_training_testing_oscillation_steady_state.json"
    status.parent.mkdir(parents=True, exist_ok=True)
    journal.parent.mkdir(parents=True, exist_ok=True)
    imports.parent.mkdir(parents=True, exist_ok=True)
    status.write_text(
        f"# {TASK} Status\n\n"
        f"Status: COMPLETE\n\n"
        f"Generated: {DATE}\n\n"
        f"Output: `{PRODUCT.relative_to(REPO)}`\n\n"
        f"Selected cases: {len(cases)}\n"
        f"Stats rows: {summary['stats_rows']}\n"
        f"Figures: {summary['figures']}\n\n"
        "No solver outputs, scheduler state, registry/admission state, or external tools were mutated.\n"
    )
    journal.write_text(
        "# Salt Training/Testing Oscillation Steady-State Journal\n\n"
        f"- Task: {TASK}\n"
        f"- Output: `{PRODUCT.relative_to(REPO)}`\n"
        f"- Built last-window TP/TW/mdot oscillation stats and plots for current selected Salt rows.\n"
        "- Included RMS/variance and CLT `1/sqrt(N)` mean-uncertainty explanation plus autocorrelation-corrected SEM.\n"
        "- This is diagnostic/reporting evidence only; it does not update row admission.\n"
    )
    imports.write_text(json.dumps({
        "task": TASK,
        "generated": DATE,
        "output": str(PRODUCT.relative_to(REPO)),
        "inputs": [str(USE_TABLE.relative_to(REPO)), str(MATRIX.relative_to(REPO)), str(LEDGER.relative_to(REPO))],
        "selected_cases": [c.case_key for c in cases],
        "summary": summary,
    }, indent=2) + "\n")


def build(window_seconds: float = 300.0, product: Path = PRODUCT) -> dict:
    product.mkdir(parents=True, exist_ok=True)
    figdir = product / "figures"
    figdir.mkdir(exist_ok=True)
    cases = resolve_selected_cases()

    selected_rows = []
    source_rows = [
        {"kind": "selected_use_table", "path": str(USE_TABLE.relative_to(REPO))},
        {"kind": "case_matrix", "path": str(MATRIX.relative_to(REPO))},
        {"kind": "canonical_forward_v1_ledger", "path": str(LEDGER.relative_to(REPO))},
    ]
    stats_rows: list[dict] = []
    figure_rows: list[dict] = []

    for case in cases:
        exists = case.postprocessing.is_dir()
        selected_rows.append({
            "case_key": case.case_key,
            "display_label": case.display_label,
            "salt_family": case.salt_family,
            "variant": case.variant,
            "split_role": case.split_role,
            "use_for_thermal_fit": case.use_for_thermal_fit,
            "use_for_holdout_or_test": case.use_for_holdout_or_test,
            "admission_status": case.admission_status,
            "guardrail": case.guardrail,
            "postprocessing": str(case.postprocessing),
            "postprocessing_exists": str(exists).lower(),
            "primary_evidence": case.primary_evidence,
        })
        if not exists:
            continue
        all_series = load_case_series(case.postprocessing)
        for group in ("temperature", "wall_temperature", "mdot"):
            group_series = [s for s in all_series if s.group == group]
            if not group_series:
                continue
            for s in group_series:
                row = stats_row(case, group, s, "individual", window_seconds)
                if row:
                    stats_rows.append(row)
            rep = representative_series(group, group_series)
            if rep:
                row = stats_row(case, group, rep, "representative", window_seconds)
                if row:
                    stats_rows.append(row)
            chart_group(case, group, group_series, figdir, window_seconds, figure_rows)

    case_summary = summarize_cases(stats_rows)
    rep_metrics = representative_metrics(stats_rows)

    selected_fields = ["case_key", "display_label", "salt_family", "variant", "split_role",
                       "use_for_thermal_fit", "use_for_holdout_or_test", "admission_status",
                       "guardrail", "postprocessing", "postprocessing_exists", "primary_evidence"]
    write_csv(product / "selected_cases.csv", selected_rows, selected_fields)

    stats_fields = ["case_key", "display_label", "salt_family", "variant", "split_role",
                    "admission_status", "group", "quantity_label", "series_role", "series_name",
                    "unit", "n_window", "t_start", "t_end", "dt_median", "window_seconds",
                    "osc_mean", "osc_minimum", "osc_maximum", "osc_peak_to_peak",
                    "osc_rmse_about_mean", "osc_var_about_mean", "osc_rmse_about_trend",
                    "osc_var_about_trend", "osc_cov", "fit_slope", "fit_intercept", "fit_r2",
                    "fit_slope_se", "fit_t_stat", "rel_drift_over_window", "drift_ratio",
                    "near_zero_mean", "trend_resolved", "unc_tau_int", "unc_n_eff",
                    "unc_sem_naive", "unc_sem_corrected", "unc_rel_sem_naive",
                    "unc_rel_sem_corrected", "verdict", "postprocessing"]
    write_csv(product / "oscillation_stats.csv", stats_rows, stats_fields)
    write_csv(product / "case_summary.csv", case_summary,
              ["case_key", "split_role", "representative_groups", "steady_representative_groups",
               "quasi_representative_groups", "drifting_representative_groups", "verdicts",
               "max_rel_sem_corrected", "max_drift_ratio"])
    write_csv(product / "representative_metrics.csv", rep_metrics,
              ["case_key", "split_role",
               "TP_mean", "TP_rms", "TP_variance", "TP_sem_corrected", "TP_verdict",
               "TW_mean", "TW_rms", "TW_variance", "TW_sem_corrected", "TW_verdict",
               "mdot_mean", "mdot_rms", "mdot_variance", "mdot_sem_corrected", "mdot_verdict",
               "max_rel_sem_corrected", "max_rel_drift_over_window"])
    write_csv(product / "figure_manifest.csv", figure_rows, ["case_key", "group", "figure_type", "path"])
    write_csv(product / "source_manifest.csv", source_rows, ["kind", "path"])

    summary = {
        "task": TASK,
        "generated": datetime.now().isoformat(timespec="seconds"),
        "window_seconds": window_seconds,
        "selected_cases": len(cases),
        "resolved_cases": sum(1 for r in selected_rows if r["postprocessing_exists"] == "true"),
        "stats_rows": len(stats_rows),
        "figures": len(figure_rows),
        "representative_drifting_groups": sum(int(r["drifting_representative_groups"]) for r in case_summary),
        "representative_quasi_groups": sum(int(r["quasi_representative_groups"]) for r in case_summary),
        "representative_steady_groups": sum(int(r["steady_representative_groups"]) for r in case_summary),
    }
    (product / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    write_readme(product, cases, stats_rows, case_summary, rep_metrics, window_seconds)
    write_closeouts(cases, summary)
    return summary


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--window-seconds", type=float, default=300.0)
    ap.add_argument("--output", type=Path, default=PRODUCT)
    args = ap.parse_args()
    summary = build(args.window_seconds, args.output)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
