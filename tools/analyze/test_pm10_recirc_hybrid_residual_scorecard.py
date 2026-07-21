#!/usr/bin/env python3
"""Tests for the PM10 recirculation hybrid residual scorecard."""
from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path

from tools.analyze import build_pm10_recirc_hybrid_residual_scorecard as mod


FEATURE_FIELDS = [
    "case_key",
    "plane_location",
    "representative_time_s",
    "recirculation_severity_class",
    "reverse_area_fraction",
    "reverse_mass_fraction",
    "secondary_velocity_fraction",
    "Ri",
    "bulk_T_K",
    "wall_T_K",
    "wallHeatFlux_W_m2",
    "delta_T_wall_bulk_K",
    "Re",
    "Pr",
    "Gz",
    "recirculation_anchor_allowed",
    "recirculation_calibration_allowed",
    "hybrid_validation_allowed",
    "source_paths",
]

ADMISSION_FIELDS = [
    "case_key",
    "recirculation_anchor_allowed",
    "recirculation_calibration_allowed",
    "recirculation_model_selection_allowed",
    "hybrid_validation_allowed",
    "ordinary_pipe_fit_allowed",
    "recirculation_severity_class",
    "max_reverse_area_fraction",
    "max_reverse_mass_fraction",
    "max_secondary_velocity_fraction",
    "max_Ri",
    "min_abs_delta_T_wall_bulk_K",
    "allowed_use_now",
    "use_condition",
    "source_paths",
]


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_fixture_inputs(root: Path) -> tuple[Path, Path]:
    feature_path = root / "pm10_recirculation_feature_matrix.csv"
    admission_path = root / "pm10_recirculation_anchor_admission.csv"
    feature_rows: list[dict[str, str]] = []
    admission_rows: list[dict[str, str]] = []
    for index, case_key in enumerate(mod.PM10_CASES, start=1):
        for plane, raf, svf, delta in [
            ("upcomer_inlet", "0.62", "0.08", "-6.0"),
            ("upcomer_mid", "0.37", "0.01", "5.0"),
            ("upcomer_outlet", "0.78", "0.74", "-3.0"),
        ]:
            feature_rows.append(
                {
                    "case_key": case_key,
                    "plane_location": plane,
                    "representative_time_s": str(12000 + index),
                    "recirculation_severity_class": "strong_recirculation",
                    "reverse_area_fraction": raf,
                    "reverse_mass_fraction": "0.50",
                    "secondary_velocity_fraction": svf,
                    "Ri": "100.0",
                    "bulk_T_K": "450.0",
                    "wall_T_K": "444.0",
                    "wallHeatFlux_W_m2": "-300.0",
                    "delta_T_wall_bulk_K": delta,
                    "Re": "100.0",
                    "Pr": "25.0",
                    "Gz": "70.0",
                    "recirculation_anchor_allowed": "yes",
                    "recirculation_calibration_allowed": "conditional",
                    "hybrid_validation_allowed": "yes",
                    "source_paths": f"fixture/{case_key}",
                }
            )
        admission_rows.append(
            {
                "case_key": case_key,
                "recirculation_anchor_allowed": "yes",
                "recirculation_calibration_allowed": "conditional",
                "recirculation_model_selection_allowed": "conditional",
                "hybrid_validation_allowed": "yes",
                "ordinary_pipe_fit_allowed": "no",
                "recirculation_severity_class": "strong_recirculation",
                "max_reverse_area_fraction": "0.78",
                "max_reverse_mass_fraction": "0.50",
                "max_secondary_velocity_fraction": "0.74",
                "max_Ri": "100.0",
                "min_abs_delta_T_wall_bulk_K": "3.0",
                "allowed_use_now": "recirculation_aware_calibration_and_hybrid_validation",
                "use_condition": "recirculation_aware_or_hybrid_models_only",
                "source_paths": f"fixture/{case_key}",
            }
        )
    write_csv(feature_path, FEATURE_FIELDS, feature_rows)
    write_csv(admission_path, ADMISSION_FIELDS, admission_rows)
    return feature_path, admission_path


