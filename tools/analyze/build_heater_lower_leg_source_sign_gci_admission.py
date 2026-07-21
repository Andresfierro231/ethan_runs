#!/usr/bin/env python3
"""Build AGENT-468 heater lower-leg source/sign/GCI admission package.

This pass uses existing AGENT-459/466 evidence only. It narrows the
`closure-qoi-mesh-gci` blocker around the heater lower leg by separating source
ownership, sign/heat-balance, recirculation, and same-QOI mesh/GCI gates before
any Internal-Nu row can be admitted.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


TASK = "AGENT-468"
DATE = "2026-07-16"
ROOT = Path(__file__).resolve().parents[2]
OUT_REL = Path("work_products/2026-07/2026-07-16/2026-07-16_heater_lower_leg_source_sign_gci_admission")
OUT = ROOT / OUT_REL

AGENT459 = ROOT / "work_products/2026-07/2026-07-16/2026-07-16_branch_local_internal_nu_unblock"
AGENT466 = ROOT / "work_products/2026-07/2026-07-16/2026-07-16_downcomer_internal_nu_unlock_and_blocker_roadmap"
THERMAL_MAP = ROOT / "operational_notes/maps/thermal-closures-and-internal-nu.md"
MESH_MAP = ROOT / "operational_notes/maps/mesh-gci-and-uncertainty.md"
BLOCKERS = ROOT / ".agent/blockers.yml"

BRANCH_ADMISSION = AGENT459 / "branch_local_thermal_admission.csv"
FIT_ROWS = AGENT459 / "internal_nu_fit_admissible_rows.csv"
FINAL_USE_GCI = AGENT459 / "final_use_closure_qoi_gci.csv"
UNBLOCK_QUEUE = AGENT459 / "targeted_extraction_admission_queue.csv"
FUTURE_STUDIES = AGENT466 / "future_studies_and_blockers.csv"

SOURCE_PATHS = {
    "agent459_branch_admission": BRANCH_ADMISSION,
    "agent459_fit_rows": FIT_ROWS,
    "agent459_final_use_gci": FINAL_USE_GCI,
    "agent459_unblock_queue": UNBLOCK_QUEUE,
    "agent466_future_studies": FUTURE_STUDIES,
    "thermal_map": THERMAL_MAP,
    "mesh_map": MESH_MAP,
    "blocker_register": BLOCKERS,
}

SOURCE_SIGN_COLUMNS = [
    "canonical_leg_id",
    "leg_role",
    "candidate_rows",
    "nu_candidate_rows",
    "source_allows_fit_pass_rows",
    "residual_owner_pass_rows",
    "sign_heat_balance_pass_rows",
    "recirculation_pass_rows",
    "mesh_gci_pass_rows",
    "fit_admissible_internal_nu_rows",
    "source_region_status",
    "sign_heat_balance_status",
    "heat_balance_residual_status",
    "decision",
    "blocking_reason",
    "source_path",
]
MESH_COLUMNS = [
    "qoi_id",
    "quantity",
    "qoi_family",
    "complete_triplet",
    "current_publication_ready",
    "current_fit_admissible",
    "gci_status",
    "same_qoi_gate",
    "admission_use",
    "required_action",
    "source_paths",
]
CANDIDATE_COLUMNS = [
    "candidate_id",
    "case_id",
    "reported_segment_or_span",
    "qoi",
    "source_allows_fit",
    "residual_owner",
    "sign_heat_balance",
    "recirculation",
    "mesh_gci",
    "fit_admissible",
    "admission_decision",
    "failure_reasons",
    "source_path",
]
DELTA_COLUMNS = ["metric", "before_agent468", "after_agent468", "delta", "interpretation"]
QUEUE_COLUMNS = [
    "queue_id",
    "priority",
    "canonical_leg_id",
    "gate_family",
    "blocked_rows",
    "required_next_artifact",
    "acceptance_signal",
    "do_not_do_guardrail",
    "source_path",
]
DECISION_COLUMNS = [
    "blocker_id",
    "decision",
    "can_update_blocker_register",
    "resolved_by",
    "resolved_on",
    "criteria_passed",
    "criteria_failed",
    "scientific_interpretation",
    "next_unlock_sequence",
]
GCI_ADMITTED_COLUMNS = [
    "qoi_id",
    "canonical_leg_id",
    "reported_span_or_segment",
    "qoi_family",
    "quantity",
    "gci_status",
    "source_paths",
]
MANIFEST_COLUMNS = ["source_id", "path", "exists", "role"]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT.resolve()))
    except ValueError:
        return str(path)


def format_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, float):
        return f"{value:.12g}" if math.isfinite(value) else ""
    return str(value)


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
            writer.writerow({column: format_value(row.get(column, "")) for column in columns})
    return len(materialized)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def yes(value: Any) -> bool:
    return str(value).strip().lower() in {"yes", "true", "1", "pass", "admitted"}


def split_gate_vector(row: dict[str, str]) -> dict[str, str]:
    vector: dict[str, str] = {}
    for part in row.get("gate_vector", "").split(";"):
        if "=" not in part:
            continue
        key, value = part.split("=", 1)
        vector[key.strip()] = value.strip()
    return vector


def gate_pass(row: dict[str, str], gate: str) -> bool:
    return split_gate_vector(row).get(gate) == "yes"


def heater_fit_rows() -> list[dict[str, str]]:
    return [row for row in read_csv(FIT_ROWS) if row.get("canonical_leg_id") == "heater_lower_leg"]


def heater_final_gci_rows() -> list[dict[str, str]]:
    return [row for row in read_csv(FINAL_USE_GCI) if row.get("canonical_leg_id") == "heater_lower_leg"]


def source_sign_heat_balance_rows(fit_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    branch = next(row for row in read_csv(BRANCH_ADMISSION) if row["canonical_leg_id"] == "heater_lower_leg")
    source_pass = sum(1 for row in fit_rows if gate_pass(row, "source_allows_fit"))
    admitted = sum(1 for row in fit_rows if yes(row.get("fit_admissible", "")))
    blocking = [
        "source_gate_does_not_allow_internal_Nu_fit",
        "sign_heat_balance_gate_zero_pass_rows",
        "branch_local_recirculation_metric_missing",
        "same_qoi_publication_gci_missing",
    ]
    return [
        {
            "canonical_leg_id": "heater_lower_leg",
            "leg_role": branch["leg_role"],
            "candidate_rows": branch["candidate_rows"],
            "nu_candidate_rows": branch["nu_candidate_rows"],
            "source_allows_fit_pass_rows": source_pass,
            "residual_owner_pass_rows": branch["residual_owner_pass_rows"],
            "sign_heat_balance_pass_rows": branch["sign_heat_balance_pass_rows"],
            "recirculation_pass_rows": branch["recirculation_pass_rows"],
            "mesh_gci_pass_rows": branch["mesh_gci_pass_rows"],
            "fit_admissible_internal_nu_rows": admitted,
            "source_region_status": "blocking_source_region_requires_explicit_source_ownership",
            "sign_heat_balance_status": "fail_repaired_q_sign_label_conflict_and_zero_pass_rows",
            "heat_balance_residual_status": "blocking_internal_Nu_residual_absorption_forbidden",
            "decision": "admit_heater_internal_nu" if admitted else "not_admitted_source_sign_heat_balance_recirc_mesh",
            "blocking_reason": "" if admitted else ";".join(blocking),
            "source_path": rel(BRANCH_ADMISSION),
        }
    ]


def mesh_gci_gate_rows(final_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in final_rows:
        publication_ready = yes(row.get("current_publication_ready", ""))
        fit_ready = yes(row.get("current_fit_admissible", ""))
        complete_triplet = yes(row.get("complete_triplet", ""))
        same_qoi_gate = publication_ready and fit_ready and complete_triplet
        out.append(
            {
                "qoi_id": row.get("qoi_id", ""),
                "quantity": row.get("quantity", ""),
                "qoi_family": row.get("qoi_family", ""),
                "complete_triplet": complete_triplet,
                "current_publication_ready": publication_ready,
                "current_fit_admissible": fit_ready,
                "gci_status": row.get("gci_status", ""),
                "same_qoi_gate": same_qoi_gate,
                "admission_use": "admitted_gci_evidence" if same_qoi_gate else "not_admitted",
                "required_action": row.get("resolution_action", ""),
                "source_paths": row.get("source_paths", ""),
            }
        )
    return out


def candidate_admission_rows(fit_rows: list[dict[str, str]], mesh_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    any_mesh_pass = any(row["same_qoi_gate"] for row in mesh_rows)
    rows: list[dict[str, Any]] = []
    for row in fit_rows:
        source_pass = gate_pass(row, "source_allows_fit")
        residual_pass = gate_pass(row, "residual_owner")
        sign_pass = gate_pass(row, "sign_heat_balance")
        recirc_pass = gate_pass(row, "recirculation")
        mesh_pass = gate_pass(row, "mesh_gci") and any_mesh_pass
        admitted = source_pass and residual_pass and sign_pass and recirc_pass and mesh_pass
        failed = [
            name
            for name, passed in [
                ("source_allows_fit", source_pass),
                ("residual_owner", residual_pass),
                ("sign_heat_balance", sign_pass),
                ("recirculation", recirc_pass),
                ("mesh_gci", mesh_pass),
            ]
            if not passed
        ]
        existing_reason = row.get("failure_reasons", "")
        rows.append(
            {
                "candidate_id": row.get("candidate_id", ""),
                "case_id": row.get("case_id", ""),
                "reported_segment_or_span": row.get("reported_segment_or_span", ""),
                "qoi": row.get("qoi", ""),
                "source_allows_fit": source_pass,
                "residual_owner": residual_pass,
                "sign_heat_balance": sign_pass,
                "recirculation": recirc_pass,
                "mesh_gci": mesh_pass,
                "fit_admissible": admitted,
                "admission_decision": "admitted" if admitted else "not_admitted",
                "failure_reasons": ";".join(failed + ([existing_reason] if existing_reason else [])),
                "source_path": row.get("source_path", ""),
            }
        )
    return rows


def blocker_delta_rows(
    source_rows: list[dict[str, Any]],
    mesh_rows: list[dict[str, Any]],
    candidate_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    source = source_rows[0]
    mesh_pass = sum(1 for row in mesh_rows if row["same_qoi_gate"])
    admitted = sum(1 for row in candidate_rows if row["admission_decision"] == "admitted")
    return [
        {
            "metric": "heater_candidate_rows_reviewed",
            "before_agent468": source["candidate_rows"],
            "after_agent468": source["candidate_rows"],
            "delta": 0,
            "interpretation": "AGENT-468 narrows existing heater evidence; it does not add new CFD rows.",
        },
        {
            "metric": "heater_nu_candidate_rows_reviewed",
            "before_agent468": source["nu_candidate_rows"],
            "after_agent468": len(candidate_rows),
            "delta": int(len(candidate_rows)) - int(source["nu_candidate_rows"]),
            "interpretation": "The existing two heater Nu-equivalent rows are reviewed at row level.",
        },
        {
            "metric": "heater_source_sign_heat_balance_pass_rows",
            "before_agent468": 0,
            "after_agent468": source["sign_heat_balance_pass_rows"],
            "delta": source["sign_heat_balance_pass_rows"],
            "interpretation": "No source/sign/heat-balance pass row exists yet.",
        },
        {
            "metric": "heater_same_qoi_publication_gci_rows",
            "before_agent468": 0,
            "after_agent468": mesh_pass,
            "delta": mesh_pass,
            "interpretation": "No heater final-use GCI row is publication-ready.",
        },
        {
            "metric": "heater_fit_admissible_internal_nu_rows",
            "before_agent468": 0,
            "after_agent468": admitted,
            "delta": admitted,
            "interpretation": "The blocker remains open because no heater row passes all hard gates.",
        },
    ]


def next_queue_rows(mesh_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    thermal_sign_blocked = sum(
        1 for row in mesh_rows if row["qoi_family"] == "thermal" and row["gci_status"] == "not_publication_gci_sign_review_required"
    )
    missing_triplet = sum(1 for row in mesh_rows if row["gci_status"] == "not_computed_missing_triplet")
    nonpublication_hydraulic = sum(1 for row in mesh_rows if row["qoi_family"] == "closure" and not row["same_qoi_gate"])
    return [
        {
            "queue_id": "heater_source_enthalpy_sign_heat_balance_admission",
            "priority": "P0",
            "canonical_leg_id": "heater_lower_leg",
            "gate_family": "source_sign_heat_balance",
            "blocked_rows": thermal_sign_blocked,
            "required_next_artifact": "row-level heater source ownership, enthalpy direction, q-sign label, and heat-balance residual admission table",
            "acceptance_signal": ">=1 heater Nu-equivalent row has source ownership and sign/heat-balance gates passing without residual absorption",
            "do_not_do_guardrail": "do not use Nu to absorb heater source, wall-storage, passive loss, or sign-label residuals",
            "source_path": rel(FINAL_USE_GCI),
        },
        {
            "queue_id": "heater_same_qoi_nu_or_htc_ua_gci_reconciliation",
            "priority": "P0",
            "canonical_leg_id": "heater_lower_leg",
            "gate_family": "same_qoi_mesh_gci",
            "blocked_rows": missing_triplet + thermal_sign_blocked,
            "required_next_artifact": "same-QOI Nu triplet or explicit HTC/UA closure-QOI choice after source/sign admission",
            "acceptance_signal": ">=1 heater Nu-equivalent row has publication-ready same-QOI GCI or is explicitly excluded",
            "do_not_do_guardrail": "do not treat HTC/UA GCI as Nu GCI unless the admitted final-use QOI is explicitly HTC/UA",
            "source_path": rel(FINAL_USE_GCI),
        },
        {
            "queue_id": "heater_branch_recirculation_metric",
            "priority": "P1",
            "canonical_leg_id": "heater_lower_leg",
            "gate_family": "recirculation",
            "blocked_rows": 2,
            "required_next_artifact": "branch-local heater recirculation/throughflow metric or explicit low-recirculation admission",
            "acceptance_signal": "heater recirculation gate passes for the admitted source/sign/GCI row",
            "do_not_do_guardrail": "do not assume source-region heater flow is single-stream until the branch-local metric is documented",
            "source_path": rel(FIT_ROWS),
        },
        {
            "queue_id": "heater_hydraulic_final_use_exclude_or_reextract",
            "priority": "P2",
            "canonical_leg_id": "heater_lower_leg",
            "gate_family": "final_use_exclusion_or_reextract",
            "blocked_rows": nonpublication_hydraulic,
            "required_next_artifact": "exclude lower-leg hydraulic rows from thermal closeout or rerun same-QOI extraction on admitted source contract",
            "acceptance_signal": "every heater final-use row is either publication-ready or explicitly excluded before blocker closeout",
            "do_not_do_guardrail": "do not spend GCI effort on final-use rows that branch-local admission excludes",
            "source_path": rel(FINAL_USE_GCI),
        },
    ]


def decision_rows(candidate_rows: list[dict[str, Any]], queue: list[dict[str, Any]]) -> list[dict[str, Any]]:
    admitted = sum(1 for row in candidate_rows if row["admission_decision"] == "admitted")
    return [
        {
            "blocker_id": "closure-qoi-mesh-gci",
            "decision": "resolved" if admitted else "not_resolved_heater_narrowed",
            "can_update_blocker_register": "yes",
            "resolved_by": rel(OUT) if admitted else "",
            "resolved_on": DATE if admitted else "",
            "criteria_passed": "heater_rows_reviewed;source_sign_gci_queue_narrowed;admitted_only_gci_exported",
            "criteria_failed": "" if admitted else "heater_source_gate_missing;heater_sign_heat_balance_missing;heater_recirculation_missing;heater_same_qoi_publication_gci_missing",
            "scientific_interpretation": "Heater lower-leg evidence is now row-level reviewed, but no Internal-Nu or same-QOI GCI row can be admitted yet.",
            "next_unlock_sequence": " -> ".join(row["queue_id"] for row in queue),
        }
    ]


def source_manifest_rows() -> list[dict[str, Any]]:
    roles = {
        "agent459_branch_admission": "branch-local gate summary",
        "agent459_fit_rows": "row-level Internal-Nu gate vectors",
        "agent459_final_use_gci": "heater final-use mesh/GCI state",
        "agent459_unblock_queue": "prior targeted unblock queue",
        "agent466_future_studies": "blocker roadmap queue",
        "thermal_map": "thermal/Internal-Nu continuity hub",
        "mesh_map": "mesh/GCI continuity hub",
        "blocker_register": "current blocker ledger",
    }
    return [{"source_id": key, "path": rel(path), "exists": path.exists(), "role": roles[key]} for key, path in SOURCE_PATHS.items()]


def write_readme(out: Path, summary: dict[str, Any]) -> None:
    text = f"""---
