#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import math
import os
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
TMP_MPL_ROOT = ROOT / "tmp" / "mplconfig"
TMP_MPL_ROOT.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(TMP_MPL_ROOT))

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.common import csv_dump, ensure_dir, iso_timestamp, json_dump, save_matplotlib_figure, safe_float  # noqa: E402

PRESENTATION_DIR = ROOT / "reports" / "2026-06-23_presentation"
FIGURE_ROOT = PRESENTATION_DIR / "figures"
DEFAULT_IMPORT_PATH = ROOT / "imports" / "2026-06-23_presentation.json"
BAKEOFF_DIR = ROOT / "reports" / "2026-06-23_ethan_1d_closure_bakeoff"
DEFENDED_SURFACE_DIR = BAKEOFF_DIR / "defended_full_coverage_surface"


@dataclass(frozen=True)
class FigureAsset:
    slide_id: str
    slide_title: str
    role: str
    local_stem: str
    source_png: Path | None
    source_pdf: Path | None
    provenance_package: str
    use_note: str
    assumption_note: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Stage the chosen June 23 presentation figures into one local figure pack "
            "and build the presentation-local 1D gap summary figure for Slide 10."
        )
    )
    parser.add_argument("--presentation-dir", default=str(PRESENTATION_DIR))
    parser.add_argument("--import-manifest-path", default=str(DEFAULT_IMPORT_PATH))
    return parser.parse_args()


def load_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def finite_float(value: Any) -> float:
    parsed = safe_float(value)
    if parsed is None or not math.isfinite(parsed):
        return math.nan
    return float(parsed)


def scenario_label(name: str) -> str:
    mapping = {
        "ethan_cfd_informed_salt_baseline_ins_1.0in_rad_0": "Baseline 1.0 in, rad off",
        "ethan_cfd_informed_salt_baseline_ins_1.0in_rad_1": "Baseline 1.0 in, rad on",
        "ethan_cfd_informed_salt_baseline_ins_2.0in_rad_1": "Baseline 2.0 in, rad on",
        "ethan_cfd_informed_salt_hybrid_ins_1.0in_rad_0": "Hybrid 1.0 in, rad off",
        "ethan_cfd_informed_salt_hybrid_ins_1.0in_rad_1": "Hybrid 1.0 in, rad on",
        "ethan_cfd_informed_salt_hybrid_ins_2.0in_rad_1": "Hybrid 2.0 in, rad on",
    }
    return mapping.get(name, name)


