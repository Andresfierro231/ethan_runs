#!/usr/bin/env python3
"""Build AGENT-495 upcomer onset data-sparsity progress package."""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


TASK = "AGENT-495"
DATE = "2026-07-17"
ROOT = Path(__file__).resolve().parents[2]
OUT_REL = Path("work_products/2026-07/2026-07-17/2026-07-17_upcomer_onset_data_sparsity_progress")
OUT = ROOT / OUT_REL

AGENT464 = ROOT / "work_products/2026-07/2026-07-16/2026-07-16_f6_upcomer_blocker_status_scorecard"
AGENT467 = ROOT / "work_products/2026-07/2026-07-16/2026-07-16_recirc_feature_admission_and_hybrid_contract"
AGENT484 = ROOT / "work_products/2026-07/2026-07-17/2026-07-17_salt2_pm5q_val_salt2_readiness_ledger"
AGENT485 = ROOT / "work_products/2026-07/2026-07-17/2026-07-17_high_heat_harvest_readiness_and_live_monitor"
AGENT487 = ROOT / "work_products/2026-07/2026-07-17/2026-07-17_f6_friction_re_correction_unblock"

UPCOMER_CLASS = AGENT464 / "upcomer_onset_classification.csv"
NEXT_QUEUE = AGENT464 / "next_evidence_queue.csv"
RECIRC_FEATURES = AGENT467 / "recirculation_feature_admission_table.csv"
PM5_READINESS = AGENT484 / "pm5_recirc_readiness_ledger.csv"
HIGH_HEAT_QUEUE = AGENT485 / "harvest_readiness_queue.csv"
F6_INVENTORY = AGENT487 / "f6_candidate_inventory.csv"

LOW_BACKFLOW_LIMIT = 0.02
TRANSITION_BACKFLOW_LIMIT = 0.10
LOW_RI_LIMIT = 0.30

LEDGER_COLUMNS = [
    "row_id",
    "case_key",
    "segment",
    "source_family",
    "split_or_use_class",
    "Re",
    "Ri_median",
    "backflow_fraction",
    "reverse_area_fraction",
    "reverse_mass_fraction",
    "pressure_evidence_status",
    "wall_bulk_deltaT_status",
    "wallHeatFlux_status",
    "same_window_consistency_status",
    "mesh_time_uncertainty_status",
    "classification",
    "allowed_use",
    "forbidden_use",
    "ordinary_Nu_fit_allowed",
    "ordinary_f_D_fit_allowed",
    "component_K_fit_allowed",
    "reason",
    "source_path",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT.resolve()))
    except ValueError:
        return str(path)


def safe_float(value: Any) -> float | None:
    try:
        number = float(str(value).strip())
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def fmt(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        return f"{value:.12g}" if math.isfinite(value) else ""
    return str(value)


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: Iterable[dict[str, Any]], columns: list[str]) -> int:
    materialized = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in materialized:
            writer.writerow({column: fmt(row.get(column, "")) for column in columns})
    return len(materialized)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def metric_status(*values: Any) -> str:
    return "present" if any(str(value or "").strip() for value in values) else "missing"


def max_reverse(backflow: float | None, raf: float | None, rmf: float | None) -> float | None:
    values = [value for value in (backflow, raf, rmf) if value is not None]
    return max(values) if values else None


