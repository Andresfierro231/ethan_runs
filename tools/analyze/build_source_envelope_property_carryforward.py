#!/usr/bin/env python3
"""Build AGENT-538 source-envelope/property-mode carryforward package.

This is an existing-evidence contract package. It makes source-validity
envelope and property-mode sensitivity labels explicit for future closure
scorecards without fitting, scoring, launching solvers, or changing admission.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


TASK = "AGENT-538"
DATE = "2026-07-18"
ROOT = Path(__file__).resolve().parents[2]
OUT_REL = Path("work_products/2026-07/2026-07-18/2026-07-18_source_envelope_property_carryforward")
OUT = ROOT / OUT_REL

SOURCE_ENVELOPE_DIR = ROOT / "work_products/2026-07/2026-07-13/2026-07-13_litrev_source_envelope"
PROPERTY_DIR = ROOT / "work_products/2026-07/2026-07-13/2026-07-13_litrev_property_sensitivity"
AGENT521_DIR = ROOT / "work_products/2026-07/2026-07-17/2026-07-17_litrev_gate_carryforward_ledger"
FINAL_SHELL_DIR = ROOT / "work_products/2026-07/2026-07-17/2026-07-17_final_predictive_scorecard_shell"

SOURCES = {
    "source_overlap_flags": SOURCE_ENVELOPE_DIR / "source_overlap_flags.csv",
    "branch_source_envelope": SOURCE_ENVELOPE_DIR / "branch_source_envelope.csv",
    "property_mode_matrix": PROPERTY_DIR / "property_mode_matrix.csv",
    "property_sensitivity_summary": PROPERTY_DIR / "property_sensitivity_summary.csv",
    "agent521_contract": AGENT521_DIR / "target_package_gate_contract.csv",
    "agent521_branch_summary": AGENT521_DIR / "branch_gate_carryforward_summary.csv",
    "agent521_source_crosswalk": AGENT521_DIR / "source_gate_crosswalk.csv",
    "final_shell_case_partition": FINAL_SHELL_DIR / "case_partition_contract.csv",
    "final_shell_prediction_join": FINAL_SHELL_DIR / "prediction_join_shell.csv",
    "blocker_register": ROOT / ".agent/blockers.yml",
}

LABEL_COLUMNS = [
    "case_id",
    "section_or_segment",
    "property_mode",
    "property_mode_status",
    "property_sensitivity_label",
    "mean_Re_ratio_to_replication",
    "mean_Pr_ratio_to_replication",
    "mean_Gz_ratio_to_replication",
    "source_validity_envelope_status",
    "source_overlap_counts",
    "source_use_categories",
    "source_bounded_promotion_status",
    "provenance_author_title",
    "fit_use_status",
    "carryforward_blocker_status",
    "source_paths",
]

CONTRACT_COLUMNS = [
    "target_package",
    "consumer_lane",
    "required_label_columns",
    "source_contract_status",
    "property_contract_status",
    "default_status_until_labels_present",
    "acceptance_rule",
    "forbidden_shortcut",
    "source_paths",
]

AUDIT_COLUMNS = [
    "artifact",
    "artifact_type",
    "has_property_mode",
    "has_source_overlap_status",
    "has_property_sensitivity_label",
    "has_source_validity_envelope_status",
    "adoption_status",
    "next_step",
]

COVERAGE_COLUMNS = [
    "case_key",
    "normalized_case_id",
    "final_scorecard_partition",
    "fit_allowed",
    "model_selection_allowed",
    "source_property_label_coverage",
    "coverage_reason",
    "next_step",
    "source_paths",
]

NEXT_STEP_COLUMNS = [
    "item_id",
    "category",
    "priority",
    "blocker_or_path",
    "current_status",
    "required_next_step",
    "acceptance_signal",
    "guardrail",
    "source_paths",
]

MANIFEST_COLUMNS = ["source_id", "path", "exists", "role"]

REQUIRED_LABEL_FIELDS = [
    "case_id",
    "section_or_segment",
    "property_mode",
    "property_mode_status",
    "property_sensitivity_label",
    "source_validity_envelope_status",
    "source_overlap_status",
    "source_use_category",
    "provenance_author_title",
    "fit_use_status",
]


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


def csv_header(path: Path) -> set[str]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        return set(next(reader, []))


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
        raise FileNotFoundError("Missing AGENT-538 source files: " + "; ".join(missing))


def counter_summary(values: Iterable[str]) -> str:
    counts = Counter(value or "blank" for value in values)
    return ";".join(f"{key}={counts[key]}" for key in sorted(counts))


def normalize_case_key(case_key: str) -> str:
    if case_key.startswith("salt1"):
        return "salt_1"
    if case_key.startswith("salt2"):
        return "salt_2"
    if case_key.startswith("salt3"):
        return "salt_3"
    if case_key.startswith("salt4"):
        return "salt_4"
    return case_key


def parse_open_blockers(path: Path) -> list[dict[str, str]]:
    blockers: list[dict[str, str]] = []
    current: dict[str, str] | None = None
    in_blockers = False
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()
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
        if key in {"title", "status", "severity", "evidence", "last_reviewed"}:
            current[key] = value.strip().strip('"')
    if current:
        blockers.append(current)
    return [row for row in blockers if row.get("status") == "open"]


def source_envelope_status(status_counts: Counter[str]) -> str:
    if not status_counts:
        return "source_envelope_missing"
    if status_counts.get("outside", 0) or status_counts.get("unknown", 0):
        return "mixed_or_outside_envelope_label_required"
    if status_counts.get("inside", 0):
        return "inside_method_envelope_not_admission"
    return "source_envelope_unknown"


def property_mode_status(property_mode: str, summary_row: dict[str, str] | None) -> str:
    if summary_row is None:
        return "property_mode_summary_missing"
    if property_mode in {"replication_reis_jadyn", "sohal_janz_full"}:
        return "reference_or_replication_mode_reported"
    return "sensitivity_mode_no_fit_until_lane_declared"


def property_sensitivity_label(property_mode: str, summary_row: dict[str, str] | None) -> str:
    if summary_row is None:
        return "missing_property_sensitivity_summary"
    if summary_row.get("admission_summary") == "reported_reference_mode":
        return "reported_reference_mode"
    return "property_sensitivity_material_closure_fit_blocked"


def build_label_rows() -> list[dict[str, Any]]:
    branch_rows = read_csv(SOURCES["branch_source_envelope"])
    overlap_rows = read_csv(SOURCES["source_overlap_flags"])
    property_summaries = {
        (row["case_id"], row["property_mode"]): row
        for row in read_csv(SOURCES["property_sensitivity_summary"])
    }

    overlap_by_key: dict[tuple[str, str, str], list[dict[str, str]]] = defaultdict(list)
    for row in overlap_rows:
        overlap_by_key[(row["case_id"], row["span"], row["property_mode"])].append(row)

    rows: list[dict[str, Any]] = []
    for branch in branch_rows:
        key = (branch["case_id"], branch["span"], branch["property_mode"])
        overlaps = overlap_by_key.get(key, [])
        status_counts = Counter(row.get("overlap_status", "") for row in overlaps)
        use_categories = sorted({row.get("source_use_category", "") for row in overlaps if row.get("source_use_category")})
        provenance = sorted({row.get("provenance_author_title", "") for row in overlaps if row.get("provenance_author_title")})
        promotable = [
            row
            for row in overlaps
            if row.get("admission_recommendation") not in {"", "do_not_promote", "reference_only"}
        ]
        summary = property_summaries.get((branch["case_id"], branch["property_mode"]))
        rows.append(
            {
                "case_id": branch["case_id"],
                "section_or_segment": branch["span"],
                "property_mode": branch["property_mode"],
                "property_mode_status": property_mode_status(branch["property_mode"], summary),
                "property_sensitivity_label": property_sensitivity_label(branch["property_mode"], summary),
                "mean_Re_ratio_to_replication": "" if summary is None else summary.get("mean_Re_ratio_to_replication", ""),
                "mean_Pr_ratio_to_replication": "" if summary is None else summary.get("mean_Pr_ratio_to_replication", ""),
                "mean_Gz_ratio_to_replication": "" if summary is None else summary.get("mean_Gz_ratio_to_replication", ""),
                "source_validity_envelope_status": source_envelope_status(status_counts),
                "source_overlap_counts": counter_summary(row.get("overlap_status", "") for row in overlaps) or "no_overlap_rows",
                "source_use_categories": ";".join(use_categories) or "none",
                "source_bounded_promotion_status": (
                    f"candidate_or_gate_rows={len(promotable)}" if promotable else "no_active_source_promotion"
                ),
                "provenance_author_title": " | ".join(provenance),
                "fit_use_status": branch.get("fit_use_status", ""),
                "carryforward_blocker_status": (
                    "label_only_not_admission"
                    if branch.get("fit_use_status") == "fit_target"
                    else "diagnostic_or_blocked_label_required"
                ),
                "source_paths": f"{rel(SOURCES['branch_source_envelope'])};{rel(SOURCES['source_overlap_flags'])};{rel(SOURCES['property_sensitivity_summary'])}",
            }
        )
    return sorted(rows, key=lambda row: (row["case_id"], row["section_or_segment"], row["property_mode"]))


def build_contract_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for contract in read_csv(SOURCES["agent521_contract"]):
        required = set(contract["required_gate_columns"].split(";"))
        rows.append(
            {
                "target_package": contract["target_package"],
                "consumer_lane": contract["consumer_lane"],
                "required_label_columns": ";".join(REQUIRED_LABEL_FIELDS),
                "source_contract_status": (
                    "present_in_agent521_contract" if "source_overlap_status" in required else "missing_source_overlap_status"
                ),
                "property_contract_status": (
                    "present_in_agent521_contract" if "property_mode" in required else "missing_property_mode"
                ),
                "default_status_until_labels_present": "blocked_or_diagnostic_until_source_property_labels_present",
                "acceptance_rule": (
                    "A future closure scorecard can report fit/admission only after each row carries a declared property mode, "
                    "source-envelope status, source-use category, and author/title provenance."
                ),
                "forbidden_shortcut": "closure_fit_or_claim_without_source_envelope_and_property_mode_labels",
                "source_paths": contract["source_paths"],
            }
        )
    return rows


def build_scorecard_adoption_audit() -> list[dict[str, Any]]:
    artifacts = [
        ("agent521_target_package_gate_contract", SOURCES["agent521_contract"], "contract_csv"),
        ("final_predictive_prediction_join_shell", SOURCES["final_shell_prediction_join"], "scorecard_shell_csv"),
    ]
    rows: list[dict[str, Any]] = []
    for name, path, artifact_type in artifacts:
        headers = csv_header(path)
        checks = {
            "property_mode": "property_mode" in headers or path == SOURCES["agent521_contract"],
            "source_overlap_status": "source_overlap_status" in headers or path == SOURCES["agent521_contract"],
            "property_sensitivity_label": "property_sensitivity_label" in headers,
            "source_validity_envelope_status": "source_validity_envelope_status" in headers,
        }
        if name == "agent521_target_package_gate_contract":
            checks["property_sensitivity_label"] = True
            checks["source_validity_envelope_status"] = True
            adoption = "ready_contract_requires_labels"
            next_step = "Consume AGENT-538 label contract in future scorecard builders."
        elif all(checks.values()):
            adoption = "ready"
            next_step = "Preserve labels through score aggregation."
        else:
            adoption = "missing_labels"
            next_step = "Add AGENT-538 label fields before reporting final frozen closure scores."
        rows.append(
            {
                "artifact": rel(path),
                "artifact_type": artifact_type,
                "has_property_mode": "yes" if checks["property_mode"] else "no",
                "has_source_overlap_status": "yes" if checks["source_overlap_status"] else "no",
                "has_property_sensitivity_label": "yes" if checks["property_sensitivity_label"] else "no",
                "has_source_validity_envelope_status": "yes" if checks["source_validity_envelope_status"] else "no",
                "adoption_status": adoption,
                "next_step": next_step,
            }
        )
    return rows


def build_coverage_rows() -> list[dict[str, Any]]:
    covered_cases = {row["case_id"] for row in read_csv(SOURCES["property_sensitivity_summary"])}
    row_specific_nominal_cases = {"salt2_jin_nominal", "salt3_jin_nominal", "salt4_nominal"}
    rows = []
    for row in read_csv(SOURCES["final_shell_case_partition"]):
        normalized = normalize_case_key(row["case_key"])
        if row["case_key"] in row_specific_nominal_cases and normalized in covered_cases:
            coverage = "source_property_labels_available"
            reason = "July 13 source-envelope and property-sensitivity rows cover this nominal Salt case."
            next_step = "Join AGENT-538 labels by case, section, and property mode in future scorecard."
        else:
            coverage = "source_or_property_gate_missing"
            reason = "Current July 13 source/property tables do not provide row-specific branch/property coverage for this scorecard row."
            next_step = "Refresh source-envelope/property-sensitivity labels before fitting or scoring this row."
        rows.append(
            {
                "case_key": row["case_key"],
                "normalized_case_id": normalized,
                "final_scorecard_partition": row["final_scorecard_partition"],
                "fit_allowed": row["fit_allowed"],
                "model_selection_allowed": row["model_selection_allowed"],
                "source_property_label_coverage": coverage,
                "coverage_reason": reason,
                "next_step": next_step,
                "source_paths": f"{rel(SOURCES['final_shell_case_partition'])};{rel(SOURCES['property_sensitivity_summary'])}",
            }
        )
    return rows


def build_next_steps() -> list[dict[str, Any]]:
    open_blockers = parse_open_blockers(SOURCES["blocker_register"])
    rows: list[dict[str, Any]] = []
    for index, blocker in enumerate(open_blockers, start=1):
        rows.append(
            {
                "item_id": f"B{index}",
                "category": "blocker_label",
                "priority": blocker.get("severity", ""),
                "blocker_or_path": blocker["id"],
                "current_status": "open",
                "required_next_step": "Carry this blocker as a row-level label when the affected closure family is scored.",
                "acceptance_signal": "Future scorecard includes blocker_status and does not promote affected rows while blocker remains open.",
                "guardrail": "Do not reopen resolved blockers or treat this label as scientific admission.",
                "source_paths": blocker.get("evidence", ""),
            }
        )
    research_paths = [
        (
            "P1",
            "scorecard_label_enforcement",
            "high",
            "Add source/property labels to future F6, HTC, wall/test-section, and final predictive scorecards before reporting fit/admission.",
            "A future scorecard has no blank property/source label fields on fit/admission rows.",
        ),
        (
            "P2",
            "salt1_source_property_refresh",
            "high",
            "Extend source-envelope and property-sensitivity coverage to Salt1 nominal before final Salt1-4 training claims.",
            "Salt1 rows classify as covered instead of source_or_property_gate_missing.",
        ),
        (
            "P3",
            "source_bounded_correlation_guard",
            "medium",
            "Only use source-bounded correlations where envelope status and author/title provenance are present.",
            "Every source-bounded candidate states inside/outside/unknown status and source_use_category.",
        ),
        (
            "P4",
            "property_mode_sensitivity_axis",
            "medium",
            "Keep replication and updated-property modes separate in fit, score, and uncertainty tables.",
            "Scorecard reports property mode and sensitivity label before residual interpretation.",
        ),
        (
            "P5",
            "thesis_claim_carryforward",
            "medium",
            "Use this package as the thesis/report citation target for source-envelope and property-lane caveats.",
            "Claim prose cites AGENT-538 labels instead of generic source/property warnings.",
        ),
    ]
    for item_id, path_id, priority, next_step, acceptance in research_paths:
        rows.append(
            {
                "item_id": item_id,
                "category": "research_path",
                "priority": priority,
                "blocker_or_path": path_id,
                "current_status": "startable_existing_evidence",
                "required_next_step": next_step,
                "acceptance_signal": acceptance,
                "guardrail": "No solver/postprocessing launch, fitting, tuning, or admission change is implied by this carryforward package.",
                "source_paths": f"{rel(SOURCES['agent521_contract'])};{rel(SOURCES['source_overlap_flags'])};{rel(SOURCES['property_sensitivity_summary'])}",
            }
        )
    return rows


def build_source_manifest() -> list[dict[str, Any]]:
    return [
        {"source_id": key, "path": rel(path), "exists": path.exists(), "role": "read-only source"}
        for key, path in SOURCES.items()
    ]


def write_readme(path: Path, summary: dict[str, Any]) -> None:
    path.write_text(
        f"""---
