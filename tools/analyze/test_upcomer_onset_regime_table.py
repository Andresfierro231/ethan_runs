from pathlib import Path

from tools.analyze.build_upcomer_onset_regime_table import build


def test_upcomer_onset_outputs() -> None:
    summary = build()
    out = Path("work_products/2026-07-08_upcomer_onset")
    assert summary["rows"] == 3
    assert (out / "upcomer_onset_regime_table.csv").exists()
    assert (out / "figures/upcomer_onset_regime.svg").exists()
    assert (out / "README.md").exists()


def test_upcomer_onset_keeps_work_in_progress_boundaries() -> None:
    summary = build()
    assert summary["mesh_uncertainty_status"] == "work_in_progress_not_claimed"
    assert summary["corrected_salt_perturbation_status"] == "converged_rows_closure_fit_admissible"
    table = Path("work_products/2026-07-08_upcomer_onset/upcomer_onset_regime_table.csv").read_text()
    assert "recirculation_cell_observed" in table
    assert "exclude_from_pipe_friction_fit" in table
