#!/usr/bin/env python3
"""Build paper-facing uncertainty tables from AGENT-244 time-series statistics.

Reusable entry point:

    python3.11 tools/analyze/build_time_series_uncertainty_story.py

The default input is the AGENT-244 `steady_state_summary.csv`; override it with
`--input` for a refreshed time-series package and `--output-dir` for smoke tests
or dated follow-on packages. The script is intentionally read-only with respect
to solver outputs: it only reads CSV summaries and writes derived tables.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter
from datetime import datetime
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
DEFAULT_INPUT = REPO / "work_products/2026-07/2026-07-09/2026-07-09_timeseries_steadystate/steady_state_summary.csv"
DEFAULT_OUTPUT = REPO / "work_products/2026-07/2026-07-13/2026-07-13_time_series_uncertainty_story"
TASK_ID = "AGENT-272"
PRESENTATION_TASK_ID = "AGENT-273"
DOC_TASK_ID = "AGENT-275"
PRESENTATION_DRIFT_WINDOW_S = 300.0

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

COMPONENT_FIELDS = [
    "case_slug",
    "fluid",
    "group",
    "series",
    "unit",
    "n_window",
    "t_start",
    "t_end",
    "window_s",
    "verdict",
    "osc_mean",
    "osc_rmse_about_trend",
    "fit_slope",
    "fit_slope_se",
    "unc_sem_corrected",
    "unc_rel_sem_corrected",
    "drift_over_window",
    "half_drift_over_window",
    "two_sided_95_sem",
    "paper_envelope_abs",
    "paper_envelope_rel",
    "near_zero_mean",
    "trend_resolved",
    "drift_ratio",
    "rel_drift_over_window",
    "use_note",
]

PRESENTATION_FIELDS = [
    "case",
    "fluid",
    "quantity",
    "series",
    "unit",
    "mean",
    "corrected_sem",
    "oscillation_amplitude",
    "drift_over_300s",
    "verdict",
    "note",
]

CASE_LABELS = {
    "salt2": "Salt2",
    "salt3": "Salt3",
    "salt4": "Salt4",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = list(rows[0].keys()) if rows else []
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def as_float(value: str) -> float:
    if value == "" or value.lower() == "nan":
        return math.nan
    return float(value)


def fmt(value: float) -> str:
    if not math.isfinite(value):
        return ""
    return f"{value:.12g}"


def live_exclusion_reason(case_slug: str) -> str:
    for needle in LIVE_CASE_SUBSTRINGS:
        if needle in case_slug:
            return f"live_or_active_case:{needle}"
    return ""


def verdict_is_uncertainty_usable(verdict: str) -> bool:
    return verdict == "steady" or verdict.startswith("quasi-steady")


def is_mainline_salt234(case_slug: str) -> bool:
    return any(needle in case_slug for needle in MAINLINE_SLUG_SUBSTRINGS)


def case_label(fluid: str) -> str:
    return CASE_LABELS.get(fluid, fluid)


def uncertainty_use_note(row: dict[str, str]) -> str:
    group = row.get("group", "")
    verdict = row.get("verdict", "")
    if group == "heat":
        return "Use absolute W components; total_Q is a near-zero net residual, so relative percentages can be misleading."
    if verdict.startswith("quasi-steady"):
        return "Use with caveat: bounded oscillation/drift screen, not fully steady."
    return "Use as steady-window uncertainty component."


def component_row(row: dict[str, str]) -> dict[str, str]:
    t_start = as_float(row["t_start"])
    t_end = as_float(row["t_end"])
    slope = as_float(row["fit_slope"])
    sem = as_float(row["unc_sem_corrected"])
    rmse = as_float(row["osc_rmse_about_trend"])
    mean = as_float(row["osc_mean"])

    window_s = t_end - t_start
    drift = slope * window_s
    half_drift = 0.5 * abs(drift)
    sem_95 = 1.96 * sem
    envelope = sem_95 + rmse + half_drift
    envelope_rel = abs(envelope / mean) if mean and math.isfinite(mean) else math.nan

    return {
        "case_slug": row["case_slug"],
        "fluid": row["fluid"],
        "group": row["group"],
        "series": row["series"],
        "unit": row["unit"],
        "n_window": row["n_window"],
        "t_start": row["t_start"],
        "t_end": row["t_end"],
        "window_s": fmt(window_s),
        "verdict": row["verdict"],
        "osc_mean": row["osc_mean"],
        "osc_rmse_about_trend": row["osc_rmse_about_trend"],
        "fit_slope": row["fit_slope"],
        "fit_slope_se": row.get("fit_slope_se", ""),
        "unc_sem_corrected": row["unc_sem_corrected"],
        "unc_rel_sem_corrected": row["unc_rel_sem_corrected"],
        "drift_over_window": fmt(drift),
        "half_drift_over_window": fmt(half_drift),
        "two_sided_95_sem": fmt(sem_95),
        "paper_envelope_abs": fmt(envelope),
        "paper_envelope_rel": fmt(envelope_rel),
        "near_zero_mean": row.get("near_zero_mean", ""),
        "trend_resolved": row.get("trend_resolved", ""),
        "drift_ratio": row.get("drift_ratio", ""),
        "rel_drift_over_window": row.get("rel_drift_over_window", ""),
        "use_note": uncertainty_use_note(row),
    }


def screened_row(row: dict[str, str], reason: str) -> dict[str, str]:
    return {
        "case_slug": row["case_slug"],
        "fluid": row["fluid"],
        "group": row["group"],
        "series": row["series"],
        "unit": row["unit"],
        "verdict": row["verdict"],
        "screen_reason": reason,
        "osc_mean": row.get("osc_mean", ""),
        "osc_rmse_about_trend": row.get("osc_rmse_about_trend", ""),
        "fit_slope": row.get("fit_slope", ""),
        "unc_sem_corrected": row.get("unc_sem_corrected", ""),
        "unc_rel_sem_corrected": row.get("unc_rel_sem_corrected", ""),
    }


def split_components(rows: list[dict[str, str]]) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    components: list[dict[str, str]] = []
    screened: list[dict[str, str]] = []
    for row in rows:
        live_reason = live_exclusion_reason(row["case_slug"])
        if live_reason:
            screened.append(screened_row(row, live_reason))
            continue
        if not verdict_is_uncertainty_usable(row["verdict"]):
            screened.append(screened_row(row, f"not_uncertainty_usable_verdict:{row['verdict']}"))
            continue
        components.append(component_row(row))
    return components, screened


def blank_mainline_case(case_slug: str, fluid: str) -> dict[str, str]:
    return {
        "case_slug": case_slug,
        "fluid": fluid,
        "mdot_osc_mean_kg_s": "",
        "mdot_unc_sem_corrected_kg_s": "",
        "mdot_unc_rel_sem_corrected": "",
        "mdot_osc_rmse_about_trend_kg_s": "",
        "mdot_fit_slope_kg_s_per_s": "",
        "mdot_drift_over_window_kg_s": "",
        "mdot_paper_envelope_abs_kg_s": "",
        "mdot_verdict": "",
        "wall_temperature_osc_mean_K": "",
        "wall_temperature_unc_sem_corrected_K": "",
        "wall_temperature_osc_rmse_about_trend_K": "",
        "wall_temperature_fit_slope_K_per_s": "",
        "wall_temperature_drift_over_window_K": "",
        "wall_temperature_paper_envelope_abs_K": "",
        "wall_temperature_verdict": "",
        "temperature_probe_max_sem_series": "",
        "temperature_probe_max_unc_sem_corrected_K": "",
        "temperature_probe_max_rmse_series": "",
        "temperature_probe_max_osc_rmse_about_trend_K": "",
        "temperature_probe_max_envelope_series": "",
        "temperature_probe_max_paper_envelope_abs_K": "",
        "total_Q_osc_mean_W": "",
        "total_Q_unc_sem_corrected_W": "",
        "total_Q_osc_rmse_about_trend_W": "",
        "total_Q_fit_slope_W_per_s": "",
        "total_Q_drift_over_window_W": "",
        "total_Q_paper_envelope_abs_W": "",
        "total_Q_verdict": "",
        "total_Q_screen_note": "",
        "recommended_use": "Use component rows for paper uncertainty; envelope is SEM95 + detrended RMS + half-window drift, not a formal confidence interval.",
    }


def _set_if_abs_larger(row: dict[str, str], value_key: str, series_key: str, series: str, value: str) -> None:
    current = as_float(row[value_key]) if row[value_key] else -math.inf
    candidate = as_float(value) if value else -math.inf
    if candidate > current:
        row[value_key] = value
        row[series_key] = series


def compact_mainline_summary(
    components: list[dict[str, str]], screened: list[dict[str, str]]
) -> list[dict[str, str]]:
    by_case: dict[str, dict[str, str]] = {}
    for row in components:
        if not is_mainline_salt234(row["case_slug"]):
            continue
        case = by_case.setdefault(row["case_slug"], blank_mainline_case(row["case_slug"], row["fluid"]))
        group = row["group"]
        if group == "mdot" and "lower" in row["series"]:
            case["mdot_osc_mean_kg_s"] = row["osc_mean"]
            case["mdot_unc_sem_corrected_kg_s"] = row["unc_sem_corrected"]
            case["mdot_unc_rel_sem_corrected"] = row["unc_rel_sem_corrected"]
            case["mdot_osc_rmse_about_trend_kg_s"] = row["osc_rmse_about_trend"]
            case["mdot_fit_slope_kg_s_per_s"] = row["fit_slope"]
            case["mdot_drift_over_window_kg_s"] = row["drift_over_window"]
            case["mdot_paper_envelope_abs_kg_s"] = row["paper_envelope_abs"]
            case["mdot_verdict"] = row["verdict"]
        elif group == "wall_temperature":
            case["wall_temperature_osc_mean_K"] = row["osc_mean"]
            case["wall_temperature_unc_sem_corrected_K"] = row["unc_sem_corrected"]
            case["wall_temperature_osc_rmse_about_trend_K"] = row["osc_rmse_about_trend"]
            case["wall_temperature_fit_slope_K_per_s"] = row["fit_slope"]
            case["wall_temperature_drift_over_window_K"] = row["drift_over_window"]
            case["wall_temperature_paper_envelope_abs_K"] = row["paper_envelope_abs"]
            case["wall_temperature_verdict"] = row["verdict"]
        elif group == "temperature":
            _set_if_abs_larger(
                case,
                "temperature_probe_max_unc_sem_corrected_K",
                "temperature_probe_max_sem_series",
                row["series"],
                row["unc_sem_corrected"],
            )
            _set_if_abs_larger(
                case,
                "temperature_probe_max_osc_rmse_about_trend_K",
                "temperature_probe_max_rmse_series",
                row["series"],
                row["osc_rmse_about_trend"],
            )
            _set_if_abs_larger(
                case,
                "temperature_probe_max_paper_envelope_abs_K",
                "temperature_probe_max_envelope_series",
                row["series"],
                row["paper_envelope_abs"],
            )
        elif group == "heat":
            case["total_Q_osc_mean_W"] = row["osc_mean"]
            case["total_Q_unc_sem_corrected_W"] = row["unc_sem_corrected"]
            case["total_Q_osc_rmse_about_trend_W"] = row["osc_rmse_about_trend"]
            case["total_Q_fit_slope_W_per_s"] = row["fit_slope"]
            case["total_Q_drift_over_window_W"] = row["drift_over_window"]
            case["total_Q_paper_envelope_abs_W"] = row["paper_envelope_abs"]
            case["total_Q_verdict"] = row["verdict"]

    for row in screened:
        if not is_mainline_salt234(row["case_slug"]) or row["group"] != "heat":
            continue
        case = by_case.setdefault(row["case_slug"], blank_mainline_case(row["case_slug"], row["fluid"]))
        note = f"{row['verdict']} screened out ({row['screen_reason']}); do not use total_Q as steady-state uncertainty bound."
        case["total_Q_screen_note"] = note
    return [by_case[key] for key in sorted(by_case)]


def _temperature_probe_index(series: str) -> int:
    parts = series.split()
    if len(parts) >= 2 and parts[0] == "probe":
        try:
            return int(parts[1])
        except ValueError:
            return 999
    return 999


def _presentation_quantity(row: dict[str, str]) -> tuple[int, str] | None:
    group = row["group"]
    series = row["series"]
    if group == "mdot":
        if "lower" not in series:
            return None
        return 0, "mdot"
    if group == "temperature":
        idx = _temperature_probe_index(series)
        return 1 + idx, f"T probe {idx}" if idx != 999 else "T probe"
    if group == "wall_temperature":
        return 20, "wall T"
    if group == "heat":
        return 30, "total_Q residual"
    return None


def presentation_salt234_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    presentation: list[tuple[tuple[int, int, str], dict[str, str]]] = []
    case_order = {"salt2": 2, "salt3": 3, "salt4": 4}
    for row in rows:
        if not is_mainline_salt234(row["case_slug"]):
            continue
        quantity = _presentation_quantity(row)
        if quantity is None:
            continue
        order, label = quantity
        slope = as_float(row["fit_slope"])
        drift_300 = slope * PRESENTATION_DRIFT_WINDOW_S
        note = ""
        if row["group"] == "heat":
            note = "Absolute W residual; avoid relative error because mean is near zero."
        out = {
            "case": case_label(row["fluid"]),
            "fluid": row["fluid"],
            "quantity": label,
            "series": row["series"],
            "unit": row["unit"],
            "mean": row["osc_mean"],
            "corrected_sem": row["unc_sem_corrected"],
            "oscillation_amplitude": row["osc_rmse_about_trend"],
            "drift_over_300s": fmt(drift_300),
            "verdict": row["verdict"],
            "note": note,
        }
        presentation.append(((case_order.get(row["fluid"], 999), order, row["series"]), out))
    return [row for _, row in sorted(presentation, key=lambda item: item[0])]


def _md_cell(value: str) -> str:
    return value.replace("|", "\\|")


def write_presentation_markdown(path: Path, rows: list[dict[str, str]]) -> None:
    lines = [
        "# Salt2/3/4 Presentation Uncertainty Table",
        "",
        "Mean, corrected SEM, oscillation amplitude, and drift are taken from the last 300 s AGENT-244 time-series window.",
        "`total_Q residual` is shown in absolute W terms; do not emphasize relative error for that near-zero residual.",
        "",
        "| Case | Quantity | Mean | Corrected SEM | Osc. amp. | Drift / 300 s | Unit | Verdict | Note |",
        "| --- | --- | ---: | ---: | ---: | ---: | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| {case} | {quantity} | {mean} | {sem} | {osc} | {drift} | {unit} | {verdict} | {note} |".format(
                case=_md_cell(row["case"]),
                quantity=_md_cell(row["quantity"]),
                mean=_md_cell(row["mean"]),
                sem=_md_cell(row["corrected_sem"]),
                osc=_md_cell(row["oscillation_amplitude"]),
                drift=_md_cell(row["drift_over_300s"]),
                unit=_md_cell(row["unit"]),
                verdict=_md_cell(row["verdict"]),
                note=_md_cell(row["note"]),
            )
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_readme(output_dir: Path, summary: dict[str, object]) -> None:
    text = f"""# Time-Series Uncertainty Story

