#!/usr/bin/env python3
"""Build AGENT-523 named pressure-loss extraction readiness package."""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


TASK = "AGENT-523"
DATE = "2026-07-17"
ROOT = Path(__file__).resolve().parents[2]
OUT_REL = Path("work_products/2026-07/2026-07-17/2026-07-17_named_pressure_extraction_readiness")
OUT = ROOT / OUT_REL

LITREV_RESET_DIR = ROOT / "work_products/2026-07/2026-07-13/2026-07-13_litrev_reset_named_losses"
GATE_DIR = ROOT / "work_products/2026-07/2026-07-17/2026-07-17_litrev_gate_carryforward_ledger"
SEG_PRESSURE_DIR = ROOT / "work_products/2026-07/2026-07-17/2026-07-17_predict_segment_pressure_models"
F6_DIR = ROOT / "work_products/2026-07/2026-07-17/2026-07-17_f6_litrev_hydraulic_model_form_ladder"
VAL_DIR = ROOT / "work_products/2026-07/2026-07-17/2026-07-17_val_salt2_pressure_evidence_corner_k_diagnosis"

SOURCES = {
    "named_pressure_loss_table": LITREV_RESET_DIR / "named_pressure_loss_table.csv",
    "reset_distance_map": LITREV_RESET_DIR / "reset_distance_map.csv",
    "target_package_gate_contract": GATE_DIR / "target_package_gate_contract.csv",
    "branch_gate_carryforward_summary": GATE_DIR / "branch_gate_carryforward_summary.csv",
    "segment_pressure_model_scorecard": SEG_PRESSURE_DIR / "segment_pressure_model_scorecard.csv",
    "pressure_model_slot_admission": SEG_PRESSURE_DIR / "pressure_model_slot_admission.csv",
    "pressure_evidence_rollup": SEG_PRESSURE_DIR / "pressure_evidence_rollup.csv",
    "hydraulic_model_form_ladder": F6_DIR / "hydraulic_model_form_ladder.csv",
    "corner_k_gate_matrix": VAL_DIR / "corner_k_gate_matrix.csv",
    "next_pressure_evidence_queue": VAL_DIR / "next_pressure_evidence_queue.csv",
}

ROW_COLUMNS = [
    "row_id",
    "case_id",
    "name",
    "loss_class",
    "span_or_feature",
    "pressure_basis",
    "velocity_basis",
    "fit_use_status",
    "coefficient_naming_status",
    "readiness_status",
    "blocking_fields",
    "priority",
    "recommended_next_action",
    "allowed_use_now",
    "forbidden_use",
    "source_path",
]

QUEUE_COLUMNS = [
    "priority",
    "queue_item",
    "target_rows",
    "why",
    "required_fields",
    "acceptance_gate",
    "unblocks",
    "guardrail",
    "source_paths",
]

