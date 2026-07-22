#!/usr/bin/env python3
"""Focused checks for the setup-only BC UQ propagation contract."""

from __future__ import annotations

import csv
import importlib.util
import json
import sys
import tempfile
from pathlib import Path


SCRIPT = Path(__file__).with_name("build_1d_setup_only_bc_uq_propagation.py")


def load_builder():
    spec = importlib.util.spec_from_file_location("setup_uq_builder", SCRIPT)
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
    with tempfile.TemporaryDirectory(prefix="setup_uq_") as tmp:
        tmp_path = Path(tmp)
        rel = tmp_path.relative_to(builder.repo_root()) if tmp_path.is_relative_to(builder.repo_root()) else tmp_path
        summary = builder.build(rel)
        out = builder.repo_root() / rel

        assert summary["decision"] == "setup_only_uq_contract_ready_no_compute_no_publication_interval"
        assert summary["screening_priors_not_publication_intervals"] is True
        assert summary["source_property_release_rows"] == 0
        assert summary["candidate_admission_rows"] == 0
        assert summary["protected_scoring_rows"] == 0
        assert summary["fit_or_model_selection_rows"] == 0
        assert summary["scheduler_or_sampler_launched"] is False

        source_rows = read_csv(out / "uncertainty_source_table.csv")
        assert len(source_rows) >= 8
        assert all(row["protected_row_tuning_allowed"] == "false" for row in source_rows)
        assert any(row["input_family"] == "sensor_projection" for row in source_rows)
        assert any(row["input_family"] == "pressure_loss_terms" for row in source_rows)

        protected = read_csv(out / "protected_row_guardrails.csv")
        protected_items = {row["protected_item"] for row in protected}
        for required in ("CFD_mdot", "realized_CFD_wallHeatFlux", "imposed_CFD_cooler_duty", "validation_temperatures"):
            assert required in protected_items
        assert all(row["fit_allowed"] in {"false", "false_from_this_row"} for row in protected)

        readiness = read_csv(out / "readiness_gate.csv")
        assert any(row["gate"] == "publication_interval" and row["status"] == "not_ready" for row in readiness)
        assert any(row["gate"] == "protected_scoring" and row["status"] == "blocked" for row in readiness)

        manifest = read_csv(out / "source_manifest.csv")
        assert all(row["exists"] == "true" for row in manifest)

        summary_file = json.loads((out / "summary.json").read_text(encoding="utf-8"))
        assert summary_file["counts"]["source_rows"] == len(source_rows)

    print("1d setup-only BC UQ propagation checks passed")


if __name__ == "__main__":
    main()
