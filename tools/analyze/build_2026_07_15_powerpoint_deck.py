#!/usr/bin/env python3
"""Build July 15 presentation figures and a PPTX deck.

The environment does not provide python-pptx, so this script creates
presentation-ready PNG figures, full-slide PNG renderings, and then packages
the slide PNGs into a minimal OOXML PowerPoint file.
"""

from __future__ import annotations

import csv
import html
import json
import math
import os
import textwrap
import zipfile
from dataclasses import dataclass
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib-ethan-runs")

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Wedge
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "work_products/2026-07/2026-07-14/2026-07-14_powerpoint_figures_and_deck"
FIG = OUT / "figures"
SLIDES = OUT / "slides"
REPORT_DECK = ROOT / "reports/thesis_dossier/2026-07-15_powerpoint_deck.pptx"
OUTLINE = ROOT / "reports/thesis_dossier/2026-07-15_powerpoint_outline.md"

CASE_MATRIX = ROOT / "work_products/2026-07/2026-07-14/2026-07-14_flow_rate_temperature_bc_response_study/case_bc_response_matrix.csv"
PM5_MATRIX = ROOT / "work_products/2026-07/2026-07-14/2026-07-14_corrected_q_pm5_admission_split_processing/corrected_q_pm5_split_admission_matrix.csv"
GATES = ROOT / "work_products/2026-07/2026-07-14/2026-07-14_scientific_closure_forward_v1_execution_dashboard/gate_landing_requirements.csv"
WORKSTREAM = ROOT / "work_products/2026-07/2026-07-14/2026-07-14_scientific_closure_forward_v1_execution_dashboard/workstream_execution_dashboard.csv"
HEAT_LEG = ROOT / "work_products/2026-07/2026-07-14/2026-07-14_best_predictive_heat_loss_discrepancy/best_predictive_leg_heat_loss_discrepancy.csv"
LITREV = ROOT / "reports/2026-07/2026-07-13/2026-07-13_litrev_lessons_and_research_pathways/litrev_to_current_evidence_crosswalk.csv"

W, H = 1600, 900
EMU_W, EMU_H = 12192000, 6858000
BG = "#f7f8fb"
INK = "#1f2933"
MUTED = "#59636e"
BLUE = "#2f6f9f"
GREEN = "#2c8c5a"
YELLOW = "#d79b24"
RED = "#c43c3c"
PURPLE = "#7d5ac6"
GRAY = "#d8dde6"


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/dejavu/DejaVuSans.ttf",
    ]
    for c in candidates:
        if Path(c).exists():
            return ImageFont.truetype(c, size=size)
    return ImageFont.load_default()


def save_matplotlib(fig: plt.Figure, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=170, bbox_inches="tight")
    plt.close(fig)


def wrap_text(text: str, width: int) -> list[str]:
    lines: list[str] = []
    for part in text.split("\n"):
        wrapped = textwrap.wrap(part, width=width, break_long_words=False)
        lines.extend(wrapped if wrapped else [""])
    return lines


def draw_wrapped(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str, fnt, fill=INK, width=58, line_gap=8) -> int:
    x, y = xy
    for line in wrap_text(text, width):
        draw.text((x, y), line, font=fnt, fill=fill)
        y += fnt.size + line_gap
    return y


def rounded(draw: ImageDraw.ImageDraw, box, fill, outline="#000000", radius=18, width=2) -> None:
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def arrow(ax, start, end, color=INK, lw=2.5, style="-|>") -> None:
    ax.annotate("", xy=end, xytext=start, arrowprops=dict(arrowstyle=style, lw=lw, color=color))


def fig_loop_schematic() -> Path:
    path = FIG / "01_loop_schematic.png"
    fig, ax = plt.subplots(figsize=(10, 5.8))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 7)
    ax.axis("off")
    ax.plot([2, 2, 8, 8, 2], [1, 6, 6, 1, 1], color=BLUE, lw=10, solid_capstyle="round")
    arrow(ax, (2, 1.4), (2, 5.3), GREEN, 3)
    arrow(ax, (2.8, 6), (7.2, 6), GREEN, 3)
    arrow(ax, (8, 5.5), (8, 1.7), GREEN, 3)
    arrow(ax, (7.2, 1), (2.8, 1), GREEN, 3)
    labels = [
        (1.0, 3.5, "Upcomer /\ntest section", "#e9f5ef"),
        (3.6, 6.35, "Cooling branch", "#eef3fb"),
        (8.25, 3.4, "Downcomer", "#eef3fb"),
        (3.0, 0.2, "Heated lower leg", "#fff4df"),
        (6.7, 0.2, "Junctions /\nstubs", "#fdecec"),
    ]
    for x, y, text, fc in labels:
        ax.text(x, y, text, ha="center", va="center", fontsize=12, color=INK,
                bbox=dict(boxstyle="round,pad=0.35", fc=fc, ec="#9aa6b2"))
    ax.text(5, 6.85, "TAMU molten-salt natural-circulation loop: branchwise ledger", ha="center", fontsize=15, weight="bold")
    save_matplotlib(fig, path)
    return path