SUMMARY_COLUMNS = ["category", "count", "interpretation"]
MANIFEST_COLUMNS = ["source_id", "path", "exists", "role"]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT.resolve()))
    except ValueError:
        return str(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: Iterable[dict[str, Any]], columns: list[str]) -> int:
    materialized = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in materialized:
            writer.writerow({column: "" if row.get(column) is None else str(row.get(column, "")) for column in columns})
    return len(materialized)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def require_sources() -> None:
    missing = [rel(path) for path in SOURCES.values() if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing AGENT-523 source files: " + ", ".join(missing))


def finite(value: str) -> bool:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return False
    return math.isfinite(number)


def classify_named_row(row: dict[str, str]) -> tuple[str, list[str], int, str]:
    blockers: list[str] = []
    quality = row.get("quality_flags", "")
    if row.get("fit_use_status") != "fit_target":
        blockers.append("not_fit_status")
    if "recirculation" in quality or row.get("coefficient_naming_status") == "reject_universal_name":
        blockers.append("recirculation_or_universal_name_rejected")
    if "coarse_no_gci" in quality:
        blockers.append("same_qoi_mesh_gci_missing")
    if "tap_length_proxy_abs_dz_not_centerline_length" in quality:
        blockers.append("centerline_tap_length_missing")
    if "K_local_still_upper_bound" in quality:
        blockers.append("local_K_upper_bound")
    if "component_K_not_isolated" in quality:
        blockers.append("component_isolation_missing")
    if row.get("loss_class") == "cluster_K" and not finite(row.get("K_local", "")):
        blockers.append("K_local_missing")
    if row.get("loss_class") == "straight_section" and not finite(row.get("f_D_delta_p", "")):
        blockers.append("f_D_delta_p_missing")
    if row.get("pressure_basis", "").startswith("debuoyed_total_pressure_proxy"):
        blockers.append("pressure_basis_proxy_not_final")
    if row.get("velocity_basis", "").startswith("q_ref_pa_from_pressure_ledger") or row.get("velocity_basis") == "mean":
        blockers.append("velocity_basis_needs_final_definition")

    if not blockers:
        return "fit_ready_candidate", [], 1, "Score against F3 with pressure residual primary and mdot guardrail."
    if "recirculation_or_universal_name_rejected" in blockers:
        return "diagnostic_or_section_effective_only", blockers, 4, "Keep section-effective/diagnostic label; wait for low-reverse terminal anchor."
    if row.get("loss_class") in {"cluster_K", "component_K"}:
        return "extraction_required_component_or_cluster", blockers, 2, "Repair tap basis, centerline lengths, straight-loss subtraction, component isolation, and UQ."
    return "extraction_required_branch_or_straight", blockers, 3, "Repair pressure/velocity basis, geometry normalization, straight-loss/development basis, and UQ."


def build_readiness_rows() -> list[dict[str, Any]]:
    rows = []
    for idx, row in enumerate(read_csv(SOURCES["named_pressure_loss_table"]), start=1):
        status, blockers, priority, action = classify_named_row(row)
        rows.append(
            {
                "row_id": f"named_pressure:{idx:03d}",
                "case_id": row["case_id"],
                "name": row["name"],
                "loss_class": row["loss_class"],
                "span_or_feature": row["span_or_feature"],
                "pressure_basis": row["pressure_basis"],
                "velocity_basis": row["velocity_basis"],
                "fit_use_status": row["fit_use_status"],
                "coefficient_naming_status": row["coefficient_naming_status"],
                "readiness_status": status,
                "blocking_fields": ";".join(blockers),
                "priority": priority,
                "recommended_next_action": action,
                "allowed_use_now": "diagnostic_pressure_ledger_or_extraction_design",
                "forbidden_use": "admitted_K_or_f_D; universal_K; hidden_global_friction_multiplier",
                "source_path": rel(SOURCES["named_pressure_loss_table"]),
            }
        )
    return rows


def build_queue(readiness_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    status_counts = Counter(row["readiness_status"] for row in readiness_rows)
    blockers = Counter()
    for row in readiness_rows:
        for blocker in str(row["blocking_fields"]).split(";"):
            if blocker:
                blockers[blocker] += 1
    return [
        {
            "priority": 1,
            "queue_item": "raw_two_tap_connector_and_component_repair",
            "target_rows": status_counts.get("extraction_required_component_or_cluster", 0),
            "why": "Component/cluster rows are the nearest path to named K, but current K values are upper-bound/proxy or missing.",
            "required_fields": "centerline_tap_length;final_pressure_basis;final_velocity_basis;straight_loss_subtraction;component_isolation;same_qoi_mesh_time_UQ",
            "acceptance_gate": "nonnegative local K after straight-loss subtraction with non-recirculating adjacent taps and explicit UQ",
            "unblocks": "named component/cluster K scorecard against F3",
            "guardrail": "do not admit universal K or proxy K_local rows",
            "source_paths": f"{rel(SOURCES['named_pressure_loss_table'])};{rel(SOURCES['corner_k_gate_matrix'])}",
        },
        {
            "priority": 2,
            "queue_item": "pressure_and_velocity_basis_finalization",
            "target_rows": blockers.get("pressure_basis_proxy_not_final", 0),
            "why": "Most current rows use pressure-ledger proxy bases; future score rows need explicit static/hydrostatic/kinetic/straight-loss accounting.",
            "required_fields": "static_pressure_basis;hydrostatic_correction;kinetic_correction;velocity_basis;density_basis;units",
            "acceptance_gate": "basis fields are explicit and no buoyancy/kinetic term is double-counted",
            "unblocks": "branch-apparent and straight-section f_D_delta_p review",
            "guardrail": "do not score coefficients from ambiguous pressure basis",
            "source_paths": f"{rel(SOURCES['target_package_gate_contract'])};{rel(SOURCES['pressure_evidence_rollup'])}",
        },
        {
            "priority": 3,
            "queue_item": "recirculation_mask_and_section_effective_policy",
            "target_rows": blockers.get("recirculation_or_universal_name_rejected", 0),
            "why": "Recirculating rows cannot be ordinary f_D/K rows; they need low-reverse anchors or section-effective/onset labels.",
            "required_fields": "RAF;RMF;SVF;coefficient_naming_limit;ordinary_vs_section_effective_label;steady_window",
            "acceptance_gate": "ordinary rows require RAF < 0.01 and RMF < 0.01; otherwise diagnostic/section-effective only",
            "unblocks": "ordinary F6 gate or recirculation-mode pressure residual analysis",
            "guardrail": "do not export ordinary f_D/K from material reverse-flow sections",
            "source_paths": f"{rel(SOURCES['branch_gate_carryforward_summary'])};{rel(SOURCES['hydraulic_model_form_ladder'])}",
        },
        {
            "priority": 4,
            "queue_item": "same_qoi_mesh_time_uncertainty_attachment",
            "target_rows": blockers.get("same_qoi_mesh_gci_missing", 0),
            "why": "Current named pressure rows are coarse/diagnostic; admission needs same-QOI mesh/time uncertainty.",
            "required_fields": "mesh_family;time_window;pressure_QOI;monotonicity_or_nonGCI_flag;uncertainty_bound",
            "acceptance_gate": "mesh/time uncertainty attached or row remains diagnostic",
            "unblocks": "publication-grade pressure coefficient admission",
            "guardrail": "do not fabricate GCI for non-monotone, two-level, or unavailable data",
            "source_paths": rel(SOURCES["pressure_model_slot_admission"]),
        },
        {
            "priority": 5,
            "queue_item": "reset_development_basis_to_Fluid_API_contract",
            "target_rows": "all reset/development candidates",
            "why": "Reset distance is available but no runtime reset/development pressure API is admitted.",
            "required_fields": "reset_type;L_over_D_from_reset;L_plus_or_development_metric;development_or_recovery_basis;property_mode",
            "acceptance_gate": "reset/development basis can be reproduced in a Fluid scorecard without hidden multiplier",
            "unblocks": "faithful H1/reset-development pressure model implementation",
            "guardrail": "do not assume fully developed flow solely from geometry",
            "source_paths": f"{rel(SOURCES['reset_distance_map'])};{rel(SOURCES['hydraulic_model_form_ladder'])}",
        },
    ]


def build_summary_rows(readiness_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counts = Counter(row["readiness_status"] for row in readiness_rows)
    classes = Counter(row["loss_class"] for row in readiness_rows)
    return [
        {"category": "total_named_pressure_rows", "count": len(readiness_rows), "interpretation": "Rows reviewed from LitRev reset/named-loss table."},
        {"category": "fit_ready_candidate", "count": counts.get("fit_ready_candidate", 0), "interpretation": "Rows with no readiness blockers under AGENT-523 gates."},
        {"category": "component_or_cluster_extraction_required", "count": counts.get("extraction_required_component_or_cluster", 0), "interpretation": "Nearest named-K lane, but extraction fields are missing."},
        {"category": "branch_or_straight_extraction_required", "count": counts.get("extraction_required_branch_or_straight", 0), "interpretation": "Needs pressure/velocity/development/UQ repair before scoring."},
        {"category": "diagnostic_or_section_effective_only", "count": counts.get("diagnostic_or_section_effective_only", 0), "interpretation": "Recirculation/universal-name guardrails block ordinary coefficients."},
        {"category": "loss_class_cluster_K", "count": classes.get("cluster_K", 0), "interpretation": "Cluster/component-like K candidates."},
        {"category": "loss_class_branch_apparent", "count": classes.get("branch_apparent", 0), "interpretation": "Branch-apparent pressure rows."},
        {"category": "loss_class_straight_section", "count": classes.get("straight_section", 0), "interpretation": "Straight-section f_D_delta_p candidates."},
    ]


def build_manifest() -> list[dict[str, Any]]:
    return [{"source_id": key, "path": rel(path), "exists": path.exists(), "role": "read-only readiness source"} for key, path in SOURCES.items()]


def write_readme(path: Path, summary: dict[str, Any]) -> None:
    path.write_text(
        f"""---
provenance:
  - {rel(SOURCES['named_pressure_loss_table'])}
  - {rel(SOURCES['target_package_gate_contract'])}
  - {rel(SOURCES['segment_pressure_model_scorecard'])}
  - {rel(SOURCES['hydraulic_model_form_ladder'])}
tags: [pressure-ledger, named-losses, f6, extraction-readiness]
related:
  - .agent/status/2026-07-17_AGENT-523.md
  - .agent/journal/2026-07-17/named-pressure-extraction-readiness.md
task: {TASK}
date: {DATE}
role: Hydraulics/Implementer/Tester/Writer
type: work_product
status: complete
---
# Named Pressure Extraction Readiness

Generated: `{summary['generated_at_utc']}`

## Decision

No named pressure-loss row is fit-admitted yet. The package ranks what must be
extracted or repaired before F6, reset-development, component/cluster K, or
branch-apparent pressure rows can be scored.

## Outputs

- `named_pressure_readiness.csv`
- `next_pressure_extraction_queue.csv`
- `pressure_readiness_summary.csv`
- `source_manifest.csv`
- `summary.json`

## Counts

- Named pressure rows reviewed: `{summary['named_pressure_rows']}`.
- Fit-ready rows: `{summary['fit_ready_rows']}`.
- Component/cluster extraction-required rows: `{summary['component_or_cluster_extraction_required_rows']}`.
- Branch/straight extraction-required rows: `{summary['branch_or_straight_extraction_required_rows']}`.
- Diagnostic/section-effective rows: `{summary['diagnostic_or_section_effective_rows']}`.

## Guardrails

No native CFD outputs, registry/admission state, scheduler state, external Fluid
files, generated index files, or active-agent scoped artifacts were mutated. This
is an extraction-readiness package, not a pressure coefficient admission, model
fit, solver run, or scheduler action.
""",
        encoding="utf-8",
    )


def build_package(out: Path = OUT) -> dict[str, Any]:
    require_sources()
    out.mkdir(parents=True, exist_ok=True)

    readiness = build_readiness_rows()
    queue = build_queue(readiness)
    summary_rows = build_summary_rows(readiness)
    manifest = build_manifest()
    counts = Counter(row["readiness_status"] for row in readiness)
    summary = {
        "task": TASK,
        "date": DATE,
        "generated_at_utc": utc_now(),
        "output_dir": rel(out),
        "named_pressure_rows": len(readiness),
        "fit_ready_rows": counts.get("fit_ready_candidate", 0),
        "component_or_cluster_extraction_required_rows": counts.get("extraction_required_component_or_cluster", 0),
        "branch_or_straight_extraction_required_rows": counts.get("extraction_required_branch_or_straight", 0),
        "diagnostic_or_section_effective_rows": counts.get("diagnostic_or_section_effective_only", 0),
        "queue_rows": len(queue),
        "summary_rows": len(summary_rows),
        "source_rows": len(manifest),
        "production_closure": "F3_shah_apparent",
        "scientific_admission_change": "none",
        "native_output_mutation": "none",
        "registry_mutation": "none",
        "scheduler_action": "none",
        "external_fluid_edit": "none",
        "generated_index_refresh": "not_run_active_agents_own_generated_index_paths",
    }
    write_csv(out / "named_pressure_readiness.csv", readiness, ROW_COLUMNS)
    write_csv(out / "next_pressure_extraction_queue.csv", queue, QUEUE_COLUMNS)
    write_csv(out / "pressure_readiness_summary.csv", summary_rows, SUMMARY_COLUMNS)
    write_csv(out / "source_manifest.csv", manifest, MANIFEST_COLUMNS)
    write_readme(out / "README.md", summary)
    write_json(out / "summary.json", summary)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args()
    print(json.dumps(build_package(args.out), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
