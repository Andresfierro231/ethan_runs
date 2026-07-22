#!/usr/bin/env python3
"""Build a PASSIVE-H2 source-basis release preflight.

This reducer separates independently source-backed evidence from diagnostic
wallHeatFlux-derived evidence before any passive-boundary repair/freeze.
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


TASK_ID = "TODO-THERMAL-PASSIVE-H2-SOURCE-BASIS-RELEASE-PREFLIGHT-2026-07-22"
OUT = WORKSPACE_ROOT / (
    "work_products/2026-07/2026-07-22/"
    "2026-07-22_thermal_passive_h2_source_basis_release_preflight"
)

SOURCES = {
    "unblock_packet": WORKSPACE_ROOT
    / "work_products/2026-07/2026-07-22/2026-07-22_thermal_passive_source_sink_unblock_packet",
    "passive_basis": WORKSPACE_ROOT
    / "work_products/2026-07/2026-07-21/2026-07-21_passive_h2_cand001_physical_basis",
    "passive_enrichment": WORKSPACE_ROOT
    / "work_products/2026-07/2026-07-21/2026-07-21_fluid_extbc_passive_h2_cand001_source_basis_enrichment",
    "external_bc": WORKSPACE_ROOT
    / "work_products/2026-07/2026-07-21/2026-07-21_heatloss_phase_1_external_bc_radiation_integration",
}


def rel(path: Path) -> str:
    return relative_to_workspace(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def require_sources() -> None:
    required = [
        SOURCES["unblock_packet"] / "summary.json",
        SOURCES["unblock_packet"] / "passive_physical_basis_gate.csv",
        SOURCES["passive_basis"] / "area_coverage_basis.csv",
        SOURCES["passive_basis"] / "ambient_surroundings_basis.csv",
        SOURCES["passive_basis"] / "independent_h_estimate_range.csv",
        SOURCES["passive_basis"] / "expected_q_loss_envelope.csv",
        SOURCES["passive_basis"] / "repair_gate.csv",
        SOURCES["passive_basis"] / "current_hA_basis_and_provenance_risk.csv",
        SOURCES["passive_enrichment"] / "source_basis_coverage.csv",
        SOURCES["passive_enrichment"] / "repair_readiness_decision.csv",
        SOURCES["external_bc"] / "external_bc_segment_role_audit.csv",
    ]
    missing = [rel(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("missing thermal passive H2 preflight sources: " + "; ".join(missing))


def by_family(path: Path) -> dict[str, dict[str, str]]:
    return {row["source_family"]: row for row in read_csv(path)}


def passive_source_release_checklist() -> list[dict[str, Any]]:
    areas = by_family(SOURCES["passive_basis"] / "area_coverage_basis.csv")
    ambient = by_family(SOURCES["passive_basis"] / "ambient_surroundings_basis.csv")
    h_ranges = by_family(SOURCES["passive_basis"] / "independent_h_estimate_range.csv")
    q_ranges = by_family(SOURCES["passive_basis"] / "expected_q_loss_envelope.csv")
    h_basis = by_family(SOURCES["passive_basis"] / "current_hA_basis_and_provenance_risk.csv")
    enrichment = by_family(SOURCES["passive_enrichment"] / "source_basis_coverage.csv")

    rows: list[dict[str, Any]] = []
    for family in sorted(enrichment):
        area = areas[family]
        amb = ambient[family]
        h_row = h_ranges[family]
        q_row = q_ranges[family]
        h_base = h_basis[family]
        enr = enrichment[family]

        area_supported_for_aggregation = area["aggregation_defensible_now"] == "True"
        geometry_released = area["geometry_support_status"] == "source_released"
        ambient_released = amb["ambient_basis_status"] == "source_released"
        h_released = h_row["literature_provenance_status"] == "source_released"
        q_released = q_row["material_q_basis_for_repair"] == "True"
        wall_heat_flux_independent = enr["wall_heat_flux_provenance_present"] == "False"
        release_ready = all(
            [
                area_supported_for_aggregation,
                geometry_released,
                ambient_released,
                h_released,
                q_released,
                wall_heat_flux_independent,
                enr["independent_source_release_allowed_now"] == "true",
            ]
        )

        missing = []
        if not geometry_released:
            missing.append(area["required_before_repair"])
        if not ambient_released:
            missing.append("setup room/surroundings temperature source and role-vs-ledger reconciliation")
        if not h_released:
            missing.append(h_row["needed_for_source_release"])
        if not q_released:
            missing.append("source-backed q-loss basis independent of Phase E fixed-state diagnostic estimate")
        if not wall_heat_flux_independent:
            missing.append("replace wallHeatFlux-derived passive h provenance with independent source basis")

        rows.append(
            {
                "candidate_id": "PASSIVE-H2-CAND001",
                "source_family": family,
                "priority_rank": h_base["priority_rank"],
                "current_area_m2": area["current_area_m2"],
                "current_hA_W_K": enr["current_hA_W_K"],
                "current_q_inside_engineering_envelope": enr["current_q_inside_engineering_envelope"],
                "area_supported_for_aggregation": area_supported_for_aggregation,
                "geometry_source_released": geometry_released,
                "ambient_source_released": ambient_released,
                "h_correlation_source_released": h_released,
                "q_loss_source_released": q_released,
                "wallHeatFlux_independent": wall_heat_flux_independent,
                "source_basis_release_ready_now": release_ready,
                "repair_ready_now": enr["repair_ready_now"] == "true",
                "exact_missing_provenance": " | ".join(dict.fromkeys(item for item in missing if item)),
                "next_action": enr["next_required"],
                "claim_boundary": "preflight only; no runtime wallHeatFlux, Qwall, source-property release, repair, fit, or freeze",
                "source_paths": ";".join(
                    [
                        rel(SOURCES["passive_basis"] / "area_coverage_basis.csv"),
                        rel(SOURCES["passive_basis"] / "ambient_surroundings_basis.csv"),
                        rel(SOURCES["passive_basis"] / "independent_h_estimate_range.csv"),
                        rel(SOURCES["passive_basis"] / "expected_q_loss_envelope.csv"),
                        rel(SOURCES["passive_enrichment"] / "source_basis_coverage.csv"),
                    ]
                ),
            }
        )
    return rows


def source_backed_vs_diagnostic_split() -> list[dict[str, Any]]:
    external_rows = read_csv(SOURCES["external_bc"] / "external_bc_segment_role_audit.csv")
    by_role: defaultdict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "segment_rows": 0,
            "has_h_and_layers_rows": 0,
            "schema_ready_rows": 0,
            "diagnostic_wallHeatFlux_rows": 0,
            "predictive_wallHeatFlux_runtime_allowed_rows": 0,
            "source_property_released_rows": 0,
        }
    )
    for row in external_rows:
        role = row["segment_id"]
        bucket = by_role[role]
        bucket["segment_rows"] += 1
        if "h_and_layers_present" in row["wall_layer_metadata_status"]:
            bucket["has_h_and_layers_rows"] += 1
        if row["predictive_runtime_status"] == "schema_ready_setup_inputs_only":
            bucket["schema_ready_rows"] += 1
        if row["realized_wallHeatFlux_diagnostic_W"] != "":
            bucket["diagnostic_wallHeatFlux_rows"] += 1
        if row["wallHeatFlux_runtime_allowed_predictive"] == "true":
            bucket["predictive_wallHeatFlux_runtime_allowed_rows"] += 1
        if row["source_property_label_status"] == "released":
            bucket["source_property_released_rows"] += 1

    rows = []
    for role, bucket in sorted(by_role.items()):
        rows.append(
            {
                "segment_or_family": role,
                "segment_rows": bucket["segment_rows"],
                "setup_hA_layer_schema_present_rows": bucket["has_h_and_layers_rows"],
                "schema_ready_setup_input_rows": bucket["schema_ready_rows"],
                "diagnostic_wallHeatFlux_rows": bucket["diagnostic_wallHeatFlux_rows"],
                "predictive_wallHeatFlux_runtime_allowed_rows": bucket[
                    "predictive_wallHeatFlux_runtime_allowed_rows"
                ],
                "source_property_released_rows": bucket["source_property_released_rows"],
                "classification": "mixed_schema_and_diagnostic_evidence_no_runtime_release",
                "allowed_use_now": "traceability/accounting only",
                "forbidden_runtime_input": "realized wallHeatFlux; validation temperatures; CFD mdot; fitted passive multipliers",
            }
        )
    return rows


def exact_missing_provenance_fields(checklist: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for item in checklist:
        fields = [field.strip() for field in item["exact_missing_provenance"].split("|") if field.strip()]
        for field in fields:
            rows.append(
                {
                    "candidate_id": item["candidate_id"],
                    "source_family": item["source_family"],
                    "missing_field_or_basis": field,
                    "blocks_source_basis_release": True,
                    "blocks_repair_or_freeze": True,
                    "allowed_resolution": "source-backed document/table/package row only",
                    "forbidden_resolution": "diagnostic wallHeatFlux, validation-temperature, or global-multiplier fit",
                }
            )
    return rows


def repair_freeze_decision() -> list[dict[str, Any]]:
    repair_gate = read_csv(SOURCES["passive_basis"] / "repair_gate.csv")[0]
    readiness = read_csv(SOURCES["passive_enrichment"] / "repair_readiness_decision.csv")[0]
    return [
        {
            "candidate_id": "PASSIVE-H2-CAND001",
            "decision": "no_repair_no_freeze_source_basis_not_released",
            "current_gate": repair_gate["gate_decision"],
            "run_one_train_repair": False,
            "source_property_release_allowed_now": False,
            "runtime_input_release_allowed_now": False,
            "freeze_or_admission_allowed_now": False,
            "predeclared_change": readiness["predeclared_change"],
            "rationale": readiness["rationale"],
            "next_claimable": readiness["next_claimable"],
            "forbidden_shortcut": repair_gate["forbidden_shortcut"],
        }
    ]


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
        {"guardrail": "passive_repair_run", "value": False},
        {"guardrail": "candidate_freeze", "value": False},
        {"guardrail": "fitting_or_model_selection", "value": False},
        {"guardrail": "residual_absorbed_into_internal_Nu", "value": False},
    ]


def write_readme(out: Path, summary: dict[str, Any]) -> None:
    text = f"""---
