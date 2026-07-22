#!/usr/bin/env python3
"""Build a thesis-facing diagnostic test package for suggested model forms."""

from __future__ import annotations

import csv
import json
import math
import re
import time
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Callable


ROOT = Path(__file__).resolve().parents[2]
TASK = "TODO-THESIS-SUGGESTED-MODEL-FORM-DIAGNOSTIC-TESTS-2026-07-22"
OUT = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_thesis_suggested_model_form_diagnostic_tests"
SCOREBOARD = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_thesis_master_model_form_scoreboard"
DISPATCH = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_thesis_scoreboard_signed_error_shape_and_model_form_dispatch"
SIGNED_ERRORS = SCOREBOARD / "signed_sensor_errors.csv"
MASTER_SCOREBOARD = SCOREBOARD / "master_model_form_scoreboard.csv"
RECOMMENDED_FORMS = SCOREBOARD / "recommended_model_forms_to_try.csv"
ERROR_REDUCTION_TARGETS = DISPATCH / "model_form_error_reduction_targets.csv"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({name: row.get(name, "") for name in fieldnames})


def write_json(path: Path, data: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def fnum(value: object) -> float | None:
    if value in (None, ""):
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(result) or math.isinf(result):
        return None
    return result


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else float("nan")


def rmse(values: list[float]) -> float:
    return math.sqrt(sum(v * v for v in values) / len(values)) if values else float("nan")


def mae(values: list[float]) -> float:
    return mean([abs(v) for v in values]) if values else float("nan")


def finite(value: float) -> bool:
    return not (math.isnan(value) or math.isinf(value))


def fmt(value: object) -> object:
    if isinstance(value, float):
        if not finite(value):
            return ""
        return f"{value:.12g}"
    return value


def sensor_index(sensor: str) -> int:
    match = re.search(r"(\d+)$", sensor or "")
    return int(match.group(1)) if match else 999


def ols_intercept_slope(xs: list[float], ys: list[float]) -> tuple[float, float]:
    if len(xs) < 2:
        return mean(ys), 0.0
    xbar = mean(xs)
    ybar = mean(ys)
    denom = sum((x - xbar) ** 2 for x in xs)
    if denom == 0.0:
        return ybar, 0.0
    slope = sum((x - xbar) * (y - ybar) for x, y in zip(xs, ys)) / denom
    return ybar - slope * xbar, slope


def local_shape_rmse(errors: list[float]) -> float:
    if not errors:
        return float("nan")
    bias = mean(errors)
    return rmse([e - bias for e in errors])


def svg_escape(text: object) -> str:
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


@dataclass(frozen=True)
class FormSpec:
    tested_model_form_id: str
    base_model_form_id: str
    label: str
    model_form_family: str
    construction_formula: str
    fit_basis: str
    fitted_dof: int
    correction: Callable[[dict[str, str]], float]
    assumptions: str
    thesis_use: str
    next_decision: str


def train_rows(rows: list[dict[str, str]], model: str) -> list[dict[str, str]]:
    return [
        r
        for r in rows
        if r["model_form_id"] == model
        and r["finite_prediction"].lower() == "true"
        and r["split_or_use_class"] == "train_candidate"
    ]


def base_rows(rows: list[dict[str, str]], model: str) -> list[dict[str, str]]:
    return [
        r
        for r in rows
        if r["model_form_id"] == model and r["finite_prediction"].lower() == "true"
    ]


def build_forms(rows: list[dict[str, str]]) -> list[FormSpec]:
    m3_train = train_rows(rows, "M3")
    m3_train_errors = [fnum(r["signed_error_K"]) for r in m3_train]
    m3_train_errors = [e for e in m3_train_errors if e is not None]
    global_correction = -mean(m3_train_errors)

    by_kind: dict[str, list[float]] = defaultdict(list)
    by_segment: dict[str, list[float]] = defaultdict(list)
    tw_xs: list[float] = []
    tw_ys: list[float] = []
    for row in m3_train:
        err = fnum(row["signed_error_K"])
        if err is None:
            continue
        by_kind[row["sensor_kind"]].append(err)
        by_segment[row["prediction_source_segment"]].append(err)
        if row["sensor_kind"] == "TW":
            tw_xs.append(float(sensor_index(row["sensor"])))
            tw_ys.append(err)
    kind_corrections = {kind: -mean(vals) for kind, vals in by_kind.items()}
    segment_corrections = {
        segment: -mean(vals) for segment, vals in by_segment.items() if len(vals) >= 2
    }
    tw_intercept, tw_slope = ols_intercept_slope(tw_xs, tw_ys)
    tp_correction = kind_corrections.get("TP", global_correction)

    return [
        FormSpec(
            tested_model_form_id="M2_as_is",
            base_model_form_id="M2",
            label="M2 current scoreboard baseline",
            model_form_family="baseline",
            construction_formula="predicted_adjusted_K = M2_predicted_K",
            fit_basis="none",
            fitted_dof=0,
            correction=lambda _row: 0.0,
            assumptions="No new construction; included to preserve the old scoreboard reference point.",
            thesis_use="baseline comparator",
            next_decision="Use only as historical numeric context unless the M0 setup-only baseline is built.",
        ),
        FormSpec(
            tested_model_form_id="M3_as_is",
            base_model_form_id="M3",
            label="M3 current best legacy numeric comparator",
            model_form_family="baseline",
            construction_formula="predicted_adjusted_K = M3_predicted_K",
            fit_basis="none",
            fitted_dof=0,
            correction=lambda _row: 0.0,
            assumptions="No new construction; this is the best current legacy numeric comparator from the master scoreboard.",
            thesis_use="baseline comparator",
            next_decision="Keep as the reference for residual-shape tests.",
        ),
        FormSpec(
            tested_model_form_id="D1_M3_global_bias_offset_train",
            base_model_form_id="M3",
            label="M3 plus one Salt2-trained global temperature offset",
            model_form_family="passive_wall_or_setup_level_bias_probe",
            construction_formula=f"predicted_adjusted_K = M3_predicted_K + ({global_correction:.12g} K)",
            fit_basis="Salt2 train_candidate M3 finite TP/TW signed errors only",
            fitted_dof=1,
            correction=lambda _row, c=global_correction: c,
            assumptions="A single missing setup/passive heat term shifts all TP/TW targets by the same temperature increment.",
            thesis_use="diagnostic residual ownership test",
            next_decision="If transfer improves without large shape error, prioritize source-bounded passive wall/test-section repair.",
        ),
        FormSpec(
            tested_model_form_id="D2_M3_sensor_kind_offsets_train",
            base_model_form_id="M3",
            label="M3 plus Salt2-trained TP and TW offsets",
            model_form_family="qoi_projection_or_wall_fluid_split_probe",
            construction_formula=(
                "predicted_adjusted_K = M3_predicted_K + offset[sensor_kind], "
                f"offsets={json.dumps({k: round(v, 9) for k, v in sorted(kind_corrections.items())}, sort_keys=True)}"
            ),
            fit_basis="Salt2 train_candidate M3 finite signed errors grouped by TP/TW",
            fitted_dof=len(kind_corrections),
            correction=lambda row, c=kind_corrections, fallback=global_correction: c.get(row["sensor_kind"], fallback),
            assumptions="Bulk-fluid sensors and wall sensors may have different systematic projection or exchange errors.",
            thesis_use="diagnostic QOI split test",
            next_decision="If TP/TW offsets transfer, prioritize wall/core exchange and QOI projection uncertainty work.",
        ),
        FormSpec(
            tested_model_form_id="D3_M3_wall_linear_shape_train",
            base_model_form_id="M3",
            label="M3 plus Salt2-trained wall-index shape correction",
            model_form_family="thermal_shape_or_axial_mixing_probe",
            construction_formula=(
                "TW correction = -(a + b*sensor_index), TP correction = TP mean offset; "
                f"a={tw_intercept:.12g}, b={tw_slope:.12g}, TP_offset={tp_correction:.12g} K"
            ),
            fit_basis="Salt2 train_candidate M3 finite TW residuals fit by sensor index; TP uses TP mean residual",
            fitted_dof=3,
            correction=lambda row, a=tw_intercept, b=tw_slope, tp=tp_correction: (
                -(a + b * sensor_index(row["sensor"])) if row["sensor_kind"] == "TW" else tp
            ),
            assumptions="Wall residual has a repeatable axial/sensor-order component; TP residual is treated as a level offset.",
            thesis_use="diagnostic thermal-shape test",
            next_decision="If transfer improves local shape, prioritize S12 thermal-shape and axial-mixing studies.",
        ),
        FormSpec(
            tested_model_form_id="D4_M3_segment_offsets_min2_train",
            base_model_form_id="M3",
            label="M3 plus Salt2-trained segment offsets with min two sensors",
            model_form_family="segment_source_placement_probe",
            construction_formula=(
                "predicted_adjusted_K = M3_predicted_K + offset[prediction_source_segment] "
                f"for train segments with n>=2 else global offset; offsets={json.dumps({k: round(v, 9) for k, v in sorted(segment_corrections.items())}, sort_keys=True)}"
            ),
            fit_basis="Salt2 train_candidate M3 finite signed errors grouped by prediction_source_segment, n>=2",
            fitted_dof=len(segment_corrections) + 1,
            correction=lambda row, c=segment_corrections, fallback=global_correction: c.get(
                row["prediction_source_segment"], fallback
            ),
            assumptions="Missing thermal/source placement error is local to repeated loop segments and transfers by segment label.",
            thesis_use="diagnostic segment/local-source test",
            next_decision="If transfer improves a subset but harms another, prioritize source-bounded local heat-path ownership before fitting.",
        ),
    ]


def score_form(rows: list[dict[str, str]], spec: FormSpec) -> list[dict[str, object]]:
    scored: list[dict[str, object]] = []
    for row in base_rows(rows, spec.base_model_form_id):
        predicted = fnum(row["predicted_K"])
        target = fnum(row["target_K"])
        if predicted is None or target is None:
            continue
        correction = spec.correction(row)
        adjusted = predicted + correction
        error = adjusted - target
        percent = 100.0 * error / target if target != 0.0 else float("nan")
        split_group = "train" if row["split_or_use_class"] == "train_candidate" else "transfer"
        scored.append(
            {
                "tested_model_form_id": spec.tested_model_form_id,
                "base_model_form_id": spec.base_model_form_id,
                "model_form_label": spec.label,
                "model_form_family": spec.model_form_family,
                "case_id": row["case_id"],
                "split_or_use_class": row["split_or_use_class"],
                "split_group": split_group,
                "sensor": row["sensor"],
                "sensor_kind": row["sensor_kind"],
                "prediction_source_segment": row["prediction_source_segment"],
                "base_predicted_K": predicted,
                "correction_K": correction,
                "adjusted_predicted_K": adjusted,
                "target_K": target,
                "signed_error_K": error,
                "signed_error_percent_of_target": percent,
                "absolute_error_K": abs(error),
                "uses_train_targets_for_fit": spec.fitted_dof > 0,
                "uses_transfer_targets_for_fit": False,
                "admission_status": "diagnostic_not_admitted",
                "source_path": str(SIGNED_ERRORS.relative_to(ROOT)),
            }
        )
    return scored


def metrics_for(rows: list[dict[str, object]], group: str | None = None, sensor_kind: str | None = None) -> dict[str, float | int]:
    filtered = rows
    if group is not None:
        filtered = [r for r in filtered if r["split_group"] == group]
    if sensor_kind is not None:
        filtered = [r for r in filtered if r["sensor_kind"] == sensor_kind]
    errors = [float(r["signed_error_K"]) for r in filtered]
    pcts = [float(r["signed_error_percent_of_target"]) for r in filtered]
    return {
        "rows": len(errors),
        "rmse_K": rmse(errors),
        "mae_K": mae(errors),
        "mean_signed_error_K": mean(errors),
        "mean_signed_error_percent": mean(pcts),
        "local_shape_rmse_after_bias_K": local_shape_rmse(errors),
        "max_abs_error_K": max([abs(e) for e in errors], default=float("nan")),
    }


def build_scoreboard(scored_by_form: dict[str, list[dict[str, object]]], forms: list[FormSpec]) -> list[dict[str, object]]:
    m3_transfer = metrics_for(scored_by_form["M3_as_is"], group="transfer")["rmse_K"]
    scoreboard: list[dict[str, object]] = []
    for spec in forms:
        scored = scored_by_form[spec.tested_model_form_id]
        train = metrics_for(scored, group="train")
        transfer = metrics_for(scored, group="transfer")
        all_rows = metrics_for(scored)
        val = metrics_for([r for r in scored if r["split_or_use_class"] == "validation_candidate"])
        holdout = metrics_for([r for r in scored if r["split_or_use_class"] == "holdout_candidate"])
        transfer_tp = metrics_for(scored, group="transfer", sensor_kind="TP")
        transfer_tw = metrics_for(scored, group="transfer", sensor_kind="TW")
        delta = float(transfer["rmse_K"]) - float(m3_transfer)
        reduction = -100.0 * delta / float(m3_transfer) if m3_transfer else float("nan")
        scoreboard.append(
            {
                "tested_model_form_id": spec.tested_model_form_id,
                "base_model_form_id": spec.base_model_form_id,
                "model_form_label": spec.label,
                "model_form_family": spec.model_form_family,
                "fit_basis": spec.fit_basis,
                "fitted_dof": spec.fitted_dof,
                "uses_train_targets_for_fit": spec.fitted_dof > 0,
                "uses_transfer_targets_for_fit": False,
                "train_rows": train["rows"],
                "transfer_rows": transfer["rows"],
                "all_rows": all_rows["rows"],
                "train_rmse_K": train["rmse_K"],
                "train_mae_K": train["mae_K"],
                "train_mean_signed_error_K": train["mean_signed_error_K"],
                "transfer_rmse_K": transfer["rmse_K"],
                "transfer_mae_K": transfer["mae_K"],
                "transfer_mean_signed_error_K": transfer["mean_signed_error_K"],
                "transfer_mean_signed_error_percent": transfer["mean_signed_error_percent"],
                "transfer_local_shape_rmse_after_bias_K": transfer["local_shape_rmse_after_bias_K"],
                "transfer_max_abs_error_K": transfer["max_abs_error_K"],
                "transfer_tp_rmse_K": transfer_tp["rmse_K"],
                "transfer_tw_rmse_K": transfer_tw["rmse_K"],
                "validation_candidate_rmse_K": val["rmse_K"],
                "holdout_candidate_rmse_K": holdout["rmse_K"],
                "all_rmse_K": all_rows["rmse_K"],
                "m3_transfer_rmse_delta_K": delta,
                "m3_transfer_rmse_reduction_pct": reduction,
                "construction_formula": spec.construction_formula,
                "assumptions": spec.assumptions,
                "thesis_use": spec.thesis_use,
                "next_decision": spec.next_decision,
                "admission_status": "diagnostic_not_admitted",
            }
        )
    return scoreboard


def build_assumptions(forms: list[FormSpec]) -> list[dict[str, object]]:
    return [
        {
            "tested_model_form_id": spec.tested_model_form_id,
            "geometry_or_physics_class": spec.model_form_family,
            "construction_formula": spec.construction_formula,
            "fit_basis": spec.fit_basis,
            "fitted_dof": spec.fitted_dof,
            "allowed_inputs": "existing master signed_sensor_errors.csv finite rows; Salt2 train_candidate residuals for fitted diagnostic forms",
            "forbidden_inputs": "Salt3/Salt4 targets for fitting; validation/holdout tuning; CFD native-field mutation; source/property release; protected final scoring; solver/sampler/UQ launches",
            "split_contract": "fit on Salt2 train_candidate only, report Salt3 validation_candidate and Salt4 holdout_candidate as transfer diagnostics only",
            "pressure_velocity_basis_requirements": "none for these thermal TP/TW residual tests; pressure/mdot coupling remains a separate diagnostic row",
            "missing_fields": "no independent source-bounded Q_wall/passive wall term, no same-QOI UQ, no M0 setup-only baseline, no source/property release",
            "admission_status": "diagnostic_not_admitted",
            "assumptions": spec.assumptions,
        }
        for spec in forms
    ]


def build_append(scoreboard: list[dict[str, object]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for row in scoreboard:
        rows.append(
            {
                "master_scoreboard_action": "append_candidate_addendum_not_inplace_mutation",
                "candidate_id": row["tested_model_form_id"],
                "model_form_family": row["model_form_family"],
                "qoi": "TP/TW signed temperature errors",
                "split_contract": "Salt2 train fit where fitted; Salt3/Salt4 transfer report only",
                "construction_summary": row["construction_formula"],
                "train_rmse_K": row["train_rmse_K"],
                "transfer_rmse_K": row["transfer_rmse_K"],
                "transfer_mean_signed_error_K": row["transfer_mean_signed_error_K"],
                "transfer_local_shape_rmse_after_bias_K": row["transfer_local_shape_rmse_after_bias_K"],
                "transfer_tp_rmse_K": row["transfer_tp_rmse_K"],
                "transfer_tw_rmse_K": row["transfer_tw_rmse_K"],
                "admission_status": row["admission_status"],
                "board_task_to_claim_if_promising": suggested_board_task(str(row["tested_model_form_id"])),
            }
        )
    return rows


def suggested_board_task(candidate_id: str) -> str:
    if candidate_id == "D1_M3_global_bias_offset_train":
        return "TODO-M2-PASSIVE-WALL-TEST-SECTION-SOURCE-BOUNDED-REPAIR-GATE-2026-07-22"
    if candidate_id == "D2_M3_sensor_kind_offsets_train":
        return "TODO-S13/S12 wall-core exchange or QOI projection UQ row after active rows close"
    if candidate_id == "D3_M3_wall_linear_shape_train":
        return "TODO-S12-TP-FIRST-UPCOMER-EXCHANGE-EVIDENCE-GATE-2026-07-22 after active gate output"
    if candidate_id == "D4_M3_segment_offsets_min2_train":
        return "TODO-M2-PASSIVE-WALL-TEST-SECTION-SOURCE-BOUNDED-REPAIR-GATE-2026-07-22"
    return "baseline_no_new_row"


def make_bar_svg(scoreboard: list[dict[str, object]], path: Path) -> None:
    rows = sorted(scoreboard, key=lambda r: float(r["transfer_rmse_K"]))
    width = 980
    row_h = 34
    left = 300
    top = 50
    chart_w = 540
    height = top + row_h * len(rows) + 60
    max_v = max(float(r["transfer_rmse_K"]) for r in rows)
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        '<text x="24" y="28" font-family="Arial" font-size="18" font-weight="700">Transfer RMSE for tested model forms</text>',
        '<text x="24" y="46" font-family="Arial" font-size="12" fill="#555">Salt3/Salt4 transfer rows; fitted forms use Salt2 train residuals only</text>',
    ]
    for i, row in enumerate(rows):
        y = top + i * row_h
        value = float(row["transfer_rmse_K"])
        bar_w = chart_w * value / max_v if max_v else 0.0
        color = "#2f6f73" if row["tested_model_form_id"] != "M3_as_is" else "#a6423a"
        parts.append(f'<text x="24" y="{y + 20}" font-family="Arial" font-size="12">{svg_escape(row["tested_model_form_id"])}</text>')
        parts.append(f'<rect x="{left}" y="{y + 6}" width="{bar_w:.2f}" height="20" fill="{color}"/>')
        parts.append(f'<text x="{left + bar_w + 8:.2f}" y="{y + 21}" font-family="Arial" font-size="12">{value:.2f} K</text>')
    parts.append("</svg>\n")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(parts))


def make_sensor_svg(sensor_rows: list[dict[str, object]], best_id: str, path: Path) -> None:
    selected = [
        r
        for r in sensor_rows
        if r["tested_model_form_id"] in {"M3_as_is", best_id} and r["split_group"] == "transfer"
    ]
    selected.sort(key=lambda r: (str(r["case_id"]), str(r["sensor_kind"]), sensor_index(str(r["sensor"])), str(r["tested_model_form_id"])))
    width = 1180
    row_h = 18
    left = 250
    zero = 610
    scale = 3.0
    height = 60 + row_h * len(selected) + 30
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        '<text x="24" y="28" font-family="Arial" font-size="18" font-weight="700">Signed transfer errors: M3 baseline vs best diagnostic form</text>',
        f'<line x1="{zero}" x2="{zero}" y1="48" y2="{height - 18}" stroke="#333" stroke-width="1"/>',
        '<text x="620" y="48" font-family="Arial" font-size="11" fill="#555">hot / positive</text>',
        '<text x="500" y="48" font-family="Arial" font-size="11" fill="#555">cold / negative</text>',
    ]
    for i, row in enumerate(selected):
        y = 60 + i * row_h
        err = float(row["signed_error_K"])
        x = zero if err >= 0 else zero + err * scale
        bar_w = abs(err) * scale
        color = "#a6423a" if row["tested_model_form_id"] == "M3_as_is" else "#2f6f73"
        label = f'{row["case_id"]} {row["sensor"]} {row["tested_model_form_id"]}'
        parts.append(f'<text x="24" y="{y + 11}" font-family="Arial" font-size="10">{svg_escape(label)}</text>')
        parts.append(f'<rect x="{x:.2f}" y="{y}" width="{bar_w:.2f}" height="12" fill="{color}"/>')
        tx = x - 46 if err < 0 else x + bar_w + 5
        parts.append(f'<text x="{tx:.2f}" y="{y + 10}" font-family="Arial" font-size="10">{err:+.1f} K</text>')
    parts.append("</svg>\n")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(parts))


