#!/usr/bin/env python3
"""Build AGENT-521 LitRev gate carryforward ledger."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


TASK = "AGENT-521"
DATE = "2026-07-17"
ROOT = Path(__file__).resolve().parents[2]
OUT_REL = Path("work_products/2026-07/2026-07-17/2026-07-17_litrev_gate_carryforward_ledger")
OUT = ROOT / OUT_REL

SOURCE_ENVELOPE_DIR = ROOT / "work_products/2026-07/2026-07-13/2026-07-13_litrev_source_envelope"
PROPERTY_DIR = ROOT / "work_products/2026-07/2026-07-13/2026-07-13_litrev_property_sensitivity"
RESET_DIR = ROOT / "work_products/2026-07/2026-07-13/2026-07-13_litrev_reset_named_losses"
HEAT_LOSS_DIR = ROOT / "work_products/2026-07/2026-07-13/2026-07-13_litrev_heat_loss_calibration"
CFD_VALIDITY_DIR = ROOT / "work_products/2026-07/2026-07-13/2026-07-13_litrev_cfd_validity_diagnostics"
ROADMAP_DIR = ROOT / "work_products/2026-07/2026-07-17/2026-07-17_research_studies_roadmap_and_today_start"

SOURCES = {
    "source_overlap_flags": SOURCE_ENVELOPE_DIR / "source_overlap_flags.csv",
    "branch_source_envelope": SOURCE_ENVELOPE_DIR / "branch_source_envelope.csv",
    "property_mode_matrix": PROPERTY_DIR / "property_mode_matrix.csv",
    "property_sensitivity_summary": PROPERTY_DIR / "property_sensitivity_summary.csv",
    "reset_distance_map": RESET_DIR / "reset_distance_map.csv",
    "named_pressure_loss_table": RESET_DIR / "named_pressure_loss_table.csv",
    "heat_closure_admission": HEAT_LOSS_DIR / "heat_closure_admission.csv",
    "separated_heat_loss_ledger": HEAT_LOSS_DIR / "separated_heat_loss_ledger.csv",
    "cfd_single_stream_validity": CFD_VALIDITY_DIR / "cfd_single_stream_validity.csv",
    "coefficient_naming_limits": CFD_VALIDITY_DIR / "coefficient_naming_limits.csv",
    "study_priority_matrix": ROADMAP_DIR / "study_priority_matrix.csv",
    "today_start_ledger": ROADMAP_DIR / "today_start_ledger.csv",
}

BRANCH_COLUMNS = [
    "case_id",
    "section",
    "source_overlap_summary",
    "source_bounded_promotion_status",
    "property_mode_requirement",
    "property_modes_seen",
    "reset_type",
    "hydraulic_reset_status",
    "L_over_D_from_reset",
    "pressure_loss_basis_status",
    "heat_loss_separation_status",
    "internal_Nu_status",
    "single_stream_validity",
    "coefficient_naming_limit",
    "fit_use_status",
    "carryforward_decision",
    "required_next_fields",
    "source_paths",
]

CONTRACT_COLUMNS = [
    "target_package",
    "consumer_lane",
    "required_gate_columns",
    "required_evidence_inputs",
    "acceptance_gate",
    "default_status_until_satisfied",
    "forbidden_shortcut",
    "source_paths",
]

SOURCE_CROSSWALK_COLUMNS = [
    "gate_family",
    "source_file",
    "rows",
    "key_status_counts",
    "carryforward_use",
    "must_not_infer",
]

GUARDRAIL_COLUMNS = ["guardrail_id", "applies_to", "reason", "required_label", "forbidden_label_or_action", "source_paths"]
MANIFEST_COLUMNS = ["source_id", "path", "exists", "role"]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT.resolve()))
    except ValueError:
        return str(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: Iterable[dict[str, Any]], columns: list[str]) -> int:
    materialized = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in materialized:
            writer.writerow({column: "" if row.get(column) is None else str(row.get(column, "")) for column in columns})
    return len(materialized)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def require_sources() -> None:
    missing = [rel(path) for path in SOURCES.values() if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing AGENT-521 source files: " + ", ".join(missing))


def counter_summary(values: Iterable[str]) -> str:
    counts = Counter(value or "blank" for value in values)
    return ";".join(f"{key}={counts[key]}" for key in sorted(counts))


def index_first(rows: list[dict[str, str]], key_fields: tuple[str, str], value_field: str) -> dict[tuple[str, str], dict[str, str]]:
    out: dict[tuple[str, str], dict[str, str]] = {}
    for row in rows:
        key = (row.get(key_fields[0], ""), row.get(key_fields[1], ""))
        if key not in out or row.get(value_field):
            out[key] = row
    return out


def build_branch_gate_summary() -> list[dict[str, Any]]:
    overlap = read_csv(SOURCES["source_overlap_flags"])
    prop = read_csv(SOURCES["property_mode_matrix"])
    reset = read_csv(SOURCES["reset_distance_map"])
    pressure = read_csv(SOURCES["named_pressure_loss_table"])
    heat = read_csv(SOURCES["heat_closure_admission"])
    validity = read_csv(SOURCES["cfd_single_stream_validity"])

    overlap_by_key: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in overlap:
        overlap_by_key[(row["case_id"], row["span"])].append(row)

    prop_modes_by_key: dict[tuple[str, str], set[str]] = defaultdict(set)
    for row in prop:
        prop_modes_by_key[(row["case_id"], row["span"])].add(row["property_mode"])

    reset_by_key = index_first(reset, ("case_id", "downstream_span"), "L_over_D_from_reset")
    pressure_by_key = index_first(pressure, ("case_id", "span_or_feature"), "pressure_basis")
    heat_by_key = index_first(heat, ("case_id", "one_d_segment"), "internal_Nu_admission")

    rows: list[dict[str, Any]] = []
    for row in validity:
        key = (row["case_id"], row["section"])
        overlap_rows = overlap_by_key.get(key, [])
        overlap_summary = counter_summary(r["overlap_status"] for r in overlap_rows)
        promote_count = sum(1 for r in overlap_rows if r.get("admission_recommendation") not in {"do_not_promote", "reference_only", ""})
        reset_row = reset_by_key.get(key, {})
        pressure_row = pressure_by_key.get(key, {})
        heat_row = heat_by_key.get(key, {})
        single_stream = row["single_stream_validity"]
        if single_stream != "single_stream_plausible":
            decision = "diagnostic_or_section_effective_only"
        elif heat_row.get("internal_Nu_admission", "missing_heat_loss_row") in {
            "blocked_from_absorbing_external_heat_loss",
            "missing_heat_loss_row",
        }:
            decision = "single_stream_candidate_but_thermal_fit_blocked"
        else:
            decision = "candidate_pending_source_property_pressure_heat_uq_gates"
        rows.append(
            {
                "case_id": row["case_id"],
                "section": row["section"],
                "source_overlap_summary": overlap_summary or "no_source_overlap_rows",
                "source_bounded_promotion_status": "no_active_source_promotion" if promote_count == 0 else f"gate_or_candidate_rows={promote_count}",
                "property_mode_requirement": "property_mode_label_required_before_any_fit",
                "property_modes_seen": ";".join(sorted(prop_modes_by_key.get(key, set()))) or "none",
                "reset_type": reset_row.get("reset_type", "missing_reset_row"),
                "hydraulic_reset_status": reset_row.get("hydraulic_reset_status", "missing_reset_row"),
                "L_over_D_from_reset": reset_row.get("L_over_D_from_reset", ""),
                "pressure_loss_basis_status": pressure_row.get("coefficient_naming_status", "missing_named_pressure_row"),
                "heat_loss_separation_status": heat_row.get("UA_or_emissivity_admission", "missing_heat_loss_row"),
                "internal_Nu_status": heat_row.get("internal_Nu_admission", "missing_heat_loss_row"),
                "single_stream_validity": single_stream,
                "coefficient_naming_limit": row["coefficient_naming_limit"],
                "fit_use_status": row["fit_use_status"],
                "carryforward_decision": decision,
                "required_next_fields": "property_mode;source_overlap_status;reset_distance;pressure_basis;velocity_basis;heat_path_separation;RAF;RMF;SVF;steady_window;mesh_time_UQ",
                "source_paths": ";".join(
                    [
                        rel(SOURCES["source_overlap_flags"]),
                        rel(SOURCES["property_mode_matrix"]),
                        rel(SOURCES["reset_distance_map"]),
                        rel(SOURCES["named_pressure_loss_table"]),
                        rel(SOURCES["heat_closure_admission"]),
                        rel(SOURCES["cfd_single_stream_validity"]),
                    ]
                ),
            }
        )
    return rows


def build_contract_rows() -> list[dict[str, Any]]:
    common = "case_id;section_or_segment;property_mode;source_overlap_status;provenance_author_title;runtime_input_audit;quality_flags"
    return [
        {
            "target_package": "terminal_anchor_harvest_and_F6_phi_Re",
            "consumer_lane": "hydraulic_f6",
            "required_gate_columns": common + ";Re;Pr;Ri;Gr;Ra;Gz;pressure_basis;RAF;RMF;SVF;steady_window;mesh_time_UQ",
            "required_evidence_inputs": "terminal high-heat/PM10 CFD reductions plus AGENT-505/512 anchor gates",
            "acceptance_gate": "ordinary F6 only if RAF < 0.01 and RMF < 0.01 with same-window pressure loss and holdout mdot guardrail",
            "default_status_until_satisfied": "blocked_no_ordinary_F6_fit",
            "forbidden_shortcut": "ordinary F6 fit from PM5, recirculating, or non-terminal rows",
            "source_paths": f"{rel(SOURCES['cfd_single_stream_validity'])};{rel(SOURCES['study_priority_matrix'])}",
        },
        {
            "target_package": "named_pressure_loss_or_reset_development_extraction",
            "consumer_lane": "hydraulic_pressure",
            "required_gate_columns": common + ";reset_type;L_over_D_from_reset;pressure_basis;velocity_basis;straight_loss_correction;development_or_recovery_basis;K_local;K_apparent;f_D_delta_p;UQ",
            "required_evidence_inputs": "reset_distance_map.csv; named_pressure_loss_table.csv; future admitted two-tap/plane pressure basis",
            "acceptance_gate": "no component/cluster/branch coefficient admitted without pressure basis, velocity basis, split, development/recovery, straight-loss subtraction, and UQ",
            "default_status_until_satisfied": "diagnostic_or_extraction_contract_only",
            "forbidden_shortcut": "universal K or hidden global friction multiplier",
            "source_paths": f"{rel(SOURCES['reset_distance_map'])};{rel(SOURCES['named_pressure_loss_table'])}",
        },
        {
            "target_package": "branchwise_internal_HTC_bakeoff",
            "consumer_lane": "thermal_internal_htc",
            "required_gate_columns": common + ";Nu_candidate;wall_bulk_deltaT;Gz;heat_path_separation;radiation_bound;single_stream_validity;recirculation_flag;temperature_residual_movement",
            "required_evidence_inputs": "source_overlap_flags.csv; property_mode_matrix.csv; heat_closure_admission.csv; cfd_single_stream_validity.csv",
            "acceptance_gate": "HTC candidate cannot improve temperature by absorbing external heat-loss residual or using recirculating rows as ordinary Nu evidence",
            "default_status_until_satisfied": "blocked_or_reference_only",
            "forbidden_shortcut": "global Nu or internal Nu fit before heat-loss/radiation separation",
            "source_paths": f"{rel(SOURCES['source_overlap_flags'])};{rel(SOURCES['heat_closure_admission'])};{rel(SOURCES['cfd_single_stream_validity'])}",
        },
        {
            "target_package": "CFD_reduction_validity_diagnostics",
            "consumer_lane": "cfd_admission",
            "required_gate_columns": common + ";U;T;wallHeatFlux;RAF;RMF;SVF;wall_core_deltaT;secondary_velocity_fraction;coefficient_naming_limit;steady_window;mesh_time_UQ",
            "required_evidence_inputs": "future terminal CFD postprocessing plus existing CFD validity naming policy",
            "acceptance_gate": "section-effective closure flagged when reverse/secondary flow is material",
            "default_status_until_satisfied": "diagnostic_until_full_validity_metrics_exist",
            "forbidden_shortcut": "ordinary f_D/K/Nu exported from material reverse-flow sections",
            "source_paths": f"{rel(SOURCES['cfd_single_stream_validity'])};{rel(SOURCES['coefficient_naming_limits'])}",
        },
        {
            "target_package": "wall_test_section_temperature_shape_candidate",
            "consumer_lane": "thermal_wall_forward_predictive",
            "required_gate_columns": common + ";heater_source_basis;wall_drive_selector;heat_path_separation;radiation_bound;runtime_forbidden_inputs;mdot_delta_vs_M3;all_probe_delta_vs_M3;TW_delta_vs_M3",
            "required_evidence_inputs": "AGENT-520/511/513 wall candidates plus heat-loss carryforward gates",
            "acceptance_gate": "candidate must improve mdot without worsening all-probe/TW RMSE versus M3 on validation/holdout",
            "default_status_until_satisfied": "freeze_blocked_no_wall_candidate_admitted",
            "forbidden_shortcut": "realized wallHeatFlux, CFD mdot, imposed cooler duty, or validation temperatures at runtime",
            "source_paths": f"{rel(SOURCES['heat_closure_admission'])};{rel(SOURCES['today_start_ledger'])}",
        },
        {
            "target_package": "final_predictive_scorecard_or_thesis_claim",
            "consumer_lane": "forward_model_thesis",
            "required_gate_columns": common + ";split_role;training_or_holdout_status;admission_status;blocker_status;caveat;uncertainty_status",
            "required_evidence_inputs": "all above gate ledgers plus final frozen prediction rows",
            "acceptance_gate": "claims must state evidence class, split, blocker status, and caveats; prediction rows cannot consume runtime-forbidden CFD outputs",
            "default_status_until_satisfied": "blocked_or_diagnostic_only",
            "forbidden_shortcut": "final predictive claim from diagnostic replay or missing frozen candidate rows",
            "source_paths": rel(SOURCES["study_priority_matrix"]),
        },
    ]


def build_source_crosswalk() -> list[dict[str, Any]]:
    specs = [
        ("source_envelope", "source_overlap_flags", "overlap_status", "source overlap status gates source-bounded closures", "inside status alone does not promote a closure"),
        ("property_sensitivity", "property_sensitivity_summary", "admission_summary", "property mode labels must travel with every fit/score row", "do not hide property sensitivity inside residual fit"),
        ("reset_named_losses", "reset_distance_map", "hydraulic_reset_status", "reset provenance and L/D support development sensitivity", "do not infer fully developed flow from long-looking branches"),
        ("named_pressure_losses", "named_pressure_loss_table", "coefficient_naming_status", "pressure and velocity basis guard named K/f rows", "do not use universal K"),
        ("heat_loss", "heat_closure_admission", "internal_Nu_admission", "external heat paths block internal Nu residual absorption", "do not tune Nu to absorb passive/jacket/radiation loss"),
        ("cfd_validity", "cfd_single_stream_validity", "single_stream_validity", "reverse and secondary flow decide ordinary vs section-effective labels", "do not export ordinary coefficients from recirculation"),
    ]
    rows = []
    for family, source_id, status_field, use, must_not in specs:
        path = SOURCES[source_id]
        data = read_csv(path)
        rows.append(
            {
                "gate_family": family,
                "source_file": rel(path),
                "rows": len(data),
                "key_status_counts": counter_summary(row.get(status_field, "") for row in data),
                "carryforward_use": use,
                "must_not_infer": must_not,
            }
        )
    return rows


def build_guardrails() -> list[dict[str, Any]]:
    return [
        {
            "guardrail_id": "no_pm5_ordinary_f6",
            "applies_to": "F6_phi_Re; terminal_anchor_harvest",
            "reason": "PM5 rows are material recirculation diagnostics with 0 ordinary scoreable rows.",
            "required_label": "diagnostic_recirculation_or_blocked_pending_terminal",
            "forbidden_label_or_action": "ordinary_F6_fit",
            "source_paths": rel(SOURCES["study_priority_matrix"]),
        },
        {
            "guardrail_id": "no_universal_K_or_global_f",
            "applies_to": "named_pressure_loss_or_reset_development_extraction",
            "reason": "LitRev supports named pressure basis, geometry, velocity basis, split, and UQ, not universal multipliers.",
            "required_label": "component_or_cluster_or_branch_apparent_with_basis",
            "forbidden_label_or_action": "universal_K; hidden_global_friction_multiplier",
            "source_paths": rel(SOURCES["named_pressure_loss_table"]),
        },
        {
            "guardrail_id": "no_internal_Nu_heat_loss_absorption",
            "applies_to": "branchwise_internal_HTC_bakeoff; wall_test_section_temperature_shape_candidate",
            "reason": "Jacket, passive, radiation, heater efficiency, wall/storage, and residual paths must stay separated.",
            "required_label": "heat_path_separated_or_blocked",
            "forbidden_label_or_action": "internal_Nu_fit_absorbs_external_heat_loss",
            "source_paths": rel(SOURCES["heat_closure_admission"]),
        },
        {
            "guardrail_id": "recirculation_labels",
            "applies_to": "CFD_reduction_validity_diagnostics; all closure tables",
            "reason": "Material reverse or secondary flow invalidates single-stream ordinary coefficient names.",
            "required_label": "section_effective_or_diagnostic",
            "forbidden_label_or_action": "ordinary_f_D_K_Nu_from_material_reverse_flow",
            "source_paths": rel(SOURCES["coefficient_naming_limits"]),
        },
        {
            "guardrail_id": "runtime_legality",
            "applies_to": "final_predictive_scorecard_or_thesis_claim",
            "reason": "Predictive rows must not consume validation temperatures or realized CFD outputs at runtime.",
            "required_label": "runtime_input_audit_pass",
            "forbidden_label_or_action": "realized_wallHeatFlux; CFD_mdot; imposed_cooler_duty; validation_temperature_runtime_input",
            "source_paths": rel(SOURCES["today_start_ledger"]),
        },
    ]


def build_source_manifest() -> list[dict[str, Any]]:
    return [
        {"source_id": key, "path": rel(path), "exists": path.exists(), "role": "read-only carryforward source"}
        for key, path in SOURCES.items()
    ]


def write_readme(path: Path, summary: dict[str, Any]) -> None:
    path.write_text(
        f"""---
