#!/usr/bin/env python3
"""Build a sensor projection-operator contract for TP/TW observations."""

from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TASK_ID = "TODO-1D-SENSOR-PROJECTION-OPERATOR-TP-TW-WALL-BULK-2026-07-22"
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_1d_sensor_projection_operator_tp_tw_wall_bulk"

N4 = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_thesis_n4_sensor_qoi_projection_uncertainty_table"
D2 = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_mf_d2_tp_tw_qoi_projection_gate"
ELEV = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_thesis_figtable_model_form_and_blocked_scorecard_panels"
SHAPE = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_thesis_scoreboard_signed_error_shape_and_model_form_dispatch"
MASTER = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_thesis_master_model_form_scoreboard"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def read_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def dump_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def operator_for(row: dict[str, str]) -> tuple[str, str, str, str]:
    sensor = row["sensor"]
    kind = row["kind"]
    segment = row["one_d_segment_or_state"]
    marker = row["one_d_fraction_or_marker"]
    if row["acceptance_class"] == "excluded":
        return (
            "excluded_no_projection",
            "not_emitted",
            "no operator because active-HX shell state is absent",
            "excluded from score and runtime release",
        )
    if kind == "TP":
        return (
            "bulk_fluid_projection",
            "T_bulk_1d",
            f"T_hat_{sensor} = P_bulk(sensor={sensor}, segment={segment}, marker={marker})[T_bulk_1d]",
            "bulk-to-TP thermal-development offset not released",
        )
    return (
        "wall_state_projection",
        "T_wall_1d",
        f"T_hat_{sensor} = P_wall(sensor={sensor}, segment={segment}, marker={marker})[T_wall_1d]",
        "TW correction should follow TP/bulk projection release",
    )


def build_operator_rows() -> list[dict[str, Any]]:
    n4_rows = read_csv(N4 / "sensor_qoi_projection_table.csv")
    caveats = {row["sensor"]: row for row in read_csv(N4 / "sensor_uncertainty_caveat_table.csv")}
    runtime = {row["sensor"]: row for row in read_csv(N4 / "sensor_runtime_input_audit.csv")}
    elev_rows = read_csv(ELEV / "tp_tw_temperature_elevation_panel_points.csv")
    elev_by_sensor = {}
    for row in elev_rows:
        if row["case_id"] == "salt_2":
            elev_by_sensor.setdefault(row["sensor_id"], row)

    rows: list[dict[str, Any]] = []
    for row in n4_rows:
        op_type, state, equation, release_status = operator_for(row)
        elev = elev_by_sensor.get(row["sensor"], {})
        run = runtime[row["sensor"]]
        caveat = caveats[row["sensor"]]
        rows.append(
            {
                "sensor": row["sensor"],
                "sensor_kind": row["kind"],
                "acceptance_class": row["acceptance_class"],
                "projection_operator": op_type,
                "one_d_state_source": state,
                "one_d_segment_or_state": row["one_d_segment_or_state"],
                "one_d_fraction_or_marker": row["one_d_fraction_or_marker"],
                "elevation_m": elev.get("elevation_m", ""),
                "coordinate_claim_level": caveat["coordinate_claim_level"],
                "score_target_use": row["score_target_use"],
                "runtime_temperature_allowed": run["runtime_temperature_allowed"],
                "fit_allowed": run["fit_allowed"],
                "model_selection_allowed": run["model_selection_allowed"],
                "projection_equation": equation,
                "release_status": release_status,
                "uncertainty_caveat": row["uncertainty_caveat"],
                "publication_effect": caveat["publication_effect"],
            }
        )
    return rows


