#!/usr/bin/env python3
"""Build Phase 2 split heat-loss evidence from existing ledgers.

This builder only consumes prior repo artifacts. It does not read or mutate
native solver outputs, launch extraction, fit coefficients, or admit models.
"""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TASK = "TODO-HEATLOSS-PHASE-2-SPLIT-HEAT-LOSS-EVIDENCE"
ROOT = Path(__file__).resolve().parents[2]
OUT_REL = Path("work_products/2026-07/2026-07-21/2026-07-21_heatloss_phase_2_split_heat_loss_evidence")
OUT = ROOT / OUT_REL

PATCHWISE = ROOT / "work_products/2026-07/2026-07-08/2026-07-08_patchwise_heat_ledger"
INTERFACES = (
    ROOT
    / "work_products/2026-07/2026-07-08/"
    "2026-07-08_patchwise_heat_ledger_enthalpy_interfaces"
)
HEAT_AUDIT = (
    ROOT
    / "work_products/2026-07/2026-07-16/"
    "2026-07-16_pressure_loop_plot_and_cfd_heat_audit"
)
HEAT_CONTRACT = (
    ROOT
    / "work_products/2026-07/2026-07-21/"
    "2026-07-21_litrev_thermal_heat_loss_contract_alignment"
)
PHASE1 = (
    ROOT
    / "work_products/2026-07/2026-07-21/"
    "2026-07-21_heatloss_phase_1_external_bc_radiation_integration"
)
THERMAL_MAP = ROOT / "operational_notes/maps/thermal-boundary-and-radiation.md"

PATCHWISE_LEDGER = PATCHWISE / "patchwise_heat_ledger.csv"
SEGMENT_RESIDUALS = INTERFACES / "segment_enthalpy_residuals.csv"
RESISTANCE_TERMS = INTERFACES / "resistance_network_terms.csv"
JUNCTION_TRENDS = HEAT_AUDIT / "junction_heat_loss_trends.csv"
HEAT_CONTRACT_CSV = HEAT_CONTRACT / "heat_loss_path_contract.csv"
PHASE1_SEGMENT_AUDIT = PHASE1 / "external_bc_segment_role_audit.csv"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = []
        for row in rows:
            for key in row:
                if key not in fieldnames:
                    fieldnames.append(key)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def as_float(value: str) -> float:
    if value is None or value == "":
        return 0.0
    return float(value)


def patch_family(patch_name: str) -> str:
    for family in ("lower_left", "lower_right", "upper_left", "upper_right"):
        if family in patch_name:
            return family
    return "other_junction_or_stub"


def split_patch_names(value: str) -> list[str]:
    return [part.strip() for part in value.split(",") if part.strip()]


def split_junction_rows(patch_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str], dict[str, Any]] = {}
    for row in patch_rows:
        if row["patch_group"] != "junction_other":
            continue
        names = split_patch_names(row["patch_names"])
        total_area = as_float(row["patch_area_m2"])
        total_heat = as_float(row["wallHeatFlux_integral_W"])
        count_by_family = defaultdict(int)
        for name in names:
            count_by_family[patch_family(name)] += 1
        denominator = sum(count_by_family.values()) or 1
        for family in ("lower_left", "lower_right", "upper_left", "upper_right"):
            count = count_by_family.get(family, 0)
            key = (row["case_id"], row["source_id"], family)
            grouped[key] = {
                "case_id": row["case_id"],
                "source_id": row["source_id"],
                "junction_family": family,
                "patch_count": count,
                "split_basis": "patch_name_family_fraction_of_grouped_junction_wallHeatFlux",
                "split_status": "estimated_from_grouped_junction_row_not_new_sampling",
                "wallHeatFlux_diagnostic_W": f"{total_heat * count / denominator:.10g}",
                "area_m2": f"{total_area * count / denominator:.10g}",
                "qr_presence_status": row["radiation_output_term"] or "absent_no_qr_output",
                "storage_proxy_status": "absent_no_solid_storage_field",
                "residual_owner": "junction_stub_heat_diagnostic",
                "runtime_legality": "diagnostic/scoring evidence only; forbidden predictive wallHeatFlux runtime input",
                "source_paths": row["wallheatflux_source_path"],
            }
    return [grouped[key] for key in sorted(grouped)]