def fig_predictive_contract() -> Path:
    path = FIG / "02_predictive_contract.png"
    fig, ax = plt.subplots(figsize=(10.5, 5.6))
    ax.axis("off")
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)
    boxes = [
        (0.4, 3.5, 2.4, 1.4, "Setup inputs\ngeometry, powers,\nBC metadata", "#eaf4ff"),
        (3.8, 3.35, 2.5, 1.7, "1D Fluid model\nsetup-only runtime", "#eef8ee"),
        (7.3, 3.5, 2.2, 1.4, "Predictions\nmdot, pressure,\ntemperatures", "#fff4df"),
    ]
    for x, y, w, h, text, fc in boxes:
        ax.add_patch(plt.Rectangle((x, y), w, h, fc=fc, ec="#7b8794", lw=2))
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=12, weight="bold", color=INK)
    arrow(ax, (2.8, 4.2), (3.75, 4.2), BLUE)
    arrow(ax, (6.35, 4.2), (7.25, 4.2), BLUE)
    ax.add_patch(plt.Rectangle((1.0, 0.55), 8.0, 1.45, fc="#fdecec", ec=RED, lw=2))
    ax.text(5, 1.55, "Targets / diagnostics only - not runtime predictive inputs", ha="center", va="center", fontsize=13, weight="bold", color=RED)
    ax.text(5, 0.95, "CFD mdot   |   realized wallHeatFlux / cooler duty   |   validation temperatures", ha="center", va="center", fontsize=12, color=INK)
    arrow(ax, (5, 2.0), (5, 3.25), RED, 2, "-[")
    ax.text(5, 5.65, "Predictive contract", ha="center", fontsize=17, weight="bold")
    save_matplotlib(fig, path)
    return path


def fig_evidence_ladder() -> Path:
    path = FIG / "03_evidence_ladder_dashboard.png"
    fig, ax = plt.subplots(figsize=(11.0, 5.8))
    ax.axis("off")
    rows = [
        ("Predictive", "setup-only inputs, held-out score", GREEN),
        ("Calibrated", "fit on declared training with split limits", BLUE),
        ("Diagnostic", "physics/screening; not closure-fit rows", YELLOW),
        ("Reference", "limits and comparators only", "#8391a1"),
        ("Blocked / pending", "named gate required before use", RED),
    ]
    y = 0.82
    for i, (name, desc, color) in enumerate(rows):
        ax.add_patch(plt.Rectangle((0.08, y - i * 0.15), 0.18, 0.095, fc=color, ec="white"))
        ax.text(0.29, y + 0.045 - i * 0.15, name, fontsize=14, weight="bold", va="center", color=INK)
        ax.text(0.52, y + 0.045 - i * 0.15, desc, fontsize=12, va="center", color=MUTED)
    lane_rows = [
        ("CFD rows", "admitted split: Salt2/Salt3/Salt4; +/-5Q sensitivity"),
        ("Hydraulics", "API progress; K/F6 still blocked"),
        ("Heat loss", "diagnostic wrong-location result"),
        ("Internal Nu", "recirculation rule; 0 fit rows"),
        ("Forward-v1", "no-go until gates land"),
    ]
    for j, (lane, state) in enumerate(lane_rows):
        y0 = 0.08 + j * 0.105
        ax.add_patch(plt.Rectangle((0.08, y0), 0.84, 0.075, fc="#f2f4f7", ec="#cbd2dc"))
        ax.text(0.11, y0 + 0.038, lane, fontsize=10.5, weight="bold", va="center", color=INK)
        ax.text(0.31, y0 + 0.038, state, fontsize=10.2, va="center", color=MUTED)
    ax.text(0.5, 0.96, "Evidence language for the deck", ha="center", fontsize=17, weight="bold")
    save_matplotlib(fig, path)
    return path


def fig_gate_dashboard() -> Path:
    path = FIG / "04_gate_dashboard.png"
    df = pd.read_csv(WORKSTREAM).head(7)
    fig, ax = plt.subplots(figsize=(12.2, 6.2))
    ax.axis("off")
    display = [
        ("CFD admission", "landed + pending", "yellow"),
        ("Matched planes", "pending job", "red"),
        ("Internal Nu", "0 fit rows", "red"),
        ("F6 hydraulics", "blocked", "red"),
        ("Boundary API", "architecture only", "yellow"),
        ("Forward-v1", "no-go", "red"),
        ("Candidate inventory", "split locked", "green"),
    ]
    colors = {"green": GREEN, "yellow": YELLOW, "red": RED}
    for i, (lane, state, c) in enumerate(display):
        y = 0.82 - i * 0.105
        ax.add_patch(plt.Rectangle((0.05, y), 0.32, 0.072, fc="#f7f8fb", ec="#b8c0ca"))
        ax.add_patch(plt.Rectangle((0.39, y), 0.16, 0.072, fc=colors[c], ec="white"))
        ax.add_patch(plt.Rectangle((0.57, y), 0.38, 0.072, fc="#f7f8fb", ec="#b8c0ca"))
        ax.text(0.07, y + 0.036, lane, fontsize=11.5, weight="bold", va="center", color=INK)
        ax.text(0.47, y + 0.036, state, fontsize=10.5, ha="center", va="center", color="white", weight="bold")
        if i < len(df):
            ax.text(0.59, y + 0.036, str(df.iloc[i]["next_action"])[:80], fontsize=8.6, va="center", color=MUTED)
    ax.text(0.5, 0.95, "One-day gate status: progress, but final forward-v1 remains blocked", ha="center", fontsize=15.5, weight="bold")
    save_matplotlib(fig, path)
    return path


