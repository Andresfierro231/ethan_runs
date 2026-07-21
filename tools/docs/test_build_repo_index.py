#!/usr/bin/env python3
"""Self-contained tests for build_repo_index (no pytest dependency).

Run: python3 tools/docs/test_build_repo_index.py
"""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_repo_index as bri  # noqa: E402


class ParseFrontmatter(unittest.TestCase):
    def test_frontmatter_parsed(self):
        text = "---\ntask: AGENT-1\ntags: [a, b]\nstatus: complete\n---\n# Title\nbody\n"
        fm, body = bri.parse_frontmatter(text)
        self.assertEqual(fm["task"], "AGENT-1")
        self.assertEqual(fm["tags"], ["a", "b"])
        self.assertTrue(body.startswith("# Title"))

    def test_no_frontmatter(self):
        fm, body = bri.parse_frontmatter("# Title\nno fm\n")
        self.assertIsNone(fm)


class Inference(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()

    def _write(self, rel, text):
        full = os.path.join(self.d, rel)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8") as fh:
            fh.write(text)
        return rel

    def test_legacy_status_inferred_from_conventions(self):
        rel = self._write(
            ".agent/status/2026-07-13_AGENT-42.md",
            "# AGENT-42 Status\n\nDate: `2026-07-13`\nRole: Writer\n"
            "STATUS: BLOCKED waiting on mesh\nTags: #mesh-gci #foo\n")
        rec = bri.build_record(self.d, rel, "status")
        self.assertEqual(rec["task"], "AGENT-42")
        self.assertEqual(rec["date"], "2026-07-13")
        self.assertEqual(rec["status"], "blocked")
        self.assertIn("mesh-gci", rec["tags"])
        self.assertFalse(rec["has_frontmatter"])

    def test_frontmatter_wins_over_inference(self):
        rel = self._write(
            "operational_notes/07-26/13/note.md",
            "---\ntask: AGENT-9\ndate: 2026-07-13\nstatus: complete\n"
            "tags: [radiation]\n---\n# Note\nSTATUS: BLOCKED (this should be ignored)\n")
        rec = bri.build_record(self.d, rel, "operational_note")
        self.assertTrue(rec["has_frontmatter"])
        self.assertEqual(rec["status"], "complete")
        self.assertEqual(rec["tags"], ["radiation"])


class BoardParsing(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.d, ".agent"))

    def test_active_rows_and_status_token(self):
        with open(os.path.join(self.d, ".agent", "BOARD.md"), "w") as fh:
            fh.write(
                "# Task Board\n## Active\n"
                "| Task ID | Role | Owner | Scope | Goal |\n| --- | --- | --- | --- | --- |\n"
                "| AGENT-1 | Writer | claude | x | did a thing. STATUS: COMPLETE 2026-07-13. |\n"
                "| AGENT-2 | Impl | codex | y | pending. STATUS: BLOCKED on mesh. |\n"
                "## Planned\n| AGENT-99 | ... | ... | ... | ... STATUS: OPEN |\n")
        rows = bri.parse_board(self.d)
        self.assertEqual(len(rows), 2)  # Planned excluded
        self.assertEqual(rows[0]["status"], "COMPLETE")
        # board status is kept as a phrase so substring token-matching works
        self.assertTrue(rows[1]["status"].startswith("BLOCKED"))
        self.assertTrue(any(t in rows[1]["status"] for t in bri.OPEN_STATUS_TOKENS))


class BlockerValidation(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        # create an evidence file used by valid entries
        os.makedirs(os.path.join(self.d, "ev"))
        open(os.path.join(self.d, "ev", "e.md"), "w").close()

    def test_valid_register(self):
        blockers = [
            {"id": "a", "status": "open", "severity": "high",
             "evidence": "ev/e.md", "last_reviewed": "2026-07-13"},
            {"id": "b", "status": "resolved", "resolved_by": "x",
             "resolved_on": "2026-07-01", "evidence": "ev/e.md"},
            {"id": "c", "status": "superseded", "superseded_by": "a",
             "superseded_on": "2026-07-09", "evidence": "ev/e.md"},
        ]
        self.assertEqual(bri.validate_blockers(self.d, blockers), [])

    def test_open_with_resolved_by_fails(self):
        blockers = [{"id": "a", "status": "open", "resolved_by": "x",
                     "evidence": "ev/e.md", "last_reviewed": "2026-07-13"}]
        errs = bri.validate_blockers(self.d, blockers)
        self.assertTrue(any("resolved_by/superseded_by" in e for e in errs))

    def test_missing_evidence_fails(self):
        blockers = [{"id": "a", "status": "open", "evidence": "ev/nope.md",
                     "last_reviewed": "2026-07-13"}]
        errs = bri.validate_blockers(self.d, blockers)
        self.assertTrue(any("evidence path missing" in e for e in errs))

    def test_superseded_by_unknown_id_fails(self):
        blockers = [{"id": "a", "status": "superseded", "superseded_by": "ghost",
                     "superseded_on": "2026-07-09", "evidence": "ev/e.md"}]
        errs = bri.validate_blockers(self.d, blockers)
        self.assertTrue(any("unknown id" in e for e in errs))


class RealRegister(unittest.TestCase):
    """The shipped .agent/blockers.yml must validate against the real repo."""
    def test_repo_register_valid(self):
        root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        reg = os.path.join(root, ".agent", "blockers.yml")
        if not os.path.isfile(reg) or bri.yaml is None:
            self.skipTest("no register or no yaml")
        errs = bri.validate_blockers(root, bri.load_blockers(root))
        self.assertEqual(errs, [], "seeded register should validate: %r" % errs)


if __name__ == "__main__":
    unittest.main(verbosity=2)
