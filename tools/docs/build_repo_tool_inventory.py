#!/usr/bin/env python3
"""Build a categorized inventory for scripts and helpers under tools/."""

from __future__ import annotations

import argparse
import ast
import csv
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TOOLS_DIR = ROOT / "tools"
DEFAULT_OUT_DIR = ROOT / "docs" / "repo_user_guide"


@dataclass(frozen=True)
class ToolRow:
    path: str
    category: str
    kind: str
    purpose: str
    typical_inputs: str
    typical_outputs: str
    safe_example: str
    when_to_use: str
    when_not_to_use: str
    safety: str


def _clean(value: str, max_len: int | None = None) -> str:
    text = " ".join(value.replace("|", "/").split())
    text = text.encode("ascii", errors="replace").decode("ascii")
    if max_len is not None and len(text) > max_len:
        return text[: max_len - 3].rstrip() + "..."
    return text


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _first_docstring(path: Path) -> str:
    if path.suffix != ".py":
        return ""
    try:
        tree = ast.parse(_read_text(path))
    except SyntaxError:
        return ""
    doc = ast.get_docstring(tree)
    if not doc:
        return ""
    return _clean(doc, 220)


def _leading_comment(path: Path) -> str:
    comments: list[str] = []
    for line in _read_text(path).splitlines()[:20]:
        stripped = line.strip()
        if stripped.startswith("#!") or not stripped:
            continue
        if stripped.startswith("#"):
            comments.append(stripped.lstrip("#").strip())
            continue
        break
    return _clean(" ".join(comments), 220)


def _title_from_name(path: Path) -> str:
    stem = path.stem
    prefixes = (
        "build_",
        "test_",
        "run_",
        "sample_",
        "extract_",
        "render_",
        "write_",
        "submit_",
        "check_",
        "derive_",
        "monitor_",
        "prepare_",
        "register_",
        "publish_",
        "download_",
        "upload_",
    )
    for prefix in prefixes:
        if stem.startswith(prefix):
            stem = stem[len(prefix) :]
            break
    return _clean(stem.replace("_", " "), 220)


def _category(path: Path) -> str:
    parts = path.relative_to(TOOLS_DIR).parts
    if len(parts) == 1:
        return "root workflow helper"
    top = parts[0]
    return {
        "agent": "agent coordination and linting",
        "analyze": "analysis and package builders",
        "docs": "documentation tooling",
        "extract": "CFD extraction and rendering",
        "intake": "case intake and registry",
        "ofenv": "OpenFOAM environment",
        "papers": "paper/thesis support",
        "publish": "publishing and transfer",
    }.get(top, top)


def _kind(path: Path) -> str:
    if path.suffix == ".py":
        return "python"
    if path.suffix == ".sh":
        return "shell"
    if path.suffix == ".md":
        return "markdown"
    return path.suffix.lstrip(".") or "file"


def _safety(path: Path) -> str:
    rel = path.as_posix()
    name = path.name.lower()
    text = rel.lower()
    if "test_" in name:
        return "local/lightweight test; usually read-only except temporary outputs"
    if any(token in text for token in ("submit_", "sbatch", "run_openfoam", "postprocess_case")):
        return "HPC/mutating capable; inspect first and do not run heavy work on login nodes"
    if any(token in text for token in ("publish", "upload", "download", "rsync")):
        return "transfer/publish capable; verify destination and provenance before use"
    if "register_case" in text or "build_import_manifest" in text:
        return "metadata/provenance mutating; use only under an assigned row"
    if any(token in text for token in ("render_", "sample_", "extract_", "stage_")):
        return "may read large case trees or write generated artifacts; prefer compute-node use for heavy cases"
    return "normally safe to inspect; run only after checking arguments and task scope"


def _inputs(path: Path) -> str:
    text = path.as_posix().lower()
    if "/agent/" in text:
        return ".agent/BOARD.md, status/journal/import docs, target package paths"
    if "/extract/" in text:
        return "registered case metadata, staged/native OpenFOAM outputs, mesh/time-window arguments"
    if "/intake/" in text:
        return "source case path, source id, registry/config metadata"
    if "/publish/" in text:
        return "registered work products, reports, destination paths"
    if "/analyze/" in text:
        return "existing work_products/reports/imports plus task-specific CSV/JSON inputs"
    if "/docs/" in text:
        return "repo markdown docs, blockers register, board, generated metadata"
    return "task-specific arguments; run with --help or read the source first"


def _outputs(path: Path) -> str:
    text = path.as_posix().lower()
    if "test_" in path.name.lower():
        return "test pass/fail result; may create temporary files"
    if "/agent/" in text:
        return "preflight/finish/lint/dashboard output; may validate required handoff docs"
    if "/extract/" in text:
        return "work_products, tmp_extract, staging/render_inputs, figures, or sampled tables"
    if "/intake/" in text:
        return "registry rows and import manifests when explicitly invoked"
    if "/publish/" in text:
        return "published campaign artifacts or transfer logs"
    if "/analyze/" in text:
        return "task-scoped work_products package, CSV/JSON tables, README, figures"
    if "/docs/" in text:
        return ".agent generated index files or docs/repo_user_guide outputs"
    return "script-defined outputs"


