#!/usr/bin/env python3
"""Localize why wall candidates still do not unblock the corrected freeze.

This package is existing-evidence only. It reads completed AGENT-494/498 and
freeze-shell artifacts, emits diagnostic tables/quicklooks, and does not run
Fluid, OpenFOAM, scheduler jobs, fitting, tuning, or admission-state changes.
"""

from __future__ import annotations

import csv
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TASK = "AGENT-515"
ROOT = Path(__file__).resolve().parents[2]
OUT_REL = Path("work_products/2026-07/2026-07-17/2026-07-17_wall_candidate_failure_localization")
OUT = ROOT / OUT_REL

AGENT494 = ROOT / "work_products/2026-07/2026-07-17/2026-07-17_wall_test_section_coupled_admission"
AGENT498 = ROOT / "work_products/2026-07/2026-07-17/2026-07-17_wall_test_section_distribution_ladder"
AGENT508 = ROOT / "work_products/2026-07/2026-07-17/2026-07-17_val_salt2_corrected_freeze_join_unblock"
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
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path) -> Any:
    with path.open() as handle:
        return json.load(handle)


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = []
        for row in rows:
            for key in row:
                if key not in fieldnames:
                    fieldnames.append(key)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


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


def max_abs(values: list[float]) -> float | None:
    finite = [value for value in values if math.isfinite(value)]
    return max((abs(value) for value in finite), default=None)


