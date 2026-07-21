#!/usr/bin/env python3
"""Generate an always-current documentation index for the ethan_runs repo.

Scans the repo's durable markdown (status files, journal entries, operational
notes, report READMEs, work_product READMEs) plus the structured blocker
register, and emits machine-generated artifacts that CANNOT drift the way
hand-maintained summaries do:

  .agent/catalog.json   - every doc as a queryable record (frontmatter-aware,
                          filename+conventional-line fallback for legacy docs)
  .agent/catalog.csv    - same, flat, greppable
  .agent/STATE.md       - current state: open/blocked board tasks, blocker
                          summary, recent activity, latest doc per tag
  .agent/BLOCKERS.md    - rendered from .agent/blockers.yml

Usage:
  python3 tools/docs/build_repo_index.py            # regenerate all artifacts
  python3 tools/docs/build_repo_index.py --check     # validate only, nonzero exit on failure
  python3 tools/docs/build_repo_index.py --root /path/to/repo

The --check mode is the automatable "no-stale-blocker" guard: it fails if a
blocker's evidence file is missing, if an `open` blocker also claims to be
resolved/superseded, or if a `superseded_by` points at an unknown blocker id.

Design goal: useful on day one WITHOUT a full frontmatter backfill, and strictly
better as frontmatter adoption grows.
"""
from __future__ import annotations

import argparse
import csv
import datetime as _dt
import json
import os
import re
import sys

try:
    import yaml  # PyYAML
except Exception:  # pragma: no cover - environment guard
    yaml = None

# Doc roots to scan: (glob-ish root, doc type, filename filter).
# More specific roots MUST come before broader ones: maps/ before operational_notes/,
# because the first root to claim a path (via `seen`) sets its type.
DOC_ROOTS = [
    ("operational_notes/maps", "map", lambda n: n.endswith(".md")),
    (".agent/status", "status", lambda n: n.endswith(".md")),
    (".agent/journal", "journal", lambda n: n.endswith(".md")),
    ("operational_notes", "operational_note", lambda n: n.endswith(".md")),
    ("reports", "report", lambda n: n.lower() == "readme.md"),
    ("work_products", "work_product", lambda n: n.lower() == "readme.md"),
]

_DATE_RE = re.compile(r"(20\d{2}-\d{2}-\d{2})")
_TASK_RE = re.compile(r"\b(AGENT-\d+|T\d+|F\d+|TODO-[A-Z0-9-]+)\b")
_STATUS_LINE_RE = re.compile(r"STATUS:\s*([A-Za-z][A-Za-z /_-]*)", re.IGNORECASE)
_TAGS_LINE_RE = re.compile(r"^\s*Tags?:\s*(.+)$", re.IGNORECASE | re.MULTILINE)
_HASHTAG_RE = re.compile(r"#([a-z0-9][a-z0-9-]*)", re.IGNORECASE)
# Docs are shared team artifacts: there is intentionally NO per-doc owner field.
# Traceability is via `task`. See .agent/DOC_FRONTMATTER_SCHEMA.md.
_KV_RE = {
    "date": re.compile(r"^\s*Date:\s*`?(20\d{2}-\d{2}-\d{2})", re.IGNORECASE | re.MULTILINE),
    "task": re.compile(r"^\s*Task(?:\s*anchor)?:\s*`?([A-Za-z0-9-]+)", re.IGNORECASE | re.MULTILINE),
    "role": re.compile(r"^\s*Role:\s*`?([A-Za-z /]+)", re.IGNORECASE | re.MULTILINE),
}
_H1_RE = re.compile(r"^#\s+(.+)$", re.MULTILINE)
_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)

OPEN_STATUS_TOKENS = ("BLOCKED", "ACTIVE", "IN PROGRESS", "IN-PROGRESS",
                      "SUBMITTED", "RUNNING", "STARTED", "PENDING", "DESIGN")


def _read(path):
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        return fh.read()


def parse_frontmatter(text):
    """Return (frontmatter_dict_or_None, body)."""
    m = _FRONTMATTER_RE.match(text)
    if not m:
        return None, text
    if yaml is None:
        return None, text
    try:
        data = yaml.safe_load(m.group(1)) or {}
        if not isinstance(data, dict):
            return None, text
    except Exception:
        return None, text
    return data, text[m.end():]


def _as_list(v):
    if v is None:
        return []
    if isinstance(v, (list, tuple)):
        return [str(x) for x in v if x is not None]
    return [str(v)]


