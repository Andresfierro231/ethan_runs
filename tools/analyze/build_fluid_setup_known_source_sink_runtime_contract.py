#!/usr/bin/env python3
"""Build the setup-known source/sink runtime contract package.

This is a gate package, not an admission package. It records that the existing
Fluid solver can express the lower-leg heater redistribution from setup-known
case power via ``heater_source_mode=tw4_to_tp3_three_span``. It does not mutate
Fluid or promote source/sink rows into validation/holdout scoring.
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_fluid_setup_known_source_sink_runtime_contract"
TASK_ID = "TODO-FLUID-SETUP-KNOWN-SOURCE-SINK-RUNTIME-CONTRACT-2026-07-21"
SOURCE_LEDGER = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_extbc_source_sink_provenance_recovery/setup_source_sink_provenance_ledger.csv"
NEXT_GATE = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_extbc_source_sink_provenance_recovery/next_use_gate.csv"
HEATED_AUDIT = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_heated_incline_tw4_tw6_local_audit/failure_classification.csv"
FLUID_ROOT = ROOT.parent / "cfd-modeling-tools/tamu_first_order_model/Fluid"


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path.resolve())


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = []
        for row in rows:
            for key in row:
                if key not in fieldnames:
                    fieldnames.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames or ["empty"])
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def import_fluid_symbols() -> dict[str, Any]:
    sys.path.insert(0, str(FLUID_ROOT))
    from tamu_loop_model_v2.solver import (  # type: ignore
        DEFAULT_HEATER_SOURCE_SPAN_WEIGHTS,
        HEATER_SOURCE_TW4_TO_TP3_SPANS,
        ScenarioConfig,
        heating_power_for_segment_with_scenario,
    )

    return {
        "DEFAULT_HEATER_SOURCE_SPAN_WEIGHTS": DEFAULT_HEATER_SOURCE_SPAN_WEIGHTS,
        "HEATER_SOURCE_TW4_TO_TP3_SPANS": HEATER_SOURCE_TW4_TO_TP3_SPANS,
        "ScenarioConfig": ScenarioConfig,
        "heating_power_for_segment_with_scenario": heating_power_for_segment_with_scenario,
    }


def build_contract_rows(source_rows: list[dict[str, str]], fluid: dict[str, Any]) -> list[dict[str, Any]]:
    weights = fluid["DEFAULT_HEATER_SOURCE_SPAN_WEIGHTS"]
    rows: list[dict[str, Any]] = []
    for row in source_rows:
        if row["case_id"] != "salt_2" or row["source_segment_id"] != "lower_leg" or row["physical_role"] != "heater":
            continue
        setup_q = float(row["setup_value_W"])
        for span, weight in weights.items():
            rows.append(
                {
                    "case_id": row["case_id"],
                    "split_role": row["split_role"],
                    "source_segment_id": row["source_segment_id"],
                    "physical_role": row["physical_role"],
                    "fluid_api": "ScenarioConfig.heater_source_mode",
                    "scenario_value": "tw4_to_tp3_three_span",
                    "span_id": span,
                    "span_fraction_start": fluid["HEATER_SOURCE_TW4_TO_TP3_SPANS"][span][0],
                    "span_fraction_end": fluid["HEATER_SOURCE_TW4_TO_TP3_SPANS"][span][1],
                    "default_weight_fraction": weight,
                    "setup_heater_Q_total_W": setup_q,
                    "allocated_setup_Q_W": setup_q * float(weight),
                    "provenance_status": row["provenance_class_after_recovery"],
                    "runtime_contract_status": "setup_known_contract_executable_train_only",
                    "runtime_admitted_now": False,
                    "source_property_released_now": False,
                    "claim_boundary": "lower-leg setup heater redistribution contract only; no validation/holdout/external scoring or admission",
                    "source_path": row["source_path"],
                }
            )
    return rows


def build_api_rows(fluid: dict[str, Any]) -> list[dict[str, Any]]:
    weights = fluid["DEFAULT_HEATER_SOURCE_SPAN_WEIGHTS"]
    spans = fluid["HEATER_SOURCE_TW4_TO_TP3_SPANS"]
    return [
        {
            "capability": "heater_source_mode",
            "status": "present",
            "evidence": "ScenarioConfig exposes heater_source_mode with supported tw4_to_tp3_three_span path",
            "allowed_use_now": "train_only_contract_and_diagnostic_run",
            "blocked_use": "source_property_release;freeze;validation_holdout_external_scoring;admission",
            "source_path": rel(FLUID_ROOT / "tamu_loop_model_v2/solver.py"),
        },
        {
            "capability": "default_heater_source_weights",
            "status": "present",
            "evidence": json.dumps(weights, sort_keys=True),
            "allowed_use_now": "predeclared deterministic weights",
            "blocked_use": "fit_or_tune_weights_from_residuals",
            "source_path": rel(FLUID_ROOT / "tamu_loop_model_v2/solver.py"),
        },
        {
            "capability": "heater_source_span_bounds",
            "status": "present",
            "evidence": json.dumps(spans, sort_keys=True),
            "allowed_use_now": "TW4-to-TP3 lower-leg source distribution",
            "blocked_use": "sensor-temperature runtime input",
            "source_path": rel(FLUID_ROOT / "tamu_loop_model_v2/solver.py"),
        },
    ]


def build_runtime_rows() -> list[dict[str, Any]]:
    forbidden = [
        "realized CFD wallHeatFlux",
        "CFD mdot",
        "validation temperatures",
        "holdout temperatures",
        "external-test temperatures",
        "imposed cooler duty replay",
        "hidden heat residual",
    ]
    return [
        {
            "check_id": f"RT-{index:03d}",
            "runtime_input": item,
            "status": "forbidden",
            "used_by_contract": False,
            "evidence": "contract uses setup-known heater Q and predeclared solver source distribution only",
        }
        for index, item in enumerate(forbidden, start=1)
    ]


def build_source_property_rows() -> list[dict[str, Any]]:
    return [
        {
            "gate_id": "SP-001",
            "gate": "setup_known_source_contract",
            "status": "pass",
            "result": "lower-leg heater Q has setup-known provenance and executable Fluid source mode",
        },
        {
            "gate_id": "SP-002",
            "gate": "train_only_residual_effect_test",
            "status": "next_row_required",
            "result": "must run train-only residual decomposition before source/property release",
        },
        {
            "gate_id": "SP-003",
            "gate": "source_property_release",
            "status": "blocked",
            "result": "no freeze/admission/source-property release from contract evidence alone",
        },
    ]


def write_docs(summary: dict[str, Any]) -> None:
    readme = f"""---
