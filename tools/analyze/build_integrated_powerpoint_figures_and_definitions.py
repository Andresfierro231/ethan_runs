#!/usr/bin/env python3
"""Build advisor-facing figures and definitions for the 2026-07-15 deck."""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from xml.sax.saxutils import escape


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "work_products/2026-07/2026-07-15/2026-07-15_integrated_powerpoint_figures_and_definitions"
FIG = OUT / "figures"

MODE_SUMMARY = ROOT / "work_products/2026-07/2026-07-15/2026-07-15_setup_bc_model_error_synthesis_report/mode_error_summary.csv"
CASE_MODE = ROOT / "work_products/2026-07/2026-07-15/2026-07-15_setup_bc_model_error_synthesis_report/case_mode_error_matrix.csv"
HX_ERRORS = ROOT / "work_products/2026-07/2026-07-15/2026-07-15_setup_bc_model_error_synthesis_report/heater_cooler_model_form_errors.csv"
OSC_METRICS = ROOT / "work_products/2026-07/2026-07-15/2026-07-15_salt_oscillation_user_train_scope/representative_metrics.csv"
F6_SUMMARY = ROOT / "work_products/2026-07/2026-07-15/2026-07-15_f6_internal_nu_admission_review_and_forward_unblock/summary.json"


BLUE = "#2563eb"
ORANGE = "#f97316"
GREEN = "#16a34a"
RED = "#dc2626"
PURPLE = "#7c3aed"
INK = "#111827"
MUTED = "#4b5563"
GRID = "#d1d5db"
PAPER = "#ffffff"
PALE = "#f8fafc"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        return
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def num(value: str | None) -> float | None:
    if value is None or value == "":
        return None
    return float(value)


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def text(x: float, y: float, body: str, size: int = 18, weight: str = "400",
         fill: str = INK, anchor: str = "start") -> str:
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" font-family="Arial, Helvetica, sans-serif" '
        f'font-size="{size}" font-weight="{weight}" fill="{fill}" '
        f'text-anchor="{anchor}">{escape(body)}</text>'
    )


def line(x1: float, y1: float, x2: float, y2: float, stroke: str = GRID,
         width: float = 2.0, dash: str | None = None, marker: str | None = None) -> str:
    extra = f' stroke-dasharray="{dash}"' if dash else ""
    marker_end = f' marker-end="url(#{marker})"' if marker else ""
    return (
        f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
        f'stroke="{stroke}" stroke-width="{width:.1f}"{extra}{marker_end}/>'
    )


def rect(x: float, y: float, w: float, h: float, fill: str = PALE,
         stroke: str = GRID, width: float = 1.5, rx: float = 8.0) -> str:
    return (
        f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" '
        f'rx="{rx:.1f}" fill="{fill}" stroke="{stroke}" stroke-width="{width:.1f}"/>'
    )


def circle(cx: float, cy: float, r: float, fill: str = PALE,
           stroke: str = GRID, width: float = 2.0) -> str:
    return (
        f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" '
        f'fill="{fill}" stroke="{stroke}" stroke-width="{width:.1f}"/>'
    )


def svg_doc(width: int, height: int, elems: list[str]) -> str:
    defs = """
  <defs>
    <marker id="arrow" markerWidth="10" markerHeight="8" refX="9" refY="4" orient="auto" markerUnits="strokeWidth">
      <path d="M0,0 L10,4 L0,8 z" fill="#111827"/>
    </marker>
  </defs>"""
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">\n'
        f'  <rect width="{width}" height="{height}" fill="{PAPER}"/>\n'
        f'{defs}\n  ' + "\n  ".join(elems) + "\n</svg>\n"
    )


def wrap_lines(body: str, max_chars: int = 44) -> list[str]:
    words = body.split()
    lines: list[str] = []
    current = ""
    for word in words:
        if len(current) + len(word) + (1 if current else 0) <= max_chars:
            current = f"{current} {word}".strip()
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def paragraph(x: float, y: float, body: str, size: int = 16, fill: str = MUTED,
              max_chars: int = 48, line_h: int = 21) -> list[str]:
    return [text(x, y + i * line_h, line, size=size, fill=fill) for i, line in enumerate(wrap_lines(body, max_chars))]


def multiline_center(x: float, y: float, body: str, size: int = 13,
                     weight: str = "600", fill: str = INK,
                     max_chars: int = 14, line_h: int = 16) -> list[str]:
    return [
        text(x, y + i * line_h, line, size=size, weight=weight, fill=fill, anchor="middle")
        for i, line in enumerate(wrap_lines(body, max_chars))
    ]


