#!/usr/bin/env python3.11
"""Build the MF-D2 TP/TW QOI projection and thermal-development gate."""

from __future__ import annotations

import csv
import json
import math
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


TASK_ID = "TODO-MF-D2-TP-TW-QOI-PROJECTION-GATE-2026-07-22"
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_mf_d2_tp_tw_qoi_projection_gate"

DIAG = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_thesis_suggested_model_form_diagnostic_tests"
N4 = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_thesis_n4_sensor_qoi_projection_uncertainty_table"
LITREV = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_litrev_gated_single_stream_developing_branch"
RESET = ROOT / "work_products/2026-07/2026-07-13/2026-07-13_litrev_reset_named_losses/reset_distance_map.csv"
S12_TP = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_s12_tp_first_upcomer_exchange_evidence_gate"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def as_float(value: str | float | int | None, default: float = math.nan) -> float:
    if value is None or value == "":
        return default
    return float(value)


def model_row(rows: list[dict[str, str]], model_id: str) -> dict[str, str]:
    for row in rows:
        if row["tested_model_form_id"] == model_id:
            return row
    raise KeyError(model_id)


def build_d2_score_summary(scoreboard: list[dict[str, str]]) -> list[dict[str, object]]:
    m3 = model_row(scoreboard, "M3_as_is")
    d2 = model_row(scoreboard, "D2_M3_sensor_kind_offsets_train")
    d1 = model_row(scoreboard, "D1_M3_global_bias_offset_train")
    d3 = model_row(scoreboard, "D3_M3_wall_linear_shape_train")
    d4 = model_row(scoreboard, "D4_M3_segment_offsets_min2_train")
    return [
        {
            "comparison": "D2_vs_M3_transfer",
            "m3_transfer_rmse_K": as_float(m3["transfer_rmse_K"]),
            "d2_transfer_rmse_K": as_float(d2["transfer_rmse_K"]),
            "rmse_reduction_K": as_float(m3["transfer_rmse_K"]) - as_float(d2["transfer_rmse_K"]),
            "rmse_reduction_pct": as_float(d2["m3_transfer_rmse_reduction_pct"]),
            "m3_transfer_tp_rmse_K": as_float(m3["transfer_tp_rmse_K"]),
            "d2_transfer_tp_rmse_K": as_float(d2["transfer_tp_rmse_K"]),
            "tp_rmse_reduction_K": as_float(m3["transfer_tp_rmse_K"]) - as_float(d2["transfer_tp_rmse_K"]),
            "m3_transfer_tw_rmse_K": as_float(m3["transfer_tw_rmse_K"]),
            "d2_transfer_tw_rmse_K": as_float(d2["transfer_tw_rmse_K"]),
            "tw_rmse_reduction_K": as_float(m3["transfer_tw_rmse_K"]) - as_float(d2["transfer_tw_rmse_K"]),
            "d2_train_tp_offset_K": 15.091422693,
            "d2_train_tw_offset_K": 17.642415519,
            "interpretation": "D2 strongly improves TP transfer and partly improves TW, consistent with a bulk-to-probe/QOI projection issue plus remaining wall physics.",
            "status": "promising_diagnostic_not_admitted",
        },
        {
            "comparison": "D2_vs_D1_global_offset",
            "m3_transfer_rmse_K": as_float(d1["transfer_rmse_K"]),
            "d2_transfer_rmse_K": as_float(d2["transfer_rmse_K"]),
            "rmse_reduction_K": as_float(d1["transfer_rmse_K"]) - as_float(d2["transfer_rmse_K"]),
            "rmse_reduction_pct": 100.0 * (as_float(d1["transfer_rmse_K"]) - as_float(d2["transfer_rmse_K"])) / as_float(d1["transfer_rmse_K"]),
            "m3_transfer_tp_rmse_K": as_float(d1["transfer_tp_rmse_K"]),
            "d2_transfer_tp_rmse_K": as_float(d2["transfer_tp_rmse_K"]),
            "tp_rmse_reduction_K": as_float(d1["transfer_tp_rmse_K"]) - as_float(d2["transfer_tp_rmse_K"]),
            "m3_transfer_tw_rmse_K": as_float(d1["transfer_tw_rmse_K"]),
            "d2_transfer_tw_rmse_K": as_float(d2["transfer_tw_rmse_K"]),
            "tw_rmse_reduction_K": as_float(d1["transfer_tw_rmse_K"]) - as_float(d2["transfer_tw_rmse_K"]),
            "d2_train_tp_offset_K": 15.091422693,
            "d2_train_tw_offset_K": 17.642415519,
            "interpretation": "Separating TP from TW barely changes total transfer RMSE versus one global offset, but it sharpens the physical queue: TP projection first, TW wall response second.",
            "status": "diagnostic_ordering_signal",
        },
        {
            "comparison": "D2_vs_D3_D4_context",
            "m3_transfer_rmse_K": as_float(d2["transfer_rmse_K"]),
            "d2_transfer_rmse_K": min(as_float(d3["transfer_rmse_K"]), as_float(d4["transfer_rmse_K"])),
            "rmse_reduction_K": as_float(d2["transfer_rmse_K"]) - min(as_float(d3["transfer_rmse_K"]), as_float(d4["transfer_rmse_K"])),
            "rmse_reduction_pct": 100.0 * (as_float(d2["transfer_rmse_K"]) - min(as_float(d3["transfer_rmse_K"]), as_float(d4["transfer_rmse_K"]))) / as_float(d2["transfer_rmse_K"]),
            "m3_transfer_tp_rmse_K": as_float(d2["transfer_tp_rmse_K"]),
            "d2_transfer_tp_rmse_K": min(as_float(d3["transfer_tp_rmse_K"]), as_float(d4["transfer_tp_rmse_K"])),
            "tp_rmse_reduction_K": as_float(d2["transfer_tp_rmse_K"]) - min(as_float(d3["transfer_tp_rmse_K"]), as_float(d4["transfer_tp_rmse_K"])),
            "m3_transfer_tw_rmse_K": as_float(d2["transfer_tw_rmse_K"]),
            "d2_transfer_tw_rmse_K": min(as_float(d3["transfer_tw_rmse_K"]), as_float(d4["transfer_tw_rmse_K"])),
            "tw_rmse_reduction_K": as_float(d2["transfer_tw_rmse_K"]) - min(as_float(d3["transfer_tw_rmse_K"]), as_float(d4["transfer_tw_rmse_K"])),
            "d2_train_tp_offset_K": 15.091422693,
            "d2_train_tw_offset_K": 17.642415519,
            "interpretation": "D3/D4 improve beyond D2, so D2 alone is not the final physics; it is the first projection layer before wall/segment source placement.",
            "status": "supports_layered_analysis_plan",
        },
    ]