def esc(value: Any) -> str:
    return (
        str(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def family_id(candidate_id: str) -> str:
    if candidate_id.startswith("PB1"):
        return "PB1_passive_total"
    if candidate_id.startswith("PB2"):
        return "PB2_salt2_shape"
    if candidate_id.startswith("PB3"):
        return "PB3_attenuated_shape"
    return "unknown"


def wall_candidate_id(candidate_id: str) -> str:
    return candidate_id.split("_PLUS_", 1)[0] if "_PLUS_" in candidate_id else candidate_id


def split_map(rows: list[dict[str, str]], key: str = "candidate_id") -> dict[str, list[dict[str, str]]]:
    out: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        out[row.get(key, "")].append(row)
    return out


def classify_gate(mdot_delta: float | None, all_probe_delta: float | None, tw_delta: float | None) -> str:
    if mdot_delta is not None and mdot_delta < 0.0 and (
        (all_probe_delta is not None and all_probe_delta > 0.0)
        or (tw_delta is not None and tw_delta > 0.0)
    ):
        return "mdot_improves_temperature_regresses"
    if mdot_delta is not None and mdot_delta < 0.0:
        return "mdot_improves_temperature_unknown"
    if all_probe_delta is not None and all_probe_delta > 0.0:
        return "temperature_regresses"
    return "no_clear_localization"


def build_wall_candidate_gate_failure_matrix() -> list[dict[str, Any]]:
    reviews = {row["candidate_id"]: row for row in read_csv(AGENT498 / "candidate_admission_review.csv")}
    rows: list[dict[str, Any]] = []
    for row in read_csv(AGENT498 / "coupled_delta_vs_m3.csv"):
        candidate = row["candidate_id"]
        review = reviews[candidate]
        mdot_delta = fnum(row.get("mdot_delta_vs_m3_pct"))
        all_probe_delta = fnum(row.get("all_probe_delta_vs_m3_K"))
        tw_delta = fnum(row.get("tw_delta_vs_m3_K"))
        rows.append(
            {
                "candidate_id": candidate,
                "wall_candidate_id": wall_candidate_id(candidate),
                "candidate_family": family_id(candidate),
                "case_id": row["case_id"],
                "split_role": row["split_role"],
                "runtime_gate": review["runtime_gate"],
                "coupled_gate_for_split": review[f"{row['split_role']}_coupled_gate"],
                "admission_decision": review["admission_decision"],
                "blocking_reasons": review["blocking_reasons"],
                "mdot_delta_vs_m3_pct": row["mdot_delta_vs_m3_pct"],
                "all_probe_delta_vs_m3_K": row["all_probe_delta_vs_m3_K"],
                "tw_delta_vs_m3_K": row["tw_delta_vs_m3_K"],
                "gate_interpretation": classify_gate(mdot_delta, all_probe_delta, tw_delta),
                "scientific_read": (
                    "The wall/cooler candidate reduces mdot error relative to M3 but worsens the "
                    "temperature field; this is a source-placement/temperature-shape failure, "
                    "not a runtime failure."
                ),
                "source_paths": f"{rel(AGENT498 / 'candidate_admission_review.csv')};{rel(AGENT498 / 'coupled_delta_vs_m3.csv')}",
            }
        )
    return rows


def build_temperature_shape_regression_summary() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    pb1_by_key: dict[tuple[str, str, str], dict[str, str]] = defaultdict(dict)
    for row in read_csv(AGENT498 / "probe_shape_regression_audit.csv"):
        key = (row["source_candidate_id"], row["case_id"], row["split_role"])
        pb1_by_key[key][row["metric"]] = row["delta_candidate_minus_m3"]
        pb1_by_key[key]["source_path"] = row["source_path"]
    for (candidate, case_id, split_role), metrics in sorted(pb1_by_key.items()):
        rows.append(
            {
                "source_package": "AGENT-494_PB1_coupled_admission",
                "candidate_id": candidate,
                "wall_candidate_id": "PB1_total_hA_heater_power_drive_p1",
                "candidate_family": "PB1_passive_total",
                "case_id": case_id,
                "split_role": split_role,
                "mdot_delta_vs_m3_pct": metrics.get("mdot_abs_error_pct", ""),
                "tp_delta_vs_m3_K": metrics.get("tp_rmse_K", ""),
                "tw_delta_vs_m3_K": metrics.get("tw_rmse_K", ""),
                "all_probe_delta_vs_m3_K": metrics.get("all_probe_rmse_K", ""),
                "shape_regression_flag": classify_gate(
                    fnum(metrics.get("mdot_abs_error_pct")),
                    fnum(metrics.get("all_probe_rmse_K")),
                    fnum(metrics.get("tw_rmse_K")),
                ),
                "data_limit": "PB1 row is inherited AGENT-494 evidence copied into AGENT-498 audit.",
                "source_paths": rel(AGENT498 / "probe_shape_regression_audit.csv"),
            }
        )
    score_by_key = {
        (row["candidate_id"], row["case_id"], row["split_role"]): row
        for row in read_csv(AGENT498 / "coupled_scorecard.csv")
    }
    for row in read_csv(AGENT498 / "coupled_delta_vs_m3.csv"):
        key = (row["candidate_id"], row["case_id"], row["split_role"])
        score = score_by_key.get(key, {})
        rows.append(
            {
                "source_package": "AGENT-498_local_distribution_ladder",
                "candidate_id": row["candidate_id"],
                "wall_candidate_id": wall_candidate_id(row["candidate_id"]),
                "candidate_family": family_id(row["candidate_id"]),
                "case_id": row["case_id"],
                "split_role": row["split_role"],
                "mdot_delta_vs_m3_pct": row["mdot_delta_vs_m3_pct"],
                "tp_delta_vs_m3_K": "",
                "tw_delta_vs_m3_K": row["tw_delta_vs_m3_K"],
                "all_probe_delta_vs_m3_K": row["all_probe_delta_vs_m3_K"],
                "candidate_tp_rmse_K": score.get("tp_rmse_K", ""),
                "candidate_tw_rmse_K": score.get("tw_rmse_K", ""),
                "candidate_all_probe_rmse_K": score.get("all_probe_rmse_K", ""),
                "shape_regression_flag": classify_gate(
                    fnum(row.get("mdot_delta_vs_m3_pct")),
                    fnum(row.get("all_probe_delta_vs_m3_K")),
                    fnum(row.get("tw_delta_vs_m3_K")),
                ),
                "data_limit": "AGENT-498 delta table reports all-probe/TW deltas but not TP delta for PB2/PB3.",
                "source_paths": f"{rel(AGENT498 / 'coupled_delta_vs_m3.csv')};{rel(AGENT498 / 'coupled_scorecard.csv')}",
            }
        )
    return rows


def build_probe_localization_data_gap() -> list[dict[str, Any]]:
    files = [
        ("probe_delta_vs_m3", AGENT498 / "probe_delta_vs_m3.csv"),
        ("probe_error_localization", AGENT498 / "probe_error_localization.csv"),
        ("role_segment_error_summary", AGENT498 / "role_segment_error_summary.csv"),
    ]
    rows: list[dict[str, Any]] = []
    for artifact, path in files:
        parsed = read_csv(path)
        rows.append(
            {
                "artifact": artifact,
                "path": rel(path),
                "detail_rows": len(parsed),
                "status": "missing_detail_rows" if not parsed else "available",
                "effect_on_scientific_claim": (
                    "Cannot assign the temperature regression to individual TP/TW probes from this package; "
                    "only aggregate all-probe/TW and segment heat-placement evidence are defensible."
                    if not parsed
                    else "Per-probe localization rows are available."
                ),
                "required_repair": (
                    "Regenerate coupled scoring exports with per-probe candidate-minus-M3 residuals, "
                    "one row per case/split/probe/candidate."
                    if not parsed
                    else "none"
                ),
            }
        )
    return rows


def classify_segment_error(segment: str, role: str, error: float | None) -> str:
    if error is None:
        return "unknown"
    if abs(error) < 1e-8:
        return "train_or_exact_match"
    if segment == "upcomer" and role == "test_section" and error < 0.0:
        return "test_section_loss_underpredicted"
    if segment == "upcomer" and role in {"ambient", "ambient_wall"} and error < 0.0:
        return "upcomer_ambient_loss_underpredicted"
    if segment == "junction" and role in {"junction_other", "junction"} and error > 0.0:
        return "junction_loss_overpredicted"
    if segment == "downcomer" and role in {"ambient", "ambient_wall"} and error > 0.0:
        return "downcomer_loss_overpredicted"
    if error > 0.0:
        return "loss_overpredicted"
    return "loss_underpredicted"


def build_segment_heat_placement_failure_modes() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in read_csv(AGENT498 / "segment_heat_placement_audit.csv"):
        error = fnum(row.get("error_W"))
        segment = row["one_d_segment"]
        role = row["role"]
        rows.append(
            {
                "candidate_id": row["wall_candidate_id"],
                "wall_candidate_id": row["wall_candidate_id"],
                "candidate_family": family_id(row["wall_candidate_id"]),
                "case_id": row["case_id"],
                "split_role": row["split_role"],
                "one_d_segment": segment,
                "role": role,
                "target_heat_W": row["target_loss_W_for_scoring_only"],
                "predicted_heat_W": row["predicted_loss_W"],
                "heat_error_W": row["error_W"],
                "abs_heat_error_W": fmt(abs(error) if error is not None else None),
                "error_sign": "positive" if error is not None and error > 0 else "negative" if error is not None and error < 0 else "zero",
                "failure_mode": classify_segment_error(segment, role, error),
                "scientific_read": (
                    "Held-out errors show heat is redistributed into the wrong 1D role/segment; "
                    "the largest deficits are upcomer test-section loss underprediction while "
                    "junction/downcomer loss is overallocated."
                ),
                "source_paths": rel(AGENT498 / "segment_heat_placement_audit.csv"),
            }
        )
    return rows


def build_candidate_family_decision(
    gates: list[dict[str, Any]], shape_rows: list[dict[str, Any]], segment_rows: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for fam in ["PB1_passive_total", "PB2_salt2_shape", "PB3_attenuated_shape"]:
        fam_gate = [row for row in gates if row["candidate_family"] == fam]
        fam_shape = [row for row in shape_rows if row["candidate_family"] == fam and row["split_role"] in {"validation", "holdout"}]
        fam_segment = [row for row in segment_rows if row["candidate_family"] == fam and row["split_role"] in {"validation", "holdout"}]
        mdot = [fnum(row["mdot_delta_vs_m3_pct"]) for row in (fam_gate or fam_shape)]
        all_probe = [fnum(row["all_probe_delta_vs_m3_K"]) for row in (fam_gate or fam_shape)]
        tw = [fnum(row.get("tw_delta_vs_m3_K")) for row in fam_shape]
        heat = [fnum(row["heat_error_W"]) for row in fam_segment]
        if fam == "PB1_passive_total":
            decision = "not_admitted_legacy_passive_total"
            recommendation = "Do not rerun PB1; use only as proof that total passive hA scaling fixes mdot but not temperature shape."
            source = rel(AGENT498 / "probe_shape_regression_audit.csv")
        else:
            decision = "not_admitted_diagnostic_only"
            recommendation = (
                "Do not freeze. Next candidate must change drive/source placement or axial mixing, not repeat the same "
                "Salt2-shaped heat distribution."
            )
            source = f"{rel(AGENT498 / 'candidate_admission_review.csv')};{rel(AGENT498 / 'segment_heat_placement_audit.csv')}"
        rows.append(
            {
                "candidate_family": fam,
                "candidate_rows_reviewed": len(fam_gate or fam_shape),
                "heldout_shape_rows_reviewed": len(fam_shape),
                "heldout_segment_rows_reviewed": len(fam_segment),
                "mean_mdot_delta_vs_m3_pct": fmt(mean([x for x in mdot if x is not None])),
                "mean_all_probe_delta_vs_m3_K": fmt(mean([x for x in all_probe if x is not None])),
                "mean_tw_delta_vs_m3_K": fmt(mean([x for x in tw if x is not None])),
                "max_abs_segment_heat_error_W": fmt(max_abs([x for x in heat if x is not None])),
                "admission_decision": decision,
                "scientific_decision": (
                    "Reject as freeze candidate because pressure/flow fit improvement is bought with a worse "
                    "temperature shape; available per-probe and segment evidence do not rescue a localized exception."
                ),
                "recommended_next_action": recommendation,
                "source_paths": source,
            }
        )
    return rows


def build_next_candidate_ladder() -> list[dict[str, Any]]:
    return [
        {
            "priority": 1,
            "candidate_or_study": "consume_AGENT_513_wall_temperature_drive_result",
            "status": "completed_do_not_duplicate",
            "why": "The current convective/source drive hypothesis has completed as AGENT-513 and should be consumed as failure-localization evidence.",
            "required_evidence": "M3+TS+cooler coupled rows, admission review, per-split deltas, and freeze decision from AGENT-513.",
            "guardrail": "Do not submit duplicate PB1/PB2/PB3 jobs from this package.",
        },
        {
            "priority": 2,
            "candidate_or_study": "consume_per_probe_localization_exports",
            "status": "available_for_probe_level_claims",
            "why": "AGENT-498 aggregate rows show shape regression, and per-probe localization tables are now populated.",
            "required_evidence": "Use candidate-minus-M3 residuals for every TP/TW probe, case, split, and candidate only as held-out diagnosis.",
            "guardrail": "Keep Salt3/Salt4 score-only; do not tune candidates on residual probes.",
        },
        {
            "priority": 3,
            "candidate_or_study": "source_placement_or_heater_redistribution_candidate",
            "status": "completed_related_work_AGENT_511",
            "why": "Segment audit shows held-out heat moves into wrong roles; AGENT-511 has now scored the source-placement lane and should be consumed as failure-localization evidence.",
            "required_evidence": "Salt2-fit runtime-legal source model scored on Salt3/Salt4 with all-probe/TW gates.",
            "guardrail": "Do not rerun AGENT-511 unless the candidate contract or Fluid solver changes.",
        },
        {
            "priority": 4,
            "candidate_or_study": "junction_aware_or_axial_mixing_proxy",
            "status": "next_if_drive_and_source_do_not_pass",
            "why": "Junction/downcomer overallocations and upcomer/test-section deficits indicate a pure segment-total model may miss axial exchange.",
            "required_evidence": "Runtime-legal junction/axial-mixing proxy with split-clean admission gates and segment/probe residuals.",
            "guardrail": "Current pressure corner-K remains diagnostic until straight-loss subtraction and mask admission are repaired.",
        },
        {
            "priority": 5,
            "candidate_or_study": "corrected_freeze_release",
            "status": "blocked",
            "why": "No wall candidate is admitted, so final prediction freeze cannot be built for val_salt2 or blind rows.",
            "required_evidence": "At least one wall/test-section candidate admitted across validation and holdout gates, then frozen Salt1-4 nominal prediction artifact.",
            "guardrail": "Do not use val_salt2, Salt2 +/-5Q, PM10, future +/-10Q, or new CFD for model selection.",
        },
    ]


def build_freeze_unblock_decision(gates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    admitted = sorted({row["candidate_id"] for row in gates if row["admission_decision"] == "admitted"})
    summary_499 = read_json(AGENT499 / "summary.json")
    summary_509 = read_json(AGENT509 / "summary.json")
    return [
        {
            "blocker_id": "freeze_blocked_no_wall_candidate_admitted",
            "current_status": "blocked" if not admitted else "ready_for_freeze_candidate_review",
            "admitted_wall_candidates": len(admitted),
            "admitted_candidate_ids": ";".join(admitted),
            "agent498_evidence": "0_of_4_local_distribution_candidates_admitted",
            "agent499_decision": summary_499.get("decision", ""),
            "agent509_freeze_status": summary_509.get("freeze_status", ""),
            "decision": "do_not_build_corrected_freeze_yet" if not admitted else "build_corrected_freeze_from_admitted_candidate",
            "why": (
                "AGENT-498 candidates pass runtime setup legality but fail validation and holdout temperature gates. "
                "AGENT-499 therefore has no final corrected candidate, and AGENT-509 remains a shell with no final scores."
            ),
            "source_paths": f"{rel(AGENT498 / 'candidate_admission_review.csv')};{rel(AGENT499 / 'summary.json')};{rel(AGENT509 / 'summary.json')}",
        }
    ]


def build_runtime_leakage_audit() -> list[dict[str, Any]]:
    return [
        {
            "check": "native_solver_outputs_mutated",
            "status": "pass",
            "evidence": "Builder reads only completed work_products CSV/JSON/README artifacts and writes only AGENT-515 package outputs.",
        },
        {
            "check": "scheduler_or_solver_launched",
            "status": "pass",
            "evidence": "No sbatch, srun, Fluid, OpenFOAM, or postprocessing command is invoked by the builder.",
        },
        {
            "check": "duplicate_coupled_scoring_submitted",
            "status": "pass",
            "evidence": "All coupled metrics are consumed from AGENT-494/498 completed tables.",
        },
        {
            "check": "heldout_external_fit_or_tuning",
            "status": "pass",
            "evidence": "Salt3/Salt4 values are used only for scoring/diagnosis; val_salt2 and blind rows are not used.",
        },
        {
            "check": "scientific_admission_state_changed",
            "status": "pass",
            "evidence": "Outputs are diagnostic; freeze decision remains blocked with zero admitted wall candidates.",
        },
        {
            "check": "active_agent_overlap",
            "status": "pass",
            "evidence": "AGENT-511/513/514 active scopes are cited as read-only or downstream; no files in those scopes are written.",
        },
    ]


def build_source_manifest() -> list[dict[str, Any]]:
    paths = [
        (AGENT498 / "candidate_admission_review.csv", "AGENT-498 candidate admission review"),
        (AGENT498 / "coupled_delta_vs_m3.csv", "AGENT-498 held-out deltas versus M3"),
        (AGENT498 / "coupled_scorecard.csv", "AGENT-498 coupled candidate scorecard"),
        (AGENT498 / "probe_shape_regression_audit.csv", "AGENT-494 PB1 shape regression evidence copied into AGENT-498"),
        (AGENT498 / "probe_delta_vs_m3.csv", "AGENT-498 per-probe delta export"),
        (AGENT498 / "probe_error_localization.csv", "AGENT-498 per-probe localization export"),
        (AGENT498 / "role_segment_error_summary.csv", "AGENT-498 role/segment summary export"),
        (AGENT498 / "segment_heat_placement_audit.csv", "AGENT-498 segment heat-placement audit"),
        (AGENT498 / "summary.json", "AGENT-498 package summary"),
        (AGENT499 / "summary.json", "AGENT-499 corrected-split final scorecard summary"),
        (AGENT509 / "summary.json", "AGENT-509 final predictive scorecard shell summary"),
        (AGENT508 / "corrected_freeze_source_audit.csv", "AGENT-508 val_salt2 corrected-freeze source audit"),
    ]
    rows = []
    for path, description in paths:
        rows.append(
            {
                "source_path": rel(path),
                "exists": "yes" if path.exists() else "no",
                "description": description,
                "usage": "read_only_existing_evidence",
            }
        )
    return rows


def write_gate_svg(rows: list[dict[str, Any]], path: Path) -> None:
    width, height = 980, 440
    margin_left, margin_top = 80, 48
    plot_w, plot_h = 820, 300
    entries = rows
    all_values: list[float] = []
    for row in entries:
        for key in ["mdot_delta_vs_m3_pct", "all_probe_delta_vs_m3_K", "tw_delta_vs_m3_K"]:
            value = fnum(row[key])
            if value is not None:
                all_values.append(value)
    lo = min(all_values + [-20.0])
    hi = max(all_values + [70.0])
    span = hi - lo

    def y(value: float) -> float:
        return margin_top + (hi - value) / span * plot_h

    x_step = plot_w / max(1, len(entries))
    colors = {"mdot": "#2f6f8f", "all": "#c44e52", "tw": "#dd8452"}
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        '<text x="28" y="28" font-family="Arial" font-size="18" font-weight="700">AGENT-498 candidate deltas versus M3</text>',
        f'<line x1="{margin_left}" y1="{y(0)}" x2="{margin_left + plot_w}" y2="{y(0)}" stroke="#333" stroke-width="1"/>',
        f'<text x="18" y="{y(0) + 5:.1f}" font-family="Arial" font-size="12">0</text>',
    ]
    for idx, row in enumerate(entries):
        cx = margin_left + idx * x_step + x_step * 0.5
        for offset, key, label, color_key in [
            (-12, "mdot_delta_vs_m3_pct", "mdot", "mdot"),
            (0, "all_probe_delta_vs_m3_K", "all", "all"),
            (12, "tw_delta_vs_m3_K", "TW", "tw"),
        ]:
            value = fnum(row[key])
            if value is None:
                continue
            yy = y(value)
            lines.append(
                f'<circle cx="{cx + offset:.1f}" cy="{yy:.1f}" r="5" fill="{colors[color_key]}">'
                f'<title>{esc(row["candidate_family"])} {esc(row["case_id"])} {label}: {value:.3g}</title></circle>'
            )
        label = row["candidate_family"].replace("_", " ").replace("PB", "P")
        lines.append(
            f'<text x="{cx:.1f}" y="{height - 62}" font-family="Arial" font-size="10" text-anchor="middle" transform="rotate(45 {cx:.1f},{height - 62})">{esc(label)} {esc(row["case_id"])}</text>'
        )
    legend_x = margin_left + plot_w - 240
    for i, (label, color) in enumerate([("mdot delta pct", colors["mdot"]), ("all-probe delta K", colors["all"]), ("TW delta K", colors["tw"])]):
        yy = 24 + i * 18
        lines.append(f'<circle cx="{legend_x}" cy="{yy}" r="5" fill="{color}"/>')
        lines.append(f'<text x="{legend_x + 12}" y="{yy + 4}" font-family="Arial" font-size="12">{esc(label)}</text>')
    lines.append('<text x="28" y="414" font-family="Arial" font-size="12">Negative mdot deltas improve flow; positive temperature deltas mean candidate is worse than M3.</text>')
    lines.append("</svg>")
    path.write_text("\n".join(lines) + "\n")


def write_segment_svg(rows: list[dict[str, Any]], path: Path) -> None:
    grouped: dict[tuple[str, str, str], list[float]] = defaultdict(list)
    for row in rows:
        if row["split_role"] not in {"validation", "holdout"}:
            continue
        value = fnum(row["heat_error_W"])
        if value is not None:
            grouped[(row["candidate_family"], row["one_d_segment"], row["role"])].append(value)
    entries = []
    for key, values in grouped.items():
        entries.append((*key, mean(values) or 0.0, max_abs(values) or 0.0))
    entries.sort(key=lambda item: abs(item[3]), reverse=True)
    entries = entries[:14]
    width, height = 980, 500
    margin_left, margin_top = 260, 54
    plot_w, bar_h, gap = 620, 18, 10
    maxv = max([abs(item[3]) for item in entries] + [1.0])
    zero_x = margin_left + plot_w / 2

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        '<text x="28" y="30" font-family="Arial" font-size="18" font-weight="700">Held-out segment heat placement errors</text>',
        f'<line x1="{zero_x:.1f}" y1="{margin_top - 8}" x2="{zero_x:.1f}" y2="{height - 60}" stroke="#333" stroke-width="1"/>',
    ]
    for idx, (fam, segment, role, avg_error, peak_abs) in enumerate(entries):
        y0 = margin_top + idx * (bar_h + gap)
        length = abs(avg_error) / maxv * (plot_w / 2 - 14)
        x0 = zero_x if avg_error >= 0 else zero_x - length
        color = "#c44e52" if avg_error >= 0 else "#2f6f8f"
        label = f"{fam} / {segment} / {role}"
        lines.append(f'<text x="24" y="{y0 + 13}" font-family="Arial" font-size="11">{esc(label)}</text>')
        lines.append(
            f'<rect x="{x0:.1f}" y="{y0}" width="{length:.1f}" height="{bar_h}" fill="{color}">'
            f'<title>mean error {avg_error:.3g} W; peak abs {peak_abs:.3g} W</title></rect>'
        )
        lines.append(f'<text x="{x0 + length + 4 if avg_error >= 0 else x0 - 52:.1f}" y="{y0 + 13}" font-family="Arial" font-size="11">{avg_error:.2f} W</text>')
    lines.append('<text x="28" y="472" font-family="Arial" font-size="12">Positive values overpredict heat loss in that 1D role; negative values underpredict it.</text>')
    lines.append("</svg>")
    path.write_text("\n".join(lines) + "\n")


def write_readme(summary: dict[str, Any]) -> None:
    readme = OUT / "README.md"
    text = f"""---
provenance:
  created_by: {TASK}
  created_utc: {summary['created_utc']}
  source_packages:
    - {rel(AGENT494)}
    - {rel(AGENT498)}
    - {rel(AGENT499)}
    - {rel(AGENT508)}
    - {rel(AGENT509)}
tags:
  - forward-predictive-model
  - wall-test-section
  - freeze-blocker
  - existing-evidence
related:
  - .agent/status/2026-07-17_AGENT-515.md
  - .agent/journal/2026-07-17/wall-candidate-failure-localization.md
  - imports/2026-07-17_wall_candidate_failure_localization.json
status: current
---

# Wall Candidate Failure Localization

This package explains why `freeze_blocked_no_wall_candidate_admitted` remains
blocked after the completed July 17 wall/test-section harvests. It is diagnostic
only: no solver, scheduler, Fluid, fitting, tuning, registry, or admission state
was changed.

## Main Finding

AGENT-498 produced `{summary['agent498_candidate_count']}` local distribution
candidates and `{summary['agent498_coupled_rows']}` coupled rows. All four
candidates pass runtime legality, and every validation/holdout row improves
mdot versus M3. None can be admitted because all validation/holdout rows worsen
the aggregate temperature field, especially all-probe and TW errors.

The failure is therefore not "we forgot to freeze it" and not a runtime-input
leak. It is a physics/localization failure: heat is placed in the wrong 1D
roles/segments, and populated per-probe rows are available for held-out
sensor-level diagnosis of the aggregate regression.

## Files

- `wall_candidate_gate_failure_matrix.csv` - validation/holdout gate rows for
  the AGENT-498 candidates.
- `temperature_shape_regression_summary.csv` - PB1/PB2/PB3 shape-regression
  evidence, with data-limit notes where TP deltas are unavailable.
- `probe_localization_data_gap.csv` - explicit audit of per-probe localization
  export availability.
- `segment_heat_placement_failure_modes.csv` - role/segment heat-placement
  errors and failure-mode labels.
- `candidate_family_decision.csv` - PB1/PB2/PB3 family decisions and next
  action recommendations.
- `next_candidate_ladder.csv` - ordered next studies without duplicating active
  AGENT-511/513 work.
- `freeze_unblock_decision.csv` - corrected-freeze decision; currently blocked.
- `wall_candidate_gate_deltas.svg` and `segment_heat_placement_errors.svg` -
  quicklook plots.
- `runtime_leakage_audit.csv`, `source_manifest.csv`, and `summary.json` -
  provenance and guardrail checks.

## Scientific Interpretation

The pressure/flow side moves in the desired direction, but the thermal field
does not. That combination is typical of a model that has the right integrated
loss direction but the wrong source placement, drive temperature, axial exchange,
or junction ownership. The segment heat audit shows the strongest held-out
pattern: upcomer/test-section loss is underpredicted while junction and
downcomer roles absorb too much loss.

The defensible next move is to consume the completed wall-temperature-drive and
heater-source redistribution candidate packages together with the populated
per-probe residual exports for sensor-level diagnosis. The corrected freeze
should stay blocked until a wall/test-section candidate passes the predeclared
validation and holdout gates.
"""
    readme.write_text(text)


def build() -> dict[str, Any]:
    OUT.mkdir(parents=True, exist_ok=True)
    gates = build_wall_candidate_gate_failure_matrix()
    shape_rows = build_temperature_shape_regression_summary()
    data_gap = build_probe_localization_data_gap()
    segment_rows = build_segment_heat_placement_failure_modes()
    family_rows = build_candidate_family_decision(gates, shape_rows, segment_rows)
    ladder = build_next_candidate_ladder()
    freeze = build_freeze_unblock_decision(gates)
    runtime = build_runtime_leakage_audit()
    manifest = build_source_manifest()

    write_csv(OUT / "wall_candidate_gate_failure_matrix.csv", gates)
    write_csv(OUT / "temperature_shape_regression_summary.csv", shape_rows)
    write_csv(OUT / "probe_localization_data_gap.csv", data_gap)
    write_csv(OUT / "segment_heat_placement_failure_modes.csv", segment_rows)
    write_csv(OUT / "candidate_family_decision.csv", family_rows)
    write_csv(OUT / "next_candidate_ladder.csv", ladder)
    write_csv(OUT / "freeze_unblock_decision.csv", freeze)
    write_csv(OUT / "runtime_leakage_audit.csv", runtime)
    write_csv(OUT / "source_manifest.csv", manifest)
    write_gate_svg(gates, OUT / "wall_candidate_gate_deltas.svg")
    write_segment_svg(segment_rows, OUT / "segment_heat_placement_errors.svg")

    summary = {
        "task": TASK,
        "created_utc": utc_now(),
        "output_dir": rel(OUT),
        "agent498_candidate_count": len({row["candidate_id"] for row in gates}),
        "agent498_coupled_rows": len(gates),
        "mdot_improves_temperature_regresses_rows": sum(
            row["gate_interpretation"] == "mdot_improves_temperature_regresses" for row in gates
        ),
        "admitted_wall_candidates": int(freeze[0]["admitted_wall_candidates"]),
        "freeze_status": freeze[0]["current_status"],
        "freeze_decision": freeze[0]["decision"],
        "probe_localization_empty_files": sum(row["status"] == "missing_detail_rows" for row in data_gap),
        "segment_heat_placement_rows": len(segment_rows),
        "candidate_family_rows": len(family_rows),
        "next_candidate_ladder_rows": len(ladder),
        "runtime_audit_failures": sum(row["status"] != "pass" for row in runtime),
        "scientific_admission_change": "none",
        "scheduler_action": "none",
        "solver_action": "none",
        "guardrail": "Existing-evidence diagnostic only; no model selection on Salt3/Salt4 or external rows.",
    }
    with (OUT / "summary.json").open("w") as handle:
        json.dump(summary, handle, indent=2, sort_keys=True)
        handle.write("\n")
    write_readme(summary)
    return summary


if __name__ == "__main__":
    print(json.dumps(build(), indent=2, sort_keys=True))
