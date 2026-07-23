#!/usr/bin/env python3
"""Build a thesis appendix handoff from the PASSIVE-H2 diagnostic bundle."""

from __future__ import annotations

import csv
import json
import shutil
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.common import csv_dump, ensure_dir, iso_timestamp, json_dump, relative_to_workspace

TASK_ID = "TODO-PASSIVE-H2-THESIS-EVIDENCE-APPENDIX-HANDOFF-2026-07-22"
SLUG = "passive_h2_thesis_evidence_appendix_handoff"
OUT = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_passive_h2_thesis_evidence_appendix_handoff"
STATUS = ROOT / f".agent/status/2026-07-22_{TASK_ID}.md"
JOURNAL = ROOT / ".agent/journal/2026-07-22/passive-h2-thesis-evidence-appendix-handoff.md"
IMPORT = ROOT / f"imports/2026-07-22_{SLUG}.json"

SOURCE = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_passive_h2_thesis_diagnostic_bundle_runtime_contract_source_disposition"
PREDICTIVE = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_passive_h2_predictive_finish_readiness_closure"
HOLDOUT = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_holdout_readiness_all_models_fastest_path"


def rel(path: Path) -> str:
    return relative_to_workspace(path)


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def source_manifest_rows() -> list[dict[str, str]]:
    paths = [
        ("diagnostic_bundle_summary", SOURCE / "summary.json"),
        ("diagnostic_score_bundle", SOURCE / "thesis_diagnostic_score_bundle.csv"),
        ("runtime_diagnostic", SOURCE / "passive_h2_four_case_runtime_diagnostic.csv"),
        ("runtime_input_contract", SOURCE / "no_score_runtime_input_contract.csv"),
        ("runtime_output_contract", SOURCE / "no_score_runtime_output_contract.csv"),
        ("source_property_disposition", SOURCE / "source_property_final_disposition.csv"),
        ("figure_manifest", SOURCE / "figure_manifest.csv"),
        ("figure_caption_bank", SOURCE / "figure_caption_bank.csv"),
        ("claim_language", SOURCE / "thesis_claim_language.csv"),
        ("predictive_finish_summary", PREDICTIVE / "summary.json"),
        ("holdout_readiness_summary", HOLDOUT / "summary.json"),
    ]
    return [{"role": role, "path": rel(path), "mode": "read_only", "exists": str(path.exists()).lower()} for role, path in paths]


def copy_figures() -> list[dict[str, str]]:
    rows = []
    for row in read_csv(SOURCE / "figure_manifest.csv"):
        src = SOURCE / row["filename"]
        dest = OUT / "figures" / Path(row["filename"]).name
        ensure_dir(dest.parent)
        if src.exists():
            shutil.copy2(src, dest)
        rows.append(
            {
                "figure_id": row["figure_id"],
                "source_path": rel(src),
                "handoff_path": rel(dest),
                "exists": str(dest.exists()).lower(),
                "data_rows": row["data_rows"],
                "primary_message": row["primary_message"],
                "caption_caveat": row["caption_caveat"],
            }
        )
    return rows


def appendix_numeric_evidence_rows() -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for row in read_csv(SOURCE / "thesis_diagnostic_score_bundle.csv"):
        out.append(
            {
                "table": "diagnostic_scores",
                "item": row["score_id"],
                "scope": row["case_scope"],
                "metric": row["metric"],
                "value": row["score_value"],
                "status": row["admission_status"],
                "caption_note": row["thesis_caption_status"],
            }
        )
    for row in read_csv(SOURCE / "passive_h2_four_case_runtime_diagnostic.csv"):
        out.append(
            {
                "table": "runtime_diagnostics",
                "item": row["case_id"],
                "scope": row["split_role"],
                "metric": "radiation_delta_W",
                "value": row["radiation_delta_W"],
                "status": "diagnostic_runtime_not_admitted",
                "caption_note": row["target_status"],
            }
        )
    source_rows = read_csv(SOURCE / "source_property_final_disposition.csv")
    out.extend(
        [
            {
                "table": "gate_counts",
                "item": "source_property_release_allowed_rows",
                "scope": "current PASSIVE-H2 corpus",
                "metric": "count",
                "value": str(sum(1 for row in source_rows if row["release_allowed_now"] == "true")),
                "status": "fail_closed",
                "caption_note": "release remains zero",
            },
            {
                "table": "gate_counts",
                "item": "candidate_freeze_allowed_rows",
                "scope": "current PASSIVE-H2 corpus",
                "metric": "count",
                "value": str(sum(1 for row in source_rows if row["freeze_allowed_now"] == "true")),
                "status": "fail_closed",
                "caption_note": "freeze remains zero",
            },
            {
                "table": "gate_counts",
                "item": "score_allowed_rows",
                "scope": "current PASSIVE-H2 corpus",
                "metric": "count",
                "value": str(sum(1 for row in source_rows if row["score_allowed_now"] == "true")),
                "status": "fail_closed",
                "caption_note": "final score remains zero",
            },
        ]
    )
    return out


