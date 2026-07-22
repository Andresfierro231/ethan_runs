#!/usr/bin/env python3
"""Build the thesis thermal accounting traceability evidence packet.

This is an evidence reducer only. It copies and normalizes existing ledgers so
external thesis writing can cite heat-path ownership without turning diagnostic
CFD wall heat or validation temperatures into runtime inputs.
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


TASK_ID = "TODO-THESIS-STUDY-THERMAL-ACCOUNTING-TRACEABILITY-EVIDENCE-PACKET-2026-07-22"
OUT = WORKSPACE_ROOT / (
    "work_products/2026-07/2026-07-22/"
    "2026-07-22_thesis_study_thermal_accounting_traceability_evidence_packet"
)

SOURCES = {
    "phase0": WORKSPACE_ROOT / "work_products/2026-07/2026-07-21/2026-07-21_heatloss_phase_0_baseline_release_gate",
    "phase1": WORKSPACE_ROOT / "work_products/2026-07/2026-07-21/2026-07-21_heatloss_phase_1_external_bc_radiation_integration",
    "phase2": WORKSPACE_ROOT / "work_products/2026-07/2026-07-21/2026-07-21_heatloss_phase_2_split_heat_loss_evidence",
    "phase3": WORKSPACE_ROOT / "work_products/2026-07/2026-07-21/2026-07-21_heatloss_phase_3_wall_test_section_model_score",
    "phase4": WORKSPACE_ROOT / "work_products/2026-07/2026-07-21/2026-07-21_heatloss_phase_4_upcomer_exchange_and_internal_nu_gate",
    "phase5": WORKSPACE_ROOT / "work_products/2026-07/2026-07-21/2026-07-21_heatloss_phase_5_frozen_scorecard_and_thesis_handoff",
    "phase_h2": WORKSPACE_ROOT / "work_products/2026-07/2026-07-21/2026-07-21_fluid_extbc_phase_h2_passive_heat_loss_attribution",
    "setup_source": WORKSPACE_ROOT / "work_products/2026-07/2026-07-21/2026-07-21_fluid_setup_known_source_sink_runtime_contract",
    "n3": WORKSPACE_ROOT / "work_products/2026-07/2026-07-22/2026-07-22_thesis_n3_thermal_residual_owner_train_ablation",
    "m2": WORKSPACE_ROOT / "work_products/2026-07/2026-07-22/2026-07-22_m2_passive_wall_test_section_source_bounded_repair_gate",
    "mf08": WORKSPACE_ROOT / "work_products/2026-07/2026-07-22/2026-07-22_mf08_signed_wall_flux_developing_thermal_branches",
    "signed_wall_flux": WORKSPACE_ROOT / "work_products/2026-07/2026-07-22/2026-07-22_mf_signed_wall_flux_thermal_development_gate",
    "radiation_capability": WORKSPACE_ROOT / "work_products/2026-07/2026-07-21/2026-07-21_1d_radiation_capability",
    "litrev_split": WORKSPACE_ROOT / "work_products/2026-07/2026-07-21/2026-07-21_litrev_split_junction_storage_radiation_extraction",
}


def rel(path: Path) -> str:
    return relative_to_workspace(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def as_float(value: str) -> float:
    if value == "":
        return 0.0
    return float(value)


def require_sources() -> None:
    required = [
        SOURCES["phase0"] / "summary.json",
        SOURCES["phase0"] / "heat_path_release_gate.csv",
        SOURCES["phase1"] / "radiation_semantics_audit.csv",
        SOURCES["phase2"] / "summary.json",
        SOURCES["phase2"] / "heat_path_evidence_matrix.csv",
        SOURCES["phase2"] / "split_junction_stub_heat_rows.csv",
        SOURCES["phase2"] / "missing_field_queue.csv",
        SOURCES["phase3"] / "summary.json",
        SOURCES["phase3"] / "runtime_thermal_input_audit.csv",
        SOURCES["phase3"] / "wall_test_section_candidate_gate_scorecard.csv",
        SOURCES["phase4"] / "summary.json",
        SOURCES["phase4"] / "heat_path_modeling_contract.csv",
        SOURCES["phase_h2"] / "summary.json",
        SOURCES["phase_h2"] / "source_sink_coupling_matrix.csv",
        SOURCES["phase_h2"] / "segment_heat_loss_sweep.csv",
        SOURCES["setup_source"] / "summary.json",
        SOURCES["setup_source"] / "setup_known_source_contract.csv",
        SOURCES["setup_source"] / "source_property_gate.csv",
        SOURCES["n3"] / "thermal_residual_ablation_table.csv",
        SOURCES["m2"] / "runtime_legality_matrix.csv",
        SOURCES["m2"] / "wall_test_section_residual_owner_split.csv",
        SOURCES["signed_wall_flux"] / "summary.json",
        SOURCES["signed_wall_flux"] / "residual_owner_decomposition_table.csv",
        SOURCES["signed_wall_flux"] / "runtime_legality_audit.csv",
    ]
    missing = [rel(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("missing required thermal accounting sources: " + "; ".join(missing))


def heat_path_ledger() -> list[dict[str, Any]]:
    rows = []
    for row in read_csv(SOURCES["phase0"] / "heat_path_release_gate.csv"):
        rows.append(
            {
                "heat_path": row["heat_path"],
                "current_best_evidence_package": row["current_best_evidence_package"],
                "executable_status": row["executable_status"],
                "score_admission_status": row["score_admission_status"],
                "runtime_allowed_inputs": row["runtime_allowed_inputs"],
                "forbidden_runtime_inputs": row["forbidden_runtime_inputs"],
                "source_property_label_status": row["source_property_label_status"],
                "uncertainty_status": row["uncertainty_status"],
                "residual_owner_policy": (
                    "forbidden runtime absorption; named owner lane only; never hide unresolved heat in internal Nu or runtime residual"
                    if row["heat_path"] != "residual"
                    else "forbidden runtime closure; diagnostic blocker accounting only; not a runtime closure"
                ),
                "consumer_allowed": row["consumer_allowed"],
            }
        )
    return rows


def source_sink_values() -> list[dict[str, Any]]:
    rows = []
    for row in read_csv(SOURCES["phase_h2"] / "source_sink_coupling_matrix.csv"):
        rows.append(
            {
                "case_id": row["case_id"],
                "split_role": row["split_role"],
                "source_segment_id": row["source_segment_id"],
                "physical_role": row["physical_role"],
                "setup_patch_or_group": row["setup_patch_or_group"],
                "setup_value_W": row["setup_value_W"],
                "runtime_allowed_now": row["runtime_allowed_now"],
                "provenance_class": row["provenance_class_after_recovery"],
                "coupling_decision": row["coupling_decision"],
                "protected_split_scoring_status": row["protected_split_scoring_status"],
                "next_gate": row["next_gate"],
                "claim_boundary": row["claim_boundary"],
            }
        )
    return rows


def diagnostic_heat_values() -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str], dict[str, Any]] = {}
    for row in read_csv(SOURCES["phase2"] / "heat_path_evidence_matrix.csv"):
        key = (row["case_id"], row["physical_role"], row["residual_owner"])
        item = grouped.setdefault(
            key,
            {
                "case_id": row["case_id"],
                "physical_role": row["physical_role"],
                "residual_owner": row["residual_owner"],
                "row_count": 0,
                "diagnostic_wallHeatFlux_W_sum": 0.0,
                "diagnostic_heat_to_fluid_W_sum": 0.0,
                "runtime_use": "diagnostic_only_for_traceability_forbidden_as_predictive_input",
                "quality_flags": set(),
            },
        )
        item["row_count"] += 1
        item["diagnostic_wallHeatFlux_W_sum"] += as_float(row["wallHeatFlux_diagnostic_W"])
        item["diagnostic_heat_to_fluid_W_sum"] += as_float(row["heat_to_fluid_diagnostic_W"])
        for flag in row["quality_flags"].split(";"):
            if flag:
                item["quality_flags"].add(flag)

    out = []
    for item in grouped.values():
        out.append(
            {
                **{key: value for key, value in item.items() if key != "quality_flags"},
                "quality_flags": ";".join(sorted(item["quality_flags"])),
            }
        )
    return sorted(out, key=lambda row: (row["case_id"], row["physical_role"], row["residual_owner"]))


def residual_owner_gate_matrix() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    n3_summary = read_json(SOURCES["n3"] / "summary.json")
    signed_summary = read_json(SOURCES["signed_wall_flux"] / "summary.json")
    phase4_summary = read_json(SOURCES["phase4"] / "summary.json")
    m2_summary = read_json(SOURCES["m2"] / "summary.json")

    rows.append(
        {
            "owner_family": "passive_wall_and_external_boundary",
            "evidence_package": rel(SOURCES["phase_h2"]),
            "support_status": read_json(SOURCES["phase_h2"] / "summary.json")["decision"],
            "candidate_reviewable_rows": m2_summary.get(
                "s11_reviewable_candidate_rows",
                m2_summary.get("s11_reviewable_candidates", 0),
            ),
            "admission_allowed": False,
            "runtime_release_allowed": False,
            "residual_policy": "forbidden release/admission: broad/global response is diagnostic; no source-bounded passive repair",
        }
    )
    rows.append(
        {
            "owner_family": "test_section_source_or_loss",
            "evidence_package": rel(SOURCES["phase3"]),
            "support_status": read_json(SOURCES["phase3"] / "summary.json")["phase3_release_status"],
            "candidate_reviewable_rows": read_json(SOURCES["phase3"] / "summary.json")["admitted_candidate_rows"],
            "admission_allowed": False,
            "runtime_release_allowed": False,
            "residual_policy": "forbidden release/admission: test-section rows remain diagnostic; realized test-section heat is forbidden at runtime",
        }
    )
    rows.append(
        {
            "owner_family": "junction_stub_heat",
            "evidence_package": rel(SOURCES["phase2"]),
            "support_status": "diagnostic_split_rows_only",
            "candidate_reviewable_rows": 0,
            "admission_allowed": False,
            "runtime_release_allowed": False,
            "residual_policy": "forbidden fit target: junction family heat is estimated from grouped wallHeatFlux and not independently bracketed",
        }
    )
    rows.append(
        {
            "owner_family": "radiation",
            "evidence_package": rel(SOURCES["phase1"]),
            "support_status": "schema_and_policy_ready_no_separate_qr",
            "candidate_reviewable_rows": 0,
            "admission_allowed": False,
            "runtime_release_allowed": False,
            "residual_policy": "forbidden inference: predictive radiation requires setup emissivity/Tsur/area and solved surface temperature; do not double count wallHeatFlux replay",
        }
    )
    rows.append(
        {
            "owner_family": "upcomer_exchange_and_internal_Nu",
            "evidence_package": rel(SOURCES["phase4"]),
            "support_status": "upcomer_exchange_blocked_internal_Nu_closed",
            "candidate_reviewable_rows": phase4_summary["exchange_cell_fit_ready_rows"],
            "admission_allowed": False,
            "runtime_release_allowed": False,
            "residual_policy": "forbidden residual absorption: ordinary internal Nu has zero fit rows and cannot absorb exchange or heat residual",
        }
    )
    rows.append(
        {
            "owner_family": "signed_wall_flux_thermal_development",
            "evidence_package": rel(SOURCES["signed_wall_flux"]),
            "support_status": signed_summary["decision"],
            "candidate_reviewable_rows": signed_summary["candidate_reviewable_rows"],
            "admission_allowed": False,
            "runtime_release_allowed": False,
            "residual_policy": "forbidden release/admission: sign convention and owner decomposition are useful; source/property release is closed",
        }
    )
    rows.append(
        {
            "owner_family": "train_only_residual_ablation",
            "evidence_package": rel(SOURCES["n3"]),
            "support_status": n3_summary["decision"],
            "candidate_reviewable_rows": n3_summary["candidate_reviewable_rows"],
            "admission_allowed": False,
            "runtime_release_allowed": False,
            "residual_policy": "forbidden release/admission: train-only diagnostic; no validation/holdout/external scoring or candidate release",
        }
    )
    return rows


def runtime_forbidden_audit() -> list[dict[str, Any]]:
    forbidden = [
        ("realized CFD wallHeatFlux", "wallHeatFlux is post-solve diagnostic/replay evidence only"),
        ("CFD mdot", "flow state is a predicted QOI or solver result, not a setup input"),
        ("imposed CFD cooler duty", "cooler/HX removal must come from setup-facing contract before use"),
        ("realized test-section heat", "test-section source/loss remains diagnostic unless independently source released"),
        ("validation temperatures", "TP/TW target temperatures are residual evidence only"),
        ("hidden residual multiplier", "residual owner terms must remain explicit ledgers"),
        ("internal Nu residual absorption", "Nu cannot absorb heater/cooler/passive/radiation/storage/exchange residuals"),
    ]
    rows = []
    for item, reason in forbidden:
        rows.append(
            {
                "forbidden_input": item,
                "runtime_allowed": False,
                "fit_allowed": False,
                "diagnostic_allowed": True,
                "reason": f"forbidden runtime/fit use: {reason}",
                "source_paths": (
                    f"{rel(SOURCES['phase0'] / 'heat_path_release_gate.csv')};"
                    f"{rel(SOURCES['phase3'] / 'runtime_thermal_input_audit.csv')};"
                    f"{rel(SOURCES['signed_wall_flux'] / 'runtime_legality_audit.csv')}"
                ),
            }
        )
    return rows


def missing_setup_fields() -> list[dict[str, Any]]:
    rows = []
    for row in read_csv(SOURCES["phase2"] / "missing_field_queue.csv"):
        rows.append(
            {
                "missing_field_id": row["missing_field_id"],
                "affected_lanes": row["affected_lanes"],
                "current_status": row["current_status"],
                "what_not_to_infer": row["what_not_to_infer"],
                "next_action": row["next_action"],
                "source_paths": row["source_paths"],
            }
        )
    return rows


def figure_table_targets() -> list[dict[str, Any]]:
    return [
        {
            "target_id": "thermal_accounting_traceability_ledger",
            "artifact": "thermal_accounting_traceability_ledger.csv",
            "writer_use": "chapter table listing heat owner, status, allowed inputs, forbidden inputs, and unresolved blocker",
            "caption_boundary": "Evidence/accounting only; no closure admission or runtime residual fit.",
        },
        {
            "target_id": "setup_source_sink_values",
            "artifact": "setup_source_sink_values.csv",
            "writer_use": "exact heater/cooler/test-section setup values by case and split role",
            "caption_boundary": "Setup-known metadata, not source/property release or final score.",
        },
        {
            "target_id": "diagnostic_heat_values",
            "artifact": "diagnostic_heat_values_by_case_role.csv",
            "writer_use": "diagnostic wall/source heat magnitudes by case, physical role, and residual owner",
            "caption_boundary": "Uses realized CFD wallHeatFlux as diagnostic trace only; forbidden as predictive runtime input.",
        },
        {
            "target_id": "runtime_forbidden_audit",
            "artifact": "runtime_forbidden_input_audit.csv",
            "writer_use": "claim-boundary table for runtime legality",
            "caption_boundary": "forbidden: Validation temperatures, CFD mdot, and realized heat terms cannot drive predictions.",
        },
        {
            "target_id": "residual_owner_gate_matrix",
            "artifact": "residual_owner_gate_matrix.csv",
            "writer_use": "shows why accounting proceeds before fitting",
            "caption_boundary": "Every owner remains diagnostic or blocked; residual is not hidden in internal Nu.",
        },
    ]


def source_manifest() -> list[dict[str, Any]]:
    rows = []
    for source_id, path in SOURCES.items():
        rows.append(
            {
                "source_id": source_id,
                "path": rel(path),
                "exists": path.exists(),
                "mutation_status": "read_only",
            }
        )
    return rows


def write_readme(summary: dict[str, Any]) -> None:
    text = f"""---