def fig_pm5_split_matrix() -> Path:
    path = FIG / "05_pm5_split_matrix.png"
    df = pd.read_csv(PM5_MATRIX)
    fig, ax = plt.subplots(figsize=(11.8, 5.5))
    ax.axis("off")
    cols = ["case_key", "q_ratio", "current_split_family", "closure_fit_admissible_terminal_gate", "can_expand_training_now"]
    data = df[cols].copy()
    data.columns = ["case", "Q ratio", "split family", "terminal gate", "training expansion"]
    table = ax.table(cellText=data.values, colLabels=data.columns, cellLoc="center", colLoc="center", loc="center")
    table.auto_set_font_size(False)
    table.set_fontsize(9.5)
    table.scale(1, 1.7)
    for (r, c), cell in table.get_celld().items():
        if r == 0:
            cell.set_facecolor("#2f6f9f")
            cell.set_text_props(color="white", weight="bold")
        elif c == 4:
            cell.set_facecolor("#fdecec")
            cell.set_text_props(color=RED, weight="bold")
        elif c == 3:
            cell.set_facecolor("#e9f5ef")
            cell.set_text_props(color=GREEN, weight="bold")
        else:
            cell.set_facecolor("#f7f8fb")
    ax.text(0.5, 0.93, "+/-5Q corrected-Q rows: harvested, but not independent training rows", ha="center", fontsize=15, weight="bold")
    save_matplotlib(fig, path)
    return path


def fig_mdot_probe_temperature() -> Path:
    path = FIG / "06_mdot_vs_probe_temperature.png"
    df = pd.read_csv(CASE_MATRIX)
    main = df[df["case_key"].isin(["salt2_jin", "salt3_jin", "salt4_jin"])].copy()
    fig, ax = plt.subplots(figsize=(9.8, 5.7))
    colors = {"training": GREEN, "validation": BLUE, "holdout": PURPLE}
    for _, r in main.iterrows():
        ax.scatter(r["timeseries_probe_T_avg_K"], r["mdot_mean_abs_kg_s"], s=120, color=colors.get(r["split_or_use_status"], BLUE), edgecolor="black", zorder=3)
        ax.text(r["timeseries_probe_T_avg_K"] + 0.45, r["mdot_mean_abs_kg_s"], f"{r['fluid']} ({r['split_or_use_status']})", fontsize=10, va="center")
    main = main.sort_values("timeseries_probe_T_avg_K")
    ax.plot(main["timeseries_probe_T_avg_K"], main["mdot_mean_abs_kg_s"], color="#5b6673", lw=2, zorder=2)
    ax.set_xlabel("Time-series probe temperature average [K]")
    ax.set_ylabel("|mdot| [kg/s]")
    ax.set_title("Observed mainline ordering: |mdot| rises with probe temperature")
    ax.grid(True, alpha=0.25)
    ax.text(0.02, 0.96, "Observational only: temperature, heater, cooler, and BCs co-vary", transform=ax.transAxes, fontsize=10, va="top", color=RED,
            bbox=dict(fc="white", ec=RED, boxstyle="round,pad=0.3"))
    save_matplotlib(fig, path)
    return path


def fig_confounding() -> Path:
    path = FIG / "07_confounding_and_perturbation.png"
    fig, ax = plt.subplots(figsize=(10.5, 5.8))
    ax.axis("off")
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)
    centers = {
        "Salt case": (1.3, 3.1),
        "Probe T": (3.4, 4.6),
        "Heater power": (3.4, 3.25),
        "Cooler power": (3.4, 1.9),
        "External h": (3.4, 0.65),
        "mdot": (7.5, 3.1),
    }
    for label, (x, y) in centers.items():
        fc = "#eaf4ff" if label == "Salt case" else "#fff4df" if label != "mdot" else "#e9f5ef"
        ax.add_patch(plt.Rectangle((x - 0.8, y - 0.35), 1.6, 0.7, fc=fc, ec="#7b8794", lw=1.8))
        ax.text(x, y, label, ha="center", va="center", fontsize=11, weight="bold")
    for target in ["Probe T", "Heater power", "Cooler power", "External h"]:
        arrow(ax, (2.1, 3.1), (centers[target][0] - 0.85, centers[target][1]), BLUE, 2)
        arrow(ax, (centers[target][0] + 0.85, centers[target][1]), (6.65, 3.1), "#5b6673", 1.7)
    ax.text(5.1, 5.45, "Correlations are descriptive, not causal coefficients", ha="center", fontsize=14, weight="bold")
    ax.add_patch(plt.Rectangle((5.5, 0.45), 4.0, 1.05, fc="#fdecec", ec=RED, lw=2))
    ax.text(7.5, 1.18, "Old Q perturbations: false-steady provenance", ha="center", fontsize=10.5, color=RED, weight="bold")
    ax.text(7.5, 0.78, "Observed mdot moves were far below expected operating-point response", ha="center", fontsize=9.5, color=INK)
    save_matplotlib(fig, path)
    return path


