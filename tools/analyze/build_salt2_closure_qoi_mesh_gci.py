#!/usr/bin/env python3
"""Build Salt2-first Closure-QOI mesh GCI package.

Reusable entry point:

    python3.11 tools/analyze/build_salt2_closure_qoi_mesh_gci.py

This consumes existing coarse closure observations, AGENT-262 medium/fine
pressure-family comparisons, and AGENT-267 repaired medium thermal rows. It
does not run OpenFOAM extraction, reconstruct fields, mutate solver outputs, or
change closure-observation admission state.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.analyze.compute_gci import compute_gci  # noqa: E402

TASK_ID = "AGENT-284"
DEFAULT_CLOSURE_OBSERVATIONS = (
    ROOT
    / "work_products/2026-07/2026-07-09"
    / "2026-07-09_closure_observation_table_thermal_refresh/closure_observations.csv"
)
DEFAULT_PRESSURE_DIR = (
    ROOT
    / "work_products/2026-07/2026-07-13"
    / "2026-07-13_salt2_pressure_only_mesh_family_comparison"
)
DEFAULT_REPAIR_THERMAL = (
    ROOT
    / "work_products/2026-07/2026-07-13"
    / "2026-07-13_reconstructed_t_repair_trial/outputs/medium"
    / "segment_htc_uaprime_viscosity_screening_salt_test_2_jin_coarse_mesh.csv"
)
DEFAULT_OUTPUT = (
    ROOT
    / "work_products/2026-07/2026-07-13"
    / "2026-07-13_salt2_closure_qoi_mesh_gci"
)
CASE_ID = "salt_2"
SOURCE_ID = "viscosity_screening_salt_test_2_jin_coarse_mesh"
R21 = 1.5
R32 = 1.5

TRIPLET_FIELDS = [
    "case_id",
    "qoi_id",
    "lane",
    "span",
    "method",
    "quantity",
    "units",
    "coarse_value",
    "medium_value",
    "fine_value",
    "r21",
    "r32",
    "numeric_triplet_complete",
    "coarse_source_path",
    "medium_source_path",
    "fine_source_path",
    "coarse_admission_status",
    "medium_admission_status",
    "fine_admission_status",
    "source_gate",
    "blocker",
]

GCI_FIELDS = [
    "case_id",
    "qoi_id",
    "lane",
    "span",
    "method",
    "quantity",
    "units",
    "coarse",
    "medium",
    "fine",
    "r21",
    "r32",
    "verdict",
    "order_status",
    "observed_order_p",
    "f_exact_richardson",
    "gci_fine_pct",
    "gci_coarse_pct",
    "asymptotic_range_ratio",
    "gci_trustworthy",
    "note",
]

ADMISSION_FIELDS = [
    "case_id",
    "qoi_id",
    "lane",
    "span",
    "method",
    "quantity",
    "numeric_triplet_complete",
    "source_gate",
    "gci_verdict",
    "gci_trustworthy",
    "publication_ready",
    "admission_decision",
    "blocker",
    "recommended_use",
]

BLOCKED_FIELDS = [
    "case_id",
    "qoi_id",
    "lane",
    "span",
    "method",
    "quantity",
    "coarse_value",
    "medium_value",
    "fine_value",
    "blocker",
    "recommended_next_action",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: Iterable[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: format_value(row.get(key)) for key in fieldnames})


def format_value(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, float):
        if not math.isfinite(value):
            return ""
        return f"{value:.12g}"
    return str(value)


def number(value: str | object | None) -> float | None:
    if value is None or value == "":
        return None
    try:
        parsed = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def coarse_pressure_index(rows: list[dict[str, str]]) -> dict[tuple[str, str, str], dict[str, str]]:
    index: dict[tuple[str, str, str], dict[str, str]] = {}
    for row in rows:
        if row.get("source_id") != SOURCE_ID or row.get("case_id") != CASE_ID:
            continue
        if row.get("observable_family") != "pressure":
            continue
        quantity = row.get("quantity", "")
        if quantity == "apparent_darcy_f":
            key = ("apparent_darcy_f", row.get("span", ""), row.get("pressure_method", ""))
            index[key] = row
        elif quantity == "f_corrected":
            key = ("f_corrected", row.get("span", ""), "streamwise_momentum_budget_debuoyed")
            index[key] = row
    return index


def source_gate_from_fit_safety(fit_safety: str) -> str:
    if fit_safety in {"fit_safe_pressure_gradient", "fit_safe_momentum_corrected"}:
        return "medium_fine_source_rows_admitted"
    return "diagnostic_or_not_fit_safe"


def triplet_complete(row: dict[str, object]) -> bool:
    return all(number(row.get(level)) is not None for level in ("coarse_value", "medium_value", "fine_value"))


def build_pressure_triplets(
    closure_rows: list[dict[str, str]],
    pressure_dir: Path,
) -> list[dict[str, object]]:
    coarse = coarse_pressure_index(closure_rows)
    triplets: list[dict[str, object]] = []
    friction_rows = read_csv(pressure_dir / "friction_mesh_comparison.csv")
    for row in friction_rows:
        method = row["method"]
        span = row["span"]
        coarse_row = coarse.get(("apparent_darcy_f", span, method), {})
        source_gate = source_gate_from_fit_safety(row["fit_safety"])
        blocker = "" if source_gate == "medium_fine_source_rows_admitted" else row["fit_safety"]
        triplets.append(
            {
                "case_id": CASE_ID,
                "qoi_id": f"pressure_gradient_friction::{span}::{method}",
                "lane": "pressure_gradient_friction",
                "span": span,
                "method": method,
                "quantity": "apparent_darcy_f",
                "units": "dimensionless",
                "coarse_value": number(coarse_row.get("value")),
                "medium_value": number(row.get("medium_apparent_darcy_f")),
                "fine_value": number(row.get("fine_apparent_darcy_f")),
                "r21": R21,
                "r32": R32,
                "coarse_source_path": coarse_row.get("source_path", ""),
                "medium_source_path": rel(pressure_dir / "friction_mesh_comparison.csv"),
                "fine_source_path": rel(pressure_dir / "friction_mesh_comparison.csv"),
                "coarse_admission_status": coarse_row.get("admission_status", ""),
                "medium_admission_status": row["fit_safety"],
                "fine_admission_status": row["fit_safety"],
                "source_gate": source_gate,
                "blocker": blocker,
            }
        )

    momentum_rows = read_csv(pressure_dir / "momentum_mesh_comparison.csv")
    for row in momentum_rows:
        span = row["span"]
        coarse_row = coarse.get(("f_corrected", span, "streamwise_momentum_budget_debuoyed"), {})
        source_gate = source_gate_from_fit_safety(row["fit_safety"])
        blocker = "" if source_gate == "medium_fine_source_rows_admitted" else row["fit_safety"]
        triplets.append(
            {
                "case_id": CASE_ID,
                "qoi_id": f"momentum_corrected_friction::{span}",
                "lane": "momentum_corrected_friction",
                "span": span,
                "method": "streamwise_momentum_budget_debuoyed",
                "quantity": "f_corrected",
                "units": "dimensionless",
                "coarse_value": number(coarse_row.get("value")),
                "medium_value": number(row.get("medium_f_corrected")),
                "fine_value": number(row.get("fine_f_corrected")),
                "r21": R21,
                "r32": R32,
                "coarse_source_path": coarse_row.get("source_path", ""),
                "medium_source_path": rel(pressure_dir / "momentum_mesh_comparison.csv"),
                "fine_source_path": rel(pressure_dir / "momentum_mesh_comparison.csv"),
                "coarse_admission_status": coarse_row.get("admission_status", ""),
                "medium_admission_status": row["fit_safety"],
                "fine_admission_status": row["fit_safety"],
                "source_gate": source_gate,
                "blocker": blocker,
            }
        )
    for row in triplets:
        row["numeric_triplet_complete"] = "yes" if triplet_complete(row) else "no"
    return triplets


def finite_metric(row: dict[str, str], column: str) -> float | None:
    value = number(row.get(column))
    return value


def build_thermal_triplets(thermal_path: Path) -> list[dict[str, object]]:
    if not thermal_path.exists():
        return [
            {
                "case_id": CASE_ID,
                "qoi_id": "thermal_segment_closure::all::missing_repair_trial",
                "lane": "thermal_segment_closure",
                "quantity": "htc_uaprime_nu",
                "units": "mixed",
                "r21": R21,
                "r32": R32,
                "numeric_triplet_complete": "no",
                "source_gate": "blocked_missing_repaired_medium_thermal",
                "blocker": "AGENT-267 repaired medium thermal table not found",
            }
        ]
    rows = read_csv(thermal_path)
    triplets: list[dict[str, object]] = []
    metric_specs = [
        ("htc_wm2k", "htc_wm2k", "W/m2/K"),
        ("uaprime_wmk", "uaprime_wmk", "W/m/K"),
        ("Nu", "Nu", "dimensionless"),
    ]
    for row in rows:
        segment = row.get("segment", "")
        status = row.get("status", "")
        if status != "computed":
            triplets.append(
                {
                    "case_id": CASE_ID,
                    "qoi_id": f"thermal_segment_closure::{segment}::blocked",
                    "lane": "thermal_segment_closure",
                    "span": segment,
                    "method": "segment_htc_uaprime_repair_trial",
                    "quantity": "thermal_segment_closure",
                    "units": "mixed",
                    "coarse_value": "",
                    "medium_value": "",
                    "fine_value": "",
                    "r21": R21,
                    "r32": R32,
                    "numeric_triplet_complete": "no",
                    "coarse_source_path": "",
                    "medium_source_path": rel(thermal_path),
                    "fine_source_path": "",
                    "coarse_admission_status": "",
                    "medium_admission_status": status,
                    "fine_admission_status": "missing_fine_thermal_extraction",
                    "source_gate": "blocked_thermal_segment",
                    "blocker": row.get("status", "thermal row not computed"),
                }
            )
            continue
        for column, quantity, units in metric_specs:
            value = finite_metric(row, column)
            if value is None:
                blocker = f"medium_{quantity}_not_finite_or_not_admitted"
            else:
                blocker = "fine_thermal_extraction_missing; coarse_thermal_triplet_not_reconciled"
            triplets.append(
                {
                    "case_id": CASE_ID,
                    "qoi_id": f"thermal_segment_closure::{segment}::{quantity}",
                    "lane": "thermal_segment_closure",
                    "span": segment,
                    "method": "segment_htc_uaprime_repair_trial",
                    "quantity": quantity,
                    "units": units,
                    "coarse_value": "",
                    "medium_value": value,
                    "fine_value": "",
                    "r21": R21,
                    "r32": R32,
                    "numeric_triplet_complete": "no",
                    "coarse_source_path": "",
                    "medium_source_path": rel(thermal_path),
                    "fine_source_path": "",
                    "coarse_admission_status": "not_reconciled_for_thermal_gci",
                    "medium_admission_status": "repair_smoke_computed_not_closure_admitted",
                    "fine_admission_status": "missing_fine_thermal_extraction",
                    "source_gate": "blocked_missing_thermal_triplet",
                    "blocker": blocker,
                }
            )
    return triplets


def build_gci_rows(triplets: list[dict[str, object]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for triplet in triplets:
        if triplet.get("numeric_triplet_complete") != "yes":
            continue
        coarse = number(triplet.get("coarse_value"))
        medium = number(triplet.get("medium_value"))
        fine = number(triplet.get("fine_value"))
        if coarse is None or medium is None or fine is None:
            continue
        result = compute_gci(coarse, medium, fine, R21, R32)
        rows.append(
            {
                "case_id": triplet["case_id"],
                "qoi_id": triplet["qoi_id"],
                "lane": triplet["lane"],
                "span": triplet.get("span", ""),
                "method": triplet.get("method", ""),
                "quantity": triplet["quantity"],
                "units": triplet["units"],
                "coarse": coarse,
                "medium": medium,
                "fine": fine,
                "r21": R21,
                "r32": R32,
                "verdict": result["verdict"],
                "order_status": result["order_status"],
                "observed_order_p": result["observed_order_p"],
                "f_exact_richardson": result["f_exact_richardson"],
                "gci_fine_pct": result["gci_fine_pct"],
                "gci_coarse_pct": result["gci_coarse_pct"],
                "asymptotic_range_ratio": result["asymptotic_range_ratio"],
                "gci_trustworthy": "yes" if result["gci_trustworthy"] else "no",
                "note": result["gci_note"],
            }
        )
    return rows


def admission_decision(
    triplet: dict[str, object], gci: dict[str, object] | None
) -> tuple[str, str, str]:
    if triplet.get("numeric_triplet_complete") != "yes":
        blocker = str(triplet.get("blocker") or "missing_coarse_medium_or_fine_numeric_qoi")
        return "blocked_missing_triplet_qoi", blocker, "extract or reconcile the missing mesh-level QoI"
    if triplet.get("source_gate") != "medium_fine_source_rows_admitted":
        blocker = str(triplet.get("blocker") or "source row is diagnostic or not fit-safe")
        return "diagnostic_not_publication_gci", blocker, "keep diagnostic; do not publish as closure-QOI mesh GCI"
    if gci is None:
        return "blocked_gci_not_computed", "numeric triplet was complete but GCI row missing", "rerun builder"
    if gci.get("gci_trustworthy") != "yes":
        verdict = gci.get("verdict", "")
        return (
            "blocked_gci_not_trustworthy",
            f"computed GCI failed monotonic/asymptotic gate: {verdict}",
            "treat as mesh sensitivity diagnostic; refine extraction/admission before publication",
        )
    return "publication_ready", "", "eligible for closure-QOI mesh uncertainty table"


def build_admission_rows(
    triplets: list[dict[str, object]], gci_rows: list[dict[str, object]]
) -> list[dict[str, object]]:
    gci_by_id = {row["qoi_id"]: row for row in gci_rows}
    rows: list[dict[str, object]] = []
    for triplet in triplets:
        gci = gci_by_id.get(triplet["qoi_id"])
        decision, blocker, recommended_use = admission_decision(triplet, gci)
        rows.append(
            {
                "case_id": triplet["case_id"],
                "qoi_id": triplet["qoi_id"],
                "lane": triplet["lane"],
                "span": triplet.get("span", ""),
                "method": triplet.get("method", ""),
                "quantity": triplet["quantity"],
                "numeric_triplet_complete": triplet.get("numeric_triplet_complete", ""),
                "source_gate": triplet.get("source_gate", ""),
                "gci_verdict": "" if gci is None else gci.get("verdict", ""),
                "gci_trustworthy": "" if gci is None else gci.get("gci_trustworthy", ""),
                "publication_ready": "yes" if decision == "publication_ready" else "no",
                "admission_decision": decision,
                "blocker": blocker,
                "recommended_use": recommended_use,
            }
        )
    return rows


def build_blocked_rows(admission_rows: list[dict[str, object]], triplets: list[dict[str, object]]) -> list[dict[str, object]]:
    triplet_by_id = {row["qoi_id"]: row for row in triplets}
    blocked: list[dict[str, object]] = []
    for row in admission_rows:
        if row["publication_ready"] == "yes":
            continue
        triplet = triplet_by_id[row["qoi_id"]]
        blocked.append(
            {
                "case_id": row["case_id"],
                "qoi_id": row["qoi_id"],
                "lane": row["lane"],
                "span": row["span"],
                "method": row["method"],
                "quantity": row["quantity"],
                "coarse_value": triplet.get("coarse_value", ""),
                "medium_value": triplet.get("medium_value", ""),
                "fine_value": triplet.get("fine_value", ""),
                "blocker": row["blocker"],
                "recommended_next_action": row["recommended_use"],
            }
        )
    return blocked


def make_readme(summary: dict[str, object]) -> str:
    return f"""# Salt2 Closure-QOI Mesh GCI

