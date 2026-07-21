import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.analyze import build_wall_temperature_drive_candidate as wtd


class WallTemperatureDriveCandidateTests(unittest.TestCase):
    def test_candidate_definitions_use_declared_drive_selectors(self):
        rows = wtd.wall_candidate_definitions()
        self.assertEqual([row["wall_candidate_id"] for row in rows], wtd.WALL_IDS)
        by_id = {row["wall_candidate_id"]: row for row in rows}
        self.assertEqual(
            by_id["WTD1_upcomer_test_section_pipe_outer_wall_drive"]["upcomer_role_drive_selector"],
            "pipe_outer_wall_temperature",
        )
        self.assertEqual(
            by_id["WTD2_upcomer_test_section_outer_surface_drive"]["upcomer_role_drive_selector"],
            "outer_surface_temperature",
        )
        self.assertTrue(all(row["base_distribution"] == "PB2_salt2_local_shape_passive_hA_p1" for row in rows))

    def test_role_rows_override_only_targeted_upcomer_roles(self):
        gates = wtd.static_candidate_gate_rows(wtd.static_drive_audit_rows())
        contracts = wtd.scenario_contract_rows(gates)
        self.assertEqual(len(contracts), 3 * 3)
        wtd1 = next(
            row
            for row in contracts
            if row["candidate_id"] == "WTD1_upcomer_test_section_pipe_outer_wall_drive_PLUS_HX_LUMPED_UA_NTU"
            and row["case_id"] == "salt_3"
        )
        payload = json.loads(wtd1["scenario_json"])
        targeted = [
            row
            for row in payload["role_rows"]
            if row["parent_segment"] == wtd.UPCOMER_PARENT and row["role"] in wtd.TARGET_ROLES
        ]
        self.assertEqual(len(targeted), 2)
        self.assertEqual({row["drive_selector"] for row in targeted}, {"pipe_outer_wall_temperature"})
        parent_selectors = payload["parent_boundary_maps"]["external_boundary_drive_selector_by_parent_segment"]
        self.assertNotIn("pipe_outer_wall_temperature", set(parent_selectors.values()))

    def test_runtime_audit_excludes_forbidden_validation_inputs(self):
        contracts = wtd.scenario_contract_rows(wtd.static_candidate_gate_rows(wtd.static_drive_audit_rows()))
        audit = wtd.runtime_input_audit_rows(contracts, run_fluid=False)
        text = " ".join(row["forbidden_runtime_input"] + " " + row["evidence"] for row in audit)
        self.assertIn("realized wallHeatFlux", text)
        self.assertIn("validation/holdout wall-shell temperature", text)
        self.assertIn("validation/holdout outer-surface temperature", text)
        self.assertIn("validation/holdout probe temperatures", text)
        self.assertNotIn("Salt3_shape", text)
        self.assertNotIn("Salt4_shape", text)

    def test_static_gate_is_selector_support_not_admission(self):
        gates = wtd.static_candidate_gate_rows(wtd.static_drive_audit_rows())
        self.assertEqual(len(gates), len(wtd.WALL_IDS) * 3)
        for row in gates:
            self.assertIn("static_proxy_never_admits", row["admission_policy"])
            if row["split_role"] != "train":
                self.assertEqual(row["static_gate"], "pass")

    def test_default_coupled_rows_are_pending_background_run(self):
        contracts = wtd.scenario_contract_rows(wtd.static_candidate_gate_rows(wtd.static_drive_audit_rows()))
        rows, probes = wtd.coupled_scorecard_rows(contracts, run_fluid=False, timeout_seconds=wtd.DEFAULT_TIMEOUT_SECONDS)
        self.assertEqual({row["coupled_run_status"] for row in rows}, {"not_run_submit_background_srun"})
        self.assertEqual({row["coupled_gate"] for row in rows}, {"pending_background_fluid_score"})
        self.assertEqual(probes, [])

    def test_admission_requires_runtime_validation_and_holdout_passes(self):
        deltas = [
            {
                "candidate_id": "candidate",
                "case_id": "salt_3",
                "split_role": "validation",
                "score_gate": "pass",
            },
            {
                "candidate_id": "candidate",
                "case_id": "salt_4",
                "split_role": "holdout",
                "score_gate": "fail",
            },
        ]
        runtime = [
            {"audit_id": "R1", "gate": "pass"},
            {"audit_id": "R2", "gate": "pass"},
        ]
        rows = wtd.candidate_admission_review_rows(deltas, runtime)
        self.assertEqual(rows[0]["admission_decision"], "not_admitted")
        self.assertIn("holdout_mdot_all_probe_tw_gate_failed", rows[0]["blocking_reasons"])

    def test_build_emits_required_outputs_in_tempdir(self):
        original_out = wtd.OUT
        with tempfile.TemporaryDirectory() as tmp:
            wtd.OUT = Path(tmp)
            try:
                summary = wtd.build(run_fluid=False)
                self.assertEqual(summary["task"], wtd.TASK)
                required = [
                    "wall_candidate_definitions.csv",
                    "candidate_definitions.csv",
                    "static_drive_audit.csv",
                    "static_candidate_gate.csv",
                    "scenario_contracts.csv",
                    "runtime_input_audit.csv",
                    "coupled_scorecard.csv",
                    "coupled_delta_vs_m3.csv",
                    "probe_error_localization.csv",
                    "probe_delta_vs_m3.csv",
                    "role_segment_error_summary.csv",
                    "candidate_admission_review.csv",
                    "next_steps.csv",
                    "background_run_contract.csv",
                    "blocker_decision.json",
                    "source_manifest.csv",
                    "summary.json",
                    "README.md",
                ]
                for name in required:
                    self.assertTrue((wtd.OUT / name).exists(), name)
                with (wtd.OUT / "scenario_contracts.csv").open(newline="", encoding="utf-8") as handle:
                    rows = list(csv.DictReader(handle))
                self.assertEqual(len(rows), 9)
            finally:
                wtd.OUT = original_out


if __name__ == "__main__":
    unittest.main()