provenance:
  - {rel(SOURCES['source_overlap_flags'])}
  - {rel(SOURCES['property_mode_matrix'])}
  - {rel(SOURCES['property_sensitivity_summary'])}
  - {rel(SOURCES['agent521_contract'])}
  - {rel(SOURCES['final_shell_case_partition'])}
tags: [litrev-gates, source-envelope, property-sensitivity, carryforward-ledger, closure-scorecard]
related:
  - .agent/status/2026-07-18_AGENT-538.md
  - .agent/journal/2026-07-18/source-envelope-property-carryforward.md
  - imports/2026-07-18_source_envelope_property_carryforward.json
task: {TASK}
date: {DATE}
role: Literature-synthesis/Tester/Writer
type: work_product
status: complete
---
# Source Envelope / Property Carryforward

Generated: `{summary['generated_at_utc']}`

## Decision

Future closure scorecards must carry source-validity envelope and property-mode
sensitivity labels before reporting fit, admission, or thesis claims. This
package is label enforcement from existing evidence; it does not promote a
closure.

## Outputs

- `source_property_label_contract.csv`
- `future_scorecard_label_contract.csv`
- `scorecard_adoption_audit.csv`
- `final_scorecard_case_coverage_audit.csv`
- `blockers_research_paths_next_steps.csv`
- `source_manifest.csv`
- `summary.json`

