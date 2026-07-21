#!/usr/bin/env python3
"""Build the two-tap raw endpoint blocker and next-step roadmap."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


TASK = "TODO-TWO-TAP-BLOCKER-ROADMAP"
DATE = "2026-07-18"
ROOT = Path(__file__).resolve().parents[2]
OUT_REL = Path("work_products/2026-07/2026-07-18/2026-07-18_two_tap_blocker_roadmap")
OUT = ROOT / OUT_REL

RAW_PLAN = ROOT / "work_products/2026-07/2026-07-18/2026-07-18_two_tap_component_raw_endpoint_plan"
SOURCES = {
    "raw_plan_readme": RAW_PLAN / "README.md",
    "target_feature_taps": RAW_PLAN / "target_feature_taps.csv",
    "pressure_surface_sampling_contract": RAW_PLAN / "pressure_surface_sampling_contract.csv",
    "basis_field_contract": RAW_PLAN / "basis_field_contract.csv",
    "recirculation_metric_contract": RAW_PLAN / "recirculation_metric_contract.csv",
    "same_qoi_uncertainty_contract": RAW_PLAN / "same_qoi_uncertainty_contract.csv",
    "launch_readiness_gate": RAW_PLAN / "launch_readiness_gate.csv",
    "raw_endpoint_summary": RAW_PLAN / "summary.json",
}

BLOCKER_COLUMNS = [
    "blocker_id",
    "gate",
    "current_status",
    "severity",
    "evidence_path",
    "why_blocks_admission",
    "resolving_artifact",
    "acceptance_signal",
    "research_path_id",
    "next_step_id",
    "guardrail",
    "admission_impact",
]
PATH_COLUMNS = [
    "research_path_id",
    "title",
    "blockers_addressed",
    "objective",
    "inputs",
    "method",
    "outputs",
    "acceptance_signal",
    "stop_condition",
    "next_owner_role",
    "guardrail",
]
STEP_COLUMNS = [
    "priority",
    "step_id",
    "title",
    "depends_on",
    "role",
    "allowed_edit_paths",
    "read_only_context",
    "action",
    "acceptance_signal",
    "do_not_do",
    "expected_output",
]
RULE_COLUMNS = ["rule_id", "condition", "decision", "evidence_required", "forbidden_shortcut"]
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
        raise FileNotFoundError("Missing roadmap sources: " + ", ".join(missing))


def blocker_matrix() -> list[dict[str, Any]]:
    gates = read_csv(SOURCES["launch_readiness_gate"])
    path_for_gate = {
        "task_scope": "PATH-A",
        "target_taps_resolved": "PATH-A",
        "pressure_velocity_basis": "PATH-B",
        "straight_reference_component_isolation": "PATH-C",
        "recirculation_metrics": "PATH-D",
        "same_qoi_uncertainty": "PATH-E",
        "F6_separation": "PATH-F",
    }
    step_for_gate = {
        "task_scope": "STEP-01",
        "target_taps_resolved": "STEP-02",
        "pressure_velocity_basis": "STEP-03",
        "straight_reference_component_isolation": "STEP-04",
        "recirculation_metrics": "STEP-05",
        "same_qoi_uncertainty": "STEP-06",
        "F6_separation": "STEP-07",
    }
    severity_for_status = {
        "pass_plan_only": "process_gate",
        "pass_contract": "resolved_input",
        "specified_not_sampled": "blocking_missing_raw_output",
        "blocked_pending_raw_basis": "blocking_basis_failure",
        "specified_not_available": "blocking_missing_uq",
        "pass_guardrail": "separation_guardrail",
    }
    why = {
        "task_scope": "Sampling cannot start inside the completed plan package; it requires a separately claimed staged-copy postprocessing row.",
        "target_taps_resolved": "This gate is resolved, but all future outputs must preserve the exact lower_leg__s04 to right_leg__s00 labels and time windows.",
        "pressure_velocity_basis": "Endpoint p/p_rgh/U/density fields are specified but not sampled, so feature loss and K basis cannot be recomputed.",
        "straight_reference_component_isolation": "Current centerline straight-reference subtraction gives negative K_local, so component isolation is not physically admissible.",
        "recirculation_metrics": "RAF/RMF/SVF are missing at the same endpoint surfaces and windows, so ordinary non-recirculating K cannot be claimed.",
        "same_qoi_uncertainty": "No mesh/time uncertainty is attached to the same local pressure-loss QoI.",
        "F6_separation": "The component-K endpoint thread must not be collapsed into an F6 fit or coefficient admission shortcut.",
    }
    artifacts = {
        "task_scope": "new board row with staged-copy-only scope",
        "target_taps_resolved": "raw output preserving target_feature_taps.csv labels",
        "pressure_velocity_basis": "finite p,p_rgh,U,T_or_rho,flux,area,normal reductions at both endpoint surfaces",
        "straight_reference_component_isolation": "documented local straight reference yielding nonnegative K_local without clipping, or apparent_cluster_only decision",
        "recirculation_metrics": "same-window aggregate RAF/RMF/SVF for upstream and downstream endpoint surfaces",
        "same_qoi_uncertainty": "same-QOI mesh/time uncertainty table or explicit missing_no_GCI diagnostic status",
        "F6_separation": "separate F6 nonrecirculating-anchor row if F6 is pursued",
    }
    rows = []
    for index, gate in enumerate(gates, start=1):
        gate_name = gate["gate"]
        rows.append(
            {
                "blocker_id": f"BLK-{index:02d}",
                "gate": gate_name,
                "current_status": gate["current_status"],
                "severity": severity_for_status.get(gate["current_status"], "review_required"),
                "evidence_path": gate["evidence"],
                "why_blocks_admission": why[gate_name],
                "resolving_artifact": artifacts[gate_name],
                "acceptance_signal": gate["required_before_coefficient_use"],
                "research_path_id": path_for_gate[gate_name],
                "next_step_id": step_for_gate[gate_name],
                "guardrail": gate["guardrail"],
                "admission_impact": "no coefficient use until this gate is resolved or explicitly marked diagnostic-only",
            }
        )
    return rows


def research_path_matrix() -> list[dict[str, Any]]:
    raw_dir = rel(RAW_PLAN)
    return [
        {
            "research_path_id": "PATH-A",
            "title": "Staged-copy raw endpoint sampler",
            "blockers_addressed": "task_scope;target_taps_resolved",
            "objective": "Turn the plan into finite raw endpoint reductions without mutating native cases.",
            "inputs": f"{raw_dir}/target_feature_taps.csv; {raw_dir}/pressure_surface_sampling_contract.csv",
            "method": "Claim a new cfd-pp row, stage copies into task-owned tmp/work_products, and sample lower_leg__s04/right_leg__s00 at 7915/7618/10000.",
            "outputs": "raw_endpoint_pressure_velocity.csv; raw_endpoint_surface_files; source_manifest.csv",
            "acceptance_signal": "3 cases x 2 endpoint surfaces with finite p, p_rgh, U, density/proxy, flux, area, normal, face counts, labels, and windows.",
            "stop_condition": "Any source case missing, endpoint label mismatch, or write attempt into native case tree.",
            "next_owner_role": "Hydraulics/cfd-pp/Implementer/Tester",
            "guardrail": "No login-node heavy OpenFOAM run; no native-output mutation.",
        },
        {
            "research_path_id": "PATH-B",
            "title": "Pressure and velocity basis audit",
            "blockers_addressed": "pressure_velocity_basis",
            "objective": "Prove the endpoint pressure-loss basis is reproducible without hydrostatic or kinetic double counting.",
            "inputs": f"{raw_dir}/basis_field_contract.csv plus PATH-A raw outputs",
            "method": "Compute static-p, p_rgh, hydrostatic correction, kinetic correction, local density, and local dynamic pressure with the declared sign convention.",
            "outputs": "pressure_velocity_basis_audit.csv",
            "acceptance_signal": "Feature loss can be recomputed from raw endpoints and every correction term is separated once.",
            "stop_condition": "Missing p/p_rgh/U/density basis or inconsistent sign convention.",
            "next_owner_role": "Hydraulics/Tester",
            "guardrail": "Do not infer endpoint pressure from preserved proxy losses.",
        },
        {
            "research_path_id": "PATH-C",
            "title": "Straight-reference and component-isolation audit",
            "blockers_addressed": "straight_reference_component_isolation",
            "objective": "Decide whether corner_lower_right can become a local component K or must remain apparent/cluster diagnostic.",
            "inputs": f"{raw_dir}/basis_field_contract.csv plus PATH-B basis output",
            "method": "Evaluate the current centerline reference and candidate local straight references; require K_local nonnegative without clipping.",
            "outputs": "component_isolation_audit.csv; apparent_cluster_decision.json",
            "acceptance_signal": "Either nonnegative unclipped K_local with documented straight reference, or explicit apparent_cluster_only status.",
            "stop_condition": "Only route to nonnegative K requires clipping, global multiplier, or hidden F6 tuning.",
            "next_owner_role": "Hydraulics/Reviewer",
            "guardrail": "Negative K_local is a blocker, not a value to clip.",
        },
        {
            "research_path_id": "PATH-D",
            "title": "Same-window recirculation metrics",
            "blockers_addressed": "recirculation_metrics",
            "objective": "Classify ordinary versus diagnostic rows using endpoint RAF/RMF/SVF.",
            "inputs": f"{raw_dir}/recirculation_metric_contract.csv plus PATH-A raw endpoint velocity/flux data",
            "method": "Compute upstream, downstream, and aggregate RAF/RMF/SVF with positive normal along expected feature flow.",
            "outputs": "endpoint_recirculation_metrics.csv",
            "acceptance_signal": "Ordinary row candidate only if aggregate RAF < 0.01 and RMF < 0.01; SVF retained as diagnostic.",
            "stop_condition": "RAF/RMF missing, normal direction ambiguous, or aggregate RAF/RMF >= 0.01.",
            "next_owner_role": "Hydraulics/cfd-pp/Tester",
            "guardrail": "Material reverse-flow rows remain diagnostic or section-effective.",
        },
        {
            "research_path_id": "PATH-E",
            "title": "Same-QOI mesh/time uncertainty",
            "blockers_addressed": "same_qoi_uncertainty",
            "objective": "Attach uncertainty to the same corner_lower_right pressure-loss/K QoI or mark it diagnostic-only.",
            "inputs": f"{raw_dir}/same_qoi_uncertainty_contract.csv plus available same-case mesh/time members",
            "method": "Repeat the exact endpoint contract over valid mesh/time family members, or emit missing_no_GCI with reason.",
            "outputs": "same_qoi_uncertainty_audit.csv",
            "acceptance_signal": "Uncertainty bound attaches to this same pressure-loss QoI and uses the same labels/formulas/sign convention.",
            "stop_condition": "Only unrelated GCI exists, family is unavailable, or monotonicity is fabricated.",
            "next_owner_role": "Hydraulics/Mesh-GCI/Tester",
            "guardrail": "Do not reuse unrelated GCI or fabricate monotonicity.",
        },
        {
            "research_path_id": "PATH-F",
            "title": "Separated admission and F6 governance",
            "blockers_addressed": "F6_separation",
            "objective": "Prevent component endpoint evidence from being misused as an F6 fit or direct component-K admission.",
            "inputs": "PATH-A through PATH-E outputs",
            "method": "Build a new extractor/admission review only after raw outputs exist; route F6 to a separate nonrecirculating-anchor task.",
            "outputs": "component_admission_review.csv; next_action_or_admission_decision.json",
            "acceptance_signal": "No coefficient admitted unless all pressure, isolation, recirculation, and UQ gates pass.",
            "stop_condition": "Attempt to overwrite AGENT-530, fit F6, clip K, or use proxy endpoint pressure.",
            "next_owner_role": "Hydraulics/Reviewer/Writer",
            "guardrail": "No F6 fit and no component-K admission from roadmap outputs.",
        },
    ]


def next_step_queue() -> list[dict[str, Any]]:
    raw_dir = rel(RAW_PLAN)
    return [
        {
            "priority": 1,
            "step_id": "STEP-01",
            "title": "Claim staged-copy cfd-pp row",
            "depends_on": "roadmap complete",
            "role": "Coordinator/Hydraulics/cfd-pp",
            "allowed_edit_paths": ".agent own row; task status/journal/import; task tools/analyze or tools/extract scripts; task work_products/**; task tmp/**",
            "read_only_context": f"{raw_dir}/**; native CFD/OpenFOAM outputs; registry/admission state; scheduler state except claimed launch",
            "action": "Create a non-overlapping board row before any sampling.",
            "acceptance_signal": "Board row names exact source cases, endpoint labels, scheduler policy, and no native mutation.",
            "do_not_do": "Do not run OpenFOAM or edit native cases before the row exists.",
            "expected_output": "active board row for staged-copy sampler",
        },
        {
            "priority": 2,
            "step_id": "STEP-02",
            "title": "Stage and sample raw endpoint surfaces",
            "depends_on": "STEP-01",
            "role": "Hydraulics/cfd-pp/Implementer/Tester",
            "allowed_edit_paths": "task-owned tmp/** and work_products/** only",
            "read_only_context": f"{raw_dir}/target_feature_taps.csv; {raw_dir}/pressure_surface_sampling_contract.csv",
            "action": "Sample lower_leg__s04 and right_leg__s00 endpoint surfaces for Salt2/Salt3/Salt4 at 7915/7618/10000.",
            "acceptance_signal": "6 endpoint rows with finite p, p_rgh, U, T_or_rho, flux/area/normal reductions and exact labels.",
            "do_not_do": "Do not substitute left_lower_leg__s00/left_upper_leg__s04 precedent surfaces.",
            "expected_output": "raw_endpoint_pressure_velocity.csv",
        },
        {
            "priority": 3,
            "step_id": "STEP-03",
            "title": "Audit pressure and velocity basis",
            "depends_on": "STEP-02",
            "role": "Hydraulics/Tester",
            "allowed_edit_paths": "task-owned tools/analyze script/test and work_products/**",
            "read_only_context": f"{raw_dir}/basis_field_contract.csv; raw endpoint sampler outputs",
            "action": "Recompute feature loss, hydrostatic correction, kinetic correction, local density, and local dynamic pressure from raw endpoint outputs.",
            "acceptance_signal": "Basis reproduces feature loss without buoyancy or kinetic double counting.",
            "do_not_do": "Do not infer missing endpoint fields from proxy losses.",
            "expected_output": "pressure_velocity_basis_audit.csv",
        },
        {
            "priority": 4,
            "step_id": "STEP-04",
            "title": "Resolve straight reference and component isolation",
            "depends_on": "STEP-03",
            "role": "Hydraulics/Reviewer",
            "allowed_edit_paths": "task-owned tools/analyze script/test and work_products/**",
            "read_only_context": f"{raw_dir}/basis_field_contract.csv; pressure basis audit outputs",
            "action": "Test whether a physically comparable local straight reference gives nonnegative K_local without clipping.",
            "acceptance_signal": "Unclipped nonnegative K_local with documented reference, or apparent_cluster_only decision.",
            "do_not_do": "Do not clip K_local or introduce hidden global multipliers.",
            "expected_output": "component_isolation_audit.csv",
        },
        {
            "priority": 5,
            "step_id": "STEP-05",
            "title": "Compute same-window recirculation metrics",
            "depends_on": "STEP-02",
            "role": "Hydraulics/cfd-pp/Tester",
            "allowed_edit_paths": "task-owned tools/analyze script/test and work_products/**",
            "read_only_context": f"{raw_dir}/recirculation_metric_contract.csv; raw endpoint sampler outputs",
            "action": "Compute upstream/downstream/aggregate RAF, RMF, and SVF using declared endpoint normals.",
            "acceptance_signal": "Ordinary candidate only when aggregate RAF < 0.01 and RMF < 0.01.",
            "do_not_do": "Do not admit material reverse-flow rows.",
            "expected_output": "endpoint_recirculation_metrics.csv",
        },
        {
            "priority": 6,
            "step_id": "STEP-06",
            "title": "Attach same-QOI uncertainty status",
            "depends_on": "STEP-02;STEP-03",
            "role": "Hydraulics/Mesh-GCI/Tester",
            "allowed_edit_paths": "task-owned tools/analyze script/test and work_products/**",
            "read_only_context": f"{raw_dir}/same_qoi_uncertainty_contract.csv; raw endpoint sampler outputs",
            "action": "Repeat exact endpoint QoI over valid mesh/time family members or emit missing_no_GCI diagnostic status.",
            "acceptance_signal": "Same-QOI uncertainty bound or explicit diagnostic-only status.",
            "do_not_do": "Do not borrow unrelated GCI or fabricate monotonicity.",
            "expected_output": "same_qoi_uncertainty_audit.csv",
        },
        {
            "priority": 7,
            "step_id": "STEP-07",
            "title": "Build new extractor and admission review",
            "depends_on": "STEP-03;STEP-04;STEP-05;STEP-06",
            "role": "Hydraulics/Implementer/Reviewer/Writer",
            "allowed_edit_paths": "new task-owned extractor package only",
            "read_only_context": "raw sampler and audit packages; AGENT-530 extractor read-only",
            "action": "Consume raw/audit outputs in a new extractor/admission package and decide diagnostic versus ordinary component-K status.",
            "acceptance_signal": "Admission decision follows predeclared rules and records every failed gate.",
            "do_not_do": "Do not overwrite AGENT-530, fit F6, or admit component K from incomplete gates.",
            "expected_output": "component_admission_review.csv; next_action_or_admission_decision.json",
        },
    ]


def admission_rules() -> list[dict[str, Any]]:
    return [
        {
            "rule_id": "RULE-01",
            "condition": "raw endpoint p/p_rgh/U/density fields are missing or ambiguous",
            "decision": "diagnostic_blocked_missing_raw_endpoint_basis",
            "evidence_required": "finite labeled endpoint reductions for all required fields",
            "forbidden_shortcut": "infer endpoint pressure from preserved proxy feature loss",
        },
        {
            "rule_id": "RULE-02",
            "condition": "pressure basis double-counts hydrostatic or kinetic correction",
            "decision": "diagnostic_blocked_pressure_basis",
            "evidence_required": "separate static-p, p_rgh, hydrostatic, kinetic, and q_local ledger",
            "forbidden_shortcut": "mix p and p_rgh losses without explicit correction policy",
        },
        {
            "rule_id": "RULE-03",
            "condition": "K_local is negative after straight-reference subtraction",
            "decision": "apparent_cluster_only_or_blocked",
            "evidence_required": "unclipped nonnegative K_local with physically comparable straight reference",
            "forbidden_shortcut": "clip negative K_local",
        },
        {
            "rule_id": "RULE-04",
            "condition": "aggregate RAF >= 0.01 or aggregate RMF >= 0.01, or metrics are missing",
            "decision": "diagnostic_or_section_effective_only",
            "evidence_required": "same-window endpoint RAF/RMF/SVF",
            "forbidden_shortcut": "treat reverse-flow endpoint as ordinary K",
        },
        {
            "rule_id": "RULE-05",
            "condition": "same-QOI mesh/time uncertainty missing",
            "decision": "diagnostic_blocked_missing_same_qoi_UQ",
            "evidence_required": "same endpoint labels/formulas/sign convention over mesh/time family or explicit missing_no_GCI",
            "forbidden_shortcut": "reuse unrelated GCI",
        },
        {
            "rule_id": "RULE-06",
            "condition": "all pressure, isolation, recirculation, and UQ gates pass",
            "decision": "candidate_component_K_review_allowed",
            "evidence_required": "raw/audit package and reviewer signoff in a new admission package",
            "forbidden_shortcut": "automatic admission without separate extractor/admission review",
        },
        {
            "rule_id": "RULE-07",
            "condition": "F6 friction correction is requested",
            "decision": "route_to_separate_nonrecirculating_anchor_task",
            "evidence_required": "ordinary nonrecirculating pressure anchors independent of component-K endpoint thread",
            "forbidden_shortcut": "fit F6 from component endpoint roadmap or proxy K",
        },
    ]


def source_manifest() -> list[dict[str, Any]]:
    return [
        {
            "source_id": source_id,
            "path": rel(path),
            "exists": path.exists(),
            "role": "read-only roadmap input",
            "mutation_status": "not_mutated",
        }
        for source_id, path in SOURCES.items()
    ]


def summary_rows(blockers: list[dict[str, Any]], paths: list[dict[str, Any]], steps: list[dict[str, Any]], rules: list[dict[str, Any]]) -> list[dict[str, Any]]:
    unresolved = sum("blocking" in row["severity"] for row in blockers)
    return [
        {"category": "blocker_rows", "count": len(blockers), "interpretation": "All launch/admission gates represented."},
        {"category": "blocking_rows", "count": unresolved, "interpretation": "Rows that still block coefficient use."},
        {"category": "research_paths", "count": len(paths), "interpretation": "Concrete research lanes from staged sampling through governance."},
        {"category": "next_steps", "count": len(steps), "interpretation": "Ordered executable follow-on queue."},
        {"category": "admission_rules", "count": len(rules), "interpretation": "Decision rules for future extractor/admission package."},
        {"category": "sampling_jobs_launched", "count": 0, "interpretation": "Roadmap only."},
        {"category": "ordinary_admissions", "count": 0, "interpretation": "No F6 or component-K coefficient admitted."},
    ]


def write_readme(path: Path, summary: dict[str, Any]) -> None:
    path.write_text(
        f"""---
