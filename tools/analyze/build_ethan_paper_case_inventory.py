#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.analyze.ethan_closure_modeling_v3_common import csv_dump_rows, load_csv_rows, write_json  # noqa: E402
from tools.common import base_case_id, case_variant_label, ensure_dir, iso_timestamp, relative_to_workspace  # noqa: E402

DEFAULT_REPORT_DAY_DIR = ROOT / "reports" / "2026-06" / "2026-06-29"
DEFAULT_OUTPUT_DIR = DEFAULT_REPORT_DAY_DIR / "2026-06-29_ethan_paper_case_inventory"
DEFAULT_WORK_PRODUCT_DIR = ROOT / "work_products" / "2026-06-29_ethan_paper_case_inventory"
DEFAULT_IMPORT_MANIFEST_PATH = ROOT / "imports" / "2026-06-29_ethan_paper_case_inventory.json"
DEFAULT_FREEZE_WINDOWS_CSV = (
    ROOT / "reports" / "2026-06" / "2026-06-23" / "2026-06-23_ethan_cfd_freeze_checkpoint" / "freeze_case_windows.csv"
)
DEFAULT_REPRESENTATIVE_TIMESTEPS_CSV = (
    ROOT
    / "reports"
    / "2026-06"
    / "2026-06-23"
    / "2026-06-23_ethan_cfd_freeze_checkpoint"
    / "representative_timesteps.csv"
)
DEFAULT_VALIDATION_DIR = (
    ROOT / "reports" / "2026-06" / "2026-06-23" / "2026-06-23_ethan_frozen_state_1d_validation"
)
DEFAULT_BAKEOFF_DIR = ROOT / "reports" / "2026-06" / "2026-06-23" / "2026-06-23_ethan_1d_closure_bakeoff"
DEFAULT_QUEUE_PATH = (
    ROOT
    / "reports"
    / "2026-06"
    / "2026-06-26"
    / "2026-06-26_ethan_progressive_story_synthesis"
    / "open_analysis_queue.md"
)
DEFAULT_PAPER_SAFE_ASSET_MAP = (
    ROOT / "reports" / "2026-06" / "2026-06-17" / "2026-06-17_ethan_transport_scrutiny_package" / "paper_safe_asset_map.csv"
)
DEFAULT_PROMOTION_CANDIDATE_INDEX = (
    ROOT / "reports" / "2026-06" / "2026-06-18" / "2026-06-18_ethan_transport_analysis_package" / "promotion_candidate_index.csv"
)
DEFAULT_PRESENTATION_FIGURE_MANIFEST = (
    ROOT / "reports" / "2026-06" / "2026-06-23" / "2026-06-23_presentation" / "figures" / "figure_manifest.csv"
)
WORK_PRODUCTS_ROOT = ROOT / "work_products"