Task: `{TASK_ID}`  
Presentation table addendum: `{PRESENTATION_TASK_ID}`  
Documentation polish: `{DOC_TASK_ID}`  
Source: `work_products/2026-07/2026-07-09/2026-07-09_timeseries_steadystate/steady_state_summary.csv`

This package turns the AGENT-244 steady-state time-series metrics into
paper-facing uncertainty components for considered steady/quasi-steady CFD
solutions.

## Start Here

For the next presentation, start with:

- `presentation_salt234_timeseries_uncertainty.md` for a slide-readable table.
- `presentation_salt234_timeseries_uncertainty.csv` for spreadsheet cleanup or
  plotting.

For paper methods and uncertainty provenance, start with:

- `uncertainty_components_steady_or_quasi.csv` for the full steady/quasi
  component table.
- `screened_out_not_steady_or_live.csv` for rows intentionally excluded from
  uncertainty use.
- `summary.json` for counts, source path, and policy metadata.

## Recommended Use

- `osc_mean`: best estimate of the steady-window mean.
- `unc_sem_corrected`: autocorrelation-corrected standard error of that mean.
- `unc_rel_sem_corrected`: relative SEM from the source package.
- `osc_rmse_about_trend`: detrended oscillation amplitude; use as the
  persistent time-variation component after drift removal.
