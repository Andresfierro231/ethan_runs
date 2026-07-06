#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
TMP_MPL_ROOT = ROOT / "tmp" / "mplconfig"
TMP_MPL_ROOT.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(TMP_MPL_ROOT))

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.common import csv_dump, ensure_dir, iso_timestamp, json_dump, save_matplotlib_figure, safe_float  # noqa: E402

DEFAULT_OUTPUT_DIR = ROOT / "reports" / "2026-06-18_ethan_transport_analysis_package"
DEFAULT_SCRUTINY_DIR = ROOT / "reports" / "2026-06-17_ethan_transport_scrutiny_package"
DEFAULT_REPRESENTATIVE_DIR = ROOT / "reports" / "2026-06-15_ethan_representative_transport_comparison"
DEFAULT_FIELD_CAMPAIGN_DIR = ROOT / "reports" / "2026-06-15_ethan_field_transport_campaign"
DEFAULT_ALL_RUNS_DIR = ROOT / "reports" / "2026-06-15_ethan_all_runs_field_transport_campaign"
DEFAULT_MATH_REFERENCE = ROOT / "reports" / "2026-06-17_ethan_streamwise_transport_math_reference" / "MATH_COMPANION.md"
DEFAULT_INTERPRETATION_README = ROOT / "reports" / "2026-06-17_ethan_transport_interpretation_package" / "README.md"
DEFAULT_CASE_ORDER = (
    "val_salt_test_2_coarse_mesh_laminar",
    "viscosity_screening_salt_test_1_jin_coarse_mesh",
    "viscosity_screening_salt_test_1_kirst_coarse_mesh",
    "viscosity_screening_salt_test_2_jin_coarse_mesh",
    "viscosity_screening_salt_test_2_kirst_coarse_mesh",
    "viscosity_screening_salt_test_3_jin_coarse_mesh",
    "viscosity_screening_salt_test_3_kirst_coarse_mesh",
    "viscosity_screening_salt_test_4_jin_coarse_mesh",
    "viscosity_screening_salt_test_4_kirst_coarse_mesh",
    "val_water_test_1_coarse_mesh_laminar",
    "val_water_test_2_coarse_mesh_laminar",
    "val_water_test_3_coarse_mesh_laminar",
    "val_water_test_4_coarse_mesh_laminar",
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
    "val_water_test_1_coarse_mesh_laminar": ("Water 1", "#2563eb"),
    "val_water_test_2_coarse_mesh_laminar": ("Water 2", "#0891b2"),
    "val_water_test_3_coarse_mesh_laminar": ("Water 3", "#0f766e"),
    "val_water_test_4_coarse_mesh_laminar": ("Water 4", "#4338ca"),
}
STATUS_CODE = {"do_not_promote": 0, "internal_only": 1, "paper_safe": 2}
STATUS_LABEL = {
    "do_not_promote": "Do not promote",
    "internal_only": "Internal only",
    "paper_safe": "Paper safe",
}
SAFE_BRANCHES = ("left_lower_leg", "test_section_span", "left_upper_leg", "upcomer")

try:
    plt.style.use("seaborn-v0_8-whitegrid")
except OSError:
    plt.style.use("ggplot")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build an all-runs transport analysis package on top of the June 15/17 "
            "transport outputs, scrutiny gate, and representative/campaign packages."
        )
    )
    parser.add_argument("--scrutiny-dir", default=str(DEFAULT_SCRUTINY_DIR))
    parser.add_argument("--representative-dir", default=str(DEFAULT_REPRESENTATIVE_DIR))
    parser.add_argument("--field-campaign-dir", default=str(DEFAULT_FIELD_CAMPAIGN_DIR))
    parser.add_argument("--all-runs-dir", default=str(DEFAULT_ALL_RUNS_DIR))
    parser.add_argument("--math-reference", default=str(DEFAULT_MATH_REFERENCE))
    parser.add_argument("--interpretation-readme", default=str(DEFAULT_INTERPRETATION_README))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def sort_key(source_id: str) -> int:
    try:
        return DEFAULT_CASE_ORDER.index(source_id)
    except ValueError:
        return len(DEFAULT_CASE_ORDER)


def case_label(source_id: str) -> str:
    return CASE_STYLE.get(source_id, (source_id, "#4b5563"))[0]


def case_color(source_id: str) -> str:
    return CASE_STYLE.get(source_id, (source_id, "#4b5563"))[1]


