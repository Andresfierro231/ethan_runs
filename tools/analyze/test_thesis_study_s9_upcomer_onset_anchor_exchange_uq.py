import csv
import json
import tempfile
from pathlib import Path

from tools.analyze.build_thesis_study_s9_upcomer_onset_anchor_exchange_uq import build


def read_rows(path: Path):
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def test_s9_builder_keeps_s11_blocked_without_exchange_candidate():
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "s9"
        summary = build(out)

        assert summary["study_state"] == "negative_result_s11_still_blocked"
        assert summary["s11_unblocked"] is False
        assert summary["s11_ready_candidates"] == 0
        assert summary["ordinary_upcomer_nu_fd_k_admitted_rows"] == 0
        assert summary["exchange_cell_coefficient_admitted_rows"] == 0
        assert summary["solver_or_sampler_or_harvest_launch"] is False
        assert summary["registry_or_admission_mutated"] is False

        required = [
            "README.md",
            "summary.json",
            "onset_anchor_ledger.csv",
            "near_onset_gap_table.csv",
            "exchange_qoi_contract.csv",
            "same_window_uq_requirements.csv",
            "s9_admission_gate_matrix.csv",
            "s11_unblock_decision.csv",
            "source_manifest.csv",
        ]
        for name in required:
            assert (out / name).exists(), name

        onset = read_rows(out / "onset_anchor_ledger.csv")
        assert len(onset) == summary["onset_anchor_rows"]
        assert all(row["s11_candidate_status"] == "not_ready" for row in onset)
        assert any(float(row["max_reverse_area_fraction"]) > 0 for row in onset)

        qois = {row["qoi_name"]: row for row in read_rows(out / "exchange_qoi_contract.csv")}
        for qoi in ["V_recirc", "mdot_exchange", "tau_recirc"]:
            assert qoi in qois
            assert qois[qoi]["admission_use_now"] == "false"

        gates = {row["gate_id"]: row for row in read_rows(out / "s9_admission_gate_matrix.csv")}
        assert gates["S9-G1"]["status"] == "pass"
        assert gates["S9-G6"]["status"] == "fail"

        decision = read_rows(out / "s11_unblock_decision.csv")[0]
        assert decision["s11_unblocked"] == "false"
        assert decision["ordinary_upcomer_closures"] == "disabled"

        parsed = json.loads((out / "summary.json").read_text())
        assert parsed["native_solver_outputs_mutated"] is False