- `fit_slope`: residual drift rate. This package also reports
  `drift_over_window = fit_slope * (t_end - t_start)`.
- `verdict`: screen. Use `steady` directly and use `quasi-steady...` with a
  caveat. Rows with `not steady...` or live/active slugs are screened out.

The derived `paper_envelope_abs` is a conservative display bound:

```text
1.96 * unc_sem_corrected + osc_rmse_about_trend + 0.5 * abs(drift_over_window)
```

It is not a formal confidence interval; the paper methods should report the
components separately when precision matters.

## Reusable Script

Primary script:

```bash
python3.11 tools/analyze/build_time_series_uncertainty_story.py
```

Useful variants:

```bash
# Regenerate this package from the default AGENT-244 source.
python3.11 tools/analyze/build_time_series_uncertainty_story.py

# Smoke-test into /tmp without touching the dated package.
python3.11 tools/analyze/build_time_series_uncertainty_story.py \\
  --output-dir /tmp/time_series_uncertainty_story_smoke

# Reuse against a refreshed steady-state summary.
python3.11 tools/analyze/build_time_series_uncertainty_story.py \\
  --input path/to/steady_state_summary.csv \\
  --output-dir work_products/2026-07/2026-07-XX/your_package_name
```

Validation:

```bash
python3.11 -m py_compile \\
  tools/analyze/build_time_series_uncertainty_story.py \\
  tools/analyze/test_time_series_uncertainty_story.py
python3.11 tools/analyze/test_time_series_uncertainty_story.py
```

