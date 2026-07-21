#!/usr/bin/env python3
"""Unit tests for AGENT-411 Salt oscillation report builder."""

from __future__ import annotations

import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_salt_training_testing_oscillation_steady_state import (
    common_mean_series,
    fluctuation_series,
    normalize_postprocessing,
    representative_series,
)
from openfoam_timeseries import Series


class SaltOscillationBuilderTests(unittest.TestCase):
    def test_normalize_postprocessing_accepts_case_or_postprocessing_path(self) -> None:
        base = Path("/tmp/example_case")
        self.assertEqual(normalize_postprocessing(str(base)), base / "postProcessing")
        self.assertEqual(normalize_postprocessing(str(base / "postProcessing")), base / "postProcessing")

    def test_common_mean_series_aligns_common_times_only(self) -> None:
        a = Series("a", "temperature", "K", [0.0, 1.0, 2.0], [10.0, 12.0, 14.0])
        b = Series("b", "temperature", "K", [1.0, 2.0, 3.0], [20.0, 22.0, 24.0])
        mean = common_mean_series([a, b], "mean", "temperature")
        self.assertIsNotNone(mean)
        assert mean is not None
        self.assertEqual(mean.t, [1.0, 2.0])
        self.assertEqual(mean.y, [16.0, 18.0])

    def test_representative_prefers_lower_heater_for_mdot(self) -> None:
        upper = Series("upper (cooler)", "mdot", "kg/s", [0, 1], [1, 1])
        lower = Series("lower (heater)", "mdot", "kg/s", [0, 1], [2, 2])
        self.assertIs(representative_series("mdot", [upper, lower]), lower)

    def test_fluctuation_series_removes_last_window_mean(self) -> None:
        s = Series("x", "temperature", "K", [0, 1, 2, 3], [1.0, 2.0, 4.0, 6.0])
        f = fluctuation_series(s, 2.0)
        self.assertIsNotNone(f)
        assert f is not None
        self.assertEqual(f.t, [1, 2, 3])
        self.assertAlmostEqual(sum(f.y), 0.0)
        self.assertTrue(math.isclose(f.y[0], -2.0))


if __name__ == "__main__":
    unittest.main()
