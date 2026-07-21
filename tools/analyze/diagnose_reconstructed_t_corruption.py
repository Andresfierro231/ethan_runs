#!/usr/bin/env python3
"""Diagnose the AGENT-245 reconstructed-T blocker without mutating case data."""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "work_products/2026-07/2026-07-13/2026-07-13_reconstructed_t_repair_diagnosis"

AGENT245 = ROOT / "work_products/2026-07/2026-07-09/2026-07-09_salt2_refined_closure_qoi_repair_batch"
AGENT248 = ROOT / "work_products/2026-07/2026-07-10/2026-07-10_salt2_refined_pressure_smoke_and_8pm_batch"

RECON_T = AGENT245 / "recon/medium/518/T"
SOURCE_T = Path(
    "/home1/09748/andresfierro231/bubble_flow_loop/tamu_loop_box/ethan_data/modern_runs/salt/"
    "medium/viscosity_screening_salt_test_2_jin_medium_mesh/processors64/518/T"
)
FOAMPOST_LOG = AGENT245 / "outputs/medium/foampostprocess_viscosity_screening_salt_test_2_jin_coarse_mesh.log"
RECONSTRUCT_LOG = AGENT245 / "logs/reconstruct_medium.log"
AGENT248_MEDIUM_DIAG = AGENT248 / "outputs/medium/t_diagnostic_medium.json"
AGENT248_FINE_DIAG = AGENT248 / "outputs/fine/t_diagnostic_fine.json"

NUMERIC_RE = re.compile(
    r"(?<![A-Za-z_])[-+]?(?:nan|inf|(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?)(?![A-Za-z_])",
    re.IGNORECASE,
)


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except Exception:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def find_fatal_line(log_path: Path) -> dict[str, Any]:
    out: dict[str, Any] = {"log": rel(log_path), "line": None, "message": ""}
    if not log_path.exists():
        return out
    lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()
    for idx, line in enumerate(lines):
        if "wrong token type" in line:
            out["message"] = line.strip()
            match = re.search(r"line\s+(\d+)", line)
            if match:
                out["line"] = int(match.group(1))
            out["context"] = lines[max(0, idx - 2) : idx + 5]
            return out
    return out


def snippet(path: Path, center_line: int | None, radius: int = 10) -> list[dict[str, Any]]:
    if not center_line or not path.exists():
        return []
    start = max(1, center_line - radius)
    end = center_line + radius
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line_no, text in enumerate(handle, start=1):
            if line_no < start:
                continue
            if line_no > end:
                break
            rows.append({"line": line_no, "text": text.rstrip("\n")})
    return rows