def fig_heat_loss_grouped() -> Path:
    path = FIG / "08_heat_loss_leg_grouped.png"
    df = pd.read_csv(HEAT_LEG)
    order = ["lower_leg", "upcomer", "cooling_branch", "downcomer", "junction"]
    labels = {
        "lower_leg": "Lower\nleg",
        "upcomer": "Upcomer /\ntest",
        "cooling_branch": "Cooling\nbranch",
        "downcomer": "Downcomer",
        "junction": "Junctions /\nstubs",
    }
    g = df.groupby("leg")[["model_total_loss_W", "cfd_realized_loss_W"]].mean().loc[order]
    x = np.arange(len(g))
    width = 0.36
    fig, ax = plt.subplots(figsize=(11, 5.9))
    ax.bar(x - width / 2, g["model_total_loss_W"], width, label="1D model loss", color=BLUE)
    ax.bar(x + width / 2, g["cfd_realized_loss_W"], width, label="CFD realized loss", color=YELLOW)
    for i, leg in enumerate(order):
        delta = g.loc[leg, "model_total_loss_W"] - g.loc[leg, "cfd_realized_loss_W"]
        ax.text(i, max(g.loc[leg]) + 4, f"{delta:+.1f} W", ha="center", fontsize=9, color=RED if delta < 0 else INK, weight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels([labels[o] for o in order])
    ax.set_ylabel("Mean heat loss across Salt2-4 [W]")
    ax.set_title("Aggregate heat balance hides wrong-location heat loss")
    ax.legend(loc="upper left")
    ax.grid(axis="y", alpha=0.25)
    save_matplotlib(fig, path)
    return path


def fig_thermal_ledger() -> Path:
    path = FIG / "09_thermal_ledger.png"
    fig, ax = plt.subplots(figsize=(11.2, 5.9))
    ax.axis("off")
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)
    lanes = [
        ("Heater realized\nfraction", "#fff4df"),
        ("Cooler / HX\nUA or effectiveness", "#eaf4ff"),
        ("Wall conduction\nand shell drive", "#f1f5f9"),
        ("External convection\nh, Ta", "#e9f5ef"),
        ("Radiation metadata\nemissivity, Tsur", "#f2ecfb"),
        ("Storage / residual\nnot Nu", "#fdecec"),
    ]
    for i, (label, fc) in enumerate(lanes):
        x = 0.35 + (i % 3) * 3.2
        y = 3.7 - (i // 3) * 1.8
        ax.add_patch(plt.Rectangle((x, y), 2.75, 1.0, fc=fc, ec="#7b8794", lw=1.8))
        ax.text(x + 1.375, y + 0.5, label, ha="center", va="center", fontsize=11, weight="bold")
        arrow(ax, (x + 1.375, y), (5, 2.95), "#7b8794", 1.5)
    ax.add_patch(plt.Rectangle((3.6, 2.5), 2.8, 0.75, fc="#ffffff", ec=BLUE, lw=2.2))
    ax.text(5, 2.88, "Setup-only thermal boundary model", ha="center", va="center", fontsize=12, weight="bold", color=BLUE)
    ax.text(5, 0.6, "Guardrail: realized CFD wallHeatFlux and cooler duty are score targets, not runtime inputs", ha="center", fontsize=11, color=RED,
            bbox=dict(fc="white", ec=RED, boxstyle="round,pad=0.35"))
    ax.text(5, 5.55, "Thermal ledger lanes to implement", ha="center", fontsize=16, weight="bold")
    save_matplotlib(fig, path)
    return path


def fig_pressure_ledger() -> Path:
    path = FIG / "10_pressure_ledger.png"
    fig, ax = plt.subplots(figsize=(11.2, 5.5))
    ax.axis("off")
    terms = [
        ("Straight\nfriction", GREEN),
        ("Reset /\ndevelopment", YELLOW),
        ("Component\nK", BLUE),
        ("Cluster\nK", PURPLE),
        ("Buoyancy /\nkinetic", "#8391a1"),
        ("Residual\nblocked", RED),
    ]
    x0 = 0.05
    for i, (t, c) in enumerate(terms):
        x = x0 + i * 0.155
        ax.add_patch(plt.Rectangle((x, 0.44), 0.125, 0.25, fc=c, ec="white"))
        ax.text(x + 0.0625, 0.565, t, ha="center", va="center", fontsize=9.5, color="white", weight="bold")
        if i < len(terms) - 1:
            ax.text(x + 0.14, 0.565, "+", ha="center", va="center", fontsize=22, color=INK, weight="bold")
    ax.text(0.5, 0.82, "Pressure ledger: no global friction multiplier", ha="center", fontsize=16, weight="bold")
    ax.text(0.5, 0.25, "Current state: API bridge exists, but component/cluster K has 0 fit-admissible rows; F6 waits for admitted Re-variation.", ha="center", fontsize=11, color=MUTED)
    save_matplotlib(fig, path)
    return path


def fig_upcomer_recirculation() -> Path:
    path = FIG / "11_upcomer_recirculation_schematic.png"
    fig, ax = plt.subplots(figsize=(10, 5.8))
    ax.axis("off")
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)
    ax.add_patch(plt.Circle((3, 3), 1.7, fc="#eaf4ff", ec=BLUE, lw=3))
    ax.add_patch(Wedge((3, 3), 1.65, 105, 255, fc="#fdecec", ec=RED, alpha=0.9))
    ax.text(3, 4.85, "Matched upcomer plane", ha="center", fontsize=13, weight="bold")
    arrow(ax, (3.1, 1.55), (3.1, 4.45), GREEN, 3)
    arrow(ax, (2.15, 4.25), (2.15, 1.8), RED, 3)
    ax.text(4.85, 4.2, "Forward core flow", fontsize=11, color=GREEN, weight="bold")
    ax.text(0.65, 1.15, "Reverse-flow region", fontsize=11, color=RED, weight="bold")
    ax.add_patch(plt.Rectangle((5.7, 1.2), 3.8, 3.5, fc="#f7f8fb", ec="#aab3bf", lw=1.8))
    metrics = [
        "Re_upcomer: 71.125-134.883",
        "Backflow fraction: 0.278 -> 0.172",
        "Ri_median: 1.498-2.634",
        "Single-stream Nu/f_D/K invalid",
    ]
    for i, m in enumerate(metrics):
        ax.text(5.95, 4.3 - i * 0.65, m, fontsize=11, color=INK if i < 3 else RED, weight="bold" if i == 3 else "normal")
    ax.text(5, 5.55, "Recirculation is a scientific/admission result", ha="center", fontsize=16, weight="bold")
    save_matplotlib(fig, path)
    return path


