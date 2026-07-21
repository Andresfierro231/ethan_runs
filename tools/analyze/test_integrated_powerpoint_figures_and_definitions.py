#!/usr/bin/env python3
"""Tests for integrated PowerPoint figures and definitions."""

from __future__ import annotations

import importlib.util
from pathlib import Path


SCRIPT = Path(__file__).with_name("build_integrated_powerpoint_figures_and_definitions.py")
spec = importlib.util.spec_from_file_location("build_integrated_powerpoint_figures_and_definitions", SCRIPT)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def test_glossary_defines_advisor_unfriendly_shorthand() -> None:
    terms = {row["term"]: row for row in mod.glossary_rows()}
    for term in ["M1", "M1b", "M2", "M3", "PM5", "F6", "h_proxy", "Nu", "f_D", "K", "UA", "SEM", "H1"]:
        assert term in terms
        assert terms[term]["advisor_definition"]
        assert terms[term]["presentation_use"]
    assert "diagnostic" in terms["M2"]["presentation_use"].lower()
    assert "legacy shorthand" in terms["H1"]["advisor_definition"].lower()


def test_equation_register_contains_required_assumptions() -> None:
    equations = {row["name"]: row["equation"] for row in mod.equation_rows()}
    required = [
        "Pressure balance",
        "RMSE",
        "Mean absolute mdot error",
        "HX/cooler conductance",
        "Heater efficiency",
        "h_proxy",
        "Nusselt number",
        "CLT SEM",
        "Autocorrelation-corrected SEM",
    ]
    for name in required:
        assert name in equations
    assert "sqrt(N)" in equations["CLT SEM"]
    assert "q''" in equations["h_proxy"]
    assert "Nu" in equations["Nusselt number"]


def test_build_outputs_expected_manifest() -> None:
    summary = mod.build()
    out = mod.OUT
    assert summary["figure_count"] == 9
    for name in [
        "fig01_loop_schematic.svg",
        "fig02_glossary_equations.svg",
        "fig03_boundary_mode_ladder.svg",
        "fig04_mode_error_bars.svg",
        "fig05_test_section_tradeoff.svg",
        "fig06_heater_cooler_rmse.svg",
        "fig07_steady_state_rms_sem.svg",
        "fig08_admission_gate_funnel.svg",
        "fig09_forward_v1_roadmap.svg",
    ]:
        path = out / "figures" / name
        assert path.exists()
        body = path.read_text()
        assert body.startswith("<svg")
        assert "</svg>" in body
    assert (out / "term_glossary.csv").exists()
    assert (out / "equation_register.csv").exists()


def test_loop_schematic_names_physical_legs_and_junctions() -> None:
    mod.build()
    body = (mod.OUT / "figures" / "fig01_loop_schematic.svg").read_text()
    for label in [
        "Upcomer",
        "test section",
        "Downcomer",
        "Cooling leg",
        "Heated lower leg",
        "Lower",
        "Upper",
        "junction",
        "TP/TW probes",
        "mdot plane",
    ]:
        assert label in body


def test_heater_cooler_figure_states_rmse_reference_and_fit_policy() -> None:
    mod.build()
    body = (mod.OUT / "figures" / "fig06_heater_cooler_rmse.svg").read_text()
    for phrase in [
        "RMSE reference = CFD-realized cooler removal or heater-to-fluid power",
        "Q_cool = UA DeltaT_bulk",
        "Q_heater = eta P_electrical",
        "one scalar fit on Salt2",
        "not final admitted predictive results",
    ]:
        assert phrase in body


def test_steady_state_figure_has_short_labels_and_no_duplicate_small_ticks() -> None:
    mod.build()
    body = (mod.OUT / "figures" / "fig07_steady_state_rms_sem.svg").read_text()
    for phrase in [
        "Salt4",
        "Salt2 val",
        "Case labels:",
        "autocorrelation-corrected effective sample counts",
    ]:
        assert phrase in body
    assert "Salt4 are current training/reference rows" in body
    assert body.count(">0.1<") <= 1
    assert body.count(">0.2<") <= 1
