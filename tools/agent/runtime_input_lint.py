#!/usr/bin/env python3
"""Heuristic lint for forbidden predictive runtime inputs."""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.agent.common import REPO_ROOT, iter_files  # noqa: E402

FORBIDDEN = [
    "wallHeatFlux",
    "realized wallHeatFlux",
    "CFD mdot",
    "validation temperature",
    "validation temperatures",
    "holdout temperature",
    "sensor temperature",
    "imposed CFD cooler duty",
    "realized cooler duty",
]
INPUT_CONTEXT_RE = re.compile(r"\b(runtime|predictive|model|solver|input|feature|parameter)\b", re.I)
SAFE_CONTEXT_RE = re.compile(r"\b(forbidden|not\s+runtime|not\s+predictive|scoring-only|diagnostic|target|audit|violation\s*0|never\s+fit|do\s+not\s+use|must\s+not\s+use)\b", re.I)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+")
    args = parser.parse_args()

    findings: list[str] = []
    for file_path in iter_files([REPO_ROOT / p for p in args.paths]):
        text = file_path.read_text(encoding="utf-8", errors="replace")
        for idx, line in enumerate(text.splitlines(), start=1):
            if SAFE_CONTEXT_RE.search(line):
                continue
            if INPUT_CONTEXT_RE.search(line) and any(token in line for token in FORBIDDEN):
                findings.append(f"{file_path.relative_to(REPO_ROOT)}:{idx}: possible runtime-input leakage: {line.strip()}")
    if findings:
        print("\n".join(findings))
        return 1
    print("runtime_input_lint: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