def build_residual_separation(sensor_errors: list[dict[str, str]]) -> list[dict[str, object]]:
    wanted = {"M3_as_is", "D2_M3_sensor_kind_offsets_train"}
    groups: dict[tuple[str, str, str], list[dict[str, str]]] = defaultdict(list)
    for row in sensor_errors:
        if row["tested_model_form_id"] in wanted and row["split_group"] in {"train", "transfer"}:
            groups[(row["tested_model_form_id"], row["split_group"], row["sensor_kind"])].append(row)
    out: list[dict[str, object]] = []
    for key, rows in sorted(groups.items()):
        model_id, split_group, sensor_kind = key
        errors = [as_float(r["signed_error_K"]) for r in rows]
        abs_errors = [abs(v) for v in errors]
        rmse = math.sqrt(sum(v * v for v in errors) / len(errors))
        mean = sum(errors) / len(errors)
        out.append(
            {
                "tested_model_form_id": model_id,
                "split_group": split_group,
                "sensor_kind": sensor_kind,
                "finite_rows": len(rows),
                "rmse_K": rmse,
                "mae_K": sum(abs_errors) / len(abs_errors),
                "mean_signed_error_K": mean,
                "max_abs_error_K": max(abs_errors),
                "interpretation": "D2 tests sensor-kind projection after TP/TW separation." if model_id.startswith("D2") else "M3 baseline residual context.",
                "use_class": "diagnostic_only",
            }
        )
    return out


