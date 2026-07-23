from pathlib import Path

from tools.analyze.build_mesh_uncertainty_package import build


def test_mesh_uncertainty_outputs() -> None:
    summary = build()
    out = Path("work_products/2026-07/2026-07-22/2026-07-22_mesh_uncertainty")
    assert summary["task"] == "TODO-MESH-UNCERTAINTY"
    assert summary["qoi_rows"] == 4
    assert summary["case_qoi_rows"] == 12
    assert summary["formal_gci_allowed_rows"] == 0
    assert (out / "qoi_mesh_uncertainty_disposition.csv").exists()
    assert (out / "case_qoi_mesh_sensitivity.csv").exists()
    assert (out / "formal_gci_admissibility_matrix.csv").exists()
    assert (out / "source_manifest.csv").exists()
    assert (out / "README.md").exists()


def test_mesh_uncertainty_refuses_formal_gci_without_admitted_coarse() -> None:
    build()
    out = Path("work_products/2026-07/2026-07-22/2026-07-22_mesh_uncertainty")
    table = (out / "qoi_mesh_uncertainty_disposition.csv").read_text()
    matrix = (out / "formal_gci_admissibility_matrix.csv").read_text()
    assert "Q_wall_W" in table
    assert "diagnostic_only_no_formal_gci" in table
    assert "same_label_coarse_not_admitted" in table
    assert "do_not_fabricate_gci" in matrix
