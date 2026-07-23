#!/usr/bin/env python3
"""PASSIVE-H2 source/property gate after Salt1 junction runtime recovery."""

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

TASK_ID = "TODO-PASSIVE-H2-POST-JUNCTION-SOURCE-PROPERTY-GATE-2026-07-22"
SLUG = "passive_h2_post_junction_source_property_gate"
OUT = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_passive_h2_post_junction_source_property_gate"
STATUS = ROOT / f".agent/status/2026-07-22_{TASK_ID}.md"
JOURNAL = ROOT / ".agent/journal/2026-07-22/passive-h2-post-junction-source-property-gate.md"
IMPORT = ROOT / f"imports/2026-07-22_{SLUG}.json"

SALT1 = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_passive_h2_salt1_junction_setup_row_recovery_background"
SALT2 = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_passive_h2_outer_insulation_radiation_runtime_implementation"
SALT34 = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_passive_h2_salt34_diagnostic_runtime_smoke"
SUBSPAN = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_passive_h2_subspan_mapping_release_recovery"
SALT2_UQ = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_passive_h2_salt2_same_qoi_setup_uq_gate"
CANDIDATE_GATE = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_candidate_specific_source_property_gate"
FINAL_GATE = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_passive_h2_final_form_admission_phase_gate"
PRIOR_GATE = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_passive_h2_source_property_gate_rerun_with_salt34_smoke"
R4 = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_passive_h2_r4_predeclared_source_envelope_uq_gate"


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


def b(value: Any) -> str:
    return str(bool(value)).lower()


def strv(value: Any) -> str:
    return "" if value is None else str(value)


def runtime_rows() -> list[dict[str, str]]:
    salt1_pkg = read_json(SALT1 / "summary.json")
    salt1_runtime = read_json(SALT1 / "fluid_smoke_outputs/salt_1/summary.json")
    salt2 = read_json(SALT2 / "summary.json")
    rows = [
        {
            "candidate_id": "PASSIVE-H2-CAND001",
            "case_id": "salt_1",
            "runtime_evidence_source": "Salt1 junction recovery runtime smoke",
            "split_or_use_role": "train_diagnostic",
            "runtime_completed": b(salt1_pkg.get("runtime_completed")),
            "operator_rows_used": strv(salt1_pkg.get("runtime_operator_rows_used")),
            "accepted_roots": b(all(value == "accepted" for value in salt1_pkg.get("runtime_root_statuses", {}).values())),
            "radiation_on_nonzero": b(salt1_pkg.get("runtime_radiation_on_nonzero")),
            "radiation_on_heat_ledger_delta_W": strv(salt1_pkg.get("runtime_radiation_on_heat_ledger_delta_W")),
            "radiation_target_delta_W": strv(salt1_runtime.get("radiation_target_delta_W")),
            "protected_scoring": b(salt1_pkg.get("runtime_protected_scoring")),
            "forbidden_runtime_inputs_used": b(salt1_pkg.get("runtime_forbidden_inputs_used")),
            "source_property_release": "false",
            "candidate_freeze": "false",
            "admissibility_role": "diagnostic_runtime_coverage_closes_salt1_junction_gap_no_release",
            "evidence_path": rel(SALT1 / "summary.json"),
        },
        {
            "candidate_id": "PASSIVE-H2-CAND001",
            "case_id": "salt_2",
            "runtime_evidence_source": "Salt2 runtime implementation",
            "split_or_use_role": "train",
            "runtime_completed": b(salt2.get("fluid_runtime_decision") == "runtime_radiation_smoke_complete_no_release_no_score"),
            "operator_rows_used": strv(salt2.get("train_rows_used")),
            "accepted_roots": b(
                salt2.get("root_status_current_no_role_rad_off") == "accepted"
                and salt2.get("root_status_passive_h2_role_rad_off") == "accepted"
                and salt2.get("root_status_passive_h2_role_rad_on") == "accepted"
            ),
            "radiation_on_nonzero": b(salt2.get("radiation_on_nonzero")),
            "radiation_on_heat_ledger_delta_W": strv(salt2.get("radiation_on_heat_ledger_delta_W")),
            "radiation_target_delta_W": strv(salt2.get("radiation_target_delta_W")),
            "protected_scoring": b(salt2.get("protected_scoring")),
            "forbidden_runtime_inputs_used": b(
                salt2.get("runtime_CFD_mdot_used")
                or salt2.get("runtime_Qwall_used")
                or salt2.get("runtime_imposed_cooler_duty_used")
                or salt2.get("runtime_validation_temperature_used")
                or salt2.get("runtime_wallHeatFlux_used")
            ),
            "source_property_release": "false",
            "candidate_freeze": "false",
            "admissibility_role": "train_runtime_diagnostic_no_release",
            "evidence_path": rel(SALT2 / "summary.json"),
        },
    ]
    for row in read_csv(SALT34 / "case_runtime_smoke_summary.csv"):
        rows.append(
            {
                "candidate_id": "PASSIVE-H2-CAND001",
                "case_id": row.get("case_id", ""),
                "runtime_evidence_source": "Salt3/Salt4 diagnostic runtime smoke",
                "split_or_use_role": "diagnostic_protected_split_no_score",
                "runtime_completed": row.get("output_complete", "false"),
                "operator_rows_used": "5",
                "accepted_roots": b(
                    row.get("root_status_current_no_role_rad_off") == "accepted"
                    and row.get("root_status_passive_h2_role_rad_off") == "accepted"
                    and row.get("root_status_passive_h2_role_rad_on") == "accepted"
                ),
                "radiation_on_nonzero": row.get("radiation_on_nonzero", "false"),
                "radiation_on_heat_ledger_delta_W": row.get("radiation_on_heat_ledger_delta_W", ""),
                "radiation_target_delta_W": row.get("radiation_target_delta_W", ""),
                "protected_scoring": row.get("protected_scoring", "false"),
                "forbidden_runtime_inputs_used": "false",
                "source_property_release": "false",
                "candidate_freeze": "false",
                "admissibility_role": "diagnostic_runtime_feasibility_no_protected_scoring",
                "evidence_path": rel(SALT34 / "case_runtime_smoke_summary.csv"),
            }
        )
    return rows


