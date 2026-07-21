#!/usr/bin/env python3
"""Build a launch-readiness package for the lower-right two-tap same-QOI anchor."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DATE = "2026-07-20"
TASK = "TODO-TWO-TAP-SAME-QOI-ANCHOR-LAUNCH-PACKAGE"
OUT = ROOT / "work_products/2026-07/2026-07-20/2026-07-20_two_tap_same_qoi_anchor_launch_package"
ANCHOR = ROOT / "work_products/2026-07/2026-07-20/2026-07-20_two_tap_nonrecirculating_same_qoi_anchor_request_refresh"
ISOLATION = ROOT / "work_products/2026-07/2026-07-20/2026-07-20_two_tap_corner_lower_right_isolation_uq_progress"
STATUS = ROOT / ".agent/status/2026-07-20_TODO-TWO-TAP-SAME-QOI-ANCHOR-LAUNCH-PACKAGE.md"
JOURNAL = ROOT / ".agent/journal/2026-07-20/two-tap-same-qoi-anchor-launch-package.md"
IMPORT = ROOT / "imports/2026-07-20_two_tap_same_qoi_anchor_launch_package.json"

FEATURE = "corner_lower_right"
ENDPOINT_PAIR = "lower_leg__s04->right_leg__s00"


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
    required = [ANCHOR / "anchor_request.csv", ANCHOR / "sampling_contract.csv", ANCHOR / "uq_requirements.csv", ANCHOR / "launch_gate.csv", ISOLATION / "component_k_decision.csv"]
    missing = [rel(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing two-tap launch package sources: " + "; ".join(missing))


def build_staged_copy_case_request() -> list[dict[str, Any]]:
    anchor = read_csv(ANCHOR / "anchor_request.csv")[0]
    return [
        {
            "request_id": anchor["request_id"],
            "feature": FEATURE,
            "endpoint_pair": ENDPOINT_PAIR,
            "source_case_status": "missing_named_nonrecirculating_source_case",
            "staged_copy_status": "blocked",
            "required_operating_point": "nonrecirculating RAF < 0.01 and RMF < 0.01 at both endpoint planes",
            "auto_submit": "false",
            "next_action": "identify or create source case before sbatch generation",
            "source_path": rel(ANCHOR / "anchor_request.csv"),
        }
    ]


def build_endpoint_sampling_contract() -> list[dict[str, Any]]:
    rows = []
    for row in read_csv(ANCHOR / "sampling_contract.csv"):
        rows.append(
            {
                "feature": FEATURE,
                "endpoint_pair": ENDPOINT_PAIR,
                "qoi": row["qoi"],
                "formula": row["formula"],
                "pressure_basis_primary": "static_p_pa",
                "pressure_basis_cross_check": "p_rgh_with_documented_hydrostatic_conversion",
                "sign_convention": "p_upstream_minus_p_downstream",
                "retained_time_window": row["retained_time_window"],
                "clipping_policy": "reject_nonphysical_no_make_positive_correction",
            }
        )
    return rows


def build_nonrecirc_gate_preflight() -> list[dict[str, Any]]:
    launch = {row["gate"]: row for row in read_csv(ANCHOR / "launch_gate.csv")}
    return [
        {
            "gate": "ordinary_flow",
            "required_threshold": "RAF < 0.01 and RMF < 0.01",
            "current_status": launch["ordinary_flow"]["current_status"],
            "preflight_status": "blocked_missing_new_nonrecirculating_source",
            "auto_submit": "false",
        },
        {
            "gate": "component_isolation",
            "required_threshold": "same-basis straight/development subtraction with Re/rho/mu/window/sign",
            "current_status": launch["component_isolation"]["current_status"],
            "preflight_status": "blocked_current_rows_apparent_cluster_only",
            "auto_submit": "false",
        },
    ]


def build_mesh_time_uq_request() -> list[dict[str, Any]]:
    rows = []
    for row in read_csv(ANCHOR / "uq_requirements.csv"):
        rows.append(
            {
                "requirement_id": row["requirement_id"],
                "current_evidence_status": row["current_evidence_status"],
                "request_status": "required_before_component_K_admission",
                "minimum_acceptance": row["minimum_acceptance"],
                "fit_use_before_pass": "forbidden",
            }
        )
    return rows


def build_sbatch_or_manual_launch_plan(preflight: list[dict[str, Any]]) -> list[dict[str, Any]]:
    blocked = any("blocked" in row["preflight_status"] for row in preflight)
    return [
        {
            "launch_plan_id": "two_tap_same_qoi_anchor",
            "launch_ready": str(not blocked).lower(),
            "auto_submit": "false",
            "sbatch_path": "",
            "manual_action": "identify source case and rerun package" if blocked else "review generated sbatch before manual submit",
            "guardrail": "do not submit without exact endpoint labels and nonrecirculating preflight",
        }
    ]


def build_source_manifest() -> list[dict[str, Any]]:
    sources = [
        (ANCHOR / "anchor_request.csv", "anchor request"),
        (ANCHOR / "sampling_contract.csv", "same-QOI sampling contract"),
        (ANCHOR / "uq_requirements.csv", "UQ requirements"),
        (ANCHOR / "launch_gate.csv", "launch gates"),
        (ISOLATION / "component_k_decision.csv", "current component-K decision"),
    ]
    return [{"source_path": rel(path), "exists": "yes" if path.exists() else "no", "source_role": role, "mutation": "read_only"} for path, role in sources]


def write_readme(summary: dict[str, Any]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "README.md").write_text(f"# Two-Tap Same-QOI Anchor Launch Package\n\nLaunch ready: {summary['launch_ready']}. Auto-submit: {summary['auto_submit']}.\n", encoding="utf-8")


def write_status_files(summary: dict[str, Any]) -> None:
    STATUS.parent.mkdir(parents=True, exist_ok=True)
    STATUS.write_text(f"# {TASK}\n\n- status: complete\n- launch_ready: {summary['launch_ready']}\n- output: {rel(OUT)}\n", encoding="utf-8")
    JOURNAL.parent.mkdir(parents=True, exist_ok=True)
    JOURNAL.write_text(f"# {DATE} two-tap same-QOI anchor launch package\n\nBuilt no-submit launch-readiness package.\n", encoding="utf-8")
    write_json(IMPORT, {"task": TASK, "date": DATE, "output_dir": rel(OUT), "native_solver_outputs_mutated": False, "summary_path": rel(OUT / "summary.json")})


def main() -> dict[str, Any]:
    require_sources()
    staged = build_staged_copy_case_request()
    contract = build_endpoint_sampling_contract()
    preflight = build_nonrecirc_gate_preflight()
    uq = build_mesh_time_uq_request()
    launch = build_sbatch_or_manual_launch_plan(preflight)
    sources = build_source_manifest()
    summary = {
        "task": TASK,
        "date": DATE,
        "generated_at_utc": utc_now(),
        "feature": FEATURE,
        "endpoint_pair": ENDPOINT_PAIR,
        "launch_ready": launch[0]["launch_ready"] == "true",
        "auto_submit": False,
        "component_k_current_status": "blocked_current_rows_diagnostic_only",
        "native_solver_outputs_mutated": False,
        "registry_mutation": "none",
    }
    write_csv(OUT / "staged_copy_case_request.csv", staged)
    write_csv(OUT / "endpoint_sampling_contract.csv", contract)
    write_csv(OUT / "nonrecirc_gate_preflight.csv", preflight)
    write_csv(OUT / "mesh_time_uq_request.csv", uq)
    write_csv(OUT / "sbatch_or_manual_launch_plan.csv", launch)
    write_csv(OUT / "source_manifest.csv", sources)
    write_json(OUT / "summary.json", summary)
    write_readme(summary)
    write_status_files(summary)
    return summary


if __name__ == "__main__":
    print(json.dumps(main(), indent=2, sort_keys=True))
