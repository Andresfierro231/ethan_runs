#!/usr/bin/env python3
"""Build a read-only PM10 terminal/admission disposition packet.

This script consumes existing scheduler, drift, split-policy, steady-window,
and upcomer-recirculation evidence. It does not launch, stage, harvest, admit
to registry state, fit, score protected rows, or mutate native CFD outputs.
"""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


TASK_ID = "TODO-PREDICT-SALT-PM10-TERMINAL-ADMISSION"
DATE = "2026-07-22"
OUTDIR = Path("work_products/2026-07/2026-07-22/2026-07-22_predict_salt_pm10_terminal_admission")

READINESS_DIR = Path("work_products/2026-07/2026-07-17/2026-07-17_salt_pm10_terminal_admission_readiness")
STATUS_TABLE = Path(
    "work_products/2026-07/2026-07-14/"
    "2026-07-14_corrected_q_postprocess_harvest_submission/"
    "selected_salt2_salt4_pm10q_after_3293924/status_table/selected_corrected_q_status_table.csv"
)
LIVE_MONITOR = Path(
    "work_products/2026-07/2026-07-14/"
    "2026-07-14_corrected_q_postprocess_harvest_submission/"
    "selected_salt2_salt4_pm10q_after_3293924/terminal_monitor_after_3293924/"
    "live_salt_sanity_monitor.csv"
)
TERMINAL_CLASS_DIR = Path(
    "work_products/2026-07/2026-07-20/2026-07-20_salt_pm10_terminal_admission_classification"
)
TERMINAL_DRIFT = TERMINAL_CLASS_DIR / "pm10_terminal_drift.csv"
SPLIT_TABLE = Path(
    "work_products/2026-07/2026-07-17/2026-07-17_corrected_split_final_predictive_scorecard/"
    "split_legal_case_table.csv"
)
UPCOMER_DIR = Path("work_products/2026-07/2026-07-20/2026-07-20_pm10_upcomer_anchor_admission")
UPCOMER_CLASS = UPCOMER_DIR / "pm10_upcomer_anchor_classification.csv"
UPCOMER_GATE = UPCOMER_DIR / "pm10_model_use_gate.csv"
ONSET_LEDGER = Path(
    "work_products/2026-07/2026-07-20/2026-07-20_upcomer_onset_blocker_execution/"
    "upcomer_anchor_admission_ledger_pm10_resolved.csv"
)
STEADY_BASE = Path("work_products/2026-07/2026-07-09/2026-07-09_timeseries_steadystate/cases")

CASE_KEYS = ["salt2_lo10q", "salt2_hi10q", "salt4_lo10q", "salt4_hi10q"]
SOURCE_KEYS = {
    "salt2_lo10q": "salt2_jin_lo10q_corrected",
    "salt2_hi10q": "salt2_jin_hi10q_corrected",
    "salt4_lo10q": "salt4_jin_lo10q_corrected",
    "salt4_hi10q": "salt4_jin_hi10q_corrected",
}

SCHEDULER_ROWS = [
    {
        "job_id": "3293924",
        "step": "3293924",
        "job_name": "saltq_sel_cont",
        "state": "TIMEOUT",
        "exit_code": "0:0",
        "elapsed": "5-00:00:06",
        "start": "2026-07-13T17:03:56",
        "end": "2026-07-18T17:04:02",
        "nodelist": "c318-016",
        "role": "packed Salt2/Salt4 +/-10Q solver continuation",
        "terminal_for_this_packet": "yes_timeout_terminal",
        "source": "sacct -j 3293924,3295438 --format=JobID,JobName,State,ExitCode,Elapsed,Start,End,NodeList -P on 2026-07-22",
    },
    {
        "job_id": "3293924",
        "step": "3293924.batch",
        "job_name": "batch",
        "state": "CANCELLED",
        "exit_code": "0:15",
        "elapsed": "5-00:00:06",
        "start": "2026-07-13T17:03:56",
        "end": "2026-07-18T17:04:02",
        "nodelist": "c318-016",
        "role": "solver batch step cancelled by timeout",
        "terminal_for_this_packet": "yes_timeout_step_terminal",
        "source": "sacct -j 3293924,3295438 --format=JobID,JobName,State,ExitCode,Elapsed,Start,End,NodeList -P on 2026-07-22",
    },
    {
        "job_id": "3295438",
        "step": "3295438",
        "job_name": "saltq_s24_sel_harv",
        "state": "COMPLETED",
        "exit_code": "0:0",
        "elapsed": "00:35:41",
        "start": "2026-07-18T17:04:13",
        "end": "2026-07-18T17:39:54",
        "nodelist": "c318-019",
        "role": "dependent Salt2/Salt4 +/-10Q harvest/postprocess job",
        "terminal_for_this_packet": "yes_completed_terminal",
        "source": "sacct -j 3293924,3295438 --format=JobID,JobName,State,ExitCode,Elapsed,Start,End,NodeList -P on 2026-07-22",
    },
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: Iterable[dict[str, object]], fieldnames: list[str] | None = None) -> None:
    rows = list(rows)
    if fieldnames is None:
        keys: list[str] = []
        for row in rows:
            for key in row:
                if key not in keys:
                    keys.append(key)
        fieldnames = keys
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def stats_path_for(case_key: str) -> Path:
    source_key = SOURCE_KEYS[case_key]
    salt = "salt2" if case_key.startswith("salt2") else "salt4"
    slug = (
        f"modern_runs__2026-07-04_corrected_salt_q_perturbations__{source_key}__"
        f"viscosity_screening_salt_test_{salt[-1]}_jin_coarse_mesh_continuation"
    )
    return STEADY_BASE / slug / "stats.csv"