def heat_path_rows(patch_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    rows = []
    for row in patch_rows:
        if row["patch_group"] == "ambient_wall":
            path = "external_convection;wall_conduction;radiation_absence_status"
            owner = "passive_wall_external"
        elif row["patch_group"] == "heater":
            path = "heater_source_to_fluid;storage_proxy_status"
            owner = "heater_source_storage_gap"
        elif row["patch_group"] == "cooler":
            path = "jacket_cooler_removal"
            owner = "cooler_hx_removal"
        elif row["patch_group"] == "test_section":
            path = "insulation_quartz;test_section_source_loss;radiation_absence_status"
            owner = "test_section_source_loss"
        elif row["patch_group"] == "junction_other":
            path = "junction_stub_heat;external_convection;radiation_absence_status"
            owner = "junction_stub_heat"
        else:
            path = "residual"
            owner = "unresolved_thermal_residual"
        rows.append(
            {
                "case_id": row["case_id"],
                "source_id": row["source_id"],
                "span": row["span"],
                "patch_group": row["patch_group"],
                "physical_role": row["physical_role"],
                "heat_path": path,
                "wallHeatFlux_diagnostic_W": row["wallHeatFlux_integral_W"],
                "heat_to_fluid_diagnostic_W": row["heat_to_fluid_W"],
                "heater_imposed_duty_W": row["heater_imposed_duty_W"],
                "cooler_removed_duty_W": row["cooler_removed_duty_W"],
                "imposed_Q_minus_wallHeatFlux_W": row["imposed_Q_minus_wallHeatFlux_W"],
                "external_convection_status": (
                    "fields_present" if row["boundary_h_W_m2K"] else "missing_or_not_applicable"
                ),
                "wall_layer_contact_status": (
                    "resistance_terms_present"
                    if row["wall_conduction_resistance_m2K_W"] or row["total_boundary_resistance_m2K_W"]
                    else "missing_or_not_applicable"
                ),
                "radiation_qr_presence_status": row["radiation_output_term"] or "absent_no_qr_output",
                "storage_status": "absent_no_solid_storage_field",
                "residual_owner": owner,
                "fit_or_admission_status": "diagnostic_only_no_fit_no_admission",
                "runtime_legality": "diagnostic/scoring evidence only; forbidden predictive wallHeatFlux runtime input",
                "quality_flags": row["quality_flags"],
                "source_paths": row["wallheatflux_source_path"],
            }
        )
    return rows


def residual_rows(segment_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    rows = []
    for row in segment_rows:
        rows.append(
            {
                "case_id": row["case_id"],
                "source_id": row["source_id"],
                "physical_segment": row["physical_segment"],
                "bracket_status": row["bracket_status"],
                "enthalpy_change_W": row["enthalpy_change_W"],
                "segment_wallHeatFlux_diagnostic_W": row["segment_wallHeatFlux_sum_W"],
                "energy_residual_W": row["wallHeatFlux_vs_enthalpy_residual_W"],
                "residual_fraction": row["residual_fraction"],
                "residual_assignment": row["residual_assignment"],
                "max_interface_recirc_ratio": row["max_interface_recirc_ratio"],
                "runtime_legality": "diagnostic residual; forbidden predictive wallHeatFlux runtime input",
                "next_owner": (
                    "TODO-HEATLOSS-PHASE-4-UPCOMER-EXCHANGE-AND-INTERNAL-NU-GATE"
                    if row["physical_segment"] == "upcomer"
                    else "TODO-HEATLOSS-PHASE-3-WALL-TEST-SECTION-MODEL-SCORE"
                ),
                "source_paths": row["source_files"],
            }
        )
    return rows


def missing_field_rows() -> list[dict[str, str]]:
    return [
        {
            "missing_field_id": "qr_separate_radiation_output",
            "affected_lanes": "radiation;external_convection;test_section;junction_stub_heat",
            "current_status": "absent_no_qr_output",
            "what_not_to_infer": "do not infer qr from emissivity metadata or thermal residual",
            "next_action": "record qr absence in Phase 3 scoring; implement predictive radiation separately in TODO-1D-RADIATION-CAPABILITY",
            "source_paths": rel(THERMAL_MAP),
        },
        {
            "missing_field_id": "solid_storage_or_wall_energy_time_derivative",
            "affected_lanes": "heater_source_to_fluid;storage;residual",
            "current_status": "absent_no_solid_storage_field",
            "what_not_to_infer": "do not tune steady storage from heater imposed-minus-realized diagnostic gap",
            "next_action": "keep storage residual owner explicit until a transient/source audit exists",
            "source_paths": rel(PATCHWISE_LEDGER),
        },
        {
            "missing_field_id": "junction_family_direct_wallHeatFlux",
            "affected_lanes": "junction_stub_heat",
            "current_status": "estimated_from_grouped_junction_row_not_new_sampling",
            "what_not_to_infer": "do not treat patch-name fractional split as admitted junction-family target",
            "next_action": "future extraction may sample named junction/stub groups directly",
            "source_paths": rel(PATCHWISE_LEDGER),
        },
        {
            "missing_field_id": "junction_enthalpy_bracketing",
            "affected_lanes": "junction_stub_heat;residual",
            "current_status": "not_bracketed_by_available_secmean_surfaces",
            "what_not_to_infer": "do not assign grouped junction heat to a clean segment enthalpy closure",
            "next_action": "retain junction/stub heat as diagnostic residual owner",
            "source_paths": rel(SEGMENT_RESIDUALS),
        },
        {
            "missing_field_id": "contact_layer_isolation",
            "affected_lanes": "contact_layer_resistance;wall_conduction;insulation_quartz",
            "current_status": "available_as_metadata_not_independently_isolated",
            "what_not_to_infer": "do not back-calculate contact resistance from held-out residual",
            "next_action": "Phase 3 candidates may consume setup metadata only with source/property labels",
            "source_paths": rel(PHASE1_SEGMENT_AUDIT),
        },
    ]


def runtime_audit_rows() -> list[dict[str, str]]:
    return [
        {
            "audit_id": "wallHeatFlux_predictive_runtime",
            "status": "pass_forbidden",
            "policy": "forbidden predictive wallHeatFlux runtime input; diagnostic evidence only",
            "source_paths": rel(PATCHWISE_LEDGER),
        },
        {
            "audit_id": "qr_absence",
            "status": "pass_recorded_absent",
            "policy": "forbidden inference from emissivity or residual; qr is absent in cited outputs",
            "source_paths": rel(THERMAL_MAP),
        },
        {
            "audit_id": "storage_absence",
            "status": "pass_recorded_absent",
            "policy": "forbidden steady storage tuning from residual",
            "source_paths": rel(PATCHWISE_LEDGER),
        },
        {
            "audit_id": "model_scoring",
            "status": "not_performed",
            "policy": "Phase 2 improves evidence only; no fitting/model selection/admission",
            "source_paths": rel(HEAT_CONTRACT_CSV),
        },
    ]


def source_manifest_rows() -> list[dict[str, str]]:
    sources = [
        (PATCHWISE_LEDGER, "patchwise heat rows and grouped junction evidence"),
        (SEGMENT_RESIDUALS, "segment enthalpy residual ownership"),
        (RESISTANCE_TERMS, "wall/external/radiation resistance status"),
        (JUNCTION_TRENDS, "junction heat trend interpretation"),
        (HEAT_CONTRACT_CSV, "heat-path contract and guardrails"),
        (PHASE1_SEGMENT_AUDIT, "external BC/radiation setup field status"),
        (THERMAL_MAP, "radiation current state and no-double-counting policy"),
        (ROOT / ".agent/BOARD.md", "task scope and guardrails"),
    ]
    return [
        {"source_path": rel(path), "used_for": purpose, "mutation_status": "read_only"}
        for path, purpose in sources
    ]


def write_readme(summary: dict[str, Any]) -> None:
    text = f"""---
provenance:
  - {rel(PATCHWISE_LEDGER)}
  - {rel(SEGMENT_RESIDUALS)}
  - {rel(RESISTANCE_TERMS)}
  - {rel(PHASE1_SEGMENT_AUDIT)}
  - {rel(HEAT_CONTRACT_CSV)}
tags: [thermal-modeling, heat-loss, split-evidence, radiation, fluid-walls]
related:
  - .agent/status/2026-07-21_TODO-HEATLOSS-PHASE-2-SPLIT-HEAT-LOSS-EVIDENCE.md
  - .agent/journal/2026-07-21/heatloss-phase-2-split-heat-loss-evidence.md
  - work_products/2026-07/2026-07-21/2026-07-21_heatloss_phase_1_external_bc_radiation_integration/README.md
task: {TASK}
date: 2026-07-21
role: Thermal-modeling/cfd-pp/Tester/Writer
type: work_product
status: complete
supersedes: []
superseded_by:
---
# Heat-Loss Phase 2 Split Heat-Loss Evidence

## Decision

Phase 2 improves the evidence split from existing patchwise and enthalpy
ledgers. It publishes split junction/stub estimates, heat-path evidence rows,
residual ownership, and a missing-field queue. It does not launch extraction,
mutate native outputs, score a model, fit coefficients, or admit a closure.

## Result

- Split junction/stub rows: `{summary['split_junction_rows']}`.
- Heat-path evidence rows: `{summary['heat_path_rows']}`.
- Residual owner rows: `{summary['residual_owner_rows']}`.
- Missing-field rows: `{summary['missing_field_rows']}`.
- Separate `qr` output rows admitted: `0`.
- Solid storage runtime rows admitted: `0`.
- Model scoring/admission rows: `0`.

The split junction/stub rows are estimates from the existing grouped junction
row and patch-name family counts. They are not new sampled native fields and are
not admitted fit targets.

## Outputs

- `split_junction_stub_heat_rows.csv`
- `heat_path_evidence_matrix.csv`
- `energy_residual_owner_matrix.csv`
- `missing_field_queue.csv`
- `runtime_legality_audit.csv`
- `source_manifest.csv`
- `summary.json`
- `README.md`

## Guardrails

- Do not infer `qr` from emissivity metadata or residual.
- Do not tune steady storage from heater imposed-minus-realized diagnostic gaps.
- Do not use diagnostic wall heat flux as a predictive runtime input.
- Do not hide split heat residual in internal `Nu`.

## Next Action

Phase 3 wall/test-section scoring may consume this package only as an evidence
and missing-field contract. A stronger junction/stub target still needs direct
named-group extraction or accepted bracketing.
"""
    (OUT / "README.md").write_text(text, encoding="utf-8")


def build() -> dict[str, Any]:
    patch_rows = read_csv(PATCHWISE_LEDGER)
    segment_rows = read_csv(SEGMENT_RESIDUALS)
    split_rows = split_junction_rows(patch_rows)
    path_rows = heat_path_rows(patch_rows)
    owner_rows = residual_rows(segment_rows)
    missing_rows = missing_field_rows()
    runtime_rows = runtime_audit_rows()
    manifest_rows = source_manifest_rows()

    write_csv(OUT / "split_junction_stub_heat_rows.csv", split_rows)
    write_csv(OUT / "heat_path_evidence_matrix.csv", path_rows)
    write_csv(OUT / "energy_residual_owner_matrix.csv", owner_rows)
    write_csv(OUT / "missing_field_queue.csv", missing_rows)
    write_csv(OUT / "runtime_legality_audit.csv", runtime_rows)
    write_csv(OUT / "source_manifest.csv", manifest_rows)

    summary = {
        "task_id": TASK,
        "date": "2026-07-21",
        "generated_at_utc": utc_now(),
        "status": "complete",
        "split_junction_rows": len(split_rows),
        "junction_families": sorted({row["junction_family"] for row in split_rows}),
        "heat_path_rows": len(path_rows),
        "residual_owner_rows": len(owner_rows),
        "missing_field_rows": len(missing_rows),
        "qr_output_rows_admitted": 0,
        "solid_storage_runtime_rows_admitted": 0,
        "model_scoring_or_admission": False,
        "native_output_mutation": False,
        "registry_mutation": False,
        "scheduler_action": False,
        "fluid_edit": False,
        "next_phase": "TODO-HEATLOSS-PHASE-3-WALL-TEST-SECTION-MODEL-SCORE",
    }
    write_json(OUT / "summary.json", summary)
    write_readme(summary)
    return summary


def main() -> None:
    print(json.dumps(build(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
