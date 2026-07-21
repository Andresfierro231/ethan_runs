#!/usr/bin/env python3
"""Build the repo-local 1D radiation sensitivity/capability package."""

from __future__ import annotations

import csv
import json
import math
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TASK = "TODO-1D-RADIATION-CAPABILITY"
ROOT = Path(__file__).resolve().parents[2]
OUT_REL = Path("work_products/2026-07/2026-07-21/2026-07-21_1d_radiation_capability")
OUT = ROOT / OUT_REL

FLUID_BC = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_fluid_external_bc_dict"
PHASE1 = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_heatloss_phase_1_external_bc_radiation_integration"
SPLIT = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_litrev_split_junction_storage_radiation_extraction"
RADIATION_GUIDANCE = ROOT / "work_products/2026-07/2026-07-13/2026-07-13_cfd_radiative_boundary_guidance"
THERMAL_MAP = ROOT / "operational_notes/maps/thermal-boundary-and-radiation.md"

SOURCE_RUNTIME_DICT = FLUID_BC / "fluid_external_boundary_runtime_dictionary.csv"
SOURCE_PHASE1_TESTS = PHASE1 / "radiation_analytic_tests.csv"
SOURCE_PHASE1_RUNTIME = PHASE1 / "runtime_mode_matrix.csv"
SOURCE_SPLIT_RUNTIME = SPLIT / "runtime_legality_guardrail.csv"
SOURCE_GUIDANCE = RADIATION_GUIDANCE / "cfd_emissivity_by_run.csv"

