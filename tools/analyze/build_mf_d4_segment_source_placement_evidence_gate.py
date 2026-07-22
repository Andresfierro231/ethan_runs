#!/usr/bin/env python3
"""Build the D4 segment source-placement evidence gate."""

from __future__ import annotations

import csv
import json
import math
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TASK = "TODO-MF-D4-SEGMENT-SOURCE-PLACEMENT-EVIDENCE-GATE-2026-07-22"
OUT = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_mf_d4_segment_source_placement_evidence_gate"

DIAG = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_thesis_suggested_model_form_diagnostic_tests"
SENSOR_ERRORS = DIAG / "tested_model_form_sensor_errors.csv"
SCOREBOARD = DIAG / "tested_model_form_scoreboard.csv"

SOURCE_PROVENANCE = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_extbc_source_sink_provenance_recovery/setup_source_sink_provenance_ledger.csv"
SOURCE_CONTRACT = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_fluid_setup_known_source_sink_runtime_contract/setup_known_source_contract.csv"
PASSIVE_SOURCE = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_fluid_extbc_passive_h2_cand001_source_basis_enrichment/source_basis_coverage.csv"
PASSIVE_ENVELOPE = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_passive_h2_cand001_physical_basis/expected_q_loss_envelope.csv"
S8_S12_OWNER = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_s8_s12_thermal_residual_ownership_gate/residual_owner_matrix.csv"
N3_ABLATION = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_thesis_n3_thermal_residual_owner_train_ablation/thermal_residual_ablation_table.csv"

TARGET_SEGMENTS = ["heated_incline", "left_lower_vertical", "left_upper_vertical", "right_vertical"]
SEGMENT_TO_EVIDENCE = {
    "heated_incline": {
        "primary_source_family": "lower_leg",
        "physical_owner": "setup heater redistribution plus passive lower_leg",
        "reason": "D4 correction is local to TW4/TW5/TW6 heated-incline wall rows and aligns with the existing lower-leg setup/source lane.",
    },
    "left_lower_vertical": {
        "primary_source_family": "upcomer",
        "physical_owner": "test-section/upcomer source placement plus passive upcomer",
        "reason": "D4 correction touches TP3/TP4/TW7 source-segment rows and is closest to the setup-known upcomer/test-section source family.",
    },
    "left_upper_vertical": {
        "primary_source_family": "upcomer",
        "physical_owner": "upper upcomer wall/core exchange or passive upcomer",
        "reason": "D4 correction is a left-leg continuation signal with no separate released source family from the upcomer/test-section lane.",
    },
    "right_vertical": {
        "primary_source_family": "downcomer",
        "physical_owner": "passive downcomer wall heat path",
        "reason": "D4 correction is largest for TW1/TW2/TW3 and maps to the right/downcomer wall family in passive heat-path evidence.",
    },
}


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


def mae(values: list[float]) -> float:
    return mean([abs(v) for v in values]) if values else float("nan")


def fmt(value: object) -> object:
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return ""
        return f"{value:.12g}"
    return value


def metric_rows(rows: list[dict[str, str]]) -> dict[tuple[str, str], dict[str, float | int]]:
    grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        if row["tested_model_form_id"] in {"M3_as_is", "D4_M3_segment_offsets_min2_train"}:
            grouped[(row["tested_model_form_id"], row["prediction_source_segment"])].append(row)
    out: dict[tuple[str, str], dict[str, float | int]] = {}
    for key, items in grouped.items():
        all_errors = [fnum(r["signed_error_K"]) for r in items]
        all_errors = [v for v in all_errors if v is not None]
        transfer_errors = [fnum(r["signed_error_K"]) for r in items if r["split_group"] == "transfer"]
        transfer_errors = [v for v in transfer_errors if v is not None]
        train_errors = [fnum(r["signed_error_K"]) for r in items if r["split_group"] == "train"]
        train_errors = [v for v in train_errors if v is not None]
        corrections = [fnum(r["correction_K"]) for r in items if r["tested_model_form_id"].startswith("D4")]
        corrections = [v for v in corrections if v is not None]
        out[key] = {
            "all_rows": len(all_errors),
            "train_rows": len(train_errors),
            "transfer_rows": len(transfer_errors),
            "train_mean_signed_error_K": mean(train_errors),
            "transfer_mean_signed_error_K": mean(transfer_errors),
            "transfer_rmse_K": rmse(transfer_errors),
            "transfer_mae_K": mae(transfer_errors),
            "mean_correction_K": mean(corrections),
        }
    return out


