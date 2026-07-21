#!/usr/bin/env python3
"""Close out wall/passive/test-section admission from completed coupled evidence.

This script does not rerun Fluid or change admission state. It consolidates the
completed PB1 M3+TS+cooler coupled scoring and the separate local
test-section/distribution assessment into one auditable decision package.
"""

from __future__ import annotations

import csv
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TASK = "AGENT-507"
ROOT = Path(__file__).resolve().parents[2]
OUT_REL = Path("work_products/2026-07/2026-07-17/2026-07-17_wall_passive_test_section_admission_closeout")
OUT = ROOT / OUT_REL

AGENT492 = ROOT / (
    "work_products/2026-07/2026-07-17/"
    "2026-07-17_cooler_fluid_timeout_and_wall_circuit_study"
)
AGENT494 = ROOT / (
    "work_products/2026-07/2026-07-17/"
    "2026-07-17_wall_test_section_coupled_admission"
)
AGENT498 = ROOT / (
    "work_products/2026-07/2026-07-17/"
    "2026-07-17_wall_test_section_distribution_ladder"
)


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


def read_json(path: Path) -> Any:
    with path.open() as handle:
        return json.load(handle)


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


def parent_wall_candidate(candidate_id: str) -> str:
    marker = "_PLUS_"
    return candidate_id.split(marker, 1)[0] if marker in candidate_id else candidate_id