def presentation_assets() -> list[FigureAsset]:
    return [
        FigureAsset(
            slide_id="01",
            slide_title="Title And Question",
            role="main",
            local_stem="01_title_salt_dashboard_overview",
            source_png=ROOT / "reports" / "2026-06-17_ethan_nondimensional_dashboard_package" / "figures" / "png" / "salt_dashboard_overview.png",
            source_pdf=ROOT / "reports" / "2026-06-17_ethan_nondimensional_dashboard_package" / "figures" / "pdf" / "salt_dashboard_overview.pdf",
            provenance_package="reports/2026-06-17_ethan_nondimensional_dashboard_package",
            use_note="Open with the Salt operating envelope and the claim that the repo now has a coherent evidence stack.",
            assumption_note="Chosen as the title-side overview because it remains the cleanest family-level state summary.",
        ),
        FigureAsset(
            slide_id="02",
            slide_title="What We Can Quantify Along The Loop Today",
            role="main",
            local_stem="02_loop_heat_loss_comparison",
            source_png=ROOT / "reports" / "2026-06-15_ethan_field_transport_campaign" / "figures" / "png" / "field_transport_heat_loss_comparison.png",
            source_pdf=ROOT / "reports" / "2026-06-15_ethan_field_transport_campaign" / "figures" / "pdf" / "field_transport_heat_loss_comparison.pdf",
            provenance_package="reports/2026-06-15_ethan_field_transport_campaign",
            use_note="Show the streamwise Salt heat-loss story without depending on active breakout work.",
            assumption_note="Uses the completed June 15 campaign figure rather than the still-active Salt heat-loss breakout lane.",
        ),
        FigureAsset(
            slide_id="03",
            slide_title="Pressure Losses Are Quantified, But Only On Bounded Support",
            role="main",
            local_stem="03_bounded_pressure_closure",
            source_png=ROOT / "reports" / "2026-06-17_ethan_pressure_htc_boundarylayer_package" / "figures" / "png" / "pressure_closure_straight_sections.png",
            source_pdf=ROOT / "reports" / "2026-06-17_ethan_pressure_htc_boundarylayer_package" / "figures" / "pdf" / "pressure_closure_straight_sections.pdf",
            provenance_package="reports/2026-06-17_ethan_pressure_htc_boundarylayer_package",
            use_note="Keep the bounded straight-lane hydraulic closure story explicit.",
            assumption_note="Straight sections remain the strongest hydraulic evidence lane for the main deck.",
        ),
        FigureAsset(
            slide_id="04",
            slide_title="p_rgh Is Not Dynamic Pressure",
            role="main",
            local_stem="04_prgh_vs_qdyn_salt2_kirst",
            source_png=ROOT / "reports" / "2026-06-23_ethan_prgh_vs_dynamic_profiles" / "figures" / "png" / "viscosity_screening_salt_test_2_kirst_coarse_mesh_prgh_vs_dynamic_by_leg.png",
            source_pdf=ROOT / "reports" / "2026-06-23_ethan_prgh_vs_dynamic_profiles" / "figures" / "pdf" / "viscosity_screening_salt_test_2_kirst_coarse_mesh_prgh_vs_dynamic_by_leg.pdf",
            provenance_package="reports/2026-06-23_ethan_prgh_vs_dynamic_profiles",
            use_note="Separate hydrostatic-corrected pressure from the kinetic-energy scale on one representative Salt case.",
            assumption_note="Salt 2 Kirst is used as the representative mechanism case for both Slide 4 and the redevelopment backup slide.",
        ),
        FigureAsset(
            slide_id="05",
            slide_title="Major And Minor Friction Extrapolation Is Partly Ready",
            role="main",
            local_stem="05_salt_hydraulic_agreement",
            source_png=ROOT / "reports" / "2026-06-18_ethan_salt_closure_correlation_package" / "figures" / "png" / "salt_hydraulic_agreement.png",
            source_pdf=ROOT / "reports" / "2026-06-18_ethan_salt_closure_correlation_package" / "figures" / "pdf" / "salt_hydraulic_agreement.pdf",
            provenance_package="reports/2026-06-18_ethan_salt_closure_correlation_package",
            use_note="Carry the current straight-versus-feature closure readiness story.",
            assumption_note="Slide text will add the current June 22 / June 23 feature fit counts that are newer than the original figure package.",
        ),
        FigureAsset(
            slide_id="06",
            slide_title="Internal HTC / Thermal Closures Are Strongest On A Safe Subset",
            role="main",
            local_stem="06_salt_branch_usability",
            source_png=ROOT / "reports" / "2026-06-18_ethan_salt_closure_correlation_package" / "figures" / "png" / "salt_branch_usability.png",
            source_pdf=ROOT / "reports" / "2026-06-18_ethan_salt_closure_correlation_package" / "figures" / "pdf" / "salt_branch_usability.pdf",
            provenance_package="reports/2026-06-18_ethan_salt_closure_correlation_package",
            use_note="Show the safe thermal subset and keep loop-wide Nu claims bounded.",
            assumption_note="The deck continues to use the branch usability map rather than a newer custom subset figure.",
        ),
        FigureAsset(
            slide_id="07",
            slide_title="Current Correlation Inventory",
            role="main",
            local_stem="07_salt_heat_loss_partition",
            source_png=ROOT / "reports" / "2026-06-18_ethan_salt_closure_correlation_package" / "figures" / "png" / "salt_heat_loss_partition.png",
            source_pdf=ROOT / "reports" / "2026-06-18_ethan_salt_closure_correlation_package" / "figures" / "pdf" / "salt_heat_loss_partition.pdf",
            provenance_package="reports/2026-06-18_ethan_salt_closure_correlation_package",
            use_note="Anchor the closure-menu slide with the heat-loss-partition reminder that thermal mismatch still matters.",
            assumption_note="Retained as the closure-menu anchor because it ties correlation discussion back to external-loss accounting.",
        ),
        FigureAsset(
            slide_id="08",
            slide_title="The Main Result: Current 1D Predictiveness Is Still Poor",
            role="main",
            local_stem="08_primary_scenario_metric_heatmap",
            source_png=BAKEOFF_DIR / "baseline_full_surface" / "figures" / "png" / "primary_scenario_metric_heatmap.png",
            source_pdf=BAKEOFF_DIR / "baseline_full_surface" / "figures" / "pdf" / "primary_scenario_metric_heatmap.pdf",
            provenance_package="reports/2026-06-23_ethan_1d_closure_bakeoff/baseline_full_surface",
            use_note="Show the fresh baseline-surface metric ranking from the rebuilt bakeoff subpackage.",
            assumption_note="Uses the rebuilt baseline-full-surface figure rather than the older top-level bakeoff PNGs.",
        ),
        FigureAsset(
            slide_id="09",
            slide_title="Why The 1D Still Misses",
            role="main",
            local_stem="09_primary_branch_development",
            source_png=BAKEOFF_DIR / "baseline_full_surface" / "figures" / "png" / "primary_branch_development.png",
            source_pdf=BAKEOFF_DIR / "baseline_full_surface" / "figures" / "pdf" / "primary_branch_development.pdf",
            provenance_package="reports/2026-06-23_ethan_1d_closure_bakeoff/baseline_full_surface",
            use_note="Use the fresh branch-development figure from the rebuilt baseline bakeoff surface.",
            assumption_note="Chosen over the older frozen-state package figure so Slide 9 stays aligned with the refreshed bakeoff wording.",
        ),
        FigureAsset(
            slide_id="10",
            slide_title="What Is Done Versus What Still Needs The Next Hour",
            role="main",
            local_stem="10_current_1d_gap_summary",
            source_png=None,
            source_pdf=None,
            provenance_package="reports/2026-06-23_presentation",
            use_note="New presentation-local summary figure: defended metric cards plus readable-scenario coverage status.",
            assumption_note="Generated only from current bakeoff CSV truth to avoid depending on ambiguous older top-level bakeoff PNGs.",
        ),
        FigureAsset(
            slide_id="A",
            slide_title="Backup Slide A: Representative Mechanism Comparison",
            role="backup",
            local_stem="A_representative_friction_and_pressure",
            source_png=ROOT / "reports" / "2026-06-15_ethan_representative_transport_comparison" / "figures" / "png" / "representative_friction_and_pressure.png",
            source_pdf=ROOT / "reports" / "2026-06-15_ethan_representative_transport_comparison" / "figures" / "pdf" / "representative_friction_and_pressure.pdf",
            provenance_package="reports/2026-06-15_ethan_representative_transport_comparison",
            use_note="Detailed matched-case hydraulic mechanism backup.",
            assumption_note="Retained as the first mechanism backup because it stays presentation-safe and already review-clean.",
        ),
        FigureAsset(
            slide_id="B",
            slide_title="Backup Slide B: Sensor Parity For The Current Best 1D Row",
            role="backup",
            local_stem="B_primary_best_sensor_parity",
            source_png=BAKEOFF_DIR / "baseline_full_surface" / "figures" / "png" / "primary_best_sensor_parity.png",
            source_pdf=BAKEOFF_DIR / "baseline_full_surface" / "figures" / "pdf" / "primary_best_sensor_parity.pdf",
            provenance_package="reports/2026-06-23_ethan_1d_closure_bakeoff/baseline_full_surface",
            use_note="Concrete parity backup for the current best readable 1D row.",
            assumption_note="Uses the rebuilt baseline bakeoff parity figure for provenance consistency with Slides 8-9.",
        ),
        FigureAsset(
            slide_id="C",
            slide_title="Backup Slide C: Salt 2 Kirst Redevelopment Follow-On",
            role="backup",
            local_stem="C_salt2_kirst_redevelopment_followon",
            source_png=ROOT / "reports" / "2026-06-23_ethan_salt_redevelopment_followon" / "figures" / "figures" / "png" / "viscosity_screening_salt_test_2_kirst_coarse_mesh_redevelopment_followon.png",
            source_pdf=ROOT / "reports" / "2026-06-23_ethan_salt_redevelopment_followon" / "figures" / "figures" / "pdf" / "viscosity_screening_salt_test_2_kirst_coarse_mesh_redevelopment_followon.pdf",
            provenance_package="reports/2026-06-23_ethan_salt_redevelopment_followon",
            use_note="Backup slide for the straight-leg redevelopment story with p_rgh(s), q_dyn(s), and q'(s).",
            assumption_note="Uses the same representative Salt 2 Kirst case as Slide 4 so the main-deck and backup mechanism stories stay aligned.",
        ),
        FigureAsset(
            slide_id="D",
            slide_title="Backup Slide D: Salt 1-4 Metric Cards",
            role="backup",
            local_stem="D_salt1to4_metric_cards",
            source_png=None,
            source_pdf=None,
            provenance_package="reports/2026-06-23_presentation",
            use_note="Presentation-local case cards for the defended Salt 1-4 Jin progression on one consistent 1D scenario.",
            assumption_note="Uses the readable Jin progression because it is the only four-case Salt 1-4 family span on the current defended full-coverage surface.",
        ),
    ]


