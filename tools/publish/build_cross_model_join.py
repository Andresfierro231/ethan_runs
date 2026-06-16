#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.common import base_case_id, case_variant_label, WORKSPACE_ROOT, csv_dump, get_registry_row, json_dump, safe_float  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Join Ethan 2D metrics against the canonical 1D/2D reference contract.")
    parser.add_argument("--source-id", required=True, help="Registered source identifier.")
    parser.add_argument(
        "--reference-contract",
        default=(
            "/scratch/09748/andresfierro231/projects_scratch/cfd-modeling-tools/"
            "cross_model_comparison/campaigns/2026-05-28_2d_vs_1d_upcomer_baseline_v1/"
            "data/cross_model_case_contract.csv"
        ),
        help="Reference cross-model case contract CSV.",
    )
    return parser.parse_args()


def load_csv_rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def compute_relative_error(value: float | None, target: float | None) -> str:
    if value is None or target in (None, 0.0):
        return ""
    return str(abs(value - target) / abs(target) * 100.0)


def main() -> int:
    args = parse_args()
    registry_row = get_registry_row(WORKSPACE_ROOT / "registry" / "case_registry.csv", args.source_id)
    qoi_path = WORKSPACE_ROOT / "work_products" / args.source_id / "qoi_summary.json"
    if not qoi_path.exists():
        raise SystemExit(f"QoI summary not found: {qoi_path}")

    with qoi_path.open("r", encoding="utf-8") as handle:
        qoi = json.load(handle)

    fieldnames, reference_rows = load_csv_rows(Path(args.reference_contract))
    source_case_id = registry_row["case_id"]
    matched_test_id = base_case_id(source_case_id)
    matched = next((row for row in reference_rows if row.get("test_id") == matched_test_id), None)
    if matched is None:
        raise SystemExit(f"No reference contract row found for test_id={matched_test_id}")

    joined = dict(matched)
    ethan_mdot = safe_float(qoi.get("mdot_mean_abs_kg_s"))
    target_mdot = safe_float(matched.get("two_d_target_mdot_kgs"))
    reference_two_d_mdot = safe_float(matched.get("two_d_mdot_full_kgs"))
    ethan_qabs = safe_float(qoi.get("final_total_wall_heat_abs_w"))
    reference_qabs = safe_float(matched.get("two_d_q_external_loss_w"))
    variant_label = case_variant_label(source_case_id)

    joined["two_d_case_id"] = registry_row["source_id"]
    joined["two_d_selection_basis"] = "ethan_intake_mean_abs_mdot_from_4_sections"
    joined["two_d_mdot_full_kgs"] = "" if ethan_mdot is None else str(ethan_mdot)
    joined["two_d_mdot_abs_error_pct"] = compute_relative_error(ethan_mdot, target_mdot)
    joined["two_d_q_external_loss_w"] = "" if ethan_qabs is None else str(ethan_qabs)
    joined["two_d_q_balance_err_pct"] = ""
    joined["two_d_route_disagreement_pct"] = ""
    joined["two_d_friction_factor_p_rgh"] = ""
    joined["two_d_friction_factor_wall"] = ""
    joined["flow_alignment_note"] = (
        (matched.get("flow_alignment_note", "") + " | " if matched.get("flow_alignment_note") else "")
        + "Ethan direct-intake row uses mean absolute mdot across four monitored faceZones and total wall heat from postProcessing."
        + (f" Variant: {variant_label}." if variant_label else "")
    )

    summary = {
        "source_id": registry_row["source_id"],
        "case_id": registry_row["case_id"],
        "matched_test_id": matched.get("test_id", ""),
        "case_variant_label": variant_label,
        "ethan_two_d_mdot_mean_abs_kgs": ethan_mdot,
        "reference_two_d_mdot_full_kgs": reference_two_d_mdot,
        "ethan_minus_reference_two_d_mdot_kgs": None
        if ethan_mdot is None or reference_two_d_mdot is None
        else ethan_mdot - reference_two_d_mdot,
        "ethan_two_d_q_external_loss_w": ethan_qabs,
        "reference_two_d_q_external_loss_w": reference_qabs,
        "ethan_minus_reference_two_d_q_w": None
        if ethan_qabs is None or reference_qabs is None
        else ethan_qabs - reference_qabs,
        "reference_one_d_stage1_mdot_kg_s": safe_float(matched.get("one_d_stage1_mdot_kg_s")),
        "reference_one_d_stage1_qambient_total_w": safe_float(matched.get("one_d_stage1_qambient_total_w")),
        "reference_one_d_stage2_mdot_kg_s": safe_float(matched.get("one_d_stage2_mdot_kg_s")),
        "reference_one_d_stage2_qambient_total_w": safe_float(matched.get("one_d_stage2_qambient_total_w")),
        "ethan_validation_status": qoi.get("validation_status", ""),
        "ethan_render_status": qoi.get("render_status", ""),
        "ethan_run_status": qoi.get("run_status", ""),
        "ethan_convergence_reached": qoi.get("convergence_reached", False),
    }

    output_root = WORKSPACE_ROOT / "work_products" / args.source_id
    csv_dump(output_root / "cross_model_case_contract_joined.csv", fieldnames, [joined])
    json_dump(output_root / "cross_model_join_summary.json", summary)
    print(json.dumps({"source_id": args.source_id, "matched_test_id": matched.get("test_id", "")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