def write_svg(rows: list[dict[str, Any]]) -> None:
    path = OUT / "figures/svg/1d_sensor_projection_operator_map.svg"
    path.parent.mkdir(parents=True, exist_ok=True)
    groups = Counter(row["projection_operator"] for row in rows)
    width, height = 900, 420
    colors = {
        "bulk_fluid_projection": "#2d6f9f",
        "wall_state_projection": "#b96b25",
        "excluded_no_projection": "#777777",
    }
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        '<text x="32" y="42" font-family="Arial, sans-serif" font-size="23" font-weight="700" fill="#1f252b">1D Sensor Projection Operator</text>',
        '<text x="32" y="68" font-family="Arial, sans-serif" font-size="14" fill="#4b5663">Maps 1D bulk and wall states to TP/TW observations for score-only comparison.</text>',
    ]
    x = 55
    for label, count in groups.items():
        color = colors.get(label, "#555555")
        parts.extend(
            [
                f'<rect x="{x}" y="108" width="220" height="96" rx="4" fill="#f7f8f9" stroke="#d7dde2"/>',
                f'<circle cx="{x + 28}" cy="140" r="11" fill="{color}"/>',
                f'<text x="{x + 48}" y="146" font-family="Arial, sans-serif" font-size="14" font-weight="700" fill="#1f252b">{label}</text>',
                f'<text x="{x + 48}" y="174" font-family="Arial, sans-serif" font-size="26" font-weight="700" fill="{color}">{count}</text>',
            ]
        )
        x += 270
    notes = [
        "TP: project from 1D bulk/fluid temperature at mapped segment/fraction.",
        "TW: project from 1D wall temperature at mapped segment/fraction.",
        "TW10: excluded until active-HX shell state is emitted.",
        "All observed TP/TW temperatures remain score-only; no runtime temperature release.",
    ]
    for idx, note in enumerate(notes):
        y = 255 + idx * 34
        parts.extend(
            [
                f'<circle cx="48" cy="{y - 5}" r="5" fill="#2f3b45"/>',
                f'<text x="65" y="{y}" font-family="Arial, sans-serif" font-size="15" fill="#2f3b45">{note}</text>',
            ]
        )
    parts.append("</svg>\n")
    path.write_text("\n".join(parts), encoding="utf-8")


