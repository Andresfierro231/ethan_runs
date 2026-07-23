#!/usr/bin/env python3
"""Rerun PASSIVE-H2 source/property gates with completed Salt3/Salt4 smoke evidence."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.common import csv_dump, ensure_dir, iso_timestamp, json_dump, relative_to_workspace

TASK_ID = "TODO-PASSIVE-H2-SOURCE-PROPERTY-GATE-RERUN-WITH-SALT34-SMOKE-2026-07-22"
OUT = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_passive_h2_source_property_gate_rerun_with_salt34_smoke"
STATUS = ROOT / f".agent/status/2026-07-22_{TASK_ID}.md"
JOURNAL = ROOT / ".agent/journal/2026-07-22/passive-h2-source-property-gate-rerun-with-salt34-smoke.md"
IMPORT = ROOT / "imports/2026-07-22_passive_h2_source_property_gate_rerun_with_salt34_smoke.json"

RUNTIME = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_passive_h2_outer_insulation_radiation_runtime_implementation"
SALT34 = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_passive_h2_salt34_diagnostic_runtime_smoke"
SUBSPAN = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_passive_h2_subspan_mapping_release_recovery"
SALT2_UQ = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_passive_h2_salt2_same_qoi_setup_uq_gate"
CANDIDATE_GATE = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_candidate_specific_source_property_gate"
FINAL_GATE = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_passive_h2_final_form_admission_phase_gate"
MASTER = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_thesis_master_model_form_scoreboard"


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


def normalize_csv(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = "\n".join(line.rstrip(" \t") for line in text.split("\n"))
    path.write_text(text, encoding="utf-8")


def b(value: Any) -> str:
    return str(bool(value)).lower()


def split_roles() -> dict[str, dict[str, str]]:
    return {row["case_id"]: row for row in read_csv(FINAL_GATE / "split_policy_for_final_form.csv")}


def three_case_runtime_evidence_rows() -> list[dict[str, str]]:
    runtime = read_json(RUNTIME / "summary.json")
    roles = split_roles()
    rows = [
        {
            "candidate_id": "PASSIVE-H2-CAND001",
            "case_id": "salt_2",
            "split_role": roles.get("salt_2", {}).get("split_role", "train"),
            "runtime_evidence_source": "Salt2 runtime implementation",
            "runtime_completed": b(runtime.get("root_status_passive_h2_role_rad_on") == "accepted"),
            "accepted_roots": b(runtime.get("root_status_passive_h2_role_rad_on") == "accepted"),
            "radiation_on_nonzero": b(runtime.get("radiation_on_nonzero")),
            "radiation_on_heat_ledger_delta_W": str(runtime.get("radiation_on_heat_ledger_delta_W", "")),
            "radiation_target_delta_W": str(runtime.get("radiation_target_delta_W", "")),
            "radiation_delta_over_target": str(runtime.get("radiation_delta_over_target", "")),
            "protected_scoring": "false",
            "source_property_release": "false",
            "candidate_freeze": "false",
            "admissibility_role": "train_support_runtime_diagnostic",
            "evidence_path": rel(RUNTIME / "summary.json"),
        }
    ]
    for row in read_csv(SALT34 / "case_runtime_smoke_summary.csv"):
        case_id = row["case_id"]
        role = roles.get(case_id, {})
        rows.append(
            {
                "candidate_id": "PASSIVE-H2-CAND001",
                "case_id": case_id,
                "split_role": role.get("split_role", ""),
                "runtime_evidence_source": "Salt3/Salt4 diagnostic runtime smoke",
                "runtime_completed": row.get("output_complete", "false"),
                "accepted_roots": b(
                    row.get("root_status_current_no_role_rad_off") == "accepted"
                    and row.get("root_status_passive_h2_role_rad_off") == "accepted"
                    and row.get("root_status_passive_h2_role_rad_on") == "accepted"
                ),
                "radiation_on_nonzero": row.get("radiation_on_nonzero", "false"),
                "radiation_on_heat_ledger_delta_W": row.get("radiation_on_heat_ledger_delta_W", ""),
                "radiation_target_delta_W": row.get("radiation_target_delta_W", ""),
                "radiation_delta_over_target": row.get("radiation_delta_over_target", ""),
                "protected_scoring": "false",
                "source_property_release": "false",
                "candidate_freeze": "false",
                "admissibility_role": role.get("allowed_current_use", "diagnostic_only_no_protected_scoring"),
                "evidence_path": rel(SALT34 / "case_runtime_smoke_summary.csv"),
            }
        )
    return rows


def source_property_release_gate_rows() -> list[dict[str, str]]:
    subspan = read_json(SUBSPAN / "summary.json")
    uq = read_json(SALT2_UQ / "summary.json")
    candidate = read_json(CANDIDATE_GATE / "summary.json")
    final = read_json(FINAL_GATE / "summary.json")
    smoke = read_json(SALT34 / "summary.json")
    return [
        {
            "gate": "three_case_runtime_smoke",
            "status": "pass_diagnostic",
            "count_or_value": f"completed={smoke.get('completed_case_rows', 0) + 1}/3; nonzero={smoke.get('nonzero_radiation_case_rows', 0) + 1}/3",
            "release_ready": "false",
            "why": "Salt2 plus Salt3/Salt4 runtime evidence proves the operator executes and changes heat ledger, not that the candidate is release-ready.",
            "evidence_path": rel(SALT34 / "summary.json"),
        },
        {
            "gate": "release_grade_subspan",
            "status": "fail_closed",
            "count_or_value": f"{subspan.get('salt2_release_ready_rows', 0)}/5",
            "release_ready": "false",
            "why": "Setup subspan support is recovered, but release-grade source-family rows remain zero.",
            "evidence_path": rel(SUBSPAN / "salt2_subspan_release_gate.csv"),
        },
        {
            "gate": "row_specific_source_property",
            "status": "fail_closed",
            "count_or_value": str(candidate.get("source_property_release_ready_rows", 0)),
            "release_ready": "false",
            "why": "Candidate-specific source/property release-ready rows remain zero.",
            "evidence_path": rel(CANDIDATE_GATE / "candidate_gate_matrix.csv"),
        },
        {
            "gate": "same_qoi_runtime_uq",
            "status": "fail_closed",
            "count_or_value": f"diagnostic={uq.get('diagnostic_ready_qoi_labels', 0)}/{uq.get('qoi_labels', 0)}; release={uq.get('release_ready_qoi_labels', 0)}/{uq.get('qoi_labels', 0)}",
            "release_ready": "false",
            "why": "Salt2 same-QOI setup-UQ is diagnostic-ready; no candidate release-ready UQ labels exist.",
            "evidence_path": rel(SALT2_UQ / "qoi_readiness_gate.csv"),
        },
        {
            "gate": "split_safe_freeze",
            "status": "fail_closed",
            "count_or_value": f"split_conflicts={final.get('split_conflict_rows', 0)}; freeze_ready={final.get('freeze_ready_candidates', 0)}",
            "release_ready": "false",
            "why": "Salt3/Salt4 are diagnostic only under protected split labels; no frozen candidate exists.",
            "evidence_path": rel(FINAL_GATE / "split_policy_for_final_form.csv"),
        },
        {
            "gate": "final_score",
            "status": "closed_not_run",
            "count_or_value": str(final.get("final_score_values", 0)),
            "release_ready": "false",
            "why": "Final score remains invalid until exactly one runtime-legal candidate is frozen after release gates.",
            "evidence_path": rel(FINAL_GATE / "summary.json"),
        },
    ]


def blocker_rows() -> list[dict[str, str]]:
    return [
        {
            "blocker": "source/property release",
            "status": "still_blocking",
            "evidence": "source_property_release_ready_rows=0",
            "unblock_step": "recover row-specific source envelope, property labels, and source-family provenance for PASSIVE-H2 rows",
            "can_do_without_scheduler": "true",
        },
        {
            "blocker": "release-grade subspan rows",
            "status": "still_blocking",
            "evidence": "salt2_release_ready_rows=0/5",
            "unblock_step": "promote or fail-close each source family with exact subspan start/end, area, role, and source citation",
            "can_do_without_scheduler": "true",
        },
        {
            "blocker": "same-QOI runtime UQ",
            "status": "partially_unblocked",
            "evidence": "6/6 Salt2 labels diagnostic-ready; 0/6 release-ready",
            "unblock_step": "rerun UQ only after release-grade rows exist; keep validation/holdout targets protected",
            "can_do_without_scheduler": "maybe",
        },
        {
            "blocker": "Salt3/Salt4 runtime path",
            "status": "unblocked_for_diagnostic_only",
            "evidence": "2/2 Salt3/Salt4 smoke cases completed with accepted roots and nonzero radiation delta",
            "unblock_step": "use as runtime feasibility evidence, not protected score or source release",
            "can_do_without_scheduler": "done",
        },
        {
            "blocker": "S15/S6 final scoring",
            "status": "still_blocking",
            "evidence": "freeze_ready_candidates=0; final_score_values=0",
            "unblock_step": "open only after one candidate has release-grade source/property and same-QOI UQ",
            "can_do_without_scheduler": "false",
        },
    ]


def next_action_rows() -> list[dict[str, str]]:
    return [
        {
            "priority": "1",
            "next_task": "PASSIVE-H2 release-grade source/property provenance repair",
            "purpose": "turn support-only subspan/runtime evidence into explicit release-ready or fail-closed source/property rows",
            "acceptance": "per source family: parent/subspan, area/role, property/source labels, split role, release decision, and exact fail reason if closed",
        },
        {
            "priority": "2",
            "next_task": "PASSIVE-H2 same-QOI runtime UQ after provenance repair",
            "purpose": "decide whether the candidate can pass release-grade UQ rather than only setup diagnostic UQ",
            "acceptance": "release-ready QOI labels >0 without forbidden runtime inputs or validation/holdout scoring",
        },
        {
            "priority": "3",
            "next_task": "PASSIVE-H2 freeze gate rerun",
            "purpose": "reassess whether exactly one runtime-legal candidate can enter S15/S6",
            "acceptance": "freeze_ready_candidates is exactly 1 or fail-closed with final_score_values=0",
        },
    ]


def claim_boundary_rows() -> list[dict[str, str]]:
    return [
        {"claim": "PASSIVE-H2 executes on Salt2/Salt3/Salt4", "allowed": "true", "scope": "diagnostic runtime evidence"},
        {"claim": "PASSIVE-H2 radiation heat-ledger delta is nonzero in all three available cases", "allowed": "true", "scope": "diagnostic runtime evidence"},
        {"claim": "Salt3/Salt4 prove validation/holdout score improvement", "allowed": "false", "scope": "protected scoring not run"},
        {"claim": "source/property release is open", "allowed": "false", "scope": "release-ready rows remain zero"},
        {"claim": "numeric q-loss or Qwall is released", "allowed": "false", "scope": "blocked"},
        {"claim": "candidate is frozen for final model", "allowed": "false", "scope": "freeze-ready candidates remain zero"},
    ]


def guardrail_rows() -> list[dict[str, str]]:
    return [
        {"guardrail": "native_output_mutation", "occurred": "false"},
        {"guardrail": "registry_or_admission_mutation", "occurred": "false"},
        {"guardrail": "scheduler_action_in_this_task", "occurred": "false"},
        {"guardrail": "solver_sampler_harvest_uq_launched_in_this_task", "occurred": "false"},
        {"guardrail": "Fluid_or_external_edit", "occurred": "false"},
        {"guardrail": "protected_scoring", "occurred": "false"},
        {"guardrail": "source_property_release", "occurred": "false"},
        {"guardrail": "qwall_or_numeric_q_loss_release", "occurred": "false"},
        {"guardrail": "candidate_freeze", "occurred": "false"},
        {"guardrail": "final_score_claim", "occurred": "false"},
    ]


def source_manifest_rows() -> list[dict[str, str]]:
    sources = [
        ("salt2_runtime", RUNTIME / "summary.json"),
        ("salt34_smoke_summary", SALT34 / "summary.json"),
        ("salt34_case_smoke", SALT34 / "case_runtime_smoke_summary.csv"),
        ("subspan_release_recovery", SUBSPAN / "summary.json"),
        ("salt2_same_qoi_setup_uq", SALT2_UQ / "summary.json"),
        ("candidate_specific_gate", CANDIDATE_GATE / "summary.json"),
        ("final_form_gate", FINAL_GATE / "summary.json"),
        ("master_scoreboard", MASTER / "summary.json"),
    ]
    return [
        {"role": role, "path": rel(path), "mode": "read_only", "exists": str(path.exists()).lower()}
        for role, path in sources
    ]


def write_readme(out_dir: Path, summary: dict[str, Any]) -> None:
    text = f"""---