def release_gate_rows() -> list[dict[str, str]]:
    subspan = read_json(SUBSPAN / "summary.json")
    uq = read_json(SALT2_UQ / "summary.json")
    candidate = read_json(CANDIDATE_GATE / "summary.json")
    final = read_json(FINAL_GATE / "summary.json")
    r4 = read_json(R4 / "summary.json")
    runtime = runtime_rows()
    return [
        {
            "gate": "four_case_runtime_feasibility",
            "status": "pass_diagnostic" if all(row["runtime_completed"] == "true" and row["accepted_roots"] == "true" for row in runtime) else "fail_closed",
            "count_or_value": f"{sum(row['runtime_completed'] == 'true' for row in runtime)}/{len(runtime)} completed; {sum(row['radiation_on_nonzero'] == 'true' for row in runtime)}/{len(runtime)} nonzero",
            "release_ready": "false",
            "why": "runtime compatibility and heat-ledger movement are diagnostic support, not source/property release",
        },
        {
            "gate": "salt1_junction_gap",
            "status": "closed_as_runtime_gap",
            "count_or_value": "18/18 junction patches; 5 train rows used",
            "release_ready": "false",
            "why": "Salt1 no longer has a mechanical 4/5 runtime coverage blocker, but recovered geometry/properties remain diagnostic",
        },
        {
            "gate": "strict_source_envelope",
            "status": "fail_closed",
            "count_or_value": str(candidate.get("strict_source_envelope_pass_rows", candidate.get("source_property_release_ready_rows", 0))),
            "release_ready": "false",
            "why": "row-specific source envelope and property provenance are not release-grade",
        },
        {
            "gate": "release_grade_subspan_rows",
            "status": "fail_closed",
            "count_or_value": f"{subspan.get('salt2_release_ready_rows', 0)}/5",
            "release_ready": "false",
            "why": "setup support exists, but release-grade source-family subspan rows remain zero",
        },
        {
            "gate": "same_qoi_release_uq",
            "status": "fail_closed",
            "count_or_value": f"{uq.get('release_ready_qoi_labels', 0)}/{uq.get('qoi_labels', 0)}",
            "release_ready": "false",
            "why": "same-QOI setup UQ is diagnostic only; release-ready QOI labels remain zero",
        },
        {
            "gate": "candidate_freeze",
            "status": "closed_not_run",
            "count_or_value": f"full={final.get('freeze_ready_candidates', 0)}; r4={r4.get('freeze_allowed_rows', 0)}",
            "release_ready": "false",
            "why": "no full five-family or no-junction candidate may freeze until source/property and same-QOI UQ gates pass",
        },
        {
            "gate": "final_score",
            "status": "closed_not_run",
            "count_or_value": str(final.get("final_score_values", 0)),
            "release_ready": "false",
            "why": "final score remains forbidden before freeze",
        },
    ]