def relative_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT.resolve()))
    except ValueError:
        return str(path.resolve())


def family_bucket_for_source_id(source_id: str) -> tuple[str, str]:
    if "salt" in source_id:
        family_group = "salt"
    elif "water" in source_id:
        family_group = "water"
    else:
        family_group = "unknown"
    if "salt_test_1" in source_id:
        return family_group, "salt1"
    if "salt_test_2" in source_id:
        return family_group, "salt2"
    if "salt_test_3" in source_id:
        return family_group, "salt3"
    if "salt_test_4" in source_id:
        return family_group, "salt4"
    if "water_test_1" in source_id:
        return family_group, "water1"
    if "water_test_2" in source_id:
        return family_group, "water2"
    if "water_test_3" in source_id:
        return family_group, "water3"
    if "water_test_4" in source_id:
        return family_group, "water4"
    return family_group, "unknown"


def load_claim_rows(scrutiny_dir: Path) -> list[dict[str, Any]]:
    path = scrutiny_dir / "transport_claim_matrix.csv"
    rows: list[dict[str, Any]] = []
    for row in load_csv_rows(path):
        family_group, case_family = family_bucket_for_source_id(str(row["source_id"]))
        rows.append(
            {
                **row,
                "family_group": family_group,
                "case_family": case_family,
                "metric_value": safe_float(row.get("metric_value"), math.nan),
            }
        )
    return rows


def load_contradiction_rows(scrutiny_dir: Path) -> list[dict[str, Any]]:
    path = scrutiny_dir / "transport_contradiction_log.csv"
    rows: list[dict[str, Any]] = []
    for row in load_csv_rows(path):
        family_group, case_family = family_bucket_for_source_id(str(row["source_id"]))
        rows.append(
            {
                **row,
                "family_group": family_group,
                "case_family": case_family,
            }
        )
    return rows


def load_promotion_rows(scrutiny_dir: Path) -> list[dict[str, Any]]:
    return load_csv_rows(scrutiny_dir / "paper_safe_asset_map.csv")