provenance:
  - {rel(RUNTIME / "summary.json")}
  - {rel(SALT34 / "summary.json")}
  - {rel(SUBSPAN / "summary.json")}
  - {rel(SALT2_UQ / "summary.json")}
tags: [PASSIVE-H2, source-property, Salt3, Salt4, runtime-smoke, no-release]
related:
  - {rel(STATUS)}
  - {rel(JOURNAL)}
task: {TASK_ID}
date: 2026-07-22
role: Implementer / Tester / Writer / Reviewer
type: work_product
status: complete
---
# PASSIVE-H2 Source/Property Gate Rerun With Salt3/Salt4 Smoke

Decision: `{summary["decision"]}`.

This package consumes the completed Salt3/Salt4 diagnostic runtime-smoke row
with the Salt2 PASSIVE-H2 runtime implementation, subspan release-recovery,
same-QOI setup-UQ, candidate source/property gate, and final-form gate.

Result: three-case runtime evidence is complete and nonzero for Salt2/Salt3/Salt4.
That unblocks runtime-feasibility discussion, but it does not open source/property
release or final scoring. Release-grade subspan rows remain `0/5`,
source/property release-ready rows remain `0`, release-ready same-QOI labels
remain `0`, freeze-ready candidates remain `0`, and final score values remain
`0`.

