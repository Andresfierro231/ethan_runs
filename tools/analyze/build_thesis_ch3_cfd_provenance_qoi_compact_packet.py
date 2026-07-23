#!/usr/bin/env python3
"""Validate the Chapter 3 CFD provenance/QoI compact packet."""

from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_thesis_ch3_cfd_provenance_qoi_compact_packet"

EXPECTED_CSV_ROWS = {
    "case_provenance_table.csv": 11,
    "retained_window_table.csv": 5,
    "qoi_dictionary.csv": 12,
    "postprocessing_method_table.csv": 8,
    "claim_boundary_table.csv": 9,
    "figure_table_targets.csv": 7,
    "native_source_path_manifest.csv": 8,
    "no_mutation_guardrails.csv": 8,
}

EXPECTED_SUMMARY = {
    "decision": "chapter3_cfd_database_packet_ready_diagnostic_only_no_runtime_release",
    "source_count": 23,
    "parsed_source_count": 23,
    "tidy_rows": 1405596,
    "window_stat_rows": 16353,
    "runtime_forbidden_inputs_released": False,
    "native_solver_outputs_mutated": False,
    "registry_or_admission_mutated": False,
    "scheduler_action": False,
    "fluid_external_repository_mutated": False,
    "heat_residual_hidden_in_internal_nu": False,
}


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def build() -> dict[str, object]:
    """Return a validated summary for the already-published compact packet."""

    if not OUT.exists():
        raise FileNotFoundError(OUT)

    row_counts: dict[str, int] = {}
    for name, expected_rows in EXPECTED_CSV_ROWS.items():
        rows = _read_csv_rows(OUT / name)
        row_counts[name] = len(rows)
        if len(rows) != expected_rows:
            raise AssertionError(f"{name}: expected {expected_rows} rows, found {len(rows)}")

    summary = json.loads((OUT / "summary.json").read_text(encoding="utf-8"))
    for key, expected in EXPECTED_SUMMARY.items():
        actual = summary.get(key)
        if actual != expected:
            raise AssertionError(f"summary[{key!r}] expected {expected!r}, found {actual!r}")

    guardrails = {row["guardrail"]: row["status"] for row in _read_csv_rows(OUT / "no_mutation_guardrails.csv")}
    if any(value.lower() != "false" for value in guardrails.values()):
        raise AssertionError(f"guardrail failure: {guardrails}")

    result = dict(summary)
    result["validated_csv_row_counts"] = row_counts
    result["validated_package_path"] = str(OUT.relative_to(ROOT))
    return result


def main() -> int:
    print(json.dumps(build(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