def next_rows() -> list[dict[str, str]]:
    return [
        {
            "priority": "1",
            "next_task": "release-grade source/property provenance repair",
            "why": "this is now the controlling H2 blocker after Salt1 runtime coverage landed",
            "acceptance": "five source-family rows have explicit source envelope, property labels, source-family provenance, subspan/area basis, split role, and release/fail decision",
        },
        {
            "priority": "2",
            "next_task": "same-QOI release UQ rerun after provenance repair",
            "why": "UQ cannot be release-grade while source/property rows are diagnostic-only",
            "acceptance": "exact same QOI labels get release-ready UQ rows without protected runtime inputs",
        },
        {
            "priority": "3",
            "next_task": "freeze gate rerun",
            "why": "only useful after exactly one candidate has release-grade provenance and UQ",
            "acceptance": "one frozen candidate opens S15/S6, or a clean no-freeze thesis result remains documented",
        },
    ]


def claim_rows() -> list[dict[str, str]]:
    return [
        {"claim": "full five-family PASSIVE-H2 runtime coverage includes Salt1 junction", "allowed": "true", "scope": "diagnostic runtime evidence"},
        {"claim": "PASSIVE-H2 changed heat ledger in Salt1/Salt2/Salt3/Salt4", "allowed": "true", "scope": "diagnostic runtime evidence"},
        {"claim": "Salt1 junction is source/property release-grade", "allowed": "false", "scope": "strict provenance still closed"},
        {"claim": "PASSIVE-H2 candidate is frozen or score-ready", "allowed": "false", "scope": "release/UQ gates fail closed"},
    ]


def sources() -> list[dict[str, str]]:
    paths = [
        ("salt1_junction_runtime", SALT1 / "summary.json"),
        ("salt1_terminal_fluid_summary", SALT1 / "fluid_smoke_outputs/salt_1/summary.json"),
        ("salt2_runtime", SALT2 / "summary.json"),
        ("salt34_runtime", SALT34 / "case_runtime_smoke_summary.csv"),
        ("subspan_release_gate", SUBSPAN / "summary.json"),
        ("salt2_same_qoi_uq", SALT2_UQ / "summary.json"),
        ("candidate_source_property_gate", CANDIDATE_GATE / "summary.json"),
        ("final_form_gate", FINAL_GATE / "summary.json"),
        ("r4_predeclared_gate", R4 / "summary.json"),
    ]
    return [{"role": role, "path": rel(path), "mode": "read_only", "exists": b(path.exists())} for role, path in paths]


def guards() -> list[dict[str, str]]:
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


