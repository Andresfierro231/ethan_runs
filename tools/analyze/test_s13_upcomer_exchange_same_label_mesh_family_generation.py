from __future__ import annotations

import csv
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.analyze import build_s13_upcomer_exchange_same_label_mesh_family_generation as builder


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class S13SameLabelMeshFamilyGenerationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.scan_rows = builder.scan_local_candidates()
        cls.matrix_rows = builder.candidate_matrix_rows(cls.scan_rows)

    def test_candidate_matrix_is_exact_four_qois_by_three_mesh_levels(self) -> None:
        self.assertEqual(len(self.matrix_rows), 12)
        self.assertEqual({row["qoi_label"] for row in self.matrix_rows}, set(builder.QOI_LABELS))
        self.assertEqual({row["mesh_level"] for row in self.matrix_rows}, set(builder.MESH_LEVELS))
        self.assertGreater(len(self.scan_rows), 0)

    def test_strict_same_label_mesh_rows_are_absent_fail_closed(self) -> None:
        self.assertTrue(all(row["strict_same_label_mesh_rows"] == "0" for row in self.matrix_rows))
        self.assertTrue(all(row["admissible_for_mesh_gci_now"] == "false" for row in self.matrix_rows))
        self.assertTrue(
            all(row["decision"] == "missing_strict_same_label_mesh_level_row" for row in self.matrix_rows)
        )

    def test_generation_preflight_covers_all_cases_qois_and_mesh_levels(self) -> None:
        rows = builder.generation_input_preflight_rows(self.matrix_rows)
        self.assertEqual(len(rows), 36)
        self.assertEqual({row["case_id"] for row in rows}, set(builder.CASE_WINDOWS))
        coarse_rows = [row for row in rows if row["mesh_level"] == "coarse"]
        self.assertTrue(all(row["current_single_mesh_temporal_triplet_available"] == "true" for row in coarse_rows))
        self.assertTrue(
            all(
                row["preflight_status"] == "current_coarse_temporal_triplet_available_not_mesh_family"
                for row in coarse_rows
            )
        )
        noncoarse_rows = [row for row in rows if row["mesh_level"] != "coarse"]
        self.assertTrue(all(row["current_single_mesh_temporal_triplet_available"] == "false" for row in noncoarse_rows))
        self.assertTrue(all(row["preflight_status"] == "missing_generation_artifact" for row in noncoarse_rows))

    def test_current_coarse_rows_and_gap_matrix_are_explicit(self) -> None:
        current_rows = builder.current_coarse_generated_rows()
        self.assertEqual(len(current_rows), 12)
        self.assertEqual({row["mesh_level"] for row in current_rows}, {"current_coarse_continuation"})
        self.assertTrue(all(row["mesh_gci_use_allowed_now"] == "false" for row in current_rows))
        gap_rows = builder.required_mesh_level_gap_rows()
        self.assertEqual(len(gap_rows), 36)
        medium_fine = [row for row in gap_rows if row["mesh_level"] in {"medium", "fine"}]
        self.assertTrue(all(row["same_label_row_present"] == "false" for row in medium_fine))

    def test_build_outputs_no_submit_contract_and_closed_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "pkg"
            original_scan = builder.scan_local_candidates
            builder.scan_local_candidates = lambda: list(self.scan_rows)
            try:
                summary = builder.build(out)
            finally:
                builder.scan_local_candidates = original_scan
            self.assertEqual(
                summary["decision"],
                "fail_closed_current_coarse_only_medium_fine_missing_no_submit_contract_ready",
            )
            self.assertEqual(summary["qoi_mesh_level_cells"], 12)
            self.assertEqual(summary["strict_same_label_mesh_level_cells_ready"], 0)
            self.assertEqual(summary["current_coarse_rows_generated"], 12)
            self.assertEqual(summary["required_mesh_level_gap_rows"], 36)
            self.assertEqual(summary["generation_input_preflight_rows"], 36)
            self.assertEqual(summary["command_contract_rows"], 9)
            self.assertFalse(summary["scheduler_or_sampler_launched"])
            self.assertFalse(summary["mesh_gci_computed"])
            self.assertFalse(summary["production_harvest_allowed"])
            self.assertFalse(summary["admission_allowed"])
            gates = {row["gate"]: row for row in read_rows(out / "production_gate.csv")}
            self.assertEqual(gates["strict_same_label_mesh_level_rows"]["status"], "blocked")
            self.assertEqual(gates["scheduler_or_sampler_launch"]["status"], "forbidden")
            self.assertEqual(gates["production_harvest_or_admission"]["status"], "do_not_run")
            commands = read_rows(out / "compute_node_command_contract.csv")
            self.assertTrue(all(row["run_allowed_from_this_task"] == "false" for row in commands))
            mesh_gate = {row["qoi_label"]: row for row in read_rows(out / "mesh_gci_generation_gate.csv")}
            self.assertEqual(set(mesh_gate), set(builder.QOI_LABELS))
            self.assertTrue(all(row["mesh_gci_ready"] == "false" for row in mesh_gate.values()))


if __name__ == "__main__":
    unittest.main()