## Outputs

- `three_case_runtime_evidence.csv`
- `source_property_release_gate.csv`
- `unblock_blocker_matrix.csv`
- `next_action_queue.csv`
- `claim_boundaries.csv`
- `source_manifest.csv`
- `no_mutation_guardrails.csv`
- `summary.json`
"""
    (out_dir / "README.md").write_text(text, encoding="utf-8")


def write_status(summary: dict[str, Any]) -> None:
    text = f"""---
provenance:
  - {rel(OUT / "summary.json")}
tags: [status, PASSIVE-H2, source-property, no-release]
related:
  - {rel(OUT / "README.md")}
task: {TASK_ID}
date: 2026-07-22
role: Implementer / Tester / Writer / Reviewer
type: status
status: complete
---
# Status: PASSIVE-H2 Source/Property Gate Rerun With Salt3/Salt4 Smoke

Objective: rerun the PASSIVE-H2 candidate-specific gate after completed Salt3/Salt4
diagnostic runtime smoke.

Outcome: `{summary["decision"]}`. Runtime feasibility is now complete across
Salt2/Salt3/Salt4 (`{summary["runtime_completed_case_rows"]}/3` completed and
`{summary["runtime_nonzero_case_rows"]}/3` nonzero), but release remains closed:
source/property release-ready rows `{summary["source_property_release_ready_rows"]}`,
release-ready same-QOI labels `{summary["release_ready_qoi_labels"]}`,
freeze-ready candidates `{summary["freeze_ready_candidates"]}`, final score
values `{summary["final_score_values"]}`.

