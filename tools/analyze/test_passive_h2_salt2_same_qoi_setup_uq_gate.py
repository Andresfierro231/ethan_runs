from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from tools.analyze import build_passive_h2_salt2_same_qoi_setup_uq_gate as builder


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class PassiveH2Salt2SameQoiSetupUqGateTests(unittest.TestCase):
    def test_qoi_readiness_is_diagnostic_not_release(self) -> None:
        readiness = builder.qoi_readiness_rows()
        self.assertEqual(len(readiness), 6)
        self.assertTrue(all(row["target_minus_plus_available"] == "true" for row in readiness))
        self.assertTrue(all(row["setup_only_uq_gate"] == "pass_diagnostic" for row in readiness))
        self.assertTrue(all(row["release_ready_now"] == "false" for row in readiness))

    def test_qoi_envelopes_are_finite_for_all_labels(self) -> None:
        envelopes = builder.qoi_envelope_rows()
        self.assertEqual(len(envelopes), 6)
        self.assertTrue(all(row["gate_decision"] == "pass_diagnostic_no_release" for row in envelopes))
        self.assertTrue(all(int(row["release_ready_rows"]) == 0 for row in envelopes))

    def test_build_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "pkg"
            summary = builder.build(out)
            self.assertEqual(summary["decision"], "passive_h2_salt2_same_qoi_setup_uq_diagnostic_ready_no_release")
            self.assertEqual(summary["diagnostic_ready_qoi_labels"], 6)
            self.assertEqual(summary["release_ready_qoi_labels"], 0)
            self.assertEqual(
                summary["subspan_release_recovery_available"],
                (builder.SUBSPAN / "summary.json").exists(),
            )
            self.assertFalse(summary["candidate_freeze"])
            self.assertFalse(summary["protected_scoring"])
            self.assertEqual(len(rows(out / "qoi_readiness_gate.csv")), 6)


if __name__ == "__main__":
    unittest.main()