def copy_asset(asset: FigureAsset, output_dir: Path) -> dict[str, str]:
    png_dir = ensure_dir(output_dir / "figures" / "png")
    pdf_dir = ensure_dir(output_dir / "figures" / "pdf")
    output_paths: dict[str, str] = {}
    if asset.source_png is not None:
        if not asset.source_png.exists():
            raise FileNotFoundError(asset.source_png)
        png_path = png_dir / f"{asset.local_stem}.png"
        shutil.copy2(asset.source_png, png_path)
        output_paths["local_png"] = str(png_path)
    if asset.source_pdf is not None:
        if not asset.source_pdf.exists():
            raise FileNotFoundError(asset.source_pdf)
        pdf_path = pdf_dir / f"{asset.local_stem}.pdf"
        shutil.copy2(asset.source_pdf, pdf_path)
        output_paths["local_pdf"] = str(pdf_path)
    return output_paths


def draw_metric_card(axis: Any, title: str, value_text: str, subtitle: str, facecolor: str) -> None:
    axis.set_axis_off()
    patch = FancyBboxPatch(
        (0.02, 0.06),
        0.96,
        0.88,
        boxstyle="round,pad=0.02,rounding_size=0.04",
        linewidth=1.2,
        edgecolor="#1f2937",
        facecolor=facecolor,
        transform=axis.transAxes,
    )
    axis.add_patch(patch)
    axis.text(0.08, 0.76, title, transform=axis.transAxes, fontsize=10, fontweight="bold", color="#111827")
    axis.text(0.08, 0.42, value_text, transform=axis.transAxes, fontsize=18, fontweight="bold", color="#111827")
    axis.text(0.08, 0.18, subtitle, transform=axis.transAxes, fontsize=9, color="#374151")


