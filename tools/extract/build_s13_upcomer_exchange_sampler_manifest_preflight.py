#!/usr/bin/env python3
"""Build the S13 upcomer exchange sampler manifest preflight package.

This package only assembles a fail-closed manifest after geometry/surface input
disposition. It does not launch the sampler or mutate native outputs.
"""

from __future__ import annotations

import csv
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.common import csv_dump, ensure_dir, iso_timestamp, json_dump, relative_to_workspace


TASK_ID = "TODO-S13-UPCOMER-EXCHANGE-SAMPLER-MANIFEST-PREFLIGHT-2026-07-21"
OUT = ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_s13_upcomer_exchange_sampler_manifest_preflight"
)
GEOMETRY = ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_s13_upcomer_exchange_geometry_contract"
)
SURFACE = ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_s13_upcomer_exchange_surface_vtk_extraction"
)
SCAFFOLD = ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_upcomer_exchange_sampler_reusable_harvest_scaffold"
)

SOURCE_FILES = {
    "geometry_downstream_inputs": GEOMETRY / "downstream_surface_vtk_inputs.csv",
    "surface_manifest_fragment": SURFACE / "downstream_manifest_fragment.csv",
    "scaffold_manifest_template": SCAFFOLD / "case_vtk_input_manifest.template.csv",
    "scaffold_validator": SCAFFOLD / "scripts/validate_exchange_case_inputs.py",
}


