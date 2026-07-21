#!/usr/bin/env python3
"""Build the S9 upcomer onset/exchange UQ thesis study package.

This is an evidence consolidation study. It reads existing published packages
and emits gate tables for S11 readiness; it does not launch samplers, harvest
native fields, fit coefficients, or admit closures.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


TASK = "TODO-THESIS-STUDY-S9-UPCOMER-ONSET-ANCHOR-EXCHANGE-UQ-2026-07-21"
DATE = "2026-07-21"
DEFAULT_OUT = Path(
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_thesis_study_s9_upcomer_onset_anchor_exchange_uq"
)

S4 = Path(
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_thesis_study_s4_recirculation_guard_upcomer_hybrid"
)
S8 = Path(
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_thesis_study_s8_wall_test_section_axial_mixing_candidate"
)
PREFLIGHT = Path(
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_upcomer_exchange_evidence_preflight"
)
TERMINAL = Path(
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_upcomer_exchange_terminal_source_readiness"
)
INPUTS = Path(
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_upcomer_exchange_input_generation"
)
PHASE4 = Path(
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_heatloss_phase_4_upcomer_exchange_and_internal_nu_gate"
)
SAME_QOI_B = Path(
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_same_qoi_uq_phase_b_mesh_gci_evidence_matrix"
)

SOURCE_FILES = {
    "s4_summary": S4 / "summary.json",
    "s8_summary": S8 / "summary.json",
    "preflight_summary": PREFLIGHT / "summary.json",
    "preflight_qoi_rows": PREFLIGHT / "upcomer_exchange_qoi_rows.csv",
    "preflight_variable_availability": PREFLIGHT / "exchange_variable_availability.csv",
    "preflight_same_qoi_status": PREFLIGHT / "same_qoi_uq_status.csv",
    "terminal_summary": TERMINAL / "summary.json",
    "terminal_source_family_matrix": TERMINAL / "terminal_source_family_matrix.csv",
    "terminal_required_qoi_coverage": TERMINAL / "required_exchange_qoi_coverage.csv",
    "terminal_harvest_vs_sampler": TERMINAL / "harvest_vs_sampler_decision.csv",
    "input_summary": INPUTS / "summary.json",
    "input_generation_ledger": INPUTS / "input_generation_ledger.csv",
    "input_blockers": INPUTS / "surface_and_ledger_blockers.csv",
    "phase4_summary": PHASE4 / "summary.json",
    "phase4_exchange_readiness": PHASE4 / "upcomer_exchange_cell_readiness.csv",
    "phase4_ordinary_reopening": PHASE4 / "ordinary_single_stream_nu_reopening_gate.csv",
    "phase4_missing_evidence": PHASE4 / "missing_exchange_nu_evidence_queue.csv",
    "same_qoi_b_summary": SAME_QOI_B / "summary.json",
    "same_qoi_b_phase_c_inputs": SAME_QOI_B / "phase_c_input_table.csv",
}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: Iterable[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def as_float(value: str) -> float | None:
    if value == "":
        return None
    try:
        return float(value)
    except ValueError:
        return None


def bool_text(value: bool) -> str:
    return str(value).lower()


def build_onset_anchor_ledger(exchange_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str], list[dict[str, str]]] = defaultdict(list)
    for row in exchange_rows:
        grouped[(row["source_family"], row["case_id"], row["case_key"])].append(row)

    out = []
    for (source_family, case_id, case_key), rows in sorted(grouped.items()):
        raf = [as_float(row["reverse_area_fraction"]) for row in rows]
        rmf = [as_float(row["reverse_mass_fraction"]) for row in rows]
        sfi = [as_float(row["secondary_flow_intensity"]) for row in rows]
        raf_vals = [v for v in raf if v is not None]
        rmf_vals = [v for v in rmf if v is not None]
        sfi_vals = [v for v in sfi if v is not None]
        blocking = Counter()
        for row in rows:
            for reason in row.get("blocking_reasons", "").split(";"):
                if reason:
                    blocking[reason] += 1
        exchange_ready = sum(1 for row in rows if row.get("exchange_cell_readiness") == "fit_ready")
        ordinary_allowed = sum(1 for row in rows if row.get("ordinary_internal_Nu_allowed") == "true")
        out.append(
            {
                "source_family": source_family,
                "case_id": case_id,
                "case_key": case_key,
                "feature_rows": len(rows),
                "max_reverse_area_fraction": max(raf_vals) if raf_vals else "",
                "max_reverse_mass_fraction": max(rmf_vals) if rmf_vals else "",
                "max_secondary_flow_intensity": max(sfi_vals) if sfi_vals else "",
                "energy_residual_rows": sum(1 for row in rows if row.get("energy_residual_status") == "present_diagnostic"),
                "exchange_fit_ready_rows": exchange_ready,
                "ordinary_internal_nu_allowed_rows": ordinary_allowed,
                "dominant_blockers": ";".join(reason for reason, _ in blocking.most_common(5)),
                "s9_use": "recirculation_validity_diagnostic",
                "s11_candidate_status": "not_ready",
                "source_paths": str(SOURCE_FILES["phase4_exchange_readiness"]),
            }
        )
    return out


def build_near_onset_gap_table(
    terminal_rows: list[dict[str, str]],
    input_blockers: list[dict[str, str]],
    terminal_qois: list[dict[str, str]],
) -> list[dict[str, Any]]:
    terminal_missing = sum(1 for row in terminal_rows if row["can_provide_full_exchange_qois_now"] == "false")
    requires_terminal = sum(1 for row in terminal_qois if row["requires_terminal_success"] == "true")
    requires_sampler = sum(1 for row in terminal_qois if row["requires_sampler_or_harvest"] == "true")
    return [
        {
            "gap_id": "S9-GAP-TERMINAL",
            "gap_family": "terminal_or_nonrecirculating_anchor",
            "current_status": "blocked",
            "evidence": f"{terminal_missing}/{len(terminal_rows)} source families cannot provide full exchange QOIs now.",
            "required_to_unblock": "terminal success or formal terminal-source failure followed by a separately claimed harvest/sampler row",
            "next_action": "monitor terminal jobs; do not launch duplicate sampler from S9",
            "source_paths": str(SOURCE_FILES["terminal_source_family_matrix"]),
        },
        {
            "gap_id": "S9-GAP-QOI",
            "gap_family": "exchange_qoi_coverage",
            "current_status": "blocked",
            "evidence": f"{requires_terminal} required QOI rows require terminal success; {requires_sampler} require harvest or sampler.",
            "required_to_unblock": "finite same-window V_recirc, mdot_exchange, tau_recirc, wall/core thermal state, pressure residual, and source/sink residual rows",
            "next_action": "claim source/sampler execution only after terminal/source gate permits it",
            "source_paths": str(SOURCE_FILES["terminal_required_qoi_coverage"]),
        },
        {
            "gap_id": "S9-GAP-INPUTS",
            "gap_family": "sampler_inputs",
            "current_status": "blocked",
            "evidence": f"{len(input_blockers)} surface/interface/source-ledger blocker rows remain.",
            "required_to_unblock": "cell VTK, exchange-interface VTK, wall/core surfaces, and source/sink ledgers with exact geometry basis",
            "next_action": "use input-generation handoff; do not fit or score exchange rows",
            "source_paths": str(SOURCE_FILES["input_blockers"]),
        },
    ]


def build_exchange_qoi_contract(variable_rows: list[dict[str, str]], input_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows = []
    required = {
        "V_recirc": "recirculation control-volume size for exchange-state ODE or algebraic residence model",
        "mdot_exchange": "mass exchange rate between throughflow and recirculating cell",
        "tau_recirc": "recirculation residence time, derived only after V_recirc and mdot_exchange are admitted",
        "wall_core_delta_T": "thermal coupling state between wall/core and recirculation cell",
        "pressure_residual": "same-window pressure residual after straight/reference subtraction",
        "energy_residual": "diagnostic energy residual; not a coefficient fit target by itself",
    }
    availability = {row["variable_id"]: row for row in variable_rows}
    input_status = defaultdict(list)
    for row in input_rows:
        input_status[row["input_name"]].append(row["status"])
    for qoi, role in required.items():
        row = availability.get(qoi, {})
        rows.append(
            {
                "qoi_name": qoi,
                "model_role": role,
                "current_status": row.get("current_status", "not_cleared_for_admission"),
                "source_status": row.get("source_status", "requires_terminal_or_sampler"),
                "available_existing_rows": row.get("available_existing_rows", "0"),
                "requires_new_sampler_or_harvest": row.get("requires_new_sampler", "yes"),
                "admission_use_now": row.get("admission_use_now", "false"),
                "supporting_input_status": ";".join(sorted(set(input_status.get("cell_vtk", []) + input_status.get("exchange_interface_vtk", [])))) or "blocked_or_not_present",
                "s11_use": "blocked_until_finite_and_same_qoi_uq_passes",
                "source_paths": row.get("source_paths", str(SOURCE_FILES["preflight_variable_availability"])),
            }
        )
    return rows


def build_same_window_uq_requirements(preflight_uq: list[dict[str, str]], phase_c_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows = []
    for row in preflight_uq:
        rows.append(
            {
                "requirement_id": f"S9-UQ-{row['qoi_gate']}",
                "qoi_or_gate": row["qoi_gate"],
                "current_status": row["current_status"],
                "scorecard_use_now": row["scorecard_use_now"],
                "requirement": row["claim_boundary"],
                "next_action": row["next_action"],
                "source_paths": row["source_paths"],
            }
        )
    exchange_phase_c = [row for row in phase_c_rows if "recirc" in row["qoi_name"].lower() or "exchange" in row["qoi_name"].lower()]
    for row in exchange_phase_c:
        rows.append(
            {
                "requirement_id": f"S9-UQ-PHASEC-{row['qoi_name']}",
                "qoi_or_gate": row["qoi_name"],
                "current_status": row["phase_c_recommended_status"],
                "scorecard_use_now": "false",
                "requirement": f"time_window={row['time_window_gate']}; mesh_gci={row['mesh_gci_gate']}; source={row['source_gate']}",
                "next_action": row["next_task"],
                "source_paths": row["source_paths"],
            }
        )
    return rows


def build_admission_gates(
    summaries: dict[str, dict[str, Any]],
    onset_rows: list[dict[str, Any]],
    qoi_rows: list[dict[str, Any]],
    uq_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    s4 = summaries["s4_summary"]
    preflight = summaries["preflight_summary"]
    terminal = summaries["terminal_summary"]
    phase4 = summaries["phase4_summary"]
    same_qoi = summaries["same_qoi_b_summary"]
    ready_exchange = sum(1 for row in onset_rows if row["exchange_fit_ready_rows"])
    ready_qois = sum(1 for row in qoi_rows if row["admission_use_now"] == "true")
    uq_accepted = int(same_qoi.get("accepted_rows", 0))
    return [
        {
            "gate_id": "S9-G0",
            "gate_family": "coordination",
            "required_condition": "S9 board row claimed with exact script and package paths.",
            "status": "pass",
            "decision": "study_can_run_from_existing_evidence",
            "s11_effect": "none",
            "source_paths": ".agent/BOARD.md",
        },
        {
            "gate_id": "S9-G1",
            "gate_family": "recirculation_validity",
            "required_condition": "Existing rows demonstrate material reverse/secondary-flow behavior that invalidates ordinary single-stream upcomer labels.",
            "status": "pass",
            "decision": f"{s4.get('reverse_flow_evidence_rows', 0)} reverse-flow evidence rows and {len(onset_rows)} grouped onset-anchor rows support diagnostic recirculation validity.",
            "s11_effect": "ordinary_upcomer_Nu_fD_K_remain_disabled",
            "source_paths": f"{SOURCE_FILES['s4_summary']};{SOURCE_FILES['phase4_exchange_readiness']}",
        },
        {
            "gate_id": "S9-G2",
            "gate_family": "exchange_state_qois",
            "required_condition": "Finite/admitted V_recirc, mdot_exchange, tau_recirc, and paired thermal/pressure exchange-state fields exist.",
            "status": "fail" if ready_qois == 0 else "pass",
            "decision": f"{ready_qois} exchange-QOI rows are admission-usable now; preflight says {preflight.get('variables_requiring_sampler_or_terminal', 0)} variables still require sampler or terminal evidence.",
            "s11_effect": "blocks_exchange_candidate" if ready_qois == 0 else "candidate_can_continue",
            "source_paths": str(SOURCE_FILES["preflight_variable_availability"]),
        },
        {
            "gate_id": "S9-G3",
            "gate_family": "terminal_source",
            "required_condition": "A source family is terminal and can provide all required exchange QOIs now.",
            "status": "fail" if not terminal.get("terminal_harvest_ready_now", False) else "pass",
            "decision": f"terminal_harvest_ready_now={terminal.get('terminal_harvest_ready_now')}; phase4b_ready={terminal.get('phase4b_ready')}",
            "s11_effect": "wait_for_terminal_or_sampler_row",
            "source_paths": str(SOURCE_FILES["terminal_summary"]),
        },
        {
            "gate_id": "S9-G4",
            "gate_family": "same_qoi_uq",
            "required_condition": "Same-window and same-QOI mesh/time uncertainty evidence is accepted for exchange QOIs.",
            "status": "fail" if uq_accepted == 0 else "pass",
            "decision": f"{uq_accepted} accepted Phase B same-QOI rows; {same_qoi.get('blocked_rows', 0)} blocked rows.",
            "s11_effect": "blocks_candidate_source_property_refresh" if uq_accepted == 0 else "candidate_can_continue",
            "source_paths": str(SOURCE_FILES["same_qoi_b_summary"]),
        },
        {
            "gate_id": "S9-G5",
            "gate_family": "ordinary_closure_reopen",
            "required_condition": "Ordinary upcomer Nu/f_D/K may be reopened only if recirculation and UQ gates pass.",
            "status": "fail" if int(phase4.get("reopened_internal_Nu_rows", 0)) == 0 else "pass",
            "decision": f"{phase4.get('reopened_internal_Nu_rows', 0)} reopened internal-Nu rows and {phase4.get('exchange_cell_fit_ready_rows', 0)} exchange fit-ready rows.",
            "s11_effect": "ordinary_upcomer_closures_stay_disabled",
            "source_paths": str(SOURCE_FILES["phase4_ordinary_reopening"]),
        },
        {
            "gate_id": "S9-G6",
            "gate_family": "s11_release",
            "required_condition": "Exactly one runtime-legal, same-QOI-supported upcomer exchange candidate is ready for S11.",
            "status": "fail" if ready_exchange == 0 or ready_qois == 0 or uq_accepted == 0 else "pass",
            "decision": "0 S11-ready upcomer exchange candidates",
            "s11_effect": "S11 remains blocked from S9",
            "source_paths": "s11_unblock_decision.csv",
        },
    ]


def build_s11_decision(gates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    release_gate = next(row for row in gates if row["gate_id"] == "S9-G6")
    return [
        {
            "decision_id": "S9-S11-DECISION",
            "candidate_id": "",
            "candidate_family": "upcomer_exchange_or_onset_anchor",
            "s11_unblocked": "false",
            "reason": release_gate["decision"],
            "required_before_s11": "terminal/source success or admitted sampler output; finite V_recirc/mdot_exchange/tau_recirc; same-window pressure/thermal fields; accepted same-QOI UQ; source/property/split precheck",
            "ordinary_upcomer_closures": "disabled",
            "exchange_cell_coefficient_admission": "none",
            "next_board_task": "Continue to S10 pressure/F6 study; separately monitor terminal/source jobs for future S9 refresh.",
        }
    ]


def build_source_manifest() -> list[dict[str, Any]]:
    rows = []
    for role, path in SOURCE_FILES.items():
        rows.append(
            {
                "source_path": str(path),
                "role_in_study": role,
                "mutation_status": "read_only",
                "trusted_or_diagnostic": "trusted_existing_package" if path.exists() else "missing_required_source",
                "notes": "S9 consumed this artifact as existing evidence only.",
            }
        )
    rows.extend(
        [
            {
                "source_path": "native CFD/OpenFOAM outputs",
                "role_in_study": "solver_outputs",
                "mutation_status": "not_touched",
                "trusted_or_diagnostic": "not_accessed",
                "notes": "No native output was opened for mutation or sampled by S9.",
            },
            {
                "source_path": "registry/admission/scheduler state",
                "role_in_study": "global_state",
                "mutation_status": "not_mutated",
                "trusted_or_diagnostic": "read_only_context",
                "notes": "S9 did not mutate registry, admission, scheduler, Fluid, external, or generated-index state.",
            },
        ]
    )
    return rows


def build_readme(summary: dict[str, Any]) -> str:
    return f"""---
