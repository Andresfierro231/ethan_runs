from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path

from tools.extract import build_s13_upcomer_exchange_medium_fine_exact_label_sampler as builder


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class S13MediumFineExactLabelSamplerTests(unittest.TestCase):
    def test_contract_covers_expected_case_mesh_pairs(self) -> None:
        contract = builder.contract_rows()
        pairs = {(row["case_id"], row["mesh_level"]) for row in contract}
        self.assertEqual(len(contract), 6)
        self.assertEqual(
            pairs,
            {
                ("salt_2", "medium"),
                ("salt_2", "fine"),
                ("salt_3", "medium"),
                ("salt_3", "fine"),
                ("salt_4", "medium"),
                ("salt_4", "fine"),
            },
        )
        self.assertTrue(all(builder.split_semicolon(row["fallback_terminal_candidate_windows_s"]) for row in contract))
        self.assertTrue(all(row["strict_contract_windows_available"] == "false" for row in contract))

    def test_source_preflight_has_compute_node_status_labels(self) -> None:
        preflight = builder.source_preflight_rows(builder.contract_rows())
        self.assertEqual(len(preflight), 6)
        self.assertTrue(all(row["native_solver_output_mutated"] == "false" for row in preflight))
        self.assertEqual({row["processor_count"] for row in preflight}, {"64", "128"})
        self.assertTrue(
            {
                "ready_for_compute_node_sampling",
                "blocked_missing_required_native_path",
            }.issuperset({row["preflight_status"] for row in preflight})
        )

    def test_filtered_contract_rows_and_limited_windows_support_smoke(self) -> None:
        contract = builder.contract_rows()
        filtered = builder.filtered_contract_rows(contract, case_id="salt_2", mesh_level="medium")

        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]["case_id"], "salt_2")
        self.assertEqual(filtered[0]["mesh_level"], "medium")
        self.assertEqual(len(builder.limited_windows(filtered[0], max_windows=1)), 1)
        self.assertGreater(len(builder.limited_windows(filtered[0], max_windows=0)), 1)

    def test_dry_build_writes_fail_closed_gate_without_heavy_sampling(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "sampler"
            summary = builder.build(out, execute=False, job_id="dry")
            self.assertEqual(summary["decision"], "preflight_ready_heavy_execution_not_run")
            self.assertFalse(summary["execute_mode"])
            self.assertEqual(summary["source_contract_rows"], 6)
            self.assertEqual(summary["terminal_window_reduction_rows"], 0)
            self.assertEqual(summary["exact_label_qoi_rows"], 0)
            self.assertFalse(summary["same_label_mesh_gci_ready"])
            self.assertTrue((out / "source_preflight.csv").exists())
            self.assertTrue((out / "mesh_gci_readiness_gate.csv").exists())
            self.assertEqual(
                {row["gate_status"] for row in rows(out / "mesh_gci_readiness_gate.csv")},
                {"blocked_not_executed_or_no_sampled_rows"},
            )
            json.loads((out / "summary.json").read_text(encoding="utf-8"))

    def test_dry_build_can_target_one_case_window_for_smoke(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "smoke"
            summary = builder.build(
                out,
                execute=False,
                job_id="dry_smoke",
                case_id="salt_2",
                mesh_level="medium",
                max_windows=1,
            )

            self.assertEqual(summary["source_contract_rows"], 1)
            self.assertEqual(summary["case_id_filter"], "salt_2")
            self.assertEqual(summary["mesh_level_filter"], "medium")
            self.assertEqual(summary["max_windows"], 1)
            source_rows = rows(out / "source_preflight.csv")
            self.assertEqual(len(source_rows), 1)
            self.assertEqual(len(source_rows[0]["terminal_candidate_windows_s"].split(";")), 1)

    def test_qoi_rows_preserve_diagnostic_admission_status(self) -> None:
        window_rows = [
            {
                "case_id": "salt_2",
                "mesh_level": "medium",
                "mesh_mask_id": "salt_2_medium",
                "window_role": "terminal",
                "time_window_s": "517",
                "Q_wall_W": "1.0",
                "mdot_exchange_positive_outward_proxy_kg_s": "2.0",
                "tau_recirc_proxy_s": "3.0",
                "wall_core_bulk_temperature_contrast_K": "4.0",
                "sample_status": "terminal_exact_label_sampled_from_read_only_native_processors",
            }
        ]
        qois = builder.qoi_rows(window_rows)
        self.assertEqual(len(qois), 4)
        self.assertEqual({row["qoi_label"] for row in qois}, set(builder.QOI_LABELS))
        self.assertTrue(
            all(row["admission_status"] == "diagnostic_only_mesh_time_equivalence_gate_pending" for row in qois)
        )
        self.assertTrue(all(row["geometry_mask_id"] == "salt_2_medium" for row in qois))

    def test_interface_reduction_uses_supplied_medium_fine_area_vectors(self) -> None:
        interface_rows = [
            {
                "face_id": 10,
                "owner": 1,
                "neighbour": 2,
                "seed_owner_cell": 1,
                "adjacent_core_cell": 2,
                "area_m2": 2.0,
                "area_vector_x_m2": 2.0,
                "area_vector_y_m2": 0.0,
                "area_vector_z_m2": 0.0,
            },
            {
                "face_id": 11,
                "owner": 3,
                "neighbour": 4,
                "seed_owner_cell": 4,
                "adjacent_core_cell": 3,
                "area_m2": 3.0,
                "area_vector_x_m2": 3.0,
                "area_vector_y_m2": 0.0,
                "area_vector_z_m2": 0.0,
            },
        ]
        fields = {
            1: {"T": 300.0, "rho": 10.0, "U": (1.0, 0.0, 0.0)},
            2: {"T": 310.0, "rho": 10.0, "U": (1.0, 0.0, 0.0)},
            3: {"T": 320.0, "rho": 20.0, "U": (1.0, 0.0, 0.0)},
            4: {"T": 330.0, "rho": 20.0, "U": (1.0, 0.0, 0.0)},
        }

        reduced = builder.interface_reduction(interface_rows, fields)

        self.assertAlmostEqual(reduced["area_m2"], 5.0)
        self.assertAlmostEqual(reduced["seed_T_area_K"], (300.0 * 2.0 + 330.0 * 3.0) / 5.0)
        self.assertAlmostEqual(reduced["core_T_area_K"], (310.0 * 2.0 + 320.0 * 3.0) / 5.0)
        self.assertAlmostEqual(reduced["mdot_net_kg_s"], 20.0 - 60.0)
        self.assertAlmostEqual(reduced["mdot_positive_outward_kg_s"], 20.0)
        self.assertAlmostEqual(reduced["mdot_negative_inward_kg_s"], -60.0)

    def test_face_contract_writer_preserves_area_vector_columns(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "faces.csv"
            builder.dump_csv(
                path,
                [
                    builder.add_area_vector_columns(
                        {
                            "face_id": 7,
                            "area_m2": 2.0,
                            "owner": 1,
                            "neighbour": 2,
                        },
                        (2.0, 0.5, -0.25),
                    )
                ],
            )

            face_rows = rows(path)

        selfEqual = self.assertEqual
        selfEqual(face_rows[0]["area_vector_x_m2"], "2.0")
        selfEqual(face_rows[0]["area_vector_y_m2"], "0.5")
        selfEqual(face_rows[0]["area_vector_z_m2"], "-0.25")

    def test_interface_reduction_fails_closed_without_area_vectors(self) -> None:
        with self.assertRaisesRegex(ValueError, "missing area vectors"):
            builder.interface_reduction(
                [
                    {
                        "face_id": 10,
                        "owner": 1,
                        "neighbour": 2,
                        "seed_owner_cell": 1,
                        "adjacent_core_cell": 2,
                        "area_m2": 1.0,
                    }
                ],
                {
                    1: {"T": 300.0, "rho": 10.0, "U": (1.0, 0.0, 0.0)},
                    2: {"T": 310.0, "rho": 10.0, "U": (1.0, 0.0, 0.0)},
                },
            )


if __name__ == "__main__":
    unittest.main()