class Pm10RecircHybridResidualScorecardTests(unittest.TestCase):
    def test_missing_residual_targets_are_explicit_blockers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            feature_path, admission_path = write_fixture_inputs(root)
            residual_path = root / "pressure_upcomer_admission_rollup.csv"
            write_csv(
                residual_path,
                ["case_key", "admission_status", "reason"],
                [{"case_key": case_key, "admission_status": "diagnostic_only_recirculating", "reason": "no_residual"} for case_key in mod.PM10_CASES],
            )

            summary = mod.build_package(
                feature_matrix_path=feature_path,
                anchor_admission_path=admission_path,
                hybrid_contract_path=root / "hybrid_1d_model_contract.csv",
                direct_dry_scorecard_path=root / "upcomer_hybrid_dry_scorecard.csv",
                residual_candidate_paths=[residual_path],
                output_dir=root / "out",
            )

            self.assertEqual(summary["case_count"], 4)
            self.assertEqual(summary["plane_feature_rows"], 12)
            self.assertEqual(summary["residual_target_available_cases"], 0)

            with (root / "out/pm10_recirc_residual_join.csv").open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(len(rows), 4)
            self.assertEqual({row["target_status"] for row in rows}, {"matched_pm10_source_without_pressure_or_thermal_residual"})
            self.assertTrue(all(row["fit_allowed_now"] == "no" for row in rows))

            with (root / "out/pm10_recirc_model_form_scorecard.csv").open(newline="", encoding="utf-8") as handle:
                scores = list(csv.DictReader(handle))
            self.assertEqual(len(scores), 16)
            self.assertEqual({row["score_use"] for row in scores}, {"diagnostic_readiness_only_residual_target_missing"})
            self.assertTrue(all("component_K" in row["forbidden_labels"] for row in scores))

    def test_synthetic_residual_targets_produce_finite_candidate_scores_without_admission(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            feature_path, admission_path = write_fixture_inputs(root)
            residual_path = root / "pm10_residual_targets.csv"
            write_csv(
                residual_path,
                ["case_key", "pressure_residual_pa", "target_status"],
                [
                    {"case_key": case_key, "pressure_residual_pa": str(index * -2.5), "target_status": "synthetic_available"}
                    for index, case_key in enumerate(mod.PM10_CASES, start=1)
                ],
            )

            summary = mod.build_package(
                feature_matrix_path=feature_path,
                anchor_admission_path=admission_path,
                hybrid_contract_path=root / "hybrid_1d_model_contract.csv",
                direct_dry_scorecard_path=root / "upcomer_hybrid_dry_scorecard.csv",
                residual_candidate_paths=[residual_path],
                output_dir=root / "out",
            )

            self.assertEqual(summary["residual_target_available_cases"], 4)
            with (root / "out/pm10_recirc_model_form_scorecard.csv").open(newline="", encoding="utf-8") as handle:
                scores = list(csv.DictReader(handle))
            self.assertEqual({row["score_use"] for row in scores}, {"residual_weighted_candidate_ranking_only"})
            self.assertTrue(all(float(row["residual_weighted_score"]) >= 0.0 for row in scores if row["residual_weighted_score"]))
            self.assertEqual({row["fit_allowed_now"] for row in scores}, {"no"})
            self.assertEqual({row["model_selection_allowed_now"] for row in scores}, {"no"})
            self.assertEqual({row["runtime_input_allowed_now"] for row in scores}, {"no"})

    def test_current_default_package_keeps_pm10_in_recirc_lane(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "out"
            summary = mod.build_package(output_dir=out)

            self.assertEqual(summary["case_count"], 4)
            self.assertEqual(summary["plane_feature_rows"], 12)
            self.assertEqual(summary["residual_target_available_cases"], 4)
            self.assertEqual(summary["ordinary_pipe_fit_allowed_rows"], 0)
            self.assertEqual(summary["fit_allowed_now"], 0)

            payload = json.loads((out / "summary.json").read_text(encoding="utf-8"))
            self.assertEqual(payload["recirculation_lane"], "recirculating_upcomer_effective")
            with (out / "pm10_recirc_feature_summary.csv").open(newline="", encoding="utf-8") as handle:
                features = list(csv.DictReader(handle))
            self.assertEqual({row["ordinary_pipe_fit_allowed"] for row in features}, {"no"})
            self.assertEqual({row["runtime_input_allowed_now"] for row in features}, {"no"})
            with (out / "pm10_recirc_model_form_scorecard.csv").open(newline="", encoding="utf-8") as handle:
                scores = list(csv.DictReader(handle))
            self.assertEqual({row["score_use"] for row in scores}, {"residual_weighted_candidate_ranking_only"})


if __name__ == "__main__":
    unittest.main()
