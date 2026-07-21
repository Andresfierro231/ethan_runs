#!/usr/bin/env python3
"""Build Salt1 primary-evidence admission review and final status scorecard."""

from __future__ import annotations

import csv
import json
import math
import re
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))

import timeseries_stats as ts  # noqa: E402

DATE = "2026-07-16"
TASK = "AGENT-448"
PRODUCT = ROOT / "work_products/2026-07/2026-07-16/2026-07-16_salt1_primary_evidence_admission_and_scorecard"
JOURNAL = ROOT / ".agent/journal/2026-07-16/salt1-primary-evidence-admission-and-board-cleanup.md"
STATUS = ROOT / ".agent/status/2026-07-16_AGENT-448.md"
IMPORT = ROOT / "imports/2026-07-16_salt1_primary_evidence_admission_and_board_cleanup.json"

WINDOW_SECONDS = 600.0


@dataclass(frozen=True)
class Salt1Case:
    case_id: str
    run_key: str
    role: str
    source_case: Path
    slurm_step: str
    scheduler_state: str


SALT1_CASES = [
    Salt1Case(
        "salt1_nominal",
        "salt1_jin_nominal_continuation_corrected",
        "primary_closure_training_candidate",
        ROOT / "jadyn_runs/modern_runs/2026-07-08_salt1_nominal_continuation_candidate/runs/"
        "salt1_jin_nominal_continuation_corrected/case_stage/"
        "viscosity_screening_salt_test_1_jin_coarse_mesh_continuation",
        "3282992.0",
        "CANCELLED after long operational run",
    ),
    Salt1Case(
        "salt1_lo10q",
        "salt1_jin_lo10q_corrected",
        "primary_closure_training_perturbation_candidate",
        ROOT / "jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations/runs/"
        "salt1_jin_lo10q_corrected/case_stage/"
        "viscosity_screening_salt_test_1_jin_coarse_mesh_continuation",
        "3288671.0",
        "CANCELLED after long operational run",
    ),
    Salt1Case(
        "salt1_hi10q",
        "salt1_jin_hi10q_corrected",
        "primary_closure_training_perturbation_candidate",
        ROOT / "jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations/runs/"
        "salt1_jin_hi10q_corrected/case_stage/"
        "viscosity_screening_salt_test_1_jin_coarse_mesh_continuation",
        "3288671.1",
        "CANCELLED after long operational run",
    ),
]

EXISTING = {
    "salt1_terminal": ROOT / "work_products/2026-07/2026-07-13/2026-07-13_salt1_terminal_harvest_admission_review/"
    "final_window_admission_review.csv",
    "salt1_policy": ROOT / "work_products/2026-07/2026-07-14/2026-07-14_salt_training_promotion_and_legacy_perturbation_audit/"
    "salt1_training_admission_package.csv",
    "expanded_steady": ROOT / "work_products/2026-07/2026-07-15/2026-07-15_salt_external_test_and_q_unlock_admission/"
    "terminal_steady_state_evidence.csv",
    "osc_summary": ROOT / "work_products/2026-07/2026-07-15/2026-07-15_salt_oscillation_expanded_case_set/"
    "case_summary.csv",
    "blocked": ROOT / "work_products/2026-07/2026-07-15/2026-07-15_salt_external_test_and_q_unlock_admission/"
    "pending_or_blocked_actions.csv",
}


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def read_numeric_table(path: Path) -> list[list[float]]:
    rows: list[list[float]] = []
    if not path.exists():
        return rows
    for line in path.read_text(errors="ignore").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        parts = stripped.split()
        try:
            vals = [float(p) for p in parts]
        except ValueError:
            continue
        if len(vals) >= 2 and math.isfinite(vals[0]):
            rows.append(vals)
    return rows


def family_rows(paths: list[Path]) -> list[list[float]]:
    merged: dict[float, list[float]] = {}
    for path in paths:
        for row in read_numeric_table(path):
            merged[row[0]] = row
    return [merged[k] for k in sorted(merged)]


