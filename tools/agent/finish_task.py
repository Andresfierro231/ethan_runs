#!/usr/bin/env python3
"""Validate that an agent task has a complete handoff surface."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.agent.common import REPO_ROOT, find_task, parse_board, rel, run_check, write_json_stdout  # noqa: E402
from tools.agent.source_property_gate import audit_paths  # noqa: E402

REQUIRED_STATUS_PHRASES = [
    "## Changes Made",
    "## Validation",
    "## Guardrails",
]

REQUIRED_MANIFEST_KEYS = [
    "changed_files",
    "read_only_context",
    "native_solver_outputs_mutated",
    "registry_mutated",
    "scheduler_action",
    "external_fluid_edit",
]


def _doc_declares_task(path: Path, task_id: str) -> bool:
    text = path.read_text(encoding="utf-8", errors="ignore")
    patterns = [
        rf"(?m)^task:\s*{re.escape(task_id)}\s*$",
        rf"(?m)^Task:\s*`?{re.escape(task_id)}`?\s*$",
        rf"(?m)^Task\s+{re.escape(task_id)}\b",
    ]
    return any(re.search(pattern, text) for pattern in patterns)


def _find_artifacts(task_id: str) -> dict[str, list[Path]]:
    status = sorted((REPO_ROOT / ".agent" / "status").glob(f"*{task_id}.md"))
    journals = [p for p in (REPO_ROOT / ".agent" / "journal").glob("*/*.md") if _doc_declares_task(p, task_id)]
    imports = []
    for p in (REPO_ROOT / "imports").glob("*.json"):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        if data.get("task") == task_id:
            imports.append(p)
    return {"status": status, "journal": sorted(journals), "imports": sorted(imports)}


def _validate_manifest(path: Path) -> list[str]:
    errors: list[str] = []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return [f"{path}: invalid JSON: {exc}"]
    for key in REQUIRED_MANIFEST_KEYS:
        if key not in data:
            errors.append(f"{path}: missing required manifest key: {key}")
    changed = data.get("changed_files", [])
    if not isinstance(changed, list):
        errors.append(f"{path}: changed_files must be a list")
        return errors
    if not changed:
        errors.append(f"{path}: changed_files must not be empty")
    for rel in changed:
        if not (REPO_ROOT / str(rel)).exists():
            errors.append(f"{path}: changed file does not exist: {rel}")
    readonly = data.get("read_only_context", [])
    if not isinstance(readonly, list):
        errors.append(f"{path}: read_only_context must be a list")
    return errors


def _load_manifest(path: Path) -> dict[str, object] | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return data if isinstance(data, dict) else None


def _source_property_gate_warnings(path: Path) -> list[str]:
    data = _load_manifest(path)
    if data is None:
        return []
    if data.get("no_scorecard_outputs") is True:
        return []
    changed = data.get("changed_files", [])
    if not isinstance(changed, list):
        return []
    candidate_paths = [
        REPO_ROOT / str(item)
        for item in changed
        if isinstance(item, str) and (REPO_ROOT / item).exists() and (REPO_ROOT / item).suffix == ".csv"
    ]
    if not candidate_paths:
        return []
    result = audit_paths(candidate_paths)
    if not result["fit_or_admission_candidate_rows"] or not result["rows_with_source_property_findings"]:
        return []
    failure_modes = ", ".join(f"{mode}={count}" for mode, count in result["failure_mode_counts"].items())
    top = ", ".join(item["artifact"] for item in result["top_artifacts_by_findings"][:3])
    todo_hint = (
        "python3.11 tools/agent/source_property_gate.py "
        + " ".join(rel(path) for path in candidate_paths)
        + " --warn --todo-out <task-owned-source-property-todo.csv>"
    )
    return [
        "SOURCE_PROPERTY_GATE_WARNING: "
        f"{rel(path)} changed {result['fit_or_admission_candidate_rows']} fit/admission candidate rows "
        f"with {result['rows_with_source_property_findings']} source/property findings. "
        f"failure_modes: {failure_modes or 'none'}; top_artifacts: {top or 'none'}. "
        f"TODO: {todo_hint}"
    ]


def _validate_status_doc(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    errors = []
    for phrase in REQUIRED_STATUS_PHRASES:
        if phrase not in text:
            errors.append(f"{path}: missing required status section {phrase!r}")
    return errors


def _validate_journal_doc(path: Path, task_id: str) -> list[str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    errors = []
    if task_id not in text:
        errors.append(f"{path}: journal must include task id {task_id}")
    if len(text.strip().splitlines()) < 8:
        errors.append(f"{path}: journal is too short to be a durable handoff")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-id", required=True)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--rebuild-index", action="store_true", help="Run tools/docs/build_repo_index.py before --check.")
    args = parser.parse_args()

    errors: list[str] = []
    rows = parse_board(include_archive=True)
    row = find_task(args.task_id, rows)
    if row is None:
        errors.append(f"task {args.task_id} not found on board")
    elif row.status not in {"complete", "blocked"}:
        errors.append(f"task {args.task_id} board status is {row.status}, expected complete or blocked")

    artifacts = _find_artifacts(args.task_id)
    for key in ("status", "journal", "imports"):
        if not artifacts[key]:
            errors.append(f"missing {key} artifact for {args.task_id}")
    for status_doc in artifacts["status"]:
        errors.extend(_validate_status_doc(status_doc))
    for journal_doc in artifacts["journal"]:
        errors.extend(_validate_journal_doc(journal_doc, args.task_id))
    for manifest in artifacts["imports"]:
        errors.extend(_validate_manifest(manifest))
    warnings: list[str] = []
    for manifest in artifacts["imports"]:
        warnings.extend(_source_property_gate_warnings(manifest))

    if args.rebuild_index:
        code, out = run_check([sys.executable, "tools/docs/build_repo_index.py"])
        if code:
            errors.append(f"index rebuild failed:\n{out}")
    code, out = run_check([sys.executable, "tools/docs/build_repo_index.py", "--check"])
    if code:
        errors.append(f"index check failed:\n{out}")

    result = {
        "task_id": args.task_id,
        "artifacts": {k: [str(p.relative_to(REPO_ROOT)) for p in v] for k, v in artifacts.items()},
        "errors": errors,
        "warnings": warnings,
        "ok": not errors,
    }
    if args.json:
        write_json_stdout(result)
    else:
        for key, values in result["artifacts"].items():
            print(f"{key}:")
            for value in values:
                print(f"  - {value}")
        if errors:
            print("Errors:")
            for err in errors:
                print(f"  - {err}")
        else:
            print("finish_task: OK")
        if warnings:
            print("Warnings:")
            for warning in warnings:
                print(f"  - {warning}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
