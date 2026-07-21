from __future__ import annotations

import csv
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.analyze import build_rc_external_temperature_publication_evidence as pub


class RcExternalTemperaturePublicationEvidenceTests(unittest.TestCase):
    def rows(self, path: Path) -> list[dict[str, str]]:
        with path.open(newline="", encoding="utf-8") as handle:
            return list(csv.DictReader(handle))

    def build_plan_only(self) -> Path:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        out = Path(tmp.name) / "pkg"
        args = pub.parse_args(["--output-dir", str(out), "--plan-only", "--strict"])
        meta = pub.build_package(args)
        self.assertEqual(4, meta["microcase_matrix_rows"])
        self.assertEqual(4, meta["microcase_run_rows"])
        return out

    def test_microcase_matrix_has_isolated_perturbations(self) -> None:
        out = self.build_plan_only()
        rows = self.rows(out / "microcase_matrix.csv")
        by_id = {row["variant_id"]: row for row in rows}

        self.assertEqual("none", by_id["baseline"]["changed_parameter"])
        self.assertEqual("emissivity", by_id["emissivity_low"]["changed_parameter"])
        self.assertEqual("emissivity", by_id["emissivity_zero"]["changed_parameter"])
        self.assertEqual("Tsur", by_id["tsur_high"]["changed_parameter"])
        self.assertEqual(by_id["baseline"]["Tsur_K"], by_id["emissivity_low"]["Tsur_K"])
        self.assertEqual(by_id["baseline"]["Tsur_K"], by_id["emissivity_zero"]["Tsur_K"])
        self.assertEqual(by_id["baseline"]["emissivity"], by_id["tsur_high"]["emissivity"])

    def test_plan_only_does_not_claim_microcase_confirmation(self) -> None:
        out = self.build_plan_only()
        run_rows = self.rows(out / "microcase_run_results.csv")
        decision = (out / "publication_evidence_decision.json").read_text(encoding="utf-8")

        self.assertEqual({"plan_only_not_run"}, {row["run_status"] for row in run_rows})
        self.assertIn('"microcase_confirmed": false', decision)

    def test_delta_detection_requires_nonzero_delta(self) -> None:
        run_rows = [
            {"variant_id": "baseline", "wallHeatFlux_integral_W": "10", "wallHeatFlux_mean_W_m2": "100"},
            {"variant_id": "emissivity_low", "wallHeatFlux_integral_W": "10.5", "wallHeatFlux_mean_W_m2": "101"},
            {"variant_id": "emissivity_zero", "wallHeatFlux_integral_W": "10.0", "wallHeatFlux_mean_W_m2": "100"},
            {"variant_id": "tsur_high", "wallHeatFlux_integral_W": "9.5", "wallHeatFlux_mean_W_m2": "99"},
        ]
        deltas = pub.build_delta_rows(run_rows, 1.0e-8)
        by_id = {row["comparison_id"]: row for row in deltas}

        self.assertTrue(by_id["baseline_vs_emissivity_low"]["effect_detected"])
        self.assertFalse(by_id["baseline_vs_emissivity_zero"]["effect_detected"])
        self.assertTrue(by_id["baseline_vs_tsur_high"]["effect_detected"])

    def test_wallheatflux_parser_area_weights_multi_patch_mean(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        case_dir = Path(tmp.name)
        post_dir = case_dir / "postProcessing/wallHeatFlux/0"
        post_dir.mkdir(parents=True)
        (post_dir / "wallHeatFlux.dat").write_text(
            "\n".join(
                [
                    "# Wall heat-flux",
                    "# Time patch min max Q q",
                    "0 glass -1 -1 -100 -10",
                    "0 floor 0 0 0 0",
                    "0 roof -1 -1 -400 -20",
                    "1 glass -1 -1 -20 -2",
                    "1 roof -1 -1 -90 -3",
                ]
            ),
            encoding="utf-8",
        )

        _, patches, integral, mean = pub.parse_wallheatflux(case_dir)

        self.assertEqual("glass+roof", patches)
        self.assertEqual(-110.0, integral)
        self.assertAlmostEqual(-110.0 / 40.0, mean)

    def test_source_confirmation_requires_custom_source_not_stock(self) -> None:
        source_rows = [
            {
                "kind": "stock_OF13_reference_not_custom_source",
                "exists": True,
                "relevant_excerpt": "updateCoeffs emissivity Tsur",
            },
            {
                "kind": "compiled_custom_library",
                "exists": True,
                "relevant_excerpt": "updateCoeffs emissivity Tsur",
            },
        ]
        self.assertFalse(pub.source_confirmed(source_rows))

        source_rows.append(
            {
                "kind": "candidate_custom_source",
                "exists": True,
                "relevant_excerpt": "updateCoeffs emissivity Tsur",
            }
        )
        self.assertTrue(pub.source_confirmed(source_rows))


if __name__ == "__main__":
    unittest.main()
