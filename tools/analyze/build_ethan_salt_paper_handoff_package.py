#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import shutil
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
TMP_MPL_ROOT = ROOT / "tmp" / "mplconfig"
TMP_MPL_ROOT.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(TMP_MPL_ROOT))

import matplotlib.pyplot as plt
import numpy as np

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.common import csv_dump, ensure_dir, iso_timestamp, json_dump, save_matplotlib_figure, safe_float  # noqa: E402

DEFAULT_OUTPUT_DIR = ROOT / "reports" / "2026-06-18_ethan_salt_paper_handoff_package"
DEFAULT_SCRUTINY_DIR = ROOT / "reports" / "2026-06-17_ethan_transport_scrutiny_package"
DEFAULT_ANALYSIS_DIR = ROOT / "reports" / "2026-06-18_ethan_transport_analysis_package"
DEFAULT_CLOSURE_DIR = ROOT / "reports" / "2026-06-18_ethan_transport_interpretation_closure"
DEFAULT_FIELD_CAMPAIGN_DIR = ROOT / "reports" / "2026-06-15_ethan_field_transport_campaign"
DEFAULT_REPRESENTATIVE_DIR = ROOT / "reports" / "2026-06-15_ethan_representative_transport_comparison"
SAFE_BRANCHES = ("left_lower_leg", "test_section_span", "left_upper_leg", "upcomer")
SALT_FAMILY_ORDER = (
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
CASE_STYLE = {
    "val_salt_test_2_coarse_mesh_laminar": ("Salt 2 val", "#111827"),
    "viscosity_screening_salt_test_1_jin_coarse_mesh": ("Salt 1 Jin", "#0b6e4f"),
    "viscosity_screening_salt_test_1_kirst_coarse_mesh": ("Salt 1 Kirst", "#7c3aed"),
    "viscosity_screening_salt_test_2_jin_coarse_mesh": ("Salt 2 Jin", "#0f766e"),
    "viscosity_screening_salt_test_2_kirst_coarse_mesh": ("Salt 2 Kirst", "#bc3908"),
    "viscosity_screening_salt_test_3_jin_coarse_mesh": ("Salt 3 Jin", "#1d4ed8"),
    "viscosity_screening_salt_test_3_kirst_coarse_mesh": ("Salt 3 Kirst", "#be123c"),
    "viscosity_screening_salt_test_4_jin_coarse_mesh": ("Salt 4 Jin", "#a16207"),
    "viscosity_screening_salt_test_4_kirst_coarse_mesh": ("Salt 4 Kirst", "#b45309"),
}
SALT_CASE_GROUPS = {
    "salt2": (
        "val_salt_test_2_coarse_mesh_laminar",
        "viscosity_screening_salt_test_2_jin_coarse_mesh",
        "viscosity_screening_salt_test_2_kirst_coarse_mesh",
    ),
    "salt4": (
        "viscosity_screening_salt_test_4_jin_coarse_mesh",
        "viscosity_screening_salt_test_4_kirst_coarse_mesh",
    ),
}

try:
    plt.style.use("seaborn-v0_8-whitegrid")
except OSError:
    plt.style.use("ggplot")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build a Salt-only paper handoff package from the current scrutiny, "
            "analysis, campaign, and representative transport outputs."
        )
    )
    parser.add_argument("--scrutiny-dir", default=str(DEFAULT_SCRUTINY_DIR))
    parser.add_argument("--analysis-dir", default=str(DEFAULT_ANALYSIS_DIR))
    parser.add_argument("--closure-dir", default=str(DEFAULT_CLOSURE_DIR))
    parser.add_argument("--field-campaign-dir", default=str(DEFAULT_FIELD_CAMPAIGN_DIR))
    parser.add_argument("--representative-dir", default=str(DEFAULT_REPRESENTATIVE_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    return parser.parse_args()


def load_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def case_label(source_id: str) -> str:
    return CASE_STYLE.get(source_id, (source_id, "#4b5563"))[0]


def case_color(source_id: str) -> str:
    return CASE_STYLE.get(source_id, (source_id, "#4b5563"))[1]


def sort_key(source_id: str) -> int:
    try:
        return SALT_FAMILY_ORDER.index(source_id)
    except ValueError:
        return len(SALT_FAMILY_ORDER)


def relative_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT.resolve()))
    except ValueError:
        return str(path.resolve())