def classify_row(
    *,
    backflow: float | None,
    raf: float | None,
    rmf: float | None,
    ri: float | None,
    pressure_status: str,
    thermal_status: str,
    uncertainty_status: str,
) -> tuple[str, str, str, str, str, str]:
    reverse = max_reverse(backflow, raf, rmf)
    has_required_fields = pressure_status == "present" and thermal_status == "present" and uncertainty_status == "present"

    if reverse is None or ri is None:
        return (
            "not_admissible_missing_same_window_fields",
            "diagnostic_or_future_extraction_queue",
            "ordinary_Nu; ordinary_f_D; component_K",
            "no",
            "no",
            "no",
        )
    if reverse <= LOW_BACKFLOW_LIMIT and ri < LOW_RI_LIMIT and has_required_fields:
        return (
            "ordinary_single_stream_candidate",
            "candidate_only_after_independent_sign_heat_balance_mesh_review",
            "",
            "conditional",
            "conditional",
            "conditional",
        )
    if reverse <= TRANSITION_BACKFLOW_LIMIT and has_required_fields:
        return (
            "transition_anchor_candidate",
            "onset_bracketing_candidate_not_ordinary_fit",
            "ordinary_Nu; ordinary_f_D; component_K",
            "no",
            "no",
            "no",
        )
    if reverse > TRANSITION_BACKFLOW_LIMIT or ri >= LOW_RI_LIMIT:
        return (
            "recirculation_diagnostic",
            "hybrid_onset_diagnostic_and_validity_boundary",
            "ordinary_Nu; ordinary_f_D; component_K",
            "no",
            "no",
            "no",
        )
    return (
        "not_admissible_missing_same_window_fields",
        "diagnostic_or_future_extraction_queue",
        "ordinary_Nu; ordinary_f_D; component_K",
        "no",
        "no",
        "no",
    )


def make_ledger_row(
    *,
    row_id: str,
    case_key: str,
    segment: str,
    source_family: str,
    split_or_use_class: str,
    Re: Any = "",
    Ri_median: Any = "",
    backflow_fraction: Any = "",
    reverse_area_fraction: Any = "",
    reverse_mass_fraction: Any = "",
    pressure_evidence_status: str = "missing",
    wall_bulk_deltaT_status: str = "missing",
    wallHeatFlux_status: str = "missing",
    same_window_consistency_status: str = "missing",
    mesh_time_uncertainty_status: str = "missing",
    reason: str = "",
    source_path: str = "",
) -> dict[str, Any]:
    classification, allowed, forbidden, nu, fd, k = classify_row(
        backflow=safe_float(backflow_fraction),
        raf=safe_float(reverse_area_fraction),
        rmf=safe_float(reverse_mass_fraction),
        ri=safe_float(Ri_median),
        pressure_status=pressure_evidence_status,
        thermal_status=wall_bulk_deltaT_status,
        uncertainty_status=mesh_time_uncertainty_status,
    )
    if classification == "recirculation_diagnostic" and not reason:
        reason = "material reverse-flow or Ri evidence invalidates ordinary single-stream closure labels"
    elif classification == "not_admissible_missing_same_window_fields" and not reason:
        reason = "required same-window onset, pressure, thermal, or uncertainty fields are missing"
    return {
        "row_id": row_id,
        "case_key": case_key,
        "segment": segment,
        "source_family": source_family,
        "split_or_use_class": split_or_use_class,
        "Re": Re,
        "Ri_median": Ri_median,
        "backflow_fraction": backflow_fraction,
        "reverse_area_fraction": reverse_area_fraction,
        "reverse_mass_fraction": reverse_mass_fraction,
        "pressure_evidence_status": pressure_evidence_status,
        "wall_bulk_deltaT_status": wall_bulk_deltaT_status,
        "wallHeatFlux_status": wallHeatFlux_status,
        "same_window_consistency_status": same_window_consistency_status,
        "mesh_time_uncertainty_status": mesh_time_uncertainty_status,
        "classification": classification,
        "allowed_use": allowed,
        "forbidden_use": forbidden,
        "ordinary_Nu_fit_allowed": nu,
        "ordinary_f_D_fit_allowed": fd,
        "component_K_fit_allowed": k,
        "reason": reason,
        "source_path": source_path,
    }


