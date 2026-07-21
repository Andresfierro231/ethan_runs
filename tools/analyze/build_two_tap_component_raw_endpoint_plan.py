#!/usr/bin/env python3
"""Build the two-tap raw endpoint sampling contract for corner_lower_right."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


TASK = "TODO-TWO-TAP-COMPONENT-RAW-ENDPOINTS"
DATE = "2026-07-18"
ROOT = Path(__file__).resolve().parents[2]
OUT_REL = Path("work_products/2026-07/2026-07-18/2026-07-18_two_tap_component_raw_endpoint_plan")
OUT = ROOT / OUT_REL

EXTRACTOR = ROOT / "work_products/2026-07/2026-07-17/2026-07-17_two_tap_component_repair_extractor"
CONTRACT = ROOT / "work_products/2026-07/2026-07-17/2026-07-17_two_tap_component_repair_contract"
MINOR = ROOT / "work_products/2026-07/2026-07-08/2026-07-08_minor_loss_two_tap"
TAP = ROOT / "work_products/2026-07/2026-07-14/2026-07-14_hydraulic_tap_length_admission_refresh"
RAW = ROOT / "work_products/2026-07/2026-07-15/2026-07-15_staged_closure_qoi_pressure_sbatch"
NOTE = ROOT / "operational_notes/07-26/17/2026-07-17_MONDAY_HYDRAULICS_CONTEXT_AND_NEXT_STEPS.md"

SOURCES = {
    "raw_queue": EXTRACTOR / "next_raw_postprocessing_queue.csv",
    "extractor_output": EXTRACTOR / "two_tap_component_repair_output.csv",
    "extractor_gates": EXTRACTOR / "extractor_gate_results.csv",
    "component_targets": CONTRACT / "component_repair_targets.csv",
    "repair_field_contract": CONTRACT / "repair_field_contract.csv",
    "future_extractor_schema": CONTRACT / "future_extractor_schema.csv",
    "minor_loss_two_tap": MINOR / "minor_loss_two_tap.csv",
    "tap_centerline_lengths": TAP / "tap_centerline_length_table.csv",
    "component_k_recomputed": TAP / "component_cluster_k_recomputed_admission_table.csv",
    "raw_pressure_preflight": RAW / "raw_pressure_preflight.csv",
    "raw_pressure_two_tap_harvest": RAW / "raw_pressure_two_tap_harvest.csv",
    "monday_handoff": NOTE,
}

TARGET_COLUMNS = [
    "case_id",
    "case_key",
    "source_id",
    "source_case_path",
    "feature",
    "time_window_s",
    "upstream_patch",
    "downstream_patch",
    "upstream_station_label",
    "downstream_station_label",
    "upstream_output_label",
    "downstream_output_label",
    "downstream_span",
    "adjacent_spans",
    "centerline_tap_length_m",
    "required_endpoint_fields",
    "required_basis_fields",
    "required_recirculation_fields",
    "status",
    "guardrail",
]

PRESSURE_COLUMNS = [
    "case_id",
    "feature",
    "time_window_s",
    "surface_function",
    "surface_label",
    "tap_role",
    "patch_or_station",
    "sampled_fields",
    "required_reductions",
    "pressure_basis_policy",
    "hydrostatic_policy",
    "kinetic_policy",
    "acceptance_signal",
    "output_fields",
]

BASIS_COLUMNS = [
    "field",
    "units",
    "sample_level",
    "formula_or_source",
    "required_for_gate",
    "acceptance_rule",
    "reject_if_missing_or_ambiguous",
    "source_paths",
]

RECIRC_COLUMNS = [
    "case_id",
    "feature",
    "time_window_s",
    "metric_scope",
    "tap_labels",
    "normal_direction_policy",
    "RAF_definition",
    "RMF_definition",
    "SVF_definition",
    "ordinary_acceptance_rule",
    "diagnostic_fallback",
]

UQ_COLUMNS = [
    "case_id",
    "feature",
    "qoi",
    "required_sample_set",
    "time_uncertainty_requirement",
    "mesh_uncertainty_requirement",
    "current_status",
    "acceptance_signal",
    "guardrail",
]

GATE_COLUMNS = [
    "gate",
    "current_status",
    "required_before_sampling_launch",
    "required_before_coefficient_use",
    "evidence",
    "guardrail",
]

SUMMARY_COLUMNS = ["category", "count", "interpretation"]
MANIFEST_COLUMNS = ["source_id", "path", "exists", "role", "mutation_status"]


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
        raise FileNotFoundError("Missing raw endpoint plan sources: " + ", ".join(missing))


def by_case_feature(rows: list[dict[str, str]]) -> dict[tuple[str, str], dict[str, str]]:
    return {(row.get("case_id", ""), row.get("feature", "")): row for row in rows}


def by_case(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {row.get("case_id", ""): row for row in rows}


def target_rows() -> list[dict[str, Any]]:
    targets = by_case_feature(read_csv(SOURCES["component_targets"]))
    extractor = by_case_feature(read_csv(SOURCES["extractor_output"]))
    tap = by_case_feature(read_csv(SOURCES["tap_centerline_lengths"]))
    component = by_case_feature(read_csv(SOURCES["component_k_recomputed"]))
    preflight = by_case(read_csv(SOURCES["raw_pressure_preflight"]))
    rows: list[dict[str, Any]] = []
    for case_id in ["salt_2", "salt_3", "salt_4"]:
        feature = "corner_lower_right"
        key = (case_id, feature)
        target = targets[key]
        tap_row = tap[key]
        component_row = component[key]
        preflight_row = preflight[case_id]
        time_window = extractor[key]["time_window"] or preflight_row["time_s"]
        rows.append(
            {
                "case_id": case_id,
                "case_key": preflight_row["case_key"],
                "source_id": preflight_row["source_id"],
                "source_case_path": preflight_row.get("source_case_path") or preflight_row["source_case"],
                "feature": feature,
                "time_window_s": time_window,
                "upstream_patch": tap_row["start_patch"],
                "downstream_patch": tap_row["end_patch"],
                "upstream_station_label": tap_row["start_station_label"],
                "downstream_station_label": tap_row["end_station_label"],
                "upstream_output_label": "corner_lower_right__upstream_lower_leg__s04",
                "downstream_output_label": "corner_lower_right__downstream_right_leg__s00",
                "downstream_span": tap_row["downstream_span"],
                "adjacent_spans": component_row["adjacent_spans"],
                "centerline_tap_length_m": tap_row["centerline_tap_length_m"],
                "required_endpoint_fields": "p;p_rgh;U;T_or_rho;face_area;face_normal;face_flux_or_phi",
                "required_basis_fields": "p_upstream_pa;p_downstream_pa;hydrostatic_correction_pa;kinetic_correction_pa;rho_local_kg_m3;local_dynamic_pressure_pa;straight_loss_subtraction_pa",
                "required_recirculation_fields": "RAF;RMF;SVF at upstream and downstream taps in same time window",
                "status": target["readiness_status"],
                "guardrail": "sampling contract only; do not mutate source case, admit K, clip negative K, or use this row for F6 fitting",
            }
        )
    return rows


def pressure_surface_rows(targets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for target in targets:
        for role, label_key, station_key in [
            ("upstream", "upstream_output_label", "upstream_station_label"),
            ("downstream", "downstream_output_label", "downstream_station_label"),
        ]:
            rows.append(
                {
                    "case_id": target["case_id"],
                    "feature": target["feature"],
                    "time_window_s": target["time_window_s"],
                    "surface_function": "twoTapCornerLowerRightRawEndpointSurfaces",
                    "surface_label": target[label_key],
                    "tap_role": role,
                    "patch_or_station": target[station_key],
                    "sampled_fields": "p,p_rgh,U,T_or_rho,phi_or_surface_flux,face_area,face_normal",
                    "required_reductions": "area_weighted_mean(p);area_weighted_mean(p_rgh);area_weighted_mean(U);mass_flux;reverse_area;reverse_mass;secondary_velocity_fraction",
                    "pressure_basis_policy": "emit both static pressure p and p_rgh; compute feature Delta-p from endpoint means with sign convention downstream-minus-upstream and retain both signs in raw output",
                    "hydrostatic_policy": "report hydrostatic_correction_pa separately as Delta(p)-Delta(p_rgh); do not add it again when using p_rgh-derived loss",
                    "kinetic_policy": "report kinetic_correction_pa as downstream dynamic head minus upstream dynamic head using local density and bulk endpoint velocity; do not double count it inside total-pressure loss",
                    "acceptance_signal": "finite endpoint p and p_rgh means, finite U/rho basis, face counts, labels, and exact time window",
                    "output_fields": f"p_{role}_pa;p_rgh_{role}_pa;U_bulk_{role}_m_s;rho_{role}_kg_m3;mass_flux_{role}_kg_s;face_count_{role}",
                }
            )
    return rows


def basis_rows() -> list[dict[str, Any]]:
    src = f"{rel(SOURCES['future_extractor_schema'])};{rel(SOURCES['repair_field_contract'])};{rel(SOURCES['minor_loss_two_tap'])}"
    return [
        {
            "field": "p_upstream_pa",
            "units": "Pa",
            "sample_level": "upstream endpoint surface",
            "formula_or_source": "area-weighted mean static p on corner_lower_right upstream surface lower_leg__s04",
            "required_for_gate": "pressure_basis_resolved",
            "acceptance_rule": "finite value with surface label, field name, time_window_s, and source_case_path",
            "reject_if_missing_or_ambiguous": "yes",
            "source_paths": src,
        },
        {
            "field": "p_downstream_pa",
            "units": "Pa",
            "sample_level": "downstream endpoint surface",
            "formula_or_source": "area-weighted mean static p on corner_lower_right downstream surface right_leg__s00",
            "required_for_gate": "pressure_basis_resolved",
            "acceptance_rule": "finite value with surface label, field name, time_window_s, and source_case_path",
            "reject_if_missing_or_ambiguous": "yes",
            "source_paths": src,
        },
        {
            "field": "hydrostatic_correction_pa",
            "units": "Pa",
            "sample_level": "endpoint pair",
            "formula_or_source": "(p_downstream_pa - p_upstream_pa) - (p_rgh_downstream_pa - p_rgh_upstream_pa)",
            "required_for_gate": "no_buoyancy_double_counting",
            "acceptance_rule": "reported separately with sign convention; not folded into both p and p_rgh losses",
            "reject_if_missing_or_ambiguous": "yes",
            "source_paths": src,
        },
        {
            "field": "kinetic_correction_pa",
            "units": "Pa",
            "sample_level": "endpoint pair",
            "formula_or_source": "0.5*rho_downstream*U_bulk_downstream^2 - 0.5*rho_upstream*U_bulk_upstream^2",
            "required_for_gate": "no_dynamic_head_double_counting",
            "acceptance_rule": "local density basis and bulk velocity basis are recorded for both endpoints",
            "reject_if_missing_or_ambiguous": "yes",
            "source_paths": src,
        },
        {
            "field": "local_dynamic_pressure_pa",
            "units": "Pa",
            "sample_level": "feature normalization",
            "formula_or_source": "0.5*rho_local*U_ref_local^2, with rho_local and U_ref_local from the same endpoint window and documented averaging policy",
            "required_for_gate": "velocity_basis_resolved",
            "acceptance_rule": "same-window local value; not inherited from branch-average pressure-ledger proxy",
            "reject_if_missing_or_ambiguous": "yes",
            "source_paths": src,
        },
        {
            "field": "straight_loss_subtraction_pa",
            "units": "Pa",
            "sample_level": "local straight-reference contract",
            "formula_or_source": "document selected local straight reference or mark component_isolation_label=apparent_cluster_only; current centerline subtraction is not admissible because K_local is negative",
            "required_for_gate": "component_isolation",
            "acceptance_rule": "nonnegative K_local emerges without clipping, or row remains apparent/cluster diagnostic",
            "reject_if_missing_or_ambiguous": "yes",
            "source_paths": f"{rel(SOURCES['component_k_recomputed'])};{rel(SOURCES['extractor_gates'])}",
        },
        {
            "field": "K_apparent",
            "units": "dimensionless",
            "sample_level": "diagnostic output",
            "formula_or_source": "feature_total_pressure_loss_pa / local_dynamic_pressure_pa before straight-reference subtraction",
            "required_for_gate": "diagnostic_pressure_ledger",
            "acceptance_rule": "may be emitted as diagnostic only while isolation/UQ/recirculation gates fail",
            "reject_if_missing_or_ambiguous": "yes",
            "source_paths": src,
        },
        {
            "field": "K_local",
            "units": "dimensionless",
            "sample_level": "candidate coefficient output",
            "formula_or_source": "(feature_total_pressure_loss_pa - straight_loss_subtraction_pa) / local_dynamic_pressure_pa",
            "required_for_gate": "ordinary_component_K_candidate",
            "acceptance_rule": "finite, nonnegative without clipping, RAF < 0.01, RMF < 0.01, component isolation and same-QOI UQ attached",
            "reject_if_missing_or_ambiguous": "yes",
            "source_paths": src,
        },
    ]


def recirculation_rows(targets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for target in targets:
        rows.append(
            {
                "case_id": target["case_id"],
                "feature": target["feature"],
                "time_window_s": target["time_window_s"],
                "metric_scope": "upstream_and_downstream_endpoint_surfaces",
                "tap_labels": f"{target['upstream_output_label']};{target['downstream_output_label']}",
                "normal_direction_policy": "normal is positive along expected lower_leg__s04 to right_leg__s00 feature flow; reverse flow is U dot n_expected < 0",
                "RAF_definition": "reverse_area_fraction = sum(area where U dot n_expected < 0) / sum(area) for each tap; aggregate RAF = max(upstream_RAF, downstream_RAF)",
                "RMF_definition": "reverse_mass_fraction = abs(sum(rho*U dot n_expected*area where reverse)) / sum(abs(rho*U dot n_expected*area)) for each tap; aggregate RMF = max(upstream_RMF, downstream_RMF)",
                "SVF_definition": "secondary_velocity_fraction = area- or mass-weighted mean(sqrt(|U|^2 - (U dot n_expected)^2) / max(|U|, eps)) for each tap; report aggregate max",
                "ordinary_acceptance_rule": "ordinary component-K row requires aggregate RAF < 0.01 and aggregate RMF < 0.01; SVF is retained as diagnostic",
                "diagnostic_fallback": "if RAF or RMF is missing or >= 0.01, keep row diagnostic/section-effective and do not fit F6 or component K",
            }
        )
    return rows


def uncertainty_rows(targets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for target in targets:
        rows.append(
            {
                "case_id": target["case_id"],
                "feature": target["feature"],
                "qoi": "corner_lower_right_feature_pressure_loss_and_K_local",
                "required_sample_set": "same endpoint labels, same pressure/basis formulas, and same sign convention for every mesh/time member",
                "time_uncertainty_requirement": "sample target time_window_s plus neighboring saved times in the same quasi-steady window when available; report mean, standard deviation, and max-min for feature_total_pressure_loss_pa and K_local",
                "mesh_uncertainty_requirement": "repeat exact endpoint contract on every available same-case mesh level or mark mesh_uncertainty_status=missing_no_GCI",
                "current_status": "missing_same_qoi_mesh_time_UQ",
                "acceptance_signal": "uncertainty bound is attached to this same pressure-loss QoI, not borrowed from unrelated pressure or thermal rows",
                "guardrail": "if mesh/time family is unavailable or nonmonotone, emit explicit diagnostic-only uncertainty status; do not fabricate GCI",
            }
        )
    return rows


def launch_gate_rows(targets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    case_count = len(targets)
    return [
        {
            "gate": "task_scope",
            "current_status": "pass_plan_only",
            "required_before_sampling_launch": "claim separate staged-copy postprocessing row if any OpenFOAM sampling is run",
            "required_before_coefficient_use": "new extractor/admission package after raw outputs exist",
            "evidence": f"{case_count} target rows converted to exact sampling requirements",
            "guardrail": "this package launches no solver/postprocessing and changes no scientific admission",
        },
        {
            "gate": "target_taps_resolved",
            "current_status": "pass_contract",
            "required_before_sampling_launch": "use lower_leg__s04 and right_leg__s00 endpoint labels for all Salt2/Salt3/Salt4 rows",
            "required_before_coefficient_use": "raw output must carry those labels and exact time windows",
            "evidence": rel(SOURCES["tap_centerline_lengths"]),
            "guardrail": "do not substitute left_lower_leg__s00/left_upper_leg__s04 staged precedent surfaces for this feature",
        },
        {
            "gate": "pressure_velocity_basis",
            "current_status": "specified_not_sampled",
            "required_before_sampling_launch": "sample p,p_rgh,U,T_or_rho,phi_or_surface_flux,face_area,face_normal at both endpoint surfaces",
            "required_before_coefficient_use": "basis fields reproduce feature loss without buoyancy or kinetic double counting",
            "evidence": rel(SOURCES["raw_queue"]),
            "guardrail": "do not infer endpoint p fields from preserved proxy losses",
        },
        {
            "gate": "straight_reference_component_isolation",
            "current_status": "blocked_pending_raw_basis",
            "required_before_sampling_launch": "record current centerline reference and candidate local straight-reference policy",
            "required_before_coefficient_use": "K_local nonnegative without clipping, or row remains apparent/cluster diagnostic",
            "evidence": rel(SOURCES["component_k_recomputed"]),
            "guardrail": "negative K is a blocker, not a value to clip",
        },
        {
            "gate": "recirculation_metrics",
            "current_status": "specified_not_sampled",
            "required_before_sampling_launch": "compute RAF, RMF, and SVF on same endpoint surfaces/time windows",
            "required_before_coefficient_use": "ordinary rows require aggregate RAF < 0.01 and RMF < 0.01",
            "evidence": rel(SOURCES["extractor_gates"]),
            "guardrail": "material reverse-flow rows remain diagnostic or section-effective only",
        },
        {
            "gate": "same_qoi_uncertainty",
            "current_status": "specified_not_available",
            "required_before_sampling_launch": "declare mesh/time family members or explicit non-GCI diagnostic-only status",
            "required_before_coefficient_use": "same pressure-loss QoI uncertainty attached",
            "evidence": rel(SOURCES["raw_queue"]),
            "guardrail": "do not reuse unrelated GCI or fabricate monotonicity",
        },
        {
            "gate": "F6_separation",
            "current_status": "pass_guardrail",
            "required_before_sampling_launch": "keep this component-K endpoint sampling separate from F6 nonrecirculating anchor harvests",
            "required_before_coefficient_use": "no F6 fit or component-K admission from this plan alone",
            "evidence": rel(SOURCES["monday_handoff"]),
            "guardrail": "this attacks f6-friction-re-correction context but does not fit F6 or component K",
        },
    ]


def summary_rows(targets: list[dict[str, Any]], pressure: list[dict[str, Any]], gates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {"category": "target_rows", "count": len(targets), "interpretation": "Salt2/Salt3/Salt4 corner_lower_right feature rows."},
        {"category": "endpoint_surface_rows", "count": len(pressure), "interpretation": "Two endpoint surfaces per target row."},
        {"category": "basis_field_rows", "count": len(basis_rows()), "interpretation": "Pressure, velocity, correction, and K output contract fields."},
        {"category": "recirculation_contract_rows", "count": len(targets), "interpretation": "Same-window RAF/RMF/SVF requirements."},
        {"category": "same_qoi_uncertainty_rows", "count": len(targets), "interpretation": "Same-QOI mesh/time uncertainty requirements."},
        {"category": "launch_gate_rows", "count": len(gates), "interpretation": "Future staged-copy readiness and no-admission guardrails."},
        {"category": "sampling_jobs_launched", "count": 0, "interpretation": "This task emits a contract only."},
        {"category": "ordinary_admissions", "count": 0, "interpretation": "No F6 or component-K coefficient admitted."},
    ]


def source_manifest() -> list[dict[str, Any]]:
    rows = []
    for source_id, path in SOURCES.items():
        rows.append(
            {
                "source_id": source_id,
                "path": rel(path),
                "exists": path.exists(),
                "role": "read-only input",
                "mutation_status": "not_mutated",
            }
        )
    return rows


def write_readme(path: Path, summary: dict[str, Any]) -> None:
    path.write_text(
        f"""---