SOURCE_ID_TO_CASE_KEY = {
    "viscosity_screening_salt_test_1_jin_coarse_mesh": "salt1_jin",
    "viscosity_screening_salt_test_2_jin_coarse_mesh": "salt2_cont",
    "viscosity_screening_salt_test_3_jin_coarse_mesh": "salt3_cont",
    "viscosity_screening_salt_test_4_jin_coarse_mesh": "salt4_cont",
}
SOURCE_ID_ORDER = (
    "viscosity_screening_salt_test_1_jin_coarse_mesh",
    "viscosity_screening_salt_test_1_kirst_coarse_mesh",
    "val_salt_test_2_coarse_mesh_laminar",
    "viscosity_screening_salt_test_2_jin_coarse_mesh",
    "viscosity_screening_salt_test_2_kirst_coarse_mesh",
    "viscosity_screening_salt_test_3_jin_coarse_mesh",
    "viscosity_screening_salt_test_3_kirst_coarse_mesh",
    "viscosity_screening_salt_test_4_jin_coarse_mesh",
    "viscosity_screening_salt_test_4_kirst_coarse_mesh",
)
SOURCE_ID_TO_LABEL = {
    "viscosity_screening_salt_test_1_jin_coarse_mesh": "Salt 1 Jin",
    "viscosity_screening_salt_test_1_kirst_coarse_mesh": "Salt 1 Kirst",
    "val_salt_test_2_coarse_mesh_laminar": "Salt 2 Val",
    "viscosity_screening_salt_test_2_jin_coarse_mesh": "Salt 2 Jin",
    "viscosity_screening_salt_test_2_kirst_coarse_mesh": "Salt 2 Kirst",
    "viscosity_screening_salt_test_3_jin_coarse_mesh": "Salt 3 Jin",
    "viscosity_screening_salt_test_3_kirst_coarse_mesh": "Salt 3 Kirst",
    "viscosity_screening_salt_test_4_jin_coarse_mesh": "Salt 4 Jin",
    "viscosity_screening_salt_test_4_kirst_coarse_mesh": "Salt 4 Kirst",
}
PAPER_CLASS_RULES = {
    "viscosity_screening_salt_test_1_jin_coarse_mesh": (
        "paper-grade",
        "Nominal latest-window Salt Jin subset; keep the Salt 1 short-window caveat explicit.",
    ),
    "viscosity_screening_salt_test_2_jin_coarse_mesh": (
        "paper-grade",
        "Nominal latest-window Salt Jin subset with full 20-step checkpoint support.",
    ),
    "viscosity_screening_salt_test_3_jin_coarse_mesh": (
        "paper-grade",
        "Nominal latest-window Salt Jin subset with full 20-step checkpoint support.",
    ),
    "viscosity_screening_salt_test_4_jin_coarse_mesh": (
        "paper-grade",
        "Nominal latest-window Salt Jin subset with full 20-step checkpoint support.",
    ),
    "viscosity_screening_salt_test_2_kirst_coarse_mesh": (
        "exploratory",
        "Representative Salt 2 mechanism and stale-readable support case; do not mix it into the frozen paper subset.",
    ),
    "viscosity_screening_salt_test_1_kirst_coarse_mesh": (
        "blocked",
        "Current readable shadow comparison case, but it still depends on the stale June 19 replay surface rather than the refreshed frozen contract.",
    ),
    "val_salt_test_2_coarse_mesh_laminar": (
        "blocked",
        "Calibration-style Salt 2 row remains useful for local scoring, but the paper subset should stay separate until the validation split is formalized.",
    ),
    "viscosity_screening_salt_test_3_kirst_coarse_mesh": (
        "exclude",
        "Alternate-property sibling with no current paper-facing role beyond stale readable shadow rows.",
    ),
    "viscosity_screening_salt_test_4_kirst_coarse_mesh": (
        "exclude",
        "Alternate-property sibling with no current paper-facing role beyond stale readable shadow rows.",
    ),
}
CLAIM_DEFS = (
    {
        "claim_id": "latest_window_nominal_salt_jin",
        "claim_label": "Latest-window nominal Salt Jin frozen subset",
        "claim_status": "active_target",
        "source_ids": (
            "viscosity_screening_salt_test_1_jin_coarse_mesh",
            "viscosity_screening_salt_test_2_jin_coarse_mesh",
            "viscosity_screening_salt_test_3_jin_coarse_mesh",
            "viscosity_screening_salt_test_4_jin_coarse_mesh",
        ),
        "uses_one_d_bundle": True,
        "note": "Primary June 29 paper subset; Salt 1 remains provisional because the retained checkpoint window is short.",
    },
    {
        "claim_id": "current_local_shadow_1d_surface",
        "claim_label": "Current local readable 1D shadow surface",
        "claim_status": "stale_support_only",
        "source_ids": (
            "viscosity_screening_salt_test_1_kirst_coarse_mesh",
            "viscosity_screening_salt_test_2_kirst_coarse_mesh",
            "val_salt_test_2_coarse_mesh_laminar",
        ),
        "uses_one_d_bundle": True,
        "note": "These rows still anchor the current readable 1D score surface, but that surface is stale relative to the June 23 checkpoint contract.",
    },
    {
        "claim_id": "salt_family_campaign_support",
        "claim_label": "Salt family heat-loss and azimuthal campaign support",
        "claim_status": "allowed_with_caveat",
        "source_ids": (
            "val_salt_test_2_coarse_mesh_laminar",
            "viscosity_screening_salt_test_2_jin_coarse_mesh",
            "viscosity_screening_salt_test_2_kirst_coarse_mesh",
            "viscosity_screening_salt_test_4_jin_coarse_mesh",
            "viscosity_screening_salt_test_4_kirst_coarse_mesh",
        ),
        "uses_one_d_bundle": False,
        "note": "Trend-level family support only; Salt 2 and Salt 4 subsets stay narrower than the full Salt family.",
    },
    {
        "claim_id": "representative_salt2_mechanism",
        "claim_label": "Representative Salt 2 mechanism figure lane",
        "claim_status": "support_case",
        "source_ids": ("viscosity_screening_salt_test_2_kirst_coarse_mesh",),
        "uses_one_d_bundle": False,
        "note": "Salt 2 Kirst remains the current representative mechanism case in the presentation-facing assets.",
    },
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build a dated Salt paper-case inventory that freezes the June 29 "
            "paper subset, case classes, and current claim-to-case mappings."
        )
    )
    parser.add_argument("--freeze-windows-csv", default=str(DEFAULT_FREEZE_WINDOWS_CSV))
    parser.add_argument("--representative-timesteps-csv", default=str(DEFAULT_REPRESENTATIVE_TIMESTEPS_CSV))
    parser.add_argument("--validation-dir", default=str(DEFAULT_VALIDATION_DIR))
    parser.add_argument("--bakeoff-dir", default=str(DEFAULT_BAKEOFF_DIR))
    parser.add_argument("--queue-path", default=str(DEFAULT_QUEUE_PATH))
    parser.add_argument("--paper-safe-asset-map", default=str(DEFAULT_PAPER_SAFE_ASSET_MAP))
    parser.add_argument("--promotion-candidate-index", default=str(DEFAULT_PROMOTION_CANDIDATE_INDEX))
    parser.add_argument("--presentation-figure-manifest", default=str(DEFAULT_PRESENTATION_FIGURE_MANIFEST))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--work-product-dir", default=str(DEFAULT_WORK_PRODUCT_DIR))
    parser.add_argument("--import-manifest-path", default=str(DEFAULT_IMPORT_MANIFEST_PATH))
    return parser.parse_args()


