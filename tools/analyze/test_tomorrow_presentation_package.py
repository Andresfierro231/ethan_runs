from pathlib import Path

from tools.analyze.build_tomorrow_presentation_package import build_package


def test_tomorrow_presentation_package_outputs(tmp_path: Path) -> None:
    output_dir = tmp_path / "presentation"
    summary = build_package(output_dir)

    expected_figures = {
        "figures/minor_loss_k_apparent_vs_local.svg",
        "figures/minor_loss_separation_phi.svg",
        "figures/fixed_mdot_thermal_replay_error.svg",
        "figures/t13_re_sweep_plan.svg",
    }
    assert {str(Path(path).relative_to(output_dir)) for path in summary["figures"]} == expected_figures

    for rel_path in expected_figures:
        path = output_dir / rel_path
        assert path.exists()
        text = path.read_text()
        assert text.startswith("<svg")
        assert "</svg>" in text

    for filename in [
        "README.md",
        "slide_outline_with_speaker_notes.md",
        "slide6_thermal_replay_analysis.md",
        "missing_and_nice_to_have_figures.md",
        "figure_manifest.csv",
        "source_inventory.csv",
        "summary.json",
    ]:
        assert (output_dir / filename).exists()


def test_slide_outline_has_speaker_notes_and_claim_boundaries(tmp_path: Path) -> None:
    output_dir = tmp_path / "presentation"
    build_package(output_dir)

    outline = (output_dir / "slide_outline_with_speaker_notes.md").read_text()
    assert "## Slide 1" in outline
    assert "## Slide 12" in outline
    assert "**Speaker notes**" in outline
    assert "not a final closure coefficient" in outline
    assert "coarse_no_gci" in outline
    assert "Fixed-mdot thermal replay" in outline
    assert "cooler-plus-heater replay" in outline


def test_thermal_replay_figure_uses_readable_focused_labels(tmp_path: Path) -> None:
    output_dir = tmp_path / "presentation"
    build_package(output_dir)

    figure = (output_dir / "figures" / "fixed_mdot_thermal_replay_error.svg").read_text()
    assert "Baseline" in figure
    assert "current 1D" in figure
    assert "CFD cooler" in figure
    assert "heater flux" in figure
    assert ">P2<" not in figure
    assert ">P5<" not in figure


def test_support_tables_have_expected_rows(tmp_path: Path) -> None:
    output_dir = tmp_path / "presentation"
    build_package(output_dir)

    minor_loss_k = (output_dir / "tables" / "minor_loss_k_summary.csv").read_text().strip().splitlines()
    minor_loss_sep = (output_dir / "tables" / "minor_loss_separation_summary.csv").read_text().strip().splitlines()
    thermal = (output_dir / "tables" / "thermal_replay_summary.csv").read_text().strip().splitlines()
    t13 = (output_dir / "tables" / "t13_re_sweep_plan.csv").read_text().strip().splitlines()

    assert len(minor_loss_k) == 5  # header + four preserved corner features
    assert len(minor_loss_sep) == 4  # header + heater/cooler/downcomer
    assert len(thermal) == 4  # header + focused P0/P1/P4 comparison
    assert len(t13) == 7  # header + anchor + five proposals
