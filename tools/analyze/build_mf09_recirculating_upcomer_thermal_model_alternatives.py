#!/usr/bin/env python3
"""Build MF09 recirculating-upcomer thermal model alternatives gate.

This is an evidence reducer only. It reads completed S13/upcomer/model-form
packages and writes a model-form gate without launching CFD, fitting
coefficients, scoring protected rows, or admitting any closure.
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TASK_ID = "TODO-MF09-RECIRCULATING-UPCOMER-THERMAL-MODEL-ALTERNATIVES-2026-07-22"
ROOT = Path(__file__).resolve().parents[2]
SLUG = "mf09_recirculating_upcomer_thermal_model_alternatives"
OUT_DIR = Path(
    "work_products/2026-07/2026-07-22/"
    "2026-07-22_mf09_recirculating_upcomer_thermal_model_alternatives"
)

SOURCES = {
    "exact_qwall": Path(
        "work_products/2026-07/2026-07-21/"
        "2026-07-21_s13_upcomer_exchange_exact_pressure_qwall_compute"
    ),
    "target_plus_harvest": Path(
        "work_products/2026-07/2026-07-22/"
        "2026-07-22_s13_upcomer_exchange_target_plus_same_qoi_harvest"
    ),
    "temporal_uq": Path(
        "work_products/2026-07/2026-07-22/"
        "2026-07-22_s13_upcomer_exchange_same_qoi_neighbor_uq_after_target_plus"
    ),
    "mesh_gci_gate": Path(
        "work_products/2026-07/2026-07-22/"
        "2026-07-22_s13_upcomer_exchange_qwall_mesh_gci_uq_gate"
    ),
    "limited_sampled": Path(
        "work_products/2026-07/2026-07-22/"
        "2026-07-22_s13_upcomer_exchange_limited_sampled_field_evidence_synthesis"
    ),
    "source_side": Path(
        "work_products/2026-07/2026-07-22/"
        "2026-07-22_s13_upcomer_exchange_source_side_conservation_neighbor_uq_gate"
    ),
    "onset_sparsity": Path(
        "work_products/2026-07/2026-07-17/"
        "2026-07-17_upcomer_onset_data_sparsity_progress"
    ),
    "heatloss_phase4": Path(
        "work_products/2026-07/2026-07-21/"
        "2026-07-21_heatloss_phase_4_upcomer_exchange_and_internal_nu_gate"
    ),
    "mf_entrance_gate": Path(
        "work_products/2026-07/2026-07-22/"
        "2026-07-22_mf_entrance_development_reset_gate"
    ),
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def read_json(path: Path) -> dict[str, Any]:
    with path.open() as f:
        return json.load(f)


def bool_text(value: bool) -> str:
    return "true" if value else "false"


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    key: bool_text(value) if isinstance(value, bool) else value
                    for key, value in ((name, row.get(name, "")) for name in fieldnames)
                }
            )


def csv_all_true(rows: list[dict[str, str]], column: str) -> bool:
    return bool(rows) and all(row.get(column, "").lower() == "true" for row in rows)


def build_heat_flow_case_diagnostics(heat_match_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in heat_match_rows:
        cp_qwall = float(row["cp_required_to_match_Q_wall_J_kg_K"])
        cp_source = float(row["cp_required_to_match_source_side_J_kg_K"])
        cp_combined = float(row["cp_required_to_match_Qwall_plus_source_side_J_kg_K"])
        rows.append(
            {
                "case_id": row["case_id"],
                "target_time_window_s": row["target_time_window_s"],
                "Q_wall_W": row["Q_wall_W"],
                "Q_source_side_net_static_bc_W": row["Q_source_side_net_static_bc_W"],
                "source_minus_qwall_W": row["source_minus_qwall_W"],
                "qwall_to_source_side_ratio": row["qwall_to_source_side_ratio"],
                "mdot_exchange_positive_outward_proxy_kg_s": row[
                    "mdot_exchange_positive_outward_proxy_kg_s"
                ],
                "wall_core_bulk_temperature_contrast_K": row["wall_core_bulk_temperature_contrast_K"],
                "abs_mdot_times_deltaT_kgK_s": row["abs_mdot_times_deltaT_kgK_s"],
                "cp_required_to_match_Q_wall_J_kg_K": row[
                    "cp_required_to_match_Q_wall_J_kg_K"
                ],
                "cp_required_to_match_source_side_J_kg_K": row[
                    "cp_required_to_match_source_side_J_kg_K"
                ],
                "cp_required_to_match_Qwall_plus_source_side_J_kg_K": row[
                    "cp_required_to_match_Qwall_plus_source_side_J_kg_K"
                ],
                "minimum_cp_required_J_kg_K": f"{min(cp_qwall, cp_source, cp_combined):.12g}",
                "heat_flow_match_status": row["heat_flow_match_status"],
                "mf09_interpretation": (
                    "available mdot*DeltaT scale is orders too small to close heat flow directly; "
                    "this is a CV/residual-definition blocker, not a coefficient-fitting target"
                ),
                "admissible_action_now": "diagnose_and_define_residual_contract_only",
            }
        )
    return rows


def build_energy_residual_contract() -> list[dict[str, str]]:
    return [
        {
            "residual_label": "E_wall_exchange_resid_W",
            "formula": "Q_wall_W - mdot_exchange_positive_outward_kg_s * cp_J_kg_K * (T_recirc_K - T_core_K)",
            "positive_terms": "Q_wall_W positive into recirculation CV; exchange enthalpy positive leaving recirc CV",
            "normal_convention": "mdot_exchange_positive_outward_kg_s > 0 from recirculation cell to main-throughflow cell",
            "basis_requirement": "same recirc cell mask, same exchange interface, same time window, same property model",
            "current_status": "blocked_missing_T_recirc_T_core_cp_and_mesh_GCI",
            "claim_boundary": "diagnostic residual only; do not absorb into internal Nu",
        },
        {
            "residual_label": "E_source_exchange_resid_W",
            "formula": (
                "Q_source_side_net_static_bc_W - mdot_exchange_positive_outward_kg_s "
                "* cp_J_kg_K * (T_recirc_K - T_core_K)"
            ),
            "positive_terms": (
                "source-side static-boundary heat retained as source-side lane; "
                "exchange enthalpy positive leaving recirc CV"
            ),
            "normal_convention": "mdot_exchange_positive_outward_kg_s > 0 from recirculation cell to main-throughflow cell",
            "basis_requirement": "released source/property validity plus same-QOI temporal and mesh/GCI support on exchange energy terms",
            "current_status": "blocked_missing_source_property_release_and_same_QOI_UQ",
            "claim_boundary": "not a wall heat-flux substitute and not coefficient-fit input",
        },
        {
            "residual_label": "E_wall_plus_source_exchange_resid_W",
            "formula": (
                "Q_wall_W + Q_source_side_net_static_bc_W - mdot_exchange_positive_outward_kg_s "
                "* cp_J_kg_K * (T_recirc_K - T_core_K)"
            ),
            "positive_terms": "both heat-flow lanes positive into the diagnostic CV; exchange enthalpy positive leaving recirc CV",
            "normal_convention": "mdot_exchange_positive_outward_kg_s > 0 from recirculation cell to main-throughflow cell",
            "basis_requirement": "explicit CV showing whether wall and source lanes belong in the same balance",
            "current_status": "diagnostic_only_until_CV_membership_and_property_basis_are_proven",
            "claim_boundary": "use only to size mismatch and plan harvest, not to fit a model",
        },
    ]


def write_closeout_docs(summary: dict[str, Any]) -> None:
    source_paths = [str(path) for path in SOURCES.values()]
    status = f"""---