def _example(path: Path) -> str:
    rel = path.relative_to(ROOT).as_posix()
    if path.suffix == ".py":
        if path.name.startswith("test_"):
            dotted = rel[:-3].replace("/", ".")
            return f"python3.11 -m unittest {dotted}"
        return f"python3.11 {rel} --help"
    if path.suffix == ".sh":
        return f"bash {rel} --help"
    return f"sed -n '1,160p' {rel}"


def _when_to_use(path: Path) -> str:
    text = path.as_posix().lower()
    if "/agent/" in text:
        return "Use during task startup, guardrail checks, or closeout."
    if "/extract/" in text:
        return "Use when a board row authorizes bounded CFD data extraction or rendering."
    if "/analyze/" in text:
        return "Use to regenerate the matching report/work-product package from cited inputs."
    if "/intake/" in text:
        return "Use when a source case is being registered or manifested."
    if "/publish/" in text:
        return "Use when a package is ready to publish or transfer."
    if "/docs/" in text:
        return "Use when updating generated repo documentation/indexes."
    return "Use only when the task scope names this helper or its workflow."


def _when_not_to_use(path: Path) -> str:
    text = path.as_posix().lower()
    if any(token in text for token in ("submit_", "sbatch", "run_openfoam")):
        return "Do not use from a login node for heavy work, without a scheduler row, or as a duplicate launch."
    if "/extract/" in text:
        return "Do not use on native outputs unless the row permits read-only extraction or staged-copy work."
    if "/publish/" in text:
        return "Do not use before manifests/provenance and destination scope are checked."
    if "/intake/" in text:
        return "Do not use without an assigned intake row and known source provenance."
    if "/analyze/" in text:
        return "Do not use to fit, tune, score, or admit beyond the builder package's documented gate."
    return "Do not use outside an assigned board row or without reading its arguments."


def discover_tools() -> list[ToolRow]:
    rows: list[ToolRow] = []
    for path in sorted(TOOLS_DIR.rglob("*")):
        if not path.is_file():
            continue
        if "__pycache__" in path.parts:
            continue
        if path.suffix not in {".py", ".sh", ".md"}:
            continue
        rel = path.relative_to(ROOT).as_posix()
        purpose = _first_docstring(path) or _leading_comment(path) or _title_from_name(path)
        rows.append(
            ToolRow(
                path=rel,
                category=_category(path),
                kind=_kind(path),
                purpose=_clean(purpose, 220),
                typical_inputs=_clean(_inputs(path)),
                typical_outputs=_clean(_outputs(path)),
                safe_example=_clean(_example(path)),
                when_to_use=_clean(_when_to_use(path)),
                when_not_to_use=_clean(_when_not_to_use(path)),
                safety=_clean(_safety(path)),
            )
        )
    return rows


def write_csv(rows: list[ToolRow], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(ToolRow.__dataclass_fields__))
        writer.writeheader()
        for row in rows:
            writer.writerow(row.__dict__)


def write_markdown(rows: list[ToolRow], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    counts: dict[str, int] = {}
    for row in rows:
        counts[row.category] = counts.get(row.category, 0) + 1
    lines = [
        "---",
        "provenance:",
        "  - tools/docs/build_repo_tool_inventory.py",
        "  - tools/AGENTS.override.md",
        "  - tools/agent/README.md",
        "tags: [repo-user-guide, tool-inventory, tooling]",
        "related:",
        "  - docs/repo_user_guide/quickstart.md",
        "  - docs/repo_user_guide/common_tasks.md",
        "task: TODO-REPO-USER-GUIDE-README-TOOLING",
        "date: 2026-07-22",
        "role: Writer/Implementer/Tester",
        "type: report",
        "status: complete",
        "---",
        "# Tool Index",
        "",
        "Generated by `python3.11 tools/docs/build_repo_tool_inventory.py`.",
        "Examples that end in `--help` are discovery commands; inspect source before running mutating or HPC-capable tools.",
        "",
        "## Category Counts",
        "",
        "| Category | Count |",
        "| --- | ---: |",
    ]
    for category, count in sorted(counts.items()):
        lines.append(f"| {category} | {count} |")
    lines.extend(
        [
            "",
            "## Inventory",
            "",
            "| Path | Category | Kind | Purpose | Inputs | Outputs | Safe example | Use when | Do not use when | Safety |",
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for row in rows:
        values = [
            f"`{row.path}`",
            row.category,
            row.kind,
            row.purpose,
            row.typical_inputs,
            row.typical_outputs,
            f"`{row.safe_example}`",
            row.when_to_use,
            row.when_not_to_use,
            row.safety,
        ]
        escaped = [value.replace("|", "\\|").replace("\n", " ") for value in values]
        lines.append("| " + " | ".join(escaped) + " |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()
    rows = discover_tools()
    write_csv(rows, args.out_dir / "tool_inventory.csv")
    write_markdown(rows, args.out_dir / "tool_index.md")
    print(f"wrote {len(rows)} tool rows to {args.out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