def claim_boundary_rows() -> list[dict[str, str]]:
    rows = []
    for row in read_csv(SOURCE / "thesis_claim_language.csv"):
        rows.append(
            {
                "claim_id": row["claim_id"],
                "allowed": row["allowed"],
                "claim_text": row["claim_text"],
                "required_caveat": row["must_include_caveat"],
                "appendix_use": "include" if row["allowed"] == "true" else "forbidden_language_warning",
            }
        )
    return rows


def decision_tree_rows() -> list[dict[str, str]]:
    return [
        {
            "step": "1",
            "condition": "Need thesis-presentable evidence now",
            "action": "Use this appendix handoff as diagnostic evidence.",
            "stop_or_continue": "stop_for_current_thesis_figures",
        },
        {
            "step": "2",
            "condition": "Need admitted PASSIVE-H2 candidate",
            "action": "Predeclare a new candidate branch or repair Salt1 junction before any scoring.",
            "stop_or_continue": "continue_only_with_new_board_row",
        },
        {
            "step": "3",
            "condition": "Candidate branch exists",
            "action": "Run strict source-envelope and same-QOI release-UQ gates.",
            "stop_or_continue": "continue_only_if_release_gates_pass",
        },
        {
            "step": "4",
            "condition": "Release/freeze rows remain zero",
            "action": "Do not open S15/S6 final scoring; keep diagnostic-only thesis language.",
            "stop_or_continue": "stop_fail_closed",
        },
    ]


def markdown_table(rows: list[dict[str, str]], cols: list[str], limit: int | None = None) -> str:
    selected = rows[:limit] if limit is not None else rows
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for row in selected:
        lines.append("| " + " | ".join(row.get(col, "").replace("|", "/") for col in cols) + " |")
    return "\n".join(lines)


def write_appendix_drafts(summary: dict[str, Any]) -> None:
    captions = read_csv(OUT / "caption_bank.csv")
    evidence = read_csv(OUT / "appendix_numeric_evidence.csv")
    claims = read_csv(OUT / "claim_boundary_table.csv")
    text = f"""# Draft Thesis Appendix Section: PASSIVE-H2 Diagnostic Evidence

This appendix records diagnostic evidence for the PASSIVE-H2 model-form path.
It is not an admitted final predictive score. The current package contains
{summary["figure_count"]} figures, {summary["numeric_evidence_rows"]} numeric
evidence rows, and {summary["runtime_case_rows"]} runtime diagnostic case rows.

## Recommended Figure Captions

{markdown_table(captions, ["figure_id", "caption_text"])}

## Compact Numeric Evidence

{markdown_table(evidence, ["table", "item", "scope", "metric", "value", "status"], limit=18)}

## Claim Boundary

{markdown_table(claims, ["claim_id", "allowed", "claim_text", "required_caveat"])}

## Required Wording

Use: diagnostic model-form evidence, no-score runtime contract, fail-closed
source/property disposition.

Do not use: admitted source/property release, numeric q_loss release, Qwall
release, coefficient admission, candidate freeze, protected scoring, or final
predictive score.
"""
    (OUT / "appendix_section_draft.md").write_text(text, encoding="utf-8")

    latex = r"""\subsection{PASSIVE-H2 Diagnostic Evidence}
The PASSIVE-H2 evidence is used here as diagnostic model-form evidence, not as
an admitted final predictive score. The current evidence supports a no-score
runtime contract and four-case heat-ledger response, while source/property
release, candidate freeze, and final scoring remain closed.

% Insert figures from this handoff package only with captions from
% figure_caption_bank.csv. Do not call these final predictive scores.
"""
    (OUT / "appendix_section_latex_snippet.tex").write_text(latex, encoding="utf-8")


def guardrail_rows() -> list[dict[str, str]]:
    return [
        {"guardrail": "native_solver_outputs_mutated", "value": "false"},
        {"guardrail": "registry_or_admission_mutated", "value": "false"},
        {"guardrail": "scheduler_action", "value": "false"},
        {"guardrail": "solver_sampler_harvest_uq_launched", "value": "false"},
        {"guardrail": "fluid_or_external_edit", "value": "false"},
        {"guardrail": "thesis_current_or_latex_edit", "value": "false"},
        {"guardrail": "source_property_release", "value": "false"},
        {"guardrail": "numeric_q_loss_release", "value": "false"},
        {"guardrail": "qwall_release", "value": "false"},
        {"guardrail": "coefficient_admission", "value": "false"},
        {"guardrail": "candidate_freeze", "value": "false"},
        {"guardrail": "protected_or_final_scoring", "value": "false"},
    ]


