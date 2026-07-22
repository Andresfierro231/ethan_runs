#!/usr/bin/env python3
"""Tests for the repo tool inventory builder."""

from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from tools.docs import build_repo_tool_inventory as inventory


class RepoToolInventoryTests(unittest.TestCase):
    def test_discovery_has_core_tools_and_required_fields(self) -> None:
        rows = inventory.discover_tools()
        paths = {row.path for row in rows}
        self.assertIn("tools/agent/finish_task.py", paths)
        self.assertIn("tools/docs/build_repo_index.py", paths)
        self.assertIn("tools/run_openfoam_case.sh", paths)
        for row in rows:
            self.assertTrue(row.path)
            self.assertTrue(row.category)
            self.assertTrue(row.purpose)
            self.assertTrue(row.typical_inputs)
            self.assertTrue(row.typical_outputs)
            self.assertTrue(row.safe_example)
            self.assertTrue(row.when_to_use)
            self.assertTrue(row.when_not_to_use)
            self.assertTrue(row.safety)

    def test_writes_csv_and_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp)
            rows = inventory.discover_tools()
            inventory.write_csv(rows, out_dir / "tool_inventory.csv")
            inventory.write_markdown(rows, out_dir / "tool_index.md")

            csv_path = out_dir / "tool_inventory.csv"
            md_path = out_dir / "tool_index.md"
            self.assertTrue(csv_path.exists())
            self.assertTrue(md_path.exists())

            with csv_path.open(newline="", encoding="utf-8") as handle:
                loaded = list(csv.DictReader(handle))
            self.assertEqual(len(loaded), len(rows))
            self.assertIn("path", loaded[0])
            self.assertIn("safe_example", loaded[0])

            markdown = md_path.read_text(encoding="utf-8")
            self.assertIn("# Tool Index", markdown)
            self.assertIn("tools/agent/finish_task.py", markdown)
            self.assertIn("HPC", markdown)


if __name__ == "__main__":
    unittest.main()
