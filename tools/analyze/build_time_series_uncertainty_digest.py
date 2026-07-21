#!/usr/bin/env python3
"""Build a compact uncertainty digest from AGENT-244 time-series statistics."""

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
DEFAULT_INPUT = REPO / "work_products/2026-07/2026-07-09/2026-07-09_timeseries_steadystate/steady_state_summary.csv"
DEFAULT_OUTPUT = REPO / "work_products/2026-07/2026-07-10/2026-07-10_time_series_uncertainty_digest_sbatch"

LIVE_CASE_SUBSTRINGS = (
    "2026-07-08_salt1_nominal_continuation_candidate",
    "salt1_jin_nominal_continuation_corrected",
    "salt1_jin_lo10q_corrected",
    "salt1_jin_hi10q_corrected",
    "salt4_jin_hi10q_corrected",
)

MAINLINE_SLUG_SUBSTRINGS = (
    "modern_runs__2026-06-18_convergence_and_jin_envelope_wave__salt2_jin__",
    "modern_runs__2026-06-18_convergence_and_jin_envelope_wave__salt3_jin__",
    "modern_runs__2026-06-18_convergence_and_jin_envelope_wave__salt4_jin__",
)

PRESENTATION_GROUPS = {"mdot", "temperature", "wall_temperature", "heat"}


def _float(row: dict[str, str], key: str) -> float:
    value = row.get(key, "")
    if value == "" or value.lower() == "nan":
        return float("nan")
    return float(value)


def _excluded_reason(case_slug: str) -> str:
    for needle in LIVE_CASE_SUBSTRINGS:
        if needle in case_slug:
            return f"live_or_active_case:{needle}"
    return ""


