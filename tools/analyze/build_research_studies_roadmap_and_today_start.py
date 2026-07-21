#!/usr/bin/env python3
"""Build AGENT-518 research-studies roadmap and today-start package."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


TASK = "AGENT-518"
DATE = "2026-07-17"
ROOT = Path(__file__).resolve().parents[2]
OUT_REL = Path("work_products/2026-07/2026-07-17/2026-07-17_research_studies_roadmap_and_today_start")
OUT = ROOT / OUT_REL

SOURCES = {
    "research_pathways": ROOT / "reports/2026-07/2026-07-13/2026-07-13_litrev_lessons_and_research_pathways/research_pathways.csv",
    "litrev_map": ROOT / "operational_notes/maps/literature-synthesis-and-gates.md",
    "forward_map": ROOT / "operational_notes/maps/forward-predictive-model.md",
    "friction_map": ROOT / "operational_notes/maps/friction-closures.md",
    "blockers": ROOT / ".agent/blockers.yml",
    "f6_anchor_summary": ROOT / "work_products/2026-07/2026-07-17/2026-07-17_f6_anchor_first_refinement/summary.json",
    "f6_anchor_gate": ROOT / "work_products/2026-07/2026-07-17/2026-07-17_f6_anchor_first_refinement/anchor_gate_table.csv",
    "f6_ladder": ROOT / "work_products/2026-07/2026-07-17/2026-07-17_f6_litrev_hydraulic_model_form_ladder/hydraulic_model_form_ladder.csv",
    "f6_decision_tree": ROOT / "work_products/2026-07/2026-07-17/2026-07-17_f6_litrev_hydraulic_model_form_ladder/anchor_first_decision_tree.csv",
    "segment_pressure_summary": ROOT / "work_products/2026-07/2026-07-17/2026-07-17_predict_segment_pressure_models/summary.json",
    "segment_thermal_summary": ROOT / "work_products/2026-07/2026-07-17/2026-07-17_predict_segment_thermal_models/summary.json",
    "wall_failure_summary": ROOT / "work_products/2026-07/2026-07-17/2026-07-17_wall_candidate_failure_localization/summary.json",
    "wall_next_ladder": ROOT / "work_products/2026-07/2026-07-17/2026-07-17_wall_candidate_failure_localization/next_candidate_ladder.csv",
    "upcomer_anchor_matrix": ROOT / "work_products/2026-07/2026-07-17/2026-07-17_upcomer_onset_cfd_anchor_matrix/README.md",
    "final_scorecard_shell": ROOT / "work_products/2026-07/2026-07-17/2026-07-17_final_predictive_scorecard_shell/summary.json",
}

STUDY_COLUMNS = [
    "rank",
    "study_id",
    "title",
    "lane",
    "start_window",
    "scientific_leverage",
    "execution_cost",
    "dependency",
    "blocker_unblock_potential",
    "thesis_value",
    "primary_outputs",
    "acceptance_gate",
    "provenance",
    "status_today",
    "guardrail",
]

TODAY_COLUMNS = [
    "sequence",
    "today_task",
    "role",
    "implementation_kind",
    "input_paths",
    "outputs",
    "acceptance_signal",
    "blocker_touched",
    "do_not_do",
    "handoff",
]

CAMPAIGN_COLUMNS = [
    "wave",
    "lane",
    "agent_role",
    "trigger",
    "actions",
    "deliverables",
    "acceptance_gate",
    "downstream_dependency",
    "guardrails",
]

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


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


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
        raise FileNotFoundError("Missing AGENT-518 source files: " + ", ".join(missing))


def open_blockers(path: Path) -> list[str]:
    blockers: list[dict[str, str]] = []
    current: dict[str, str] | None = None
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line.startswith("- id:"):
            if current:
                blockers.append(current)
            current = {"id": line.split(":", 1)[1].strip()}
        elif current and line.startswith("status:"):
            current["status"] = line.split(":", 1)[1].strip()
    if current:
        blockers.append(current)
    return sorted(row["id"] for row in blockers if row.get("status") == "open")


def pathway(rows: list[dict[str, str]], key: str) -> dict[str, str]:
    for row in rows:
        if row.get("pathway") == key:
            return row
    raise KeyError(key)


def semicolon(paths: list[Path]) -> str:
    return ";".join(rel(path) for path in paths)


def build_study_priority_matrix(pathways: list[dict[str, str]]) -> list[dict[str, Any]]:
    return [
        {
            "rank": 1,
            "study_id": "terminal_anchor_and_f6_gate",
            "title": "Terminal high-heat/PM10 anchor harvest and ordinary F6 gate",
            "lane": "hydraulic_f6",
            "start_window": "when live jobs are terminal",
            "scientific_leverage": "very_high",
            "execution_cost": "medium_after_jobs_finish",
            "dependency": "PM10/high-heat terminal outputs; same-window pressure and reverse-flow metrics",
            "blocker_unblock_potential": "f6-friction-re-correction; upcomer-onset-data-sparsity",
            "thesis_value": "decides whether ordinary F6 is admissible or recirculation-mode closure is required",
            "primary_outputs": "U,T,wallHeatFlux,Re/Pr/Ri/Gr/Ra/Gz,wall-core DeltaT,RAF/RMF/SVF,steady-window,UQ",
            "acceptance_gate": "RAF < 0.01 and RMF < 0.01 plus same-window pressure loss before ordinary F6 scoring",
            "provenance": semicolon([SOURCES["f6_anchor_gate"], SOURCES["f6_ladder"]]),
            "status_today": "contract_ready_wait_for_terminal",
            "guardrail": "Do not fit ordinary F6 from PM5 or non-terminal rows.",
        },
        {
            "rank": 2,
            "study_id": "source_envelope_refresh",
            "title": pathway(pathways, "source_envelope")["thing_to_try"],
            "lane": "litrev_gate",
            "start_window": "today",
            "scientific_leverage": "very_high",
            "execution_cost": "low",
            "dependency": "existing LitRev gate output plus current branch/segment rows",
            "blocker_unblock_potential": "all closure lanes; prevents out-of-envelope promotion",
            "thesis_value": "chapter-ready table linking literature validity to TAMU operating space",
            "primary_outputs": pathway(pathways, "source_envelope")["expected_product"],
            "acceptance_gate": pathway(pathways, "source_envelope")["acceptance_gate"],
            "provenance": rel(SOURCES["research_pathways"]),
            "status_today": "startable_existing_evidence",
            "guardrail": "Author/title provenance only; no closure promotion from overlap alone.",
        },
        {
            "rank": 3,
            "study_id": "property_mode_carryforward",
            "title": pathway(pathways, "properties")["thing_to_try"],
            "lane": "litrev_gate",
            "start_window": "today",
            "scientific_leverage": "very_high",
            "execution_cost": "low_to_medium",
            "dependency": "property-mode sensitivity package and every future fit/score table",
            "blocker_unblock_potential": "prevents pressure/heat residuals from absorbing property error",
            "thesis_value": "defensible uncertainty axis for all hydraulic and thermal claims",
            "primary_outputs": pathway(pathways, "properties")["expected_product"],
            "acceptance_gate": pathway(pathways, "properties")["acceptance_gate"],
            "provenance": rel(SOURCES["research_pathways"]),
            "status_today": "startable_existing_evidence",
            "guardrail": "Do not mix replication and updated-property modes inside one fitted residual.",
        },
        {
            "rank": 4,
            "study_id": "reset_development_and_named_pressure",
            "title": "Hydraulic reset/development map plus named pressure-loss extraction contract",
            "lane": "hydraulic_pressure",
            "start_window": "today_for_ledger; after terminal for scoring",
            "scientific_leverage": "high",
            "execution_cost": "medium",
            "dependency": "reset map, pressure ledger, admitted two-tap/plane pressure basis",
            "blocker_unblock_potential": "f6-friction-re-correction",
            "thesis_value": "replaces global friction tuning with a branchwise pressure ledger",
            "primary_outputs": "reset-distance rows; component/cluster/branch-apparent pressure-loss rows",
            "acceptance_gate": "velocity basis, pressure basis, straight-loss subtraction, recovery/development, and UQ explicit",
            "provenance": semicolon([SOURCES["research_pathways"], SOURCES["f6_ladder"]]),
            "status_today": "ledger_startable_scoring_blocked",
            "guardrail": "No universal K and no hidden global friction multiplier.",
        },
        {
            "rank": 5,
            "study_id": "cfd_validity_on_every_reduction",
            "title": pathway(pathways, "cfd_validity")["thing_to_try"],
            "lane": "cfd_admission",
            "start_window": "today_for_schema; terminal harvest for data",
            "scientific_leverage": "high",
            "execution_cost": "medium",
            "dependency": "postprocessed planes with reverse and secondary-flow metrics",
            "blocker_unblock_potential": "upcomer-onset-data-sparsity; f6-friction-re-correction",
            "thesis_value": "separates single-stream closure rows from section-effective diagnostics",
            "primary_outputs": pathway(pathways, "cfd_validity")["expected_product"],
            "acceptance_gate": pathway(pathways, "cfd_validity")["acceptance_gate"],
            "provenance": rel(SOURCES["research_pathways"]),
            "status_today": "schema_startable",
            "guardrail": "Never export ordinary f_D/K/Nu names from material recirculation rows.",
        },
        {
            "rank": 6,
            "study_id": "wall_temperature_shape_physics",
            "title": "Wall/test-section local temperature-shape physics study",
            "lane": "thermal_wall",
            "start_window": "after active AGENT-511/513 results land",
            "scientific_leverage": "high",
            "execution_cost": "medium",
            "dependency": "wall failure localization, heater source redistribution, wall-temperature-drive candidate",
            "blocker_unblock_potential": "predictive-wall-test-section-submodels",
            "thesis_value": "explains why mdot can improve while TP/TW fields regress",
            "primary_outputs": "segment heat-placement errors, probe-localization rows, next wall/fluid coupling candidate contract",
            "acceptance_gate": "improve mdot without worsening all-probe/TW RMSE versus M3 on validation/holdout",
            "provenance": semicolon([SOURCES["wall_failure_summary"], SOURCES["wall_next_ladder"]]),
            "status_today": "readiness_synthesis_only_due_active_agents",
            "guardrail": "No realized wallHeatFlux, CFD mdot, imposed cooler duty, or validation temperatures at runtime.",
        },
        {
            "rank": 7,
            "study_id": "heat_loss_separation_and_radiation_bound",
            "title": "Separated heat-loss ledger plus radiation bound",
            "lane": "thermal_boundary",
            "start_window": "today_for_existing_evidence",
            "scientific_leverage": "high",
            "execution_cost": "low_to_medium",
            "dependency": "LitRev heat-loss gate, boundary/radiation packages, wall/passive evidence",
            "blocker_unblock_potential": "predictive-wall-test-section-submodels",
            "thesis_value": "prevents internal HTC from absorbing jacket/passive/radiation residuals",
            "primary_outputs": "jacket, passive, radiation, heater-efficiency, wall/storage, and residual rows",
            "acceptance_gate": "internal Nu cannot be adjusted until external heat paths are separated and bounded",
            "provenance": rel(SOURCES["research_pathways"]),
            "status_today": "startable_existing_evidence",
            "guardrail": "Do not zero radiation or fold passive loss into Nu without a quantitative bound.",
        },
        {
            "rank": 8,
            "study_id": "conditional_internal_htc_bakeoff",
            "title": "Conditional branchwise internal HTC bakeoff",
            "lane": "thermal_internal_htc",
            "start_window": "after source-envelope and heat-loss separation",
            "scientific_leverage": "medium_high",
            "execution_cost": "medium",
            "dependency": "source envelope, property lane, heat-loss separation, non-recirculating branch masks",
            "blocker_unblock_potential": "thermal closure credibility; not current primary blocker",
            "thesis_value": "shows why Nu forms are gated rather than tuned",
            "primary_outputs": pathway(pathways, "internal_htc")["expected_product"],
            "acceptance_gate": pathway(pathways, "internal_htc")["acceptance_gate"],
            "provenance": rel(SOURCES["research_pathways"]),
            "status_today": "plan_only_until_gates",
            "guardrail": "Do not use recirculating upcomer rows as ordinary Nu evidence.",
        },
        {
            "rank": 9,
            "study_id": "instrumentation_pressure_and_thermal",
            "title": "Pressure-tap and thermal instrumentation design",
            "lane": "experiment_design",
            "start_window": "this_week_after ledgers identify highest-value locations",
            "scientific_leverage": "medium_high",
            "execution_cost": "planning_low_experiment_high",
            "dependency": "pressure residual localization and wall/test-section failure localization",
            "blocker_unblock_potential": "future direct validation of F6/named losses and wall HTC",
            "thesis_value": "future-work plan grounded in current blocker anatomy",
            "primary_outputs": "tap placement, uncertainty, expected K/f extraction, wall/coolant temperature priorities",
            "acceptance_gate": "static, hydrostatic, kinetic, straight-pipe, fitting, wall, jacket, and internal-h terms separated",
            "provenance": rel(SOURCES["research_pathways"]),
            "status_today": "outline_startable",
            "guardrail": "Do not present experiment plan as evidence already available.",
        },
        {
            "rank": 10,
            "study_id": "rom_archive_schema_future_only",
            "title": "ROM-ready archive schema without ROM prediction claim",
            "lane": "future_method",
            "start_window": "after closure tables stabilize",
            "scientific_leverage": "medium",
            "execution_cost": "medium",
            "dependency": "stable FOM outputs, closure/admission rows, withheld validation metadata",
            "blocker_unblock_potential": "none immediate; preserves future option",
            "thesis_value": "future-work appendix and data-management discipline",
            "primary_outputs": pathway(pathways, "rom")["expected_product"],
            "acceptance_gate": pathway(pathways, "rom")["acceptance_gate"],
            "provenance": rel(SOURCES["research_pathways"]),
            "status_today": "future_only",
            "guardrail": "No ROM prediction claim until FOM, snapshots, stabilization, and withheld validation exist.",
        },
    ]


def build_today_start_ledger() -> list[dict[str, Any]]:
    return [
        {
            "sequence": 1,
            "today_task": "Create existing-evidence research-roadmap package",
            "role": "Coordinator/Writer/Implementer/Tester",
            "implementation_kind": "repo-local builder plus tests",
            "input_paths": semicolon([SOURCES["research_pathways"], SOURCES["f6_ladder"], SOURCES["blockers"]]),
            "outputs": "study_priority_matrix.csv; today_start_ledger.csv; multi_agent_campaign_sequence.csv; thesis_roadmap.md; handoff_tomorrow.md",
            "acceptance_signal": "package builds from source files and tests enforce guardrails",
            "blocker_touched": "all three open blockers as planning rows only",
            "do_not_do": "no solver, scheduler, generated-index refresh, fitting, or scientific admission change",
            "handoff": "Tomorrow starts from handoff_tomorrow.md and study_priority_matrix.csv.",
        },
        {
            "sequence": 2,
            "today_task": "Prepare terminal-harvest contract for high-heat/PM10 anchors",
            "role": "cfd-pp/Hydraulics",
            "implementation_kind": "contract/readiness ledger only",
            "input_paths": semicolon([SOURCES["f6_anchor_gate"], SOURCES["f6_decision_tree"]]),
            "outputs": "full output contract and ordinary-anchor classification rules",
            "acceptance_signal": "every future row requires U,T,wallHeatFlux,dimensionless groups,RAF/RMF/SVF,DeltaT,steady-window,UQ",
            "blocker_touched": "f6-friction-re-correction; upcomer-onset-data-sparsity",
            "do_not_do": "do not harvest non-terminal jobs or fit PM5 rows",
            "handoff": "Claim a separate terminal-harvest task only when scheduler/output state is terminal.",
        },
        {
            "sequence": 3,
            "today_task": "Refresh source-envelope and property-mode carryforward requirements",
            "role": "Literature-synthesis/Tester",
            "implementation_kind": "existing-evidence ledger",
            "input_paths": rel(SOURCES["research_pathways"]),
            "outputs": "closure-gate rows listing source overlap and property-lane labels required by each future scorecard",
            "acceptance_signal": "every closure row has inside/outside/unknown overlap and property mode",
            "blocker_touched": "all closure promotion lanes",
            "do_not_do": "do not calibrate residuals before property sensitivity is carried forward",
            "handoff": "Use these rows as required columns in F6, HTC, heat-loss, and CFD-reduction tasks.",
        },
        {
            "sequence": 4,
            "today_task": "Convert reset/named-loss path into extraction-ready acceptance criteria",
            "role": "Hydraulics/Writer",
            "implementation_kind": "contract before extraction",
            "input_paths": semicolon([SOURCES["f6_ladder"], SOURCES["segment_pressure_summary"]]),
            "outputs": "pressure-basis, velocity-basis, straight-loss, development, recovery, and UQ checklist",
            "acceptance_signal": "future pressure rows cannot be marked admitted without all basis fields",
            "blocker_touched": "f6-friction-re-correction",
            "do_not_do": "no universal K and no hidden global multiplier",
            "handoff": "Next implementer can build raw connector/tap extraction against this checklist.",
        },
        {
            "sequence": 5,
            "today_task": "Wall/test-section candidate handoff after active jobs land",
            "role": "Thermal-modeling/Forward-pred",
            "implementation_kind": "dependency-aware next-candidate queue",
            "input_paths": semicolon([SOURCES["wall_failure_summary"], SOURCES["wall_next_ladder"]]),
            "outputs": "wall-temperature/source-placement/axial-mixing/wall-fluid-coupling sequence",
            "acceptance_signal": "candidate must improve mdot without increasing all-probe/TW RMSE versus M3",
            "blocker_touched": "predictive-wall-test-section-submodels",
            "do_not_do": "do not duplicate active AGENT-511/513 scoring or consume validation temperatures at runtime",
            "handoff": "Wait for active AGENT-511/513 results before choosing the next coupled run.",
        },
        {
            "sequence": 6,
            "today_task": "Thesis roadmap synthesis",
            "role": "Writer/Reviewer",
            "implementation_kind": "package-local narrative only",
            "input_paths": semicolon([SOURCES["litrev_map"], SOURCES["forward_map"], SOURCES["friction_map"]]),
            "outputs": "thesis_roadmap.md",
            "acceptance_signal": "each study maps to a chapter/table/figure and lists blocked claims",
            "blocker_touched": "all open blockers as thesis structure",
            "do_not_do": "do not edit reports/thesis_dossier while AGENT-516 is active",
            "handoff": "AGENT-516 or a later thesis agent can import the roadmap after scope clears.",
        },
    ]


def build_campaign_sequence() -> list[dict[str, Any]]:
    return [
        {
            "wave": 1,
            "lane": "coordination_and_gates",
            "agent_role": "Coordinator/Writer",
            "trigger": "now",
            "actions": "Publish today package; preserve open blockers; define required columns for future scorecards",
            "deliverables": "study matrix, today ledger, campaign sequence, thesis roadmap, tomorrow handoff",
            "acceptance_gate": "all rows have provenance, acceptance gate, and guardrail",
            "downstream_dependency": "all later agents use the package as open-first context",
            "guardrails": "no solver, scheduler, registry, native output, or generated-index mutation",
        },
        {
            "wave": 2,
            "lane": "terminal_anchor_harvest",
            "agent_role": "cfd-pp/Hydraulics/Tester",
            "trigger": "PM10/high-heat jobs become terminal",
            "actions": "Harvest terminal rows; compute dimensionless groups, reverse-flow metrics, pressure residuals, steady windows, and UQ",
            "deliverables": "anchor gate table and ordinary-vs-recirculation classification",
            "acceptance_gate": "ordinary F6 rows require RAF < 0.01 and RMF < 0.01 plus same-window pressure loss",
            "downstream_dependency": "F6 phi(Re) bakeoff or recirculation-mode onset lane",
            "guardrails": "PM5 remains diagnostic; no non-terminal harvest; no scientific admission by default",
        },
        {
            "wave": 3,
            "lane": "hydraulic_pressure_models",
            "agent_role": "Hydraulics/Implementer/Tester",
            "trigger": "admitted pressure-basis fields or raw connector/tap extraction available",
            "actions": "Build reset-distance/development rows and named component/cluster pressure-loss rows",
            "deliverables": "pressure ledger with velocity basis, straight-loss subtraction, development/recovery, and UQ",
            "acceptance_gate": "score against F3_shah_apparent with pressure residual primary and mdot guardrail",
            "downstream_dependency": "F6 or named-loss closure candidate can be scored",
            "guardrails": "no one global friction multiplier; no universal K",
        },
        {
            "wave": 4,
            "lane": "thermal_wall_models",
            "agent_role": "Thermal-modeling/Forward-pred/Tester",
            "trigger": "AGENT-511 and AGENT-513 results are complete",
            "actions": "Choose the next non-duplicative wall candidate: wall-temperature drive, heater/source placement, axial mixing, or wall/fluid coupling",
            "deliverables": "runtime-legal candidate contracts plus coupled M3+TS+cooler scorecard",
            "acceptance_gate": "validation/holdout mdot improves without all-probe/TW RMSE regression versus M3",
            "downstream_dependency": "corrected freeze and final predictive scorecard",
            "guardrails": "no realized wallHeatFlux, CFD mdot, imposed cooler duty, or validation temperatures at runtime",
        },
        {
            "wave": 5,
            "lane": "heat_loss_radiation_internal_htc",
            "agent_role": "Thermal-modeling/Literature-synthesis",
            "trigger": "source-envelope and property-mode carryforward rows are attached to scorecards",
            "actions": "Separate heat-loss paths, bound radiation, then run conditional internal HTC bakeoff only where envelope overlap allows",
            "deliverables": "separated heat ledger, radiation bound, branch HTC bakeoff score table",
            "acceptance_gate": "temperature improvement cannot corrupt heat-loss residual or use recirculating rows as ordinary Nu",
            "downstream_dependency": "thermal closure chapter and predictive wall path",
            "guardrails": "internal Nu cannot absorb jacket/passive/radiation/source-placement residuals",
        },
        {
            "wave": 6,
            "lane": "thesis_and_future_experiment",
            "agent_role": "Writer/Reviewer",
            "trigger": "wave 2-5 packages produce durable results",
            "actions": "Update thesis claims, figures, tables, pressure-tap plan, thermal instrumentation plan, and future ROM archive note",
            "deliverables": "chapter-ready updates and future-work study design",
            "acceptance_gate": "claims state evidence class, split, blocker status, and caveats",
            "downstream_dependency": "weekly presentation and thesis finalization",
            "guardrails": "do not turn future experiment/ROM plans into current evidence claims",
        },
    ]


def write_thesis_roadmap(path: Path, summary: dict[str, Any], studies: list[dict[str, Any]]) -> None:
    top_rows = "\n".join(
        f"| {row['rank']} | `{row['study_id']}` | {row['lane']} | {row['thesis_value']} |"
        for row in studies[:8]
    )
    text = f"""---
