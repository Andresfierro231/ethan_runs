import csv
import json
import tempfile
import unittest
from pathlib import Path

from tools.analyze.build_forward_v1_row_admission_ledger import ALLOWED_CLASSES, build_package


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class ForwardV1RowAdmissionLedgerTests(unittest.TestCase):
    def test_ledger_uses_only_allowed_classes_and_keeps_final_blocked(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            out = Path(tmp)
            summary = build_package(out)

            self.assertEqual(summary["task"], "AGENT-407")
            self.assertEqual(
                summary["final_forward_v1_status"],
                "blocked_no_go_final_forward_v1_not_admitted",
            )
            ledger = read_csv(out / "row_admission_ledger.csv")
            self.assertGreater(len(ledger), 20)
            self.assertTrue({row["admission_class"] for row in ledger}.issubset(ALLOWED_CLASSES))
            self.assertIn("predictive_candidate", {row["admission_class"] for row in ledger})
            self.assertIn("diagnostic_replay", {row["admission_class"] for row in ledger})
            self.assertIn("diagnostic_upper_bound", {row["admission_class"] for row in ledger})
            self.assertIn("blocked_empty_fit_set", {row["admission_class"] for row in ledger})

    def test_internal_nu_rows_are_explicitly_empty_and_blocked(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            out = Path(tmp)
            summary = build_package(out)

            self.assertEqual(summary["internal_nu_admitted_rows"], 0)
            rows = read_csv(out / "internal_nu_fit_rows.csv")
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["admitted_row_count"], "0")
            self.assertEqual(rows[0]["admission_class"], "blocked_empty_fit_set")
            self.assertEqual(rows[0]["wallHeatFlux_rows"], "0")
            self.assertIn("wall-bulk/Gz/onset", rows[0]["blocker"])

    def test_predictive_hx_rows_are_setup_legal_candidates(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            out = Path(tmp)
            summary = build_package(out)

            self.assertEqual(summary["preferred_setup_legal_hx_candidate"], "salt2_fit_constant_UA_bulk_drive")
            hx_rows = read_csv(out / "final_predictive_hx_closure_rows.csv")
            preferred = [row for row in hx_rows if row["candidate_id"] == "salt2_fit_constant_UA_bulk_drive"]
            self.assertEqual({row["split_role"] for row in preferred}, {"train", "validation", "holdout"})
            self.assertTrue(all(row["runtime_input_violation_count"] == "0" for row in hx_rows))
            reconciliation = {
                row["candidate_id"]: row for row in read_csv(out / "hx_candidate_reconciliation.csv")
            }
            self.assertEqual(
                reconciliation["salt2_fit_constant_UA_bulk_drive"]["decision"],
                "preferred_current_candidate",
            )

    def test_diagnostic_leakage_rows_are_not_predictive(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            out = Path(tmp)
            build_package(out)

            imposed = read_csv(out / "imposed_cooler_diagnostic_rows.csv")
            self.assertGreaterEqual(len(imposed), 6)
            self.assertTrue(all(row["admission_class"] == "diagnostic_upper_bound" for row in imposed))
            self.assertTrue(all("never report as predictive" in row["blocker"] for row in imposed))

            ledger = read_csv(out / "row_admission_ledger.csv")
            predictive_forms = {
                row["model_form"] for row in ledger if row["admission_class"] == "predictive_candidate"
            }
            self.assertNotIn("imposed_cfd_cooler_upper_bound", predictive_forms)
            self.assertNotIn("salt2_fit_cooler_imposed_ratio", predictive_forms)

    def test_summary_json_written_with_guardrails(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            out = Path(tmp)
            build_package(out)
            parsed = json.loads((out / "summary.json").read_text(encoding="utf-8"))

            self.assertFalse(parsed["native_cfd_outputs_mutated"])
            self.assertFalse(parsed["external_cfd_modeling_tools_mutated"])
            self.assertFalse(parsed["scheduler_mutated"])
            self.assertEqual(parsed["runtime_input_audit_violations"], 0)


if __name__ == "__main__":
    unittest.main()