def axis_tick(value: float) -> str:
    if abs(value) < 1.0:
        return f"{value:.2g}"
    if abs(value) < 10.0:
        return f"{value:.2f}".rstrip("0").rstrip(".")
    return f"{value:.1f}"


def glossary_rows() -> list[dict[str, str]]:
    return [
        {
            "term": "M1",
            "advisor_definition": "Diagnostic replay using the full CFD segment heat ledger while solving loop pressure for mdot.",
            "presentation_use": "Upper-bound diagnostic for how much realized CFD heat information can explain.",
        },
        {
            "term": "M1b",
            "advisor_definition": "Thermal isolation replay using full CFD segment heat ledger and fixed CFD mdot.",
            "presentation_use": "Diagnostic only; it cannot be used as a predictive runtime model.",
        },
        {
            "term": "M2",
            "advisor_definition": "Diagnostic replay using CFD heater, test-section net heat, and cooler terms while solving pressure for mdot.",
            "presentation_use": "Best current mdot diagnostic subset; still not setup-only predictive.",
        },
        {
            "term": "M3",
            "advisor_definition": "Diagnostic replay using only CFD heater and cooler terms while solving pressure for mdot.",
            "presentation_use": "Best current temperature RMSE subset; mdot worsens relative to M2.",
        },
        {
            "term": "PM5",
            "advisor_definition": "Pressure-matched +/-5Q diagnostic upcomer rows used to examine recirculation and wall heat transfer behavior.",
            "presentation_use": "Diagnostic evidence source, not an admitted Nu/f_D/K fit set.",
        },
        {
            "term": "F6",
            "advisor_definition": "Candidate hydraulic/friction correction scorecard built from admissibility-gated Re variation evidence.",
            "presentation_use": "Current F6 fit has zero admitted rows; final hydraulic residual remains blocked.",
        },
        {
            "term": "h_proxy",
            "advisor_definition": "Section-effective heat transfer proxy q''/(T_wall - T_bulk).",
            "presentation_use": "Diagnostic only in recirculating upcomer flow.",
        },
        {
            "term": "Nu",
            "advisor_definition": "Nusselt number h D / k for ordinary single-stream internal convection.",
            "presentation_use": "Invalid as a fitted label in the current recirculating Salt2-4 upcomer regime.",
        },
        {
            "term": "f_D",
            "advisor_definition": "Darcy friction factor in a pipe-flow pressure-loss model.",
            "presentation_use": "Not fit-admissible for current recirculating upcomer evidence.",
        },
        {
            "term": "K",
            "advisor_definition": "Minor or component loss coefficient in a hydraulic pressure-loss model.",
            "presentation_use": "Needs ordinary/transition anchor rows before fitting.",
        },
        {
            "term": "UA",
            "advisor_definition": "Overall conductance used in Q = UA DeltaT heat-exchanger models.",
            "presentation_use": "Near-term setup-only cooler/HX closure target.",
        },
        {
            "term": "SEM",
            "advisor_definition": "Standard error of the mean; sigma/sqrt(N) for independent samples.",
            "presentation_use": "Steady-state mean uncertainty metric, with autocorrelation correction when samples are correlated.",
        },
        {
            "term": "H1",
            "advisor_definition": "Legacy shorthand from older hydraulic/heat-loss task names; avoid using it without spelling out the physical quantity.",
            "presentation_use": "Replace with explicit phrases such as pressure residual, heat-loss model, or h_proxy.",
        },
    ]


def equation_rows() -> list[dict[str, str]]:
    return [
        {"name": "Pressure balance", "equation": "sum(dp_drive(mdot) - dp_loss(mdot; f_D, K)) = 0", "meaning": "Loop mdot is found by pressure-root solve."},
        {"name": "RMSE", "equation": "RMSE = sqrt(mean((prediction - reference)^2))", "meaning": "Temperature and power model error metric."},
        {"name": "Mean absolute mdot error", "equation": "mean(abs((mdot_pred - mdot_CFD) / mdot_CFD)) x 100%", "meaning": "Hydraulic error metric reported for M1/M2/M3."},
        {"name": "HX/cooler conductance", "equation": "Q = UA DeltaT_drive", "meaning": "Candidate setup-only cooler/HX model form."},
        {"name": "Heater efficiency", "equation": "Q_heater = eta P_electrical", "meaning": "Candidate setup-only heater model form."},
        {"name": "h_proxy", "equation": "h_proxy = q'' / (T_wall - T_bulk)", "meaning": "Diagnostic section-effective upcomer heat transfer proxy."},
        {"name": "Nusselt number", "equation": "Nu = h D / k", "meaning": "Ordinary internal-convection label; blocked in recirculating upcomer rows."},
        {"name": "CLT SEM", "equation": "SEM_independent = sigma / sqrt(N)", "meaning": "Uncertainty in a mean for independent samples."},
        {"name": "Autocorrelation-corrected SEM", "equation": "SEM_corrected = sigma / sqrt(N_eff), with N_eff = N / tau_int", "meaning": "Used when oscillatory time samples are correlated."},
    ]