def load_branch_comparison_rows(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in load_csv_rows(path):
        family_group, case_family = family_bucket_for_source_id(str(row["source_id"]))
        rows.append(
            {
                **row,
                "family_group": family_group,
                "case_family": case_family,
                "usable_fraction": safe_float(row.get("usable_fraction"), math.nan),
                "thermal_warning_fraction": safe_float(row.get("thermal_warning_fraction"), math.nan),
                "min_abs_bulk_minus_wall_temp_k": safe_float(row.get("min_abs_bulk_minus_wall_temp_k"), math.nan),
                "mean_effective_htc_w_m2_k": safe_float(row.get("mean_effective_htc_w_m2_k"), math.nan),
            }
        )
    return rows


def aggregate_family_interpretation(
    claim_rows: list[dict[str, Any]],
    contradiction_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    contradiction_counts: Counter[tuple[str, str, str]] = Counter()
    for row in contradiction_rows:
        key = (str(row["case_family"]), str(row["scope_name"]), str(row["affected_variable_families"]).split(",")[0])
        contradiction_counts[key] += 1

    grouped: dict[tuple[str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in claim_rows:
        grouped[(str(row["case_family"]), str(row["scope_type"]), str(row["scope_name"]), str(row["variable_family"]))].append(row)
        grouped[(str(row["family_group"]) + "_all", str(row["scope_type"]), str(row["scope_name"]), str(row["variable_family"]))].append(row)
        grouped[("cross_family", str(row["scope_type"]), str(row["scope_name"]), str(row["variable_family"]))].append(row)

    output_rows: list[dict[str, Any]] = []
    for key, rows in sorted(grouped.items()):
        family_bucket, scope_type, scope_name, variable_family = key
        statuses = Counter(str(row["scrutiny_status"]) for row in rows)
        case_labels = sorted({str(row["case_label"]) for row in rows})
        source_ids = sorted({str(row["source_id"]) for row in rows}, key=sort_key)
        has_salt_safe = any(str(row["family_group"]) == "salt" and str(row["scrutiny_status"]) == "paper_safe" for row in rows)
        has_water_safe = any(str(row["family_group"]) == "water" and str(row["scrutiny_status"]) == "paper_safe" for row in rows)
        contradiction_count = sum(
            1
            for row in contradiction_rows
            if (
                (family_bucket == "cross_family")
                or (family_bucket == str(row["family_group"]) + "_all")
                or (family_bucket == str(row["case_family"]))
            )
            and str(row["scope_name"]) == scope_name
            and variable_family in str(row["affected_variable_families"]).split(",")
        )
        if contradiction_count > 0:
            interpretation_class = "contradictory"
            staging_lane = "needs_method_followup"
        elif statuses["paper_safe"] == 0 and statuses["internal_only"] == 0:
            interpretation_class = "blocked_from_paper"
            staging_lane = "needs_method_followup"
        elif statuses["paper_safe"] == 0:
            interpretation_class = "support_limited"
            staging_lane = "all_runs_screening"
        elif family_bucket == "cross_family" and has_salt_safe and has_water_safe and statuses["do_not_promote"] == 0:
            interpretation_class = "established_result"
            staging_lane = "all_runs_screening"
        elif family_bucket == "salt_all":
            interpretation_class = "salt_only_result"
            staging_lane = "salt_paper_candidate"
        elif family_bucket == "water_all":
            interpretation_class = "water_only_result"
            staging_lane = "water_internal_only"
        else:
            interpretation_class = "family_only_result"
            staging_lane = "salt_paper_candidate" if family_bucket.startswith("salt") else ("water_internal_only" if family_bucket.startswith("water") else "all_runs_screening")

        output_rows.append(
            {
                "family_bucket": family_bucket,
                "scope_type": scope_type,
                "scope_name": scope_name,
                "variable_family": variable_family,
                "paper_safe_count": statuses["paper_safe"],
                "internal_only_count": statuses["internal_only"],
                "blocked_count": statuses["do_not_promote"],
                "contradiction_count": contradiction_count,
                "case_count": len(case_labels),
                "source_ids": ", ".join(source_ids),
                "case_labels": ", ".join(case_labels),
                "interpretation_class": interpretation_class,
                "staging_lane": staging_lane,
            }
        )
    return output_rows


def prioritize_contradictions(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    prioritized: list[dict[str, Any]] = []
    for row in rows:
        if str(row["requires_code_fix"]) == "yes":
            priority = 1
            recommended = "Investigate reduction method or sign-alignment assumptions before stronger cross-family claims."
        elif str(row["family_group"]) == "salt":
            priority = 2
            recommended = "Keep out of paper narrative unless the scope narrows to a safe subset or the branch is explicitly excluded."
        else:
            priority = 3
            recommended = "Retain as internal caution and revisit after higher-priority contradictions are resolved."
        prioritized.append(
            {
                **row,
                "priority_rank": priority,
                "recommended_next_action": recommended,
            }
        )
    prioritized.sort(key=lambda row: (int(row["priority_rank"]), sort_key(str(row["source_id"])), str(row["scope_name"])))
    return prioritized


def build_promotion_candidate_index(
    promotion_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in promotion_rows:
        asset_id = str(row["asset_id"])
        if asset_id.startswith("salt_family_"):
            target_section = "04_salt_family_results"
            target_use = "main_text" if "appendix" not in str(row["recommended_placement"]) else "appendix_support"
        elif asset_id.startswith("salt2_"):
            target_section = "05_salt2_mechanism_results"
            target_use = "main_text" if "appendix" not in str(row["recommended_placement"]) else "appendix_support"
        else:
            target_section = "internal_only"
            target_use = "internal_only"
        rows.append(
            {
                "asset_id": asset_id,
                "promotion_status": str(row["promotion_status"]),
                "target_section": target_section,
                "target_use": target_use,
                "recommended_scope_filter": str(row["recommended_scope_filter"]),
                "required_caveat": str(row["blocking_reason"]),
                "source_package": str(row["primary_source_path"]),
                "stage_now": "yes" if str(row["promotion_status"]) != "blocked" and target_section != "internal_only" else "no",
            }
        )
    return rows


def plot_branch_trust_heatmap(
    output_dir: Path,
    claim_rows: list[dict[str, Any]],
    family_group: str,
    stem: str,
    title: str,
) -> dict[str, str]:
    branch_rows = [
        row
        for row in claim_rows
        if str(row["scope_type"]) == "branch"
        and str(row["variable_family"]) == "effective_htc"
        and (family_group == "all" or str(row["family_group"]) == family_group)
    ]
    branches = list(SAFE_BRANCHES) + ["lower_leg", "right_leg", "upper_leg"]
    cases = sorted({str(row["source_id"]) for row in branch_rows}, key=sort_key)
    data = np.full((len(cases), len(branches)), -1.0)
    for row in branch_rows:
        r = cases.index(str(row["source_id"]))
        c = branches.index(str(row["scope_name"]))
        data[r, c] = STATUS_CODE[str(row["scrutiny_status"])]
    cmap = ListedColormap(["#b91c1c", "#f59e0b", "#15803d"])
    fig, ax = plt.subplots(figsize=(13.5, max(4.5, 0.4 * len(cases) + 1.5)))
    image = ax.imshow(data, aspect="auto", cmap=cmap, vmin=0, vmax=2)
    ax.set_xticks(range(len(branches)))
    ax.set_xticklabels(branches, rotation=35, ha="right")
    ax.set_yticks(range(len(cases)))
    ax.set_yticklabels([case_label(case_id) for case_id in cases])
    ax.set_title(title)
    for row_index in range(len(cases)):
        for col_index in range(len(branches)):
            if data[row_index, col_index] < 0:
                continue
            ax.text(col_index, row_index, ["blocked", "internal", "safe"][int(data[row_index, col_index])], ha="center", va="center", color="white", fontsize=7)
    cbar = fig.colorbar(image, ax=ax, ticks=[0, 1, 2])
    cbar.ax.set_yticklabels(["Blocked", "Internal", "Safe"])
    fig.tight_layout()
    paths = save_matplotlib_figure(fig, output_dir, stem, dpi=220)
    plt.close(fig)
    return paths


def plot_hydraulic_disagreement_hotspots(output_dir: Path, claim_rows: list[dict[str, Any]]) -> dict[str, str]:
    rows = [
        row
        for row in claim_rows
        if str(row["scope_type"]) == "span_section" and str(row["variable_family"]) == "direct_pressure_gradient"
    ]
    spans = sorted({str(row["scope_name"]) for row in rows})
    cases = sorted({str(row["source_id"]) for row in rows}, key=sort_key)
    data = np.full((len(cases), len(spans)), -1.0)
    for row in rows:
        r = cases.index(str(row["source_id"]))
        c = spans.index(str(row["scope_name"]))
        data[r, c] = STATUS_CODE[str(row["scrutiny_status"])]
    cmap = ListedColormap(["#b91c1c", "#f59e0b", "#15803d"])
    fig, ax = plt.subplots(figsize=(12.5, max(4.5, 0.4 * len(cases) + 1.5)))
    image = ax.imshow(data, aspect="auto", cmap=cmap, vmin=0, vmax=2)
    ax.set_xticks(range(len(spans)))
    ax.set_xticklabels(spans, rotation=35, ha="right")
    ax.set_yticks(range(len(cases)))
    ax.set_yticklabels([case_label(case_id) for case_id in cases])
    ax.set_title("Hydraulic Agreement Hotspots")
    cbar = fig.colorbar(image, ax=ax, ticks=[0, 1, 2])
    cbar.ax.set_yticklabels(["Blocked", "Internal", "Safe"])
    fig.tight_layout()
    paths = save_matplotlib_figure(fig, output_dir, "transport_analysis_hydraulic_hotspots", dpi=220)
    plt.close(fig)
    return paths


def plot_branch_support_patterns(
    output_dir: Path,
    branch_rows: list[dict[str, Any]],
    family_group: str,
    stem: str,
    title: str,
) -> dict[str, str]:
    rows = [row for row in branch_rows if family_group == "all" or str(row["family_group"]) == family_group]
    branches = list(SAFE_BRANCHES)
    fig, axes = plt.subplots(3, 1, figsize=(13.5, 10.0), sharex=True)
    positions = np.arange(len(rows))
    labels = [f"{row['case_label']}\n{row['branch_name']}" for row in rows]
    axes[0].bar(positions, [safe_float(row["usable_fraction"], math.nan) for row in rows], color=[case_color(str(row["source_id"])) for row in rows])
    axes[0].axhline(0.90, color="#15803d", linestyle="--", linewidth=1.0)
    axes[0].set_ylabel("Usable fraction")
    axes[1].bar(positions, [safe_float(row["thermal_warning_fraction"], math.nan) for row in rows], color=[case_color(str(row["source_id"])) for row in rows])
    axes[1].axhline(0.10, color="#15803d", linestyle="--", linewidth=1.0)
    axes[1].set_ylabel("Warning fraction")
    axes[2].bar(positions, [safe_float(row["min_abs_bulk_minus_wall_temp_k"], math.nan) for row in rows], color=[case_color(str(row["source_id"])) for row in rows])
    axes[2].axhline(0.50, color="#15803d", linestyle="--", linewidth=1.0)
    axes[2].axhline(0.25, color="#b91c1c", linestyle="--", linewidth=1.0)
    axes[2].set_ylabel("Min |ΔT| [K]")
    axes[2].set_xticks(positions)
    axes[2].set_xticklabels(labels, rotation=35, ha="right")
    axes[0].set_title(title)
    fig.tight_layout()
    paths = save_matplotlib_figure(fig, output_dir, stem, dpi=220)
    plt.close(fig)
    return paths


def write_readme(
    output_dir: Path,
    interpretation_rows: list[dict[str, Any]],
    contradiction_rows: list[dict[str, Any]],
    promotion_rows: list[dict[str, Any]],
    args: argparse.Namespace,
) -> None:
    class_counts = Counter(str(row["interpretation_class"]) for row in interpretation_rows)
    staged_now = [row for row in promotion_rows if str(row["stage_now"]) == "yes"]
    lines = [
        "# Ethan Transport Analysis Package",
        "",
        f"Generated: `{iso_timestamp()}`",
        "",
        "This package performs the all-runs interpretive pass that sits between",
        "the June 17 scrutiny gate and any later manuscript promotion. It does",
        "not reopen extraction; it classifies the current outputs into stable",
        "family-level results, support-limited results, and contradiction-driven",
        "follow-up items.",
        "",
        "## Canonical Inputs",
        "",
        f"- scrutiny gate: `{relative_path(Path(args.scrutiny_dir))}`",
        f"- representative Salt 2 package: `{relative_path(Path(args.representative_dir))}`",
        f"- Salt-family campaign: `{relative_path(Path(args.field_campaign_dir))}`",
        f"- all-runs campaign: `{relative_path(Path(args.all_runs_dir))}`",
        f"- math reference: `{relative_path(Path(args.math_reference))}`",
        f"- interpretation reference: `{relative_path(Path(args.interpretation_readme))}`",
        "",
        "## Interpretation Snapshot",
        "",
        f"- established results: `{class_counts['established_result']}` grouped rows",
        f"- Salt-only results: `{class_counts['salt_only_result']}` grouped rows",
        f"- Water-only results: `{class_counts['water_only_result']}` grouped rows",
        f"- family-only results: `{class_counts['family_only_result']}` grouped rows",
        f"- support-limited rows: `{class_counts['support_limited']}` grouped rows",
        f"- contradictory rows: `{class_counts['contradictory']}` grouped rows",
        f"- blocked-from-paper rows: `{class_counts['blocked_from_paper']}` grouped rows",
        "",
        "## Current Promotion Candidates",
        "",
    ]
    for row in staged_now:
        lines.append(
            f"- `{row['asset_id']}` -> `{row['target_section']}` with scope `{row['recommended_scope_filter']}`"
        )
    lines.extend(
        [
            "",
            "## Highest-Priority Contradictions",
            "",
        ]
    )
    for row in contradiction_rows[:6]:
        lines.append(
            f"- priority `{row['priority_rank']}`: `{row['case_label']} / {row['scope_name']}` -> {row['likely_cause']}"
        )
    lines.extend(
        [
            "",
            "## Salt Paper Boundary",
            "",
            "- This package is all-runs by design, but it does not itself promote",
            "  assets into `../papers/3d_analysis`.",
            "- The next stage should use the Salt-paper handoff package to stage only",
            "  the scrutiny-cleared Salt subset and its required caveats.",
        ]
    )
    (output_dir / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    output_dir = ensure_dir(Path(args.output_dir).resolve())
    scrutiny_dir = Path(args.scrutiny_dir).resolve()
    representative_dir = Path(args.representative_dir).resolve()
    field_campaign_dir = Path(args.field_campaign_dir).resolve()
    all_runs_dir = Path(args.all_runs_dir).resolve()

    claim_rows = load_claim_rows(scrutiny_dir)
    contradiction_rows = prioritize_contradictions(load_contradiction_rows(scrutiny_dir))
    promotion_rows = build_promotion_candidate_index(load_promotion_rows(scrutiny_dir))
    branch_rows = load_branch_comparison_rows(field_campaign_dir / "field_transport_branch_thermal_comparison.csv")
    interpretation_rows = aggregate_family_interpretation(claim_rows, contradiction_rows)

    cross_family_heatmap_paths = plot_branch_trust_heatmap(
        output_dir,
        claim_rows,
        "all",
        "transport_analysis_cross_family_branch_trust",
        "Cross-Family Branch Trust",
    )
    salt_heatmap_paths = plot_branch_trust_heatmap(
        output_dir,
        claim_rows,
        "salt",
        "transport_analysis_salt_branch_trust",
        "Salt-Only Branch Trust",
    )
    water_heatmap_paths = plot_branch_trust_heatmap(
        output_dir,
        claim_rows,
        "water",
        "transport_analysis_water_branch_trust",
        "Water-Only Branch Trust",
    )
    hydraulic_paths = plot_hydraulic_disagreement_hotspots(output_dir, claim_rows)
    salt_support_paths = plot_branch_support_patterns(
        output_dir,
        [row for row in branch_rows if str(row["branch_name"]) in SAFE_BRANCHES],
        "salt",
        "transport_analysis_salt_safe_branch_support",
        "Salt Safe-Branch Thermal Support Patterns",
    )
    water_support_paths = plot_branch_support_patterns(
        output_dir,
        [row for row in branch_rows if str(row["branch_name"]) in SAFE_BRANCHES],
        "water",
        "transport_analysis_water_safe_branch_support",
        "Water Safe-Branch Thermal Support Patterns",
    )

    csv_dump(
        output_dir / "case_family_interpretation_matrix.csv",
        [
            "family_bucket",
            "scope_type",
            "scope_name",
            "variable_family",
            "paper_safe_count",
            "internal_only_count",
            "blocked_count",
            "contradiction_count",
            "case_count",
            "source_ids",
            "case_labels",
            "interpretation_class",
            "staging_lane",
        ],
        interpretation_rows,
    )
    csv_dump(
        output_dir / "transport_contradiction_priority.csv",
        [
            "source_id",
            "case_label",
            "family_group",
            "case_family",
            "scope_name",
            "contradiction_type",
            "affected_variable_families",
            "observed_pattern",
            "likely_cause",
            "requires_code_fix",
            "primary_source_path",
            "priority_rank",
            "recommended_next_action",
        ],
        contradiction_rows,
    )
    csv_dump(
        output_dir / "promotion_candidate_index.csv",
        [
            "asset_id",
            "promotion_status",
            "target_section",
            "target_use",
            "recommended_scope_filter",
            "required_caveat",
            "source_package",
            "stage_now",
        ],
        promotion_rows,
    )

    write_readme(output_dir, interpretation_rows, contradiction_rows, promotion_rows, args)

    summary = {
        "generated_at": iso_timestamp(),
        "inputs": {
            "scrutiny_dir": str(scrutiny_dir),
            "representative_dir": str(representative_dir),
            "field_campaign_dir": str(field_campaign_dir),
            "all_runs_dir": str(all_runs_dir),
            "math_reference": str(Path(args.math_reference).resolve()),
            "interpretation_readme": str(Path(args.interpretation_readme).resolve()),
        },
        "artifacts": {
            "case_family_interpretation_matrix_csv": str(output_dir / "case_family_interpretation_matrix.csv"),
            "transport_contradiction_priority_csv": str(output_dir / "transport_contradiction_priority.csv"),
            "promotion_candidate_index_csv": str(output_dir / "promotion_candidate_index.csv"),
        },
        "figure_paths": {
            "cross_family_branch_trust": cross_family_heatmap_paths,
            "salt_branch_trust": salt_heatmap_paths,
            "water_branch_trust": water_heatmap_paths,
            "hydraulic_hotspots": hydraulic_paths,
            "salt_safe_branch_support": salt_support_paths,
            "water_safe_branch_support": water_support_paths,
        },
        "promotion_stage_now_count": sum(1 for row in promotion_rows if str(row["stage_now"]) == "yes"),
        "priority_one_contradiction_count": sum(1 for row in contradiction_rows if int(row["priority_rank"]) == 1),
    }
    json_dump(output_dir / "summary.json", summary)


if __name__ == "__main__":
    main()
