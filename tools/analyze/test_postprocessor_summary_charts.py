from pathlib import Path

from tools.analyze.build_postprocessor_summary_charts import build_package


def test_build_postprocessor_summary_charts_outputs(tmp_path: Path) -> None:
    output_dir = tmp_path / "charts"
    summary = build_package(output_dir)

    expected_figures = {
        "figures/pressure_decomposition_by_span.svg",
        "figures/heat_source_sink_by_patch_group.svg",
        "figures/heat_enthalpy_residual_by_segment.svg",
        "figures/friction_form_mdot_error.svg",
        "figures/friction_per_leg_pressure_drop.svg",
        "figures/f5_ri_screen_coefficients.svg",
        "figures/upcomer_backflow_vs_re.svg",
        "figures/corrected_salt_gate_status.svg",
    }
    assert set(summary["figures"]) == expected_figures
    for rel_path in expected_figures:
        path = output_dir / rel_path
        assert path.exists()
        text = path.read_text()
        assert text.startswith("<svg")
        assert "</svg>" in text

    for filename in [
        "README.md",
        "presentation_story.md",
        "thesis_story.md",
        "trends_and_next_analysis.md",
        "source_inventory.csv",
        "figure_manifest.csv",
        "summary.json",
    ]:
        assert (output_dir / filename).exists()

    for filename in [
        "pressure_terms_summary.csv",
        "heat_terms_summary.csv",
        "heat_enthalpy_residual_summary.csv",
        "friction_mdot_summary.csv",
        "f5_fit_screen_summary.csv",
        "upcomer_regime_summary.csv",
        "corrected_salt_status_summary.csv",
        "observation_table_summary.csv",
    ]:
        assert (output_dir / "tables" / filename).exists()


def test_postprocessor_summary_charts_documents_admission_boundaries(tmp_path: Path) -> None:
    output_dir = tmp_path / "charts"
    build_package(output_dir)

    readme = (output_dir / "README.md").read_text()
    manifest = (output_dir / "figure_manifest.csv").read_text()
    presentation = (output_dir / "presentation_story.md").read_text()
    thesis = (output_dir / "thesis_story.md").read_text()

    assert "Corrected Salt Q rows are live/status evidence only" in readme
    assert "failed candidate screen" in readme
    assert "status_only_not_closure_evidence" in manifest
    assert "not a validated Richardson-number law" in readme
    assert "Do not claim final mdot predictivity until thermal replay is fixed" in presentation
    assert "mass flow alone" in thesis


def test_postprocessor_summary_charts_tables_have_expected_rows(tmp_path: Path) -> None:
    output_dir = tmp_path / "charts"
    build_package(output_dir)

    pressure_lines = (output_dir / "tables" / "pressure_terms_summary.csv").read_text().strip().splitlines()
    heat_lines = (output_dir / "tables" / "heat_terms_summary.csv").read_text().strip().splitlines()
    heat_residual_lines = (output_dir / "tables" / "heat_enthalpy_residual_summary.csv").read_text().strip().splitlines()
    corrected_lines = (output_dir / "tables" / "corrected_salt_status_summary.csv").read_text().strip().splitlines()

    assert len(pressure_lines) == 19  # header + 18 Salt 2/3/4 span rows
    assert len(heat_lines) == 16  # header + 3 cases x 5 patch groups
    assert len(heat_residual_lines) == 13  # header + 3 cases x 4 non-junction spans
    assert len(corrected_lines) > 10
