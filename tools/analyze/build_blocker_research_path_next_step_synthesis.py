#!/usr/bin/env python3
"""Build AGENT-539 blocker, research-path, and next-step synthesis."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


TASK = "AGENT-539"
DATE = "2026-07-18"
ROOT = Path(__file__).resolve().parents[2]
OUT_REL = Path("work_products/2026-07/2026-07-18/2026-07-18_blocker_research_path_next_step_synthesis")
OUT = ROOT / OUT_REL

SOURCES = {
    "blocker_register": ROOT / ".agent/blockers.yml",
    "blockers_rendered": ROOT / ".agent/BLOCKERS.md",
    "tp_tw_forensics": ROOT / "work_products/2026-07/2026-07-18/2026-07-18_tp_tw_failure_forensics/summary.json",
    "umx1_api": ROOT / "work_products/2026-07/2026-07-18/2026-07-18_umx1_api_contract_audit/summary.json",
    "source_property": ROOT / "work_products/2026-07/2026-07-18/2026-07-18_source_envelope_property_carryforward/summary.json",
    "source_property_next": ROOT / "work_products/2026-07/2026-07-18/2026-07-18_source_envelope_property_carryforward/blockers_research_paths_next_steps.csv",
    "two_tap_raw": ROOT / "work_products/2026-07/2026-07-18/2026-07-18_two_tap_component_raw_endpoint_plan/summary.json",
    "wall_blocker_audit": ROOT / "work_products/2026-07/2026-07-17/2026-07-17_wall_test_section_blocker_audit/README.md",
    "upcomer_blocker": ROOT / "work_products/2026-07/2026-07-16/2026-07-16_f6_upcomer_blocker_status_scorecard/README.md",
    "f6_unblock": ROOT / "work_products/2026-07/2026-07-17/2026-07-17_f6_friction_re_correction_unblock/README.md",
    "two_tap_readme": ROOT / "work_products/2026-07/2026-07-18/2026-07-18_two_tap_component_raw_endpoint_plan/README.md",
}

BLOCKER_COLUMNS = [
    "blocker_id",
    "severity",
    "affected_lanes",
    "evidence_path",
    "last_reviewed",
    "current_status",
    "resolution_signal",
    "forbidden_shortcut",
    "next_research_path_ids",
]

PATH_COLUMNS = [
    "path_id",
    "priority",
    "research_path",
    "blocker_addressed",
    "evidence_available_now",
    "missing_evidence",
    "expected_artifact",
    "acceptance_signal",
    "guardrails",
    "source_paths",
]

NEXT_COLUMNS = [
    "rank",
    "next_step_id",
    "owner_role",
    "allowed_path_pattern",
    "action",
    "blocked_by",
    "acceptance_signal",
    "scheduler_or_compute_policy",
    "registry_admission_policy",
    "fit_model_selection_policy",
    "runtime_input_guardrail",
    "source_paths",
]

MANIFEST_COLUMNS = ["source_id", "path", "exists", "role"]

RESOLVED_FORBIDDEN_OPEN = {
    "closure-qoi-mesh-gci",
    "refined-mesh-t-reconstruction-corruption",
    "thermal-cfd-1d-parity",
    "predictive-heater-cooler-wall-submodels",
    "fluid-external-boundary-api-gap",
    "of12-reconstructpar-segfault",
    "no-mesh-for-gci",
    "cfd-no-radiation-parity",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT.resolve()))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Expected object JSON in {path}")
    return data


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: Iterable[dict[str, Any]], columns: list[str]) -> int:
    materialized = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in materialized:
            writer.writerow({column: "" if row.get(column) is None else str(row.get(column, "")) for column in columns})
    return len(materialized)


def require_sources() -> None:
    missing = [rel(path) for path in SOURCES.values() if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing AGENT-539 source files: " + "; ".join(missing))


def parse_blockers(path: Path) -> list[dict[str, str]]:
    blockers: list[dict[str, str]] = []
    current: dict[str, str] | None = None
    in_blockers = False
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        stripped = raw_line.strip()
        if stripped == "blockers:":
            in_blockers = True
            continue
        if not in_blockers or not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("- id:"):
            if current:
                blockers.append(current)
            current = {"id": stripped.split(":", 1)[1].strip()}
            continue
        if current is None or ":" not in stripped:
            continue
        key, value = stripped.split(":", 1)
        if key in {"title", "status", "severity", "blocks", "evidence", "last_reviewed", "resolved_on", "superseded_on"}:
            current[key] = value.strip().strip('"')
    if current:
        blockers.append(current)
    return blockers


def parse_blocks(value: str) -> str:
    return value.strip("[]").replace(", ", ";")


def blocker_spec(blocker_id: str) -> dict[str, str]:
    specs = {
        "predictive-wall-test-section-submodels": {
            "resolution_signal": "Fluid exposes real upcomer mixing/stratification or distributed wall/fluid coupling, then a split-legal scorecard improves mdot without worsening TP/TW/all-probe gates.",
            "forbidden_shortcut": "UMX1 scoring grid without real API hook; duplicate AGENT-526 TSWFC1; passive wall-state selector retry; realized CFD heat/mdot/validation-temperature runtime inputs.",
            "next_research_path_ids": "RP1;RP2;RP5",
        },
        "upcomer-onset-data-sparsity": {
            "resolution_signal": "Near-onset/non-recirculating anchors plus same-window pressure, thermal, recirculation, mesh/time uncertainty, and source/property labels.",
            "forbidden_shortcut": "ordinary Nu/f_D/K promotion from recirculating PM5/upcomer rows.",
            "next_research_path_ids": "RP3;RP6",
        },
        "f6-friction-re-correction": {
            "resolution_signal": "Non-recirculating pressure anchors or explicit recirculation-modeled F6/onset closure improves validation/holdout over F3 without hidden global multiplier.",
            "forbidden_shortcut": "ordinary F6 fit from PM5, missing endpoint pressures, recirculating rows, or component-K proxy residuals.",
            "next_research_path_ids": "RP4;RP6",
        },
    }
    return specs[blocker_id]


def build_verified_blockers() -> list[dict[str, Any]]:
    rows = []
    for blocker in parse_blockers(SOURCES["blocker_register"]):
        if blocker.get("status") != "open":
            continue
        spec = blocker_spec(blocker["id"])
        rows.append(
            {
                "blocker_id": blocker["id"],
                "severity": blocker.get("severity", ""),
                "affected_lanes": parse_blocks(blocker.get("blocks", "")),
                "evidence_path": blocker.get("evidence", ""),
                "last_reviewed": blocker.get("last_reviewed", ""),
                "current_status": "verified_open",
                "resolution_signal": spec["resolution_signal"],
                "forbidden_shortcut": spec["forbidden_shortcut"],
                "next_research_path_ids": spec["next_research_path_ids"],
            }
        )
    severity_order = {"high": 0, "medium": 1, "low": 2}
    return sorted(rows, key=lambda row: (severity_order.get(row["severity"], 9), row["blocker_id"]))


def build_research_paths() -> list[dict[str, Any]]:
    umx1 = read_json(SOURCES["umx1_api"])
    tp_tw = read_json(SOURCES["tp_tw_forensics"])
    source_property = read_json(SOURCES["source_property"])
    two_tap = read_json(SOURCES["two_tap_raw"])
    return [
        {
            "path_id": "RP1",
            "priority": "P0",
            "research_path": "Fluid UMX1 API implementation contract",
            "blocker_addressed": "predictive-wall-test-section-submodels;upcomer-onset-data-sparsity",
            "evidence_available_now": f"AGENT-537 decision={umx1['decision']}; real_hook_present={umx1['real_hook_present']}; AGENT-536 recommended_next_model={tp_tw['recommended_next_model']}",
            "missing_evidence": "Writable external Fluid row implementing an energy-conserving upcomer exchange/stratification state, then dry contract audit before scoring.",
            "expected_artifact": "No-solver API implementation plan or external Fluid patch row; only after that, a split-legal dry scoring contract.",
            "acceptance_signal": "Fluid config/solver exposes declared second stream or stratified state, accepted-root criteria, runtime audit, and no mdot-only admission path.",
            "guardrails": "Do not launch a UMX1 scoring grid while AGENT-537 reports no real hook; do not fake mixing through wall loss, HTC, friction, source, or sensor adjustment.",
            "source_paths": f"{rel(SOURCES['umx1_api'])};{rel(SOURCES['tp_tw_forensics'])}",
        },
        {
            "path_id": "RP2",
            "priority": "P1",
            "research_path": "TSWFC2 distributed test-section wall/fluid nodes",
            "blocker_addressed": "predictive-wall-test-section-submodels",
            "evidence_available_now": f"AGENT-536 candidate_family_rows={tp_tw['candidate_family_rows']}; admitted_candidate_families={tp_tw['admitted_candidate_families']}; secondary_model={tp_tw['secondary_model']}",
            "missing_evidence": "Distributed wall/fluid node contract that differs from AGENT-526 single bulk-to-ambient series fallback.",
            "expected_artifact": "Dry scenario contract with role/segment wall/fluid states, TP/TW/all-probe gates, and runtime-forbidden input audit.",
            "acceptance_signal": "Candidate improves mdot and TP/TW/all-probe shape versus M3 on declared validation/holdout rows.",
            "guardrails": "Do not duplicate AGENT-526 TSWFC1 unchanged; do not use realized test-section heat or validation temperatures at runtime.",
            "source_paths": f"{rel(SOURCES['tp_tw_forensics'])};{rel(SOURCES['wall_blocker_audit'])}",
        },
        {
            "path_id": "RP3",
            "priority": "P1",
            "research_path": "Upcomer onset anchor matrix",
            "blocker_addressed": "upcomer-onset-data-sparsity",
            "evidence_available_now": "Current blocker register reports 3 observed recirculation points, 0 non-recirculating anchors, and 0 single-stream fit-admitted rows.",
            "missing_evidence": "Near-onset or non-recirculating anchors with same-window reverse-flow, pressure, wall/bulk temperature, and mesh/time uncertainty metrics.",
            "expected_artifact": "CFD anchor design or terminal admission package that labels onset, transition, and non-recirculating rows.",
            "acceptance_signal": "At least one admitted non-recirculating/transition anchor exists before ordinary coefficient promotion.",
            "guardrails": "Do not classify recirculating upcomer rows as ordinary single-stream Nu/f_D/K evidence.",
            "source_paths": f"{rel(SOURCES['upcomer_blocker'])};{rel(SOURCES['blockers_rendered'])}",
        },
        {
            "path_id": "RP4",
            "priority": "P1",
            "research_path": "F6 non-recirculating pressure anchor and raw endpoint path",
            "blocker_addressed": "f6-friction-re-correction",
            "evidence_available_now": f"Two-tap endpoint plan target_rows={two_tap['target_rows']}; ordinary_admissions={two_tap['ordinary_admissions']}; sampling_jobs_launched={two_tap['sampling_jobs_launched']}",
            "missing_evidence": "Finite raw endpoint pressure/velocity/recirculation/UQ fields from a separately claimed staged-copy postprocessing row.",
            "expected_artifact": "Endpoint-pressure harvest/admission package followed by a separate F6/component-K review.",
            "acceptance_signal": "Endpoint labels are finite and pressure, kinetic, straight-reference, recirculation, same-QOI UQ, and source/property gates pass.",
            "guardrails": "Do not infer endpoint pressures, clip negative K, fit F6, or admit component K from the plan-only package.",
            "source_paths": f"{rel(SOURCES['two_tap_raw'])};{rel(SOURCES['two_tap_readme'])}",
        },
        {
            "path_id": "RP5",
            "priority": "P1",
            "research_path": "Closure scorecard label enforcement",
            "blocker_addressed": "all closure-scorecard lanes",
            "evidence_available_now": f"AGENT-538 label_rows={source_property['source_property_label_rows']}; missing_coverage_rows={source_property['missing_source_property_coverage_rows']}",
            "missing_evidence": "Future scorecard builders must consume AGENT-538 source-envelope/property labels before reporting fit/admission rows.",
            "expected_artifact": "Scorecard contract/adoption patch or package with source/property fields on every fit/score row.",
            "acceptance_signal": "No blank property/source label fields on fit/admission rows; Salt1/perturbation/future rows refreshed before use.",
            "guardrails": "Do not treat missing source/property coverage as inside envelope or property-independent.",
            "source_paths": f"{rel(SOURCES['source_property'])};{rel(SOURCES['source_property_next'])}",
        },
        {
            "path_id": "RP6",
            "priority": "P2",
            "research_path": "Thesis-facing blocker/path index",
            "blocker_addressed": "all verified blockers",
            "evidence_available_now": "The current blocker register and July 18 synthesis packages separate open blockers from resolved/superseded ones.",
            "missing_evidence": "None for a living index; future updates should occur only after blocker or admission state changes.",
            "expected_artifact": "Dated synthesis package plus topic-map link used as the current source for report/thesis next steps.",
            "acceptance_signal": "Reports cite verified blocker IDs, research paths, and guardrails instead of stale prose or chat logs.",
            "guardrails": "Do not re-report resolved/superseded blockers as open; do not claim scientific admission from a planning package.",
            "source_paths": f"{rel(SOURCES['blockers_rendered'])};{rel(SOURCES['tp_tw_forensics'])};{rel(SOURCES['umx1_api'])};{rel(SOURCES['source_property'])}",
        },
    ]


def build_next_steps() -> list[dict[str, Any]]:
    return [
        {
            "rank": 1,
            "next_step_id": "NS1_fluid_umx1_api_row",
            "owner_role": "Implementer/Tester/Writer with external Fluid edit authority",
            "allowed_path_pattern": "new board row must explicitly claim external ../cfd-modeling-tools Fluid files plus repo-local handoff artifacts",
            "action": "Implement or formally reject a real UMX1 upcomer mixing/stratification API before any UMX1 score grid.",
            "blocked_by": "AGENT-537 no real Fluid hook",
            "acceptance_signal": "API audit passes with real hook fields, runtime legality, and accepted-root dry contract.",
            "scheduler_or_compute_policy": "no scheduler or solver until API contract exists",
            "registry_admission_policy": "no registry/admission mutation",
            "fit_model_selection_policy": "no fitting/model selection",
            "runtime_input_guardrail": "no wall-loss/HTC/friction/source/sensor adjustment used to fake mixing",
            "source_paths": rel(SOURCES["umx1_api"]),
        },
        {
            "rank": 2,
            "next_step_id": "NS2_tswfc2_dry_contract",
            "owner_role": "Forward-pred/Thermal-modeling/Implementer/Tester/Writer",
            "allowed_path_pattern": "new work_product plus optional repo-local tools/analyze builder/test; no Fluid run unless separately authorized",
            "action": "Draft distributed test-section wall/fluid node contract that is distinct from AGENT-526 TSWFC1.",
            "blocked_by": "predictive-wall-test-section-submodels",
            "acceptance_signal": "Dry contract declares states, joins, metrics, split, runtime audit, and no duplicate TSWFC1 path.",
            "scheduler_or_compute_policy": "no solver in contract task",
            "registry_admission_policy": "no registry/admission mutation",
            "fit_model_selection_policy": "no fitting/model selection",
            "runtime_input_guardrail": "no realized wallHeatFlux, CFD mdot, imposed cooler duty, realized test-section heat, or validation temperatures",
            "source_paths": rel(SOURCES["tp_tw_forensics"]),
        },
        {
            "rank": 3,
            "next_step_id": "NS3_raw_endpoint_postprocessing_row",
            "owner_role": "cfd-pp/Hydraulics/Implementer/Tester/Writer",
            "allowed_path_pattern": "separately claimed staged-copy postprocessing paths and new endpoint harvest package",
            "action": "Run the raw endpoint sampling contract for corner_lower_right only after a board row grants staged-copy postprocessing authority.",
            "blocked_by": "f6-friction-re-correction; missing endpoint pressure fields",
            "acceptance_signal": "Finite endpoint p/p_rgh/U/T/rho/flux/area plus RAF/RMF/SVF and same-QOI uncertainty gates.",
            "scheduler_or_compute_policy": "scheduler/postprocessing only in a separately claimed row",
            "registry_admission_policy": "no component-K or F6 admission in sampling row",
            "fit_model_selection_policy": "no F6 fit, no K clipping, no hidden multiplier",
            "runtime_input_guardrail": "pressure endpoints are target/extraction evidence, not Fluid runtime tuning inputs",
            "source_paths": rel(SOURCES["two_tap_raw"]),
        },
        {
            "rank": 4,
            "next_step_id": "NS4_source_property_refresh_for_scorecards",
            "owner_role": "Literature-synthesis/Tester/Writer",
            "allowed_path_pattern": "source/property carryforward package or future scorecard package",
            "action": "Refresh source-envelope/property labels for Salt1, perturbation, external, and future rows before using them in closure scorecards.",
            "blocked_by": "source_or_property_gate_missing rows in AGENT-538",
            "acceptance_signal": "Future scorecards carry property_mode, property_sensitivity_label, source_validity_envelope_status, source_use_category, and provenance.",
            "scheduler_or_compute_policy": "no scheduler",
            "registry_admission_policy": "no registry/admission mutation",
            "fit_model_selection_policy": "no fit/admission row without labels",
            "runtime_input_guardrail": "property/source labels are metadata guardrails, not runtime fitting inputs",
            "source_paths": rel(SOURCES["source_property"]),
        },
        {
            "rank": 5,
            "next_step_id": "NS5_upcomer_onset_anchor_design",
            "owner_role": "Hydraulics/Thermal-modeling/cfd-pp/Writer",
            "allowed_path_pattern": "new design package first; compute launch only in later claimed row",
            "action": "Design near-onset/non-recirculating upcomer anchor evidence before ordinary coefficient promotion.",
            "blocked_by": "upcomer-onset-data-sparsity",
            "acceptance_signal": "Anchor matrix names Q/Re/insulation cases, same-window metrics, mesh/time uncertainty, and admission gates.",
            "scheduler_or_compute_policy": "design task no scheduler; future launch requires separate row",
            "registry_admission_policy": "no registry/admission mutation in design task",
            "fit_model_selection_policy": "no ordinary Nu/f_D/K fitting from recirculating rows",
            "runtime_input_guardrail": "same-window metrics are validation/reduction evidence, not predictive runtime shortcuts",
            "source_paths": rel(SOURCES["upcomer_blocker"]),
        },
    ]


def build_source_manifest() -> list[dict[str, Any]]:
    return [{"source_id": key, "path": rel(path), "exists": path.exists(), "role": "read-only synthesis input"} for key, path in SOURCES.items()]


def write_readme(path: Path, summary: dict[str, Any]) -> None:
    path.write_text(
        f"""---
