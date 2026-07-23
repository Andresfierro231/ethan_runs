#!/usr/bin/env python3
"""Tests for the Chapter 3 CFD provenance/QoI compact packet."""

from __future__ import annotations

import unittest

from tools.analyze import build_thesis_ch3_cfd_provenance_qoi_compact_packet as builder


class ThesisCh3CfdProvenanceQoiCompactPacketTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.summary = builder.build()

    def test_inventory_counts_are_preserved(self) -> None:
        self.assertEqual(self.summary["source_count"], 23)
        self.assertEqual(self.summary["parsed_source_count"], 23)
        self.assertEqual(self.summary["tidy_rows"], 1405596)
        self.assertEqual(self.summary["window_stat_rows"], 16353)

    def test_packet_tables_have_expected_shape(self) -> None:
        counts = self.summary["validated_csv_row_counts"]
        self.assertEqual(counts["case_provenance_table.csv"], 11)
        self.assertEqual(counts["qoi_dictionary.csv"], 12)
        self.assertEqual(counts["figure_table_targets.csv"], 7)

    def test_guardrails_remain_closed(self) -> None:
        self.assertFalse(self.summary["runtime_forbidden_inputs_released"])
        self.assertFalse(self.summary["native_solver_outputs_mutated"])
        self.assertFalse(self.summary["registry_or_admission_mutated"])
        self.assertFalse(self.summary["scheduler_action"])
        self.assertFalse(self.summary["fluid_external_repository_mutated"])
        self.assertFalse(self.summary["heat_residual_hidden_in_internal_nu"])


if __name__ == "__main__":
    unittest.main()