## Counts

- Source/property label rows: `{summary['source_property_label_rows']}`.
- Future scorecard contract rows: `{summary['future_scorecard_contract_rows']}`.
- Scorecard adoption audit rows: `{summary['scorecard_adoption_audit_rows']}`.
- Final scorecard coverage rows: `{summary['final_scorecard_coverage_rows']}`.
- Missing source/property coverage rows: `{summary['missing_source_property_coverage_rows']}`.
- Open blocker labels carried: `{summary['open_blocker_labels']}`.

## Use Rules

- `property_mode` and source-envelope status travel with every fit/score row.
- Missing Salt1 or future-row source/property coverage is a blocker label, not
  permission to infer overlap.
- Resolved blockers stay resolved; current open blockers are carried only as
  labels.
- No native CFD outputs, registry/admission state, scheduler state, Fluid source,
  generated index files, fitting, tuning, model selection, or scientific
  admission state were changed.
""",
        encoding="utf-8",
    )


def build_package(out: Path = OUT) -> dict[str, Any]:
    require_sources()
    out.mkdir(parents=True, exist_ok=True)

    label_rows = build_label_rows()
    contract_rows = build_contract_rows()
    adoption_rows = build_scorecard_adoption_audit()
    coverage_rows = build_coverage_rows()
    next_step_rows = build_next_steps()
    manifest_rows = build_source_manifest()
    label_status_counts = Counter(row["source_validity_envelope_status"] for row in label_rows)
    coverage_counts = Counter(row["source_property_label_coverage"] for row in coverage_rows)
    adoption_counts = Counter(row["adoption_status"] for row in adoption_rows)

    summary = {
        "task": TASK,
        "date": DATE,
        "generated_at_utc": utc_now(),
        "output_dir": rel(out),
        "source_property_label_rows": len(label_rows),
        "future_scorecard_contract_rows": len(contract_rows),
        "scorecard_adoption_audit_rows": len(adoption_rows),
        "final_scorecard_coverage_rows": len(coverage_rows),
        "missing_source_property_coverage_rows": coverage_counts.get("source_or_property_gate_missing", 0),
        "open_blocker_labels": sum(1 for row in next_step_rows if row["category"] == "blocker_label"),
        "research_path_rows": sum(1 for row in next_step_rows if row["category"] == "research_path"),
        "source_validity_envelope_counts": dict(sorted(label_status_counts.items())),
        "coverage_counts": dict(sorted(coverage_counts.items())),
        "adoption_counts": dict(sorted(adoption_counts.items())),
        "scientific_admission_change": "none",
        "native_output_mutation": "none",
        "registry_mutation": "none",
        "scheduler_action": "none",
        "solver_or_postprocessing_launch": "none",
        "external_fluid_edit": "none",
        "generated_index_refresh": "not_run_active_agent_owns_generated_index_paths",
    }

    write_csv(out / "source_property_label_contract.csv", label_rows, LABEL_COLUMNS)
    write_csv(out / "future_scorecard_label_contract.csv", contract_rows, CONTRACT_COLUMNS)
    write_csv(out / "scorecard_adoption_audit.csv", adoption_rows, AUDIT_COLUMNS)
    write_csv(out / "final_scorecard_case_coverage_audit.csv", coverage_rows, COVERAGE_COLUMNS)
    write_csv(out / "blockers_research_paths_next_steps.csv", next_step_rows, NEXT_STEP_COLUMNS)
    write_csv(out / "source_manifest.csv", manifest_rows, MANIFEST_COLUMNS)
    write_readme(out / "README.md", summary)
    write_json(out / "summary.json", summary)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args()
    summary = build_package(args.out)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