def ledger_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    for row in read_csv(UPCOMER_CLASS):
        rows.append(
            make_ledger_row(
                row_id=f"mainline_onset:{row.get('label', '')}",
                case_key=row.get("label", ""),
                segment="upcomer",
                source_family="mainline_onset",
                split_or_use_class="mainline_onset_diagnostic",
                Re=row.get("Re_upcomer", ""),
                Ri_median=row.get("Ri_median", ""),
                backflow_fraction=row.get("backflow_fraction", ""),
                pressure_evidence_status="present",
                wall_bulk_deltaT_status="missing",
                wallHeatFlux_status="missing",
                same_window_consistency_status="partial",
                mesh_time_uncertainty_status="missing",
                reason=row.get("reason", ""),
                source_path=row.get("source_path", rel(UPCOMER_CLASS)),
            )
        )

    for row in read_csv(F6_INVENTORY):
        rows.append(
            make_ledger_row(
                row_id=f"f6_inventory:{row.get('case_key', '')}:{row.get('span', '')}",
                case_key=row.get("case_key", ""),
                segment=row.get("span", ""),
                source_family="pm5_f6_inventory",
                split_or_use_class=row.get("case_role", ""),
                Re=row.get("Re", ""),
                Ri_median=row.get("Ri", ""),
                reverse_area_fraction=row.get("reverse_area_fraction", ""),
                reverse_mass_fraction=row.get("reverse_mass_fraction", ""),
                pressure_evidence_status="present",
                wall_bulk_deltaT_status="missing",
                wallHeatFlux_status="partial",
                same_window_consistency_status="partial",
                mesh_time_uncertainty_status="missing",
                reason=row.get("reason", ""),
                source_path=row.get("source_path", rel(F6_INVENTORY)),
            )
        )

    for row in read_csv(PM5_READINESS):
        rows.append(
            make_ledger_row(
                row_id=f"pm5_readiness:{row.get('case_key', '')}:{row.get('span', '')}",
                case_key=row.get("case_key", ""),
                segment=row.get("span", ""),
                source_family="pm5_recirc_readiness",
                split_or_use_class=row.get("split_role", ""),
                Re=row.get("Re", ""),
                Ri_median=row.get("Ri", ""),
                reverse_area_fraction=row.get("reverse_area_fraction", ""),
                reverse_mass_fraction=row.get("reverse_mass_fraction", ""),
                pressure_evidence_status="present" if row.get("metric_status", "").startswith("complete") else "missing",
                wall_bulk_deltaT_status="present" if row.get("Gz", "") else "missing",
                wallHeatFlux_status="present" if row.get("wallHeatFlux_available", "") == "true" else "missing",
                same_window_consistency_status="present" if row.get("representative_time_s", "") else "missing",
                mesh_time_uncertainty_status="missing",
                reason=row.get("next_action", ""),
                source_path=row.get("source_paths", rel(PM5_READINESS)),
            )
        )

    for row in read_csv(RECIRC_FEATURES):
        rows.append(
            make_ledger_row(
                row_id=f"recirc_feature:{row.get('evidence_id', '')}",
                case_key=row.get("case_key", ""),
                segment=row.get("span", ""),
                source_family=row.get("source_kind", "recirculation_feature"),
                split_or_use_class=row.get("split_role", ""),
                Re=row.get("Re", ""),
                Ri_median=row.get("Ri", ""),
                backflow_fraction=row.get("backflow_fraction", ""),
                reverse_area_fraction=row.get("reverse_area_fraction", ""),
                reverse_mass_fraction=row.get("reverse_mass_fraction", ""),
                pressure_evidence_status="present" if row.get("source_kind", "").startswith(("pm5", "pressure", "mainline")) else "partial",
                wall_bulk_deltaT_status="missing",
                wallHeatFlux_status="missing",
                same_window_consistency_status="partial",
                mesh_time_uncertainty_status="missing",
                reason=row.get("allowed_use", ""),
                source_path=row.get("source_path", rel(RECIRC_FEATURES)),
            )
        )

    for row in read_csv(HIGH_HEAT_QUEUE):
        if not row:
            continue
        case_key = row.get("case_key") or row.get("case_id") or row.get("run_id") or row.get("scenario_id", "")
        status = row.get("harvest_status") or row.get("status") or row.get("readiness_status", "")
        rows.append(
            make_ledger_row(
                row_id=f"high_heat_queue:{case_key}",
                case_key=case_key,
                segment="upcomer",
                source_family="high_heat_no_recirc_probe_queue",
                split_or_use_class=status,
                pressure_evidence_status="missing",
                wall_bulk_deltaT_status="missing",
                wallHeatFlux_status="missing",
                same_window_consistency_status="missing",
                mesh_time_uncertainty_status="missing",
                reason="high-heat/no-recirculation probe is queued or not harvested in current evidence",
                source_path=rel(HIGH_HEAT_QUEUE),
            )
        )

    return rows