def source_sort_key(source_id: str) -> int:
    try:
        return SOURCE_ID_ORDER.index(source_id)
    except ValueError:
        return len(SOURCE_ID_ORDER)


def join_tokens(values: list[str]) -> str:
    payload = [value for value in values if value]
    return "|".join(payload)


def paper_class_for_source_id(source_id: str) -> tuple[str, str]:
    return PAPER_CLASS_RULES[source_id]


def load_case_root_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for source_id in SOURCE_ID_ORDER:
        case_root = WORK_PRODUCTS_ROOT / source_id
        inventory_rows = load_csv_rows(case_root / "case_inventory.csv")
        if not inventory_rows:
            continue
        inventory_row = inventory_rows[0]
        qoi_rows = load_csv_rows(case_root / "qoi_summary.csv")
        qoi_row = qoi_rows[0] if qoi_rows else {}
        contract_rows = load_csv_rows(case_root / "cross_model_case_contract_joined.csv")
        contract_row = contract_rows[0] if contract_rows else {}
        rows.append(
            {
                "source_id": source_id,
                "case_root": case_root,
                "inventory_row": inventory_row,
                "qoi_row": qoi_row,
                "contract_row": contract_row,
            }
        )
    return rows


def freeze_rows_by_source_id(path: Path) -> dict[str, dict[str, str]]:
    rows = load_csv_rows(path)
    by_source_id: dict[str, dict[str, str]] = {}
    for row in rows:
        case_key = row.get("case_key", "")
        for candidate_source_id, candidate_case_key in SOURCE_ID_TO_CASE_KEY.items():
            if candidate_case_key == case_key:
                by_source_id[candidate_source_id] = row
                break
    return by_source_id


def validation_rows_by_source_id(validation_dir: Path) -> dict[str, list[dict[str, str]]]:
    rows = load_csv_rows(validation_dir / "case_metric_summary.csv")
    grouped: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        grouped.setdefault(str(row["frozen_source_id"]), []).append(row)
    return grouped


