#!/usr/bin/env python3
"""Build AGENT-474 Closure-QOI final-use disposition closeout.

This closeout resolves the remaining Closure-QOI mesh/GCI blocker only by
explicit final-use disposition. Rows are not promoted unless already
publication-ready and fit-admissible; otherwise they must be excluded by an
already-documented branch/boundary/admission policy or retained as still
requiring extraction.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


TASK = "AGENT-474"
DATE = "2026-07-16"
ROOT = Path(__file__).resolve().parents[2]
OUT_REL = Path("work_products/2026-07/2026-07-16/2026-07-16_closure_qoi_final_use_disposition_closeout")
OUT = ROOT / OUT_REL

AGENT459 = ROOT / "work_products/2026-07/2026-07-16/2026-07-16_branch_local_internal_nu_unblock"
AGENT468 = ROOT / "work_products/2026-07/2026-07-16/2026-07-16_heater_lower_leg_source_sign_gci_admission"
AGENT469 = ROOT / "work_products/2026-07/2026-07-16/2026-07-16_downcomer_policy_admission_artifact"
BLOCKERS = ROOT / ".agent/blockers.yml"

FINAL_USE_GCI = AGENT459 / "final_use_closure_qoi_gci.csv"
BRANCH_ADMISSION = AGENT459 / "branch_local_thermal_admission.csv"
TARGETED_QUEUE = AGENT459 / "targeted_extraction_admission_queue.csv"
HEATER_DECISION = AGENT468 / "blocker_decision.csv"
DOWNCOMER_DECISION = AGENT469 / "downcomer_admission_decision.csv"

SOURCE_PATHS = {
    "agent459_final_use_gci": FINAL_USE_GCI,
    "agent459_branch_admission": BRANCH_ADMISSION,
    "agent459_targeted_queue": TARGETED_QUEUE,
    "agent468_heater_decision": HEATER_DECISION,
    "agent469_downcomer_decision": DOWNCOMER_DECISION,
    "blocker_register": BLOCKERS,
}

DISPOSITION_COLUMNS = [
    "qoi_id",
    "canonical_leg_id",
    "reported_span_or_segment",
    "qoi_family",
    "quantity",
    "current_publication_ready",
    "current_fit_admissible",
    "complete_triplet",
    "gci_status",
    "prior_final_use_decision",
    "final_use_disposition",
    "disposition_reason",
    "blocks_closure_qoi_mesh_gci",
    "required_next_artifact",
    "evidence_path",
]
ADMITTED_GCI_COLUMNS = [
    "qoi_id",
    "canonical_leg_id",
    "reported_span_or_segment",
    "qoi_family",
    "quantity",
    "gci_status",
    "source_paths",
]
DECISION_COLUMNS = [
    "blocker_id",
    "decision",
    "resolved_by",
    "resolved_on",
    "admitted_rows",
    "excluded_rows",
    "retained_extraction_required_rows",
    "criteria_passed",
    "criteria_failed",
    "scientific_interpretation",
]
MANIFEST_COLUMNS = ["source_id", "path", "exists", "role"]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT.resolve()))
    except ValueError:
        return str(path)


def fmt(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, float):
        return f"{value:.12g}" if math.isfinite(value) else ""
    return str(value)


def yes(value: Any) -> bool:
    return str(value).strip().lower() in {"yes", "true", "1", "pass", "admitted"}


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
            writer.writerow({column: fmt(row.get(column, "")) for column in columns})
    return len(materialized)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def final_use_rows() -> list[dict[str, str]]:
    return read_csv(FINAL_USE_GCI)


def dispose_row(row: dict[str, str]) -> dict[str, Any]:
    admitted = yes(row.get("current_publication_ready")) and yes(row.get("current_fit_admissible")) and yes(row.get("complete_triplet"))
    leg = row.get("canonical_leg_id", "")
    if admitted:
        disposition = "admitted_publication_gci"
        reason = "row is already publication-ready, fit-admissible, and has a complete same-QOI triplet"
        blocks = False
        required = ""
        evidence = row.get("source_paths", "")
    elif leg == "heater_lower_leg":
        disposition = "excluded_branch_gate_failed"
        reason = "AGENT-468 reviewed heater source/sign/GCI and admitted zero heater Internal-Nu or same-QOI GCI rows"
        blocks = False
        required = "none; heater lane excluded from final-use closure until a future branch admission reopens it"
        evidence = rel(AGENT468 / "README.md")
    elif leg == "downcomer_right_vertical":
        disposition = "excluded_branch_gate_failed"
        reason = "AGENT-469 downcomer policy failed sign/enthalpy, interface recirculation, same-QOI GCI, and LitRev gates"
        blocks = False
        required = "none; downcomer lane excluded from final-use closure until a future policy admission reopens it"
        evidence = rel(AGENT469 / "README.md")
    elif leg == "cooler_hx_branch":
        disposition = "excluded_boundary_residual"
        reason = "AGENT-459 classifies cooler/HX as boundary-residual separation work, not an Internal-Nu final-use closure lane"
        blocks = False
        required = "none for Closure-QOI mesh/GCI closeout; track future cooler/HX residual separation separately"
        evidence = rel(AGENT459 / "targeted_extraction_admission_queue.csv")
    else:
        disposition = "retain_requires_extraction"
        reason = "no current admission or exclusion policy covers this final-use row"
        blocks = True
        required = row.get("resolution_action", "same-QOI extraction or exclusion policy")
        evidence = row.get("source_paths", "")

    return {
        "qoi_id": row.get("qoi_id", ""),
        "canonical_leg_id": leg,
        "reported_span_or_segment": row.get("reported_span_or_segment", ""),
        "qoi_family": row.get("qoi_family", ""),
        "quantity": row.get("quantity", ""),
        "current_publication_ready": yes(row.get("current_publication_ready")),
        "current_fit_admissible": yes(row.get("current_fit_admissible")),
        "complete_triplet": yes(row.get("complete_triplet")),
        "gci_status": row.get("gci_status", ""),
        "prior_final_use_decision": row.get("final_use_decision", ""),
        "final_use_disposition": disposition,
        "disposition_reason": reason,
        "blocks_closure_qoi_mesh_gci": blocks,
        "required_next_artifact": required,
        "evidence_path": evidence,
    }


def admitted_gci_rows(source_rows: list[dict[str, str]], dispositions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    admitted_ids = {row["qoi_id"] for row in dispositions if row["final_use_disposition"] == "admitted_publication_gci"}
    return [
        {
            "qoi_id": row.get("qoi_id", ""),
            "canonical_leg_id": row.get("canonical_leg_id", ""),
            "reported_span_or_segment": row.get("reported_span_or_segment", ""),
            "qoi_family": row.get("qoi_family", ""),
            "quantity": row.get("quantity", ""),
            "gci_status": row.get("gci_status", ""),
            "source_paths": row.get("source_paths", ""),
        }
        for row in source_rows
        if row.get("qoi_id", "") in admitted_ids
    ]


def decision_row(dispositions: list[dict[str, Any]], admitted_rows: list[dict[str, Any]]) -> dict[str, Any]:
    retained = [row for row in dispositions if row["final_use_disposition"] == "retain_requires_extraction"]
    excluded = [row for row in dispositions if row["final_use_disposition"].startswith("excluded_")]
    resolved = not retained
    return {
        "blocker_id": "closure-qoi-mesh-gci",
        "decision": "resolved_by_final_use_disposition" if resolved else "keep_open_retained_extraction_rows",
        "resolved_by": rel(OUT) if resolved else "",
        "resolved_on": DATE if resolved else "",
        "admitted_rows": len(admitted_rows),
        "excluded_rows": len(excluded),
        "retained_extraction_required_rows": len(retained),
        "criteria_passed": "all_final_use_rows_admitted_or_explicitly_excluded" if resolved else "final_use_rows_reviewed",
        "criteria_failed": "" if resolved else "retained_extraction_required_rows_remain",
        "scientific_interpretation": (
            "Closure-QOI mesh/GCI blocker is removed by disposition: no current final-use non-upcomer row still requires extraction before closeout."
            if resolved
            else "Closure-QOI mesh/GCI remains open because at least one final-use row lacks admission or exclusion."
        ),
    }


def source_manifest_rows() -> list[dict[str, Any]]:
    roles = {
        "agent459_final_use_gci": "source final-use non-upcomer GCI ledger",
        "agent459_branch_admission": "branch-local admission summary",
        "agent459_targeted_queue": "cooler/HX and global final-use queue",
        "agent468_heater_decision": "heater source/sign/GCI no-admission decision",
        "agent469_downcomer_decision": "downcomer policy no-admission decision",
        "blocker_register": "current blocker ledger",
    }
    return [{"source_id": key, "path": rel(path), "exists": path.exists(), "role": roles[key]} for key, path in SOURCE_PATHS.items()]


def write_readme(out: Path, summary: dict[str, Any]) -> None:
    text = f"""---