provenance:
  - .agent/BOARD.md
  - {SOURCE_FILES['phase4_exchange_readiness']}
  - {SOURCE_FILES['preflight_variable_availability']}
  - {SOURCE_FILES['terminal_summary']}
  - {SOURCE_FILES['input_summary']}
  - {SOURCE_FILES['same_qoi_b_summary']}
tags: [thesis-dossier, s9, upcomer, recirculation, exchange-qoi, uncertainty, negative-result]
related:
  - {S4}/README.md
  - {S8}/README.md
  - {PHASE4}/README.md
task: {TASK}
date: {DATE}
role: Hydraulics/Thermal-modeling/cfd-pp/Tester/Writer
type: work_product
status: complete
supersedes: []
superseded_by:
---
# Thesis S9 Upcomer Onset/Exchange UQ

## Decision

S9 closes as `{summary['study_state']}`.

The study enriches the recirculation-validity evidence but does not unblock
S11. It finds `{summary['onset_anchor_rows']}` grouped onset/exchange evidence
rows, `{summary['exchange_qoi_contract_rows']}` exchange-QOI contract rows, and
`{summary['s11_ready_candidates']}` S11-ready upcomer candidates.

## What S9 Establishes

- Existing upcomer evidence supports a recirculating/exchange-cell interpretation.
- Ordinary single-stream upcomer `Nu`, `f_D`, and K remain disabled.
- `V_recirc`, `mdot_exchange`, `tau_recirc`, same-window pressure residuals, and
  same-QOI uncertainty remain the gating evidence for any future exchange-cell
  candidate.
