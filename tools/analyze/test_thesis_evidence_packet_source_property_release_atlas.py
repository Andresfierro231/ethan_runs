import csv
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools.analyze import build_thesis_evidence_packet_source_property_release_atlas as builder


class ThesisEvidencePacketSourcePropertyReleaseAtlasTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tempdir = tempfile.TemporaryDirectory()
        cls.out = Path(cls.tempdir.name) / "source-property-atlas"
        cls.patch = mock.patch.object(builder, "OUT", cls.out)
        cls.patch.start()
        cls.summary = builder.build()

    @classmethod
    def tearDownClass(cls):
        cls.patch.stop()
        cls.tempdir.cleanup()

    def rows(self, name):
        with (self.out / name).open(newline="", encoding="utf-8") as handle:
            return list(csv.DictReader(handle))

    def test_atlas_has_no_release_ready_rows(self):
        rows = self.rows("source_property_release_atlas.csv")
        self.assertGreaterEqual(len(rows), 10)
        self.assertEqual({row["release_ready"] for row in rows}, {"no"})
        self.assertEqual({row["protected_row_release_allowed"] for row in rows}, {"no"})

    def test_core_blockers_are_preserved(self):
        rows = self.rows("source_property_release_atlas.csv")
        text = " ".join(row["source_or_property_family"] + " " + row["primary_blocker"] for row in rows)
        for token in ("Salt1", "mixed/outside/unknown", "S13 exchange Qwall", "empirical correction", "junction/stub"):
            self.assertIn(token, text)

    def test_runtime_legality_blocks_target_leakage(self):
        rows = self.rows("runtime_legality_audit.csv")
        text = " ".join(row["input_family"] for row in rows)
        for token in ("CFD mdot", "wallHeatFlux", "cooler duty", "validation/holdout/external temperatures"):
            self.assertIn(token, text)
        self.assertTrue(all(row["runtime_allowed"] in {"no", "label_only"} for row in rows))

    def test_summary_guardrails(self):
        with (self.out / "summary.json").open(encoding="utf-8") as handle:
            summary = json.load(handle)
        self.assertEqual(summary["release_ready_rows"], 0)
        self.assertEqual(summary["protected_rows_released"], 0)
        self.assertFalse(summary["source_property_release"])
        self.assertFalse(summary["candidate_freeze"])
        self.assertFalse(summary["residual_absorbed_into_internal_nu"])


if __name__ == "__main__":
    unittest.main()
