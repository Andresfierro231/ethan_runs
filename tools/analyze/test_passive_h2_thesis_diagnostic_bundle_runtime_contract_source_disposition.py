import csv
import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "tools/analyze/build_passive_h2_thesis_diagnostic_bundle_runtime_contract_source_disposition.py"
OUT = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_passive_h2_thesis_diagnostic_bundle_runtime_contract_source_disposition"


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class PassiveH2ThesisDiagnosticBundleTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        subprocess.run([sys.executable, str(SCRIPT)], cwd=ROOT, check=True, stdout=subprocess.PIPE, text=True)

    def test_summary_declares_diagnostic_completion_and_closed_admission(self) -> None:
        summary = json.loads((OUT / "summary.json").read_text(encoding="utf-8"))
        self.assertEqual(
            summary["decision"],
            "passive_h2_thesis_diagnostic_bundle_complete_no_score_runtime_contract_source_property_fail_closed",
        )
        self.assertEqual(summary["runtime_diagnostic_case_rows"], 4)
        self.assertEqual(summary["runtime_completed_rows"], 4)
        self.assertEqual(summary["runtime_nonzero_delta_rows"], 4)
        self.assertEqual(summary["diagnostic_score_rows"], 12)
        self.assertEqual(summary["svg_figure_files"], 5)
        self.assertEqual(summary["release_allowed_rows"], 0)
        self.assertEqual(summary["freeze_allowed_rows"], 0)
        self.assertEqual(summary["score_allowed_rows"], 0)
        self.assertFalse(summary["source_property_release"])
        self.assertFalse(summary["candidate_freeze"])
        self.assertFalse(summary["protected_or_final_scoring"])

    def test_four_case_runtime_table_includes_salt1(self) -> None:
        runtime = rows(OUT / "passive_h2_four_case_runtime_diagnostic.csv")
        self.assertEqual({row["case_id"] for row in runtime}, {"salt_1", "salt_2", "salt_3", "salt_4"})
        self.assertTrue(all(row["runtime_completed"] == "true" for row in runtime))
        self.assertTrue(all(row["protected_scoring"] == "false" for row in runtime))
        salt1 = [row for row in runtime if row["case_id"] == "salt_1"][0]
        self.assertEqual(salt1["target_status"], "no_target_ratio_emitted")
        self.assertGreater(float(salt1["radiation_delta_W"]), 0.0)

    def test_runtime_contract_forbids_solver_and_protected_inputs(self) -> None:
        contract = rows(OUT / "no_score_runtime_input_contract.csv")
        by_field = {row["field"]: row for row in contract}
        self.assertEqual(by_field["area_m2"]["allowed_as_runtime_input"], "true")
        self.assertEqual(by_field["predicted_outer_surface_temperature_K"]["allowed_as_runtime_input"], "true")
        for field in ["wallHeatFlux", "Qwall_W", "CFD_mdot", "TP_or_TW_observed_K", "hidden_global_multiplier"]:
            self.assertEqual(by_field[field]["allowed_as_runtime_input"], "false")
            self.assertEqual(by_field[field]["protected_or_forbidden"], "true")

    def test_source_property_disposition_fail_closes_all_current_rows(self) -> None:
        disposition = rows(OUT / "source_property_final_disposition.csv")
        self.assertEqual(len(disposition), 20)
        self.assertTrue(all(row["release_allowed_now"] == "false" for row in disposition))
        self.assertTrue(all(row["freeze_allowed_now"] == "false" for row in disposition))
        self.assertTrue(all(row["score_allowed_now"] == "false" for row in disposition))
        salt1_junction = [
            row for row in disposition if row["case_id"] == "salt_1" and row["source_family"] == "junction"
        ]
        self.assertEqual(len(salt1_junction), 1)
        self.assertEqual(salt1_junction[0]["setup_basis_status"], "missing_case_family_coverage")

    def test_figures_and_captions_exist_and_mark_caveats(self) -> None:
        figure_rows = rows(OUT / "figure_manifest.csv")
        caption_rows = rows(OUT / "figure_caption_bank.csv")
        self.assertEqual(len(figure_rows), 5)
        self.assertEqual(len(caption_rows), 5)
        for row in figure_rows:
            svg = OUT / row["filename"]
            self.assertTrue(svg.exists(), svg)
            text = svg.read_text(encoding="utf-8")
            self.assertIn("<svg", text)
            self.assertIn("Diagnostic", text)
        captions = " ".join(row["caption_text"] for row in caption_rows)
        self.assertIn("not final", captions.lower())
        self.assertIn("no release", captions.lower())

    def test_claim_language_has_allowed_and_forbidden_claims(self) -> None:
        claims = rows(OUT / "thesis_claim_language.csv")
        self.assertGreaterEqual(sum(row["allowed"] == "true" for row in claims), 3)
        self.assertGreaterEqual(sum(row["allowed"] == "false" for row in claims), 2)
        forbidden_text = " ".join(row["claim_text"] for row in claims if row["allowed"] == "false")
        self.assertIn("source/property release", forbidden_text)
        self.assertIn("final frozen score", forbidden_text)

    def test_guardrails_all_false(self) -> None:
        guardrails = rows(OUT / "no_mutation_guardrails.csv")
        self.assertTrue(guardrails)
        self.assertTrue(all(row["value"] == "false" for row in guardrails))


if __name__ == "__main__":
    unittest.main()
