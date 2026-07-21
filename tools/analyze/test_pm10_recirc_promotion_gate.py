#!/usr/bin/env python3
"""Tests for PM10 recirculation promotion gate."""
from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from tools.analyze import build_pm10_pressure_component_isolation as component_mod
from tools.analyze import build_pm10_recirc_promotion_gate as mod
from tools.analyze import build_pm10_same_qoi_uq_preflight as uq_mod


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields: list[str] = []
    for row in rows:
        for field in row:
            if field not in fields:
                fields.append(field)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


class Pm10RecircPromotionGateTests(unittest.TestCase):
    def test_synthetic_pass_opens_conditional_review_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            recirc = root / "recirc.csv"
            component = root / "component.csv"
            uq = root / "uq.csv"
            write_csv(recirc, [{"case_key": case_key, "target_status": "residual_target_available", "source_paths": "fixture"} for case_key in mod.PM10_CASES])
            write_csv(component, [{"case_key": case_key, "component_isolation_status": "component_isolation_ready", "component_isolation_ready": "true"} for case_key in mod.PM10_CASES])
            write_csv(uq, [{"case_key": case_key, "same_qoi_uq_gate": "same_qoi_uq_pass"} for case_key in mod.PM10_CASES])

            summary = mod.build_package(recirc, component, uq, root / "out")

            self.assertEqual(summary["conditional_model_selection_review_ready_cases"], 4)
            with (root / "out/pm10_recirc_promotion_gate.csv").open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual({row["promotion_state"] for row in rows}, {"conditional_model_selection_review_ready"})
            self.assertEqual({row["ordinary_pipe_fit_allowed"] for row in rows}, {"no"})
            self.assertEqual({row["runtime_input_allowed_now"] for row in rows}, {"no"})

    def test_current_default_blocks_on_component_isolation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            component_mod.build_package(output_dir=root / "component")
            uq_mod.build_package(output_dir=root / "uq")
            summary = mod.build_package(
                component_gate_path=root / "component/pm10_component_isolation_gate.csv",
                uq_gate_path=root / "uq/pm10_uq_gate.csv",
                output_dir=root / "out",
            )

            self.assertEqual(summary["case_count"], 4)
            self.assertEqual(summary["conditional_model_selection_review_ready_cases"], 0)
            self.assertEqual(summary["blocked_missing_component_isolation_cases"], 4)
            self.assertEqual(summary["required_same_qoi_uq_cases"], 4)


if __name__ == "__main__":
    unittest.main()
