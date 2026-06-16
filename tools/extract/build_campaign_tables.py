#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.common import (  # noqa: E402
    WORKSPACE_ROOT,
    base_case_id,
    case_variant_label,
    csv_dump,
    iso_timestamp,
    json_dump,
    safe_float,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build campaign-level tables from extracted Ethan case work products.")
    parser.add_argument("--campaign-slug", required=True, help="Output campaign slug under work_products/campaigns/.")
    parser.add_argument("--source-id", action="append", required=True, help="Registered source id with extracted work products.")
    return parser.parse_args()


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_case_payload(source_id: str) -> dict:
    output_root = WORKSPACE_ROOT / "work_products" / source_id
    inventory = load_json(output_root / "case_inventory.json")
    qoi = load_json(output_root / "qoi_summary.json")
    return {
        "source_id": source_id,
        "output_root": str(output_root),
        "inventory": inventory,
        "qoi": qoi,
    }


def sort_key(record: dict) -> tuple:
    case_id = record["inventory"].get("case_id", "")
    digits = "".join(ch for ch in case_id if ch.isdigit())
    return (record["inventory"].get("fluid", ""), int(digits or 0), case_id)


def build_inventory_rows(records: list[dict]) -> list[dict[str, object]]:
    rows = []
    for record in records:
        inventory = record["inventory"]
        row = {
            "source_id": record["source_id"],
            "case_id": inventory.get("case_id", ""),
            "fluid": inventory.get("fluid", ""),
            "turbulence_model": inventory.get("turbulence_model", ""),
            "heater_power_W": inventory.get("operating_point", {}).get("heater_power_W", ""),
            "cooling_power_W": inventory.get("operating_point", {}).get("cooling_power_W", ""),
            "T_init_K": inventory.get("operating_point", {}).get("T_init_K", ""),
            "nprocs": inventory.get("nprocs", ""),
            "mesh_group_id": inventory.get("mesh_summary", {}).get("mesh_group_id", ""),
            "qoi_rtol": inventory.get("convergence_summary", {}).get("qoi_rtol", ""),
            "qoi_window": inventory.get("convergence_summary", {}).get("qoi_window", ""),
        }
        rows.append(row)
    return rows


def build_qoi_rows(records: list[dict]) -> list[dict[str, object]]:
    rows = []
    for record in records:
        qoi = dict(record["qoi"])
        qoi["source_id"] = record["source_id"]
        rows.append(qoi)
    return rows


def build_salt_pair_rows(records: list[dict]) -> list[dict[str, object]]:
    grouped: dict[str, dict[str, dict]] = {}
    for record in records:
        inventory = record["inventory"]
        case_id = str(inventory.get("case_id", ""))
        variant = case_variant_label(case_id)
        if not case_id.startswith("salt_test_") or not variant:
            continue
        grouped.setdefault(base_case_id(case_id), {})[variant] = record

    rows = []
    for test_id in sorted(grouped.keys(), key=lambda value: int("".join(ch for ch in value if ch.isdigit()) or 0)):
        pair = grouped[test_id]
        jin = pair.get("jin")
        kirst = pair.get("kirst")
        jin_qoi = jin["qoi"] if jin else {}
        kirst_qoi = kirst["qoi"] if kirst else {}
        jin_mdot = safe_float(jin_qoi.get("mdot_mean_abs_kg_s"))
        kirst_mdot = safe_float(kirst_qoi.get("mdot_mean_abs_kg_s"))
        jin_qabs = safe_float(jin_qoi.get("final_total_wall_heat_abs_w"))
        kirst_qabs = safe_float(kirst_qoi.get("final_total_wall_heat_abs_w"))
        rows.append(
            {
                "base_test_id": test_id,
                "jin_source_id": "" if not jin else jin["source_id"],
                "kirst_source_id": "" if not kirst else kirst["source_id"],
                "jin_fluid": "" if not jin else jin["inventory"].get("fluid", ""),
                "kirst_fluid": "" if not kirst else kirst["inventory"].get("fluid", ""),
                "jin_mdot_mean_abs_kg_s": "" if jin_mdot is None else jin_mdot,
                "kirst_mdot_mean_abs_kg_s": "" if kirst_mdot is None else kirst_mdot,
                "kirst_minus_jin_mdot_kg_s": "" if jin_mdot is None or kirst_mdot is None else kirst_mdot - jin_mdot,
                "jin_total_wall_heat_abs_w": "" if jin_qabs is None else jin_qabs,
                "kirst_total_wall_heat_abs_w": "" if kirst_qabs is None else kirst_qabs,
                "kirst_minus_jin_total_wall_heat_abs_w": "" if jin_qabs is None or kirst_qabs is None else kirst_qabs - jin_qabs,
                "jin_final_time": jin_qoi.get("final_time", "") if jin else "",
                "kirst_final_time": kirst_qoi.get("final_time", "") if kirst else "",
                "jin_run_status": jin_qoi.get("run_status", "") if jin else "",
                "kirst_run_status": kirst_qoi.get("run_status", "") if kirst else "",
                "jin_convergence_reached": jin_qoi.get("convergence_reached", "") if jin else "",
                "kirst_convergence_reached": kirst_qoi.get("convergence_reached", "") if kirst else "",
                "jin_convergence_dTsigma": jin_qoi.get("convergence_dTsigma", "") if jin else "",
                "kirst_convergence_dTsigma": kirst_qoi.get("convergence_dTsigma", "") if kirst else "",
            }
        )
    return rows


