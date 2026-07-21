#!/usr/bin/env python3
"""Diagnose val_salt2 pressure evidence and corner-K fit-admission blockers.

This package is existing-evidence only. It does not run CFD, Fluid,
postprocessing jobs, or coefficient fits, and it does not change admission
state. Its purpose is to make the current `0` fit-admitted corner-K result
auditable row by row.
"""

from __future__ import annotations

import csv
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TASK = "AGENT-503"
ROOT = Path(__file__).resolve().parents[2]
OUT_REL = Path("work_products/2026-07/2026-07-17/2026-07-17_val_salt2_pressure_evidence_corner_k_diagnosis")
OUT = ROOT / OUT_REL

AGENT483_DIR = ROOT / (
    "work_products/2026-07/2026-07-17/"
    "2026-07-17_val_salt2_training_readiness_and_corner_k_unlock"
)
CORNER_ADMISSION = AGENT483_DIR / "pressure_corner_k_admission_table.csv"
CORNER_UNLOCK_QUEUE = AGENT483_DIR / "pressure_corner_k_unlock_queue.csv"
VAL_PRESSURE_MAP = AGENT483_DIR / "val_salt2_pressure_map.csv"
BRANCH_ADMISSION = ROOT / (
    "work_products/2026-07/2026-07-16/"
    "2026-07-16_pressure_ladder_harvest_admission_table/"
    "branch_orientation_straight_loss_recirc_admission.csv"
)

CASE_KEY = "val_salt2"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = []
        for row in rows:
            for key in row:
                if key not in fieldnames:
                    fieldnames.append(key)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def fnum(value: Any, default: float | None = None) -> float | None:
    try:
        if value in ("", None, "nan", "NaN"):
            return default
        number = float(value)
    except (TypeError, ValueError):
        return default
    return number if math.isfinite(number) else default


def fmt(value: float | None, digits: int = 8) -> str:
    if value is None or not math.isfinite(value):
        return ""
    return f"{value:.{digits}g}"


def yes_no(value: bool) -> str:
    return "yes" if value else "no"


def blocker_list(text: str) -> list[str]:
    return [item.strip() for item in text.split(";") if item.strip()]


def primary_failure(blockers: list[str]) -> str:
    priority = [
        "straight_loss_reference_over_subtracts",
        "recirculation_mask",
        "pressure_definition_conflict",
        "coarse_only_no_mesh_gci",
        "component_K_not_isolated",
    ]
    for item in priority:
        if item in blockers:
            return item
    return blockers[0] if blockers else "none"


def station_rollup(station_rows: list[dict[str, str]]) -> dict[str, dict[str, Any]]:
    by_span: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in station_rows:
        by_span[row["cfd_span"]].append(row)

    out: dict[str, dict[str, Any]] = {}
    for span, rows in by_span.items():
        raf_values = [fnum(row.get("reverse_area_fraction_proxy"), 0.0) or 0.0 for row in rows]
        out[span] = {
            "station_count": len(rows),
            "max_station_reverse_area_fraction_proxy": max(raf_values) if raf_values else 0.0,
            "mean_station_reverse_area_fraction_proxy": sum(raf_values) / len(raf_values) if raf_values else 0.0,
            "source_path": rel(VAL_PRESSURE_MAP),
        }
    return out