def draw_case_metric_card(
    axis: Any,
    title: str,
    subtitle: str,
    metrics: list[tuple[str, str]],
    facecolor: str,
) -> None:
    axis.set_axis_off()
    patch = FancyBboxPatch(
        (0.02, 0.04),
        0.96,
        0.92,
        boxstyle="round,pad=0.02,rounding_size=0.04",
        linewidth=1.2,
        edgecolor="#1f2937",
        facecolor=facecolor,
        transform=axis.transAxes,
    )
    axis.add_patch(patch)
    axis.text(0.08, 0.82, title, transform=axis.transAxes, fontsize=14, fontweight="bold", color="#111827")
    axis.text(0.08, 0.71, subtitle, transform=axis.transAxes, fontsize=9, color="#374151")

    y_position = 0.54
    for label, value_text in metrics:
        axis.text(0.08, y_position, label, transform=axis.transAxes, fontsize=10, color="#111827")
        axis.text(
            0.92,
            y_position,
            value_text,
            transform=axis.transAxes,
            fontsize=11,
            fontweight="bold",
            color="#111827",
            ha="right",
        )
        y_position -= 0.15


def build_gap_summary_figure(output_dir: Path) -> dict[str, str]:
    surface_rows = load_csv_rows(BAKEOFF_DIR / "surface_summary.csv")
    scenario_rows = load_csv_rows(BAKEOFF_DIR / "scenario_shadow_summary.csv")
    top_surface = next(row for row in surface_rows if row["surface_label"] == "baseline_full_surface")
    defended_scenario = top_surface["best_primary_scenario"]
    total_cases = max(int(float(row["scenario_case_count"])) for row in scenario_rows)

    scenario_rows = sorted(
        scenario_rows,
        key=lambda row: (
            row["scenario"] != defended_scenario,
            row["profile_descriptor_mode"] == "ethan_cfd_informed_salt_v1",
            row["scenario"],
        ),
    )

    fig = plt.figure(figsize=(14, 7.5), constrained_layout=True)
    grid = fig.add_gridspec(2, 3, width_ratios=[1, 1, 1.55], wspace=0.35, hspace=0.28)
    card_axes = [
        fig.add_subplot(grid[0, 0]),
        fig.add_subplot(grid[0, 1]),
        fig.add_subplot(grid[1, 0]),
        fig.add_subplot(grid[1, 1]),
    ]
    coverage_axis = fig.add_subplot(grid[:, 2])

    metric_cards = [
        (
            "Energy error",
            f"{finite_float(top_surface['best_primary_mean_energy_error_pct_of_heater']):.2f}%",
            "mean |energy| vs heater",
            "#dbeafe",
        ),
        (
            "TW RMSE",
            f"{finite_float(top_surface['best_primary_mean_tw_rmse_k']):.2f} K",
            "wall temperature",
            "#dcfce7",
        ),
        (
            "TP RMSE",
            f"{finite_float(top_surface['best_primary_mean_tp_rmse_k']):.2f} K",
            "centerline temperature",
            "#fef3c7",
        ),
        (
            "Mass-flow error",
            f"{finite_float(top_surface['best_primary_mean_mass_flow_relative_error_pct_vs_cfd']):.2f}%",
            "mean relative error vs CFD",
            "#fee2e2",
        ),
    ]
    for axis, (title, value_text, subtitle, facecolor) in zip(card_axes, metric_cards):
        draw_metric_card(axis, title, value_text, subtitle, facecolor)

    y_positions = list(range(len(scenario_rows)))
    coverage_values = [int(float(row["scenario_case_count"])) for row in scenario_rows]
    accepted_values = [int(float(row["scenario_all_accepted_count"])) for row in scenario_rows]
    labels = [scenario_label(row["scenario"]) for row in scenario_rows]
    colors = [
        "#1d4ed8" if row["scenario"] == defended_scenario else ("#60a5fa" if row["profile_descriptor_mode"] == "disabled" else "#f59e0b")
        for row in scenario_rows
    ]

    coverage_axis.barh(y_positions, [total_cases] * len(scenario_rows), color="#e5e7eb", edgecolor="none", label="missing readable cases")
    coverage_axis.barh(y_positions, coverage_values, color=colors, edgecolor="#1f2937", linewidth=0.8, label="readable cases")
    for index, row in enumerate(scenario_rows):
        coverage_axis.text(
            coverage_values[index] + 0.08,
            index,
            f"{accepted_values[index]}/{coverage_values[index]} accepted",
            va="center",
            fontsize=9,
            color="#111827",
        )
        if row["scenario"] == defended_scenario:
            coverage_axis.text(
                0.04,
                index - 0.32,
                "defended full-coverage row",
                fontsize=9,
                color="#1d4ed8",
                fontweight="bold",
            )

    coverage_axis.set_yticks(y_positions)
    coverage_axis.set_yticklabels(labels, fontsize=9)
    coverage_axis.invert_yaxis()
    coverage_axis.set_xlim(0, total_cases + 1.0)
    coverage_axis.set_xlabel("Readable Salt cases available out of 4")
    coverage_axis.set_title("Readable scenario coverage and acceptance status")
    coverage_axis.grid(axis="x", linestyle="--", alpha=0.35)

    family_handles = [
        plt.Line2D([0], [0], color="#60a5fa", linewidth=8, label="baseline family"),
        plt.Line2D([0], [0], color="#f59e0b", linewidth=8, label="hybrid family"),
        plt.Line2D([0], [0], color="#1d4ed8", linewidth=8, label="defended full-coverage winner"),
    ]
    coverage_axis.legend(handles=family_handles, loc="lower right", fontsize=8, frameon=False)

    fig.suptitle(
        "Current Salt 1D gap summary for today’s presentation\n"
        "Metric cards use the best readable full-coverage row; coverage bars show why hybrid rows stay under-supported",
        fontsize=14,
    )
    paths = save_matplotlib_figure(fig, output_dir, "10_current_1d_gap_summary")
    plt.close(fig)
    return paths


