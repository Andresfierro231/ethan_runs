from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path

from tools.analyze.build_flow_rate_temperature_bc_response_study import FIGURES, build


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


class FlowRateTemperatureBCResponseStudyTests(unittest.TestCase):
    def test_builds_expected_outputs(self) -> None:
        with tempfile.TemporaryDirectory(prefix="flow-bc-study-") as tmp:
            out = Path(tmp)
            summary = build(out)
            self.assertEqual(summary["task"], "AGENT-351")
            self.assertEqual(summary["paper_hardened_by"], "AGENT-359")
            self.assertGreaterEqual(summary["case_rows"], 10)
            for name in [
                "README.md",
                "case_bc_response_matrix.csv",
                "patch_role_bc_summary.csv",
                "flow_temperature_response_summary.csv",
                "trend_correlation_analysis.csv",
                "paper_conclusions.csv",
                "corrected_q_pm5_response_overlay.csv",
                "paper_ready_analysis.md",
                "invalid_or_diagnostic_runs.csv",
                "bc_semantics_and_assumptions.csv",
                "source_manifest.csv",
                "summary.json",
            ]:
                self.assertTrue((out / name).exists(), name)
            for fig in FIGURES:
                path = out / "figures" / fig
                self.assertTrue(path.exists(), fig)
                self.assertGreater(path.stat().st_size, 500, fig)

    def test_mainline_salt_rows_have_mdot_temperature_and_split(self) -> None:
        with tempfile.TemporaryDirectory(prefix="flow-bc-study-") as tmp:
            out = Path(tmp)
            build(out)
            by_key = {row["case_key"]: row for row in rows(out / "case_bc_response_matrix.csv")}
            for key, split in {
                "salt2_jin": "training",
                "salt3_jin": "validation",
                "salt4_jin": "holdout",
            }.items():
                self.assertIn(key, by_key)
                self.assertEqual(by_key[key]["evidence_class"], "admitted_or_usable")
                self.assertIn(split, by_key[key]["split_or_use_status"])
                self.assertNotEqual(by_key[key]["mdot_mean_abs_kg_s"], "")
                self.assertNotEqual(by_key[key]["timeseries_probe_T_avg_K"], "")

    def test_corrected_q_terminal_rows_are_split_pending_not_training(self) -> None:
        with tempfile.TemporaryDirectory(prefix="flow-bc-study-") as tmp:
            out = Path(tmp)
            build(out)
            by_key = {row["case_key"]: row for row in rows(out / "case_bc_response_matrix.csv")}
            for key in {"salt2_lo5q", "salt2_hi5q", "salt4_lo5q", "salt4_hi5q"}:
                self.assertIn(key, by_key)
                self.assertEqual(by_key[key]["evidence_class"], "terminal_harvested_split_pending")
                self.assertNotEqual(by_key[key]["evidence_class"], "admitted_or_usable")
                self.assertNotEqual(by_key[key]["source_case_key"], "")
                self.assertNotEqual(by_key[key]["q_ratio"], "")
                self.assertNotEqual(by_key[key]["pm5_cooling_branch_total_removal_mean_W"], "")
                self.assertIn("sensitivity/admission evidence", by_key[key]["split_or_use_status"])

    def test_false_steady_rows_are_invalid_provenance(self) -> None:
        with tempfile.TemporaryDirectory(prefix="flow-bc-study-") as tmp:
            out = Path(tmp)
            build(out)
            invalid = rows(out / "invalid_or_diagnostic_runs.csv")
            by_key = {row["case_key"]: row for row in invalid}
            self.assertIn("salt2_jin_hiq_hiins", by_key)
            self.assertEqual(by_key["salt2_jin_hiq_hiins"]["evidence_class"], "invalid_false_steady")
            self.assertIn("T3-perturbation", by_key["salt2_jin_hiq_hiins"]["evidence_paths"])
            self.assertNotEqual(by_key["salt2_jin_hiq_hiins"]["expected_mdot_move_pct"], "")

    def test_radiation_semantics_and_patch_roles_are_explicit(self) -> None:
        with tempfile.TemporaryDirectory(prefix="flow-bc-study-") as tmp:
            out = Path(tmp)
            build(out)
            semantics = {row["rule_id"]: row for row in rows(out / "bc_semantics_and_assumptions.csv")}
            self.assertIn("radiation_embedded_in_wallheatflux", semantics)
            self.assertIn("no separate exported `qr`", semantics["radiation_embedded_in_wallheatflux"]["study_consequence"])

            patch_roles = rows(out / "patch_role_bc_summary.csv")
            roles = {row["role"] for row in patch_roles}
            for role in {"heater", "cooler", "test_section", "ambient_wall", "junction_other"}:
                self.assertIn(role, roles)
            salt2_heater = [
                row for row in patch_roles
                if row["source_id"] == "viscosity_screening_salt_test_2_jin_coarse_mesh"
                and row["role"] == "heater"
            ]
            self.assertEqual(len(salt2_heater), 1)
            self.assertNotEqual(salt2_heater[0]["area_weighted_emissivity"], "")

    def test_summary_and_import_record_no_mutation(self) -> None:
        with tempfile.TemporaryDirectory(prefix="flow-bc-study-") as tmp:
            out = Path(tmp)
            summary = build(out)
            self.assertFalse(summary["native_cfd_outputs_mutated"])
            self.assertFalse(summary["external_cfd_modeling_tools_mutated"])
            parsed = json.loads((out / "summary.json").read_text(encoding="utf-8"))
            self.assertEqual(parsed["task"], "AGENT-351")
            self.assertEqual(parsed["paper_hardened_by"], "AGENT-359")

    def test_trend_analysis_is_paper_limited_not_causal(self) -> None:
        with tempfile.TemporaryDirectory(prefix="flow-bc-study-") as tmp:
            out = Path(tmp)
            build(out)
            trends = rows(out / "trend_correlation_analysis.csv")
            by_scope_var = {(row["scope"], row["variable"]): row for row in trends}
            probe = by_scope_var[("admitted_or_usable_with_mdot", "timeseries_probe_T_avg_K")]
            self.assertEqual(probe["n"], "3")
            self.assertNotEqual(probe["slope_kg_s_per_unit"], "")
            self.assertNotEqual(probe["r_squared"], "")
            self.assertIn("not a controlled causal fit", probe["trend_statement"])
            self.assertEqual(probe["paper_use"], "paper_observational_trend_limited_n3")

    def test_paper_ready_outputs_capture_conclusions_and_guardrails(self) -> None:
        with tempfile.TemporaryDirectory(prefix="flow-bc-study-") as tmp:
            out = Path(tmp)
            build(out)
            conclusions = {row["conclusion_id"]: row for row in rows(out / "paper_conclusions.csv")}
            for key in {
                "C1_mainline_flow_temperature_ordering",
                "C4_old_q_perturbations_are_not_physical_response_rows",
                "C5_corrected_pm5q_rows_are_sensitivity_evidence",
                "C6_radiation_semantics",
            }:
                self.assertIn(key, conclusions)
            self.assertIn("observational", conclusions["C1_mainline_flow_temperature_ordering"]["paper_claim_strength"])
            text = (out / "paper_ready_analysis.md").read_text(encoding="utf-8")
            self.assertIn("not a controlled causal fit", text)
            self.assertIn("no separate exported `qr`", text)
            self.assertIn("Old Q perturbation", text)
            self.assertIn("Salt2", text)
            self.assertIn("Salt3", text)
            self.assertIn("Salt4", text)


if __name__ == "__main__":
    unittest.main()