def anchor_inventory_rows(ledger: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in ledger:
        classification = row["classification"]
        if classification in {"ordinary_single_stream_candidate", "transition_anchor_candidate"}:
            anchor_status = "candidate_anchor"
        elif classification == "recirculation_diagnostic":
            anchor_status = "not_anchor_recirculating"
        else:
            anchor_status = "not_anchor_missing_fields"
        out.append(
            {
                "row_id": row["row_id"],
                "case_key": row["case_key"],
                "segment": row["segment"],
                "classification": classification,
                "anchor_status": anchor_status,
                "Re": row["Re"],
                "Ri_median": row["Ri_median"],
                "backflow_fraction": row["backflow_fraction"],
                "reverse_area_fraction": row["reverse_area_fraction"],
                "reverse_mass_fraction": row["reverse_mass_fraction"],
                "source_path": row["source_path"],
            }
        )
    return out


def same_window_gap_rows(ledger: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in ledger:
        missing = [
            name
            for name in [
                "pressure_evidence_status",
                "wall_bulk_deltaT_status",
                "wallHeatFlux_status",
                "same_window_consistency_status",
                "mesh_time_uncertainty_status",
            ]
            if row[name] != "present"
        ]
        rows.append(
            {
                "row_id": row["row_id"],
                "case_key": row["case_key"],
                "segment": row["segment"],
                "classification": row["classification"],
                "missing_field_count": len(missing),
                "missing_fields": ";".join(missing),
                "blocks_fit_admission": "yes" if missing else "no",
            }
        )
    return rows


def evidence_gap_queue_rows() -> list[dict[str, Any]]:
    base = read_csv(NEXT_QUEUE)
    rows = []
    for row in base:
        rows.append(
            {
                "blocker_id": row.get("blocker_id", ""),
                "queue_id": row.get("queue_id", ""),
                "required_evidence": row.get("required_evidence", ""),
                "minimum_acceptance": row.get("minimum_acceptance", ""),
                "current_status": row.get("status", ""),
                "priority": "high" if row.get("queue_id") in {"upcomer:1", "upcomer:2"} else "medium",
                "source_path": row.get("source_path", rel(NEXT_QUEUE)),
            }
        )
    rows.append(
        {
            "blocker_id": "upcomer-onset-data-sparsity",
            "queue_id": "upcomer:row_policy",
            "required_evidence": "row-level policy guardrail that current recirculating rows are diagnostic only",
            "minimum_acceptance": "0 ordinary Nu/f_D/K rows admitted from material recirculation evidence",
            "current_status": "complete_in_AGENT_495_package",
            "priority": "complete",
            "source_path": rel(OUT / "upcomer_row_admission_ledger.csv"),
        }
    )
    return rows


def hybrid_contract_rows() -> list[dict[str, Any]]:
    return [
        {
            "model_lane": "ordinary_single_stream_upcomer",
            "applies_when": "backflow_fraction <= 0.02 and Ri_median < 0.30 with same-window pressure, wall/bulk Delta-T, wallHeatFlux, and mesh/time uncertainty",
            "allowed_labels": "Nu; f_D; component_K only after independent sign/heat-balance/mesh gates",
            "forbidden_labels": "none once all gates pass",
            "current_status": "no_current_rows",
            "do_not_do_guardrail": "do not infer ordinary pipe coefficients from recirculating upcomer/test-section rows",
        },
        {
            "model_lane": "transition_or_onset_anchor",
            "applies_when": "0.02 < backflow_fraction <= 0.10 or bounded pair straddling the 0.02-0.10 transition band",
            "allowed_labels": "onset bracket; regime classifier training candidate",
            "forbidden_labels": "ordinary Nu; ordinary f_D; component_K",
            "current_status": "missing_anchor",
            "do_not_do_guardrail": "do not call a transition point an ordinary fit row",
        },
        {
            "model_lane": "recirculating_upcomer_effective",
            "applies_when": "backflow_fraction > 0.10 or Ri_median >= 0.30",
            "allowed_labels": "hybrid_onset_diagnostic; effective section pressure/thermal diagnostic",
            "forbidden_labels": "ordinary Nu; ordinary f_D; component_K",
            "current_status": "current_evidence_lane",
            "do_not_do_guardrail": "do not hide recirculation in a global multiplier",
        },
    ]


def misuse_guardrail_rows(ledger: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counts = Counter(row["classification"] for row in ledger)
    ordinary = sum(1 for row in ledger if row["ordinary_Nu_fit_allowed"] in {"yes", "conditional"})
    return [
        {
            "guardrail_id": "G1_no_current_ordinary_upcomer_fit",
            "status": "pass" if ordinary == 0 else "fail",
            "evidence": f"{ordinary} ordinary/conditional rows in current ledger",
            "action": "keep all current upcomer/test-section rows diagnostic-only for ordinary Nu/f_D/K",
        },
        {
            "guardrail_id": "G2_material_recirculation_blocks_single_stream_labels",
            "status": "pass",
            "evidence": f"{counts.get('recirculation_diagnostic', 0)} recirculation diagnostic rows",
            "action": "route these rows to the hybrid/onset lane",
        },
        {
            "guardrail_id": "G3_missing_same_window_fields_block_promotion",
            "status": "pass",
            "evidence": f"{counts.get('not_admissible_missing_same_window_fields', 0)} rows missing required same-window fields",
            "action": "extract or design same-window pressure/thermal/uncertainty evidence before promotion",
        },
    ]


def decision_payload(ledger: list[dict[str, Any]], anchors: list[dict[str, Any]]) -> dict[str, Any]:
    counts = Counter(row["classification"] for row in ledger)
    ordinary = [row for row in ledger if row["ordinary_Nu_fit_allowed"] in {"yes", "conditional"}]
    anchor_candidates = [row for row in anchors if row["anchor_status"] == "candidate_anchor"]
    return {
        "task": TASK,
        "created_utc": utc_now(),
        "blocker_id": "upcomer-onset-data-sparsity",
        "decision": "keep_open",
        "classification_counts": dict(counts),
        "ordinary_fit_rows": len(ordinary),
        "anchor_candidate_rows": len(anchor_candidates),
        "current_rows_are_fit_evidence": False,
        "why": (
            "Current upcomer/test-section evidence remains recirculation diagnostics or incomplete queued evidence; "
            "there are no non-recirculating/transition anchors with same-window pressure, thermal, and uncertainty fields."
        ),
        "next_unlock_sequence": [
            "harvest or design near-onset Re points",
            "obtain a non-recirculating or bounded transition anchor",
            "extract same-window wall/bulk Delta-T, pressure, wallHeatFlux, and onset metrics",
            "add mesh/time uncertainty before any closure promotion",
        ],
    }


def source_manifest_rows() -> list[dict[str, Any]]:
    sources = {
        "upcomer_onset_classification": UPCOMER_CLASS,
        "upcomer_next_evidence_queue": NEXT_QUEUE,
        "recirculation_feature_admission_table": RECIRC_FEATURES,
        "pm5_recirc_readiness_ledger": PM5_READINESS,
        "high_heat_harvest_queue": HIGH_HEAT_QUEUE,
        "f6_candidate_inventory": F6_INVENTORY,
    }
    return [
        {
            "source_id": key,
            "path": rel(path),
            "exists": "yes" if path.exists() else "no",
            "use": "upcomer onset data-sparsity evidence and admission guardrail input",
        }
        for key, path in sources.items()
    ]


def readme_text(summary: dict[str, Any], decision: dict[str, Any]) -> str:
    return f"""---
provenance:
  - {rel(UPCOMER_CLASS)}
  - {rel(RECIRC_FEATURES)}
  - {rel(PM5_READINESS)}
  - {rel(F6_INVENTORY)}
tags: [upcomer, onset, recirculation, internal-nu, friction]
related:
  - upcomer-onset-data-sparsity
  - f6-friction-re-correction
task: {TASK}
date: {DATE}
role: Hydraulics/Thermal-modeling/Implementer/Tester/Writer
type: work_product
status: complete
---
# Upcomer Onset Data-Sparsity Progress

Generated: `{summary['created_utc']}`

## Decision

`upcomer-onset-data-sparsity`: `{decision['decision']}`.

Current upcomer/test-section rows are not ordinary `Nu`, `f_D`, or component
`K` fit evidence. They remain recirculation diagnostics, hybrid/onset
diagnostics, or queued/incomplete rows.

## Results

- Ledger rows reviewed: `{summary['ledger_rows']}`.
- Ordinary fit rows admitted: `{decision['ordinary_fit_rows']}`.
- Anchor candidate rows: `{decision['anchor_candidate_rows']}`.
- Classification counts: `{json.dumps(decision['classification_counts'], sort_keys=True)}`.

## Next Unlock Sequence

1. Harvest or design near-onset Re points.
2. Obtain a non-recirculating or bounded transition anchor.
3. Extract same-window wall/bulk Delta-T, pressure, wallHeatFlux, and onset
   metrics.
4. Add mesh/time uncertainty before any closure promotion.

## Outputs

- `upcomer_row_admission_ledger.csv`
- `anchor_inventory.csv`
- `same_window_field_gap_table.csv`
- `evidence_gap_queue.csv`
- `hybrid_upcomer_model_contract.csv`
- `misuse_guardrail_summary.csv`
- `blocker_decision.json`
- `source_manifest.csv`
- `summary.json`
"""


def build() -> dict[str, Any]:
    OUT.mkdir(parents=True, exist_ok=True)
    ledger = ledger_rows()
    anchors = anchor_inventory_rows(ledger)
    gaps = same_window_gap_rows(ledger)
    queue = evidence_gap_queue_rows()
    contract = hybrid_contract_rows()
    guardrails = misuse_guardrail_rows(ledger)
    decision = decision_payload(ledger, anchors)
    counts = {
        "upcomer_row_admission_ledger.csv": write_csv(OUT / "upcomer_row_admission_ledger.csv", ledger, LEDGER_COLUMNS),
        "anchor_inventory.csv": write_csv(
            OUT / "anchor_inventory.csv",
            anchors,
            [
                "row_id",
                "case_key",
                "segment",
                "classification",
                "anchor_status",
                "Re",
                "Ri_median",
                "backflow_fraction",
                "reverse_area_fraction",
                "reverse_mass_fraction",
                "source_path",
            ],
        ),
        "same_window_field_gap_table.csv": write_csv(
            OUT / "same_window_field_gap_table.csv",
            gaps,
            ["row_id", "case_key", "segment", "classification", "missing_field_count", "missing_fields", "blocks_fit_admission"],
        ),
        "evidence_gap_queue.csv": write_csv(
            OUT / "evidence_gap_queue.csv",
            queue,
            ["blocker_id", "queue_id", "required_evidence", "minimum_acceptance", "current_status", "priority", "source_path"],
        ),
        "hybrid_upcomer_model_contract.csv": write_csv(
            OUT / "hybrid_upcomer_model_contract.csv",
            contract,
            ["model_lane", "applies_when", "allowed_labels", "forbidden_labels", "current_status", "do_not_do_guardrail"],
        ),
        "misuse_guardrail_summary.csv": write_csv(
            OUT / "misuse_guardrail_summary.csv",
            guardrails,
            ["guardrail_id", "status", "evidence", "action"],
        ),
        "source_manifest.csv": write_csv(
            OUT / "source_manifest.csv",
            source_manifest_rows(),
            ["source_id", "path", "exists", "use"],
        ),
    }
    write_json(OUT / "blocker_decision.json", decision)
    summary = {
        "task": TASK,
        "created_utc": utc_now(),
        "output_dir": rel(OUT),
        "ledger_rows": len(ledger),
        "counts": counts,
        "decision": decision,
    }
    write_json(OUT / "summary.json", summary)
    (OUT / "README.md").write_text(readme_text(summary, decision), encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    print(json.dumps(build(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
