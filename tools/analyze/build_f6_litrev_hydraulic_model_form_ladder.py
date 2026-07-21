#!/usr/bin/env python3
"""Build AGENT-512 LitRev-guided F6/hydraulic model-form ladder."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


TASK = "AGENT-512"
DATE = "2026-07-17"
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "work_products/2026-07/2026-07-17/2026-07-17_f6_litrev_hydraulic_model_form_ladder"

F6_ANCHOR_DIR = ROOT / "work_products/2026-07/2026-07-17/2026-07-17_f6_anchor_first_refinement"
LITREV_DIR = ROOT / "reports/2026-07/2026-07-13/2026-07-13_litrev_lessons_and_research_pathways"
BOUNDARY_LAYER_DIR = ROOT / "work_products/2026-07/2026-07-17/2026-07-17_predict_boundary_layer_development_scorecard"

F6_SUMMARY = F6_ANCHOR_DIR / "summary.json"
F6_ANCHOR_GATE = F6_ANCHOR_DIR / "anchor_gate_table.csv"
F6_LANE_DECISION = F6_ANCHOR_DIR / "f6_lane_decision.csv"
F6_NEXT_CFD = F6_ANCHOR_DIR / "recommended_next_cfd_runs.csv"
LITREV_UNTRIED = LITREV_DIR / "untried_litrev_model_forms.csv"
LITREV_REJECTED = LITREV_DIR / "rejected_or_demoted_litrev_shortcuts.csv"
LITREV_CROSSWALK = LITREV_DIR / "litrev_to_current_evidence_crosswalk.csv"
BOUNDARY_PREREQ = BOUNDARY_LAYER_DIR / "prerequisite_gate_scorecard.csv"
BOUNDARY_TOGGLES = BOUNDARY_LAYER_DIR / "development_toggle_scorecard.csv"

SOURCES = {
    "f6_anchor_summary": (F6_SUMMARY, "current anchor-first F6 state"),
    "f6_anchor_gate": (F6_ANCHOR_GATE, "PM5/PM10/high-heat anchor lane gates"),
    "f6_lane_decision": (F6_LANE_DECISION, "current F6 lane decision table"),
    "f6_next_cfd_runs": (F6_NEXT_CFD, "Salt3 onset-matrix recommendations"),
    "litrev_untried_forms": (LITREV_UNTRIED, "LitRev model-form backlog"),
    "litrev_rejected_shortcuts": (LITREV_REJECTED, "LitRev guardrails and demotions"),
    "litrev_crosswalk": (LITREV_CROSSWALK, "LitRev to current evidence crosswalk"),
    "boundary_prereq": (BOUNDARY_PREREQ, "boundary-layer prerequisite gates"),
    "boundary_toggles": (BOUNDARY_TOGGLES, "boundary-layer toggle readiness"),
}

LADDER_COLUMNS = [
    "tier",
    "rank",
    "model_form",
    "research_decision",
    "current_gate_status",
    "current_blocker",
    "required_gate",
    "next_executable_action",
    "allowed_use_now",
    "forbidden_use",
    "primary_sources",
    "evidence_path",
]

ANCHOR_TREE_COLUMNS = [
    "sequence",
    "evidence_stage",
    "condition",
    "decision",
    "next_action",
    "outputs_required",
    "source_path",
]

CROSSWALK_COLUMNS = [
    "model_family",
    "litrev_form_or_lesson",
    "provenance_author_title",
    "tried_status",
    "evidence_class",
    "current_status",
    "next_action",
    "current_ethan_evidence",
]

SHORTCUT_COLUMNS = ["shortcut", "demoted_to", "reason", "allowed_use", "forbidden_use", "current_evidence"]
MANIFEST_COLUMNS = ["source_id", "path", "exists", "role"]

HYDRAULIC_CROSSWALK_FAMILIES = {
    "property_modes",
    "pressure_ledger",
    "fully_developed_friction_reference",
    "developing_redeveloping_friction",
    "component_cluster_k",
    "f6_phi_re",
    "h1_localized_fixed_k",
    "nonuniform_heating_inclination",
    "upcomer_recirculation_rule",
    "corrected_q_re_variation",
    "transient_extension",
    "rom_extension",
}


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
            writer.writerow({key: "" if row.get(key) is None else str(row.get(key, "")) for key in columns})
    return len(materialized)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def require_sources() -> None:
    missing = [rel(path) for path, _role in SOURCES.values() if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing AGENT-512 source files: " + ", ".join(missing))


def find_untried(rows: list[dict[str, str]], prefix: str) -> dict[str, str]:
    for row in rows:
        if row.get("model_form", "").startswith(prefix):
            return row
    raise KeyError(prefix)


def shortcut_by_prefix(rows: list[dict[str, str]], prefix: str) -> dict[str, str]:
    for row in rows:
        if row.get("shortcut", "").startswith(prefix):
            return row
    raise KeyError(prefix)


def build_ladder(
    f6_summary: dict[str, Any],
    untried_rows: list[dict[str, str]],
    rejected_rows: list[dict[str, str]],
    boundary_prereq_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    f6 = find_untried(untried_rows, "F6 phi(Re)")
    reset = find_untried(untried_rows, "Faithful H1 reset/development")
    upcomer = find_untried(untried_rows, "Upcomer internal Nu")
    property_rows = find_untried(untried_rows, "Nonuniform heating")
    transient = find_untried(untried_rows, "Transient")
    rom = find_untried(untried_rows, "ROM/POD")
    fd_friction = shortcut_by_prefix(rejected_rows, "Fully developed f_D=64/Re")
    global_f = shortcut_by_prefix(rejected_rows, "One global friction multiplier")
    universal_k = shortcut_by_prefix(rejected_rows, "Universal K")
    recirc_labels = shortcut_by_prefix(rejected_rows, "Universal f_D/K/Nu")
    prereq_status = "; ".join(f"{row['gate']}={row['status']}({row['admitted_rows']})" for row in boundary_prereq_rows)

    return [
        {
            "tier": "1_anchor_first",
            "rank": 1,
            "model_form": "Terminal anchor harvest and ordinary F6 gate",
            "research_decision": "try_first",
            "current_gate_status": f"ordinary_anchors={f6_summary.get('pm5_ordinary_anchor_rows', 0)}; blocked_pending_terminal={f6_summary.get('blocked_pending_terminal_rows', 0)}",
            "current_blocker": "PM10/high-heat terminal harvest and full output-contract postprocessing missing",
            "required_gate": "RAF < 0.01, RMF < 0.01, same-window pressure loss, Re/Ri/properties, steady-window/UQ",
            "next_executable_action": "Harvest high-heat and PM10 only after terminal; classify before fitting",
            "allowed_use_now": "readiness and gate planning",
            "forbidden_use": "ordinary F6 fit from PM5 or non-terminal rows",
            "primary_sources": "AGENT-505 anchor-first refinement",
            "evidence_path": rel(F6_ANCHOR_GATE),
        },
        {
            "tier": "1_hydraulic_candidate",
            "rank": 2,
            "model_form": f6["model_form"],
            "research_decision": "try_after_anchor_gate",
            "current_gate_status": "blocked_no_admitted_Re_variation_rows",
            "current_blocker": f6["current_blocker"],
            "required_gate": f6["required_gate"],
            "next_executable_action": f6["next_executable_action"],
            "allowed_use_now": "candidate form definition and future scorecard shell",
            "forbidden_use": "promotion without pressure-loss validation and holdout mdot guardrail",
            "primary_sources": f6["primary_sources"],
            "evidence_path": f6["primary_sources"],
        },
        {
            "tier": "1_hydraulic_candidate",
            "rank": 3,
            "model_form": "Reset-distance / redevelopment pressure loss",
            "research_decision": "prepare_extraction_and_api",
            "current_gate_status": "blocked_no_admitted_pressure_rows",
            "current_blocker": reset["current_blocker"],
            "required_gate": reset["required_gate"],
            "next_executable_action": reset["next_executable_action"],
            "allowed_use_now": "diagnostic/reset ledger and implementation planning",
            "forbidden_use": fd_friction["forbidden_use"],
            "primary_sources": reset["primary_sources"],
            "evidence_path": reset["primary_sources"],
        },
        {
            "tier": "1_hydraulic_candidate",
            "rank": 4,
            "model_form": "Named component/cluster/branch-apparent pressure losses",
            "research_decision": "prepare_extraction_not_fit",
            "current_gate_status": "blocked_0_fit_admissible_component_or_cluster_K_rows",
            "current_blocker": "raw two-tap connector extraction and admission missing",
            "required_gate": "admitted tap/plane pressure basis plus velocity basis, split, development, recovery, and UQ",
            "next_executable_action": "Extract raw connector rows, admit component/cluster K, then score against F3",
            "allowed_use_now": universal_k["allowed_use"],
            "forbidden_use": universal_k["forbidden_use"],
            "primary_sources": "Lin et al.; Patino-Jaramillo et al.; Salehi et al.; LitRev reset/named-loss gate",
            "evidence_path": reset["primary_sources"],
        },
        {
            "tier": "1_hydraulic_candidate",
            "rank": 5,
            "model_form": "Recirculation-modeled section-effective loss / onset penalty",
            "research_decision": "try_if_no_low_reverse_anchor",
            "current_gate_status": "diagnostic_only_12_PM5_recirc_rows_0_scoreable",
            "current_blocker": upcomer["current_blocker"],
            "required_gate": "same-window RAF/RMF/SVF, pressure residual movement, Delta T, Gz, mesh/time UQ, validation/holdout improvement",
            "next_executable_action": "After terminal harvest, score named section-effective/onset penalty only if features and residual movement exist",
            "allowed_use_now": recirc_labels["allowed_use"],
            "forbidden_use": recirc_labels["forbidden_use"],
            "primary_sources": upcomer["primary_sources"],
            "evidence_path": rel(F6_ANCHOR_GATE),
        },
        {
            "tier": "2_boundary_layer",
            "rank": 6,
            "model_form": "Boundary-layer development toggles",
            "research_decision": "diagnostic_ready_not_executable",
            "current_gate_status": prereq_status,
            "current_blocker": "segment pressure blocked; thermal partial; ordinary-pipe branch aggregate blocked; upcomer hybrid diagnostic only",
            "required_gate": "admitted pressure/thermal closure rows before coupled ablation",
            "next_executable_action": "Keep toggle contracts; wait for pressure/thermal admissions before runtime ablation",
            "allowed_use_now": "diagnostic scorecard and ablation contract",
            "forbidden_use": "coupled score claim before prerequisite gates pass",
            "primary_sources": "boundary-layer development scorecard; Shah; Muzychka-Yovanovich",
            "evidence_path": rel(BOUNDARY_PREREQ),
        },
        {
            "tier": "2_sensitivity_diagnostic",
            "rank": 7,
            "model_form": "Property-lane sensitivity before residual fitting",
            "research_decision": "carry_in_every_scorecard",
            "current_gate_status": "sensitivity_package_exists",
            "current_blocker": "active property lane must be declared before calibration",
            "required_gate": "separate replication and updated-property modes in every fit/score table",
            "next_executable_action": "Propagate property mode labels into all future hydraulic scorecards",
            "allowed_use_now": "sensitivity and uncertainty axis",
            "forbidden_use": "mixing replication and updated properties inside one fitted residual",
            "primary_sources": "Reis Seo Hassan; Sohal; Jin; Parida/Basu; Santini",
            "evidence_path": "work_products/2026-07/2026-07-13/2026-07-13_litrev_property_sensitivity/README.md",
        },
        {
            "tier": "2_sensitivity_diagnostic",
            "rank": 8,
            "model_form": property_rows["model_form"],
            "research_decision": "metadata_diagnostic",
            "current_gate_status": "not_encoded_in_branch_scorecards",
            "current_blocker": property_rows["current_blocker"],
            "required_gate": property_rows["required_gate"],
            "next_executable_action": property_rows["next_executable_action"],
            "allowed_use_now": "diagnostic metadata and future stratification",
            "forbidden_use": "active closure outside matched geometry/range/BC overlap",
            "primary_sources": property_rows["primary_sources"],
            "evidence_path": property_rows["primary_sources"],
        },
        {
            "tier": "3_future_method",
            "rank": 9,
            "model_form": transient["model_form"],
            "research_decision": "future_only",
            "current_gate_status": "outside_current_steady_scope",
            "current_blocker": transient["current_blocker"],
            "required_gate": transient["required_gate"],
            "next_executable_action": transient["next_executable_action"],
            "allowed_use_now": "thesis future-work note",
            "forbidden_use": "steady closure calibration shortcut",
            "primary_sources": transient["primary_sources"],
            "evidence_path": transient["primary_sources"],
        },
        {
            "tier": "3_future_method",
            "rank": 10,
            "model_form": rom["model_form"],
            "research_decision": "future_only",
            "current_gate_status": "no_snapshot_validation_package",
            "current_blocker": rom["current_blocker"],
            "required_gate": rom["required_gate"],
            "next_executable_action": rom["next_executable_action"],
            "allowed_use_now": "archive-design requirement",
            "forbidden_use": "predictive ROM claim",
            "primary_sources": rom["primary_sources"],
            "evidence_path": rom["primary_sources"],
        },
        {
            "tier": "guardrail",
            "rank": 99,
            "model_form": "One global friction multiplier",
            "research_decision": "forbidden",
            "current_gate_status": "rejected_by_litrev",
            "current_blocker": "not a valid model-form path",
            "required_gate": "none; use separated pressure ledger instead",
            "next_executable_action": global_f["allowed_use"],
            "allowed_use_now": global_f["allowed_use"],
            "forbidden_use": global_f["forbidden_use"],
            "primary_sources": "LitRev reset/named-loss gate",
            "evidence_path": global_f["current_evidence"],
        },
    ]


def build_anchor_tree(f6_summary: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "sequence": 1,
            "evidence_stage": "PM5 current evidence",
            "condition": f"ordinary_anchors={f6_summary.get('pm5_ordinary_anchor_rows', 0)}; recirc_rows={f6_summary.get('pm5_recirculation_diagnostic_rows', 0)}",
            "decision": "diagnostic_only",
            "next_action": "Do not fit ordinary F6 from PM5.",
            "outputs_required": "none; existing PM5 gate table is sufficient for diagnostic status",
            "source_path": rel(F6_ANCHOR_GATE),
        },
        {
            "sequence": 2,
            "evidence_stage": "PM10/high-heat terminal harvest",
            "condition": f"blocked_or_unknown_rows={f6_summary.get('blocked_pending_terminal_rows', 0)}",
            "decision": "wait_for_terminal_then_harvest",
            "next_action": "Claim separate terminal harvest/postprocess task when jobs are terminal.",
            "outputs_required": "U;T;wallHeatFlux;Re/Pr/Ri/Gr/Ra/Gz;DeltaT;RAF/RMF/SVF;pressure residuals;steady-window;UQ",
            "source_path": rel(F6_ANCHOR_GATE),
        },
        {
            "sequence": 3,
            "evidence_stage": "Ordinary anchor gate",
            "condition": "RAF < 0.01 and RMF < 0.01 with same-window pressure loss",
            "decision": "run_F6_phi_Re_bakeoff",
            "next_action": "Score pressure residual primary and mdot guardrail against F3_shah_apparent.",
            "outputs_required": "train/validation/holdout score with no hidden global multiplier",
            "source_path": rel(F6_LANE_DECISION),
        },
        {
            "sequence": 4,
            "evidence_stage": "No ordinary anchors after terminal harvest",
            "condition": "terminal rows remain material-recirculating",
            "decision": "run_Salt3_sentinels_before_full_matrix",
            "next_action": "Stage high-Re/high-insulation and low-Q/low-insulation sentinels before full Q x insulation matrix.",
            "outputs_required": "same output contract as terminal harvest plus mesh/time uncertainty",
            "source_path": rel(F6_NEXT_CFD),
        },
        {
            "sequence": 5,
            "evidence_stage": "Recirculation-modeled lane",
            "condition": "material reverse flow plus pressure residual movement and complete features",
            "decision": "score_named_section_effective_or_onset_penalty",
            "next_action": "Use only section-effective/onset labels, never ordinary f_D/K/Nu.",
            "outputs_required": "RAF/RMF/SVF;DeltaT;Gz;pressure residual;UQ;validation/holdout improvement",
            "source_path": rel(F6_LANE_DECISION),
        },
        {
            "sequence": 6,
            "evidence_stage": "Reset/named-loss path",
            "condition": "raw connector/tap evidence becomes admitted",
            "decision": "prepare_reset_development_and_component_K_score",
            "next_action": "Score named losses only after admitted pressure basis and reset distance exist.",
            "outputs_required": "pressure basis;velocity basis;split;development/recovery;component/cluster label;UQ",
            "source_path": "work_products/2026-07/2026-07-13/2026-07-13_litrev_reset_named_losses/README.md",
        },
    ]


def build_crosswalk(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    return [
        {column: row.get(column, "") for column in CROSSWALK_COLUMNS}
        for row in rows
        if row.get("model_family") in HYDRAULIC_CROSSWALK_FAMILIES
    ]


def build_forbidden_shortcuts(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    prefixes = [
        "One global friction multiplier",
        "Fully developed f_D=64/Re",
        "Universal K",
        "Localized fixed K",
        "Universal f_D/K/Nu",
        "ROM prediction claim",
    ]
    selected = []
    for prefix in prefixes:
        selected.append(shortcut_by_prefix(rows, prefix))
    return selected


def build_manifest() -> list[dict[str, Any]]:
    return [
        {"source_id": source_id, "path": rel(path), "exists": "yes" if path.exists() else "no", "role": role}
        for source_id, (path, role) in SOURCES.items()
    ]


def write_readme(path: Path, generated_at: str, summary: dict[str, Any]) -> None:
    path.write_text(
        f"""---