def write_svg(path: Path, width: int, height: int, elems: list[str]) -> None:
    path.write_text(svg_doc(width, height, elems))


def fig_loop_schematic(path: Path) -> None:
    elems = [text(55, 50, "Physical loop schematic and scoring locations", 28, "700")]
    elems += [
        line(235, 455, 235, 145, INK, 11, marker="arrow"),
        line(235, 145, 805, 145, INK, 11, marker="arrow"),
        line(805, 145, 805, 455, INK, 11, marker="arrow"),
        line(805, 455, 235, 455, INK, 11, marker="arrow"),
    ]
    elems += [
        rect(90, 260, 210, 96, "#f0fdf4", GREEN, 2.5),
        text(195, 292, "Upcomer /", 20, "700", GREEN, "middle"),
        text(195, 318, "test section", 20, "700", GREEN, "middle"),
        text(195, 342, "TP/TW score region", 13, "600", MUTED, "middle"),
        rect(745, 260, 190, 96, "#eff6ff", BLUE, 2.5),
        text(840, 300, "Downcomer", 21, "700", BLUE, "middle"),
        text(840, 328, "return leg", 14, "600", MUTED, "middle"),
        rect(350, 76, 330, 84, "#fff7ed", ORANGE, 2.5),
        text(515, 110, "Cooling leg / cooler branch", 20, "700", ORANGE, "middle"),
        text(515, 136, "HX or airside heat removal", 13, "600", MUTED, "middle"),
        rect(330, 430, 370, 88, "#fef2f2", RED, 2.5),
        text(515, 464, "Heated lower leg", 21, "700", RED, "middle"),
        text(515, 492, "heater input and buoyancy source", 13, "600", MUTED, "middle"),
    ]
    elems += [
        circle(235, 455, 38, "#ffffff", INK, 3),
        text(235, 448, "Lower", 14, "700", INK, "middle"),
        text(235, 468, "junction", 14, "700", INK, "middle"),
        circle(235, 145, 38, "#ffffff", INK, 3),
        text(235, 138, "Upper", 14, "700", INK, "middle"),
        text(235, 158, "junction", 14, "700", INK, "middle"),
        circle(805, 145, 38, "#ffffff", INK, 3),
        text(805, 138, "Cooler", 14, "700", INK, "middle"),
        text(805, 158, "junction", 14, "700", INK, "middle"),
        circle(805, 455, 38, "#ffffff", INK, 3),
        text(805, 448, "Return", 14, "700", INK, "middle"),
        text(805, 468, "junction", 14, "700", INK, "middle"),
        text(520, 552, "Junction/stub regions are not hidden in Nu, f_D, K, or UA; they need explicit boundary/loss treatment.", 16, "600", MUTED, "middle"),
    ]
    elems += [
        rect(45, 88, 145, 62, "#f8fafc", GRID, 1.5),
        text(117, 114, "mdot plane", 15, "700", INK, "middle"),
        text(117, 135, "CFD reference", 12, "600", MUTED, "middle"),
        line(190, 120, 225, 145, GRID, 2, "5 5"),
        rect(890, 88, 145, 62, "#f8fafc", GRID, 1.5),
        text(962, 114, "pressure", 15, "700", INK, "middle"),
        text(962, 135, "root solve", 12, "600", MUTED, "middle"),
        line(890, 120, 820, 145, GRID, 2, "5 5"),
        rect(65, 385, 160, 54, "#f8fafc", GRID, 1.5),
        text(145, 417, "TP/TW probes", 15, "700", INK, "middle"),
        line(170, 385, 215, 335, GRID, 2, "5 5"),
    ]
    write_svg(path, 1080, 600, elems)


