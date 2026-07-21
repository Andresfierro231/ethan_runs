#!/usr/bin/env python3
"""Build AGENT-467 recirculation admission and hybrid 1D contract package."""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


TASK = "AGENT-467"
DATE = "2026-07-16"
ROOT = Path(__file__).resolve().parents[2]
OUT_REL = Path("work_products/2026-07/2026-07-16/2026-07-16_recirc_feature_admission_and_hybrid_contract")
OUT = ROOT / OUT_REL

AGENT455 = ROOT / "work_products/2026-07/2026-07-16/2026-07-16_closure_qoi_mesh_gci_resolution"
AGENT457 = ROOT / "work_products/2026-07/2026-07-16/2026-07-16_postprocessed_cfd_streamwise_pressure_1d_maps"
AGENT461 = ROOT / "work_products/2026-07/2026-07-16/2026-07-16_coupled_m3ts_test_section_scorecard"
AGENT464 = ROOT / "work_products/2026-07/2026-07-16/2026-07-16_f6_upcomer_blocker_status_scorecard"
AGENT460 = ROOT / "work_products/2026-07/2026-07-16/2026-07-16_pressure_map_scientific_review_and_junction_corner_state"
AGENT449 = ROOT / "work_products/2026-07/2026-07-16/2026-07-16_pressure_ladder_harvest_admission_table"

F6_SCORECARD = AGENT464 / "f6_status_scorecard.csv"
UPCOMER_ONSET = AGENT464 / "upcomer_onset_classification.csv"
UPCOMER_QUEUE = AGENT464 / "next_evidence_queue.csv"
HYBRID_LANE = AGENT455 / "upcomer_exclusion_and_hybrid_lane.csv"
PRESSURE_ADMISSION = AGENT449 / "branch_orientation_straight_loss_recirc_admission.csv"
PRESSURE_MAP_REVIEW = AGENT460 / "pressure_branch_scientific_review.csv"
M3TS_CONTRACT = AGENT461 / "next_execution_contract.csv"
M3TS_SCORECARD = AGENT461 / "coupled_candidate_scorecard.csv"
ALL_PRESSURE_MAP = AGENT457 / "all_branch_average_pressure_map.csv"

SOURCES = {
    "f6_status_scorecard": F6_SCORECARD,
    "upcomer_onset_classification": UPCOMER_ONSET,
    "upcomer_next_evidence_queue": UPCOMER_QUEUE,
    "upcomer_exclusion_and_hybrid_lane": HYBRID_LANE,
    "pressure_branch_admission": PRESSURE_ADMISSION,
    "pressure_branch_scientific_review": PRESSURE_MAP_REVIEW,
    "m3ts_next_execution_contract": M3TS_CONTRACT,
    "m3ts_candidate_scorecard": M3TS_SCORECARD,
    "all_branch_pressure_map": ALL_PRESSURE_MAP,
}

FEATURE_COLUMNS = [
    "evidence_id",
    "case_key",
    "split_role",
    "span",
    "canonical_lane",
    "Re",
    "Ri",
    "reverse_area_fraction",
    "reverse_mass_fraction",
    "backflow_fraction",
    "regime_class",
    "single_stream_fit_allowed",
    "allowed_use",
    "blocked_labels",
    "source_kind",
    "source_path",
]
CONTRACT_COLUMNS = [
    "model_lane",
    "applies_when",
    "allowed_labels",
    "forbidden_labels",
    "solver_facing_behavior",
    "required_evidence_to_admit",
    "current_status",
    "do_not_do_guardrail",
]
QUEUE_COLUMNS = [
    "queue_id",
    "blocker_id",
    "required_evidence",
    "minimum_acceptance",
    "current_status",
    "why_needed",
    "source_path",
]
DECISION_COLUMNS = [
    "claim_id",
    "decision",
    "evidence_count",
    "scientific_interpretation",
    "allowed_claim",
    "forbidden_claim",
]
MANIFEST_COLUMNS = ["source_id", "path", "exists", "role"]