def build_segment_residual_map(sensor_rows: list[dict[str, str]]) -> list[dict[str, object]]:
    metrics = metric_rows(sensor_rows)
    segments = sorted({key[1] for key in metrics if key[1]})
    rows: list[dict[str, object]] = []
    for segment in segments:
        m3 = metrics.get(("M3_as_is", segment), {})
        d4 = metrics.get(("D4_M3_segment_offsets_min2_train", segment), {})
        m3_rmse = fnum(m3.get("transfer_rmse_K"))
        d4_rmse = fnum(d4.get("transfer_rmse_K"))
        rows.append(
            {
                "prediction_source_segment": segment,
                "target_gate_segment": segment in TARGET_SEGMENTS,
                "train_rows": d4.get("train_rows", 0),
                "transfer_rows": d4.get("transfer_rows", 0),
                "d4_mean_correction_K": d4.get("mean_correction_K", ""),
                "m3_transfer_rmse_K": m3.get("transfer_rmse_K", ""),
                "d4_transfer_rmse_K": d4.get("transfer_rmse_K", ""),
                "d4_minus_m3_transfer_rmse_K": (d4_rmse - m3_rmse) if d4_rmse is not None and m3_rmse is not None else "",
                "m3_transfer_mean_signed_error_K": m3.get("transfer_mean_signed_error_K", ""),
                "d4_transfer_mean_signed_error_K": d4.get("transfer_mean_signed_error_K", ""),
                "d4_transfer_mae_K": d4.get("transfer_mae_K", ""),
                "interpretation": interpret_segment(segment, d4.get("mean_correction_K", ""), d4_rmse, m3_rmse),
            }
        )
    return rows


def interpret_segment(segment: str, correction: object, d4_rmse: float | None, m3_rmse: float | None) -> str:
    if segment not in TARGET_SEGMENTS:
        return "non_target_or_global_fallback_segment"
    improvement = d4_rmse is not None and m3_rmse is not None and d4_rmse < m3_rmse
    corr = fnum(correction)
    direction = "warming_correction" if corr is not None and corr > 0 else "non_warming_or_unavailable"
    return f"{direction}; {'transfer_improved' if improvement else 'transfer_not_improved'}; needs_independent_source_evidence"


def first_row(rows: list[dict[str, str]], key: str, value: str) -> dict[str, str]:
    for row in rows:
        if row.get(key) == value:
            return row
    return {}


def source_rows(rows: list[dict[str, str]], key: str, value: str) -> list[dict[str, str]]:
    return [row for row in rows if row.get(key) == value]