provenance:
  - {rel(SOURCES['research_pathways'])}
  - {rel(SOURCES['f6_ladder'])}
  - {rel(SOURCES['wall_failure_summary'])}
  - {rel(SOURCES['blockers'])}
tags: [research-roadmap, thesis-roadmap, closure-ledger, forward-model]
related:
  - {rel(OUT_REL / 'study_priority_matrix.csv')}
  - {rel(OUT_REL / 'multi_agent_campaign_sequence.csv')}
task: {TASK}
date: {DATE}
role: Coordinator/Writer
type: work_product
status: complete
---
# Thesis Research Roadmap

Generated: `{summary['generated_at_utc']}`

## Thesis Use

The research program should be presented as a branchwise closure-ledger workflow,
not a search for one fitted coefficient. The current open blockers are
`predictive-wall-test-section-submodels`, `upcomer-onset-data-sparsity`, and
`f6-friction-re-correction`. Each study below either resolves one of those
blockers, protects the model from an invalid closure promotion, or produces a
chapter-ready limitation/future-work artifact.

## Study-To-Thesis Map

| Rank | Study | Lane | Thesis value |
| --- | --- | --- | --- |
{top_rows}

## Chapter Contributions

- Literature/method chapter: source-envelope, property-mode, reset/development,
  heat-loss separation, and CFD-validity gates show why the model uses a
  branchwise ledger instead of global `f`, `Nu`, `K`, or `UA`.