provenance:
  - {rel(SOURCES["phase0"] / "heat_path_release_gate.csv")}
  - {rel(SOURCES["phase2"] / "heat_path_evidence_matrix.csv")}
  - {rel(SOURCES["phase_h2"] / "source_sink_coupling_matrix.csv")}
  - {rel(SOURCES["signed_wall_flux"] / "residual_owner_decomposition_table.csv")}
tags: [thermal-accounting, traceability, source-sink, runtime-guardrails, no-fitting]
related:
  - .agent/status/2026-07-22_{TASK_ID}.md
  - .agent/journal/2026-07-22/thesis-study-thermal-accounting-traceability-evidence-packet.md
  - imports/2026-07-22_thesis_study_thermal_accounting_traceability_evidence_packet.json
task: {TASK_ID}
date: 2026-07-22
role: Thermal-modeling/Writer/Reviewer/Tester
type: work_product
status: complete
---
# Thermal Accounting Traceability Evidence Packet

Decision: `{summary["decision"]}`.

This packet keeps thermal work on accounting and ownership, not fitting. It
separates heater input, cooler/HX removal, passive wall losses, test-section
source/loss, junction/stub heat, radiation policy, storage absence, source/sink
metadata, upcomer exchange, internal Nu, and named residual lanes.

Key counts:

- Heat-path ledger rows: `{summary["heat_path_ledger_rows"]}`.
- Setup source/sink rows: `{summary["setup_source_sink_rows"]}`.
- Diagnostic heat-value rows: `{summary["diagnostic_heat_value_rows"]}`.
- Missing setup-field rows: `{summary["missing_setup_field_rows"]}`.
- Residual-owner gate rows: `{summary["residual_owner_gate_rows"]}`.
- Runtime-forbidden input rows: `{summary["runtime_forbidden_input_rows"]}`.

Primary outputs:

- `thermal_accounting_traceability_ledger.csv`
- `setup_source_sink_values.csv`
- `diagnostic_heat_values_by_case_role.csv`
- `passive_wall_segment_response.csv`
- `junction_stub_traceability_rows.csv`
- `missing_setup_fields.csv`
- `residual_owner_gate_matrix.csv`
- `runtime_forbidden_input_audit.csv`
- `figure_table_caption_targets.csv`
- `source_manifest.csv`
- `no_mutation_guardrails.csv`
- `summary.json`

Forbidden runtime-input audit: no realized CFD `wallHeatFlux`, CFD `mdot`,
imposed CFD cooler duty, realized test-section heat, or validation temperature
was released as a runtime input.
No fitting, protected scoring, source/property release, coefficient admission,
candidate freeze, solver/scheduler action, Fluid edit, native-output mutation,
registry/admission mutation, or residual absorption into internal `Nu` occurred.
"""
    (OUT / "README.md").write_text(text, encoding="utf-8")


def build(out: Path = OUT) -> dict[str, Any]:
    global OUT
    OUT = out
    ensure_dir(OUT)
    require_sources()

    heat_rows = heat_path_ledger()
    source_sink_rows = source_sink_values()
    diagnostic_rows = diagnostic_heat_values()
    passive_rows = read_csv(SOURCES["phase_h2"] / "segment_heat_loss_sweep.csv")
    junction_rows = read_csv(SOURCES["phase2"] / "split_junction_stub_heat_rows.csv")
    missing_rows = missing_setup_fields()
    residual_rows = residual_owner_gate_matrix()
    runtime_rows = runtime_forbidden_audit()
    figure_rows = figure_table_targets()
    manifest_rows = source_manifest()

    no_mutation = [
        {"guardrail": "native_output_mutation", "value": False},
        {"guardrail": "registry_or_admission_mutation", "value": False},
        {"guardrail": "scheduler_action", "value": False},
        {"guardrail": "solver_postprocessing_sampler_harvest_uq_launch", "value": False},
        {"guardrail": "Fluid_or_external_repo_mutation", "value": False},
        {"guardrail": "thesis_current_or_latex_edit", "value": False},
        {"guardrail": "validation_holdout_external_scoring", "value": False},
        {"guardrail": "fitting_or_model_selection", "value": False},
        {"guardrail": "source_property_release", "value": False},
        {"guardrail": "runtime_wallHeatFlux_or_validation_temperature_release", "value": False},
        {"guardrail": "coefficient_admission", "value": False},
        {"guardrail": "candidate_freeze", "value": False},
        {"guardrail": "s11_s12_s13_s15_s6_trigger", "value": False},
        {"guardrail": "residual_absorbed_into_internal_nu", "value": False},
    ]

    csv_dump(OUT / "thermal_accounting_traceability_ledger.csv", list(heat_rows[0]), heat_rows)
    csv_dump(OUT / "setup_source_sink_values.csv", list(source_sink_rows[0]), source_sink_rows)
    csv_dump(OUT / "diagnostic_heat_values_by_case_role.csv", list(diagnostic_rows[0]), diagnostic_rows)
    csv_dump(OUT / "passive_wall_segment_response.csv", list(passive_rows[0]), passive_rows)
    csv_dump(OUT / "junction_stub_traceability_rows.csv", list(junction_rows[0]), junction_rows)
    csv_dump(OUT / "missing_setup_fields.csv", list(missing_rows[0]), missing_rows)
    csv_dump(OUT / "residual_owner_gate_matrix.csv", list(residual_rows[0]), residual_rows)
    csv_dump(OUT / "runtime_forbidden_input_audit.csv", list(runtime_rows[0]), runtime_rows)
    csv_dump(OUT / "figure_table_caption_targets.csv", list(figure_rows[0]), figure_rows)
    csv_dump(OUT / "source_manifest.csv", list(manifest_rows[0]), manifest_rows)
    csv_dump(OUT / "no_mutation_guardrails.csv", list(no_mutation[0]), no_mutation)

    total_setup_by_role: dict[str, float] = defaultdict(float)
    for row in source_sink_rows:
        total_setup_by_role[row["physical_role"]] += as_float(row["setup_value_W"])

    summary = {
        "task_id": TASK_ID,
        "generated_at": iso_timestamp(),
        "decision": "thermal_accounting_traceability_packet_ready_no_fit_no_runtime_leakage",
        "heat_path_ledger_rows": len(heat_rows),
        "setup_source_sink_rows": len(source_sink_rows),
        "diagnostic_heat_value_rows": len(diagnostic_rows),
        "passive_wall_segment_rows": len(passive_rows),
        "junction_stub_rows": len(junction_rows),
        "missing_setup_field_rows": len(missing_rows),
        "residual_owner_gate_rows": len(residual_rows),
        "runtime_forbidden_input_rows": len(runtime_rows),
        "figure_table_caption_targets": len(figure_rows),
        "setup_value_totals_by_role_W": dict(sorted(total_setup_by_role.items())),
        "runtime_wallHeatFlux_or_validation_temperature_release": False,
        "source_property_release": False,
        "coefficient_admission": False,
        "candidate_freeze": False,
        "validation_holdout_external_rows_scored": 0,
        "fitting_or_model_selection": False,
        "native_output_mutation": False,
        "registry_or_admission_mutation": False,
        "scheduler_action": False,
        "solver_sampler_harvest_uq_launched": False,
        "Fluid_or_external_repo_mutation": False,
        "thesis_current_or_latex_edit": False,
        "s11_s12_s13_s15_s6_trigger": False,
        "blocker_register_change": False,
        "generated_index_refresh": False,
        "residual_absorbed_into_internal_nu": False,
    }
    json_dump(OUT / "summary.json", summary)
    write_readme(summary)
    return summary


def main() -> int:
    summary = build()
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