def fig_residual_ownership() -> Path:
    path = FIG / "12_residual_ownership.png"
    fig, ax = plt.subplots(figsize=(11, 5.8))
    ax.axis("off")
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)
    ax.add_patch(plt.Circle((5, 3), 0.9, fc="#eaf4ff", ec=BLUE, lw=2.5))
    ax.text(5, 3.05, "Internal\nNu/HTC", ha="center", va="center", fontsize=12, weight="bold", color=BLUE)
    items = [
        ("heater\nrealization", 2.1, 4.8),
        ("cooler/HX\nduty", 5.0, 5.25),
        ("passive\nwall loss", 7.9, 4.8),
        ("radiation\nmetadata", 8.4, 2.2),
        ("storage /\ntransient", 5.0, 0.75),
        ("branch mixing /\nrecirculation", 1.6, 2.2),
        ("hydraulic\nresidual", 3.1, 0.95),
        ("sign / heat\nbalance", 6.9, 0.95),
    ]
    for label, x, y in items:
        ax.add_patch(plt.Rectangle((x - 0.75, y - 0.35), 1.5, 0.7, fc="#fdecec", ec=RED, lw=1.5))
        ax.text(x, y, label, ha="center", va="center", fontsize=9.5, color=RED, weight="bold")
        arrow(ax, (x, y), (5, 3), RED, 1.2, "-[")
    ax.text(5, 5.75, "Residuals forbidden from being hidden inside Nu", ha="center", fontsize=15.5, weight="bold")
    save_matplotlib(fig, path)
    return path


def fig_gate_funnel() -> Path:
    path = FIG / "13_forward_v1_gate_funnel.png"
    df = pd.read_csv(GATES)
    fig, ax = plt.subplots(figsize=(11.2, 5.8))
    ax.axis("off")
    stages = [
        ("Terminal /\nsplit admission", "blocked"),
        ("Matched\nplanes", "pending"),
        ("F6\nRe variation", "blocked"),
        ("Setup-only\nboundaries", "blocked"),
        ("Internal Nu\nreopen/no-fit", "blocked"),
        ("Forward-v1\nrefresh", "no-go"),
    ]
    widths = [8.8, 7.4, 6.2, 5.0, 3.8, 2.7]
    for i, (label, status) in enumerate(stages):
        y = 5.1 - i * 0.75
        w = widths[i]
        x = 5 - w / 2
        fc = YELLOW if status == "pending" else RED if status in {"blocked", "no-go"} else GREEN
        ax.add_patch(plt.Polygon([(x, y), (x + w, y), (x + w - 0.35, y - 0.5), (x + 0.35, y - 0.5)], fc=fc, ec="white"))
        ax.text(5, y - 0.25, f"{label}  |  {status}", ha="center", va="center", fontsize=10.5, color="white", weight="bold")
    ax.text(5, 5.75, "Forward-v1 gate funnel: no-go until upstream gates pass", ha="center", fontsize=15.5, weight="bold")
    save_matplotlib(fig, path)
    return path


def fig_next_work() -> Path:
    path = FIG / "14_next_work_roadmap.png"
    fig, ax = plt.subplots(figsize=(11.2, 5.8))
    ax.axis("off")
    headers = [("Evidence gates", 0.08), ("Model implementation gates", 0.54)]
    for header, x in headers:
        ax.add_patch(plt.Rectangle((x, 0.82), 0.38, 0.09, fc=BLUE, ec="white"))
        ax.text(x + 0.19, 0.865, header, ha="center", va="center", fontsize=13, color="white", weight="bold")
    left = ["Harvest matched pressure/upcomer planes", "Admit or demote +/-5Q rows by split policy", "Extract ordinary/transition upcomer anchors", "Validate F6 only after Re variation"]
    right = ["Build setup-only heater fraction", "Replace imposed cooler duty with HX UA/effectiveness", "Add wall/external/radiation dictionaries", "Add junction/stub heat-loss coverage"]
    for i, text in enumerate(left):
        y = 0.68 - i * 0.14
        ax.add_patch(plt.Rectangle((0.08, y), 0.38, 0.1, fc="#f7f8fb", ec="#cbd2dc"))
        ax.text(0.10, y + 0.05, text, va="center", fontsize=10.2, color=INK)
    for i, text in enumerate(right):
        y = 0.68 - i * 0.14
        ax.add_patch(plt.Rectangle((0.54, y), 0.38, 0.1, fc="#f7f8fb", ec="#cbd2dc"))
        ax.text(0.56, y + 0.05, text, va="center", fontsize=10.2, color=INK)
    ax.text(0.5, 0.96, "Next work: land evidence gates and implement physical boundary lanes", ha="center", fontsize=15.5, weight="bold")
    save_matplotlib(fig, path)
    return path


