#!/usr/bin/env python3
"""Build a thermal passive/source-sink unblock packet from existing evidence.

This is an accounting and gate reducer only. It ranks source-evidence gaps and
records one freeze/no-freeze decision without using realized wallHeatFlux or
validation temperatures as runtime inputs.
"""

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

from tools.common import WORKSPACE_ROOT, csv_dump, ensure_dir, iso_timestamp, json_dump, relative_to_workspace


TASK_ID = "TODO-THERMAL-PASSIVE-SOURCE-SINK-UNBLOCK-PACKET-2026-07-22"
OUT = WORKSPACE_ROOT / (
    "work_products/2026-07/2026-07-22/"
    "2026-07-22_thermal_passive_source_sink_unblock_packet"
)

SOURCES = {
    "thermal_accounting": WORKSPACE_ROOT
    / "work_products/2026-07/2026-07-22/2026-07-22_thesis_study_thermal_accounting_traceability_evidence_packet",
    "passive_basis": WORKSPACE_ROOT
    / "work_products/2026-07/2026-07-21/2026-07-21_passive_h2_cand001_physical_basis",
    "passive_enrichment": WORKSPACE_ROOT
    / "work_products/2026-07/2026-07-21/2026-07-21_fluid_extbc_passive_h2_cand001_source_basis_enrichment",
    "source_runtime": WORKSPACE_ROOT
    / "work_products/2026-07/2026-07-21/2026-07-21_fluid_setup_known_source_sink_runtime_contract",
    "mf13": WORKSPACE_ROOT
    / "work_products/2026-07/2026-07-22/2026-07-22_mf13_signed_source_property_heat_path_release_preflight",
    "mf15": WORKSPACE_ROOT
    / "work_products/2026-07/2026-07-22/2026-07-22_mf15_runtime_wall_profile_basis_gate",
    "four_study": WORKSPACE_ROOT
    / "work_products/2026-07/2026-07-22/2026-07-22_four_study_thesis_support_gate",
    "s13_exact": WORKSPACE_ROOT
    / "work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_exact_pressure_qwall_compute",
}


