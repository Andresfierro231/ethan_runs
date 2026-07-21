#!/usr/bin/env python3
"""Tests for AGENT-416 user train scope builder."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import build_salt_oscillation_user_train_scope as scope


class UserTrainScopeTests(unittest.TestCase):
    def test_requested_scope_contains_salt1_salt2_salt3_train_and_salt2_val(self) -> None:
        keys = {row["case_key"]: row for row in scope.USER_SCOPE_CASES}
        self.assertEqual(keys["salt1_jin_nominal"]["split_role"], "canonical_forward_train")
        self.assertEqual(keys["salt2_jin_nominal"]["split_role"], "canonical_forward_train")
        self.assertEqual(keys["salt3_jin_nominal"]["split_role"], "canonical_forward_train")
        self.assertEqual(keys["salt2_native_val"]["split_role"], "diagnostic_validation_comparison")

    def test_selected_cases_promotes_salt1_nominal_continuation(self) -> None:
        cases, _resolution = scope.selected_cases()
        by_key = {case.case_key: case for case in cases}
        self.assertEqual(by_key["salt1_nominal"].split_role, "canonical_forward_train")
        self.assertIn("salt2_native_val", by_key)


if __name__ == "__main__":
    unittest.main()
