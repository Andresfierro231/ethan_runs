#!/usr/bin/env python3
"""Build a pressure unblock inventory for low-recirculation/F6 anchors.

This reducer consumes existing evidence only. It keeps the lower-right two-tap
rows as section-effective residual evidence and asks what would have to pass
before any F3/F6/Shah comparison can be reopened.
"""

from __future__ import annotations

import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.common import WORKSPACE_ROOT, csv_dump, ensure_dir, iso_timestamp, json_dump, relative_to_workspace


TASK_ID = "TODO-PRESSURE-LOW-RECIRC-NONRECIRC-ANCHOR-INVENTORY-2026-07-22"
OUT = WORKSPACE_ROOT / (
    "work_products/2026-07/2026-07-22/"
    "2026-07-22_pressure_low_recirc_nonrecirc_anchor_inventory"
)

SOURCES = {
    "non_upcomer": WORKSPACE_ROOT
    / "work_products/2026-07/2026-07-20/2026-07-20_f6_non_upcomer_branch_modeling_analysis",
    "raw_face": WORKSPACE_ROOT
    / "work_products/2026-07/2026-07-21/2026-07-21_f6_endpoint_raw_face_sampler",
    "basis_ladder": WORKSPACE_ROOT
    / "work_products/2026-07/2026-07-22/2026-07-22_thesis_study_pressure_basis_ladder_evidence_packet",
    "source_recovery": WORKSPACE_ROOT
    / "work_products/2026-07/2026-07-22/2026-07-22_thesis_study_pressure_f6_source_recovery_low_recirc_anchors",
}