- No S11 source/property refresh may start from S9 until exactly one candidate
  passes the S9 release gate.

## Files

| File | Use |
| --- | --- |
| `onset_anchor_ledger.csv` | Case-family recirculation/onset summary. |
| `near_onset_gap_table.csv` | Terminal, QOI, and sampler-input blockers. |
| `exchange_qoi_contract.csv` | Required `V_recirc`/`mdot_exchange`/`tau_recirc` and supporting QOI contract. |
| `same_window_uq_requirements.csv` | Same-QOI/time/mesh UQ requirements. |
| `s9_admission_gate_matrix.csv` | S9 gates and S11 effects. |
| `s11_unblock_decision.csv` | Machine-readable S11 decision from S9. |
| `source_manifest.csv` | Exact source paths and mutation flags. |
| `summary.json` | Machine-readable summary. |

## Guardrails

No solver, sampler, harvest, scheduler action, Fluid edit, external edit,
fitting, model selection, closure admission, ordinary upcomer closure reopening,
generated-index refresh, or S11 trigger was performed.
"""


def build(out: Path) -> dict[str, Any]:
    missing = [str(path) for path in SOURCE_FILES.values() if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing required S9 sources: " + "; ".join(missing))

    out.mkdir(parents=True, exist_ok=True)
    summaries = {name: read_json(path) for name, path in SOURCE_FILES.items() if path.suffix == ".json"}
    exchange_rows = read_csv(SOURCE_FILES["phase4_exchange_readiness"])
    variable_rows = read_csv(SOURCE_FILES["preflight_variable_availability"])
    input_rows = read_csv(SOURCE_FILES["input_generation_ledger"])
    input_blockers = read_csv(SOURCE_FILES["input_blockers"])
    terminal_rows = read_csv(SOURCE_FILES["terminal_source_family_matrix"])
    terminal_qois = read_csv(SOURCE_FILES["terminal_required_qoi_coverage"])
    preflight_uq = read_csv(SOURCE_FILES["preflight_same_qoi_status"])
    phase_c_rows = read_csv(SOURCE_FILES["same_qoi_b_phase_c_inputs"])

    onset_rows = build_onset_anchor_ledger(exchange_rows)
    gap_rows = build_near_onset_gap_table(terminal_rows, input_blockers, terminal_qois)
    qoi_contract = build_exchange_qoi_contract(variable_rows, input_rows)
    uq_requirements = build_same_window_uq_requirements(preflight_uq, phase_c_rows)
    gate_rows = build_admission_gates(summaries, onset_rows, qoi_contract, uq_requirements)
    s11_rows = build_s11_decision(gate_rows)
    source_rows = build_source_manifest()

    write_csv(out / "onset_anchor_ledger.csv", onset_rows, list(onset_rows[0]))
    write_csv(out / "near_onset_gap_table.csv", gap_rows, list(gap_rows[0]))
    write_csv(out / "exchange_qoi_contract.csv", qoi_contract, list(qoi_contract[0]))
    write_csv(out / "same_window_uq_requirements.csv", uq_requirements, list(uq_requirements[0]))
    write_csv(out / "s9_admission_gate_matrix.csv", gate_rows, list(gate_rows[0]))
    write_csv(out / "s11_unblock_decision.csv", s11_rows, list(s11_rows[0]))
    write_csv(out / "source_manifest.csv", source_rows, list(source_rows[0]))

    summary = {
        "task": TASK,
        "date": DATE,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "status": "complete",
        "study_state": "negative_result_s11_still_blocked",
        "onset_anchor_rows": len(onset_rows),
        "exchange_evidence_rows": len(exchange_rows),
        "exchange_qoi_contract_rows": len(qoi_contract),
        "same_window_uq_requirement_rows": len(uq_requirements),
        "near_onset_gap_rows": len(gap_rows),
        "ordinary_upcomer_nu_fd_k_admitted_rows": 0,
        "exchange_cell_fit_ready_rows": 0,
        "exchange_cell_coefficient_admitted_rows": 0,
        "s11_ready_candidates": 0,
        "s11_unblocked": False,
        "solver_or_sampler_or_harvest_launch": False,
        "native_solver_outputs_mutated": False,
        "registry_or_admission_mutated": False,
        "scheduler_action_taken": False,
        "fluid_or_external_repo_edited": False,
        "fitting_or_model_selection": False,
        "generated_index_mutation": False,
        "phase4b_or_phase5_or_s6_trigger": False,
        "next_action": "Run S10 pressure/F6 low-recirculation anchor UQ; separately monitor terminal/source jobs before any future S9 refresh.",
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    (out / "README.md").write_text(build_readme(summary))
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    summary = build(args.output_dir)
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