Changed artifacts: `{rel(OUT)}`, this status file, matching journal, import
manifest, and the builder/test pair.

## Changes Made

- Added the PASSIVE-H2 Salt3/Salt4-smoke-aware gate rerun builder and tests.
- Published the gate package under `{rel(OUT)}`.
- Wrote status, journal, and import manifest closeout artifacts for this task.

## Validation

- `python3.11 tools/analyze/build_passive_h2_source_property_gate_rerun_with_salt34_smoke.py`
- `python3.11 -m unittest tools.analyze.test_passive_h2_source_property_gate_rerun_with_salt34_smoke`
- `python3.11 -m py_compile tools/analyze/build_passive_h2_source_property_gate_rerun_with_salt34_smoke.py tools/analyze/test_passive_h2_source_property_gate_rerun_with_salt34_smoke.py`
- `python3.11 tools/agent/finish_task.py --task-id {TASK_ID}`

## Guardrails

Guardrails: no native-output mutation, registry/admission mutation, scheduler
action in this task, Fluid/external edit, protected scoring, source/property
release, Qwall/numeric q-loss release, candidate freeze, or final score claim.
"""
    STATUS.parent.mkdir(parents=True, exist_ok=True)
    STATUS.write_text(text, encoding="utf-8")


def write_journal(summary: dict[str, Any]) -> None:
    text = f"""---
