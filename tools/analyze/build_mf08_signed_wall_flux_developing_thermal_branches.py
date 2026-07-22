#!/usr/bin/env python3.11
"""Build the MF08 signed wall-flux developing thermal branch gate."""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


TASK_ID = "TODO-MF08-SIGNED-WALL-FLUX-DEVELOPING-THERMAL-BRANCHES-2026-07-22"
SLUG = "mf08_signed_wall_flux_developing_thermal_branches"
ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_mf08_signed_wall_flux_developing_thermal_branches"

SOURCE_PROVENANCE = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_extbc_source_sink_provenance_recovery/setup_source_sink_provenance_ledger.csv"
SOURCE_CONTRACT = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_fluid_setup_known_source_sink_runtime_contract/setup_known_source_contract.csv"
SOURCE_PROPERTY_GATE = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_fluid_setup_known_source_sink_runtime_contract/source_property_gate.csv"
M2_RUNTIME = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_m2_passive_wall_test_section_source_bounded_repair_gate/runtime_legality_matrix.csv"
M2_SUMMARY = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_m2_passive_wall_test_section_source_bounded_repair_gate/summary.json"
D2_SUMMARY = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_mf_d2_tp_tw_qoi_projection_gate/summary.json"
D3_SUMMARY = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_mf_d3_wall_shape_axial_mixing_gate/summary.json"
D4_SUMMARY = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_mf_d4_segment_source_placement_evidence_gate/summary.json"


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str] | None = None) -> None:
    if fieldnames is None:
        fieldnames = []
        for row in rows:
            for key in row:
                if key not in fieldnames:
                    fieldnames.append(key)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def bool_from_text(value: str) -> bool:
    return value.strip().lower() == "true"


def source_stats() -> dict[tuple[str, str], dict[str, object]]:
    stats: dict[tuple[str, str], dict[str, object]] = defaultdict(
        lambda: {
            "count": 0,
            "min_W": None,
            "max_W": None,
            "train_min_W": None,
            "train_max_W": None,
            "cases": [],
            "splits": [],
            "source_paths": [],
            "runtime_allowed_now_all": True,
        }
    )
    for row in read_csv(SOURCE_PROVENANCE):
        key = (row["source_segment_id"], row["physical_role"])
        value = float(row["setup_value_W"])
        item = stats[key]
        item["count"] = int(item["count"]) + 1
        item["min_W"] = value if item["min_W"] is None else min(float(item["min_W"]), value)
        item["max_W"] = value if item["max_W"] is None else max(float(item["max_W"]), value)
        if row["split_role"] == "train":
            item["train_min_W"] = value if item["train_min_W"] is None else min(float(item["train_min_W"]), value)
            item["train_max_W"] = value if item["train_max_W"] is None else max(float(item["train_max_W"]), value)
        item["cases"].append(row["case_id"])
        item["splits"].append(row["split_role"])
        item["source_paths"].append(row["source_path"])
        item["runtime_allowed_now_all"] = bool(item["runtime_allowed_now_all"]) and bool_from_text(row["runtime_allowed_now"])
    return stats


