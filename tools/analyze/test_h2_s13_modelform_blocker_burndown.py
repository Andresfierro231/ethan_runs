from __future__ import annotations

import csv
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.analyze import build_h2_s13_modelform_blocker_burndown as builder


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class H2S13ModelFormBlockerBurndownTests(unittest.TestCase):
    def test_passive_role_filter_recovers_all_subspan_rows(self) -> None:
        matrix = builder.provenance_rows()
        self.assertEqual(len(matrix), 15)
        self.assertEqual({row["case_id"] for row in matrix}, {"salt_2", "salt_3", "salt_4"})
        self.assertEqual({row["source_family"] for row in matrix}, set(builder.PASSIVE_FAMILIES))
        self.assertEqual({row["release_grade_subspan_evidence_recovered"] for row in matrix}, {"true"})
        self.assertEqual({row["setup_property_provenance_ready"] for row in matrix}, {"true"})
        self.assertTrue(all(float(row["passive_role_area_delta_pct"]) <= 5.0 for row in matrix))

    def test_source_sink_exclusions_are_documented_for_mixed_role_segments(self) -> None:
        matrix = builder.provenance_rows()
        by_family = {(row["case_id"], row["source_family"]): row for row in matrix}
        for family in ("cooling_branch", "lower_leg", "upcomer"):
            self.assertGreater(float(by_family[("salt_2", family)]["source_sink_excluded_area_m2"]), 0.0)
            self.assertNotEqual(by_family[("salt_2", family)]["excluded_source_sink_roles"], "none")
        for family in ("downcomer", "junction"):
            self.assertEqual(float(by_family[("salt_2", family)]["source_sink_excluded_area_m2"]), 0.0)
            self.assertEqual(by_family[("salt_2", family)]["excluded_source_sink_roles"], "none")

    def test_strict_source_envelope_still_blocks_admission_release(self) -> None:
        matrix = builder.provenance_rows()
        self.assertEqual({row["strict_source_envelope_pass"] for row in matrix}, {"false"})
        self.assertEqual({row["source_property_admission_release_ready"] for row in matrix}, {"false"})
        self.assertEqual({row["source_property_release_allowed_now"] for row in matrix}, {"false"})
        blockers = {row["blocker"]: row for row in builder.blocker_summary_rows(matrix)}
        self.assertEqual(blockers["release_grade_subspan_rows"]["status"], "unblocked_for_evidence_contract")
        self.assertEqual(blockers["strict_source_envelope"]["status"], "still_blocking")

    def test_exact_h2_runner_contract_remains_non_scoring(self) -> None:
        contract = builder.h2_exact_nonscoring_runner_contract_rows()
        by_key = {row["case_key"]: row for row in contract}
        self.assertEqual(by_key["salt1_nominal"]["status"], "missing_runtime_prediction")
        self.assertEqual(by_key["salt2_jin_nominal"]["runtime_ready_now"], "true")
        self.assertEqual(by_key["salt2_lo5q"]["status"], "target_only_no_frozen_prediction")
        self.assertEqual({row["fit_allowed_now"] for row in contract}, {"false"})
        self.assertEqual({row["score_allowed_now"] for row in contract}, {"false"})

    def test_s13_endpoint_exact_field_contract_blocks_harvest(self) -> None:
        contract = builder.s13_endpoint_exact_field_contract_rows()
        missing = {row["required_field_or_artifact"] for row in contract if row["current_status"] == "missing"}
        self.assertIn("area_m2", missing)
        self.assertIn("area_vector_x_m2", missing)
        self.assertIn("owner_cell", missing)
        self.assertEqual({row["release_or_harvest_allowed_now"] for row in contract}, {"false"})

    def test_d4_d3_d2_successor_preflight_is_not_admission(self) -> None:
        rows = builder.d4_d3_d2_physical_successor_preflight_rows()
        families = {row["successor_family"] for row in rows}
        self.assertTrue({"D4", "D3", "D2"}.issubset(families))
        self.assertEqual({row["admission_ready_now"] for row in rows}, {"false"})
        self.assertEqual({row["freeze_ready_now"] for row in rows}, {"false"})
        self.assertEqual({row["final_score_ready_now"] for row in rows}, {"false"})

    def test_presentable_diagnostic_scores_are_not_admissions(self) -> None:
        scores = builder.presentable_diagnostic_score_rows()
        ids = {row["score_id"] for row in scores}
        self.assertIn("D4_M3_segment_offsets_min2_train", ids)
        self.assertIn("PASSIVE-H2_runtime_salt_2", ids)
        self.assertIn("HX_LUMPED_UA_NTU_fixed_mdot_duty_salt_3", ids)
        self.assertIn("S13_Q_wall_W_medium_fine_mesh_spread", ids)
        self.assertEqual({row["admission_status"] for row in scores}, {"diagnostic_presentable_not_admitted"})

    def test_build_outputs_summary_and_contracts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "pkg"
            summary = builder.build(out)
            self.assertEqual(
                summary["decision"],
                "passive_h2_provenance_recovered_diagnostic_scores_presentable_no_admission",
            )
            self.assertEqual(summary["passive_h2_case_family_rows"], 15)
            self.assertEqual(summary["release_grade_subspan_evidence_recovered_rows"], 15)
            self.assertEqual(summary["setup_property_provenance_ready_rows"], 15)
            self.assertEqual(summary["strict_source_envelope_pass_rows"], 0)
            self.assertEqual(summary["source_property_admission_release_ready_rows"], 0)
            self.assertEqual(summary["h2_fit_allowed_rows"], 0)
            self.assertEqual(summary["h2_score_allowed_rows"], 0)
            self.assertEqual(summary["s13_endpoint_release_or_harvest_allowed_rows"], 0)
            self.assertEqual(summary["d4_d3_d2_admission_ready_rows"], 0)
            self.assertGreaterEqual(summary["presentable_diagnostic_score_rows"], 10)
            self.assertEqual(summary["final_admitted_score_rows"], 0)
            self.assertEqual(summary["best_temperature_diagnostic"], "D4_M3_segment_offsets_min2_train")
            self.assertEqual(summary["passive_h2_runtime_score_rows"], 3)
            self.assertEqual(summary["s13_qwall_mesh_spread_score_rows"], 1)
            self.assertFalse(summary["source_property_release"])
            self.assertFalse(summary["candidate_freeze"])
            self.assertEqual(len(rows(out / "support_contracts.csv")), 4)
            self.assertEqual(len(rows(out / "h2_exact_nonscoring_runner_contract.csv")), 8)
            self.assertGreaterEqual(len(rows(out / "s13_endpoint_exact_field_regeneration_contract.csv")), 9)
            self.assertGreaterEqual(len(rows(out / "d4_d3_d2_physical_successor_preflight.csv")), 3)
            self.assertEqual(len(rows(out / "presentable_diagnostic_scoreboard.csv")), summary["presentable_diagnostic_score_rows"])
            self.assertEqual(len(rows(out / "forbidden_claims.csv")), 5)
            self.assertEqual(len(rows(out / "passive_h2_source_property_provenance_recovery_matrix.csv")), 15)


if __name__ == "__main__":
    unittest.main()
