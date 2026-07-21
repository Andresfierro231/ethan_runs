#!/usr/bin/env python3
"""Audit two-tap raw endpoint pressure/velocity basis and recirculation gates.

This consumes the harvested staged endpoint sampler rows for
corner_lower_right.  It separates static pressure, p_rgh, hydrostatic, kinetic,
and local dynamic-pressure terms, but does not admit component K or fit F6.
"""

from __future__ import annotations

import csv
import json
import math
from collections.abc import Iterable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
TASK = "TODO-TWO-TAP-PRESSURE-BASIS-RECIRC-AUDIT"
DATE = "2026-07-18"
SLUG = "2026-07-18_two_tap_pressure_basis_recirc_audit"
OUT_REL = Path("work_products/2026-07/2026-07-18") / SLUG
OUT = ROOT / OUT_REL
SAMPLER = ROOT / "work_products/2026-07/2026-07-18/2026-07-18_two_tap_staged_endpoint_sampler"
PLAN = ROOT / "work_products/2026-07/2026-07-18/2026-07-18_two_tap_component_raw_endpoint_plan"
ROADMAP = ROOT / "work_products/2026-07/2026-07-18/2026-07-18_two_tap_blocker_roadmap"
TARGET_FEATURE = "corner_lower_right"
RECIRC_LIMIT = 0.01

BASIS_FIELDS = [
    "case_id",
    "case_key",
    "source_id",
    "feature",
    "time_s",
    "upstream_surface_label",
    "downstream_surface_label",
    "upstream_sample_status",
    "downstream_sample_status",
    "basis_status",
    "p_upstream_pa",
    "p_downstream_pa",
    "delta_p_down_minus_up_pa",
    "p_rgh_upstream_pa",
    "p_rgh_downstream_pa",
    "delta_p_rgh_down_minus_up_pa",
    "hydrostatic_correction_pa",
    "rho_upstream_kg_m3",
    "rho_downstream_kg_m3",
    "U_bulk_upstream_m_s",
    "U_bulk_downstream_m_s",
    "dynamic_pressure_upstream_pa",
    "dynamic_pressure_downstream_pa",
    "local_dynamic_pressure_mean_pa",
    "kinetic_correction_pa",
    "feature_total_pressure_loss_pa",
    "feature_total_pressure_loss_sign_convention",
    "K_apparent_diagnostic",
    "K_local_candidate",
    "component_k_admitted",
    "f6_fit_performed",
    "guardrail",
]

RECIRC_FIELDS = [
    "case_id",
    "case_key",
    "feature",
    "time_s",
    "upstream_RAF",
    "downstream_RAF",
    "aggregate_RAF",
    "upstream_RMF",
    "downstream_RMF",
    "aggregate_RMF",
    "upstream_SVF",
    "downstream_SVF",
    "aggregate_SVF",
    "ordinary_recirculation_gate",
    "recirculation_decision",
    "guardrail",
]

GATE_FIELDS = [
    "case_id",
    "case_key",
    "feature",
    "time_s",
    "raw_endpoint_surface_availability",
    "pressure_velocity_basis_gate",
    "recirculation_gate",
    "component_isolation_gate",
    "same_qoi_uncertainty_gate",
    "ordinary_component_k_candidate",
    "admission_decision",
    "next_action",
    "f6_fit_performed",
    "component_k_admitted",
    "guardrail",
]

