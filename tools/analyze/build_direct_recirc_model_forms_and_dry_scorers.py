#!/usr/bin/env python3
"""Freeze direct recirculation model forms and emit dry scorers.

This package deliberately separates diagnostic recirculation scoring from
ordinary coefficient admission. It does not fit Nu, f_D, K, F6, or Fluid
parameters.
"""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[2]
DATE = "2026-07-20"
TASK = "TODO-DIRECT-RECIRC-MODEL-FORMS-AND-DRY-SCORERS"
OUT = ROOT / "work_products/2026-07/2026-07-20/2026-07-20_direct_recirc_model_forms_and_dry_scorers"
STATUS = ROOT / f".agent/status/{DATE}_{TASK}.md"
JOURNAL = ROOT / ".agent/journal/2026-07-20/direct-recirc-model-forms-and-dry-scorers.md"
IMPORT = ROOT / "imports/2026-07-20_direct_recirc_model_forms_and_dry_scorers.json"

PM10_CLASSIFICATION = (
    ROOT
    / "work_products/2026-07/2026-07-20/2026-07-20_pm10_upcomer_anchor_admission"
    / "pm10_upcomer_anchor_classification.csv"
)
UPCOMER_FEATURES = (
    ROOT
    / "work_products/2026-07/2026-07-17/2026-07-17_upcomer_pipe_cell_hybrid_model"
    / "recirculation_feature_scorecard.csv"
)
UPCOMER_HYBRID_CONTRACT = (
    ROOT
    / "work_products/2026-07/2026-07-17/2026-07-17_upcomer_pipe_cell_hybrid_model"
    / "hybrid_model_candidate_contract.csv"
)
UPCOMER_FROZEN_CANDIDATE = (
    ROOT
    / "work_products/2026-07/2026-07-17/2026-07-17_upcomer_hybrid_frozen_candidate_score"
    / "frozen_candidate_definition.csv"
)
CORNER_SECTION_CONTRACT = (
    ROOT
    / "work_products/2026-07/2026-07-20/2026-07-20_two_tap_recirc_section_effective_model"
    / "section_effective_model_contract.csv"
)
CORNER_RESIDUAL_SCORECARD = (
    ROOT
    / "work_products/2026-07/2026-07-20/2026-07-20_two_tap_recirc_residual_scorer"
    / "recirc_residual_scorecard.csv"
)
CORNER_QREF_AUDIT = (
    ROOT
    / "work_products/2026-07/2026-07-20/2026-07-20_two_tap_recirc_residual_scorer"
    / "q_ref_orientation_audit.csv"
)
UMX1_DECISION = (
    ROOT
    / "work_products/2026-07/2026-07-20/2026-07-20_umx1_fluid_intake_decision"
    / "decision_matrix.csv"
)
UMX1_SCENARIOS = (
    ROOT
    / "work_products/2026-07/2026-07-20/2026-07-20_umx1_fluid_intake_decision"
    / "scenario_score_intake.csv"
)
ONSET_ANCHOR_DESIGN = (
    ROOT
    / "work_products/2026-07/2026-07-20/2026-07-20_upcomer_onset_anchor_design"
    / "README.md"
)

SOURCES = {
    "pm10_upcomer_anchor_classification": PM10_CLASSIFICATION,
    "upcomer_feature_scorecard": UPCOMER_FEATURES,
    "upcomer_hybrid_contract": UPCOMER_HYBRID_CONTRACT,
    "upcomer_frozen_candidate": UPCOMER_FROZEN_CANDIDATE,
    "corner_section_contract": CORNER_SECTION_CONTRACT,
    "corner_residual_scorecard": CORNER_RESIDUAL_SCORECARD,
    "corner_qref_audit": CORNER_QREF_AUDIT,
    "umx1_decision": UMX1_DECISION,
    "umx1_scenarios": UMX1_SCENARIOS,
    "onset_anchor_design": ONSET_ANCHOR_DESIGN,
}

FROZEN_FORM_FIELDS = [
    "form_id",
    "avenue",
    "name",
    "frozen_status",
    "state_variables",
    "diagnostic_features",
    "model_equation",
    "dry_scorer_output",
    "fit_allowed_now",
    "admission_allowed_now",
    "blocked_by",
    "literature_review_need",
    "do_not_do",
]