provenance:
  - {rel(SOURCES['raw_queue'])}
  - {rel(SOURCES['extractor_output'])}
  - {rel(SOURCES['tap_centerline_lengths'])}
  - {rel(SOURCES['monday_handoff'])}
tags: [pressure-ledger, two-tap, raw-endpoints, component-k, f6]
related:
  - .agent/status/2026-07-18_TODO-TWO-TAP-COMPONENT-RAW-ENDPOINTS.md
  - .agent/journal/2026-07-18/two-tap-component-raw-endpoints.md
  - work_products/2026-07/2026-07-17/2026-07-17_two_tap_component_repair_extractor/README.md
task: {TASK}
date: {DATE}
role: Hydraulics/cfd-pp/Implementer/Tester/Writer
type: work_product
status: complete
---
# Two-Tap Component Raw Endpoint Plan

Generated: `{summary['generated_at_utc']}`

## Decision

The AGENT-530 raw postprocessing queue is converted into an exact sampling
contract for the three `corner_lower_right` Salt2/Salt3/Salt4 rows. This is a
plan only: no OpenFOAM sampling, scheduler action, registry mutation, Fluid
edit, F6 fit, or component-K admission was performed.

## Outputs

- `target_feature_taps.csv`
- `pressure_surface_sampling_contract.csv`
- `basis_field_contract.csv`
- `recirculation_metric_contract.csv`
- `same_qoi_uncertainty_contract.csv`
- `launch_readiness_gate.csv`
- `raw_endpoint_plan_summary.csv`
- `source_manifest.csv`
- `summary.json`