provenance:
  - {rel(SOURCES['blockers_rendered'])}
  - {rel(SOURCES['tp_tw_forensics'])}
  - {rel(SOURCES['umx1_api'])}
  - {rel(SOURCES['source_property'])}
  - {rel(SOURCES['two_tap_raw'])}
tags: [blocker-synthesis, research-paths, next-steps, closure-scorecard]
related:
  - .agent/status/2026-07-18_AGENT-539.md
  - .agent/journal/2026-07-18/blocker-research-path-next-step-synthesis.md
  - imports/2026-07-18_blocker_research_path_next_step_synthesis.json
task: {TASK}
date: {DATE}
role: Coordinator/Literature-synthesis/Tester/Writer
type: work_product
status: complete
---
# Blocker / Research Path / Next-Step Synthesis

Generated: `{summary['generated_at_utc']}`

## Decision

This package identifies the current verified blockers, research paths, and next
steps from existing evidence only. It does not change scientific admission.

## Outputs

- `verified_blockers.csv`
- `research_paths.csv`
- `next_steps_queue.csv`
- `source_manifest.csv`
- `summary.json`

## Counts

- Verified open blockers: `{summary['verified_open_blockers']}`.
- Resolved/superseded blockers excluded from open list: `{summary['resolved_or_superseded_blockers_excluded']}`.
- Research paths: `{summary['research_paths']}`.
- Ordered next steps: `{summary['next_steps']}`.