provenance:
  - {rel(SOURCE_LEDGER)}
  - {rel(NEXT_GATE)}
  - {rel(HEATED_AUDIT)}
tags: [fluid, setup-known-source, heater-source, train-only]
related:
  - {rel(ROOT / 'work_products/2026-07/2026-07-21/2026-07-21_heated_incline_tw4_tw6_local_audit')}
task: {TASK_ID}
date: 2026-07-21
role: Forward-pred / Thermal-modeling / Implementer / Tester / Writer
type: work_product
status: complete
---
# Setup-Known Source/Sink Runtime Contract

This package releases a train-only runtime contract for the lower-leg heater
source lane using the existing Fluid `heater_source_mode=tw4_to_tp3_three_span`
capability and recovered setup-known Salt2 heater power.

Result: `{summary['decision']}`.

- contract rows: `{summary['contract_rows']}`
- runtime-admitted rows: `0`
- source/property release rows: `0`
- external Fluid mutation: `false`

Next action is the separately claimed train-only residual decomposition row.
"""
    (PACKAGE / "README.md").write_text(readme, encoding="utf-8")

    write_csv(
        PACKAGE / "source_manifest.csv",
        [
            {"source_id": "source_sink_provenance", "path": rel(SOURCE_LEDGER), "use": "setup-known Q evidence", "mutation": False},
            {"source_id": "next_use_gate", "path": rel(NEXT_GATE), "use": "source-model gate requirements", "mutation": False},
            {"source_id": "heated_incline_audit", "path": rel(HEATED_AUDIT), "use": "TW4-TW6 failure classification", "mutation": False},
            {"source_id": "fluid_solver", "path": rel(FLUID_ROOT / "tamu_loop_model_v2/solver.py"), "use": "existing heater_source_mode capability", "mutation": False},
            {"source_id": "fluid_tests", "path": rel(FLUID_ROOT / "tests/test_solver_contracts.py"), "use": "existing source-mode tests", "mutation": False},
        ],
        ["source_id", "path", "use", "mutation"],
    )


def build() -> dict[str, Any]:
    PACKAGE.mkdir(parents=True, exist_ok=True)
    source_rows = read_csv(SOURCE_LEDGER)
    fluid = import_fluid_symbols()
    contract_rows = build_contract_rows(source_rows, fluid)
    if not contract_rows:
        raise RuntimeError("No Salt2 lower-leg heater contract rows were generated.")

    write_csv(PACKAGE / "setup_known_source_contract.csv", contract_rows)
    write_csv(PACKAGE / "fluid_api_capability_audit.csv", build_api_rows(fluid))
    write_csv(PACKAGE / "runtime_leakage_audit.csv", build_runtime_rows())
    write_csv(PACKAGE / "source_property_gate.csv", build_source_property_rows())

    summary = {
        "task_id": TASK_ID,
        "date": "2026-07-21",
        "status": "complete",
        "decision": "setup_known_lower_leg_heater_contract_ready_for_train_only_residual_decomposition",
        "contract_rows": len(contract_rows),
        "runtime_admitted_rows": 0,
        "source_property_released_rows": 0,
        "external_fluid_mutation": False,
        "native_output_mutation": False,
        "registry_or_admission_mutation": False,
        "scheduler_action": False,
        "validation_rows_consumed": 0,
        "holdout_rows_consumed": 0,
        "external_test_rows_consumed": 0,
        "next_action": "run train-only heater-source residual decomposition",
    }
    write_json(PACKAGE / "summary.json", summary)
    write_docs(summary)
    return summary


if __name__ == "__main__":
    build()
    print(f"wrote {rel(PACKAGE)}")
