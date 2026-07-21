#!/usr/bin/env python3
"""Build the upcomer-onset blocker-resolution package.

This package is intentionally conservative: it consolidates current evidence,
documents the math and assumptions, and states what evidence would be needed to
resolve the upcomer onset blocker. It does not claim a calibrated regime switch.
"""
from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "work_products/2026-07/2026-07-14/2026-07-14_upcomer_onset_blocker_resolution"

DATA = ROOT / "work_products/2026-07/2026-07-07/2026-07-07_upcomer_correlation_v2/upcomer_dataset.csv"
FIT = ROOT / "work_products/2026-07/2026-07-07/2026-07-07_upcomer_correlation_v2/upcomer_correlation_fit.csv"
PRIOR_ONSET = ROOT / "work_products/2026-07/2026-07-08/2026-07-08_upcomer_onset/upcomer_onset_regime_table.csv"
SHEAR_EVIDENCE = ROOT / "reports/2026-06/2026-06-29/2026-06-29_ethan_upcomer_recirculation_evidence/upcomer_recirculation_case_summary.csv"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: Iterable[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def fnum(value: Any) -> float:
    return float(value)


def classify(backflow_fraction: float, ri_median: float) -> tuple[str, str, str]:
    if backflow_fraction >= 0.10 or ri_median >= 1.0:
        return (
            "recirculation_cell_observed",
            "not_fit_single_stream_pipe_closure",
            "material reverse-flow/Ri evidence invalidates ordinary pipe-friction label",
        )
    if backflow_fraction > 0.02 or ri_median >= 0.30:
        return (
            "transition_candidate",
            "validation_only_pending_dense_design",
            "near-onset point needs neighboring cases before threshold fit",
        )
    return (
        "ordinary_pipe_candidate",
        "candidate_after_mesh_and_repeatability_gate",
        "non-recirculating point could anchor ordinary-pipe side of threshold",
    )


@dataclass(frozen=True)
class OnsetStats:
    n_points: int
    re_min: float
    re_max: float
    recirculating_points: int
    non_recirculating_points: int
    route_a_mid: float
    route_b_mid: float
    route_a_above_calibration_by: float
    route_b_mid_above_calibration_by: float
    min_backflow_fraction: float
    min_ri_median: float


def build_evidence_rows() -> tuple[list[dict[str, Any]], OnsetStats]:
    dataset = read_csv(DATA)
    fit = read_csv(FIT)[0]
    route_a_mid = fnum(fit["onset_Re_route_A_mid"])
    route_b_mid = fnum(fit["onset_Re_route_B_mid"])
    rows: list[dict[str, Any]] = []
    for raw in dataset:
        backflow = fnum(raw["backflow_fraction"])
        ri = fnum(raw["Ri_median"])
        regime, admission, reason = classify(backflow, ri)
        gr_proxy = fnum(raw["Ra_median"]) / fnum(raw["Pr_median"])
        re_up = fnum(raw["Re_upcomer"])
        rows.append(
            {
                "label": raw["label"],
                "source_id": raw["source_id"],
                "Re_upcomer": re_up,
                "Re_section_median": raw["Re_section_median"],
                "Pr_median": raw["Pr_median"],
                "Ra_median": raw["Ra_median"],
                "Gr_proxy_from_Ra_Pr": gr_proxy,
                "Ri_median": ri,
                "backflow_fraction": backflow,
                "recirculation_intensity": raw["recirculation_intensity"],
                "Nu_upcomer": raw["Nu_upcomer"],
                "T_bulk_K": raw["T_bulk_K"],
                "u_bulk_m_s": raw["u_bulk_m_s"],
                "regime_class": regime,
                "admission_for_closure": admission,
                "decision_reason": reason,
                "onset_route_a_mid_Re": route_a_mid,
                "onset_route_b_mid_Re": route_b_mid,
                "calibration_status": "inside_calibration_range_for_observation_only",
                "mesh_status": "coarse_no_publication_gci",
                "allowed_use": "regime_diagnostic_and_blocker_evidence",
                "excluded_use": "calibrated_regime_switch_or_single_stream_f_D_K_Nu_fit",
            }
        )
    re_vals = [fnum(row["Re_upcomer"]) for row in rows]
    backflow_vals = [fnum(row["backflow_fraction"]) for row in rows]
    ri_vals = [fnum(row["Ri_median"]) for row in rows]
    recirc = sum(1 for row in rows if row["regime_class"] == "recirculation_cell_observed")
    stats = OnsetStats(
        n_points=len(rows),
        re_min=min(re_vals),
        re_max=max(re_vals),
        recirculating_points=recirc,
        non_recirculating_points=len(rows) - recirc,
        route_a_mid=route_a_mid,
        route_b_mid=route_b_mid,
        route_a_above_calibration_by=max(0.0, route_a_mid - max(re_vals)),
        route_b_mid_above_calibration_by=max(0.0, route_b_mid - max(re_vals)),
        min_backflow_fraction=min(backflow_vals),
        min_ri_median=min(ri_vals),
    )
    return rows, stats


def build_math_rows() -> list[dict[str, str]]:
    return [
        {
            "quantity": "Re",
            "equation": "Re = rho * U_bulk * D_h / mu",
            "source_or_basis": "existing upcomer correlation dataset",
            "assumption": "Use the dataset's Re_upcomer for regime position; do not recompute properties in this packet.",
            "implication": "Current admitted rows span Re 71.1-134.9 only.",
        },
        {
            "quantity": "Pr",
            "equation": "Pr = cp * mu / k",
            "source_or_basis": "existing upcomer correlation dataset",
            "assumption": "Property-mode effects are upstream inputs; this packet does not mix property lanes.",
            "implication": "Pr decreases across Salt2-4 but does not create a non-recirculating point.",
        },
        {
            "quantity": "Gr_proxy",
            "equation": "Gr_proxy = Ra_median / Pr_median",
            "source_or_basis": "prior onset package convention",
            "assumption": "Proxy is used for documentation only, not threshold fitting.",
            "implication": "Useful for thesis explanation of buoyancy scale, not a closure coefficient.",
        },
        {
            "quantity": "Ri_median",
            "equation": "Ri_median = median local buoyancy/inertia indicator from source reduction",
            "source_or_basis": "existing upcomer correlation dataset",
            "assumption": "Use the source median rather than mean to avoid near-zero velocity domination.",
            "implication": "All current points have Ri_median >= 1, so ordinary single-stream pipe friction remains invalid.",
        },
        {
            "quantity": "backflow_fraction",
            "equation": "backflow_fraction = reverse-flow count / sampled upcomer count",
            "source_or_basis": "AGENT-196 reduced upcomer evidence",
            "assumption": "Backflow fraction is a regime diagnostic, not a volumetric recirculation fraction.",
            "implication": "All current points exceed 0.10, so no ordinary-pipe anchor exists.",
        },
        {
            "quantity": "onset_fit",
            "equation": "bf = a + b / Re",
            "source_or_basis": "upcomer_correlation_fit.csv",
            "assumption": "Positive fitted asymptote means zero-backflow crossing is not a valid direct threshold.",
            "implication": "Route A/B onset estimates remain extrapolated brackets, not calibrated closure rules.",
        },
    ]


def build_next_evidence_rows(stats: OnsetStats) -> list[dict[str, Any]]:
    return [
        {
            "priority": 1,
            "needed_evidence": "terminal corrected Salt-Q points near onset",
            "minimum_acceptance": "At least one admitted point below/near route_B_mid and one admitted point above route_A_mid, with no refit to validation/holdout rows.",
            "target_values": "Re targets 150, 200, 250, plus any terminal corrected-Q rows that naturally land in this range",
            "why_needed": "Current Re_max is %.3f; route_B_mid is %.1f and route_A_mid is %.1f." % (stats.re_max, stats.route_b_mid, stats.route_a_mid),
            "status": "blocked_pending_terminal_admission_or_new_design",
        },
        {
            "priority": 2,
            "needed_evidence": "non-recirculating or transition anchor",
            "minimum_acceptance": "A point with backflow_fraction <= 0.02 and Ri_median < 0.30, or a bounded transition pair straddling backflow_fraction 0.02-0.10.",
            "target_values": "ordinary-pipe anchor plus adjacent transition point",
            "why_needed": "All %d current points are recirculation_cell_observed." % stats.n_points,
            "status": "missing",
        },
        {
            "priority": 3,
            "needed_evidence": "mesh/time uncertainty for onset metrics",
            "minimum_acceptance": "Coarse/medium/fine or documented time-window uncertainty for backflow_fraction, Ri_median, and Nu_upcomer.",
            "target_values": "no publication threshold until uncertainty is bounded",
            "why_needed": "Current onset evidence is coarse/no-GCI.",
            "status": "missing",
        },
        {
            "priority": 4,
            "needed_evidence": "wall-core or wall-bulk Delta T extraction",
            "minimum_acceptance": "Wall/bulk temperature difference on the same retained window and section definition as backflow/Ri.",
            "target_values": "connect onset to mixed-convection thermal drive rather than Re alone",
            "why_needed": "Prior onset table leaves wall_bulk_delta_T_K blank.",
            "status": "missing",
        },
    ]


def build_blocker_rows(stats: OnsetStats) -> list[dict[str, Any]]:
    if stats.non_recirculating_points == 0:
        decision = "blocker_remains_open"
        why = "No non-recirculating admitted point exists; all current points are already in-cell."
    else:
        decision = "candidate_for_narrowing"
        why = "At least one non-recirculating anchor exists, but dense transition and uncertainty gates still apply."
    return [
        {
            "blocker_id": "upcomer-onset-data-sparsity",
            "current_decision": decision,
            "severity": "medium",
            "n_points": stats.n_points,
            "recirculating_points": stats.recirculating_points,
            "non_recirculating_points": stats.non_recirculating_points,
            "current_Re_span": "%.6g-%.6g" % (stats.re_min, stats.re_max),
            "route_A_mid_Re": stats.route_a_mid,
            "route_B_mid_Re": stats.route_b_mid,
            "route_A_above_current_Re_max": stats.route_a_above_calibration_by,
            "route_B_mid_above_current_Re_max": stats.route_b_mid_above_calibration_by,
            "minimum_backflow_fraction": stats.min_backflow_fraction,
            "minimum_Ri_median": stats.min_ri_median,
            "why": why,
            "allowed_claim_now": "Observed Salt2/3/4 upcomer rows are recirculation-cell regime diagnostics.",
            "excluded_claim_now": "A calibrated onset threshold or predictive regime switch.",
        }
    ]


def write_readme(stats: OnsetStats) -> None:
    text = f"""---
provenance:
  - {rel(DATA)}
  - {rel(FIT)}
  - {rel(PRIOR_ONSET)}
  - {rel(SHEAR_EVIDENCE)}
tags: [upcomer-onset, recirculation, blocker-resolution, thermal-closure]
related:
  - .agent/BLOCKERS.md
  - .agent/journal/2026-07-08/upcomer-onset.md
task: AGENT-324
date: 2026-07-14
role: Implementer/Tester/Writer
type: work_product
status: complete
---
# Upcomer Onset Blocker Resolution

## Purpose

This package implements the upcomer-onset work packet from the project plan. It
consolidates the current onset evidence, documents the math and assumptions,
and states exactly what is still needed before a regime switch can be claimed.

## Result

The blocker remains open. Current admitted evidence has `{stats.n_points}` points
from Re `{stats.re_min:.1f}` to `{stats.re_max:.1f}`. All `{stats.recirculating_points}`
points classify as `recirculation_cell_observed`; there are `{stats.non_recirculating_points}`
ordinary-pipe anchor points. Route A midpoint Re is `{stats.route_a_mid:.1f}`
and Route B midpoint Re is `{stats.route_b_mid:.1f}`, both above the current
maximum admitted Re if judged by midpoint.

## Files

- `upcomer_onset_evidence_status.csv`: current row-level evidence and allowed
  use.
- `math_and_theory.csv`: equations, assumptions, and implications.
- `next_evidence_requirements.csv`: minimum evidence needed to resolve the
  blocker.
- `blocker_status.csv`: one-row admission/blocker decision.
- `results_interpretation.md`: thesis-ready interpretation.
- `source_manifest.csv`: exact input provenance.

## Interpretation Boundary

Use this as blocker-resolution evidence and thesis wording. Do not use it as a
calibrated onset threshold, a single-stream upcomer friction closure, or an
internal-Nu admission.
"""
    (OUT / "README.md").write_text(text, encoding="utf-8")


def write_results_interpretation(stats: OnsetStats) -> None:
    text = f"""# Results Interpretation

## Observed Facts

- Current admitted onset dataset has `{stats.n_points}` rows.
- Re range is `{stats.re_min:.3f}` to `{stats.re_max:.3f}`.
- All rows classify as `recirculation_cell_observed`.
- Minimum current backflow fraction is `{stats.min_backflow_fraction:.6f}`.
- Minimum current `Ri_median` is `{stats.min_ri_median:.6f}`.
- Route A midpoint Re `{stats.route_a_mid:.1f}` is `{stats.route_a_above_calibration_by:.3f}` above current Re max.
- Route B midpoint Re `{stats.route_b_mid:.1f}` is `{stats.route_b_mid_above_calibration_by:.3f}` above current Re max.

## Inferred Interpretation

The current evidence supports a strong diagnostic claim: the admitted Salt2/3/4
upcomer rows are mixed-convection recirculation-cell rows and should not be
named as ordinary single-stream `f_D`, `K`, or `Nu` closures. The evidence does
not support a calibrated onset threshold because there is no non-recirculating
anchor, no dense transition bracket, and no mesh/time uncertainty bound for the
onset metrics.

## Thesis-Safe Claim

For the admitted Salt2/3/4 points, the upcomer is observed in a recirculating
mixed-convection regime. The onset location is bracketed only by extrapolation
from the current three-point trend and should be treated as an experimental or
CFD-design target, not a closure.

## Excluded Claims

- A calibrated recirculation onset Reynolds number.
- A production regime switch for the 1D model.
- A universal upcomer `f_D`, `K`, or `Nu` value across the recirculating region.
- Any claim that corrected Salt-Q resolves onset before terminal admission.
"""
    (OUT / "results_interpretation.md").write_text(text, encoding="utf-8")


def write_source_manifest() -> None:
    rows = [
        {
            "source_path": rel(DATA),
            "role": "primary current onset dataset",
            "use": "row-level Re/Pr/Ri/Ra/backflow/Nu evidence",
        },
        {
            "source_path": rel(FIT),
            "role": "prior onset fit and route brackets",
            "use": "route A/B midpoint and extrapolation warning",
        },
        {
            "source_path": rel(PRIOR_ONSET),
            "role": "prior regime table",
            "use": "continuity with TODO-UPCOMER-ONSET",
        },
        {
            "source_path": rel(SHEAR_EVIDENCE),
            "role": "wall-shear recirculation evidence",
            "use": "qualitative upcomer/right-leg contrast provenance",
        },
    ]
    write_csv(OUT / "source_manifest.csv", rows, ["source_path", "role", "use"])


def build() -> dict[str, Any]:
    OUT.mkdir(parents=True, exist_ok=True)
    evidence_rows, stats = build_evidence_rows()
    write_csv(
        OUT / "upcomer_onset_evidence_status.csv",
        evidence_rows,
        [
            "label",
            "source_id",
            "Re_upcomer",
            "Re_section_median",
            "Pr_median",
            "Ra_median",
            "Gr_proxy_from_Ra_Pr",
            "Ri_median",
            "backflow_fraction",
            "recirculation_intensity",
            "Nu_upcomer",
            "T_bulk_K",
            "u_bulk_m_s",
            "regime_class",
            "admission_for_closure",
            "decision_reason",
            "onset_route_a_mid_Re",
            "onset_route_b_mid_Re",
            "calibration_status",
            "mesh_status",
            "allowed_use",
            "excluded_use",
        ],
    )
    write_csv(OUT / "math_and_theory.csv", build_math_rows(), ["quantity", "equation", "source_or_basis", "assumption", "implication"])
    write_csv(OUT / "next_evidence_requirements.csv", build_next_evidence_rows(stats), ["priority", "needed_evidence", "minimum_acceptance", "target_values", "why_needed", "status"])
    write_csv(
        OUT / "blocker_status.csv",
        build_blocker_rows(stats),
        [
            "blocker_id",
            "current_decision",
            "severity",
            "n_points",
            "recirculating_points",
            "non_recirculating_points",
            "current_Re_span",
            "route_A_mid_Re",
            "route_B_mid_Re",
            "route_A_above_current_Re_max",
            "route_B_mid_above_current_Re_max",
            "minimum_backflow_fraction",
            "minimum_Ri_median",
            "why",
            "allowed_claim_now",
            "excluded_claim_now",
        ],
    )
    write_source_manifest()
    write_readme(stats)
    write_results_interpretation(stats)
    summary = {
        "task": "AGENT-324",
        "status": "complete",
        "blocker_id": "upcomer-onset-data-sparsity",
        "blocker_decision": "remains_open",
        "n_points": stats.n_points,
        "recirculating_points": stats.recirculating_points,
        "non_recirculating_points": stats.non_recirculating_points,
        "re_min": stats.re_min,
        "re_max": stats.re_max,
        "route_A_mid_Re": stats.route_a_mid,
        "route_B_mid_Re": stats.route_b_mid,
        "outputs": [
            "upcomer_onset_evidence_status.csv",
            "math_and_theory.csv",
            "next_evidence_requirements.csv",
            "blocker_status.csv",
            "results_interpretation.md",
            "source_manifest.csv",
            "README.md",
            "summary.json",
        ],
        "generated_at": datetime.now().isoformat(timespec="seconds"),
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary


def main() -> int:
    print(json.dumps(build(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
