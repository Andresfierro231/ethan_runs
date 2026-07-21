#!/usr/bin/env python3
"""Build Salt oscillation package with user-requested nominal train scope."""

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
TASK = "AGENT-416"
PRODUCT = REPO / "work_products/2026-07/2026-07-15/2026-07-15_salt_oscillation_user_train_scope"
FIGDIR = PRODUCT / "figures"
MATRIX = REPO / "work_products/2026-07/2026-07-14/2026-07-14_flow_rate_temperature_bc_response_study/case_bc_response_matrix.csv"

USER_SCOPE_CASES = [
    {
        "case_key": "salt1_jin_nominal",
        "matrix_key": "salt1_jin",
        "display_label": "viscosity_screening_salt_test_1_jin_coarse_mesh",
        "salt_family": "salt1",
        "variant": "nominal",
        "split_role": "canonical_forward_train",
        "admission_status": "user_requested_forward_train_reporting_row",
        "guardrail": "user-requested forward train label; does not mutate registry/admission state",
    },
    {
        "case_key": "salt2_jin_nominal",
        "matrix_key": "salt2_jin",
        "display_label": "viscosity_screening_salt_test_2_jin_coarse_mesh",
        "salt_family": "salt2",
        "variant": "nominal",
        "split_role": "canonical_forward_train",
        "admission_status": "canonical_forward_train_reporting_row",
        "guardrail": "canonical/user-requested forward train label; keep distinct from native val_salt2",
    },
    {
        "case_key": "salt3_jin_nominal",
        "matrix_key": "salt3_jin",
        "display_label": "viscosity_screening_salt_test_3_jin_coarse_mesh",
        "salt_family": "salt3",
        "variant": "nominal",
        "split_role": "canonical_forward_train",
        "admission_status": "user_requested_forward_train_reporting_row",
        "guardrail": "user-requested forward train label; older ledgers may still call Salt3 validation",
    },
    {
        "case_key": "salt2_native_val",
        "matrix_key": "salt_test_2",
        "display_label": "val_salt_test_2_coarse_mesh_laminar",
        "salt_family": "salt2",
        "variant": "native_validation_comparison",
        "split_role": "diagnostic_validation_comparison",
        "admission_status": "context_row_not_current_fit_row",
        "guardrail": "native val_salt2 comparison; do not mix with Salt2 Jin train row",
    },
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as fh:
        return list(csv.DictReader(fh))


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in fields})


def matrix_index() -> dict[str, dict[str, str]]:
    out: dict[str, dict[str, str]] = {}
    for row in read_csv(MATRIX):
        for key_name in ("case_key", "source_case_key", "canonical_case_key"):
            key = row.get(key_name, "")
            if key and key not in out:
                out[key] = row
    return out


def selected_cases() -> tuple[list[base.SelectedCase], list[dict[str, str]]]:
    cases = base.resolve_selected_cases()
    idx = matrix_index()
    resolution: list[dict[str, str]] = []

    # Promote the already-selected Salt1 continuation row into the requested train reporting scope.
    for case in cases:
        if case.case_key == "salt1_nominal":
            case.split_role = "canonical_forward_train"
            case.admission_status = "user_requested_forward_train_reporting_row"
            case.guardrail = "Salt1 nominal continuation retained and labeled as user-requested forward train reporting row."

    seen = {c.case_key for c in cases}
    for item in USER_SCOPE_CASES:
        match = idx.get(item["matrix_key"])
        if not match:
            resolution.append({
                "requested": item["case_key"],
                "status": "missing_in_case_matrix",
                "resolved_case_key": "",
                "postprocessing": "",
                "note": item["guardrail"],
            })
            continue
        pp = base.normalize_postprocessing(match["source_root"])
        resolution.append({
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
            use_for_thermal_fit="yes" if item["split_role"] == "canonical_forward_train" else "no",
            use_for_holdout_or_test="yes",
            admission_status=item["admission_status"],
            guardrail=item["guardrail"],
            primary_evidence=str(MATRIX.relative_to(REPO)),
            postprocessing=pp,
            matrix_case_key=match.get("case_key", ""),
        ))
        seen.add(item["case_key"])
    return cases, resolution


