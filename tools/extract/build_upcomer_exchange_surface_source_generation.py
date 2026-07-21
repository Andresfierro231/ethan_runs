#!/usr/bin/env python3
"""Build the upcomer exchange surface/source generation package.

This row is allowed to prepare scheduler-safe extraction scripts, but it must
fail closed unless the exchange interface and wall/core geometry are explicit.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import stat
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.common import csv_dump, ensure_dir, iso_timestamp, json_dump, relative_to_workspace

TASK_ID = "TODO-UPCOMER-EXCHANGE-SURFACE-SOURCE-GENERATION-2026-07-21"
PACKAGE_DIR = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_surface_source_generation"
INPUT_PACKAGE = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_input_generation"
SOURCE_AUDIT = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_heatloss_upcomer_source_field_audit"
SAMPLER_PACKAGE = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_sampler_design"

SURFACE_FIELDS = [
    "case_id",
    "case_key",
    "time_window_s",
    "input_lane",
    "target_path",
    "status",
    "basis",
    "release_condition",
    "launch_allowed_now",
    "native_solver_output_mutated",
    "fit_allowed_now",
    "score_allowed_now",
    "residual_policy",
]
Q_FIELDS = [
    "case_id",
    "case_key",
    "time_window_s",
    "patch",
    "q_w",
    "q_lane",
    "bc_type",
    "source_file",
    "status",
    "basis",
    "admission_use",
]
SUMMARY_FIELDS = [
    "case_id",
    "case_key",
    "time_window_s",
    "q_source_w",
    "q_sink_w",
    "q_net_w",
    "source_row_count",
    "sink_row_count",
    "status",
    "energy_residual_release_condition",
]
DECISION_FIELDS = [
    "decision_id",
    "submit_status",
    "scheduler_action",
    "openfoam_launch",
    "reason",
    "release_condition",
    "script",
]
GUARD_FIELDS = ["guard_id", "status", "policy"]
HANDOFF_FIELDS = ["sequence", "work_package", "objective", "entry_condition", "forbidden_action"]
MANIFEST_FIELDS = ["path", "role", "exists", "native_solver_output", "mutated"]


def rel(path: Path) -> str:
    return relative_to_workspace(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def sh_quote(text: str) -> str:
    return "'" + text.replace("'", "'\"'\"'") + "'"


def case_rows() -> list[dict[str, str]]:
    return read_csv(SOURCE_AUDIT / "case_window_source_audit.csv")


def strip_comments(text: str) -> str:
    return re.sub(r"//.*", "", text)


def patch_blocks(text: str) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        match = re.match(r'\s*"([^"]+)"\s*$', lines[i])
        if not match:
            i += 1
            continue
        patch = match.group(1)
        j = i + 1
        while j < len(lines) and "{" not in lines[j]:
            j += 1
        if j >= len(lines):
            i += 1
            continue
        depth = lines[j].count("{") - lines[j].count("}")
        body = [lines[j]]
        j += 1
        while j < len(lines) and depth > 0:
            body.append(lines[j])
            depth += lines[j].count("{") - lines[j].count("}")
            j += 1
        rows.append((patch, "\n".join(body)))
        i = j
    return rows


def parse_t_boundary_q(path: Path) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8", errors="replace")
    rows: list[dict[str, Any]] = []
    for patch, body in patch_blocks(text):
        clean = strip_comments(body)
        q_match = re.search(r"\bQ\s+constant\s+([-+0-9.eE]+)\s*;", clean)
        if not q_match:
            continue
        type_match = re.search(r"\btype\s+([A-Za-z0-9_]+)\s*;", clean)
        q_value = float(q_match.group(1))
        rows.append(
            {
                "patch": patch,
                "q_w": q_value,
                "q_lane": "Q_source_W" if q_value >= 0.0 else "Q_sink_W",
                "bc_type": type_match.group(1) if type_match else "",
                "basis": "constant_Q_in_0_T_boundary_condition",
            }
        )
    return rows


def source_sink_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for case in case_rows():
        t_path = ROOT / case["case_dir"] / "0/T"
        for item in parse_t_boundary_q(t_path):
            rows.append(
                {
                    "case_id": case["case_id"],
                    "case_key": case["case_key"],
                    "time_window_s": case["time_window_s"],
                    "patch": item["patch"],
                    "q_w": f"{item['q_w']:.12g}",
                    "q_lane": item["q_lane"],
                    "bc_type": item["bc_type"],
                    "source_file": rel(t_path),
                    "status": "present_static_boundary_Q_contract",
                    "basis": item["basis"],
                    "admission_use": "diagnostic_source_ledger_only_no_fit_no_exchange_cell_admission",
                }
            )
    return rows


def source_sink_summary_rows(q_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    for row in q_rows:
        grouped.setdefault((row["case_id"], row["case_key"], row["time_window_s"]), []).append(row)
    rows: list[dict[str, Any]] = []
    for (case_id, case_key, time_s), items in sorted(grouped.items()):
        sources = [float(row["q_w"]) for row in items if row["q_lane"] == "Q_source_W"]
        sinks = [abs(float(row["q_w"])) for row in items if row["q_lane"] == "Q_sink_W"]
        q_source = sum(sources)
        q_sink = sum(sinks)
        rows.append(
            {
                "case_id": case_id,
                "case_key": case_key,
                "time_window_s": time_s,
                "q_source_w": f"{q_source:.12g}",
                "q_sink_w": f"{q_sink:.12g}",
                "q_net_w": f"{q_source - q_sink:.12g}",
                "source_row_count": len(sources),
                "sink_row_count": len(sinks),
                "status": "static_bc_source_sink_ready_wall_loss_still_blocked",
                "energy_residual_release_condition": "requires Q_wall_W from task-owned wallHeatFlux integration plus exchange state",
            }
        )
    return rows


def surface_rows(output_dir: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    input_rows = [row for row in read_csv(INPUT_PACKAGE / "input_generation_ledger.csv") if row["input_name"] == "cell_volume_csv"]
    volume_by_case = {row["case_id"]: row for row in input_rows}
    for case in case_rows():
        case_id = case["case_id"]
        case_dir = ROOT / case["case_dir"]
        targets = {
            "cell_volume_csv": (
                volume_by_case[case_id]["path"],
                "ready_from_input_generation",
                "task-owned cell-volume CSV validated",
                "already ready",
                "false",
            ),
            "cell_vtk": (
                rel(output_dir / "surfaces" / f"{case_id}_cell_fields.vtk"),
                "blocked_requires_cell_region_and_cellId_vtk_policy",
                "native U/T/rho fields exist, but VTK region and cellId/order contract is not fixed",
                "choose whole-mesh cell VTK or approved upcomer cellSet and verify cellId aligns with volume CSV",
                "false",
            ),
            "exchange_interface_vtk": (
                rel(output_dir / "surfaces" / f"{case_id}_exchange_interface.vtk"),
                "blocked_requires_named_exchange_interface_geometry",
                "no source names conservative main/recirculation interface point-normal/area/sign basis",
                "approve exchange-interface point, normal, area basis, and sign convention",
                "false",
            ),
            "wall_vtk": (
                rel(output_dir / "surfaces" / f"{case_id}_exchange_wall_core.vtk"),
                "blocked_requires_wall_core_band_geometry",
                "wall diagnostics exist, but exchange-wall/core band is not confirmed",
                "approve wall/core surface or band tied to recirculation cell region",
                "false",
            ),
            "source_sink_bc_ledger": (
                rel(output_dir / "source_sink_static_ledger.csv"),
                "ready_static_boundary_Q_contract_wall_loss_blocked",
                "0/T constant Q entries parsed into source/sink lanes",
                "Q_wall_W still requires task-owned wallHeatFlux integration before energy residual",
                "false",
            ),
        }
        for lane, (target, status, basis, release, launch) in targets.items():
            rows.append(
                {
                    "case_id": case_id,
                    "case_key": case["case_key"],
                    "time_window_s": case["time_window_s"],
                    "input_lane": lane,
                    "target_path": target,
                    "status": status,
                    "basis": basis,
                    "release_condition": release,
                    "launch_allowed_now": launch,
                    "native_solver_output_mutated": "false",
                    "fit_allowed_now": "false",
                    "score_allowed_now": "false",
                    "residual_policy": "do_not_hide_heat_residual_in_internal_Nu",
                }
            )
    return rows


def decision_rows(output_dir: Path) -> list[dict[str, Any]]:
    return [
        {
            "decision_id": "surface_source_generation_submit_gate",
            "submit_status": "not_submitted_fail_closed",
            "scheduler_action": "false",
            "openfoam_launch": "false",
            "reason": "cell_vtk, exchange_interface_vtk, and wall_vtk geometry contracts remain blocked",
            "release_condition": "approve exact cell-region/cellId, exchange-interface, and wall/core geometry before sbatch",
            "script": rel(output_dir / "scripts/run_surface_source_generation.sh"),
        }
    ]


def guard_rows() -> list[dict[str, str]]:
    return [
        {"guard_id": "native_outputs", "status": "pass_no_mutation", "policy": "write only under task work-product package"},
        {"guard_id": "scheduler", "status": "not_submitted", "policy": "generated scripts fail closed until geometry release conditions pass"},
        {"guard_id": "openfoam", "status": "blocked", "policy": "no OpenFOAM launch without explicit surface geometry"},
        {"guard_id": "admission", "status": "blocked", "policy": "no fit, score, model selection, exchange-cell admission, Phase 4B/5/S6 trigger"},
        {"guard_id": "residual_lane", "status": "pass", "policy": "energy residual and wall/source/sink terms remain explicit lanes, not internal Nu"},
    ]


def handoff_rows() -> list[dict[str, Any]]:
    return [
        {
            "sequence": 1,
            "work_package": "geometry_release",
            "objective": "approve cell-region/cellId basis, exchange-interface plane, and wall/core band",
            "entry_condition": "surface_extraction_contract.csv blocked rows resolved",
            "forbidden_action": "do not substitute representative upcomer outlet proxy for exchange interface",
        },
        {
            "sequence": 2,
            "work_package": "scheduler_surface_generation",
            "objective": "run task-owned staged OpenFOAM sampling after geometry release",
            "entry_condition": "run script preflight exits 0 under a new scheduler-authorized row",
            "forbidden_action": "do not write VTK or postProcessing outputs into native case directories",
        },
        {
            "sequence": 3,
            "work_package": "diagnostic_sampler_execution",
            "objective": "run sample_upcomer_exchange_cell.py with ready volume/source/surface lanes",
            "entry_condition": "cell/interface/wall VTK and source/sink/Q_wall ledgers exist",
            "forbidden_action": "do not fit, score, or admit exchange-cell coefficients",
        },
    ]


def manifest_rows(output_dir: Path) -> list[dict[str, Any]]:
    paths = [
        Path("tools/extract/build_upcomer_exchange_surface_source_generation.py"),
        Path("tools/extract/test_build_upcomer_exchange_surface_source_generation.py"),
        INPUT_PACKAGE,
        SOURCE_AUDIT,
        SAMPLER_PACKAGE,
        output_dir,
    ]
    paths.extend(ROOT / row["case_dir"] / "0/T" for row in case_rows())
    rows: list[dict[str, Any]] = []
    for path in paths:
        full = path if path.is_absolute() else ROOT / path
        task_output = full == output_dir or str(path).startswith("tools/extract/build_upcomer_exchange_surface_source_generation") or str(path).startswith("tools/extract/test_build_upcomer_exchange_surface_source_generation")
        native = str(path).startswith("jadyn_runs/")
        rows.append(
            {
                "path": rel(full),
                "role": "task_output" if task_output else "read_only_context",
                "exists": str(full.exists()).lower(),
                "native_solver_output": str(native).lower(),
                "mutated": str(task_output and full != output_dir).lower(),
            }
        )
    return rows


def write_scripts(output_dir: Path) -> None:
    scripts = ensure_dir(output_dir / "scripts")
    runner = scripts / "run_surface_source_generation.sh"
    cases = "\n".join("|".join([row["case_id"], row["case_key"], row["time_window_s"], str(ROOT / row["case_dir"])]) for row in case_rows())
    runner.write_text(
        "\n".join(
            [
                "#!/usr/bin/env bash",
                "set -euo pipefail",
                f"ROOT={sh_quote(str(ROOT))}",
                f"OUT={sh_quote(str(output_dir))}",
                'mkdir -p "$OUT/logs" "$OUT/surfaces" "$OUT/staged_cases"',
                'cat > "$OUT/queued_surface_cases.txt" <<\'CASES\'',
                cases,
                "CASES",
                'echo "blocked: exchange-interface and wall/core geometry are not released" >&2',
                'echo "see $OUT/surface_extraction_contract.csv" >&2',
                "exit 2",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    runner.chmod(runner.stat().st_mode | stat.S_IXUSR)
    sbatch = scripts / "submit_surface_source_generation.sbatch"
    sbatch.write_text(
        "\n".join(
            [
                "#!/usr/bin/env bash",
                "#SBATCH -J upx_surface_source",
                "#SBATCH -N 1",
                "#SBATCH -n 1",
                "#SBATCH -t 02:00:00",
                "#SBATCH -p NuclearEnergy",
                "#SBATCH -A ASC23046",
                f"#SBATCH -o {output_dir}/logs/slurm-%j.out",
                f"#SBATCH -e {output_dir}/logs/slurm-%j.err",
                "",
                "set -euo pipefail",
                f"{runner}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    sbatch.chmod(sbatch.stat().st_mode | stat.S_IXUSR)


def readme(summary: dict[str, Any]) -> str:
    return f"""---
