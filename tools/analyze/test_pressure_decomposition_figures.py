"""Tests for build_pressure_decomposition_figures.py (AGENT-234)."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from build_pressure_decomposition_figures import (
    C_BUOYANCY,
    C_DEV,
    C_FRICTION,
    C_MINOR,
    DEFAULT_INPUT,
    build,
    extract_rows,
    fmt_signed,
    read_ledger,
)

FIG_MECH = "figures/mechanical_loss_composition_by_span.svg"
FIG_DRIVE = "figures/buoyancy_drive_vs_resistance_by_span.svg"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def ledger() -> list[dict[str, str]]:
    return read_ledger(DEFAULT_INPUT)


@pytest.fixture()
def rows(ledger: list[dict[str, str]]) -> list[dict]:
    return extract_rows(ledger)


@pytest.fixture()
def output(tmp_path: Path) -> Path:
    out = tmp_path / "figures_test"
    build(out)
    return out


def _text(output: Path, rel: str) -> str:
    return (output / rel).read_text()


# ---------------------------------------------------------------------------
# Data-layer tests
# ---------------------------------------------------------------------------

def test_ledger_loads(ledger: list[dict[str, str]]) -> None:
    assert len(ledger) == 18


def test_rows_count(rows: list[dict]) -> None:
    assert len(rows) == 18


def test_rows_span_order(rows: list[dict]) -> None:
    expected = ["lower_leg", "right_leg", "left_lower_leg",
                "test_section_span", "left_upper_leg", "upper_leg"]
    for case in ["salt_2", "salt_3", "salt_4"]:
        assert [r["span"] for r in rows if r["case"] == case] == expected


def test_friction_always_positive(rows: list[dict]) -> None:
    for r in rows:
        assert r["friction"] > 0


def test_dev_loss_zero_for_non_entry(rows: list[dict]) -> None:
    for r in rows:
        if r["span"] in {"test_section_span", "left_upper_leg"}:
            assert r["dev"] == 0.0


def test_recirculation_flag(rows: list[dict]) -> None:
    for r in rows:
        expected = r["span"] in {"left_lower_leg", "left_upper_leg"}
        assert r["recirculation"] is expected


def test_upper_leg_buoyancy_large_negative(rows: list[dict]) -> None:
    for r in rows:
        if r["span"] == "upper_leg":
            assert r["buoyancy"] < -20


def test_fmt_signed() -> None:
    assert fmt_signed(5.2).startswith("+")
    assert fmt_signed(-39.3).startswith("−")  # proper minus glyph


# ---------------------------------------------------------------------------
# Output file existence / metadata
# ---------------------------------------------------------------------------

def test_output_files_exist(output: Path) -> None:
    assert (output / FIG_MECH).exists()
    assert (output / FIG_DRIVE).exists()
    assert (output / "README.md").exists()
    assert (output / "summary.json").exists()


def test_no_stale_filenames(output: Path) -> None:
    figs = {p.name for p in (output / "figures").glob("*.svg")}
    assert figs == {
        "mechanical_loss_composition_by_span.svg",
        "buoyancy_drive_vs_resistance_by_span.svg",
    }


def test_summary_json(output: Path) -> None:
    s = json.loads((output / "summary.json").read_text())
    assert s["counts"] == {"rows": 18, "cases": 3, "spans": 6}
    assert s["palette"]["friction"] == C_FRICTION
    assert s["palette"]["buoyancy"] == C_BUOYANCY
    assert len(s["limitations"]) >= 4
    assert "replaced_figures" in s
    # palette validation must be recorded and passing
    assert s["palette_validation"]["ok"] is True
    assert s["palette_validation"]["worst_cvd_delta_e"] >= 12
    assert "column_map" in s and "reusable_modules" in s


def test_readme_content(output: Path) -> None:
    txt = (output / "README.md").read_text()
    for needle in ["What was wrong before", "How this was made",
                   "Reusable components", "palette_validator", "svg_chart_kit"]:
        assert needle in txt, f"README missing {needle!r}"


def test_data_disclosure(output: Path) -> None:
    txt = (output / "DATA_DISCLOSURE.md").read_text()
    for needle in ["Ledger column", "Units and sign convention",
                   "Palette validation", "coarse_no_gci",
                   "distributed_friction_pa", "buoyancy_contribution_pa"]:
        assert needle in txt, f"DATA_DISCLOSURE missing {needle!r}"


def test_figure_data_csv(output: Path) -> None:
    import csv as _csv
    with (output / "figure_data.csv").open() as fh:
        data = list(_csv.DictReader(fh))
    assert len(data) == 18
    # every plotted value is disclosed and the total is the sum of the parts
    for r in data:
        parts = float(r["friction_pa"]) + float(r["dev_reset_pa"]) + float(r["minor_pa"])
        assert abs(parts - float(r["mechanical_total_pa"])) < 1e-3
        assert abs(abs(float(r["buoyancy_signed_pa"])) - float(r["buoyancy_abs_pa"])) < 1e-3


# ---------------------------------------------------------------------------
# SVG structural tests — no collisions, correct marks
# ---------------------------------------------------------------------------

def test_no_zero_width_marks(output: Path) -> None:
    for rel in (FIG_MECH, FIG_DRIVE):
        txt = _text(output, rel)
        assert 'width="0.0"' not in txt
        assert 'width="0"' not in txt


def test_section_headers_present(output: Path) -> None:
    for rel in (FIG_MECH, FIG_DRIVE):
        txt = _text(output, rel)
        sections = re.findall(r'class="section">([^<]+)</text>', txt)
        assert sections == ["Salt 2", "Salt 3", "Salt 4"], f"{rel}: {sections}"


def test_no_case_label_collision(output: Path) -> None:
    """Case names must be section headers, never in the span-label column."""
    for rel in (FIG_MECH, FIG_DRIVE):
        txt = _text(output, rel)
        span_labels = re.findall(r'class="spanlbl[^"]*">([^<]+)</text>', txt)
        # No span label should be a bare case name
        assert not any(lbl.strip() in {"Salt 2", "Salt 3", "Salt 4"} for lbl in span_labels)


def test_mech_has_all_three_series(output: Path) -> None:
    txt = _text(output, FIG_MECH)
    # friction 18 bars + 1 legend chip; dev 12 bars + 1 chip; minor 12 bars + 1 chip
    assert txt.count(C_FRICTION) >= 18
    assert txt.count(C_DEV) >= 12
    assert txt.count(C_MINOR) >= 12


def test_mech_value_labels_every_row(output: Path) -> None:
    txt = _text(output, FIG_MECH)
    vals = re.findall(r'class="val">[^<]*Pa</text>', txt)
    assert len(vals) == 18


def test_drive_paired_bars(output: Path) -> None:
    txt = _text(output, FIG_DRIVE)
    # 18 buoyancy (green) + 1 legend chip; 18 mechanical (blue) + 1 chip
    assert txt.count(C_BUOYANCY) >= 18
    assert txt.count(C_FRICTION) >= 18


def test_drive_buoyancy_labels_signed(output: Path) -> None:
    txt = _text(output, FIG_DRIVE)
    valg = re.findall(r'class="valg">([^<]+)</text>', txt)
    assert len(valg) == 18
    negatives = [v for v in valg if v.startswith("−")]
    positives = [v for v in valg if v.startswith("+")]
    assert len(negatives) == 3, f"expected 3 negative (upper_leg) buoyancy, got {negatives}"
    assert len(positives) == 15


def test_drive_mech_labels_every_row(output: Path) -> None:
    txt = _text(output, FIG_DRIVE)
    vals = re.findall(r'class="val">[^<]+</text>', txt)
    assert len(vals) == 18


def test_recirc_labels_italic_class(output: Path) -> None:
    for rel in (FIG_MECH, FIG_DRIVE):
        txt = _text(output, rel)
        recirc = re.findall(r'class="spanlbl-r">([^<]+)</text>', txt)
        # 2 recirc spans × 3 cases = 6, all carry the asterisk
        assert len(recirc) == 6, f"{rel}: {recirc}"
        assert all("*" in r for r in recirc)


def test_rounded_data_ends_present(output: Path) -> None:
    """Bars use path elements for rounded outer ends."""
    for rel in (FIG_MECH, FIG_DRIVE):
        txt = _text(output, rel)
        assert "<path d=" in txt