def write_outputs() -> dict[str, Any]:
    ensure_dir(OUT)
    figure_rows = copy_figures()
    evidence_rows = appendix_numeric_evidence_rows()
    claim_rows = claim_boundary_rows()
    decision_rows = decision_tree_rows()
    caption_rows = read_csv(SOURCE / "figure_caption_bank.csv")

    csv_dump(OUT / "source_manifest.csv", ["role", "path", "mode", "exists"], source_manifest_rows())
    csv_dump(OUT / "figure_asset_manifest.csv", ["figure_id", "source_path", "handoff_path", "exists", "data_rows", "primary_message", "caption_caveat"], figure_rows)
    csv_dump(OUT / "caption_bank.csv", ["figure_id", "caption_text"], caption_rows)
    csv_dump(OUT / "appendix_numeric_evidence.csv", ["table", "item", "scope", "metric", "value", "status", "caption_note"], evidence_rows)
    csv_dump(OUT / "claim_boundary_table.csv", ["claim_id", "allowed", "claim_text", "required_caveat", "appendix_use"], claim_rows)
    csv_dump(OUT / "next_decision_tree.csv", ["step", "condition", "action", "stop_or_continue"], decision_rows)
    csv_dump(OUT / "no_mutation_guardrails.csv", ["guardrail", "value"], guardrail_rows())

    source_summary = read_json(SOURCE / "summary.json")
    summary = {
        "task_id": TASK_ID,
        "generated_at": iso_timestamp(),
        "decision": "passive_h2_thesis_appendix_handoff_ready_diagnostic_only",
        "figure_count": len(figure_rows),
        "copied_figure_count": sum(1 for row in figure_rows if row["exists"] == "true"),
        "caption_rows": len(caption_rows),
        "numeric_evidence_rows": len(evidence_rows),
        "runtime_case_rows": int(source_summary.get("runtime_diagnostic_case_rows", 0)),
        "claim_boundary_rows": len(claim_rows),
        "forbidden_claim_rows": sum(1 for row in claim_rows if row["allowed"] == "false"),
        "release_allowed_rows": int(source_summary.get("release_allowed_rows", 0)),
        "freeze_allowed_rows": int(source_summary.get("freeze_allowed_rows", 0)),
        "score_allowed_rows": int(source_summary.get("score_allowed_rows", 0)),
        "source_property_release": False,
        "numeric_q_loss_release": False,
        "qwall_release": False,
        "coefficient_admission": False,
        "candidate_freeze": False,
        "protected_or_final_scoring": False,
        "thesis_current_or_latex_edit": False,
        "scheduler_action": False,
        "native_output_mutation": False,
        "registry_or_admission_mutation": False,
        "fluid_or_external_edit": False,
    }
    json_dump(OUT / "summary.json", summary)
    write_appendix_drafts(summary)
    write_readme(summary)
    write_closeout(summary)
    write_import_manifest(summary)
    return summary


def write_readme(summary: dict[str, Any]) -> None:
    text = f"""---
provenance:
  - {rel(SOURCE / "summary.json")}
  - {rel(SOURCE / "figure_caption_bank.csv")}
  - {rel(SOURCE / "source_property_final_disposition.csv")}
tags: [PASSIVE-H2, thesis-appendix, diagnostic-only, figure-handoff]
related:
  - {rel(STATUS)}
  - {rel(JOURNAL)}
task: {TASK_ID}
date: 2026-07-22
role: Writer / Implementer / Tester / Reviewer
type: work_product
status: complete
---
# PASSIVE-H2 Thesis Evidence Appendix Handoff

Decision: `{summary["decision"]}`.

This package prepares the PASSIVE-H2 diagnostic evidence for thesis appendix
use without editing thesis source files. It carries copied SVG figure assets,
caption text, compact numeric evidence, claim boundaries, and draft appendix
snippets.

Results: `{summary["copied_figure_count"]}` copied figures,
`{summary["caption_rows"]}` captions, `{summary["numeric_evidence_rows"]}`
numeric evidence rows, and `{summary["claim_boundary_rows"]}` claim rows.

Admission boundary: release/freeze/score rows remain
`{summary["release_allowed_rows"]}` / `{summary["freeze_allowed_rows"]}` /
`{summary["score_allowed_rows"]}`.
"""
    (OUT / "README.md").write_text(text, encoding="utf-8")


