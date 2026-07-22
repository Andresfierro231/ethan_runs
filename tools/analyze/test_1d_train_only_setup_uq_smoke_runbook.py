#!/usr/bin/env python3
"""Focused checks for the train-only setup-UQ smoke runbook builder."""

from __future__ import annotations

import csv
import importlib.util
import json
import sys
import tempfile
from pathlib import Path


SCRIPT = Path(__file__).with_name("build_1d_train_only_setup_uq_smoke_runbook.py")


def load_builder():
    spec = importlib.util.spec_from_file_location("setup_uq_smoke_runbook", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load builder")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main() -> None:
    builder = load_builder()
    with tempfile.TemporaryDirectory(prefix="setup_uq_smoke_") as tmp:
        tmp_path = Path(tmp)
        rel = tmp_path.relative_to(builder.repo_root()) if tmp_path.is_relative_to(builder.repo_root()) else tmp_path
        summary = builder.build(rel)
        out = builder.repo_root() / rel

        assert summary["decision"] == "train_only_setup_uq_smoke_runbook_ready_no_execution"
        assert summary["execution_launched"] is False
        assert summary["train_only"] is True
        assert summary["protected_scoring_rows"] == 0
        assert summary["source_property_release_rows"] == 0
        assert summary["coefficient_admission_rows"] == 0

        variations = read_csv(out / "setup_legal_variation_matrix.csv")
        assert len(variations) >= 8
        assert any(row["input_family"] == "heater_source_fraction" for row in variations)
        assert any(row["input_family"] == "pressure_loss_terms" for row in variations)

        qois = read_csv(out / "qoi_output_contract.csv")
        qoi_names = {row["qoi"] for row in qois}
        for required in ("mdot_model", "TP_projection_predictions", "TW_projection_predictions", "heat_path_terms", "segment_residual_R_s"):
            assert required in qoi_names

        guards = read_csv(out / "split_and_runtime_guardrails.csv")
        guard_names = {row["field_or_action"] for row in guards}
        for required in ("CFD_mdot", "realized_CFD_wallHeatFlux", "imposed_CFD_cooler_duty", "validation_temperatures"):
            assert required in guard_names
        assert all(row["fit_allowed"] in {"false", "false_from_this_row"} for row in guards)

        stops = read_csv(out / "stop_rules.csv")
        assert any("forbidden field" in row["condition"] for row in stops)
        manifest = read_csv(out / "source_manifest.csv")
        assert all(row["exists"] == "true" for row in manifest)

        summary_file = json.loads((out / "summary.json").read_text(encoding="utf-8"))
        assert summary_file["counts"]["variation_rows"] == len(variations)

    print("1d train-only setup-UQ smoke runbook checks passed")


if __name__ == "__main__":
    main()