## Counts

- Target rows: `{summary['target_rows']}`.
- Endpoint surface rows: `{summary['endpoint_surface_rows']}`.
- Basis field rows: `{summary['basis_field_rows']}`.
- Recirculation contract rows: `{summary['recirculation_contract_rows']}`.
- Same-QOI uncertainty rows: `{summary['same_qoi_uncertainty_rows']}`.
- Ordinary admissions: `0`.

## Required Endpoint Contract

For each target, sample `corner_lower_right` from upstream
`lower_leg__s04` / `ncc_pipeleg_lower_09_fitting_end` to downstream
`right_leg__s00` / `ncc_pipeleg_right_01_lower_start` at the same existing
time windows: Salt2 `7915`, Salt3 `7618`, Salt4 `10000`.

Each endpoint must emit `p`, `p_rgh`, `U`, `T_or_rho`, flux/area/normal data,
bulk velocity, local density, RAF, RMF, and SVF. The downstream extractor can
use the result only if endpoint labels are finite and the pressure, kinetic,
straight-reference, recirculation, and same-QOI UQ gates pass.

## Guardrails

Do not infer missing endpoint pressure fields from proxy losses. Do not clip the
negative current `K_local` values. Do not use this component endpoint plan to
fit F6 or admit component K; a future staged-copy postprocessing row and a new
extractor/admission review are required.
""",
        encoding="utf-8",
    )


def build_package(out: Path = OUT) -> dict[str, Any]:
    require_sources()
    out.mkdir(parents=True, exist_ok=True)
    targets = target_rows()
    pressure = pressure_surface_rows(targets)
    basis = basis_rows()
    recirc = recirculation_rows(targets)
    uncertainty = uncertainty_rows(targets)
    gates = launch_gate_rows(targets)
    manifest = source_manifest()
    summary_table = summary_rows(targets, pressure, gates)
    counts = {row["category"]: int(row["count"]) for row in summary_table}
    summary = {
        "task": TASK,
        "date": DATE,
        "generated_at_utc": utc_now(),
        "output_dir": rel(out),
        **counts,
        "source_rows": len(manifest),
        "native_output_mutation": "none",
        "registry_mutation": "none",
        "scheduler_action": "none",
        "solver_or_postprocessing_launched": "none",
        "external_fluid_edit": "none",
        "generated_index_refresh": "not_run_active_agent_owns_generated_index_paths",
        "scientific_admission_change": "none",
    }
    write_csv(out / "target_feature_taps.csv", targets, TARGET_COLUMNS)
    write_csv(out / "pressure_surface_sampling_contract.csv", pressure, PRESSURE_COLUMNS)
    write_csv(out / "basis_field_contract.csv", basis, BASIS_COLUMNS)
    write_csv(out / "recirculation_metric_contract.csv", recirc, RECIRC_COLUMNS)
    write_csv(out / "same_qoi_uncertainty_contract.csv", uncertainty, UQ_COLUMNS)
    write_csv(out / "launch_readiness_gate.csv", gates, GATE_COLUMNS)
    write_csv(out / "raw_endpoint_plan_summary.csv", summary_table, SUMMARY_COLUMNS)
    write_csv(out / "source_manifest.csv", manifest, MANIFEST_COLUMNS)
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
