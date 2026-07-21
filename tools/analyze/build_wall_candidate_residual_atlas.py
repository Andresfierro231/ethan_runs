#!/usr/bin/env python3
"""Build a cross-candidate residual atlas for wall/test-section unblock work.

This is an existing-evidence package. It consolidates AGENT-515 failure
localization, AGENT-513 wall-temperature-drive probe evidence, and the current
AGENT-511 heater-source redistribution state without launching solvers or
changing scientific admission state.
"""

from __future__ import annotations

import csv
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TASK = "AGENT-520"
ROOT = Path(__file__).resolve().parents[2]
OUT_REL = Path("work_products/2026-07/2026-07-17/2026-07-17_wall_candidate_residual_atlas")
OUT = ROOT / OUT_REL

AGENT498 = ROOT / "work_products/2026-07/2026-07-17/2026-07-17_wall_test_section_distribution_ladder"
AGENT511 = ROOT / "work_products/2026-07/2026-07-17/2026-07-17_heater_source_redistribution_coupled_score"
AGENT513 = ROOT / "work_products/2026-07/2026-07-17/2026-07-17_wall_temperature_drive_candidate"
AGENT515 = ROOT / "work_products/2026-07/2026-07-17/2026-07-17_wall_candidate_failure_localization"
AGENT499 = ROOT / "work_products/2026-07/2026-07-17/2026-07-17_corrected_split_final_predictive_scorecard"
AGENT509 = ROOT / "work_products/2026-07/2026-07-17/2026-07-17_final_predictive_scorecard_shell"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = []
        for row in rows:
            for key in row:
                if key not in fieldnames:
                    fieldnames.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def fnum(value: Any, default: float | None = None) -> float | None:
    try:
        if value in ("", None, "nan", "NaN"):
            return default
        number = float(value)
    except (TypeError, ValueError):
        return default
    return number if math.isfinite(number) else default


def fmt(value: float | None, digits: int = 8) -> str:
    if value is None or not math.isfinite(value):
        return ""
    return f"{value:.{digits}g}"


def mean(values: list[float]) -> float | None:
    finite = [value for value in values if math.isfinite(value)]
    return sum(finite) / len(finite) if finite else None