def build_salt_progression_metric_cards(output_dir: Path) -> dict[str, str]:
    surface_rows = load_csv_rows(BAKEOFF_DIR / "surface_summary.csv")
    case_rows = load_csv_rows(DEFENDED_SURFACE_DIR / "case_metric_summary.csv")
    top_surface = next(row for row in surface_rows if row["surface_label"] == "baseline_full_surface")
    defended_scenario = top_surface["best_primary_scenario"]
    wanted_labels = ["Salt 1 Jin", "Salt 2 Jin", "Salt 3 Jin", "Salt 4 Jin"]
    selected_rows = []
    for label in wanted_labels:
        row = next(
            (
                item
                for item in case_rows
                if item["scenario"] == defended_scenario and item["frozen_case_label"] == label
            ),
            None,
        )
        if row is None:
            raise ValueError(f"Missing defended case row for {label}")
        selected_rows.append(row)

    fig = plt.figure(figsize=(12.5, 8.4), constrained_layout=True)
    grid = fig.add_gridspec(2, 2, wspace=0.18, hspace=0.18)
    axes = [
        fig.add_subplot(grid[0, 0]),
        fig.add_subplot(grid[0, 1]),
        fig.add_subplot(grid[1, 0]),
        fig.add_subplot(grid[1, 1]),
    ]
    facecolors = ["#dbeafe", "#dcfce7", "#fef3c7", "#fee2e2"]

    for axis, row, facecolor in zip(axes, selected_rows, facecolors):
        salt_label = row["frozen_case_label"].replace(" Jin", "")
        metrics = [
            ("Energy error", f"{finite_float(row['energy_error_pct_of_heater']):.2f}% heater"),
            ("TW RMSE", f"{finite_float(row['tw_rmse_k']):.2f} K"),
            ("TP RMSE", f"{finite_float(row['tp_rmse_k']):.2f} K"),
            ("Mass-flow error", f"{finite_float(row['mass_flow_relative_error_pct_vs_cfd']):.2f}%"),
        ]
        draw_case_metric_card(
            axis,
            salt_label,
            "latest readable Jin frozen-window row",
            metrics,
            facecolor,
        )

    fig.suptitle(
        "Salt 1-4 metric cards on the current defended full-coverage 1D scenario\n"
        "All cards use the same baseline 1.0 in, radiation-on row against the readable Jin progression",
        fontsize=14,
    )
    paths = save_matplotlib_figure(fig, output_dir, "D_salt1to4_metric_cards")
    plt.close(fig)
    return paths