def build_runtime_legal_source_table(stats: dict[tuple[str, str], dict[str, object]]) -> list[dict[str, object]]:
    source_property_released = all(bool_from_text(row["source_property_released_now"]) for row in read_csv(SOURCE_CONTRACT))
    source_gate = read_csv(SOURCE_PROPERTY_GATE)
    gate_summary = "; ".join(f"{row['gate']}={row['status']}" for row in source_gate)
    rows: list[dict[str, object]] = []
    for (segment, role), item in sorted(stats.items()):
        sign = "positive_fluid_heating" if float(item["max_W"]) > 0 else "negative_fluid_cooling"
        rows.append(
            {
                "source_segment_id": segment,
                "physical_role": role,
                "setup_q_sign_convention": sign,
                "setup_q_min_W": item["min_W"],
                "setup_q_max_W": item["max_W"],
                "train_setup_q_min_W": item["train_min_W"],
                "train_setup_q_max_W": item["train_max_W"],
                "setup_provenance_status": "setup_known_candidate",
                "runtime_source_status": "contract_only_not_released",
                "runtime_allowed_now": False,
                "source_property_released_now": source_property_released,
                "realized_wallHeatFlux_runtime_input_allowed": False,
                "gate_context": gate_summary,
                "reason": "Setup-side Q sign/magnitude can define candidate form direction, but source/property release is blocked and CFD wallHeatFlux is not a legal runtime input.",
            }
        )
    rows.append(
        {
            "source_segment_id": "downcomer_or_passive_wall",
            "physical_role": "passive_loss",
            "setup_q_sign_convention": "negative_fluid_cooling_expected_not_source_released",
            "setup_q_min_W": "",
            "setup_q_max_W": "",
            "train_setup_q_min_W": "",
            "train_setup_q_max_W": "",
            "setup_provenance_status": "source_basis_needed",
            "runtime_source_status": "needed_future_input",
            "runtime_allowed_now": False,
            "source_property_released_now": False,
            "realized_wallHeatFlux_runtime_input_allowed": False,
            "gate_context": "M2 passive source-bounded repair gate found no reviewable candidate.",
            "reason": "Passive wall/downcomer branch needs independent area/material/ambient/insulation/literature basis before any train smoke test.",
        }
    )
    return rows


def build_source_envelope(stats: dict[tuple[str, str], dict[str, object]]) -> list[dict[str, object]]:
    d2 = read_json(D2_SUMMARY)
    d3 = read_json(D3_SUMMARY)
    d4 = read_json(D4_SUMMARY)
    m2 = read_json(M2_SUMMARY)
    rows: list[dict[str, object]] = []
    for (segment, role), item in sorted(stats.items()):
        rows.append(
            {
                "evidence_id": f"setup_{segment}_{role}",
                "evidence_type": "setup_known_Q",
                "segment_or_branch": segment,
                "physical_role": role,
                "value_envelope_W": f"{item['min_W']} to {item['max_W']}",
                "cases": ";".join(item["cases"]),
                "splits": ";".join(item["splits"]),
                "provenance": rel(SOURCE_PROVENANCE),
                "release_status": "setup_known_not_runtime_released",
                "claim_use": "candidate direction and sign only",
            }
        )
    rows.extend(
        [
            {
                "evidence_id": "D2_tp_tw_projection",
                "evidence_type": "diagnostic_projection",
                "segment_or_branch": "thermal_development_path",
                "physical_role": "bulk_to_TP_TW",
                "value_envelope_W": "",
                "cases": "",
                "splits": "diagnostic",
                "provenance": rel(D2_SUMMARY),
                "release_status": "diagnostic_only",
                "claim_use": f"D2 decision {d2['decision']}; TP RMSE {d2['d2_transfer_tp_rmse_K']} K and TW RMSE {d2['d2_transfer_tw_rmse_K']} K, but no correction release.",
            },
            {
                "evidence_id": "D3_wall_shape_axial_mixing",
                "evidence_type": "diagnostic_projection",
                "segment_or_branch": "wall_shape_axial_mixing",
                "physical_role": "TP_to_TW_shape",
                "value_envelope_W": "",
                "cases": "",
                "splits": "diagnostic",
                "provenance": rel(D3_SUMMARY),
                "release_status": "diagnostic_only",
                "claim_use": f"D3 decision {d3['decision']}; candidate-ready rows {d3['candidate_ready_rows']}.",
            },
            {
                "evidence_id": "D4_segment_source_placement",
                "evidence_type": "diagnostic_projection",
                "segment_or_branch": "source_placement",
                "physical_role": "segment_heat_placement",
                "value_envelope_W": "",
                "cases": "",
                "splits": "diagnostic",
                "provenance": rel(D4_SUMMARY),
                "release_status": "diagnostic_only",
                "claim_use": f"D4 decision {d4['decision']}; source-bounded ready rows {d4['source_bounded_candidate_ready_rows']}.",
            },
            {
                "evidence_id": "M2_passive_wall_test_section",
                "evidence_type": "source_basis_gate",
                "segment_or_branch": "passive_wall_test_section",
                "physical_role": "passive_loss",
                "value_envelope_W": "",
                "cases": "",
                "splits": "train_diagnostic",
                "provenance": rel(M2_SUMMARY),
                "release_status": "needs_source_basis",
                "claim_use": f"M2 decision {m2['decision']}; S11-reviewable candidates {m2['s11_reviewable_candidates']}.",
            },
        ]
    )
    return rows