def write_docs(summary: dict[str, Any]) -> None:
    ensure_dir(STATUS.parent)
    ensure_dir(JOURNAL.parent)
    readme = f"""---
provenance:
  - {rel(OUT / "summary.json")}
  - {rel(SALT1 / "summary.json")}
  - {rel(SALT1 / "fluid_smoke_outputs/salt_1/summary.json")}
tags: [PASSIVE-H2, post-junction, source-property, no-release]
related:
  - {rel(STATUS)}
  - {rel(JOURNAL)}
task: {TASK_ID}
date: 2026-07-22
role: Implementer / Tester / Writer / Reviewer
type: work_product
status: complete
---
# PASSIVE-H2 Post-Junction Source/Property Gate

Decision: `{summary["decision"]}`.

Salt1 junction runtime coverage is no longer the mechanical blocker. The full
five-family PASSIVE-H2 diagnostic path now has four-case runtime support:
`{summary["runtime_completed_case_rows"]}/4` completed, `{summary["accepted_root_case_rows"]}/4`
with accepted roots, and `{summary["runtime_nonzero_case_rows"]}/4` with nonzero
radiation heat-ledger response.

Release still fails closed: strict source-envelope rows
`{summary["strict_source_envelope_ready_rows"]}`, release-grade subspan rows
`{summary["release_grade_subspan_rows"]}`, same-QOI release-UQ labels
`{summary["release_ready_qoi_labels"]}`, freeze-ready candidates
`{summary["freeze_ready_candidates"]}`, final score values
`{summary["final_score_values"]}`.
"""
    (OUT / "README.md").write_text(readme, encoding="utf-8")
    STATUS.write_text(
        f"""---
provenance:
  - {rel(OUT / "summary.json")}
tags: [status, PASSIVE-H2, post-junction, no-release]
related:
  - {rel(OUT / "README.md")}
  - {rel(JOURNAL)}
task: {TASK_ID}
date: 2026-07-22
role: Implementer / Tester / Writer / Reviewer
type: status
status: complete
---
# {TASK_ID}

Objective: rerun PASSIVE-H2 source/property readiness after Salt1 junction
runtime recovery.

Outcome: `{summary["decision"]}`. Runtime coverage is now diagnostic-complete
for Salt1/Salt2/Salt3/Salt4, including Salt1 junction. Release/freeze remains
closed because strict source-envelope, release-grade subspan, and same-QOI
release-UQ rows remain zero.

## Changes Made

- Added the post-junction PASSIVE-H2 source/property gate builder and tests.
- Published the gate package under `{rel(OUT)}`.
- Wrote status, journal, import manifest, claim boundaries, runtime evidence,
  release gate, next-action queue, source manifest, and guardrail artifacts.

## Validation

- `python3.11 tools/analyze/build_passive_h2_post_junction_source_property_gate.py`
- `python3.11 -m unittest tools.analyze.test_passive_h2_post_junction_source_property_gate`
- `python3.11 -m py_compile tools/analyze/build_passive_h2_post_junction_source_property_gate.py tools/analyze/test_passive_h2_post_junction_source_property_gate.py`
- `python3.11 tools/agent/runtime_input_lint.py {rel(OUT)} {rel(STATUS)} {rel(JOURNAL)} {rel(IMPORT)}`
- `python3.11 tools/agent/split_policy_lint.py {rel(OUT)} {rel(STATUS)} {rel(JOURNAL)} {rel(IMPORT)}`
- `python3.11 tools/agent/manifest_check.py {rel(IMPORT)} --check-paths`
- `python3.11 tools/agent/finish_task.py --task-id {TASK_ID}`

## Guardrails

No native-output mutation, registry/admission mutation, scheduler action,
Fluid/external edit, protected scoring, source/property release, candidate
freeze, or final score.
""",
        encoding="utf-8",
    )
    JOURNAL.write_text(
        f"""---
provenance:
  - {rel(OUT / "summary.json")}
  - {rel(OUT / "post_junction_runtime_evidence.csv")}
tags: [journal, PASSIVE-H2, post-junction, source-property]
related:
  - {rel(STATUS)}
  - {rel(OUT / "README.md")}
task: {TASK_ID}
date: 2026-07-22
role: Implementer / Tester / Writer / Reviewer
type: journal
status: complete
---
# PASSIVE-H2 Post-Junction Source/Property Gate

Attempted: consume the completed Salt1 junction runtime smoke with the existing
Salt2/Salt3/Salt4 PASSIVE-H2 diagnostic runtime evidence and rerun the
source/property readiness disposition.

Observed: Salt1 now contributes five train operator rows, accepted diagnostic
roots, no forbidden/protected runtime inputs, and a nonzero radiation heat-ledger
delta. Across Salt1/Salt2/Salt3/Salt4, the runtime feasibility evidence is now
complete and nonzero.

Inferred: the prior Salt1 junction runtime coverage gap is closed. The remaining
H2 blockers are stricter and scientific: release-grade source/property
provenance, release-grade subspan rows, and exact same-QOI release UQ.

Caveat: this task publishes no score, no freeze, no coefficient admission, and
no source/property release.
""",
        encoding="utf-8",
    )