provenance:
  generated_by: tools/analyze/build_mf09_recirculating_upcomer_thermal_model_alternatives.py
  task_id: {TASK_ID}
  generated_at_utc: {summary['generated_at_utc']}
task: {TASK_ID}
tags:
  - status
  - MF09
  - recirculating-upcomer
related:
  - {OUT_DIR}
---

# {TASK_ID}

## Objective

Evaluate recirculating-upcomer thermal model alternatives without forcing a
single-stream entrance/development correction or admitting ordinary upcomer
`Nu/f_D/K`.

## Outcome

Decision: `{summary['decision']}`. Variants evaluated: `{summary['variant_rows']}`.
Smoke-ready variants: `{summary['smoke_ready_variants']}`. Admission-ready
variants: `{summary['admission_allowed_variants']}`. Accepted same-label
mesh/GCI QOIs: `{summary['accepted_same_label_mesh_gci_qois']}`.

The best next science lane is
`{summary['best_next_science_lane']}`, but it remains blocked by missing
same-label mesh/GCI, missing source/property and cp basis, and no production
same-window exchange-cell harvest. Ordinary upcomer `Nu/f_D/K` remains disabled.

Heat-flow matching remains a residual-contract problem. Direct `Q_wall_W` spans
`{summary['qwall_range_W']}` W, source-side static heat spans
`{summary['source_side_range_W']}` W, and forcing the current exchange
`mdot*DeltaT` scale to match `Q_wall_W` would require `cp` spanning
`{summary['cp_required_qwall_range_J_kg_K']}` J/kg/K.

## Changes Made

- Wrote variant comparison table.
- Wrote QOI availability and UQ/source/property status table.
- Wrote ordinary-upcomer disabled-reasons table.
- Wrote production/admission gate, next work queue, source manifest,
  heat-path guardrail snapshot, onset/source gap snapshot, README, summary,
  status, journal, and import manifest.
- Wrote heat-flow match case diagnostics and energy residual bridge contract
  tables to define the mismatch and sign convention without fitting.

## Validation

- `python3.11 -m py_compile tools/analyze/build_mf09_recirculating_upcomer_thermal_model_alternatives.py tools/analyze/test_mf09_recirculating_upcomer_thermal_model_alternatives.py` passed.
- `python3.11 -m unittest tools.analyze.test_mf09_recirculating_upcomer_thermal_model_alternatives` passed.

