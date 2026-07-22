#!/usr/bin/env python3
"""Screen existing pressure evidence for alternate low-reverse anchors.

This reducer is intentionally no-launch and fail-closed. It asks whether
existing PM5/PM10/branch/inventory evidence can replace the lower-right
CAND001 path without revisiting the failed component-K route.
"""

from __future__ import annotations

import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.common import WORKSPACE_ROOT, csv_dump, ensure_dir, iso_timestamp, json_dump, relative_to_workspace


TASK_ID = "TODO-PRESSURE-ALTERNATE-LOW-REVERSE-ANCHOR-SCREEN-2026-07-22"
OUT = WORKSPACE_ROOT / (
    "work_products/2026-07/2026-07-22/"
    "2026-07-22_pressure_alternate_low_reverse_anchor_screen"
)

SOURCES = {
    "low_recirc_inventory": WORKSPACE_ROOT
    / "work_products/2026-07/2026-07-22/2026-07-22_pressure_low_recirc_nonrecirc_anchor_inventory",
    "anchor_first": WORKSPACE_ROOT
    / "work_products/2026-07/2026-07-17/2026-07-17_f6_anchor_first_refinement",
    "branch_scorecard": WORKSPACE_ROOT
    / "work_products/2026-07/2026-07-17/2026-07-17_branch_specific_ordinary_pipe_scorecard",
    "pm10_terminal": WORKSPACE_ROOT
    / "work_products/2026-07/2026-07-22/2026-07-22_predict_salt_pm10_terminal_admission",
}


