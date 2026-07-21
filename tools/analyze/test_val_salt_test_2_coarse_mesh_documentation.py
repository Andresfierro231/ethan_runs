from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path

from tools.analyze.build_val_salt_test_2_coarse_mesh_documentation import build


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


class ValSaltTest2CoarseMeshDocumentationTests(unittest.TestCase):
    def test_builds_required_package_files(self) -> None:
        with tempfile.TemporaryDirectory(prefix="val-salt2-doc-") as tmp:
            out = Path(tmp)
            summary = build(out)

            self.assertEqual(summary["task"], "AGENT-354")
            self.assertEqual(summary["canonical_display_label"], "val_salt_test_2_coarse_mesh")
            self.assertFalse(summary["native_cfd_outputs_mutated"])
            self.assertFalse(summary["registry_mutated"])

            for name in [
                "README.md",
                "lineage_migration_plan.csv",
                "boundary_condition_summary.csv",
                "boundary_condition_patch_detail.csv",
                "material_property_evidence.csv",
                "salt2_jin_comparison.csv",
                "source_manifest.csv",
                "summary.json",
            ]:
                self.assertTrue((out / name).exists(), name)

            parsed = json.loads((out / "summary.json").read_text(encoding="utf-8"))
            self.assertEqual(parsed["legacy_source_id"], "val_salt_test_2_coarse_mesh_laminar")

    def test_lineage_preserves_historical_paths_while_using_display_alias(self) -> None:
        with tempfile.TemporaryDirectory(prefix="val-salt2-doc-") as tmp:
            out = Path(tmp)
            build(out)
            lineage = {row["lineage_item"]: row for row in rows(out / "lineage_migration_plan.csv")}

            self.assertIn("val_salt_test_2_coarse_mesh", lineage["canonical_display_label"]["current_or_legacy_label"])
            self.assertIn("Do not rename", lineage["canonical_display_label"]["migration_action"])
            self.assertIn(
                "val_salt_test_2_coarse_mesh_laminar",
                lineage["original_external_source"]["current_or_legacy_label"],
            )
            self.assertIn("2026-06-01_continuation_candidate", lineage["staged_continuation_runtime"]["path_or_value"])

    def test_boundary_summary_covers_heat_cooler_passive_radiation_and_closed_loop(self) -> None:
        with tempfile.TemporaryDirectory(prefix="val-salt2-doc-") as tmp:
            out = Path(tmp)
            build(out)
            summary_rows = rows(out / "boundary_condition_summary.csv")
            by_case_role = {(r["case_label"], r["field"], r["role"]): r for r in summary_rows}

            val_heater = by_case_role[("val_salt_test_2_coarse_mesh", "T", "heater")]
            self.assertEqual(val_heater["patch_count"], "3")
            self.assertEqual(val_heater["imposed_Q_W_sum"], "265.7")
            self.assertIn("0.95", val_heater["emissivity_values"])
            self.assertIn("radiation", val_heater["semantics"])

            val_cooler = by_case_role[("val_salt_test_2_coarse_mesh", "T", "cooler")]
            self.assertIn("-136.35074", val_cooler["imposed_Q_W_sum"])
            self.assertIn("fixed negative Q", val_cooler["semantics"])

            val_passive = by_case_role[("val_salt_test_2_coarse_mesh", "T", "passive_ambient_wall")]
            self.assertIn("rcExternalTemperature", val_passive["patch_types"])
            self.assertIn("299.19", val_passive["Tsur_K_values"])

            val_u = by_case_role[("val_salt_test_2_coarse_mesh", "U", "closed_loop_wall_default")]
            self.assertIn("No named inlet/outlet", val_u["semantics"])

            patch_rows = rows(out / "boundary_condition_patch_detail.csv")
            test_section = [
                r for r in patch_rows
                if r["case_label"] == "val_salt_test_2_coarse_mesh"
                and r["patch"] == "pipeleg_left_04_test_section"
            ]
            self.assertEqual(test_section[0]["Q_W"], "37.0")

    def test_material_properties_and_jin_comparison_are_explicit(self) -> None:
        with tempfile.TemporaryDirectory(prefix="val-salt2-doc-") as tmp:
            out = Path(tmp)
            build(out)
            material = {(r["case_label"], r["property_group"]): r for r in rows(out / "material_property_evidence.csv")}
            self.assertEqual(material[("val_salt_test_2_coarse_mesh", "fluid_label")]["value"], "hitec_salt")
            self.assertIn("1423.47", material[("val_salt_test_2_coarse_mesh", "CpCoeffs")]["value"])
            self.assertIn("2293.6", material[("val_salt_test_2_coarse_mesh", "rhoCoeffs")]["value"])
            self.assertEqual(material[("salt2_jin", "momentum_transport")]["value"], "laminar")

            comparison = {row["comparison_axis"]: row for row in rows(out / "salt2_jin_comparison.csv")}
            self.assertEqual(comparison["canonical_display_label"]["val_salt_test_2_coarse_mesh"], "val_salt_test_2_coarse_mesh")
            self.assertIn("Distinct lineages", comparison["lineage"]["interpretation"])
            self.assertIn("historical/diagnostic", comparison["possible_uses"]["val_salt_test_2_coarse_mesh"])
            self.assertIn("thermal", comparison["current_steady_status"]["interpretation"])


if __name__ == "__main__":
    unittest.main()