def rel(path: Path) -> str:
    return relative_to_workspace(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def require_sources() -> None:
    required = [
        SOURCES["non_upcomer"] / "non_upcomer_f6_candidate_matrix.csv",
        SOURCES["non_upcomer"] / "same_qoi_uq_requirements.csv",
        SOURCES["non_upcomer"] / "f3_vs_branch_f6_gate.csv",
        SOURCES["raw_face"] / "ordinary_flow_gate.csv",
        SOURCES["raw_face"] / "stage_a_endpoint_face_matrix.csv",
        SOURCES["basis_ladder"] / "summary.json",
        SOURCES["basis_ladder"] / "section_effective_residual_values.csv",
        SOURCES["source_recovery"] / "summary.json",
        SOURCES["source_recovery"] / "pressure_basis_ladder_update.csv",
    ]
    missing = [rel(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("missing pressure sources: " + "; ".join(missing))


def anchor_inventory() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    candidates = read_csv(SOURCES["non_upcomer"] / "non_upcomer_f6_candidate_matrix.csv")
    flow_rows = read_csv(SOURCES["raw_face"] / "ordinary_flow_gate.csv")
    flow_by_case_branch: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for flow in flow_rows:
        flow_by_case_branch[(flow["case_id"], flow["branch"])].append(flow)

    for row in candidates:
        key = (row["case_key"], row["leg_id"])
        sampled_flow = flow_by_case_branch.get(key, [])
        ordinary_flow_pass = bool(sampled_flow) and all(item["ordinary_flow_gate"] == "pass" for item in sampled_flow)
        max_raf = max((float(item["RAF"]) for item in sampled_flow), default=None)
        max_rmf = max((float(item["RMF"]) for item in sampled_flow), default=None)
        is_preferred_future_anchor = row["candidate_bucket"] == "ordinary_f6_candidate"
        endpoint_ready = row["endpoint_pressure_status"].startswith("pass") and row["endpoint_velocity_status"].startswith("pass")
        uq_ready = row["mesh_uq_status"].startswith("pass") and row["time_uq_status"].startswith("pass")
        source_ready = row["source_property_label_status"].startswith("pass")
        fit_ready = is_preferred_future_anchor and ordinary_flow_pass and endpoint_ready and uq_ready and source_ready
        blocker_fields = [
            name
            for name, passed in [
                ("ordinary_flow", ordinary_flow_pass),
                ("finite_raw_endpoint_pair", endpoint_ready),
                ("same_qoi_mesh_time_uq", uq_ready),
                ("source_property_label", source_ready),
                ("ordinary_branch_slot", is_preferred_future_anchor),
            ]
            if not passed
        ]
        rows.append(
            {
                "candidate_id": row["row_id"],
                "case_id": row["case_key"],
                "branch": row["leg_id"],
                "candidate_bucket": row["candidate_bucket"],
                "leg_class": row["leg_class"],
                "preferred_future_anchor": is_preferred_future_anchor,
                "sampled_endpoint_rows_now": len(sampled_flow),
                "max_RAF_sampled_now": "" if max_raf is None else max_raf,
                "max_RMF_sampled_now": "" if max_rmf is None else max_rmf,
                "ordinary_flow_pass_now": ordinary_flow_pass,
                "endpoint_pair_ready_now": endpoint_ready,
                "same_qoi_uq_ready_now": uq_ready,
                "source_property_labels_available": source_ready,
                "f6_fit_ready_now": fit_ready,
                "f3_f6_revisit_allowed_now": False,
                "primary_blockers": ";".join(blocker_fields),
                "next_unblock_action": next_action(row, sampled_flow),
                "claim_boundary": "no F6/component-K/F3-Shah comparison until all gate columns pass",
                "source_paths": row["source_paths"] + ";" + rel(SOURCES["raw_face"] / "ordinary_flow_gate.csv"),
            }
        )
    return rows


def next_action(row: dict[str, str], sampled_flow: list[dict[str, str]]) -> str:
    if row["candidate_bucket"] != "ordinary_f6_candidate":
        return "keep_out_of_ordinary_F6; use only as diagnostic or future separate model-form lane"
    if sampled_flow and any(item["ordinary_flow_gate"] == "fail" for item in sampled_flow):
        return "do_not_fit; find lower-recirculation or forced/alternate branch anchor before endpoint/UQ scoring"
    if "blocked_missing_raw_endpoint_pair" in {
        row["endpoint_pressure_status"],
        row["endpoint_velocity_status"],
        row["same_window_status"],
    }:
        return "claim exact raw endpoint sampler row only after terminal source cases and paths are ready"
    if row["mesh_uq_status"].startswith("blocked") or row["time_uq_status"].startswith("blocked"):
        return "build same-label same-formula same-sign mesh/time UQ family"
    return "hold for formal admission row"


def sampled_flow_gate() -> list[dict[str, Any]]:
    out = []
    for row in read_csv(SOURCES["raw_face"] / "ordinary_flow_gate.csv"):
        out.append(
            {
                "case_id": row["case_id"],
                "mesh_level": row["mesh_level"],
                "branch": row["branch"],
                "endpoint_pair": row["endpoint_pair"],
                "station_label": row["station_label"],
                "RAF": row["RAF"],
                "RMF": row["RMF"],
                "RAF_limit": row["RAF_limit"],
                "RMF_limit": row["RMF_limit"],
                "ordinary_flow_gate": row["ordinary_flow_gate"],
                "fit_gate_effect": row["fit_gate_effect"],
                "interpretation": "sampled medium/fine rows are useful diagnostics but fail ordinary-flow anchor gate",
            }
        )
    return out


def f3_f6_gate(summary: dict[str, Any], source_summary: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "gate": "lower_right_two_tap_component_K",
            "status": "closed_section_effective_only",
            "evidence": f"{summary['section_effective_rows']} section-effective rows; {summary['component_k_admitted_rows']} component-K rows",
            "release_allowed": False,
            "next_required": "none for component-K; keep as Delta_p_recirc_section diagnostic evidence",
        },
        {
            "gate": "ordinary_low_recirc_anchor",
            "status": "blocked",
            "evidence": f"{source_summary['low_recirc_anchor_rows']} low-recirc candidates but {source_summary['ordinary_candidate_pairs']} ordinary candidate pairs ready",
            "release_allowed": False,
            "next_required": "terminal source case plus finite endpoint fields with RAF/RMF below 0.01",
        },
        {
            "gate": "same_qoi_pressure_uq",
            "status": "blocked",
            "evidence": f"{source_summary['same_qoi_mesh_uq_admissible_rows']} same-QOI admissible mesh/UQ rows",
            "release_allowed": False,
            "next_required": "same-label same-formula same-sign mesh/time UQ family for the same pressure residual QOI",
        },
        {
            "gate": "F3_F6_Shah_numeric_comparison",
            "status": "closed",
            "evidence": f"{summary['admitted_f6_rows']} admitted F6 rows; released={summary['f3_f6_numeric_comparison_released']}",
            "release_allowed": False,
            "next_required": "at least one ordinary anchor with endpoint, UQ, source/property, and split-safe admission gates",
        },
    ]


def next_unblock_queue() -> list[dict[str, Any]]:
    source_summary = read_json(SOURCES["source_recovery"] / "summary.json")
    return [
        {
            "priority": 1,
            "action": "monitor_CAND001_terminal_disposition",
            "current_status": f"job {source_summary['job_id_checked']} observed {source_summary['job_state_observed']} in read-only prior packet",
            "allowed_now": False,
            "unlock_signal": "terminal successful source cases with required endpoint fields",
            "forbidden_shortcut": "duplicate submit, harvest while running, or treat running state as terminal evidence",
        },
        {
            "priority": 2,
            "action": "search_right_leg_or_test_section_low_reverse_anchor",
            "current_status": "preferred ordinary branches exist but sampled medium/fine RAF/RMF fail",
            "allowed_now": True,
            "unlock_signal": "RAF < 0.01 and RMF < 0.01 at both endpoint stations",
            "forbidden_shortcut": "use lower-right recirculating corner rows as ordinary F6",
        },
        {
            "priority": 3,
            "action": "same_QOI_mesh_time_UQ_family",
            "current_status": "requirements defined but no admissible family for current candidate pressure residual",
            "allowed_now": False,
            "unlock_signal": "numeric same-QOI UQ bound for same labels/formula/sign convention",
            "forbidden_shortcut": "borrow corner/upcomer UQ or mix pressure bases",
        },
        {
            "priority": 4,
            "action": "revisit_F3_F6_Shah_comparison",
            "current_status": "closed",
            "allowed_now": False,
            "unlock_signal": "ordinary anchor passes endpoint, flow, UQ, source/property, and admission rows",
            "forbidden_shortcut": "fit F6 or component K from diagnostic residuals",
        },
    ]


def source_manifest() -> list[dict[str, str]]:
    return [
        {"source_id": key, "path": rel(path), "mutation": "read_only", "role": "evidence source"}
        for key, path in SOURCES.items()
    ]


def no_mutation_guardrails() -> list[dict[str, Any]]:
    return [
        {"guardrail": "native_output_mutation", "value": False},
        {"guardrail": "registry_or_admission_mutation", "value": False},
        {"guardrail": "scheduler_action", "value": False},
        {"guardrail": "solver_postprocessing_sampler_harvest_uq_launched", "value": False},
        {"guardrail": "fitting_or_model_selection", "value": False},
        {"guardrail": "component_K_or_F6_admission", "value": False},
        {"guardrail": "F3_F6_Shah_numeric_comparison_released", "value": False},
        {"guardrail": "lower_right_component_K_promotion", "value": False},
    ]


def write_readme(out: Path, summary: dict[str, Any]) -> None:
    text = f"""---
provenance:
  - {rel(SOURCES['non_upcomer'] / 'non_upcomer_f6_candidate_matrix.csv')}
  - {rel(SOURCES['raw_face'] / 'ordinary_flow_gate.csv')}
  - {rel(SOURCES['basis_ladder'] / 'summary.json')}
tags: [pressure, f6, nonrecirculating-anchor, section-effective, no-admission]
related:
  - .agent/status/2026-07-22_{TASK_ID}.md
  - .agent/journal/2026-07-22/pressure-low-recirc-nonrecirc-anchor-inventory.md
  - imports/2026-07-22_pressure_low_recirc_nonrecirc_anchor_inventory.json
task: {TASK_ID}
date: 2026-07-22
role: Hydraulics/Implementer/Tester/Writer/Reviewer
type: work_product
status: complete
---
# Pressure Low-Recirculation / Nonrecirculating Anchor Inventory

Decision: `{summary['decision']}`.

This package advances the pressure unblock by ranking admissible-anchor
requirements before any F3/F6/Shah comparison. It preserves lower-right two-tap
pressure as section-effective residual evidence only.

Key counts:

- candidate rows reviewed: `{summary['candidate_rows_reviewed']}`
- preferred future ordinary anchor rows: `{summary['preferred_future_anchor_rows']}`
- sampled endpoint ordinary-flow pass rows: `{summary['sampled_endpoint_ordinary_flow_pass_rows']}`
- F6 fit-ready rows now: `{summary['f6_fit_ready_rows']}`
- lower-right section-effective rows preserved: `{summary['lower_right_section_effective_rows_preserved']}`

Primary outputs:

- `anchor_inventory_gate.csv`
- `sampled_endpoint_ordinary_flow_gate.csv`
- `f3_f6_shah_revisit_gate.csv`
- `next_unblock_queue.csv`
- `source_manifest.csv`
- `no_mutation_guardrails.csv`
- `summary.json`

No scheduler action, sampler/harvest/UQ launch, native-output mutation, fitting,
component-K admission, F6 admission, clipped K, hidden multiplier, or F3/F6/Shah
numeric comparison occurred.
"""
    (out / "README.md").write_text(text, encoding="utf-8")


def build(out: Path = OUT) -> dict[str, Any]:
    require_sources()
    ensure_dir(out)
    inventory = anchor_inventory()
    flow = sampled_flow_gate()
    basis_summary = read_json(SOURCES["basis_ladder"] / "summary.json")
    source_summary = read_json(SOURCES["source_recovery"] / "summary.json")
    revisit_gate = f3_f6_gate(basis_summary, source_summary)
    queue = next_unblock_queue()

    csv_dump(out / "anchor_inventory_gate.csv", list(inventory[0].keys()), inventory)
    csv_dump(out / "sampled_endpoint_ordinary_flow_gate.csv", list(flow[0].keys()), flow)
    csv_dump(out / "f3_f6_shah_revisit_gate.csv", list(revisit_gate[0].keys()), revisit_gate)
    csv_dump(out / "next_unblock_queue.csv", list(queue[0].keys()), queue)
    csv_dump(out / "source_manifest.csv", ["source_id", "path", "mutation", "role"], source_manifest())
    guardrails = no_mutation_guardrails()
    csv_dump(out / "no_mutation_guardrails.csv", ["guardrail", "value"], guardrails)

    by_bucket = Counter(row["candidate_bucket"] for row in inventory)
    summary = {
        "task_id": TASK_ID,
        "generated_at": iso_timestamp(),
        "decision": "pressure_anchor_inventory_ready_no_f6_revisit_yet",
        "candidate_rows_reviewed": len(inventory),
        "preferred_future_anchor_rows": sum(row["preferred_future_anchor"] for row in inventory),
        "candidate_rows_by_bucket": dict(sorted(by_bucket.items())),
        "sampled_endpoint_rows_reviewed": len(flow),
        "sampled_endpoint_ordinary_flow_pass_rows": sum(row["ordinary_flow_gate"] == "pass" for row in flow),
        "sampled_endpoint_ordinary_flow_fail_rows": sum(row["ordinary_flow_gate"] == "fail" for row in flow),
        "f6_fit_ready_rows": sum(row["f6_fit_ready_now"] for row in inventory),
        "same_qoi_uq_ready_rows": sum(row["same_qoi_uq_ready_now"] for row in inventory),
        "endpoint_pair_ready_rows": sum(row["endpoint_pair_ready_now"] for row in inventory),
        "source_property_label_available_rows": sum(row["source_property_labels_available"] for row in inventory),
        "lower_right_section_effective_rows_preserved": basis_summary["section_effective_rows"],
        "component_k_admitted_rows": 0,
        "f6_fit_rows": 0,
        "f3_f6_shah_numeric_comparison_released": False,
        "scheduler_action": False,
        "solver_postprocessing_sampler_harvest_uq_launched": False,
        "native_output_mutation": False,
        "registry_or_admission_mutation": False,
        "fitting_or_model_selection": False,
        "candidate_freeze": False,
    }
    json_dump(out / "summary.json", summary)
    write_readme(out, summary)
    return summary


def main() -> None:
    summary = build()
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