def preferred_shadow_scenario(bakeoff_dir: Path) -> str:
    surface_rows = load_csv_rows(bakeoff_dir / "surface_summary.csv")
    for row in surface_rows:
        if row.get("surface_label") == "defended_full_coverage_surface":
            return str(row.get("best_primary_scenario", ""))
    return str(surface_rows[0].get("best_primary_scenario", "")) if surface_rows else ""


def winner_alignment_row(bakeoff_dir: Path, scenario: str) -> dict[str, str]:
    rows = load_csv_rows(bakeoff_dir / "scenario_bundle_alignment.csv")
    for row in rows:
        if row.get("scenario") == scenario:
            return row
    return rows[0] if rows else {}


def retained_window_status(source_id: str, freeze_row: dict[str, str] | None) -> tuple[str, str]:
    if not freeze_row:
        return ("not_in_nominal_checkpoint_family", "This case is outside the nominal June 23 latest-window Salt Jin checkpoint subset.")
    count = int(float(freeze_row["representative_time_count"]))
    if count < 20:
        return (
            f"checkpoint_short_window_{count}",
            "Checkpoint representative window is shorter than the nominal 20-step target; keep the case as provisional paper-grade evidence.",
        )
    return (f"checkpoint_full_window_{count}", "Checkpoint representative window retained the full nominal 20-step set.")


def choose_shadow_row(rows: list[dict[str, str]], scenario: str) -> dict[str, str] | None:
    for row in rows:
        if row.get("scenario") == scenario:
            return row
    return rows[0] if rows else None


def claim_ids_for_source_id(source_id: str) -> list[str]:
    claim_ids: list[str] = []
    for claim in CLAIM_DEFS:
        if source_id in claim["source_ids"]:
            claim_ids.append(str(claim["claim_id"]))
    return claim_ids


