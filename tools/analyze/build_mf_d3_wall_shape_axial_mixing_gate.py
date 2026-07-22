#!/usr/bin/env python3
"""Build the D3 wall-shape / axial-mixing evidence gate."""

from __future__ import annotations

import csv
import json
import math
import re
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TASK = "TODO-MF-D3-WALL-SHAPE-AXIAL-MIXING-GATE-2026-07-22"
OUT = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_mf_d3_wall_shape_axial_mixing_gate"

DIAG = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_thesis_suggested_model_form_diagnostic_tests"
SENSOR_ERRORS = DIAG / "tested_model_form_sensor_errors.csv"
SCOREBOARD = DIAG / "tested_model_form_scoreboard.csv"

S12_EXCHANGE = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_s12_tp_first_upcomer_exchange_evidence_gate/s12_tp_exchange_evidence_table.csv"
S12_UNLOCK = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_s12_tp_first_upcomer_exchange_evidence_gate/s12_tp_unlock_gate_matrix.csv"
S13_TRIPLETS = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_target_plus_same_qoi_harvest/same_qoi_neighbor_triplet_matrix.csv"
S13_SUMMARY = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_target_plus_same_qoi_harvest/summary.json"
N4_SENSOR = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_thesis_n4_sensor_qoi_projection_uncertainty_table/sensor_qoi_projection_table.csv"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


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


def fmt(value: object) -> object:
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return ""
        return f"{value:.12g}"
    return value


def sensor_index(sensor: str) -> int:
    match = re.search(r"(\d+)$", sensor or "")
    return int(match.group(1)) if match else 999


def slope(xs: list[float], ys: list[float]) -> float:
    if len(xs) < 2:
        return float("nan")
    xbar = mean(xs)
    ybar = mean(ys)
    denom = sum((x - xbar) ** 2 for x in xs)
    if denom == 0.0:
        return float("nan")
    return sum((x - xbar) * (y - ybar) for x, y in zip(xs, ys)) / denom


def build_wall_shape_rows(sensor_rows: list[dict[str, str]]) -> list[dict[str, object]]:
    by_key: dict[tuple[str, str, str], dict[str, str]] = {}
    for row in sensor_rows:
        if row["tested_model_form_id"] in {"M3_as_is", "D3_M3_wall_linear_shape_train"} and row["sensor_kind"] == "TW":
            by_key[(row["tested_model_form_id"], row["case_id"], row["sensor"])] = row

    rows: list[dict[str, object]] = []
    for (model, case, sensor), m3 in sorted(by_key.items()):
        if model != "M3_as_is":
            continue
        d3 = by_key.get(("D3_M3_wall_linear_shape_train", case, sensor))
        if not d3:
            continue
        m3_err = fnum(m3["signed_error_K"])
        d3_err = fnum(d3["signed_error_K"])
        if m3_err is None or d3_err is None:
            continue
        rows.append(
            {
                "case_id": case,
                "split_group": m3["split_group"],
                "sensor": sensor,
                "sensor_index": sensor_index(sensor),
                "prediction_source_segment": m3["prediction_source_segment"],
                "m3_signed_error_K": m3_err,
                "d3_signed_error_K": d3_err,
                "d3_minus_m3_signed_error_K": d3_err - m3_err,
                "d3_reduced_abs_error": abs(d3_err) < abs(m3_err),
                "d3_correction_K": fnum(d3["correction_K"]),
                "target_K": fnum(d3["target_K"]),
            }
        )
    return rows