def _digest_row(row: dict[str, str]) -> dict[str, str]:
    t_start = _float(row, "t_start")
    t_end = _float(row, "t_end")
    slope = _float(row, "fit_slope")
    window_s = t_end - t_start
    signed_drift = slope * window_s
    absolute_drift = abs(signed_drift)
    mean = _float(row, "osc_mean")
    sem = _float(row, "unc_sem_corrected")
    rmse_trend = _float(row, "osc_rmse_about_trend")
    rel_sem_pct = abs(sem / mean) * 100.0 if mean and mean == mean else float("nan")
    drift_pct = abs(signed_drift / mean) * 100.0 if mean and mean == mean else float("nan")
    near_zero = row.get("near_zero_mean", "")
    heat_note = ""
    if row.get("group") == "heat":
        heat_note = "total_Q is a near-zero net residual; emphasize absolute W and drift, not only relative percent."
    return {
        "case_slug": row["case_slug"],
        "fluid": row["fluid"],
        "group": row["group"],
        "series": row["series"],
        "unit": row["unit"],
        "n_window": row["n_window"],
        "t_start_s": row["t_start"],
        "t_end_s": row["t_end"],
        "window_s": f"{window_s:.9g}",
        "verdict": row["verdict"],
        "mean": row["osc_mean"],
        "autocorr_corrected_sem": row["unc_sem_corrected"],
        "relative_sem_percent": f"{rel_sem_pct:.9g}",
        "rmse_about_trend": row["osc_rmse_about_trend"],
        "rmse_about_mean": row["osc_rmse_about_mean"],
        "signed_drift_over_window": f"{signed_drift:.9g}",
        "absolute_drift_over_window": f"{absolute_drift:.9g}",
        "drift_percent_of_mean": f"{drift_pct:.9g}",
        "drift_ratio": row["drift_ratio"],
        "autocorrelation_time": row["unc_tau_int"],
        "effective_n": row["unc_n_eff"],
        "near_zero_mean": near_zero,
        "trend_resolved": row["trend_resolved"],
        "presentation_note": heat_note,
    }


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    rows = list(csv.DictReader(args.input.open(newline="", encoding="utf-8")))
    terminal: list[dict[str, str]] = []
    excluded: list[dict[str, str]] = []
    for row in rows:
        reason = _excluded_reason(row["case_slug"])
        if reason:
            excluded.append(
                {
                    "case_slug": row["case_slug"],
                    "fluid": row["fluid"],
                    "group": row["group"],
                    "series": row["series"],
                    "reason": reason,
                }
            )
            continue
        terminal.append(row)

    digest = [_digest_row(row) for row in terminal if row.get("group") in PRESENTATION_GROUPS]
    mainline = [
        row
        for row in digest
        if any(needle in row["case_slug"] for needle in MAINLINE_SLUG_SUBSTRINGS)
    ]

    by_case: dict[str, dict[str, str]] = {}
    for row in mainline:
        key = row["case_slug"]
        bucket = by_case.setdefault(
            key,
            {
                "case_slug": key,
                "fluid": row["fluid"],
                "mdot_mean_kg_s": "",
                "mdot_sem_kg_s": "",
                "mdot_rmse_kg_s": "",
                "mdot_drift_kg_s": "",
                "mdot_verdict": "",
                "wall_temperature_mean_K": "",
                "wall_temperature_sem_K": "",
                "temperature_probe_max_sem_K": "",
                "temperature_probe_max_rmse_K": "",
                "total_Q_mean_W": "",
                "total_Q_sem_W": "",
                "total_Q_abs_drift_W": "",
                "total_Q_verdict": "",
                "note": "All rows come from terminal/non-live AGENT-244 time-series products; total_Q is a near-zero residual.",
            },
        )
        group = row["group"]
        if group == "mdot" and "lower" in row["series"]:
            bucket["mdot_mean_kg_s"] = row["mean"]
            bucket["mdot_sem_kg_s"] = row["autocorr_corrected_sem"]
            bucket["mdot_rmse_kg_s"] = row["rmse_about_trend"]
            bucket["mdot_drift_kg_s"] = row["signed_drift_over_window"]
            bucket["mdot_verdict"] = row["verdict"]
        elif group == "wall_temperature":
            bucket["wall_temperature_mean_K"] = row["mean"]
            bucket["wall_temperature_sem_K"] = row["autocorr_corrected_sem"]
        elif group == "temperature":
            current_sem = float(bucket["temperature_probe_max_sem_K"] or "0")
            current_rmse = float(bucket["temperature_probe_max_rmse_K"] or "0")
            bucket["temperature_probe_max_sem_K"] = f"{max(current_sem, _float(row, 'autocorr_corrected_sem')):.9g}"
            bucket["temperature_probe_max_rmse_K"] = f"{max(current_rmse, _float(row, 'rmse_about_trend')):.9g}"
        elif group == "heat":
            bucket["total_Q_mean_W"] = row["mean"]
            bucket["total_Q_sem_W"] = row["autocorr_corrected_sem"]
            bucket["total_Q_abs_drift_W"] = row["absolute_drift_over_window"]
            bucket["total_Q_verdict"] = row["verdict"]

    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(output_dir / "uncertainty_digest_all_terminal_cases.csv", digest)
    _write_csv(output_dir / "uncertainty_digest_admitted_mainline_salt234.csv", mainline)
    _write_csv(output_dir / "presentation_uncertainty_summary_salt234.csv", list(by_case.values()))
    _write_csv(output_dir / "excluded_live_or_active_cases.csv", excluded)

    summary = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "input": str(args.input),
        "output_dir": str(output_dir),
        "input_rows": len(rows),
        "terminal_digest_rows": len(digest),
        "mainline_salt234_rows": len(mainline),
        "presentation_case_rows": len(by_case),
        "excluded_live_or_active_rows": len(excluded),
        "excluded_live_case_substrings": list(LIVE_CASE_SUBSTRINGS),
        "terminal_verdict_counts": dict(Counter(row["verdict"] for row in digest)),
        "terminal_group_counts": dict(Counter(row["group"] for row in digest)),
        "mainline_case_slugs": sorted(by_case),
    }
    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    (output_dir / "README.md").write_text(
        "# Time-Series Uncertainty Digest\n\n"
        "This package condenses the AGENT-244 time-series steady-state statistics into\n"
        "presentation-usable uncertainty tables. It excludes currently live or active\n"
        "case keys: Salt1 nominal continuation and selected corrected-Q continuation\n"
        "rows under jobs `3282992` and `3288671`.\n\n"
        "## Outputs\n\n"
        "- `uncertainty_digest_all_terminal_cases.csv`: all non-live series rows.\n"
        "- `uncertainty_digest_admitted_mainline_salt234.csv`: Salt2/3/4 mainline rows.\n"
        "- `presentation_uncertainty_summary_salt234.csv`: one compact row per admitted mainline Salt case.\n"
        "- `excluded_live_or_active_cases.csv`: rows intentionally excluded because they are live/active.\n"
        "- `summary.json`: row counts and verdict summaries.\n\n"
        "Use autocorrelation-corrected SEM for uncertainty bounds. For `total_Q`, use\n"
        "absolute W values because it is a near-zero net heat residual.\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