provenance:
  - {rel(SOURCES['passive_basis'] / 'area_coverage_basis.csv')}
  - {rel(SOURCES['passive_basis'] / 'independent_h_estimate_range.csv')}
  - {rel(SOURCES['passive_enrichment'] / 'source_basis_coverage.csv')}
tags: [thermal, passive-boundary, source-basis, no-repair, no-freeze]
related:
  - .agent/status/2026-07-22_{TASK_ID}.md
  - .agent/journal/2026-07-22/thermal-passive-h2-source-basis-release-preflight.md
  - imports/2026-07-22_thermal_passive_h2_source_basis_release_preflight.json
task: {TASK_ID}
date: 2026-07-22
role: Thermal-modeling/Forward-pred/Implementer/Tester/Writer/Reviewer
type: work_product
status: complete
---
# Thermal PASSIVE-H2 Source-Basis Release Preflight

Decision: `{summary['decision']}`.

This package turns the passive H2 physical-basis evidence into a family-by-family
release preflight. The broad h/q screens are useful but remain diagnostic until
geometry, ambient, insulation, and literature/correlation provenance are
source-backed and independent of realized `wallHeatFlux`.

Key counts:

- passive source-family rows: `{summary['passive_source_family_rows']}`
- source-basis release-ready rows: `{summary['source_basis_release_ready_rows']}`
- repair-ready rows: `{summary['repair_ready_rows']}`
- exact missing provenance rows: `{summary['exact_missing_provenance_rows']}`
- diagnostic wallHeatFlux segment rows: `{summary['diagnostic_wallHeatFlux_segment_rows']}`