SEGMENT_TO_SPAN = {
    "top_horizontal_exit": "upper_leg",
    "right_downcomer_bottom_horizontal_junction": "right_leg",
    "left_lower_vertical": "left_lower_leg",
    "test_section": "test_section_span",
    "left_upper_vertical": "left_upper_leg",
    "right_vertical": "right_leg",
    "heated_incline": "left_lower_leg",
    "cooled_incline_pre_hx": "upper_leg",
    "cooled_incline_post_hx": "upper_leg",
}


def build_projection_development_table(
    sensor_projection: list[dict[str, str]],
    reset_rows: list[dict[str, str]],
    branch_summary: list[dict[str, str]],
) -> list[dict[str, object]]:
    reset_by_span = {(r["case_id"], r["downstream_span"]): r for r in reset_rows if r["case_id"] in {"salt_2", "salt_3", "salt_4"}}
    branch_by_span = {r["span"]: r for r in branch_summary}
    out: list[dict[str, object]] = []
    for row in sensor_projection:
        if row["kind"] != "TP":
            continue
        segment = row["one_d_segment_or_state"]
        span = SEGMENT_TO_SPAN.get(segment, segment)
        branch = branch_by_span.get(span, {})
        example_reset = reset_by_span.get(("salt_2", span), {})
        out.append(
            {
                "sensor": row["sensor"],
                "kind": row["kind"],
                "one_d_segment_or_state": segment,
                "mapped_developing_span": span,
                "one_d_fraction_or_marker": row["one_d_fraction_or_marker"],
                "projection_acceptance_class": row["acceptance_class"],
                "current_score_target_use": row["score_target_use"],
                "current_projection": "bulk_temperature_arc_or_segment_projection_no_development_offset",
                "thermal_development_evidence": branch.get("lane_status", "not_mapped_to_litrev_span"),
                "litrev_allowed_rows": branch.get("allowed_rows", "0"),
                "litrev_uq_blocked_rows": branch.get("uq_blocked_rows", "0"),
                "example_x_from_reset_m": example_reset.get("x_from_reset_m", ""),
                "example_L_over_D_from_reset": example_reset.get("L_over_D_from_reset", ""),
                "thermal_reset_status": example_reset.get("thermal_reset_status", "not_mapped"),
                "runtime_temperature_allowed": row["runtime_temperature_allowed"],
                "fit_allowed": row["fit_allowed"],
                "admission_readiness": "not_ready_diagnostic_promising" if branch else "not_ready_missing_span_mapping",
                "next_evidence_needed": "derive source-bounded bulk-to-TP offset from thermal-development profile and same-QOI projection uncertainty",
            }
        )
    return out