def build_sign_magnitude_envelope(stats: dict[tuple[str, str], dict[str, object]]) -> list[dict[str, object]]:
    def item(segment: str, role: str) -> dict[str, object]:
        return stats[(segment, role)]

    heater = item("lower_leg", "heater")
    cooler = item("cooling_branch", "cooler")
    test_section = item("upcomer", "test_section")
    return [
        {
            "branch_id": "cooling_branch",
            "physical_role": "cooler_or_HX",
            "fluid_energy_sign": "negative",
            "interpretation": "negative wall/source flux cools the fluid",
            "setup_magnitude_envelope_W": f"{abs(float(cooler['max_W']))} to {abs(float(cooler['min_W']))}",
            "train_setup_magnitude_envelope_W": f"{abs(float(cooler['train_max_W']))} to {abs(float(cooler['train_min_W']))}",
            "runtime_status": "setup_known_not_released",
        },
        {
            "branch_id": "downcomer_or_passive_wall",
            "physical_role": "passive_loss",
            "fluid_energy_sign": "negative_expected",
            "interpretation": "passive wall loss should cool the fluid but independent source basis is missing",
            "setup_magnitude_envelope_W": "missing",
            "train_setup_magnitude_envelope_W": "missing",
            "runtime_status": "needs_source_basis",
        },
        {
            "branch_id": "lower_leg",
            "physical_role": "heater",
            "fluid_energy_sign": "positive",
            "interpretation": "positive source flux heats the fluid",
            "setup_magnitude_envelope_W": f"{heater['min_W']} to {heater['max_W']}",
            "train_setup_magnitude_envelope_W": f"{heater['train_min_W']} to {heater['train_max_W']}",
            "runtime_status": "setup_known_contract_only",
        },
        {
            "branch_id": "upcomer",
            "physical_role": "test_section",
            "fluid_energy_sign": "positive",
            "interpretation": "positive source flux heats the fluid in the test-section/upcomer segment",
            "setup_magnitude_envelope_W": f"{test_section['min_W']} to {test_section['max_W']}",
            "train_setup_magnitude_envelope_W": f"{test_section['train_min_W']} to {test_section['train_max_W']}",
            "runtime_status": "setup_known_not_released_and_upcomer_recirculation_guarded",
        },
    ]


def build_reset_graetz_basis() -> list[dict[str, object]]:
    return [
        {
            "basis_id": "hydraulic_reset_after_bends_or_components",
            "required_inputs": "segment length, hydraulic diameter, Re, local disturbance/reset markers",
            "current_status": "pending_MF07_or_source_basis",
            "use_in_MF08": "needed to separate straight/developing branch correction from wall-flux sign effect",
            "admissibility": "not_ready",
        },
        {
            "basis_id": "thermal_Graetz_coordinate",
            "required_inputs": "Re, Pr, hydraulic diameter, thermal entrance origin, source sign by branch",
            "current_status": "pending_MF07_or_source_basis",
            "use_in_MF08": "needed to evaluate whether a signed heat-transfer term is physically developing or merely a residual fit",
            "admissibility": "not_ready",
        },
        {
            "basis_id": "piecewise_memory_reset",
            "required_inputs": "component boundaries, branch sign, recirculation validity, reset length scale",
            "current_status": "pending_MF07_and_MF09",
            "use_in_MF08": "needed for the piecewise signed wall-flux reset-memory variant",
            "admissibility": "not_ready",
        },
    ]