def rows_by_candidate(rows: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    out: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        out[row["candidate_id"]].append(row)
    return out


def split_row(rows: list[dict[str, str]], split_role: str) -> dict[str, str]:
    for row in rows:
        if row.get("split_role") == split_role:
            return row
    return {}


def metric(row: dict[str, str], key: str) -> float | None:
    return fnum(row.get(key))


def build_admission_matrix() -> list[dict[str, Any]]:
    pb1_review = {row["candidate_id"]: row for row in read_csv(AGENT494 / "coupled_admission_review.csv")}
    pb1_deltas = rows_by_candidate(read_csv(AGENT494 / "coupled_delta_vs_m3.csv"))
    local_review = {row["candidate_id"]: row for row in read_csv(AGENT498 / "candidate_admission_review.csv")}
    local_deltas = rows_by_candidate(read_csv(AGENT498 / "coupled_delta_vs_m3.csv"))
    local_static = read_csv(AGENT498 / "static_candidate_gate.csv")
    static_gate_by_parent: dict[str, str] = {}
    for row in local_static:
        if row["split_role"] in {"validation", "holdout"}:
            parent = row["wall_candidate_id"]
            previous = static_gate_by_parent.get(parent, "pass")
            static_gate_by_parent[parent] = "fail" if row["static_gate"] == "fail" or previous == "fail" else "pass"

    rows: list[dict[str, Any]] = []
    for candidate_id, review in sorted(pb1_review.items()):
        deltas = pb1_deltas.get(candidate_id, [])
        validation = split_row(deltas, "validation")
        holdout = split_row(deltas, "holdout")
        rows.append(
            {
                "evidence_lane": "PB1_passive_total_plus_cooler",
                "candidate_id": candidate_id,
                "wall_candidate_id": "PB1_total_hA_heater_power_drive_p1",
                "cooler_candidate": candidate_id.replace("PB1_PLUS_", ""),
                "static_passive_or_distribution_gate": "pass",
                "local_test_section_gate": review.get("local_test_section_gate", "diagnostic_nonblocking"),
                "runtime_gate": review.get("runtime_gate", ""),
                "validation_coupled_gate": review.get("validation_coupled_gate", ""),
                "holdout_coupled_gate": review.get("holdout_coupled_gate", ""),
                "admission_decision": review.get("admission_decision", ""),
                "blocking_reasons": review.get("blocking_reasons", ""),
                "validation_mdot_delta_vs_m3_pct": validation.get("mdot_delta_vs_m3_pct", ""),
                "holdout_mdot_delta_vs_m3_pct": holdout.get("mdot_delta_vs_m3_pct", ""),
                "validation_all_probe_delta_vs_m3_K": validation.get("all_probe_delta_vs_m3_K", ""),
                "holdout_all_probe_delta_vs_m3_K": holdout.get("all_probe_delta_vs_m3_K", ""),
                "validation_tw_delta_vs_m3_K": "",
                "holdout_tw_delta_vs_m3_K": "",
                "interpretation": (
                    "PB1 passive-total heat prediction passes static gates and improves mdot, "
                    "but coupled all-probe temperature error is much worse than M3."
                ),
                "source_paths": f"{rel(AGENT494 / 'coupled_admission_review.csv')};{rel(AGENT494 / 'coupled_delta_vs_m3.csv')}",
            }
        )

    for candidate_id, review in sorted(local_review.items()):
        deltas = local_deltas.get(candidate_id, [])
        validation = split_row(deltas, "validation")
        holdout = split_row(deltas, "holdout")
        parent = parent_wall_candidate(candidate_id)
        rows.append(
            {
                "evidence_lane": "local_distribution_plus_cooler",
                "candidate_id": candidate_id,
                "wall_candidate_id": parent,
                "cooler_candidate": candidate_id.split("_PLUS_", 1)[1] if "_PLUS_" in candidate_id else "",
                "static_passive_or_distribution_gate": static_gate_by_parent.get(parent, ""),
                "local_test_section_gate": "coupled_local_distribution_screen",
                "runtime_gate": review.get("runtime_gate", ""),
                "validation_coupled_gate": review.get("validation_coupled_gate", ""),
                "holdout_coupled_gate": review.get("holdout_coupled_gate", ""),
                "admission_decision": review.get("admission_decision", ""),
                "blocking_reasons": review.get("blocking_reasons", ""),
                "validation_mdot_delta_vs_m3_pct": validation.get("mdot_delta_vs_m3_pct", ""),
                "holdout_mdot_delta_vs_m3_pct": holdout.get("mdot_delta_vs_m3_pct", ""),
                "validation_all_probe_delta_vs_m3_K": validation.get("all_probe_delta_vs_m3_K", ""),
                "holdout_all_probe_delta_vs_m3_K": holdout.get("all_probe_delta_vs_m3_K", ""),
                "validation_tw_delta_vs_m3_K": validation.get("tw_delta_vs_m3_K", ""),
                "holdout_tw_delta_vs_m3_K": holdout.get("tw_delta_vs_m3_K", ""),
                "interpretation": (
                    "Local heat-placement redistribution is runtime-legal and static-total plausible, "
                    "but it still worsens all-probe and TW RMSE relative to M3."
                ),
                "source_paths": f"{rel(AGENT498 / 'candidate_admission_review.csv')};{rel(AGENT498 / 'coupled_delta_vs_m3.csv')}",
            }
        )
    return rows


def build_pb1_coupled_score_summary(matrix_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in matrix_rows:
        if row["evidence_lane"] != "PB1_passive_total_plus_cooler":
            continue
        rows.append(
            {
                "candidate_id": row["candidate_id"],
                "pb1_static_gate": row["static_passive_or_distribution_gate"],
                "runtime_gate": row["runtime_gate"],
                "validation_coupled_gate": row["validation_coupled_gate"],
                "holdout_coupled_gate": row["holdout_coupled_gate"],
                "admission_decision": row["admission_decision"],
                "validation_mdot_delta_vs_m3_pct": row["validation_mdot_delta_vs_m3_pct"],
                "holdout_mdot_delta_vs_m3_pct": row["holdout_mdot_delta_vs_m3_pct"],
                "validation_all_probe_delta_vs_m3_K": row["validation_all_probe_delta_vs_m3_K"],
                "holdout_all_probe_delta_vs_m3_K": row["holdout_all_probe_delta_vs_m3_K"],
                "scientific_read": (
                    "mdot improves but temperature field degrades; passive-total hA scaling is not enough for admission"
                ),
            }
        )
    return rows


def build_local_test_section_assessment() -> list[dict[str, Any]]:
    static = read_csv(AGENT494 / "static_component_scorecard.csv")
    local_component_rows = [
        row for row in static if row.get("component_class", "").startswith("test_section_local")
    ]
    rows: list[dict[str, Any]] = []
    for row in local_component_rows:
        rows.append(
            {
                "assessment_lane": "direct_test_section_static_component",
                "candidate_id": row["candidate_id"],
                "case_id": row["case_id"],
                "split_role": row["split_role"],
                "predicted_or_candidate_value": row["predicted_loss_W"],
                "target_or_comparator_value": row["target_loss_W_for_scoring_only"],
                "abs_error": row["abs_error_W"],
                "abs_error_pct": row["abs_error_pct"],
                "gate": row["qoi_gate"],
                "diagnosis": (
                    "Salt2-fit local test-section heat model underpredicts validation/holdout test-section loss"
                    if row["split_role"] != "train"
                    else "fit row only; not a generalization score"
                ),
                "source_paths": rel(AGENT494 / "static_component_scorecard.csv"),
            }
        )

    static_distribution = read_csv(AGENT498 / "static_candidate_gate.csv")
    for row in static_distribution:
        rows.append(
            {
                "assessment_lane": "local_distribution_static_total",
                "candidate_id": row["wall_candidate_id"],
                "case_id": row["case_id"],
                "split_role": row["split_role"],
                "predicted_or_candidate_value": row["predicted_total_loss_W"],
                "target_or_comparator_value": row["target_total_loss_W_for_scoring_only"],
                "abs_error": row["abs_error_W"],
                "abs_error_pct": row["abs_error_pct"],
                "gate": row["static_gate"],
                "diagnosis": (
                    "Local distribution preserves passive-total heat but does not prove local TP/TW behavior"
                    if row["split_role"] != "train"
                    else "fit row only; not a generalization score"
                ),
                "source_paths": rel(AGENT498 / "static_candidate_gate.csv"),
            }
        )

    deltas = read_csv(AGENT498 / "coupled_delta_vs_m3.csv")
    for row in deltas:
        rows.append(
            {
                "assessment_lane": "local_distribution_coupled_probe_tw",
                "candidate_id": row["candidate_id"],
                "case_id": row["case_id"],
                "split_role": row["split_role"],
                "predicted_or_candidate_value": row["candidate_tw_rmse_K"],
                "target_or_comparator_value": row["m3_tw_rmse_K"],
                "abs_error": row["tw_delta_vs_m3_K"],
                "abs_error_pct": "",
                "gate": row["score_gate"],
                "diagnosis": "Coupled local distribution worsens TW RMSE and all-probe RMSE despite mdot improvement",
                "source_paths": rel(AGENT498 / "coupled_delta_vs_m3.csv"),
            }
        )
    return rows


def max_float(rows: list[dict[str, Any]], key: str) -> float | None:
    values = [fnum(row.get(key)) for row in rows]
    values = [value for value in values if value is not None]
    return max(values) if values else None


def min_float(rows: list[dict[str, Any]], key: str) -> float | None:
    values = [fnum(row.get(key)) for row in rows]
    values = [value for value in values if value is not None]
    return min(values) if values else None


def build_failure_modes(matrix_rows: list[dict[str, Any]], local_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    pb1_rows = [row for row in matrix_rows if row["evidence_lane"] == "PB1_passive_total_plus_cooler"]
    distribution_rows = [row for row in matrix_rows if row["evidence_lane"] == "local_distribution_plus_cooler"]
    ts_static_failures = [
        row
        for row in local_rows
        if row["assessment_lane"] == "direct_test_section_static_component"
        and row["split_role"] != "train"
        and row["gate"] == "fail"
    ]
    local_coupled = [row for row in local_rows if row["assessment_lane"] == "local_distribution_coupled_probe_tw"]
    return [
        {
            "failure_mode": "passive_total_not_sufficient",
            "evidence": (
                "PB1 static passive-total gate passes, but every PB1+cooler coupled candidate fails validation and holdout."
            ),
            "count": len(pb1_rows),
            "worst_temperature_penalty": fmt(max_float(pb1_rows, "holdout_all_probe_delta_vs_m3_K")),
            "admission_effect": "keep_blocker_open",
            "source_paths": f"{rel(AGENT494 / 'static_component_scorecard.csv')};{rel(AGENT494 / 'coupled_admission_review.csv')}",
        },
        {
            "failure_mode": "local_test_section_static_underprediction",
            "evidence": "TS6/TS7 Salt2-fit local test-section heat rows fail validation and holdout percent gates.",
            "count": len(ts_static_failures),
            "worst_temperature_penalty": "",
            "admission_effect": "local_test_section_not_admitted",
            "source_paths": rel(AGENT494 / "static_component_scorecard.csv"),
        },
        {
            "failure_mode": "local_distribution_still_temperature_wrong",
            "evidence": (
                "PB2/PB3 preserve passive-total heat and improve mdot, but all-probe and TW RMSE are far worse than M3."
            ),
            "count": len(distribution_rows),
            "worst_temperature_penalty": fmt(max_float(distribution_rows, "holdout_tw_delta_vs_m3_K")),
            "admission_effect": "local_distribution_not_admitted",
            "source_paths": rel(AGENT498 / "coupled_delta_vs_m3.csv"),
        },
        {
            "failure_mode": "runtime_not_current_blocker",
            "evidence": "AGENT-494 and AGENT-498 each completed 12/12 coupled rows with accepted roots.",
            "count": 24,
            "worst_temperature_penalty": "",
            "admission_effect": "focus_next_work_on_physics_not_timeout",
            "source_paths": f"{rel(AGENT494 / 'summary.json')};{rel(AGENT498 / 'summary.json')}",
        },
    ]


def build_next_steps() -> list[dict[str, Any]]:
    return [
        {
            "priority": 1,
            "next_step": "Add local wall-temperature drive/state to the test-section and upcomer wall model.",
            "why": "Static hA redistribution preserves total heat but misses TP/TW by tens of kelvin.",
            "success_signal": "Validation and holdout all-probe/TW RMSE beat M3 while mdot stays no worse.",
        },
        {
            "priority": 2,
            "next_step": "Separate heater/source placement from passive loss before another wall hA fit.",
            "why": "Current candidates improve mdot but shift the thermal field in the wrong places.",
            "success_signal": "Probe residuals localize to fewer spans and do not create a global TW penalty.",
        },
        {
            "priority": 3,
            "next_step": "Model upcomer axial mixing/thermal stratification instead of ordinary local Nu in the test-section lane.",
            "why": "The test section sits inside the recirculating upcomer; single-stream heat transfer fits remain invalid.",
            "success_signal": "A recirculation-aware upcomer/test-section candidate improves TW and TP probes without using realized wallHeatFlux.",
        },
        {
            "priority": 4,
            "next_step": "Only after a wall/test-section candidate passes, rerun the final corrected-split end-to-end scorecard.",
            "why": "Current PB1/PB2/PB3 candidates all fail coupled admission gates.",
            "success_signal": "A frozen candidate has train/validation/holdout/external rows with no runtime leakage.",
        },
    ]


def build_decision(matrix_rows: list[dict[str, Any]], local_rows: list[dict[str, Any]]) -> dict[str, Any]:
    coupled_completed = (
        int(read_json(AGENT494 / "summary.json")["decision"]["coupled_completed_rows"])
        + int(read_json(AGENT498 / "summary.json")["decision"]["coupled_completed_rows"])
    )
    admitted = [row for row in matrix_rows if row["admission_decision"] == "admitted"]
    pb1_rows = [row for row in matrix_rows if row["evidence_lane"] == "PB1_passive_total_plus_cooler"]
    distribution_rows = [row for row in matrix_rows if row["evidence_lane"] == "local_distribution_plus_cooler"]
    return {
        "task": TASK,
        "created_utc": utc_now(),
        "decision": "keep_predictive_wall_test_section_submodels_open",
        "plain_language_answer": (
            "PB1_total_hA_heater_power_drive_p1 has already been scored in coupled M3+TS+cooler form, "
            "and local test-section/distribution behavior has been assessed separately. The blocker stays open: "
            "PB1/PB2/PB3 improve mdot but fail temperature-field gates, and TS6/TS7 fail local test-section heat gates."
        ),
        "coupled_completed_rows_reviewed": coupled_completed,
        "candidate_rows_reviewed": len(matrix_rows),
        "admitted_candidate_rows": len(admitted),
        "pb1_coupled_candidates": len(pb1_rows),
        "pb1_admitted_candidates": sum(1 for row in pb1_rows if row["admission_decision"] == "admitted"),
        "local_distribution_candidates": len(distribution_rows),
        "local_distribution_admitted_candidates": sum(
            1 for row in distribution_rows if row["admission_decision"] == "admitted"
        ),
        "local_test_section_rows_reviewed": len(local_rows),
        "runtime_blocker": "no",
        "primary_remaining_blocker": "local_wall_temperature_source_placement_or_upcomer_mixing_physics",
        "admission_change": "none",
    }


def write_readme(decision: dict[str, Any]) -> None:
    readme = f"""---
provenance:
  - {rel(AGENT492)}
  - {rel(AGENT494)}
  - {rel(AGENT498)}
tags: [forward-model, wall-circuit, test-section, passive-boundary, admission]
related:
  - .agent/status/2026-07-17_AGENT-507.md
  - .agent/journal/2026-07-17/wall-passive-test-section-admission-closeout.md
  - operational_notes/maps/forward-predictive-model.md
task: {TASK}
date: 2026-07-17
role: Implementer/Tester/Writer
type: work_product
status: complete
---
# Wall/Passive/Test-Section Admission Closeout

## Result

`PB1_total_hA_heater_power_drive_p1` has been taken into coupled M3+TS+cooler
scoring, and local test-section/distribution behavior has been assessed
separately. The blocker decision is still:

`{decision["decision"]}`

The reason is not runtime failure. The completed evidence reviewed here covers
`{decision["coupled_completed_rows_reviewed"]}` coupled rows. The reason is
scientific: passive-total heat matching improves mdot but worsens the
temperature field, while local test-section and heat-placement candidates still
fail validation/holdout gates.

## Files

- `admission_decision_matrix.csv`: all PB1/PB2/PB3 coupled admission rows.
- `pb1_coupled_score_summary.csv`: PB1+cooler scoring summary.
- `local_test_section_assessment.csv`: direct TS6/TS7 and PB2/PB3 local behavior.
- `failure_mode_evidence.csv`: concise blocker diagnosis.
- `next_steps.csv`: prioritized next studies.
- `decision.json` and `summary.json`: machine-readable closeout.

## Guardrails

- No solver or Fluid rerun was launched.
- No native CFD output, registry/admission state, blocker register, or external
  Fluid source was modified.
- No new fit, tuning, model selection, or scientific admission change was made.
"""
    (OUT / "README.md").write_text(readme)


def write_manifest() -> None:
    rows = [
        {
            "source_id": "cooler_wall_circuit_study",
            "path": rel(AGENT492),
            "read_only": "true",
            "notes": "PB1 static candidate source and wall/test-section circuit framing",
        },
        {
            "source_id": "wall_test_section_coupled_admission",
            "path": rel(AGENT494),
            "read_only": "true",
            "notes": "PB1+cooler coupled scoring and local TS6/TS7 component gates",
        },
        {
            "source_id": "wall_test_section_distribution_ladder",
            "path": rel(AGENT498),
            "read_only": "true",
            "notes": "PB2/PB3 local heat-placement coupled scoring",
        },
    ]
    write_csv(OUT / "source_manifest.csv", rows)


def build() -> dict[str, Any]:
    OUT.mkdir(parents=True, exist_ok=True)
    matrix_rows = build_admission_matrix()
    pb1_summary = build_pb1_coupled_score_summary(matrix_rows)
    local_rows = build_local_test_section_assessment()
    failure_rows = build_failure_modes(matrix_rows, local_rows)
    next_rows = build_next_steps()
    decision = build_decision(matrix_rows, local_rows)

    write_csv(OUT / "admission_decision_matrix.csv", matrix_rows)
    write_csv(OUT / "pb1_coupled_score_summary.csv", pb1_summary)
    write_csv(OUT / "local_test_section_assessment.csv", local_rows)
    write_csv(OUT / "failure_mode_evidence.csv", failure_rows)
    write_csv(OUT / "next_steps.csv", next_rows)
    (OUT / "decision.json").write_text(json.dumps(decision, indent=2, sort_keys=True) + "\n")
    (OUT / "summary.json").write_text(json.dumps(decision, indent=2, sort_keys=True) + "\n")
    write_manifest()
    write_readme(decision)
    return decision


def main() -> None:
    print(json.dumps(build(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
