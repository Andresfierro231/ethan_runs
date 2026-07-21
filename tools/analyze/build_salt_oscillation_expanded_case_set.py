#!/usr/bin/env python3
"""Build expanded Salt oscillation package after user-requested scope correction."""

from __future__ import annotations

import csv
import json
import sys
from datetime import datetime
from pathlib import Path

THIS = Path(__file__).resolve()
REPO = THIS.parents[2]
TOOLS = REPO / "tools" / "analyze"
sys.path.insert(0, str(TOOLS))

import build_salt_training_testing_oscillation_steady_state as base  # noqa: E402
from openfoam_timeseries import load_case_series  # noqa: E402


DATE = "2026-07-15"
TASK = "AGENT-415"
PRODUCT = REPO / "work_products/2026-07/2026-07-15/2026-07-15_salt_oscillation_expanded_case_set"
FIGDIR = PRODUCT / "figures"
MATRIX = REPO / "work_products/2026-07/2026-07-14/2026-07-14_flow_rate_temperature_bc_response_study/case_bc_response_matrix.csv"


EXTRA_CASES = [
    {
        "case_key": "salt2_jin_nominal",
        "matrix_key": "salt2_jin",
        "display_label": "viscosity_screening_salt_test_2_jin_coarse_mesh",
        "salt_family": "salt2",
        "variant": "nominal",
        "split_role": "canonical_forward_train",
        "admission_status": "admitted_or_usable_for_current_forward_split",
        "guardrail": "canonical forward-v1 train row; keep separate from broader July 15 thermal-training table",
    },
    {
        "case_key": "salt3_jin_nominal",
        "matrix_key": "salt3_jin",
        "display_label": "viscosity_screening_salt_test_3_jin_coarse_mesh",
        "salt_family": "salt3",
        "variant": "nominal",
        "split_role": "canonical_forward_validation",
        "admission_status": "admitted_or_usable_for_current_forward_split",
        "guardrail": "canonical forward-v1 validation row; not a fit row after model choice",
    },
    {
        "case_key": "salt2_native_val",
        "matrix_key": "salt_test_2",
        "display_label": "val_salt_test_2_coarse_mesh_laminar",
        "salt_family": "salt2",
        "variant": "native_validation_comparison",
        "split_role": "diagnostic_validation_comparison",
        "admission_status": "context_row_not_current_forward_split",
        "guardrail": "historical/native val_salt2 comparison; do not mix with Salt2 Jin train row",
    },
    {
        "case_key": "salt1_jin_reference_not_val",
        "matrix_key": "salt1_jin",
        "display_label": "viscosity_screening_salt_test_1_jin_coarse_mesh",
        "salt_family": "salt1",
        "variant": "nominal_reference",
        "split_role": "diagnostic_reference_not_val",
        "admission_status": "diagnostic_context_only",
        "guardrail": "included because user asked for Salt1 val; no val_salt_test_1 case was found",
    },
]


def matrix_index() -> dict[str, dict[str, str]]:
    rows = base.read_csv(MATRIX)
    out: dict[str, dict[str, str]] = {}
    for row in rows:
        for key in ("case_key", "source_case_key", "canonical_case_key"):
            if row.get(key) and row[key] not in out:
                out[row[key]] = row
    return out


def expanded_cases() -> tuple[list[base.SelectedCase], list[dict[str, str]]]:
    cases = base.resolve_selected_cases()
    seen = {c.case_key for c in cases}
    idx = matrix_index()
    resolution_rows: list[dict[str, str]] = []
    for item in EXTRA_CASES:
        match = idx.get(item["matrix_key"])
        if not match:
            resolution_rows.append({
                "requested": item["case_key"],
                "status": "missing_in_case_matrix",
                "resolved_case_key": "",
                "postprocessing": "",
                "note": item["guardrail"],
            })
            continue
        pp = base.normalize_postprocessing(match["source_root"])
        resolution_rows.append({
            "requested": item["case_key"],
            "status": "resolved" if pp.is_dir() else "postprocessing_missing",
            "resolved_case_key": match.get("case_key", ""),
            "postprocessing": str(pp),
            "note": item["guardrail"],
        })
        if item["case_key"] in seen:
            continue
        cases.append(base.SelectedCase(
            case_key=item["case_key"],
            display_label=item["display_label"],
            salt_family=item["salt_family"],
            variant=item["variant"],
            split_role=item["split_role"],
            use_for_thermal_fit="no",
            use_for_holdout_or_test="yes",
            admission_status=item["admission_status"],
            guardrail=item["guardrail"],
            primary_evidence=str(MATRIX.relative_to(REPO)),
            postprocessing=pp,
            matrix_case_key=match.get("case_key", ""),
        ))
        seen.add(item["case_key"])
    resolution_rows.append({
        "requested": "val_salt_test_1 / salt1_val",
        "status": "not_found",
        "resolved_case_key": "",
        "postprocessing": "",
        "note": "No val_salt_test_1* directory or case-matrix row was found; Salt1 Jin reference is included as diagnostic context only.",
    })
    return cases, resolution_rows


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in fields})