def build_evidence_rows() -> list[dict[str, object]]:
    setup = read_csv(SOURCE_PROVENANCE)
    contract = read_csv(SOURCE_CONTRACT)
    passive = read_csv(PASSIVE_SOURCE)
    envelope = read_csv(PASSIVE_ENVELOPE)
    owner = read_csv(S8_S12_OWNER)
    n3 = read_csv(N3_ABLATION)

    rows: list[dict[str, object]] = []
    for segment in TARGET_SEGMENTS:
        mapping = SEGMENT_TO_EVIDENCE[segment]
        family = mapping["primary_source_family"]
        setup_family = source_rows(setup, "source_segment_id", family)
        setup_train = [r for r in setup_family if r.get("case_id") == "salt_2"]
        setup_q = sum(fnum(r.get("setup_value_W")) or 0.0 for r in setup_train)
        contract_rows = source_rows(contract, "source_segment_id", family)
        passive_row = first_row(passive, "source_family", family)
        envelope_row = first_row(envelope, "source_family", family)
        owner_hits = [
            r for r in owner
            if family in r.get("owner_family", "") or segment in r.get("owner_family", "")
        ]
        n3_hits = [
            r for r in n3
            if family in r.get("lane", "") or family in r.get("evidence", "") or family in r.get("reason", "")
        ]
        source_property_released = any(r.get("source_property_released_now", "").lower() == "true" for r in contract_rows)
        passive_release = passive_row.get("independent_source_release_allowed_now", "").lower() == "true"
        independent_geometry = passive_row.get("geometry_support_status", "") not in {"needs_independent_geometry_trace", ""}
        has_setup = bool(setup_family)
        evidence_status = "fail_closed_source_property_not_released"
        if source_property_released and passive_release and independent_geometry:
            evidence_status = "candidate_reviewable"
        rows.append(
            {
                "prediction_source_segment": segment,
                "mapped_source_family": family,
                "physical_owner_hypothesis": mapping["physical_owner"],
                "mapping_reason": mapping["reason"],
                "setup_known_rows": len(setup_family),
                "salt2_setup_Q_W": setup_q if has_setup else "",
                "setup_runtime_allowed_now": any(r.get("runtime_allowed_now", "").lower() == "true" for r in setup_family),
                "contract_rows": len(contract_rows),
                "contract_executable_train_only": any("train_only" in r.get("runtime_contract_status", "") for r in contract_rows),
                "source_property_released_now": source_property_released,
                "passive_source_basis_status": passive_row.get("repair_ready_now", ""),
                "passive_independent_release_allowed_now": passive_release,
                "passive_geometry_support_status": passive_row.get("geometry_support_status", ""),
                "independent_q_loss_nominal_W": envelope_row.get("independent_q_loss_nominal_W", ""),
                "current_q_inside_engineering_envelope": envelope_row.get("current_q_inside_envelope", ""),
                "s8_s12_owner_hits": len(owner_hits),
                "n3_ablation_hits": len(n3_hits),
                "evidence_status": evidence_status,
                "blocking_reason": "setup/passive evidence is useful but independent source/property and geometry release gates are not all satisfied",
            }
        )
    return rows


