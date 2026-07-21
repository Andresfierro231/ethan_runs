#!/usr/bin/env python3
"""Read-only validation for the external CSEM thesis instruction layer.

This script intentionally writes nothing. It is kept under ethan_runs so agents
can run the common CSEM checks from an in-scope path without creating ad hoc
/tmp scripts.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PAPERS_ROOT = ROOT.parent / "papers"
CSEM_ROOT = PAPERS_ROOT / "UTexas_Research" / "csem-Masters_dissertation"
LITREV_ROOT = (
    PAPERS_ROOT
    / "UTexas_Research"
    / "LitRev-start---Closure-and-Modeling-Decisions-for-Developing-HITEC-Flow-TAMU-MSFL"
)


def read(path: Path) -> str:
    try:
        return path.read_text()
    except FileNotFoundError:
        return ""


def find_files(root: Path, name: str) -> list[Path]:
    if not root.exists():
        return []
    return sorted(p for p in root.rglob(name) if ".git" not in p.parts)


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate the external CSEM thesis local instruction layer without writing files."
    )
    parser.add_argument("--csem-root", type=Path, default=CSEM_ROOT)
    parser.add_argument("--litrev-root", type=Path, default=LITREV_ROOT)
    parser.add_argument(
        "--strict-placeholders",
        action="store_true",
        help="Treat TODO[source] manuscript placeholders as failures instead of residual notes.",
    )
    args = parser.parse_args()

    csem_root = args.csem_root.resolve()
    litrev_root = args.litrev_root.resolve()
    failures: list[str] = []
    notes: list[str] = []

    required = [
        csem_root / "AGENTS.md",
        csem_root / "README.md",
        csem_root / "scripts" / "build_thesis.sh",
        csem_root / "scripts" / "check_guardrails.sh",
    ]
    for path in required:
        if not path.exists():
            failures.append(f"missing required file: {rel(path)}")

    agents = read(csem_root / "AGENTS.md")
    readme = read(csem_root / "README.md")
    if "Do not add `TODO.md` files" not in agents:
        failures.append("AGENTS.md does not state the local TODO.md prohibition")
    if "Use the papers board for task queues" not in readme:
        failures.append("README.md does not route task queues to the papers board")
    if "enumitem" not in agents or "enumitem" not in readme:
        failures.append("local docs do not preserve the enumitem compatibility rule")

    todo_files = find_files(csem_root, "TODO.md") + find_files(litrev_root, "TODO.md")
    if todo_files:
        failures.append(
            "TODO.md files belong on the papers board, not in CSEM/LitRev trees:\n"
            + "\n".join(f"  - {rel(path)}" for path in todo_files)
        )

    preamble = read(csem_root / "structural" / "preamble.tex")
    if re.search(r"(?m)^[^%]*\\usepackage(?:\[[^\]]*\])?\{enumitem\}", preamble):
        failures.append("live enumitem package use found in structural/preamble.tex")

    optional_list_hits: list[str] = []
    for base in [csem_root / "intro_adjacent", csem_root / "chapters"]:
        if not base.exists():
            continue
        for tex in sorted(base.rglob("*.tex")):
            for line_no, line in enumerate(read(tex).splitlines(), start=1):
                if re.search(r"^[^%]*\\begin\{(?:itemize|enumerate)\}\[", line):
                    optional_list_hits.append(f"{rel(tex)}:{line_no}:{line}")
    if optional_list_hits:
        failures.append(
            "live optional itemize/enumerate starts require enumitem:\n"
            + "\n".join(f"  - {hit}" for hit in optional_list_hits)
        )

    placeholder_hits: list[str] = []
    for base in [csem_root / "intro_adjacent", csem_root / "chapters"]:
        if not base.exists():
            continue
        for tex in sorted(base.rglob("*.tex")):
            for line_no, line in enumerate(read(tex).splitlines(), start=1):
                if "TODO[source]" in line:
                    placeholder_hits.append(f"{rel(tex)}:{line_no}:{line.strip()}")
    if placeholder_hits:
        message = (
            "TODO[source] placeholders remain; keep them tied to board-scoped evidence-import rows:\n"
            + "\n".join(f"  - {hit}" for hit in placeholder_hits)
        )
        if args.strict_placeholders:
            failures.append(message)
        else:
            notes.append(message)

    log_text = read(csem_root / "masterthesis.log")
    if log_text:
        if re.search(r"undefined references|undefined citations|Package natbib Warning", log_text):
            failures.append("masterthesis.log contains unresolved citation/reference warnings")
    else:
        notes.append("masterthesis.log not present; run the CSEM build helper when build validation is needed")

    print("CSEM local instruction layer check")
    print(f"csem_root: {csem_root}")
    print(f"litrev_root: {litrev_root}")
    print()
    if notes:
        print("Notes:")
        for note in notes:
            print(note)
        print()
    if failures:
        print("FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