provenance:
  - {rel(F6_SUMMARY)}
  - {rel(LITREV_UNTRIED)}
  - {rel(LITREV_CROSSWALK)}
  - {rel(BOUNDARY_PREREQ)}
tags: [f6, friction, litrev, hydraulic-model-forms]
related:
  - .agent/status/2026-07-17_AGENT-512.md
  - .agent/journal/2026-07-17/f6-litrev-hydraulic-model-form-ladder.md
task: {TASK}
date: {DATE}
role: Hydraulics/Literature-synthesis/Implementer/Tester/Writer
type: work_product
status: complete
---
# F6 LitRev Hydraulic Model-Form Ladder

Generated: `{generated_at}`

## Decision

This package ranks the hydraulic/friction model forms worth trying next. It
does not promote a closure. Anchor-first remains the research path: terminal
PM10/high-heat rows must produce admitted low-reverse pressure anchors before
ordinary F6 can be scored.

## Current Counts

- Ladder rows: `{summary["ladder_rows"]}`.
- Anchor tree rows: `{summary["anchor_tree_rows"]}`.
- LitRev hydraulic crosswalk rows: `{summary["crosswalk_rows"]}`.
- Forbidden shortcut rows: `{summary["forbidden_shortcut_rows"]}`.
- PM5 ordinary anchors: `{summary["pm5_ordinary_anchor_rows"]}`.
- PM5 recirculation diagnostics: `{summary["pm5_recirculation_diagnostic_rows"]}`.
- Production closure: `{summary["production_closure"]}`.
- Promotion allowed now: `{summary["promotion_allowed"]}`.