def build_val_salt2_pressure_evidence_status() -> list[dict[str, Any]]:
    stations = read_csv(VAL_PRESSURE_MAP)
    rollup = station_rollup(stations)
    branch_rows = [row for row in read_csv(BRANCH_ADMISSION) if row.get("case_key") == CASE_KEY]

    rows: list[dict[str, Any]] = []
    for row in sorted(branch_rows, key=lambda r: r["branch"]):
        branch = row["branch"]
        blockers = blocker_list(row.get("blockers", ""))
        span_rollup = rollup.get(branch, {})
        fit = row.get("true_f_D_or_K_fit_admitted") == "yes"
        rows.append(
            {
                "case_key": CASE_KEY,
                "branch": branch,
                "station_count": row.get("station_count", span_rollup.get("station_count", "")),
                "adjacent_pair_count": row.get("adjacent_pair_count", ""),
                "net_delta_p_to_minus_from_Pa": row.get("net_delta_p_to_minus_from_Pa", ""),
                "net_delta_p_rgh_to_minus_from_Pa": row.get("net_delta_p_rgh_to_minus_from_Pa", ""),
                "max_station_reverse_area_fraction_proxy": fmt(
                    fnum(span_rollup.get("max_station_reverse_area_fraction_proxy"), 0.0)
                ),
                "max_pair_reverse_area_fraction_proxy": row.get("max_pair_reverse_area_fraction_proxy", ""),
                "recirculation_mask_status": row.get("recirculation_mask_status", ""),
                "pressure_definition_status": row.get("pressure_definition_status", ""),
                "orientation_status": row.get("orientation_status", ""),
                "straight_loss_subtraction_status": row.get("straight_loss_subtraction_status", ""),
                "admission_status": row.get("admission_status", ""),
                "true_f_D_or_K_fit_admitted": row.get("true_f_D_or_K_fit_admitted", ""),
                "fit_evidence_use": "ordinary_fD_or_K_fit" if fit else "diagnostic_pressure_map_only",
                "primary_blocker": primary_failure(blockers),
                "blockers": row.get("blockers", ""),
                "next_use": row.get("next_use", ""),
                "source_paths": ";".join(
                    [
                        row.get("source_paths", rel(BRANCH_ADMISSION)),
                        span_rollup.get("source_path", rel(VAL_PRESSURE_MAP)),
                    ]
                ),
            }
        )
    return rows


def build_corner_k_failure_modes() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in read_csv(CORNER_ADMISSION):
        blockers = blocker_list(row.get("why_diagnostic", ""))
        feature_dp = fnum(row.get("feature_total_pressure_loss_pa"))
        subtracted_dp = fnum(row.get("centerline_adjacent_straight_loss_subtracted_pa"))
        ratio = None
        excess = None
        if feature_dp is not None and subtracted_dp is not None and feature_dp != 0:
            ratio = subtracted_dp / feature_dp
            excess = subtracted_dp - feature_dp
        k_local = fnum(row.get("K_local_centerline"))
        rows.append(
            {
                "case_key": row.get("case_key", ""),
                "feature": row.get("feature", ""),
                "downstream_span": row.get("downstream_span", ""),
                "adjacent_spans": row.get("adjacent_spans", ""),
                "K_apparent": row.get("K_apparent", ""),
                "K_local_centerline": row.get("K_local_centerline", ""),
                "feature_total_pressure_loss_pa": row.get("feature_total_pressure_loss_pa", ""),
                "centerline_adjacent_straight_loss_subtracted_pa": row.get(
                    "centerline_adjacent_straight_loss_subtracted_pa", ""
                ),
                "centerline_straight_to_feature_loss_ratio": fmt(ratio, 8),
                "centerline_subtraction_excess_pa": fmt(excess, 8),
                "centerline_local_K_negative": yes_no(k_local is not None and k_local < 0.0),
                "recirculation_blocked_branch_count": row.get("recirculation_blocked_branch_count", ""),
                "pressure_definition_conflict_branch_count": row.get(
                    "pressure_definition_conflict_branch_count", ""
                ),
                "fit_admitted": row.get("fit_admitted", ""),
                "admission_status": row.get("admission_status", ""),
                "primary_failure_mode": primary_failure(blockers),
                "why_diagnostic": row.get("why_diagnostic", ""),
                "interpretation": (
                    "centerline straight-loss reference over-subtracts the preserved feature pressure loss"
                    if k_local is not None and k_local < 0.0
                    else "diagnostic only pending admission gates"
                ),
                "source_paths": row.get("source_paths", rel(CORNER_ADMISSION)),
            }
        )
    return rows