provenance:
  - {rel(BRANCH_ADMISSION)}
  - {rel(FIT_ROWS)}
  - {rel(FINAL_USE_GCI)}
  - {rel(UNBLOCK_QUEUE)}
  - {rel(FUTURE_STUDIES)}
tags: [internal-nu, heater, closure-qoi, mesh-gci, source-sign, blocker-roadmap]
related:
  - .agent/blockers.yml
  - operational_notes/maps/thermal-closures-and-internal-nu.md
  - operational_notes/maps/mesh-gci-and-uncertainty.md
task: {TASK}
date: {DATE}
role: Coordinator/Thermal-modeling/Mesh-GCI/Implementer/Tester/Writer
type: work_product
status: complete
---
# Heater Lower-Leg Source/Sign/GCI Admission

Generated: `{summary["generated_at"]}`

## Decision

`closure-qoi-mesh-gci`: `{summary["blocker_decision"]}`.

The heater lower leg is reviewed at source/sign/heat-balance and same-QOI
mesh/GCI level, but no row is admitted. Current evidence still has zero
source/sign heat-balance pass rows, zero branch-local recirculation pass rows,
and zero publication-ready heater same-QOI GCI rows.

## Results

- Heater branch candidate rows reviewed: `{summary["heater_candidate_rows"]}`.
- Heater Nu-equivalent candidate rows reviewed: `{summary["heater_nu_candidate_rows"]}`.
- Heater fit-admissible rows: `{summary["heater_fit_admissible_rows"]}`.
- Heater final-use GCI rows reviewed: `{summary["heater_final_use_gci_rows"]}`.
- Heater publication-ready same-QOI GCI rows: `{summary["heater_publication_ready_gci_rows"]}`.
- Next extraction/admission rows: `{summary["next_extraction_queue_rows"]}`.

