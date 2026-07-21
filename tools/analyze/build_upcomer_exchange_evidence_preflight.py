#!/usr/bin/env python3
"""Build a no-solver upcomer exchange-evidence preflight package.

This builder consumes existing repo artifacts only. It does not read or mutate
native solver outputs, launch a sampler, fit coefficients, select a model, or
change closure/admission state.
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TASK = "TODO-UPCOMER-EXCHANGE-EVIDENCE-PREFLIGHT-2026-07-21"
ROOT = Path(__file__).resolve().parents[2]
OUT_REL = Path("work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_evidence_preflight")
OUT = ROOT / OUT_REL

PHASE4 = ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_heatloss_phase_4_upcomer_exchange_and_internal_nu_gate"
)
RECIRC = ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_litrev_matched_plane_recirc_field_harvest"
)
FIRST_WAVE = ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_predictive_first_key_studies_wave"
)
FORWARD_MAP = ROOT / "operational_notes/maps/forward-predictive-model.md"

PHASE4_UPCOMER = PHASE4 / "upcomer_exchange_cell_readiness.csv"
PHASE4_MISSING = PHASE4 / "missing_exchange_nu_evidence_queue.csv"
PHASE4_DECISION = PHASE4 / "phase4_decision_gate.csv"
PHASE4_ORDINARY = PHASE4 / "ordinary_single_stream_nu_reopening_candidates.csv"
PHASE4_RUNTIME = PHASE4 / "runtime_internal_nu_audit.csv"
RECIRC_READINESS = RECIRC / "recirc_harvest_readiness.csv"
RECIRC_ROWS = RECIRC / "matched_plane_recirc_field_harvest.csv"
FIRST_WAVE_QUEUE = FIRST_WAVE / "next_gate_queue.csv"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


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
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def count_present(rows: list[dict[str, str]], field: str) -> int:
    return sum(1 for row in rows if row.get(field, "").lower() not in {"", "missing", "none"})


def status_counter(rows: list[dict[str, str]], field: str) -> Counter[str]:
    return Counter(row.get(field, "") for row in rows)


def variable_availability() -> list[dict[str, Any]]:
    upcomer_rows = read_csv(PHASE4_UPCOMER)
    missing_rows = read_csv(PHASE4_MISSING)
    missing_by_field = {row["field_or_group"]: row for row in missing_rows}

    def source(field: str) -> str:
        row = missing_by_field.get(field)
        return row["source_paths"] if row else rel(PHASE4_UPCOMER)

    def missing_status(field: str, next_action: str, *, source_status: str = "requires_new_sampler_or_terminal") -> dict[str, Any]:
        row = missing_by_field.get(field, {})
        return {
            "variable_id": field,
            "variable_group": row.get("needed_for", "exchange_cell_state"),
            "current_status": row.get("phase4_status", "not_cleared_for_admission"),
            "source_status": source_status,
            "available_existing_rows": 0,
            "terminal_gated_rows": 0,
            "requires_new_sampler": "yes",
            "admission_use_now": "false",
            "next_action": next_action,
            "source_paths": source(field),
        }

    terminal_gated = sum(
        1
        for row in upcomer_rows
        if "terminal" in row.get("blocking_reasons", "").lower()
        or "compute-node-sampling-required" in row.get("blocking_reasons", "").lower()
    )

    rows = [
        missing_status(
            "recirculation_volume",
            "Extract or admit V_recirc before opening exchange-state calibration.",
        ),
        missing_status(
            "exchange_rate",
            "Extract mdot_exchange and tau_recirc from a claimed terminal/sampler row.",
        ),
        {
            "variable_id": "V_recirc",
            "variable_group": "exchange_cell_state",
            "current_status": "missing_V_recirc",
            "source_status": "requires_new_sampler_or_terminal",
            "available_existing_rows": 0,
            "terminal_gated_rows": terminal_gated,
            "requires_new_sampler": "yes",
            "admission_use_now": "false",
            "next_action": "Do not fit exchange cells until an admitted volume definition exists.",
            "source_paths": rel(PHASE4_UPCOMER),
        },
        {
            "variable_id": "mdot_exchange",
            "variable_group": "exchange_cell_state",
            "current_status": "missing_mdot_exchange",
            "source_status": "requires_new_sampler_or_terminal",
            "available_existing_rows": 0,
            "terminal_gated_rows": terminal_gated,
            "requires_new_sampler": "yes",
            "admission_use_now": "false",
            "next_action": "Do not infer exchange rate from RAF/RMF/SVF proxy metrics.",
            "source_paths": rel(PHASE4_UPCOMER),
        },
        {
            "variable_id": "tau_recirc",
            "variable_group": "exchange_cell_state",
            "current_status": "missing_tau_recirc",
            "source_status": "requires_new_sampler_or_terminal",
            "available_existing_rows": 0,
            "terminal_gated_rows": terminal_gated,
            "requires_new_sampler": "yes",
            "admission_use_now": "false",
            "next_action": "Compute residence time only after V_recirc and mdot_exchange are both admitted.",
            "source_paths": rel(PHASE4_UPCOMER),
        },
        missing_status(
            "thermal_state",
            "Require same-window T_main/T_recirc or enthalpy state before energy closure.",
        ),
        {
            "variable_id": "T_main_T_recirc",
            "variable_group": "exchange_energy_state",
            "current_status": "missing_T_recirc_or_same_window_enthalpy_state",
            "source_status": "requires_new_sampler_or_terminal",
            "available_existing_rows": 0,
            "terminal_gated_rows": terminal_gated,
            "requires_new_sampler": "yes",
            "admission_use_now": "false",
            "next_action": "Extract paired main/recirculation thermal states in the same window as exchange rates.",
            "source_paths": source("thermal_state"),
        },
        {
            "variable_id": "wall_core_delta_T",
            "variable_group": "exchange_energy_state",
            "current_status": "missing_wall_core_delta_T",
            "source_status": "requires_new_sampler_or_terminal",
            "available_existing_rows": count_present(upcomer_rows, "wall_core_delta_T_status"),
            "terminal_gated_rows": terminal_gated,
            "requires_new_sampler": "yes",
            "admission_use_now": "false",
            "next_action": "Use present proxy rows as diagnostics only; require admitted wall/core field extraction for scoring.",
            "source_paths": rel(PHASE4_UPCOMER),
        },
        {
            "variable_id": "energy_residual",
            "variable_group": "thermal_residual_attribution",
            "current_status": "available_existing_diagnostic",
            "source_status": "available_existing_diagnostic_only",
            "available_existing_rows": count_present(upcomer_rows, "energy_residual_W"),
            "terminal_gated_rows": 0,
            "requires_new_sampler": "no",
            "admission_use_now": "false",
            "next_action": "Use for residual attribution narrative; do not absorb into internal Nu or exchange coefficient.",
            "source_paths": rel(PHASE4_UPCOMER),
        },
        {
            "variable_id": "pressure_residual_basis",
            "variable_group": "pressure_residual_attribution",
            "current_status": status_counter(upcomer_rows, "pressure_residual_status").most_common(1)[0][0],
            "source_status": "requires_same_window_pressure_basis",
            "available_existing_rows": 0,
            "terminal_gated_rows": terminal_gated,
            "requires_new_sampler": "yes",
            "admission_use_now": "false",
            "next_action": "Do not score pressure residual until static p/p_rgh and straight-development subtraction are same-window.",
            "source_paths": source("pressure_basis"),
        },
        {
            "variable_id": "same_QOI_UQ",
            "variable_group": "uncertainty_and_admission",
            "current_status": "blocked_missing_same_qoi_UQ",
            "source_status": "requires_same_qoi_mesh_time_uq",
            "available_existing_rows": 0,
            "terminal_gated_rows": terminal_gated,
            "requires_new_sampler": "yes",
            "admission_use_now": "false",
            "next_action": "Keep all exchange-cell rows diagnostic until same-QOI uncertainty exists.",
            "source_paths": source("same_qoi_uq"),
        },
        {
            "variable_id": "RAF_RMF_SVF",
            "variable_group": "recirculation_guard_diagnostics",
            "current_status": "available_existing_diagnostic",
            "source_status": "available_existing_diagnostic_only",
            "available_existing_rows": count_present(upcomer_rows, "reverse_area_fraction"),
            "terminal_gated_rows": 0,
            "requires_new_sampler": "no",
            "admission_use_now": "false",
            "next_action": "Use to disable ordinary single-stream closure, not to fit exchange coefficients.",
            "source_paths": rel(PHASE4_UPCOMER),
        },
        {
            "variable_id": "secondary_flow_intensity",
            "variable_group": "recirculation_guard_diagnostics",
            "current_status": "available_existing_diagnostic",
            "source_status": "available_existing_diagnostic_only",
            "available_existing_rows": count_present(upcomer_rows, "secondary_flow_intensity"),
            "terminal_gated_rows": 0,
            "requires_new_sampler": "no",
            "admission_use_now": "false",
            "next_action": "Use as diagnostic recirculation severity, not as a predictive exchange variable.",
            "source_paths": rel(PHASE4_UPCOMER),
        },
        {
            "variable_id": "runtime_split_role",
            "variable_group": "runtime_and_split_guard",
            "current_status": "available_existing_audit",
            "source_status": "available_existing_policy_only",
            "available_existing_rows": len(read_csv(PHASE4_RUNTIME)),
            "terminal_gated_rows": 0,
            "requires_new_sampler": "no",
            "admission_use_now": "false",
            "next_action": "Carry the no-runtime-leakage split audit into any later sampler or scorecard row.",
            "source_paths": rel(PHASE4_RUNTIME),
        },
    ]
    return rows


def sampler_source_queue() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in read_csv(RECIRC_READINESS):
        source_family = row["source_family"]
        if source_family in {"high_heat_terminal_gated", "latest_corrected_Q_live_continuation"}:
            preflight_action = "wait_terminal_or_claim_terminal_harvest"
            decision = "terminal_gated_no_duplicate_sampler"
        elif source_family == "pm10_pressure_only_target":
            preflight_action = "not_exchange_sampler_source"
            decision = "blocked_not_exchange_evidence"
        else:
            preflight_action = "diagnostic_only_no_new_sampler"
            decision = "diagnostic_proxy_no_coefficient_admission"
        rows.append(
            {
                "source_family": source_family,
                "row_count": row["row_count"],
                "rows_with_RAF_RMF_SVF": row["rows_with_RAF_RMF_SVF"],
                "current_admission_readiness": row["admission_readiness"],
                "preflight_decision": decision,
                "sampler_allowed_now": "false",
                "phase4b_candidate_source": "false",
                "next_action": preflight_action,
                "coefficient_admission_status": row["coefficient_admission_status"],
                "source_paths": rel(RECIRC_READINESS),
            }
        )
    return rows


def qoi_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in read_csv(PHASE4_UPCOMER):
        rows.append(
            {
                "readiness_id": row["readiness_id"],
                "source_family": row["source_family"],
                "case_key": row["case_key"],
                "case_id": row["case_id"],
                "feature_or_span": row["feature_or_span"],
                "reverse_area_fraction": row["reverse_area_fraction"],
                "reverse_mass_fraction": row["reverse_mass_fraction"],
                "secondary_flow_intensity": row["secondary_flow_intensity"],
                "energy_residual_W": row["energy_residual_W"],
                "energy_residual_status": row["energy_residual_status"],
                "missing_exchange_state": ";".join(
                    [
                        row["V_recirc_status"],
                        row["mdot_exchange_status"],
                        row["tau_recirc_status"],
                        row["wall_core_delta_T_status"],
                        row["pressure_residual_status"],
                        row["same_qoi_uq_status"],
                    ]
                ),
                "admission_use": "false",
                "preflight_use": "diagnostic_only",
                "next_action": "Do not fit or rescore from this row until missing exchange-state fields are admitted.",
                "source_paths": rel(PHASE4_UPCOMER),
            }
        )
    return rows


def same_qoi_status() -> list[dict[str, Any]]:
    decision_rows = read_csv(PHASE4_DECISION)
    evidence = {row["decision_id"]: row for row in decision_rows}
    return [
        {
            "qoi_gate": "same_qoi_UQ",
            "current_status": "blocked_missing_same_qoi_UQ",
            "scorecard_use_now": "false",
            "claim_boundary": "no exchange-cell admission without same-QOI mesh/time uncertainty",
            "next_action": "Pair mesh/time uncertainty with the exact exchange-state QOIs before Phase 4B.",
            "source_paths": rel(PHASE4_UPCOMER),
        },
        {
            "qoi_gate": "pressure_basis",
            "current_status": "missing_or_partial_no_same_window_pressure_residual",
            "scorecard_use_now": "false",
            "claim_boundary": "pressure residual can be attributed only after same-window pressure basis and straight-loss subtraction",
            "next_action": "Keep current pressure evidence in diagnostic/source-envelope lane.",
            "source_paths": rel(PHASE4_MISSING),
        },
        {
            "qoi_gate": "thermal_energy_residual",
            "current_status": "available_existing_diagnostic",
            "scorecard_use_now": "diagnostic_only",
            "claim_boundary": "thermal residual can support attribution but not coefficient fitting",
            "next_action": "Use as thesis evidence for why exchange state is needed.",
            "source_paths": rel(PHASE4_UPCOMER),
        },
        {
            "qoi_gate": "mesh_time_status",
            "current_status": "blocked_or_terminal_gated",
            "scorecard_use_now": "false",
            "claim_boundary": evidence.get("terminal_or_sampling_dependency", {}).get(
                "evidence",
                "terminal/sampling dependency unresolved",
            ),
            "next_action": "Wait for terminal/admission rows or claim a narrow sampler row after this preflight.",
            "source_paths": rel(RECIRC_READINESS),
        },
    ]


def phase4b_decision() -> list[dict[str, Any]]:
    return [
        {
            "decision_id": "scoped_sampler_launch",
            "status": "blocked_no_launch_from_preflight",
            "evidence": "No source family is safe for immediate exchange-state sampling from this row.",
            "admission_change": "none",
            "next_action": "Claim a separate terminal-harvest or sampler row only after source family and QOI contract are fixed.",
            "source_paths": rel(RECIRC_READINESS),
        },
        {
            "decision_id": "phase4b_rescore",
            "status": "blocked_waiting_evidence",
            "evidence": "V_recirc, mdot_exchange, tau_recirc, same-window thermal/pressure states, and same-QOI UQ are not admitted.",
            "admission_change": "none",
            "next_action": "Do not rescore exchange cells or ordinary internal Nu from proxy recirculation metrics.",
            "source_paths": rel(PHASE4_MISSING),
        },
        {
            "decision_id": "phase5_trigger",
            "status": "not_triggered",
            "evidence": "Phase 4 remains negative and Phase 4B is blocked.",
            "admission_change": "none",
            "next_action": "Keep final predictive scorecard trigger-gated.",
            "source_paths": rel(PHASE4_DECISION),
        },
        {
            "decision_id": "thesis_use",
            "status": "positive_diagnostic_negative_result",
            "evidence": "Current evidence strengthens the recirculation guard and narrows the missing exchange-state variables.",
            "admission_change": "none",
            "next_action": "Write as rigorous blocker-narrowing, not as final predictive accuracy or closure admission.",
            "source_paths": rel(PHASE4_UPCOMER),
        },
    ]


def source_manifest() -> list[dict[str, Any]]:
    paths = [
        PHASE4_UPCOMER,
        PHASE4_MISSING,
        PHASE4_DECISION,
        PHASE4_ORDINARY,
        PHASE4_RUNTIME,
        RECIRC_READINESS,
        RECIRC_ROWS,
        FIRST_WAVE_QUEUE,
        FORWARD_MAP,
    ]
    return [
        {
            "path": rel(path),
            "role": "read_only_input",
            "exists": str(path.exists()).lower(),
            "native_solver_output": "false",
            "mutated": "false",
        }
        for path in paths
    ]


def readme(summary: dict[str, Any]) -> str:
    return f"""---