def build_runtime_legality(evidence_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for row in evidence_rows:
        ready = row["evidence_status"] == "candidate_reviewable"
        rows.append(
            {
                "prediction_source_segment": row["prediction_source_segment"],
                "runtime_input": row["physical_owner_hypothesis"],
                "uses_train_residual_fit": False,
                "uses_validation_holdout_targets": False,
                "uses_native_realized_wallHeatFlux": False,
                "source_property_released_now": row["source_property_released_now"],
                "independent_geometry_released_now": row["passive_geometry_support_status"] not in {"needs_independent_geometry_trace", ""},
                "runtime_legal_now": ready,
                "decision": "candidate_runtime_legal" if ready else "fail_closed_not_runtime_legal",
            }
        )
    return rows


def build_candidate_gate(segment_rows: list[dict[str, object]], evidence_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    residual_by_segment = {row["prediction_source_segment"]: row for row in segment_rows}
    rows: list[dict[str, object]] = []
    for evidence in evidence_rows:
        segment = evidence["prediction_source_segment"]
        residual = residual_by_segment.get(segment, {})
        d4_delta = fnum(residual.get("d4_minus_m3_transfer_rmse_K"))
        transfer_improved = d4_delta is not None and d4_delta < 0
        evidence_ready = evidence["evidence_status"] == "candidate_reviewable"
        release = transfer_improved and evidence_ready
        rows.append(
            {
                "candidate_id": f"D4-SOURCE-{segment}",
                "prediction_source_segment": segment,
                "mapped_source_family": evidence["mapped_source_family"],
                "transfer_improved": transfer_improved,
                "d4_minus_m3_transfer_rmse_K": residual.get("d4_minus_m3_transfer_rmse_K", ""),
                "d4_mean_correction_K": residual.get("d4_mean_correction_K", ""),
                "independent_evidence_ready": evidence_ready,
                "source_bounded_candidate_ready": release,
                "gate_status": "candidate_reviewable" if release else "fail_closed_empirical_upper_bound_only",
                "decision_reason": (
                    "transfer improvement has independent released source evidence"
                    if release
                    else "D4 transfer improvement is empirical; independent source/property or geometry release is missing"
                ),
            }
        )
    return rows


def main() -> None:
    sensor_rows = read_csv(SENSOR_ERRORS)
    scoreboard_rows = read_csv(SCOREBOARD)
    segment_rows = build_segment_residual_map(sensor_rows)
    evidence_rows = build_evidence_rows()
    runtime_rows = build_runtime_legality(evidence_rows)
    gate_rows = build_candidate_gate(segment_rows, evidence_rows)

    write_csv(
        OUT / "segment_residual_map.csv",
        [{k: fmt(v) for k, v in row.items()} for row in segment_rows],
        [
            "prediction_source_segment",
            "target_gate_segment",
            "train_rows",
            "transfer_rows",
            "d4_mean_correction_K",
            "m3_transfer_rmse_K",
            "d4_transfer_rmse_K",
            "d4_minus_m3_transfer_rmse_K",
            "m3_transfer_mean_signed_error_K",
            "d4_transfer_mean_signed_error_K",
            "d4_transfer_mae_K",
            "interpretation",
        ],
    )
    write_csv(
        OUT / "independent_source_heat_path_evidence.csv",
        [{k: fmt(v) for k, v in row.items()} for row in evidence_rows],
        [
            "prediction_source_segment",
            "mapped_source_family",
            "physical_owner_hypothesis",
            "mapping_reason",
            "setup_known_rows",
            "salt2_setup_Q_W",
            "setup_runtime_allowed_now",
            "contract_rows",
            "contract_executable_train_only",
            "source_property_released_now",
            "passive_source_basis_status",
            "passive_independent_release_allowed_now",
            "passive_geometry_support_status",
            "independent_q_loss_nominal_W",
            "current_q_inside_engineering_envelope",
            "s8_s12_owner_hits",
            "n3_ablation_hits",
            "evidence_status",
            "blocking_reason",
        ],
    )
    write_csv(
        OUT / "runtime_legality_matrix.csv",
        runtime_rows,
        [
            "prediction_source_segment",
            "runtime_input",
            "uses_train_residual_fit",
            "uses_validation_holdout_targets",
            "uses_native_realized_wallHeatFlux",
            "source_property_released_now",
            "independent_geometry_released_now",
            "runtime_legal_now",
            "decision",
        ],
    )
    write_csv(
        OUT / "source_bounded_candidate_gate.csv",
        [{k: fmt(v) for k, v in row.items()} for row in gate_rows],
        [
            "candidate_id",
            "prediction_source_segment",
            "mapped_source_family",
            "transfer_improved",
            "d4_minus_m3_transfer_rmse_K",
            "d4_mean_correction_K",
            "independent_evidence_ready",
            "source_bounded_candidate_ready",
            "gate_status",
            "decision_reason",
        ],
    )
    write_csv(
        OUT / "publication_claim_boundary.csv",
        [
            {
                "claim": "D4 segment offsets identify where source-placement evidence should be tested next",
                "allowed": True,
                "forbidden": "Do not claim D4 is a source-bounded closure or admitted repair.",
                "basis": "Salt2-trained residual correction transfers to Salt3/Salt4 but independent release gates fail closed.",
            },
            {
                "claim": "The right_vertical and heated/left-leg segments are high-priority source-placement targets",
                "allowed": True,
                "forbidden": "Do not use D4 coefficients as runtime inputs.",
                "basis": "Segment residual map plus independent evidence crosswalk.",
            },
            {
                "claim": "A local source-placement candidate is ready for freeze review",
                "allowed": any(row["source_bounded_candidate_ready"] for row in gate_rows),
                "forbidden": "No freeze/admission claim when all candidate rows are fail-closed.",
                "basis": "source_bounded_candidate_gate.csv",
            },
        ],
        ["claim", "allowed", "forbidden", "basis"],
    )
    write_csv(
        OUT / "source_manifest.csv",
        [
            {"path": str(SENSOR_ERRORS.relative_to(ROOT)), "used": True, "mutation_status": "read_only"},
            {"path": str(SCOREBOARD.relative_to(ROOT)), "used": True, "mutation_status": "read_only"},
            {"path": str(SOURCE_PROVENANCE.relative_to(ROOT)), "used": True, "mutation_status": "read_only"},
            {"path": str(SOURCE_CONTRACT.relative_to(ROOT)), "used": True, "mutation_status": "read_only"},
            {"path": str(PASSIVE_SOURCE.relative_to(ROOT)), "used": True, "mutation_status": "read_only"},
            {"path": str(PASSIVE_ENVELOPE.relative_to(ROOT)), "used": True, "mutation_status": "read_only"},
            {"path": str(S8_S12_OWNER.relative_to(ROOT)), "used": True, "mutation_status": "read_only"},
            {"path": str(N3_ABLATION.relative_to(ROOT)), "used": True, "mutation_status": "read_only"},
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
            {"guardrail": "new fitting/tuning/model selection", "mutation": False},
            {"guardrail": "source/property release or repair execution", "mutation": False},
        ],
        ["guardrail", "mutation"],
    )

    d4_score = next(row for row in scoreboard_rows if row["tested_model_form_id"] == "D4_M3_segment_offsets_min2_train")
    ready_count = sum(1 for row in gate_rows if row["source_bounded_candidate_ready"])
    summary = {
        "task": TASK,
        "decision": "d4_segment_signal_explained_as_empirical_upper_bound_no_source_bounded_candidate",
        "target_segments": len(TARGET_SEGMENTS),
        "segment_rows": len(segment_rows),
        "candidate_rows": len(gate_rows),
        "source_bounded_candidate_ready_rows": ready_count,
        "d4_transfer_rmse_K": float(d4_score["transfer_rmse_K"]),
        "d4_transfer_mean_signed_error_K": float(d4_score["transfer_mean_signed_error_K"]),
        "d4_transfer_rmse_reduction_pct": float(d4_score["m3_transfer_rmse_reduction_pct"]),
        "publication_use": "diagnostic_segment_source_placement_priority_only",
        "admission_status": "fail_closed_not_admitted",
    }
    write_json(OUT / "summary.json", summary)

    readme = f"""---
provenance:
  - {str(SENSOR_ERRORS.relative_to(ROOT))}
  - {str(SOURCE_PROVENANCE.relative_to(ROOT))}
  - {str(PASSIVE_SOURCE.relative_to(ROOT))}
tags: [model-form, d4, segment-source-placement, source-bounded-gate, thesis]
related:
  - .agent/status/2026-07-22_{TASK}.md
  - .agent/journal/2026-07-22/mf-d4-segment-source-placement-evidence-gate.md
task: {TASK}
date: 2026-07-22
role: Thermal-modeling / Forward-pred / Tester / Writer / Reviewer
type: work_product
status: complete
---
# D4 Segment Source-Placement Evidence Gate

This package tests whether the best diagnostic residual form,
`D4_M3_segment_offsets_min2_train`, can be explained by independent
source/geometry evidence. It does not fit a new model, release source/property
terms, execute a repair, or admit D4.

## Decision

`D4` remains an empirical upper-bound diagnostic. No source-bounded local
source-placement candidate is ready for freeze review.

The evidence is useful: D4 reduced transfer RMSE to
`{float(d4_score["transfer_rmse_K"]):.6g} K`, a
`{float(d4_score["m3_transfer_rmse_reduction_pct"]):.6g} %` reduction versus
M3. But the independent source/property and geometry release gates remain
closed for all target segments.

## Outputs

- `segment_residual_map.csv`
- `independent_source_heat_path_evidence.csv`
- `runtime_legality_matrix.csv`
- `source_bounded_candidate_gate.csv`
- `publication_claim_boundary.csv`
- `source_manifest.csv`
- `no_mutation_guardrails.csv`
- `summary.json`
"""
    (OUT / "README.md").write_text(readme)


if __name__ == "__main__":
    main()