def rel(path: Path) -> str:
    return relative_to_workspace(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def source_manifest() -> list[dict[str, Any]]:
    return [
        {
            "path": rel(path),
            "role": role,
            "exists": str(path.exists()).lower(),
            "native_solver_output": "false",
            "mutated": "false",
        }
        for role, path in SOURCE_FILES.items()
    ]


def manifest_rows(template_rows: list[dict[str, str]], surface_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    surface_by_case = {row["case_id"]: row for row in surface_rows}
    rows: list[dict[str, str]] = []
    for row in template_rows:
        case_id = row["case_id"]
        surface = surface_by_case.get(case_id, {})
        rows.append(
            {
                "case_id": case_id,
                "time_window_s": row["time_window_s"],
                "cell_vtk": surface.get("cell_vtk", row["cell_vtk"]),
                "interface_vtk": "MISSING_EXCHANGE_INTERFACE_VTK",
                "wall_vtk": "MISSING_WALL_VTK",
                "volume_csv": row["volume_csv"],
                "throughflow_nx": "",
                "throughflow_ny": "",
                "throughflow_nz": "",
                "interface_nx": "",
                "interface_ny": "",
                "interface_nz": "",
                "output_dir": rel(OUT / "sample_outputs" / case_id),
                "cp_J_kg_K": "",
            }
        )
    return rows


def missing_input_matrix(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    checks = [
        ("cell_vtk", "file"),
        ("interface_vtk", "file"),
        ("wall_vtk", "file"),
        ("volume_csv", "file"),
        ("throughflow_normal", "vector"),
        ("interface_normal", "vector"),
    ]
    out_rows: list[dict[str, str]] = []
    for row in rows:
        for input_name, kind in checks:
            if input_name == "throughflow_normal":
                present = all(row.get(f"throughflow_n{axis}", "") for axis in "xyz")
                value = ";".join(row.get(f"throughflow_n{axis}", "") for axis in "xyz")
            elif input_name == "interface_normal":
                present = all(row.get(f"interface_n{axis}", "") for axis in "xyz")
                value = ";".join(row.get(f"interface_n{axis}", "") for axis in "xyz")
            else:
                value = row.get(input_name, "")
                present = bool(value) and not value.startswith("MISSING_") and (ROOT / value).exists()
            out_rows.append(
                {
                    "case_id": row["case_id"],
                    "input_name": input_name,
                    "input_kind": kind,
                    "value": value,
                    "present": str(present).lower(),
                    "blocks_harvest": "false" if input_name in {"cell_vtk", "volume_csv"} and present else "true",
                    "blocking_reason": "" if present else f"missing_{input_name}",
                }
            )
    return out_rows


def run_validator(manifest: Path) -> dict[str, Any]:
    validator = SOURCE_FILES["scaffold_validator"]
    completed = subprocess.run(
        [sys.executable, str(validator), str(manifest)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    return {
        "validator_path": rel(validator),
        "manifest_path": rel(manifest),
        "return_code": completed.returncode,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
    }


def validation_report(result: dict[str, Any]) -> list[dict[str, str]]:
    status = "expected_fail_closed" if result["return_code"] != 0 else "unexpected_pass"
    return [
        {
            "validator": result["validator_path"],
            "manifest": result["manifest_path"],
            "return_code": str(result["return_code"]),
            "validation_status": status,
            "expected_to_pass_now": "false",
            "stdout": result["stdout"],
            "stderr": result["stderr"],
        }
    ]


def harvest_gate(rows: list[dict[str, str]], missing: list[dict[str, str]]) -> list[dict[str, str]]:
    rows_out: list[dict[str, str]] = []
    missing_by_case: dict[str, list[str]] = {}
    for item in missing:
        if item["present"] == "false":
            missing_by_case.setdefault(item["case_id"], []).append(item["input_name"])
    for row in rows:
        missing_items = sorted(set(missing_by_case.get(row["case_id"], [])))
        rows_out.append(
            {
                "case_id": row["case_id"],
                "time_window_s": row["time_window_s"],
                "manifest_ready": "false" if missing_items else "true",
                "harvest_allowed": "false",
                "sampler_launch_allowed": "false",
                "missing_inputs": ";".join(missing_items),
                "next_task": "release trusted interface/wall surfaces and numeric normal vectors before sampler launch",
            }
        )
    return rows_out


def write_readme(summary: dict[str, Any]) -> None:
    text = f"""---
provenance:
  generated_by: {Path(__file__).name}
  generated_at: {summary["generated_at"]}
tags:
  - s13
  - upcomer-exchange
  - sampler-manifest
  - fail-closed
related:
  - {rel(SOURCE_FILES["surface_manifest_fragment"])}
  - {rel(SOURCE_FILES["scaffold_manifest_template"])}
---

# S13 Upcomer Exchange Sampler Manifest Preflight

This package populates the reusable exchange sampler manifest as far as current
inputs allow. The Salt2, Salt3, and Salt4 cell VTK and volume CSV paths are
present, but interface VTKs, wall VTKs, and trusted normal vectors remain
missing.

Result: fail-closed. The scaffold validator was run as a preflight and is
expected to fail until the missing geometry/surface lanes are released. No
sampler, harvest, scheduler job, solver, postprocessing run, fit, score, or
admission step was launched.
"""
    (OUT / "README.md").write_text(text, encoding="utf-8")


def build() -> dict[str, Any]:
    ensure_dir(OUT)
    template = read_csv(SOURCE_FILES["scaffold_manifest_template"])
    surface = read_csv(SOURCE_FILES["surface_manifest_fragment"])
    rows = manifest_rows(template, surface)
    manifest_path = OUT / "case_vtk_input_manifest.preflight.csv"
    csv_dump(manifest_path, list(rows[0]), rows)

    missing = missing_input_matrix(rows)
    validator_result = run_validator(manifest_path)
    report = validation_report(validator_result)
    gate = harvest_gate(rows, missing)
    sources = source_manifest()

    csv_dump(OUT / "manifest_validation_report.csv", list(report[0]), report)
    csv_dump(OUT / "missing_input_matrix.csv", list(missing[0]), missing)
    csv_dump(OUT / "harvest_gate.csv", list(gate[0]), gate)
    csv_dump(OUT / "source_manifest.csv", list(sources[0]), sources)

    ready_rows = len([row for row in gate if row["manifest_ready"] == "true"])
    summary: dict[str, Any] = {
        "task_id": TASK_ID,
        "generated_at": iso_timestamp(),
        "package": rel(OUT),
        "manifest_rows": len(rows),
        "ready_manifest_rows": ready_rows,
        "fail_closed_rows": len(rows) - ready_rows,
        "validator_return_code": validator_result["return_code"],
        "scaffold_validator_expected_to_fail": True,
        "harvest_allowed": False,
        "sampler_launch_allowed": False,
        "scheduler_action": False,
        "native_output_mutation": False,
        "registry_mutation": False,
        "solver_or_postprocessing_or_sampler_launched": False,
        "fitting_or_model_selection": False,
        "closure_admission_change": False,
    }
    json_dump(OUT / "summary.json", summary)
    write_readme(summary)
    return summary


def main() -> int:
    build()
    print(f"wrote {rel(OUT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