def build_water_rows(records: list[dict]) -> list[dict[str, object]]:
    rows = []
    for record in records:
        inventory = record["inventory"]
        qoi = record["qoi"]
        if inventory.get("fluid") != "water" or inventory.get("turbulence_model") != "laminar":
            continue
        rows.append(
            {
                "source_id": record["source_id"],
                "case_id": inventory.get("case_id", ""),
                "heater_power_W": inventory.get("operating_point", {}).get("heater_power_W", ""),
                "cooling_power_W": inventory.get("operating_point", {}).get("cooling_power_W", ""),
                "T_init_K": inventory.get("operating_point", {}).get("T_init_K", ""),
                "final_time": qoi.get("final_time", ""),
                "mdot_mean_abs_kg_s": qoi.get("mdot_mean_abs_kg_s", ""),
                "final_total_wall_heat_abs_w": qoi.get("final_total_wall_heat_abs_w", ""),
                "probe_T_avg_K": qoi.get("probe_T_avg_K", ""),
                "run_status": qoi.get("run_status", ""),
                "run_termination_reason": qoi.get("run_termination_reason", ""),
                "convergence_reached": qoi.get("convergence_reached", ""),
                "convergence_iteration": qoi.get("convergence_iteration", ""),
                "convergence_dTsigma": qoi.get("convergence_dTsigma", ""),
            }
        )
    rows.sort(key=lambda row: int("".join(ch for ch in str(row["case_id"]) if ch.isdigit()) or 0))
    return rows


def build_qoi_availability_rows(records: list[dict]) -> list[dict[str, object]]:
    rows = []
    for record in records:
        qoi = record["qoi"]
        rows.append(
            {
                "source_id": record["source_id"],
                "case_id": record["inventory"].get("case_id", ""),
                "has_mdot": bool(qoi.get("mdot_mean_abs_kg_s") not in ("", None)),
                "has_total_wall_heat": bool(qoi.get("final_total_wall_heat_abs_w") not in ("", None)),
                "has_piv_slab": bool(qoi.get("piv_slab_magU_m_s") not in ("", None)),
                "has_probe_temperatures": bool(qoi.get("probe_T_avg_K") not in ("", None)),
                "run_status": qoi.get("run_status", ""),
                "validation_status": qoi.get("validation_status", ""),
                "convergence_reached": qoi.get("convergence_reached", ""),
            }
        )
    return rows


def main() -> int:
    args = parse_args()
    records = [load_case_payload(source_id) for source_id in args.source_id]
    records.sort(key=sort_key)

    inventory_rows = build_inventory_rows(records)
    qoi_rows = build_qoi_rows(records)
    salt_pair_rows = build_salt_pair_rows(records)
    water_rows = build_water_rows(records)
    qoi_availability_rows = build_qoi_availability_rows(records)

    output_root = WORKSPACE_ROOT / "work_products" / "campaigns" / args.campaign_slug
    csv_dump(output_root / "case_inventory.csv", list(inventory_rows[0].keys()), inventory_rows)
    json_dump(output_root / "case_inventory.json", inventory_rows)
    csv_dump(output_root / "qoi_summary.csv", list(qoi_rows[0].keys()), qoi_rows)
    json_dump(output_root / "qoi_summary.json", qoi_rows)
    csv_dump(output_root / "salt_variant_pairs.csv", list(salt_pair_rows[0].keys()), salt_pair_rows)
    json_dump(output_root / "salt_variant_pairs.json", salt_pair_rows)
    csv_dump(output_root / "water_laminar_operating_points.csv", list(water_rows[0].keys()), water_rows)
    json_dump(output_root / "water_laminar_operating_points.json", water_rows)
    csv_dump(output_root / "qoi_availability.csv", list(qoi_availability_rows[0].keys()), qoi_availability_rows)
    json_dump(output_root / "qoi_availability.json", qoi_availability_rows)

    summary = {
        "generated_at": iso_timestamp(),
        "campaign_slug": args.campaign_slug,
        "source_count": len(records),
        "source_ids": [record["source_id"] for record in records],
        "fluids": dict(Counter(str(record["inventory"].get("fluid", "")) for record in records)),
        "turbulence_models": dict(Counter(str(record["inventory"].get("turbulence_model", "")) for record in records)),
        "run_status_counts": dict(Counter(str(record["qoi"].get("run_status", "")) for record in records)),
        "validation_status_counts": dict(Counter(str(record["qoi"].get("validation_status", "")) for record in records)),
        "convergence_reached_counts": dict(Counter(str(record["qoi"].get("convergence_reached", "")) for record in records)),
    }
    json_dump(output_root / "summary.json", summary)
    print(json.dumps({"campaign_slug": args.campaign_slug, "output_root": str(output_root)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
