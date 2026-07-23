import csv
import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "tools/analyze/build_passive_h2_thesis_evidence_appendix_handoff.py"
OUT = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_passive_h2_thesis_evidence_appendix_handoff"


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class PassiveH2ThesisEvidenceAppendixHandoffTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        subprocess.run([sys.executable, str(SCRIPT)], cwd=ROOT, check=True, stdout=subprocess.PIPE, text=True)

    def test_summary_handoff_ready_and_fail_closed(self) -> None:
        summary = json.loads((OUT / "summary.json").read_text(encoding="utf-8"))
        self.assertEqual(summary["decision"], "passive_h2_thesis_appendix_handoff_ready_diagnostic_only")
        self.assertEqual(summary["figure_count"], 5)
        self.assertEqual(summary["copied_figure_count"], 5)
        self.assertEqual(summary["caption_rows"], 5)
        self.assertGreaterEqual(summary["numeric_evidence_rows"], 19)
        self.assertEqual(summary["runtime_case_rows"], 4)
        self.assertEqual(summary["release_allowed_rows"], 0)
        self.assertEqual(summary["freeze_allowed_rows"], 0)
        self.assertEqual(summary["score_allowed_rows"], 0)
        self.assertFalse(summary["thesis_current_or_latex_edit"])
        self.assertFalse(summary["protected_or_final_scoring"])

    def test_figure_assets_copied_and_captioned(self) -> None:
        figures = rows(OUT / "figure_asset_manifest.csv")
        captions = rows(OUT / "caption_bank.csv")
        self.assertEqual(len(figures), 5)
        self.assertEqual(len(captions), 5)
        for row in figures:
            self.assertEqual(row["exists"], "true")
            target = ROOT / row["handoff_path"]
            self.assertTrue(target.exists(), target)
            self.assertIn("<svg", target.read_text(encoding="utf-8"))
        caption_text = " ".join(row["caption_text"] for row in captions).lower()
        self.assertIn("diagnostic", caption_text)
        self.assertIn("not final", caption_text)

    def test_appendix_drafts_preserve_claim_boundary(self) -> None:
        md = (OUT / "appendix_section_draft.md").read_text(encoding="utf-8")
        tex = (OUT / "appendix_section_latex_snippet.tex").read_text(encoding="utf-8")
        self.assertIn("not an admitted final predictive score", md)
        self.assertIn("Do not use", md)
        self.assertIn("not as", tex)
        self.assertIn("Do not call these final predictive scores", tex)

    def test_numeric_evidence_includes_runtime_and_gate_counts(self) -> None:
        evidence = rows(OUT / "appendix_numeric_evidence.csv")
        tables = {row["table"] for row in evidence}
        self.assertIn("diagnostic_scores", tables)
        self.assertIn("runtime_diagnostics", tables)
        self.assertIn("gate_counts", tables)
        gate_counts = {row["item"]: row for row in evidence if row["table"] == "gate_counts"}
        self.assertEqual(gate_counts["source_property_release_allowed_rows"]["value"], "0")
        self.assertEqual(gate_counts["candidate_freeze_allowed_rows"]["value"], "0")
        self.assertEqual(gate_counts["score_allowed_rows"]["value"], "0")

    def test_claim_boundaries_include_forbidden_warnings(self) -> None:
        claims = rows(OUT / "claim_boundary_table.csv")
        self.assertGreaterEqual(sum(row["allowed"] == "true" for row in claims), 3)
        self.assertGreaterEqual(sum(row["allowed"] == "false" for row in claims), 2)
        forbidden = " ".join(row["claim_text"] for row in claims if row["allowed"] == "false")
        self.assertIn("source/property release", forbidden)
        self.assertIn("final frozen score", forbidden)

    def test_guardrails_all_false(self) -> None:
        guardrails = rows(OUT / "no_mutation_guardrails.csv")
        self.assertTrue(guardrails)
        self.assertTrue(all(row["value"] == "false" for row in guardrails))


if __name__ == "__main__":
    unittest.main()
