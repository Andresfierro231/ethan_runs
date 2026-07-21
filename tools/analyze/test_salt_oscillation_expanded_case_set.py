#!/usr/bin/env python3
"""Tests for the expanded Salt oscillation case-set builder."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import build_salt_oscillation_expanded_case_set as expanded


class ExpandedCaseSetTests(unittest.TestCase):
    def test_extra_cases_include_requested_nominal_rows_and_val2(self) -> None:
        keys = {r["case_key"] for r in expanded.EXTRA_CASES}
        self.assertIn("salt2_jin_nominal", keys)
        self.assertIn("salt3_jin_nominal", keys)
        self.assertIn("salt2_native_val", keys)

    def test_expanded_cases_record_missing_salt1_val(self) -> None:
        _cases, resolution = expanded.expanded_cases()
        missing = [r for r in resolution if r["requested"] == "val_salt_test_1 / salt1_val"]
        self.assertEqual(len(missing), 1)
        self.assertEqual(missing[0]["status"], "not_found")


if __name__ == "__main__":
    unittest.main()