def fig_glossary_equations(path: Path) -> None:
    elems = [text(48, 50, "Define the shorthand before the results", 26, "700")]
    left = [
        ("M1", "Full CFD heat ledger + pressure solve; diagnostic upper bound."),
        ("M1b", "Full CFD heat ledger + fixed CFD mdot; thermal diagnostic."),
        ("M2", "CFD heater + test-section + cooler; best current mdot diagnostic."),
        ("M3", "CFD heater + cooler only; best current TP/TW RMSE diagnostic."),
        ("PM5/F6", "Pressure-matched upcomer evidence / candidate friction scorecard."),
        ("H1", "Legacy shorthand; spell out pressure residual or heat-loss term."),
    ]
    right = [
        ("Pressure root", "sum(dp_drive - dp_loss) = 0"),
        ("HX / cooler", "Q = UA DeltaT_drive"),
        ("Heater", "Q_heater = eta P_electrical"),
        ("h_proxy", "q'' / (T_wall - T_bulk)"),
        ("Nu", "h D / k; blocked for recirculating upcomer fits"),
        ("Mean uncertainty", "SEM = sigma/sqrt(N); use N_eff if autocorrelated"),
    ]
    elems += [rect(40, 82, 470, 430, "#f8fafc", GRID), text(70, 120, "Model modes and evidence labels", 20, "700")]
    y = 158
    for term, definition in left:
        elems += [text(72, y, term, 17, "700", BLUE), *paragraph(132, y, definition, 15, MUTED, 42, 19)]
        y += 57
    elems += [rect(560, 82, 480, 430, "#f8fafc", GRID), text(590, 120, "Equations and modeling assumptions", 20, "700")]
    y = 158
    for name, eqn in right:
        elems += [text(592, y, name, 17, "700", GREEN), *paragraph(742, y, eqn, 15, MUTED, 31, 19)]
        y += 57
    write_svg(path, 1080, 560, elems)


def fig_boundary_ladder(path: Path) -> None:
    modes = [
        ("M1", "Full CFD segment heat ledger", "pressure solve", "Diagnostic upper bound", RED),
        ("M1b", "Full CFD segment heat ledger", "fixed CFD mdot", "Thermal isolation only", PURPLE),
        ("M2", "CFD heater + test-section + cooler", "pressure solve", "Best mdot diagnostic", BLUE),
        ("M3", "CFD heater + cooler only", "pressure solve", "Best TP/TW diagnostic", GREEN),
    ]
    elems = [text(50, 52, "Boundary-condition ladder: what information is allowed?", 26, "700")]
    x0 = 70
    for i, (name, heat, mdot, note, color) in enumerate(modes):
        x = x0 + i * 245
        elems += [rect(x, 110, 205, 330, "#ffffff", color, 3), text(x + 102, 150, name, 30, "700", color, "middle")]
        elems += paragraph(x + 24, 190, heat, 16, INK, 21, 22)
        elems += [line(x + 24, 262, x + 181, 262, GRID, 1.5)]
        elems += paragraph(x + 24, 300, mdot, 16, INK, 21, 22)
        elems += [line(x + 24, 352, x + 181, 352, GRID, 1.5)]
        elems += paragraph(x + 24, 392, note, 15, MUTED, 22, 19)
    elems += [text(540, 504, "All four modes are diagnostic until runtime inputs are setup-only and admitted.", 18, "600", MUTED, "middle")]
    write_svg(path, 1080, 560, elems)


def bar_panel(elems: list[str], x: int, y: int, w: int, h: int, title: str,
              labels: list[str], values: list[float], colors: list[str], unit: str,
              label_max_chars: int = 14) -> None:
    elems += [text(x, y - 18, title, 18, "700")]
    max_v = max(values) if values else 1.0
    top = max_v * 1.18 if max_v > 0 else 1.0
    elems += [line(x, y + h, x + w, y + h, INK, 1.8), line(x, y, x, y + h, INK, 1.8)]
    for frac in [0.25, 0.5, 0.75, 1.0]:
        yy = y + h - frac * h
        elems += [line(x, yy, x + w, yy, GRID, 1.0), text(x - 8, yy + 5, axis_tick(top * frac), 12, fill=MUTED, anchor="end")]
    gap = 18
    bw = (w - gap * (len(values) + 1)) / len(values)
    for i, (label, value, color) in enumerate(zip(labels, values, colors)):
        bh = value / top * h if top else 0
        bx = x + gap + i * (bw + gap)
        by = y + h - bh
        elems += [rect(bx, by, bw, bh, color, color, 0, 3)]
        elems += [text(bx + bw / 2, by - 8, f"{axis_tick(value)}{unit}", 13, "700", INK, "middle")]
        elems += multiline_center(bx + bw / 2, y + h + 24, label, 13, "600", INK, label_max_chars, 16)