task: {TASK}
date: 2026-07-21
role: Forward-pred / Implementer / Tester / Writer
type: work_product
status: complete
tags: [forward-model, upcomer, recirculation, heat-loss, no-solver-preflight]
related:
  - {rel(PHASE4)}
  - {rel(RECIRC)}
  - {rel(FIRST_WAVE)}
---
# Upcomer Exchange Evidence Preflight

This package implements a no-solver evidence preflight before any Phase 4B
exchange-state sampler is launched.

## Decision

- `sampler_allowed_now`: `{str(summary["sampler_allowed_now"]).lower()}`
- `phase4b_ready`: `{str(summary["phase4b_ready"]).lower()}`
- `phase5_trigger`: `{summary["phase5_trigger"]}`
- `exchange_cell_admission`: `{summary["exchange_cell_admission"]}`

The current evidence is scientifically useful but not admission-grade. Existing
upcomer rows carry diagnostic RAF/RMF/SVF and energy-residual information, but
they do not admit `V_recirc`, `mdot_exchange`, `tau_recirc`, same-window
wall/core thermal state, same-window pressure residual basis, or same-QOI UQ.

## Outputs

- `exchange_variable_availability.csv`: field-by-field availability and claim
  boundary for the exchange model.
- `scoped_sampler_source_queue.csv`: source-family queue with explicit
  no-launch decisions for this row.