def representative_stats(case_key: str) -> list[dict[str, str]]:
    path = stats_path_for(case_key)
    rows = read_csv(path)
    selected = []
    for row in rows:
        if row.get("representative") != "True":
            continue
        if row.get("group") in {"mdot", "temperature", "wall_temperature", "heat"}:
            out = dict(row)
            out["case_key"] = case_key
            out["source_key"] = SOURCE_KEYS[case_key]
            out["stats_path"] = str(path)
            selected.append(out)
    return selected


def summarize_stats(case_key: str) -> dict[str, object]:
    rows = representative_stats(case_key)

    def group_rows(group: str) -> list[dict[str, str]]:
        return [row for row in rows if row.get("group") == group]

    def max_float(group: str, field: str) -> float | None:
        vals: list[float] = []
        for row in group_rows(group):
            try:
                vals.append(abs(float(row[field])))
            except (KeyError, TypeError, ValueError):
                pass
        return max(vals) if vals else None

    mdot = group_rows("mdot")[0] if group_rows("mdot") else {}
    heat = group_rows("heat")[0] if group_rows("heat") else {}
    return {
        "case_key": case_key,
        "source_key": SOURCE_KEYS[case_key],
        "representative_mdot_verdict": mdot.get("verdict", ""),
        "representative_mdot_rel_drift_fraction": mdot.get("rel_drift_over_window", ""),
        "representative_mdot_t_last_s": mdot.get("t_last", ""),
        "representative_mdot_kg_s_mean": mdot.get("osc_mean", ""),
        "max_representative_T_rel_drift_fraction": max_float("temperature", "rel_drift_over_window"),
        "max_representative_wall_T_rel_drift_fraction": max_float("wall_temperature", "rel_drift_over_window"),
        "total_Q_verdict": heat.get("verdict", ""),
        "total_Q_rel_drift_fraction": heat.get("rel_drift_over_window", ""),
        "total_Q_mean_W": heat.get("osc_mean", ""),
        "stats_path": str(stats_path_for(case_key)),
    }


def by_key(rows: list[dict[str, str]], key: str = "case_key") -> dict[str, dict[str, str]]:
    return {row[key]: row for row in rows if row.get(key)}


