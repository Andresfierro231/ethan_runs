#!/usr/bin/env python3
"""Tests for direct recirculation model forms and dry scorers."""

from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools.analyze import build_direct_recirc_model_forms_and_dry_scorers as mod


class DirectRecircModelFormsDryScorersTest(unittest.TestCase):
    def test_frozen_forms_are_research_only(self) -> None:
        rows = mod.frozen_model_forms()

        self.assertEqual([row["form_id"] for row in rows], ["UH1", "CR1", "ROX1"])
        self.assertTrue(all(row["fit_allowed_now"] == "false" for row in rows))
        self.assertTrue(all(row["admission_allowed_now"] == "false" for row in rows))
        self.assertIn("ordinary Nu", rows[0]["do_not_do"])
        self.assertIn("component K", rows[1]["do_not_do"])

    def test_regime_label_detects_recirculation_and_transition(self) -> None:
        self.assertEqual(mod.regime_label(0.79, 0.50, 200.0, 0.75), "recirculation_diagnostic")
        self.assertEqual(mod.regime_label(0.02, 0.0, 0.1, 0.0), "transition_near_onset_candidate")
        self.assertEqual(mod.regime_label(0.0, 0.0, 0.0, 0.0), "ordinary_candidate_requires_pressure_uq")

    def test_upcomer_dry_scores_remain_non_admission(self) -> None:
        rows = mod.upcomer_hybrid_dry_score_rows()

        self.assertGreaterEqual(len(rows), 4)
        self.assertTrue(all(row["fit_allowed_now"] == "false" for row in rows))
        self.assertTrue(all(row["admission_allowed_now"] == "false" for row in rows))
        self.assertTrue(any(row["source_family"] == "PM10_matched_plane" for row in rows))
        self.assertTrue(any(row["regime_classification"] == "recirculation_diagnostic" for row in rows))

    def test_corner_dry_scores_do_not_admit_component_k_or_f6(self) -> None:
        rows = mod.corner_residual_dry_score_rows()

        self.assertEqual(len(rows), 3)
        self.assertTrue(all(row["fit_allowed_now"] == "false" for row in rows))
        self.assertTrue(all(row["component_k_admitted"] == "false" for row in rows))
        self.assertTrue(all(row["f6_fit_performed"] == "false" for row in rows))
        self.assertTrue(all("do_not_promote" in row["guardrail"] for row in rows))

    def test_main_writes_package(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            out = base / "out"
            status = base / "status.md"
            journal = base / "journal.md"
            import_manifest = base / "import.json"
            with (
                mock.patch.object(mod, "OUT", out),
                mock.patch.object(mod, "STATUS", status),
                mock.patch.object(mod, "JOURNAL", journal),
                mock.patch.object(mod, "IMPORT", import_manifest),
            ):
                summary = mod.main()

            self.assertEqual(summary["frozen_model_forms"], 3)
            self.assertEqual(summary["corner_component_k_admitted_rows"], 0)
            self.assertFalse(summary["umx1_grid_authorized"])
            self.assertTrue((out / "frozen_direct_recirc_model_forms.csv").exists())
            self.assertTrue((out / "upcomer_hybrid_dry_scorecard.csv").exists())
            self.assertTrue((out / "corner_residual_dry_scorecard.csv").exists())
            self.assertTrue(status.exists())
            self.assertTrue(journal.exists())
            self.assertTrue(import_manifest.exists())

            with (out / "frozen_direct_recirc_model_forms.csv").open(newline="", encoding="utf-8") as handle:
                forms = list(csv.DictReader(handle))
            self.assertEqual(len(forms), 3)
            with import_manifest.open(encoding="utf-8") as handle:
                manifest = json.load(handle)
            self.assertFalse(manifest["ordinary_coefficients_admitted"])
            self.assertFalse(manifest["native_solver_outputs_mutated"])


if __name__ == "__main__":
    unittest.main()