## Guardrails

- Production harvest: false.
- Mesh/GCI execution: false.
- Scheduler/solver/sampler launch: false.
- Fluid solve: false.
- Validation/holdout/external-test scoring: false.
- Fitting/tuning/model selection: false.
- Ordinary upcomer `Nu/f_D/K` admission: false.
- Qwall/source/property release, coefficient admission, final score: false.
- Native-output mutation, registry/admission mutation, Fluid/external edit,
  blocker-register change, and generated-index refresh before closeout: false.
- Source-side heat was not relabeled as `Q_wall_W`.
- Residual was not absorbed into internal Nu.
"""
    (ROOT / f".agent/status/2026-07-22_{TASK_ID}.md").write_text(status, encoding="utf-8")

    journal = f"""---
provenance:
  generated_by: tools/analyze/build_mf09_recirculating_upcomer_thermal_model_alternatives.py
  task_id: {TASK_ID}
  generated_at_utc: {summary['generated_at_utc']}
task: {TASK_ID}
tags:
  - journal
  - MF09
  - recirculating-upcomer
related:
  - {OUT_DIR}
---

# MF09 recirculating-upcomer thermal model alternatives

## Attempted

Compared four predeclared alternatives: guarded ordinary-upcomer exclusion,
throughflow-plus-recirculation exchange cell with signed wall heat, two-zone
stratified mixed-convection upcomer, and source-side energy residual bridge.

## Observed

Temporal UQ exists for the proxy S13 exchange QOIs, but same-label mesh/GCI has
0 accepted rows. Source/property conservation is not released, ordinary internal
Nu fit rows are 0, exchange-cell fit-ready rows are 0, and onset anchor rows are
0.

## Inferred

The exchange-cell model is the highest-value physical lane, but it is not
smoke-ready. The current result should be used to define the missing QOIs and
source/property work, not to fit a coefficient or force ordinary upcomer closure.

## Contradictions or Caveats

Pressure support remains support evidence only; it is not component-K/F6
admission. Source-side heat remains source-side and must not be relabeled as
direct wall heat. Heat residuals must remain explicit instead of being absorbed
into internal Nu.

The heat-flow match check makes the same point numerically: with the current
diagnostic exchange scale, matching wall or source-side heat would require
unphysical cp-scale values. The right next step is same-mask `T_recirc`,
`T_core`, and property harvest after mesh/GCI and source/property gates pass.

## Next Useful Actions