provenance:
  - {rel(SOURCES['launch_readiness_gate'])}
  - {rel(SOURCES['target_feature_taps'])}
  - {rel(SOURCES['raw_endpoint_summary'])}
tags: [pressure-ledger, two-tap, raw-endpoints, blockers, component-k, f6]
related:
  - .agent/status/2026-07-18_TODO-TWO-TAP-BLOCKER-ROADMAP.md
  - .agent/journal/2026-07-18/two-tap-blocker-roadmap.md
  - {rel(SOURCES['raw_plan_readme'])}
task: {TASK}
date: {DATE}
role: Hydraulics/cfd-pp/Implementer/Tester/Writer
type: work_product
status: complete
---
# Two-Tap Blocker Roadmap

Generated: `{summary['generated_at_utc']}`

## Decision

This package turns the completed `corner_lower_right` raw endpoint contract into
a blocker matrix, research-path matrix, ordered next-step queue, and admission
decision rules. It is roadmap-only: no sampling job, solver launch, F6 fit, or
component-K admission was performed.

## Outputs

- `blocker_matrix.csv`
- `research_path_matrix.csv`
- `next_step_queue.csv`
- `admission_decision_rules.csv`
- `roadmap_summary.csv`
- `source_manifest.csv`
- `summary.json`

## Counts