def write_closeout(summary: dict[str, Any]) -> None:
    ensure_dir(STATUS.parent)
    status = f"""---
provenance:
  - {rel(OUT / "summary.json")}
  - {rel(OUT / "appendix_section_draft.md")}
  - {rel(OUT / "figure_asset_manifest.csv")}
tags: [PASSIVE-H2, thesis-appendix, diagnostic-only]
related:
  - {rel(OUT / "README.md")}
  - {rel(JOURNAL)}
task: {TASK_ID}
date: 2026-07-22
role: Writer / Implementer / Tester / Reviewer
type: status
status: complete
---
# {TASK_ID}

Objective: package the PASSIVE-H2 diagnostic results for thesis appendix use
without mutating thesis files or claiming admitted scores.

Outcome: `{summary["decision"]}`. Copied figures:
`{summary["copied_figure_count"]}`; captions: `{summary["caption_rows"]}`;
numeric evidence rows: `{summary["numeric_evidence_rows"]}`; release/freeze/
score rows: `{summary["release_allowed_rows"]}` /
`{summary["freeze_allowed_rows"]}` / `{summary["score_allowed_rows"]}`.

## Changes Made

- Copied thesis-ready SVG figures into the handoff package.
- Emitted caption, numeric evidence, claim-boundary, and decision-tree CSVs.
- Wrote `appendix_section_draft.md` and `appendix_section_latex_snippet.tex`
  as source-free drafts; no thesis files were edited.
- Wrote README, status, journal, and import manifest.

## Validation

- `python3.11 tools/analyze/build_passive_h2_thesis_evidence_appendix_handoff.py`
- `python3.11 -m unittest tools.analyze.test_passive_h2_thesis_evidence_appendix_handoff`
- `python3.11 -m py_compile tools/analyze/build_passive_h2_thesis_evidence_appendix_handoff.py tools/analyze/test_passive_h2_thesis_evidence_appendix_handoff.py`
- `python3.11 tools/agent/manifest_check.py imports/2026-07-22_passive_h2_thesis_evidence_appendix_handoff.json --check-paths`
- `python3.11 tools/agent/finish_task.py --task-id {TASK_ID}`

## Guardrails

No native-output mutation, registry/admission mutation, scheduler action,
solver/sampler/harvest/UQ launch, Fluid/external edit, thesis source edit,
source/property release, numeric q-loss release, Qwall release, coefficient
admission, candidate freeze, protected/final scoring, hidden multiplier, or
residual absorption.
"""
    STATUS.write_text(status, encoding="utf-8")

    ensure_dir(JOURNAL.parent)
    journal = f"""---
provenance:
  - {rel(OUT / "summary.json")}
  - {rel(OUT / "claim_boundary_table.csv")}
tags: [PASSIVE-H2, thesis-appendix, diagnostic-only]
related:
  - {rel(STATUS)}
  - {rel(OUT / "README.md")}
task: {TASK_ID}
date: 2026-07-22
role: Writer / Implementer / Tester / Reviewer
type: journal
status: complete
---
# PASSIVE-H2 Thesis Evidence Appendix Handoff

Attempted: convert the completed diagnostic PASSIVE-H2 package into a
thesis-facing appendix handoff.

Observed: the figure/caption bundle is complete and can be used as diagnostic
evidence. The source package still reports zero release, freeze, and score
rows, so the appendix must not imply admitted predictive performance.

Inferred: this is the best near-term thesis path because it presents scored
diagnostic evidence while preserving admission rigor.

Caveats: snippets are drafts only; no thesis current/LaTeX files were edited.
"""
    JOURNAL.write_text(journal, encoding="utf-8")


def write_import_manifest(summary: dict[str, Any]) -> None:
    package_files = [rel(path) for path in sorted(OUT.rglob("*")) if path.is_file()]
    changed = [
        ".agent/BOARD.md",
        rel(STATUS),
        rel(JOURNAL),
        rel(IMPORT),
        "tools/analyze/build_passive_h2_thesis_evidence_appendix_handoff.py",
        "tools/analyze/test_passive_h2_thesis_evidence_appendix_handoff.py",
    ]
    payload = {
        "task": TASK_ID,
        "task_id": TASK_ID,
        "generated_at": iso_timestamp(),
        "changed_files": sorted(dict.fromkeys(changed + package_files)),
        "read_only_context": [row["path"] for row in source_manifest_rows()],
        "results": summary,
        "native_solver_outputs_mutated": False,
        "registry_mutated": False,
        "scheduler_action": False,
        "external_fluid_edit": False,
        "mutation_flags": {
            "native_solver_outputs_mutated": False,
            "registry_or_admission_mutated": False,
            "scheduler_action": False,
            "solver_sampler_harvest_uq_launched": False,
            "fluid_or_external_edit": False,
            "thesis_current_or_latex_edit": False,
            "source_property_release": False,
            "candidate_freeze": False,
            "protected_or_final_scoring": False,
        },
    }
    json_dump(IMPORT, payload)


def main() -> int:
    summary = write_outputs()
    print(json.dumps(summary, indent=2, sort_keys=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