NEXT_FIELDS = [
    "priority",
    "step_id",
    "title",
    "depends_on",
    "action",
    "acceptance_signal",
    "guardrail",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT.resolve()))
    except ValueError:
        return str(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: Iterable[dict[str, Any]], fieldnames: list[str]) -> int:
    data = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in data:
            writer.writerow({field: row.get(field, "") for field in fieldnames})
    return len(data)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def to_float(value: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return float("nan")
    return number


def fmt(value: Any) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return ""
    return f"{number:.12g}" if math.isfinite(number) else ""


def load_sampled_pairs(raw_rows: list[dict[str, str]]) -> list[tuple[dict[str, str], dict[str, str]]]:
    grouped: dict[tuple[str, str, str], dict[str, dict[str, str]]] = {}
    for row in raw_rows:
        if row.get("feature") != TARGET_FEATURE:
            continue
        key = (row["case_id"], row["feature"], row["time_s"])
        grouped.setdefault(key, {})[row["tap_role"]] = row
    pairs = []
    for key in sorted(grouped):
        taps = grouped[key]
        if "upstream" in taps and "downstream" in taps:
            pairs.append((taps["upstream"], taps["downstream"]))
    return pairs


def dynamic_pressure(row: dict[str, str]) -> float:
    rho = to_float(row["rho_kg_m3"])
    speed = to_float(row["U_bulk_m_s"])
    return 0.5 * rho * speed * speed


def pressure_basis_rows(pairs: list[tuple[dict[str, str], dict[str, str]]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for upstream, downstream in pairs:
        p_up = to_float(upstream["p_pa"])
        p_down = to_float(downstream["p_pa"])
        p_rgh_up = to_float(upstream["p_rgh_pa"])
        p_rgh_down = to_float(downstream["p_rgh_pa"])
        q_up = dynamic_pressure(upstream)
        q_down = dynamic_pressure(downstream)
        local_q = 0.5 * (q_up + q_down)
        delta_p = p_down - p_up
        delta_p_rgh = p_rgh_down - p_rgh_up
        basis_ok = all(
            math.isfinite(value)
            for value in (p_up, p_down, p_rgh_up, p_rgh_down, q_up, q_down, local_q)
        ) and upstream["sample_status"] == "sampled" and downstream["sample_status"] == "sampled"
        rows.append(
            {
                "case_id": upstream["case_id"],
                "case_key": upstream["case_key"],
                "source_id": upstream["source_id"],
                "feature": upstream["feature"],
                "time_s": upstream["time_s"],
                "upstream_surface_label": upstream["surface_label"],
                "downstream_surface_label": downstream["surface_label"],
                "upstream_sample_status": upstream["sample_status"],
                "downstream_sample_status": downstream["sample_status"],
                "basis_status": "basis_resolved_raw_endpoint_diagnostic" if basis_ok else "basis_blocked_missing_or_nonfinite",
                "p_upstream_pa": fmt(p_up),
                "p_downstream_pa": fmt(p_down),
                "delta_p_down_minus_up_pa": fmt(delta_p),
                "p_rgh_upstream_pa": fmt(p_rgh_up),
                "p_rgh_downstream_pa": fmt(p_rgh_down),
                "delta_p_rgh_down_minus_up_pa": fmt(delta_p_rgh),
                "hydrostatic_correction_pa": fmt(delta_p - delta_p_rgh),
                "rho_upstream_kg_m3": upstream["rho_kg_m3"],
                "rho_downstream_kg_m3": downstream["rho_kg_m3"],
                "U_bulk_upstream_m_s": upstream["U_bulk_m_s"],
                "U_bulk_downstream_m_s": downstream["U_bulk_m_s"],
                "dynamic_pressure_upstream_pa": fmt(q_up),
                "dynamic_pressure_downstream_pa": fmt(q_down),
                "local_dynamic_pressure_mean_pa": fmt(local_q),
                "kinetic_correction_pa": fmt(q_down - q_up),
                "feature_total_pressure_loss_pa": fmt(delta_p),
                "feature_total_pressure_loss_sign_convention": "p_downstream_minus_p_upstream; diagnostic basis term, not admitted K",
                "K_apparent_diagnostic": fmt(delta_p / local_q) if local_q > 0.0 else "",
                "K_local_candidate": "",
                "component_k_admitted": "false",
                "f6_fit_performed": "false",
                "guardrail": "raw_basis_only_no_F6_fit_no_component_K_admission",
            }
        )
    return rows


def recirculation_rows(pairs: list[tuple[dict[str, str], dict[str, str]]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for upstream, downstream in pairs:
        up_raf = to_float(upstream["reverse_area_fraction"])
        down_raf = to_float(downstream["reverse_area_fraction"])
        up_rmf = to_float(upstream["reverse_mass_fraction"])
        down_rmf = to_float(downstream["reverse_mass_fraction"])
        up_svf = to_float(upstream["secondary_velocity_fraction"])
        down_svf = to_float(downstream["secondary_velocity_fraction"])
        agg_raf = max(up_raf, down_raf)
        agg_rmf = max(up_rmf, down_rmf)
        agg_svf = max(up_svf, down_svf)
        passes = agg_raf < RECIRC_LIMIT and agg_rmf < RECIRC_LIMIT
        rows.append(
            {
                "case_id": upstream["case_id"],
                "case_key": upstream["case_key"],
                "feature": upstream["feature"],
                "time_s": upstream["time_s"],
                "upstream_RAF": fmt(up_raf),
                "downstream_RAF": fmt(down_raf),
                "aggregate_RAF": fmt(agg_raf),
                "upstream_RMF": fmt(up_rmf),
                "downstream_RMF": fmt(down_rmf),
                "aggregate_RMF": fmt(agg_rmf),
                "upstream_SVF": fmt(up_svf),
                "downstream_SVF": fmt(down_svf),
                "aggregate_SVF": fmt(agg_svf),
                "ordinary_recirculation_gate": "pass_nonrecirculating" if passes else "fail_material_reverse_flow",
                "recirculation_decision": "ordinary_candidate_allowed" if passes else "diagnostic_or_section_effective_only",
                "guardrail": "RAF_RMF_must_be_below_0p01_for_ordinary_component_K",
            }
        )
    return rows


def gate_decision_rows(
    basis_rows: list[dict[str, Any]], recirc_rows: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    recirc_by_case = {row["case_id"]: row for row in recirc_rows}
    rows: list[dict[str, Any]] = []
    for row in basis_rows:
        recirc = recirc_by_case[row["case_id"]]
        basis_pass = row["basis_status"] == "basis_resolved_raw_endpoint_diagnostic"
        recirc_pass = recirc["ordinary_recirculation_gate"] == "pass_nonrecirculating"
        ordinary = basis_pass and recirc_pass and False
        if not recirc_pass:
            decision = "diagnostic_only_recirculation_blocked"
            next_action = "do not admit K; decide apparent/cluster treatment or seek nonrecirculating anchor"
        else:
            decision = "blocked_pending_component_isolation_and_same_qoi_UQ"
            next_action = "run straight-reference/component-isolation audit, then same-QOI UQ"
        rows.append(
            {
                "case_id": row["case_id"],
                "case_key": row["case_key"],
                "feature": row["feature"],
                "time_s": row["time_s"],
                "raw_endpoint_surface_availability": "pass_six_raw_surfaces_harvested",
                "pressure_velocity_basis_gate": "pass_basis_resolved" if basis_pass else "fail_basis_missing",
                "recirculation_gate": recirc["ordinary_recirculation_gate"],
                "component_isolation_gate": "blocked_not_audited",
                "same_qoi_uncertainty_gate": "blocked_not_audited",
                "ordinary_component_k_candidate": str(ordinary).lower(),
                "admission_decision": decision,
                "next_action": next_action,
                "f6_fit_performed": "false",
                "component_k_admitted": "false",
                "guardrail": "no_F6_fit_no_component_K_admission_from_basis_audit",
            }
        )
    return rows


def next_action_rows() -> list[dict[str, Any]]:
    return [
        {
            "priority": 1,
            "step_id": "NEXT-01",
            "title": "Component-isolation/apparent-cluster decision",
            "depends_on": "pressure_velocity_basis_audit;endpoint_recirculation_metrics",
            "action": "Evaluate local straight-reference policy but do not clip negative K or tune a multiplier.",
            "acceptance_signal": "nonnegative unclipped K_local with documented reference, or apparent_cluster_only decision",
            "guardrail": "material reverse-flow rows remain diagnostic; no F6 fit",
        },
        {
            "priority": 2,
            "step_id": "NEXT-02",
            "title": "Same-QOI uncertainty status",
            "depends_on": "pressure_velocity_basis_audit",
            "action": "Search valid same endpoint/time/mesh family members or emit missing_no_GCI diagnostic status.",
            "acceptance_signal": "same-QOI uncertainty attached or explicit non-GCI blocker",
            "guardrail": "do not borrow unrelated GCI or fabricate monotonicity",
        },
        {
            "priority": 3,
            "step_id": "NEXT-03",
            "title": "Separated admission review",
            "depends_on": "component_isolation_audit;same_qoi_uncertainty_audit",
            "action": "Build a new review package that consumes all gates and decides diagnostic versus ordinary status.",
            "acceptance_signal": "every gate is recorded and no coefficient is admitted unless all gates pass",
            "guardrail": "do not overwrite AGENT-530 or route this into F6",
        },
    ]


def source_manifest_rows() -> list[dict[str, str]]:
    return [
        {
            "source_id": "harvested_raw_endpoint_rows",
            "path": rel(SAMPLER / "raw_endpoint_pressure_velocity.csv"),
            "use": "primary six sampled endpoint rows",
            "mutation": "read_only",
        },
        {
            "source_id": "basis_field_contract",
            "path": rel(PLAN / "basis_field_contract.csv"),
            "use": "basis formulas and gate meanings",
            "mutation": "read_only",
        },
        {
            "source_id": "recirculation_metric_contract",
            "path": rel(PLAN / "recirculation_metric_contract.csv"),
            "use": "RAF/RMF/SVF ordinary acceptance",
            "mutation": "read_only",
        },
        {
            "source_id": "roadmap_next_steps",
            "path": rel(ROADMAP / "next_step_queue.csv"),
            "use": "downstream task ordering",
            "mutation": "read_only",
        },
    ]


def write_readme(summary: dict[str, Any]) -> None:
    (OUT / "README.md").write_text(
        f"""---
provenance:
  - {rel(SAMPLER / 'raw_endpoint_pressure_velocity.csv')}
  - {rel(PLAN / 'basis_field_contract.csv')}
  - {rel(PLAN / 'recirculation_metric_contract.csv')}
tags: [pressure-ledger, two-tap, raw-endpoints, recirculation]
related:
  - .agent/status/2026-07-18_{TASK}.md
  - .agent/journal/2026-07-18/two-tap-pressure-basis-recirc-audit.md
task: {TASK}
date: {DATE}
role: Hydraulics/Tester/Implementer/Writer
type: work_product
status: complete
---
# Two-Tap Pressure Basis Recirculation Audit

Generated: `{summary['generated_at']}`

## Result

This package consumes the six harvested `corner_lower_right` raw endpoint rows
and separates static pressure, `p_rgh`, hydrostatic correction, kinetic
correction, local density, bulk velocity, and local dynamic-pressure basis
terms. It also aggregates same-window endpoint RAF/RMF/SVF recirculation
metrics.

The raw pressure/velocity basis is finite for all three Salt2/Salt3/Salt4
feature pairs. Ordinary component-K admission remains blocked because all three
pairs fail the recirculation gate. Component isolation and same-QOI uncertainty
are not audited here and remain downstream tasks.

## Current Counts

- Feature pairs audited: `{summary['feature_pairs']}`
- Basis resolved pairs: `{summary['basis_resolved_pairs']}`
- Recirculation pass pairs: `{summary['recirculation_pass_pairs']}`
- Recirculation fail pairs: `{summary['recirculation_fail_pairs']}`
- Ordinary component-K candidates: `{summary['ordinary_component_k_candidates']}`

## Outputs

- `pressure_velocity_basis_audit.csv`
- `endpoint_recirculation_metrics.csv`
- `gate_decision_table.csv`
- `next_action_queue.csv`
- `source_manifest.csv`
- `summary.json`

## Guardrails

No native CFD/OpenFOAM output was mutated. No registry/admission state, Fluid
source, F6 fit, component-K admission, model selection, or endpoint-pressure
invention was performed.
""",
        encoding="utf-8",
    )


def build_package() -> dict[str, Any]:
    OUT.mkdir(parents=True, exist_ok=True)
    raw_rows = read_csv(SAMPLER / "raw_endpoint_pressure_velocity.csv")
    pairs = load_sampled_pairs(raw_rows)
    if len(pairs) != 3:
        raise RuntimeError(f"Expected 3 upstream/downstream feature pairs, found {len(pairs)}")
    basis = pressure_basis_rows(pairs)
    recirc = recirculation_rows(pairs)
    gates = gate_decision_rows(basis, recirc)
    next_actions = next_action_rows()
    write_csv(OUT / "pressure_velocity_basis_audit.csv", basis, BASIS_FIELDS)
    write_csv(OUT / "endpoint_recirculation_metrics.csv", recirc, RECIRC_FIELDS)
    write_csv(OUT / "gate_decision_table.csv", gates, GATE_FIELDS)
    write_csv(OUT / "next_action_queue.csv", next_actions, NEXT_FIELDS)
    write_csv(OUT / "source_manifest.csv", source_manifest_rows(), ["source_id", "path", "use", "mutation"])
    summary = {
        "task": TASK,
        "generated_at": utc_now(),
        "output_dir": rel(OUT),
        "feature_pairs": len(basis),
        "basis_resolved_pairs": sum(1 for row in basis if row["basis_status"] == "basis_resolved_raw_endpoint_diagnostic"),
        "recirculation_pass_pairs": sum(1 for row in recirc if row["ordinary_recirculation_gate"] == "pass_nonrecirculating"),
        "recirculation_fail_pairs": sum(1 for row in recirc if row["ordinary_recirculation_gate"] != "pass_nonrecirculating"),
        "ordinary_component_k_candidates": sum(1 for row in gates if row["ordinary_component_k_candidate"] == "true"),
        "f6_fit_performed": False,
        "component_k_admitted": False,
        "native_solver_outputs_mutated": False,
        "registry_or_admission_mutated": False,
        "scheduler_action": "none",
        "generated_docs_index_refreshed": False,
    }
    write_json(OUT / "summary.json", summary)
    write_readme(summary)
    return summary


def main() -> None:
    summary = build_package()
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