def write_readme(summary: dict[str, object], best: dict[str, object]) -> None:
    readme = f"""---
provenance:
  - {SIGNED_ERRORS.relative_to(ROOT)}
  - {MASTER_SCOREBOARD.relative_to(ROOT)}
  - {RECOMMENDED_FORMS.relative_to(ROOT)}
  - {ERROR_REDUCTION_TARGETS.relative_to(ROOT)}
tags: [thesis, model-form-scoreboard, diagnostic-tests, signed-errors]
related:
  - .agent/status/2026-07-22_{TASK}.md
  - .agent/journal/2026-07-22/thesis-suggested-model-form-diagnostic-tests.md
task: {TASK}
date: 2026-07-22
role: Implementer / Tester / Writer / Reviewer
type: work_product
status: complete
---
# Suggested Model-Form Diagnostic Tests

This package tests selected suggested model forms as a scoreboard addendum. It
does not modify the canonical master scoreboard in place. All fitted diagnostic
forms use only Salt2 `train_candidate` residuals from the master
`signed_sensor_errors.csv`; Salt3 and Salt4 are reported as transfer diagnostics
only.

## Terms

- MF: model form, meaning a proposed 1D closure or correction family.
- M2: current legacy numeric model form after the major thermal-boundary and
  segment-model improvement.
- M3: current best legacy numeric comparator in the master scoreboard.
- TP: fluid thermocouple or bulk-temperature probe row.
- TW: wall thermocouple row.
- Salt2: train-candidate case used here to construct empirical diagnostics.
- Salt3/Salt4: transfer rows used only to report whether a diagnostic shape
  transfers; no fitting uses these targets.
- Signed error: `predicted_K - target_K`. Negative means the model is cold.
- RMSE: root mean square signed error magnitude in K.
- MAE: mean absolute error in K.
- Bias: mean signed error. Local shape RMSE removes that mean first.
- Source-bounded: a candidate has an independent physical/source envelope,
  not just an empirical residual correction.
- Admission: permission to use a model form as accepted evidence. Every fitted
  row here is `diagnostic_not_admitted`.

## Tested Forms

- `M2_as_is`: existing M2 finite TP/TW predictions.
- `M3_as_is`: existing M3 finite TP/TW predictions.
- `D1_M3_global_bias_offset_train`: one Salt2-trained global temperature offset.
- `D2_M3_sensor_kind_offsets_train`: separate Salt2-trained TP and TW offsets.
- `D3_M3_wall_linear_shape_train`: Salt2-trained TW sensor-index line plus TP
  mean offset.
- `D4_M3_segment_offsets_min2_train`: Salt2-trained segment offsets where at
  least two finite train sensors support the segment, with global fallback.

## Result

- tested forms: `{summary["tested_forms"]}`
- scored sensor rows: `{summary["scored_sensor_rows"]}`
- best transfer diagnostic: `{summary["best_transfer_diagnostic_id"]}`
- best transfer RMSE: `{float(best["transfer_rmse_K"]):.6g} K`
- M3 as-is transfer RMSE: `{summary["m3_transfer_rmse_K"]:.6g} K`
- total runtime: `{summary["total_runtime_s"]:.6g} s`

The best empirical transfer test is useful as a research-priority signal only.
It is not a source-bounded repair and should not be admitted or used for final
protected scoring.

## Outputs

- `tested_model_form_scoreboard.csv`
- `tested_model_form_sensor_errors.csv`
- `construction_assumptions.csv`
- `model_form_scoreboard_append.csv`
- `runtime_audit.csv`
- `source_manifest.csv`
- `no_mutation_guardrails.csv`
- `summary.json`
- `figures/svg/tested_model_form_transfer_rmse.svg`
- `figures/svg/transfer_signed_sensor_errors_best_vs_m3.svg`
"""
    (OUT / "README.md").write_text(readme)


