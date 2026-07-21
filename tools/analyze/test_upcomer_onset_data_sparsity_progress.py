import csv
import tempfile
import unittest
from pathlib import Path

from tools.analyze import build_upcomer_onset_data_sparsity_progress as prog


class UpcomerOnsetDataSparsityProgressTests(unittest.TestCase):
    def test_material_recirculation_blocks_ordinary_labels(self):
        classification, allowed, forbidden, nu, fd, k = prog.classify_row(
            backflow=0.20,
            raf=None,
            rmf=None,
            ri=1.5,
            pressure_status="present",
            thermal_status="present",
            uncertainty_status="present",
        )
        self.assertEqual(classification, "recirculation_diagnostic")
        self.assertIn("hybrid", allowed)
        self.assertIn("ordinary_Nu", forbidden)
        self.assertEqual((nu, fd, k), ("no", "no", "no"))

    def test_ordinary_candidate_requires_all_fields(self):
        missing = prog.classify_row(
            backflow=0.0,
            raf=None,
            rmf=None,
            ri=0.1,
            pressure_status="present",
            thermal_status="missing",
            uncertainty_status="present",
        )
        self.assertNotEqual(missing[0], "ordinary_single_stream_candidate")
        complete = prog.classify_row(
            backflow=0.0,
            raf=None,
            rmf=None,
            ri=0.1,
            pressure_status="present",
            thermal_status="present",
            uncertainty_status="present",
        )
        self.assertEqual(complete[0], "ordinary_single_stream_candidate")
        self.assertEqual(complete[3:], ("conditional", "conditional", "conditional"))

    def test_current_ledger_has_zero_ordinary_fit_rows(self):
        rows = prog.ledger_rows()
        self.assertGreater(len(rows), 0)
        ordinary = [
            row
            for row in rows
            if row["ordinary_Nu_fit_allowed"] in {"yes", "conditional"}
            or row["ordinary_f_D_fit_allowed"] in {"yes", "conditional"}
            or row["component_K_fit_allowed"] in {"yes", "conditional"}
        ]
        self.assertEqual(ordinary, [])
        self.assertIn("recirculation_diagnostic", {row["classification"] for row in rows})

    def test_decision_keeps_blocker_open(self):
        rows = prog.ledger_rows()
        decision = prog.decision_payload(rows, prog.anchor_inventory_rows(rows))
        self.assertEqual(decision["decision"], "keep_open")
        self.assertEqual(decision["ordinary_fit_rows"], 0)
        self.assertFalse(decision["current_rows_are_fit_evidence"])

    def test_build_emits_required_outputs_in_tempdir(self):
        original_out = prog.OUT
        with tempfile.TemporaryDirectory() as tmp:
            prog.OUT = Path(tmp)
            try:
                summary = prog.build()
                self.assertEqual(summary["task"], prog.TASK)
                required = [
                    "upcomer_row_admission_ledger.csv",
                    "anchor_inventory.csv",
                    "same_window_field_gap_table.csv",
                    "evidence_gap_queue.csv",
                    "hybrid_upcomer_model_contract.csv",
                    "misuse_guardrail_summary.csv",
                    "blocker_decision.json",
                    "source_manifest.csv",
                    "summary.json",
                    "README.md",
                ]
                for name in required:
                    self.assertTrue((prog.OUT / name).exists(), name)
                with (prog.OUT / "upcomer_row_admission_ledger.csv").open(newline="", encoding="utf-8") as handle:
                    rows = list(csv.DictReader(handle))
                self.assertEqual(len(rows), summary["ledger_rows"])
                self.assertEqual({row["ordinary_Nu_fit_allowed"] for row in rows}, {"no"})
            finally:
                prog.OUT = original_out


if __name__ == "__main__":
    unittest.main()