- Hydraulic chapter: terminal anchor harvest, F6 `phi(Re)`, reset-distance, and
  named-loss studies decide whether the pressure model can move beyond
  `F3_shah_apparent`.
- Thermal chapter: wall/test-section temperature-shape, heat-loss/radiation,
  and conditional HTC studies separate source placement, passive loss, and
  internal heat transfer.
- Predictive chapter: the campaign sequence preserves runtime legality and
  canonical split discipline before any corrected freeze or final scorecard.
- Future-work chapter: pressure taps, thermal instrumentation, and ROM archive
  design are framed as planned evidence pathways, not current validation.

## Claims Not Yet Allowed

- No ordinary F6 closure from PM5 rows.
- No universal fitting `K`, hidden global friction multiplier, or global `Nu`.
- No internal HTC adjustment that absorbs jacket, passive, radiation, wall, or
  source-placement residuals.
- No final predictive claim until the wall/test-section blocker and final
  scorecard gates clear.
- No ROM prediction claim until stable full-order outputs, snapshots, and
  withheld validation exist.
"""
    path.write_text(text, encoding="utf-8")


def write_handoff(path: Path, summary: dict[str, Any]) -> None:
    text = f"""---
provenance:
  - {rel(OUT_REL / 'study_priority_matrix.csv')}
  - {rel(OUT_REL / 'today_start_ledger.csv')}
  - {rel(OUT_REL / 'multi_agent_campaign_sequence.csv')}