def build_record(root, rel_path, doc_type):
    """Build a catalog record from a doc, preferring frontmatter, else inferring."""
    text = _read(os.path.join(root, rel_path))
    fm, body = parse_frontmatter(text)
    head = "\n".join(text.splitlines()[:60])

    rec = {
        "path": rel_path.replace(os.sep, "/"),
        "type": doc_type,
        "has_frontmatter": fm is not None,
        "date": None, "task": None, "role": None,
        "status": None, "tags": [], "title": None,
        # priority core: provenance / tags / related
        "provenance": [], "related": [], "supersedes": [], "superseded_by": None,
    }

    if fm:
        rec["date"] = str(fm["date"]) if fm.get("date") else None
        rec["task"] = str(fm["task"]) if fm.get("task") else None
        rec["role"] = fm.get("role")
        rec["status"] = (str(fm["status"]).lower() if fm.get("status") else None)
        rec["tags"] = _as_list(fm.get("tags"))
        rec["provenance"] = _as_list(fm.get("provenance"))
        rec["related"] = _as_list(fm.get("related"))
        rec["supersedes"] = _as_list(fm.get("supersedes"))
        rec["superseded_by"] = fm.get("superseded_by")

    # --- inference fallbacks (fill any field frontmatter did not provide) ---
    if not rec["date"]:
        m = _KV_RE["date"].search(head) or _DATE_RE.search(rel_path)
        rec["date"] = m.group(1) if m else None
    if not rec["task"]:
        m = _KV_RE["task"].search(head)
        if m:
            rec["task"] = m.group(1)
        else:
            m2 = _TASK_RE.search(os.path.basename(rel_path)) or _TASK_RE.search(head)
            rec["task"] = m2.group(1) if m2 else None
    if not rec["role"]:
        m = _KV_RE["role"].search(head)
        rec["role"] = m.group(1).strip() if m else None
    if not rec["status"]:
        m = _STATUS_LINE_RE.search(text)
        # doc-level status is a single canonical token (first word of the phrase)
        rec["status"] = m.group(1).strip().split()[0].lower() if m else None
    if not rec["tags"]:
        m = _TAGS_LINE_RE.search(head)
        if m:
            rec["tags"] = sorted(set(_HASHTAG_RE.findall(m.group(1))))
    if not rec["title"]:
        m = _H1_RE.search(text)
        rec["title"] = m.group(1).strip() if m else os.path.basename(rel_path)
    return rec


def scan_docs(root):
    seen = set()
    records = []
    for sub, doc_type, keep in DOC_ROOTS:
        base = os.path.join(root, sub)
        if not os.path.isdir(base):
            continue
        for dirpath, _dirs, files in os.walk(base):
            if "__pycache__" in dirpath:
                continue
            for name in files:
                if not keep(name):
                    continue
                full = os.path.join(dirpath, name)
                rel = os.path.relpath(full, root)
                if rel in seen:
                    continue
                seen.add(rel)
                records.append(build_record(root, rel, doc_type))
    records.sort(key=lambda r: (r["date"] or "", r["path"]))
    return records


def parse_board(root):
    """Parse .agent/BOARD.md Active rows -> list of {task, owner, status_token}."""
    path = os.path.join(root, ".agent", "BOARD.md")
    if not os.path.isfile(path):
        return []
    text = _read(path)
    # Only the Active section (before the first "## Planned"/"## Archived").
    active = text.split("## Planned")[0].split("## Archived")[0]
    task_cell_re = re.compile(r"^(AGENT-\d+|TODO-[A-Z0-9-]+|T\d+|F\d+)$")
    rows = []
    for line in active.splitlines():
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 5 or not task_cell_re.match(cells[0]):
            continue
        task, goal = cells[0], cells[-1]
        m = _STATUS_LINE_RE.search(goal)
        status = m.group(1).strip().upper() if m else "UNKNOWN"
        rows.append({"task": task, "status": status})
    return rows


def load_blockers(root):
    path = os.path.join(root, ".agent", "blockers.yml")
    if not os.path.isfile(path) or yaml is None:
        return []
    data = yaml.safe_load(_read(path)) or {}
    return data.get("blockers", []) or []


def validate_blockers(root, blockers):
    """Return list of error strings (empty == valid)."""
    errors = []
    ids = set()
    for b in blockers:
        bid = b.get("id")
        if not bid:
            errors.append("blocker with no id: %r" % (b.get("title"),))
            continue
        if bid in ids:
            errors.append("duplicate blocker id: %s" % bid)
        ids.add(bid)
    for b in blockers:
        bid = b.get("id", "?")
        status = (b.get("status") or "").lower()
        ev = b.get("evidence")
        if ev and not os.path.exists(os.path.join(root, ev)):
            errors.append("[%s] evidence path missing: %s" % (bid, ev))
        if status == "open":
            if b.get("resolved_by") or b.get("superseded_by"):
                errors.append("[%s] status=open but has resolved_by/superseded_by" % bid)
            if not b.get("last_reviewed"):
                errors.append("[%s] status=open but no last_reviewed" % bid)
        elif status == "resolved":
            if not b.get("resolved_by") or not b.get("resolved_on"):
                errors.append("[%s] status=resolved needs resolved_by+resolved_on" % bid)
        elif status == "superseded":
            if not b.get("superseded_on"):
                errors.append("[%s] status=superseded needs superseded_on" % bid)
        elif status:
            errors.append("[%s] unknown status: %s" % (bid, status))
        else:
            errors.append("[%s] missing status" % bid)
    # superseded_by must resolve to a known id when it looks like an id (no slash).
    for b in blockers:
        sb = b.get("superseded_by")
        if sb and "/" not in str(sb) and str(sb) not in ids:
            errors.append("[%s] superseded_by points at unknown id: %s"
                          % (b.get("id", "?"), sb))
    return errors