SIGMA = 5.670374419e-8
SCENARIOS = [
    ("surface_equals_surroundings", 0.0, "capability_zero_net_case"),
    ("surface_plus_10K", 10.0, "small_positive_loss_sensitivity"),
    ("surface_plus_25K", 25.0, "nominal_positive_loss_sensitivity"),
    ("surface_plus_50K", 50.0, "high_positive_loss_sensitivity"),
    ("surface_minus_10K", -10.0, "radiative_gain_sensitivity"),
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def as_float(value: str) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except ValueError:
        return None


def radiation_heat_w(emissivity: float, area_m2: float, surface_k: float, surroundings_k: float) -> float:
    return emissivity * SIGMA * area_m2 * (surface_k**4 - surroundings_k**4)


def linearized_hr_w_m2_k(emissivity: float, mean_k: float) -> float:
    return 4.0 * emissivity * SIGMA * mean_k**3


def analytic_rows() -> list[dict[str, str]]:
    cases = [
        {
            "test_id": "zero_emissivity",
            "emissivity": 0.0,
            "area_m2": 1.0,
            "surface_K": 350.0,
            "surroundings_K": 300.0,
            "expected_W": 0.0,
            "reason": "zero emissivity disables radiative exchange",
        },
        {
            "test_id": "zero_delta",
            "emissivity": 0.95,
            "area_m2": 1.0,
            "surface_K": 300.0,
            "surroundings_K": 300.0,
            "expected_W": 0.0,
            "reason": "equal surface and surroundings temperatures produce zero net exchange",
        },
        {
            "test_id": "hot_surface_loss",
            "emissivity": 0.95,
            "area_m2": 1.0,
            "surface_K": 350.0,
            "surroundings_K": 300.0,
            "expected_W": 372.029722,
            "reason": "hotter surface gives positive heat loss",
        },
        {
            "test_id": "cool_surface_gain",
            "emissivity": 0.95,
            "area_m2": 1.0,
            "surface_K": 290.0,
            "surroundings_K": 300.0,
            "expected_W": -55.333243,
            "reason": "cooler surface gives radiative heat gain",
        },
    ]
    rows: list[dict[str, str]] = []
    for case in cases:
        computed = radiation_heat_w(
            float(case["emissivity"]),
            float(case["area_m2"]),
            float(case["surface_K"]),
            float(case["surroundings_K"]),
        )
        rows.append(
            {
                "test_id": str(case["test_id"]),
                "formula": "epsilon*sigma*area*(surface_K^4-surroundings_K^4)",
                "emissivity": f"{case['emissivity']}",
                "area_m2": f"{case['area_m2']}",
                "surface_K": f"{case['surface_K']}",
                "surroundings_K": f"{case['surroundings_K']}",
                "computed_W": f"{computed:.6f}",
                "expected_W": f"{float(case['expected_W']):.6f}",
                "abs_error_W": f"{abs(computed - float(case['expected_W'])):.9f}",
                "pass_fail": "pass" if math.isclose(computed, float(case["expected_W"]), abs_tol=1e-6) else "fail",
                "reason": str(case["reason"]),
            }
        )
    h = linearized_hr_w_m2_k(0.95, 325.0)
    rows.append(
        {
            "test_id": "linearized_coefficient",
            "formula": "4*epsilon*sigma*Tmean^3",
            "emissivity": "0.95",
            "area_m2": "not_applicable",
            "surface_K": "not_applicable",
            "surroundings_K": "not_applicable",
            "computed_W": f"{h:.6f}",
            "expected_W": "7.396826",
            "abs_error_W": f"{abs(h - 7.396826):.9f}",
            "pass_fail": "pass" if math.isclose(h, 7.396826, abs_tol=1e-6) else "fail",
            "reason": "linearized coefficient is available only when explicitly labeled",
        }
    )
    return rows


def eligible_boundary_rows() -> list[dict[str, str]]:
    rows = []
    for row in read_csv(SOURCE_RUNTIME_DICT):
        if row.get("mode") != "predictive":
            continue
        if row.get("radiation_active") != "true":
            continue
        if not all(as_float(row.get(field, "")) is not None for field in ("Tsur_K", "emissivity", "area_m2")):
            continue
        rows.append(row)
    return rows


def sensitivity_rows(boundary: list[dict[str, str]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for row in boundary:
        t_sur = as_float(row["Tsur_K"])
        eps = as_float(row["emissivity"])
        area = as_float(row["area_m2"])
        assert t_sur is not None and eps is not None and area is not None
        for scenario_id, delta, scenario_class in SCENARIOS:
            surface = t_sur + delta
            q = radiation_heat_w(eps, area, surface, t_sur)
            mean_t = (surface + t_sur) / 2.0
            rows.append(
                {
                    "case_id": row["case_id"],
                    "validation_split_role": row["validation_split_role"],
                    "segment_id": row["segment_id"],
                    "patch_group": row["patch_group"],
                    "physical_role": row["physical_role"],
                    "scenario_id": scenario_id,
                    "scenario_class": scenario_class,
                    "surface_temperature_basis": "declared_sensitivity_offset_from_setup_Tsur",
                    "delta_surface_minus_Tsur_K": f"{delta:.6f}",
                    "Tsur_K": f"{t_sur:.6f}",
                    "surface_K": f"{surface:.6f}",
                    "emissivity": f"{eps:.6f}",
                    "area_m2": f"{area:.9f}",
                    "q_radiation_W": f"{q:.9f}",
                    "linearized_h_rad_W_m2_K": f"{linearized_hr_w_m2_k(eps, mean_t):.9f}",
                    "predictive_term_allowed": "true",
                    "replay_term_allowed": "false",
                    "source_use_category": "setup_sensitivity_not_fit_candidate",
                    "source_validity_envelope_status": "setup_boundary_fields_available",
                    "property_mode": "setup_case_property",
                    "property_sensitivity_label": "radiation_on_off_sensitivity",
                    "provenance_author_title": "AGENT-287 radiative boundary correction; Phase 1 external BC radiation integration",
                    "source_paths": row["source_paths"],
                }
            )
    return rows


def energy_ledger_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    grouped: dict[tuple[str, str], dict[str, float]] = defaultdict(lambda: {"q": 0.0, "area": 0.0, "n": 0.0})
    for row in rows:
        key = (row["case_id"], row["scenario_id"])
        grouped[key]["q"] += float(row["q_radiation_W"])
        grouped[key]["area"] += float(row["area_m2"])
        grouped[key]["n"] += 1
    ledger = []
    for (case_id, scenario_id), values in sorted(grouped.items()):
        ledger.append(
            {
                "case_id": case_id,
                "scenario_id": scenario_id,
                "radiation_rows": f"{int(values['n'])}",
                "active_radiating_area_m2": f"{values['area']:.9f}",
                "sum_q_radiation_W": f"{values['q']:.9f}",
                "energy_lane": "external_radiation",
                "external_convection_lane_status": "separate_lane_not_combined_in_this_package",
                "storage_or_residual_absorption": "forbidden",
                "admission_status": "sensitivity_only_no_fit_no_admission",
            }
        )
    return ledger


def runtime_audit_rows() -> list[dict[str, str]]:
    return [
        {
            "mode": "predictive_setup",
            "radiation_term_status": "allowed_from_setup_emissivity_Tsur_area_and_solved_surface_state",
            "realized_total_heat_replay_status": "forbidden_for_predictive_input",
            "double_counting_policy": "separate_radiation_allowed_only_when_total_replay_heat_is_not_consumed",
            "source_paths": rel(SOURCE_RUNTIME_DICT),
        },
        {
            "mode": "cfd_total_heat_replay",
            "radiation_term_status": "disabled_to_prevent_double_counting",
            "realized_total_heat_replay_status": "diagnostic_or_replay_only",
            "double_counting_policy": "do_not_add_radiation_on_top_of_total_replay_heat",
            "source_paths": rel(SOURCE_PHASE1_RUNTIME),
        },
        {
            "mode": "radiation_off_sensitivity",
            "radiation_term_status": "disabled_and_labeled_sensitivity",
            "realized_total_heat_replay_status": "not_a_cfd_parity_claim",
            "double_counting_policy": "radiation_off_rows_are_sensitivity_not_admission",
            "source_paths": rel(PHASE1 / "README.md"),
        },
        {
            "mode": "split_qr_extraction",
            "radiation_term_status": "no_separate_exported_qr_in_current_sources",
            "realized_total_heat_replay_status": "diagnostic_only",
            "double_counting_policy": "do_not_infer_qr_from_grouped_heat_or_residual",
            "source_paths": rel(SOURCE_SPLIT_RUNTIME),
        },
    ]


def source_manifest_rows() -> list[dict[str, str]]:
    sources = [
        SOURCE_RUNTIME_DICT,
        SOURCE_PHASE1_TESTS,
        SOURCE_PHASE1_RUNTIME,
        SOURCE_SPLIT_RUNTIME,
        SOURCE_GUIDANCE,
        THERMAL_MAP,
    ]
    return [
        {
            "source_path": rel(source),
            "use": "Read-only radiation capability/source-contract evidence.",
            "mutation_status": "read_only",
        }
        for source in sources
    ]


def readme(summary: dict[str, Any]) -> str:
    return f"""---
provenance:
  - {rel(SOURCE_RUNTIME_DICT)}
  - {rel(PHASE1 / "README.md")}
  - {rel(SPLIT / "README.md")}
tags: [thermal-modeling, radiation, heat-loss, one-d, no-admission]
related:
  - .agent/status/2026-07-21_{TASK}.md
  - .agent/journal/2026-07-21/1d-radiation-capability.md
task: {TASK}
date: 2026-07-21
role: Implementer/Tester/Writer
type: work_product
status: complete
supersedes: []
superseded_by:
---
# 1D Radiation Capability

## Decision

This package releases a repo-local 1D radiation capability and sensitivity
ledger. It computes radiative exchange from setup emissivity, surroundings
temperature, area, and declared surface-temperature offsets. It does not edit
Fluid/API code, consume solver output as a predictive input, fit a coefficient,
or admit a closure.

## Results

- Analytic tests: `{summary["analytic_test_rows"]}` rows, `{summary["analytic_tests_failed"]}` failures.
- Predictive setup boundary rows: `{summary["predictive_boundary_rows"]}`.
- Radiation sensitivity rows: `{summary["sensitivity_rows"]}`.
- Case/scenario energy ledger rows: `{summary["energy_ledger_rows"]}`.
- Fit/admission rows released: `0`.

## Outputs

- `radiation_analytic_tests.csv`
- `radiation_sensitivity_scenarios.csv`
- `radiation_energy_ledger.csv`
- `runtime_double_counting_audit.csv`
- `source_manifest.csv`
- `summary.json`

## Guardrails

Current 3D CFD includes radiative exchange through `rcExternalTemperature`, but
the cited sources expose no separate exported `qr` heat-loss term. Predictive 1D
may compute radiation from setup fields and solved states. Replay/diagnostic
use of total CFD heat disables a separate radiation term to prevent double
counting. No native CFD/OpenFOAM output, registry/admission state, scheduler
state, Fluid source, external repository, blocker register, generated index,
fit, tuning, model-selection, or admission state was changed.
"""


def build() -> dict[str, Any]:
    OUT.mkdir(parents=True, exist_ok=True)
    analytic = analytic_rows()
    boundary = eligible_boundary_rows()
    sensitivity = sensitivity_rows(boundary)
    ledger = energy_ledger_rows(sensitivity)
    runtime = runtime_audit_rows()
    manifest = source_manifest_rows()
    summary = {
        "task": TASK,
        "created_utc": utc_now(),
        "output_dir": rel(OUT),
        "analytic_test_rows": len(analytic),
        "analytic_tests_failed": sum(1 for row in analytic if row["pass_fail"] != "pass"),
        "predictive_boundary_rows": len(boundary),
        "sensitivity_rows": len(sensitivity),
        "energy_ledger_rows": len(ledger),
        "case_count": len({row["case_id"] for row in boundary}),
        "fit_rows_released": 0,
        "admission_rows_released": 0,
        "native_solver_outputs_mutated": False,
        "registry_mutated": False,
        "scheduler_action": False,
        "solver_or_postprocessing_launched": False,
        "staged_copy_or_extraction_launched": False,
        "fluid_or_external_edit": False,
        "external_repositories_mutated": False,
        "fitting_or_model_selection_performed": False,
        "admission_state_mutated": False,
        "blocker_register_mutated": False,
        "generated_docs_index_mutated": False,
        "no_scorecard_outputs": True,
    }
    write_csv(OUT / "radiation_analytic_tests.csv", analytic)
    write_csv(OUT / "radiation_sensitivity_scenarios.csv", sensitivity)
    write_csv(OUT / "radiation_energy_ledger.csv", ledger)
    write_csv(OUT / "runtime_double_counting_audit.csv", runtime)
    write_csv(OUT / "source_manifest.csv", manifest)
    write_json(OUT / "summary.json", summary)
    (OUT / "README.md").write_text(readme(summary), encoding="utf-8")
    return summary


if __name__ == "__main__":
    print(json.dumps(build(), indent=2, sort_keys=True))
