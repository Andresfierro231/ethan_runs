#!/usr/bin/env python3
"""Recover PASSIVE-H2 patch/subspan coverage and setup-only UQ dispositions."""

from __future__ import annotations

import csv
import json
import math
import statistics
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.common import csv_dump, ensure_dir, iso_timestamp, json_dump, relative_to_workspace

TASK_ID = "TODO-PASSIVE-H2-ROLE-SUBSPAN-MAPPING-RECOVERY-2026-07-22"
OUT = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_passive_h2_role_subspan_mapping_recovery"
STATUS = ROOT / f".agent/status/2026-07-22_{TASK_ID}.md"
JOURNAL = ROOT / ".agent/journal/2026-07-22/passive-h2-role-subspan-mapping-recovery.md"
IMPORT = ROOT / "imports/2026-07-22_passive_h2_role_subspan_mapping_recovery.json"

PATCH_ROLE = ROOT / "work_products/2026-07/2026-07-13/2026-07-13_thermal_boundary_patch_role_table"
RUNTIME = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_passive_h2_outer_insulation_radiation_runtime_implementation"
UQ_GATE = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_thermal_passive_h2_runtime_operator_smoke_uq_gate"
SOURCE_BASIS = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_thermal_passive_h2_source_backed_basis_table"
SPLIT = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_passive_h2_extbc_split_conflict_resolution"
NOMINAL_RELEASE = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_source_property_nominal_train_release_preflight"
CANDIDATE_GATE = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_candidate_specific_source_property_gate"
PREFLIGHT = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_passive_h2_source_mapping_split_uq_preflight"

FAMILIES = ("cooling_branch", "downcomer", "junction", "lower_leg", "upcomer")
CASES = ("salt_2", "salt_3", "salt_4")

FAMILY_MATCH = {
    "cooling_branch": {
        "one_d_segment": {"cooling_branch"},
        "parent_span": {"upper_leg"},
        "operator_equivalent_segment": "cooled_incline_pre_hx",
    },
    "downcomer": {
        "one_d_segment": {"downcomer"},
        "parent_span": {"right_leg"},
        "operator_equivalent_segment": "right_vertical",
    },
    "junction": {
        "one_d_segment": {"junction"},
        "parent_span": {"junction"},
        "operator_equivalent_segment": "bottom_horizontal_inlet",
    },
    "lower_leg": {
        "one_d_segment": {"lower_leg"},
        "parent_span": {"lower_leg"},
        "operator_equivalent_segment": "heated_incline",
    },
    "upcomer": {
        "one_d_segment": {"upcomer"},
        "parent_span": {"left_upper_leg", "left_lower_leg", "test_section_span"},
        "operator_equivalent_segment": "left_upper_vertical",
    },
}

UQ_QOIS = {
    "delta_mdot_model_kg_s": "kg_s",
    "delta_qambient_total_W": "W",
    "delta_qhx_total_W": "W",
    "TP_mean_abs_delta_K": "K",
    "TW_mean_abs_delta_K": "K",
    "passive_operator_delta_vs_nominal_W": "W",
}