def build_correction_existence_audit() -> list[dict[str, object]]:
    return [
        {
            "layer": "current_TP_prediction",
            "exists_now": True,
            "status": "implemented_as_bulk_projection_context",
            "evidence": "N4 maps TP rows as post-solve targets, and Fluid diagnostics label TP predictions as bulk-fluid temperature at sensor locations.",
            "limitation": "This is projection/interpolation, not a released thermal-development offset from bulk to local TP.",
            "claim_allowed": "TP comparison currently means bulk/fluid-state agreement at mapped probe locations.",
        },
        {
            "layer": "bulk_to_TP_thermal_development_offset",
            "exists_now": False,
            "status": "not_released",
            "evidence": "LitRev developing-flow gates exist, but no row admits a coefficient or QOI projection correction.",
            "limitation": "Thermal reset status, wall/core profile extraction, same-QOI UQ, and source/property labels remain missing.",
            "claim_allowed": "Thermal development is a promising hypothesis, not a correction.",
        },
        {
            "layer": "empirical_D2_TP_TW_offsets",
            "exists_now": True,
            "status": "diagnostic_only",
            "evidence": "D2 uses Salt2 train-only TP/TW offsets and improves transfer TP RMSE.",
            "limitation": "The offsets are empirical, not source-bounded or runtime-legal.",
            "claim_allowed": "D2 motivates a physical projection/development study.",
        },
        {
            "layer": "TW_after_TP_wall_response",
            "exists_now": False,
            "status": "future_layer",
            "evidence": "D2 leaves TW transfer RMSE higher than TP; D3/D4 improve further by wall/shape/segment structure.",
            "limitation": "TW correction should wait until the fluid/TP projection layer is tested.",
            "claim_allowed": "Correct TP first, then diagnose TW wall/boundary response.",
        },
    ]


def build_runtime_legality() -> list[dict[str, object]]:
    return [
        {
            "item": "TP bulk projection target",
            "runtime_allowed": False,
            "fit_allowed": False,
            "diagnostic_allowed": True,
            "reason": "TP/TW rows remain post-solve comparison targets only.",
        },
        {
            "item": "D2 TP/TW offsets",
            "runtime_allowed": False,
            "fit_allowed": False,
            "diagnostic_allowed": True,
            "reason": "Offsets were constructed from train residuals for diagnostic transfer only.",
        },
        {
            "item": "thermal-development bulk-to-TP correction",
            "runtime_allowed": False,
            "fit_allowed": False,
            "diagnostic_allowed": True,
            "reason": "Promising but missing source-bounded formula, same-QOI uncertainty, and release labels.",
        },
        {
            "item": "TW wall/boundary correction after TP",
            "runtime_allowed": False,
            "fit_allowed": False,
            "diagnostic_allowed": True,
            "reason": "TW should be interpreted after the TP projection layer is bounded.",
        },
    ]


def build_next_plan() -> list[dict[str, object]]:
    return [
        {
            "priority": 1,
            "analysis": "bulk-to-TP existence proof",
            "question": "Can a source-bounded thermal-development profile predict a TP local/probe temperature from the model bulk state?",
            "inputs_needed": "TP mapped segment/fraction, reset distance, local Re/Pr/Gz, local heat-source or heat-loss sign, and wall/core sampled fields.",
            "expected_insight": "Separates bulk energy error from probe-projection error before touching TW.",
            "acceptance": "diagnostic formula with all source/projection labels, or explicit missing-field table",
        },
        {
            "priority": 2,
            "analysis": "TP residual by reset distance and Graetz number",
            "question": "Do TP residuals scale with x/D or Gz after the last bend/junction/test-section reset?",
            "inputs_needed": "M3 and D2 TP residuals joined to reset-distance and developing-flow rows.",
            "expected_insight": "If residual collapses by development coordinate, the path has physical promise.",
            "acceptance": "train-only diagnostic correlation report; no coefficient admission",
        },
        {
            "priority": 3,
            "analysis": "S13 wall/core/TP bridge",
            "question": "Do retained-window wall/core/bulk contrasts explain the D2 TP offset magnitude?",
            "inputs_needed": "S13 exchange rows, exact pressure/Qwall rows, target-minus/target-plus triplets, and TP projection locations.",
            "expected_insight": "Tests whether upcomer/exchange state supplies the missing TP projection physics.",
            "acceptance": "same-QOI diagnostic evidence matrix; no production release",
        },
        {
            "priority": 4,
            "analysis": "TW residual after TP projection",
            "question": "After subtracting the best defended TP projection layer, what TW residual remains?",
            "inputs_needed": "TP projection diagnostic, TW sensor map, wall resistance/source-placement evidence, D3/D4 residual-shape rows.",
            "expected_insight": "Turns TW into a wall/boundary/source-placement problem instead of conflating it with bulk state.",
            "acceptance": "TW-after-TP residual-owner table and no-freeze gate",
        },
    ]