def main() -> None:
    total_start = time.perf_counter()
    phase_starts: dict[str, float] = {}
    timings: dict[str, float] = {}

    phase_starts["load_inputs"] = time.perf_counter()
    rows = read_csv(SIGNED_ERRORS)
    timings["load_inputs_s"] = time.perf_counter() - phase_starts["load_inputs"]

    phase_starts["construct_forms"] = time.perf_counter()
    forms = build_forms(rows)
    timings["construct_forms_s"] = time.perf_counter() - phase_starts["construct_forms"]

    phase_starts["score_forms"] = time.perf_counter()
    scored_by_form = {spec.tested_model_form_id: score_form(rows, spec) for spec in forms}
    sensor_rows = [row for spec in forms for row in scored_by_form[spec.tested_model_form_id]]
    scoreboard = build_scoreboard(scored_by_form, forms)
    best = min(
        [r for r in scoreboard if str(r["tested_model_form_id"]).startswith("D")],
        key=lambda r: float(r["transfer_rmse_K"]),
    )
    timings["score_forms_s"] = time.perf_counter() - phase_starts["score_forms"]

    phase_starts["write_outputs"] = time.perf_counter()
    scoreboard_fields = [
        "tested_model_form_id",
        "base_model_form_id",
        "model_form_label",
        "model_form_family",
        "fit_basis",
        "fitted_dof",
        "uses_train_targets_for_fit",
        "uses_transfer_targets_for_fit",
        "train_rows",
        "transfer_rows",
        "all_rows",
        "train_rmse_K",
        "train_mae_K",
        "train_mean_signed_error_K",
        "transfer_rmse_K",
        "transfer_mae_K",
        "transfer_mean_signed_error_K",
        "transfer_mean_signed_error_percent",
        "transfer_local_shape_rmse_after_bias_K",
        "transfer_max_abs_error_K",
        "transfer_tp_rmse_K",
        "transfer_tw_rmse_K",
        "validation_candidate_rmse_K",
        "holdout_candidate_rmse_K",
        "all_rmse_K",
        "m3_transfer_rmse_delta_K",
        "m3_transfer_rmse_reduction_pct",
        "construction_formula",
        "assumptions",
        "thesis_use",
        "next_decision",
        "admission_status",
    ]
    sensor_fields = [
        "tested_model_form_id",
        "base_model_form_id",
        "model_form_label",
        "model_form_family",
        "case_id",
        "split_or_use_class",
        "split_group",
        "sensor",
        "sensor_kind",
        "prediction_source_segment",
        "base_predicted_K",
        "correction_K",
        "adjusted_predicted_K",
        "target_K",
        "signed_error_K",
        "signed_error_percent_of_target",
        "absolute_error_K",
        "uses_train_targets_for_fit",
        "uses_transfer_targets_for_fit",
        "admission_status",
        "source_path",
    ]
    assumptions_fields = [
        "tested_model_form_id",
        "geometry_or_physics_class",
        "construction_formula",
        "fit_basis",
        "fitted_dof",
        "allowed_inputs",
        "forbidden_inputs",
        "split_contract",
        "pressure_velocity_basis_requirements",
        "missing_fields",
        "admission_status",
        "assumptions",
    ]
    append_fields = [
        "master_scoreboard_action",
        "candidate_id",
        "model_form_family",
        "qoi",
        "split_contract",
        "construction_summary",
        "train_rmse_K",
        "transfer_rmse_K",
        "transfer_mean_signed_error_K",
        "transfer_local_shape_rmse_after_bias_K",
        "transfer_tp_rmse_K",
        "transfer_tw_rmse_K",
        "admission_status",
        "board_task_to_claim_if_promising",
    ]

    write_csv(OUT / "tested_model_form_scoreboard.csv", [{k: fmt(v) for k, v in r.items()} for r in scoreboard], scoreboard_fields)
    write_csv(OUT / "tested_model_form_sensor_errors.csv", [{k: fmt(v) for k, v in r.items()} for r in sensor_rows], sensor_fields)
    write_csv(OUT / "construction_assumptions.csv", build_assumptions(forms), assumptions_fields)
    write_csv(OUT / "model_form_scoreboard_append.csv", [{k: fmt(v) for k, v in r.items()} for r in build_append(scoreboard)], append_fields)
    write_csv(
        OUT / "source_manifest.csv",
        [
            {"path": str(SIGNED_ERRORS.relative_to(ROOT)), "used": True, "mutation_status": "read_only"},
            {"path": str(MASTER_SCOREBOARD.relative_to(ROOT)), "used": MASTER_SCOREBOARD.exists(), "mutation_status": "read_only"},
            {"path": str(RECOMMENDED_FORMS.relative_to(ROOT)), "used": RECOMMENDED_FORMS.exists(), "mutation_status": "read_only"},
            {"path": str(ERROR_REDUCTION_TARGETS.relative_to(ROOT)), "used": ERROR_REDUCTION_TARGETS.exists(), "mutation_status": "read_only"},
        ],
        ["path", "used", "mutation_status"],
    )
    write_csv(
        OUT / "no_mutation_guardrails.csv",
        [
            {"guardrail": "native CFD/OpenFOAM outputs", "mutation": False},
            {"guardrail": "registry/admission state", "mutation": False},
            {"guardrail": "scheduler/solver/sampler/UQ", "mutation": False},
            {"guardrail": "Fluid or external source trees", "mutation": False},
            {"guardrail": "thesis current/LaTeX files", "mutation": False},
            {"guardrail": "canonical master scoreboard in-place edit", "mutation": False},
            {"guardrail": "validation/holdout target use for fitting", "mutation": False},
        ],
        ["guardrail", "mutation"],
    )
    make_bar_svg(scoreboard, OUT / "figures/svg/tested_model_form_transfer_rmse.svg")
    make_sensor_svg(sensor_rows, str(best["tested_model_form_id"]), OUT / "figures/svg/transfer_signed_sensor_errors_best_vs_m3.svg")
    timings["write_outputs_s"] = time.perf_counter() - phase_starts["write_outputs"]
    total_runtime = time.perf_counter() - total_start
    timings["total_runtime_s"] = total_runtime

    m3_row = next(r for r in scoreboard if r["tested_model_form_id"] == "M3_as_is")
    summary = {
        "task": TASK,
        "decision": "diagnostic_model_form_tests_executed_scoreboard_addendum_only",
        "input_signed_error_rows": len(rows),
        "finite_input_rows": sum(1 for r in rows if r.get("finite_prediction", "").lower() == "true"),
        "tested_forms": len(forms),
        "scored_sensor_rows": len(sensor_rows),
        "train_rows_per_m3_form": len(train_rows(rows, "M3")),
        "transfer_rows_per_m3_form": len([r for r in base_rows(rows, "M3") if r["split_or_use_class"] != "train_candidate"]),
        "m3_transfer_rmse_K": float(m3_row["transfer_rmse_K"]),
        "best_transfer_diagnostic_id": best["tested_model_form_id"],
        "best_transfer_rmse_K": float(best["transfer_rmse_K"]),
        "best_transfer_rmse_delta_vs_m3_K": float(best["m3_transfer_rmse_delta_K"]),
        "best_transfer_rmse_reduction_vs_m3_pct": float(best["m3_transfer_rmse_reduction_pct"]),
        "best_transfer_mean_signed_error_K": float(best["transfer_mean_signed_error_K"]),
        "admission_status": "diagnostic_not_admitted",
        "uses_transfer_targets_for_fit": False,
        "total_runtime_s": total_runtime,
        "phase_runtime_s": timings,
    }
    write_json(OUT / "summary.json", summary)
    write_csv(
        OUT / "runtime_audit.csv",
        [{"phase": key.removesuffix("_s"), "runtime_s": f"{value:.12g}"} for key, value in timings.items()],
        ["phase", "runtime_s"],
    )
    write_readme(summary, best)


if __name__ == "__main__":
    main()