- Blocker rows: `{summary['blocker_rows']}`.
- Blocking rows: `{summary['blocking_rows']}`.
- Research paths: `{summary['research_paths']}`.
- Next steps: `{summary['next_steps']}`.
- Admission rules: `{summary['admission_rules']}`.
- Ordinary admissions: `0`.

## Next Executable Move

Claim a separate staged-copy cfd-pp row before any OpenFOAM sampling. The first
technical task is to sample Salt2/Salt3/Salt4 `corner_lower_right` endpoint
surfaces from `lower_leg__s04` to `right_leg__s00` at `7915/7618/10000`, writing
only into task-owned `tmp/` or `work_products/`.

## Guardrails

Do not overwrite AGENT-530. Do not infer endpoint pressure fields. Do not clip
negative `K_local`. Do not borrow unrelated GCI. Do not fit F6 or admit
component K unless a future raw-output extractor/admission package resolves all
predeclared gates.
""",
        encoding="utf-8",
    )


def build_package(out: Path = OUT) -> dict[str, Any]:
    require_sources()
    out.mkdir(parents=True, exist_ok=True)
    blockers = blocker_matrix()
    paths = research_path_matrix()
    steps = next_step_queue()
    rules = admission_rules()
    manifest = source_manifest()
    summary_table = summary_rows(blockers, paths, steps, rules)
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
    write_csv(out / "blocker_matrix.csv", blockers, BLOCKER_COLUMNS)
    write_csv(out / "research_path_matrix.csv", paths, PATH_COLUMNS)
    write_csv(out / "next_step_queue.csv", steps, STEP_COLUMNS)
    write_csv(out / "admission_decision_rules.csv", rules, RULE_COLUMNS)
    write_csv(out / "roadmap_summary.csv", summary_table, SUMMARY_COLUMNS)
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
