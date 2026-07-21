#!/usr/bin/env python3
"""Refresh the two-tap lower-right nonrecirculating same-QOI anchor request."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DATE = "2026-07-20"
TASK = "TODO-TWO-TAP-NONRECIRCULATING-SAME-QOI-ANCHOR-REQUEST-REFRESH"
OUT = ROOT / "work_products/2026-07/2026-07-20/2026-07-20_two_tap_nonrecirculating_same_qoi_anchor_request_refresh"
PRIOR = ROOT / "work_products/2026-07/2026-07-18/2026-07-18_two_tap_nonrecirc_anchor_request"
REPAIR = ROOT / "work_products/2026-07/2026-07-20/2026-07-20_two_tap_corner_lower_right_admission_repair"
ISOLATION = ROOT / "work_products/2026-07/2026-07-20/2026-07-20_two_tap_corner_lower_right_isolation_uq_progress"
STATUS = ROOT / ".agent/status/2026-07-20_TODO-TWO-TAP-NONRECIRCULATING-SAME-QOI-ANCHOR-REQUEST-REFRESH.md"
JOURNAL = ROOT / ".agent/journal/2026-07-20/two-tap-nonrecirculating-same-qoi-anchor-request-refresh.md"
IMPORT = ROOT / "imports/2026-07-20_two_tap_nonrecirculating_same_qoi_anchor_request_refresh.json"

FEATURE = "corner_lower_right"
UPSTREAM_LABEL = "lower_leg__s04"
DOWNSTREAM_LABEL = "right_leg__s00"
ENDPOINT_PAIR = f"{UPSTREAM_LABEL}->{DOWNSTREAM_LABEL}"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = []
        for row in rows:
            for field in row:
                if field not in fieldnames:
                    fieldnames.append(field)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def require_sources() -> None:
    required = [
        PRIOR / "nonrecirculating_anchor_request.csv",
        PRIOR / "launch_gate_contract.csv",
        REPAIR / "endpoint_reverse_flow_gate.csv",
        ISOLATION / "component_k_decision.csv",
        ISOLATION / "same_qoi_time_uq.csv",
        ISOLATION / "same_qoi_mesh_uq.csv",
    ]
    missing = [rel(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing two-tap anchor refresh sources: " + "; ".join(missing))


def build_anchor_request() -> list[dict[str, Any]]:
    prior_rows = read_csv(PRIOR / "nonrecirculating_anchor_request.csv")
    prior = next((row for row in prior_rows if row.get("feature") == FEATURE), prior_rows[0])
    return [
        {
            "request_id": "NR-CLR-SAME-QOI-2026-07-20",
            "feature": FEATURE,
            "request_type": "nonrecirculating_same_qoi_anchor",
            "target": prior.get("target", "same corner_lower_right topology at a non-recirculating operating point"),
            "required_endpoint_pair": ENDPOINT_PAIR,
            "required_endpoint_labels": f"{UPSTREAM_LABEL};{DOWNSTREAM_LABEL}",
            "pressure_basis_primary": "static_p_pa",
            "pressure_basis_cross_check": "p_rgh_with_documented_hydrostatic_conversion",
            "required_fields": "p;p_rgh;U;rho;mu;T;face_area;face_normal;RAF;RMF;Delta_p;K_app",
            "acceptance_signal": "RAF < 0.01 and RMF < 0.01 at both endpoint planes with same retained window",
            "current_rows_use": "diagnostic_apparent_cluster_loss_only",
            "component_k_release_policy": "blocked_until_nonrecirculating_same_qoi_time_and_mesh_UQ",
            "auto_submit": "false",
            "source_path": rel(PRIOR / "nonrecirculating_anchor_request.csv"),
        }
    ]


def build_sampling_contract() -> list[dict[str, Any]]:
    formulas = [
        ("Delta_p", "p_upstream_minus_p_downstream", "static_p_pa_primary"),
        ("K_app", "Delta_p_over_half_rho_Ubulk_squared", "same_sign_as_Delta_p_no_make_positive"),
        ("RAF", "reverse_area_fraction_endpoint_plane", "ordinary_reverse_flow_gate"),
        ("RMF", "reverse_mass_fraction_endpoint_plane", "ordinary_reverse_flow_gate"),
    ]
    return [
        {
            "feature": FEATURE,
            "endpoint_pair": ENDPOINT_PAIR,
            "qoi": qoi,
            "formula": formula,
            "pressure_or_flow_basis": basis,
            "retained_time_window": "same_window_as_candidate_endpoint_sampling",
            "mesh_family_requirement": "same endpoint labels and same formula on coarse/medium/fine where available",
            "sign_convention": "p_upstream_minus_p_downstream",
            "clipping_policy": "reject_nonphysical_no_make_positive_correction",
        }
        for qoi, formula, basis in formulas
    ]


def build_uq_requirements() -> list[dict[str, Any]]:
    time_rows = read_csv(ISOLATION / "same_qoi_time_uq.csv")
    mesh_rows = read_csv(ISOLATION / "same_qoi_mesh_uq.csv")
    return [
        {
            "requirement_id": "same_label_same_formula_same_sign",
            "status": "required_future",
            "current_evidence_status": "blocked_current_rows_not_admissible",
            "minimum_acceptance": f"all QOIs use {ENDPOINT_PAIR}, static p, same sign convention",
            "source_path": rel(ISOLATION / "component_k_decision.csv"),
        },
        {
            "requirement_id": "time_window_uq",
            "status": "required_future",
            "current_evidence_status": (
                "available" if any(row.get("time_uq_status") == "available_same_window_neighbors" for row in time_rows)
                else "missing_no_same_window_neighbors"
            ),
            "minimum_acceptance": "at least one same-label same-formula retained-window neighbor family per candidate row",
            "source_path": rel(ISOLATION / "same_qoi_time_uq.csv"),
        },
        {
            "requirement_id": "mesh_uq",
            "status": "required_future",
            "current_evidence_status": (
                "available" if any(row.get("mesh_uq_status") != "missing_no_GCI_not_same_qoi" for row in mesh_rows)
                else "missing_no_GCI_not_same_qoi"
            ),
            "minimum_acceptance": "Salt2 coarse/medium/fine same-QOI family or explicit blocked mesh-UQ missing decision",
            "source_path": rel(ISOLATION / "same_qoi_mesh_uq.csv"),
        },
    ]


def build_launch_gate() -> list[dict[str, Any]]:
    repair_split = read_csv(REPAIR / "split_decision.csv")
    blocked_rows = sum(row.get("component_k_admitted") == "false" for row in repair_split)
    return [
        {
            "gate": "ordinary_flow",
            "requirement": "RAF < 0.01 and RMF < 0.01 at lower_leg__s04 and right_leg__s00",
            "current_status": "required_future",
            "launch_status": "not_submitted",
            "guardrail": "current reverse-flow rows remain diagnostic",
        },
        {
            "gate": "component_isolation",
            "requirement": "subtract straight/development loss on same Re/rho/mu/window/sign basis",
            "current_status": "blocked_current_component_k_rows" if blocked_rows else "available",
            "launch_status": "not_submitted",
            "guardrail": "no clipping and no make-positive correction",
        },
        {
            "gate": "same_qoi_uq",
            "requirement": "same endpoint labels, formulas, sign convention, retained window, and mesh family where available",
            "current_status": "required_future",
            "launch_status": "not_submitted",
            "guardrail": "do not borrow section-mean or proxy pressure GCI",
        },
    ]


def build_source_manifest() -> list[dict[str, Any]]:
    sources = [
        (PRIOR / "nonrecirculating_anchor_request.csv", "prior anchor request"),
        (PRIOR / "launch_gate_contract.csv", "prior launch gates"),
        (REPAIR / "endpoint_reverse_flow_gate.csv", "reverse-flow blocker evidence"),
        (ISOLATION / "component_k_decision.csv", "component-K split decision"),
        (ISOLATION / "same_qoi_time_uq.csv", "time UQ status"),
        (ISOLATION / "same_qoi_mesh_uq.csv", "mesh UQ status"),
    ]
    return [
        {
            "source_id": path.name,
            "source_path": rel(path),
            "exists": "yes" if path.exists() else "no",
            "source_role": role,
            "mutation": "read_only",
        }
        for path, role in sources
    ]


def write_readme(summary: dict[str, Any]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "README.md").write_text(
        "\n".join(
            [
                "# Two-Tap Nonrecirculating Same-QOI Anchor Request Refresh",
                "",
                "This package refreshes the launch-ready evidence request for lower-right two-tap component-K admission.",
                "It does not submit new jobs.",
                "",
                "Primary outputs:",
                "",
                "- `anchor_request.csv`",
                "- `sampling_contract.csv`",
                "- `uq_requirements.csv`",
                "- `launch_gate.csv`",
                "- `source_manifest.csv`",
                "- `summary.json`",
                "",
                f"Endpoint pair: `{ENDPOINT_PAIR}`.",
                f"Auto-submit: {summary['auto_submit']}.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def write_status_files(summary: dict[str, Any]) -> None:
    STATUS.parent.mkdir(parents=True, exist_ok=True)
    STATUS.write_text(
        "\n".join(
            [
                f"# {TASK}",
                "",
                "- status: complete",
                f"- endpoint_pair: {ENDPOINT_PAIR}",
                f"- auto_submit: {summary['auto_submit']}",
                f"- output: {rel(OUT)}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    JOURNAL.parent.mkdir(parents=True, exist_ok=True)
    JOURNAL.write_text(
        "\n".join(
            [
                f"# {DATE} two-tap same-QOI anchor request refresh",
                "",
                "Refreshed nonrecirculating same-QOI evidence contract for corner lower-right two-tap component-K admission.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    write_json(
        IMPORT,
        {
            "task": TASK,
            "date": DATE,
            "output_dir": rel(OUT),
            "native_solver_outputs_mutated": False,
            "generated_index_refreshed": False,
            "summary_path": rel(OUT / "summary.json"),
        },
    )


def main() -> dict[str, Any]:
    require_sources()
    anchor = build_anchor_request()
    sampling = build_sampling_contract()
    uq = build_uq_requirements()
    launch = build_launch_gate()
    sources = build_source_manifest()
    summary = {
        "task": TASK,
        "date": DATE,
        "generated_at_utc": utc_now(),
        "feature": FEATURE,
        "endpoint_pair": ENDPOINT_PAIR,
        "anchor_request_rows": len(anchor),
        "sampling_contract_rows": len(sampling),
        "uq_requirement_rows": len(uq),
        "launch_gate_rows": len(launch),
        "auto_submit": False,
        "component_k_current_status": "blocked_current_rows_diagnostic_only",
        "native_solver_outputs_mutated": False,
        "registry_mutation": "none",
    }

    write_csv(OUT / "anchor_request.csv", anchor)
    write_csv(OUT / "sampling_contract.csv", sampling)
    write_csv(OUT / "uq_requirements.csv", uq)
    write_csv(OUT / "launch_gate.csv", launch)
    write_csv(OUT / "source_manifest.csv", sources)
    write_json(OUT / "summary.json", summary)
    write_readme(summary)
    write_status_files(summary)
    return summary


if __name__ == "__main__":
    print(json.dumps(main(), indent=2, sort_keys=True))
