from __future__ import annotations

import csv
import json
import unittest

from tools.analyze import build_fluid_extbc_passive_h2_cand001_source_basis_enrichment as builder


class PassiveH2SourceBasisEnrichmentTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        builder.main()
        cls.out = builder.OUT

    def read_csv(self, name: str) -> list[dict[str, str]]:
        with (self.out / name).open(newline="", encoding="utf-8") as handle:
            return list(csv.DictReader(handle))

    def test_summary_remains_no_repair(self) -> None:
        summary = json.loads((self.out / "summary.json").read_text(encoding="utf-8"))
        self.assertEqual(summary["decision"], builder.DECISION)
        self.assertEqual(summary["source_family_rows"], 5)
        self.assertEqual(summary["families_released"], 0)
        self.assertFalse(summary["source_property_release"])
        self.assertFalse(summary["run_one_train_repair"])

    def test_no_family_is_source_released(self) -> None:
        rows = self.read_csv("source_basis_coverage.csv")
        self.assertEqual(len(rows), 5)
        self.assertTrue(all(row["current_q_inside_engineering_envelope"] == "True" for row in rows))
        self.assertTrue(all(row["independent_source_release_allowed_now"] == "false" for row in rows))
        self.assertTrue(all(row["repair_ready_now"] == "false" for row in rows))

    def test_wall_heat_flux_provenance_blocks_current_basis(self) -> None:
        rows = self.read_csv("wallheatflux_dependence_audit.csv")
        self.assertEqual(len(rows), 12)
        self.assertTrue(all(row["wall_heat_flux_provenance_present"] == "True" for row in rows))
        self.assertTrue(all(row["release_effect"] == "blocks_source_property_release" for row in rows))

    def test_s11_s15_s6_stay_blocked(self) -> None:
        rows = self.read_csv("s11_s15_s6_consequence.csv")
        self.assertEqual(rows[0]["s11_unblocked"], "false")
        self.assertEqual(rows[0]["s15_unblocked"], "false")
        self.assertEqual(rows[0]["s6_unblocked"], "false")
        self.assertEqual(rows[0]["candidate_count_released"], "0")


if __name__ == "__main__":
    unittest.main()