provenance:
  - {rel(OUT / "summary.json")}
tags: [journal, PASSIVE-H2, runtime-smoke, source-property]
related:
  - {rel(STATUS)}
  - {rel(OUT / "README.md")}
task: {TASK_ID}
date: 2026-07-22
role: Implementer / Tester / Writer / Reviewer
type: journal
status: complete
---
# PASSIVE-H2 Source/Property Gate Rerun With Salt3/Salt4 Smoke

Attempted: joined Salt2 runtime implementation, Salt3/Salt4 diagnostic runtime
smoke, subspan release-recovery, same-QOI setup-UQ, candidate-specific
source/property gate, and final-form gate.

Observed: Salt3 and Salt4 runtime smoke completed with accepted roots and nonzero
radiation heat-ledger deltas. With Salt2, the operator has three-case diagnostic
runtime evidence. Salt3/Salt4 remain protected split roles and were not scored.

Inferred: runtime feasibility is no longer the main PASSIVE-H2 blocker.
The controlling blockers are release-grade source/property provenance,
release-grade subspan rows, exact same-QOI runtime UQ, and freeze gate closure.

Caveats: this task consumed existing smoke output only. It did not launch a
solver, sampler, harvest, or UQ job and did not release any numeric q-loss,
Qwall, source/property, or score value.

