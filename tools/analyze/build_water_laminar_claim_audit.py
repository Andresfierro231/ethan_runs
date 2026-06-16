#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.common import WORKSPACE_ROOT, csv_dump, iso_timestamp, json_dump, safe_float  # noqa: E402

DEFAULT_SOURCE_IDS = [
    "val_water_test_1_coarse_mesh_laminar",
    "val_water_test_2_coarse_mesh_laminar",
    "val_water_test_3_coarse_mesh_laminar",
    "val_water_test_4_coarse_mesh_laminar",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a claim-readiness audit for the staged water laminar cases.")
    parser.add_argument("--source-id", action="append", help="Optional source ids to audit. Defaults to the 4 staged water laminar cases.")
    parser.add_argument(
        "--report-slug",
        default="2026-06-02_water_laminar_claim_audit",
        help="Output folder under reports/.",
    )
    return parser.parse_args()


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def determine_claim_status(qoi: dict) -> tuple[str, str]:
    run_status = qoi.get("run_status", "")
    reached = bool(qoi.get("convergence_reached", False))
    final_time = safe_float(qoi.get("final_time"), 0.0) or 0.0
    if run_status == "completed" and reached:
        return (
            "acceptable_current_local_claim",
            "Completed normally after reaching the coded convergence monitor.",
        )
    if reached and run_status == "terminated":
        return (
            "acceptable_with_termination_caveat",
            "Hit the coded convergence monitor before scheduler termination; acceptable for bounded local trend claims but still not equivalent to a clean normal shutdown.",
        )
    if reached:
        return (
            "review_before_claim",
            "Reached the coded convergence monitor but lacks a clean completion/termination interpretation; manual review required.",
        )
    if final_time < 2000.0:
        return (
            "needs_convergence_audit",
            "Shorter runtime and no recorded convergence marker; not suitable for validation claims without further audit or continuation.",
        )
    return (
        "needs_convergence_audit",
        "No recorded convergence marker; use only for preliminary trend inspection until a convergence audit is completed.",
    )


def main() -> int:
    args = parse_args()
    source_ids = args.source_id or DEFAULT_SOURCE_IDS
    rows = []
    for source_id in source_ids:
        qoi_path = WORKSPACE_ROOT / "work_products" / source_id / "qoi_summary.json"
        inventory_path = WORKSPACE_ROOT / "work_products" / source_id / "case_inventory.json"
        qoi = load_json(qoi_path)
        inventory = load_json(inventory_path)
        claim_status, determination = determine_claim_status(qoi)
        rows.append(
            {
                "source_id": source_id,
                "case_id": inventory.get("case_id", ""),
                "heater_power_W": inventory.get("operating_point", {}).get("heater_power_W", ""),
                "cooling_power_W": inventory.get("operating_point", {}).get("cooling_power_W", ""),
                "final_time": qoi.get("final_time", ""),
                "run_status": qoi.get("run_status", ""),
                "run_termination_reason": qoi.get("run_termination_reason", ""),
                "convergence_reached": qoi.get("convergence_reached", False),
                "convergence_iteration": qoi.get("convergence_iteration", ""),
                "convergence_dTsigma": qoi.get("convergence_dTsigma", ""),
                "mdot_mean_abs_kg_s": qoi.get("mdot_mean_abs_kg_s", ""),
                "final_total_wall_heat_abs_w": qoi.get("final_total_wall_heat_abs_w", ""),
                "probe_T_avg_K": qoi.get("probe_T_avg_K", ""),
                "claim_status": claim_status,
                "determination": determination,
            }
        )

    output_root = WORKSPACE_ROOT / "reports" / args.report_slug
    csv_dump(output_root / "water_laminar_claim_audit.csv", list(rows[0].keys()), rows)
    json_dump(
        output_root / "summary.json",
        {
            "generated_at": iso_timestamp(),
            "source_ids": source_ids,
            "claim_status_counts": {status: sum(1 for row in rows if row["claim_status"] == status) for status in sorted({row["claim_status"] for row in rows})},
            "rows": rows,
        },
    )
    lines = [
        "# Water Laminar Claim Audit",
        "",
        f"Generated: `{iso_timestamp()}`",
        "",
        "## Determination",
        "",
    ]
    for row in rows:
        lines.append(f"- `{row['source_id']}`: `{row['claim_status']}`. {row['determination']}")
    lines.extend([
        "",
        "## Interpretation rule used",
        "",
        "- `acceptable_current_local_claim`: completed normally and reached the coded convergence monitor.",
        "- `acceptable_with_termination_caveat`: reached the coded convergence monitor before scheduler termination.",
        "- `needs_convergence_audit`: no recorded convergence marker, so validation claims should wait for audit or continuation.",
        "",
    ])
    (output_root / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"report_root": str(output_root), "source_count": len(rows)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