tags: [handoff, research-roadmap, tomorrow-start]
related:
  - {rel(OUT_REL / 'README.md')}
task: {TASK}
date: {DATE}
role: Coordinator/Writer
type: work_product
status: complete
---
# Tomorrow Handoff

Generated: `{summary['generated_at_utc']}`

## Open First

1. `{rel(OUT_REL / 'README.md')}`
2. `{rel(OUT_REL / 'study_priority_matrix.csv')}`
3. `{rel(OUT_REL / 'today_start_ledger.csv')}`
4. `{rel(OUT_REL / 'multi_agent_campaign_sequence.csv')}`
5. `{rel(OUT_REL / 'thesis_roadmap.md')}`

## Current State

- Production hydraulic closure remains `F3_shah_apparent`.
- PM5 rows remain recirculation diagnostics: `12` diagnostic rows and `0`
  ordinary F6 scoreable rows.
- Terminal PM10/high-heat rows are still contract-gated, not harvested here.
- Segment pressure rows have `0` fit-admitted pressure closures.
- Segment thermal rows have setup-admitted heater/cooler support but `0`
  residual internal-Nu fit admissions.
- Wall/test-section candidates remain blocked because mdot improvements are
  paired with TP/TW or all-probe regression.

## Next Actions

- If high-heat/PM10 jobs are terminal, claim a separate terminal-harvest task
  and apply the output contract from `today_start_ledger.csv`.