def fig_blockers() -> Path:
    path = FIG / "15_blocker_table.png"
    blockers = [
        "closure-QOI mesh/GCI",
        "thermal CFD-to-1D parity",
        "predictive heater/cooler/wall submodels",
        "upcomer onset data sparsity",
        "Fluid external-boundary API gap",
        "F6/Re friction correction validation",
    ]
    stale = ["OF12 reconstruction", "no mesh for GCI", "CFD-no-radiation", "reconstructed-T corruption"]
    fig, ax = plt.subplots(figsize=(11, 5.6))
    ax.axis("off")
    ax.add_patch(plt.Rectangle((0.07, 0.75), 0.42, 0.1, fc=RED, ec="white"))
    ax.add_patch(plt.Rectangle((0.53, 0.75), 0.40, 0.1, fc=GREEN, ec="white"))
    ax.text(0.28, 0.8, "Real open blockers", ha="center", va="center", fontsize=13, color="white", weight="bold")
    ax.text(0.73, 0.8, "Do not re-report as open", ha="center", va="center", fontsize=13, color="white", weight="bold")
    for i, b in enumerate(blockers):
        ax.text(0.09, 0.67 - i * 0.09, f"- {b}", fontsize=11, color=INK)
    for i, s in enumerate(stale):
        ax.text(0.55, 0.67 - i * 0.09, f"- {s}", fontsize=11, color=INK)
    ax.text(0.5, 0.94, "Blocker hygiene for the meeting", ha="center", fontsize=16, weight="bold")
    save_matplotlib(fig, path)
    return path


def fig_litrev_crosswalk() -> Path:
    path = FIG / "16_litrev_crosswalk_summary.png"
    df = pd.read_csv(LITREV)
    buckets = {
        "Tried / demoted": df[df["tried_status"].isin(["tried_diagnostic", "tried_rejected_or_demoted"])]["model_family"].tolist()[:6],
        "Partly tried / gated": df[df["tried_status"] == "partially_tried_needs_gate"]["model_family"].tolist()[:6],
        "Not tried / future": df[df["tried_status"] == "not_tried"]["model_family"].tolist()[:6],
    }
    fig, ax = plt.subplots(figsize=(11.4, 5.8))
    ax.axis("off")
    xs = [0.06, 0.37, 0.68]
    colors = [YELLOW, BLUE, "#8391a1"]
    for (title, items), x, c in zip(buckets.items(), xs, colors):
        ax.add_patch(plt.Rectangle((x, 0.78), 0.27, 0.1, fc=c, ec="white"))
        ax.text(x + 0.135, 0.83, title, ha="center", va="center", fontsize=11.5, color="white", weight="bold")
        ax.add_patch(plt.Rectangle((x, 0.18), 0.27, 0.58, fc="#f7f8fb", ec="#cbd2dc"))
        for i, item in enumerate(items):
            ax.text(x + 0.02, 0.70 - i * 0.085, f"- {item}", fontsize=9.5, color=INK)
    ax.text(0.5, 0.95, "LitRev crosswalk: branchwise ledger, not global coefficients", ha="center", fontsize=15.5, weight="bold")
    save_matplotlib(fig, path)
    return path


def fig_say_avoid() -> Path:
    path = FIG / "17_say_avoid.png"
    pairs = [
        ("Forward-v0 executes; final forward-v1 is no-go", "The predictive model is admitted"),
        ("Heat-loss placement diagnosis identifies wrong-location losses", "Final predictive HX is validated"),
        ("Recirculation invalidates single-stream labels", "Nu is merely blocked"),
        ("+/-5Q rows are sensitivity/admission evidence", "+/-5Q rows expand training today"),
    ]
    fig, ax = plt.subplots(figsize=(11.2, 5.7))
    ax.axis("off")
    ax.add_patch(plt.Rectangle((0.06, 0.78), 0.42, 0.1, fc=GREEN, ec="white"))
    ax.add_patch(plt.Rectangle((0.52, 0.78), 0.42, 0.1, fc=RED, ec="white"))
    ax.text(0.27, 0.83, "Say", ha="center", va="center", fontsize=14, color="white", weight="bold")
    ax.text(0.73, 0.83, "Avoid", ha="center", va="center", fontsize=14, color="white", weight="bold")
    for i, (say, avoid) in enumerate(pairs):
        y = 0.65 - i * 0.135
        ax.add_patch(plt.Rectangle((0.06, y), 0.42, 0.11, fc="#e9f5ef", ec="#cbd2dc"))
        ax.add_patch(plt.Rectangle((0.52, y), 0.42, 0.11, fc="#fdecec", ec="#cbd2dc"))
        ax.text(0.08, y + 0.055, say, va="center", fontsize=9.5, color=INK)
        ax.text(0.54, y + 0.055, avoid, va="center", fontsize=9.5, color=INK)
    ax.text(0.5, 0.95, "Claim boundaries for live narration", ha="center", fontsize=15.5, weight="bold")
    save_matplotlib(fig, path)
    return path