## Current Priority

UMX1 remains the top research path, but AGENT-537 makes it an API
implementation path, not a score-grid path. A UMX1 solver/scoring grid is
blocked until Fluid exposes a real upcomer mixing/stratification hook.

## Guardrails

No native CFD outputs, registry/admission state, scheduler state, Fluid source,
generated index files, fitting, tuning, model selection, or scientific
admission state were changed. Resolved and superseded blockers are not listed
as open.
""",
        encoding="utf-8",
    )


def build_package(out: Path = OUT) -> dict[str, Any]:
    require_sources()
    out.mkdir(parents=True, exist_ok=True)

    blockers = build_verified_blockers()
    paths = build_research_paths()
    next_steps = build_next_steps()
    manifest = build_source_manifest()
    all_blockers = parse_blockers(SOURCES["blocker_register"])
    resolved_excluded = [row for row in all_blockers if row.get("status") in {"resolved", "superseded"}]
    blocker_ids = {row["blocker_id"] for row in blockers}
    if blocker_ids & RESOLVED_FORBIDDEN_OPEN:
        raise ValueError(f"Resolved blockers leaked into open list: {sorted(blocker_ids & RESOLVED_FORBIDDEN_OPEN)}")

    summary = {
        "task": TASK,
        "date": DATE,
        "generated_at_utc": utc_now(),
        "output_dir": rel(out),
        "verified_open_blockers": len(blockers),
        "open_blocker_ids": sorted(blocker_ids),
        "resolved_or_superseded_blockers_excluded": len(resolved_excluded),
        "research_paths": len(paths),
        "next_steps": len(next_steps),
        "top_next_step": next_steps[0]["next_step_id"],
        "umx1_grid_status": "blocked_no_real_hook",
        "scientific_admission_change": "none",
        "native_output_mutation": "none",
        "registry_mutation": "none",
        "scheduler_action": "none",
        "solver_or_postprocessing_launch": "none",
        "external_fluid_edit": "none",
        "generated_index_refresh": "not_run_synthesis_package_only",
        "next_step_policy_counts": dict(sorted(Counter(row["scheduler_or_compute_policy"] for row in next_steps).items())),
    }

    write_csv(out / "verified_blockers.csv", blockers, BLOCKER_COLUMNS)
    write_csv(out / "research_paths.csv", paths, PATH_COLUMNS)
    write_csv(out / "next_steps_queue.csv", next_steps, NEXT_COLUMNS)
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
