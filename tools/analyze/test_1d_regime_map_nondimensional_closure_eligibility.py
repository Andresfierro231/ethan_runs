#!/usr/bin/env python3
"""Focused checks for the 1D nondimensional regime map builder."""

from __future__ import annotations

import csv
import importlib.util
import json
import sys
import tempfile
from pathlib import Path


SCRIPT = Path(__file__).with_name("build_1d_regime_map_nondimensional_closure_eligibility.py")


def load_builder():
    spec = importlib.util.spec_from_file_location("regime_builder", SCRIPT)
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
    with tempfile.TemporaryDirectory(prefix="regime_map_") as tmp:
        tmp_path = Path(tmp)
        rel = tmp_path.relative_to(builder.repo_root()) if tmp_path.is_relative_to(builder.repo_root()) else tmp_path
        summary = builder.build(rel)
        out = builder.repo_root() / rel

        assert summary["decision"] == "regime_map_ready_fail_closed_no_closure_admission"
        assert summary["ordinary_single_stream_fit_rows"] == 0
        assert summary["internal_nu_fit_rows"] == 0
        assert summary["component_k_or_f6_fit_rows"] == 0
        assert summary["exchange_cell_admitted_rows"] == 0
        assert summary["source_property_release_rows"] == 0

        formulas = read_csv(out / "formula_validity_table.csv")
        formula_names = {row["quantity"] for row in formulas}
        for required in ("Reynolds number", "Prandtl number", "Grashof number", "Rayleigh number", "Richardson number", "Graetz number"):
            assert required in formula_names

        regimes = read_csv(out / "segment_case_regime_map.csv")
        assert len(regimes) >= 10
        assert all(row["scientific_interpretation"].startswith("fail closed") for row in regimes)
        assert any("blocked" in row["closure_eligibility"] for row in regimes)

        decisions = read_csv(out / "closure_eligibility_decisions.csv")
        assert all(row["admitted_rows"] == "0" for row in decisions)
        assert any(row["model_family"] == "throughflow_recirc_exchange_cell" for row in decisions)

        manifest = read_csv(out / "source_manifest.csv")
        assert all(row["exists"] == "true" for row in manifest)
        assert (out / "figures/svg/regime_eligibility_map.svg").exists()

        summary_file = json.loads((out / "summary.json").read_text(encoding="utf-8"))
        assert summary_file["counts"]["regime_rows"] == len(regimes)

    print("1d regime map nondimensional closure eligibility checks passed")


if __name__ == "__main__":
    main()