## Method

This package replays existing AGENT-459 gate vectors and final-use GCI rows for
`heater_lower_leg`. It admits a heater row only when source ownership,
residual-owner, sign/heat-balance, recirculation, and same-QOI publication-GCI
gates all pass. No native CFD output, registry state, scheduler state, or
external Fluid file is changed.

## Outputs

- `heater_source_sign_heat_balance_gate.csv`
- `heater_same_qoi_mesh_gci_gate.csv`
- `heater_internal_nu_candidate_admission.csv`
- `gci_results_admitted_only.csv`
- `closure_qoi_blocker_delta.csv`
- `next_extraction_queue.csv`
- `blocker_decision.csv`
- `closure_qoi_resolution_decision.md`
- `source_manifest.csv`
- `summary.json`
"""
    (out / "README.md").write_text(text, encoding="utf-8")


def write_resolution_md(out: Path, summary: dict[str, Any]) -> None:
    text = f"""---
provenance:
  - {rel(OUT / "blocker_decision.csv")}
  - {rel(OUT / "heater_source_sign_heat_balance_gate.csv")}
  - {rel(OUT / "heater_same_qoi_mesh_gci_gate.csv")}
tags: [closure-qoi, mesh-gci, heater, blocker-decision]
related:
  - .agent/blockers.yml
