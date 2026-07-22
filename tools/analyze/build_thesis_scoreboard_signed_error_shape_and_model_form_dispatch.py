#!/usr/bin/env python3
"""Build thesis scoreboard signed-error shape and model-form dispatch package."""

from __future__ import annotations

import csv
import json
import math
import re
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_thesis_scoreboard_signed_error_shape_and_model_form_dispatch"
SCOREBOARD = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_thesis_master_model_form_scoreboard"

SIGNED_ERRORS = SCOREBOARD / "signed_sensor_errors.csv"
SIGNED_SUMMARY = SCOREBOARD / "signed_sensor_error_summary.csv"
MASTER_SCOREBOARD = SCOREBOARD / "master_model_form_scoreboard.csv"
RECOMMENDED_FORMS = SCOREBOARD / "recommended_model_forms_to_try.csv"

EVIDENCE = {
    "endpoint_bakeoff": ROOT / "work_products/2026-07/2026-07-17/2026-07-17_thesis_endpoint_model_form_bakeoff/model_form_scores.csv",
    "s13_neighbor_uq": ROOT / "work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_qwall_same_qoi_neighbor_uq_execution/summary.json",
    "s13_neighbor_sampling": ROOT / "work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_qwall_neighbor_window_sampling/summary.json",
    "n3_thermal_ablation": ROOT / "work_products/2026-07/2026-07-22/2026-07-22_thesis_n3_thermal_residual_owner_train_ablation/summary.json",
    "s12_disposition": ROOT / "work_products/2026-07/2026-07-22/2026-07-22_s12_thermal_residual_candidate_disposition_and_thesis_panels/summary.json",
    "pressure_retry_gate": ROOT / "work_products/2026-07/2026-07-22/2026-07-22_s10_s14_pressure_f6_cand001_retry_and_uq_gate/summary.json",
    "n1_frozen_gate": ROOT / "work_products/2026-07/2026-07-22/2026-07-22_thesis_n1_frozen_runtime_legal_candidate_gate/summary.json",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in fieldnames})