def build_assumptions_caveats() -> list[dict[str, object]]:
    return [
        {
            "item_id": "sign_convention",
            "statement": "Positive setup Q or source flux heats the fluid; negative setup Q or source flux cools the fluid.",
            "impact": "prevents mislabeling cooler/passive loss as an internal Nu correction with the wrong sign",
        },
        {
            "item_id": "setup_Q_not_runtime_release",
            "statement": "Setup-known Q values are evidence for sign and magnitude envelopes only; runtime source/property release remains blocked.",
            "impact": "no train smoke, validation, holdout, or admission can be claimed from this gate",
        },
        {
            "item_id": "wallHeatFlux_forbidden",
            "statement": "Realized CFD wallHeatFlux is a diagnostic output and remains forbidden as a runtime input.",
            "impact": "prevents leakage from target fields into a predictive 1D model",
        },
        {
            "item_id": "D2_D3_D4_are_diagnostic",
            "statement": "D2/D3/D4 support missing thermal-development/source-placement structure but do not release a correction.",
            "impact": "direction-of-effect can be documented, but no F6/F3/scored closure follows here",
        },
        {
            "item_id": "upcomer_guard",
            "statement": "Upcomer/test-section heat must be handled with recirculation and source-side guards.",
            "impact": "ordinary single-stream upcomer Nu/f_D/K remains disabled until MF09-type evidence passes",
        },
    ]


def build_expected_effects() -> list[dict[str, object]]:
    return [
        {
            "variant_id": "MF08a_cooler_negative_wall_flux_strong_development",
            "branch_or_segment": "cooling_branch",
            "wall_flux_sign": "negative",
            "expected_TP_effect": "lower downstream TP/bulk if the cooler sink is underrepresented or shifted",
            "expected_TW_effect": "lower nearby wall temperatures and alter TP-to-TW shape",
            "expected_pressure_effect": "no pressure-K claim; pressure coupling only diagnostic through density/buoyancy if later sourced",
            "decision": "needs_source_basis",
            "reason": "Cooler sink sign is setup-known, but source/property release and reset/Graetz basis are not ready.",
        },
        {
            "variant_id": "MF08b_downcomer_negative_wall_flux_weak_passive_cooling",
            "branch_or_segment": "downcomer_or_passive_wall",
            "wall_flux_sign": "negative_expected",
            "expected_TP_effect": "slightly lower bulk temperatures before heater/upcomer if passive cooling is independently sourced",
            "expected_TW_effect": "could reduce cold-bias residual locally only if wall/ambient/source basis is released",
            "expected_pressure_effect": "no pressure-K claim; ordinary pressure loss unaffected in this gate",
            "decision": "needs_source_basis",
            "reason": "Passive/downcomer source basis is not released and M2 found no reviewable repair candidate.",
        },
        {
            "variant_id": "MF08c_heater_positive_wall_flux_development",
            "branch_or_segment": "lower_leg",
            "wall_flux_sign": "positive",
            "expected_TP_effect": "raise downstream TP/bulk if lower-leg heater source placement or development is underrepresented",
            "expected_TW_effect": "raise heated wall-side sensors with branch-dependent developing profile",
            "expected_pressure_effect": "no component-K claim; coupling only via future buoyancy/density model form",
            "decision": "needs_source_basis",
            "reason": "Lower-leg heater Q is setup-known and Fluid contract-only, but train-only residual tests did not release source/property admission.",
        },
        {
            "variant_id": "MF08d_piecewise_signed_wall_flux_reset_memory",
            "branch_or_segment": "loop_piecewise",
            "wall_flux_sign": "mixed_signed",
            "expected_TP_effect": "cooler/passive branches lower TP while heater/test-section branches raise TP with memory/reset transitions",
            "expected_TW_effect": "could separate bulk-to-TP, TP-to-TW, wall-shape, and source-placement residual owners",
            "expected_pressure_effect": "diagnostic only; pressure path remains separate and cannot be relabeled as K evidence",
            "decision": "needs_source_basis",
            "reason": "Requires released signed source envelopes plus MF07 reset/Graetz and MF09 upcomer guards.",
        },
    ]