- If they are not terminal, start the low-cost existing-evidence lanes:
  source-envelope refresh, property-mode carryforward, reset/named-loss
  extraction checklist, and heat-loss/radiation separation ledger.
- Wait for active AGENT-511/513 results before launching another wall/test-section
  coupled candidate, then choose a non-duplicative temperature-shape model.

## Do Not Do

- Do not mutate native CFD/OpenFOAM outputs, registry/admission state, scheduler
  state, Fluid source, or generated index files from this package.
- Do not fit ordinary F6 from PM5, tune a global multiplier, or promote a closure
  without the predeclared gates.
"""
    path.write_text(text, encoding="utf-8")


def write_readme(path: Path, summary: dict[str, Any]) -> None:
    text = f"""---
provenance:
  - {rel(SOURCES['research_pathways'])}
  - {rel(SOURCES['f6_ladder'])}
  - {rel(SOURCES['wall_failure_summary'])}
  - {rel(SOURCES['segment_pressure_summary'])}
  - {rel(SOURCES['segment_thermal_summary'])}
  - {rel(SOURCES['blockers'])}
tags: [research-roadmap, closure-ledger, thesis-roadmap, forward-model]
related:
  - .agent/status/2026-07-17_AGENT-518.md
  - .agent/journal/2026-07-17/research-studies-roadmap-and-today-start.md