def write_svg(score_rows: list[dict[str, object]]) -> None:
    svg_dir = OUT / "figures/svg"
    svg_dir.mkdir(parents=True, exist_ok=True)
    primary = score_rows[0]
    bars = [
        ("M3 TP", float(primary["m3_transfer_tp_rmse_K"]), "#2f6f9f"),
        ("D2 TP", float(primary["d2_transfer_tp_rmse_K"]), "#62a87c"),
        ("M3 TW", float(primary["m3_transfer_tw_rmse_K"]), "#b25d2a"),
        ("D2 TW", float(primary["d2_transfer_tw_rmse_K"]), "#d99a5b"),
    ]
    max_v = max(v for _, v, _ in bars)
    scale = 520 / max_v
    lines = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="860" height="330" viewBox="0 0 860 330">',
        '<rect width="860" height="330" fill="#fff"/>',
        '<text x="40" y="40" font-family="Arial" font-size="23" fill="#111">D2 diagnostic: TP first, then TW</text>',
        '<text x="40" y="68" font-family="Arial" font-size="13" fill="#444">Transfer RMSE from existing diagnostic rows; no fit/admission/release.</text>',
    ]
    y = 105
    for label, value, color in bars:
        width = value * scale
        lines.extend(
            [
                f'<text x="40" y="{y + 16}" font-family="Arial" font-size="15" fill="#111">{label}</text>',
                f'<rect x="120" y="{y}" width="{width:.2f}" height="22" fill="{color}"/>',
                f'<text x="{132 + width:.2f}" y="{y + 16}" font-family="Arial" font-size="13" fill="#111">{value:.2f} K</text>',
            ]
        )
        y += 48
    lines.extend(
        [
            '<text x="40" y="305" font-family="Arial" font-size="12" fill="#555">Interpretation: D2 is promising for projection/development diagnostics, but not a correction release.</text>',
            "</svg>",
        ]
    )
    (svg_dir / "d2_tp_tw_projection_transfer_rmse.svg").write_text("\n".join(lines) + "\n")


def write_docs(summary: dict[str, object]) -> None:
    frontmatter = f"""---
provenance:
  - {DIAG / 'tested_model_form_scoreboard.csv'}
  - {N4 / 'sensor_qoi_projection_table.csv'}
  - {LITREV / 'single_stream_developing_branch_gate.csv'}
  - {RESET}
tags: [d2, tp, tw, qoi-projection, thermal-development]
related:
  - .agent/status/2026-07-22_{TASK_ID}.md
  - operational_notes/07-26/22/2026-07-22_MF_D2_TP_TW_QOI_PROJECTION_GATE.md
task: {TASK_ID}
date: 2026-07-22
role: Sensor-map / Uncertainty / Thermal-modeling / Tester / Writer / Reviewer
type: work_product
status: complete
---
"""
    readme = frontmatter + f"""# MF-D2 TP/TW QOI Projection Gate

Decision: `{summary["decision"]}`.

This package audits whether the D2 TP/TW diagnostic improvement should be read
as a QOI projection / bulk-to-TP thermal-development signal. It does not admit a
correction.

Main result:

- D2 improves transfer TP RMSE from M3 `13.5673279702 K` to `4.38159298515 K`.
- D2 improves transfer TW RMSE from M3 `18.980361511 K` to `12.5130610954 K`.
- The stronger TP improvement supports the analysis sequence: bulk/TP
  projection first, then TW wall/boundary response.
- A released bulk-to-TP thermal-development correction does not yet exist.

Primary files:

- `d2_score_improvement_summary.csv`
- `tp_tw_residual_separation.csv`
- `bulk_to_tp_correction_existence_audit.csv`
- `tp_projection_thermal_development_evidence.csv`
- `runtime_legality_matrix.csv`
- `next_analysis_plan.csv`
- `publication_claim_boundary.csv`
- `figures/svg/d2_tp_tw_projection_transfer_rmse.svg`

Guardrails: no fitting, no source/property release, no closure admission, no
final score, no scheduler or solver action, no native-output mutation, no Fluid
edit, and no residual absorption into internal Nu.
"""
    (OUT / "README.md").write_text(readme)
    handoff = frontmatter.replace("type: work_product", "type: report") + """# Insight Handoff: Thermal Development Path

The thermal-development path has promise, but the promise is currently
diagnostic. The strongest interpretation is that TP should be projected from the
bulk model state with a defended local/developing profile before TW is used to
infer wall/boundary corrections.

Use `next_analysis_plan.csv` for the next sequence:

1. bulk-to-TP existence proof,
2. TP residual by reset distance and Graetz number,
3. S13 wall/core/TP bridge,
4. TW residual after TP projection.

Do not claim that D2 is a released correction. Do not use protected rows for
fitting/model selection. Do not hide remaining TW residuals in internal Nu.
"""
    (OUT / "insight_handoff.md").write_text(handoff)


