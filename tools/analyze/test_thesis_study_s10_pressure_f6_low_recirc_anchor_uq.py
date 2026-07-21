import csv
import json
import tempfile
from pathlib import Path

from tools.analyze.build_thesis_study_s10_pressure_f6_low_recirc_anchor_uq import build


def read_rows(path: Path):
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def test_s10_builder_blocks_s11_without_low_recirc_anchor():
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "s10"
        summary = build(out)

        assert summary["study_state"] == "negative_result_s11_still_blocked"
        assert summary["s11_unblocked"] is False
        assert summary["s11_ready_candidates"] == 0
        assert summary["component_k_admitted_rows"] == 0
        assert summary["f6_fit_rows"] == 0
        assert summary["clipped_k_rows"] == 0
        assert summary["hidden_global_multiplier_rows"] == 0
        assert summary["solver_or_sampler_or_harvest_launch"] is False

        required = [
            "README.md",
            "summary.json",
            "s10_candidate_admission_matrix.csv",
            "s10_gate_matrix.csv",
            "s11_unblock_decision.csv",
            "source_manifest.csv",
        ]
        for name in required:
            assert (out / name).exists(), name

        candidates = read_rows(out / "s10_candidate_admission_matrix.csv")
        assert len(candidates) == summary["candidate_rows"]
        assert all(row["s11_candidate_status"] == "not_ready" for row in candidates)
        assert all(row["admission_decision"] in {"not_admitted", "not_admitted_for_component_K_or_F6"} for row in candidates)
        assert any(row["lane"] == "low_recirc_pressure_anchor" for row in candidates)
        assert any(row["lane"] == "F6_endpoint_pair" for row in candidates)

        gates = {row["gate_id"]: row for row in read_rows(out / "s10_gate_matrix.csv")}
        assert gates["S10-G5"]["status"] == "pass"
        assert gates["S10-G6"]["status"] == "fail"

        decision = read_rows(out / "s11_unblock_decision.csv")[0]
        assert decision["s11_unblocked"] == "false"
        assert decision["component_k_admission"] == "none"
        assert decision["f6_fit_admission"] == "none"

        parsed = json.loads((out / "summary.json").read_text())
        assert parsed["native_solver_outputs_mutated"] is False
