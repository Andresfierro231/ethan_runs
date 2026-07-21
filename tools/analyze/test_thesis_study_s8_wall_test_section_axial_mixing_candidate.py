import csv
import json
import tempfile
from pathlib import Path

from tools.analyze.build_thesis_study_s8_wall_test_section_axial_mixing_candidate import build


def read_rows(path: Path):
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def test_s8_builder_outputs_negative_result_package():
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "s8"
        summary = build(out)

        assert summary["study_state"] == "negative_result_no_s11_candidate"
        assert summary["admitted_candidate_rows"] == 0
        assert summary["s11_ready_candidates"] == 0
        assert summary["runtime_leakage_pass"] is True
        assert summary["final_predictive_accuracy_claimed"] is False

        required = [
            "README.md",
            "summary.json",
            "candidate_contract.csv",
            "m3_prior_candidate_comparison.csv",
            "smoke_family_verdicts.csv",
            "acceptance_gate_matrix.csv",
            "runtime_leakage_audit.csv",
            "negative_or_admission_ready_summary.csv",
            "figure_table_manifest.csv",
            "source_manifest.csv",
        ]
        for name in required:
            assert (out / name).exists(), name

        prior = read_rows(out / "m3_prior_candidate_comparison.csv")
        assert len(prior) == summary["phase3_candidate_rows"]
        assert any(row["validation_tw5_delta_vs_m3_K"] for row in prior)

        smoke = read_rows(out / "smoke_family_verdicts.csv")
        assert len(smoke) == summary["smoke_family_rows"]
        assert all(row["s11_ready"] == "no" for row in smoke)

        gates = {row["gate_id"]: row for row in read_rows(out / "acceptance_gate_matrix.csv")}
        assert gates["S8-G1"]["status"] == "pass"
        assert gates["S8-G4"]["status"] == "fail"

        leakage = read_rows(out / "runtime_leakage_audit.csv")
        forbidden = {row["input_or_target"] for row in leakage if row["runtime_allowed"] == "no"}
        assert "CFD_mdot" in forbidden
        assert "realized_CFD_wallHeatFlux" in forbidden

        parsed = json.loads((out / "summary.json").read_text())
        assert parsed["native_solver_outputs_mutated"] is False