REQUIRED_COLUMNS = {
    F6_SCORECARD: {"case_key", "case_role", "span", "Re", "Ri", "reverse_area_fraction", "reverse_mass_fraction", "fit_admissible_now", "source_path"},
    UPCOMER_ONSET: {"label", "Re_upcomer", "backflow_fraction", "Ri_median", "regime_class", "single_stream_fit_allowed", "source_path"},
    HYBRID_LANE: {"evidence_id", "case_key", "reported_location_or_span", "corrected_parent_leg", "reverse_area_fraction", "reverse_mass_fraction", "allowed_label_now", "excluded_single_stream_labels", "source_path"},
    UPCOMER_QUEUE: {"blocker_id", "queue_id", "required_evidence", "minimum_acceptance", "status", "source_path"},
    M3TS_CONTRACT: {"task_step", "required_input", "forbidden_input", "required_output", "acceptance_signal"},
    M3TS_SCORECARD: {"candidate_id", "candidate_class", "admission_decision", "next_required_action", "source_path"},
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT.resolve()))
    except ValueError:
        return str(path)


def fmt(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        return f"{value:.12g}" if math.isfinite(value) else ""
    return str(value)


def parse_float(value: Any) -> float | None:
    text = str(value if value is not None else "").strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    required = REQUIRED_COLUMNS.get(path)
    if required is not None:
        actual = set(rows[0].keys() if rows else [])
        missing = sorted(required - actual)
        if missing:
            raise ValueError(f"{rel(path)} missing required columns: {missing}")
    return rows


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


def classify_regime(raf: float | None, rmf: float | None, ri: float | None, observed: str = "") -> tuple[str, str, str, str]:
    if observed == "recirculation_cell_observed":
        return (
            "recirculating_upcomer_effective",
            "no",
            "regime_diagnostic_and_hybrid_model_evidence",
            "Nu; f_D; component_K",
        )
    max_reverse = max([v for v in [raf, rmf] if v is not None], default=None)
    if max_reverse is not None and max_reverse < 0.01 and (ri is None or ri < 1.0):
        return ("ordinary_pipe_candidate", "conditional_after_other_gates", "ordinary_pipe_candidate_screen", "")
    if max_reverse is not None and max_reverse < 0.10 and (ri is None or ri < 1.0):
        return ("transition_diagnostic", "no", "transition_diagnostic_only", "Nu; f_D; component_K")
    if (max_reverse is not None and max_reverse >= 0.10) or (ri is not None and ri >= 1.0):
        return ("recirculating_upcomer_effective", "no", "regime_diagnostic_and_hybrid_model_evidence", "Nu; f_D; component_K")
    return ("unknown_or_incomplete", "no", "diagnostic_pending_complete_metrics", "Nu; f_D; component_K")


def feature_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    for row in read_csv(F6_SCORECARD):
        raf = parse_float(row.get("reverse_area_fraction"))
        rmf = parse_float(row.get("reverse_mass_fraction"))
        ri = parse_float(row.get("Ri"))
        lane, allowed, use, blocked = classify_regime(raf, rmf, ri)
        blocked_labels = row.get("excluded_single_stream_labels", "") or blocked or "Nu; f_D; component_K"
        rows.append(
            {
                "evidence_id": f"f6_pm5:{row.get('case_key', '')}:{row.get('span', '')}",
                "case_key": row.get("case_key", ""),
                "split_role": row.get("case_role", ""),
                "span": row.get("span", ""),
                "canonical_lane": lane,
                "Re": row.get("Re", ""),
                "Ri": row.get("Ri", ""),
                "reverse_area_fraction": row.get("reverse_area_fraction", ""),
                "reverse_mass_fraction": row.get("reverse_mass_fraction", ""),
                "backflow_fraction": "",
                "regime_class": lane,
                "single_stream_fit_allowed": "no" if row.get("fit_admissible_now") != "yes" else allowed,
                "allowed_use": use,
                "blocked_labels": blocked,
                "source_kind": "pm5_f6_matched_plane",
                "source_path": row.get("source_path", rel(F6_SCORECARD)),
            }
        )

    for row in read_csv(UPCOMER_ONSET):
        ri = parse_float(row.get("Ri_median"))
        bf = parse_float(row.get("backflow_fraction"))
        lane, allowed, use, blocked = classify_regime(bf, None, ri, row.get("regime_class", ""))
        rows.append(
            {
                "evidence_id": f"mainline_onset:{row.get('label', '')}",
                "case_key": row.get("label", ""),
                "split_role": "mainline_onset",
                "span": "upcomer",
                "canonical_lane": lane,
                "Re": row.get("Re_upcomer", ""),
                "Ri": row.get("Ri_median", ""),
                "reverse_area_fraction": "",
                "reverse_mass_fraction": "",
                "backflow_fraction": row.get("backflow_fraction", ""),
                "regime_class": row.get("regime_class", lane),
                "single_stream_fit_allowed": "no" if row.get("single_stream_fit_allowed") != "yes" else allowed,
                "allowed_use": use,
                "blocked_labels": blocked,
                "source_kind": "mainline_onset",
                "source_path": row.get("source_path", rel(UPCOMER_ONSET)),
            }
        )

    seen = {row["evidence_id"] for row in rows}
    for row in read_csv(HYBRID_LANE):
        evidence_id = f"hybrid_lane:{row.get('evidence_id', '')}"
        if evidence_id in seen:
            continue
        raf = parse_float(row.get("reverse_area_fraction"))
        rmf = parse_float(row.get("reverse_mass_fraction"))
        lane, allowed, use, blocked = classify_regime(raf, rmf, None)
        rows.append(
            {
                "evidence_id": evidence_id,
                "case_key": row.get("case_key", ""),
                "split_role": "hybrid_lane_support",
                "span": row.get("reported_location_or_span", ""),
                "canonical_lane": lane if lane != "unknown_or_incomplete" else "recirculating_upcomer_effective",
                "Re": "",
                "Ri": "",
                "reverse_area_fraction": row.get("reverse_area_fraction", ""),
                "reverse_mass_fraction": row.get("reverse_mass_fraction", ""),
                "backflow_fraction": "",
                "regime_class": lane,
                "single_stream_fit_allowed": "no" if blocked_labels else allowed,
                "allowed_use": row.get("allowed_label_now", use),
                "blocked_labels": blocked_labels,
                "source_kind": "hybrid_lane_policy",
                "source_path": row.get("source_path", rel(HYBRID_LANE)),
            }
        )

    return rows


def contract_rows() -> list[dict[str, str]]:
    return [
        {
            "model_lane": "ordinary_pipe",
            "applies_when": "RAF < 0.01 and RMF < 0.01, with pressure definition, straight-loss subtraction, thermal residual-owner, and mesh/GCI gates passed.",
            "allowed_labels": "Nu; f_D; component_K",
            "forbidden_labels": "none beyond normal admission gates",
            "solver_facing_behavior": "Use conventional single-stream segment closure only after explicit row admission.",
            "required_evidence_to_admit": "low-recirculation masks; same-window pressure/thermal fields; accepted geometry lengths; mesh/GCI; split-safe validation.",
            "current_status": "no_current_upcomer_rows_admitted",
            "do_not_do_guardrail": "Do not infer ordinary-pipe behavior from recirculating Salt2-4 or PM5 rows.",
        },
        {
            "model_lane": "transition_diagnostic",
            "applies_when": "0.01 <= RAF or RMF < 0.10, or onset is bracketed but not resolved.",
            "allowed_labels": "onset_probability; transition_diagnostic",
            "forbidden_labels": "Nu; f_D; component_K",
            "solver_facing_behavior": "Classify and report; do not fit closure coefficients.",
            "required_evidence_to_admit": "paired ordinary and recirculating anchors plus uncertainty on RAF/RMF/Ri.",
            "current_status": "missing_transition_anchor",
            "do_not_do_guardrail": "Do not tune a continuous coefficient through the transition band without anchors.",
        },
        {
            "model_lane": "recirculating_upcomer_effective",
            "applies_when": "RAF >= 0.10, RMF >= 0.10, Ri >= 1, or recirculation_zone_flag is true.",
            "allowed_labels": "section_effective_loss; mixing_penalty; regime_diagnostic",
            "forbidden_labels": "single_stream_Nu; single_stream_f_D; component_K",
            "solver_facing_behavior": "Future solver may add a named section-effective upcomer penalty/mixing lane, explicitly separate from ordinary pipe closures.",
            "required_evidence_to_admit": "same-window RAF/RMF/SVF, wall-bulk or wall-core Delta T, Gz, pressure residual movement, mesh/time uncertainty, and split scoring.",
            "current_status": "observed_but_not_predictive",
            "do_not_do_guardrail": "Do not collapse recirculation into a global friction multiplier or an ordinary K.",
        },
        {
            "model_lane": "test_section_upcomer_subspan",
            "applies_when": "span is test_section_span/test_section in the upcomer path.",
            "allowed_labels": "test_section_heat_loss_model; upcomer_subspan_diagnostic",
            "forbidden_labels": "standalone_non_upcomer_Nu_fit; ordinary_component_K",
            "solver_facing_behavior": "Model test-section passive loss through M3+TS external-boundary/resistance-network path; keep hydraulic recirculation admission separate.",
            "required_evidence_to_admit": "Salt2-trained setup-only TS1/TS2 frozen candidate plus Salt3/Salt4 coupled mdot/Tmean/loop-delta/TP/TW scores.",
            "current_status": "M3TS_candidate_not_admitted",
            "do_not_do_guardrail": "Do not use realized wallHeatFlux, imposed CFD cooler duty, CFD mdot, or validation temperatures at runtime.",
        },
    ]


def queue_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in read_csv(UPCOMER_QUEUE):
        rows.append(
            {
                "queue_id": row.get("queue_id", ""),
                "blocker_id": row.get("blocker_id", ""),
                "required_evidence": row.get("required_evidence", ""),
                "minimum_acceptance": row.get("minimum_acceptance", ""),
                "current_status": row.get("status", ""),
                "why_needed": "bracket upcomer onset or make recirculation metrics admissible",
                "source_path": row.get("source_path", rel(UPCOMER_QUEUE)),
            }
        )
    for row in read_csv(M3TS_CONTRACT):
        rows.append(
            {
                "queue_id": f"m3ts:{row.get('task_step', '')}",
                "blocker_id": "predictive-wall-test-section-submodels",
                "required_evidence": row.get("required_input", ""),
                "minimum_acceptance": row.get("acceptance_signal", ""),
                "current_status": "open_from_agent461_contract",
                "why_needed": "separate test-section heat-loss model from recirculation and ordinary upcomer coefficients",
                "source_path": rel(M3TS_CONTRACT),
            }
        )
    for row in read_csv(M3TS_SCORECARD):
        if row.get("admission_decision") == "not_admitted" and row.get("candidate_id") in {"TS1_salt2_fit_hA_constant_drive_deltaT", "TS2_salt2_fit_constant_loss_W"}:
            rows.append(
                {
                    "queue_id": f"m3ts_candidate:{row.get('candidate_id')}",
                    "blocker_id": "predictive-wall-test-section-submodels",
                    "required_evidence": row.get("next_required_action", ""),
                    "minimum_acceptance": "coupled M3+TS validation/holdout score without forbidden runtime inputs",
                    "current_status": "candidate_runtime_legal_but_not_admitted",
                    "why_needed": "avoid promoting heat-loss replay diagnostics as predictive model evidence",
                    "source_path": row.get("source_path", rel(M3TS_SCORECARD)),
                }
            )
    return rows


def decision_rows(features: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counts = Counter(row["canonical_lane"] for row in features)
    blocked = sum(1 for row in features if row["single_stream_fit_allowed"] == "no")
    return [
        {
            "claim_id": "current_recirc_model_state",
            "decision": "no_admitted_predictive_recirculation_model",
            "evidence_count": len(features),
            "scientific_interpretation": "Current rows establish recirculation as a validity boundary, not an ordinary-pipe closure.",
            "allowed_claim": "Recirculating upcomer evidence should be used for regime/admission diagnostics and future hybrid-lane design.",
            "forbidden_claim": "A calibrated transferable upcomer Nu/f_D/K closure exists today.",
        },
        {
            "claim_id": "single_stream_fit_gate",
            "decision": "ordinary_coefficients_blocked_for_material_recirculation",
            "evidence_count": blocked,
            "scientific_interpretation": "Rows with material reverse flow or Ri evidence invalidate true single-stream coefficient labels.",
            "allowed_claim": "Use section-effective or diagnostic labels for current recirculating spans.",
            "forbidden_claim": "Promote recirculating test-section/upcomer rows to true Nu, f_D, or component K fits.",
        },
        {
            "claim_id": "hybrid_lane_needed",
            "decision": "future_model_should_be_hybrid_upcomer_lane",
            "evidence_count": counts.get("recirculating_upcomer_effective", 0),
            "scientific_interpretation": "The next model should distinguish ordinary pipe, transition, and recirculating upcomer behavior.",
            "allowed_claim": "A hybrid upcomer lane is the scientifically honest next model form.",
            "forbidden_claim": "A single global multiplier or hidden F6/K term is a recirculation model.",
        },
    ]


def source_manifest_rows() -> list[dict[str, Any]]:
    return [
        {
            "source_id": key,
            "path": rel(path),
            "exists": path.exists(),
            "role": "input_evidence" if path.exists() else "missing_input",
        }
        for key, path in SOURCES.items()
    ]


def write_decision_note(path: Path, summary: dict[str, Any]) -> None:
    text = f"""# Recirculation Feature Admission And Hybrid 1D Contract

Generated: `{summary['generated_at']}`

## Decision

Current evidence does not admit a predictive recirculation model for the 1D
solver. It does admit a stronger rule: material upcomer/test-section
recirculation blocks ordinary single-stream `Nu`, `f_D`, and component `K`
labels.

## Current Evidence

- Feature/admission rows consolidated: `{summary['feature_rows']}`.
- Rows allowing ordinary single-stream fit today: `{summary['single_stream_allowed_rows']}`.
- Recirculating/effective-lane rows: `{summary['recirculating_lane_rows']}`.
- Future evidence queue rows: `{summary['queue_rows']}`.

## Thesis-Safe Claim

Say that the current admitted upcomer/test-section evidence is a recirculating
mixed-convection regime and therefore a validity boundary for ordinary 1D
closures. The next predictive model should use a named hybrid upcomer lane with
ordinary-pipe, transition, and recirculating-section states.

## Do Not Claim

Do not claim a calibrated transferable recirculation closure, ordinary upcomer
`Nu`, ordinary upcomer `f_D`, or component `K` from the current rows. Do not hide
recirculation in a global friction multiplier.
"""
    path.write_text(text, encoding="utf-8")


def write_readme(path: Path, summary: dict[str, Any]) -> None:
    text = f"""---
provenance:
  - {rel(F6_SCORECARD)}
  - {rel(UPCOMER_ONSET)}
  - {rel(HYBRID_LANE)}
  - {rel(M3TS_CONTRACT)}
tags: [recirculation, upcomer, predictive-1d, admission, hybrid-model]
related:
  - .agent/status/2026-07-16_AGENT-467.md
  - .agent/journal/2026-07-16/recirc-feature-admission-and-hybrid-contract.md
task: {TASK}
date: {DATE}
role: Hydraulics/Upcomer-onset/Implementer/Tester/Writer
type: work_product
status: complete
---
# Recirculation Feature Admission And Hybrid Contract

Generated: `{summary['generated_at']}`

## Decision

Current evidence does not admit a predictive recirculation model. It does admit
the coefficient-naming rule: material recirculation invalidates ordinary
single-stream `Nu`, `f_D`, and component `K` fits for the current upcomer and
test-section rows.

## Outputs

- `recirculation_feature_admission_table.csv`
- `hybrid_1d_model_contract.csv`
- `next_extraction_queue.csv`
- `recirculation_decision_table.csv`
- `decision_note.md`
- `source_manifest.csv`
- `summary.json`

## Counts

- Feature/admission rows: `{summary['feature_rows']}`.
- Ordinary single-stream fit rows allowed today: `{summary['single_stream_allowed_rows']}`.
- Recirculating/effective-lane rows: `{summary['recirculating_lane_rows']}`.
- Queue rows: `{summary['queue_rows']}`.

## Guardrails

No native CFD outputs, registry/admission state, scheduler state, blocker files,
generated index files, OpenFOAM jobs, Fluid source, or external paths were
mutated.
"""
    path.write_text(text, encoding="utf-8")


def build_package(output_dir: Path = OUT) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    for source_id, path in SOURCES.items():
        if not path.exists():
            raise FileNotFoundError(f"required source {source_id} missing: {rel(path)}")

    features = feature_rows()
    contracts = contract_rows()
    queue = queue_rows()
    decisions = decision_rows(features)
    manifest = source_manifest_rows()

    recirculating = sum(1 for row in features if row["canonical_lane"] == "recirculating_upcomer_effective")
    allowed = sum(1 for row in features if row["single_stream_fit_allowed"] == "yes")
    summary = {
        "task": TASK,
        "generated_at": utc_now(),
        "feature_rows": write_csv(output_dir / "recirculation_feature_admission_table.csv", features, FEATURE_COLUMNS),
        "contract_rows": write_csv(output_dir / "hybrid_1d_model_contract.csv", contracts, CONTRACT_COLUMNS),
        "queue_rows": write_csv(output_dir / "next_extraction_queue.csv", queue, QUEUE_COLUMNS),
        "decision_rows": write_csv(output_dir / "recirculation_decision_table.csv", decisions, DECISION_COLUMNS),
        "source_rows": write_csv(output_dir / "source_manifest.csv", manifest, MANIFEST_COLUMNS),
        "single_stream_allowed_rows": allowed,
        "recirculating_lane_rows": recirculating,
        "ordinary_coefficient_claim": "not_admitted",
        "hybrid_lane_contract": "published",
        "runtime_or_native_mutation": "none",
    }
    write_decision_note(output_dir / "decision_note.md", summary)
    write_readme(output_dir / "README.md", summary)
    write_json(output_dir / "summary.json", summary)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=OUT)
    args = parser.parse_args()
    summary = build_package(args.output_dir)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
