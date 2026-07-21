#!/usr/bin/env python3
"""Build reusable, fail-closed harvest scaffolding for upcomer exchange sampling."""

from __future__ import annotations

import argparse
import csv
import json
import stat
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.common import csv_dump, ensure_dir, iso_timestamp, json_dump, relative_to_workspace

TASK_ID = "TODO-UPCOMER-EXCHANGE-SAMPLER-REUSABLE-HARVEST-SCAFFOLD-2026-07-21"
PACKAGE_DIR = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_sampler_reusable_harvest_scaffold"
INPUT_PACKAGE = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_input_generation"
SAMPLER_PACKAGE = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_sampler_design"
COMPUTE_GATE = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_sampler_compute_execution"
SURFACE_SOURCE_PACKAGE = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_surface_source_generation"
INPUT_LEDGER = INPUT_PACKAGE / "input_generation_ledger.csv"
INPUT_BLOCKERS = INPUT_PACKAGE / "surface_and_ledger_blockers.csv"
SAMPLER = ROOT / "tools/extract/sample_upcomer_exchange_cell.py"

CASE_VOLUME_FIELDS = [
    "case_id",
    "case_key",
    "time_window_s",
    "cell_volume_csv",
    "cell_volume_summary_json",
    "volume_status",
    "n_cells",
    "negative_volume_cells",
    "zero_or_negative_volume_cells",
    "normal_status",
    "sampler_ready_now",
    "release_condition",
]
CONTRACT_FIELDS = [
    "case_id",
    "time_window_s",
    "input_role",
    "required_fields",
    "path",
    "current_status",
    "blocking_for_harvest",
    "release_condition",
]
TEMPLATE_FIELDS = [
    "case_id",
    "time_window_s",
    "cell_vtk",
    "interface_vtk",
    "wall_vtk",
    "volume_csv",
    "throughflow_nx",
    "throughflow_ny",
    "throughflow_nz",
    "interface_nx",
    "interface_ny",
    "interface_nz",
    "output_dir",
    "cp_J_kg_K",
]
BLOCKER_FIELDS = [
    "case_id",
    "time_window_s",
    "blocked_input",
    "blocker",
    "next_action",
    "script_behavior",
    "fit_allowed_now",
    "score_allowed_now",
]
SCRIPT_FIELDS = ["script", "purpose", "side_effects", "scheduler_action", "syntax_checked"]
GUARD_FIELDS = ["guard_id", "status", "policy"]
MANIFEST_FIELDS = ["path", "role", "exists", "native_solver_output", "mutated"]