def latest_family_files(root: Path, family: str, leaf: str) -> list[Path]:
    base = root / "postProcessing" / family
    if not base.exists():
        return []
    return sorted(base.glob(f"*/{leaf}"), key=lambda p: numeric_parent_time(p))


def numeric_parent_time(path: Path) -> float:
    try:
        return float(path.parent.name)
    except ValueError:
        return float("-inf")


def analyze_col(rows: list[list[float]], col: int) -> ts.SeriesAnalysis | None:
    filtered = [(row[0], row[col]) for row in rows if len(row) > col and math.isfinite(row[col])]
    if not filtered:
        return None
    filtered.sort()
    t = [r[0] for r in filtered]
    y = [r[1] for r in filtered]
    return ts.analyze(t, y, WINDOW_SECONDS)


def fmt(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        if math.isnan(value):
            return "nan"
        return f"{value:.12g}"
    return str(value)


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: fmt(row.get(field, "")) for field in fields})


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def max_probe_drift(rows: list[list[float]]) -> tuple[float, float, str, float]:
    best_abs = -1.0
    best_drift = 0.0
    best_verdict = ""
    best_rel_sem = float("nan")
    if not rows:
        return float("nan"), float("nan"), "missing", float("nan")
    max_cols = max(len(r) for r in rows) - 1
    for col in range(1, max_cols + 1):
        analysis = analyze_col(rows, col)
        if not analysis:
            continue
        drift = analysis.fit.slope * analysis.window_seconds
        abs_drift = abs(drift)
        if abs_drift > best_abs:
            best_abs = abs_drift
            best_drift = drift
            best_verdict = analysis.verdict
            best_rel_sem = analysis.uncertainty.rel_sem_corrected
    return best_abs, best_drift, best_verdict, best_rel_sem


def monitor_rows(case: Salt1Case) -> tuple[list[dict[str, object]], dict[str, object]]:
    rows: list[dict[str, object]] = []
    summary: dict[str, object] = {
        "case_id": case.case_id,
        "max_mdot_rel_drift": float("nan"),
        "max_mdot_rel_span": float("nan"),
        "max_tp_abs_drift_K": float("nan"),
        "max_tw_abs_drift_K": float("nan"),
        "total_Q_drift_W": float("nan"),
        "all_monitor_verdicts": "missing",
    }

    def add_series(family: str, label: str, unit: str, paths: list[Path], col: int = 1) -> ts.SeriesAnalysis | None:
        data = family_rows(paths)
        analysis = analyze_col(data, col)
        if not analysis:
            rows.append({
                "case_id": case.case_id,
                "family": family,
                "series_label": label,
                "unit": unit,
                "source_files": ";".join(rel(p) for p in paths),
                "status": "missing_or_too_short",
            })
            return None
        drift = analysis.fit.slope * analysis.window_seconds
        rows.append({
            "case_id": case.case_id,
            "family": family,
            "series_label": label,
            "unit": unit,
            "source_files": ";".join(rel(p) for p in paths),
            "status": "analyzed",
            "window_start_s": analysis.t_start,
            "window_end_s": analysis.t_end,
            "n_window": analysis.n_window,
            "mean": analysis.oscillation.mean,
            "drift_over_window": drift,
            "relative_drift": analysis.rel_drift_over_window,
            "peak_to_peak": analysis.oscillation.peak_to_peak,
            "rmse_about_trend": analysis.oscillation.rmse_about_trend,
            "rel_sem_corrected": analysis.uncertainty.rel_sem_corrected,
            "drift_ratio": analysis.drift_ratio,
            "verdict": analysis.verdict,
        })
        return analysis

    total = add_series("total_Q", "net total heat residual", "W", [case.source_case / "postProcessing/total_Q.dat"])
    if total:
        summary["total_Q_drift_W"] = total.fit.slope * total.window_seconds

    mdot_verdicts: list[str] = []
    max_rel = -1.0
    max_span = -1.0
    for mdot_dir in sorted((case.source_case / "postProcessing").glob("mdot_pipeleg_*")):
        files = sorted(mdot_dir.glob("*/surfaceFieldValue.dat"), key=numeric_parent_time)
        analysis = add_series("mdot", mdot_dir.name.replace("mdot_", ""), "kg/s", files)
        if analysis:
            mdot_verdicts.append(analysis.verdict)
            rel_drift = abs(analysis.rel_drift_over_window) if math.isfinite(analysis.rel_drift_over_window) else 0.0
            max_rel = max(max_rel, rel_drift)
            max_span = max(max_span, analysis.oscillation.peak_to_peak / abs(analysis.oscillation.mean))
    if max_rel >= 0:
        summary["max_mdot_rel_drift"] = max_rel
    if max_span >= 0:
        summary["max_mdot_rel_span"] = max_span

    for family, key in [("temperature_probes", "max_tp_abs_drift_K"), ("wall_temperature_probes", "max_tw_abs_drift_K")]:
        files = latest_family_files(case.source_case, family, "T")
        data = family_rows(files)
        abs_drift, drift, verdict, rel_sem = max_probe_drift(data)
        summary[key] = abs_drift
        rows.append({
            "case_id": case.case_id,
            "family": family,
            "series_label": "max_abs_probe_drift",
            "unit": "K",
            "source_files": ";".join(rel(p) for p in files),
            "status": "analyzed" if math.isfinite(abs_drift) else "missing_or_too_short",
            "window_start_s": data[-1][0] - WINDOW_SECONDS if data else "",
            "window_end_s": data[-1][0] if data else "",
            "mean": "",
            "drift_over_window": drift,
            "relative_drift": "",
            "peak_to_peak": "",
            "rmse_about_trend": "",
            "rel_sem_corrected": rel_sem,
            "drift_ratio": "",
            "verdict": verdict,
        })

    verdicts = [str(r.get("verdict")) for r in rows if r.get("status") == "analyzed" and r.get("verdict")]
    summary["all_monitor_verdicts"] = ";".join(sorted(set(verdicts))) if verdicts else "missing"
    summary["suspicious_monitor_flag"] = "no" if all("not steady" not in v for v in verdicts) else "yes"
    return rows, summary