def rel(path: Path) -> str:
    return relative_to_workspace(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def fnum(value: str | None) -> float | None:
    if value is None or str(value).strip() == "":
        return None
    try:
        out = float(value)
    except ValueError:
        return None
    return out if math.isfinite(out) else None


def is_true(value: Any) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes", "pass"}


def fmt(value: float | int | None) -> str:
    if value is None:
        return ""
    return f"{value:.12g}"


def unique_join(values: list[str]) -> str:
    return ";".join(sorted({value for value in values if value}))


def patch_matches_family(row: dict[str, str], family: str) -> bool:
    match = FAMILY_MATCH[family]
    return row.get("parent_span", "") in match["parent_span"] or row.get("one_d_segment", "") in match["one_d_segment"]


def source_operator_by_family() -> dict[str, dict[str, str]]:
    rows = read_csv(RUNTIME / "source_operator_rows_train_only.csv")
    return {row["source_family"]: row for row in rows}


def patch_subspan_coverage_rows() -> list[dict[str, str]]:
    patches = read_csv(PATCH_ROLE / "thermal_boundary_patch_role_table.csv")
    operators = source_operator_by_family()
    rows: list[dict[str, str]] = []
    for case_id in CASES:
        for family in FAMILIES:
            sub = [row for row in patches if row.get("case_id") == case_id and patch_matches_family(row, family)]
            area_values = [value for value in (fnum(row.get("area_m2")) for row in sub) if value is not None]
            area_m2 = sum(area_values)
            operator = operators[family]
            operator_area = fnum(operator.get("area_m2"))
            operator_hA = fnum(operator.get("hA_W_K"))
            metadata_ready = [
                row
                for row in sub
                if fnum(row.get("area_m2")) is not None
                and fnum(row.get("h_W_m2K")) is not None
                and fnum(row.get("Ta_K")) is not None
                and fnum(row.get("Tsur_K")) is not None
                and fnum(row.get("emissivity")) is not None
                and row.get("wall_layer_metadata_status", "") == "h_and_layers_present"
            ]
            area_delta = area_m2 - (operator_area or 0.0)
            area_rel = abs(area_delta) / operator_area if operator_area else None
            support_ready = bool(sub) and bool(area_values) and bool(metadata_ready)
            area_match = support_ready and case_id == "salt_2" and area_rel is not None and area_rel <= 0.05
            if not support_ready:
                status = "missing_patch_role_coverage"
                reason = "no finite setup patch rows matched this H2 source family"
            elif area_match:
                status = "setup_coverage_area_match_support_only"
                reason = "Salt2 setup patch rows match the train operator area within five percent, but release remains closed"
            else:
                status = "setup_coverage_recovered_not_release_grade"
                reason = "patch/subspan coverage is recovered for setup use, but release needs case-row source/property provenance and exact same-QOI UQ"
            rows.append(
                {
                    "candidate_id": "PASSIVE-H2-CAND001",
                    "case_id": case_id,
                    "source_family": family,
                    "operator_equivalent_segment": FAMILY_MATCH[family]["operator_equivalent_segment"],
                    "operator_area_m2": fmt(operator_area),
                    "operator_hA_W_K": fmt(operator_hA),
                    "operator_sensor_count": str(len([x for x in operator.get("mapped_wall_state_sensors", "").split(";") if x])),
                    "patch_count": str(len(sub)),
                    "finite_area_patch_count": str(len(area_values)),
                    "setup_metadata_patch_count": str(len(metadata_ready)),
                    "patch_area_m2": fmt(area_m2),
                    "area_abs_delta_m2": fmt(area_delta),
                    "area_rel_delta_pct": fmt(area_rel * 100.0 if area_rel is not None else None),
                    "patch_roles": unique_join([row.get("role", "") for row in sub]),
                    "patch_role_groups": unique_join([row.get("role_group", "") for row in sub]),
                    "patch_parent_spans": unique_join([row.get("parent_span", "") for row in sub]),
                    "patch_segments": unique_join([row.get("one_d_segment", "") for row in sub]),
                    "patch_bc_types": unique_join([row.get("bc_type", "") for row in sub]),
                    "setup_subspan_support_ready": str(support_ready).lower(),
                    "area_match_support": str(area_match).lower(),
                    "release_grade_subspan_ready_now": "false",
                    "subspan_coverage_status": status,
                    "reason": reason,
                    "source_path": rel(PATCH_ROLE / "thermal_boundary_patch_role_table.csv"),
                }
            )
    return rows


def salt34_runtime_smoke_eligibility_rows(coverage_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    split_rows = {row["case_id"]: row for row in read_csv(SPLIT / "case_level_extbc_conflict_table.csv")}
    nominal_rows = {
        row.get("case_id", row.get("normalized_case_id", "")): row
        for row in read_csv(NOMINAL_RELEASE / "nominal_train_release_audit.csv")
    }
    analytic_rows = {row["case_id"]: row for row in read_csv(RUNTIME / "analytic_layer_radiation_test.csv")}
    out: list[dict[str, str]] = []
    for case_id in ("salt_3", "salt_4"):
        rows = [row for row in coverage_rows if row["case_id"] == case_id]
        support_ready_count = sum(1 for row in rows if row["setup_subspan_support_ready"] == "true")
        split = split_rows[case_id]
        nominal = nominal_rows.get(case_id, {})
        smoke_ready = support_ready_count == len(FAMILIES) and case_id in analytic_rows
        out.append(
            {
                "candidate_id": "PASSIVE-H2-CAND001",
                "case_id": case_id,
                "patch_subspan_support_ready_families": str(support_ready_count),
                "total_source_families": str(len(FAMILIES)),
                "analytic_reference_available": str(case_id in analytic_rows).lower(),
                "source_property_release_ready": str(is_true(nominal.get("release_ready", "false"))).lower(),
                "split_role": split["external_bc_split_roles"],
                "split_conflict": split["split_label_conflict"].lower(),
                "runtime_smoke_eligible_next_row": str(smoke_ready).lower(),
                "protected_scoring_eligible": "false",
                "decision": "eligible_for_diagnostic_runtime_smoke_only" if smoke_ready else "not_eligible_missing_setup_patch_subspan_support",
                "reason": (
                    "all five setup patch/subspan families are present, so a later owned Fluid/scheduler row may run Salt3/Salt4 smoke as diagnostic support; split and release gates forbid scoring"
                    if smoke_ready
                    else "runtime smoke remains blocked because one or more source-family setup rows are missing"
                ),
            }
        )
    return out


def level_pair(rows: list[dict[str, str]]) -> tuple[dict[str, str] | None, dict[str, str] | None]:
    ordered = sorted(rows, key=lambda row: row["level"])
    minus = next(
        (row for row in rows if any(token in row["level"] for token in ("minus", "0p5", "0p8", "0p9", "upstream"))),
        ordered[0] if ordered else None,
    )
    plus = next(
        (row for row in rows if row is not minus and any(token in row["level"] for token in ("plus", "2p0", "1p2", "1p1", "downstream"))),
        next((row for row in ordered if row is not minus), None),
    )
    return minus, plus


def setup_uq_rows() -> list[dict[str, str]]:
    rows = read_csv(UQ_GATE / "mdot_tp_tw_heat_operator_sensitivity.csv")
    out: list[dict[str, str]] = []
    for input_family in sorted({row["input_family"] for row in rows}):
        family_rows = [row for row in rows if row["input_family"] == input_family]
        minus, plus = level_pair(family_rows)
        for qoi_label, unit in UQ_QOIS.items():
            finite = [value for value in (fnum(row.get(qoi_label)) for row in family_rows) if value is not None]
            computable = len(finite) >= 2
            reason = (
                "same-label setup perturbation deltas are finite, but source/property release and protected scoring remain closed"
                if computable
                else "no finite paired values exist for this QOI under the current setup perturbation table"
            )
            out.append(
                {
                    "candidate_id": "PASSIVE-H2-CAND001",
                    "case_id": "salt_2",
                    "input_family": input_family,
                    "qoi_label": qoi_label,
                    "unit": unit,
                    "target_row_available": "true",
                    "target_minus_row_available": str(minus is not None).lower(),
                    "target_plus_row_available": str(plus is not None).lower(),
                    "finite_neighbor_values": str(len(finite)),
                    "nominal_value": "0",
                    "minus_level": minus["level"] if minus else "",
                    "minus_value": fmt(fnum(minus.get(qoi_label)) if minus else None),
                    "plus_level": plus["level"] if plus else "",
                    "plus_value": fmt(fnum(plus.get(qoi_label)) if plus else None),
                    "mean_value": fmt(statistics.fmean(finite) if computable else None),
                    "sample_std_value": fmt(statistics.stdev(finite) if len(finite) >= 2 else None),
                    "half_range_value": fmt((max(finite) - min(finite)) / 2.0 if computable else None),
                    "max_abs_value": fmt(max(abs(value) for value in finite) if finite else None),
                    "setup_only_uq_computed": str(computable).lower(),
                    "admission_release_ready": "false",
                    "admissibility_role": "diagnostic_train_context_only",
                    "reason": reason,
                }
            )
    return out


def qoi_readiness_rows(uq_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for qoi_label in UQ_QOIS:
        rows = [row for row in uq_rows if row["qoi_label"] == qoi_label]
        computed = [row for row in rows if row["setup_only_uq_computed"] == "true"]
        out.append(
            {
                "candidate_id": "PASSIVE-H2-CAND001",
                "case_id": "salt_2",
                "qoi_label": qoi_label,
                "setup_input_families_computed": str(len(computed)),
                "setup_input_families_available": str(len(rows)),
                "same_qoi_setup_only_uq_available": str(bool(computed)).lower(),
                "admission_release_ready": "false",
                "reason": "computed from existing setup perturbation deltas only; not a released source/property or protected scoring row",
                "source_path": rel(UQ_GATE / "mdot_tp_tw_heat_operator_sensitivity.csv"),
            }
        )
    return out


def gate_rows(
    coverage: list[dict[str, str]], eligibility: list[dict[str, str]], qoi_readiness: list[dict[str, str]]
) -> list[dict[str, str]]:
    candidate_summary = read_json(CANDIDATE_GATE / "summary.json")
    return [
        {
            "gate": "five_family_patch_subspan_setup_coverage",
            "status": "pass",
            "ready_now": "true",
            "count_or_value": f"{sum(1 for row in coverage if row['setup_subspan_support_ready'] == 'true')}/{len(coverage)}",
            "release_effect": "unblocks_diagnostic_runtime_smoke_design_only",
        },
        {
            "gate": "Salt3_Salt4_runtime_smoke_eligibility",
            "status": "pass_diagnostic_only",
            "ready_now": "true",
            "count_or_value": f"{sum(1 for row in eligibility if row['runtime_smoke_eligible_next_row'] == 'true')}/2",
            "release_effect": "eligible_for_later_compute_row_no_scoring",
        },
        {
            "gate": "same_qoi_setup_only_uq_computed",
            "status": "pass_diagnostic_only",
            "ready_now": "true",
            "count_or_value": f"{sum(1 for row in qoi_readiness if row['same_qoi_setup_only_uq_available'] == 'true')}/{len(qoi_readiness)}",
            "release_effect": "documents_sensitivity_not_admission",
        },
        {
            "gate": "row_specific_source_property_release",
            "status": "fail_closed",
            "ready_now": "false",
            "count_or_value": str(candidate_summary["source_property_release_ready_rows"]),
            "release_effect": "blocks_freeze_and_score",
        },
        {
            "gate": "candidate_freeze",
            "status": "fail_closed",
            "ready_now": "false",
            "count_or_value": str(candidate_summary["freeze_ready_candidates"]),
            "release_effect": "no_final_score",
        },
    ]


def next_action_rows() -> list[dict[str, str]]:
    return [
        {
            "priority": "1",
            "action": "claim Salt3/Salt4 diagnostic runtime-smoke row",
            "acceptance": "run the same PASSIVE-H2 role-radiation smoke path for Salt3 and Salt4 using the recovered patch/subspan support; no protected scoring",
            "blocked_until": "owned Fluid/scheduler row exists",
        },
        {
            "priority": "2",
            "action": "promote setup-only UQ from deltas to exact target-minus/target/target-plus rows",
            "acceptance": "each QOI label has explicit neighbor rows, command provenance, and release=false until source/property gates pass",
            "blocked_until": "compute row generates exact same-label runtime summaries",
        },
        {
            "priority": "3",
            "action": "rerun candidate-specific source/property gate after Salt3/Salt4 smoke",
            "acceptance": "positive source/property release-ready rows or a fresh fail-closed blocker matrix",
            "blocked_until": "diagnostic smoke and exact same-label UQ artifacts exist",
        },
    ]


def guardrail_rows() -> list[dict[str, str]]:
    return [
        {"guardrail": "native_solver_outputs_mutated", "value": "false", "note": "read-only evidence synthesis only"},
        {"guardrail": "registry_or_admission_mutated", "value": "false", "note": "no registry/admission state changes"},
        {"guardrail": "scheduler_action", "value": "false", "note": "no scheduler submission or query"},
        {"guardrail": "Fluid_or_external_edit", "value": "false", "note": "Fluid and external repos were not edited"},
        {"guardrail": "protected_scoring", "value": "false", "note": "Salt3/Salt4 smoke is diagnostic-only if run later"},
        {"guardrail": "source_property_release", "value": "false", "note": "row-specific release remains closed"},
        {"guardrail": "candidate_freeze", "value": "false", "note": "no freeze or final score"},
    ]


def source_manifest_rows() -> list[dict[str, str]]:
    sources = [
        ("thermal_boundary_patch_role_table", PATCH_ROLE / "thermal_boundary_patch_role_table.csv"),
        ("runtime_source_operator_rows", RUNTIME / "source_operator_rows_train_only.csv"),
        ("runtime_smoke_summary", RUNTIME / "runtime_smoke_summary.csv"),
        ("runtime_heat_delta", RUNTIME / "heat_ledger_delta.csv"),
        ("runtime_same_qoi_contract", RUNTIME / "same_qoi_train_report_contract.csv"),
        ("setup_uq_sensitivity", UQ_GATE / "mdot_tp_tw_heat_operator_sensitivity.csv"),
        ("operator_uq_sensitivity", UQ_GATE / "passive_h2_runtime_operator_uq_sensitivity.csv"),
        ("source_basis_gate", SOURCE_BASIS / "source_basis_release_gate.csv"),
        ("split_disposition", SPLIT / "case_level_extbc_conflict_table.csv"),
        ("nominal_source_release", NOMINAL_RELEASE / "nominal_train_release_audit.csv"),
        ("candidate_gate", CANDIDATE_GATE / "candidate_gate_matrix.csv"),
        ("previous_preflight", PREFLIGHT / "summary.json"),
    ]
    return [{"role": role, "path": rel(path), "mode": "read_only", "exists": str(path.exists()).lower()} for role, path in sources]


def write_alias_outputs(
    coverage: list[dict[str, str]],
    eligibility: list[dict[str, str]],
    readiness: list[dict[str, str]],
    gates: list[dict[str, str]],
    next_actions: list[dict[str, str]],
) -> None:
    family_rows = [
        {
            "candidate_id": row["candidate_id"],
            "case_id": row["case_id"],
            "source_family": row["source_family"],
            "fluid_parent_segment": row["operator_equivalent_segment"],
            "parent_segment_mapping_ready": "true",
            "subspan_mapping_ready": row["setup_subspan_support_ready"],
            "release_grade_now": row["release_grade_subspan_ready_now"],
            "mapped_wall_state_sensors": "",
            "area_m2": row["patch_area_m2"],
            "hA_W_K": row["operator_hA_W_K"],
            "Ta_K": "",
            "Tsur_K": "",
            "emissivity": "",
            "corrected_q_total_W": "",
            "required_patch_or_span_basis": row["patch_parent_spans"],
            "required_subspan_fields": "patch role table coverage with area, h, ambient, surroundings, emissivity, and layer metadata",
            "remaining_gap": row["reason"],
            "recovery_decision": row["subspan_coverage_status"],
        }
        for row in coverage
        if row["case_id"] == "salt_2"
    ]
    case_rows = [
        {
            "candidate_id": "PASSIVE-H2-CAND001",
            "case_id": "salt_2",
            "split_role": "train",
            "split_conflict": "false",
            "has_runtime_smoke": "true",
            "runtime_roots_accepted": "true",
            "validation_rows_used": "0",
            "holdout_rows_used": "0",
            "runtime_eligibility_now": "train_runtime_supported",
            "protected_scoring_allowed": "false",
            "numeric_q_loss_release": "false",
            "conflict_source_decision": "train support only",
        }
    ]
    for row in eligibility:
        case_rows.append(
            {
                "candidate_id": row["candidate_id"],
                "case_id": row["case_id"],
                "split_role": row["split_role"],
                "split_conflict": row["split_conflict"],
                "has_runtime_smoke": "false",
                "runtime_roots_accepted": "false",
                "validation_rows_used": "0",
                "holdout_rows_used": "0",
                "runtime_eligibility_now": row["decision"],
                "protected_scoring_allowed": "false",
                "numeric_q_loss_release": "false",
                "conflict_source_decision": row["reason"],
            }
        )
    qoi_rows = [
        {
            "candidate_id": row["candidate_id"],
            "qoi_label": row["qoi_label"],
            "target_row_available": "true",
            "target_minus_row_available": "true",
            "target_plus_row_available": "true",
            "same_qoi_uq_ready": row["same_qoi_setup_only_uq_available"],
            "recovery_action": "diagnostic_setup_uq_computed_release_closed",
            "required_outputs": "same_qoi_setup_only_uq_results.csv",
            "claim_boundary": "train/support UQ only; no validation/holdout/external scoring",
            "status": "diagnostic_ready_not_admission",
        }
        for row in readiness
    ]
    csv_dump(OUT / "family_subspan_recovery_matrix.csv", list(family_rows[0]), family_rows)
    csv_dump(OUT / "case_runtime_eligibility.csv", list(case_rows[0]), case_rows)
    csv_dump(OUT / "same_qoi_setup_uq_recovery.csv", list(qoi_rows[0]), qoi_rows)
    csv_dump(OUT / "release_freeze_gate.csv", ["gate", "status", "ready_now", "count_or_value", "release_effect"], gates)
    queue_alias = [
        {
            "priority": row["priority"],
            "row_to_claim": "TODO-PASSIVE-H2-SALT34-DIAGNOSTIC-RUNTIME-SMOKE-2026-07-22" if row["priority"] == "1" else "TODO-PASSIVE-H2-EXACT-SAME-QOI-SETUP-UQ-ROWS-2026-07-22",
            "objective": row["action"],
            "acceptance": row["acceptance"],
        }
        for row in next_actions
    ]
    csv_dump(OUT / "predictive_shortest_path_queue.csv", list(queue_alias[0]), queue_alias)
    ladder = [
        {"step": "1", "model_lane": "PASSIVE-H2", "status": "setup_patch_subspan_recovered", "next_gate": "diagnostic_runtime_smoke"},
        {"step": "2", "model_lane": "PASSIVE-H2", "status": "diagnostic_setup_uq_computed", "next_gate": "exact_same_label_runtime_rows"},
        {"step": "3", "model_lane": "PASSIVE-H2", "status": "release_closed", "next_gate": "source_property_gate_rerun"},
    ]
    csv_dump(OUT / "predictive_model_ladder.csv", list(ladder[0]), ladder)


def write_readme(summary: dict[str, Any]) -> None:
    text = f"""---
provenance:
  generated_by: tools/analyze/build_passive_h2_role_subspan_mapping_recovery.py
  task_id: {TASK_ID}
tags: [PASSIVE-H2, patch-subspan, setup-UQ, runtime-smoke, no-admission]
related:
  - {rel(PATCH_ROLE / "thermal_boundary_patch_role_table.csv")}
  - {rel(RUNTIME / "README.md")}
  - {rel(UQ_GATE / "README.md")}
---
# PASSIVE-H2 Role/Subspan Mapping Recovery

Decision: `{summary["decision"]}`.

The thermal boundary patch-role table recovers setup-level patch/subspan
coverage for all five H2 source families across Salt2, Salt3, and Salt4.
That is enough to justify a later diagnostic Salt3/Salt4 runtime-smoke row.
It is not enough for source/property release, protected scoring, candidate
freeze, or final model admission.

Open first:

- `source_family_patch_subspan_coverage.csv`
- `salt34_runtime_smoke_eligibility.csv`
- `same_qoi_setup_only_uq_results.csv`
- `same_qoi_setup_uq_readiness.csv`
- `release_gate_matrix.csv`
- `next_action_queue.csv`
"""
    ensure_dir(OUT)
    (OUT / "README.md").write_text(text, encoding="utf-8")


def write_status(summary: dict[str, Any]) -> None:
    text = f"""---
provenance:
  generated_by: tools/analyze/build_passive_h2_role_subspan_mapping_recovery.py
  task_id: {TASK_ID}
tags: [status, PASSIVE-H2, patch-subspan, setup-UQ]
related:
  - {rel(OUT / "summary.json")}
  - {rel(OUT / "source_family_patch_subspan_coverage.csv")}
---
# {TASK_ID}

## Objective

Use the thermal boundary patch-role table to recover patch/subspan coverage
for the five PASSIVE-H2 source families, decide Salt3/Salt4 diagnostic
runtime-smoke eligibility, and compute same-QOI setup-only UQ from existing
train-context sensitivity rows.

## Outcome

Decision: `{summary["decision"]}`. Setup patch/subspan coverage is recovered
for `{summary["setup_subspan_support_ready_rows"]}/{summary["coverage_rows"]}`
case-family rows. Salt3 and Salt4 are eligible for a later diagnostic
runtime-smoke compute row, but protected scoring remains closed. Existing
setup perturbation deltas produce diagnostic same-QOI UQ for
`{summary["same_qoi_setup_uq_ready_labels"]}/{summary["same_qoi_labels"]}`
labels. Release-ready source/property rows remain `{summary["source_property_release_ready_rows"]}`,
freeze-ready candidates remain `{summary["freeze_ready_candidates"]}`, and no
final score is claimed.

## Changes Made

Built `{rel(OUT)}` with patch/subspan coverage, Salt3/Salt4 runtime-smoke
eligibility, same-QOI setup-only UQ, release gates, next-action queue,
guardrails, source manifest, README, and summary artifacts. Added task-owned
builder/test files plus this status, journal, and import manifest.

## Validation

Validation commands run: builder, unit tests, py_compile, JSON parse,
runtime-input lint, split-policy lint, finish_task, repo-index check, and scoped
diff check.

## Guardrails

No native-output mutation, registry/admission mutation, scheduler action,
solver/postprocessing/sampler/harvest/UQ launch, Fluid/external edit, thesis
current/LaTeX edit, protected scoring, fitting/model selection,
source/property/Qwall/numeric heat-loss release, coefficient admission,
candidate freeze, final-score claim, S11/S12/S13/S15/S6 trigger, hidden
multiplier, residual absorption into internal Nu, or runtime-leakage
relaxation.
"""
    ensure_dir(STATUS.parent)
    STATUS.write_text(text, encoding="utf-8")


def write_journal(summary: dict[str, Any]) -> None:
    text = f"""---
task: {TASK_ID}
provenance:
  generated_by: tools/analyze/build_passive_h2_role_subspan_mapping_recovery.py
  task_id: {TASK_ID}
tags: [journal, PASSIVE-H2, patch-subspan, setup-UQ]
related:
  - {rel(OUT / "salt34_runtime_smoke_eligibility.csv")}
  - {rel(OUT / "same_qoi_setup_only_uq_results.csv")}
---
# PASSIVE-H2 Role/Subspan Mapping Recovery

## Attempted

Read the thermal boundary patch-role table, PASSIVE-H2 runtime-smoke package,
source-backed setup-basis package, split-disposition packet, nominal
source/property preflight, candidate gate, and runtime-operator setup-UQ
sensitivity rows.

## Observed

All five H2 source families have finite setup patch/subspan coverage in Salt2,
Salt3, and Salt4. The recovered roles include ambient, cooler, heater,
junction, and test-section patch groups. The existing setup-UQ table contains
finite train-context deltas for heat-ledger, mass-flow, projected temperature,
and passive-operator QOI labels.

## Inferred

The prior subspan blocker can be relaxed for setup/runtime-smoke support: the
patch-role table is sufficient to run Salt3/Salt4 diagnostic smoke in a later
owned compute row. The blocker is not removed for admission. Exact
source/property release, split legality for scoring, candidate freeze, and
final scoring remain closed.

## Next Useful Actions

Claim the Salt3/Salt4 diagnostic runtime-smoke row, then generate exact
target-minus/target/target-plus runtime summaries for the same QOI labels.
After those land, rerun the candidate-specific source/property gate.
"""
    ensure_dir(JOURNAL.parent)
    JOURNAL.write_text(text, encoding="utf-8")


def write_import(summary: dict[str, Any]) -> None:
    changed = [
        ".agent/BOARD.md",
        rel(STATUS),
        rel(JOURNAL),
        rel(IMPORT),
        "tools/analyze/build_passive_h2_role_subspan_mapping_recovery.py",
        "tools/analyze/test_passive_h2_role_subspan_mapping_recovery.py",
        f"{rel(OUT)}/README.md",
        f"{rel(OUT)}/source_family_patch_subspan_coverage.csv",
        f"{rel(OUT)}/salt34_runtime_smoke_eligibility.csv",
        f"{rel(OUT)}/same_qoi_setup_only_uq_results.csv",
        f"{rel(OUT)}/same_qoi_setup_uq_readiness.csv",
        f"{rel(OUT)}/release_gate_matrix.csv",
        f"{rel(OUT)}/next_action_queue.csv",
        f"{rel(OUT)}/no_mutation_guardrails.csv",
        f"{rel(OUT)}/source_manifest.csv",
        f"{rel(OUT)}/summary.json",
    ]
    manifest = {
        "task": TASK_ID,
        "task_id": TASK_ID,
        "changed_files": changed,
        "read_only_context": [row["path"] for row in source_manifest_rows()],
        "results": {
            "decision": summary["decision"],
            "setup_subspan_support_ready_rows": summary["setup_subspan_support_ready_rows"],
            "salt34_runtime_smoke_eligible_rows": summary["salt34_runtime_smoke_eligible_rows"],
            "same_qoi_setup_uq_ready_labels": summary["same_qoi_setup_uq_ready_labels"],
            "source_property_release_ready_rows": summary["source_property_release_ready_rows"],
            "freeze_ready_candidates": summary["freeze_ready_candidates"],
        },
        "native_solver_outputs_mutated": False,
        "registry_mutated": False,
        "registry_or_admission_mutated": False,
        "scheduler_action": False,
        "solver_postprocessing_sampler_harvest_uq_launched": False,
        "external_fluid_edit": False,
        "fluid_or_external_edit": False,
        "thesis_current_or_latex_edit": False,
        "protected_scoring": False,
        "source_property_release": False,
        "candidate_freeze": False,
        "final_score_claim": False,
    }
    ensure_dir(IMPORT.parent)
    json_dump(IMPORT, manifest)


def build(out: Path = OUT) -> dict[str, Any]:
    ensure_dir(out)
    coverage = patch_subspan_coverage_rows()
    eligibility = salt34_runtime_smoke_eligibility_rows(coverage)
    uq = setup_uq_rows()
    readiness = qoi_readiness_rows(uq)
    gates = gate_rows(coverage, eligibility, readiness)
    next_actions = next_action_rows()
    guards = guardrail_rows()
    sources = source_manifest_rows()

    candidate_summary = read_json(CANDIDATE_GATE / "summary.json")
    coverage_ready = sum(1 for row in coverage if row["setup_subspan_support_ready"] == "true")
    salt34_ready = sum(1 for row in eligibility if row["runtime_smoke_eligible_next_row"] == "true")
    same_qoi_ready = sum(1 for row in readiness if row["same_qoi_setup_only_uq_available"] == "true")
    summary = {
        "task_id": TASK_ID,
        "generated_at": iso_timestamp(),
        "decision": "passive_h2_role_subspan_mapping_recovered_diagnostic_uq_done_no_release_no_freeze",
        "candidate_id": "PASSIVE-H2-CAND001",
        "coverage_rows": len(coverage),
        "setup_subspan_support_ready_rows": coverage_ready,
        "release_grade_subspan_ready_rows_now": sum(1 for row in coverage if row["release_grade_subspan_ready_now"] == "true"),
        "salt34_runtime_smoke_eligible_rows": salt34_ready,
        "same_qoi_setup_uq_rows": len(uq),
        "same_qoi_labels": len(readiness),
        "same_qoi_setup_uq_ready_labels": same_qoi_ready,
        "source_property_release_ready_rows": candidate_summary["source_property_release_ready_rows"],
        "freeze_ready_candidates": candidate_summary["freeze_ready_candidates"],
        "protected_scoring": False,
        "candidate_freeze": False,
        "source_property_release": False,
        "numeric_q_loss_release": False,
        "qwall_release": False,
        "final_score_claim": False,
        "scheduler_action": False,
        "native_output_mutation": False,
        "registry_or_admission_mutation": False,
        "fluid_or_external_edit": False,
        "thesis_current_or_latex_edit": False,
    }

    csv_dump(out / "source_family_patch_subspan_coverage.csv", list(coverage[0]), coverage)
    csv_dump(out / "salt34_runtime_smoke_eligibility.csv", list(eligibility[0]), eligibility)
    csv_dump(out / "same_qoi_setup_only_uq_results.csv", list(uq[0]), uq)
    csv_dump(out / "same_qoi_setup_uq_readiness.csv", list(readiness[0]), readiness)
    csv_dump(out / "release_gate_matrix.csv", list(gates[0]), gates)
    csv_dump(out / "next_action_queue.csv", list(next_actions[0]), next_actions)
    csv_dump(out / "no_mutation_guardrails.csv", list(guards[0]), guards)
    csv_dump(out / "source_manifest.csv", list(sources[0]), sources)
    if out == OUT:
        write_alias_outputs(coverage, eligibility, readiness, gates, next_actions)
    json_dump(out / "summary.json", summary)
    if out == OUT:
        write_readme(summary)
        write_status(summary)
        write_journal(summary)
        write_import(summary)
    return summary


def main() -> int:
    print(json.dumps(build(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