def copy_figure_bundle(source_figure_root: Path, source_stem: str, destination_root: Path, destination_stem: str) -> dict[str, str]:
    bundle_root = ensure_dir(destination_root / "figures")
    copied: dict[str, str] = {}
    for ext in ("pdf", "png", "svg"):
        source_path = source_figure_root / ext / f"{source_stem}.{ext}"
        if not source_path.exists():
            continue
        destination_dir = ensure_dir(bundle_root / ext)
        destination_path = destination_dir / f"{destination_stem}.{ext}"
        shutil.copy2(source_path, destination_path)
        copied[ext] = str(destination_path)
    return copied


def load_staging_gate(scrutiny_dir: Path, analysis_dir: Path) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    return (
        load_csv_rows(scrutiny_dir / "paper_safe_asset_map.csv"),
        load_csv_rows(analysis_dir / "promotion_candidate_index.csv"),
    )


def generate_heat_loss_subset_figure(
    output_dir: Path,
    family_key: str,
    total_rows: list[dict[str, str]],
    grouped_rows: list[dict[str, str]],
) -> dict[str, str]:
    family_cases = SALT_CASE_GROUPS[family_key]
    grouped_total: dict[str, list[dict[str, str]]] = defaultdict(list)
    grouped_role: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in total_rows:
        source_id = str(row["source_id"])
        if source_id in family_cases:
            grouped_total[source_id].append(row)
    for row in grouped_rows:
        source_id = str(row["source_id"])
        if source_id in family_cases:
            grouped_role[(source_id, str(row["thermal_role_group"]))].append(row)

    fig, axes = plt.subplots(2, 1, figsize=(12, 8.5), sharex=True)
    for source_id in sorted(grouped_total, key=sort_key):
        payload = sorted(grouped_total[source_id], key=lambda row: safe_float(row.get("loop_s_mid_m"), math.nan) or math.nan)
        x = [float(row["loop_s_mid_m"]) for row in payload]
        axes[0].plot(x, [float(row["mean_wall_heat_per_length_w_m"]) for row in payload], color=case_color(source_id), linewidth=2.4, label=f"{case_label(source_id)} total")
        axes[1].plot(x, [float(row["mean_cumulative_wall_heat_w"]) for row in payload], color=case_color(source_id), linewidth=2.4, label=f"{case_label(source_id)} total")
        for role_name, style, role_label in (
            ("parasitic_loss", ":", "parasitic"),
            ("intended_transfer", "--", "intended"),
        ):
            role_payload = sorted(
                grouped_role.get((source_id, role_name), []),
                key=lambda row: safe_float(row.get("loop_s_mid_m"), math.nan) or math.nan,
            )
            if not role_payload:
                continue
            role_x = [float(row["loop_s_mid_m"]) for row in role_payload]
            axes[0].plot(role_x, [float(row["mean_wall_heat_per_length_w_m"]) for row in role_payload], color=case_color(source_id), linewidth=1.5, linestyle=style, label=f"{case_label(source_id)} {role_label}")
            axes[1].plot(role_x, [float(row["mean_cumulative_wall_heat_w"]) for row in role_payload], color=case_color(source_id), linewidth=1.5, linestyle=style)
    axes[0].axhline(0.0, color="#9ca3af", linewidth=0.9)
    axes[1].axhline(0.0, color="#9ca3af", linewidth=0.9)
    axes[0].set_ylabel("q' [W/m]")
    axes[1].set_ylabel("Cumulative Q [W]")
    axes[1].set_xlabel("Distance along loop [m]")
    axes[0].set_title(f"{family_key.upper()} streamwise heat-loss comparison")
    axes[1].set_title("Cumulative grouped heat-loss context")
    handles, labels = axes[0].get_legend_handles_labels()
    if handles:
        axes[0].legend(handles, labels, loc="best", fontsize=8)
    axes[1].legend(loc="best", fontsize=8)
    fig.tight_layout()
    paths = save_matplotlib_figure(fig, output_dir, f"salt_paper_{family_key}_heat_loss", dpi=220)
    plt.close(fig)
    return paths