## Outputs

- `hydraulic_model_form_ladder.csv`
- `anchor_first_decision_tree.csv`
- `litrev_hydraulic_crosswalk.csv`
- `forbidden_shortcuts.csv`
- `source_manifest.csv`
- `summary.json`

## Guardrails

No native CFD outputs, registry/admission state, scheduler state, external
Fluid files, blocker register, generated index files, or active-agent scopes
were mutated. The package is a research planning and evidence-ranking artifact,
not a CFD launch, terminal harvest, or model admission.
""",
        encoding="utf-8",
    )


def build_package(out_dir: Path = OUT) -> dict[str, Any]:
    require_sources()
    generated_at = utc_now()
    out_dir.mkdir(parents=True, exist_ok=True)

    f6_summary = read_json(F6_SUMMARY)
    anchor_gate_rows = read_csv(F6_ANCHOR_GATE)
    untried_rows = read_csv(LITREV_UNTRIED)
    rejected_rows = read_csv(LITREV_REJECTED)
    crosswalk_source_rows = read_csv(LITREV_CROSSWALK)
    boundary_prereq_rows = read_csv(BOUNDARY_PREREQ)

    ladder_rows = build_ladder(f6_summary, untried_rows, rejected_rows, boundary_prereq_rows)
    anchor_tree_rows = build_anchor_tree(f6_summary)
    crosswalk_rows = build_crosswalk(crosswalk_source_rows)
    shortcut_rows = build_forbidden_shortcuts(rejected_rows)
    manifest_rows = build_manifest()

    write_csv(out_dir / "hydraulic_model_form_ladder.csv", ladder_rows, LADDER_COLUMNS)
    write_csv(out_dir / "anchor_first_decision_tree.csv", anchor_tree_rows, ANCHOR_TREE_COLUMNS)
    write_csv(out_dir / "litrev_hydraulic_crosswalk.csv", crosswalk_rows, CROSSWALK_COLUMNS)
    write_csv(out_dir / "forbidden_shortcuts.csv", shortcut_rows, SHORTCUT_COLUMNS)
    write_csv(out_dir / "source_manifest.csv", manifest_rows, MANIFEST_COLUMNS)

    anchor_counts = Counter(row.get("lane", "") for row in anchor_gate_rows)
    summary = {
        "task": TASK,
        "date": DATE,
        "generated_at_utc": generated_at,
        "output_dir": rel(out_dir),
        "ladder_rows": len(ladder_rows),
        "anchor_tree_rows": len(anchor_tree_rows),
        "crosswalk_rows": len(crosswalk_rows),
        "forbidden_shortcut_rows": len(shortcut_rows),
        "pm5_ordinary_anchor_rows": f6_summary.get("pm5_ordinary_anchor_rows", anchor_counts.get("ordinary_F6_anchor", 0)),
        "pm5_recirculation_diagnostic_rows": f6_summary.get("pm5_recirculation_diagnostic_rows", anchor_counts.get("recirculation_diagnostic", 0)),
        "blocked_pending_terminal_rows": f6_summary.get("blocked_pending_terminal_rows", anchor_counts.get("blocked_pending_terminal", 0)),
        "boundary_layer_executable_rows": 0,
        "production_closure": "F3_shah_apparent",
        "promotion_allowed": "no",
        "native_output_mutation": "none",
        "registry_mutation": "none",
        "scheduler_action": "none",
        "scientific_admission_change": "none",
        "generated_index_refresh": "not_run_active_agents_own_generated_index_paths",
    }
    write_json(out_dir / "summary.json", summary)
    write_readme(out_dir / "README.md", generated_at, summary)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=OUT)
    args = parser.parse_args()
    summary = build_package(args.out_dir)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