task: {TASK}
date: {DATE}
type: decision
status: complete
---
# Closure-QOI Resolution Decision

Decision: `{summary["blocker_decision"]}`.

AGENT-468 does not clear `closure-qoi-mesh-gci`. It narrows the heater lower-leg
piece of the blocker to a precise extraction/admission queue: source/enthalpy
sign and heat-balance admission, same-QOI Nu-or-HTC/UA GCI reconciliation,
heater branch recirculation evidence, and explicit exclusion or re-extraction
for non-publication lower-leg hydraulic final-use rows.

`gci_results_admitted_only.csv` is intentionally empty apart from its header:
there are `{summary["heater_publication_ready_gci_rows"]}` admitted heater
same-QOI GCI rows.
"""
    (out / "closure_qoi_resolution_decision.md").write_text(text, encoding="utf-8")


def build_package(out: Path = OUT) -> dict[str, Any]:
    fit_rows = heater_fit_rows()
    final_rows = heater_final_gci_rows()
    source_rows = source_sign_heat_balance_rows(fit_rows)
    mesh_rows = mesh_gci_gate_rows(final_rows)
    candidate_rows = candidate_admission_rows(fit_rows, mesh_rows)
    delta = blocker_delta_rows(source_rows, mesh_rows, candidate_rows)
    queue = next_queue_rows(mesh_rows)
    decision = decision_rows(candidate_rows, queue)
    manifest = source_manifest_rows()
    admitted_gci = [
        {
            "qoi_id": row["qoi_id"],
            "canonical_leg_id": "heater_lower_leg",
            "reported_span_or_segment": "lower_leg",
            "qoi_family": row["qoi_family"],
            "quantity": row["quantity"],
            "gci_status": row["gci_status"],
            "source_paths": row["source_paths"],
        }
        for row in mesh_rows
        if row["same_qoi_gate"]
    ]

    source_summary = source_rows[0]
    summary = {
        "task": TASK,
        "generated_at": utc_now(),
        "blocker_decision": decision[0]["decision"],
        "source_package": rel(OUT),
        "heater_candidate_rows": int(source_summary["candidate_rows"]),
        "heater_nu_candidate_rows": int(source_summary["nu_candidate_rows"]),
        "heater_fit_admissible_rows": sum(1 for row in candidate_rows if row["admission_decision"] == "admitted"),
        "heater_source_allows_fit_pass_rows": int(source_summary["source_allows_fit_pass_rows"]),
        "heater_sign_heat_balance_pass_rows": int(source_summary["sign_heat_balance_pass_rows"]),
        "heater_recirculation_pass_rows": int(source_summary["recirculation_pass_rows"]),
        "heater_mesh_gci_pass_rows": int(source_summary["mesh_gci_pass_rows"]),
        "heater_final_use_gci_rows": len(mesh_rows),
        "heater_publication_ready_gci_rows": len(admitted_gci),
        "heater_thermal_sign_blocked_gci_rows": sum(
            1 for row in mesh_rows if row["gci_status"] == "not_publication_gci_sign_review_required"
        ),
        "heater_missing_triplet_gci_rows": sum(1 for row in mesh_rows if row["gci_status"] == "not_computed_missing_triplet"),
        "heater_nonpublication_hydraulic_gci_rows": sum(
            1 for row in mesh_rows if row["qoi_family"] == "closure" and not row["same_qoi_gate"]
        ),
        "next_extraction_queue_rows": len(queue),
        "outputs": [
            "README.md",
            "heater_source_sign_heat_balance_gate.csv",
            "heater_same_qoi_mesh_gci_gate.csv",
            "heater_internal_nu_candidate_admission.csv",
            "gci_results_admitted_only.csv",
            "closure_qoi_blocker_delta.csv",
            "next_extraction_queue.csv",
            "blocker_decision.csv",
            "closure_qoi_resolution_decision.md",
            "source_manifest.csv",
            "summary.json",
        ],
    }

    out.mkdir(parents=True, exist_ok=True)
    write_csv(out / "heater_source_sign_heat_balance_gate.csv", source_rows, SOURCE_SIGN_COLUMNS)
    write_csv(out / "heater_same_qoi_mesh_gci_gate.csv", mesh_rows, MESH_COLUMNS)
    write_csv(out / "heater_internal_nu_candidate_admission.csv", candidate_rows, CANDIDATE_COLUMNS)
    write_csv(out / "gci_results_admitted_only.csv", admitted_gci, GCI_ADMITTED_COLUMNS)
    write_csv(out / "closure_qoi_blocker_delta.csv", delta, DELTA_COLUMNS)
    write_csv(out / "next_extraction_queue.csv", queue, QUEUE_COLUMNS)
    write_csv(out / "blocker_decision.csv", decision, DECISION_COLUMNS)
    write_csv(out / "source_manifest.csv", manifest, MANIFEST_COLUMNS)
    write_json(out / "summary.json", summary)
    write_readme(out, summary)
    write_resolution_md(out, summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args()
    summary = build_package(args.out)
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
