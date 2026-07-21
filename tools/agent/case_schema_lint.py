#!/usr/bin/env python3
"""Check whether a package appears to carry the CFD-to-1D postprocessing schema."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.agent.common import REPO_ROOT, iter_files, write_json_stdout  # noqa: E402

REQUIRED = {
    "bc_source_roles": ("bc", "source", "role"),
    "material_geometry": ("material", "geometry"),
    "patchwise_heat_ledger": ("patch", "heat", "ledger"),
    "pressure_ladder": ("pressure", "ladder"),
    "thermal_score_rows": ("thermal", "score"),
    "sensor_targets": ("sensor", "target"),
    "runtime_input_audit": ("runtime", "input", "audit"),
    "pm5_f6_internal_nu": ("pm5", "f6", "nu"),
    "admission_table": ("admission",),
}


def _hits(path: Path) -> set[str]:
    files = list(iter_files([path], suffixes=(".md", ".csv", ".json", ".txt")))
    haystack = "\n".join(str(p.name).lower() for p in files)
    for p in files:
        try:
            haystack += "\n" + p.read_text(encoding="utf-8", errors="replace").lower()[:20000]
        except OSError:
            pass
    found: set[str] = set()
    for key, terms in REQUIRED.items():
        if all(term in haystack for term in terms):
            found.add(key)
    return found


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package_path")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    path = REPO_ROOT / args.package_path
    found = _hits(path)
    missing = [key for key in REQUIRED if key not in found]
    result = {"path": args.package_path, "found": sorted(found), "missing": missing, "ok": not missing}
    if args.json:
        write_json_stdout(result)
    else:
        if missing:
            print("Missing schema lanes:")
            for key in missing:
                print(f"  - {key}")
        else:
            print("case_schema_lint: OK")
    return 1 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main())