def rel(path: Path) -> str:
    return relative_to_workspace(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def require_sources() -> None:
    required = [
        SOURCES["low_recirc_inventory"] / "summary.json",
        SOURCES["low_recirc_inventory"] / "anchor_inventory_gate.csv",
        SOURCES["anchor_first"] / "anchor_gate_table.csv",
        SOURCES["anchor_first"] / "recommended_next_cfd_runs.csv",
        SOURCES["branch_scorecard"] / "ordinary_pipe_branch_mask.csv",
        SOURCES["pm10_terminal"] / "summary.json",
        SOURCES["pm10_terminal"] / "pm10_recirc_onset_summary.csv",
        SOURCES["pm10_terminal"] / "pm10_case_terminal_gate.csv",
    ]
    missing = [rel(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("missing pressure alternate-anchor sources: " + "; ".join(missing))


def as_float(value: str) -> float | str:
    return "" if value == "" else float(value)


def bool_string(value: str) -> bool:
    return value.lower() in {"true", "yes"}


def add_common(
    rows: list[dict[str, Any]],
    *,
    evidence_id: str,
    evidence_family: str,
    case_or_branch: str,
    basis_status: str,
    reverse_flow_status: str,
    endpoint_status: str,
    same_qoi_uq_status: str,
    terminal_status: str,
    disqualification_reasons: list[str],
    next_action: str,
    source_paths: str,
    raf: float | str = "",
    rmf: float | str = "",
    evidence_is_existing: bool = True,
) -> None:
    rows.append(
        {
            "evidence_id": evidence_id,
            "evidence_family": evidence_family,
            "case_or_branch": case_or_branch,
            "evidence_is_existing": evidence_is_existing,
            "basis_status": basis_status,
            "max_RAF": raf,
            "max_RMF": rmf,
            "reverse_flow_status": reverse_flow_status,
            "endpoint_status": endpoint_status,
            "same_qoi_uq_status": same_qoi_uq_status,
            "terminal_status": terminal_status,
            "can_replace_CAND001_now": False,
            "component_K_or_F6_release_allowed": False,
            "admissible_comparison_allowed_now": False,
            "disqualification_reasons": ";".join(disqualification_reasons),
            "next_action": next_action,
            "claim_boundary": "section-effective residual evidence only; no component-K, F6, Shah, fit, or mixed-basis promotion",
            "source_paths": source_paths,
        }
    )


def alternate_anchor_screen() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    for row in read_csv(SOURCES["low_recirc_inventory"] / "anchor_inventory_gate.csv"):
        if row["preferred_future_anchor"] != "True":
            continue
        reasons = [item for item in row["primary_blockers"].split(";") if item]
        add_common(
            rows,
            evidence_id="inventory:" + row["candidate_id"],
            evidence_family="preferred_inventory_slot",
            case_or_branch=f"{row['case_id']}:{row['branch']}",
            basis_status=row["candidate_bucket"],
            raf=as_float(row["max_RAF_sampled_now"]),
            rmf=as_float(row["max_RMF_sampled_now"]),
            reverse_flow_status="ordinary_flow_pass" if row["ordinary_flow_pass_now"] == "True" else "ordinary_flow_failed_or_unsampled",
            endpoint_status="ready" if row["endpoint_pair_ready_now"] == "True" else "missing_or_failed",
            same_qoi_uq_status="ready" if row["same_qoi_uq_ready_now"] == "True" else "missing",
            terminal_status="inventory_only",
            disqualification_reasons=reasons,
            next_action=row["next_unblock_action"],
            source_paths=row["source_paths"],
        )

    for row in read_csv(SOURCES["anchor_first"] / "anchor_gate_table.csv"):
        if row["evidence_family"] != "PM5":
            continue
        add_common(
            rows,
            evidence_id=row["row_id"],
            evidence_family="pm5_recirculation_diagnostic",
            case_or_branch=f"{row['case_key']}:{row['lane']}",
            basis_status=row["pressure_evidence"],
            raf=as_float(row["RAF"]),
            rmf=as_float(row["RMF"]),
            reverse_flow_status=row["reverse_flow_gate"],
            endpoint_status="not_admitted_for_anchor",
            same_qoi_uq_status="missing",
            terminal_status="existing_diagnostic",
            disqualification_reasons=[
                "material_reverse_flow",
                "missing_hybrid_admission_evidence",
                "same_qoi_uq_missing",
            ],
            next_action=row["next_action"],
            source_paths=row["source_path"],
        )

    terminal_by_case = {row["case_key"]: row for row in read_csv(SOURCES["pm10_terminal"] / "pm10_case_terminal_gate.csv")}
    for row in read_csv(SOURCES["pm10_terminal"] / "pm10_recirc_onset_summary.csv"):
        terminal = terminal_by_case[row["case_key"]]
        reasons = [
            "strong_material_reverse_flow",
            "total_Q_drifting",
            "future_blind_holdout_only",
            "ordinary_pipe_fit_forbidden",
        ]
        add_common(
            rows,
            evidence_id="pm10:" + row["case_key"],
            evidence_family="pm10_terminal_recirculation_diagnostic",
            case_or_branch=f"{row['case_key']}:upcomer",
            basis_status=terminal["admission_disposition"],
            raf=as_float(row["max_reverse_area_fraction"]),
            rmf=as_float(row["max_reverse_mass_fraction"]),
            reverse_flow_status=row["recirculation_severity_class"],
            endpoint_status="terminal_evidence_only",
            same_qoi_uq_status="missing",
            terminal_status=f"{terminal['terminal_evidence_admitted']}; {terminal['total_Q_verdict']}",
            disqualification_reasons=reasons,
            next_action="keep as recirculation/onset diagnostic; do not use as ordinary low-reverse pressure anchor",
            source_paths=";".join(
                [
                    rel(SOURCES["pm10_terminal"] / "pm10_recirc_onset_summary.csv"),
                    rel(SOURCES["pm10_terminal"] / "pm10_case_terminal_gate.csv"),
                ]
            ),
        )

    for row in read_csv(SOURCES["branch_scorecard"] / "ordinary_pipe_branch_mask.csv"):
        reasons = [item for item in row["blocked_labels"].split(";") if item]
        if row["ordinary_pipe_fit_included"] != "true":
            reasons.append("ordinary_pipe_fit_not_included")
        add_common(
            rows,
            evidence_id="branch:" + row["branch_id"],
            evidence_family="branch_scorecard_mask",
            case_or_branch=row["branch_id"],
            basis_status=row["admission_status"],
            reverse_flow_status=row["reason"],
            endpoint_status="branch_aggregate_not_endpoint_anchor",
            same_qoi_uq_status="missing_or_failed",
            terminal_status="not_case_terminal_anchor",
            disqualification_reasons=reasons,
            next_action=row["reason"],
            source_paths=row["source_paths"],
        )

    for row in read_csv(SOURCES["anchor_first"] / "recommended_next_cfd_runs.csv"):
        add_common(
            rows,
            evidence_id="future_design:" + row["case_key"],
            evidence_family="future_onset_anchor_design",
            case_or_branch=row["case_key"],
            basis_status=row["target_regime"],
            reverse_flow_status="not_yet_measured",
            endpoint_status="not_yet_available",
            same_qoi_uq_status="not_yet_available",
            terminal_status="not_launched_in_this_task",
            evidence_is_existing=False,
            disqualification_reasons=[
                "future_run_not_existing_evidence",
                "reverse_flow_unverified",
                "endpoint_pair_missing",
                "same_qoi_uq_missing",
                "scheduler_launch_forbidden_in_this_row",
            ],
            next_action=row["precondition"],
            source_paths=row["source_path"],
        )
    return rows


def disqualification_matrix(screen: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counts: Counter[str] = Counter()
    families: defaultdict[str, set[str]] = defaultdict(set)
    for row in screen:
        for reason in row["disqualification_reasons"].split(";"):
            if reason:
                counts[reason] += 1
                families[reason].add(row["evidence_family"])

    guidance = {
        "material_reverse_flow": "find lower-recirculation or nonrecirculating anchors before F6 comparison",
        "strong_material_reverse_flow": "keep PM10 as recirculation/onset evidence only",
        "same_qoi_uq_missing": "build same-label same-formula same-sign pressure UQ after endpoint/source readiness",
        "future_run_not_existing_evidence": "claim a separate launch/monitor row if terminal evidence remains insufficient",
        "total_Q_drifting": "do not use terminal PM10 rows for runtime/source release or closure fitting",
        "future_blind_holdout_only": "preserve as protected future evidence, not train/model-selection data",
    }
    rows = []
    for reason, count in sorted(counts.items(), key=lambda item: (-item[1], item[0])):
        rows.append(
            {
                "blocker": reason,
                "affected_rows": count,
                "affected_families": ";".join(sorted(families[reason])),
                "blocks_CAND001_replacement_now": True,
                "next_unblock_action": guidance.get(reason, "keep row fail-closed until its source-specific gate is cleared"),
                "forbidden_shortcut": "do not promote diagnostic pressure residuals to component-K/F6/Shah closure evidence",
            }
        )
    return rows


def no_launch_shortlist(screen: list[dict[str, Any]]) -> list[dict[str, Any]]:
    existing_replacements = sum(row["can_replace_CAND001_now"] for row in screen if row["evidence_is_existing"])
    future_rows = [row for row in screen if row["evidence_family"] == "future_onset_anchor_design"]
    return [
        {
            "priority": 1,
            "candidate_or_action": "CAND001 terminal disposition",
            "status": "owned by active scheduler monitor row; not queried or harvested here",
            "can_do_in_this_task": False,
            "unlock_signal": "terminal lower-recirculation source evidence with finite endpoint fields",
            "forbidden_action": "scheduler query/action or duplicate harvest from this row",
        },
        {
            "priority": 2,
            "candidate_or_action": "existing PM5/PM10/branch/inventory replacement anchor",
            "status": f"{existing_replacements} existing rows can replace CAND001 now",
            "can_do_in_this_task": False,
            "unlock_signal": "an existing row must pass reverse-flow, endpoint, same-QOI UQ, source, and admission gates",
            "forbidden_action": "use recirculation diagnostics as ordinary F6 anchors",
        },
        {
            "priority": 3,
            "candidate_or_action": "future onset-anchor design shortlist",
            "status": f"{len(future_rows)} future designs preserved as no-launch candidates",
            "can_do_in_this_task": False,
            "unlock_signal": "separate launch row after current terminal/source evidence is exhausted",
            "forbidden_action": "launch, stage, or mutate solver/source outputs from this screen",
        },
    ]


def source_manifest() -> list[dict[str, str]]:
    return [
        {"source_id": key, "path": rel(path), "mutation": "read_only", "role": "evidence source"}
        for key, path in SOURCES.items()
    ]


def no_mutation_guardrails() -> list[dict[str, Any]]:
    return [
        {"guardrail": "native_output_mutation", "value": False},
        {"guardrail": "registry_or_admission_mutation", "value": False},
        {"guardrail": "scheduler_query_or_action", "value": False},
        {"guardrail": "solver_postprocessing_sampler_harvest_uq_launched", "value": False},
        {"guardrail": "fitting_or_model_selection", "value": False},
        {"guardrail": "component_K_or_F6_or_Shah_release", "value": False},
        {"guardrail": "candidate_freeze", "value": False},
        {"guardrail": "mixed_basis_promotion", "value": False},
    ]


def write_readme(out: Path, summary: dict[str, Any]) -> None:
    text = f"""---
provenance:
  - {rel(SOURCES['low_recirc_inventory'] / 'anchor_inventory_gate.csv')}
  - {rel(SOURCES['anchor_first'] / 'anchor_gate_table.csv')}
  - {rel(SOURCES['pm10_terminal'] / 'pm10_recirc_onset_summary.csv')}
tags: [pressure, f6, low-reverse-anchor, no-launch, no-admission]
related:
  - .agent/status/2026-07-22_{TASK_ID}.md
  - .agent/journal/2026-07-22/pressure-alternate-low-reverse-anchor-screen.md
  - imports/2026-07-22_pressure_alternate_low_reverse_anchor_screen.json
task: {TASK_ID}
date: 2026-07-22
role: Hydraulics/Implementer/Tester/Writer/Reviewer
type: work_product
status: complete
---
# Pressure Alternate Low-Reverse Anchor Screen

Decision: `{summary['decision']}`.

This package screens existing pressure evidence after the lower-right two-tap
component-isolation path failed. It treats the lower-right evidence as
section-effective residual evidence and asks whether any existing PM5, PM10,
branch-mask, or inventory row can replace `CAND001`.

Key counts:

- screen rows: `{summary['screen_rows']}`
- existing evidence rows: `{summary['existing_evidence_rows']}`
- future design rows: `{summary['future_design_rows']}`
- existing replacement-ready rows: `{summary['existing_replacement_ready_rows']}`
- PM10 strong-recirculation rows: `{summary['pm10_strong_recirculation_rows']}`
- future designs preserved without launch: `{summary['future_design_rows']}`

Primary outputs:

- `alternate_anchor_screen.csv`
- `disqualification_matrix.csv`
- `no_launch_shortlist.csv`
- `source_manifest.csv`
- `no_mutation_guardrails.csv`
- `summary.json`

No scheduler query/action, launch, harvest, sampler/UQ run, fitting, model
selection, component-K/F6/Shah release, source/property release, candidate
freeze, or native-output mutation occurred.
"""
    (out / "README.md").write_text(text, encoding="utf-8")


def build(out: Path = OUT) -> dict[str, Any]:
    require_sources()
    ensure_dir(out)

    screen = alternate_anchor_screen()
    disq = disqualification_matrix(screen)
    shortlist = no_launch_shortlist(screen)
    guardrails = no_mutation_guardrails()

    csv_dump(out / "alternate_anchor_screen.csv", list(screen[0].keys()), screen)
    csv_dump(out / "disqualification_matrix.csv", list(disq[0].keys()), disq)
    csv_dump(out / "no_launch_shortlist.csv", list(shortlist[0].keys()), shortlist)
    csv_dump(out / "source_manifest.csv", ["source_id", "path", "mutation", "role"], source_manifest())
    csv_dump(out / "no_mutation_guardrails.csv", ["guardrail", "value"], guardrails)

    by_family = Counter(row["evidence_family"] for row in screen)
    summary = {
        "task_id": TASK_ID,
        "generated_at": iso_timestamp(),
        "decision": "pressure_alternate_anchor_screen_complete_existing_replacement_not_found",
        "screen_rows": len(screen),
        "existing_evidence_rows": sum(row["evidence_is_existing"] for row in screen),
        "future_design_rows": by_family.get("future_onset_anchor_design", 0),
        "rows_by_family": dict(sorted(by_family.items())),
        "existing_replacement_ready_rows": sum(
            row["can_replace_CAND001_now"] for row in screen if row["evidence_is_existing"]
        ),
        "component_K_or_F6_release_rows": sum(row["component_K_or_F6_release_allowed"] for row in screen),
        "admissible_comparison_allowed_rows": sum(row["admissible_comparison_allowed_now"] for row in screen),
        "pm10_strong_recirculation_rows": sum(
            row["evidence_family"] == "pm10_terminal_recirculation_diagnostic"
            and row["reverse_flow_status"] == "strong_recirculation"
            for row in screen
        ),
        "pm5_material_reverse_flow_rows": sum(
            row["evidence_family"] == "pm5_recirculation_diagnostic"
            and "material_reverse_flow" in row["disqualification_reasons"]
            for row in screen
        ),
        "same_qoi_uq_ready_rows": sum(row["same_qoi_uq_status"] == "ready" for row in screen),
        "scheduler_query_or_action": False,
        "solver_postprocessing_sampler_harvest_uq_launched": False,
        "native_output_mutation": False,
        "registry_or_admission_mutation": False,
        "fitting_or_model_selection": False,
        "candidate_freeze": False,
    }
    json_dump(out / "summary.json", summary)
    write_readme(out, summary)
    return summary


def main() -> None:
    summary = build()
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
