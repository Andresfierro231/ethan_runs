#!/usr/bin/env python3
"""Tests for the section-effective hybrid pressure scorecard builder."""
from __future__ import annotations

import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from tools.analyze import build_two_tap_section_effective_hybrid_pressure_scorecard as builder
from tools.analyze import check_two_tap_section_effective_hybrid_pressure_scorecard as checker


class SectionEffectiveHybridPressureScorecardTests(unittest.TestCase):
    def test_builds_expected_case_rows(self) -> None:
        rows = builder.build_scorecard_rows()
        self.assertEqual({"salt_2", "salt_3", "salt_4"}, {row["case_id"] for row in rows})
        self.assertTrue(all(row["final_label"] == "section_effective" for row in rows))
        self.assertTrue(all("component_K" in row["forbidden_use"] for row in rows))

    def test_salt2_frozen_diagnostic_is_not_refit(self) -> None:
        rows = builder.build_scorecard_rows()
        three = builder.build_three_level_rows(rows)
        salt2_k = next(row["K_eff_recirc_diagnostic"] for row in rows if row["case_id"] == "salt_2")
        frozen = [row for row in three if row["score_level"] == "salt2_frozen_diagnostic"]
        self.assertEqual(3, len(frozen))
        self.assertTrue(all(row["K_eff_recirc_used"] == salt2_k for row in frozen))
        self.assertTrue(all(row["admission_status"] == "not_admitted" for row in frozen))

    def test_oracle_rows_are_nonpredictive_and_exact(self) -> None:
        rows = builder.build_scorecard_rows()
        three = builder.build_three_level_rows(rows)
        oracle = [row for row in three if row["score_level"] == "oracle_envelope_nonpredictive"]
        self.assertEqual(3, len(oracle))
        self.assertTrue(all(row["score_status"] == "oracle_upper_bound_nonpredictive" for row in oracle))
        self.assertTrue(all(Decimal(row["abs_error_pa"]) == Decimal("0") for row in oracle))

    def test_package_checker_passes_after_build(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp)
            summary = builder.build(out_dir)
            self.assertEqual(0, summary["component_k_admitted_rows"])
            self.assertEqual([], checker.check(out_dir))


if __name__ == "__main__":
    unittest.main()