task: {TASK}
date: {DATE}
role: Coordinator/Writer/Implementer/Tester
type: work_product
status: complete
---
# Research Studies Roadmap And Today-Start Package

Generated: `{summary['generated_at_utc']}`

## Decision

The highest-value studies are gate/ledger studies that make future closure
claims identifiable: terminal anchor harvest, source envelope, property-mode
carryforward, reset/named pressure losses, CFD validity diagnostics, wall
temperature-shape physics, heat-loss/radiation separation, and conditional HTC.
This package does not launch jobs or promote any model.

## Outputs

- `study_priority_matrix.csv`
- `today_start_ledger.csv`
- `multi_agent_campaign_sequence.csv`
- `thesis_roadmap.md`
- `handoff_tomorrow.md`
- `source_manifest.csv`
- `summary.json`

## Current Counts

- Study rows: `{summary['study_rows']}`.
- Today-start rows: `{summary['today_rows']}`.
- Campaign waves: `{summary['campaign_rows']}`.
- Open blockers preserved: `{', '.join(summary['open_blockers'])}`.
- PM5 ordinary F6 scoreable rows: `{summary['ordinary_f6_scoreable_rows']}`.
- PM5 recirculation diagnostic rows: `{summary['pm5_recirculation_diagnostic_rows']}`.
- Segment pressure fit-admitted rows: `{summary['fit_admitted_pressure_rows']}`.
- Residual internal-Nu fit-admitted rows: `{summary['residual_internal_nu_fit_admitted_rows']}`.