def rel(path: Path) -> str:
    return relative_to_workspace(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def volume_rows() -> list[dict[str, str]]:
    return [row for row in read_csv(INPUT_LEDGER) if row.get("input_name") == "cell_volume_csv"]


def summary_path_for(volume_csv: Path) -> Path:
    stem = volume_csv.name.replace("_cell_volumes.csv", "_cell_volumes_summary.json")
    return volume_csv.parent / stem


def int_summary_value(summary: dict[str, Any], key: str, default: int) -> int:
    value = summary.get(key, default)
    if value in ("", None):
        return default
    return int(value)


def case_volume_map_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in volume_rows():
        volume_csv = ROOT / row["path"]
        summary_json = summary_path_for(volume_csv)
        summary = load_json(summary_json)
        n_cells = int_summary_value(summary, "n_cells", 0)
        negative = int_summary_value(summary, "negative_volume_cells", 1)
        zero_or_negative = int_summary_value(summary, "zero_or_negative_volume_cells", 1)
        volume_ready = volume_csv.exists() and summary_json.exists() and n_cells > 0 and negative == 0 and zero_or_negative == 0
        rows.append(
            {
                "case_id": row["case_id"],
                "case_key": row["case_key"],
                "time_window_s": row["time_window_s"],
                "cell_volume_csv": rel(volume_csv),
                "cell_volume_summary_json": rel(summary_json),
                "volume_status": "ready" if volume_ready else "blocked_or_missing",
                "n_cells": n_cells,
                "negative_volume_cells": negative,
                "zero_or_negative_volume_cells": zero_or_negative,
                "normal_status": "blocked_until_throughflow_and_interface_normals_are_declared",
                "sampler_ready_now": "false",
                "release_condition": "provide same-window cell/interface/wall VTK paths and explicit normal vectors",
            }
        )
    return rows


def vtk_input_contract_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for case in case_volume_map_rows():
        base = {"case_id": case["case_id"], "time_window_s": case["time_window_s"]}
        rows.extend(
            [
                {
                    **base,
                    "input_role": "cell_vtk",
                    "required_fields": "U;T;rho;cellId_or_same_order_with_volume_csv;optional_mu;optional_recircMask",
                    "path": "",
                    "current_status": "blocked_missing_same_window_cell_vtk",
                    "blocking_for_harvest": "true",
                    "release_condition": "surface/source-generation or extraction row emits same-window exchange-cell VTK",
                },
                {
                    **base,
                    "input_role": "exchange_interface_vtk",
                    "required_fields": "U;rho;polygon_area;explicit_interface_normal_sign",
                    "path": "",
                    "current_status": "blocked_missing_named_exchange_interface_vtk",
                    "blocking_for_harvest": "true",
                    "release_condition": "named interface geometry and normal sign convention are published",
                },
                {
                    **base,
                    "input_role": "wall_vtk",
                    "required_fields": "T;polygon_area;optional_wallHeatFlux_for_diagnostic_energy_residual",
                    "path": "",
                    "current_status": "blocked_missing_wall_core_vtk",
                    "blocking_for_harvest": "true",
                    "release_condition": "wall/core surface definition and sample output are published",
                },
                {
                    **base,
                    "input_role": "source_sink_ledger",
                    "required_fields": "Q_source_W;Q_sink_W;cp_J_kg_K;sign_convention;source_paths",
                    "path": "",
                    "current_status": "blocked_missing_same_window_source_sink_ledger",
                    "blocking_for_harvest": "true",
                    "release_condition": "same-window source/sink extractor publishes ledger rows",
                },
            ]
        )
    return rows


def manifest_template_rows(output_dir: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for case in case_volume_map_rows():
        rows.append(
            {
                "case_id": case["case_id"],
                "time_window_s": case["time_window_s"],
                "cell_vtk": "MISSING_CELL_VTK",
                "interface_vtk": "MISSING_EXCHANGE_INTERFACE_VTK",
                "wall_vtk": "MISSING_WALL_VTK",
                "volume_csv": case["cell_volume_csv"],
                "throughflow_nx": "",
                "throughflow_ny": "",
                "throughflow_nz": "",
                "interface_nx": "",
                "interface_ny": "",
                "interface_nz": "",
                "output_dir": rel(output_dir / "sample_outputs" / case["case_id"]),
                "cp_J_kg_K": "",
            }
        )
    return rows


def blocker_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in read_csv(INPUT_BLOCKERS):
        rows.append(
            {
                "case_id": row["case_id"],
                "time_window_s": row["time_window_s"],
                "blocked_input": row["blocked_input"],
                "blocker": row["blocker"],
                "next_action": row["next_action"],
                "script_behavior": "validator_fails_closed_until_path_and_normal_contract_are_supplied",
                "fit_allowed_now": "false",
                "score_allowed_now": "false",
            }
        )
    return rows


def guardrail_rows() -> list[dict[str, str]]:
    return [
        {
            "guard_id": "harvest_execution",
            "status": "blocked_by_default",
            "policy": "generated scripts only run when an explicit populated manifest is passed by a later task",
        },
        {
            "guard_id": "scheduler",
            "status": "blocked",
            "policy": "this scaffold does not submit, cancel, requeue, or monitor scheduler jobs",
        },
        {
            "guard_id": "native_outputs",
            "status": "blocked",
            "policy": "scripts read supplied VTK/CSV files and write task-selected output directories only",
        },
        {
            "guard_id": "admission",
            "status": "blocked",
            "policy": "no fit, model selection, score release, exchange-cell admission, or residual absorption into internal Nu",
        },
    ]


def source_manifest(output_dir: Path) -> list[dict[str, Any]]:
    paths = [
        Path("tools/extract/build_upcomer_exchange_sampler_reusable_harvest_scaffold.py"),
        Path("tools/extract/test_build_upcomer_exchange_sampler_reusable_harvest_scaffold.py"),
        Path("tools/extract/sample_upcomer_exchange_cell.py"),
        INPUT_LEDGER,
        INPUT_BLOCKERS,
        SAMPLER_PACKAGE / "exchange_sampler_required_schema.csv",
        COMPUTE_GATE / "README.md",
        SURFACE_SOURCE_PACKAGE / "README.md",
        output_dir / "scripts/harvest_one_exchange_case.sh",
        output_dir / "scripts/harvest_exchange_case_matrix.sh",
        output_dir / "scripts/validate_exchange_case_inputs.py",
        output_dir / "scripts/check_exchange_outputs.py",
    ]
    rows: list[dict[str, Any]] = []
    for path in paths:
        full = path if path.is_absolute() else ROOT / path
        generated = str(full).startswith(str(output_dir)) or path.name.startswith(
            ("build_upcomer_exchange_sampler_reusable_harvest_scaffold", "test_build_upcomer_exchange_sampler_reusable_harvest_scaffold")
        )
        rows.append(
            {
                "path": rel(full),
                "role": "task_output" if generated else "read_only_context",
                "exists": str(full.exists()).lower(),
                "native_solver_output": "false",
                "mutated": str(generated).lower(),
            }
        )
    return rows


def write_executable(path: Path, text: str) -> None:
    ensure_dir(path.parent)
    path.write_text(text, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP)


def harvest_one_script() -> str:
    return f"""#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 9 ]; then
  echo "usage: $0 CASE_ID TIME_WINDOW_S CELL_VTK INTERFACE_VTK WALL_VTK_OR_NONE VOLUME_CSV OUTPUT_DIR THROUGHFLOW_NORMAL INTERFACE_NORMAL [CP_J_KG_K]" >&2
  exit 64
fi

ROOT="{ROOT}"
CASE_ID="$1"
TIME_WINDOW_S="$2"
CELL_VTK="$3"
INTERFACE_VTK="$4"
WALL_VTK="$5"
VOLUME_CSV="$6"
OUTPUT_DIR="$7"
THROUGHFLOW_NORMAL="$8"
INTERFACE_NORMAL="$9"
CP_J_KG_K="${{10:-}}"

for required in "$CELL_VTK" "$INTERFACE_VTK" "$VOLUME_CSV"; do
  if [ ! -f "$required" ]; then
    echo "missing required input: $required" >&2
    exit 66
  fi
done

if [ "$WALL_VTK" != "NONE" ] && [ "$WALL_VTK" != "" ] && [ ! -f "$WALL_VTK" ]; then
  echo "missing optional wall input requested as required by manifest: $WALL_VTK" >&2
  exit 66
fi

mkdir -p "$OUTPUT_DIR"
cmd=(python3.11 "$ROOT/tools/extract/sample_upcomer_exchange_cell.py"
  --output-dir "$OUTPUT_DIR"
  --emit-extraction-row
  --case-id "$CASE_ID"
  --time-window-s "$TIME_WINDOW_S"
  --cell-vtk "$CELL_VTK"
  --interface-vtk "$INTERFACE_VTK"
  --volume-csv "$VOLUME_CSV"
  --throughflow-normal "$THROUGHFLOW_NORMAL"
  --interface-normal "$INTERFACE_NORMAL")

if [ "$WALL_VTK" != "NONE" ] && [ "$WALL_VTK" != "" ]; then
  cmd+=(--wall-vtk "$WALL_VTK")
fi
if [ "$CP_J_KG_K" != "" ]; then
  cmd+=(--cp-j-kg-k "$CP_J_KG_K")
fi

"${{cmd[@]}}"
"""


def harvest_matrix_script() -> str:
    return f"""#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 1 ]; then
  echo "usage: $0 CASE_VTK_INPUT_MANIFEST.csv" >&2
  exit 64
fi

SCRIPT_DIR="$(cd "$(dirname "${{BASH_SOURCE[0]}}")" && pwd)"
MANIFEST="$1"
python3.11 "$SCRIPT_DIR/validate_exchange_case_inputs.py" "$MANIFEST"

tail -n +2 "$MANIFEST" | while IFS=, read -r case_id time_window_s cell_vtk interface_vtk wall_vtk volume_csv throughflow_nx throughflow_ny throughflow_nz interface_nx interface_ny interface_nz output_dir cp_J_kg_K; do
  [ -z "$case_id" ] && continue
  "$SCRIPT_DIR/harvest_one_exchange_case.sh" \\
    "$case_id" \\
    "$time_window_s" \\
    "$cell_vtk" \\
    "$interface_vtk" \\
    "$wall_vtk" \\
    "$volume_csv" \\
    "$output_dir" \\
    "$throughflow_nx,$throughflow_ny,$throughflow_nz" \\
    "$interface_nx,$interface_ny,$interface_nz" \\
    "$cp_J_kg_K"
done
"""


def validate_inputs_script() -> str:
    field_literal = repr(TEMPLATE_FIELDS)
    return f"""#!/usr/bin/env python3
from __future__ import annotations

import csv
import math
import sys
from pathlib import Path

FIELDS = {field_literal}


def parse_vector(row: dict[str, str], prefix: str) -> list[float]:
    values = []
    for axis in ("x", "y", "z"):
        key = f"{{prefix}}_n{{axis}}"
        try:
            values.append(float(row.get(key, "")))
        except ValueError as exc:
            raise ValueError(f"{{row.get('case_id', '<unknown>')}} missing numeric {{key}}") from exc
    norm = math.sqrt(sum(value * value for value in values))
    if norm <= 0.0:
        raise ValueError(f"{{row.get('case_id', '<unknown>')}} has zero {{prefix}} normal")
    return values


def require_file(row: dict[str, str], key: str) -> None:
    value = row.get(key, "")
    if key == "wall_vtk" and value in ("", "NONE"):
        return
    if not value or value.startswith("MISSING_") or not Path(value).is_file():
        raise FileNotFoundError(f"{{row.get('case_id', '<unknown>')}} missing {{key}}: {{value}}")


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: validate_exchange_case_inputs.py CASE_VTK_INPUT_MANIFEST.csv", file=sys.stderr)
        return 64
    manifest = Path(sys.argv[1])
    with manifest.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        missing_fields = [field for field in FIELDS if field not in (reader.fieldnames or [])]
        if missing_fields:
            print(f"missing manifest columns: {{';'.join(missing_fields)}}", file=sys.stderr)
            return 65
        rows = list(reader)
    if not rows:
        print("manifest has no case rows", file=sys.stderr)
        return 65
    errors = []
    for row in rows:
        try:
            for key in ("cell_vtk", "interface_vtk", "volume_csv"):
                require_file(row, key)
            require_file(row, "wall_vtk")
            parse_vector(row, "throughflow")
            parse_vector(row, "interface")
        except (FileNotFoundError, ValueError) as exc:
            errors.append(str(exc))
    if errors:
        print("\\n".join(errors), file=sys.stderr)
        return 66
    print(f"validated_exchange_input_rows={{len(rows)}}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
"""


def check_outputs_script() -> str:
    return """#!/usr/bin/env python3
from __future__ import annotations

import csv
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) < 3:
        print("usage: check_exchange_outputs.py CASE_ID OUTPUT_DIR [CASE_ID OUTPUT_DIR ...]", file=sys.stderr)
        return 64
    pairs = sys.argv[1:]
    if len(pairs) % 2:
        print("case/output arguments must be pairs", file=sys.stderr)
        return 64
    failures = []
    checked = 0
    for case_id, output_dir in zip(pairs[0::2], pairs[1::2]):
        rows_path = Path(output_dir) / "exchange_sampler_rows.csv"
        if not rows_path.is_file():
            failures.append(f"{case_id}: missing {rows_path}")
            continue
        with rows_path.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        if len(rows) != 1:
            failures.append(f"{case_id}: expected 1 sampler row, found {len(rows)}")
            continue
        if rows[0].get("case_id") != case_id:
            failures.append(f"{case_id}: row case_id mismatch {rows[0].get('case_id')}")
            continue
        checked += 1
    if failures:
        print("\\n".join(failures), file=sys.stderr)
        return 65
    print(f"checked_exchange_output_cases={checked}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
"""


def script_index_rows() -> list[dict[str, str]]:
    return [
        {
            "script": "scripts/harvest_one_exchange_case.sh",
            "purpose": "Run sample_upcomer_exchange_cell.py for one fully populated same-window case.",
            "side_effects": "writes only the caller-selected output directory",
            "scheduler_action": "false",
            "syntax_checked": "pending_until_validation",
        },
        {
            "script": "scripts/harvest_exchange_case_matrix.sh",
            "purpose": "Validate and run a manifest of fully populated same-window cases.",
            "side_effects": "writes only output directories listed in manifest",
            "scheduler_action": "false",
            "syntax_checked": "pending_until_validation",
        },
        {
            "script": "scripts/validate_exchange_case_inputs.py",
            "purpose": "Fail closed unless each row has files and explicit normal vectors.",
            "side_effects": "none",
            "scheduler_action": "false",
            "syntax_checked": "pending_until_validation",
        },
        {
            "script": "scripts/check_exchange_outputs.py",
            "purpose": "Check sampler row files after a harvest run.",
            "side_effects": "none",
            "scheduler_action": "false",
            "syntax_checked": "pending_until_validation",
        },
    ]


def readme(summary: dict[str, Any]) -> str:
    return f"""---
task: {TASK_ID}
date: 2026-07-21
role: Hydraulics / Thermal-modeling / cfd-pp / Implementer / Tester / Writer
type: work_product
status: complete
tags: [upcomer, recirculation, exchange-cell, reusable-scripts, no-scheduler]
related:
  - {rel(INPUT_PACKAGE)}
  - {rel(SAMPLER_PACKAGE)}
---
# Upcomer Exchange Sampler Reusable Harvest Scaffold

This package turns the dry exchange-cell sampler into reusable, fail-closed
harvest plumbing. It wires the ready Salt2/Salt3/Salt4 cell-volume CSVs into a
manifest template and provides scripts that future rows can use once the
same-window cell, interface, wall, and source inputs exist.

## Current State

- case volume rows: `{summary["case_volume_rows"]}`
- ready volume CSVs: `{summary["ready_volume_csvs"]}`
- VTK/source contract rows: `{summary["vtk_contract_rows"]}`
- blocker rows: `{summary["blocker_rows"]}`
- sampler harvest launched now: `false`
- scheduler action: `false`

The template intentionally contains `MISSING_*` placeholders and blank normal
vectors. `scripts/validate_exchange_case_inputs.py` rejects that template until
a later row supplies real same-window VTK paths and explicit normal vectors.

## Reusable Scripts

- `scripts/validate_exchange_case_inputs.py`: validates paths and normal-vector
  columns before any run.
- `scripts/harvest_one_exchange_case.sh`: invokes
  `tools/extract/sample_upcomer_exchange_cell.py` for one populated case.
- `scripts/harvest_exchange_case_matrix.sh`: validates and runs a populated
  case matrix.
- `scripts/check_exchange_outputs.py`: verifies one sampler row per output
  directory after harvest.

## Guardrails

No native CFD/OpenFOAM output, registry/admission state, scheduler state, Fluid
source, external repository, blocker register, or generated docs index was
mutated. No OpenFOAM postprocessing, sampler harvest, fitting, model selection,
exchange-cell admission, Phase 4B rescore, Phase 5/S6 trigger, or internal-Nu
residual absorption was performed.
"""


def build_package(output_dir: Path = PACKAGE_DIR) -> dict[str, Any]:
    ensure_dir(output_dir)
    ensure_dir(output_dir / "scripts")
    case_map = case_volume_map_rows()
    contract = vtk_input_contract_rows()
    template = manifest_template_rows(output_dir)
    blockers = blocker_rows()
    scripts = script_index_rows()
    guards = guardrail_rows()

    write_executable(output_dir / "scripts/harvest_one_exchange_case.sh", harvest_one_script())
    write_executable(output_dir / "scripts/harvest_exchange_case_matrix.sh", harvest_matrix_script())
    write_executable(output_dir / "scripts/validate_exchange_case_inputs.py", validate_inputs_script())
    write_executable(output_dir / "scripts/check_exchange_outputs.py", check_outputs_script())

    csv_dump(output_dir / "case_volume_input_map.csv", CASE_VOLUME_FIELDS, case_map)
    csv_dump(output_dir / "required_vtk_input_contract.csv", CONTRACT_FIELDS, contract)
    csv_dump(output_dir / "case_vtk_input_manifest.template.csv", TEMPLATE_FIELDS, template)
    csv_dump(output_dir / "geometry_source_blockers.csv", BLOCKER_FIELDS, blockers)
    csv_dump(output_dir / "reusable_script_index.csv", SCRIPT_FIELDS, scripts)
    csv_dump(output_dir / "no_mutation_guardrails.csv", GUARD_FIELDS, guards)

    summary = {
        "task": TASK_ID,
        "generated_at": iso_timestamp(),
        "case_volume_rows": len(case_map),
        "ready_volume_csvs": sum(1 for row in case_map if row["volume_status"] == "ready"),
        "vtk_contract_rows": len(contract),
        "manifest_template_rows": len(template),
        "blocker_rows": len(blockers),
        "script_rows": len(scripts),
        "guardrail_rows": len(guards),
        "sampler_harvest_launched": False,
        "scheduler_action": False,
        "solver_or_postprocessing_launched": False,
        "native_output_mutation": False,
        "registry_or_admission_mutation": False,
        "fitting_or_model_selection": False,
        "exchange_cell_admission_change": False,
        "blocker_register_change": False,
        "generated_index_refresh": False,
        "phase4b_rescore_run": False,
        "phase5_or_s6_trigger": False,
    }
    json_dump(output_dir / "summary.json", summary)
    (output_dir / "README.md").write_text(readme(summary), encoding="utf-8")
    csv_dump(output_dir / "source_manifest.csv", MANIFEST_FIELDS, source_manifest(output_dir))
    return {
        "summary": summary,
        "case_map": case_map,
        "contract": contract,
        "template": template,
        "blockers": blockers,
        "scripts": scripts,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default=str(PACKAGE_DIR))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = build_package(Path(args.output_dir))
    print(json.dumps(payload["summary"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