def fig_mode_error_bars(path: Path) -> None:
    rows = read_csv(MODE_SUMMARY)
    labels_mdot, mdot_vals = [], []
    labels_rmse, rmse_vals = [], []
    for row in rows:
        name = row["label"].split()[0]
        if num(row["mean_abs_mdot_error_pct"]) is not None:
            labels_mdot.append(name)
            mdot_vals.append(num(row["mean_abs_mdot_error_pct"]) or 0)
        labels_rmse.append(name)
        rmse_vals.append(num(row["mean_all_probe_rmse_K"]) or 0)
    elems = [text(52, 52, "Mdot and TP/TW error depend on boundary placement", 26, "700")]
    bar_panel(elems, 90, 115, 390, 300, "Mean absolute mdot error", labels_mdot, mdot_vals, [RED, BLUE, GREEN], "%")
    bar_panel(elems, 610, 115, 390, 300, "All-probe temperature RMSE", labels_rmse, rmse_vals, [RED, PURPLE, BLUE, GREEN], " K")
    elems += [text(540, 505, "M2 has the lowest mdot error (10.4%); M3 has the lowest temperature RMSE (18.0 K).", 18, "600", MUTED, "middle")]
    write_svg(path, 1080, 560, elems)


def fig_test_section_tradeoff(path: Path) -> None:
    rows = [r for r in read_csv(CASE_MODE) if r["mode_id"].startswith("M2_") or r["mode_id"].startswith("M3_")]
    cases = ["salt_2", "salt_3", "salt_4"]
    elems = [text(52, 52, "M2 versus M3: removing the test-section net heat improves TP/TW but hurts mdot", 24, "700")]
    panels = [
        ("Absolute mdot error", "mdot_error_pct", "%", 90, [abs(float(r["mdot_error_pct"])) for r in rows]),
        ("All-probe temperature RMSE", "all_probe_rmse_K", " K", 610, [float(r["all_probe_rmse_K"]) for r in rows]),
    ]
    for title, field, unit, x, values in panels:
        y, w, h = 120, 390, 295
        top = max(values) * 1.2
        elems += [text(x, y - 18, title, 18, "700"), line(x, y + h, x + w, y + h, INK, 1.8), line(x, y, x, y + h, INK, 1.8)]
        for frac in [0.25, 0.5, 0.75, 1.0]:
            yy = y + h - frac * h
            elems += [line(x, yy, x + w, yy, GRID, 1), text(x - 8, yy + 5, f"{top*frac:.1f}", 12, fill=MUTED, anchor="end")]
        group_w = w / len(cases)
        for i, case in enumerate(cases):
            subset = {("M2" if r["mode_id"].startswith("M2_") else "M3"): r for r in rows if r["case_id"] == case}
            for j, mode in enumerate(["M2", "M3"]):
                value = abs(float(subset[mode][field])) if field == "mdot_error_pct" else float(subset[mode][field])
                bw = 38
                bx = x + i * group_w + 28 + j * 46
                bh = value / top * h
                color = BLUE if mode == "M2" else GREEN
                elems += [rect(bx, y + h - bh, bw, bh, color, color, 0, 3)]
                elems += [text(bx + bw / 2, y + h - bh - 7, f"{value:.1f}", 12, "700", INK, "middle")]
            elems += [text(x + i * group_w + group_w / 2, y + h + 24, case.replace("_", " ").title(), 13, "600", INK, "middle")]
    elems += [rect(430, 456, 18, 18, BLUE, BLUE), text(455, 471, "M2", 14, "700"), rect(500, 456, 18, 18, GREEN, GREEN), text(525, 471, "M3", 14, "700")]
    write_svg(path, 1080, 560, elems)