Primary outputs:

- `passive_source_release_checklist.csv`
- `source_backed_vs_diagnostic_split.csv`
- `exact_missing_provenance_fields.csv`
- `repair_freeze_decision.csv`
- `source_manifest.csv`
- `no_mutation_guardrails.csv`
- `summary.json`

No runtime `wallHeatFlux`, validation-temperature, CFD-mdot, Qwall,
source-property, coefficient, repair, freeze, fitting, model-selection, or
residual-absorption release occurred.
"""
    (out / "README.md").write_text(text, encoding="utf-8")


def build(out: Path = OUT) -> dict[str, Any]:
    require_sources()
    ensure_dir(out)

    checklist = passive_source_release_checklist()
    split = source_backed_vs_diagnostic_split()
    missing = exact_missing_provenance_fields(checklist)
    decision = repair_freeze_decision()
    guardrails = no_mutation_guardrails()

    csv_dump(out / "passive_source_release_checklist.csv", list(checklist[0].keys()), checklist)
    csv_dump(out / "source_backed_vs_diagnostic_split.csv", list(split[0].keys()), split)
    csv_dump(out / "exact_missing_provenance_fields.csv", list(missing[0].keys()), missing)
    csv_dump(out / "repair_freeze_decision.csv", list(decision[0].keys()), decision)
    csv_dump(out / "source_manifest.csv", ["source_id", "path", "mutation", "role"], source_manifest())
    csv_dump(out / "no_mutation_guardrails.csv", ["guardrail", "value"], guardrails)

    upstream = read_json(SOURCES["unblock_packet"] / "summary.json")
    summary = {
        "task_id": TASK_ID,
        "generated_at": iso_timestamp(),
        "decision": "thermal_passive_h2_preflight_complete_no_source_release_no_repair_no_freeze",
        "passive_source_family_rows": len(checklist),
        "source_basis_release_ready_rows": sum(row["source_basis_release_ready_now"] for row in checklist),
        "repair_ready_rows": sum(row["repair_ready_now"] for row in checklist),
        "exact_missing_provenance_rows": len(missing),
        "source_backed_vs_diagnostic_rows": len(split),
        "diagnostic_wallHeatFlux_segment_rows": sum(int(row["diagnostic_wallHeatFlux_rows"]) for row in split),
        "predictive_wallHeatFlux_runtime_allowed_rows": sum(
            int(row["predictive_wallHeatFlux_runtime_allowed_rows"]) for row in split
        ),
        "source_property_released_rows": sum(int(row["source_property_released_rows"]) for row in split),
        "candidate_freeze": False,
        "passive_repair_run": False,
        "runtime_wallHeatFlux_or_validation_temperature_release": False,
        "Qwall_or_source_property_release": False,
        "fitting_or_model_selection": False,
        "native_output_mutation": False,
        "registry_or_admission_mutation": False,
        "scheduler_action": False,
        "solver_sampler_harvest_uq_launched": False,
        "residual_absorbed_into_internal_Nu": False,
        "upstream_unblock_decision": upstream["decision"],
    }
    json_dump(out / "summary.json", summary)
    write_readme(out, summary)
    return summary


def main() -> None:
    summary = build()
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
