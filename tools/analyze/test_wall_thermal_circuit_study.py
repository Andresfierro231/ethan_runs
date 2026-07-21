import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.analyze import build_wall_thermal_circuit_study as study


class WallThermalCircuitStudyTests(unittest.TestCase):
    def test_candidate_set_is_exact_nonduplicative_ladder(self):
        rows = study.wall_candidate_definitions()
        self.assertEqual([row["wall_candidate_id"] for row in rows], study.WALL_CIRCUIT_IDS)
        lanes = {row["lane"] for row in rows}
        self.assertEqual(lanes, {"heated_incline_wall_drive", "test_section_wall_fluid_coupling"})
        self.assertTrue(all(row["base_distribution"] == "PB2_salt2_local_shape_passive_hA_p1" for row in rows))

    def test_contracts_cover_four_candidates_two_coolers_three_cases(self):
        rows = study.scenario_contract_rows()
        self.assertEqual(len(rows), len(study.WALL_CIRCUIT_IDS) * len(study.COOLER_IDS) * 3)
        self.assertEqual({row["case_id"] for row in rows}, {"salt_2", "salt_3", "salt_4"})
        self.assertEqual({row["cooler_candidate_id"] for row in rows}, set(study.COOLER_IDS))
        self.assertEqual({row["runtime_input_violations"] for row in rows}, {0})

    def test_heated_incline_candidate_overrides_only_heated_incline_ambient_wall(self):
        row = next(
            row
            for row in study.scenario_contract_rows()
            if row["wall_candidate_id"] == "HIW1_heated_incline_pipe_outer_wall_drive"
            and row["case_id"] == "salt_3"
            and row["cooler_candidate_id"] == "HX_LUMPED_UA_NTU"
        )
        payload = json.loads(row["scenario_json"])
        targeted = [
            role
            for role in payload["role_rows"]
            if role["parent_segment"] == "heated_incline" and role["role"] == "ambient_wall"
        ]
        self.assertEqual(len(targeted), 1)
        self.assertEqual(targeted[0]["drive_selector"], "pipe_outer_wall_temperature")

    def test_test_section_candidate_overrides_only_test_section_role(self):
        row = next(
            row
            for row in study.scenario_contract_rows()
            if row["wall_candidate_id"] == "TSC2_test_section_only_outer_surface_drive"
            and row["case_id"] == "salt_4"
            and row["cooler_candidate_id"] == "HX_SEGMENTED_UA_NTU_N16"
        )
        payload = json.loads(row["scenario_json"])
        targeted = [
            role
            for role in payload["role_rows"]
            if role["parent_segment"] == "left_upper_vertical" and role["role"] == "test_section"
        ]
        self.assertEqual(len(targeted), 1)
        self.assertEqual(targeted[0]["drive_selector"], "outer_surface_temperature")

    def test_runtime_audit_excludes_forbidden_inputs_and_caps_parallelism(self):
        audit = study.runtime_input_audit_rows(study.scenario_contract_rows(), run_fluid=False, parallel_workers=8)
        self.assertEqual([row["gate"] for row in audit], ["pass", "pass", "pending"])
        text = " ".join(row["forbidden_runtime_input"] + " " + row["evidence"] for row in audit)
        self.assertIn("realized wallHeatFlux", text)
        self.assertIn("validation/holdout probe temperatures", text)
        self.assertIn("unbounded parallelism", text)

    def test_default_coupled_rows_are_pending_background_sbatch(self):
        rows, probes = study.coupled_scorecard_rows(
            study.scenario_contract_rows(),
            run_fluid=False,
            timeout_seconds=study.DEFAULT_TIMEOUT_SECONDS,
            parallel_workers=8,
        )
        self.assertEqual({row["coupled_run_status"] for row in rows}, {"not_run_submit_background_sbatch"})
        self.assertEqual({row["coupled_gate"] for row in rows}, {"pending_background_fluid_score"})
        self.assertEqual(probes, [])

    def test_admission_requires_mdot_tp_tw_and_all_probe(self):
        rows = [
            {
                "candidate_id": "candidate",
                "case_id": "salt_3",
                "split_role": "validation",
                "coupled_run_status": "completed",
                "mdot_error_pct": "0.1",
                "tp_rmse_K": "99.0",
                "tw_rmse_K": "99.0",
                "all_probe_rmse_K": "99.0",
            }
        ]
        deltas = study.coupled_delta_rows(rows)
        self.assertEqual(deltas[0]["score_gate"], "fail")
        self.assertGreater(float(deltas[0]["tp_delta_vs_m3_K"]), 0.0)
        self.assertGreater(float(deltas[0]["tw_delta_vs_m3_K"]), 0.0)
        self.assertGreater(float(deltas[0]["all_probe_delta_vs_m3_K"]), 0.0)

    def test_build_emits_required_outputs_in_tempdir(self):
        original_out = study.OUT
        original_log = study.LOG_DIR
        with tempfile.TemporaryDirectory() as tmp:
            study.OUT = Path(tmp) / "out"
            study.LOG_DIR = Path(tmp) / "logs"
            try:
                summary = study.build(run_fluid=False, parallel_workers=8)
                self.assertEqual(summary["task"], study.TASK)
                required = [
                    "wall_candidate_definitions.csv",
                    "candidate_definitions.csv",
                    "scenario_contracts.csv",
                    "runtime_input_audit.csv",
                    "agent511_import_status.csv",
                    "coupled_scorecard.csv",
                    "coupled_delta_vs_m3.csv",
                    "probe_error_localization.csv",
                    "probe_delta_vs_m3.csv",
                    "role_segment_error_summary.csv",
                    "candidate_admission_review.csv",
                    "background_run_contract.csv",
                    "ag522_wall_circuit.sbatch",
                    "blocker_decision.json",
                    "source_manifest.csv",
                    "summary.json",
                    "README.md",
                ]
                for name in required:
                    self.assertTrue((study.OUT / name).exists(), name)
                with (study.OUT / "scenario_contracts.csv").open(newline="", encoding="utf-8") as handle:
                    rows = list(csv.DictReader(handle))
                self.assertEqual(len(rows), len(study.WALL_CIRCUIT_IDS) * len(study.COOLER_IDS) * 3)
            finally:
                study.OUT = original_out
                study.LOG_DIR = original_log


if __name__ == "__main__":
    unittest.main()