def fig_heater_cooler(path: Path) -> None:
    rows = read_csv(HX_ERRORS)
    keep = [
        ("Current cooler model", "current_fluid_airside_hx_fixed_mdot", ORANGE),
        ("Salt2-fit UA candidate", "salt2_fit_constant_UA_bulk_drive", GREEN),
        ("Electrical heater 1:1", "electrical_heater_power_1_to_1", BLUE),
        ("Salt2-fit eta candidate", "salt2_fit_constant_heater_efficiency", PURPLE),
    ]
    vals = []
    for _, model, _ in keep:
        vals.append(next(float(r["rmse_W"]) for r in rows if r["model_form"] == model))
    elems = [
        text(52, 48, "Heater/cooler closure: power error versus CFD-realized heat", 25, "700"),
        text(52, 78, "RMSE reference = CFD-realized cooler removal or heater-to-fluid power; rows = Salt2/3/4 nominal cases.", 15, "600", MUTED),
    ]
    bar_panel(
        elems,
        110,
        150,
        840,
        245,
        "Power RMSE by model form",
        [k[0] for k in keep],
        vals,
        [k[2] for k in keep],
        " W",
        label_max_chars=13,
    )
    elems += [
        rect(82, 470, 210, 86, "#fff7ed", ORANGE, 2),
        text(102, 498, "Current cooler", 15, "700", ORANGE),
        *paragraph(102, 522, "Existing Fluid airside-HX style cooler model; not fitted to these powers.", 12, MUTED, 27, 15),
        rect(316, 470, 210, 86, "#f0fdf4", GREEN, 2),
        text(336, 498, "Salt2-fit UA", 15, "700", GREEN),
        *paragraph(336, 522, "Q_cool = UA DeltaT_bulk; one scalar fit on Salt2, scored on Salt3/4 without refit.", 12, MUTED, 29, 15),
        rect(550, 470, 210, 86, "#eff6ff", BLUE, 2),
        text(570, 498, "Electrical heater", 15, "700", BLUE),
        *paragraph(570, 522, "Q_heater = P_electrical; setup 1:1 assumption compared to CFD heater-to-fluid power.", 12, MUTED, 29, 15),
        rect(784, 470, 210, 86, "#f5f3ff", PURPLE, 2),
        text(804, 498, "Salt2-fit eta", 15, "700", PURPLE),
        *paragraph(804, 522, "Q_heater = eta P_electrical; one scalar fit on Salt2, scored on Salt3/4 without refit.", 12, MUTED, 29, 15),
        text(540, 612, "Interpretation: these are model-form clues for setup-only closures, not final admitted predictive results.", 16, "700", MUTED, "middle"),
    ]
    write_svg(path, 1080, 650, elems)


def fig_steady_state(path: Path) -> None:
    wanted = [
        "salt1_nominal",
        "salt1_jin_nominal",
        "salt2_jin_nominal",
        "salt3_jin_nominal",
        "salt4_nominal",
        "salt2_native_val",
    ]
    data = {r["case_key"]: r for r in read_csv(OSC_METRICS) if r["case_key"] in wanted}
    elems = [text(52, 52, "Steady-state check: last-window RMS and CLT mean uncertainty", 25, "700")]
    temp_vals = [max(float(data[k]["TP_rms"]), float(data[k]["TW_rms"])) for k in wanted]
    mdot_vals = [float(data[k]["mdot_rms"]) * 1e6 for k in wanted]
    labels = [k.replace("_", " ") for k in wanted]
    short_labels = ["Salt1", "Salt1 Jin", "Salt2 Jin", "Salt3 Jin", "Salt4", "Salt2 val"]
    temp_colors = [BLUE, BLUE, BLUE, BLUE, BLUE, GREEN]
    mdot_colors = [ORANGE, ORANGE, ORANGE, ORANGE, ORANGE, GREEN]
    bar_panel(elems, 90, 120, 420, 285, "Max TP/TW RMS", short_labels, temp_vals, temp_colors, " K", label_max_chars=9)
    bar_panel(elems, 620, 120, 370, 285, "mdot RMS", short_labels, mdot_vals, mdot_colors, "e-6 kg/s", label_max_chars=9)
    elems += [text(92, 438, "Case labels: Salt1/Salt1 Jin/Salt2 Jin/Salt3 Jin/Salt4 are current training/reference rows; Salt2 val is diagnostic validation.", 13, "600", MUTED)]
    y = 492
    elems += [text(90, y, "Corrected relative SEM range:", 16, "700", INK)]
    sems = [float(data[k]["max_rel_sem_corrected"]) for k in wanted]
    elems += [text(335, y, f"{min(sems):.2e} to {max(sems):.2e}", 16, "700", GREEN)]
    elems += [text(90, y + 28, "Interpretation: final windows are steady; SEM uses CLT logic with autocorrelation-corrected effective sample counts.", 15, "600", MUTED)]
    write_svg(path, 1080, 600, elems)