def build_shape_summary(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        grouped[(str(row["split_group"]), str(row["case_id"]))].append(row)
    out: list[dict[str, object]] = []
    for (split_group, case), items in sorted(grouped.items()):
        xs = [float(r["sensor_index"]) for r in items]
        m3 = [float(r["m3_signed_error_K"]) for r in items]
        d3 = [float(r["d3_signed_error_K"]) for r in items]
        out.append(
            {
                "case_id": case,
                "split_group": split_group,
                "tw_rows": len(items),
                "m3_tw_rmse_K": rmse(m3),
                "d3_tw_rmse_K": rmse(d3),
                "d3_minus_m3_tw_rmse_K": rmse(d3) - rmse(m3),
                "m3_error_slope_K_per_sensor_index": slope(xs, m3),
                "d3_error_slope_K_per_sensor_index": slope(xs, d3),
                "d3_reduced_abs_error_rows": sum(1 for r in items if r["d3_reduced_abs_error"]),
            }
        )
    return out


def build_crosswalk() -> list[dict[str, object]]:
    s12_unlock = read_csv(S12_UNLOCK)
    triplets = read_csv(S13_TRIPLETS)
    n4 = read_csv(N4_SENSOR)
    s13_summary = json.loads(S13_SUMMARY.read_text())

    gates = {row["gate"]: row for row in s12_unlock}
    qoi_ready = sum(1 for row in triplets if row["same_qoi_neighbor_triplet_ready"].lower() == "true")
    runtime_temp_allowed = sum(1 for row in n4 if row["runtime_temperature_allowed"].lower() == "true")
    bounded_tw = sum(1 for row in n4 if row["kind"] == "TW" and row["acceptance_class"] == "bounded")

    return [
        {
            "evidence_family": "S12 TP-first exchange evidence",
            "status": gates.get("finite_exchange_proxy_rows", {}).get("status", "missing"),
            "production_ready": gates.get("finite_exchange_proxy_rows", {}).get("production_ready", "False"),
            "supports_d3_mechanism": True,
            "blocks_candidate": True,
            "reason": "finite exchange proxy rows exist but are diagnostic-only and require production harvest/UQ before promotion",
        },
        {
            "evidence_family": "S12 source/property conservation release",
            "status": gates.get("source_property_conservation_release", {}).get("status", "missing"),
            "production_ready": gates.get("source_property_conservation_release", {}).get("production_ready", "False"),
            "supports_d3_mechanism": False,
            "blocks_candidate": True,
            "reason": "source/property release rows remain failed, so wall-shape mechanism cannot be admitted",
        },
        {
            "evidence_family": "S13 same-QOI target/minus/plus triplets",
            "status": "triplets_ready_uq_not_executed",
            "production_ready": s13_summary.get("production_harvest_allowed", False),
            "supports_d3_mechanism": qoi_ready >= 4,
            "blocks_candidate": True,
            "reason": f"{qoi_ready} QOI labels have triplets, but same-QOI UQ and production use are not executed",
        },
        {
            "evidence_family": "N4 sensor projection",
            "status": "bounded_not_runtime_input",
            "production_ready": False,
            "supports_d3_mechanism": bounded_tw > 0,
            "blocks_candidate": True,
            "reason": f"{bounded_tw} TW sensors are bounded as score targets; runtime temperature allowed rows = {runtime_temp_allowed}",
        },
    ]


def build_uq_requirements() -> list[dict[str, object]]:
    triplets = read_csv(S13_TRIPLETS)
    rows: list[dict[str, object]] = []
    for row in triplets:
        rows.append(
            {
                "qoi_label": row["qoi_label"],
                "target_ready_rows": row["target_ready_rows"],
                "target_minus_ready_rows": row["target_minus_ready_rows"],
                "target_plus_ready_rows": row["target_plus_ready_rows"],
                "triplet_ready": row["same_qoi_neighbor_triplet_ready"],
                "same_qoi_uq_execution_status": row["same_qoi_neighbor_uq_execution_status"],
                "mesh_gci_allowed_now": row["move_to_mesh_gci_uq_allowed_now"],
                "production_use_allowed_now": row["production_use_allowed_now"],
                "d3_use": "required_support_for_wall_core_exchange_or_axial_mixing_claim",
                "next_action": row["blocking_or_next_reason"],
            }
        )
    return rows


def build_candidate_gate(crosswalk: list[dict[str, object]]) -> list[dict[str, object]]:
    blockers = [row for row in crosswalk if row["blocks_candidate"]]
    common_ready = len(blockers) == 0
    return [
        {
            "candidate_id": "D3-WALL-CORE-EXCHANGE-SHAPE",
            "mechanism": "source-bounded wall/core exchange",
            "positive_evidence": "D3 transfer RMSE improves and S13 QOI triplets are ready",
            "blocking_evidence": "same-QOI UQ not executed; source/property conservation release failed; production use not allowed",
            "runtime_legal_source_bounded_study_defined": False,
            "candidate_ready": common_ready,
            "gate_status": "fail_closed_diagnostic_only",
        },
        {
            "candidate_id": "D3-AXIAL-MIXING-SHAPE",
            "mechanism": "axial mixing or wall-index thermal-shape transport",
            "positive_evidence": "D3 reduces TW wall-index signed-error slope and transfer RMSE",
            "blocking_evidence": "no independent axial-mixing/source-bounded coefficient or same-QOI UQ admission basis",
            "runtime_legal_source_bounded_study_defined": False,
            "candidate_ready": False,
            "gate_status": "fail_closed_diagnostic_only",
        },
        {
            "candidate_id": "D3-SENSOR-PROJECTION-SHAPE",
            "mechanism": "sensor/QOI projection uncertainty",
            "positive_evidence": "N4 bounds TW sensors as post-solve score targets",
            "blocking_evidence": "runtime temperature inputs remain forbidden; projection supports uncertainty, not closure repair",
            "runtime_legal_source_bounded_study_defined": False,
            "candidate_ready": False,
            "gate_status": "supporting_uncertainty_only",
        },
    ]


def main() -> None:
    sensor_rows = read_csv(SENSOR_ERRORS)
    scoreboard = read_csv(SCOREBOARD)
    d3_score = next(row for row in scoreboard if row["tested_model_form_id"] == "D3_M3_wall_linear_shape_train")

    wall_rows = build_wall_shape_rows(sensor_rows)
    shape_summary = build_shape_summary(wall_rows)
    crosswalk = build_crosswalk()
    uq_rows = build_uq_requirements()
    gate_rows = build_candidate_gate(crosswalk)

    write_csv(
        OUT / "wall_index_residual_shape_decomposition.csv",
        [{k: fmt(v) for k, v in row.items()} for row in wall_rows],
        [
            "case_id",
            "split_group",
            "sensor",
            "sensor_index",
            "prediction_source_segment",
            "m3_signed_error_K",
            "d3_signed_error_K",
            "d3_minus_m3_signed_error_K",
            "d3_reduced_abs_error",
            "d3_correction_K",
            "target_K",
        ],
    )
    write_csv(
        OUT / "wall_shape_case_summary.csv",
        [{k: fmt(v) for k, v in row.items()} for row in shape_summary],
        [
            "case_id",
            "split_group",
            "tw_rows",
            "m3_tw_rmse_K",
            "d3_tw_rmse_K",
            "d3_minus_m3_tw_rmse_K",
            "m3_error_slope_K_per_sensor_index",
            "d3_error_slope_K_per_sensor_index",
            "d3_reduced_abs_error_rows",
        ],
    )
    write_csv(
        OUT / "s12_s13_evidence_crosswalk.csv",
        crosswalk,
        [
            "evidence_family",
            "status",
            "production_ready",
            "supports_d3_mechanism",
            "blocks_candidate",
            "reason",
        ],
    )
    write_csv(
        OUT / "same_qoi_uq_requirement_table.csv",
        uq_rows,
        [
            "qoi_label",
            "target_ready_rows",
            "target_minus_ready_rows",
            "target_plus_ready_rows",
            "triplet_ready",
            "same_qoi_uq_execution_status",
            "mesh_gci_allowed_now",
            "production_use_allowed_now",
            "d3_use",
            "next_action",
        ],
    )
    write_csv(
        OUT / "candidate_gate.csv",
        gate_rows,
        [
            "candidate_id",
            "mechanism",
            "positive_evidence",
            "blocking_evidence",
            "runtime_legal_source_bounded_study_defined",
            "candidate_ready",
            "gate_status",
        ],
    )
    write_csv(
        OUT / "publication_claim_boundary.csv",
        [
            {
                "claim": "D3 wall-index correction is a useful thermal-shape diagnostic",
                "allowed": True,
                "forbidden": "Do not claim an admitted wall/core exchange or axial-mixing closure.",
                "basis": "D3 improves transfer RMSE but remains residual-trained.",
            },
            {
                "claim": "S13 triplet-ready QOIs are relevant to D3 wall-shape follow-up",
                "allowed": True,
                "forbidden": "Do not claim same-QOI UQ, mesh/GCI UQ, production harvest, or source/property release has occurred.",
                "basis": "same_qoi_uq_requirement_table.csv",
            },
            {
                "claim": "D3 is ready as runtime-legal source-bounded study",
                "allowed": False,
                "forbidden": "No D3 runtime coefficient or correction may enter the model.",
                "basis": "candidate_gate.csv",
            },
        ],
        ["claim", "allowed", "forbidden", "basis"],
    )
    write_csv(
        OUT / "source_manifest.csv",
        [
            {"path": str(SENSOR_ERRORS.relative_to(ROOT)), "used": True, "mutation_status": "read_only"},
            {"path": str(SCOREBOARD.relative_to(ROOT)), "used": True, "mutation_status": "read_only"},
            {"path": str(S12_EXCHANGE.relative_to(ROOT)), "used": True, "mutation_status": "read_only"},
            {"path": str(S12_UNLOCK.relative_to(ROOT)), "used": True, "mutation_status": "read_only"},
            {"path": str(S13_TRIPLETS.relative_to(ROOT)), "used": True, "mutation_status": "read_only"},
            {"path": str(S13_SUMMARY.relative_to(ROOT)), "used": True, "mutation_status": "read_only"},
            {"path": str(N4_SENSOR.relative_to(ROOT)), "used": True, "mutation_status": "read_only"},
        ],
        ["path", "used", "mutation_status"],
    )
    write_csv(
        OUT / "no_mutation_guardrails.csv",
        [
            {"guardrail": "native CFD/OpenFOAM outputs", "mutation": False},
            {"guardrail": "registry/admission state", "mutation": False},
            {"guardrail": "scheduler/solver/sampler/harvest/UQ", "mutation": False},
            {"guardrail": "Fluid or external source trees", "mutation": False},
            {"guardrail": "thesis current/LaTeX files", "mutation": False},
            {"guardrail": "fitting/tuning/model selection", "mutation": False},
            {"guardrail": "runtime temperature input release", "mutation": False},
        ],
        ["guardrail", "mutation"],
    )

    ready_candidates = sum(1 for row in gate_rows if row["candidate_ready"])
    transfer_rows = [row for row in wall_rows if row["split_group"] == "transfer"]
    summary = {
        "task": TASK,
        "decision": "d3_wall_shape_signal_supported_diagnostic_only_same_qoi_triplets_ready_uq_not_executed",
        "wall_rows": len(wall_rows),
        "transfer_wall_rows": len(transfer_rows),
        "candidate_rows": len(gate_rows),
        "candidate_ready_rows": ready_candidates,
        "d3_transfer_rmse_K": float(d3_score["transfer_rmse_K"]),
        "d3_transfer_local_shape_rmse_after_bias_K": float(d3_score["transfer_local_shape_rmse_after_bias_K"]),
        "d3_transfer_rmse_reduction_pct": float(d3_score["m3_transfer_rmse_reduction_pct"]),
        "same_qoi_triplet_ready_qois": sum(1 for row in uq_rows if str(row["triplet_ready"]).lower() == "true"),
        "same_qoi_uq_executed": False,
        "production_use_allowed_now": False,
        "admission_status": "diagnostic_not_admitted",
    }
    write_json(OUT / "summary.json", summary)

    readme = f"""---
provenance:
  - {str(SENSOR_ERRORS.relative_to(ROOT))}
  - {str(S12_UNLOCK.relative_to(ROOT))}
  - {str(S13_TRIPLETS.relative_to(ROOT))}
  - {str(N4_SENSOR.relative_to(ROOT))}
tags: [model-form, d3, wall-shape, axial-mixing, same-qoi, thesis]
related:
  - .agent/status/2026-07-22_{TASK}.md
  - .agent/journal/2026-07-22/mf-d3-wall-shape-axial-mixing-gate.md
task: {TASK}
date: 2026-07-22
role: Thermal-modeling / Hydraulics / Forward-pred / Tester / Writer / Reviewer
type: work_product
status: complete
---
# D3 Wall-Shape / Axial-Mixing Gate

This package tests whether the D3 wall-index diagnostic improvement can be
explained by source-bounded wall/core exchange, axial mixing, or sensor
projection evidence.

## Decision

D3 is supported as a diagnostic wall-shape signal only. S13 now has same-QOI
target/minus/plus triplets ready for four QOI labels, but same-QOI UQ,
production use, source/property release, and admission remain unexecuted.

## Outputs

- `wall_index_residual_shape_decomposition.csv`
- `wall_shape_case_summary.csv`
- `s12_s13_evidence_crosswalk.csv`
- `same_qoi_uq_requirement_table.csv`
- `candidate_gate.csv`
- `publication_claim_boundary.csv`
- `source_manifest.csv`
- `no_mutation_guardrails.csv`
- `summary.json`
"""
    (OUT / "README.md").write_text(readme)


if __name__ == "__main__":
    main()