task: {TASK_ID}
date: 2026-07-21
role: Hydraulics / Thermal-modeling / cfd-pp / Implementer / Tester / Writer
type: work_product
status: complete
tags: [upcomer, exchange-cell, surface-generation, source-ledger, no-solver]
related:
  - {rel(INPUT_PACKAGE)}
  - {rel(SOURCE_AUDIT)}
  - {rel(SAMPLER_PACKAGE)}
---
# Upcomer Exchange Surface/Source Generation

This package advances the post-volume input lanes for the upcomer exchange
sampler. It parses the static `0/T` boundary-condition `Q` terms into explicit
source/sink lanes and emits a fail-closed surface extraction contract for the
cell, exchange-interface, and wall/core VTKs.

## Decision

- case windows: `{summary["case_rows"]}`
- surface/input contract rows: `{summary["surface_contract_rows"]}`
- static source/sink rows: `{summary["source_sink_rows"]}`
- source/sink summary rows: `{summary["source_sink_summary_rows"]}`
- ready static source/sink summaries: `{summary["ready_source_sink_summary_rows"]}/3`
- scheduler action: `false`
- OpenFOAM launch: `false`
- fit/score/admission allowed now: `false`

No surface sampling was launched because the exchange interface and wall/core
band are not defined by an approved source. The generated sbatch wrapper exits
before OpenFOAM work until a later row supplies those geometry contracts.