def build_inventory_rows(
    *,
    case_rows: list[dict[str, Any]],
    freeze_rows: dict[str, dict[str, str]],
    validation_rows: dict[str, list[dict[str, str]]],
    preferred_scenario: str,
    alignment_row: dict[str, str],
) -> list[dict[str, Any]]:
    rows_out: list[dict[str, Any]] = []
    branch_summary = (
        f"straight={alignment_row.get('straight_friction_closure_name', '')}:{alignment_row.get('straight_friction_target_regions', '')}; "
        f"ua={alignment_row.get('primary_ua_closure_name', '')}:{alignment_row.get('primary_ua_target_regions', '')}; "
        f"nu={alignment_row.get('direct_nu_closure_name', '')}:{alignment_row.get('direct_nu_target_regions', '')}"
    )
    for case_row in case_rows:
        source_id = str(case_row["source_id"])
        inventory_row = case_row["inventory_row"]
        qoi_row = case_row["qoi_row"]
        contract_row = case_row["contract_row"]
        paper_class, paper_class_reason = paper_class_for_source_id(source_id)
        freeze_row = freeze_rows.get(source_id)
        retained_status, retained_note = retained_window_status(source_id, freeze_row)
        shadow_row = choose_shadow_row(validation_rows.get(source_id, []), preferred_scenario)
        rows_out.append(
            {
                "source_id": source_id,
                "case_label": SOURCE_ID_TO_LABEL.get(source_id, source_id),
                "paper_class": paper_class,
                "paper_class_reason": paper_class_reason,
                "family_case_id": base_case_id(str(inventory_row.get("case_id", ""))),
                "variant": case_variant_label(str(inventory_row.get("case_id", ""))) or "validation",
                "fluid": str(inventory_row.get("fluid", "")),
                "turbulence_model": str(inventory_row.get("turbulence_model", "")),
                "mesh_group_id": str(inventory_row.get("mesh_group_id", "")),
                "heater_power_w": str(inventory_row.get("heater_power_W", "")),
                "cooling_power_w": str(inventory_row.get("cooling_power_W", "")),
                "qoi_run_status": str(qoi_row.get("run_status", "")),
                "qoi_validation_status": str(qoi_row.get("validation_status", "")),
                "source_case_path": str(qoi_row.get("source_case_path", "")),
                "retained_window_status": retained_status,
                "retained_window_note": retained_note,
                "checkpoint_case_key": str(freeze_row.get("case_key", "")) if freeze_row else "",
                "checkpoint_lane": str(freeze_row.get("lane", "")) if freeze_row else "",
                "checkpoint_representative_time_count": str(freeze_row.get("representative_time_count", "")) if freeze_row else "",
                "checkpoint_latest_retained_time_s": str(freeze_row.get("latest_retained_time_s", "")) if freeze_row else "",
                "shadow_surface_scenario": str(shadow_row.get("scenario", "")) if shadow_row else "",
                "shadow_surface_role": str(shadow_row.get("comparison_class", "")) if shadow_row else "not_present",
                "shadow_surface_energy_error_pct_of_heater": str(shadow_row.get("energy_error_pct_of_heater", "")) if shadow_row else "",
                "shadow_surface_tw_rmse_k": str(shadow_row.get("tw_rmse_k", "")) if shadow_row else "",
                "shadow_surface_tp_rmse_k": str(shadow_row.get("tp_rmse_k", "")) if shadow_row else "",
                "shadow_surface_mass_flow_error_pct": str(shadow_row.get("mass_flow_relative_error_pct_vs_cfd", "")) if shadow_row else "",
                "two_d_case_id": str(contract_row.get("two_d_case_id", "")),
                "two_d_selection_basis": str(contract_row.get("two_d_selection_basis", "")),
                "current_claim_ids": join_tokens(claim_ids_for_source_id(source_id)),
                "reduced_products": join_tokens(
                    [
                        relative_to_workspace(case_row["case_root"] / "case_inventory.csv"),
                        relative_to_workspace(case_row["case_root"] / "qoi_summary.csv"),
                        relative_to_workspace(case_row["case_root"] / "cross_model_case_contract_joined.csv")
                        if (case_row["case_root"] / "cross_model_case_contract_joined.csv").exists()
                        else "",
                    ]
                ),
                "one_d_branch_contract": branch_summary if claim_ids_for_source_id(source_id) else "",
            }
        )
    rows_out.sort(key=lambda row: source_sort_key(str(row["source_id"])))
    return rows_out


def build_claim_rows(
    *,
    inventory_rows: list[dict[str, Any]],
    alignment_row: dict[str, str],
    queue_path: Path,
    paper_safe_asset_map: Path,
    promotion_candidate_index: Path,
    validation_dir: Path,
    bakeoff_dir: Path,
    presentation_figure_manifest: Path,
) -> list[dict[str, Any]]:
    inventory_lookup = {str(row["source_id"]): row for row in inventory_rows}
    rows_out: list[dict[str, Any]] = []
    for claim in CLAIM_DEFS:
        source_ids = list(claim["source_ids"])
        classes = [str(inventory_lookup[source_id]["paper_class"]) for source_id in source_ids if source_id in inventory_lookup]
        rows_out.append(
            {
                "claim_id": str(claim["claim_id"]),
                "claim_label": str(claim["claim_label"]),
                "claim_status": str(claim["claim_status"]),
                "source_ids": join_tokens(source_ids),
                "source_labels": join_tokens([SOURCE_ID_TO_LABEL.get(source_id, source_id) for source_id in source_ids]),
                "paper_classes": join_tokens(classes),
                "source_packages": join_tokens(
                    [
                        relative_to_workspace(queue_path),
                        relative_to_workspace(validation_dir / "case_metric_summary.csv"),
                        relative_to_workspace(bakeoff_dir / "surface_summary.csv"),
                        relative_to_workspace(paper_safe_asset_map),
                        relative_to_workspace(promotion_candidate_index),
                        relative_to_workspace(presentation_figure_manifest),
                    ]
                ),
                "one_d_straight_friction_input": (
                    f"{alignment_row.get('straight_friction_closure_name', '')}:{alignment_row.get('straight_friction_target_regions', '')}"
                    if claim["uses_one_d_bundle"]
                    else "n/a"
                ),
                "one_d_primary_ua_input": (
                    f"{alignment_row.get('primary_ua_closure_name', '')}:{alignment_row.get('primary_ua_target_regions', '')}"
                    if claim["uses_one_d_bundle"]
                    else "n/a"
                ),
                "one_d_direct_nu_input": (
                    f"{alignment_row.get('direct_nu_closure_name', '')}:{alignment_row.get('direct_nu_target_regions', '')}"
                    if claim["uses_one_d_bundle"]
                    else "n/a"
                ),
                "note": str(claim["note"]),
            }
        )
    return rows_out