def build_candidate_gate(expected_effects: list[dict[str, object]]) -> list[dict[str, object]]:
    rows = []
    for row in expected_effects:
        rows.append(
            {
                "variant_id": row["variant_id"],
                "gate_decision": row["decision"],
                "ready_for_train_only_smoke": False,
                "source_basis_ready": False,
                "reset_graetz_ready": False,
                "wallHeatFlux_fit_forbidden": True,
                "ordinary_upcomer_or_pressure_K_claim": False,
                "reason": row["reason"],
            }
        )
    rows.append(
        {
            "variant_id": "forbidden_realized_wallHeatFlux_fit",
            "gate_decision": "forbidden_as_wallHeatFlux_fit",
            "ready_for_train_only_smoke": False,
            "source_basis_ready": False,
            "reset_graetz_ready": False,
            "wallHeatFlux_fit_forbidden": True,
            "ordinary_upcomer_or_pressure_K_claim": False,
            "reason": "Realized CFD wallHeatFlux is an output/diagnostic field and cannot be used as a predictive runtime input.",
        }
    )
    return rows


def build_guardrails() -> list[dict[str, object]]:
    return [
        {"guardrail": "fluid_solve", "performed": False},
        {"guardrail": "scheduler_action", "performed": False},
        {"guardrail": "solver_postprocessing_sampler_harvest_uq_launch", "performed": False},
        {"guardrail": "native_output_mutation", "performed": False},
        {"guardrail": "registry_or_admission_mutation", "performed": False},
        {"guardrail": "fluid_or_external_edit", "performed": False},
        {"guardrail": "validation_holdout_external_scoring", "performed": False},
        {"guardrail": "fitting_tuning_model_selection", "performed": False},
        {"guardrail": "source_property_release", "performed": False},
        {"guardrail": "coefficient_admission", "performed": False},
        {"guardrail": "final_score_claim", "performed": False},
        {"guardrail": "realized_wallHeatFlux_runtime_input", "performed": False},
        {"guardrail": "residual_internal_nu_absorption", "performed": False},
    ]


