from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from tools.analyze import (
    build_s13_upcomer_exchange_same_label_mesh_family_inventory_and_generation_contract as builder,
)


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class S13SameLabelMeshFamilyInventoryTests(unittest.TestCase):
    def test_inventory_reviews_exact_four_s13_qois(self) -> None:
        rows = builder.same_label_mesh_family_inventory_rows()
        self.assertEqual(len(rows), 4)
        self.assertEqual(set(row["qoi_label"] for row in rows), set(builder.QOI_SPECS))
        self.assertTrue(all(row["temporal_uq_available"] == "true" for row in rows))

    def test_inventory_fails_closed_without_same_label_mesh_family_rows(self) -> None:
        rows = builder.same_label_mesh_family_inventory_rows()
        self.assertTrue(all(row["existing_same_label_mesh_family_rows"] == "0" for row in rows))
        self.assertTrue(all(row["accepted_same_label_mesh_gci_rows"] == "0" for row in rows))
        self.assertTrue(
            all(row["inventory_decision"] == "missing_same_label_mesh_family_generate_contract" for row in rows)
        )
        self.assertTrue(all(row["production_use_allowed_now"] == "false" for row in rows))

    def test_generation_contract_pins_exact_labels_and_windows(self) -> None:
        rows = builder.generation_contract_rows()
        self.assertEqual(len(rows), 4)
        self.assertTrue(all(row["same_qoi_rule"].startswith("exact label") for row in rows))
        self.assertTrue(all("salt_2:7914,7915,7916" in row["required_time_windows_s"] for row in rows))
        qwall = next(row for row in rows if row["qoi_label"] == "Q_wall_W")
        self.assertIn("positive Q_wall_W adds heat", qwall["formula_sign_basis_required"])

    def test_build_outputs_next_compute_contract_and_closed_production_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "pkg"
            summary = builder.build(out)
            self.assertEqual(summary["decision"], "same_label_mesh_family_absent_generation_contract_ready")
            self.assertEqual(summary["qoi_label_count"], 4)
            self.assertEqual(summary["accepted_same_label_mesh_gci_rows"], 0)
            self.assertTrue(summary["next_compute_contract_ready"])
            self.assertFalse(summary["production_harvest_allowed"])
            gates = {row["gate"]: row for row in read_rows(out / "production_gate.csv")}
            self.assertEqual(gates["same_label_mesh_gci_uq"]["status"], "blocked_missing_same_label_mesh_family")
            self.assertEqual(gates["next_compute_contract"]["status"], "ready_to_claim")
            self.assertEqual(gates["production_harvest_or_admission"]["status"], "do_not_run")


if __name__ == "__main__":
    unittest.main()
