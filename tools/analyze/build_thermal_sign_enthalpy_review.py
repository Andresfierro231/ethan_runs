#!/usr/bin/env python3
"""Build a thermal sign/enthalpy review for repaired Salt2 thermal rows.

The review compares repaired medium/fine segment HTC/UA/Nu sign labels against
the existing coarse physical-interface enthalpy ledger. It is an admission
gate, not a closure fitter.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[2]
TASK_ID = "AGENT-305"
DEFAULT_THERMAL_QOIS = (
    ROOT / "work_products/2026-07/2026-07-13/2026-07-13_thermal_mesh_gate/thermal_mesh_gate_qois.csv"
)
DEFAULT_ENTHALPY = (
    ROOT
    / "work_products/2026-07/2026-07-08/2026-07-08_patchwise_heat_ledger_enthalpy_interfaces"
    / "segment_enthalpy_residuals.csv"
)
DEFAULT_OUTPUT = ROOT / "work_products/2026-07/2026-07-13/2026-07-13_thermal_sign_enthalpy_review"

FIELDS = [
    "case_id",
    "source_id",
    "segment",
    "quantities_reviewed",
    "medium_q_signs",
    "fine_q_signs",
    "medium_wall_duty_W",
    "fine_wall_duty_W",
    "coarse_delta_T_K",
    "coarse_enthalpy_change_W",
    "coarse_segment_wallHeatFlux_sum_W",
    "coarse_residual_W",
    "coarse_residual_fraction",
    "coarse_max_interface_recirc_ratio",
    "coarse_enthalpy_status",
    "coarse_quality_flags",
    "wall_vs_enthalpy_direction",
    "repaired_q_sign_conflict",
    "admission_verdict",
    "fit_admissible",
    "review_notes",
    "thermal_qoi_source",
    "enthalpy_source",
]

BLOCKER_FIELDS = [
    "case_id",
    "source_id",
    "segment",
    "blocker",
    "details",
    "next_action",
]


def now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except Exception:
        return str(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: Iterable[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: format_value(row.get(field)) for field in fields})


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


def number(value: object | None) -> float | None:
    if value is None or value == "":
        return None
    try:
        parsed = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def sign(value: float | None, tol: float = 1.0e-9) -> int:
    if value is None:
        return 0
    if value > tol:
        return 1
    if value < -tol:
        return -1
    return 0


def sign_label(value: float | None) -> str:
    labels = {1: "positive", -1: "negative", 0: "missing_or_zero"}
    return labels[sign(value)]


def group_qois(rows: list[dict[str, str]]) -> dict[tuple[str, str, str], list[dict[str, str]]]:
    groups: dict[tuple[str, str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        groups[(row["case_id"], row["source_id"], row["segment"])].append(row)
    return groups


def enthalpy_by_segment(rows: list[dict[str, str]]) -> dict[tuple[str, str, str], dict[str, str]]:
    out: dict[tuple[str, str, str], dict[str, str]] = {}
    for row in rows:
        if row.get("case_id") != "salt_2":
            continue
        segment = row.get("physical_segment", "")
        if segment in {"lower_leg", "upcomer", "downcomer"}:
            out[(row["case_id"], row["source_id"], segment)] = row
    return out


def q_sign_conflict(q_signs: set[str], wall_sign: int, enthalpy_sign: int) -> bool:
    text = ";".join(sorted(q_signs)).lower()
    if not text:
        return False
    if "positive_out_of_fluid" in text and (wall_sign > 0 or enthalpy_sign > 0):
        return True
    if "negative_into_fluid" in text and (wall_sign < 0 or enthalpy_sign > 0):
        return True
    if "heated" in text and wall_sign < 0 and enthalpy_sign < 0:
        return True
    if "cooled" in text and wall_sign > 0 and enthalpy_sign > 0:
        return True
    return False


def verdict(
    segment: str,
    enthalpy: dict[str, str] | None,
    q_conflict: bool,
    thermal_decisions: set[str],
) -> tuple[str, str, list[dict[str, str]]]:
    blockers: list[dict[str, str]] = []
    if segment == "downcomer" or "blocked_downcomer_policy" in thermal_decisions:
        blockers.append(
            {
                "blocker": "downcomer_policy",
                "details": "downcomer/right-leg thermal segment is policy-blocked in repaired thermal extraction",
                "next_action": "decide whether downcomer remains excluded or define a separate right-leg extraction policy",
            }
        )
    if enthalpy is None:
        blockers.append(
            {
                "blocker": "missing_enthalpy_row",
                "details": "no matching physical-interface enthalpy residual row",
                "next_action": "run or locate physical-interface enthalpy extraction for this segment",
            }
        )
    else:
        recirc = number(enthalpy.get("max_interface_recirc_ratio")) or 0.0
        if recirc >= 0.5:
            blockers.append(
                {
                    "blocker": "high_recirculation_interface",
                    "details": f"max_interface_recirc_ratio={recirc:.6g}",
                    "next_action": "keep diagnostic-only or design recirculation-aware control-volume sampling",
                }
            )
        flags = enthalpy.get("quality_flags", "")
        status = enthalpy.get("enthalpy_change_status", "")
        if "not_bracketed" in flags or "not_bracketed" in status:
            blockers.append(
                {
                    "blocker": "not_bracketed",
                    "details": flags or status,
                    "next_action": "sample physical interfaces that bracket this control volume",
                }
            )
        residual_fraction = abs(number(enthalpy.get("residual_fraction")) or 0.0)
        if residual_fraction > 0.25:
            blockers.append(
                {
                    "blocker": "large_wall_enthalpy_residual",
                    "details": f"abs_residual_fraction={residual_fraction:.6g}",
                    "next_action": "audit wall patch grouping and enthalpy interface placement",
                }
            )
    if q_conflict:
        blockers.append(
            {
                "blocker": "repaired_q_sign_label_conflict",
                "details": "segment_htc q_sign label conflicts with wall/enthalpy sign evidence",
                "next_action": "audit q_sign label convention in sample_segment_htc_uaprime before admission",
            }
        )
    if any(decision != "diagnostic_two_level_missing_coarse" for decision in thermal_decisions):
        blockers.append(
            {
                "blocker": "thermal_mesh_gate_not_admitted",
                "details": ";".join(sorted(thermal_decisions)),
                "next_action": "resolve thermal mesh gate blockers before closure use",
            }
        )
    if blockers:
        return "blocked_diagnostic_only", "no", blockers
    return "review_passed_pending_coarse_triplet", "no", blockers


def build_review(thermal_qois: Path, enthalpy_csv: Path, output_dir: Path) -> dict[str, object]:
    qoi_rows = read_csv(thermal_qois)
    enthalpy_rows = read_csv(enthalpy_csv)
    qoi_groups = group_qois(qoi_rows)
    enthalpy = enthalpy_by_segment(enthalpy_rows)
    review_rows: list[dict[str, object]] = []
    blocker_rows: list[dict[str, object]] = []

    for key, rows in sorted(qoi_groups.items()):
        case_id, source_id, segment = key
        if case_id != "salt_2":
            continue
        quantities = sorted({row.get("quantity", "") for row in rows})
        medium_q_signs = {row.get("medium_q_sign", "") for row in rows if row.get("medium_q_sign", "")}
        fine_q_signs = {row.get("fine_q_sign", "") for row in rows if row.get("fine_q_sign", "")}
        medium_duties = [number(row.get("medium_wall_duty_Q_w")) for row in rows]
        fine_duties = [number(row.get("fine_wall_duty_Q_w")) for row in rows]
        medium_duty = next((value for value in medium_duties if value is not None), None)
        fine_duty = next((value for value in fine_duties if value is not None), None)
        ent = enthalpy.get(key)
        enthalpy_change = number(None if ent is None else ent.get("enthalpy_change_W"))
        wall_sum = number(None if ent is None else ent.get("segment_wallHeatFlux_sum_W"))
        wall_sign = sign(wall_sum)
        enthalpy_sign = sign(enthalpy_change)
        if wall_sign == 0 or enthalpy_sign == 0:
            direction = "missing_or_zero"
        elif wall_sign == enthalpy_sign:
            direction = "same_direction"
        else:
            direction = "opposed_direction"
        q_conflict = q_sign_conflict(medium_q_signs | fine_q_signs, wall_sign, enthalpy_sign)
        thermal_decisions = {row.get("admission_decision", "") for row in rows if row.get("admission_decision", "")}
        row_verdict, fit_admissible, blockers = verdict(segment, ent, q_conflict, thermal_decisions)
        review_row = {
            "case_id": case_id,
            "source_id": source_id,
            "segment": segment,
            "quantities_reviewed": ";".join(quantities),
            "medium_q_signs": ";".join(sorted(medium_q_signs)),
            "fine_q_signs": ";".join(sorted(fine_q_signs)),
            "medium_wall_duty_W": medium_duty,
            "fine_wall_duty_W": fine_duty,
            "coarse_delta_T_K": number(None if ent is None else ent.get("delta_T_K")),
            "coarse_enthalpy_change_W": enthalpy_change,
            "coarse_segment_wallHeatFlux_sum_W": wall_sum,
            "coarse_residual_W": number(None if ent is None else ent.get("wallHeatFlux_vs_enthalpy_residual_W")),
            "coarse_residual_fraction": number(None if ent is None else ent.get("residual_fraction")),
            "coarse_max_interface_recirc_ratio": number(None if ent is None else ent.get("max_interface_recirc_ratio")),
            "coarse_enthalpy_status": "" if ent is None else ent.get("enthalpy_change_status", ""),
            "coarse_quality_flags": "" if ent is None else ent.get("quality_flags", ""),
            "wall_vs_enthalpy_direction": direction,
            "repaired_q_sign_conflict": q_conflict,
            "admission_verdict": row_verdict,
            "fit_admissible": fit_admissible,
            "review_notes": (
                f"wallHeatFlux sign={sign_label(wall_sum)}; enthalpy sign={sign_label(enthalpy_change)}; "
                "review is diagnostic and does not admit closure targets"
            ),
            "thermal_qoi_source": rel(thermal_qois),
            "enthalpy_source": rel(enthalpy_csv),
        }
        review_rows.append(review_row)
        for blocker in blockers:
            blocker_rows.append(
                {
                    "case_id": case_id,
                    "source_id": source_id,
                    "segment": segment,
                    **blocker,
                }
            )

    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(output_dir / "thermal_sign_enthalpy_review.csv", review_rows, FIELDS)
    write_csv(output_dir / "thermal_sign_enthalpy_blockers.csv", blocker_rows, BLOCKER_FIELDS)
    verdict_counts = Counter(str(row["admission_verdict"]) for row in review_rows)
    summary = {
        "task_id": TASK_ID,
        "generated_at": now(),
        "native_solver_outputs_mutated": False,
        "thermal_qoi_source": rel(thermal_qois),
        "enthalpy_source": rel(enthalpy_csv),
        "output_dir": rel(output_dir),
        "review_row_count": len(review_rows),
        "blocker_row_count": len(blocker_rows),
        "fit_admissible_count": sum(1 for row in review_rows if row["fit_admissible"] == "yes"),
        "admission_verdict_counts": dict(sorted(verdict_counts.items())),
        "overall_status": "thermal_sign_enthalpy_review_blocks_closure_admission",
        "next_recommended_action": "run Salt2 coarse thermal repair smoke, then rebuild thermal mesh/sign gates with coarse/medium/fine evidence",
    }
    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    (output_dir / "README.md").write_text(
        f"""---