def write_docs(summary: dict[str, object], validation_status: str = "pending") -> None:
    generated_at = str(summary["generated_at_utc"])
    readme = f"""---
provenance:
  generated_by: tools/analyze/build_mf08_signed_wall_flux_developing_thermal_branches.py
  task_id: {TASK_ID}
  generated_at_utc: {generated_at}
task: {TASK_ID}
tags:
  - MF08
  - signed-wall-flux
  - thermal-development
related:
  - {rel(SOURCE_PROVENANCE)}
  - {rel(D2_SUMMARY)}
  - {rel(M2_SUMMARY)}
---

# MF08 Signed Wall-Flux Developing Thermal Branches

## Decision

Decision: `{summary['decision']}`.

The useful finding is sign-aware but still fail-closed. Setup-known branch heat
exchange gives the right physical signs: cooler/HX and passive-loss branches
cool the fluid, while heater and test-section branches heat the fluid. That is
enough to define candidate model forms and direction-of-effect, but not enough
to run or admit them.

All four required variants are labeled `needs_source_basis`. The package also
records the forbidden shortcut `forbidden_realized_wallHeatFlux_fit`.

## Scientific Use

Use this result to write that signed wall/source heat exchange is a plausible
missing-physics axis for TP/TW residuals, supported by D2/D3/D4 diagnostic
evidence and setup-side sign envelopes. Do not cite it as a released
coefficient, Fluid source/property release, wallHeatFlux runtime feature,
ordinary upcomer closure, pressure K evidence, or final score.

## Guardrails

No Fluid solve, scheduler action, solver/postprocessing/sampler/harvest/UQ
launch, native-output mutation, registry/admission mutation, Fluid/external
edit, fitting/model selection, validation/holdout/external scoring,
source/property release, coefficient admission, final score, realized
wallHeatFlux runtime input, or residual absorption into internal Nu was
performed.
"""
    write_text(OUT_DIR / "README.md", readme)

    status = f"""---
provenance:
  generated_by: tools/analyze/build_mf08_signed_wall_flux_developing_thermal_branches.py
  task_id: {TASK_ID}
  generated_at_utc: {generated_at}
task: {TASK_ID}
tags:
  - status
  - MF08
  - signed-wall-flux
related:
  - {rel(OUT_DIR)}
---

# {TASK_ID}

## Objective

Create sign-aware thermal-development model-form candidates for cooler/passive
cooling and heater/test-section heating branches without using realized
wallHeatFlux, fitting, or source/property release.

## Outcome

Decision: `{summary['decision']}`. Required variants: `{summary['required_variant_rows']}`.
Train-smoke-ready variants: `{summary['ready_for_train_only_smoke_rows']}`.
Required variants needing source basis: `{summary['needs_source_basis_rows']}`.
Forbidden wallHeatFlux-fit shortcuts: `{summary['forbidden_wallHeatFlux_fit_rows']}`.

## Changes Made

- Wrote runtime-legal source table.
- Wrote setup/source-envelope provenance table.
- Wrote signed branch flux magnitude envelope.
- Wrote reset/Graetz basis table.
- Wrote assumptions/caveats and expected TP/TW/pressure direction-of-effect.
- Wrote candidate gate, guardrails, README, summary, status, journal, and import manifest.

## Validation

{validation_status}

## Guardrails

- Fluid solve: false.
- Scheduler action or solver/postprocessing/sampler/harvest/UQ launch: false.
- Native-output mutation: false.
- Registry/admission mutation: false.
- Fluid/external edit: false.
- Validation/holdout/external-test scoring: false.
- Fitting/tuning/model selection: false.
- Realized wallHeatFlux runtime input: false.
- Source/property release, coefficient admission, final score: false.
- Residual-internal-Nu absorption: false.
"""
    write_text(ROOT / f".agent/status/2026-07-22_{TASK_ID}.md", status)

    journal = f"""---
provenance:
  generated_by: tools/analyze/build_mf08_signed_wall_flux_developing_thermal_branches.py
  task_id: {TASK_ID}
  generated_at_utc: {generated_at}
task: {TASK_ID}
tags:
  - journal
  - MF08
  - signed-wall-flux
related:
  - {rel(OUT_DIR)}
---

# MF08 signed wall-flux developing thermal branches

## Attempted

Built an evidence-only gate for four predeclared sign-aware thermal-development
variants: cooler negative wall flux, passive/downcomer negative cooling, heater
positive heating, and piecewise signed reset-memory.

## Observed

Setup-known source/sink rows provide consistent signs and rough magnitudes for
cooler, lower-leg heater, and test-section/upcomer heat. The runtime contract
and source/property gate still block source release. M2 blocks passive repair
execution. D2/D3/D4 support thermal-development/source-placement structure but
remain diagnostic-only.

## Inferred

The model-form axis is scientifically worth preserving, but not worth running
yet. The correct next state is `needs_source_basis`, not a train-smoke candidate
and not a wallHeatFlux fit.

## Contradictions or Caveats

The setup-known signs are not a predictive source model. MF08 does not decide
the magnitude or reset length scale, and it does not repair upcomer
recirculation. Those remain separate source-basis/MF07/MF09 problems.

## Next Useful Actions

Finish the reset/Graetz source basis, assemble independent passive/source-side
heat basis, and evaluate recirculating-upcomer alternatives before any
train-only smoke execution.
"""
    write_text(ROOT / ".agent/journal/2026-07-22/mf08-signed-wall-flux-developing-thermal-branches.md", journal)