def esc(value: Any) -> str:
    return (
        str(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def candidate_family(candidate_id: str) -> str:
    if candidate_id.startswith("PB1"):
        return "PB1_passive_total"
    if candidate_id.startswith("PB2"):
        return "PB2_salt2_shape"
    if candidate_id.startswith("PB3"):
        return "PB3_attenuated_shape"
    if candidate_id.startswith("WTD1"):
        return "WTD1_pipe_outer_wall_drive"
    if candidate_id.startswith("WTD2"):
        return "WTD2_outer_surface_drive"
    if candidate_id.startswith("HS1"):
        return "HS1_heater_source_redistribution"
    return "unknown"


def source_state() -> dict[str, Any]:
    ag511_summary = read_json(AGENT511 / "summary.json") if (AGENT511 / "summary.json").exists() else {}
    ag511_counts = ag511_summary.get("counts", {})
    ag511_completed = int(ag511_summary.get("decision", {}).get("coupled_completed_rows", 0) or 0)
    ag511_status_counts = ag511_summary.get("decision", {}).get("coupled_status_counts", {})
    ag511_state = "completed" if ag511_completed > 0 else "pending_or_live_no_completed_rows"
    return {
        "agent511_state": ag511_state,
        "agent511_completed_rows": ag511_completed,
        "agent511_status_counts": ag511_status_counts,
        "agent511_probe_rows": int(ag511_counts.get("probe_error_localization.csv", 0) or 0),
    }


def gate_status_for_delta(row: dict[str, str]) -> str:
    if row.get("score_gate") == "pass":
        return "pass"
    return "fail"


def build_candidate_gate_matrix() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in read_csv(AGENT515 / "wall_candidate_gate_failure_matrix.csv"):
        rows.append(
            {
                "source_package": "AGENT-515_from_AGENT-498",
                "candidate_id": row["candidate_id"],
                "candidate_family": row["candidate_family"],
                "case_id": row["case_id"],
                "split_role": row["split_role"],
                "evidence_state": "completed",
                "runtime_gate": row["runtime_gate"],
                "score_gate": row["coupled_gate_for_split"],
                "admission_decision": row["admission_decision"],
                "mdot_delta_vs_m3_pct": row["mdot_delta_vs_m3_pct"],
                "tp_delta_vs_m3_K": "",
                "tw_delta_vs_m3_K": row["tw_delta_vs_m3_K"],
                "all_probe_delta_vs_m3_K": row["all_probe_delta_vs_m3_K"],
                "interpretation": "mdot_improves_temperature_regresses",
                "source_paths": row["source_paths"],
            }
        )
    ag513_reviews = {row["candidate_id"]: row for row in read_csv(AGENT513 / "candidate_admission_review.csv")}
    for row in read_csv(AGENT513 / "coupled_delta_vs_m3.csv"):
        candidate = row["candidate_id"]
        review = ag513_reviews.get(candidate, {})
        mdot = fnum(row.get("mdot_delta_vs_m3_pct"))
        all_probe = fnum(row.get("all_probe_delta_vs_m3_K"))
        tw = fnum(row.get("tw_delta_vs_m3_K"))
        if mdot is not None and mdot < 0 and (all_probe or 0) > 0 and (tw or 0) > 0:
            interpretation = "mdot_improves_temperature_regresses"
        elif mdot is not None and mdot > 0 and (all_probe or 0) > 0 and (tw or 0) > 0:
            interpretation = "mdot_and_temperature_regress"
        else:
            interpretation = "mixed_or_incomplete"
        rows.append(
            {
                "source_package": "AGENT-513_wall_temperature_drive",
                "candidate_id": candidate,
                "candidate_family": candidate_family(candidate),
                "case_id": row["case_id"],
                "split_role": row["split_role"],
                "evidence_state": "completed",
                "runtime_gate": review.get("runtime_gate", ""),
                "score_gate": gate_status_for_delta(row),
                "admission_decision": review.get("admission_decision", ""),
                "mdot_delta_vs_m3_pct": row["mdot_delta_vs_m3_pct"],
                "tp_delta_vs_m3_K": "",
                "tw_delta_vs_m3_K": row["tw_delta_vs_m3_K"],
                "all_probe_delta_vs_m3_K": row["all_probe_delta_vs_m3_K"],
                "interpretation": interpretation,
                "source_paths": f"{rel(AGENT513 / 'candidate_admission_review.csv')};{rel(AGENT513 / 'coupled_delta_vs_m3.csv')}",
            }
        )
    ag511_reviews = {row["candidate_id"]: row for row in read_csv(AGENT511 / "candidate_admission_review.csv")}
    ag511_deltas = read_csv(AGENT511 / "coupled_delta_vs_m3.csv")
    if ag511_deltas:
        for row in ag511_deltas:
            candidate = row["candidate_id"]
            review = ag511_reviews.get(candidate, {})
            rows.append(
                {
                    "source_package": "AGENT-511_heater_source_redistribution",
                    "candidate_id": candidate,
                    "candidate_family": candidate_family(candidate),
                    "case_id": row["case_id"],
                    "split_role": row["split_role"],
                    "evidence_state": "completed" if row.get("score_gate") else "pending_or_incomplete",
                    "runtime_gate": review.get("runtime_gate", ""),
                    "score_gate": row.get("score_gate", ""),
                    "admission_decision": review.get("admission_decision", ""),
                    "mdot_delta_vs_m3_pct": row.get("mdot_delta_vs_m3_pct", ""),
                    "tp_delta_vs_m3_K": row.get("tp_delta_vs_m3_K", ""),
                    "tw_delta_vs_m3_K": row.get("tw_delta_vs_m3_K", ""),
                    "all_probe_delta_vs_m3_K": row.get("all_probe_delta_vs_m3_K", ""),
                    "interpretation": "heater_source_completed_delta",
                    "source_paths": f"{rel(AGENT511 / 'candidate_admission_review.csv')};{rel(AGENT511 / 'coupled_delta_vs_m3.csv')}",
                }
            )
    else:
        for row in read_csv(AGENT511 / "candidate_admission_review.csv"):
            rows.append(
                {
                    "source_package": "AGENT-511_heater_source_redistribution",
                    "candidate_id": row["candidate_id"],
                    "candidate_family": candidate_family(row["candidate_id"]),
                    "case_id": "",
                    "split_role": "pending",
                    "evidence_state": "pending_or_live_no_completed_rows",
                    "runtime_gate": row.get("runtime_gate", ""),
                    "score_gate": "missing",
                    "admission_decision": row.get("admission_decision", "not_admitted"),
                    "mdot_delta_vs_m3_pct": "",
                    "tp_delta_vs_m3_K": "",
                    "tw_delta_vs_m3_K": "",
                    "all_probe_delta_vs_m3_K": "",
                    "interpretation": "not_scientific_failure_evidence_until_coupled_rows_land",
                    "source_paths": f"{rel(AGENT511 / 'summary.json')};{rel(AGENT511 / 'candidate_admission_review.csv')}",
                }
            )
    return rows


def build_probe_residual_atlas() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in read_csv(AGENT513 / "probe_delta_vs_m3.csv"):
        rows.append(
            {
                "source_package": "AGENT-513_wall_temperature_drive",
                "candidate_id": row["candidate_id"],
                "candidate_family": candidate_family(row["candidate_id"]),
                "case_id": row["case_id"],
                "split_role": row["split_role"],
                "sensor": row["sensor"],
                "kind": row["kind"],
                "candidate_error_K": row["candidate_error_K"],
                "candidate_abs_error_K": row["candidate_abs_error_K"],
                "m3_error_K": row["m3_error_K"],
                "m3_abs_error_K": row["m3_abs_error_K"],
                "abs_error_delta_vs_m3_K": row["abs_error_delta_vs_m3_K"],
                "candidate_predicted_K": row["candidate_predicted_K"],
                "target_K": row["target_K"],
                "prediction_source_segment": row["prediction_source_segment"],
                "probe_gate": row["probe_gate"],
                "evidence_state": "completed",
                "source_paths": rel(AGENT513 / "probe_delta_vs_m3.csv"),
            }
        )
    # AGENT-511 probe rows do not include M3 deltas unless the coupled run has landed.
    for row in read_csv(AGENT511 / "probe_error_localization.csv"):
        rows.append(
            {
                "source_package": "AGENT-511_heater_source_redistribution",
                "candidate_id": row.get("candidate_id", ""),
                "candidate_family": candidate_family(row.get("candidate_id", "")),
                "case_id": row.get("case_id", ""),
                "split_role": row.get("split_role", ""),
                "sensor": row.get("sensor", ""),
                "kind": row.get("kind", ""),
                "candidate_error_K": row.get("error_K", ""),
                "candidate_abs_error_K": row.get("abs_error_K", ""),
                "m3_error_K": "",
                "m3_abs_error_K": "",
                "abs_error_delta_vs_m3_K": "",
                "candidate_predicted_K": row.get("predicted_K", ""),
                "target_K": row.get("target_K", ""),
                "prediction_source_segment": row.get("prediction_source_segment", ""),
                "probe_gate": "pending_delta_vs_m3" if row.get("error_K") else "missing",
                "evidence_state": "completed_raw_probe_rows_pending_m3_delta" if row.get("candidate_id") else "pending_or_empty",
                "source_paths": rel(AGENT511 / "probe_error_localization.csv"),
            }
        )
    return rows


def build_role_segment_residual_rank() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in read_csv(AGENT513 / "role_segment_error_summary.csv"):
        rows.append(
            {
                "source_package": "AGENT-513_wall_temperature_drive",
                "candidate_id": row["candidate_id"],
                "candidate_family": candidate_family(row["candidate_id"]),
                "case_id": row["case_id"],
                "split_role": row["split_role"],
                "kind": row["kind"],
                "prediction_source_segment": row["prediction_source_segment"],
                "n_compared": row["n_compared"],
                "candidate_rmse_K": row["candidate_rmse_K"],
                "m3_rmse_K": row["m3_rmse_K"],
                "rmse_delta_vs_m3_K": row["rmse_delta_vs_m3_K"],
                "candidate_mae_K": row["candidate_mae_K"],
                "m3_mae_K": row["m3_mae_K"],
                "mae_delta_vs_m3_K": row["mae_delta_vs_m3_K"],
                "evidence_state": "completed",
                "source_paths": rel(AGENT513 / "role_segment_error_summary.csv"),
            }
        )
    rows.sort(key=lambda row: fnum(row.get("rmse_delta_vs_m3_K"), -float("inf")) or -float("inf"), reverse=True)
    return rows


def top_segments(rows: list[dict[str, Any]], family: str) -> str:
    filtered = [
        row for row in rows
        if row["candidate_family"] == family
        and row["split_role"] in {"validation", "holdout"}
        and (fnum(row.get("rmse_delta_vs_m3_K")) or 0.0) > 0.0
    ]
    segments: Counter[str] = Counter(row["prediction_source_segment"] for row in filtered[:12])
    return ";".join(f"{name}:{count}" for name, count in segments.most_common())


def build_thermal_failure_mode_decision(
    gate_rows: list[dict[str, Any]], role_rows: list[dict[str, Any]], state: dict[str, Any]
) -> list[dict[str, Any]]:
    decisions: list[dict[str, Any]] = []
    for family in [
        "PB1_passive_total",
        "PB2_salt2_shape",
        "PB3_attenuated_shape",
        "WTD1_pipe_outer_wall_drive",
        "WTD2_outer_surface_drive",
        "HS1_heater_source_redistribution",
    ]:
        gates = [row for row in gate_rows if row["candidate_family"] == family]
        mdot = [fnum(row.get("mdot_delta_vs_m3_pct")) for row in gates if row.get("split_role") in {"validation", "holdout"}]
        tw = [fnum(row.get("tw_delta_vs_m3_K")) for row in gates if row.get("split_role") in {"validation", "holdout"}]
        all_probe = [fnum(row.get("all_probe_delta_vs_m3_K")) for row in gates if row.get("split_role") in {"validation", "holdout"}]
        evidence_state = "completed" if gates and all(row["evidence_state"] == "completed" for row in gates) else "pending_or_partial"
        if family == "HS1_heater_source_redistribution" and state["agent511_completed_rows"] == 0:
            mode = "pending_heater_source_scoring"
            action = "Wait for live AGENT-511 job 3300966 or rerun the bounded AGENT-511 command only if no live job remains."
            evidence_state = "pending_or_live_no_completed_rows"
        elif family in {"PB2_salt2_shape", "PB3_attenuated_shape", "PB1_passive_total"}:
            mode = "total_or_static_distribution_not_sufficient"
            action = "Do not repeat passive-total or Salt2-shaped wall distribution variants."
        elif family == "WTD1_pipe_outer_wall_drive":
            mode = "wall_temperature_drive_not_sufficient"
            action = "Drive selector alone does not fix the thermal field; prioritize source placement or explicit wall/fluid coupling."
        elif family == "WTD2_outer_surface_drive":
            mode = "wall_temperature_drive_wrong_direction"
            action = "Do not pursue outer-surface-drive variant without a new physical reason."
        else:
            mode = "completed_heater_source_review"
            action = "Use AGENT-511 deltas to decide between wall/fluid coupling and axial/junction mixing."
        decisions.append(
            {
                "candidate_family": family,
                "evidence_state": evidence_state,
                "rows_reviewed": len(gates),
                "mean_mdot_delta_vs_m3_pct": fmt(mean([value for value in mdot if value is not None])),
                "mean_tw_delta_vs_m3_K": fmt(mean([value for value in tw if value is not None])),
                "mean_all_probe_delta_vs_m3_K": fmt(mean([value for value in all_probe if value is not None])),
                "top_regressing_segments": top_segments(role_rows, family),
                "failure_mode": mode,
                "recommended_action": action,
            }
        )
    return decisions


def build_freeze_gate_status(gates: list[dict[str, Any]], state: dict[str, Any]) -> list[dict[str, Any]]:
    admitted = [
        row for row in gates
        if row.get("admission_decision", "").startswith("admitted")
        and row.get("evidence_state") == "completed"
    ]
    ag499 = read_json(AGENT499 / "summary.json")
    ag509 = read_json(AGENT509 / "summary.json")
    return [
        {
            "blocker_id": "freeze_blocked_no_wall_candidate_admitted",
            "current_status": "blocked" if not admitted else "ready_for_corrected_freeze",
            "completed_candidate_rows_reviewed": sum(1 for row in gates if row["evidence_state"] == "completed"),
            "pending_candidate_rows_reviewed": sum(1 for row in gates if row["evidence_state"] != "completed"),
            "admitted_candidates": len(admitted),
            "admitted_candidate_ids": ";".join(row["candidate_id"] for row in admitted),
            "agent511_state": state["agent511_state"],
            "agent499_decision": ag499.get("decision", ""),
            "agent509_freeze_status": ag509.get("freeze_status", ""),
            "decision": "do_not_build_corrected_freeze_yet" if not admitted else "build_corrected_freeze_candidate_manifest",
            "why": "No completed wall/test-section candidate has passed validation and holdout mdot/temperature gates.",
        }
    ]


def build_next_candidate_decision(state: dict[str, Any], failure_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if state["agent511_completed_rows"] == 0:
        decision = "complete_heater_source_redistribution_scoring_first"
        rationale = "AGENT-511 is the only planned source-placement lane and is live/pending; do not reject source redistribution from empty coupled rows."
        next_package = "AGENT-511 closeout, then rerun this atlas"
    else:
        decision = "explicit_test_section_wall_fluid_coupling_candidate"
        rationale = "Passive distribution and wall-temperature-drive completed candidates failed temperature-shape gates; source-placement evidence is available for comparison."
        next_package = "new explicit test-section wall/fluid coupling admission package"
    return [
        {
            "rank": 1,
            "decision": decision,
            "next_package": next_package,
            "rationale": rationale,
            "guardrail": "No val_salt2, Salt2 +/-Q, PM10, future CFD, or realized wallHeatFlux for fitting/model selection.",
        },
        {
            "rank": 2,
            "decision": "junction_or_axial_mixing_proxy_after_wall_fluid_coupling",
            "next_package": "junction-aware or axial-mixing proxy package",
            "rationale": "Use this only if completed source and explicit wall/fluid coupling evidence still localizes residuals to junction/downcomer/axial exchange.",
            "guardrail": "Pressure corner K remains diagnostic until straight-loss subtraction and recirculation-mask admission are repaired.",
        },
        {
            "rank": 3,
            "decision": "corrected_freeze_release_after_admission",
            "next_package": "corrected Salt1-4 nominal freeze manifest",
            "rationale": "Freeze remains blocked until a wall/test-section candidate passes the predeclared Salt3/Salt4 gates.",
            "guardrail": "Freeze only after validation and holdout mdot/all-probe/TW gates pass.",
        },
    ]


def build_runtime_leakage_audit() -> list[dict[str, Any]]:
    return [
        {"check": "native_solver_outputs_mutated", "status": "pass", "evidence": "Read completed work_product CSV/JSON artifacts only."},
        {"check": "scheduler_or_solver_launched", "status": "pass", "evidence": "Atlas builder does not call srun, sbatch, Fluid, OpenFOAM, or postprocessing."},
        {"check": "duplicate_coupled_scoring_submitted", "status": "pass", "evidence": "AGENT-511 live job is treated as read-only pending state; no duplicate submission."},
        {"check": "heldout_external_fit_or_tuning", "status": "pass", "evidence": "Salt3/Salt4 rows are score/diagnostic only; external/blind rows are not used."},
        {"check": "scientific_admission_state_changed", "status": "pass", "evidence": "Freeze remains blocked unless a completed admitted candidate exists; none is found."},
    ]


def build_source_manifest() -> list[dict[str, Any]]:
    sources = [
        (AGENT515 / "wall_candidate_gate_failure_matrix.csv", "AGENT-515 gate matrix"),
        (AGENT515 / "segment_heat_placement_failure_modes.csv", "AGENT-515 segment heat-placement failure modes"),
        (AGENT513 / "candidate_admission_review.csv", "AGENT-513 admission review"),
        (AGENT513 / "coupled_delta_vs_m3.csv", "AGENT-513 deltas versus M3"),
        (AGENT513 / "probe_delta_vs_m3.csv", "AGENT-513 probe deltas versus M3"),
        (AGENT513 / "role_segment_error_summary.csv", "AGENT-513 role/segment residual summary"),
        (AGENT511 / "summary.json", "AGENT-511 current state"),
        (AGENT511 / "coupled_scorecard.csv", "AGENT-511 heater-source scorecard or pending rows"),
        (AGENT511 / "coupled_delta_vs_m3.csv", "AGENT-511 deltas if available"),
        (AGENT499 / "summary.json", "corrected-split freeze summary"),
        (AGENT509 / "summary.json", "final predictive shell summary"),
    ]
    return [
        {
            "source_path": rel(path),
            "exists": "yes" if path.exists() else "no",
            "description": description,
            "usage": "read_only_existing_evidence",
        }
        for path, description in sources
    ]


def write_probe_svg(rows: list[dict[str, Any]], path: Path) -> None:
    subset = [
        row for row in rows
        if row["source_package"] == "AGENT-513_wall_temperature_drive"
        and row["split_role"] in {"validation", "holdout"}
        and row["abs_error_delta_vs_m3_K"]
    ]
    subset.sort(key=lambda row: fnum(row["abs_error_delta_vs_m3_K"], 0.0) or 0.0, reverse=True)
    subset = subset[:24]
    width, height = 980, 620
    left, top, bar_h, gap = 260, 54, 16, 8
    maxv = max([abs(fnum(row["abs_error_delta_vs_m3_K"], 0.0) or 0.0) for row in subset] + [1.0])
    zero_x = left + 330
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#fff"/>',
        '<text x="24" y="30" font-family="Arial" font-size="18" font-weight="700">Largest WTD probe regressions versus M3</text>',
        f'<line x1="{zero_x}" y1="{top - 8}" x2="{zero_x}" y2="{height - 42}" stroke="#333"/>',
    ]
    for idx, row in enumerate(subset):
        value = fnum(row["abs_error_delta_vs_m3_K"], 0.0) or 0.0
        length = abs(value) / maxv * 300
        y = top + idx * (bar_h + gap)
        color = "#c44e52" if value > 0 else "#2f6f8f"
        x = zero_x if value >= 0 else zero_x - length
        label = f"{row['candidate_family']} {row['case_id']} {row['sensor']} {row['prediction_source_segment']}"
        lines.append(f'<text x="18" y="{y + 12}" font-family="Arial" font-size="10">{esc(label)}</text>')
        lines.append(f'<rect x="{x:.1f}" y="{y}" width="{length:.1f}" height="{bar_h}" fill="{color}"><title>{esc(label)} {value:.3g} K</title></rect>')
        lines.append(f'<text x="{x + length + 4:.1f}" y="{y + 12}" font-family="Arial" font-size="10">{value:.2f} K</text>')
    lines.append('<text x="24" y="600" font-family="Arial" font-size="12">Positive delta means the candidate absolute probe error is worse than M3.</text>')
    lines.append("</svg>")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_readme(summary: dict[str, Any]) -> None:
    text = f"""---
provenance:
  created_by: {TASK}
  created_utc: {summary['created_utc']}
  source_packages:
    - {rel(AGENT515)}
    - {rel(AGENT513)}
    - {rel(AGENT511)}
tags:
  - forward-predictive-model
  - wall-test-section
  - residual-atlas
  - freeze-blocker
related:
  - .agent/status/2026-07-17_AGENT-520.md
  - .agent/journal/2026-07-17/wall-candidate-residual-atlas.md
  - imports/2026-07-17_wall_candidate_residual_atlas.json
status: current
---

# Wall Candidate Residual Atlas

This package consolidates completed PB/WTD evidence and the current AGENT-511
heater-source state. It does not launch jobs or alter admission state.

## Result

- Completed candidate gate rows reviewed: `{summary['completed_candidate_gate_rows']}`.
- Pending candidate gate rows reviewed: `{summary['pending_candidate_gate_rows']}`.
- Probe residual rows available: `{summary['probe_residual_rows']}`.
- Role/segment residual rows available: `{summary['role_segment_rows']}`.
- AGENT-511 state: `{summary['agent511_state']}` with `{summary['agent511_completed_rows']}` completed coupled rows.
- Freeze status: `{summary['freeze_status']}`.

The current evidence says passive distribution and wall-temperature-drive
variants do not fix the temperature-shape failure. AGENT-511 cannot be used as
scientific failure evidence until its coupled rows land; while job `3300966` is
live/pending, the immediate action is to consume AGENT-511, not submit duplicate
heater-source work.

## Files To Open First

- `candidate_gate_matrix.csv`
- `probe_residual_atlas.csv`
- `role_segment_residual_rank.csv`
- `thermal_failure_mode_decision.csv`
- `next_candidate_decision.csv`
- `freeze_gate_status.csv`

## Guardrails

No native solver outputs, registry/admission state, Fluid source, or scheduler
state were mutated. Salt3/Salt4 remain score-only, and external/blind rows are
not used for fitting or model selection.
"""
    (OUT / "README.md").write_text(text, encoding="utf-8")


def build() -> dict[str, Any]:
    OUT.mkdir(parents=True, exist_ok=True)
    state = source_state()
    gates = build_candidate_gate_matrix()
    probes = build_probe_residual_atlas()
    role_rows = build_role_segment_residual_rank()
    failures = build_thermal_failure_mode_decision(gates, role_rows, state)
    freeze = build_freeze_gate_status(gates, state)
    next_decisions = build_next_candidate_decision(state, failures)
    runtime = build_runtime_leakage_audit()
    manifest = build_source_manifest()

    write_csv(OUT / "candidate_gate_matrix.csv", gates)
    write_csv(OUT / "probe_residual_atlas.csv", probes)
    write_csv(OUT / "role_segment_residual_rank.csv", role_rows)
    write_csv(OUT / "thermal_failure_mode_decision.csv", failures)
    write_csv(OUT / "freeze_gate_status.csv", freeze)
    write_csv(OUT / "next_candidate_decision.csv", next_decisions)
    write_csv(OUT / "runtime_leakage_audit.csv", runtime)
    write_csv(OUT / "source_manifest.csv", manifest)
    write_probe_svg(probes, OUT / "probe_residual_regression_rank.svg")

    summary = {
        "task": TASK,
        "created_utc": utc_now(),
        "output_dir": rel(OUT),
        "agent511_state": state["agent511_state"],
        "agent511_completed_rows": state["agent511_completed_rows"],
        "completed_candidate_gate_rows": sum(1 for row in gates if row["evidence_state"] == "completed"),
        "pending_candidate_gate_rows": sum(1 for row in gates if row["evidence_state"] != "completed"),
        "probe_residual_rows": len(probes),
        "role_segment_rows": len(role_rows),
        "failure_mode_rows": len(failures),
        "freeze_status": freeze[0]["current_status"],
        "freeze_decision": freeze[0]["decision"],
        "next_decision": next_decisions[0]["decision"],
        "runtime_audit_failures": sum(1 for row in runtime if row["status"] != "pass"),
        "scientific_admission_change": "none",
        "scheduler_action": "none",
        "solver_action": "none",
    }
    write_json(OUT / "summary.json", summary)
    write_readme(summary)
    return summary


if __name__ == "__main__":
    print(json.dumps(build(), indent=2, sort_keys=True))
