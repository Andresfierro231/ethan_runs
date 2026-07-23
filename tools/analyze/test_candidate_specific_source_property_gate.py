import csv
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools.analyze import build_candidate_specific_source_property_gate as builder


class CandidateSpecificSourcePropertyGateTest(unittest.TestCase):
    @staticmethod
    def rows(path: Path) -> list[dict[str, str]]:
        with path.open(newline="", encoding="utf-8") as handle:
            return list(csv.DictReader(handle))

    def build_tmp(self) -> Path:
        out = Path(tempfile.mkdtemp())
        with mock.patch.object(builder, "OUT", out):
            self.summary = builder.build()
        return out

    def test_three_candidates_are_evaluated_with_no_full_release(self) -> None:
        out = self.build_tmp()
        decisions = self.rows(out / "candidate_gate_matrix.csv")
        self.assertEqual(
            {row["candidate_id"] for row in decisions},
            {"P1D-BULK-CV-H2-CAND001", "PASSIVE-H2-CAND001", "HX_LUMPED_UA_NTU"},
        )
        self.assertEqual(self.summary["s11_open_ready_candidates"], 0)
        self.assertEqual(self.summary["freeze_ready_candidates"], 0)
        self.assertEqual(self.summary["source_property_release_ready_rows"], 0)

    def test_passive_h2_and_p1d_have_runtime_source_progress_but_release_fails(self) -> None:
        out = self.build_tmp()
        rows = self.rows(out / "candidate_subgate_status.csv")
        by_candidate_gate = {(row["candidate_id"], row["subgate"]): row for row in rows}
        self.assertEqual(by_candidate_gate[("PASSIVE-H2-CAND001", "setup_source_basis")]["status"], "pass_support_only")
        self.assertEqual(by_candidate_gate[("PASSIVE-H2-CAND001", "runtime_legality")]["status"], "pass_train_only_runtime_smoke")
        self.assertEqual(by_candidate_gate[("PASSIVE-H2-CAND001", "uq_residual_prerequisites")]["status"], "fail_closed_missing_same_qoi_uq")
        self.assertEqual(by_candidate_gate[("P1D-BULK-CV-H2-CAND001", "runtime_legality")]["status"], "prototype_runs_no_fit")
        self.assertEqual(by_candidate_gate[("P1D-BULK-CV-H2-CAND001", "row_specific_source_property_release")]["status"], "fail_closed")

    def test_passive_h2_next_blocker_is_not_runtime_patch(self) -> None:
        out = self.build_tmp()
        blockers = self.rows(out / "blocker_to_next_action.csv")
        blocker_names = {row["blocker"] for row in blockers}
        self.assertIn("passive_H2_source_mapping_split_uq", blocker_names)
        self.assertNotIn("passive_H2_external_runtime_patch", blocker_names)
        decisions = self.rows(out / "candidate_gate_matrix.csv")
        passive = next(row for row in decisions if row["candidate_id"] == "PASSIVE-H2-CAND001")
        self.assertIn("runtime_delta_qambient_W=14.629985767350746", passive["primary_numeric_context"])

    def test_hx_cooler_is_compute_pending_not_admitted(self) -> None:
        out = self.build_tmp()
        decisions = self.rows(out / "candidate_gate_matrix.csv")
        hx = next(row for row in decisions if row["candidate_id"] == "HX_LUMPED_UA_NTU")
        self.assertEqual(hx["runtime_legality"], "pending_solver_coupled_compute_run")
        self.assertEqual(hx["fit_or_admission_readiness"], "fail_closed_compute_pending")
        rows = self.rows(out / "candidate_subgate_status.csv")
        hx_subgates = [row for row in rows if row["candidate_id"] == "HX_LUMPED_UA_NTU"]
        self.assertTrue(any(row["subgate"] == "uq_residual_prerequisites" and row["status"] == "fail_closed_coupled_rows_not_run" for row in hx_subgates))

    def test_compatibility_outputs_use_same_candidate_set(self) -> None:
        out = self.build_tmp()
        expected = {"P1D-BULK-CV-H2-CAND001", "PASSIVE-H2-CAND001", "HX_LUMPED_UA_NTU"}
        for name in (
            "candidate_priority_ranking.csv",
            "candidate_release_decision.csv",
            "candidate_specific_gate_matrix.csv",
            "next_unblock_sequence.csv",
        ):
            rows = self.rows(out / name)
            self.assertEqual({row["candidate_id"] for row in rows}, expected)
            self.assertNotIn("M3+TS-SETUP-LOSS-CAND001", {row["candidate_id"] for row in rows})


if __name__ == "__main__":
    unittest.main()