## Input Contract

The input CSV must contain AGENT-244-style columns including:

- identity: `case_slug`, `fluid`, `group`, `series`, `unit`
- window: `n_window`, `t_start`, `t_end`
- screen: `verdict`, `near_zero_mean`, `trend_resolved`
- values: `osc_mean`, `osc_rmse_about_trend`, `fit_slope`,
  `unc_sem_corrected`, `unc_rel_sem_corrected`

The script does not read native OpenFOAM fields or mutate solver outputs.

## Output Contract

The generated tables are:

- full component rows: `uncertainty_components_steady_or_quasi.csv`
- screened rows: `screened_out_not_steady_or_live.csv`
- mainline component rows: `mainline_salt234_uncertainty_components.csv`
- compact paper bounds: `paper_uncertainty_bounds_salt234.csv`
- presentation table: `presentation_salt234_timeseries_uncertainty.csv`
- presentation Markdown: `presentation_salt234_timeseries_uncertainty.md`

## Outputs

- `uncertainty_components_steady_or_quasi.csv`: all terminal/non-live rows whose
  verdict is steady or quasi-steady, preserving the requested AGENT-244 metric
  names plus derived bound columns.
- `mainline_salt234_uncertainty_components.csv`: steady/quasi component rows
  for the current mainline Salt2/3/4 Jin continuations.