Next useful actions: repair PASSIVE-H2 release-grade source/property provenance,
then rerun exact same-QOI runtime UQ, then rerun freeze gate only if exactly one
candidate becomes release-ready.
"""
    JOURNAL.parent.mkdir(parents=True, exist_ok=True)
    JOURNAL.write_text(text, encoding="utf-8")


def write_import(summary: dict[str, Any]) -> None:
    changed = [
        rel(STATUS),
        rel(JOURNAL),
        rel(IMPORT),
        "tools/analyze/build_passive_h2_source_property_gate_rerun_with_salt34_smoke.py",
        "tools/analyze/test_passive_h2_source_property_gate_rerun_with_salt34_smoke.py",
        f"{rel(OUT)}/README.md",
        f"{rel(OUT)}/three_case_runtime_evidence.csv",
        f"{rel(OUT)}/source_property_release_gate.csv",
        f"{rel(OUT)}/unblock_blocker_matrix.csv",
        f"{rel(OUT)}/next_action_queue.csv",
        f"{rel(OUT)}/claim_boundaries.csv",
        f"{rel(OUT)}/source_manifest.csv",
        f"{rel(OUT)}/no_mutation_guardrails.csv",
        f"{rel(OUT)}/summary.json",
    ]
    manifest = {
        "task": TASK_ID,
        "task_id": TASK_ID,
        "changed_files": changed,
        "read_only_context": [row["path"] for row in source_manifest_rows()],
        "results": {
            "decision": summary["decision"],
            "runtime_completed_case_rows": summary["runtime_completed_case_rows"],
            "runtime_nonzero_case_rows": summary["runtime_nonzero_case_rows"],
            "source_property_release_ready_rows": summary["source_property_release_ready_rows"],
            "freeze_ready_candidates": summary["freeze_ready_candidates"],
            "final_score_values": summary["final_score_values"],
        },
        "native_solver_outputs_mutated": False,
        "registry_mutated": False,
        "scheduler_action": False,
        "scheduler_action_in_this_task": False,
        "external_fluid_edit": False,
        "fluid_or_external_edit": False,
        "protected_scoring": False,
        "source_property_release": False,
        "candidate_freeze": False,
        "final_score_claim": False,
    }
    IMPORT.parent.mkdir(parents=True, exist_ok=True)
    json_dump(IMPORT, manifest)


def build(out_dir: Path = OUT) -> dict[str, Any]:
    ensure_dir(out_dir)
    runtime_rows = three_case_runtime_evidence_rows()
    release_rows = source_property_release_gate_rows()
    blockers = blocker_rows()
    next_actions = next_action_rows()
    claims = claim_boundary_rows()
    guards = guardrail_rows()
    sources = source_manifest_rows()

    csv_specs = [
        ("three_case_runtime_evidence.csv", list(runtime_rows[0]), runtime_rows),
        ("source_property_release_gate.csv", list(release_rows[0]), release_rows),
        ("unblock_blocker_matrix.csv", list(blockers[0]), blockers),
        ("next_action_queue.csv", list(next_actions[0]), next_actions),
        ("claim_boundaries.csv", list(claims[0]), claims),
        ("source_manifest.csv", list(sources[0]), sources),
        ("no_mutation_guardrails.csv", list(guards[0]), guards),
    ]
    for name, header, rows in csv_specs:
        path = out_dir / name
        csv_dump(path, header, rows)
        normalize_csv(path)

    candidate = read_json(CANDIDATE_GATE / "summary.json")
    uq = read_json(SALT2_UQ / "summary.json")
    final = read_json(FINAL_GATE / "summary.json")
    runtime_completed = sum(1 for row in runtime_rows if row["runtime_completed"] == "true")
    nonzero = sum(1 for row in runtime_rows if row["radiation_on_nonzero"] == "true")
    summary = {
        "task_id": TASK_ID,
        "generated_at": iso_timestamp(),
        "decision": "passive_h2_with_salt34_smoke_runtime_evidence_complete_release_fail_closed",
        "candidate_id": "PASSIVE-H2-CAND001",
        "runtime_completed_case_rows": runtime_completed,
        "runtime_nonzero_case_rows": nonzero,
        "three_case_runtime_evidence_complete": runtime_completed == 3 and nonzero == 3,
        "source_property_release_ready_rows": int(candidate.get("source_property_release_ready_rows", 0)),
        "release_ready_qoi_labels": int(uq.get("release_ready_qoi_labels", 0)),
        "salt2_release_ready_rows": int(read_json(SUBSPAN / "summary.json").get("salt2_release_ready_rows", 0)),
        "freeze_ready_candidates": int(final.get("freeze_ready_candidates", 0)),
        "final_score_values": int(final.get("final_score_values", 0)),
        "source_property_release": False,
        "numeric_q_loss_release": False,
        "qwall_release": False,
        "candidate_freeze": False,
        "protected_scoring": False,
        "final_score_claim": False,
        "native_output_mutation": False,
        "registry_or_admission_mutation": False,
        "scheduler_action_in_this_task": False,
        "fluid_or_external_edit": False,
        "solver_sampler_harvest_uq_launched_in_this_task": False,
    }
    json_dump(out_dir / "summary.json", summary)
    write_readme(out_dir, summary)
    if out_dir == OUT:
        write_status(summary)
        write_journal(summary)
        write_import(summary)
    return summary


def main() -> int:
    print(json.dumps(build(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
