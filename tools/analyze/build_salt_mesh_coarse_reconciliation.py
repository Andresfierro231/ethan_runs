#!/usr/bin/env python3
"""Reconcile Ethan external Salt coarse mesh sources against repo mainline cases.

This script is read-only over source case trees. It compares the external coarse
mesh rows from the AGENT-228 mesh quality gate with the July 8 scenario-contract
mainline continuations so downstream mesh-UQ work can decide whether the coarse
level is current evidence, superseded evidence, or blocked.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.common import WORKSPACE_ROOT, ensure_dir, iso_timestamp  # noqa: E402

DEFAULT_CATALOG = (
    WORKSPACE_ROOT
    / "work_products/2026-07/2026-07-09/2026-07-09_salt_mesh_refinement_quality_gate/mesh_case_catalog.csv"
)
DEFAULT_QUALITY = (
    WORKSPACE_ROOT
    / "work_products/2026-07/2026-07-09/2026-07-09_salt_mesh_refinement_quality_gate/mesh_quality_gate.csv"
)
DEFAULT_SCENARIO = (
    WORKSPACE_ROOT
    / "work_products/2026-07/2026-07-08/2026-07-08_cfd_scenario_contract/scenario_contract.csv"
)
DEFAULT_OUTPUT_DIR = (
    WORKSPACE_ROOT
    / "work_products/2026-07/2026-07-09/2026-07-09_salt_mesh_refinement_followon_readiness"
)

ENDPOINT_CASES = ("salt_test_2_jin", "salt_test_4_jin")

FIELDS = [
    "case_id",
    "mesh_level",
    "external_source_id",
    "external_source_path",
    "external_exists",
    "external_latest_solver_time_s",
    "external_latest_postprocessing_time_s",
    "external_gate_verdict",
    "external_quality_flags",
    "mainline_source_id",
    "mainline_case_root",
    "mainline_exists",
    "mainline_latest_processor_time_s",
    "mainline_fit_use_status",
    "mainline_run_class",
    "external_case_fingerprint",
    "mainline_case_fingerprint",
    "case_fingerprint_equal",
    "external_bc_fingerprint",
    "mainline_bc_fingerprint",
    "bc_fingerprint_equal",
    "time_relation",
    "reconciliation_verdict",
    "gci_coarse_use_status",
    "notes",
]

FINGERPRINT_FILES = [
    "case_config.yaml",
    "system/controlDict",
    "system/fvSchemes",
    "system/fvSolution",
    "system/functions",
    "constant/polyMesh/boundary",
    "0/T",
    "0/U",
    "0/p_rgh",
]
BC_FILES = ["0/T", "0/U", "0/p_rgh", "system/functions"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", default=str(DEFAULT_CATALOG))
    parser.add_argument("--quality", default=str(DEFAULT_QUALITY))
    parser.add_argument("--scenario-contract", default=str(DEFAULT_SCENARIO))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    return parser.parse_args()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    ensure_dir(path.parent)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def write_json(path: Path, payload: dict[str, Any]) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(WORKSPACE_ROOT))
    except ValueError:
        return str(path)


def number(value: Any) -> float | None:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    return out


def short_hash(path: Path, names: list[str]) -> str:
    if not path.is_dir():
        return "missing"
    digest = hashlib.sha256()
    seen = 0
    for name in names:
        candidate = path / name
        if not candidate.is_file():
            continue
        seen += 1
        digest.update(name.encode("utf-8"))
        digest.update(b"\0")
        digest.update(candidate.read_bytes())
        digest.update(b"\0")
    if not seen:
        return "no_fingerprint_files"
    return digest.hexdigest()[:16]


def mainline_case_id(case_id: str) -> str:
    # salt_test_2_jin -> salt_2
    parts = case_id.split("_")
    return f"salt_{parts[2]}"


def quality_by_key(rows: list[dict[str, str]]) -> dict[tuple[str, str], dict[str, str]]:
    return {(row["case_id"], row["mesh_level"]): row for row in rows}


def scenario_by_case(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    out: dict[str, dict[str, str]] = {}
    for row in rows:
        if row.get("run_class") == "mainline_jin_continuation" and row.get("fit_use_status") == "fit_admissible_current_mainline":
            out[row["case_id"]] = row
    return out


def time_relation(external_time: float | None, mainline_time: float | None) -> str:
    if external_time is None or mainline_time is None:
        return "unknown"
    if abs(external_time - mainline_time) <= max(1.0, 0.01 * max(abs(external_time), abs(mainline_time))):
        return "similar_latest_time"
    if mainline_time > external_time:
        return "mainline_extends_external"
    return "external_later_than_mainline"


def classify(row: dict[str, Any]) -> tuple[str, str, str]:
    if row["external_exists"] != "yes" or row["mainline_exists"] != "yes":
        return "blocked_missing_source", "blocked_missing_source", "one_or_both_source_roots_missing"
    if row["external_source_path"] == row["mainline_case_root"]:
        return "same_as_mainline", "coarse_admitted_if_gate_passes", "external path is the current mainline path"
    if row["time_relation"] == "mainline_extends_external":
        return (
            "superseded_by_mainline",
            "do_not_use_external_coarse_for_publication_gci",
            "mainline continuation extends the external coarse source; use mainline continuation as central coarse evidence",
        )
    if row["bc_fingerprint_equal"] == "yes":
        return (
            "compatible_but_not_identical",
            "coarse_candidate_pending_numeric_reconciliation",
            "boundary-condition fingerprints match but roots differ",
        )
    return (
        "external_only",
        "blocked_pending_manual_reconciliation",
        "external coarse source is not proven equivalent to current mainline",
    )


def build_reconciliation(
    catalog: list[dict[str, str]],
    quality: list[dict[str, str]],
    scenario: list[dict[str, str]],
) -> list[dict[str, Any]]:
    qmap = quality_by_key(quality)
    smap = scenario_by_case(scenario)
    rows: list[dict[str, Any]] = []
    for cat in catalog:
        if cat.get("case_id") not in ENDPOINT_CASES or cat.get("mesh_level") != "coarse" or cat.get("fluid_variant") != "jin":
            continue
        qrow = qmap.get((cat["case_id"], "coarse"), {})
        mainline = smap.get(mainline_case_id(cat["case_id"]), {})
        external_root = Path(cat["source_path"])
        mainline_root = WORKSPACE_ROOT / mainline.get("case_root", "")
        external_latest = number(cat.get("latest_solver_time_s"))
        mainline_latest = number(mainline.get("latest_processor_time_s"))
        row: dict[str, Any] = {
            "case_id": cat["case_id"],
            "mesh_level": "coarse",
            "external_source_id": cat["source_id"],
            "external_source_path": cat["source_path"],
            "external_exists": "yes" if external_root.is_dir() else "no",
            "external_latest_solver_time_s": cat.get("latest_solver_time_s", ""),
            "external_latest_postprocessing_time_s": cat.get("latest_postprocessing_time_s", ""),
            "external_gate_verdict": qrow.get("gate_verdict", ""),
            "external_quality_flags": qrow.get("quality_flags", ""),
            "mainline_source_id": mainline.get("source_id", ""),
            "mainline_case_root": mainline.get("case_root", ""),
            "mainline_exists": "yes" if mainline_root.is_dir() else "no",
            "mainline_latest_processor_time_s": mainline.get("latest_processor_time_s", ""),
            "mainline_fit_use_status": mainline.get("fit_use_status", ""),
            "mainline_run_class": mainline.get("run_class", ""),
            "external_case_fingerprint": short_hash(external_root, FINGERPRINT_FILES),
            "mainline_case_fingerprint": short_hash(mainline_root, FINGERPRINT_FILES),
            "external_bc_fingerprint": short_hash(external_root, BC_FILES),
            "mainline_bc_fingerprint": short_hash(mainline_root, BC_FILES),
            "time_relation": time_relation(external_latest, mainline_latest),
        }
        row["case_fingerprint_equal"] = (
            "yes" if row["external_case_fingerprint"] == row["mainline_case_fingerprint"] else "no"
        )
        row["bc_fingerprint_equal"] = "yes" if row["external_bc_fingerprint"] == row["mainline_bc_fingerprint"] else "no"
        verdict, use_status, notes = classify(row)
        row["reconciliation_verdict"] = verdict
        row["gci_coarse_use_status"] = use_status
        row["notes"] = notes
        rows.append(row)
    return rows


def write_readme(path: Path, rows: list[dict[str, Any]], summary: dict[str, Any]) -> None:
    lines = [
        "# Salt Mesh Coarse Reconciliation",
        "",
        f"Generated: `{summary['generated_at']}`",
        "",
        "This read-only package compares Ethan external coarse mesh endpoint cases",
        "against the repo's current mainline Jin continuations from the July 8",
        "scenario contract. It does not stage data, mutate solver outputs, or",
        "update the registry.",
        "",
        "## Observed Facts",
        "",
    ]
    for row in rows:
        lines.append(
            f"- `{row['case_id']}`: `{row['reconciliation_verdict']}`; "
            f"time relation `{row['time_relation']}`; coarse use `{row['gci_coarse_use_status']}`."
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "A `superseded_by_mainline` verdict means the external coarse root is useful",
            "for provenance and screening, but should not be treated as the current",
            "publication-grade coarse level without an explicit later decision to align",
            "the mainline continuation and mesh-family endpoint values.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run(catalog_path: Path, quality_path: Path, scenario_path: Path, output_dir: Path) -> dict[str, Any]:
    out = ensure_dir(output_dir)
    rows = build_reconciliation(read_csv(catalog_path), read_csv(quality_path), read_csv(scenario_path))
    write_csv(out / "coarse_reconciliation.csv", rows, FIELDS)
    counts: dict[str, int] = {}
    for row in rows:
        counts[row["reconciliation_verdict"]] = counts.get(row["reconciliation_verdict"], 0) + 1
    summary = {
        "generated_at": iso_timestamp(),
        "task_id": "AGENT-231",
        "output_dir": rel(out),
        "row_count": len(rows),
        "verdict_counts": counts,
        "source_tree_read_only": True,
        "generated_files": [rel(out / "coarse_reconciliation.csv"), rel(out / "coarse_reconciliation_README.md")],
    }
    write_json(out / "coarse_reconciliation_summary.json", summary)
    write_readme(out / "coarse_reconciliation_README.md", rows, summary)
    return summary


def main() -> int:
    args = parse_args()
    summary = run(Path(args.catalog), Path(args.quality), Path(args.scenario_contract), Path(args.output_dir))
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