provenance:
  - {rel(SOURCES['source_overlap_flags'])}
  - {rel(SOURCES['property_mode_matrix'])}
  - {rel(SOURCES['reset_distance_map'])}
  - {rel(SOURCES['heat_closure_admission'])}
  - {rel(SOURCES['cfd_single_stream_validity'])}
tags: [litrev-gates, carryforward-ledger, closure-ledger, source-envelope]
related:
  - .agent/status/2026-07-17_AGENT-521.md
  - .agent/journal/2026-07-17/litrev-gate-carryforward-ledger.md
task: {TASK}
date: {DATE}
role: Literature-synthesis/Implementer/Tester/Writer
type: work_product
status: complete
---
# LitRev Gate Carryforward Ledger

Generated: `{summary['generated_at_utc']}`

## Decision

This package turns the LitRev gates into required columns and default statuses
for future F6, named-pressure, internal-HTC, CFD-reduction, wall-model, and final
scorecard work. It does not promote a closure.

## Outputs

- `branch_gate_carryforward_summary.csv`
- `target_package_gate_contract.csv`
- `source_gate_crosswalk.csv`
- `fit_and_runtime_guardrails.csv`
- `source_manifest.csv`
- `summary.json`

## Counts

- Branch/section gate rows: `{summary['branch_gate_rows']}`.
- Target package contract rows: `{summary['contract_rows']}`.
- Source gate crosswalk rows: `{summary['source_crosswalk_rows']}`.
- Guardrail rows: `{summary['guardrail_rows']}`.
- Single-stream plausible rows: `{summary['single_stream_plausible_rows']}`.
- Diagnostic/section-effective rows: `{summary['section_effective_or_diagnostic_rows']}`.