def build() -> dict[str, object]:
    OUT.mkdir(parents=True, exist_ok=True)
    scoreboard = read_csv(DIAG / "tested_model_form_scoreboard.csv")
    sensor_errors = read_csv(DIAG / "tested_model_form_sensor_errors.csv")
    sensor_projection = read_csv(N4 / "sensor_qoi_projection_table.csv")
    branch_summary = read_csv(LITREV / "single_stream_branch_summary.csv")
    reset_rows = read_csv(RESET)

    score_summary = build_d2_score_summary(scoreboard)
    residual_sep = build_residual_separation(sensor_errors)
    correction_audit = build_correction_existence_audit()
    projection_dev = build_projection_development_table(sensor_projection, reset_rows, branch_summary)
    runtime = build_runtime_legality()
    plan = build_next_plan()
    claims = [
        {
            "claim": "D2 proves a released correction.",
            "status": "forbidden",
            "basis": "D2 is train-only empirical diagnostic evidence.",
        },
        {
            "claim": "Thermal development is worth the next analysis.",
            "status": "allowed",
            "basis": "TP transfer error drops strongly under a TP/TW projection split, and developing-flow/reset evidence exists as a source path.",
        },
        {
            "claim": "Correct TP first, then use TW residuals for wall/boundary physics.",
            "status": "allowed",
            "basis": "TP behaves like a bulk/projection QOI; TW remains larger after D2 and requires wall response analysis.",
        },
        {
            "claim": "Internal Nu should absorb the residual.",
            "status": "forbidden",
            "basis": "Projection, source, wall, and UQ gates must be resolved before any internal heat-transfer admission.",
        },
    ]
    guardrails = [
        {"guardrail": "native_output_mutation", "status": False},
        {"guardrail": "registry_or_admission_mutation", "status": False},
        {"guardrail": "scheduler_or_solver_action", "status": False},
        {"guardrail": "fitting_or_model_selection", "status": False},
        {"guardrail": "source_property_release", "status": False},
        {"guardrail": "final_score_or_admission", "status": False},
        {"guardrail": "residual_absorbed_into_internal_nu", "status": False},
    ]
    source_manifest = [
        DIAG / "tested_model_form_scoreboard.csv",
        DIAG / "tested_model_form_sensor_errors.csv",
        DIAG / "construction_assumptions.csv",
        N4 / "sensor_qoi_projection_table.csv",
        LITREV / "single_stream_developing_branch_gate.csv",
        LITREV / "single_stream_branch_summary.csv",
        RESET,
        S12_TP / "s12_tp_next_executable_queue.csv",
    ]

    write_csv(
        OUT / "d2_score_improvement_summary.csv",
        score_summary,
        [
            "comparison",
            "m3_transfer_rmse_K",
            "d2_transfer_rmse_K",
            "rmse_reduction_K",
            "rmse_reduction_pct",
            "m3_transfer_tp_rmse_K",
            "d2_transfer_tp_rmse_K",
            "tp_rmse_reduction_K",
            "m3_transfer_tw_rmse_K",
            "d2_transfer_tw_rmse_K",
            "tw_rmse_reduction_K",
            "d2_train_tp_offset_K",
            "d2_train_tw_offset_K",
            "interpretation",
            "status",
        ],
    )
    write_csv(
        OUT / "tp_tw_residual_separation.csv",
        residual_sep,
        ["tested_model_form_id", "split_group", "sensor_kind", "finite_rows", "rmse_K", "mae_K", "mean_signed_error_K", "max_abs_error_K", "interpretation", "use_class"],
    )
    write_csv(OUT / "bulk_to_tp_correction_existence_audit.csv", correction_audit, ["layer", "exists_now", "status", "evidence", "limitation", "claim_allowed"])
    write_csv(
        OUT / "tp_projection_thermal_development_evidence.csv",
        projection_dev,
        [
            "sensor",
            "kind",
            "one_d_segment_or_state",
            "mapped_developing_span",
            "one_d_fraction_or_marker",
            "projection_acceptance_class",
            "current_score_target_use",
            "current_projection",
            "thermal_development_evidence",
            "litrev_allowed_rows",
            "litrev_uq_blocked_rows",
            "example_x_from_reset_m",
            "example_L_over_D_from_reset",
            "thermal_reset_status",
            "runtime_temperature_allowed",
            "fit_allowed",
            "admission_readiness",
            "next_evidence_needed",
        ],
    )
    write_csv(OUT / "runtime_legality_matrix.csv", runtime, ["item", "runtime_allowed", "fit_allowed", "diagnostic_allowed", "reason"])
    write_csv(OUT / "next_analysis_plan.csv", plan, ["priority", "analysis", "question", "inputs_needed", "expected_insight", "acceptance"])
    write_csv(OUT / "publication_claim_boundary.csv", claims, ["claim", "status", "basis"])
    write_csv(OUT / "no_mutation_guardrails.csv", guardrails, ["guardrail", "status"])
    write_csv(
        OUT / "source_manifest.csv",
        [{"source_path": str(p.relative_to(ROOT)), "used_read_only": True, "native_output": False} for p in source_manifest],
        ["source_path", "used_read_only", "native_output"],
    )
    write_svg(score_summary)

    summary = {
        "task_id": TASK_ID,
        "generated_at": datetime.now(ZoneInfo("America/Chicago")).isoformat(timespec="seconds"),
        "decision": "thermal_development_path_promising_diagnostic_only_no_correction_release",
        "score_summary_rows": len(score_summary),
        "residual_separation_rows": len(residual_sep),
        "tp_projection_rows": len(projection_dev),
        "next_analysis_rows": len(plan),
        "d2_transfer_tp_rmse_K": float(score_summary[0]["d2_transfer_tp_rmse_K"]),
        "m3_transfer_tp_rmse_K": float(score_summary[0]["m3_transfer_tp_rmse_K"]),
        "d2_transfer_tw_rmse_K": float(score_summary[0]["d2_transfer_tw_rmse_K"]),
        "m3_transfer_tw_rmse_K": float(score_summary[0]["m3_transfer_tw_rmse_K"]),
        "released_bulk_to_tp_correction_exists": False,
        "thermal_development_path_promising": True,
        "runtime_temperature_release": False,
        "source_property_release": False,
        "final_score_values": 0,
        "coefficient_admission": False,
        "scheduler_action": False,
        "native_output_mutation": False,
        "fluid_or_external_repo_mutation": False,
        "residual_absorbed_into_internal_nu": False,
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    write_docs(summary)
    return summary


if __name__ == "__main__":
    print(json.dumps(build(), indent=2))