def build_summary_rows(inventory_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    count_by_class: dict[str, int] = {}
    for row in inventory_rows:
        key = str(row["paper_class"])
        count_by_class[key] = count_by_class.get(key, 0) + 1
    return [{"paper_class": key, "case_count": count} for key, count in sorted(count_by_class.items())]


def build_readme(
    *,
    inventory_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    preferred_scenario: str,
) -> str:
    paper_subset = [row["case_label"] for row in inventory_rows if row["paper_class"] == "paper-grade"]
    blocked = [row["case_label"] for row in inventory_rows if row["paper_class"] == "blocked"]
    exploratory = [row["case_label"] for row in inventory_rows if row["paper_class"] == "exploratory"]
    excluded = [row["case_label"] for row in inventory_rows if row["paper_class"] == "exclude"]
    return f"""# Ethan Paper Case Inventory

Generated: `{iso_timestamp()}`

## Scope

- Freeze the June 29 Salt paper subset as a named case inventory rather than a
  moving implicit mixture of checkpoint, replay, and representative mechanism
  cases.
- Keep the current latest-window nominal Salt Jin subset distinct from the
  stale readable 1D shadow surface and the representative Salt 2 mechanism
  assets.
- Record the reduced-product provenance already on disk for each case and the
  current branch contract used by the readable Salt 1D shadow surface.

## Current paper subset

- `paper-grade`: {", ".join(paper_subset)}
- `exploratory`: {", ".join(exploratory) if exploratory else "none"}
- `blocked`: {", ".join(blocked) if blocked else "none"}
- `exclude`: {", ".join(excluded) if excluded else "none"}

## Current 1D branch contract

- Preferred current readable scenario: `{preferred_scenario}`
- Straight friction: see `paper_case_claim_map.csv`
- Primary UA': see `paper_case_claim_map.csv`
- Direct Nu: see `paper_case_claim_map.csv`

## Important boundary

- The `paper-grade` subset is intentionally the latest-window nominal Salt Jin
  family, even though the currently readable shadow surface still leans on
  older Salt 1 Kirst / Salt 2 Kirst / Salt 2 Val rows.
- This package does not claim that the stale readable surface is paper-grade.
  It records that surface as a bounded support lane until the refreshed
  latest-window validation and bakeoff land.
- Claim inventory rows are in `paper_case_claim_map.csv`.
"""


def write_import_manifest(
    *,
    freeze_windows_csv: Path,
    representative_timesteps_csv: Path,
    validation_dir: Path,
    bakeoff_dir: Path,
    queue_path: Path,
    paper_safe_asset_map: Path,
    promotion_candidate_index: Path,
    presentation_figure_manifest: Path,
    output_dir: Path,
    work_product_dir: Path,
    import_manifest_path: Path,
) -> None:
    write_json(
        import_manifest_path,
        {
            "generated_at": iso_timestamp(),
            "package": "2026-06-29_ethan_paper_case_inventory",
            "inputs": {
                "freeze_windows_csv": str(freeze_windows_csv.resolve()),
                "representative_timesteps_csv": str(representative_timesteps_csv.resolve()),
                "validation_dir": str(validation_dir.resolve()),
                "bakeoff_dir": str(bakeoff_dir.resolve()),
                "queue_path": str(queue_path.resolve()),
                "paper_safe_asset_map": str(paper_safe_asset_map.resolve()),
                "promotion_candidate_index": str(promotion_candidate_index.resolve()),
                "presentation_figure_manifest": str(presentation_figure_manifest.resolve()),
            },
            "outputs": {
                "report_dir": str(output_dir.resolve()),
                "work_product_dir": str(work_product_dir.resolve()),
                "inventory_csv": str((work_product_dir / "paper_case_inventory.csv").resolve()),
                "claim_map_csv": str((work_product_dir / "paper_case_claim_map.csv").resolve()),
                "summary_csv": str((work_product_dir / "paper_case_class_summary.csv").resolve()),
            },
        },
    )


def main() -> int:
    args = parse_args()
    freeze_windows_csv = Path(args.freeze_windows_csv)
    representative_timesteps_csv = Path(args.representative_timesteps_csv)
    validation_dir = Path(args.validation_dir)
    bakeoff_dir = Path(args.bakeoff_dir)
    queue_path = Path(args.queue_path)
    paper_safe_asset_map = Path(args.paper_safe_asset_map)
    promotion_candidate_index = Path(args.promotion_candidate_index)
    presentation_figure_manifest = Path(args.presentation_figure_manifest)
    output_dir = ensure_dir(Path(args.output_dir))
    work_product_dir = ensure_dir(Path(args.work_product_dir))
    import_manifest_path = Path(args.import_manifest_path)

    case_rows = load_case_root_rows()
    freeze_rows = freeze_rows_by_source_id(freeze_windows_csv)
    validation_rows = validation_rows_by_source_id(validation_dir)
    preferred_scenario = preferred_shadow_scenario(bakeoff_dir)
    alignment_row = winner_alignment_row(bakeoff_dir, preferred_scenario)
    inventory_rows = build_inventory_rows(
        case_rows=case_rows,
        freeze_rows=freeze_rows,
        validation_rows=validation_rows,
        preferred_scenario=preferred_scenario,
        alignment_row=alignment_row,
    )
    claim_rows = build_claim_rows(
        inventory_rows=inventory_rows,
        alignment_row=alignment_row,
        queue_path=queue_path,
        paper_safe_asset_map=paper_safe_asset_map,
        promotion_candidate_index=promotion_candidate_index,
        validation_dir=validation_dir,
        bakeoff_dir=bakeoff_dir,
        presentation_figure_manifest=presentation_figure_manifest,
    )
    summary_rows = build_summary_rows(inventory_rows)

    csv_dump_rows(work_product_dir / "paper_case_inventory.csv", inventory_rows)
    csv_dump_rows(work_product_dir / "paper_case_claim_map.csv", claim_rows)
    csv_dump_rows(work_product_dir / "paper_case_class_summary.csv", summary_rows)
    csv_dump_rows(output_dir / "paper_case_inventory.csv", inventory_rows)
    csv_dump_rows(output_dir / "paper_case_claim_map.csv", claim_rows)
    csv_dump_rows(output_dir / "paper_case_class_summary.csv", summary_rows)
    write_json(
        output_dir / "summary.json",
        {
            "generated_at": iso_timestamp(),
            "paper_grade_count": sum(1 for row in inventory_rows if row["paper_class"] == "paper-grade"),
            "exploratory_count": sum(1 for row in inventory_rows if row["paper_class"] == "exploratory"),
            "blocked_count": sum(1 for row in inventory_rows if row["paper_class"] == "blocked"),
            "exclude_count": sum(1 for row in inventory_rows if row["paper_class"] == "exclude"),
            "preferred_shadow_scenario": preferred_scenario,
        },
    )
    (output_dir / "README.md").write_text(
        build_readme(inventory_rows=inventory_rows, claim_rows=claim_rows, preferred_scenario=preferred_scenario),
        encoding="utf-8",
    )
    write_import_manifest(
        freeze_windows_csv=freeze_windows_csv,
        representative_timesteps_csv=representative_timesteps_csv,
        validation_dir=validation_dir,
        bakeoff_dir=bakeoff_dir,
        queue_path=queue_path,
        paper_safe_asset_map=paper_safe_asset_map,
        promotion_candidate_index=promotion_candidate_index,
        presentation_figure_manifest=presentation_figure_manifest,
        output_dir=output_dir,
        work_product_dir=work_product_dir,
        import_manifest_path=import_manifest_path,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