# ----------------------------- renderers -----------------------------

def _now(root):
    # Real timestamp is fine here (this is a normal CLI tool, not a workflow script).
    return _dt.datetime.now().strftime("%Y-%m-%d %H:%M")


def render_blockers_md(root, blockers):
    open_b = [b for b in blockers if (b.get("status") or "").lower() == "open"]
    closed_b = [b for b in blockers if (b.get("status") or "").lower() != "open"]
    open_b.sort(key=lambda b: {"high": 0, "medium": 1, "low": 2}.get(b.get("severity"), 3))
    lines = [
        "# BLOCKERS (generated)",
        "",
        "> Generated by `tools/docs/build_repo_index.py` from `.agent/blockers.yml`.",
        "> Do not edit by hand; edit the register and regenerate. Generated: `%s`." % _now(root),
        "",
        "## Open (%d)" % len(open_b),
        "",
        "| id | severity | blocks | evidence | last reviewed |",
        "| --- | --- | --- | --- | --- |",
    ]
    for b in open_b:
        lines.append("| `%s` | %s | %s | `%s` | %s |" % (
            b.get("id"), b.get("severity", "?"),
            ", ".join(_as_list(b.get("blocks"))) or "-",
            b.get("evidence", "-"), b.get("last_reviewed", "-")))
    lines += ["", "## Resolved / superseded — do NOT re-report as open (%d)" % len(closed_b), "",
              "| id | status | resolved/superseded by | on | evidence |",
              "| --- | --- | --- | --- | --- |"]
    for b in closed_b:
        by = b.get("resolved_by") or b.get("superseded_by") or "-"
        on = b.get("resolved_on") or b.get("superseded_on") or "-"
        lines.append("| `%s` | %s | %s | %s | `%s` |" % (
            b.get("id"), b.get("status"), by, on, b.get("evidence", "-")))
    lines += ["", "## Notes", ""]
    for b in blockers:
        note = (b.get("notes") or "").strip().replace("\n", " ")
        if note:
            lines.append("- **`%s`** (%s): %s" % (b.get("id"), b.get("status"), note))
    return "\n".join(lines) + "\n"