def build() -> dict[str, object]:
    generated_at = now_utc()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    stats = source_stats()
    runtime_sources = build_runtime_legal_source_table(stats)
    envelope = build_source_envelope(stats)
    sign_envelope = build_sign_magnitude_envelope(stats)
    reset_graetz = build_reset_graetz_basis()
    assumptions = build_assumptions_caveats()
    expected = build_expected_effects()
    candidate_gate = build_candidate_gate(expected)
    guardrails = build_guardrails()

    write_csv(OUT_DIR / "runtime_legal_source_table.csv", runtime_sources)
    write_csv(OUT_DIR / "source_envelope_provenance_table.csv", envelope)
    write_csv(OUT_DIR / "branch_wall_flux_sign_magnitude_envelope.csv", sign_envelope)
    write_csv(OUT_DIR / "reset_graetz_basis.csv", reset_graetz)
    write_csv(OUT_DIR / "assumptions_caveats_ledger.csv", assumptions)
    write_csv(OUT_DIR / "expected_tp_tw_direction_of_effect.csv", expected)
    write_csv(OUT_DIR / "candidate_gate.csv", candidate_gate)
    write_csv(OUT_DIR / "no_mutation_guardrails.csv", guardrails)

    required_rows = [row for row in candidate_gate if not row["variant_id"].startswith("forbidden_")]
    ready_rows = [row for row in required_rows if row["gate_decision"] == "ready_for_train_only_smoke"]
    needs_rows = [row for row in required_rows if row["gate_decision"] == "needs_source_basis"]
    forbidden_rows = [row for row in candidate_gate if row["gate_decision"] == "forbidden_as_wallHeatFlux_fit"]
    summary = {
        "task_id": TASK_ID,
        "generated_at_utc": generated_at,
        "decision": "needs_source_basis_sign_aware_development_promising_diagnostic_only",
        "required_variant_rows": len(required_rows),
        "runtime_source_rows": len(runtime_sources),
        "source_envelope_rows": len(envelope),
        "sign_envelope_rows": len(sign_envelope),
        "reset_graetz_rows": len(reset_graetz),
        "assumption_caveat_rows": len(assumptions),
        "expected_effect_rows": len(expected),
        "candidate_gate_rows": len(candidate_gate),
        "ready_for_train_only_smoke_rows": len(ready_rows),
        "needs_source_basis_rows": len(needs_rows),
        "forbidden_wallHeatFlux_fit_rows": len(forbidden_rows),
        "source_property_release_allowed": False,
        "coefficient_admission_allowed": False,
        "realized_wallHeatFlux_runtime_input_allowed": False,
        "fluid_solve": False,
        "native_output_mutation": False,
        "registry_or_admission_mutation": False,
        "scheduler_action": False,
        "solver_postprocessing_sampler_harvest_uq_launch": False,
        "fluid_or_external_edit": False,
        "validation_holdout_external_scoring": False,
        "fitting_tuning_model_selection": False,
        "final_score_claim": False,
        "residual_internal_nu_absorption": False,
        "source_context": [
            rel(SOURCE_PROVENANCE),
            rel(SOURCE_CONTRACT),
            rel(SOURCE_PROPERTY_GATE),
            rel(M2_RUNTIME),
            rel(M2_SUMMARY),
            rel(D2_SUMMARY),
            rel(D3_SUMMARY),
            rel(D4_SUMMARY),
        ],
    }
    write_text(OUT_DIR / "summary.json", json.dumps(summary, indent=2, sort_keys=True) + "\n")
    write_docs(summary)

    manifest = {
        "task": TASK_ID,
        "generated_at_utc": generated_at,
        "changed_files": [
            rel(OUT_DIR / "README.md"),
            rel(OUT_DIR / "summary.json"),
            rel(OUT_DIR / "runtime_legal_source_table.csv"),
            rel(OUT_DIR / "source_envelope_provenance_table.csv"),
            rel(OUT_DIR / "branch_wall_flux_sign_magnitude_envelope.csv"),
            rel(OUT_DIR / "reset_graetz_basis.csv"),
            rel(OUT_DIR / "assumptions_caveats_ledger.csv"),
            rel(OUT_DIR / "expected_tp_tw_direction_of_effect.csv"),
            rel(OUT_DIR / "candidate_gate.csv"),
            rel(OUT_DIR / "no_mutation_guardrails.csv"),
            f".agent/status/2026-07-22_{TASK_ID}.md",
            ".agent/journal/2026-07-22/mf08-signed-wall-flux-developing-thermal-branches.md",
            f"imports/2026-07-22_{SLUG}.json",
            "tools/analyze/build_mf08_signed_wall_flux_developing_thermal_branches.py",
            "tools/analyze/test_mf08_signed_wall_flux_developing_thermal_branches.py",
            ".agent/BOARD.md",
        ],
        "read_only_context": summary["source_context"]
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
            "fluid_solve": False,
            "source_property_release": False,
            "coefficient_admission": False,
            "realized_wallHeatFlux_runtime_input": False,
            "fitting_tuning_model_selection": False,
            "protected_scoring": False,
            "residual_internal_nu_absorption": False,
        },
    }
    write_text(ROOT / f"imports/2026-07-22_{SLUG}.json", json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return summary


if __name__ == "__main__":
    print(json.dumps(build(), indent=2, sort_keys=True))