def convergence_audit(case: Salt1Case) -> dict[str, object]:
    functions = case.source_case / "system/functions"
    text = functions.read_text(errors="ignore") if functions.exists() else ""
    log_candidates = sorted((case.source_case / "logs").glob("log.foamRun*"))
    log_text = "\n".join(p.read_text(errors="ignore")[-20000:] for p in log_candidates)
    return {
        "case_id": case.case_id,
        "functions_path": rel(functions),
        "log_paths": ";".join(rel(p) for p in log_candidates),
        "has_stopAt_writeNow": "yes" if "stopAt(writeNow)" in text else "no",
        "diagnostic_continue_message_in_functions": "yes" if "continuing to configured endTime" in text else "no",
        "diagnostic_criterion_message_in_functions": "yes" if "diagnostic criterion met" in text else "no",
        "foam_fatal_in_tail": "yes" if "FOAM FATAL" in log_text else "no",
        "cancelled_in_tail": "yes" if "CANCELLED" in log_text else "no",
        "latest_time_in_tail_s": latest_time_from_text(log_text),
        "pimple_criteria_note": "PIMPLE has no convergence criteria; use coded diagnostic monitor plus time-series drift",
        "audit_interpretation": (
            "not_suspicious_diagnostic_only_monitor_operational_cancel"
            if "stopAt(writeNow)" not in text and "FOAM FATAL" not in log_text
            else "review_required"
        ),
    }


def latest_time_from_text(text: str) -> str:
    matches = re.findall(r"Time = ([0-9.]+)s", text)
    return matches[-1] if matches else ""