def fig_admission_gate(path: Path) -> None:
    summary = json.loads(F6_SUMMARY.read_text())
    boxes = [
        ("PM5 diagnostic rows", 12, BLUE),
        ("wallHeatFlux rows", 12, BLUE),
        ("positive h_proxy rows", 8, ORANGE),
        ("sign + heat-balance pass", 0, RED),
        ("F6 fit-admitted rows", int(summary["f6_fit_admissible_rows"]), RED),
        ("internal-Nu fit rows", int(summary["internal_nu_fit_admissible_rows"]), RED),
    ]
    elems = [text(52, 52, "Admission gate: recirculation is a result, not just a failed fit", 25, "700")]
    for i, (label, count, color) in enumerate(boxes):
        x = 85 + i * 160
        w = 125
        elems += [rect(x, 150, w, 120, "#ffffff", color, 3), text(x + w / 2, 200, str(count), 34, "700", color, "middle")]
        elems += paragraph(x + 12, 232, label, 13, INK, 15, 16)
        if i < len(boxes) - 1:
            elems += [line(x + w + 10, 210, x + 150, 210, INK, 2.5, marker="arrow")]
    elems += [rect(110, 345, 860, 90, "#fff7ed", ORANGE, 2.5)]
    elems += [text(540, 380, "Current Salt2-4 upcomer evidence is recirculating.", 22, "700", INK, "middle")]
    elems += [text(540, 415, "Single-stream Nu, f_D, and K labels are invalid until ordinary/transition anchors exist.", 17, "600", MUTED, "middle")]
    write_svg(path, 1080, 560, elems)