def build(outdir: Path = OUTDIR) -> dict[str, object]:
    outdir.mkdir(parents=True, exist_ok=True)

    readiness = by_key(read_csv(READINESS_DIR / "pm10_case_readiness.csv"))
    status = by_key(read_csv(STATUS_TABLE))
    terminal = by_key(read_csv(TERMINAL_DRIFT))
    split = by_key(read_csv(SPLIT_TABLE))
    upcomer = by_key(read_csv(UPCOMER_CLASS))
    upcomer_gate = by_key(read_csv(UPCOMER_GATE))

    write_csv(outdir / "scheduler_terminal_evidence.csv", SCHEDULER_ROWS)

    steady_rows = [summarize_stats(case_key) for case_key in CASE_KEYS]
    write_csv(outdir / "pm10_steadiness_metric_context.csv", steady_rows)
    steady_by_case = by_key([{k: "" if v is None else str(v) for k, v in row.items()} for row in steady_rows])

    gate_rows: list[dict[str, object]] = []
    split_rows: list[dict[str, object]] = []
    recirc_rows: list[dict[str, object]] = []
    inventory_rows: list[dict[str, object]] = []

    for case_key in CASE_KEYS:
        trow = terminal[case_key]
        srow = split[case_key]
        urow = upcomer[case_key]
        grow = upcomer_gate[case_key]
        steady = steady_by_case[case_key]
        terminal_ok = (
            trow.get("terminal_drift_status") == "pass"
            and trow.get("strict_log_status") == "pass"
            and status[case_key].get("closure_fit_admissible") == "yes"
        )
        split_score_after = "yes_after_terminal_admission_and_final_freeze"
        final_fit = "no"
        final_model_selection = "no"
        blind_score_now = "no"
        gate_rows.append(
            {
                "case_key": case_key,
                "source_key": SOURCE_KEYS[case_key],
                "fluid": trow.get("fluid", ""),
                "q_ratio": trow.get("q_ratio", ""),
                "solver_job_id": "3293924",
                "solver_job_state": "TIMEOUT",
                "harvest_job_id": "3295438",
                "harvest_job_state": "COMPLETED",
                "squeue_live_on_2026_07_22": "no",
                "latest_solver_time_s": trow.get("latest_solver_time_s", ""),
                "latest_registered_timestep_s": trow.get("latest_registered_timestep", ""),
                "post_restart_advance": trow.get("post_restart_advance_so_far", ""),
                "mdot_latest_kg_s": trow.get("mdot_latest_kg_s", ""),
                "mdot_moved_pct": trow.get("mdot_moved_pct", ""),
                "mdot_late_window_drift_pct": trow.get("late_window_drift_pct", ""),
                "mdot_late_window_amp_pct": trow.get("late_window_amp_pct", ""),
                "terminal_drift_status": trow.get("terminal_drift_status", ""),
                "strict_log_status": trow.get("strict_log_status", ""),
                "status_table_verdict": status[case_key].get("status", ""),
                "representative_mdot_verdict": steady.get("representative_mdot_verdict", ""),
                "representative_mdot_rel_drift_fraction": steady.get("representative_mdot_rel_drift_fraction", ""),
                "total_Q_verdict": steady.get("total_Q_verdict", ""),
                "total_Q_rel_drift_fraction": steady.get("total_Q_rel_drift_fraction", ""),
                "terminal_evidence_admitted": "yes" if terminal_ok else "no",
                "admission_disposition": (
                    "terminal_admitted_for_future_blind_holdout_evidence_only"
                    if terminal_ok
                    else "blocked_terminal_gate"
                ),
                "fit_allowed_now": final_fit,
                "model_selection_allowed_now": final_model_selection,
                "protected_score_allowed_now": blind_score_now,
                "protected_score_allowed_after_freeze": split_score_after,
                "runtime_input_allowed_now": "no",
                "ordinary_upcomer_closure_allowed": "no",
                "source_property_release_allowed": "no",
            }
        )
        split_rows.append(
            {
                "case_key": case_key,
                "source_key": SOURCE_KEYS[case_key],
                "canonical_policy_role": srow.get("canonical_policy_role", ""),
                "corrected_scorecard_role": srow.get("corrected_scorecard_role", ""),
                "terminal_admission_update": "terminal_evidence_now_available",
                "final_fit_allowed": final_fit,
                "final_model_selection_allowed": final_model_selection,
                "blind_score_allowed_now": blind_score_now,
                "blind_score_allowed_after_final_freeze": split_score_after,
                "use_in_current_final_scorecard": "no",
                "use_now": "diagnostic_terminal_evidence_and_future_holdout_planning",
                "guardrail": (
                    "do_not_fit_or_model_select; do_not_use_as_runtime_input; "
                    "score only after an independently frozen candidate exists"
                ),
            }
        )
        recirc_rows.append(
            {
                "case_key": case_key,
                "source_key": SOURCE_KEYS[case_key],
                "upcomer_admission_classification": urow.get("upcomer_admission_classification", ""),
                "recirculation_severity_class": urow.get("recirculation_severity_class", ""),
                "representative_time_s": urow.get("representative_time_s", ""),
                "max_reverse_area_fraction": urow.get("max_reverse_area_fraction", ""),
                "max_reverse_mass_fraction": urow.get("max_reverse_mass_fraction", ""),
                "max_secondary_velocity_fraction": urow.get("max_secondary_velocity_fraction", ""),
                "max_Ri": urow.get("max_Ri", ""),
                "ordinary_pipe_fit_allowed": urow.get("ordinary_pipe_fit_allowed", ""),
                "ordinary_pipe_model_selection_allowed": urow.get("ordinary_pipe_model_selection_allowed", ""),
                "recirculation_anchor_allowed": urow.get("recirculation_anchor_allowed", ""),
                "recirculation_calibration_allowed": urow.get("recirculation_calibration_allowed", ""),
                "hybrid_validation_allowed": urow.get("hybrid_validation_allowed", ""),
                "fit_allowed_now": grow.get("fit_allowed_now", ""),
                "model_selection_allowed_now": grow.get("model_selection_allowed_now", ""),
                "runtime_input_allowed_now": grow.get("runtime_input_allowed_now", ""),
                "allowed_use_now": urow.get("allowed_use_now", "recirculation diagnostic only"),
                "blocked_use": "ordinary upcomer Nu/f_D/K; onset anchor; runtime exchange closure",
            }
        )
        inventory_rows.extend(
            [
                {
                    "case_key": case_key,
                    "evidence_family": "terminal_mdot_drift",
                    "availability": "available",
                    "admission_use": "terminal gate and future holdout evidence planning",
                    "runtime_use_allowed": "no",
                    "source_path": str(TERMINAL_DRIFT),
                },
                {
                    "case_key": case_key,
                    "evidence_family": "steady_window_temperatures_and_total_Q",
                    "availability": "available_with_total_Q_drift_label",
                    "admission_use": "diagnostic context; heat source release remains forbidden",
                    "runtime_use_allowed": "no",
                    "source_path": steady.get("stats_path", ""),
                },
                {
                    "case_key": case_key,
                    "evidence_family": "upcomer_U_T_wall_plane_recirculation",
                    "availability": "available",
                    "admission_use": "recirculation diagnostic and ordinary-closure blocker",
                    "runtime_use_allowed": "no",
                    "source_path": str(UPCOMER_CLASS),
                },
                {
                    "case_key": case_key,
                    "evidence_family": "split_policy",
                    "availability": "available",
                    "admission_use": "future holdout planning only",
                    "runtime_use_allowed": "no",
                    "source_path": str(SPLIT_TABLE),
                },
                {
                    "case_key": case_key,
                    "evidence_family": "pressure_ladder_streamwise_maps",
                    "availability": "not_built_in_this_row",
                    "admission_use": "next executable analysis before pressure-form claims",
                    "runtime_use_allowed": "no",
                    "source_path": "",
                },
                {
                    "case_key": case_key,
                    "evidence_family": "heat_loss_ledger",
                    "availability": "not_built_in_this_row",
                    "admission_use": "next executable analysis before thermal/source claims",
                    "runtime_use_allowed": "no",
                    "source_path": "",
                },
            ]
        )

    write_csv(outdir / "pm10_case_terminal_gate.csv", gate_rows)
    write_csv(outdir / "pm10_split_use_decision.csv", split_rows)
    write_csv(outdir / "pm10_recirc_onset_summary.csv", recirc_rows)
    write_csv(outdir / "pm10_heat_pressure_evidence_inventory.csv", inventory_rows)

    guardrails = [
        {
            "guardrail": "native_CFD_output_mutation",
            "status": "none",
            "reason": "all source case roots and postProcessing artifacts consumed read-only",
        },
        {
            "guardrail": "scheduler_action",
            "status": "none",
            "reason": "only squeue/sacct observations were consumed; no sbatch/srun/scancel",
        },
        {
            "guardrail": "registry_or_admission_state_mutation",
            "status": "none",
            "reason": "packet is a disposition artifact, not registry admission",
        },
        {
            "guardrail": "protected_scoring",
            "status": "none",
            "reason": "PM10 rows remain future blind holdout candidates; score only after final freeze",
        },
        {
            "guardrail": "fit_or_model_selection",
            "status": "none",
            "reason": "all four PM10 rows keep fit/model-selection forbidden",
        },
        {
            "guardrail": "runtime_input_release",
            "status": "none",
            "reason": "recirculation, wallHeatFlux, realized mdot, and total_Q evidence are diagnostics only",
        },
        {
            "guardrail": "source_property_release",
            "status": "none",
            "reason": "no source/property/Qwall release was performed",
        },
    ]
    write_csv(outdir / "no_mutation_guardrails.csv", guardrails)

    sources = [
        {
            "path": str(READINESS_DIR / "pm10_case_readiness.csv"),
            "role": "previous readiness and pre-terminal split context",
            "read_only": "yes",
        },
        {"path": str(STATUS_TABLE), "role": "post-harvest terminal status table", "read_only": "yes"},
        {"path": str(LIVE_MONITOR), "role": "legacy terminal monitor context", "read_only": "yes"},
        {"path": str(TERMINAL_DRIFT), "role": "strict terminal drift and log gate", "read_only": "yes"},
        {"path": str(SPLIT_TABLE), "role": "canonical final split legality", "read_only": "yes"},
        {"path": str(UPCOMER_CLASS), "role": "PM10 upcomer recirculation classification", "read_only": "yes"},
        {"path": str(UPCOMER_GATE), "role": "PM10 upcomer model-use gate", "read_only": "yes"},
        {"path": str(ONSET_LEDGER), "role": "recirculation/onset blocker ledger", "read_only": "yes"},
    ]
    for case_key in CASE_KEYS:
        sources.append(
            {
                "path": str(stats_path_for(case_key)),
                "role": f"{case_key} representative steady-window metrics",
                "read_only": "yes",
            }
        )
    write_csv(outdir / "source_manifest.csv", sources)

    summary = {
        "task": TASK_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "output_dir": str(outdir),
        "case_count": len(CASE_KEYS),
        "scheduler_terminal": "yes",
        "solver_job_id": "3293924",
        "solver_job_state": "TIMEOUT",
        "harvest_job_id": "3295438",
        "harvest_job_state": "COMPLETED",
        "squeue_live_rows_on_2026_07_22": 0,
        "terminal_evidence_admitted_rows": sum(1 for row in gate_rows if row["terminal_evidence_admitted"] == "yes"),
        "future_holdout_candidate_rows": len(CASE_KEYS),
        "fit_allowed_now_rows": 0,
        "model_selection_allowed_now_rows": 0,
        "protected_score_allowed_now_rows": 0,
        "runtime_input_allowed_now_rows": 0,
        "ordinary_upcomer_closure_allowed_rows": 0,
        "recirculation_diagnostic_rows": len(CASE_KEYS),
        "total_Q_not_steady_rows": sum(1 for row in steady_rows if row["total_Q_verdict"] != "steady"),
        "native_output_mutation": "none",
        "registry_mutation": "none",
        "scheduler_action": "none",
        "external_fluid_action": "none",
        "final_score": "not_performed",
        "disposition": (
            "PM10 Salt2/Salt4 +/-10Q terminal evidence is available and passes existing drift/log gates, "
            "but the rows remain future blind-holdout diagnostic evidence: no fit, no model selection, "
            "no runtime input release, and no protected score until a candidate is frozen independently."
        ),
    }
    write_json(outdir / "summary.json", summary)

    readme = f"""# {TASK_ID}

Generated: {summary['generated_at_utc']}

This package closes the pre-terminal ambiguity for the Salt2/Salt4 +/-10Q
PM10 rows using read-only evidence. `3293924` is terminal as `TIMEOUT`, the
dependent harvester `3295438` is `COMPLETED`, and the local terminal drift
classification reports four passing case gates.

## Disposition

- `salt2_lo10q`, `salt2_hi10q`, `salt4_lo10q`, and `salt4_hi10q` have terminal
  evidence available and pass the existing strict terminal drift/log gate.
- They are not admitted for fitting, model selection, runtime inputs, source
  release, or current final scorecard scoring.
- They are future blind-holdout candidates that may be scored only after an
  independently frozen predictive candidate exists.
- Upcomer evidence classifies all four as strong recirculation diagnostics.
  Ordinary upcomer `Nu`, `f_D`, or component-`K` fitting remains forbidden.
- Representative mdot and temperature windows are finite. `total_Q` remains
  drifting in the representative steady-window table, so it is diagnostic
  context only and cannot release a source/property correction.

## Outputs

- `scheduler_terminal_evidence.csv`
- `pm10_case_terminal_gate.csv`
- `pm10_steadiness_metric_context.csv`
- `pm10_split_use_decision.csv`
- `pm10_recirc_onset_summary.csv`
- `pm10_heat_pressure_evidence_inventory.csv`
- `no_mutation_guardrails.csv`
- `source_manifest.csv`
- `summary.json`

## Next Executable Work

1. Build the pressure ladder and streamwise pressure-map packet from the
   admitted terminal PM10 evidence without fitting to protected rows.
2. Build a heat-loss/source ledger that keeps wallHeatFlux and total_Q as
   diagnostics until an independent source/property release row is claimed.
3. Use the PM10 recirculation metrics as blocked-ordinary-closure evidence in
   the thesis recirculation/onset packet, not as an ordinary pipe anchor.
"""
    (outdir / "README.md").write_text(readme, encoding="utf-8")

    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=OUTDIR)
    args = parser.parse_args(argv)
    summary = build(args.output_dir)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