def build_manifest_rows(output_dir: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    assets = presentation_assets()
    for asset in assets:
        if asset.source_png is None and asset.source_pdf is None:
            continue
        staged_paths = copy_asset(asset, output_dir)
        rows.append(
            {
                "slide_id": asset.slide_id,
                "slide_title": asset.slide_title,
                "role": asset.role,
                "local_stem": asset.local_stem,
                "local_png": staged_paths.get("local_png", ""),
                "local_pdf": staged_paths.get("local_pdf", ""),
                "canonical_source_png": str(asset.source_png.resolve()) if asset.source_png else "",
                "canonical_source_pdf": str(asset.source_pdf.resolve()) if asset.source_pdf else "",
                "provenance_package": asset.provenance_package,
                "use_note": asset.use_note,
                "assumption_note": asset.assumption_note,
            }
        )

    generated_paths = build_gap_summary_figure(output_dir)
    asset = next(item for item in assets if item.slide_id == "10")
    rows.append(
        {
            "slide_id": asset.slide_id,
            "slide_title": asset.slide_title,
            "role": asset.role,
            "local_stem": asset.local_stem,
            "local_png": generated_paths.get("png", ""),
            "local_pdf": generated_paths.get("pdf", ""),
            "canonical_source_png": str((BAKEOFF_DIR / "surface_summary.csv").resolve()),
            "canonical_source_pdf": str((BAKEOFF_DIR / "scenario_shadow_summary.csv").resolve()),
            "provenance_package": asset.provenance_package,
            "use_note": asset.use_note,
            "assumption_note": asset.assumption_note,
        }
    )
    generated_paths = build_salt_progression_metric_cards(output_dir)
    asset = next(item for item in assets if item.slide_id == "D")
    rows.append(
        {
            "slide_id": asset.slide_id,
            "slide_title": asset.slide_title,
            "role": asset.role,
            "local_stem": asset.local_stem,
            "local_png": generated_paths.get("png", ""),
            "local_pdf": generated_paths.get("pdf", ""),
            "canonical_source_png": str((DEFENDED_SURFACE_DIR / "case_metric_summary.csv").resolve()),
            "canonical_source_pdf": str((BAKEOFF_DIR / "surface_summary.csv").resolve()),
            "provenance_package": asset.provenance_package,
            "use_note": asset.use_note,
            "assumption_note": asset.assumption_note,
        }
    )
    return sorted(rows, key=lambda row: row["slide_id"])


def build_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "generated_at": iso_timestamp(),
        "asset_count": len(rows),
        "main_slide_count": sum(1 for row in rows if row["role"] == "main"),
        "backup_slide_count": sum(1 for row in rows if row["role"] == "backup"),
        "local_png_paths": [row["local_png"] for row in rows],
        "local_pdf_paths": [row["local_pdf"] for row in rows],
    }


def main() -> int:
    args = parse_args()
    output_dir = ensure_dir(Path(args.presentation_dir))
    rows = build_manifest_rows(output_dir)
    csv_dump(
        output_dir / "figures" / "figure_manifest.csv",
        [
            "slide_id",
            "slide_title",
            "role",
            "local_stem",
            "local_png",
            "local_pdf",
            "canonical_source_png",
            "canonical_source_pdf",
            "provenance_package",
            "use_note",
            "assumption_note",
        ],
        rows,
    )
    summary = build_summary(rows)
    json_dump(output_dir / "figures" / "figure_pack_summary.json", summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