UPCOMER_SCORE_FIELDS = [
    "row_id",
    "case_key",
    "source_family",
    "span",
    "role",
    "Re",
    "Ri",
    "Pr",
    "Gz",
    "RAF",
    "RMF",
    "SVF",
    "abs_delta_T_wall_bulk_K",
    "w_recirc_dry",
    "exchange_proxy_K",
    "regime_classification",
    "dry_score_use",
    "fit_allowed_now",
    "admission_allowed_now",
    "blockers",
    "source_path",
]

CORNER_SCORE_FIELDS = [
    "case_key",
    "feature",
    "Delta_p_rgh_pa",
    "Delta_p_kin_pa",
    "Delta_p_resid_status",
    "q_local_dynamic_pa",
    "K_eff_recirc_local_dynamic_diagnostic",
    "abs_K_eff_recirc_local_dynamic_diagnostic",
    "RAF",
    "RMF",
    "SVF",
    "q_ref_throughflow_status",
    "dry_score_use",
    "fit_allowed_now",
    "component_k_admitted",
    "f6_fit_performed",
    "blockers",
    "guardrail",
]

REGIME_FIELDS = [
    "row_id",
    "case_key",
    "source_family",
    "span",
    "RAF",
    "RMF",
    "Ri",
    "SVF",
    "regime_label",
    "ordinary_anchor_candidate",
    "transition_anchor_candidate",
    "recirculation_diagnostic",
    "fit_allowed_now",
    "evidence_gap",
]

AVENUE_FIELDS = [
    "avenue_id",
    "assigned_agent",
    "agent_id",
    "research_avenue",
    "current_progress",
    "work_product_outputs",
    "next_research_path",
    "acceptance_signal",
    "blockers",
]

NEXT_STEP_FIELDS = [
    "priority",
    "avenue_id",
    "next_step_id",
    "owner",
    "action",
    "depends_on",
    "output_artifact",
    "acceptance_signal",
    "guardrail",
]

MANIFEST_FIELDS = ["source_id", "path", "exists", "role"]


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT.resolve()))
    except ValueError:
        return str(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: Iterable[dict[str, Any]], fields: list[str]) -> int:
    materialized = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in materialized:
            writer.writerow({field: "" if row.get(field) is None else row.get(field, "") for field in fields})
    return len(materialized)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        parsed = float(str(value).strip())
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def fmt(value: Any, precision: int = 10) -> str:
    parsed = parse_float(value)
    if parsed is None:
        return "" if value is None else str(value)
    return f"{parsed:.{precision}g}"


def finite_or_zero(value: float | None) -> float:
    return value if value is not None and math.isfinite(value) else 0.0


def clamp01(value: float) -> float:
    return min(1.0, max(0.0, value))


def recirc_weight(raf: float | None, rmf: float | None, ri: float | None, svf: float | None) -> float:
    values = [finite_or_zero(raf), finite_or_zero(rmf), finite_or_zero(svf)]
    if ri is not None:
        values.append(clamp01(ri))
    return clamp01(max(values))


def regime_label(raf: float | None, rmf: float | None, ri: float | None, svf: float | None = None) -> str:
    raf_v = finite_or_zero(raf)
    rmf_v = finite_or_zero(rmf)
    ri_v = finite_or_zero(ri)
    svf_v = finite_or_zero(svf)
    if raf_v >= 0.10 or rmf_v >= 0.10 or ri_v >= 1.0 or svf_v >= 0.50:
        return "recirculation_diagnostic"
    if raf_v >= 0.01 or rmf_v >= 0.01 or ri_v >= 0.25 or svf_v >= 0.10:
        return "transition_near_onset_candidate"
    return "ordinary_candidate_requires_pressure_uq"


def extract_feature(features: str, name: str) -> str:
    for part in features.split(";"):
        key, _, value = part.partition("=")
        if key.strip() == name:
            return value.strip()
    return ""