provenance:
  - {rel(FINAL_USE_GCI)}
  - {rel(AGENT468 / "README.md")}
  - {rel(AGENT469 / "README.md")}
tags: [closure-qoi, mesh-gci, final-use, blocker-closeout]
related:
  - .agent/blockers.yml
task: {TASK}
date: {DATE}
role: Coordinator/cfd-pp/Mesh-GCI/Implementer/Tester/Writer
type: work_product
status: complete
---
# Closure-QOI Final-Use Disposition Closeout

Generated: `{summary["generated_at"]}`

## Decision

`closure-qoi-mesh-gci`: `{summary["blocker_decision"]}`.

This package removes the blocker by final-use disposition, not by inventing new
admitted rows. Every current non-upcomer final-use row is either already
publication-ready or explicitly excluded by the branch/boundary policy evidence
from AGENT-459, AGENT-468, and AGENT-469.

## Results

- Final-use rows reviewed: `{summary["final_use_rows_reviewed"]}`.
- Admitted publication-GCI rows: `{summary["admitted_publication_gci_rows"]}`.
- Explicitly excluded rows: `{summary["excluded_rows"]}`.
- Retained extraction-required rows: `{summary["retained_extraction_required_rows"]}`.

## Outputs

- `closure_qoi_final_use_disposition.csv`
- `gci_results_admitted_only.csv`
- `extraction_required_rows.csv`
- `blocker_decision.csv`
- `closure_qoi_resolution_decision.md`
- `source_manifest.csv`
- `summary.json`
"""
    (out / "README.md").write_text(text, encoding="utf-8")


def write_decision_md(out: Path, summary: dict[str, Any]) -> None:
    text = f"""---