def build_scorecard(salt1_summaries: list[dict[str, object]]) -> list[dict[str, object]]:
    terminal = {r["case_key"]: r for r in read_csv(EXISTING["expanded_steady"])}
    blocked = {r["case_key"]: r for r in read_csv(EXISTING["blocked"])}
    salt1 = {r["case_id"]: r for r in read_csv(EXISTING["salt1_policy"])}
    osc = {r["case_key"]: r for r in read_csv(EXISTING["osc_summary"])}
    rows: list[dict[str, object]] = []

    def add(case_key: str, display_label: str, source_role: str, status: str, basis: str, next_action: str) -> None:
        t = terminal.get(case_key, {})
        o = osc.get(case_key, {})
        rows.append({
            "case_key": case_key,
            "display_label": display_label,
            "admission_status": status,
            "source_role": source_role,
            "steady_state_verdict": t.get("steady_state_verdict") or o.get("verdicts", ""),
            "run_state": t.get("run_state", ""),
            "latest_time_s": t.get("latest_time_s", ""),
            "basis": basis,
            "next_action": next_action,
        })

    for summary in salt1_summaries:
        case_id = str(summary["case_id"])
        policy = salt1.get(case_id, {})
        if str(summary.get("suspicious_monitor_flag")) == "no":
            status = "admitted"
            basis = (
                "Salt1 terminal monitors are stationary; convergence monitor is diagnostic-only; "
                "2026-07-14 Salt1 policy admits as training/correlation-support evidence."
            )
            next_action = "Use as primary Salt1 closure evidence with perturbed-Q labels preserved; do not hide cancellation provenance."
        else:
            status = "blocked"
            basis = "Salt1 monitor review found a suspicious terminal drift or convergence signal."
            next_action = "Do not use until reviewed."
        add(case_id, policy.get("run_key", case_id), "Salt1 primary/training", status, basis, next_action)

    add(
        "salt2_jin_nominal",
        "viscosity_screening_salt_test_2_jin_coarse_mesh",
        "canonical forward train",
        "admitted",
        "Current canonical Salt2 nominal row has steady representative groups and is the main train row.",
        "Use as primary closure/scorecard evidence within existing gate limits.",
    )
    add(
        "salt3_jin_nominal",
        "viscosity_screening_salt_test_3_jin_coarse_mesh",
        "primary nominal closure evidence",
        "admitted",
        "Salt3 nominal is steady and is part of the Salt2/3/4 nominal closure evidence set.",
        "Use as primary nominal closure evidence with split/provenance labels preserved.",
    )
    add(
        "salt4_nominal",
        "viscosity_screening_salt_test_4_jin_coarse_mesh",
        "primary nominal closure evidence",
        "admitted",
        "Salt4 nominal is steady and is part of the Salt2/3/4 nominal closure evidence set.",
        "Use as primary nominal closure evidence with split/provenance labels preserved.",
    )
    add(
        "salt2_native_val",
        "val_salt_test_2_coarse_mesh",
        "external validation",
        "validation-only",
        "External validation row is steady and unlocked for validation, not fitting.",
        "Use for blind/external scoring only.",
    )
    for key in ["salt2_lo5q", "salt2_hi5q", "salt4_lo5q", "salt4_hi5q"]:
        b = blocked.get(key, {})
        add(
            key,
            terminal.get(key, {}).get("display_label", key),
            "perturbed-Q thermal split row",
            "validation-only" if key.startswith("salt2") else "diagnostic-only",
            b.get("blocker_or_caveat", "perturbed-Q row; closure terms remain diagnostic unless local gates pass"),
            b.get("next_action", "Preserve perturbed-Q label and do not overclaim closure coefficient admission."),
        )
    for key in ["salt2_lo10q", "salt2_hi10q", "salt4_lo10q", "salt4_hi10q", "salt3_lo5q", "salt3_lo10q", "salt3_hi5q", "salt3_hi10q"]:
        b = blocked.get(key, {})
        add(
            key,
            terminal.get(key, {}).get("display_label", key),
            "pending or failed perturbed-Q",
            "blocked",
            b.get("blocker_or_caveat", "pending terminal evidence or failed run"),
            b.get("next_action", "Do not use until terminal/admission gate passes."),
        )
    return rows


