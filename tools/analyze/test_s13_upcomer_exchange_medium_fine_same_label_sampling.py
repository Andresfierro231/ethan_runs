from __future__ import annotations

import csv
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.analyze import build_s13_upcomer_exchange_medium_fine_same_label_sampling as builder


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class S13MediumFineSameLabelSamplingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.inventory = builder.source_run_inventory_rows()
        cls.needs = builder.sampling_need_rows(cls.inventory)

    def test_inventory_finds_all_medium_fine_salt_source_runs(self) -> None:
        self.assertEqual(len(self.inventory), 6)
        self.assertEqual({row["case_id"] for row in self.inventory}, set(builder.CASES))
        self.assertEqual({row["mesh_level"] for row in self.inventory}, set(builder.MESHES))
        self.assertTrue(all(row["source_root_exists"] == "true" for row in self.inventory))
        self.assertTrue(all(row["processors_dir_exists"] == "true" for row in self.inventory))
        self.assertTrue(all(int(row["processor_time_count"]) > 1 for row in self.inventory))

    def test_source_runs_have_terminal_fields_but_not_strict_coarse_contract_windows(self) -> None:
        for row in self.inventory:
            fields = set(row["latest_time_fields_present"].split(";"))
            self.assertTrue({"U", "T", "rho", "wallHeatFlux"}.issubset(fields))
            self.assertEqual(row["all_required_contract_windows_present"], "false")
            self.assertNotEqual(row["latest_three_nonzero_processor_times_s"], "")

    def test_sampling_need_matrix_covers_all_cases_meshes_and_qois(self) -> None:
        self.assertEqual(len(self.needs), 24)
        self.assertEqual({row["qoi_label"] for row in self.needs}, set(builder.QOI_LABELS))
        self.assertEqual({row["case_id"] for row in self.needs}, set(builder.CASES))
        self.assertEqual({row["mesh_level"] for row in self.needs}, set(builder.MESHES))
        self.assertTrue(all(row["existing_exact_s13_row_present"] == "false" for row in self.needs))
        self.assertTrue(all(row["mesh_gci_use_allowed_now"] == "false" for row in self.needs))
        self.assertTrue(
            all(
                row["sampling_status"]
                == "ready_for_terminal_window_sampling_needs_mesh_time_equivalence_gate"
                for row in self.needs
            )
        )

    def test_build_outputs_readonly_contract_and_closed_mesh_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "pkg"
            summary = builder.build(out)
            self.assertEqual(
                summary["decision"],
                "medium_fine_runs_exist_exact_s13_rows_absent_sampling_contract_ready",
            )
            self.assertEqual(summary["source_run_inventory_rows"], 6)
            self.assertEqual(summary["source_runs_available"], 6)
            self.assertEqual(summary["sampling_need_rows"], 24)
            self.assertEqual(summary["terminal_sampling_ready_rows"], 24)
            self.assertEqual(summary["exact_contract_window_ready_rows"], 0)
            self.assertEqual(summary["existing_exact_s13_medium_fine_rows"], 0)
            self.assertFalse(summary["mesh_gci_ready_now"])
            self.assertFalse(summary["scheduler_or_sampler_launched"])
            commands = read_rows(out / "sampling_command_contract.csv")
            self.assertEqual(len(commands), 6)
            self.assertTrue(all(row["run_allowed_from_this_task"] == "false" for row in commands))
            gate = read_rows(out / "mesh_gci_readiness_after_medium_fine_inventory.csv")
            self.assertEqual(len(gate), 4)
            self.assertTrue(all(row["mesh_gci_ready_now"] == "false" for row in gate))


if __name__ == "__main__":
    unittest.main()