def build(window_seconds: float = 300.0) -> dict:
    PRODUCT.mkdir(parents=True, exist_ok=True)
    FIGDIR.mkdir(exist_ok=True)
    base.PRODUCT = PRODUCT
    cases, resolution_rows = expanded_cases()
    selected_rows: list[dict] = []
    stats_rows: list[dict] = []
    figure_rows: list[dict] = []

    for case in cases:
        selected_rows.append({
            "case_key": case.case_key,
            "display_label": case.display_label,
            "salt_family": case.salt_family,
            "variant": case.variant,
            "split_role": case.split_role,
            "admission_status": case.admission_status,
            "guardrail": case.guardrail,
            "postprocessing": str(case.postprocessing),
            "postprocessing_exists": str(case.postprocessing.is_dir()).lower(),
        })
        if not case.postprocessing.is_dir():
            continue
        series = load_case_series(case.postprocessing)
        for group in ("temperature", "wall_temperature", "mdot"):
            group_series = [s for s in series if s.group == group]
            if not group_series:
                continue
            for s in group_series:
                row = base.stats_row(case, group, s, "individual", window_seconds)
                if row:
                    stats_rows.append(row)
            rep = base.representative_series(group, group_series)
            if rep:
                row = base.stats_row(case, group, rep, "representative", window_seconds)
                if row:
                    stats_rows.append(row)
            base.chart_group(case, group, group_series, FIGDIR, window_seconds, figure_rows)

    case_summary = base.summarize_cases(stats_rows)
    rep_metrics = base.representative_metrics(stats_rows)
    write_csv(PRODUCT / "selected_cases.csv", selected_rows,
              ["case_key", "display_label", "salt_family", "variant", "split_role",
               "admission_status", "guardrail", "postprocessing", "postprocessing_exists"])
    write_csv(PRODUCT / "requested_case_resolution.csv", resolution_rows,
              ["requested", "status", "resolved_case_key", "postprocessing", "note"])
    write_csv(PRODUCT / "oscillation_stats.csv", stats_rows,
              ["case_key", "display_label", "salt_family", "variant", "split_role",
               "admission_status", "group", "quantity_label", "series_role", "series_name",
               "unit", "n_window", "t_start", "t_end", "dt_median", "window_seconds",
               "osc_mean", "osc_minimum", "osc_maximum", "osc_peak_to_peak",
               "osc_rmse_about_mean", "osc_var_about_mean", "osc_rmse_about_trend",
               "osc_var_about_trend", "osc_cov", "fit_slope", "fit_intercept", "fit_r2",
               "fit_slope_se", "fit_t_stat", "rel_drift_over_window", "drift_ratio",
               "near_zero_mean", "trend_resolved", "unc_tau_int", "unc_n_eff",
               "unc_sem_naive", "unc_sem_corrected", "unc_rel_sem_naive",
               "unc_rel_sem_corrected", "verdict", "postprocessing"])
    write_csv(PRODUCT / "case_summary.csv", case_summary,
              ["case_key", "split_role", "representative_groups", "steady_representative_groups",
               "quasi_representative_groups", "drifting_representative_groups", "verdicts",
               "max_rel_sem_corrected", "max_drift_ratio"])
    write_csv(PRODUCT / "representative_metrics.csv", rep_metrics,
              ["case_key", "split_role",
               "TP_mean", "TP_rms", "TP_variance", "TP_sem_corrected", "TP_verdict",
               "TW_mean", "TW_rms", "TW_variance", "TW_sem_corrected", "TW_verdict",
               "mdot_mean", "mdot_rms", "mdot_variance", "mdot_sem_corrected", "mdot_verdict",
               "max_rel_sem_corrected", "max_rel_drift_over_window"])
    write_csv(PRODUCT / "figure_manifest.csv", figure_rows, ["case_key", "group", "figure_type", "path"])
    write_csv(PRODUCT / "source_manifest.csv", [
        {"kind": "base_agent411_package", "path": "work_products/2026-07/2026-07-15/2026-07-15_salt_training_testing_oscillation_steady_state"},
        {"kind": "case_matrix", "path": str(MATRIX.relative_to(REPO))},
    ], ["kind", "path"])

    summary = {
        "task": TASK,
        "generated": datetime.now().isoformat(timespec="seconds"),
        "window_seconds": window_seconds,
        "selected_cases": len(cases),
        "resolved_cases": sum(1 for r in selected_rows if r["postprocessing_exists"] == "true"),
        "stats_rows": len(stats_rows),
        "figures": len(figure_rows),
        "not_found_requested_cases": [r["requested"] for r in resolution_rows if r["status"] == "not_found"],
    }
    (PRODUCT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    write_readme(cases, resolution_rows, case_summary, rep_metrics, summary)
    write_closeouts(summary)
    return summary


def write_readme(cases: list[base.SelectedCase], resolution_rows: list[dict[str, str]],
                 case_summary: list[dict], rep_metrics: list[dict], summary: dict) -> None:
    lines = [
        "# Expanded Salt Oscillation Case Set",
        "",
        f"Task: {TASK}",
        f"Generated: {DATE}",
        "",
        "## Why This Exists",
        "",
        "The first AGENT-411 package followed the July 15 thermal-fit table and therefore omitted",
        "nominal Salt2 and Salt3 from the plotted case set. This package corrects that scope:",
        "it keeps the original eight Salt rows and adds canonical Salt2 nominal, canonical",
        "Salt3 nominal, native `val_salt_test_2_coarse_mesh_laminar`, and a Salt1 Jin",
        "diagnostic reference row.",
        "",
        "No `val_salt_test_1*`/`salt1_val` case was found in the case matrix or bounded",
        "directory search. The Salt1 Jin reference is included only as diagnostic context;",
        "it is not relabeled as a validation case.",
        "",
        "## Requested Case Resolution",
        "",
        "| requested | status | resolved case |",
        "| --- | --- | --- |",
    ]
    for row in resolution_rows:
        lines.append(f"| {row['requested']} | {row['status']} | {row['resolved_case_key']} |")
    lines += [
        "",
        "## Results",
        "",
        f"- Selected cases: `{summary['selected_cases']}`.",
        f"- Resolved postProcessing directories: `{summary['resolved_cases']}`.",
        f"- Statistics rows: `{summary['stats_rows']}`.",
        f"- SVG figures: `{summary['figures']}`.",
        "",
        "Representative verdicts:",
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
        "Representative RMS/variance/SEM metrics are in `representative_metrics.csv`; all",
        "per-series values are in `oscillation_stats.csv`. Figures are under `figures/` and",
        "are indexed by `figure_manifest.csv`.",
        "",
        "The math is unchanged from AGENT-411: last-window RMS and variance are computed",
        "about the last-window mean; SEM follows the independent-sample CLT `sigma/sqrt(N)`",
        "and the tables also include autocorrelation-corrected SEM using `N_eff=N/tau_int`.",
        "",
    ]
    (PRODUCT / "README.md").write_text("\n".join(lines))


def write_closeouts(summary: dict) -> None:
    status = REPO / f".agent/status/{DATE}_{TASK}.md"
    journal = REPO / ".agent/journal/2026-07-15/salt-oscillation-expanded-case-set.md"
    imports = REPO / f"imports/{DATE}_salt_oscillation_expanded_case_set.json"
    status.parent.mkdir(parents=True, exist_ok=True)
    journal.parent.mkdir(parents=True, exist_ok=True)
    imports.parent.mkdir(parents=True, exist_ok=True)
    status.write_text(
        f"# {TASK} Status\n\nStatus: COMPLETE\n\n"
        f"Output: `{PRODUCT.relative_to(REPO)}`\n\n"
        f"Selected cases: {summary['selected_cases']}\n"
        f"Stats rows: {summary['stats_rows']}\n"
        f"Figures: {summary['figures']}\n"
        f"Not found: {', '.join(summary['not_found_requested_cases']) or 'none'}\n\n"
        "No solver outputs, scheduler state, registry/admission state, generated indexes, or external tools were mutated.\n"
    )
    journal.write_text(
        "# Expanded Salt Oscillation Case Set Journal\n\n"
        "- Corrected the AGENT-411 scope after user noted missing Salt2/Salt3 and Salt1-val ambiguity.\n"
        "- Added canonical Salt2 nominal, canonical Salt3 nominal, native val_salt2 comparison, and Salt1 Jin reference-not-val.\n"
        "- Documented that no val_salt_test_1/salt1_val case was found.\n"
    )
    imports.write_text(json.dumps({
        "task": TASK,
        "output": str(PRODUCT.relative_to(REPO)),
        "summary": summary,
    }, indent=2) + "\n")


def main() -> None:
    print(json.dumps(build(), indent=2))


if __name__ == "__main__":
    main()