Task: `{TASK_ID}`

Generated: `{summary['generated_at']}`

## Purpose

This is the Salt2-first Closure-QOI mesh GCI package requested after the
terminal-harvest plan. It separates hydraulic pressure-gradient, hydraulic
momentum-corrected, and thermal segment-closure lanes.

## Result

- Numeric complete triplets: `{summary['numeric_triplet_complete_count']}`.
- Numeric GCI rows computed: `{summary['gci_row_count']}`.
- Publication-ready Closure-QOI GCI rows: `{summary['publication_ready_count']}`.
- Thermal closure-QOI GCI status: `{summary['thermal_status']}`.

## Outputs

- `closure_qoi_triplets.csv`: coarse/medium/fine QoI values and source gates.
- `closure_qoi_gci_results.csv`: numeric GCI diagnostics where triplets are
  complete.
- `closure_qoi_admission_decisions.csv`: publication/admission decision for
  every triplet candidate.
- `blocked_or_diagnostic_qois.csv`: rows requiring follow-up or diagnostic-only
  interpretation.
- `summary.json`: counts, source paths, and boundary metadata.

## Reproduce

```bash
python3.11 tools/analyze/build_salt2_closure_qoi_mesh_gci.py
python3.11 -m unittest tools.analyze.test_salt2_closure_qoi_mesh_gci
```