def generate_azimuthal_subset_figure(
    output_dir: Path,
    family_key: str,
    azimuthal_rows: list[dict[str, str]],
) -> dict[str, str]:
    family_cases = SALT_CASE_GROUPS[family_key]
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in azimuthal_rows:
        source_id = str(row["source_id"])
        if source_id in family_cases:
            grouped[source_id].append(row)

    fig, axes = plt.subplots(2, 1, figsize=(12, 8.5), sharex=True)
    for source_id in sorted(grouped, key=sort_key):
        payload = sorted(grouped[source_id], key=lambda row: safe_float(row.get("loop_s_mid_m"), math.nan) or math.nan)
        x = [float(row["loop_s_mid_m"]) for row in payload]
        axes[0].plot(x, [float(row["circumferential_mean_darcy_f_shear"]) for row in payload], color=case_color(source_id), linewidth=2.2, label=case_label(source_id))
        axes[1].plot(x, [float(row["circumferential_mean_wall_heat_flux_w_m2"]) for row in payload], color=case_color(source_id), linewidth=2.2, label=case_label(source_id))
    axes[0].set_ylabel("Circumferential mean Darcy f")
    axes[1].set_ylabel("Circumferential mean q'' [W/m$^2$]")
    axes[1].set_xlabel("Distance along loop [m]")
    axes[0].set_title(f"{family_key.upper()} circumferential-mean azimuthal transport")
    axes[1].set_title("Circumferential-mean wall heat-flux context")
    axes[0].legend(loc="best", fontsize=8)
    axes[1].legend(loc="best", fontsize=8)
    fig.tight_layout()
    paths = save_matplotlib_figure(fig, output_dir, f"salt_paper_{family_key}_azimuthal_means", dpi=220)
    plt.close(fig)
    return paths


def generate_zoomed_salt2_hydraulic_figure(output_dir: Path, transport_rows: list[dict[str, str]]) -> dict[str, str]:
    family_cases = SALT_CASE_GROUPS["salt2"]
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in transport_rows:
        source_id = str(row["source_id"])
        if source_id in family_cases:
            grouped[source_id].append(row)

    fig, axes = plt.subplots(2, 1, figsize=(14, 9), sharex=True)
    for source_id in sorted(grouped, key=sort_key):
        payload = sorted(grouped[source_id], key=lambda row: safe_float(row.get("loop_s_m"), math.nan) or math.nan)
        x = [float(row["loop_s_m"]) for row in payload]
        axes[0].plot(x, [float(row["mean_darcy_f_shear"]) for row in payload], color=case_color(source_id), linewidth=1.8, linestyle="--", label=f"{case_label(source_id)} shear")
        axes[0].plot(x, [float(row["mean_darcy_f_pressure_drop_prgh"]) for row in payload], color=case_color(source_id), linewidth=1.8, label=f"{case_label(source_id)} direct")
        axes[1].plot(x, [float(row["mean_dp_major_gradient_direct_prgh_pa_per_m"]) for row in payload], color=case_color(source_id), linewidth=1.8, label=case_label(source_id))
    axes[0].set_ylim(-20.0, 20.0)
    axes[0].set_ylabel("Darcy f")
    axes[0].set_title("Representative Salt 2 friction comparison")
    axes[0].legend(loc="best", ncol=2, fontsize=8)
    axes[1].set_ylabel("Direct dp/ds [Pa/m]")
    axes[1].set_xlabel("Distance along loop [m]")
    axes[1].set_title("Representative Salt 2 direct pressure-gradient comparison")
    axes[1].legend(loc="best", fontsize=8)
    fig.tight_layout()
    paths = save_matplotlib_figure(fig, output_dir, "salt_paper_salt2_friction_pressure_zoomed", dpi=220)
    plt.close(fig)
    return paths


def generate_salt2_branch_thermal_safe_figure(output_dir: Path, rows: list[dict[str, str]]) -> dict[str, str]:
    family_cases = SALT_CASE_GROUPS["salt2"]
    filtered = [row for row in rows if str(row["source_id"]) in family_cases and str(row["branch_name"]) in SAFE_BRANCHES]
    fig, axes = plt.subplots(2, 1, figsize=(12, 8.5), sharex=True)
    branch_positions = np.arange(len(SAFE_BRANCHES))
    for source_id in sorted({str(row["source_id"]) for row in filtered}, key=sort_key):
        payload = {str(row["branch_name"]): row for row in filtered if str(row["source_id"]) == source_id}
        x = branch_positions
        axes[0].plot(x, [safe_float(payload[branch].get("mean_effective_htc_w_m2_k"), math.nan) for branch in SAFE_BRANCHES], marker="o", linewidth=2.0, color=case_color(source_id), label=case_label(source_id))
        axes[1].plot(x, [safe_float(payload[branch].get("mean_effective_thermal_resistance_k_m_w"), math.nan) for branch in SAFE_BRANCHES], marker="o", linewidth=2.0, color=case_color(source_id), label=case_label(source_id))
    axes[0].set_ylabel("Mean effective HTC [W/m$^2$/K]")
    axes[1].set_ylabel("Mean effective R'$_{th}$ [K m / W]")
    axes[1].set_xticks(branch_positions)
    axes[1].set_xticklabels(list(SAFE_BRANCHES), rotation=25, ha="right")
    axes[1].set_xlabel("Safe Salt branch subset")
    axes[0].set_title("Salt 2 branch-thermal safe subset")
    axes[1].set_title("Derived branch thermal resistance on the same safe subset")
    axes[0].legend(loc="best", fontsize=8)
    axes[1].legend(loc="best", fontsize=8)
    fig.tight_layout()
    paths = save_matplotlib_figure(fig, output_dir, "salt_paper_salt2_branch_thermal_safe_subset", dpi=220)
    plt.close(fig)
    return paths