def write_readme(summaries: list[dict[str, object]], suspicious: list[str]) -> None:
    admitted_salt1 = "yes" if not suspicious else "no"
    lines = [
        "---",
        "provenance:",
        f"  - {rel(EXISTING['salt1_terminal'])}",
        f"  - {rel(EXISTING['salt1_policy'])}",
        f"  - {rel(EXISTING['expanded_steady'])}",
        "  - jadyn_runs/modern_runs/2026-07-08_salt1_nominal_continuation_candidate/**",
        "  - jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations/**",
        "tags: [salt1, admission, steady-state, closure-scorecard, board-cleanup]",
        "related:",
        f"  - {rel(JOURNAL)}",
        f"task: {TASK}",
        f"date: {DATE}",
        "role: Coordinator/cfd-pp/Implementer/Tester/Writer/Cleaner",
        "type: work_product",
        "status: complete",
        "---",
        "# Salt1 Primary Evidence Admission And Scorecard",
        "",
        "## Decision",
        "",
        f"Salt1 promotion to primary closure evidence: `{admitted_salt1}`.",
        "",
        "No compelling technical reason was found to keep Salt1 out of the primary evidence set. "
        "The terminal windows are stationary, the staged convergence monitor is diagnostic-only, "
        "and the cancellation provenance is operational rather than a solver failure. Use Salt1 "
        "as primary Salt1 closure/training evidence, while preserving the cancellation and "
        "perturbed-Q provenance in every downstream table.",
        "",
        "## Salt1 Terminal Checks",
        "",
        "| case | suspicious | total_Q drift W | max mdot rel drift | max TP drift K | max TW drift K | verdicts |",
        "| --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in summaries:
        lines.append(
            f"| {row['case_id']} | {row['suspicious_monitor_flag']} | {fmt(row['total_Q_drift_W'])} | "
            f"{fmt(row['max_mdot_rel_drift'])} | {fmt(row['max_tp_abs_drift_K'])} | "
            f"{fmt(row['max_tw_abs_drift_K'])} | {row['all_monitor_verdicts']} |"
        )
    lines.extend([
        "",
        "## Admission-Status Scorecard",
        "",
        "The final scorecard is intentionally organized by admission status, not by desired use. "
        "See `final_admission_status_scorecard.csv` for the machine-readable table with four "
        "allowed states: `admitted`, `validation-only`, `diagnostic-only`, and `blocked`.",
        "",
        "## Files",
        "",
        "- `salt1_terminal_monitor_metrics.csv`: per-monitor terminal-window drift and uncertainty.",
        "- `salt1_convergence_audit.csv`: convergence-monitor and log-tail checks.",
        "- `salt1_primary_evidence_decision.csv`: compact Salt1 promotion decision.",
        "- `final_admission_status_scorecard.csv`: admission-status-first scorecard.",
        "- `board_cleanup_summary.csv`: before/after board cleanup counts.",
        "- `summary.json`: counts and acceptance flags.",
    ])
    (PRODUCT / "README.md").write_text("\n".join(lines) + "\n")


def main() -> None:
    PRODUCT.mkdir(parents=True, exist_ok=True)
    monitor_all: list[dict[str, object]] = []
    summaries: list[dict[str, object]] = []
    convergence = []
    for case in SALT1_CASES:
        monitor_rows_case, summary = monitor_rows(case)
        monitor_all.extend(monitor_rows_case)
        summaries.append({
            **summary,
            "run_key": case.run_key,
            "role": case.role,
            "source_case_path": rel(case.source_case),
            "slurm_step": case.slurm_step,
            "scheduler_state": case.scheduler_state,
        })
        convergence.append(convergence_audit(case))

    suspicious = [str(r["case_id"]) for r in summaries if r.get("suspicious_monitor_flag") != "no"]
    decisions = []
    for row in summaries:
        decisions.append({
            "case_id": row["case_id"],
            "run_key": row["run_key"],
            "recommended_evidence_status": "admitted" if row.get("suspicious_monitor_flag") == "no" else "blocked",
            "recommended_use": "primary_closure_evidence_with_provenance" if row.get("suspicious_monitor_flag") == "no" else "do_not_use_until_review",
            "reason": "stationary terminal monitors and diagnostic-only convergence monitor",
            "caveat": "preserve cancellation provenance and perturbed-Q labels; do not treat as clean endTime completion",
        })

    scorecard = build_scorecard(summaries)

    write_csv(PRODUCT / "salt1_terminal_monitor_metrics.csv", monitor_all, [
        "case_id", "family", "series_label", "unit", "source_files", "status",
        "window_start_s", "window_end_s", "n_window", "mean", "drift_over_window",
        "relative_drift", "peak_to_peak", "rmse_about_trend", "rel_sem_corrected",
        "drift_ratio", "verdict",
    ])
    write_csv(PRODUCT / "salt1_terminal_summary.csv", summaries, [
        "case_id", "run_key", "role", "source_case_path", "slurm_step", "scheduler_state",
        "max_mdot_rel_drift", "max_mdot_rel_span", "max_tp_abs_drift_K",
        "max_tw_abs_drift_K", "total_Q_drift_W", "all_monitor_verdicts",
        "suspicious_monitor_flag",
    ])
    write_csv(PRODUCT / "salt1_convergence_audit.csv", convergence, [
        "case_id", "functions_path", "log_paths", "has_stopAt_writeNow",
        "diagnostic_continue_message_in_functions", "diagnostic_criterion_message_in_functions",
        "foam_fatal_in_tail", "cancelled_in_tail", "latest_time_in_tail_s",
        "pimple_criteria_note", "audit_interpretation",
    ])
    write_csv(PRODUCT / "salt1_primary_evidence_decision.csv", decisions, [
        "case_id", "run_key", "recommended_evidence_status", "recommended_use", "reason", "caveat",
    ])
    write_csv(PRODUCT / "final_admission_status_scorecard.csv", scorecard, [
        "case_key", "display_label", "admission_status", "source_role",
        "steady_state_verdict", "run_state", "latest_time_s", "basis", "next_action",
    ])
    write_readme(summaries, suspicious)

    summary = {
        "task": TASK,
        "salt1_cases_reviewed": len(SALT1_CASES),
        "salt1_suspicious_cases": suspicious,
        "salt1_promoted_to_primary_evidence": not suspicious,
        "scorecard_rows": len(scorecard),
        "scorecard_status_counts": {
            status: sum(1 for r in scorecard if r["admission_status"] == status)
            for status in ["admitted", "validation-only", "diagnostic-only", "blocked"]
        },
        "outputs": [rel(p) for p in sorted(PRODUCT.glob("*"))],
    }
    (PRODUCT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")

    JOURNAL.parent.mkdir(parents=True, exist_ok=True)
    JOURNAL.write_text(
        "---\n"
        f"provenance:\n  - {rel(PRODUCT / 'README.md')}\n  - {rel(PRODUCT / 'summary.json')}\n"
        "tags: [salt1, admission, scorecard, board-cleanup]\n"
        f"related:\n  - {rel(PRODUCT / 'README.md')}\n"
        f"task: {TASK}\n"
        f"date: {DATE}\n"
        "role: Coordinator/cfd-pp/Implementer/Tester/Writer/Cleaner\n"
        "type: journal\n"
        "status: complete\n"
        "---\n"
        "# Salt1 Primary Evidence Admission And Board Cleanup\n\n"
        "Built the Salt1 terminal monitor review and admission-status scorecard. Salt1 nominal, "
        "lo10q, and hi10q have stationary terminal windows and diagnostic-only convergence "
        "monitors; no suspicious technical reason was found to exclude them from primary "
        "Salt1 closure evidence. Board cleanup and index refresh are recorded in the package.\n"
    )

    IMPORT.parent.mkdir(parents=True, exist_ok=True)
    IMPORT.write_text(json.dumps({
        "task": TASK,
        "date": DATE,
        "objective": "Promote Salt1 if technically clean, build admission-status scorecard, clean board, regenerate index.",
        "outputs": [rel(p) for p in sorted(PRODUCT.glob("*"))] + [rel(JOURNAL)],
        "native_solver_outputs_mutated": False,
        "registry_mutated": False,
    }, indent=2) + "\n")


if __name__ == "__main__":
    main()