def build_corner_k_gate_matrix(corner_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in corner_rows:
        blockers = blocker_list(row["why_diagnostic"])
        rows.append(
            {
                "case_key": row["case_key"],
                "feature": row["feature"],
                "feature_pressure_loss_positive_gate": "pass"
                if (fnum(row.get("feature_total_pressure_loss_pa"), 0.0) or 0.0) > 0.0
                else "fail",
                "centerline_local_K_nonnegative_gate": "fail"
                if row["centerline_local_K_negative"] == "yes"
                else "pass",
                "recirculation_free_adjacent_branches_gate": "fail"
                if "recirculation_mask" in blockers
                else "pass",
                "pressure_basis_resolved_gate": "fail"
                if "pressure_definition_conflict" in blockers
                else "pass",
                "same_qoi_mesh_gci_gate": "fail" if "coarse_only_no_mesh_gci" in blockers else "pass",
                "component_isolated_gate": "fail" if "component_K_not_isolated" in blockers else "pass",
                "fit_admitted": row["fit_admitted"],
                "admission_decision": "blocked_keep_diagnostic",
                "gate_summary": (
                    "do_not_fit: pressure drop is preserved/apparent evidence, but local K extraction "
                    "fails straight-reference, recirculation, pressure-basis, mesh/GCI, and isolation gates"
                ),
            }
        )
    return rows


def build_pressure_use_policy() -> list[dict[str, Any]]:
    return [
        {
            "evidence_object": "val_salt2_streamwise_pressure_map",
            "current_status": "external_test_diagnostic_target",
            "allowed_use": "plot/check streamwise pressure behavior after frozen prediction exists",
            "forbidden_use": "training fit; model tuning; friction or K calibration",
            "reason": "external-test split plus recirculation/coarse-no-GCI pressure branch gates",
            "source_paths": rel(VAL_PRESSURE_MAP),
        },
        {
            "evidence_object": "val_salt2_branch_pressure_rows",
            "current_status": "diagnostic_only_not_fit_admitted",
            "allowed_use": "orientation and blocker narrowing",
            "forbidden_use": "ordinary single-stream f_D or K fit",
            "reason": "all six branch rows are not admitted; all carry material recirculation masks",
            "source_paths": rel(BRANCH_ADMISSION),
        },
        {
            "evidence_object": "corner_K_apparent",
            "current_status": "diagnostic_apparent_magnitude",
            "allowed_use": "rank which corners/features deserve repaired extraction",
            "forbidden_use": "publish as physical local component K",
            "reason": "apparent feature pressure includes unresolved straight/reset/development effects",
            "source_paths": rel(CORNER_ADMISSION),
        },
        {
            "evidence_object": "corner_K_local_centerline",
            "current_status": "invalid_for_fit_current_extraction",
            "allowed_use": "evidence that current tap/straight-reference construction is wrong for fitting",
            "forbidden_use": "closure coefficient or sign claim about physical corner K",
            "reason": "12/12 rows become negative after centerline straight-loss subtraction",
            "source_paths": rel(CORNER_ADMISSION),
        },
    ]


def build_next_pressure_evidence_queue() -> list[dict[str, Any]]:
    queue = read_csv(CORNER_UNLOCK_QUEUE)
    by_feature = {row["feature"]: row for row in queue}
    actions = [
        (
            "resolve_pressure_basis",
            "Choose and document one admitted pressure basis for the QoI; reconcile p vs p_rgh sign conflicts before K work.",
            "pressure_definition_conflict",
        ),
        (
            "repair_tap_placement",
            "Place taps outside recirculation and outside the hybrid upcomer/test-section lane for ordinary K extraction.",
            "recirculation_mask",
        ),
        (
            "repair_straight_reference",
            "Subtract straight loss from a physically comparable local straight span, not a centerline span that exceeds preserved feature loss.",
            "straight_loss_reference_over_subtracts",
        ),
        (
            "produce_same_qoi_mesh_gci",
            "Repeat the extraction on a mesh family for the same corner-loss QoI before publication-ready K fitting.",
            "coarse_only_no_mesh_gci",
        ),
        (
            "isolate_component_from_reset_development",
            "Separate local corner K from upstream/downstream reset, development, and branch-apparent losses.",
            "component_K_not_isolated",
        ),
    ]
    rows: list[dict[str, Any]] = []
    for priority, (action, requirement, blocker) in enumerate(actions, start=1):
        rows.append(
            {
                "priority": priority,
                "action": action,
                "required_evidence": requirement,
                "current_blocker": blocker,
                "affected_features": ";".join(sorted(by_feature)) if by_feature else "all_current_corners",
                "current_fit_admitted_count": sum(int(row.get("fit_admitted_count", "0") or 0) for row in queue),
                "do_before": "ordinary_corner_K_fit_or_1D_model_coefficient_update",
                "source_paths": rel(CORNER_UNLOCK_QUEUE),
            }
        )
    return rows


def build_decision(
    pressure_rows: list[dict[str, Any]],
    corner_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    branch_fit = sum(1 for row in pressure_rows if row["true_f_D_or_K_fit_admitted"] == "yes")
    corner_fit = sum(1 for row in corner_rows if row["fit_admitted"] == "yes")
    corner_negative = sum(1 for row in corner_rows if row["centerline_local_K_negative"] == "yes")
    branch_recirc = sum(1 for row in pressure_rows if row["recirculation_mask_status"] == "blocked_material_recirculation_mask")
    pressure_conflicts = sum(
        1 for row in pressure_rows if "conflict" in row["pressure_definition_status"]
    )
    gate_fail_counts = Counter()
    for row in gate_rows:
        for key, value in row.items():
            if key.endswith("_gate") and value == "fail":
                gate_fail_counts[key] += 1

    return {
        "task": TASK,
        "created_utc": utc_now(),
        "decision": "keep_val_salt2_pressure_and_corner_K_diagnostic_no_fit",
        "plain_language_answer": (
            "Corner K says 0 fit-admitted entries because every current corner row is diagnostic only: "
            "12/12 local centerline K values are negative after straight-loss subtraction, 12/12 carry "
            "recirculation/coarse-no-GCI/component-isolation blockers, and the val_salt2 branch pressure "
            "rows themselves have 0 ordinary f_D/K fit-admitted entries."
        ),
        "val_salt2_branch_rows": len(pressure_rows),
        "val_salt2_branch_fit_admitted_rows": branch_fit,
        "val_salt2_recirc_blocked_branch_rows": branch_recirc,
        "val_salt2_pressure_definition_conflict_rows": pressure_conflicts,
        "corner_rows": len(corner_rows),
        "corner_fit_admitted_rows": corner_fit,
        "corner_centerline_negative_k_rows": corner_negative,
        "corner_gate_fail_counts": dict(gate_fail_counts),
        "admission_change": "none",
        "next_required_artifact": "repaired pressure extraction with admitted basis, non-recirculating taps, local straight reference, component isolation, and same-QOI mesh/GCI",
    }


def write_readme(summary: dict[str, Any]) -> None:
    readme = f"""---
provenance:
  - {rel(VAL_PRESSURE_MAP)}
  - {rel(BRANCH_ADMISSION)}
  - {rel(CORNER_ADMISSION)}
  - {rel(CORNER_UNLOCK_QUEUE)}
tags: [val-salt2, pressure-evidence, corner-k, admission, diagnostic]
related:
  - .agent/status/2026-07-17_AGENT-503.md
  - .agent/journal/2026-07-17/val-salt2-pressure-evidence-corner-k-diagnosis.md
  - work_products/2026-07/2026-07-17/2026-07-17_val_salt2_training_readiness_and_corner_k_unlock/README.md
task: {TASK}
date: 2026-07-17
role: Implementer/Tester/Writer
type: work_product
status: complete
---
# val_salt2 Pressure Evidence and Corner-K Diagnosis

## Answer

Corner K has `0` fit-admitted entries because the current evidence does not pass
ordinary component-K fit gates. All `{summary["corner_rows"]}` preserved corner
rows remain diagnostic, and `{summary["corner_centerline_negative_k_rows"]}` of
them produce negative local centerline K after adjacent straight-loss
subtraction. That is not a physical negative-K claim; it is evidence that the
current tap/straight-reference construction over-subtracts the preserved
feature pressure loss.

For `val_salt2`, the pressure map is still useful as external-test diagnostic
evidence, but all `{summary["val_salt2_branch_rows"]}` branch pressure rows have
`0` ordinary `f_D`/`K` fit-admitted entries. The branch rows are recirculation
masked, coarse/no-GCI, and in two rows have pressure-basis conflict review flags.

## Files

- `val_salt2_pressure_evidence_status.csv`: branch-level pressure status and
  fit-use policy for `val_salt2`.
- `corner_k_failure_modes.csv`: row-level corner-K failure modes, including the
  straight-loss over-subtraction ratio.
- `corner_k_gate_matrix.csv`: explicit pass/fail gates for every current corner
  row.
- `pressure_evidence_use_policy.csv`: allowed and forbidden uses.
- `next_pressure_evidence_queue.csv`: minimum work before any ordinary corner-K
  fit.
- `decision.json` and `summary.json`: machine-readable answer and counts.

## Guardrails

- No native CFD output was modified.
- No registry/admission state was modified.
- No scheduler, OpenFOAM, Fluid, or duplicate pressure-ladder job was run.
- No `val_salt2` fitting, tuning, model selection, or corner-K admission change
  was made.
"""
    (OUT / "README.md").write_text(readme)


def write_manifest() -> None:
    rows = [
        {
            "source_id": "val_salt2_pressure_map",
            "path": rel(VAL_PRESSURE_MAP),
            "read_only": "true",
            "notes": "streamwise station pressure and recirculation proxy evidence",
        },
        {
            "source_id": "branch_pressure_admission",
            "path": rel(BRANCH_ADMISSION),
            "read_only": "true",
            "notes": "branch-level f_D/K admission gates",
        },
        {
            "source_id": "corner_k_admission",
            "path": rel(CORNER_ADMISSION),
            "read_only": "true",
            "notes": "current corner apparent/local K admission table",
        },
        {
            "source_id": "corner_unlock_queue",
            "path": rel(CORNER_UNLOCK_QUEUE),
            "read_only": "true",
            "notes": "prior corner-K unlock requirements",
        },
    ]
    write_csv(OUT / "source_manifest.csv", rows)


def build() -> dict[str, Any]:
    OUT.mkdir(parents=True, exist_ok=True)
    pressure_rows = build_val_salt2_pressure_evidence_status()
    corner_rows = build_corner_k_failure_modes()
    gate_rows = build_corner_k_gate_matrix(corner_rows)
    policy_rows = build_pressure_use_policy()
    queue_rows = build_next_pressure_evidence_queue()
    decision = build_decision(pressure_rows, corner_rows, gate_rows)

    write_csv(OUT / "val_salt2_pressure_evidence_status.csv", pressure_rows)
    write_csv(OUT / "corner_k_failure_modes.csv", corner_rows)
    write_csv(OUT / "corner_k_gate_matrix.csv", gate_rows)
    write_csv(OUT / "pressure_evidence_use_policy.csv", policy_rows)
    write_csv(OUT / "next_pressure_evidence_queue.csv", queue_rows)
    (OUT / "decision.json").write_text(json.dumps(decision, indent=2, sort_keys=True) + "\n")
    (OUT / "summary.json").write_text(json.dumps(decision, indent=2, sort_keys=True) + "\n")
    write_manifest()
    write_readme(decision)
    return decision


def main() -> None:
    summary = build()
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
