from __future__ import annotations

import csv
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from tools.analyze import build_pm10_upcomer_anchor_admission as mod


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "tools/analyze/build_pm10_upcomer_anchor_admission.py"
DEFAULT_OUT = ROOT / "work_products/2026-07/2026-07-20/2026-07-20_pm10_upcomer_anchor_admission"


FIELDS = [
    "case_key",
    "plane_location",
    "metric_status",
    "representative_time_s",
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
]


def write_case(parsed_dir: Path, case_key: str, rows: list[dict[str, str]]) -> None:
    parsed_dir.mkdir(parents=True, exist_ok=True)
    with (parsed_dir / f"matched_plane_metrics_{case_key}.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def base_rows(case_key: str, reverse_area: str, reverse_mass: str, secondary: str = "0.05", ri: str = "0.10") -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for plane, gz in [
        ("upcomer_inlet", "not_applicable_zero_entry_length"),
        ("upcomer_mid", "120.0"),
        ("upcomer_outlet", "80.0"),
    ]:
        rows.append(
            {
                "case_key": case_key,
                "plane_location": plane,
                "metric_status": "parsed",
                "representative_time_s": "12382",
                "reverse_area_fraction": reverse_area,
                "reverse_mass_fraction": reverse_mass,
                "secondary_velocity_fraction": secondary,
                "Ri": ri,
                "bulk_T_K": "590.0",
                "wall_T_K": "593.0",
                "wallHeatFlux_W_m2": "-100.0",
                "delta_T_wall_bulk_K": "3.0",
                "Re": "4000.0",
                "Pr": "9.0",
                "Gz": gz,
            }
        )
    return rows