## Guardrails

No native CFD outputs, registry/admission state, scheduler state, external Fluid
files, generated index files, thesis-dossier files, or active-agent scoped
artifacts were mutated. This is a planning and synthesis package, not a solver
run, postprocessing harvest, model fit, or scientific admission change.
"""
    path.write_text(text, encoding="utf-8")


def build_source_manifest() -> list[dict[str, Any]]:
    return [
        {
            "source_id": key,
            "path": rel(path),
            "exists": path.exists(),
            "role": "read-only evidence for roadmap synthesis",
        }
        for key, path in SOURCES.items()
    ]


def build_package(out: Path = OUT) -> dict[str, Any]:
    require_sources()
    out.mkdir(parents=True, exist_ok=True)

    pathways = read_csv(SOURCES["research_pathways"])
    f6_summary = read_json(SOURCES["f6_anchor_summary"])
    segment_pressure = read_json(SOURCES["segment_pressure_summary"])
    segment_thermal = read_json(SOURCES["segment_thermal_summary"])
    wall_summary = read_json(SOURCES["wall_failure_summary"])
    blockers = open_blockers(SOURCES["blockers"])

    studies = build_study_priority_matrix(pathways)
    today = build_today_start_ledger()
    campaign = build_campaign_sequence()
    manifest = build_source_manifest()

    summary = {
        "task": TASK,
        "date": DATE,
        "generated_at_utc": utc_now(),
        "output_dir": rel(out),
        "study_rows": len(studies),
        "today_rows": len(today),
        "campaign_rows": len(campaign),
        "source_rows": len(manifest),
        "open_blockers": blockers,
        "production_closure": f6_summary.get("production_closure", "F3_shah_apparent"),
        "ordinary_f6_scoreable_rows": f6_summary.get("ordinary_f6_scoreable_rows", 0),
        "pm5_recirculation_diagnostic_rows": f6_summary.get("pm5_recirculation_diagnostic_rows", 12),
        "blocked_pending_terminal_rows": f6_summary.get("blocked_pending_terminal_rows", 8),
        "fit_admitted_pressure_rows": segment_pressure.get("fit_admitted_pressure_rows", 0),
        "scoreable_predictive_model_rows": segment_pressure.get("scoreable_predictive_model_rows", 0),
        "admitted_setup_model_rows": segment_thermal.get("admitted_setup_model_rows", 0),
        "residual_internal_nu_fit_admitted_rows": segment_thermal.get("residual_internal_nu_fit_admitted_rows", 0),
        "admitted_wall_candidates": wall_summary.get("admitted_wall_candidates", 0),
        "scientific_admission_change": "none",
        "native_output_mutation": "none",
        "registry_mutation": "none",
        "scheduler_action": "none",
        "external_fluid_edit": "none",
        "generated_index_refresh": "not_run_active_AGENT_517_owns_generated_index_paths",
    }

    write_csv(out / "study_priority_matrix.csv", studies, STUDY_COLUMNS)
    write_csv(out / "today_start_ledger.csv", today, TODAY_COLUMNS)
    write_csv(out / "multi_agent_campaign_sequence.csv", campaign, CAMPAIGN_COLUMNS)
    write_csv(out / "source_manifest.csv", manifest, MANIFEST_COLUMNS)
    write_thesis_roadmap(out / "thesis_roadmap.md", summary, studies)
    write_handoff(out / "handoff_tomorrow.md", summary)
    write_readme(out / "README.md", summary)
    write_json(out / "summary.json", summary)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=OUT, help="Output directory")
    args = parser.parse_args()
    summary = build_package(args.out)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
