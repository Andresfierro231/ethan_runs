#!/usr/bin/env python3
"""Build H2/S13 blocker-burndown evidence contracts."""

from __future__ import annotations

import csv
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.common import csv_dump, ensure_dir, iso_timestamp, json_dump, relative_to_workspace

TASK_ID = "TODO-H2-S13-MODELFORM-BLOCKER-BURNDOWN-2026-07-22"
OUT = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_h2_s13_modelform_blocker_burndown"
STATUS = ROOT / f".agent/status/2026-07-22_{TASK_ID}.md"
JOURNAL = ROOT / ".agent/journal/2026-07-22/h2-s13-modelform-blocker-burndown.md"
IMPORT = ROOT / "imports/2026-07-22_h2_s13_modelform_blocker_burndown.json"

EXTBC = ROOT / "work_products/2026-07/2026-07-13/2026-07-13_predictive_external_bc_implementation_wave/cfd_external_boundary_dictionary.csv"
PATCH_SEG = ROOT / "work_products/2026-07/2026-07-13/2026-07-13_thermal_boundary_patch_role_table/segment_reduction_inputs.csv"
PATCH_TABLE = ROOT / "work_products/2026-07/2026-07-13/2026-07-13_thermal_boundary_patch_role_table/thermal_boundary_patch_role_table.csv"
SOURCE_FLAGS = ROOT / "work_products/2026-07/2026-07-13/2026-07-13_litrev_source_envelope/source_overlap_flags.csv"
SOURCE_BASIS = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_thermal_passive_h2_source_backed_basis_table/passive_h2_source_backed_basis_table.csv"
SUBSPAN = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_passive_h2_role_subspan_mapping_recovery/source_family_patch_subspan_coverage.csv"
RUNTIME_GATE = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_passive_h2_source_property_gate_rerun_with_salt34_smoke/three_case_runtime_evidence.csv"
RUNTIME_SUMMARY = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_passive_h2_source_property_gate_rerun_with_salt34_smoke/summary.json"
S13_CLEAN = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_s13_clean_sampler_gci_readiness/summary.json"
S13_STRICT = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_s13_strict_coarse_nogo_contract/summary.json"
S13_QOI = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_s13_strict_coarse_nogo_contract/qoi_formal_gci_no_go_matrix.csv"
TRAINTEST = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_passive_h2_salt14_pm5_valsalt2_diagnostic_traintest/summary.json"
MASTER_DIAGNOSTIC = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_thesis_master_model_form_scoreboard/diagnostic_tested_model_form_scoreboard.csv"
HX_DUTY = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_hx_coupled_fluid_evaluation_scheduler/coupled_fluid_output/duty_scorecard.csv"
HX_SUMMARY = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_hx_coupled_fluid_evaluation_scheduler/summary.json"
M0_SUMMARY = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_m0_setup_only_baseline_prediction_scorecard/summary.json"
CAND001_SUMMARY = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_pressure_cand001_terminal_endpoint_readiness_gate/summary.json"
TRAINTEST_SPLIT = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_passive_h2_salt14_pm5_valsalt2_diagnostic_traintest/case_split_contract.csv"
TRAINTEST_FIT = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_passive_h2_salt14_pm5_valsalt2_diagnostic_traintest/fit_and_score_decision.csv"
S13_ENDPOINT_SUMMARY = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_s13_endpoint_face_geometry_release_mask_recovery/summary.json"
S13_ENDPOINT_GAPS = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_s13_endpoint_face_geometry_release_mask_recovery/release_mask_schema_gap.csv"
S13_ENDPOINT_MATRIX = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_s13_endpoint_face_geometry_release_mask_recovery/endpoint_face_geometry_recovery_matrix.csv"
SCOREBOARD_TESTED = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_thesis_master_model_form_scoreboard/diagnostic_tested_model_form_scoreboard.csv"
SCOREBOARD_RECOMMENDED = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_thesis_master_model_form_scoreboard/recommended_model_forms_to_try.csv"

PASSIVE_FAMILIES = ("cooling_branch", "downcomer", "junction", "lower_leg", "upcomer")
FAMILY_SPANS = {
    "cooling_branch": ("upper_leg",),
    "downcomer": ("right_leg",),
    "junction": ("junction",),
    "lower_leg": ("lower_leg",),
    "upcomer": ("left_upper_leg", "test_section_span"),
}
PROPERTY_MODE = "jin_viscosity_parida_cp_santini_k"