@dataclass
class Slide:
    title: str
    bullets: list[str]
    figure: Path


def make_slide_png(slide: Slide, idx: int) -> Path:
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)
    title_font = font(44, True)
    bullet_font = font(27)
    small_font = font(18)
    draw.text((55, 42), slide.title, font=title_font, fill=INK)
    draw.line((55, 105, 1545, 105), fill="#cbd2dc", width=3)
    y = 150
    for bullet in slide.bullets:
        draw.text((70, y), "•", font=bullet_font, fill=BLUE)
        y = draw_wrapped(draw, (105, y), bullet, bullet_font, fill=INK, width=42, line_gap=6) + 8
    fig_img = Image.open(slide.figure).convert("RGB")
    max_w, max_h = 720, 610
    fig_img.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)
    x = 835 + (max_w - fig_img.width) // 2
    y_fig = 165 + (max_h - fig_img.height) // 2
    draw.rounded_rectangle((815, 135, 1570, 790), radius=24, fill="#ffffff", outline="#d4dae3", width=2)
    img.paste(fig_img, (x, y_fig))
    draw.text((60, 830), f"AGENT-367 generated deck asset | slide {idx}", font=small_font, fill="#7b8794")
    out = SLIDES / f"slide_{idx:02d}.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out)
    return out


def content_types(n: int) -> str:
    overrides = "\n".join(
        f'<Override PartName="/ppt/slides/slide{i}.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>'
        for i in range(1, n + 1)
    )
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Default Extension="png" ContentType="image/png"/>
<Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>
{overrides}
</Types>'''


def presentation_xml(n: int) -> str:
    slds = "\n".join(
        f'<p:sldId id="{255+i}" r:id="rId{i}"/>' for i in range(1, n + 1)
    )
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:presentation xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
<p:sldIdLst>{slds}</p:sldIdLst>
<p:sldSz cx="{EMU_W}" cy="{EMU_H}" type="wide"/>
<p:notesSz cx="6858000" cy="9144000"/>
</p:presentation>'''


def presentation_rels(n: int) -> str:
    rels = "\n".join(
        f'<Relationship Id="rId{i}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide{i}.xml"/>'
        for i in range(1, n + 1)
    )
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
{rels}
</Relationships>'''


def root_rels() -> str:
    return '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="ppt/presentation.xml"/>
</Relationships>'''


def slide_xml(idx: int) -> str:
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
<p:cSld><p:spTree>
<p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr/>
<p:pic>
<p:nvPicPr><p:cNvPr id="2" name="slide_{idx:02d}.png"/><p:cNvPicPr/><p:nvPr/></p:nvPicPr>
<p:blipFill><a:blip r:embed="rId1"/><a:stretch><a:fillRect/></a:stretch></p:blipFill>
<p:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{EMU_W}" cy="{EMU_H}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></p:spPr>
</p:pic>
</p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr>
</p:sld>'''


def slide_rels(idx: int) -> str:
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="../media/slide_{idx:02d}.png"/>
</Relationships>'''


def build_pptx(slide_pngs: list[Path], pptx_path: Path) -> None:
    pptx_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(pptx_path, "w", compression=zipfile.ZIP_DEFLATED) as z:
        n = len(slide_pngs)
        z.writestr("[Content_Types].xml", content_types(n))
        z.writestr("_rels/.rels", root_rels())
        z.writestr("ppt/presentation.xml", presentation_xml(n))
        z.writestr("ppt/_rels/presentation.xml.rels", presentation_rels(n))
        for idx, png in enumerate(slide_pngs, start=1):
            z.writestr(f"ppt/slides/slide{idx}.xml", slide_xml(idx))
            z.writestr(f"ppt/slides/_rels/slide{idx}.xml.rels", slide_rels(idx))
            z.write(png, f"ppt/media/slide_{idx:02d}.png")