class Pm10UpcomerAnchorAdmissionTests(unittest.TestCase):
    def test_current_default_build_handles_missing_extraction(self) -> None:
        subprocess.run(["python3.11", str(SCRIPT)], cwd=ROOT, check=True)
        with (DEFAULT_OUT / "pm10_upcomer_anchor_classification.csv").open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual({row["case_key"] for row in rows}, set(mod.PM10_CASES))
        self.assertEqual({row["parsed_plane_rows"] for row in rows}, {"3"})
        self.assertEqual({row["upcomer_admission_classification"] for row in rows}, {"recirculation_diagnostic"})
        self.assertEqual({row["recirculation_severity_class"] for row in rows}, {"strong_recirculation"})
        self.assertEqual({row["ordinary_pipe_fit_allowed"] for row in rows}, {"no"})
        self.assertEqual({row["recirculation_anchor_allowed"] for row in rows}, {"yes"})
        self.assertEqual({row["recirculation_calibration_allowed"] for row in rows}, {"conditional"})
        self.assertEqual({row["recirculation_model_selection_allowed"] for row in rows}, {"conditional"})
        self.assertEqual({row["hybrid_validation_allowed"] for row in rows}, {"yes"})
        self.assertTrue(all(row["fit_allowed_now"] == "no" for row in rows))
        self.assertTrue(all(row["model_selection_allowed_now"] == "no" for row in rows))

    def test_classifies_ordinary_onset_and_recirculation_without_fit_promotion(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            root = Path(raw_tmp)
            parsed = root / "parsed"
            out = root / "out"
            write_case(parsed, "salt2_lo10q", base_rows("salt2_lo10q", "0.005", "0.004"))
            write_case(parsed, "salt2_hi10q", base_rows("salt2_hi10q", "0.04", "0.03"))
            write_case(parsed, "salt4_lo10q", base_rows("salt4_lo10q", "0.20", "0.12"))
            summary = mod.build_package(parsed, out)
            self.assertEqual(summary["ordinary_anchor_candidates"], 1)
            self.assertEqual(summary["onset_transition_candidates"], 1)
            self.assertEqual(summary["recirculation_diagnostics"], 1)

            with (out / "pm10_upcomer_anchor_classification.csv").open(newline="", encoding="utf-8") as handle:
                rows = {row["case_key"]: row for row in csv.DictReader(handle)}
            self.assertEqual(rows["salt2_lo10q"]["upcomer_admission_classification"], "ordinary_anchor_candidate")
            self.assertEqual(rows["salt2_hi10q"]["upcomer_admission_classification"], "onset_transition_candidate")
            self.assertEqual(rows["salt4_lo10q"]["upcomer_admission_classification"], "recirculation_diagnostic")
            self.assertEqual(rows["salt4_hi10q"]["upcomer_admission_classification"], "blocked_missing_extraction")
            self.assertEqual(rows["salt2_lo10q"]["candidate_for_policy_update"], "yes")
            self.assertEqual(rows["salt2_lo10q"]["recirculation_anchor_allowed"], "no")
            self.assertEqual(rows["salt2_hi10q"]["recirculation_anchor_allowed"], "no")
            self.assertEqual(rows["salt4_lo10q"]["recirculation_anchor_allowed"], "yes")
            self.assertEqual(rows["salt4_lo10q"]["recirculation_calibration_allowed"], "conditional")
            self.assertEqual(rows["salt4_lo10q"]["hybrid_validation_allowed"], "yes")
            self.assertTrue(all(row["fit_allowed_now"] == "no" for row in rows.values()))

    def test_missing_same_window_fields_block_anchor_classification(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            root = Path(raw_tmp)
            parsed = root / "parsed"
            out = root / "out"
            rows = base_rows("salt2_lo10q", "0.005", "0.004")
            rows[0]["wallHeatFlux_W_m2"] = ""
            write_case(parsed, "salt2_lo10q", rows)
            mod.build_package(parsed, out)
            with (out / "pm10_upcomer_anchor_classification.csv").open(newline="", encoding="utf-8") as handle:
                table = {row["case_key"]: row for row in csv.DictReader(handle)}
            row = table["salt2_lo10q"]
            self.assertEqual(row["upcomer_admission_classification"], "blocked_missing_fields")
            self.assertIn("wallHeatFlux_W_m2", row["missing_required_fields"])
            self.assertEqual(row["candidate_for_policy_update"], "no")
            self.assertEqual(row["recirculation_anchor_allowed"], "no")
            self.assertEqual(row["hybrid_validation_allowed"], "no")

    def test_summary_keeps_fit_and_model_selection_closed(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            out = Path(raw_tmp) / "out"
            summary = mod.build_package(Path(raw_tmp) / "parsed", out)
            self.assertEqual(summary["fit_allowed_now"], 0)
            self.assertEqual(summary["model_selection_allowed_now"], 0)
            payload = json.loads((out / "summary.json").read_text(encoding="utf-8"))
            self.assertEqual(payload["runtime_input_allowed_now"], 0)
            self.assertEqual(payload["recirculation_anchor_allowed_rows"], 0)

    def test_recirc_outputs_expose_lane_specific_use(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            root = Path(raw_tmp)
            parsed = root / "parsed"
            out = root / "out"
            write_case(parsed, "salt2_lo10q", base_rows("salt2_lo10q", "0.20", "0.12"))
            mod.build_package(parsed, out)

            with (out / "pm10_recirculation_anchor_admission.csv").open(newline="", encoding="utf-8") as handle:
                rows = {row["case_key"]: row for row in csv.DictReader(handle)}
            self.assertEqual(rows["salt2_lo10q"]["recirculation_anchor_allowed"], "yes")
            self.assertEqual(rows["salt2_lo10q"]["recirculation_model_selection_allowed"], "conditional")
            self.assertEqual(rows["salt2_lo10q"]["ordinary_pipe_fit_allowed"], "no")
            self.assertIn("recirculation_aware_or_hybrid_models_only", rows["salt2_lo10q"]["use_condition"])

            with (out / "pm10_recirculation_feature_matrix.csv").open(newline="", encoding="utf-8") as handle:
                feature_rows = list(csv.DictReader(handle))
            self.assertEqual(len([row for row in feature_rows if row["case_key"] == "salt2_lo10q"]), 3)
            self.assertEqual({row["recirculation_anchor_allowed"] for row in feature_rows if row["case_key"] == "salt2_lo10q"}, {"yes"})

            with (out / "pm10_model_use_gate.csv").open(newline="", encoding="utf-8") as handle:
                gate = {row["case_key"]: row for row in csv.DictReader(handle)}
            self.assertEqual(gate["salt2_lo10q"]["fit_allowed_now"], "no")
            self.assertEqual(gate["salt2_lo10q"]["recirculation_calibration_allowed"], "conditional")


if __name__ == "__main__":
    unittest.main()