def generate_salt_family_branch_thermal_safe_figure(output_dir: Path, rows: list[dict[str, str]]) -> dict[str, str]:
    filtered = [
        row
        for row in rows
        if str(row["source_id"]) in SALT_FAMILY_ORDER and str(row["branch_name"]) in SAFE_BRANCHES and ("salt_test_2" in str(row["source_id"]) or "salt_test_4" in str(row["source_id"]))
    ]
    family_panels = ("salt2", "salt4")
    fig, axes = plt.subplots(2, 1, figsize=(13.5, 9.5), sharex=True)
    branch_positions = np.arange(len(SAFE_BRANCHES))
    for axis, family_key in zip(axes, family_panels):
        family_cases = SALT_CASE_GROUPS[family_key]
        for source_id in family_cases:
            payload = {
                str(row["branch_name"]): row
                for row in filtered
                if str(row["source_id"]) == source_id
            }
            if not payload:
                continue
            axis.plot(
                branch_positions,
                [safe_float(payload[branch].get("mean_effective_htc_w_m2_k"), math.nan) for branch in SAFE_BRANCHES],
                marker="o",
                linewidth=2.0,
                color=case_color(source_id),
                label=case_label(source_id),
            )
        axis.set_ylabel("Mean effective HTC [W/m$^2$/K]")
        axis.set_title(f"{family_key.upper()} safe-branch thermal subset")
        axis.legend(loc="best", fontsize=8)
    axes[-1].set_xticks(branch_positions)
    axes[-1].set_xticklabels(list(SAFE_BRANCHES), rotation=25, ha="right")
    axes[-1].set_xlabel("Safe Salt branch subset")
    fig.tight_layout()
    paths = save_matplotlib_figure(fig, output_dir, "salt_paper_family_branch_thermal_safe_subset", dpi=220)
    plt.close(fig)
    return paths


