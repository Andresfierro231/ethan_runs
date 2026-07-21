#!/usr/bin/env python3
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools.analyze import build_m2_scoring_gate_resolver as mod


class M2ScoringGateResolverTest(unittest.TestCase):
    def test_no_salt1_cooler_hx_is_not_fabricated(self) -> None:
        search = mod.build_salt1_cooler_hx_source_search()
        decision = mod.build_m2_score_ready_policy_decision(search)[0]

        self.assertFalse(any(row["salt1_cooler_hx_supported"] == "true" for row in search))
        self.assertEqual(decision["decision"], "blocked_missing_salt1_cooler_hx")
        self.assertEqual(decision["exception_granted"], "false")

    def test_holdout_release_gate_keeps_score_now_disabled(self) -> None:
        decision = {"holdout_score_release": "false"}
        rows = mod.build_holdout_score_release_gate(decision)

        self.assertTrue(rows)
        self.assertTrue(all(row["score_now"] == "no" for row in rows))
        self.assertTrue(all(row["fit_allowed"] == "no" for row in rows))

    def test_main_writes_resolver(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            with (
                mock.patch.object(mod, "OUT", base / "out"),
                mock.patch.object(mod, "STATUS", base / "status.md"),
                mock.patch.object(mod, "JOURNAL", base / "journal.md"),
                mock.patch.object(mod, "IMPORT", base / "import.json"),
            ):
                summary = mod.main()

            self.assertEqual(summary["score_gate_status"], "blocked_missing_salt1_cooler_hx")
            self.assertEqual(summary["holdout_rows_scored"], 0)
            with (base / "out/m2_score_ready_artifact_candidate.json").open() as handle:
                artifact = json.load(handle)
            self.assertFalse(artifact["score_ready"])


if __name__ == "__main__":
    unittest.main()