- `paper_uncertainty_bounds_salt234.csv`: compact case-level table for Salt2/3/4.
- `presentation_salt234_timeseries_uncertainty.csv`: compact presentation rows
  for admitted Salt2/3/4 mdot, six temperature probes, wall temperature, and
  total_Q residual.
- `presentation_salt234_timeseries_uncertainty.md`: Markdown rendering of the
  same presentation table.
- `screened_out_not_steady_or_live.csv`: rows excluded from uncertainty use and
  the reason.
- `summary.json`: counts and provenance.

## Counts

- input rows: `{summary["input_rows"]}`
- uncertainty-usable rows: `{summary["usable_rows"]}`
- screened rows: `{summary["screened_rows"]}`
- mainline Salt2/3/4 component rows: `{summary["mainline_salt234_rows"]}`
- compact Salt2/3/4 case rows: `{summary["compact_salt234_rows"]}`
- Salt2/3/4 presentation rows: `{summary["presentation_salt234_rows"]}`

For `total_Q`, use absolute W components only when the row passes the verdict
screen; it is a near-zero net residual, so relative uncertainty can look large
even when the absolute residual is physically small.
"""
    (output_dir / "README.md").write_text(text, encoding="utf-8")


def build(input_csv: Path, output_dir: Path) -> dict[str, object]:
    rows = read_csv(input_csv)
    components, screened = split_components(rows)
    mainline = [row for row in components if is_mainline_salt234(row["case_slug"])]
    compact = compact_mainline_summary(components, screened)
    presentation = presentation_salt234_rows(rows)

    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(output_dir / "uncertainty_components_steady_or_quasi.csv", components, COMPONENT_FIELDS)
    write_csv(output_dir / "screened_out_not_steady_or_live.csv", screened)
    write_csv(output_dir / "mainline_salt234_uncertainty_components.csv", mainline, COMPONENT_FIELDS)
    write_csv(output_dir / "paper_uncertainty_bounds_salt234.csv", compact)
    write_csv(
        output_dir / "presentation_salt234_timeseries_uncertainty.csv",
        presentation,
        PRESENTATION_FIELDS,
    )
    write_presentation_markdown(
        output_dir / "presentation_salt234_timeseries_uncertainty.md",
        presentation,
    )

    summary: dict[str, object] = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "task_id": TASK_ID,
        "additive_task_ids": [PRESENTATION_TASK_ID, DOC_TASK_ID],
        "latest_additive_task_id": DOC_TASK_ID,
        "input": str(input_csv),
        "output_dir": str(output_dir),
        "input_rows": len(rows),
        "usable_rows": len(components),
        "screened_rows": len(screened),
        "mainline_salt234_rows": len(mainline),
        "compact_salt234_rows": len(compact),
        "presentation_salt234_rows": len(presentation),
        "usable_verdict_counts": dict(Counter(row["verdict"] for row in components)),
        "screen_reason_counts": dict(Counter(row["screen_reason"] for row in screened)),
        "usable_group_counts": dict(Counter(row["group"] for row in components)),
        "presentation_group_counts": dict(Counter(row["quantity"] for row in presentation)),
        "mainline_case_slugs": [row["case_slug"] for row in compact],
        "live_case_substrings": list(LIVE_CASE_SUBSTRINGS),
        "presentation_total_q_policy": "Report total_Q residual in absolute W terms; avoid relative error because it is near zero.",
        "paper_envelope_formula": "1.96*unc_sem_corrected + osc_rmse_about_trend + 0.5*abs(fit_slope*(t_end-t_start))",
    }
    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    write_readme(output_dir, summary)
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    build(args.input, args.output_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
