#!/usr/bin/env python3
"""Focused checks for the 1D conservative thermal ledger contract builder."""

from __future__ import annotations

import csv
import importlib.util
import json
import sys
import tempfile
from pathlib import Path


SCRIPT = Path(__file__).with_name("build_1d_conservative_thermal_ledger_residual_owner_contract.py")


def load_builder():
    spec = importlib.util.spec_from_file_location("ledger_builder", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load builder module")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main() -> None:
    builder = load_builder()
    with tempfile.TemporaryDirectory(prefix="ledger_contract_") as tmp:
        rel = Path(tmp).relative_to(builder.repo_root()) if Path(tmp).is_relative_to(builder.repo_root()) else Path(tmp)
        summary = builder.build(rel)
        out = builder.repo_root() / rel

        assert summary["decision"] == "contract_ready_no_candidate_release_no_runtime_leakage"
        assert summary["runtime_forbidden_inputs_all_blocked"] is True
        assert summary["source_property_release_rows"] == 0
        assert summary["candidate_admission_rows"] == 0
        assert summary["final_score_values"] == 0
        assert summary["scheduler_or_sampler_launched"] is False
        assert summary["native_output_mutated"] is False

        equation_rows = read_csv(out / "conservative_equation_ledger.csv")
        assert len(equation_rows) >= 10
        assert any(row["term_id"] == "internal_Nu" for row in equation_rows)
        assert any(row["term_id"] == "final_residual_owner" for row in equation_rows)
        assert all("global multiplier" not in row["runtime_inputs_allowed"] for row in equation_rows)

        forbidden_rows = read_csv(out / "runtime_forbidden_audit.csv")
        assert len(forbidden_rows) >= 6
        assert all(row["runtime_allowed"] == "false" for row in forbidden_rows)
        assert all(row["leakage_check_status"] == "pass" for row in forbidden_rows)
        forbidden_names = {row["forbidden_input"] for row in forbidden_rows}
        for required in ("realized CFD wallHeatFlux", "CFD mdot", "imposed CFD cooler duty", "validation temperatures"):
            assert required in forbidden_names

        allowed_rows = read_csv(out / "runtime_allowed_input_list.csv")
        assert all("CFD mdot" not in row["allowed_use"] for row in allowed_rows)
        assert all("wallHeatFlux" not in row["allowed_use"] for row in allowed_rows)

        source_rows = read_csv(out / "source_manifest.csv")
        assert all(row["exists"] == "true" for row in source_rows)
        assert all(row["mutation_status"] == "not_modified_by_this_task" for row in source_rows)

        summary_file = json.loads((out / "summary.json").read_text(encoding="utf-8"))
        assert summary_file["counts"]["forbidden_rows"] == len(forbidden_rows)

    print("1d conservative thermal ledger contract checks passed")


if __name__ == "__main__":
    main()
