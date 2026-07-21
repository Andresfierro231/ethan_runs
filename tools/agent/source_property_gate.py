#!/usr/bin/env python3
"""Audit source/property labels on scorecard-like fit/admission rows."""
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.agent.common import REPO_ROOT, iter_files, rel, write_json_stdout  # noqa: E402

REQUIRED_LABELS = [
    "property_mode",
    "property_sensitivity_label",
    "source_validity_envelope_status",
    "source_use_category",
    "provenance_author_title",
]

LABEL_ALIASES = {
    "source_use_category": ("source_use_category", "source_use_categories"),
    "provenance_author_title": ("provenance_author_title", "provenance", "source_paths"),
}

SCORECARD_NAME_TOKENS = (
    "scorecard",
    "admission",
    "fit",
    "candidate",
    "gate",
    "decision",
    "readiness",
    "contract",
)

STATUS_COLUMNS = (
    "fit_allowed",
    "final_fit_allowed",
    "split_fit_allowed",
    "model_selection_allowed",
    "final_model_selection_allowed",
    "admission_status",
    "admission_decision",
    "candidate_admission_status",
    "fit_status",
    "fit_use_status",
    "source_property_gate_status",
)

ALLOW_VALUES = {"yes", "true", "fit_target", "fit", "fit_admitted", "admitted", "pass", "accepted"}
BLOCK_TOKENS = (
    "no",
    "not_",
    "non_",
    "blocked",
    "fail",
    "failed",
    "missing",
    "diagnostic",
    "excluded",
    "future",
    "pending",
    "candidate_only",
    "no_admission",
)

REFRESH_TOKENS = ("refresh_required", "source_property_refresh_required")
ENVELOPE_BLOCK_TOKENS = (
    "outside",
    "mixed_or_outside",
    "source_envelope_unknown",
    "source_envelope_missing",
    "unknown",
)
SOURCE_USE_BLOCK_TOKENS = (
    "blocked",
    "diagnostic",
    "reference",
    "no_fit",
    "no-selection",
    "no_selection",
    "future",
    "pending",
)


def normalized(value: str) -> str:
    return str(value or "").strip().lower()


def has_scorecard_name(path: Path) -> bool:
    text = f"{path.name} {path.parent.name}".lower()
    return any(token in text for token in SCORECARD_NAME_TOKENS)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8", errors="replace") as handle:
        return list(csv.DictReader(handle))


def is_positive_status(value: str) -> bool:
    value = normalized(value)
    if not value:
        return False
    if any(token in value for token in BLOCK_TOKENS):
        return False
    return value in ALLOW_VALUES or value.startswith("admit") or value.startswith("pass") or "fit_target" in value


def row_is_fit_or_admission_candidate(row: dict[str, str]) -> tuple[bool, str]:
    triggers: list[str] = []
    for col in STATUS_COLUMNS:
        if col in row and is_positive_status(row.get(col, "")):
            triggers.append(f"{col}={row.get(col, '')}")
    return bool(triggers), ";".join(triggers)


def label_columns(field: str) -> tuple[str, ...]:
    return LABEL_ALIASES.get(field, (field,))


def existing_label(row: dict[str, str], field: str) -> str:
    for col in label_columns(field):
        if row.get(col, ""):
            return row.get(col, "")
    return ""


def has_label_column(headers: set[str], field: str) -> bool:
    return any(col in headers for col in label_columns(field))


def csv_is_scorecard_like(path: Path, rows: list[dict[str, str]]) -> bool:
    headers = set(rows[0].keys()) if rows else set()
    return has_scorecard_name(path) or bool(headers.intersection(STATUS_COLUMNS))


def iter_scorecard_csvs(paths: Iterable[Path]) -> list[Path]:
    out: list[Path] = []
    for input_path in paths:
        path = input_path if input_path.is_absolute() else REPO_ROOT / input_path
        if path.is_file() and path.suffix == ".csv":
            try:
                rows = read_csv(path)
            except Exception:
                continue
            if csv_is_scorecard_like(path, rows):
                out.append(path)
            continue
        if path.is_dir():
            for file_path in iter_files([path], suffixes=(".csv",)):
                try:
                    rows = read_csv(file_path)
                except Exception:
                    continue
                if csv_is_scorecard_like(file_path, rows):
                    out.append(file_path)
    return sorted(set(out), key=rel)