def render_state_md(root, records, board, blockers, recent_days=10):
    open_tasks = [r for r in board if any(t in r["status"] for t in OPEN_STATUS_TOKENS)]
    blocked_tasks = [r for r in board if "BLOCKED" in r["status"]]
    open_blockers = [b for b in blockers if (b.get("status") or "").lower() == "open"]

    # recent activity
    today = _dt.date.today()
    recent = []
    for r in records:
        if not r["date"]:
            continue
        try:
            d = _dt.date.fromisoformat(r["date"])
        except ValueError:
            continue
        if (today - d).days <= recent_days:
            recent.append(r)
    recent.sort(key=lambda r: r["date"], reverse=True)

    # latest doc per tag
    tag_latest = {}
    for r in records:
        for t in r["tags"]:
            cur = tag_latest.get(t)
            if cur is None or (r["date"] or "") > (cur["date"] or ""):
                tag_latest[t] = r

    fm_count = sum(1 for r in records if r["has_frontmatter"])
    tagged = sum(1 for r in records if r["tags"])
    with_prov = sum(1 for r in records if r["provenance"])
    with_rel = sum(1 for r in records if r["related"])
    n = max(1, len(records))
    lines = [
        "# STATE (generated)",
        "",
        "> Machine-generated by `tools/docs/build_repo_index.py`. Do not edit by hand.",
        "> Generated: `%s`. This file replaces hand-maintained state summaries;" % _now(root),
        "> if it disagrees with a prose summary, trust this file (it cannot drift).",
        "> Claude and Codex are teammates on one shared corpus; there is no per-doc owner.",
        "",
        "Authoritative human handoff: "
        "`operational_notes/07-26/13/2026-07-13_CURRENT_CLOSURE_AND_PREDICTIVE_MODEL_START_HERE.md`",
        "",
        "## Corpus",
        "",
        "- Indexed docs: **%d** (%d with frontmatter, %d inferred)" % (
            len(records), fm_count, len(records) - fm_count),
        "- Active board tasks (not COMPLETE): **%d**" % len(open_tasks),
        "- Open blockers: **%d** (see `.agent/BLOCKERS.md`)" % len(open_blockers),
        "",
        "## Priority-field coverage (provenance / tags / related)",
        "",
        "- Tagged: **%d / %d** (%.0f%%)" % (tagged, len(records), 100.0 * tagged / n),
        "- With explicit `provenance`: **%d / %d** (%.0f%%)" % (with_prov, len(records), 100.0 * with_prov / n),
        "- With explicit `related`: **%d / %d** (%.0f%%)" % (with_rel, len(records), 100.0 * with_rel / n),
        "- (New docs should fill these three first — see `.agent/DOC_FRONTMATTER_SCHEMA.md`.)",
        "",
        "## Open blockers (frontier)",
        "",
    ]
    for b in sorted(open_blockers, key=lambda b: {"high": 0, "medium": 1}.get(b.get("severity"), 2)):
        lines.append("- **%s** (`%s`, %s) — %s" % (
            b.get("title"), b.get("id"), b.get("severity", "?"), b.get("evidence", "-")))
    lines += ["", "## Active board tasks", "", "| task | status |", "| --- | --- |"]
    for r in open_tasks:
        lines.append("| %s | %s |" % (r["task"], r["status"]))
    lines += ["", "## Recent activity (last %d days)" % recent_days, "",
              "| date | task | type | title | path |", "| --- | --- | --- | --- | --- |"]
    for r in recent[:60]:
        title = (r["title"] or "")[:70]
        lines.append("| %s | %s | %s | %s | `%s` |" % (
            r["date"], r["task"] or "-", r["type"], title, r["path"]))
    lines += ["", "## Latest doc per tag", "", "| tag | latest date | doc |", "| --- | --- | --- |"]
    for t in sorted(tag_latest):
        r = tag_latest[t]
        lines.append("| `%s` | %s | `%s` |" % (t, r["date"] or "-", r["path"]))
    lines += ["", "## Topic maps", "",
              "See `operational_notes/maps/` for the map-of-content hub per topic.", ""]
    return "\n".join(lines) + "\n"


def write_catalog(root, records):
    agent = os.path.join(root, ".agent")
    with open(os.path.join(agent, "catalog.json"), "w", encoding="utf-8") as fh:
        json.dump({"generated_at": _now(root), "count": len(records), "docs": records},
                  fh, indent=2)
        fh.write("\n")
    # priority core (tags/provenance/related) is front-and-centre in the flat view
    cols = ["path", "type", "date", "task", "status", "tags", "provenance",
            "related", "role", "has_frontmatter"]
    with open(os.path.join(agent, "catalog.csv"), "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(cols)
        for r in records:
            w.writerow([r["path"], r["type"], r["date"] or "", r["task"] or "",
                        r["status"] or "", ";".join(r["tags"]),
                        ";".join(r["provenance"]), ";".join(r["related"]),
                        r["role"] or "", r["has_frontmatter"]])


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default=os.getcwd(), help="repo root (default: cwd)")
    ap.add_argument("--check", action="store_true",
                    help="validate blockers register only; nonzero exit on failure")
    args = ap.parse_args(argv)
    root = os.path.abspath(args.root)

    blockers = load_blockers(root)
    errors = validate_blockers(root, blockers)

    if args.check:
        if errors:
            sys.stderr.write("BLOCKER REGISTER VALIDATION FAILED:\n")
            for e in errors:
                sys.stderr.write("  - %s\n" % e)
            return 1
        print("blocker register OK (%d entries)" % len(blockers))
        return 0

    if errors:
        # Warn but still generate, so a bad register does not block index refresh.
        sys.stderr.write("WARNING: blocker register has %d issue(s):\n" % len(errors))
        for e in errors:
            sys.stderr.write("  - %s\n" % e)

    records = scan_docs(root)
    board = parse_board(root)
    agent = os.path.join(root, ".agent")
    os.makedirs(agent, exist_ok=True)
    write_catalog(root, records)
    with open(os.path.join(agent, "STATE.md"), "w", encoding="utf-8") as fh:
        fh.write(render_state_md(root, records, board, blockers))
    with open(os.path.join(agent, "BLOCKERS.md"), "w", encoding="utf-8") as fh:
        fh.write(render_blockers_md(root, blockers))
    print("indexed %d docs; %d board rows; %d blockers -> "
          ".agent/{STATE.md,catalog.json,catalog.csv,BLOCKERS.md}"
          % (len(records), len(board), len(blockers)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
