#!/usr/bin/env python3
"""Tests for the AGENT-325 table update cadence contract."""

from __future__ import annotations

import csv
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.analyze import build_table_update_cadence_contract as cadence


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


class TableUpdateCadenceContractTests(unittest.TestCase):
    def test_table_contract_has_daily_and_gate_triggered_policy(self) -> None:
        rows = cadence.TABLE_CONTRACTS
        self.assertGreaterEqual(len(rows), 8)
        self.assertTrue(any("daily" in row["cadence"] for row in rows))
        self.assertTrue(any("gate_triggered" in row["cadence"] for row in rows))
        for row in rows:
            self.assertTrue(row["gate_triggers"])
            self.assertTrue(row["overclaim_guard"])
            self.assertTrue(row["max_lag"])

    def test_gate_matrix_covers_required_result_events(self) -> None:
        events = {row["gate_event"] for row in cadence.GATE_MATRIX}
        required = {
            "daily_no_gate_refresh",
            "blocker_state_changed",
            "admission_class_changed",
            "scorecard_changed",
            "boundary_model_changed",
            "terminal_cfd_harvest",
        }
        self.assertTrue(required.issubset(events))

    def test_board_parser_maps_active_rows_to_table_ids(self) -> None:
        sample = """
| AGENT-900 | Implementer | codex | `x` | Build final forward-v1 scorecard and thermal admission gate. STATUS: RUNNING 2026. |
| AGENT-901 | Writer | codex | `x` | Corrected Salt-Q terminal harvest. STATUS: COMPLETE 2026. |
"""
        rows = cadence.parse_board_rows(sample)
        self.assertEqual(len(rows), 2)
        self.assertIn("T03", rows[0]["watch_tables"])
        self.assertIn("T02", rows[0]["watch_tables"])
        self.assertIn("T06", rows[1]["watch_tables"])

    def test_run_package_outputs_expected_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp) / "cadence"
            summary = cadence.run_package(out_dir)
            self.assertEqual(summary["cadence_policy"], "daily_plus_gate_triggered")
            self.assertFalse(summary["native_solver_outputs_mutated"])
            self.assertTrue((out_dir / "README.md").exists())
            self.assertTrue((out_dir / "summary.json").exists())
            table_rows = read_csv(out_dir / "table_update_contract.csv")
            self.assertGreaterEqual(len(table_rows), 8)
            gate_rows = read_csv(out_dir / "gate_trigger_matrix.csv")
            self.assertEqual(len(gate_rows), len(cadence.GATE_MATRIX))


if __name__ == "__main__":
    unittest.main()