def require_sources() -> None:
    missing = [rel(path) for path in SOURCES.values() if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing direct recirculation sources: " + "; ".join(missing))


def frozen_model_forms() -> list[dict[str, Any]]:
    return [
        {
            "form_id": "UH1",
            "avenue": "upcomer_throughflow_plus_recirculating_cell",
            "name": "throughflow pipe plus recirculating exchange cell",
            "frozen_status": "frozen_diagnostic_form_not_fit",
            "state_variables": "m_dot_net;T_core;T_cell;p_core;p_cell",
            "diagnostic_features": "RAF;RMF;SVF;Ri;Gz;wall_bulk_delta_T",
            "model_equation": "w_recirc=max(RAF,RMF,SVF,clamp(Ri/Ri_ref)); Q_recirc=Cq*w_recirc*DeltaT; dp_recirc=Cp*w_recirc*q_ref",
            "dry_scorer_output": "upcomer_hybrid_dry_scorecard.csv",
            "fit_allowed_now": "false",
            "admission_allowed_now": "false",
            "blocked_by": "no ordinary/onset anchors; no split-safe predictive score; mesh/time uncertainty missing",
            "literature_review_need": "mixed-convection reverse-flow onset and vertical heated channel exchange-cell scalings",
            "do_not_do": "do not treat current rows as ordinary Nu or f_D",
        },
        {
            "form_id": "CR1",
            "avenue": "corner_two_tap_section_effective_residual",
            "name": "recirculating corner section-effective pressure residual",
            "frozen_status": "frozen_diagnostic_form_partial_score",
            "state_variables": "Delta_p_rgh;Delta_p_kin;Delta_p_straight;Delta_p_dev;q_ref",
            "diagnostic_features": "RAF;RMF;SVF;q_ref_orientation_status;same_qoi_UQ",
            "model_equation": "Delta_p_resid=Delta_p_rgh-Delta_p_kin-Delta_p_straight-Delta_p_dev; K_eff_recirc=Delta_p_resid/q_ref",
            "dry_scorer_output": "corner_residual_dry_scorecard.csv",
            "fit_allowed_now": "false",
            "admission_allowed_now": "false",
            "blocked_by": "straight/dev isolation missing; q_ref untrusted; same-QOI UQ missing; material reverse flow",
            "literature_review_need": "recirculating bend/corner separated-loss residuals and dynamic-pressure normalization under reverse flow",
            "do_not_do": "do not promote K_eff_recirc to component K or F6",
        },
        {
            "form_id": "ROX1",
            "avenue": "reduced_order_exchange_source",
            "name": "explicit recirculation exchange/source term for disabled-by-default Fluid UMX1 substrate",
            "frozen_status": "research_form_frozen_no_score_grid",
            "state_variables": "T_loop_nodes;T_stratified_reservoir;m_dot_setup;wall_loss_state",
            "diagnostic_features": "w_recirc;setup geometry;source/property labels;onset evidence",
            "model_equation": "S_recirc = Cmix*w_recirc*(T_reservoir-T_branch)/tau_mix with conservation ledger required",
            "dry_scorer_output": "research_path_only_no_grid",
            "fit_allowed_now": "false",
            "admission_allowed_now": "false",
            "blocked_by": "current UMX1 exchange variants score worse than baseline; source/property and onset evidence incomplete; broad grid not authorized",
            "literature_review_need": "stratified reservoir, thermal short-circuit, and low-flow mixing source closures",
            "do_not_do": "do not launch a broad UMX1 grid from the current exchange variants; keep exchange/combined rows as negative controls",
        },
    ]


def upcomer_hybrid_dry_score_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for source_row in read_csv(PM10_CLASSIFICATION):
        raf = parse_float(source_row.get("max_reverse_area_fraction"))
        rmf = parse_float(source_row.get("max_reverse_mass_fraction"))
        svf = parse_float(source_row.get("max_secondary_velocity_fraction"))
        ri = parse_float(source_row.get("max_Ri"))
        delta = parse_float(source_row.get("min_abs_delta_T_wall_bulk_K"))
        weight = recirc_weight(raf, rmf, ri, svf)
        rows.append(
            {
                "row_id": f"PM10-{source_row.get('case_key', '')}",
                "case_key": source_row.get("case_key", ""),
                "source_family": "PM10_matched_plane",
                "span": "upcomer_aggregate",
                "role": "terminal_diagnostic_holdout",
                "Re": "",
                "Ri": fmt(ri),
                "Pr": "",
                "Gz": "",
                "RAF": fmt(raf),
                "RMF": fmt(rmf),
                "SVF": fmt(svf),
                "abs_delta_T_wall_bulk_K": fmt(delta),
                "w_recirc_dry": fmt(weight),
                "exchange_proxy_K": fmt(weight * finite_or_zero(delta)),
                "regime_classification": regime_label(raf, rmf, ri, svf),
                "dry_score_use": "diagnostic_severity_only",
                "fit_allowed_now": "false",
                "admission_allowed_now": "false",
                "blockers": "ordinary_anchor_absent;near_onset_anchor_absent;split_score_missing",
                "source_path": rel(PM10_CLASSIFICATION),
            }
        )
    for source_row in read_csv(UPCOMER_FEATURES):
        raf = parse_float(source_row.get("reverse_area_fraction"))
        rmf = parse_float(source_row.get("reverse_mass_fraction"))
        svf = parse_float(source_row.get("secondary_velocity_fraction"))
        ri = parse_float(source_row.get("Ri"))
        delta = parse_float(source_row.get("delta_T_wall_bulk_K"))
        weight = recirc_weight(raf, rmf, ri, svf)
        rows.append(
            {
                "row_id": f"PM5-{source_row.get('case_key', '')}-{source_row.get('span', '')}",
                "case_key": source_row.get("case_key", ""),
                "source_family": "PM5_feature_scorecard",
                "span": source_row.get("span", ""),
                "role": source_row.get("case_role", ""),
                "Re": fmt(source_row.get("Re")),
                "Ri": fmt(ri),
                "Pr": fmt(source_row.get("Pr")),
                "Gz": fmt(source_row.get("Gz")),
                "RAF": fmt(raf),
                "RMF": fmt(rmf),
                "SVF": fmt(svf),
                "abs_delta_T_wall_bulk_K": fmt(abs(delta) if delta is not None else None),
                "w_recirc_dry": fmt(weight),
                "exchange_proxy_K": fmt(weight * abs(delta) if delta is not None else None),
                "regime_classification": regime_label(raf, rmf, ri, svf),
                "dry_score_use": "diagnostic_severity_only",
                "fit_allowed_now": "false",
                "admission_allowed_now": "false",
                "blockers": "holdout_recirculating;ordinary_anchor_absent;split_score_missing",
                "source_path": source_row.get("source_path", rel(UPCOMER_FEATURES)),
            }
        )
    return rows


def corner_residual_dry_score_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for source_row in read_csv(CORNER_RESIDUAL_SCORECARD):
        features = source_row.get("recirculation_features", "")
        k_eff = parse_float(source_row.get("K_eff_recirc_local_dynamic_diagnostic"))
        rows.append(
            {
                "case_key": source_row.get("case_key", ""),
                "feature": source_row.get("feature", ""),
                "Delta_p_rgh_pa": fmt(source_row.get("Delta_p_rgh_pa")),
                "Delta_p_kin_pa": fmt(source_row.get("Delta_p_kin_pa")),
                "Delta_p_resid_status": source_row.get("Delta_p_resid_status", ""),
                "q_local_dynamic_pa": fmt(source_row.get("q_local_dynamic_pa")),
                "K_eff_recirc_local_dynamic_diagnostic": fmt(k_eff),
                "abs_K_eff_recirc_local_dynamic_diagnostic": fmt(abs(k_eff) if k_eff is not None else None),
                "RAF": fmt(extract_feature(features, "RAF")),
                "RMF": fmt(extract_feature(features, "RMF")),
                "SVF": fmt(extract_feature(features, "SVF")),
                "q_ref_throughflow_status": source_row.get("q_ref_throughflow_status", ""),
                "dry_score_use": "diagnostic_partial_residual_only",
                "fit_allowed_now": "false",
                "component_k_admitted": source_row.get("component_k_admitted", "false"),
                "f6_fit_performed": source_row.get("f6_fit_performed", "false"),
                "blockers": source_row.get("fit_blockers", ""),
                "guardrail": source_row.get("guardrail", ""),
            }
        )
    return rows


def regime_gate_rows(upcomer_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in upcomer_rows:
        raf = parse_float(row.get("RAF"))
        rmf = parse_float(row.get("RMF"))
        ri = parse_float(row.get("Ri"))
        svf = parse_float(row.get("SVF"))
        label = regime_label(raf, rmf, ri, svf)
        rows.append(
            {
                "row_id": row.get("row_id", ""),
                "case_key": row.get("case_key", ""),
                "source_family": row.get("source_family", ""),
                "span": row.get("span", ""),
                "RAF": row.get("RAF", ""),
                "RMF": row.get("RMF", ""),
                "Ri": row.get("Ri", ""),
                "SVF": row.get("SVF", ""),
                "regime_label": label,
                "ordinary_anchor_candidate": str(label.startswith("ordinary")).lower(),
                "transition_anchor_candidate": str(label.startswith("transition")).lower(),
                "recirculation_diagnostic": str(label == "recirculation_diagnostic").lower(),
                "fit_allowed_now": "false",
                "evidence_gap": "needs nonrecirculating_or_near_onset_anchor_and_same_window_UQ",
            }
        )
    return rows


def research_avenues() -> list[dict[str, Any]]:
    return [
        {
            "avenue_id": "A1",
            "assigned_agent": "Euler",
            "agent_id": "019f816c-8daf-7013-9f75-fce8f4e5d64a",
            "research_avenue": "Upcomer throughflow plus recirculating-cell model",
            "current_progress": "UH1 frozen; dry severity scorer implemented from PM10/PM5 recirculation features",
            "work_product_outputs": "frozen_direct_recirc_model_forms.csv;upcomer_hybrid_dry_scorecard.csv",
            "next_research_path": "Use literature/onset anchors to choose Cq/Cp scalings and score split-safe when anchors arrive",
            "acceptance_signal": "ordinary/transition/recirculating anchors plus mesh/time uncertainty and no runtime leakage",
            "blockers": "no onset anchors; no split-safe coupled score; no UQ",
        },
        {
            "avenue_id": "A2",
            "assigned_agent": "Aristotle",
            "agent_id": "019f816c-9e2d-76f2-93e1-11f6f184e0d0",
            "research_avenue": "Corner/two-tap section-effective recirculation residual",
            "current_progress": "CR1 frozen; dry scorer implemented from current residual scorecard",
            "work_product_outputs": "frozen_direct_recirc_model_forms.csv;corner_residual_dry_scorecard.csv",
            "next_research_path": "Complete q_ref orientation, straight/dev isolation, and same-QOI UQ before any coefficient route",
            "acceptance_signal": "finite residual with trusted q_ref and UQ, or explicit diagnostic-only section-effective decision",
            "blockers": "q_ref untrusted; material reverse flow; same-QOI UQ missing; component isolation missing",
        },
        {
            "avenue_id": "A3",
            "assigned_agent": "Bernoulli",
            "agent_id": "019f816c-b216-7743-add5-3aacf4230e51",
            "research_avenue": "Regime/onset classifier",
            "current_progress": "dry gate implemented over PM10 and PM5 recirculation rows",
            "work_product_outputs": "regime_gate_dry_table.csv",
            "next_research_path": "Convert threshold gate to onset probability only after near-onset anchors exist",
            "acceptance_signal": "rows in ordinary, transition, and recirculation classes with same-window RAF/RMF/Ri/SVF",
            "blockers": "current rows all recirculating; transition class empty",
        },
        {
            "avenue_id": "A4",
            "assigned_agent": "Sagan",
            "agent_id": "019f816c-c5cb-7fa0-82f7-cec7d0887169",
            "research_avenue": "Reduced-order exchange/source model",
            "current_progress": "ROX1 frozen as research form; UMX1 root/ledger substrate is healthy but current exchange grid expansion remains blocked",
            "work_product_outputs": "frozen_direct_recirc_model_forms.csv;next_steps_direct_recirc.csv",
            "next_research_path": "Freeze setup-only rad-on low/mid Salt1-4 sanity candidates; use literature review to define a conservation-checked source term before any grid",
            "acceptance_signal": "source/property gate pass, accepted roots/ledgers, and thermal score improvement over baseline",
            "blockers": "current UMX1 exchange variants not scorecard-ready; source/property and onset evidence incomplete; broad grid not authorized",
        },
    ]


def next_steps() -> list[dict[str, Any]]:
    return [
        {
            "priority": 1,
            "avenue_id": "A1",
            "next_step_id": "UH1-01",
            "owner": "Ethan+Euler",
            "action": "Turn literature review into a two-parameter UH1 prior: Cq for exchange, Cp for pressure penalty, both driven by w_recirc and nondimensional groups.",
            "depends_on": "targeted literature review; onset-anchor plan",
            "output_artifact": "UH1_model_form_prior_table.csv",
            "acceptance_signal": "equations name input variables and forbid runtime validation data",
            "guardrail": "no ordinary Nu/f_D fit from recirculating rows",
        },
        {
            "priority": 2,
            "avenue_id": "A3",
            "next_step_id": "RG1-01",
            "owner": "Ethan+Bernoulli",
            "action": "Define a three-bin regime gate: ordinary, transition, recirculation, with thresholds and uncertainty handling.",
            "depends_on": "PM10/PM5 gate table; literature onset scalings",
            "output_artifact": "regime_gate_policy_v1.csv",
            "acceptance_signal": "current PM10 rows remain diagnostic while future high-heat rows can enter ordinary/transition bins",
            "guardrail": "do not force a continuous fit through an unobserved transition band",
        },
        {
            "priority": 3,
            "avenue_id": "A2",
            "next_step_id": "CR1-01",
            "owner": "Hydraulics+Aristotle",
            "action": "Resolve corner q_ref orientation and same-QOI UQ, then re-run CR1 residual scoring with straight/dev terms present or explicitly missing.",
            "depends_on": "two-tap same-QOI UQ; q_ref orientation audit",
            "output_artifact": "corner_residual_scorecard_v2.csv",
            "acceptance_signal": "trusted q_ref or explicit no-fit near-zero-throughflow status",
            "guardrail": "no component K admission, no K clipping, no F6 substitution",
        },
        {
            "priority": 4,
            "avenue_id": "A4",
            "next_step_id": "ROX1-01",
            "owner": "Fluid+Sagan",
            "action": "Draft a conservation-checked ROX1 source-term API and stage only setup-only rad-on Salt1-4 sanity candidates, not a broad UMX1 grid.",
            "depends_on": "literature review; source/property gate",
            "output_artifact": "rox1_fluid_api_contract.md",
            "acceptance_signal": "dry ledger proves energy conservation, roots/ledgers pass, runtime inputs are setup-only, and baseline score is not regressed",
            "guardrail": "no broad grid from current UMX1 exchange variants",
        },
        {
            "priority": 5,
            "avenue_id": "A1,A2,A3,A4",
            "next_step_id": "SYNC-01",
            "owner": "Coordinator",
            "action": "When high-heat no-recirculation cases terminate, harvest the same dry-scorer variables first, then decide whether any rows become anchors.",
            "depends_on": "terminal high-heat runs",
            "output_artifact": "direct_recirc_anchor_update_after_high_heat.csv",
            "acceptance_signal": "new rows are classified before any ordinary coefficient use",
            "guardrail": "terminal does not automatically mean steady or fit-admissible",
        },
    ]


def source_manifest() -> list[dict[str, Any]]:
    roles = {
        "pm10_upcomer_anchor_classification": "current PM10 regime labels and upcomer feature aggregates",
        "upcomer_feature_scorecard": "PM5 recirculation features used for UH1 dry severity rows",
        "upcomer_hybrid_contract": "prior lane definitions and forbidden labels",
        "upcomer_frozen_candidate": "UH1 frozen candidate provenance",
        "corner_section_contract": "CR1 section-effective formula provenance",
        "corner_residual_scorecard": "current corner residual diagnostic rows",
        "corner_qref_audit": "q_ref trust and orientation evidence",
        "umx1_decision": "ROX1/UMX1 blocked decision provenance",
        "umx1_scenarios": "current UMX1 score behavior",
        "onset_anchor_design": "future anchor path provenance",
    }
    return [
        {"source_id": source_id, "path": rel(path), "exists": str(path.exists()).lower(), "role": roles[source_id]}
        for source_id, path in SOURCES.items()
    ]


def write_docs(summary: dict[str, Any]) -> None:
    readme = "\n".join(
        [
            "---",
            "provenance:",
            f"  - {rel(PM10_CLASSIFICATION)}",
            f"  - {rel(UPCOMER_FEATURES)}",
            f"  - {rel(CORNER_RESIDUAL_SCORECARD)}",
            f"  - {rel(UMX1_DECISION)}",
            "tags: [recirculation, upcomer, corner, dry-scorer, model-form]",
            "related:",
            f"  - {rel(STATUS)}",
            f"  - {rel(JOURNAL)}",
            f"task: {TASK}",
            f"date: {DATE}",
            "role: Hydraulics/Thermal-modeling/Forward-pred/Coordinator/Implementer/Tester/Writer",
            "type: work_product",
            "status: complete",
            "---",
            "# Direct Recirculation Model Forms And Dry Scorers",
            "",
            "## Decision",
            "",
            "Freeze three direct recirculation research forms now: `UH1`, `CR1`, and `ROX1`. Keep the regime/onset classifier as the gate that decides when these forms apply. None of these forms admit ordinary `Nu`, `f_D`, `K`, or `F6` rows today.",
            "",
            "## Frozen Forms",
            "",
            "- `UH1`: upcomer throughflow pipe plus recirculating exchange cell.",
            "- `CR1`: corner/two-tap recirculating section-effective pressure residual.",
            "- `ROX1`: reduced-order exchange/source term for a future Fluid substrate.",
            "",
            "## Dry Scorers Implemented",
            "",
            f"- Upcomer dry rows: `{summary['upcomer_dry_rows']}`.",
            f"- Corner residual dry rows: `{summary['corner_dry_rows']}`.",
            f"- Regime gate rows: `{summary['regime_gate_rows']}`.",
            f"- Frozen model forms: `{summary['frozen_model_forms']}`.",
            "",
            "The dry scorers report diagnostic severity and blocker status only. `fit_allowed_now=false` and `admission_allowed_now=false` are intentional outputs, not failures.",
            "",
            "## Research Path",
            "",
            "1. Use the literature review to choose nondimensional priors for `UH1` and `ROX1` rather than fitting recirculating rows as ordinary coefficients.",
            "2. Use `regime_gate_dry_table.csv` as the admission gate for future high-heat or near-onset cases.",
            "3. Use `corner_residual_dry_scorecard.csv` to track section-effective pressure residuals while keeping component `K` and `F6` blocked.",
            "4. Re-score the same dry tables when terminal non-recirculating or near-onset anchors arrive.",
            "",
            "## Active Blockers",
            "",
            "- No non-recirculating or near-onset upcomer anchors are fit-admissible yet.",
            "- Corner `q_ref` is still untrusted under material reverse flow.",
            "- Same-QOI mesh/time uncertainty is missing for the corner residual lane.",
            "- Current UMX1 exchange variants are not scorecard-ready.",
            "",
            "## Generated Files",
            "",
            "- `frozen_direct_recirc_model_forms.csv`",
            "- `upcomer_hybrid_dry_scorecard.csv`",
            "- `corner_residual_dry_scorecard.csv`",
            "- `regime_gate_dry_table.csv`",
            "- `research_avenue_assignments.csv`",
            "- `next_steps_direct_recirc.csv`",
            "- `source_manifest.csv`",
            "- `summary.json`",
        ]
    )
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "README.md").write_text(readme + "\n", encoding="utf-8")

    STATUS.parent.mkdir(parents=True, exist_ok=True)
    JOURNAL.parent.mkdir(parents=True, exist_ok=True)
    STATUS.write_text(
        "\n".join(
            [
                "---",
                "provenance:",
                f"  - {rel(OUT / 'README.md')}",
                f"  - {rel(OUT / 'summary.json')}",
                "tags: [status, direct-recirculation, dry-scorer]",
                "related:",
                f"  - {rel(JOURNAL)}",
                f"  - {rel(IMPORT)}",
                f"task: {TASK}",
                f"date: {DATE}",
                "role: Coordinator/Implementer/Tester/Writer",
                "type: status",
                "status: complete",
                "---",
                f"# {TASK} Status",
                "",
                "## Result",
                "",
                "- Froze `UH1`, `CR1`, and `ROX1` as direct recirculation research forms.",
                "- Implemented dry scorecards for UH1 upcomer severity and CR1 corner residual diagnostics.",
                "- Added a regime gate table and next-step path for all four research avenues.",
                "",
                "## Validation",
                "",
                "- `python3 -m unittest tools.analyze.test_direct_recirc_model_forms_and_dry_scorers`",
                "- `python3 tools/analyze/build_direct_recirc_model_forms_and_dry_scorers.py`",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    JOURNAL.write_text(
        "\n".join(
            [
                "---",
                "provenance:",
                f"  - {rel(OUT / 'README.md')}",
                "tags: [journal, direct-recirculation]",
                f"task: {TASK}",
                f"date: {DATE}",
                "role: Coordinator/Implementer/Tester/Writer",
                "type: journal",
                "status: complete",
                "---",
                "# Direct Recirculation Model Forms And Dry Scorers",
                "",
                "Built a consolidated direct-recirculation package while waiting for non-recirculating anchors. The work keeps coefficient admission blocked and makes progress by freezing model forms, generating dry diagnostics, and assigning avenue owners.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def main() -> dict[str, Any]:
    require_sources()
    forms = frozen_model_forms()
    upcomer_scores = upcomer_hybrid_dry_score_rows()
    corner_scores = corner_residual_dry_score_rows()
    regime_rows = regime_gate_rows(upcomer_scores)
    avenues = research_avenues()
    steps = next_steps()
    manifest = source_manifest()

    write_csv(OUT / "frozen_direct_recirc_model_forms.csv", forms, FROZEN_FORM_FIELDS)
    write_csv(OUT / "upcomer_hybrid_dry_scorecard.csv", upcomer_scores, UPCOMER_SCORE_FIELDS)
    write_csv(OUT / "corner_residual_dry_scorecard.csv", corner_scores, CORNER_SCORE_FIELDS)
    write_csv(OUT / "regime_gate_dry_table.csv", regime_rows, REGIME_FIELDS)
    write_csv(OUT / "research_avenue_assignments.csv", avenues, AVENUE_FIELDS)
    write_csv(OUT / "next_steps_direct_recirc.csv", steps, NEXT_STEP_FIELDS)
    write_csv(OUT / "source_manifest.csv", manifest, MANIFEST_FIELDS)

    summary = {
        "task": TASK,
        "date": DATE,
        "frozen_model_forms": len(forms),
        "upcomer_dry_rows": len(upcomer_scores),
        "corner_dry_rows": len(corner_scores),
        "regime_gate_rows": len(regime_rows),
        "research_avenues": len(avenues),
        "next_steps": len(steps),
        "upcomer_fit_admitted_rows": 0,
        "corner_component_k_admitted_rows": 0,
        "ordinary_nu_fd_k_rows_admitted": 0,
        "umx1_grid_authorized": False,
        "native_solver_outputs_mutated": False,
        "generated_index_refreshed": False,
        "all_sources_present": all(path.exists() for path in SOURCES.values()),
    }
    write_json(OUT / "summary.json", summary)
    write_docs(summary)
    write_json(
        IMPORT,
        {
            "task": TASK,
            "date": DATE,
            "work_product": rel(OUT),
            "summary": rel(OUT / "summary.json"),
            "native_solver_outputs_mutated": False,
            "generated_index_refreshed": False,
            "ordinary_coefficients_admitted": False,
            "generated_files": [
                rel(OUT / "frozen_direct_recirc_model_forms.csv"),
                rel(OUT / "upcomer_hybrid_dry_scorecard.csv"),
                rel(OUT / "corner_residual_dry_scorecard.csv"),
                rel(OUT / "regime_gate_dry_table.csv"),
                rel(OUT / "research_avenue_assignments.csv"),
                rel(OUT / "next_steps_direct_recirc.csv"),
                rel(OUT / "README.md"),
            ],
        },
    )
    return summary


if __name__ == "__main__":
    print(json.dumps(main(), indent=2, sort_keys=True))