Complete same-label mesh-family generation for Qwall/exchange-cell QOIs, then
repeat mesh/GCI/source-property gates before any exchange-cell train-only smoke
test.
"""
    (ROOT / ".agent/journal/2026-07-22/mf09-recirculating-upcomer-thermal-model-alternatives.md").write_text(
        journal, encoding="utf-8"
    )

    changed_files = [
        str(OUT_DIR / "README.md"),
        str(OUT_DIR / "summary.json"),
        str(OUT_DIR / "variant_comparison_table.csv"),
        str(OUT_DIR / "qoi_availability_and_uq_status.csv"),
        str(OUT_DIR / "ordinary_upcomer_disabled_reasons.csv"),
        str(OUT_DIR / "production_and_admission_gate.csv"),
        str(OUT_DIR / "heat_flow_match_case_diagnostics.csv"),
        str(OUT_DIR / "energy_residual_bridge_contract.csv"),
        str(OUT_DIR / "next_work_package_queue.csv"),
        str(OUT_DIR / "source_manifest.csv"),
        str(OUT_DIR / "heat_path_guardrail_snapshot.csv"),
        str(OUT_DIR / "onset_and_source_gap_snapshot.csv"),
        f".agent/status/2026-07-22_{TASK_ID}.md",
        ".agent/journal/2026-07-22/mf09-recirculating-upcomer-thermal-model-alternatives.md",
        f"imports/2026-07-22_{SLUG}.json",
        "tools/analyze/build_mf09_recirculating_upcomer_thermal_model_alternatives.py",
        "tools/analyze/test_mf09_recirculating_upcomer_thermal_model_alternatives.py",
        ".agent/BOARD.md",
    ]
    manifest = {
        "task": TASK_ID,
        "generated_at_utc": summary["generated_at_utc"],
        "changed_files": changed_files,
        "read_only_context": source_paths
        + [
            "native CFD/OpenFOAM outputs",
            "registry/admission state",
            "scheduler state",
            "Fluid source tree",
            "external repos",
            "blocker register",
            "generated docs index files",
            "thesis current/LaTeX files",
        ],
        "native_solver_outputs_mutated": False,
        "registry_mutated": False,
        "scheduler_action": "none",
        "external_fluid_edit": False,
        "mutation_flags": {
            "production_harvest": False,
            "mesh_gci_execution": False,
            "fluid_solve": False,
            "ordinary_upcomer_nu_fd_k_admission": False,
            "qwall_source_property_release": False,
            "coefficient_admission": False,
            "fitting_tuning_model_selection": False,
            "protected_scoring": False,
            "source_side_relabel_as_Q_wall": False,
            "residual_absorbed_into_internal_nu": False,
        },
    }
    (ROOT / f"imports/2026-07-22_{SLUG}.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def build() -> dict[str, Any]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    exact_summary = read_json(SOURCES["exact_qwall"] / "summary.json")
    target_plus_summary = read_json(SOURCES["target_plus_harvest"] / "summary.json")
    temporal_summary = read_json(SOURCES["temporal_uq"] / "summary.json")
    mesh_summary = read_json(SOURCES["mesh_gci_gate"] / "summary.json")
    limited_summary = read_json(SOURCES["limited_sampled"] / "summary.json")
    source_side_summary = read_json(SOURCES["source_side"] / "summary.json")
    onset_summary = read_json(SOURCES["onset_sparsity"] / "summary.json")
    phase4_summary = read_json(SOURCES["heatloss_phase4"] / "summary.json")
    entrance_summary = read_json(SOURCES["mf_entrance_gate"] / "summary.json")

    qwall_rows = read_csv(SOURCES["exact_qwall"] / "trusted_wall_Q_wall_summary.csv")
    trend_rows = read_csv(SOURCES["limited_sampled"] / "s13_exchange_trend_table.csv")
    temporal_rows = read_csv(SOURCES["temporal_uq"] / "same_qoi_temporal_uq_summary.csv")
    heat_match_rows = read_csv(SOURCES["temporal_uq"] / "heat_flow_match_diagnostics.csv")
    mesh_rows = read_csv(SOURCES["mesh_gci_gate"] / "qwall_exchange_mesh_gci_gate_matrix.csv")
    missing_mesh_rows = read_csv(SOURCES["mesh_gci_gate"] / "missing_mesh_family_blocker_table.csv")
    source_gate_rows = read_csv(SOURCES["source_side"] / "production_readiness_gate.csv")
    onset_contract_rows = read_csv(SOURCES["onset_sparsity"] / "hybrid_upcomer_model_contract.csv")
    onset_gap_rows = read_csv(SOURCES["onset_sparsity"] / "evidence_gap_queue.csv")
    phase4_gate_rows = read_csv(SOURCES["heatloss_phase4"] / "phase4_release_gate.csv")
    heat_path_rows = read_csv(SOURCES["heatloss_phase4"] / "heat_path_modeling_contract.csv")

    heat_flow_case_rows = build_heat_flow_case_diagnostics(heat_match_rows)
    energy_residual_rows = build_energy_residual_contract()
    temporal_by_qoi = {row["qoi_label"]: row for row in temporal_rows}
    mesh_by_qoi = {row["qoi_label"]: row for row in mesh_rows}
    source_gate_by_name = {row["gate"]: row for row in source_gate_rows}

    qoi_rows: list[dict[str, Any]] = []
    qoi_specs = [
        (
            "Q_wall_W",
            "direct trusted-wall wallHeatFlux integral",
            exact_summary["Q_wall_W_released_rows"],
            "Q_wall_W_released",
            "Q_wall_W",
            "not_required_for_direct_wall_integral",
        ),
        (
            "mdot_exchange_positive_outward_proxy_kg_s",
            "positive outward exchange-flow proxy",
            len(trend_rows),
            "finite_required_metrics",
            "mdot_exchange_positive_outward_proxy_kg_s",
            "not_released",
        ),
        (
            "tau_recirc_proxy_s",
            "seeded-CV residence-time proxy",
            len(trend_rows),
            "finite_required_metrics",
            "tau_recirc_proxy_s",
            "not_released",
        ),
        (
            "wall_core_bulk_temperature_contrast_K",
            "trusted wall minus interface/core temperature contrast",
            len(trend_rows),
            "finite_required_metrics",
            "wall_core_bulk_temperature_contrast_K",
            "not_released",
        ),
        (
            "Q_source_side_net_static_bc_W",
            "source-side static-BC heat-flow comparator",
            source_side_summary["source_property_conservation_rows"],
            "source_side_heat_flow_basis",
            "",
            "blocked_missing_source_property_conservation",
        ),
        (
            "pressure_basis_p_p_rgh",
            "target-window pressure/p_rgh reduction support",
            exact_summary["pressure_basis_released_rows"],
            "exact_pressure_basis",
            "",
            "partial_pressure_only_no_energy_closure",
        ),
        (
            "cp_J_kg_K",
            "property basis for exchange-cell energy closure",
            0,
            "cp_property_release",
            "",
            "missing",
        ),
    ]

    for qoi_label, description, available_rows, release_key, temporal_key, source_property_status in qoi_specs:
        temporal = temporal_by_qoi.get(temporal_key, {})
        mesh = mesh_by_qoi.get(temporal_key, {})
        source_gate = source_gate_by_name.get(release_key, {})
        qoi_rows.append(
            {
                "qoi_label": qoi_label,
                "description": description,
                "available_case_rows": available_rows,
                "direct_or_proxy_release_status": source_gate.get("status", "available_read_only")
                if source_gate
                else ("released_read_only" if available_rows else "missing"),
                "same_window_or_neighbor_temporal_uq_status": temporal.get(
                    "same_qoi_temporal_uq_status", "not_executed"
                ),
                "same_label_mesh_gci_status": mesh.get(
                    "mesh_gci_uq_status", "missing_same_label_mesh_family"
                ),
                "source_property_or_cp_status": source_property_status,
                "production_harvest_allowed_now": False,
                "admission_allowed_now": False,
                "next_evidence_needed": {
                    "Q_wall_W": "same-label coarse/medium/fine mesh-family GCI for direct Q_wall_W",
                    "mdot_exchange_positive_outward_proxy_kg_s": "production mdot_exchange basis plus same-label mesh/GCI",
                    "tau_recirc_proxy_s": "production V_recirc/mdot basis plus same-label mesh/GCI",
                    "wall_core_bulk_temperature_contrast_K": "same-window production temperature fields plus mesh/GCI",
                    "Q_source_side_net_static_bc_W": "source-property conservation release; do not relabel as Q_wall_W",
                    "pressure_basis_p_p_rgh": "same-window pressure residual equation tied to exchange-cell energy residual",
                    "cp_J_kg_K": "runtime-legal property release for the exchange-cell enthalpy balance",
                }[qoi_label],
            }
        )

    variant_rows = [
        {
            "variant_id": "MF09a_upcomer_excluded_guarded_single_stream_invalid",
            "modeling_path": "exclude recirculating upcomer from ordinary single-stream Nu/f_D/K",
            "allowed_outputs": "diagnostic omission flag; ordinary closure remains disabled",
            "forbidden_outputs": "Nu_upcomer_fit; f_D_upcomer_fit; component_K_upcomer_fit",
            "qoi_support": "onset policy plus phase4 ordinary Nu gate",
            "current_blocker": "current upcomer/test-section rows are recirculation diagnostics or incomplete same-window rows",
            "expected_tp_tw_effect": "prevents hiding upcomer heat/source/storage residuals in internal Nu; no direct TP/TW correction",
            "expected_pressure_effect": "prevents false straight-pipe/component-K attribution in recirculating sections",
            "decision": "required_guardrail",
            "smoke_ready": False,
            "admission_allowed": False,
        },
        {
            "variant_id": "MF09b_throughflow_plus_recirculation_exchange_cell_with_signed_wall_heat",
            "modeling_path": "throughflow pipe plus recirculating exchange cell with signed direct wall heat as a separate lane",
            "allowed_outputs": "diagnostic exchange-cell balance; future train-only smoke only after source/UQ gates",
            "forbidden_outputs": "source-side heat relabeled as Q_wall_W; exchange residual folded into Nu",
            "qoi_support": "Q_wall_W, mdot proxy, tau proxy, wall/core contrast temporal UQ are available",
            "current_blocker": "same-label mesh/GCI missing for 4/4 QOIs; cp/source-property and production harvest not released",
            "expected_tp_tw_effect": "physically targets TP/TW offsets through residence time, wall/core contrast, and signed wall/source energy lanes",
            "expected_pressure_effect": "can carry recirculation pressure residual separately from ordinary K after same-window residual support",
            "decision": "best_next_science_lane_but_blocked",
            "smoke_ready": False,
            "admission_allowed": False,
        },
        {
            "variant_id": "MF09c_two-zone_stratified_mixed-convection_upcomer",
            "modeling_path": "two-zone core/recirculation or stratified mixed-convection upcomer state",
            "allowed_outputs": "paper design and diagnostic state variables",
            "forbidden_outputs": "new tuned stratification coefficient from current rows",
            "qoi_support": "wall/core/bulk contrast and recirculation proxies indicate structure",
            "current_blocker": "no non-recirculating or transition anchor and no production same-window zone enthalpy fields",
            "expected_tp_tw_effect": "could separate core-throughflow temperature from wall-adjacent recirculation temperature",
            "expected_pressure_effect": "would require coupled recirculation metric, not straight-pipe friction",
            "decision": "diagnostic_design_only",
            "smoke_ready": False,
            "admission_allowed": False,
        },
        {
            "variant_id": "MF09d_source-side_energy_residual_bridge",
            "modeling_path": "source-side energy residual bridge between setup heat paths and direct wall heat",
            "allowed_outputs": "diagnostic residual ledger and source/property preflight",
            "forbidden_outputs": "Q_source_side_net_static_bc_W treated as Q_wall_W; residual hidden in internal Nu",
            "qoi_support": "finite source-side comparator exists but direct Qwall/source-side mismatch is nonphysical at current exchange scale",
            "current_blocker": "source-property conservation release is 0 rows and cp-required-to-match is unphysical",
            "expected_tp_tw_effect": "keeps missing heat owner explicit instead of tuning internal Nu",
            "expected_pressure_effect": "no pressure closure until energy residual and pressure residual share the same window/control volume",
            "decision": "diagnostic_residual_bridge_only",
            "smoke_ready": False,
            "admission_allowed": False,
        },
    ]

    disabled_reasons = [
        {
            "reason_id": "recirculation_invalid_single_stream",
            "evidence": "current rows belong to recirculating_upcomer_effective lane or incomplete anchor rows",
            "source_path": str(SOURCES["onset_sparsity"] / "hybrid_upcomer_model_contract.csv"),
            "ordinary_nu_f_d_k_allowed": False,
        },
        {
            "reason_id": "ordinary_internal_nu_gate_zero_rows",
            "evidence": f"phase4 ordinary_internal_nu_fit_rows={phase4_summary['ordinary_internal_nu_fit_rows']}",
            "source_path": str(SOURCES["heatloss_phase4"] / "summary.json"),
            "ordinary_nu_f_d_k_allowed": False,
        },
        {
            "reason_id": "same_label_mesh_gci_missing",
            "evidence": f"accepted_same_label_mesh_gci_qois={mesh_summary['accepted_same_label_mesh_gci_qois']}/4",
            "source_path": str(SOURCES["mesh_gci_gate"] / "summary.json"),
            "ordinary_nu_f_d_k_allowed": False,
        },
        {
            "reason_id": "source_property_cp_energy_closure_missing",
            "evidence": "source-side and cp/property lanes are not conservation released",
            "source_path": str(SOURCES["source_side"] / "production_readiness_gate.csv"),
            "ordinary_nu_f_d_k_allowed": False,
        },
        {
            "reason_id": "residual_absorption_forbidden",
            "evidence": "heat-path contract requires residual to remain separately named",
            "source_path": str(SOURCES["heatloss_phase4"] / "heat_path_modeling_contract.csv"),
            "ordinary_nu_f_d_k_allowed": False,
        },
    ]

    match_status_counts = Counter(row["heat_flow_match_status"] for row in heat_match_rows)
    qwall_values = [float(row["Q_wall_W"]) for row in heat_flow_case_rows]
    source_values = [float(row["Q_source_side_net_static_bc_W"]) for row in heat_flow_case_rows]
    cp_qwall_values = [float(row["cp_required_to_match_Q_wall_J_kg_K"]) for row in heat_flow_case_rows]
    production_gate_rows = [
        {
            "gate": "ordinary_upcomer_Nu_fD_K",
            "status": "disabled",
            "pass": False,
            "reason": "single-stream ordinary closure remains invalid for recirculating/incomplete upcomer evidence",
        },
        {
            "gate": "exchange_cell_smoke",
            "status": "blocked_missing_mesh_gci_source_basis",
            "pass": False,
            "reason": "throughflow-plus-recirculation is preferred but lacks same-label mesh/GCI, cp/source-property, and production energy closure",
        },
        {
            "gate": "source_side_bridge",
            "status": "diagnostic_only",
            "pass": False,
            "reason": "source-side heat is finite but not source/property released and must not be relabeled as Q_wall_W",
        },
        {
            "gate": "production_harvest",
            "status": "blocked",
            "pass": False,
            "reason": "limited sampled-field package has 0 production-ready rows and mesh/GCI gate has 0 accepted same-label rows",
        },
        {
            "gate": "s11_s12_s13_s15_s6_trigger",
            "status": "not_triggered",
            "pass": False,
            "reason": "no exchange-cell candidate is smoke-ready or admitted",
        },
    ]

    next_rows = [
        {
            "priority": 1,
            "work_package": "finish exact same-label mesh-family inventory/generation contract",
            "why": "mesh/GCI gate found 0/4 accepted same-label rows",
            "input_paths": str(SOURCES["mesh_gci_gate"] / "missing_mesh_family_blocker_table.csv"),
            "success_signal": "coarse/medium/fine same-label Q_wall_W, mdot_exchange, tau, and wall/core contrast rows exist or generation row is launched",
        },
        {
            "priority": 2,
            "work_package": "source-property and cp basis release preflight for exchange-cell energy balance",
            "why": "Q_source_side and direct Qwall are different lanes and current cp-required-to-match values are unphysical",
            "input_paths": str(SOURCES["temporal_uq"] / "heat_flow_match_diagnostics.csv"),
            "success_signal": "runtime-legal cp_J_kg_K/source property lane and conservation equation are released without validation tuning",
        },
        {
            "priority": 3,
            "work_package": "production same-window exchange-cell harvest after gates pass",
            "why": "diagnostic proxies exist but production harvest remains blocked",
            "input_paths": str(SOURCES["limited_sampled"] / "s13_exchange_trend_table.csv"),
            "success_signal": "V_recirc, mdot_exchange, tau_recirc, wall/core enthalpy, pressure residual, and energy residual share one mask/window",
        },
        {
            "priority": 4,
            "work_package": "near-onset/non-recirculating anchor design or harvest",
            "why": "onset sparsity package found 0 anchor candidates",
            "input_paths": str(SOURCES["onset_sparsity"] / "evidence_gap_queue.csv"),
            "success_signal": "at least one non-recirculating or transition anchor with same-window thermal/pressure/UQ fields",
        },
    ]

    manifest_rows = [
        {
            "source_id": source_id,
            "source_path": str(path),
            "used_files": {
                "exact_qwall": "summary.json;trusted_wall_Q_wall_summary.csv;downstream_gate.csv",
                "target_plus_harvest": "summary.json",
                "temporal_uq": "summary.json;same_qoi_temporal_uq_summary.csv;heat_flow_match_diagnostics.csv",
                "mesh_gci_gate": "summary.json;qwall_exchange_mesh_gci_gate_matrix.csv;missing_mesh_family_blocker_table.csv",
                "limited_sampled": "summary.json;s13_exchange_trend_table.csv",
                "source_side": "summary.json;production_readiness_gate.csv",
                "onset_sparsity": "summary.json;hybrid_upcomer_model_contract.csv;evidence_gap_queue.csv",
                "heatloss_phase4": "summary.json;phase4_release_gate.csv;heat_path_modeling_contract.csv",
                "mf_entrance_gate": "summary.json;successor_implementation_queue.csv",
            }[source_id],
            "mutation_status": "read_only",
        }
        for source_id, path in SOURCES.items()
    ]

    summary = {
        "task_id": TASK_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "decision": "blocked_missing_mesh_gci_source_basis",
        "variant_rows": len(variant_rows),
        "required_guardrail_variants": 1,
        "best_next_science_lane": "MF09b_throughflow_plus_recirculation_exchange_cell_with_signed_wall_heat",
        "smoke_ready_variants": sum(1 for row in variant_rows if row["smoke_ready"]),
        "admission_allowed_variants": sum(1 for row in variant_rows if row["admission_allowed"]),
        "qoi_rows": len(qoi_rows),
        "heat_flow_case_rows": len(heat_flow_case_rows),
        "energy_residual_contract_rows": len(energy_residual_rows),
        "direct_qwall_released_rows": exact_summary["Q_wall_W_released_rows"],
        "same_qoi_temporal_uq_complete_qois": temporal_summary["same_qoi_temporal_uq_executed_qois"],
        "accepted_same_label_mesh_gci_qois": mesh_summary["accepted_same_label_mesh_gci_qois"],
        "missing_mesh_family_blocker_rows": len(missing_mesh_rows),
        "source_property_conservation_release_ready_rows": source_side_summary["conservation_release_ready_rows"],
        "limited_sampled_production_ready_rows": limited_summary["production_ready_gate_rows"],
        "ordinary_internal_nu_fit_rows": phase4_summary["ordinary_internal_nu_fit_rows"],
        "exchange_cell_fit_ready_rows": phase4_summary["exchange_cell_fit_ready_rows"],
        "onset_anchor_candidate_rows": onset_summary["decision"]["anchor_candidate_rows"],
        "onset_ordinary_fit_rows": onset_summary["decision"]["ordinary_fit_rows"],
        "heat_flow_not_physical_match_rows": match_status_counts.get(
            "not_physical_match_with_current_exchange_scale", 0
        ),
        "production_harvest_allowed": False,
        "ordinary_upcomer_nu_fd_k_allowed": False,
        "Qwall_or_source_property_release": False,
        "source_side_relabel_as_Q_wall": False,
        "coefficient_admission": False,
        "s11_s12_s13_s15_s6_trigger": False,
        "native_output_mutation": False,
        "registry_or_admission_mutation": False,
        "scheduler_action": False,
        "solver_sampler_harvest_uq_launched": False,
        "Fluid_or_external_repo_mutation": False,
        "validation_holdout_external_rows_scored": 0,
        "fitting_or_model_selection": False,
        "blocker_register_change": False,
        "generated_index_refresh": False,
        "residual_absorbed_into_internal_nu": False,
        "upstream_entrance_gate_decision": entrance_summary["decision"],
        "target_plus_harvest_decision": target_plus_summary["decision"],
        "qwall_range_W": f"{min(qwall_values):.12g} to {max(qwall_values):.12g}",
        "source_side_range_W": f"{min(source_values):.12g} to {max(source_values):.12g}",
        "cp_required_qwall_range_J_kg_K": f"{min(cp_qwall_values):.12g} to {max(cp_qwall_values):.12g}",
    }

    write_csv(
        OUT_DIR / "variant_comparison_table.csv",
        variant_rows,
        [
            "variant_id",
            "modeling_path",
            "allowed_outputs",
            "forbidden_outputs",
            "qoi_support",
            "current_blocker",
            "expected_tp_tw_effect",
            "expected_pressure_effect",
            "decision",
            "smoke_ready",
            "admission_allowed",
        ],
    )
    write_csv(
        OUT_DIR / "qoi_availability_and_uq_status.csv",
        qoi_rows,
        [
            "qoi_label",
            "description",
            "available_case_rows",
            "direct_or_proxy_release_status",
            "same_window_or_neighbor_temporal_uq_status",
            "same_label_mesh_gci_status",
            "source_property_or_cp_status",
            "production_harvest_allowed_now",
            "admission_allowed_now",
            "next_evidence_needed",
        ],
    )
    write_csv(
        OUT_DIR / "ordinary_upcomer_disabled_reasons.csv",
        disabled_reasons,
        ["reason_id", "evidence", "source_path", "ordinary_nu_f_d_k_allowed"],
    )
    write_csv(
        OUT_DIR / "production_and_admission_gate.csv",
        production_gate_rows,
        ["gate", "status", "pass", "reason"],
    )
    write_csv(
        OUT_DIR / "heat_flow_match_case_diagnostics.csv",
        heat_flow_case_rows,
        [
            "case_id",
            "target_time_window_s",
            "Q_wall_W",
            "Q_source_side_net_static_bc_W",
            "source_minus_qwall_W",
            "qwall_to_source_side_ratio",
            "mdot_exchange_positive_outward_proxy_kg_s",
            "wall_core_bulk_temperature_contrast_K",
            "abs_mdot_times_deltaT_kgK_s",
            "cp_required_to_match_Q_wall_J_kg_K",
            "cp_required_to_match_source_side_J_kg_K",
            "cp_required_to_match_Qwall_plus_source_side_J_kg_K",
            "minimum_cp_required_J_kg_K",
            "heat_flow_match_status",
            "mf09_interpretation",
            "admissible_action_now",
        ],
    )
    write_csv(
        OUT_DIR / "energy_residual_bridge_contract.csv",
        energy_residual_rows,
        [
            "residual_label",
            "formula",
            "positive_terms",
            "normal_convention",
            "basis_requirement",
            "current_status",
            "claim_boundary",
        ],
    )
    write_csv(
        OUT_DIR / "next_work_package_queue.csv",
        next_rows,
        ["priority", "work_package", "why", "input_paths", "success_signal"],
    )
    write_csv(
        OUT_DIR / "source_manifest.csv",
        manifest_rows,
        ["source_id", "source_path", "used_files", "mutation_status"],
    )
    write_csv(
        OUT_DIR / "heat_path_guardrail_snapshot.csv",
        heat_path_rows,
        ["heat_path", "allowed_use", "current_gate", "forbidden_runtime_inputs", "residual_policy", "next_action"],
    )
    write_csv(
        OUT_DIR / "onset_and_source_gap_snapshot.csv",
        onset_gap_rows + phase4_gate_rows,
        sorted(set().union(*(row.keys() for row in onset_gap_rows + phase4_gate_rows))),
    )

    (OUT_DIR / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    (OUT_DIR / "README.md").write_text(
        """---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_qwall_mesh_gci_uq_gate/summary.json
  - work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_same_qoi_neighbor_uq_after_target_plus/same_qoi_temporal_uq_summary.csv
  - work_products/2026-07/2026-07-17/2026-07-17_upcomer_onset_data_sparsity_progress/summary.json