def read_json(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def write_json(path: Path, data: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def fnum(value: str | float | int | None) -> float | None:
    if value in (None, ""):
        return None
    try:
        x = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(x) or math.isinf(x):
        return None
    return x


def sensor_index(sensor: str) -> int:
    m = re.search(r"(\d+)$", sensor or "")
    return int(m.group(1)) if m else 999


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else float("nan")


def rmse(values: list[float]) -> float:
    return math.sqrt(sum(v * v for v in values) / len(values)) if values else float("nan")


def classify_shape(values: list[float]) -> str:
    if not values:
        return "no_finite_predictions"
    pos = sum(1 for v in values if v > 0.0)
    neg = sum(1 for v in values if v < 0.0)
    bias = mean(values)
    local = rmse([v - bias for v in values])
    abs_bias = abs(bias)
    if neg and not pos:
        sign = "globally_cold"
    elif pos and not neg:
        sign = "globally_hot"
    else:
        sign = "mixed_sign"
    if local < 0.25 * max(abs_bias, 1e-9):
        shape = "bias_dominated"
    elif local < 0.75 * max(abs_bias, 1e-9):
        shape = "bias_plus_local_shape"
    else:
        shape = "local_shape_dominated"
    return f"{sign}_{shape}"


def slope_by_sensor(xs: list[float], ys: list[float]) -> float:
    if len(xs) < 2:
        return float("nan")
    xbar = mean(xs)
    ybar = mean(ys)
    denom = sum((x - xbar) ** 2 for x in xs)
    if denom == 0:
        return float("nan")
    return sum((x - xbar) * (y - ybar) for x, y in zip(xs, ys)) / denom


def load_shape_metrics() -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    rows = read_csv(SIGNED_ERRORS)
    grouped: dict[tuple[str, str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        if row.get("finite_prediction", "").lower() == "true":
            grouped[(row["model_form_id"], row["case_id"], row["sensor_kind"])].append(row)

    metrics: list[dict[str, object]] = []
    enriched: list[dict[str, object]] = []
    outliers: list[dict[str, object]] = []
    for key, group in sorted(grouped.items()):
        model, case, kind = key
        group = sorted(group, key=lambda r: sensor_index(r["sensor"]))
        vals = [fnum(r["signed_error_K"]) for r in group]
        finite_vals = [v for v in vals if v is not None]
        bias = mean(finite_vals)
        local_resids = [v - bias for v in finite_vals]
        xs = [float(sensor_index(r["sensor"])) for r in group if fnum(r["signed_error_K"]) is not None]
        slope = slope_by_sensor(xs, finite_vals)
        abs_bias = abs(bias)
        local_shape = rmse(local_resids)
        max_abs = max((abs(v) for v in finite_vals), default=float("nan"))
        span = (max(finite_vals) - min(finite_vals)) if finite_vals else float("nan")
        metrics.append(
            {
                "model_form_id": model,
                "case_id": case,
                "sensor_kind": kind,
                "finite_rows": len(finite_vals),
                "mean_signed_error_K": bias,
                "rmse_K": rmse(finite_vals),
                "local_shape_rmse_after_bias_K": local_shape,
                "max_abs_signed_error_K": max_abs,
                "signed_error_span_K": span,
                "signed_error_slope_K_per_sensor_index": slope,
                "shape_fraction_local_over_total": local_shape / rmse(finite_vals) if finite_vals and rmse(finite_vals) else "",
                "shape_class": classify_shape(finite_vals),
                "primary_error_mode": "global_bias" if abs_bias >= local_shape else "local_shape",
            }
        )
        for r in group:
            signed = fnum(r["signed_error_K"])
            residual = signed - bias if signed is not None else None
            new = dict(r)
            new["bias_removed_error_K"] = residual if residual is not None else ""
            new["group_mean_signed_error_K"] = bias
            new["shape_class"] = classify_shape(finite_vals)
            enriched.append(new)
            if residual is not None:
                outliers.append(
                    {
                        "model_form_id": model,
                        "case_id": case,
                        "sensor_kind": kind,
                        "sensor": r["sensor"],
                        "signed_error_K": signed,
                        "group_mean_signed_error_K": bias,
                        "bias_removed_error_K": residual,
                        "abs_bias_removed_error_K": abs(residual),
                        "target_K": r["target_K"],
                        "prediction_source_segment": r["prediction_source_segment"],
                    }
                )
    outliers.sort(key=lambda r: float(r["abs_bias_removed_error_K"]), reverse=True)
    return metrics, enriched, outliers


def model_level_summary(metrics: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in metrics:
        grouped[str(row["model_form_id"])].append(row)
    rows = []
    for model, items in sorted(grouped.items()):
        rmse_vals = [float(r["rmse_K"]) for r in items if fnum(r["rmse_K"]) is not None]
        bias_vals = [float(r["mean_signed_error_K"]) for r in items if fnum(r["mean_signed_error_K"]) is not None]
        shape_vals = [float(r["local_shape_rmse_after_bias_K"]) for r in items if fnum(r["local_shape_rmse_after_bias_K"]) is not None]
        rows.append(
            {
                "model_form_id": model,
                "groups": len(items),
                "mean_group_rmse_K": mean(rmse_vals),
                "mean_group_signed_bias_K": mean(bias_vals),
                "mean_abs_group_signed_bias_K": mean([abs(v) for v in bias_vals]),
                "mean_local_shape_rmse_after_bias_K": mean(shape_vals),
                "dominant_status": "best_current_legacy_numeric_comparator" if model == "M3" else "legacy_numeric_context",
            }
        )
    return rows


def improvement_rows(model_summary: list[dict[str, object]]) -> list[dict[str, object]]:
    by_model = {str(r["model_form_id"]): r for r in model_summary}
    rows: list[dict[str, object]] = []
    for base, improved in [("M1", "M2"), ("M2", "M3"), ("M1", "M3")]:
        if base in by_model and improved in by_model:
            base_rmse = float(by_model[base]["mean_group_rmse_K"])
            new_rmse = float(by_model[improved]["mean_group_rmse_K"])
            rows.append(
                {
                    "comparison": f"{base}_to_{improved}",
                    "from_model": base,
                    "to_model": improved,
                    "mean_group_rmse_before_K": base_rmse,
                    "mean_group_rmse_after_K": new_rmse,
                    "mean_group_rmse_delta_K": new_rmse - base_rmse,
                    "mean_group_rmse_reduction_pct": 100.0 * (base_rmse - new_rmse) / base_rmse if base_rmse else "",
                    "interpretation": "thermal_boundary_and_segment_model_reduces_error" if new_rmse < base_rmse else "no_improvement",
                }
            )
    return rows


def evidence_decision(path_key: str, field: str, default: str = "") -> object:
    return read_json(EVIDENCE[path_key]).get(field, default)


def study_status_rows() -> list[dict[str, object]]:
    return [
        {
            "rank": 1,
            "study": "Signed Error Shape Study",
            "status": "executed_in_this_package",
            "current_result": "sensor_by_sensor_signed_errors_and_bias_removed_shape_metrics_published",
            "next_action": "use figures to decide whether next error reduction targets global heat level, local wall shape, or mdot/pressure coupling",
            "admission_or_score_change": "none",
        },
        {
            "rank": 2,
            "study": "M0 Setup Baseline",
            "status": "gap_contract_published_not_scored",
            "current_result": "M0 remains prediction_missing_not_run in endpoint bakeoff; no frozen setup-only predictions exist in scoreboard",
            "next_action": "claim M0 setup-only baseline prediction scorecard row with runtime-input audit and missing-prediction table",
            "admission_or_score_change": "none",
        },
        {
            "rank": 3,
            "study": "S13 Same-QOI UQ / Neighbor Window Gate",
            "status": "completed_fail_closed_from_existing_evidence",
            "current_result": f"target_rows={evidence_decision('s13_neighbor_sampling', 'target_ready_rows', 12)}; target_minus_rows={evidence_decision('s13_neighbor_sampling', 'target_minus_ready_rows', 12)}; target_plus_rows={evidence_decision('s13_neighbor_sampling', 'target_plus_ready_rows', 0)}; same_qoi_ready={evidence_decision('s13_neighbor_sampling', 'same_qoi_neighbor_uq_ready_qois', 0)}",
            "next_action": "do not run production harvest until target-plus and mesh/GCI support exist",
            "admission_or_score_change": "none",
        },
        {
            "rank": 4,
            "study": "Passive Wall/Test-Section Residual Ownership",
            "status": "completed_train_only_fail_closed_for_candidate_release",
            "current_result": f"N3 decision={evidence_decision('n3_thermal_ablation', 'decision', 'train_only_residual_owner_ablation_complete_no_candidate_release')}; S12 candidate release remains zero",
            "next_action": "claim source-bounded passive wall/test-section repair gate only with independent setup/geometry/literature source basis",
            "admission_or_score_change": "none",
        },
        {
            "rank": 5,
            "study": "Pressure/Mdot Coupling Study",
            "status": "retry_gate_complete_no_pressure_admission",
            "current_result": f"pressure decision={evidence_decision('pressure_retry_gate', 'decision', 'cand001_retry_runbook_recommended_no_launch_no_f6_scoring')}; lower-right remains section-effective diagnostic",
            "next_action": "claim pressure-mdot coupling diagnostic row; do not admit component K/F6 from lower-right recirculating rows",
            "admission_or_score_change": "none",
        },
    ]


def m0_contract_rows() -> list[dict[str, object]]:
    endpoint_rows = read_csv(EVIDENCE["endpoint_bakeoff"])
    m0 = next((r for r in endpoint_rows if r.get("model_form_id") == "M0"), {})
    return [
        {
            "model_form": "M0 setup-only baseline",
            "current_score_status": m0.get("score_status", "prediction_missing_not_run"),
            "current_admission_status": m0.get("admission_status", "shell_only_lower_bound_not_scored"),
            "can_score_now": "false",
            "why_not": "no frozen setup-only predictions are available in the scoreboard; this package is not allowed to run Fluid/external solver paths",
            "minimum_required_inputs": "geometry; property lane; setup heater power; setup cooler/HX metadata; ambient/surroundings/emissivity setup inputs; runtime-input audit; split ledger",
            "forbidden_runtime_inputs": "CFD mdot; realized CFD wallHeatFlux; scored-row TP/TW temperatures; scored-row pressure losses; validation/holdout/external residuals; hidden global multipliers",
            "next_board_row": "TODO-M0-SETUP-ONLY-BASELINE-PREDICTION-SCORECARD-2026-07-22",
        }
    ]


def board_dispatch_rows() -> list[dict[str, object]]:
    return [
        {
            "rank": 1,
            "model_form": "M0 setup-only baseline",
            "board_status_after_this_task": "added_open_row",
            "task_id": "TODO-M0-SETUP-ONLY-BASELINE-PREDICTION-SCORECARD-2026-07-22",
            "purpose": "Produce the real lower-bound predictions or explicit missing-prediction matrix.",
            "claim_boundary": "No final score unless predictions are generated under runtime-input audit.",
        },
        {
            "rank": 2,
            "model_form": "M5 / MF-04 throughflow-plus-recirculation exchange cell",
            "board_status_after_this_task": "already_represented_by_S13_rows",
            "task_id": "TODO-THESIS-STUDY-S13-UPCOMER-EXCHANGE-PRODUCTION-HARVEST-UQ-2026-07-21",
            "purpose": "Unblock or fail-close production harvest for exchange CV QOIs.",
            "claim_boundary": "Diagnostic only until target-plus, same-QOI UQ, mesh/GCI, and source/property gates pass.",
        },
        {
            "rank": 3,
            "model_form": "MF-02 section-effective pressure residual / pressure-mdot coupling",
            "board_status_after_this_task": "added_open_row",
            "task_id": "TODO-MF02-PRESSURE-MDOT-COUPLING-DIAGNOSTIC-2026-07-22",
            "purpose": "Quantify how pressure residual choices move mdot and thermal level.",
            "claim_boundary": "No component K, F6, clipped K, or hidden/global multiplier admission.",
        },
        {
            "rank": 4,
            "model_form": "M2+ passive wall/test-section source-bounded repair",
            "board_status_after_this_task": "added_open_row",
            "task_id": "TODO-M2-PASSIVE-WALL-TEST-SECTION-SOURCE-BOUNDED-REPAIR-GATE-2026-07-22",
            "purpose": "Separate broad cold bias into source-bounded passive heat, axial mixing, wall/core exchange, or unresolved residual.",
            "claim_boundary": "No source/property release or repair execution unless independent source basis gates pass.",
        },
        {
            "rank": 5,
            "model_form": "MF-01 ordinary gated single-stream branch",
            "board_status_after_this_task": "already_represented_by_S10_S14_and_future_F6_rows",
            "task_id": "TODO-S10-S14-PRESSURE-F6-CAND001-RETRY-AND-UQ-GATE-2026-07-21",
            "purpose": "Keep ordinary F6 limited to right_leg/test_section_span lanes after ordinary-flow and UQ gates.",
            "claim_boundary": "No recirculating corner rows as ordinary F6 evidence.",
        },
    ]


def svg_header(width: int, height: int) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">\n'
        '<style>text{font-family:Arial,sans-serif;font-size:12px;fill:#1f2933}'
        '.title{font-size:18px;font-weight:700}.axis{stroke:#394b59;stroke-width:1}'
        '.grid{stroke:#d9e2ec;stroke-width:1}.zero{stroke:#d64545;stroke-width:1.2;stroke-dasharray:4 3}'
        '.label{font-size:11px}.small{font-size:10px}</style>\n'
        '<rect width="100%" height="100%" fill="#ffffff"/>\n'
    )


def build_shape_svg(enriched: list[dict[str, object]], path: Path) -> None:
    models = ["M1", "M1b", "M2", "M3"]
    colors = {"M1": "#c2410c", "M1b": "#7c3aed", "M2": "#0f766e", "M3": "#2563eb"}
    cases = ["salt_2", "salt_3", "salt_4"]
    kinds = ["TP", "TW"]
    grouped: dict[tuple[str, str, str], list[dict[str, object]]] = defaultdict(list)
    vals = []
    for r in enriched:
        v = fnum(r.get("signed_error_K"))
        if v is not None:
            grouped[(str(r["model_form_id"]), str(r["case_id"]), str(r["sensor_kind"]))].append(r)
            vals.append(v)
    ymin = math.floor(min(vals) / 25.0) * 25.0
    ymax = math.ceil(max(vals) / 25.0) * 25.0
    width, height = 1120, 760
    panel_w, panel_h = 320, 250
    left0, top0 = 70, 80
    gap_x, gap_y = 40, 55
    svg = [svg_header(width, height)]
    svg.append('<text class="title" x="40" y="34">Signed Sensor Error Shape by Model Form</text>\n')
    svg.append('<text x="40" y="55">Signed error = predicted temperature - CFD target. Negative values mean the 1D model is cold.</text>\n')
    for ci, case in enumerate(cases):
        for ki, kind in enumerate(kinds):
            x0 = left0 + ci * (panel_w + gap_x)
            y0 = top0 + ki * (panel_h + gap_y)
            svg.append(f'<text x="{x0}" y="{y0 - 14}" font-weight="700">{case} {kind}</text>\n')
            for frac in [0, 0.25, 0.5, 0.75, 1.0]:
                y = y0 + panel_h - frac * panel_h
                val = ymin + frac * (ymax - ymin)
                cls = "zero" if abs(val) < 1e-9 else "grid"
                svg.append(f'<line class="{cls}" x1="{x0}" y1="{y}" x2="{x0 + panel_w}" y2="{y}"/>\n')
                svg.append(f'<text class="small" x="{x0 - 42}" y="{y + 4}">{val:.0f}</text>\n')
            svg.append(f'<line class="axis" x1="{x0}" y1="{y0}" x2="{x0}" y2="{y0 + panel_h}"/>\n')
            svg.append(f'<line class="axis" x1="{x0}" y1="{y0 + panel_h}" x2="{x0 + panel_w}" y2="{y0 + panel_h}"/>\n')
            max_sensor = 6 if kind == "TP" else 11
            for si in range(1, max_sensor + 1):
                x = x0 + (si - 1) / max(1, max_sensor - 1) * panel_w
                svg.append(f'<text class="small" text-anchor="middle" x="{x}" y="{y0 + panel_h + 16}">{kind}{si}</text>\n')
            for model in models:
                group = sorted(grouped.get((model, case, kind), []), key=lambda r: sensor_index(str(r["sensor"])))
                pts = []
                for r in group:
                    v = fnum(r.get("signed_error_K"))
                    if v is None:
                        continue
                    idx = sensor_index(str(r["sensor"]))
                    x = x0 + (idx - 1) / max(1, max_sensor - 1) * panel_w
                    y = y0 + panel_h - (v - ymin) / (ymax - ymin) * panel_h
                    pts.append((x, y))
                if len(pts) > 1:
                    d = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
                    svg.append(f'<polyline points="{d}" fill="none" stroke="{colors[model]}" stroke-width="2"/>\n')
                for x, y in pts:
                    svg.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3" fill="{colors[model]}"/>\n')
    lx, ly = 830, 36
    for i, model in enumerate(models):
        svg.append(f'<line x1="{lx + i * 70}" y1="{ly}" x2="{lx + 25 + i * 70}" y2="{ly}" stroke="{colors[model]}" stroke-width="3"/>\n')
        svg.append(f'<text x="{lx + 30 + i * 70}" y="{ly + 4}">{model}</text>\n')
    svg.append("</svg>\n")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(svg))


def build_bias_shape_svg(metrics: list[dict[str, object]], path: Path) -> None:
    colors = {"M1": "#c2410c", "M1b": "#7c3aed", "M2": "#0f766e", "M3": "#2563eb"}
    points = [
        (str(r["model_form_id"]), str(r["case_id"]), str(r["sensor_kind"]), float(r["mean_signed_error_K"]), float(r["local_shape_rmse_after_bias_K"]))
        for r in metrics
    ]
    xmin = math.floor(min(p[3] for p in points) / 25.0) * 25.0
    xmax = math.ceil(max(p[3] for p in points) / 25.0) * 25.0
    ymax = math.ceil(max(p[4] for p in points) / 5.0) * 5.0
    width, height = 720, 500
    x0, y0, w, h = 80, 70, 560, 350
    svg = [svg_header(width, height)]
    svg.append('<text class="title" x="40" y="35">Global Bias vs Local Shape Error</text>\n')
    svg.append('<text x="40" y="56">Left/right position is mean signed error; vertical position is RMSE after removing group bias.</text>\n')
    for frac in [0, 0.25, 0.5, 0.75, 1.0]:
        x = x0 + frac * w
        val = xmin + frac * (xmax - xmin)
        cls = "zero" if abs(val) < 1e-9 else "grid"
        svg.append(f'<line class="{cls}" x1="{x}" y1="{y0}" x2="{x}" y2="{y0 + h}"/>\n')
        svg.append(f'<text class="small" text-anchor="middle" x="{x}" y="{y0 + h + 18}">{val:.0f}</text>\n')
        y = y0 + h - frac * h
        yval = frac * ymax
        svg.append(f'<line class="grid" x1="{x0}" y1="{y}" x2="{x0 + w}" y2="{y}"/>\n')
        svg.append(f'<text class="small" text-anchor="end" x="{x0 - 8}" y="{y + 4}">{yval:.0f}</text>\n')
    svg.append(f'<line class="axis" x1="{x0}" y1="{y0 + h}" x2="{x0 + w}" y2="{y0 + h}"/>\n')
    svg.append(f'<line class="axis" x1="{x0}" y1="{y0}" x2="{x0}" y2="{y0 + h}"/>\n')
    svg.append(f'<text class="label" text-anchor="middle" x="{x0 + w / 2}" y="{height - 35}">mean signed error K</text>\n')
    svg.append(f'<text class="label" transform="translate(20 {y0 + h / 2}) rotate(-90)" text-anchor="middle">local shape RMSE after bias K</text>\n')
    for model, case, kind, bias, local in points:
        x = x0 + (bias - xmin) / (xmax - xmin) * w
        y = y0 + h - local / ymax * h if ymax else y0 + h
        marker = "circle" if kind == "TP" else "rect"
        if marker == "circle":
            svg.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" fill="{colors.get(model, "#111827")}" opacity="0.85"/>\n')
        else:
            svg.append(f'<rect x="{x - 5:.1f}" y="{y - 5:.1f}" width="10" height="10" fill="{colors.get(model, "#111827")}" opacity="0.85"/>\n')
    lx, ly = 440, 90
    for i, model in enumerate(["M1", "M1b", "M2", "M3"]):
        svg.append(f'<circle cx="{lx}" cy="{ly + i * 22}" r="5" fill="{colors[model]}"/><text x="{lx + 12}" y="{ly + i * 22 + 4}">{model}</text>\n')
    svg.append(f'<circle cx="{lx + 85}" cy="{ly}" r="5" fill="#64748b"/><text x="{lx + 98}" y="{ly + 4}">TP</text>\n')
    svg.append(f'<rect x="{lx + 80}" y="{ly + 17}" width="10" height="10" fill="#64748b"/><text x="{lx + 98}" y="{ly + 27}">TW</text>\n')
    svg.append("</svg>\n")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(svg))


def write_readme(summary: dict[str, object]) -> None:
    readme = f"""---
provenance:
  - {SIGNED_ERRORS.relative_to(ROOT)}
  - {SIGNED_SUMMARY.relative_to(ROOT)}
  - {MASTER_SCOREBOARD.relative_to(ROOT)}
  - {RECOMMENDED_FORMS.relative_to(ROOT)}
tags: [thesis, model-form-scoreboard, signed-error-shape, no-admission]
related:
  - .agent/status/2026-07-22_TODO-THESIS-SCOREBOARD-SIGNED-ERROR-SHAPE-AND-MODEL-FORM-DISPATCH-2026-07-22.md
  - .agent/journal/2026-07-22/thesis-scoreboard-signed-error-shape-and-model-form-dispatch.md
task: TODO-THESIS-SCOREBOARD-SIGNED-ERROR-SHAPE-AND-MODEL-FORM-DISPATCH-2026-07-22
date: 2026-07-22
role: Implementer / Tester / Writer / Reviewer / Coordinator
type: work_product
status: complete
---
# Thesis Scoreboard Signed-Error Shape And Model-Form Dispatch

Decision: `{summary["decision"]}`.

This package performs the signed-error shape study requested from the thesis
master model-form scoreboard. It also records the current gate status for M0,
S13, passive wall/test-section residual ownership, and pressure/mdot coupling.

## Outputs

- `signed_error_shape_metrics.csv`
- `signed_error_shape_by_sensor.csv`
- `signed_error_local_shape_outliers.csv`
- `model_form_level_error_summary.csv`
- `model_form_error_reduction_targets.csv`
- `m0_setup_baseline_gap_contract.csv`
- `study_enrichment_status.csv`
- `model_form_board_dispatch_matrix.csv`
- `figures/svg/signed_error_shape_by_sensor.svg`
- `figures/svg/bias_vs_shape_residual.svg`
- `summary.json`

## Result

- shape metric rows: `{summary["shape_metric_rows"]}`
- finite sensor rows: `{summary["finite_sensor_rows"]}`
- model-level rows: `{summary["model_level_rows"]}`
- board dispatch rows: `{summary["board_dispatch_rows"]}`

No new prediction scoring, fitting, model selection, source/property release,
coefficient admission, S11/S12/S13/S15/S6 trigger, solver/sampler/harvest/UQ
launch, Fluid/external edit, thesis edit, or native-output mutation was
performed.
"""
    (OUT / "README.md").write_text(readme)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "figures/svg").mkdir(parents=True, exist_ok=True)

    metrics, enriched, outliers = load_shape_metrics()
    model_summary = model_level_summary(metrics)
    improvements = improvement_rows(model_summary)
    studies = study_status_rows()
    m0_contract = m0_contract_rows()
    board_rows = board_dispatch_rows()

    write_csv(
        OUT / "signed_error_shape_metrics.csv",
        metrics,
        [
            "model_form_id",
            "case_id",
            "sensor_kind",
            "finite_rows",
            "mean_signed_error_K",
            "rmse_K",
            "local_shape_rmse_after_bias_K",
            "max_abs_signed_error_K",
            "signed_error_span_K",
            "signed_error_slope_K_per_sensor_index",
            "shape_fraction_local_over_total",
            "shape_class",
            "primary_error_mode",
        ],
    )
    write_csv(
        OUT / "signed_error_shape_by_sensor.csv",
        enriched,
        list(enriched[0].keys()) if enriched else [],
    )
    write_csv(
        OUT / "signed_error_local_shape_outliers.csv",
        outliers[:40],
        [
            "model_form_id",
            "case_id",
            "sensor_kind",
            "sensor",
            "signed_error_K",
            "group_mean_signed_error_K",
            "bias_removed_error_K",
            "abs_bias_removed_error_K",
            "target_K",
            "prediction_source_segment",
        ],
    )
    write_csv(
        OUT / "model_form_level_error_summary.csv",
        model_summary,
        [
            "model_form_id",
            "groups",
            "mean_group_rmse_K",
            "mean_group_signed_bias_K",
            "mean_abs_group_signed_bias_K",
            "mean_local_shape_rmse_after_bias_K",
            "dominant_status",
        ],
    )
    write_csv(
        OUT / "model_form_error_reduction_targets.csv",
        improvements,
        [
            "comparison",
            "from_model",
            "to_model",
            "mean_group_rmse_before_K",
            "mean_group_rmse_after_K",
            "mean_group_rmse_delta_K",
            "mean_group_rmse_reduction_pct",
            "interpretation",
        ],
    )
    write_csv(
        OUT / "m0_setup_baseline_gap_contract.csv",
        m0_contract,
        [
            "model_form",
            "current_score_status",
            "current_admission_status",
            "can_score_now",
            "why_not",
            "minimum_required_inputs",
            "forbidden_runtime_inputs",
            "next_board_row",
        ],
    )
    write_csv(
        OUT / "study_enrichment_status.csv",
        studies,
        ["rank", "study", "status", "current_result", "next_action", "admission_or_score_change"],
    )
    write_csv(
        OUT / "model_form_board_dispatch_matrix.csv",
        board_rows,
        ["rank", "model_form", "board_status_after_this_task", "task_id", "purpose", "claim_boundary"],
    )
    write_csv(
        OUT / "source_manifest.csv",
        [{"source_path": str(p.relative_to(ROOT)), "exists": p.exists()} for p in [SIGNED_ERRORS, SIGNED_SUMMARY, MASTER_SCOREBOARD, RECOMMENDED_FORMS, *EVIDENCE.values()]],
        ["source_path", "exists"],
    )
    write_csv(
        OUT / "no_mutation_guardrails.csv",
        [
            {"guardrail": "native_solver_outputs_mutated", "value": False},
            {"guardrail": "registry_or_admission_mutated", "value": False},
            {"guardrail": "scheduler_action", "value": False},
            {"guardrail": "solver_sampler_harvest_uq_launched", "value": False},
            {"guardrail": "validation_holdout_external_new_scoring", "value": False},
            {"guardrail": "fitting_or_model_selection", "value": False},
            {"guardrail": "source_property_release", "value": False},
            {"guardrail": "coefficient_admission", "value": False},
            {"guardrail": "s11_s12_s13_s15_s6_trigger", "value": False},
            {"guardrail": "residual_absorbed_into_internal_nu", "value": False},
        ],
        ["guardrail", "value"],
    )

    build_shape_svg(enriched, OUT / "figures/svg/signed_error_shape_by_sensor.svg")
    build_bias_shape_svg(metrics, OUT / "figures/svg/bias_vs_shape_residual.svg")

    best = min(model_summary, key=lambda r: float(r["mean_group_rmse_K"]))
    summary = {
        "task": "TODO-THESIS-SCOREBOARD-SIGNED-ERROR-SHAPE-AND-MODEL-FORM-DISPATCH-2026-07-22",
        "decision": "signed_error_shape_executed_model_form_dispatch_updated_no_scoring_or_admission",
        "shape_metric_rows": len(metrics),
        "finite_sensor_rows": len(enriched),
        "local_shape_outlier_rows": min(40, len(outliers)),
        "model_level_rows": len(model_summary),
        "study_status_rows": len(studies),
        "board_dispatch_rows": len(board_rows),
        "best_current_legacy_numeric_model": best["model_form_id"],
        "best_current_mean_group_rmse_K": best["mean_group_rmse_K"],
        "m0_can_score_now": False,
        "s13_same_qoi_uq_ready": False,
        "passive_wall_test_section_candidate_released": False,
        "pressure_component_k_or_f6_admitted": False,
        "native_output_mutation": False,
        "registry_or_admission_mutation": False,
        "scheduler_action": False,
        "solver_sampler_harvest_uq_launched": False,
        "validation_holdout_external_new_scoring": False,
        "fitting_or_model_selection": False,
        "source_property_release": False,
        "coefficient_admission": False,
        "s11_s12_s13_s15_s6_trigger": False,
        "generated_index_refresh": False,
        "residual_absorbed_into_internal_nu": False,
    }
    write_json(OUT / "summary.json", summary)
    write_readme(summary)


if __name__ == "__main__":
    main()