def build_slides(figs: dict[str, Path]) -> list[Slide]:
    return [
        Slide("From CFD Replay To Admission-Gated 1D Prediction", ["TAMU molten-salt natural-circulation loop", "What changed today, what is trustworthy, what remains blocked", "Core story: gate discipline before prediction claims"], figs["loop"]),
        Slide("What We Are Trying To Prove", ["Setup-only 1D model: physical inputs in", "Outputs: mdot, pressure losses, branch/sensor temperatures", "CFD mdot, wallHeatFlux, and validation temperatures stay targets"], figs["contract"]),
        Slide("How We Classified Today's Evidence", ["Predictive and calibrated evidence are tightly bounded", "Diagnostic evidence explains physics but is not fit input", "Blocked/pending evidence needs a named gate before use"], figs["ladder"]),
        Slide("What Changed Today", ["4 corrected +/-5Q rows harvested; 0 independent training expansion rows", "12 hydraulic tap rows resolved; 0 fit-admissible component/cluster K rows", "Upcomer recirculation invalidates single-stream Nu/f_D/K labels"], figs["dashboard"]),
        Slide("Which CFD Rows Can Support Claims?", ["Salt2/Salt3/Salt4 split remains training/validation/holdout", "+/-5Q rows are perturbation-family evidence", "No silent training expansion before perturbation split policy"], figs["pm5"]),
        Slide("Mainline CFD Shows A Clean Monotonic Ordering", ["Salt2 to Salt4: mdot and probe temperature increase together", "Useful observed ordering, not a controlled causal law", "Temperature, heater, cooler, and BC settings co-vary"], figs["mdot"]),
        Slide("Flow Trends Cannot Be Read As One-Coefficient Physics", ["Case design confounds temperature, power, and boundary settings", "Old Q perturbations are false-steady provenance", "Radiation is embedded in rcExternalTemperature wallHeatFlux"], figs["confounding"]),
        Slide("Aggregate Heat Balance Hides Wrong-Location Heat Loss", ["Best current predictive-style model: F1_heater_only", "Pipe legs over-lose heat", "Junction/stub/horizontal regions under-lose heat most strongly"], figs["heat"]),
        Slide("Next Thermal Model Needs Physical Boundary Lanes", ["Separate heater fraction, cooler/HX, wall loss, radiation metadata, storage", "Realized CFD heat flux is a score target, not runtime input", "Junction/stub heat-loss coverage is an explicit refinement target"], figs["thermal"]),
        Slide("Hydraulics Is Cleaner, But Not Yet Admitted", ["Localized fixed-K alone worsened mdot and stays diagnostic", "Fluid reset/development API now exists", "F6 waits for admitted Re-variation evidence"], figs["pressure"]),
        Slide("Current Upcomer Regime Is Not Ordinary Pipe Flow", ["Salt2-4 upcomer observations are recirculating", "Backflow fraction remains material", "Single-stream Nu, f_D, and K labels are invalid there"], figs["upcomer"]),
        Slide("Why Internal Nu Fitting Remains Closed", ["Current internal-Nu gate has 0 fit-admissible rows", "Nu cannot absorb boundary, storage, mixing, sign, or hydraulic residuals", "Reopen only after matched planes and ordinary/transition anchors"], figs["residual"]),
        Slide("Current Final Forward-v1 Decision: No-Go, But Actionable", ["Decision: blocked_no_go_final_forward_v1_not_admitted", "Input hygiene and split discipline are admitted", "Refresh only after upstream gates land"], figs["funnel"]),
        Slide("What Should Happen Next", ["Harvest matched pressure/upcomer metrics when jobs finish", "Turn heat-loss placement diagnosis into boundary/HX/wall implementation", "Plan Re 150/200/250 upcomer candidates if onset remains unbracketed"], figs["next"]),
        Slide("Backup: Current Blockers, Without Stale Items", ["Use the real open blocker list only", "Do not reopen OF12 reconstruction, no-mesh, no-radiation, or reconstructed-T corruption", "This protects credibility and meeting focus"], figs["blockers"]),
        Slide("Backup: What The LitRev Says To Try Or Avoid", ["Branchwise ledger is the controlling architecture", "Fully developed f_D/Nu are reference-only", "Global f, Nu, K, and UA shortcuts stay demoted"], figs["litrev"]),
        Slide("Backup: Flow/Temperature Correlations Are Descriptive", ["n=3 mainline trend is clean but not causal", "Heater, cooler, temperature, and BCs co-vary", "Use as operating-point context only"], figs["mdot"]),
        Slide("Backup: Say / Do Not Say", ["Use claim-boundary wording during narration", "Separate diagnostic results from predictive validation", "Say recirculation invalidates labels, not just Nu is blocked"], figs["say"]),
    ]


def main() -> None:
    FIG.mkdir(parents=True, exist_ok=True)
    SLIDES.mkdir(parents=True, exist_ok=True)
    figs = {
        "loop": fig_loop_schematic(),
        "contract": fig_predictive_contract(),
        "ladder": fig_evidence_ladder(),
        "dashboard": fig_gate_dashboard(),
        "pm5": fig_pm5_split_matrix(),
        "mdot": fig_mdot_probe_temperature(),
        "confounding": fig_confounding(),
        "heat": fig_heat_loss_grouped(),
        "thermal": fig_thermal_ledger(),
        "pressure": fig_pressure_ledger(),
        "upcomer": fig_upcomer_recirculation(),
        "residual": fig_residual_ownership(),
        "funnel": fig_gate_funnel(),
        "next": fig_next_work(),
        "blockers": fig_blockers(),
        "litrev": fig_litrev_crosswalk(),
        "say": fig_say_avoid(),
    }
    slides = build_slides(figs)
    slide_pngs = [make_slide_png(s, i) for i, s in enumerate(slides, start=1)]
    package_deck = OUT / "2026-07-15_powerpoint_deck.pptx"
    build_pptx(slide_pngs, package_deck)
    build_pptx(slide_pngs, REPORT_DECK)

    figure_manifest = OUT / "figure_manifest.csv"
    with figure_manifest.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["figure_id", "path", "purpose", "source"])
        writer.writeheader()
        for key, p in figs.items():
            writer.writerow({"figure_id": key, "path": str(p.relative_to(ROOT)), "purpose": "presentation figure", "source": "structured CSV or schematic from cited outline"})

    summary = {
        "task_id": "AGENT-367",
        "figures": len(figs),
        "slides": len(slide_pngs),
        "deck": str(package_deck.relative_to(ROOT)),
        "report_deck": str(REPORT_DECK.relative_to(ROOT)),
        "figure_manifest": str(figure_manifest.relative_to(ROOT)),
        "native_solver_outputs_mutated": False,
        "registry_or_admission_state_mutated": False,
        "scheduler_state_mutated": False,
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")


if __name__ == "__main__":
    main()