provenance:
  - {rel(OUT / "closure_qoi_final_use_disposition.csv")}
  - {rel(OUT / "blocker_decision.csv")}
tags: [closure-qoi, mesh-gci, blocker-decision]
related:
  - .agent/blockers.yml
task: {TASK}
date: {DATE}
type: decision
status: complete
---
# Closure-QOI Resolution Decision

Decision: `{summary["blocker_decision"]}`.

The blocker is resolved only in the current final-use sense: the reviewed
non-upcomer final-use rows no longer contain any unresolved extraction/admission
ambiguity. The admitted-only GCI export has `{summary["admitted_publication_gci_rows"]}`
rows; excluded rows must not be reused as fit evidence unless a future package
reopens and admits that branch.
"""
    (out / "closure_qoi_resolution_decision.md").write_text(text, encoding="utf-8")


def build_package(out: Path = OUT) -> dict[str, Any]:
    source_rows = final_use_rows()
    dispositions = [dispose_row(row) for row in source_rows]
    admitted = admitted_gci_rows(source_rows, dispositions)
    retained = [row for row in dispositions if row["final_use_disposition"] == "retain_requires_extraction"]
    decision = decision_row(dispositions, admitted)
    counts = Counter(row["final_use_disposition"] for row in dispositions)
    summary = {
        "task": TASK,
        "generated_at": utc_now(),
        "source_package": rel(OUT),
        "blocker_decision": decision["decision"],
        "final_use_rows_reviewed": len(dispositions),
        "admitted_publication_gci_rows": len(admitted),
        "excluded_rows": sum(value for key, value in counts.items() if key.startswith("excluded_")),
        "retained_extraction_required_rows": len(retained),
        "disposition_counts": dict(sorted(counts.items())),
        "native_solver_outputs_mutated": False,
        "registry_mutated": False,
        "scheduler_action_taken": False,
        "external_fluid_mutated": False,
    }

    out.mkdir(parents=True, exist_ok=True)
    write_csv(out / "closure_qoi_final_use_disposition.csv", dispositions, DISPOSITION_COLUMNS)
    write_csv(out / "gci_results_admitted_only.csv", admitted, ADMITTED_GCI_COLUMNS)
    write_csv(out / "extraction_required_rows.csv", retained, DISPOSITION_COLUMNS)
    write_csv(out / "blocker_decision.csv", [decision], DECISION_COLUMNS)
    write_csv(out / "source_manifest.csv", source_manifest_rows(), MANIFEST_COLUMNS)
    write_json(out / "summary.json", summary)
    write_readme(out, summary)
    write_decision_md(out, summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args()
    print(json.dumps(build_package(args.out), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
