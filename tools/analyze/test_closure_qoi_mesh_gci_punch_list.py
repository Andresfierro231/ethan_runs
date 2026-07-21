"""Tests for AGENT-450 closure-QOI mesh/GCI punch-list builder."""

from __future__ import annotations

import csv
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.analyze.build_closure_qoi_mesh_gci_punch_list import (
    Inputs,
    build_package,
    bucket_for,
)


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


class ClosureQoiMeshGciPunchListTests(unittest.TestCase):
    def test_bucket_rules_prioritize_named_policy_blocks(self) -> None:
        self.assertEqual(
            bucket_for(
                {
                    "classification": "blocked-downcomer-policy",
                    "complete_triplet": "no",
                    "publication_ready": "no",
                    "fit_admissible": "no",
                }
            ),
            "downcomer_policy_blocked",
        )
        self.assertEqual(
            bucket_for(
                {
                    "classification": "blocked-sign-review",
                    "complete_triplet": "no",
                    "publication_ready": "no",
                    "fit_admissible": "no",
                }
            ),
            "thermal_admission_review_required",
        )

    def test_synthetic_fixture_exercises_all_outputs(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            root = Path(tmp)
            refreshed = root / "refreshed.csv"
            gci_results = root / "gci_results.csv"
            gci_decisions = root / "gci_decisions.csv"
            thermal = root / "thermal.csv"
            raw = root / "raw.csv"
            stations = root / "stations.csv"
            adjacent = root / "adjacent.csv"
            exp_stations = root / "expanded_stations.csv"
            exp_adjacent = root / "expanded_adjacent.csv"
            blockers = root / "blockers.yml"
            output = root / "out"

            refreshed_fields = [
                "case_id",
                "source_id",
                "qoi_family",
                "lane",
                "qoi_id",
                "span",
                "segment",
                "method",
                "quantity",
                "classification",
                "publication_ready",
                "fit_admissible",
                "complete_triplet",
                "coarse_available",
                "medium_available",
                "fine_available",
                "gci_status",
                "convergence_verdict",
                "blockers",
                "coarse_source_path",
                "medium_source_path",
                "fine_source_path",
                "decision_source_path",
                "gci_source_path",
            ]
            write_csv(
                refreshed,
                [
                    {
                        "case_id": "salt_2",
                        "source_id": "src",
                        "qoi_family": "closure",
                        "lane": "momentum_corrected_friction",
                        "qoi_id": "admitted",
                        "span": "lower_leg",
                        "quantity": "f",
                        "classification": "publication-ready GCI",
                        "publication_ready": "yes",
                        "fit_admissible": "yes",
                        "complete_triplet": "yes",
                        "coarse_available": "yes",
                        "medium_available": "yes",
                        "fine_available": "yes",
                    },
                    {
                        "case_id": "salt_2",
                        "source_id": "src",
                        "qoi_family": "closure",
                        "lane": "pressure_gradient_friction",
                        "qoi_id": "missing",
                        "span": "upper_leg",
                        "quantity": "f",
                        "classification": "blocked-missing-triplet",
                        "publication_ready": "no",
                        "fit_admissible": "no",
                        "complete_triplet": "no",
                        "coarse_available": "no",
                        "medium_available": "yes",
                        "fine_available": "yes",
                    },
                    {
                        "case_id": "salt_2",
                        "source_id": "src",
                        "qoi_family": "thermal",
                        "lane": "thermal_segment_closure",
                        "qoi_id": "sign",
                        "segment": "lower_leg",
                        "quantity": "HTC",
                        "classification": "blocked-sign-review",
                        "publication_ready": "no",
                        "fit_admissible": "no",
                        "complete_triplet": "yes",
                        "coarse_available": "yes",
                        "medium_available": "yes",
                        "fine_available": "yes",
                    },
                    {
                        "case_id": "salt_2",
                        "source_id": "src",
                        "qoi_family": "thermal",
                        "lane": "thermal_segment_closure",
                        "qoi_id": "downcomer",
                        "segment": "downcomer",
                        "quantity": "wallHeatFlux",
                        "classification": "blocked-downcomer-policy",
                        "publication_ready": "no",
                        "fit_admissible": "no",
                        "complete_triplet": "no",
                        "coarse_available": "no",
                        "medium_available": "no",
                        "fine_available": "no",
                    },
                    {
                        "case_id": "salt_2",
                        "source_id": "src",
                        "qoi_family": "closure",
                        "lane": "momentum_corrected_friction",
                        "qoi_id": "oscillatory",
                        "span": "right_leg",
                        "quantity": "f",
                        "classification": "non-monotone/oscillatory",
                        "publication_ready": "no",
                        "fit_admissible": "no",
                        "complete_triplet": "yes",
                        "coarse_available": "yes",
                        "medium_available": "yes",
                        "fine_available": "yes",
                    },
                    {
                        "case_id": "salt_2",
                        "source_id": "src",
                        "qoi_family": "closure",
                        "lane": "custom_pressure_lane",
                        "qoi_id": "pressure_gate",
                        "span": "test_section",
                        "quantity": "K",
                        "classification": "manual-review",
                        "publication_ready": "no",
                        "fit_admissible": "no",
                        "complete_triplet": "yes",
                        "coarse_available": "yes",
                        "medium_available": "yes",
                        "fine_available": "yes",
                        "blockers": "not_fit_safe_pressure_recovery_or_noise",
                    },
                ],
                refreshed_fields,
            )
            write_csv(
                gci_results,
                [
                    {"qoi_id": "admitted", "verdict": "monotonic_convergence", "gci_trustworthy": "yes"},
                    {"qoi_id": "oscillatory", "verdict": "oscillatory", "gci_trustworthy": "no"},
                ],
                ["qoi_id", "verdict", "gci_trustworthy"],
            )
            write_csv(gci_decisions, [{"qoi_id": "admitted"}], ["qoi_id"])
            write_csv(thermal, [{"case_id": "salt_2"}], ["case_id"])
            write_csv(raw, [{"case_id": "salt_2"}], ["case_id"])
            station_fields = ["case_key", "reverse_area_fraction_proxy"]
            write_csv(stations, [{"case_key": "salt2", "reverse_area_fraction_proxy": "0.25"}], station_fields)
            write_csv(exp_stations, [{"case_key": "salt1", "reverse_area_fraction_proxy": "0.005"}], station_fields)
            write_csv(adjacent, [{"case_key": "salt2"}], ["case_key"])
            write_csv(exp_adjacent, [{"case_key": "salt1"}], ["case_key"])
            blockers.write_text("blockers: []\n", encoding="utf-8")

            summary = build_package(
                output,
                Inputs(
                    refreshed_qoi_status=refreshed,
                    thermal_admission=thermal,
                    gci_decisions=gci_decisions,
                    gci_results=gci_results,
                    raw_two_tap=raw,
                    pressure_ladder_stations=stations,
                    pressure_ladder_adjacent=adjacent,
                    expanded_pressure_stations=exp_stations,
                    expanded_pressure_adjacent=exp_adjacent,
                    blockers_yml=blockers,
                ),
            )

            self.assertEqual(summary["qoi_row_count"], 6)
            self.assertEqual(summary["admitted_only_candidate_count"], 1)
            self.assertEqual(summary["extraction_queue_count"], 2)
            self.assertEqual(summary["admission_only_count"], 3)
            self.assertIn("closure-qoi-mesh-gci", (output / "closure_qoi_narrowing_decision.md").read_text())

    def test_current_repo_evidence_remains_narrowed_not_resolved(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            summary = build_package(Path(tmp) / "out")
            self.assertEqual(summary["qoi_row_count"], 25)
            self.assertEqual(summary["admitted_only_candidate_count"], 0)
            self.assertEqual(summary["extraction_queue_count"], 19)
            self.assertEqual(summary["admission_only_count"], 6)
            self.assertEqual(summary["pressure_diagnostics"]["station_rows_with_reverse_area_fraction_lt_0p01"], 0)


if __name__ == "__main__":
    unittest.main()
