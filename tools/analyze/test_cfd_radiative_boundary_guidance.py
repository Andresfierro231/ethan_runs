from __future__ import annotations

import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.analyze import build_cfd_radiative_boundary_guidance as guidance


class CfdRadiativeBoundaryGuidanceTests(unittest.TestCase):
    def test_run_summary_groups_only_rc_external_temperature(self) -> None:
        rows = [
            {
                "case_id": "salt_2",
                "source_id": "src2",
                "run_class": "mainline",
                "bc_type": "rcExternalTemperature",
                "role": "ambient_wall",
                "emissivity": "0.95",
                "Tsur_K": "299.19",
                "Ta_K": "299.19",
                "h_W_m2K": "4.0",
                "thickness_total_m": "0.041656001",
                "realized_wallHeatFlux_W": "-2.5",
            },
            {
                "case_id": "salt_2",
                "source_id": "src2",
                "run_class": "mainline",
                "bc_type": "externalTemperature",
                "role": "cooler",
                "emissivity": "",
                "Tsur_K": "",
                "Ta_K": "299.19",
                "h_W_m2K": "10.0",
                "thickness_total_m": "",
                "realized_wallHeatFlux_W": "-5.0",
            },
        ]

        out = guidance.build_run_rows(rows)

        self.assertEqual(1, len(out))
        self.assertEqual("salt_2", out[0]["case_id"])
        self.assertEqual(1, out[0]["rcExternalTemperature_patch_count"])
        self.assertEqual("0.95", out[0]["emissivity_values"])
        self.assertEqual("299.19", out[0]["Tsur_values_K"])
        self.assertIn("do not add a separate radiation term", out[0]["one_d_agent_instruction"])

    def test_full_package_writes_agent_instruction(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            meta = guidance.build_package(out)
            decision = json.loads((out / "radiation_guidance_decision.json").read_text(encoding="utf-8"))
            rows = list(csv.DictReader((out / "cfd_emissivity_by_run.csv").open(newline="", encoding="utf-8")))
            readme = (out / "README.md").read_text(encoding="utf-8")

        self.assertEqual("AGENT-287", meta["task"])
        self.assertEqual("present_in_rcExternalTemperature_inseparable_from_wallHeatFlux", decision["cfd_radiative_exchange_status"])
        self.assertEqual({"salt_2", "salt_3", "salt_4"}, {row["case_id"] for row in rows})
        self.assertTrue(all(row["emissivity_values"] == "0.95" for row in rows))
        self.assertIn("should not be described as no-radiation", readme)


if __name__ == "__main__":
    unittest.main()
