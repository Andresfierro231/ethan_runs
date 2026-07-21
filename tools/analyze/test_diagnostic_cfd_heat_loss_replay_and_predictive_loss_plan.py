import csv
import json
import tempfile
import unittest
from pathlib import Path

from tools.analyze.build_diagnostic_cfd_heat_loss_replay_and_predictive_loss_plan import build_package


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class DiagnosticCfdHeatLossReplayAndPredictiveLossPlanTests(unittest.TestCase):
    def test_forced_replay_is_exact_but_not_predictive(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            out = Path(tmp)
            summary = build_package(out)

            self.assertEqual(summary["forced_replay_rows"], 15)
            self.assertEqual(summary["case_count"], 3)
            self.assertEqual(summary["predictive_rows_admitted_from_forced_replay"], 0)

            rows = read_csv(out / "diagnostic_forced_cfd_heat_loss_replay.csv")
            self.assertEqual({row["admissibility_status"] for row in rows}, {"diagnostic_only_not_predictive"})
            self.assertEqual({row["predictive_status"] for row in rows}, {"not_predictive_runtime_leakage_diagnostic"})
            self.assertTrue(all(row["diagnostic_runtime_input"] == "realized_CFD_wallHeatFlux" for row in rows))
            self.assertLess(max(abs(float(row["model_minus_cfd_realized_net_W"])) for row in rows), 1.0e-9)

    def test_case_summary_closes_net_heat_path_by_construction(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            out = Path(tmp)
            build_package(out)

            rows = read_csv(out / "diagnostic_forced_replay_case_summary.csv")
            self.assertEqual({row["segment_count"] for row in rows}, {"5"})
            self.assertEqual({row["diagnostic_result"] for row in rows}, {"exact_net_heat_path_replay_by_construction"})
            self.assertTrue(
                all(abs(float(row["model_minus_cfd_realized_net_sum_W"])) < 1.0e-9 for row in rows)
            )
            self.assertTrue(all("realized CFD wallHeatFlux" in row["why_not_predictive"] for row in rows))

    def test_train_test_rows_do_not_promote_val_salt2(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            out = Path(tmp)
            build_package(out)

            rows = {row["case_key"]: row for row in read_csv(out / "train_test_data_sufficiency.csv")}
            self.assertEqual(rows["salt1_nominal"]["can_fit_heat_loss_variant"], "true")
            self.assertEqual(rows["salt2_lo5q"]["can_score_heat_loss_variant"], "true")
            self.assertEqual(rows["val_salt_test_2_coarse_mesh"]["can_score_heat_loss_variant"], "not_yet_for_section_heat_loss")
            self.assertIn("not_found", rows["val_salt_test_2_coarse_mesh"]["data_sufficiency_conclusion"])
            self.assertIn("Do not train Salt1-4", rows["salt2_salt3_salt4_mainline_split"]["guardrail"])

    def test_jin_vs_val_status_records_report_but_not_thermal_replay(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            out = Path(tmp)
            build_package(out)

            rows = {row["evidence_item"]: row for row in read_csv(out / "jin_vs_val_salt2_report_status.csv")}
            self.assertEqual(rows["val_salt2_lineage_and_bc_report"]["status"], "produced")
            self.assertEqual(rows["salt2_jin_vs_val_comparison_table"]["status"], "produced")
            self.assertEqual(rows["val_salt2_section_heat_loss_replay"]["exists"], "false")
            self.assertEqual(rows["val_salt2_section_heat_loss_replay"]["status"], "not_found_as_current_report_package")

    def test_predictive_plan_contains_required_setup_quantities(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            out = Path(tmp)
            build_package(out)

            plan_text = "\n".join(
                " ".join(row.values()) for row in read_csv(out / "predictive_heat_loss_variant_plan.csv")
            )
            for token in ["junction/stub", "wall/shell", "h, Ta, Tsur, emissivity", "setup-only HX/cooler"]:
                self.assertIn(token, plan_text)
            self.assertIn("No realized CFD wallHeatFlux", plan_text)

    def test_summary_json_records_no_mutation(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            out = Path(tmp)
            build_package(out)
            parsed = json.loads((out / "summary.json").read_text(encoding="utf-8"))

            self.assertFalse(parsed["native_cfd_outputs_mutated"])
            self.assertFalse(parsed["external_cfd_modeling_tools_mutated"])
            self.assertFalse(parsed["scheduler_mutated"])
            self.assertEqual(parsed["val_salt2_current_heat_loss_test_status"], "not_yet_section_heat_loss_admitted")


if __name__ == "__main__":
    unittest.main()