## Interpretation Boundary

`publication_ready=yes` requires a finite coarse/medium/fine triplet, admitted
source rows for the lane, monotonic convergence, a valid positive observed
order, and an accepted asymptotic-range GCI check. Thermal rows remain blocked
until Salt2 fine thermal extraction is successfully produced and reconciled.
"""


def build_package(
    closure_observations_path: Path,
    pressure_dir: Path,
    thermal_path: Path,
    output_dir: Path,
) -> dict[str, object]:
    closure_rows = read_csv(closure_observations_path)
    triplets = build_pressure_triplets(closure_rows, pressure_dir)
    triplets.extend(build_thermal_triplets(thermal_path))
    for row in triplets:
        if "numeric_triplet_complete" not in row:
            row["numeric_triplet_complete"] = "yes" if triplet_complete(row) else "no"

    gci_rows = build_gci_rows(triplets)
    admission_rows = build_admission_rows(triplets, gci_rows)
    blocked_rows = build_blocked_rows(admission_rows, triplets)

    write_csv(output_dir / "closure_qoi_triplets.csv", triplets, TRIPLET_FIELDS)
    write_csv(output_dir / "closure_qoi_gci_results.csv", gci_rows, GCI_FIELDS)
    write_csv(output_dir / "closure_qoi_admission_decisions.csv", admission_rows, ADMISSION_FIELDS)
    write_csv(output_dir / "blocked_or_diagnostic_qois.csv", blocked_rows, BLOCKED_FIELDS)

    decision_counts = Counter(row["admission_decision"] for row in admission_rows)
    source_gate_counts = Counter(row["source_gate"] for row in triplets)
    summary = {
        "task_id": TASK_ID,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "closure_observations": rel(closure_observations_path),
        "pressure_dir": rel(pressure_dir),
        "thermal_medium_input": rel(thermal_path),
        "output_dir": rel(output_dir),
        "case_id": CASE_ID,
        "r21": R21,
        "r32": R32,
        "triplet_count": len(triplets),
        "numeric_triplet_complete_count": sum(
            1 for row in triplets if row.get("numeric_triplet_complete") == "yes"
        ),
        "gci_row_count": len(gci_rows),
        "publication_ready_count": decision_counts["publication_ready"],
        "admission_decision_counts": dict(sorted(decision_counts.items())),
        "source_gate_counts": dict(sorted(source_gate_counts.items())),
        "thermal_status": "blocked_missing_fine_thermal_extraction",
        "native_solver_outputs_mutated": False,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    (output_dir / "README.md").write_text(make_readme(summary), encoding="utf-8")
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--closure-observations", default=str(DEFAULT_CLOSURE_OBSERVATIONS))
    parser.add_argument("--pressure-dir", default=str(DEFAULT_PRESSURE_DIR))
    parser.add_argument("--thermal-medium", default=str(DEFAULT_REPAIR_THERMAL))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    build_package(
        Path(args.closure_observations),
        Path(args.pressure_dir),
        Path(args.thermal_medium),
        Path(args.output_dir),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