def classify_candidate(row: dict[str, str], headers: set[str]) -> list[str]:
    modes: list[str] = []
    for field in REQUIRED_LABELS:
        if not has_label_column(headers, field):
            modes.append("missing_required_label_column")
        elif not existing_label(row, field).strip():
            modes.append("blank_required_label")

    gate_status = normalized(row.get("source_property_gate_status", ""))
    if "source_property_gate_status" not in headers or not gate_status:
        modes.append("source_property_gate_status_missing")
    elif not gate_status.startswith("pass_"):
        modes.append("source_property_gate_blocked")

    label_text = " ".join(normalized(existing_label(row, field)) for field in REQUIRED_LABELS)
    if any(token in label_text for token in REFRESH_TOKENS):
        modes.append("refresh_required_label_content")

    envelope = normalized(existing_label(row, "source_validity_envelope_status"))
    if any(token in envelope for token in ENVELOPE_BLOCK_TOKENS):
        modes.append("outside_or_mixed_source_envelope")

    source_use = normalized(existing_label(row, "source_use_category"))
    if any(token in source_use for token in SOURCE_USE_BLOCK_TOKENS):
        modes.append("diagnostic_or_no_fit_source_use")

    unique_modes = list(dict.fromkeys(modes))
    if unique_modes:
        unique_modes.append("candidate_allowed_but_source_property_blocked")
    return unique_modes


def audit_paths(paths: Iterable[Path | str]) -> dict[str, Any]:
    input_paths = [Path(p) for p in paths]
    csv_paths = iter_scorecard_csvs(input_paths)
    findings: list[dict[str, str]] = []
    candidate_rows = 0
    scanned_rows = 0
    artifact_candidate_counts: Counter[str] = Counter()
    artifact_finding_counts: Counter[str] = Counter()
    failure_counts: Counter[str] = Counter()

    for path in csv_paths:
        rows = read_csv(path)
        headers = set(rows[0].keys()) if rows else set()
        scanned_rows += len(rows)
        for index, row in enumerate(rows, start=1):
            candidate, trigger = row_is_fit_or_admission_candidate(row)
            if not candidate:
                continue
            candidate_rows += 1
            artifact = rel(path)
            artifact_candidate_counts[artifact] += 1
            modes = classify_candidate(row, headers)
            if not modes:
                continue
            artifact_finding_counts[artifact] += 1
            for mode in modes:
                failure_counts[mode] += 1
            findings.append(
                {
                    "artifact": artifact,
                    "row_number": str(index),
                    "fit_or_admission_trigger": trigger,
                    "failure_modes": ";".join(modes),
                    "next_step": "refresh source/property labels or mark row diagnostic/no-fit before fit/admission prose",
                }
            )

    allowed_rows = candidate_rows - len(findings)
    return {
        "required_labels": REQUIRED_LABELS,
        "scorecard_artifacts_scanned": len(csv_paths),
        "scorecard_rows_scanned": scanned_rows,
        "fit_or_admission_candidate_rows": candidate_rows,
        "rows_with_source_property_findings": len(findings),
        "allowed_candidate_rows": allowed_rows,
        "failure_mode_counts": dict(sorted(failure_counts.items())),
        "top_artifacts_by_findings": [
            {"artifact": artifact, "findings": count, "candidate_rows": artifact_candidate_counts[artifact]}
            for artifact, count in artifact_finding_counts.most_common(20)
        ],
        "findings": findings,
    }


def write_todo(path: Path, findings: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["artifact", "row_number", "fit_or_admission_trigger", "failure_modes", "next_step"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(findings)


def print_text_report(result: dict[str, Any], *, warning: bool) -> None:
    title = "SOURCE_PROPERTY_GATE_WARNING" if warning else "source_property_gate"
    print(f"{title}: candidate_rows={result['fit_or_admission_candidate_rows']} findings={result['rows_with_source_property_findings']}")
    print(f"required_labels={','.join(result['required_labels'])}")
    if result["failure_mode_counts"]:
        print("failure_modes:")
        for mode, count in result["failure_mode_counts"].items():
            print(f"  - {mode}: {count}")
    if result["top_artifacts_by_findings"]:
        print("top_artifacts:")
        for item in result["top_artifacts_by_findings"][:10]:
            print(f"  - {item['artifact']}: {item['findings']} findings / {item['candidate_rows']} candidates")
    if warning and result["rows_with_source_property_findings"]:
        print("TODO: run with --todo-out <task-owned.csv> and address each failure mode before fit/admission prose.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", help="Package, directory, or CSV path to audit.")
    parser.add_argument("--strict", action="store_true", help="Exit nonzero when source/property findings exist.")
    parser.add_argument("--warn", action="store_true", help="Print a loud warning but exit zero for findings.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    parser.add_argument("--todo-out", type=Path, help="Write row-level TODO CSV for source/property findings.")
    args = parser.parse_args()

    result = audit_paths(args.paths)
    if args.todo_out:
        write_todo(args.todo_out if args.todo_out.is_absolute() else REPO_ROOT / args.todo_out, result["findings"])

    if args.json:
        write_json_stdout(result)
    else:
        print_text_report(result, warning=args.warn or bool(result["rows_with_source_property_findings"]))

    if args.strict and result["rows_with_source_property_findings"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