def build(window_seconds: float = 300.0) -> dict:
    PRODUCT.mkdir(parents=True, exist_ok=True)
    FIGDIR.mkdir(exist_ok=True)
    base.PRODUCT = PRODUCT

    cases, resolution = selected_cases()
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
    write_outputs(selected_rows, resolution, stats_rows, case_summary, rep_metrics, figure_rows)
    summary = {
        "task": TASK,
        "generated": datetime.now().isoformat(timespec="seconds"),
        "window_seconds": window_seconds,
        "selected_cases": len(cases),
        "resolved_cases": sum(1 for r in selected_rows if r["postprocessing_exists"] == "true"),
        "stats_rows": len(stats_rows),
        "figures": len(figure_rows),
        "train_rows": [r["case_key"] for r in selected_rows if r["split_role"] == "canonical_forward_train"],
        "validation_comparison_rows": [r["case_key"] for r in selected_rows if "validation" in r["split_role"]],
    }
    (PRODUCT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    write_readme(summary, resolution, case_summary)
    write_closeouts(summary)
    return summary


def write_outputs(selected_rows: list[dict], resolution: list[dict], stats_rows: list[dict],
                  case_summary: list[dict], rep_metrics: list[dict], figure_rows: list[dict]) -> None:
    write_csv(PRODUCT / "selected_cases.csv", selected_rows,
              ["case_key", "display_label", "salt_family", "variant", "split_role",
               "admission_status", "guardrail", "postprocessing", "postprocessing_exists"])
    write_csv(PRODUCT / "requested_case_resolution.csv", resolution,
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
        {"kind": "base_agent411_builder", "path": "tools/analyze/build_salt_training_testing_oscillation_steady_state.py"},
        {"kind": "case_matrix", "path": str(MATRIX.relative_to(REPO))},
    ], ["kind", "path"])


def write_readme(summary: dict, resolution: list[dict], case_summary: list[dict]) -> None:
    lines = [
        "# Salt Oscillation User Train Scope",
        "",
        f"Task: {TASK}",
        f"Generated: {DATE}",
        "",
        "## Scope",
        "",
        "This package applies the requested reporting split: Salt1 Jin nominal, Salt2 Jin",
        "nominal, and Salt3 Jin nominal are labeled `canonical_forward_train`. Native",
        "`val_salt_test_2_coarse_mesh_laminar` is included as `diagnostic_validation_comparison`.",
        "The original Salt1/Salt4/Salt2 perturbation rows from the July 15 thermal table remain",
        "in the package for continuity.",
        "",
        "This is a reporting/plotting scope update only. It does not mutate registry/admission",
        "state and does not consume validation temperatures as predictive runtime inputs.",
        "",
        "## Requested Case Resolution",
        "",
        "| requested | status | resolved case |",
        "| --- | --- | --- |",
    ]
    for row in resolution:
        lines.append(f"| {row['requested']} | {row['status']} | {row['resolved_case_key']} |")
    lines += [
        "",
        "## Results",
        "",
        f"- Selected cases: `{summary['selected_cases']}`.",
        f"- Resolved postProcessing directories: `{summary['resolved_cases']}`.",
        f"- Statistics rows: `{summary['stats_rows']}`.",
        f"- SVG figures: `{summary['figures']}`.",
        f"- Canonical/user-requested train rows: `{', '.join(summary['train_rows'])}`.",
        f"- Validation comparison rows: `{', '.join(summary['validation_comparison_rows'])}`.",
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
        "RMS, variance, naive CLT SEM, and autocorrelation-corrected SEM are in",
        "`representative_metrics.csv` and `oscillation_stats.csv`; plots are indexed by",
        "`figure_manifest.csv`.",
        "",
    ]
    (PRODUCT / "README.md").write_text("\n".join(lines))


def write_closeouts(summary: dict) -> None:
    status = REPO / f".agent/status/{DATE}_{TASK}.md"
    journal = REPO / ".agent/journal/2026-07-15/salt-oscillation-user-train-scope.md"
    imports = REPO / f"imports/{DATE}_salt_oscillation_user_train_scope.json"
    status.parent.mkdir(parents=True, exist_ok=True)
    journal.parent.mkdir(parents=True, exist_ok=True)
    imports.parent.mkdir(parents=True, exist_ok=True)
    status.write_text(
        f"# {TASK} Status\n\nStatus: COMPLETE\n\n"
        f"Output: `{PRODUCT.relative_to(REPO)}`\n\n"
        f"Selected cases: {summary['selected_cases']}\n"
        f"Stats rows: {summary['stats_rows']}\n"
        f"Figures: {summary['figures']}\n"
        f"Train rows: {', '.join(summary['train_rows'])}\n"
        f"Validation comparison rows: {', '.join(summary['validation_comparison_rows'])}\n\n"
        "No solver outputs, scheduler state, registry/admission state, generated indexes, or external tools were mutated.\n"
    )
    journal.write_text(
        "# Salt Oscillation User Train Scope Journal\n\n"
        "- Relabeled Salt1 Jin, Salt2 Jin, and Salt3 Jin nominal rows as canonical/user-requested forward train for reporting.\n"
        "- Kept native val_salt2 included as diagnostic validation comparison.\n"
        "- Regenerated TP/TW/mdot last-window oscillation statistics and figures without mutating native outputs.\n"
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