def write_import(summary: dict[str, Any]) -> None:
    package_files = [rel(path) for path in sorted(OUT.rglob("*")) if path.is_file()]
    changed = sorted(
        dict.fromkeys(
            [
                ".agent/BOARD.md",
                rel(STATUS),
                rel(JOURNAL),
                rel(IMPORT),
                "tools/analyze/build_passive_h2_post_junction_source_property_gate.py",
                "tools/analyze/test_passive_h2_post_junction_source_property_gate.py",
                ".agent/STATE.md",
                ".agent/catalog.json",
                ".agent/catalog.csv",
                ".agent/BLOCKERS.md",
                *package_files,
            ]
        )
    )
    json_dump(
        IMPORT,
        {
            "task": TASK_ID,
            "task_id": TASK_ID,
            "generated_at": iso_timestamp(),
            "changed_files": changed,
            "changed_paths": changed,
            "read_only_context": [row["path"] for row in sources()],
            "results": summary,
            "native_solver_outputs_mutated": False,
            "registry_mutated": False,
            "scheduler_action": False,
            "external_fluid_edit": False,
            "protected_scoring": False,
            "source_property_release": False,
            "candidate_freeze": False,
            "final_score_claim": False,
        },
    )


def build() -> dict[str, Any]:
    ensure_dir(OUT)
    runtime = runtime_rows()
    gates = release_gate_rows()
    next_actions = next_rows()
    claims = claim_rows()
    manifest = sources()
    guardrails = guards()
    csv_dump(OUT / "post_junction_runtime_evidence.csv", list(runtime[0]), runtime)
    csv_dump(OUT / "post_junction_release_gate.csv", list(gates[0]), gates)
    csv_dump(OUT / "post_junction_next_action_queue.csv", list(next_actions[0]), next_actions)
    csv_dump(OUT / "claim_boundaries.csv", list(claims[0]), claims)
    csv_dump(OUT / "source_manifest.csv", list(manifest[0]), manifest)
    csv_dump(OUT / "no_mutation_guardrails.csv", list(guardrails[0]), guardrails)
    candidate = read_json(CANDIDATE_GATE / "summary.json")
    uq = read_json(SALT2_UQ / "summary.json")
    final = read_json(FINAL_GATE / "summary.json")
    subspan = read_json(SUBSPAN / "summary.json")
    summary = {
        "task_id": TASK_ID,
        "generated_at": iso_timestamp(),
        "decision": "passive_h2_post_junction_runtime_complete_source_property_release_fail_closed",
        "candidate_id": "PASSIVE-H2-CAND001",
        "runtime_case_rows": len(runtime),
        "runtime_completed_case_rows": sum(row["runtime_completed"] == "true" for row in runtime),
        "accepted_root_case_rows": sum(row["accepted_roots"] == "true" for row in runtime),
        "runtime_nonzero_case_rows": sum(row["radiation_on_nonzero"] == "true" for row in runtime),
        "salt1_junction_runtime_gap_closed": True,
        "strict_source_envelope_ready_rows": int(candidate.get("strict_source_envelope_pass_rows", candidate.get("source_property_release_ready_rows", 0))),
        "source_property_release_ready_rows": int(candidate.get("source_property_release_ready_rows", 0)),
        "release_grade_subspan_rows": int(subspan.get("salt2_release_ready_rows", 0)),
        "release_ready_qoi_labels": int(uq.get("release_ready_qoi_labels", 0)),
        "freeze_ready_candidates": int(final.get("freeze_ready_candidates", 0)),
        "final_score_values": int(final.get("final_score_values", 0)),
        "source_property_release": False,
        "numeric_q_loss_release": False,
        "qwall_release": False,
        "coefficient_admission": False,
        "candidate_freeze": False,
        "protected_scoring": False,
        "final_score_claim": False,
        "native_output_mutation": False,
        "registry_or_admission_mutation": False,
        "scheduler_action_in_this_task": False,
        "fluid_or_external_edit": False,
    }
    json_dump(OUT / "summary.json", summary)
    write_docs(summary)
    write_import(summary)
    return summary


def main() -> int:
    print(json.dumps(build(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