def scan_numeric_tokens(path: Path, *, max_examples: int = 12) -> dict[str, Any]:
    counts = {
        "path": rel(path),
        "exists": path.exists(),
        "line_count": 0,
        "numeric_token_count": 0,
        "finite_count": 0,
        "nonfinite_count": 0,
        "plausible_250_1500K_count": 0,
        "implausible_finite_count": 0,
        "first_nonfinite": None,
        "first_implausible_finite": None,
        "nonfinite_examples": [],
        "implausible_finite_examples": [],
    }
    if not path.exists():
        return counts

    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line_no, line in enumerate(handle, start=1):
            counts["line_count"] = line_no
            for match in NUMERIC_RE.finditer(line):
                token = match.group(0)
                counts["numeric_token_count"] += 1
                try:
                    value = float(token)
                except ValueError:
                    continue
                example = {"line": line_no, "token": token}
                if not math.isfinite(value):
                    counts["nonfinite_count"] += 1
                    counts["first_nonfinite"] = counts["first_nonfinite"] or example
                    if len(counts["nonfinite_examples"]) < max_examples:
                        counts["nonfinite_examples"].append(example)
                    continue
                counts["finite_count"] += 1
                if 250.0 <= value <= 1500.0:
                    counts["plausible_250_1500K_count"] += 1
                else:
                    counts["implausible_finite_count"] += 1
                    counts["first_implausible_finite"] = counts["first_implausible_finite"] or {
                        "line": line_no,
                        "token": token,
                        "value": value,
                    }
                    if len(counts["implausible_finite_examples"]) < max_examples:
                        counts["implausible_finite_examples"].append(
                            {"line": line_no, "token": token, "value": value}
                        )
    return counts


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "artifact",
        "path",
        "numeric_token_count",
        "finite_count",
        "nonfinite_count",
        "plausible_250_1500K_count",
        "implausible_finite_count",
        "first_nonfinite_line",
        "first_nonfinite_token",
        "diagnosis",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default=str(OUT))
    args = parser.parse_args()

    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)

    fatal = find_fatal_line(FOAMPOST_LOG)
    recon_scan = scan_numeric_tokens(RECON_T)
    source_medium = read_json(AGENT248_MEDIUM_DIAG)
    source_fine = read_json(AGENT248_FINE_DIAG)

    source_rows = []
    for label, diag in (("source_medium", source_medium), ("source_fine", source_fine)):
        source_rows.append(
            {
                "artifact": label,
                "path": diag.get("source_T", ""),
                "numeric_token_count": diag.get("numeric_token_count"),
                "finite_count": diag.get("finite_count"),
                "nonfinite_count": diag.get("nonfinite_count"),
                "plausible_250_1500K_count": diag.get("plausible_250_1500K_count"),
                "implausible_finite_count": "",
                "first_nonfinite_line": "",
                "first_nonfinite_token": "",
                "diagnosis": "native/decomposed source T scanned finite by AGENT-248",
            }
        )

    first_nonfinite = recon_scan.get("first_nonfinite") or {}
    rows = source_rows + [
        {
            "artifact": "agent245_reconstructed_medium",
            "path": recon_scan["path"],
            "numeric_token_count": recon_scan["numeric_token_count"],
            "finite_count": recon_scan["finite_count"],
            "nonfinite_count": recon_scan["nonfinite_count"],
            "plausible_250_1500K_count": recon_scan["plausible_250_1500K_count"],
            "implausible_finite_count": recon_scan["implausible_finite_count"],
            "first_nonfinite_line": first_nonfinite.get("line", ""),
            "first_nonfinite_token": first_nonfinite.get("token", ""),
            "diagnosis": "serial reconstructed T is syntactically/physically corrupt",
        }
    ]

    payload = {
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "task_id": "AGENT-265",
        "case": "Salt2 Jin medium refined mesh, time 518",
        "fatal_openfoam_error": fatal,
        "reconstruct_log": rel(RECONSTRUCT_LOG),
        "foampostprocess_log": rel(FOAMPOST_LOG),
        "agent248_source_diagnostics": {
            "medium": source_medium,
            "fine": source_fine,
        },
        "agent245_reconstructed_medium_scan": recon_scan,
        "source_medium_snippet_at_fatal_line_number": snippet(SOURCE_T, fatal.get("line"), radius=10),
        "reconstructed_medium_snippet_at_fatal_line": snippet(RECON_T, fatal.get("line"), radius=10),
        "diagnosis": [
            "AGENT-248 pressure-only diagnostics found zero nonfinite tokens in native/decomposed medium and fine source T files.",
            "AGENT-245 reconstructPar completed without reporting failure, but the serial reconstructed medium T contains -nan tokens and implausible finite values.",
            "foamPostProcess fails when reading the first -nan token in the reconstructed serial T at line 6825807.",
            "This is a reconstructed-field quality blocker, not evidence that the native source T field is unusable.",
        ],
        "recommended_next_steps": [
            "Keep thermal UA/HTC/Nu blocked until a reconstructed T repair is proven on medium and fine.",
            "Do not sanitize or overwrite native source outputs.",
            "For a repair trial, create a fresh task-scoped reconstruction directory and reconstruct only T under the same OF13 runtime; immediately scan the serial T for nonfinite and extreme tokens before running foamPostProcess.",
            "If OF13 reconstructPar reproduces the corruption, bypass serial T by sampling from decomposed/collated processor T or reconstruct through a different, version-pinned OpenFOAM path; document equivalence before admitting thermal rows.",
            "Only after zero nonfinite reconstructed-T tokens and successful --dump-temperature section sampling should thermal closure tables be regenerated.",
        ],
    }

    (out / "diagnosis.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    write_csv(out / "field_quality_summary.csv", rows)
    (out / "README.md").write_text(
        """# Reconstructed T Repair Diagnosis

Task: `AGENT-265`

This package diagnoses the AGENT-245 thermal blocker without mutating native
solver outputs or launching a new OpenFOAM job.

## Finding

AGENT-248 already showed the native/decomposed Salt2 refined source `T` files
have zero nonfinite tokens in both medium and fine cases. The AGENT-245 serial
reconstructed medium `T` is different: it contains `-nan` tokens and implausible
finite values, and OpenFOAM fails at the first `-nan` token while reading the
field for `foamPostProcess`.

Thermal UA/HTC/Nu remains blocked. The next repair should prove a clean
reconstructed `T`, or a validated decomposed-field sampling path, before any
thermal closure claim is regenerated.

## Outputs

- `diagnosis.json`
- `field_quality_summary.csv`
""",
        encoding="utf-8",
    )
    print(f"wrote {rel(out / 'diagnosis.json')}")
    print(f"wrote {rel(out / 'field_quality_summary.csv')}")
    print(f"wrote {rel(out / 'README.md')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