def fig_roadmap(path: Path) -> None:
    steps = [
        ("1", "Setup-only HX scorecard", "Use UA/cooler candidates without runtime CFD leakage.", GREEN),
        ("2", "Heater setup model", "Score eta P_electrical on validation/holdout.", GREEN),
        ("3", "Distributed test-section boundary", "Replace compatibility sink with physical segment heat loss.", ORANGE),
        ("4", "Matched plane extraction", "Get admission-grade upcomer planes and wall bands.", ORANGE),
        ("5", "Re 150/200/250 anchors", "Bracket ordinary-to-recirculating onset.", ORANGE),
        ("6", "Final forward-v1 gate", "Only after split/runtime/heat-balance gates pass.", RED),
    ]
    elems = [text(52, 52, "Roadmap from diagnostic replay to final forward-v1", 26, "700")]
    for i, (n, title, detail, color) in enumerate(steps):
        x = 80 + (i % 3) * 320
        y = 120 + (i // 3) * 190
        elems += [circle(x + 28, y + 36, 26, color, color), text(x + 28, y + 45, n, 22, "700", "#ffffff", "middle")]
        elems += [rect(x + 66, y, 235, 110, "#ffffff", color, 2.4)]
        elems += [text(x + 85, y + 34, title, 17, "700", INK)]
        elems += paragraph(x + 85, y + 66, detail, 14, MUTED, 28, 17)
        if i not in [2, 5]:
            elems += [line(x + 301, y + 55, x + 318, y + 55, INK, 2.2, marker="arrow")]
    elems += [text(540, 505, "Color meaning: green = ready to score, orange = build/admit next, red = still blocked.", 17, "600", MUTED, "middle")]
    write_svg(path, 1080, 560, elems)


def build() -> dict[str, object]:
    OUT.mkdir(parents=True, exist_ok=True)
    FIG.mkdir(parents=True, exist_ok=True)
    figures = [
        ("fig01_loop_schematic.svg", "Loop schematic with named legs, junctions, and measured/model quantities", fig_loop_schematic),
        ("fig02_glossary_equations.svg", "Advisor-facing definitions, assumptions, and equations", fig_glossary_equations),
        ("fig03_boundary_mode_ladder.svg", "Boundary-condition/model-mode ladder", fig_boundary_ladder),
        ("fig04_mode_error_bars.svg", "M1/M1b/M2/M3 mdot and TP/TW error bars", fig_mode_error_bars),
        ("fig05_test_section_tradeoff.svg", "M2 versus M3 mdot/temperature tradeoff by Salt case", fig_test_section_tradeoff),
        ("fig06_heater_cooler_rmse.svg", "Heater and cooler RMSE model-form comparison", fig_heater_cooler),
        ("fig07_steady_state_rms_sem.svg", "Salt train/test steady-state RMS and SEM panel", fig_steady_state),
        ("fig08_admission_gate_funnel.svg", "Internal-Nu/F6 admission gate funnel", fig_admission_gate),
        ("fig09_forward_v1_roadmap.svg", "Forward-v1 roadmap and remaining gates", fig_roadmap),
    ]
    manifest: list[dict[str, object]] = []
    for name, caption, func in figures:
        path = FIG / name
        func(path)
        manifest.append({"figure_id": name.removesuffix(".svg"), "path": rel(path), "caption": caption, "format": "svg"})

    write_csv(OUT / "term_glossary.csv", glossary_rows())
    write_csv(OUT / "equation_register.csv", equation_rows())
    write_csv(OUT / "figure_manifest.csv", manifest)
    sources = [
        MODE_SUMMARY,
        CASE_MODE,
        HX_ERRORS,
        OSC_METRICS,
        F6_SUMMARY,
        ROOT / "reports/thesis_dossier/2026-07-15_integrated_weekly_powerpoint_outline.md",
    ]
    source_rows = [{"source_path": rel(p), "used_for": "figure inputs and presentation definitions"} for p in sources]
    write_csv(OUT / "source_manifest.csv", source_rows)
    summary = {
        "created_utc": "2026-07-15T16:40:00Z",
        "task": "AGENT-434",
        "supersedes_task": "AGENT-433",
        "figure_count": len(manifest),
        "glossary_terms": len(glossary_rows()),
        "equations": len(equation_rows()),
        "native_solver_outputs_mutated": False,
        "generated_index_refreshed": False,
        "external_fluid_mutated": False,
        "outputs": [row["path"] for row in manifest] + [
            rel(OUT / "term_glossary.csv"),
            rel(OUT / "equation_register.csv"),
            rel(OUT / "figure_manifest.csv"),
            rel(OUT / "source_manifest.csv"),
            rel(OUT / "README.md"),
            rel(OUT / "summary.json"),
        ],
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    (OUT / "README.md").write_text(readme(manifest))
    return summary


def readme(manifest: list[dict[str, object]]) -> str:
    lines = [
        "# Integrated PowerPoint Figures and Definitions",
        "",
        "Task: AGENT-434 correction of AGENT-433 figure package",
        "Date: 2026-07-15",
        "",
        "This package converts the integrated weekly presentation figure suggestions into standalone advisor-facing SVG figures and explicit terminology/equation tables. AGENT-433 corrected `fig06_heater_cooler_rmse.svg` to state the RMSE reference and model assumptions, and corrected `fig07_steady_state_rms_sem.svg` to avoid overlapping bottom text and repeated-looking small tick labels. AGENT-434 then added Salt4 nominal to `fig07_steady_state_rms_sem.svg` and the matching outline discussion. The figures are presentation artifacts derived from already-landed diagnostic/admission work products; no PowerPoint files are created by this package, and no native CFD solver outputs, registry/admission state, generated indexes, or external Fluid code were changed.",
        "",
        "## Up-front definitions to use in the deck",
        "",
        "- M1: diagnostic replay using the full CFD segment heat ledger while solving pressure for mdot.",
        "- M1b: full CFD segment heat ledger with fixed CFD mdot; thermal isolation only.",
        "- M2: CFD heater + test-section net + cooler while solving pressure for mdot; best current mdot diagnostic.",
        "- M3: CFD heater + cooler only while solving pressure for mdot; best current TP/TW diagnostic.",
        "- PM5: pressure-matched +/-5Q diagnostic upcomer evidence.",
        "- F6: candidate hydraulic/friction correction scorecard; currently zero fit-admitted rows.",
        "- h_proxy = q''/(T_wall - T_bulk): section-effective diagnostic heat-transfer proxy.",
        "- Nu = hD/k, f_D, and K are not fit-admissible in the current recirculating upcomer evidence.",
        "- SEM = sigma/sqrt(N) for independent samples; use SEM = sigma/sqrt(N_eff) when autocorrelation reduces the effective sample count.",
        "",
        "## Figures",
        "",
    ]
    for row in manifest:
        lines.append(f"- `{row['figure_id']}`: `{row['path']}` - {row['caption']}")
    lines += [
        "",
        "## Tables",
        "",
        "- `term_glossary.csv`: advisor-facing definitions and presentation use.",
        "- `equation_register.csv`: modeling assumptions/equations to define before results.",
        "- `figure_manifest.csv`: stable figure IDs, paths, and captions.",
        "- `source_manifest.csv`: input evidence used by this package.",
    ]
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    result = build()
    print(json.dumps(result, indent=2, sort_keys=True))
