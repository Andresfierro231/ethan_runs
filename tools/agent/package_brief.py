#!/usr/bin/env python3
"""Print bounded summaries of work-product packages, JSON, and CSV files."""
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.agent.common import REPO_ROOT  # noqa: E402


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def scalar_summary(data: Any) -> dict[str, object]:
    if not isinstance(data, dict):
        return {"type": type(data).__name__}
    out: dict[str, object] = {}
    for key, value in data.items():
        if isinstance(value, (str, int, float, bool)) or value is None:
            out[key] = value
        elif isinstance(value, list):
            out[key] = f"list[{len(value)}]"
        elif isinstance(value, dict):
            out[key] = f"dict[{len(value)}]"
        else:
            out[key] = type(value).__name__
    return out


def csv_brief(path: Path, *, rows: int = 2) -> dict[str, object]:
    with path.open(newline="", encoding="utf-8", errors="replace") as handle:
        reader = csv.DictReader(handle)
        sample: list[dict[str, str]] = []
        count = 0
        for row in reader:
            count += 1
            if len(sample) < rows:
                sample.append(dict(row))
    return {
        "path": rel(path),
        "columns": reader.fieldnames or [],
        "row_count": count,
        "sample_rows": sample,
    }


def json_brief(path: Path) -> dict[str, object]:
    with path.open(encoding="utf-8", errors="replace") as handle:
        data = json.load(handle)
    return {"path": rel(path), "summary": scalar_summary(data)}


def markdown_brief(path: Path, *, max_headings: int = 12) -> dict[str, object]:
    title = None
    headings: list[str] = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("# "):
            title = line[2:].strip()
        elif line.startswith("## ") and len(headings) < max_headings:
            headings.append(line[3:].strip())
    return {"path": rel(path), "title": title, "headings": headings}


def summarize_path(path: Path, *, rows: int = 2, csv_limit: int = 8) -> dict[str, object]:
    path = path.resolve()
    if path.is_file():
        if path.suffix == ".csv":
            return {"kind": "csv", "csv": csv_brief(path, rows=rows)}
        if path.suffix == ".json":
            return {"kind": "json", "json": json_brief(path)}
        if path.suffix == ".md":
            return {"kind": "markdown", "markdown": markdown_brief(path)}
        return {"kind": "file", "path": rel(path), "size_bytes": path.stat().st_size}

    files = [p for p in sorted(path.rglob("*")) if p.is_file()]
    suffix_counts = Counter(p.suffix or "(none)" for p in files)
    summary_json = path / "summary.json"
    readme = path / "README.md"
    csvs = [p for p in files if p.suffix == ".csv"][:csv_limit]
    data: dict[str, object] = {
        "kind": "package",
        "path": rel(path),
        "file_count": len(files),
        "suffix_counts": dict(sorted(suffix_counts.items())),
        "csv_files_considered": len(csvs),
        "csv_files_total": sum(1 for p in files if p.suffix == ".csv"),
        "csvs": [csv_brief(p, rows=rows) for p in csvs],
    }
    if summary_json.exists():
        data["summary_json"] = json_brief(summary_json)
    if readme.exists():
        data["readme"] = markdown_brief(readme)
    return data


def print_human(data: dict[str, object]) -> None:
    print(f"kind={data['kind']}")
    if data["kind"] == "package":
        print(f"path={data['path']} files={data['file_count']} suffixes={data['suffix_counts']}")
        if "summary_json" in data:
            print(f"summary_json={data['summary_json']['summary']}")
        if "readme" in data:
            readme = data["readme"]
            print(f"readme_title={readme['title']} headings={readme['headings']}")
        print(f"csvs_printed={data['csv_files_considered']} csvs_total={data['csv_files_total']}")
        for item in data["csvs"]:
            print(f"csv={item['path']} rows={item['row_count']} columns={item['columns']}")
            for sample in item["sample_rows"]:
                print(f"  sample={sample}")
        return
    item = data.get("csv") or data.get("json") or data.get("markdown") or data
    print(item)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path")
    parser.add_argument("--rows", type=int, default=2, help="Sample rows per CSV.")
    parser.add_argument("--csv-limit", type=int, default=8, help="Maximum CSV files to preview in a package.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    path = Path(args.path)
    if not path.exists():
        print(f"missing path: {path}", file=sys.stderr)
        return 1
    data = summarize_path(path, rows=max(args.rows, 0), csv_limit=max(args.csv_limit, 0))
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        print_human(data)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
