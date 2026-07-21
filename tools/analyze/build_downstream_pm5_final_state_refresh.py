#!/usr/bin/env python3
"""Refresh downstream interpretation after AGENT-406 final PM5 wallHeatFlux state.

This package is a non-mutating supersession layer. It does not rewrite completed
AGENT-407/409 artifacts because AGENT-413 is active on the broader blocker wave.
"""

from __future__ import annotations

import csv
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


TASK = "AGENT-414"
DATE = "2026-07-15"
ROOT = Path(__file__).resolve().parents[2]
OUT_REL = Path("work_products/2026-07/2026-07-15/2026-07-15_downstream_pm5_final_state_refresh")
AGENT406 = ROOT / "work_products/2026-07/2026-07-15/2026-07-15_pm5_wall_band_vtk_and_f6_unlock_repair"
AGENT407 = ROOT / "work_products/2026-07/2026-07-15/2026-07-15_forward_v1_row_admission_ledger"
AGENT409 = ROOT / "work_products/2026-07/2026-07-15/2026-07-15_lead_closure_qoi_hydraulic_postprocess"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT.resolve()))
    except ValueError:
        return str(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_csv(path: Path, rows: Iterable[dict[str, Any]], fieldnames: list[str]) -> int:
    materialized = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in materialized:
            writer.writerow({field: row.get(field, "") for field in fieldnames})
    return len(materialized)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def safe_float(value: Any) -> float | None:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    return out if math.isfinite(out) else None


def fmt(value: Any, precision: int = 10) -> str:
    number = safe_float(value)
    if number is None:
        return "" if value is None else str(value)
    return f"{number:.{precision}g}"


def final_pm5_summary() -> dict[str, Any]:
    return read_json(AGENT406 / "summary.json")


def downstream_refresh_rows(summary: dict[str, Any]) -> list[dict[str, Any]]:
    corrected_pm5 = (
        f"{summary['parsed_metric_rows']}/12 PM5 rows parsed; "
        f"{summary['wallHeatFlux_rows']}/12 wallHeatFlux rows; "
        f"F6 unlocked={summary['f6_unlocked_for_review_not_admitted']}; "
        f"internal-Nu unlocked={summary['internal_nu_unlocked_for_review_not_admitted']}; "
        "diagnostic/not admitted"
    )
    return [
        {
            "downstream_artifact": rel(AGENT409 / "README.md"),
            "stale_or_superseded_claim": "README still says Salt2 high-Q wallHeatFlux is missing and PM5/F6 remains partial.",
            "corrected_state": corrected_pm5,
            "refresh_status": "superseded_by_agent406_final_and_agent414_refresh",
            "recommended_action": "Update AGENT-409 README prose or cite this refresh package; machine CSV/summary already reflect 12/12.",
            "may_mutate_under_agent414": "no",
        },
        {
            "downstream_artifact": ".agent/BOARD.md AGENT-409 row",
            "stale_or_superseded_claim": "Board row says PM5 landed with 9 rows and partial wallHeatFlux.",
            "corrected_state": corrected_pm5,
            "refresh_status": "superseded_by_agent406_final_and_agent414_refresh",
            "recommended_action": "Coordinator may update stale board prose after AGENT-413 completes; do not change active AGENT-413 scope here.",
            "may_mutate_under_agent414": "no",
        },
        {
            "downstream_artifact": rel(AGENT407 / "README.md"),
            "stale_or_superseded_claim": "README says internal Nu is blocked partly because AGENT-404 has wallHeatFlux_rows=0.",
            "corrected_state": "wallHeatFlux extraction blocker is cleared at diagnostic artifact level: 12/12 PM5 rows have wallHeatFlux. Internal-Nu remains 0 fit-admitted due recirculation/admission/sign/heat-balance gates.",
            "refresh_status": "dependency_narrowed_not_resolved",
            "recommended_action": "Refresh internal_nu_fit_rows dependency wording: wallHeatFlux no longer blocks extraction; admission still blocks fitting.",
            "may_mutate_under_agent414": "no",
        },
        {
            "downstream_artifact": rel(AGENT407 / "internal_nu_fit_rows.csv"),
            "stale_or_superseded_claim": "wallHeatFlux_rows=0 and pm5_internal_nu_wallHeatFlux_blocked=true.",
            "corrected_state": "wallHeatFlux_rows=12 and pm5_internal_nu_wallHeatFlux_blocked=false for extraction; admitted_row_count remains 0.",
            "refresh_status": "dependency_narrowed_not_resolved",
            "recommended_action": "Downstream admission ledger should split 'field available' from 'fit admitted'.",
            "may_mutate_under_agent414": "no",
        },
        {
            "downstream_artifact": rel(AGENT409 / "hydraulic_gate_status_after_pm5.csv"),
            "stale_or_superseded_claim": "none found in machine table.",
            "corrected_state": "Already reflects AGENT-406 final 12/12 diagnostic state.",
            "refresh_status": "already_current",
            "recommended_action": "Use as current machine-readable hydraulic gate state.",
            "may_mutate_under_agent414": "no",
        },
        {
            "downstream_artifact": rel(AGENT409 / "summary.json"),
            "stale_or_superseded_claim": "none found in machine summary.",
            "corrected_state": "Already reflects pm5_rows=12, wallHeatFlux present, and internal_nu_fit_admissible_rows_today=0.",
            "refresh_status": "already_current",
            "recommended_action": "Use as current machine-readable AGENT-409 state.",
            "may_mutate_under_agent414": "no",
        },
    ]


def f6_row_status(row: dict[str, str]) -> tuple[str, str]:
    required = ("Re", "Pr", "Ri", "bulk_T_K", "wall_T_K")
    if any(not row.get(field) for field in required):
        return ("blocked_missing_required_field", "Missing PM5 scalar/vector fields.")
    reverse_mass = safe_float(row.get("reverse_mass_fraction")) or 0.0
    reverse_area = safe_float(row.get("reverse_area_fraction")) or 0.0
    secondary = safe_float(row.get("secondary_velocity_fraction")) or 0.0
    ri = safe_float(row.get("Ri")) or 0.0
    if reverse_mass >= 0.02 or reverse_area >= 0.02:
        return ("diagnostic_onset_only_recirculating_not_f6_fit", "Reverse flow exceeds single-stream F6 fit threshold.")
    if secondary >= 0.20:
        return ("diagnostic_secondary_flow_not_f6_fit", "Secondary-flow fraction exceeds fit threshold.")
    if ri >= 0.30:
        return ("diagnostic_mixed_convection_not_f6_fit", "Ri exceeds mixed-convection fit threshold.")
    return ("candidate_for_bounded_f6_fit_review", "Passes first-pass PM5 row quality thresholds.")


def f6_readiness_rows(metrics: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows = []
    for row in metrics:
        status, reason = f6_row_status(row)
        rows.append(
            {
                "case_key": row["case_key"],
                "case_role": row["case_role"],
                "plane_location": row["plane_location"],
                "span": row["span"],
                "Re": row["Re"],
                "Pr": row["Pr"],
                "Ri": row["Ri"],
                "reverse_area_fraction": row["reverse_area_fraction"],
                "reverse_mass_fraction": row["reverse_mass_fraction"],
                "secondary_velocity_fraction": row["secondary_velocity_fraction"],
                "f6_review_status": status,
                "reason": reason,
                "fit_admissible_now": "yes" if status == "candidate_for_bounded_f6_fit_review" else "no",
                "source_metric_file": rel(AGENT406 / "resampled_pm5_matched_plane_metrics.csv"),
            }
        )
    return rows


def internal_nu_row_status(row: dict[str, str]) -> tuple[str, str, float | None]:
    q = safe_float(row.get("wallHeatFlux_W_m2"))
    delta = safe_float(row.get("delta_T_wall_bulk_K"))
    if q is None:
        return ("blocked_missing_wallHeatFlux", "No wallHeatFlux in wall-band VTK.", None)
    if delta is None or abs(delta) < 0.5:
        return ("blocked_small_or_missing_wall_bulk_deltaT", "Wall-bulk delta-T is too small/missing for stable h proxy.", None)
    h_proxy = q / delta
    reverse_mass = safe_float(row.get("reverse_mass_fraction")) or 0.0
    reverse_area = safe_float(row.get("reverse_area_fraction")) or 0.0
    if h_proxy <= 0:
        return ("diagnostic_sign_review_required", "q''/(Twall-Tbulk) is non-positive under current sign convention.", h_proxy)
    if reverse_mass >= 0.02 or reverse_area >= 0.02:
        return ("diagnostic_section_effective_recirculating_not_fit", "wallHeatFlux exists, but reverse flow invalidates single-stream fitted Nu.", h_proxy)
    return ("candidate_for_internal_nu_admission_review", "Passes first-pass field/sign/recirculation thresholds.", h_proxy)


def internal_nu_readiness_rows(metrics: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows = []
    for row in metrics:
        status, reason, h_proxy = internal_nu_row_status(row)
        rows.append(
            {
                "case_key": row["case_key"],
                "case_role": row["case_role"],
                "plane_location": row["plane_location"],
                "span": row["span"],
                "bulk_T_K": row["bulk_T_K"],
                "wall_T_K": row["wall_T_K"],
                "delta_T_wall_bulk_K": row["delta_T_wall_bulk_K"],
                "wallHeatFlux_W_m2": row["wallHeatFlux_W_m2"],
                "h_proxy_W_m2_K": fmt(h_proxy),
                "reverse_area_fraction": row["reverse_area_fraction"],
                "reverse_mass_fraction": row["reverse_mass_fraction"],
                "internal_nu_review_status": status,
                "reason": reason,
                "fit_admissible_now": "yes" if status == "candidate_for_internal_nu_admission_review" else "no",
                "source_metric_file": rel(AGENT406 / "resampled_pm5_matched_plane_metrics.csv"),
            }
        )
    return rows


def review_protocol_rows(kind: str) -> list[dict[str, str]]:
    if kind == "f6":
        return [
            {"step_id": "F6-01", "stage": "input_lock", "action": "Use AGENT-406 final resampled_pm5_matched_plane_metrics.csv only.", "acceptance": "12/12 complete_with_wallHeatFlux and VTK validation fail rows = 0.", "stop_condition": "Any missing U/rho/T/Re/Pr/Ri/Gr/Ra row.", "output": "f6_pm5_row_readiness.csv"},
            {"step_id": "F6-02", "stage": "quality_gate", "action": "Classify recirculation, secondary-flow, and mixed-convection thresholds before fitting phi(Re).", "acceptance": "Fit rows must be non-recirculating, stable, and split-labeled; diagnostic rows may inform onset only.", "stop_condition": "All rows are recirculating or diagnostic-only.", "output": "fit candidate count and diagnostic-only count"},
            {"step_id": "F6-03", "stage": "bounded_fit_if_candidates_exist", "action": "Fit phi(Re)=1+a/Re^b only on allowed training rows; preserve holdout labels.", "acceptance": "Improves per-pressure-row residuals without worsening mdot guardrail; no global friction multiplier.", "stop_condition": "No fit-admissible pressure rows or validation worsens.", "output": "F6 bounded scorecard"},
            {"step_id": "F6-04", "stage": "admission_decision", "action": "Decide screen-only, diagnostic-onset-only, or admitted bounded closure.", "acceptance": "Train/holdout split honored; pressure residual primary; mdot secondary guardrail; no thermal fitting.", "stop_condition": "Pressure evidence remains recirculating/coarse-only/unadmitted.", "output": "hydraulic admission update"},
        ]
    return [
        {"step_id": "NU-01", "stage": "input_lock", "action": "Use AGENT-406 wall-band VTK/metrics with wallHeatFlux, wall T, bulk T, and PM5 recirculation fields.", "acceptance": "12/12 wallHeatFlux rows available.", "stop_condition": "Any missing wallHeatFlux/Tbulk/Twall row.", "output": "internal_nu_pm5_row_readiness.csv"},
        {"step_id": "NU-02", "stage": "sign_and_energy_gate", "action": "Compute h_proxy=q''/(Twall-Tbulk); review sign convention and heat-balance consistency before Nu.", "acceptance": "Positive interpretable h under documented sign convention and non-small delta-T.", "stop_condition": "Non-positive h, small delta-T, or heat-balance mismatch.", "output": "sign/heat-balance decision table"},
        {"step_id": "NU-03", "stage": "recirculation_gate", "action": "Separate section-effective diagnostic Nu from fitted single-stream Nu.", "acceptance": "Fit rows must be non-recirculating; recirculating rows stay diagnostic/section-effective only.", "stop_condition": "All PM5 rows recirculate.", "output": "diagnostic-vs-fit Nu classification"},
        {"step_id": "NU-04", "stage": "property_and_uncertainty_gate", "action": "Apply k(T), D_h, mesh/time uncertainty, and downcomer/upcomer policy before admitting any Nu.", "acceptance": "Admitted row has sign, heat balance, recirculation, mesh/time, and property policy passed.", "stop_condition": "Any gate fails.", "output": "internal-Nu admission update"},
    ]


def source_rows() -> list[dict[str, Any]]:
    paths = [
        AGENT406 / "summary.json",
        AGENT406 / "resampled_pm5_matched_plane_metrics.csv",
        AGENT406 / "pm5_f6_internal_nu_unlock_scorecard.csv",
        AGENT407 / "README.md",
        AGENT407 / "internal_nu_fit_rows.csv",
        AGENT409 / "README.md",
        AGENT409 / "hydraulic_gate_status_after_pm5.csv",
        AGENT409 / "summary.json",
    ]
    return [{"path": rel(path), "role": "input", "exists": path.exists()} for path in paths]


def write_readme(out_dir: Path, summary: dict[str, Any]) -> None:
    out_dir.joinpath("README.md").write_text(
        f"""# Downstream PM5 Final-State Refresh

Date: {DATE}
Task: {TASK}

## Result

AGENT-406 final state supersedes the earlier partial PM5 state: `12/12` rows
are complete with wallHeatFlux and `12/12` plane VTK rows validate for the F6
field set. This package does not admit the rows; it refreshes downstream
interpretation and defines the review sequence.

## Current Gate State

- F6: unlocked for bounded review, not admitted.
- Internal-Nu: wallHeatFlux field blocker cleared for review, not admitted.
- F6 fit candidates now: {summary['f6_fit_candidate_rows']}
- Internal-Nu fit candidates now: {summary['internal_nu_fit_candidate_rows']}

The PM5 rows are still mostly/usefully diagnostic because first-pass row quality
shows recirculation/sign/admission issues that must be reviewed before fitting.

## Outputs

- `downstream_pm5_refresh_matrix.csv`
- `f6_pm5_row_readiness.csv`
- `internal_nu_pm5_row_readiness.csv`
- `f6_review_protocol.csv`
- `internal_nu_review_protocol.csv`
- `source_manifest.csv`
- `summary.json`
""",
        encoding="utf-8",
    )


def build(root: Path = ROOT, out_dir: Path | None = None) -> dict[str, Any]:
    out_dir = out_dir or root / OUT_REL
    out_dir.mkdir(parents=True, exist_ok=True)
    pm5_summary = final_pm5_summary()
    metrics = read_csv(AGENT406 / "resampled_pm5_matched_plane_metrics.csv")
    refresh = downstream_refresh_rows(pm5_summary)
    f6_rows = f6_readiness_rows(metrics)
    nu_rows = internal_nu_readiness_rows(metrics)
    counts = {
        "refresh_rows": write_csv(out_dir / "downstream_pm5_refresh_matrix.csv", refresh, ["downstream_artifact", "stale_or_superseded_claim", "corrected_state", "refresh_status", "recommended_action", "may_mutate_under_agent414"]),
        "f6_rows": write_csv(out_dir / "f6_pm5_row_readiness.csv", f6_rows, ["case_key", "case_role", "plane_location", "span", "Re", "Pr", "Ri", "reverse_area_fraction", "reverse_mass_fraction", "secondary_velocity_fraction", "f6_review_status", "reason", "fit_admissible_now", "source_metric_file"]),
        "internal_nu_rows": write_csv(out_dir / "internal_nu_pm5_row_readiness.csv", nu_rows, ["case_key", "case_role", "plane_location", "span", "bulk_T_K", "wall_T_K", "delta_T_wall_bulk_K", "wallHeatFlux_W_m2", "h_proxy_W_m2_K", "reverse_area_fraction", "reverse_mass_fraction", "internal_nu_review_status", "reason", "fit_admissible_now", "source_metric_file"]),
        "f6_protocol_rows": write_csv(out_dir / "f6_review_protocol.csv", review_protocol_rows("f6"), ["step_id", "stage", "action", "acceptance", "stop_condition", "output"]),
        "internal_nu_protocol_rows": write_csv(out_dir / "internal_nu_review_protocol.csv", review_protocol_rows("internal_nu"), ["step_id", "stage", "action", "acceptance", "stop_condition", "output"]),
        "source_rows": write_csv(out_dir / "source_manifest.csv", source_rows(), ["path", "role", "exists"]),
    }
    summary = {
        "task": TASK,
        "date": DATE,
        "created_utc": utc_now(),
        "pm5_rows": len(metrics),
        "pm5_wallHeatFlux_rows": pm5_summary.get("wallHeatFlux_rows"),
        "pm5_f6_unlocked_for_review_not_admitted": pm5_summary.get("f6_unlocked_for_review_not_admitted"),
        "pm5_internal_nu_unlocked_for_review_not_admitted": pm5_summary.get("internal_nu_unlocked_for_review_not_admitted"),
        "f6_fit_candidate_rows": sum(1 for row in f6_rows if row["fit_admissible_now"] == "yes"),
        "internal_nu_fit_candidate_rows": sum(1 for row in nu_rows if row["fit_admissible_now"] == "yes"),
        "stale_downstream_rows": sum(1 for row in refresh if row["refresh_status"] != "already_current"),
        "native_solver_outputs_mutated": False,
        "registry_or_admission_mutated": False,
        "scheduler_jobs_launched": False,
        "external_fluid_modified": False,
        "active_agent413_mutated": False,
        "counts": counts,
    }
    write_json(out_dir / "summary.json", summary)
    write_readme(out_dir, summary)
    return summary


def main() -> int:
    print(json.dumps(build(), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