provenance:
  - {rel(thermal_qois)}
  - {rel(enthalpy_csv)}
tags: [thermal-closure, wallHeatFlux, enthalpy, sign-convention, admission-gate]
related:
  - work_products/2026-07/2026-07-13/2026-07-13_thermal_mesh_gate/README.md
  - .agent/journal/2026-07-13/thermal-mesh-gate.md
task: {TASK_ID}
date: 2026-07-13
role: Implementer/Tester/Writer
type: work-product
status: complete
---
# Thermal Sign Enthalpy Review

This package compares repaired Salt2 thermal segment sign labels against the
existing physical-interface enthalpy ledger. It is diagnostic-only.

Outputs:

- `thermal_sign_enthalpy_review.csv`
- `thermal_sign_enthalpy_blockers.csv`
- `summary.json`

Result: `fit_admissible_count=0`. Do not use repaired HTC/UA/Nu as closure-fit
targets until sign convention, heat balance, coarse thermal triplet, Nu, and
downcomer gates are closed.
""",
        encoding="utf-8",
    )
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--thermal-qois", default=str(DEFAULT_THERMAL_QOIS))
    parser.add_argument("--enthalpy-csv", default=str(DEFAULT_ENTHALPY))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    build_review(Path(args.thermal_qois), Path(args.enthalpy_csv), Path(args.output_dir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