tags: [mf09, upcomer, recirculation, model-form, diagnostic-only]
related:
  - operational_notes/maps/thermal-closures-and-internal-nu.md
  - operational_notes/maps/forward-predictive-model.md
---
# MF09 Recirculating-Upcomer Thermal Model Alternatives

MF09 compares the current upcomer alternatives without forcing the recirculating
upcomer into an ordinary single-stream pipe closure. It uses completed evidence
only and does not run CFD, harvest production samples, fit coefficients, release
source properties, or admit a candidate.

Decision: `blocked_missing_mesh_gci_source_basis`.

The best next science lane is
`MF09b_throughflow_plus_recirculation_exchange_cell_with_signed_wall_heat`, but
it is not smoke-ready: same-label mesh/GCI is missing for 4/4 S13 exchange QOIs,
source/property and `cp_J_kg_K` are not released, and production same-window
energy/pressure residual support is still blocked. Ordinary upcomer `Nu`,
`f_D`, and component `K` remain disabled.

Outputs:

- `variant_comparison_table.csv`
- `qoi_availability_and_uq_status.csv`
- `ordinary_upcomer_disabled_reasons.csv`
- `production_and_admission_gate.csv`
- `heat_flow_match_case_diagnostics.csv`
- `energy_residual_bridge_contract.csv`
- `next_work_package_queue.csv`
- `heat_path_guardrail_snapshot.csv`
- `onset_and_source_gap_snapshot.csv`
- `source_manifest.csv`
- `summary.json`

Guardrails:

- Do not relabel source-side static heat as direct `Q_wall_W`.
- Do not hide any heat/energy residual in internal Nu.
- Do not trigger S11/S12/S13/S15/S6 from this diagnostic gate.
"""
    )

    write_closeout_docs(summary)
    return summary


def main() -> int:
    print(json.dumps(build(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