def rel(path: Path) -> str:
    return relative_to_workspace(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def truth(value: Any) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes", "pass"}


def f(value: Any, default: float = 0.0) -> float:
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return default


def fmt(value: float) -> str:
    return f"{value:.12g}"


def maybe_float(value: Any) -> float | None:
    try:
        out = float(str(value).strip())
    except (TypeError, ValueError):
        return None
    return out if out == out else None


def signed_pct(predicted: float | None, target: float | None) -> str:
    if predicted is None or target is None or abs(target) < 1.0e-12:
        return ""
    return fmt(100.0 * (predicted - target) / target)


def normalize_csv(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = "\n".join(line.rstrip(" \t") for line in text.split("\n"))
    path.write_text(text, encoding="utf-8")


def join_unique(values: list[str]) -> str:
    return ";".join(sorted({value for value in values if value}))


def by_key(rows: list[dict[str, str]], *fields: str) -> dict[tuple[str, ...], dict[str, str]]:
    return {tuple(row.get(field, "") for field in fields): row for row in rows}


def source_envelope_status(case_id: str, source_family: str, source_flags: list[dict[str, str]]) -> dict[str, str]:
    spans = FAMILY_SPANS[source_family]
    matches = [
        row
        for row in source_flags
        if row.get("case_id") == case_id
        and row.get("property_mode") == PROPERTY_MODE
        and row.get("span") in spans
    ]
    if source_family == "junction":
        return {
            "strict_source_envelope_status": "blocked_no_junction_branch_source_envelope_row",
            "strict_source_envelope_pass": "false",
            "source_envelope_gap": "junction is a grouped diagnostic/stub family absent from branch source-envelope table",
            "source_envelope_sources": "",
        }
    statuses = sorted({row.get("overlap_status", "") for row in matches if row.get("overlap_status")})
    recommendations = sorted({row.get("admission_recommendation", "") for row in matches if row.get("admission_recommendation")})
    sources = sorted({row.get("provenance_author_title", "") for row in matches if row.get("provenance_author_title")})
    strict_pass = bool(matches) and statuses == ["inside"] and all("promote" in rec for rec in recommendations)
    if strict_pass:
        status = "strict_pass"
        gap = ""
    elif not matches:
        status = "blocked_missing_source_envelope_rows"
        gap = "no row-specific source-envelope rows found for required spans"
    else:
        status = "blocked_mixed_outside_unknown_or_conversion_pending"
        gap = "observed overlap statuses/recommendations do not form a strict source-envelope admission pass"
    return {
        "strict_source_envelope_status": status,
        "strict_source_envelope_pass": str(strict_pass).lower(),
        "source_envelope_gap": gap,
        "source_envelope_sources": " | ".join(sources),
    }


def provenance_rows() -> list[dict[str, str]]:
    extbc = by_key(read_csv(EXTBC), "case_id", "one_d_segment", "role")
    subspan = by_key(read_csv(SUBSPAN), "case_id", "source_family")
    basis = by_key(read_csv(SOURCE_BASIS), "source_family")
    flags = read_csv(SOURCE_FLAGS)
    rows: list[dict[str, str]] = []
    for coverage in read_csv(SUBSPAN):
        case_id = coverage["case_id"]
        source_family = coverage["source_family"]
        passive = extbc.get((case_id, source_family, "ambient_wall")) or extbc.get((case_id, source_family, "junction_other"), {})
        family_basis = basis.get((source_family,), {})
        source_status = source_envelope_status(case_id, source_family, flags)
        passive_area = f(passive.get("area_m2"))
        operator_area = f(coverage.get("operator_area_m2"))
        all_role_area = f(coverage.get("patch_area_m2"))
        passive_delta_pct = abs(passive_area - operator_area) / operator_area * 100 if operator_area else 100.0
        source_sink_excluded_area = max(all_role_area - passive_area, 0.0)
        setup_fields = all(
            passive.get(field, "").strip()
            for field in ("area_m2", "hA_W_K", "h_W_m2K", "Ta_K", "Tsur_K", "emissivity", "thicknessLayers", "kappaLayerCoeffs")
        )
        provenance_ready = setup_fields and bool(passive.get("source_paths")) and bool(family_basis.get("source_paths"))
        role_filtered_subspan_ready = (
            truth(coverage.get("setup_subspan_support_ready"))
            and passive_delta_pct <= 5.0
            and passive.get("support_status") == "ready_for_fluid_api_consumption"
            and setup_fields
        )
        setup_property_ready = provenance_ready and role_filtered_subspan_ready
        strict_pass = truth(source_status["strict_source_envelope_pass"])
        admission_ready = setup_property_ready and strict_pass
        blocker = "none" if admission_ready else "strict_source_envelope_not_admission_ready"
        if not role_filtered_subspan_ready:
            blocker = "role_filtered_subspan_or_property_fields_incomplete"
        rows.append(
            {
                "candidate_id": "PASSIVE-H2-CAND001",
                "case_id": case_id,
                "split_role": passive.get("validation_split_role", ""),
                "source_family": source_family,
                "operator_equivalent_segment": coverage.get("operator_equivalent_segment", ""),
                "passive_role": passive.get("role", ""),
                "passive_support_status": passive.get("support_status", ""),
                "operator_area_m2": coverage.get("operator_area_m2", ""),
                "all_role_patch_area_m2": coverage.get("patch_area_m2", ""),
                "all_role_area_delta_pct": coverage.get("area_rel_delta_pct", ""),
                "passive_role_filtered_area_m2": passive.get("area_m2", ""),
                "passive_role_area_delta_pct": fmt(passive_delta_pct),
                "source_sink_excluded_area_m2": fmt(source_sink_excluded_area),
                "excluded_source_sink_roles": "none" if source_sink_excluded_area == 0 else "cooler/heater/test_section_or_other_nonpassive_patch_roles",
                "hA_W_K": passive.get("hA_W_K", ""),
                "h_W_m2K": passive.get("h_W_m2K", ""),
                "Ta_K": passive.get("Ta_K", ""),
                "Tsur_K": passive.get("Tsur_K", ""),
                "emissivity": passive.get("emissivity", ""),
                "thicknessLayers": passive.get("thicknessLayers", ""),
                "kappaLayerCoeffs": passive.get("kappaLayerCoeffs", ""),
                "property_mode": PROPERTY_MODE,
                "property_label_status": "row_specific_setup_property_fields_present" if setup_fields else "missing_setup_property_fields",
                "source_family_provenance_status": "row_specific_source_paths_present" if provenance_ready else "missing_source_paths",
                "setup_property_provenance_ready": str(setup_property_ready).lower(),
                "release_grade_subspan_evidence_recovered": str(role_filtered_subspan_ready).lower(),
                **source_status,
                "source_property_admission_release_ready": str(admission_ready).lower(),
                "source_property_release_allowed_now": "false",
                "qwall_or_numeric_q_loss_release_allowed_now": "false",
                "candidate_freeze_allowed_now": "false",
                "primary_remaining_blocker": blocker,
                "provenance_paths": " | ".join(
                    path
                    for path in [
                        rel(EXTBC),
                        rel(PATCH_SEG),
                        rel(PATCH_TABLE),
                        rel(SOURCE_BASIS),
                        rel(SOURCE_FLAGS),
                    ]
                    if path
                ),
            }
        )
    rows.sort(key=lambda row: (row["case_id"], row["source_family"]))
    return rows


def source_envelope_gap_rows() -> list[dict[str, str]]:
    flags = read_csv(SOURCE_FLAGS)
    rows: list[dict[str, str]] = []
    for case_id in ("salt_2", "salt_3", "salt_4"):
        for family, spans in FAMILY_SPANS.items():
            matches = [
                row
                for row in flags
                if row.get("case_id") == case_id
                and row.get("property_mode") == PROPERTY_MODE
                and row.get("span") in spans
            ]
            if not matches:
                rows.append(
                    {
                        "case_id": case_id,
                        "source_family": family,
                        "span": ";".join(spans),
                        "candidate_source": "",
                        "overlap_status": "missing",
                        "admission_recommendation": "do_not_promote",
                        "gap": "no strict row-specific source-envelope evidence",
                    }
                )
                continue
            for row in matches:
                promotes = row.get("overlap_status") == "inside" and "promote" in row.get("admission_recommendation", "")
                rows.append(
                    {
                        "case_id": case_id,
                        "source_family": family,
                        "span": row.get("span", ""),
                        "candidate_source": row.get("candidate_source", ""),
                        "overlap_status": row.get("overlap_status", ""),
                        "admission_recommendation": row.get("admission_recommendation", ""),
                        "gap": "" if promotes else "not_strict_promote_row",
                    }
                )
    return rows


def blocker_summary_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    total = len(rows)
    setup_ready = sum(truth(row["setup_property_provenance_ready"]) for row in rows)
    subspan_ready = sum(truth(row["release_grade_subspan_evidence_recovered"]) for row in rows)
    strict_pass = sum(truth(row["strict_source_envelope_pass"]) for row in rows)
    admission_ready = sum(truth(row["source_property_admission_release_ready"]) for row in rows)
    return [
        {
            "blocker": "release_grade_subspan_rows",
            "before": "0/15 recovered under all-role comparison",
            "after": f"{subspan_ready}/{total} recovered under passive-role-filtered comparison",
            "status": "unblocked_for_evidence_contract" if subspan_ready == total else "still_blocking",
            "release_effect": "removes false area-mismatch blocker; no source/property release in this task",
        },
        {
            "blocker": "row_specific_property_labels",
            "before": "family-level setup basis only",
            "after": f"{setup_ready}/{total} case/family rows have area, hA, h, Ta, Tsur, emissivity, and layer metadata",
            "status": "unblocked_for_setup_property_provenance" if setup_ready == total else "still_blocking",
            "release_effect": "setup-property provenance is now row-specific; admission remains closed",
        },
        {
            "blocker": "source_family_provenance",
            "before": "source paths existed in separate packages",
            "after": f"{setup_ready}/{total} case/family rows carry direct provenance paths",
            "status": "unblocked_for_traceability" if setup_ready == total else "still_blocking",
            "release_effect": "traceability improved; no mutation or release",
        },
        {
            "blocker": "strict_source_envelope",
            "before": "mixed/outside/unknown correlation source-envelope evidence",
            "after": f"{strict_pass}/{total} strict-pass rows",
            "status": "still_blocking",
            "release_effect": "blocks admission/freeze until a setup-operator-specific source-envelope policy or conversion audit passes",
        },
        {
            "blocker": "source_property_admission_release",
            "before": "0 release-ready rows",
            "after": f"{admission_ready}/{total} release-ready rows",
            "status": "still_blocking",
            "release_effect": "source/property release, final scoring, and candidate freeze remain closed",
        },
    ]


def support_contract_rows() -> list[dict[str, str]]:
    runtime = read_json(RUNTIME_SUMMARY)
    s13_clean = read_json(S13_CLEAN)
    s13_strict = read_json(S13_STRICT)
    traintest = read_json(TRAINTEST)
    return [
        {
            "contract": "PASSIVE-H2 exact non-scoring diagnostic runner",
            "current_evidence": f"runtime_completed={runtime.get('runtime_completed_case_rows', 0)}/3; nonzero={runtime.get('runtime_nonzero_case_rows', 0)}/3",
            "unblocked": "yes_diagnostic_only",
            "still_blocked": "Salt1 runtime prediction, source/property admission, protected scoring, candidate freeze",
            "source_path": rel(RUNTIME_GATE),
        },
        {
            "contract": "PASSIVE-H2 train/test diagnostic shell",
            "current_evidence": f"train_runtime_rows={traintest.get('train_runtime_rows_available', 0)}; fit_ready_rows={traintest.get('train_fit_ready_rows', 0)}; score_values={traintest.get('score_values_emitted', 0)}",
            "unblocked": "yes_for_diagnostic_inventory",
            "still_blocked": "fit/model-selection/final-score remains closed",
            "source_path": rel(TRAINTEST),
        },
        {
            "contract": "S13 endpoint exact-field regeneration",
            "current_evidence": f"released_endpoint_masks={read_json(S13_ENDPOINT_SUMMARY).get('released_endpoint_masks', 0)}; mandatory_gap_rows={read_json(S13_ENDPOINT_SUMMARY).get('mandatory_gap_rows', 0)}",
            "unblocked": "yes_as_regeneration_contract_only",
            "still_blocked": "exact area/area-vector/owner-cell/normal/sign fields; strict coarse/GCI admission remains separate active lane",
            "source_path": rel(S13_ENDPOINT_SUMMARY),
        },
        {
            "contract": "D4/D3/D2 physical-successor admission preflight",
            "current_evidence": f"clean_sampler_successful_pairs={s13_clean.get('successful_case_mesh_pairs', 0)}; formal_gci_ready_rows={s13_strict.get('formal_gci_ready_rows', 0)}",
            "unblocked": "yes_as_preflight_only",
            "still_blocked": "physical source-bounded implementation, source/property release, same-QOI UQ, formal admission",
            "source_path": rel(SCOREBOARD_TESTED),
        },
    ]


def h2_exact_nonscoring_runner_contract_rows() -> list[dict[str, str]]:
    runtime_by_case = {row.get("case_id", ""): row for row in read_csv(RUNTIME_GATE)}
    split_by_case = {row.get("case_key", ""): row for row in read_csv(TRAINTEST_SPLIT)}
    cases = [
        ("salt1_nominal", "salt_1", "train", "missing_runtime_prediction"),
        ("salt2_jin_nominal", "salt_2", "train", "runtime_ready"),
        ("salt3_jin_nominal", "salt_3", "validation", "runtime_ready_diagnostic_only"),
        ("salt4_nominal", "salt_4", "holdout_or_transfer", "runtime_ready_diagnostic_only"),
        ("salt2_lo5q", "salt2_lo5q", "blind_holdout_pm5q", "target_only_no_frozen_prediction"),
        ("salt2_hi5q", "salt2_hi5q", "blind_holdout_pm5q", "target_only_no_frozen_prediction"),
        ("val_salt2", "val_salt2", "external_or_blind_test", "target_only_no_frozen_prediction"),
    ]
    rows: list[dict[str, str]] = []
    for case_key, case_id, role, status in cases:
        runtime = runtime_by_case.get(case_id, {})
        split = split_by_case.get(case_key, {})
        runtime_ready = truth(runtime.get("runtime_completed")) and truth(runtime.get("accepted_roots"))
        if status == "missing_runtime_prediction":
            reason = "Salt1 is in the requested train set but lacks a PASSIVE-H2 runtime prediction artifact."
        elif status == "target_only_no_frozen_prediction":
            reason = "Target evidence exists only for future score use; no admitted frozen prediction exists."
        elif role == "train":
            reason = "Runtime evidence can support a train-only diagnostic runner contract."
        else:
            reason = "Runtime evidence supports feasibility only because protected split roles cannot be used for scoring or selection."
        rows.append(
            {
                "case_key": case_key,
                "case_id": case_id,
                "requested_or_split_role": split.get("final_scorecard_partition", role),
                "runner_kind": "exact_non_scoring_diagnostic",
                "runtime_ready_now": str(runtime_ready).lower(),
                "fit_allowed_now": "false",
                "score_allowed_now": "false",
                "source_property_release_allowed_now": "false",
                "candidate_freeze_allowed_now": "false",
                "required_runtime_inputs": "setup hA/area/Ta/Tsur/emissivity/layers plus model-predicted wall/fluid state",
                "forbidden_runtime_inputs": "wallHeatFlux; CFD mdot; realized Qwall; protected TP/TW targets; hidden multiplier",
                "required_outputs": "mdot, TP/TW prediction shell, heat ledger deltas, passive-operator state, runtime-input audit",
                "status": status,
                "reason": reason,
                "evidence_path": rel(TRAINTEST_SPLIT) if case_key in split_by_case else rel(RUNTIME_GATE),
            }
        )
    rows.append(
        {
            "case_key": "fit_and_score_gate",
            "case_id": "PASSIVE-H2-CAND001",
            "requested_or_split_role": "candidate_gate",
            "runner_kind": "contract_gate",
            "runtime_ready_now": "true",
            "fit_allowed_now": "false",
            "score_allowed_now": "false",
            "source_property_release_allowed_now": "false",
            "candidate_freeze_allowed_now": "false",
            "required_runtime_inputs": "complete Salt1-4 legal runtime predictions plus release-grade source/property rows",
            "forbidden_runtime_inputs": "protected-row fitting or model selection",
            "required_outputs": "frozen predictions before blind score rows",
            "status": "blocked_no_fit_no_score",
            "reason": "Train-test diagnostic package reports no fit-ready rows, no frozen blind predictions, and no score values.",
            "evidence_path": rel(TRAINTEST_FIT),
        }
    )
    return rows


def s13_endpoint_exact_field_contract_rows() -> list[dict[str, str]]:
    gaps = read_csv(S13_ENDPOINT_GAPS)
    endpoints = read_csv(S13_ENDPOINT_MATRIX)
    strict = read_json(S13_STRICT)
    rows: list[dict[str, str]] = []
    for gap in gaps:
        rows.append(
            {
                "contract_area": "endpoint_release_mask_schema",
                "required_field_or_artifact": gap.get("required_field", ""),
                "current_rows_missing": gap.get("endpoint_rows_missing_field", ""),
                "required_for_release": gap.get("release_required", "True"),
                "current_status": "missing",
                "allowed_next_action": "regenerate exact endpoint field table from source mesh/face data",
                "forbidden_substitution": gap.get("forbidden_substitution", "candidate face ids only"),
                "release_or_harvest_allowed_now": "false",
                "evidence_path": rel(S13_ENDPOINT_GAPS),
            }
        )
    rows.append(
        {
            "contract_area": "endpoint_case_coverage",
            "required_field_or_artifact": "six case/endpoints with exact fields",
            "current_rows_missing": str(sum(row.get("release_mask_ready") != "True" for row in endpoints)),
            "required_for_release": "True",
            "current_status": "candidate_face_ids_only_no_release_mask",
            "allowed_next_action": "produce one exact-field row per endpoint face for salt_2/salt_3/salt_4 inlet/outlet",
            "forbidden_substitution": "throughflow cap face ids without area vectors, owner cells, and sign convention",
            "release_or_harvest_allowed_now": "false",
            "evidence_path": rel(S13_ENDPOINT_MATRIX),
        }
    )
    rows.append(
        {
            "contract_area": "same_label_coarse_dependency",
            "required_field_or_artifact": "admitted same-label coarse rows before formal GCI",
            "current_rows_missing": str(strict.get("strict_no_go_rows", 12)),
            "required_for_release": "True",
            "current_status": "formal_gci_blocked",
            "allowed_next_action": "consume only a separate completed direct same-label coarse evidence row",
            "forbidden_substitution": "formal GCI from two-level, non-admitted, or proxy coarse data",
            "release_or_harvest_allowed_now": "false",
            "evidence_path": rel(S13_STRICT),
        }
    )
    return rows


def d4_d3_d2_physical_successor_preflight_rows() -> list[dict[str, str]]:
    tested = read_csv(SCOREBOARD_TESTED)
    recommended = read_csv(SCOREBOARD_RECOMMENDED)
    rows: list[dict[str, str]] = []
    for row in tested:
        model_id = row.get("tested_model_form_id", "")
        family = next((prefix for prefix in ("D4", "D3", "D2") if model_id.startswith(prefix)), "")
        if not family:
            continue
        rec = next((item for item in recommended if item.get("model_form_to_try", "").startswith(family)), {})
        if family == "D4":
            hypothesis = "source-bounded segment/source-placement successor"
            terms = "local heat path/source placement, PASSIVE-H2 release rows, segment energy ledger"
        elif family == "D3":
            hypothesis = "wall-shape or axial-mixing physical successor"
            terms = "wall/core exchange, axial mixing, source-side heat partition"
        else:
            hypothesis = "lower-DOF physical residual-owner successor"
            terms = "setup-only bias owner, sensor projection uncertainty, conservative thermal ledger"
        rows.append(
            {
                "successor_family": family,
                "diagnostic_model_form_id": model_id,
                "physical_successor_hypothesis": hypothesis,
                "transfer_rmse_K": row.get("transfer_rmse_K", ""),
                "transfer_mean_signed_error_K": row.get("transfer_mean_signed_error_K", ""),
                "diagnostic_rank_signal": rec.get("rank", ""),
                "current_allowed_use": "physical-successor design and admission preflight only",
                "required_physical_terms": terms,
                "required_gates_before_admission": rec.get("required_gates_before_claim", "source/property release; same-QOI UQ; no protected-row tuning"),
                "admission_ready_now": "false",
                "freeze_ready_now": "false",
                "final_score_ready_now": "false",
                "forbidden_use": "admitted predictive form, protected score, empirical residual hiding",
                "next_executable_row": f"TODO-{family}-PHYSICAL-SUCCESSOR-ADMISSION-PREFLIGHT",
                "evidence_path": rel(SCOREBOARD_TESTED),
            }
        )
    rows.sort(key=lambda item: {"D4": 0, "D3": 1, "D2": 2}.get(item["successor_family"], 9))
    return rows


def next_action_rows() -> list[dict[str, str]]:
    return [
        {
            "priority": "1",
            "action": "Create Salt1 PASSIVE-H2 exact non-scoring runtime prediction contract",
            "why": "Salt1 is the missing member of the requested Salt1-4 train set.",
            "done_when": "Salt1 has a legal prediction shell with mdot/TP/TW/heat ledger outputs and no score/freeze.",
        },
        {
            "priority": "2",
            "action": "Rerun PASSIVE-H2 candidate source/property gate using passive-role-filtered subspan evidence",
            "why": "the previous 0/5 subspan result compared operator area against all segment roles; passive rows now match 15/15",
            "done_when": "gate reports release-grade subspan evidence recovered while keeping source/property admission closed unless strict envelope policy passes",
        },
        {
            "priority": "3",
            "action": "Decide strict source-envelope policy for setup-dictionary passive operator",
            "why": "current literature/correlation envelope table is not a strict pass even though setup hA/property fields are source-backed",
            "done_when": "document whether setup-dictionary provenance is sufficient for source/property release or a correlation conversion audit is required",
        },
        {
            "priority": "4",
            "action": "Claim S13 endpoint exact-field regeneration runbook or scheduler row",
            "why": "candidate face IDs still lack area, area vectors, owner cells, and sign convention.",
            "done_when": "six endpoints have exact fields or a scheduler-safe fail-closed runbook.",
        },
        {
            "priority": "5",
            "action": "Claim D4 physical successor source-bounded preflight",
            "why": "D4 is the strongest current diagnostic successor signal and needs a physical replacement for empirical offsets.",
            "done_when": "D4 successor terms are predeclared, setup-legal, source-bounded, and ready for same-QOI UQ.",
        },
    ]


def guardrail_rows() -> list[dict[str, str]]:
    return [
        {"guardrail": "native_output_mutation", "occurred": "false"},
        {"guardrail": "registry_or_admission_mutation", "occurred": "false"},
        {"guardrail": "scheduler_action", "occurred": "false"},
        {"guardrail": "solver_sampler_harvest_uq_launch", "occurred": "false"},
        {"guardrail": "Fluid_or_external_edit", "occurred": "false"},
        {"guardrail": "protected_or_final_scoring", "occurred": "false"},
        {"guardrail": "source_property_release", "occurred": "false"},
        {"guardrail": "qwall_or_numeric_q_loss_release", "occurred": "false"},
        {"guardrail": "candidate_freeze", "occurred": "false"},
    ]


def source_manifest_rows() -> list[dict[str, str]]:
    sources = [
        ("external_boundary_dictionary", EXTBC),
        ("patch_segment_reduction_inputs", PATCH_SEG),
        ("thermal_boundary_patch_role_table", PATCH_TABLE),
        ("source_backed_basis_table", SOURCE_BASIS),
        ("role_subspan_coverage", SUBSPAN),
        ("source_envelope_flags", SOURCE_FLAGS),
        ("passive_h2_runtime_gate", RUNTIME_GATE),
        ("passive_h2_runtime_summary", RUNTIME_SUMMARY),
        ("s13_clean_sampler_gci_readiness", S13_CLEAN),
        ("s13_strict_coarse_nogo", S13_STRICT),
        ("s13_qoi_formal_gci_no_go", S13_QOI),
        ("passive_h2_train_test_diagnostic", TRAINTEST),
        ("passive_h2_train_test_split_contract", TRAINTEST_SPLIT),
        ("passive_h2_train_test_fit_decision", TRAINTEST_FIT),
        ("s13_endpoint_summary", S13_ENDPOINT_SUMMARY),
        ("s13_endpoint_schema_gaps", S13_ENDPOINT_GAPS),
        ("s13_endpoint_recovery_matrix", S13_ENDPOINT_MATRIX),
        ("master_model_form_tested_scoreboard", SCOREBOARD_TESTED),
        ("master_model_form_recommended_rows", SCOREBOARD_RECOMMENDED),
        ("hx_fixed_mdot_duty_scorecard", HX_DUTY),
        ("hx_coupled_summary", HX_SUMMARY),
        ("m0_setup_only_summary", M0_SUMMARY),
        ("pressure_cand001_summary", CAND001_SUMMARY),
    ]
    return [
        {"role": role, "path": rel(path), "mode": "read_only", "exists": str(path.exists()).lower()}
        for role, path in sources
    ]


def presentable_diagnostic_score_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    wanted = {"M3_as_is", "D2_M3_sensor_kind_offsets_train", "D3_M3_wall_linear_shape_train", "D4_M3_segment_offsets_min2_train"}
    for row in read_csv(SCOREBOARD_TESTED):
        if row.get("tested_model_form_id") in wanted:
            rows.append(
                {
                    "score_id": row["tested_model_form_id"],
                    "lane": "temperature_residual_shape",
                    "score_type": "Salt2_train_fit_Salt3_4_transfer_diagnostic",
                    "case_scope": "Salt3/Salt4 transfer",
                    "metric": "all_probe_transfer_RMSE_K",
                    "score_value": row.get("transfer_rmse_K", ""),
                    "signed_or_percent_context": f"mean_signed_error_K={row.get('transfer_mean_signed_error_K', '')}; reduction_vs_M3_pct={row.get('m3_transfer_rmse_reduction_pct', '')}",
                    "thesis_claim": "diagnostic residual-shape score; motivates source-placement and wall-shape model forms",
                    "caveat": "uses Salt2 train targets for a diagnostic correction; not final predictive admission",
                    "admission_status": "diagnostic_presentable_not_admitted",
                    "source_path": rel(SCOREBOARD_TESTED),
                }
            )
    for row in read_csv(RUNTIME_GATE):
        delta = maybe_float(row.get("radiation_on_heat_ledger_delta_W"))
        target = maybe_float(row.get("radiation_target_delta_W"))
        signed_w = "" if delta is None or target is None else fmt(delta - target)
        rows.append(
            {
                "score_id": f"PASSIVE-H2_runtime_{row.get('case_id', '')}",
                "lane": "passive_h2_runtime_heat_ledger",
                "score_type": "operator_runtime_closure_ratio_diagnostic",
                "case_scope": f"{row.get('case_id', '')} {row.get('split_role', '')}",
                "metric": "radiation_delta_over_analytic_target",
                "score_value": row.get("radiation_delta_over_target", ""),
                "signed_or_percent_context": f"signed_error_W={signed_w}; signed_error_pct={signed_pct(delta, target)}",
                "thesis_claim": "PASSIVE-H2 executes and produces nonzero heat-ledger response on all three available cases",
                "caveat": "runtime diagnostic only; no source/property release, freeze, or protected score",
                "admission_status": "diagnostic_presentable_not_admitted",
                "source_path": rel(RUNTIME_GATE),
            }
        )
    for row in read_csv(HX_DUTY):
        if row.get("candidate_id") != "HX_LUMPED_UA_NTU":
            continue
        predicted = maybe_float(row.get("predicted_qhx_W"))
        target = maybe_float(row.get("target_qhx_W_for_scoring_only"))
        rows.append(
            {
                "score_id": f"HX_LUMPED_UA_NTU_fixed_mdot_duty_{row.get('case_id', '')}",
                "lane": "hx_fixed_mdot_duty",
                "score_type": "fixed_mdot_cooler_duty_diagnostic",
                "case_scope": f"{row.get('case_id', '')} {row.get('split_role', '')}",
                "metric": "cooler_duty_signed_error_W",
                "score_value": row.get("error_W", ""),
                "signed_or_percent_context": f"abs_error_W={row.get('abs_error_W', '')}; signed_error_pct={signed_pct(predicted, target)}; duty_gate={row.get('duty_gate', '')}",
                "thesis_claim": "fixed-mdot HX duty screen is presentable as cooler submodel evidence",
                "caveat": "not a coupled final score; coupled Fluid review fails with large temperature/mdot errors",
                "admission_status": "diagnostic_presentable_not_admitted",
                "source_path": rel(HX_DUTY),
            }
        )
    for row in read_csv(S13_QOI):
        if row.get("qoi_label") == "Q_wall_W":
            rows.append(
                {
                    "score_id": "S13_Q_wall_W_medium_fine_mesh_spread",
                    "lane": "s13_m5_upcomer_exchange",
                    "score_type": "mesh_spread_diagnostic_not_formal_gci",
                    "case_scope": "Salt2/Salt3/Salt4",
                    "metric": "max_medium_fine_relative_percent_vs_fine",
                    "score_value": row.get("max_medium_fine_relative_percent_vs_fine", ""),
                    "signed_or_percent_context": f"coarse_fine_pct={row.get('max_coarse_fine_relative_percent_vs_fine', '')}; formal_gci_status={row.get('formal_gci_status', '')}",
                    "thesis_claim": "S13 Q_wall_W has low-spread diagnostic evidence for an exchange-cell heat path",
                    "caveat": "formal GCI, production harvest, and coefficient admission remain blocked by missing admitted same-label coarse evidence",
                    "admission_status": "diagnostic_presentable_not_admitted",
                    "source_path": rel(S13_QOI),
                }
            )
    order = {"temperature_residual_shape": 0, "passive_h2_runtime_heat_ledger": 1, "hx_fixed_mdot_duty": 2, "s13_m5_upcomer_exchange": 3}
    rows.sort(key=lambda item: (order.get(item["lane"], 99), item["score_id"]))
    return rows


def figure_ready_diagnostic_rows(scores: list[dict[str, str]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for row in scores:
        value = maybe_float(row.get("score_value"))
        if value is None:
            continue
        rows.append(
            {
                "figure_id": "presentable_diagnostic_scores",
                "lane": row["lane"],
                "score_id": row["score_id"],
                "metric": row["metric"],
                "value": fmt(value),
                "case_scope": row["case_scope"],
                "admission_status": row["admission_status"],
                "caveat": row["caveat"],
            }
        )
    return rows


def thesis_claim_boundary_rows() -> list[dict[str, str]]:
    return [
        {"claim_id": "CLAIM-001", "claim": "D4 is the strongest current residual-shape workaround score.", "allowed": "true", "required_wording": "diagnostic transfer score, not final predictive admission", "supporting_score_ids": "D4_M3_segment_offsets_min2_train"},
        {"claim_id": "CLAIM-002", "claim": "PASSIVE-H2 has three-case runtime feasibility evidence.", "allowed": "true", "required_wording": "runtime heat-ledger response only; no source/property release", "supporting_score_ids": "PASSIVE-H2_runtime_salt_2;PASSIVE-H2_runtime_salt_3;PASSIVE-H2_runtime_salt_4"},
        {"claim_id": "CLAIM-003", "claim": "HX_LUMPED_UA_NTU is useful as fixed-mdot cooler-duty evidence but not as a coupled admitted model.", "allowed": "true", "required_wording": "fixed-mdot duty diagnostic; coupled result failed review", "supporting_score_ids": "HX_LUMPED_UA_NTU_fixed_mdot_duty_salt_3;HX_LUMPED_UA_NTU_fixed_mdot_duty_salt_4"},
        {"claim_id": "CLAIM-004", "claim": "S13 Q_wall_W is promising as diagnostic heat-path evidence.", "allowed": "true", "required_wording": "mesh-spread diagnostic, no formal GCI", "supporting_score_ids": "S13_Q_wall_W_medium_fine_mesh_spread"},
    ]


def forbidden_claim_rows() -> list[dict[str, str]]:
    return [
        {"forbidden_claim": "final predictive score", "reason": "no frozen admitted candidate; final score values remain zero"},
        {"forbidden_claim": "source/property release", "reason": "strict source-envelope/admission release rows remain zero"},
        {"forbidden_claim": "pressure/component K admission", "reason": "CAND001 endpoint readiness remains zero and active job is non-terminal"},
        {"forbidden_claim": "M0 improvement baseline", "reason": "M0 numerical prediction rows are zero"},
        {"forbidden_claim": "S13 production harvest or formal GCI", "reason": "same-label coarse evidence is not admitted"},
    ]


def write_docs(summary: dict[str, Any]) -> None:
    readme = f"""---
provenance:
  - {rel(EXTBC)}
  - {rel(SUBSPAN)}
  - {rel(SOURCE_FLAGS)}
tags: [PASSIVE-H2, S13, source-property, subspan, blocker-burndown, no-release]
related:
  - {rel(STATUS)}
  - {rel(JOURNAL)}
task: {TASK_ID}
date: 2026-07-22
role: Implementer / Tester / Writer / Reviewer
type: work_product
status: complete
---
# H2/S13 Model-Form Blocker Burndown

Decision: `{summary["decision"]}`.

The useful unblock is PASSIVE-H2 provenance: passive-role filtering recovers
release-grade subspan evidence for all Salt2/Salt3/Salt4 source-family rows.
The old area mismatch came from including source/sink roles in segment patch
area while the PASSIVE-H2 operator uses passive ambient-wall rows.

The package also publishes an exact non-scoring diagnostic H2 runner contract,
an S13 endpoint exact-field regeneration contract, and a D4/D3/D2
physical-successor admission preflight.

It also emits presentable diagnostic score tables for residual-shape transfer,
PASSIVE-H2 runtime heat-ledger response, HX fixed-mdot cooler duty, and S13
Qwall mesh spread. These rows are for thesis diagnostic figures, not final
predictive admission.

This does not release source/property admission, numeric heat loss, Qwall,
endpoint harvest, formal GCI, candidate freeze, or final score. Strict
source-envelope/admission remains closed because the correlation/literature
envelope rows are mixed, outside, unknown, or conversion-pending rather than
strict-pass.
"""
    status = f"""---
provenance:
  - {rel(OUT / "summary.json")}
tags: [status, PASSIVE-H2, S13, source-property, no-release]
related:
  - {rel(OUT / "README.md")}
task: {TASK_ID}
date: 2026-07-22
role: Implementer / Tester / Writer / Reviewer
type: status
status: complete
---
# Status: H2/S13 Model-Form Blocker Burndown

## Objective

Burn down the PASSIVE-H2 source/property provenance blocker by recovering
row-specific source envelope, property-label, source-family provenance, and
release-grade subspan evidence where existing artifacts support it.

## Outcome

Decision: `{summary["decision"]}`. Passive-role-filtered subspan evidence is
recovered for `{summary["release_grade_subspan_evidence_recovered_rows"]}/15`
rows, setup-property provenance for `{summary["setup_property_provenance_ready_rows"]}/15`,
and strict source-envelope pass rows remain `{summary["strict_source_envelope_pass_rows"]}/15`.
Source/property admission release rows remain `{summary["source_property_admission_release_ready_rows"]}/15`.
H2 exact runner contract rows are `{summary["h2_exact_nonscoring_runner_contract_rows"]}`
with fit/score allowed rows `{summary["h2_fit_allowed_rows"]}/{summary["h2_score_allowed_rows"]}`.
S13 endpoint release/harvest allowed rows are
`{summary["s13_endpoint_release_or_harvest_allowed_rows"]}`, and D4/D3/D2
admission-ready rows are `{summary["d4_d3_d2_admission_ready_rows"]}`.
Presentable diagnostic score rows are `{summary["presentable_diagnostic_score_rows"]}`;
final admitted score rows are `{summary["final_admitted_score_rows"]}`.

## Changes Made

- Added `tools/analyze/build_h2_s13_modelform_blocker_burndown.py`.
- Added `tools/analyze/test_h2_s13_modelform_blocker_burndown.py`.
- Published `{rel(OUT)}` with provenance, subspan, source-envelope gap, contract,
  guardrail, source-manifest, README, and summary artifacts.
- Added exact H2 diagnostic-runner, S13 endpoint-field regeneration, and
  D4/D3/D2 physical-successor preflight CSV contracts.
- Added presentable diagnostic score, figure-ready score, thesis claim-boundary,
  and forbidden-claim CSV tables.
- Wrote this status file, matching journal entry, and import manifest.

## Validation

- `python3.11 tools/analyze/build_h2_s13_modelform_blocker_burndown.py`
- `python3.11 -m unittest tools.analyze.test_h2_s13_modelform_blocker_burndown`
- `python3.11 -m py_compile tools/analyze/build_h2_s13_modelform_blocker_burndown.py tools/analyze/test_h2_s13_modelform_blocker_burndown.py`
- `python3.11 tools/agent/runtime_input_lint.py ...`
- `python3.11 tools/agent/split_policy_lint.py ...`
- `python3.11 tools/agent/finish_task.py --task-id {TASK_ID}`

## Guardrails

No native-output mutation, registry/admission mutation, scheduler action,
solver/postprocessing/sampler/harvest/UQ launch, Fluid/external edit,
protected/final scoring, fitting/tuning/model selection, source/property
release, Qwall/numeric heat-loss release, coefficient admission, candidate
freeze, endpoint proxy substitution, hidden multiplier, residual absorption,
or runtime-leakage relaxation.
"""
    journal = f"""---
provenance:
  - {rel(OUT / "summary.json")}
tags: [journal, PASSIVE-H2, source-property, subspan, blocker-burndown]
related:
  - {rel(STATUS)}
  - {rel(OUT / "README.md")}
task: {TASK_ID}
date: 2026-07-22
role: Implementer / Tester / Writer / Reviewer
type: journal
status: complete
---
# H2/S13 Model-Form Blocker Burndown

Attempted: joined external-boundary dictionary rows, thermal patch-role rows,
PASSIVE-H2 role/subspan recovery rows, source-backed setup-basis rows, lit-rev
source-envelope rows, and the completed Salt2/Salt3/Salt4 diagnostic runtime
gate.

Observed: the PASSIVE-H2 operator areas match the passive ambient-wall
external-boundary rows for all 15 Salt2/Salt3/Salt4 case-family rows. The
previous mismatch came from all-role segment areas that included cooler,
heater, and test-section source/sink patches.

Inferred: release-grade subspan evidence and setup-property provenance are now
recovered as evidence contracts, and a caveated diagnostic score section is now
available. Admission release remains closed because strict source-envelope/
correlation rows are not strict-pass and this task did not run UQ, protected
final scoring, freeze, or mutate any source/admission state.

Caveats: the recovered rows are not a final source/property release. They are
the input package needed to rerun the candidate gate with the corrected
passive-role-filtered interpretation.

Next useful actions: rerun the PASSIVE-H2 candidate source/property gate using
this package, then decide whether setup-dictionary provenance can satisfy the
strict source-envelope policy or whether a separate conversion audit is needed.
"""
    OUT.mkdir(parents=True, exist_ok=True)
    STATUS.parent.mkdir(parents=True, exist_ok=True)
    JOURNAL.parent.mkdir(parents=True, exist_ok=True)
    (OUT / "README.md").write_text(readme, encoding="utf-8")
    STATUS.write_text(status, encoding="utf-8")
    JOURNAL.write_text(journal, encoding="utf-8")


def write_import(summary: dict[str, Any]) -> None:
    changed = [
        rel(STATUS),
        rel(JOURNAL),
        rel(IMPORT),
        "tools/analyze/build_h2_s13_modelform_blocker_burndown.py",
        "tools/analyze/test_h2_s13_modelform_blocker_burndown.py",
    ]
    if OUT.exists():
        for path in sorted(OUT.iterdir()):
            if path.is_file() and path.suffix in {".csv", ".json", ".md"}:
                changed.append(rel(path))
    manifest = {
        "task": TASK_ID,
        "task_id": TASK_ID,
        "changed_files": changed,
        "read_only_context": [row["path"] for row in source_manifest_rows()],
        "results": summary,
        "native_solver_outputs_mutated": False,
        "registry_mutated": False,
        "scheduler_action": False,
        "external_fluid_edit": False,
        "protected_scoring": False,
        "source_property_release": False,
        "candidate_freeze": False,
        "final_score_claim": False,
        "no_scorecard_outputs": True,
        "diagnostic_score_outputs_only": True,
    }
    json_dump(IMPORT, manifest)


def build(out_dir: Path = OUT) -> dict[str, Any]:
    ensure_dir(out_dir)
    rows = provenance_rows()
    gaps = source_envelope_gap_rows()
    summary_rows = blocker_summary_rows(rows)
    contracts = support_contract_rows()
    h2_runner = h2_exact_nonscoring_runner_contract_rows()
    s13_endpoint = s13_endpoint_exact_field_contract_rows()
    successors = d4_d3_d2_physical_successor_preflight_rows()
    diagnostic_scores = presentable_diagnostic_score_rows()
    figure_scores = figure_ready_diagnostic_rows(diagnostic_scores)
    thesis_claims = thesis_claim_boundary_rows()
    forbidden_claims = forbidden_claim_rows()
    next_actions = next_action_rows()
    guards = guardrail_rows()
    sources = source_manifest_rows()
    csv_specs = [
        ("passive_h2_source_property_provenance_recovery_matrix.csv", list(rows[0]), rows),
        ("passive_h2_source_envelope_gap_matrix.csv", list(gaps[0]), gaps),
        ("blocker_burndown_summary.csv", list(summary_rows[0]), summary_rows),
        ("support_contracts.csv", list(contracts[0]), contracts),
        ("h2_exact_nonscoring_runner_contract.csv", list(h2_runner[0]), h2_runner),
        ("s13_endpoint_exact_field_regeneration_contract.csv", list(s13_endpoint[0]), s13_endpoint),
        ("d4_d3_d2_physical_successor_preflight.csv", list(successors[0]), successors),
        ("presentable_diagnostic_scoreboard.csv", list(diagnostic_scores[0]), diagnostic_scores),
        ("figure_ready_diagnostic_scores.csv", list(figure_scores[0]), figure_scores),
        ("thesis_claim_boundaries.csv", list(thesis_claims[0]), thesis_claims),
        ("forbidden_claims.csv", list(forbidden_claims[0]), forbidden_claims),
        ("next_action_queue.csv", list(next_actions[0]), next_actions),
        ("source_manifest.csv", list(sources[0]), sources),
        ("no_mutation_guardrails.csv", list(guards[0]), guards),
    ]
    for name, header, table in csv_specs:
        path = out_dir / name
        csv_dump(path, header, table)
        normalize_csv(path)

    total = len(rows)
    subspan_ready = sum(truth(row["release_grade_subspan_evidence_recovered"]) for row in rows)
    setup_ready = sum(truth(row["setup_property_provenance_ready"]) for row in rows)
    strict_pass = sum(truth(row["strict_source_envelope_pass"]) for row in rows)
    admission_ready = sum(truth(row["source_property_admission_release_ready"]) for row in rows)
    summary = {
        "task_id": TASK_ID,
        "generated_at": iso_timestamp(),
        "decision": "passive_h2_provenance_recovered_diagnostic_scores_presentable_no_admission",
        "passive_h2_case_family_rows": total,
        "release_grade_subspan_evidence_recovered_rows": subspan_ready,
        "setup_property_provenance_ready_rows": setup_ready,
        "source_family_provenance_ready_rows": setup_ready,
        "strict_source_envelope_pass_rows": strict_pass,
        "source_property_admission_release_ready_rows": admission_ready,
        "h2_exact_nonscoring_runner_contract_rows": len(h2_runner),
        "h2_runtime_ready_contract_rows": sum(truth(row["runtime_ready_now"]) for row in h2_runner),
        "h2_fit_allowed_rows": sum(truth(row["fit_allowed_now"]) for row in h2_runner),
        "h2_score_allowed_rows": sum(truth(row["score_allowed_now"]) for row in h2_runner),
        "s13_endpoint_exact_field_contract_rows": len(s13_endpoint),
        "s13_endpoint_release_or_harvest_allowed_rows": sum(truth(row["release_or_harvest_allowed_now"]) for row in s13_endpoint),
        "d4_d3_d2_physical_successor_rows": len(successors),
        "d4_d3_d2_admission_ready_rows": sum(truth(row["admission_ready_now"]) for row in successors),
        "presentable_diagnostic_score_rows": len(diagnostic_scores),
        "figure_ready_diagnostic_score_rows": len(figure_scores),
        "final_admitted_score_rows": 0,
        "best_temperature_diagnostic": "D4_M3_segment_offsets_min2_train",
        "passive_h2_runtime_score_rows": sum(row["lane"] == "passive_h2_runtime_heat_ledger" for row in diagnostic_scores),
        "hx_fixed_mdot_duty_score_rows": sum(row["lane"] == "hx_fixed_mdot_duty" for row in diagnostic_scores),
        "s13_qwall_mesh_spread_score_rows": sum(row["lane"] == "s13_m5_upcomer_exchange" for row in diagnostic_scores),
        "m0_numerical_prediction_rows": int(read_json(M0_SUMMARY).get("numerical_prediction_rows", 0)),
        "cand001_endpoint_ready_fields": int(read_json(CAND001_SUMMARY).get("endpoint_ready_fields", 0)),
        "source_property_release": False,
        "numeric_q_loss_release": False,
        "qwall_release": False,
        "candidate_freeze": False,
        "protected_or_final_scoring": False,
        "scheduler_action": False,
        "native_output_mutation": False,
        "registry_or_admission_mutation": False,
        "fluid_or_external_edit": False,
        "solver_sampler_harvest_uq_launched": False,
    }
    json_dump(out_dir / "summary.json", summary)
    if out_dir == OUT:
        write_docs(summary)
        write_import(summary)
    return summary


def main() -> int:
    print(json.dumps(build(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