def rel(path: Path) -> str:
    return relative_to_workspace(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def as_float(value: str) -> float:
    return 0.0 if value == "" else float(value)


def require_sources() -> None:
    required = [
        SOURCES["thermal_accounting"] / "summary.json",
        SOURCES["thermal_accounting"] / "missing_setup_fields.csv",
        SOURCES["thermal_accounting"] / "setup_source_sink_values.csv",
        SOURCES["thermal_accounting"] / "diagnostic_heat_values_by_case_role.csv",
        SOURCES["thermal_accounting"] / "residual_owner_gate_matrix.csv",
        SOURCES["thermal_accounting"] / "runtime_forbidden_input_audit.csv",
        SOURCES["passive_basis"] / "repair_gate.csv",
        SOURCES["passive_basis"] / "current_hA_basis_and_provenance_risk.csv",
        SOURCES["passive_enrichment"] / "repair_readiness_decision.csv",
        SOURCES["mf13"] / "source_property_release_gate.csv",
        SOURCES["mf15"] / "wall_profile_release_gate.csv",
        SOURCES["four_study"] / "candidate_freeze_readiness_matrix.csv",
        SOURCES["s13_exact"] / "summary.json",
    ]
    missing = [rel(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("missing thermal unblock sources: " + "; ".join(missing))


def source_evidence_gap_table() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    priority = 1
    for row in read_csv(SOURCES["thermal_accounting"] / "missing_setup_fields.csv"):
        rows.append(
            {
                "priority": priority,
                "gap_id": row["missing_field_id"],
                "affected_lanes": row["affected_lanes"],
                "current_status": row["current_status"],
                "source_evidence_needed": row["next_action"],
                "why_it_unblocks": "turns residual ownership into source-backed model basis before any candidate scoring",
                "forbidden_inference": row["what_not_to_infer"],
                "release_allowed_now": False,
                "source_paths": row["source_paths"],
            }
        )
        priority += 1

    for row in read_csv(SOURCES["mf13"] / "source_property_release_gate.csv"):
        if row["status"].startswith("fail"):
            rows.append(
                {
                    "priority": priority,
                    "gap_id": "mf13_" + row["gate"],
                    "affected_lanes": "source_property;runtime_formula;passive_wall;test_section",
                    "current_status": row["status"],
                    "source_evidence_needed": row["missing_for_release"],
                    "why_it_unblocks": "source/property release is prerequisite for runtime-legal heat-path inputs",
                    "forbidden_inference": "do not convert diagnostic signs or magnitudes into released source/property inputs",
                    "release_allowed_now": row["release_allowed"],
                    "source_paths": rel(SOURCES["mf13"] / "source_property_release_gate.csv"),
                }
            )
            priority += 1

    for row in read_csv(SOURCES["mf15"] / "wall_profile_release_gate.csv"):
        if row["status"].startswith("fail"):
            rows.append(
                {
                    "priority": priority,
                    "gap_id": "mf15_" + row["gate"],
                    "affected_lanes": "wall_profile;bulk_to_TP;passive_boundary",
                    "current_status": row["status"],
                    "source_evidence_needed": row["missing_for_release"],
                    "why_it_unblocks": "runtime wall/profile operators need source-bounded basis before correction release",
                    "forbidden_inference": "do not release D3/MF15 diagnostic wall-profile correction as runtime input",
                    "release_allowed_now": row["release_allowed"],
                    "source_paths": rel(SOURCES["mf15"] / "wall_profile_release_gate.csv"),
                }
            )
            priority += 1
    return rows


def passive_basis_gate() -> list[dict[str, Any]]:
    repair = read_csv(SOURCES["passive_basis"] / "repair_gate.csv")[0]
    rows = []
    for row in read_csv(SOURCES["passive_basis"] / "current_hA_basis_and_provenance_risk.csv"):
        rows.append(
            {
                "candidate_id": repair["candidate_id"],
                "source_family": row["source_family"],
                "priority_rank": row["priority_rank"],
                "current_hA_W_K": row["current_hA_W_K"],
                "h2_tw5_abs_improvement_K": row["h2_tw5_abs_improvement_K"],
                "current_h_inside_screen": repair["current_h_inside_broad_engineering_screen_all_families"],
                "current_q_inside_screen": repair["current_q_inside_broad_engineering_screen_all_families"],
                "wallHeatFlux_provenance_present": row["wallHeatFlux_provenance_present"],
                "ambient_basis_source_released": repair["ambient_basis_source_released"],
                "repair_run_allowed_now": repair["repair_run_allowed_now"],
                "basis_decision": row["current_basis_decision"],
                "next_unblock_action": repair["next_action"],
                "forbidden_shortcut": repair["forbidden_shortcut"],
                "claim_boundary": row["claim_boundary"],
            }
        )
    return rows


def source_sink_residual_decomposition() -> list[dict[str, Any]]:
    setup_by_case_role: dict[tuple[str, str], float] = defaultdict(float)
    split_by_case: dict[str, str] = {}
    for row in read_csv(SOURCES["thermal_accounting"] / "setup_source_sink_values.csv"):
        setup_by_case_role[(row["case_id"], row["physical_role"])] += as_float(row["setup_value_W"])
        split_by_case[row["case_id"]] = row["split_role"]

    diagnostic_by_case_owner: dict[tuple[str, str], float] = defaultdict(float)
    quality_by_case_owner: dict[tuple[str, str], set[str]] = defaultdict(set)
    for row in read_csv(SOURCES["thermal_accounting"] / "diagnostic_heat_values_by_case_role.csv"):
        diagnostic_by_case_owner[(row["case_id"], row["residual_owner"])] += as_float(
            row["diagnostic_heat_to_fluid_W_sum"]
        )
        for flag in row["quality_flags"].split(";"):
            if flag:
                quality_by_case_owner[(row["case_id"], row["residual_owner"])].add(flag)

    role_to_owner = {
        "heater": "heater_source_storage_gap",
        "cooler": "cooler_hx_removal",
        "test_section": "test_section_source_loss",
    }
    out: list[dict[str, Any]] = []
    for (case_id, role), setup_w in sorted(setup_by_case_role.items()):
        owner = role_to_owner[role]
        diagnostic_w = diagnostic_by_case_owner.get((case_id, owner), 0.0)
        out.append(
            {
                "case_id": case_id,
                "split_role": split_by_case[case_id],
                "physical_role": role,
                "residual_owner": owner,
                "setup_value_W": setup_w,
                "diagnostic_heat_to_fluid_W": diagnostic_w,
                "diagnostic_minus_setup_W": diagnostic_w - setup_w,
                "runtime_allowed_now": False,
                "release_status": "diagnostic_accounting_only",
                "quality_flags": ";".join(sorted(quality_by_case_owner.get((case_id, owner), set()))),
                "claim_boundary": "source/sink residual decomposition only; no runtime source release or fit",
            }
        )
    return out


def s13_consumption_boundary() -> list[dict[str, Any]]:
    s13 = read_json(SOURCES["s13_exact"] / "summary.json")
    return [
        {
            "qoi_family": "S13-DIRECT-QWALL",
            "current_evidence": f"{s13['Q_wall_W_released_rows']} exact target-window Q_wall_W rows",
            "consume_as": "diagnostic sampled-field evidence",
            "runtime_release_allowed_now": False,
            "production_harvest_allowed_now": s13["production_harvest_allowed_now"],
            "same_qoi_uq_ready": s13["same_qoi_uq_ready"],
            "admission_allowed": s13["admission_allowed"],
            "next_unblock_action": "wait for same-QOI UQ and production-harvest gate under S13-owned rows",
            "forbidden_shortcut": "do not relabel direct Qwall as source/property release or runtime wallHeatFlux input",
        },
        {
            "qoi_family": "S13-SOURCE-SIDE-EQUIVALENT",
            "current_evidence": "source-side conservation rows exist in separate packages but are not Q_wall_W release",
            "consume_as": "source-side diagnostic consistency evidence",
            "runtime_release_allowed_now": False,
            "production_harvest_allowed_now": False,
            "same_qoi_uq_ready": False,
            "admission_allowed": False,
            "next_unblock_action": "require same-QOI source-side conservation UQ and explicit non-relabel policy",
            "forbidden_shortcut": "do not use source-side static-boundary Q as realized wall heat flux",
        },
    ]


def freeze_no_freeze_gate() -> list[dict[str, Any]]:
    rows = []
    for row in read_csv(SOURCES["four_study"] / "candidate_freeze_readiness_matrix.csv"):
        rows.append(
            {
                "candidate_or_lane": row["candidate_or_lane"],
                "basis": row["basis"],
                "diagnostic_evidence_available": row["diagnostic_evidence_available"],
                "source_property_released": row["source_property_released"],
                "qwall_or_equivalent_released": row["qwall_or_equivalent_released"],
                "same_qoi_uq_ready": row["same_qoi_uq_ready"],
                "production_or_repair_allowed": row["production_or_repair_allowed"],
                "candidate_released": row["candidate_released"],
                "freeze_decision": row["freeze_decision"],
                "blocking_reason": row["blocking_reason"],
                "current_action": (
                    "top candidate for next freeze/no-freeze revisit after source-basis release"
                    if row["candidate_or_lane"] == "PASSIVE-H2-CAND001"
                    else "hold as supporting lane"
                ),
            }
        )
    return rows


def runtime_forbidden_audit() -> list[dict[str, str]]:
    return read_csv(SOURCES["thermal_accounting"] / "runtime_forbidden_input_audit.csv")


def source_manifest() -> list[dict[str, str]]:
    return [
        {"source_id": key, "path": rel(path), "mutation": "read_only", "role": "evidence source"}
        for key, path in SOURCES.items()
    ]


def no_mutation_guardrails() -> list[dict[str, Any]]:
    return [
        {"guardrail": "native_output_mutation", "value": False},
        {"guardrail": "registry_or_admission_mutation", "value": False},
        {"guardrail": "scheduler_action", "value": False},
        {"guardrail": "solver_postprocessing_sampler_harvest_uq_launched", "value": False},
        {"guardrail": "runtime_wallHeatFlux_or_validation_temperature_release", "value": False},
        {"guardrail": "Qwall_or_source_property_release", "value": False},
        {"guardrail": "candidate_freeze", "value": False},
        {"guardrail": "fitting_or_model_selection", "value": False},
        {"guardrail": "residual_absorbed_into_internal_Nu", "value": False},
    ]


def write_readme(out: Path, summary: dict[str, Any]) -> None:
    text = f"""---
provenance:
  - {rel(SOURCES['thermal_accounting'] / 'summary.json')}
  - {rel(SOURCES['passive_basis'] / 'repair_gate.csv')}
  - {rel(SOURCES['mf13'] / 'source_property_release_gate.csv')}
  - {rel(SOURCES['four_study'] / 'candidate_freeze_readiness_matrix.csv')}
tags: [thermal, passive-boundary, source-sink, freeze-gate, no-fit]
related:
  - .agent/status/2026-07-22_{TASK_ID}.md
  - .agent/journal/2026-07-22/thermal-passive-source-sink-unblock-packet.md
  - imports/2026-07-22_thermal_passive_source_sink_unblock_packet.json
task: {TASK_ID}
date: 2026-07-22
role: Thermal-modeling/Forward-pred/Implementer/Tester/Writer/Reviewer
type: work_product
status: complete
---
# Thermal Passive / Source-Sink Unblock Packet

Decision: `{summary['decision']}`.

This package converts the thermal accounting packet into an actionable unblock
matrix. It ranks the passive physical-basis and source/sink residual evidence
still needed before any candidate freeze or repair run.

Key counts:

- source evidence gap rows: `{summary['source_evidence_gap_rows']}`
- passive basis family rows: `{summary['passive_basis_family_rows']}`
- source/sink residual decomposition rows: `{summary['source_sink_residual_decomposition_rows']}`
- S13 consumption boundary rows: `{summary['s13_consumption_boundary_rows']}`
- freeze/no-freeze rows: `{summary['freeze_no_freeze_rows']}`
- released freeze candidates: `{summary['released_freeze_candidates']}`

Primary outputs:

- `source_evidence_gap_rank.csv`
- `passive_physical_basis_gate.csv`
- `source_sink_residual_decomposition_refresh.csv`
- `s13_consumption_readiness_boundary.csv`
- `freeze_no_freeze_gate.csv`
- `runtime_forbidden_input_audit.csv`
- `source_manifest.csv`
- `no_mutation_guardrails.csv`
- `summary.json`

The next practical unblock is source-backed passive hA/area/material/ambient/
insulation evidence for `PASSIVE-H2-CAND001`. No realized CFD wallHeatFlux,
validation temperatures, CFD mdot, Qwall release, source/property release,
fit, repair, or freeze occurred in this package.
"""
    (out / "README.md").write_text(text, encoding="utf-8")


def build(out: Path = OUT) -> dict[str, Any]:
    require_sources()
    ensure_dir(out)

    gaps = source_evidence_gap_table()
    passive = passive_basis_gate()
    decomposition = source_sink_residual_decomposition()
    s13_boundary = s13_consumption_boundary()
    freeze_gate = freeze_no_freeze_gate()
    forbidden = runtime_forbidden_audit()
    guardrails = no_mutation_guardrails()

    csv_dump(out / "source_evidence_gap_rank.csv", list(gaps[0].keys()), gaps)
    csv_dump(out / "passive_physical_basis_gate.csv", list(passive[0].keys()), passive)
    csv_dump(
        out / "source_sink_residual_decomposition_refresh.csv",
        list(decomposition[0].keys()),
        decomposition,
    )
    csv_dump(out / "s13_consumption_readiness_boundary.csv", list(s13_boundary[0].keys()), s13_boundary)
    csv_dump(out / "freeze_no_freeze_gate.csv", list(freeze_gate[0].keys()), freeze_gate)
    csv_dump(out / "runtime_forbidden_input_audit.csv", list(forbidden[0].keys()), forbidden)
    csv_dump(out / "source_manifest.csv", ["source_id", "path", "mutation", "role"], source_manifest())
    csv_dump(out / "no_mutation_guardrails.csv", ["guardrail", "value"], guardrails)

    accounting_summary = read_json(SOURCES["thermal_accounting"] / "summary.json")
    s13_summary = read_json(SOURCES["s13_exact"] / "summary.json")
    summary = {
        "task_id": TASK_ID,
        "generated_at": iso_timestamp(),
        "decision": "thermal_unblock_packet_ready_no_freeze_no_runtime_leakage",
        "source_evidence_gap_rows": len(gaps),
        "passive_basis_family_rows": len(passive),
        "source_sink_residual_decomposition_rows": len(decomposition),
        "s13_consumption_boundary_rows": len(s13_boundary),
        "freeze_no_freeze_rows": len(freeze_gate),
        "released_freeze_candidates": sum(row["candidate_released"] == "true" for row in freeze_gate),
        "passive_repair_allowed_rows": sum(row["repair_run_allowed_now"] == "true" for row in passive),
        "source_property_release_allowed_rows": 0,
        "runtime_wallHeatFlux_or_validation_temperature_release": False,
        "runtime_forbidden_input_rows": len(forbidden),
        "s13_exact_qwall_rows_available_diagnostic": s13_summary["Q_wall_W_released_rows"],
        "s13_same_qoi_uq_ready": s13_summary["same_qoi_uq_ready"],
        "candidate_freeze": False,
        "fitting_or_model_selection": False,
        "validation_holdout_external_rows_scored": 0,
        "native_output_mutation": False,
        "registry_or_admission_mutation": False,
        "scheduler_action": False,
        "solver_sampler_harvest_uq_launched": False,
        "Fluid_or_external_repo_mutation": False,
        "Qwall_or_source_property_release": False,
        "residual_absorbed_into_internal_Nu": False,
        "upstream_thermal_accounting_decision": accounting_summary["decision"],
    }
    json_dump(out / "summary.json", summary)
    write_readme(out, summary)
    return summary


def main() -> None:
    summary = build()
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