## Guardrails

No native CFD outputs, registry/admission state, scheduler state, external Fluid
files, generated index files, thesis-dossier files, or active-agent scoped
artifacts were mutated. This is a carryforward contract, not a fit, run, harvest,
or admission change.
""",
        encoding="utf-8",
    )


def build_package(out: Path = OUT) -> dict[str, Any]:
    require_sources()
    out.mkdir(parents=True, exist_ok=True)

    branch_rows = build_branch_gate_summary()
    contract_rows = build_contract_rows()
    crosswalk_rows = build_source_crosswalk()
    guardrail_rows = build_guardrails()
    manifest_rows = build_source_manifest()

    decision_counts = Counter(row["carryforward_decision"] for row in branch_rows)
    summary = {
        "task": TASK,
        "date": DATE,
        "generated_at_utc": utc_now(),
        "output_dir": rel(out),
        "branch_gate_rows": len(branch_rows),
        "contract_rows": len(contract_rows),
        "source_crosswalk_rows": len(crosswalk_rows),
        "guardrail_rows": len(guardrail_rows),
        "source_rows": len(manifest_rows),
        "single_stream_plausible_rows": sum(1 for row in branch_rows if row["single_stream_validity"] == "single_stream_plausible"),
        "section_effective_or_diagnostic_rows": sum(1 for row in branch_rows if row["carryforward_decision"] == "diagnostic_or_section_effective_only"),
        "decision_counts": dict(sorted(decision_counts.items())),
        "scientific_admission_change": "none",
        "native_output_mutation": "none",
        "registry_mutation": "none",
        "scheduler_action": "none",
        "external_fluid_edit": "none",
        "generated_index_refresh": "not_run_active_agents_own_generated_index_paths",
    }

    write_csv(out / "branch_gate_carryforward_summary.csv", branch_rows, BRANCH_COLUMNS)
    write_csv(out / "target_package_gate_contract.csv", contract_rows, CONTRACT_COLUMNS)
    write_csv(out / "source_gate_crosswalk.csv", crosswalk_rows, SOURCE_CROSSWALK_COLUMNS)
    write_csv(out / "fit_and_runtime_guardrails.csv", guardrail_rows, GUARDRAIL_COLUMNS)
    write_csv(out / "source_manifest.csv", manifest_rows, MANIFEST_COLUMNS)
    write_readme(out / "README.md", summary)
    write_json(out / "summary.json", summary)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args()
    print(json.dumps(build_package(args.out), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
