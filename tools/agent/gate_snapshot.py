#!/usr/bin/env python3
"""Print compact pass/blocker/action snapshots for work-product packages."""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.agent.common import REPO_ROOT  # noqa: E402


PASS_TOKENS = (
    "pass",
    "ready",
    "accepted",
    "complete",
    "available",
    "exists",
    "supported",
    "recovered",
    "eligible",
)
BLOCK_TOKENS = (
    "block",
    "fail",
    "missing",
    "closed",
    "zero",
    "not_ready",
    "incomplete",
    "unresolved",
    "unavailable",
)
GUARDRAIL_TOKENS = (
    "no_",
    "forbidden",
    "protected",
    "leak",
    "admission",
    "freeze",
    "final_score",
    "validation",
    "holdout",
    "source_property",
    "qwall",
    "wallheatflux",
    "runtime",
)
ACTION_FILENAMES = (
    "next_action",
    "next_unblock",
    "queue",
    "gate",
    "decision",
    "readiness",
    "todo",
)
ACTION_COLUMNS = (
    "priority",
    "gate",
    "status",
    "pass_now",
    "ready_now",
    "action",
    "next_action",
    "done_when",
    "acceptance",
    "blocker",
    "reason",
    "source",
)


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def _scalar_items(data: Any, prefix: str = "") -> list[tuple[str, object]]:
    if isinstance(data, dict):
        out: list[tuple[str, object]] = []
        for key, value in data.items():
            name = f"{prefix}.{key}" if prefix else str(key)
            if isinstance(value, dict):
                out.extend(_scalar_items(value, name))
            elif isinstance(value, list):
                out.append((name, f"list[{len(value)}]"))
            elif isinstance(value, (str, int, float, bool)) or value is None:
                out.append((name, value))
        return out
    return []


def _interesting(key: str, tokens: tuple[str, ...]) -> bool:
    lowered = key.lower()
    return any(token in lowered for token in tokens)


def _as_blocker_value(value: object) -> bool:
    if value is False or value is None:
        return True
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return value == 0
    if isinstance(value, str):
        lowered = value.lower()
        return any(token in lowered for token in BLOCK_TOKENS)
    return False


def _as_pass_value(value: object) -> bool:
    if value is True:
        return True
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return value > 0
    if isinstance(value, str):
        lowered = value.lower()
        return any(token in lowered for token in PASS_TOKENS) and not any(token in lowered for token in BLOCK_TOKENS)
    return False


def _signal_text(key: str, value: object) -> str:
    return f"{key}={value}"


def summarize_summary_json(summary_path: Path, *, limit: int) -> dict[str, object]:
    with summary_path.open(encoding="utf-8", errors="replace") as handle:
        data = json.load(handle)
    scalars = _scalar_items(data)
    lookup = dict(scalars)
    pass_signals: list[str] = []
    blocker_signals: list[str] = []
    guardrail_closed: list[str] = []
    for key, value in scalars:
        key_l = key.lower()
        if _interesting(key_l, GUARDRAIL_TOKENS) and _as_blocker_value(value):
            guardrail_closed.append(_signal_text(key, value))
        if _interesting(key_l, PASS_TOKENS) and _as_pass_value(value):
            pass_signals.append(_signal_text(key, value))
        if _interesting(key_l, BLOCK_TOKENS + GUARDRAIL_TOKENS) and _as_blocker_value(value):
            blocker_signals.append(_signal_text(key, value))
    return {
        "task_id": lookup.get("task_id") or lookup.get("task"),
        "decision": lookup.get("decision") or lookup.get("status"),
        "candidate_id": lookup.get("candidate_id") or lookup.get("model_id"),
        "pass_signals": pass_signals[:limit],
        "blocker_signals": blocker_signals[:limit],
        "guardrail_closed": guardrail_closed[:limit],
        "summary_scalar_count": len(scalars),
    }


def _csv_action_rows(path: Path, *, limit: int) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    with path.open(newline="", encoding="utf-8", errors="replace") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            return rows
        columns = [column for column in ACTION_COLUMNS if column in reader.fieldnames]
        if not columns:
            columns = reader.fieldnames[: min(5, len(reader.fieldnames))]
        for row in reader:
            compact = {column: row.get(column, "") for column in columns if row.get(column, "")}
            if compact:
                rows.append(compact)
            if len(rows) >= limit:
                break
    return rows


def summarize_actions(package: Path, *, limit: int) -> list[dict[str, object]]:
    csvs = sorted(path for path in package.rglob("*.csv") if path.is_file())
    selected = [
        path
        for path in csvs
        if any(token in path.name.lower() for token in ACTION_FILENAMES)
    ]
    if not selected:
        selected = csvs[:3]
    actions: list[dict[str, object]] = []
    remaining = limit
    for path in selected:
        if remaining <= 0:
            break
        rows = _csv_action_rows(path, limit=remaining)
        if rows:
            actions.append({"path": rel(path), "rows": rows})
            remaining -= len(rows)
    return actions


def summarize_package(path: Path, *, limit: int) -> dict[str, object]:
    package = path.resolve()
    if not package.exists():
        return {"path": str(path), "missing": True}
    summary_json = package / "summary.json"
    data: dict[str, object] = {
        "path": rel(package),
        "missing": False,
        "summary_json_found": summary_json.exists(),
        "actions": summarize_actions(package, limit=limit) if package.is_dir() else [],
    }
    if summary_json.exists():
        data.update(summarize_summary_json(summary_json, limit=limit))
    return data


def _format_action(row: dict[str, str]) -> str:
    preferred = [column for column in ACTION_COLUMNS if column in row]
    columns = preferred or list(row)
    return "; ".join(f"{column}={row[column]}" for column in columns if row.get(column))


def print_human(items: list[dict[str, object]]) -> None:
    for item in items:
        print(f"package={item['path']}")
        if item.get("missing"):
            print("  missing=true")
            continue
        print(f"  summary_json_found={item['summary_json_found']}")
        for key in ("task_id", "decision", "candidate_id"):
            if item.get(key) not in (None, ""):
                print(f"  {key}={item[key]}")
        for label, key in (
            ("pass", "pass_signals"),
            ("blocked", "blocker_signals"),
            ("closed_guardrails", "guardrail_closed"),
        ):
            values = item.get(key) or []
            if values:
                print(f"  {label}: " + " | ".join(str(value) for value in values))
        actions = item.get("actions") or []
        if actions:
            print("  actions:")
            for group in actions:
                assert isinstance(group, dict)
                print(f"    from={group['path']}")
                for row in group["rows"]:
                    assert isinstance(row, dict)
                    print(f"      - {_format_action(row)}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", help="Work-product package directories or files.")
    parser.add_argument("--limit", type=int, default=8, help="Maximum signals/action rows per package.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    limit = max(args.limit, 0)
    results = [summarize_package(Path(path), limit=limit) for path in args.paths]
    if args.json:
        print(json.dumps({"packages": results}, indent=2, sort_keys=True))
    else:
        print_human(results)
    return 1 if any(item.get("missing") for item in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