def build() -> dict[str, Any]:
    OUT.mkdir(parents=True, exist_ok=True)
    rows = build_operator_rows()
    d2_summary = read_json(D2 / "summary.json")
    d2_audit = read_csv(D2 / "bulk_to_tp_correction_existence_audit.csv")

    write_csv(
        OUT / "sensor_projection_operator_table.csv",
        rows,
        [
            "sensor",
            "sensor_kind",
            "acceptance_class",
            "projection_operator",
            "one_d_state_source",
            "one_d_segment_or_state",
            "one_d_fraction_or_marker",
            "elevation_m",
            "coordinate_claim_level",
            "score_target_use",
            "runtime_temperature_allowed",
            "fit_allowed",
            "model_selection_allowed",
            "projection_equation",
            "release_status",
            "uncertainty_caveat",
            "publication_effect",
        ],
    )
    runtime_rows = [
        {
            "gate": "observed_TP_TW_temperature_as_runtime_input",
            "allowed": False,
            "reason": "validation temperatures are score targets only",
        },
        {
            "gate": "bulk_to_TP_thermal_development_offset_release",
            "allowed": False,
            "reason": "D2 shows promise, but no physical/source-bounded correction is released",
        },
        {
            "gate": "wall_temperature_projection_for_TW_score",
            "allowed": True,
            "reason": "model-predicted wall state may be projected for post-solve score comparison",
        },
        {
            "gate": "TW10_score_or_projection",
            "allowed": False,
            "reason": "active-HX shell state is absent",
        },
    ]
    equations = [
        {
            "equation_id": "TP_projection_score_only",
            "equation": "T_hat_TP_i = P_bulk_i[T_bulk_1d(s_i)]",
            "status": "operator_defined_no_offset_release",
            "notes": "P_bulk_i is a segment/fraction mapping from the N4 sensor table.",
        },
        {
            "equation_id": "TW_projection_score_only",
            "equation": "T_hat_TW_i = P_wall_i[T_wall_1d(s_i)]",
            "status": "operator_defined_score_only",
            "notes": "TW projection uses model-predicted wall state, not observed wall temperature as input.",
        },
        {
            "equation_id": "future_bulk_to_TP_development",
            "equation": "T_hat_TP_i = P_bulk_i[T_bulk_1d(s_i)] + Delta_T_dev_i",
            "status": "future_layer_not_released",
            "notes": "Delta_T_dev_i remains blocked by source/property, same-QOI UQ, and physical attribution gates.",
        },
    ]
    source_manifest = [
        {"artifact": "N4 sensor/QOI projection table", "path": rel(N4), "use": "sensor mapping, score policy, caveats"},
        {"artifact": "D2 TP/TW projection gate", "path": rel(D2), "use": "bulk-to-TP correction non-release and diagnostic RMSE context"},
        {"artifact": "TP/TW elevation panels", "path": rel(ELEV), "use": "elevation and segment mapping context"},
        {"artifact": "signed-error shape dispatch", "path": rel(SHAPE), "use": "residual-shape context"},
        {"artifact": "master model-form scoreboard", "path": rel(MASTER), "use": "source path and score-only status context"},
    ]
    no_mutation = [
        {"guardrail": "native_output_mutation", "status": False},
        {"guardrail": "registry_or_admission_mutation", "status": False},
        {"guardrail": "scheduler_action", "status": False},
        {"guardrail": "solver_sampler_harvest_uq_launch", "status": False},
        {"guardrail": "Fluid_or_external_repo_mutation", "status": False},
        {"guardrail": "validation_holdout_external_scoring", "status": False},
        {"guardrail": "runtime_temperature_release", "status": False},
        {"guardrail": "source_property_release", "status": False},
        {"guardrail": "coefficient_admission", "status": False},
        {"guardrail": "residual_absorbed_into_internal_Nu", "status": False},
    ]

    write_csv(OUT / "runtime_legality_matrix.csv", runtime_rows, ["gate", "allowed", "reason"])
    write_csv(OUT / "writer_ready_projection_equations.csv", equations, ["equation_id", "equation", "status", "notes"])
    write_csv(OUT / "bulk_to_tp_release_status.csv", d2_audit, list(d2_audit[0]))
    write_csv(OUT / "source_manifest.csv", source_manifest, ["artifact", "path", "use"])
    write_csv(OUT / "no_mutation_guardrails.csv", no_mutation, ["guardrail", "status"])
    write_svg(rows)

    counts = Counter(row["projection_operator"] for row in rows)
    summary = {
        "task_id": TASK_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "decision": "projection_operator_defined_diagnostic_only_no_runtime_temperature_release",
        "sensor_rows": len(rows),
        "tp_operator_rows": counts["bulk_fluid_projection"],
        "tw_operator_rows": counts["wall_state_projection"],
        "excluded_rows": counts["excluded_no_projection"],
        "runtime_temperature_release": False,
        "bulk_to_tp_correction_released": bool(d2_summary.get("released_bulk_to_tp_correction_exists", False)),
        "thermal_development_path_promising": bool(d2_summary.get("thermal_development_path_promising", False)),
        "d2_transfer_tp_rmse_K": d2_summary.get("d2_transfer_tp_rmse_K"),
        "m3_transfer_tp_rmse_K": d2_summary.get("m3_transfer_tp_rmse_K"),
        "d2_transfer_tw_rmse_K": d2_summary.get("d2_transfer_tw_rmse_K"),
        "m3_transfer_tw_rmse_K": d2_summary.get("m3_transfer_tw_rmse_K"),
        "validation_holdout_external_scoring": False,
        "source_property_release": False,
        "coefficient_admission": False,
        "final_score_values": 0,
        "native_output_mutation": False,
        "registry_or_admission_mutation": False,
        "scheduler_action": False,
        "solver_sampler_harvest_uq_launched": False,
        "residual_absorbed_into_internal_nu": False,
        "next_required_action": "physical/source-bounded bulk-to-TP thermal-development offset proof before any correction release",
    }
    dump_json(OUT / "summary.json", summary)
    readme = f"""---
provenance:
  task_id: {TASK_ID}
  generated_at_utc: {summary['generated_at_utc']}
tags:
  - sensor-map
  - projection-operator
  - tp
  - tw
related:
  - {rel(N4)}
  - {rel(D2)}
---

# 1D Sensor Projection Operator: TP/TW Wall/Bulk

This package defines the score-only measurement operator from 1D bulk and wall
states to TP/TW observations. It does not release observed validation
temperatures as runtime inputs and does not release a bulk-to-TP thermal
development correction.

Open `sensor_projection_operator_table.csv` first. TP sensors use
`bulk_fluid_projection`; TW sensors use `wall_state_projection`; TW10 is
excluded because the active-HX shell state is absent.

Decision: `{summary['decision']}`.
"""
    (OUT / "README.md").write_text(readme, encoding="utf-8")
    return summary


if __name__ == "__main__":
    print(json.dumps(build(), indent=2, sort_keys=True))
