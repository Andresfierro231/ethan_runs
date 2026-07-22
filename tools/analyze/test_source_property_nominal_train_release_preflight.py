import csv
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools.analyze import build_source_property_nominal_train_release_preflight as builder


class SourcePropertyNominalTrainReleasePreflightTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tempdir = tempfile.TemporaryDirectory()
        cls.out = Path(cls.tempdir.name) / "preflight"
        cls.patch = mock.patch.object(builder, "OUT", cls.out)
        cls.patch.start()
        cls.summary = builder.build()

    @classmethod
    def tearDownClass(cls):
        cls.patch.stop()
        cls.tempdir.cleanup()

    def read_rows(self, name):
        with (self.out / name).open(newline="") as handle:
            return list(csv.DictReader(handle))

    def test_nominal_rows_are_complete_but_not_released(self):
        rows = self.read_rows("nominal_train_release_audit.csv")
        self.assertEqual(len(rows), 4)
        self.assertEqual({row["labels_complete"] for row in rows}, {"True"})
        self.assertEqual({row["release_ready"] for row in rows}, {"False"})
        self.assertEqual({row["protected_row_release"] for row in rows}, {"False"})

    def test_source_family_rollup_preserves_blockers(self):
        rows = self.read_rows("source_family_blocker_rollup.csv")
        self.assertEqual(sum(int(row["nominal_train_rows"]) for row in rows), 4)
        self.assertEqual({row["release_status"] for row in rows}, {"blocked"})
        blockers = " ".join(row["missing_or_blocking_evidence"] for row in rows)
        self.assertIn("Salt1", blockers)
        self.assertIn("mixed/outside/unknown", blockers)

    def test_candidate_consequence_rows_block_s11_s15(self):
        rows = self.read_rows("candidate_lane_consequences.csv")
        self.assertGreaterEqual(len(rows), 5)
        self.assertTrue(
            all(
                any(token in row["s11_consequence"] for token in ("cannot", "no candidate", "thesis"))
                for row in rows
            )
        )
        self.assertTrue(
            all(
                any(token in row["s15_consequence"] for token in ("cannot", "no frozen"))
                for row in rows
            )
        )

    def test_summary_guardrails(self):
        with (self.out / "summary.json").open() as handle:
            summary = json.load(handle)
        self.assertEqual(summary["release_ready_rows"], 0)
        self.assertEqual(summary["protected_rows_released"], 0)
        self.assertFalse(summary["source_property_release"])
        self.assertFalse(summary["candidate_freeze"])
        self.assertFalse(summary["validation_holdout_external_scoring"])


if __name__ == "__main__":
    unittest.main()