- `upcomer_exchange_qoi_rows.csv`: row-level diagnostic QOI ledger inherited
  from Phase 4.
- `same_qoi_uq_status.csv`: pressure, thermal, and UQ gate status.
- `phase4b_rescore_decision.csv`: Phase 4B/Phase 5 trigger decision.
- `source_manifest.csv`: read-only provenance.

## Guardrails

No native CFD/OpenFOAM outputs, registry/admission state, scheduler state,
Fluid source, external repositories, or blocker register were mutated. No
solver, postprocessor, sampler, fitting, model selection, closure admission, or
Phase 5 trigger was run.
"""


def build() -> dict[str, Any]:
    OUT.mkdir(parents=True, exist_ok=True)

    variable_rows = variable_availability()
    sampler_rows = sampler_source_queue()
    qoi = qoi_rows()
    uq = same_qoi_status()
    decisions = phase4b_decision()
    manifest = source_manifest()

    write_csv(OUT / "exchange_variable_availability.csv", variable_rows)
    write_csv(OUT / "scoped_sampler_source_queue.csv", sampler_rows)
    write_csv(OUT / "upcomer_exchange_qoi_rows.csv", qoi)
    write_csv(OUT / "same_qoi_uq_status.csv", uq)
    write_csv(OUT / "phase4b_rescore_decision.csv", decisions)
    write_csv(OUT / "source_manifest.csv", manifest)

    summary = {
        "task": TASK,
        "built_at_utc": utc_now(),
        "exchange_variable_rows": len(variable_rows),
        "qoi_rows": len(qoi),
        "sampler_source_rows": len(sampler_rows),
        "sampler_allowed_now": any(row["sampler_allowed_now"] == "true" for row in sampler_rows),
        "phase4b_ready": False,
        "phase5_trigger": "not_triggered",
        "exchange_cell_admission": "none",
        "ordinary_internal_nu_admission": "none",
        "variables_available_existing": sum(
            1 for row in variable_rows if row["source_status"].startswith("available_existing")
        ),
        "variables_requiring_sampler_or_terminal": sum(
            1
            for row in variable_rows
            if "requires" in row["source_status"] or row["requires_new_sampler"] == "yes"
        ),
        "native_output_mutation": False,
        "registry_mutation": False,
        "scheduler_action": False,
        "fluid_edit": False,
        "external_repo_edit": False,
        "fitting_or_model_selection": False,
        "closure_admission_change": False,
        "blocker_register_change": False,
    }
    write_json(OUT / "summary.json", summary)
    (OUT / "README.md").write_text(readme(summary), encoding="utf-8")
    return summary


if __name__ == "__main__":
    result = build()
    print(json.dumps(result, indent=2, sort_keys=True))