def build_asset_maps(
    scrutiny_rows: list[dict[str, str]],
    analysis_rows: list[dict[str, str]],
    generated_assets: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    scrutiny_by_asset = {str(row["asset_id"]): row for row in scrutiny_rows}
    analysis_by_asset = {str(row["asset_id"]): row for row in analysis_rows}

    figure_rows: list[dict[str, Any]] = []
    manifest_rows: list[dict[str, Any]] = []
    table_rows: list[dict[str, Any]] = []
    for asset_id, asset in generated_assets.items():
        scrutiny_row = scrutiny_by_asset.get(asset["source_asset_id"], {})
        analysis_row = analysis_by_asset.get(asset["source_asset_id"], {})
        manifest_rows.append(
            {
                "asset_id": asset_id,
                "asset_kind": asset["asset_kind"],
                "staged_status": asset["staged_status"],
                "target_section": asset["target_section"],
                "target_use": asset["target_use"],
                "allowed_scope": asset["allowed_scope"],
                "required_caveat": asset["required_caveat"],
                "source_package": asset["source_package"],
                "source_path": asset["source_path"],
                "staged_pdf": asset["staged_paths"].get("pdf", ""),
                "staged_png": asset["staged_paths"].get("png", ""),
                "staged_svg": asset["staged_paths"].get("svg", ""),
            }
        )
        if asset["asset_kind"] == "figure":
            figure_rows.append(
                {
                    "figure_id": asset_id,
                    "target_section": asset["target_section"],
                    "target_use": asset["target_use"],
                    "allowed_scope": asset["allowed_scope"],
                    "required_caveat": asset["required_caveat"],
                    "promotion_status": analysis_row.get("promotion_status", scrutiny_row.get("promotion_status", "")),
                    "source_package": asset["source_package"],
                    "staged_pdf": asset["staged_paths"].get("pdf", ""),
                }
            )
        else:
            table_rows.append(
                {
                    "table_id": asset_id,
                    "target_section": asset["target_section"],
                    "target_use": asset["target_use"],
                    "allowed_scope": asset["allowed_scope"],
                    "required_caveat": asset["required_caveat"],
                    "promotion_status": analysis_row.get("promotion_status", scrutiny_row.get("promotion_status", "")),
                    "source_package": asset["source_package"],
                    "staged_csv": asset["source_path"],
                }
            )
    return manifest_rows, figure_rows, table_rows


def write_readme(
    output_dir: Path,
    manifest_rows: list[dict[str, Any]],
    closure_dir: Path,
    closure_summary: dict[str, Any],
) -> None:
    lines = [
        "# Ethan Salt Paper Handoff Package",
        "",
        f"Generated: `{iso_timestamp()}`",
        "",
        "This package stages only the Salt-focused assets that remain eligible",
        "for `../papers/3d_analysis` after the June 17 scrutiny gate, the",
        "June 18 all-runs transport analysis pass, and the narrower June 18",
        "interpretation-closure package. It does not edit the paper repo",
        "directly; it maps assets into manuscript sections and preserves the",
        "caveats required for later drafting.",
        "",
        "## Current Science Gate",
        "",
        f"- Current closure authority: `{relative_path(closure_dir / 'README.md')}`",
        f"- Cross-family hydraulic status: `{closure_summary.get('cross_family_hydraulic_status', 'unknown')}`",
        f"- Headline-eligible branch-variable rows: `{closure_summary.get('headline_eligible', 'unknown')}`",
        "- This handoff remains Salt-only even after the closure pass. The closure package",
        "  narrows the scientific gate; it does not authorize cross-family manuscript claims.",
        "",
        "## Staged Asset Summary",
        "",
    ]
    for row in manifest_rows:
        lines.append(
            f"- `{row['asset_id']}` -> `{row['target_section']}` (`{row['target_use']}`), scope `{row['allowed_scope']}`"
        )
    lines.extend(
        [
            "",
            "## Hard Promotion Boundaries",
            "",
            "- Salt 2 boundary-layer figures remain blocked from headline use.",
            "- Cross-family all-runs assets stay internal; this handoff is Salt-only.",
            "- Branch thermal promotion is limited to `left_lower_leg`, `test_section_span`, `left_upper_leg`, and `upcomer`.",
            "- The Salt 2 hydraulic figure is staged with the scrutiny caveat that mechanism claims must stay above local direct-vs-shear disagreement spikes.",
            "- The June 18 closure package supersedes the earlier all-runs analysis package as the final science gate for manuscript promotion decisions.",
        ]
    )
    (output_dir / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (output_dir / "staged_assets_readme.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    closure_note = [
        "# Closure-Aware Promotion Note",
        "",
        "This note records the narrow change between the earlier June 18 Salt handoff",
        "package and the later June 18 interpretation-closure package.",
        "",
        f"- Closure authority: `{relative_path(closure_dir / 'README.md')}`",
        f"- Cross-family hydraulic status: `{closure_summary.get('cross_family_hydraulic_status', 'unknown')}`",
        "- The Salt staged assets remain valid because the closure pass did not widen or",
        "  narrow the Salt safe-branch subset.",
        "- The closure pass does matter for paper-facing provenance because it changes the",
        "  reason cross-family hydraulics are blocked: the remaining Water left-lower-leg",
        "  rows are now resolved exclusions rather than unresolved contradictions.",
        "- The Salt paper should continue to avoid any cross-family hydraulic framing even",
        "  though the contradiction queue is now formally closed.",
    ]
    (output_dir / "closure_gate_note.md").write_text("\n".join(closure_note) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    output_dir = ensure_dir(Path(args.output_dir).resolve())
    scrutiny_dir = Path(args.scrutiny_dir).resolve()
    analysis_dir = Path(args.analysis_dir).resolve()
    closure_dir = Path(args.closure_dir).resolve()
    field_campaign_dir = Path(args.field_campaign_dir).resolve()
    representative_dir = Path(args.representative_dir).resolve()
    closure_summary = load_json(closure_dir / "interpretation_summary.json")

    scrutiny_rows, analysis_rows = load_staging_gate(scrutiny_dir, analysis_dir)
    heat_rows = load_csv_rows(field_campaign_dir / "field_transport_streamwise_heat_comparison.csv")
    grouped_heat_rows = load_csv_rows(field_campaign_dir / "field_transport_grouped_heat_comparison.csv")
    azimuthal_rows = load_csv_rows(field_campaign_dir / "field_transport_azimuthal_transport_comparison.csv")
    campaign_branch_rows = load_csv_rows(field_campaign_dir / "field_transport_branch_thermal_comparison.csv")
    representative_transport_rows = load_csv_rows(representative_dir / "representative_transport_profiles.csv")
    representative_branch_rows = load_csv_rows(representative_dir / "representative_branch_thermal_summary.csv")

    generated_assets: dict[str, dict[str, Any]] = {}

    heat_salt2 = generate_heat_loss_subset_figure(output_dir, "salt2", heat_rows, grouped_heat_rows)
    generated_assets["salt2_family_heat_loss"] = {
        "asset_kind": "figure",
        "staged_status": "ready_for_paper_task",
        "target_section": "04_salt_family_results",
        "target_use": "main_text",
        "allowed_scope": "Salt 2 family subset only",
        "required_caveat": "Use the family-level redistribution framing only; this subset inherits the campaign heat-loss definitions.",
        "source_asset_id": "salt_family_heat_loss_campaign",
        "source_package": relative_path(field_campaign_dir / "summary.json"),
        "source_path": relative_path(field_campaign_dir / "field_transport_streamwise_heat_comparison.csv"),
        "staged_paths": {fmt: relative_path(Path(path)) for fmt, path in heat_salt2.items()},
    }
    heat_salt4 = generate_heat_loss_subset_figure(output_dir, "salt4", heat_rows, grouped_heat_rows)
    generated_assets["salt4_family_heat_loss"] = {
        "asset_kind": "figure",
        "staged_status": "ready_for_paper_task",
        "target_section": "04_salt_family_results",
        "target_use": "main_text",
        "allowed_scope": "Salt 4 family subset only",
        "required_caveat": "Use the family-level redistribution framing only; this subset inherits the campaign heat-loss definitions.",
        "source_asset_id": "salt_family_heat_loss_campaign",
        "source_package": relative_path(field_campaign_dir / "summary.json"),
        "source_path": relative_path(field_campaign_dir / "field_transport_streamwise_heat_comparison.csv"),
        "staged_paths": {fmt: relative_path(Path(path)) for fmt, path in heat_salt4.items()},
    }

    azimuthal_salt2 = generate_azimuthal_subset_figure(output_dir, "salt2", azimuthal_rows)
    generated_assets["salt2_family_azimuthal_means"] = {
        "asset_kind": "figure",
        "staged_status": "ready_for_paper_task",
        "target_section": "04_salt_family_results",
        "target_use": "main_text_with_caveat",
        "allowed_scope": "Salt 2 circumferential means only",
        "required_caveat": "Keep the narration at the circumferential-mean trend level; do not present this as full theta-resolution evidence.",
        "source_asset_id": "salt_family_azimuthal_campaign",
        "source_package": relative_path(field_campaign_dir / "summary.json"),
        "source_path": relative_path(field_campaign_dir / "field_transport_azimuthal_transport_comparison.csv"),
        "staged_paths": {fmt: relative_path(Path(path)) for fmt, path in azimuthal_salt2.items()},
    }
    azimuthal_salt4 = generate_azimuthal_subset_figure(output_dir, "salt4", azimuthal_rows)
    generated_assets["salt4_family_azimuthal_means"] = {
        "asset_kind": "figure",
        "staged_status": "ready_for_paper_task",
        "target_section": "04_salt_family_results",
        "target_use": "main_text_with_caveat",
        "allowed_scope": "Salt 4 circumferential means only",
        "required_caveat": "Keep the narration at the circumferential-mean trend level; do not present this as full theta-resolution evidence.",
        "source_asset_id": "salt_family_azimuthal_campaign",
        "source_package": relative_path(field_campaign_dir / "summary.json"),
        "source_path": relative_path(field_campaign_dir / "field_transport_azimuthal_transport_comparison.csv"),
        "staged_paths": {fmt: relative_path(Path(path)) for fmt, path in azimuthal_salt4.items()},
    }

    salt2_hydraulic = generate_zoomed_salt2_hydraulic_figure(output_dir, representative_transport_rows)
    generated_assets["salt2_hydraulic_mechanism"] = {
        "asset_kind": "figure",
        "staged_status": "ready_for_paper_task",
        "target_section": "05_salt2_mechanism_results",
        "target_use": "main_text_with_caveat",
        "allowed_scope": "Salt 2 broad redistribution only",
        "required_caveat": "Narrate only the broad hydraulic redistribution; do not anchor claims on local direct-vs-shear disagreement spikes.",
        "source_asset_id": "salt2_hydraulic_mechanism",
        "source_package": relative_path(representative_dir / "summary.json"),
        "source_path": relative_path(representative_dir / "representative_transport_profiles.csv"),
        "staged_paths": {fmt: relative_path(Path(path)) for fmt, path in salt2_hydraulic.items()},
    }

    thermal_copy = copy_figure_bundle(
        representative_dir / "figures",
        "representative_thermal_and_resistance",
        output_dir,
        "salt_paper_salt2_thermal_and_resistance",
    )
    generated_assets["salt2_effective_thermal_mechanism"] = {
        "asset_kind": "figure",
        "staged_status": "ready_for_paper_task",
        "target_section": "05_salt2_mechanism_results",
        "target_use": "main_text_with_caveat",
        "allowed_scope": "Safe Salt 2 thermal regions only",
        "required_caveat": "The manuscript should narrate only branch or loop regions that pass the thermal support rubric.",
        "source_asset_id": "salt2_effective_thermal_mechanism",
        "source_package": relative_path(representative_dir / "summary.json"),
        "source_path": relative_path(representative_dir / "figures" / "pdf" / "representative_thermal_and_resistance.pdf"),
        "staged_paths": thermal_copy,
    }

    branch_rep = generate_salt2_branch_thermal_safe_figure(output_dir, representative_branch_rows)
    generated_assets["salt2_branch_thermal_safe_subset"] = {
        "asset_kind": "figure",
        "staged_status": "ready_for_paper_task",
        "target_section": "05_salt2_mechanism_results",
        "target_use": "candidate_main_text",
        "allowed_scope": ", ".join(SAFE_BRANCHES),
        "required_caveat": "This branch view is restricted to scrutiny-approved Salt 2 branches and intentionally omits corners and junctions.",
        "source_asset_id": "salt2_branch_thermal_mechanism",
        "source_package": relative_path(representative_dir / "summary.json"),
        "source_path": relative_path(representative_dir / "representative_branch_thermal_summary.csv"),
        "staged_paths": {fmt: relative_path(Path(path)) for fmt, path in branch_rep.items()},
    }

    branch_campaign = generate_salt_family_branch_thermal_safe_figure(output_dir, campaign_branch_rows)
    generated_assets["salt_family_branch_thermal_safe_subset"] = {
        "asset_kind": "figure",
        "staged_status": "ready_for_paper_task",
        "target_section": "04_salt_family_results",
        "target_use": "candidate_main_text",
        "allowed_scope": "Salt 2 and Salt 4, safe branches only",
        "required_caveat": "Only the scrutiny-approved branches are shown; right-leg and lower-leg thermal headline claims remain blocked.",
        "source_asset_id": "salt_family_branch_thermal_campaign",
        "source_package": relative_path(field_campaign_dir / "summary.json"),
        "source_path": relative_path(field_campaign_dir / "field_transport_branch_thermal_comparison.csv"),
        "staged_paths": {fmt: relative_path(Path(path)) for fmt, path in branch_campaign.items()},
    }

    trust_heatmap_copy = copy_figure_bundle(
        analysis_dir / "figures",
        "transport_analysis_salt_branch_trust",
        output_dir,
        "salt_paper_salt_branch_trust_heatmap",
    )
    generated_assets["salt_family_branch_trust_heatmap"] = {
        "asset_kind": "figure",
        "staged_status": "appendix_support_only",
        "target_section": "appendix_support",
        "target_use": "appendix_support",
        "allowed_scope": "All Salt branches, trust-only diagnostic",
        "required_caveat": "Use only as support to explain why some branches were promoted and others were withheld.",
        "source_asset_id": "salt_family_branch_thermal_qc_campaign",
        "source_package": relative_path(analysis_dir / "summary.json"),
        "source_path": relative_path(analysis_dir / "figures" / "pdf" / "transport_analysis_salt_branch_trust.pdf"),
        "staged_paths": trust_heatmap_copy,
    }

    support_copy = copy_figure_bundle(
        analysis_dir / "figures",
        "transport_analysis_salt_safe_branch_support",
        output_dir,
        "salt_paper_salt_safe_branch_support",
    )
    generated_assets["salt_family_branch_support_qc"] = {
        "asset_kind": "figure",
        "staged_status": "appendix_support_only",
        "target_section": "appendix_support",
        "target_use": "appendix_support",
        "allowed_scope": "Safe Salt branches only",
        "required_caveat": "This is a QC support figure, not a headline result figure.",
        "source_asset_id": "salt_family_branch_thermal_qc_campaign",
        "source_package": relative_path(analysis_dir / "summary.json"),
        "source_path": relative_path(analysis_dir / "figures" / "pdf" / "transport_analysis_salt_safe_branch_support.pdf"),
        "staged_paths": support_copy,
    }

    generated_assets["salt_family_branch_thermal_table"] = {
        "asset_kind": "table",
        "staged_status": "ready_for_paper_task",
        "target_section": "04_salt_family_results",
        "target_use": "table_candidate",
        "allowed_scope": "Safe-branch subset can be filtered from the staged CSV",
        "required_caveat": "Use only the scrutiny-approved Salt branches if promoted into the manuscript body.",
        "source_asset_id": "salt_family_branch_thermal_campaign",
        "source_package": relative_path(field_campaign_dir / "summary.json"),
        "source_path": relative_path(field_campaign_dir / "field_transport_branch_thermal_comparison.csv"),
        "staged_paths": {},
    }
    generated_assets["salt2_branch_thermal_table"] = {
        "asset_kind": "table",
        "staged_status": "ready_for_paper_task",
        "target_section": "05_salt2_mechanism_results",
        "target_use": "table_candidate",
        "allowed_scope": "Safe Salt 2 branches only",
        "required_caveat": "Use only the scrutiny-approved Salt 2 branches if promoted into the manuscript body.",
        "source_asset_id": "salt2_branch_thermal_mechanism",
        "source_package": relative_path(representative_dir / "summary.json"),
        "source_path": relative_path(representative_dir / "representative_branch_thermal_summary.csv"),
        "staged_paths": {},
    }

    manifest_rows, figure_rows, table_rows = build_asset_maps(scrutiny_rows, analysis_rows, generated_assets)
    csv_dump(
        output_dir / "staged_assets_manifest.csv",
        [
            "asset_id",
            "asset_kind",
            "staged_status",
            "target_section",
            "target_use",
            "allowed_scope",
            "required_caveat",
            "source_package",
            "source_path",
            "staged_pdf",
            "staged_png",
            "staged_svg",
        ],
        manifest_rows,
    )
    csv_dump(
        output_dir / "figure_claim_map.csv",
        [
            "figure_id",
            "target_section",
            "target_use",
            "allowed_scope",
            "required_caveat",
            "promotion_status",
            "source_package",
            "staged_pdf",
        ],
        figure_rows,
    )
    csv_dump(
        output_dir / "table_claim_map.csv",
        [
            "table_id",
            "target_section",
            "target_use",
            "allowed_scope",
            "required_caveat",
            "promotion_status",
            "source_package",
            "staged_csv",
        ],
        table_rows,
    )
    write_readme(output_dir, manifest_rows, closure_dir, closure_summary)

    summary = {
        "generated_at": iso_timestamp(),
        "inputs": {
            "scrutiny_dir": str(scrutiny_dir),
            "analysis_dir": str(analysis_dir),
            "closure_dir": str(closure_dir),
            "field_campaign_dir": str(field_campaign_dir),
            "representative_dir": str(representative_dir),
        },
        "closure_gate": {
            "cross_family_hydraulic_status": closure_summary.get("cross_family_hydraulic_status", "unknown"),
            "resolved_exclude_count": closure_summary.get("resolved", "unknown"),
            "headline_eligible_count": closure_summary.get("headline_eligible", "unknown"),
        },
        "staged_asset_count": len(manifest_rows),
        "main_text_candidate_count": sum(1 for row in manifest_rows if "main_text" in str(row["target_use"]) or "candidate_main_text" == str(row["target_use"])),
        "appendix_support_count": sum(1 for row in manifest_rows if str(row["target_use"]) == "appendix_support"),
        "artifacts": {
            "staged_assets_manifest_csv": str(output_dir / "staged_assets_manifest.csv"),
            "figure_claim_map_csv": str(output_dir / "figure_claim_map.csv"),
            "table_claim_map_csv": str(output_dir / "table_claim_map.csv"),
            "closure_gate_note_md": str(output_dir / "closure_gate_note.md"),
        },
    }
    json_dump(output_dir / "summary.json", summary)


if __name__ == "__main__":
    main()