## Outputs

- `surface_extraction_contract.csv`: per-case ready/blocked input lanes.
- `source_sink_static_ledger.csv`: parsed constant `Q` source/sink entries from
  `0/T`.
- `source_sink_summary.csv`: per-case `Q_source_W`, `Q_sink_W`, and net static
  boundary source/sink accounting.
- `submission_decision.csv`: fail-closed scheduler decision.
- `scripts/`: preflight-only runner and sbatch wrapper.
- `no_mutation_guardrails.csv`, `next_agent_handoff.csv`, `source_manifest.csv`.

## Guardrails

No native CFD/OpenFOAM output, registry/admission state, Fluid source, external
repository, blocker register, generated docs index, fit, score, model selection,
exchange-cell admission, Phase 4B rescore, Phase 5/S6 trigger, or internal-Nu
residual absorption is changed by this package.
"""


def build_package(output_dir: Path = PACKAGE_DIR) -> dict[str, Any]:
    ensure_dir(output_dir)
    ensure_dir(output_dir / "logs")
    ensure_dir(output_dir / "surfaces")
    write_scripts(output_dir)
    q_rows = source_sink_rows()
    summary_rows = source_sink_summary_rows(q_rows)
    surfaces = surface_rows(output_dir)
    decisions = decision_rows(output_dir)
    guards = guard_rows()
    handoff = handoff_rows()
    manifest = manifest_rows(output_dir)
    csv_dump(output_dir / "surface_extraction_contract.csv", SURFACE_FIELDS, surfaces)
    csv_dump(output_dir / "source_sink_static_ledger.csv", Q_FIELDS, q_rows)
    csv_dump(output_dir / "source_sink_summary.csv", SUMMARY_FIELDS, summary_rows)
    csv_dump(output_dir / "submission_decision.csv", DECISION_FIELDS, decisions)
    csv_dump(output_dir / "no_mutation_guardrails.csv", GUARD_FIELDS, guards)
    csv_dump(output_dir / "next_agent_handoff.csv", HANDOFF_FIELDS, handoff)
    csv_dump(output_dir / "source_manifest.csv", MANIFEST_FIELDS, manifest)
    summary = {
        "task": TASK_ID,
        "generated_at": iso_timestamp(),
        "case_rows": len(case_rows()),
        "surface_contract_rows": len(surfaces),
        "source_sink_rows": len(q_rows),
        "source_sink_summary_rows": len(summary_rows),
        "ready_source_sink_summary_rows": sum(1 for row in summary_rows if row["status"].startswith("static_bc_source_sink_ready")),
        "blocked_surface_rows": sum(1 for row in surfaces if row["status"].startswith("blocked")),
        "scheduler_action": False,
        "openfoam_launch": False,
        "native_output_mutation": False,
        "registry_or_admission_mutation": False,
        "fluid_edit": False,
        "external_repo_edit": False,
        "fitting_or_model_selection": False,
        "closure_admission_change": False,
        "blocker_register_change": False,
        "generated_index_refresh": False,
        "phase4b_rescore_run": False,
        "phase5_or_s6_trigger": False,
        "residual_absorbed_into_internal_Nu": False,
    }
    json_dump(output_dir / "summary.json", summary)
    (output_dir / "README.md").write_text(readme(summary), encoding="utf-8")
    return {"summary": summary, "surfaces": surfaces, "source_sink_rows": q_rows}


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
