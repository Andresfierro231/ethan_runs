#!/usr/bin/env python3
"""Build a guarded isolated relaunch package for pressure/upcomer extraction."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DATE = "2026-07-20"
TASK = "TODO-PRESSURE-UPCOMER-ISOLATED-RELAUNCH-SUBMISSION-PACKAGE"
OUT = ROOT / "work_products/2026-07/2026-07-20/2026-07-20_pressure_upcomer_isolated_relaunch_submission_package"
REPAIR = ROOT / "work_products/2026-07/2026-07-20/2026-07-20_pressure_upcomer_3305547_failure_repair"
RELAUNCH = ROOT / "work_products/2026-07/2026-07-20/2026-07-20_pressure_upcomer_matched_plane_relaunch_package"
RUNNER = RELAUNCH / "scripts/run_upcomer_matched_plane_compute.sh"
OF_ENV = ROOT / "tools/ofenv/of13_env.sh"
MESH_ROOT = ROOT / "work_products/2026-07/2026-07-01/2026-07-01_claude_mesh_centerlines"
STATUS = ROOT / ".agent/status/2026-07-20_TODO-PRESSURE-UPCOMER-ISOLATED-RELAUNCH-SUBMISSION-PACKAGE.md"
JOURNAL = ROOT / ".agent/journal/2026-07-20/pressure-upcomer-isolated-relaunch-submission-package.md"
IMPORT = ROOT / "imports/2026-07-20_pressure_upcomer_isolated_relaunch_submission_package.json"


EXPECTED_RELAUNCH_CASES = {
    "salt2_hi10q",
    "salt4_lo10q",
    "salt4_hi10q",
    "salt2_jin_nominal_continuation",
    "salt3_jin_nominal_continuation",
    "salt4_jin_nominal_continuation",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = []
        for row in rows:
            for field in row:
                if field not in fieldnames:
                    fieldnames.append(field)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def require_sources() -> None:
    required = [REPAIR / "remaining_case_relaunch_queue.csv", RELAUNCH / "candidate_readiness_matrix.csv", RUNNER, OF_ENV]
    missing = [rel(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing pressure/upcomer isolated relaunch sources: " + "; ".join(missing))


def geometry_source_id(source_id: str) -> str:
    if source_id.startswith("salt2_jin_"):
        return "viscosity_screening_salt_test_2_jin_coarse_mesh"
    if source_id.startswith("salt4_jin_"):
        return "viscosity_screening_salt_test_4_jin_coarse_mesh"
    return source_id


def abs_path(raw: str) -> Path:
    path = Path(raw)
    return path if path.is_absolute() else ROOT / path


def candidate_by_case() -> dict[str, dict[str, str]]:
    return {row["case_key"]: row for row in read_csv(RELAUNCH / "candidate_readiness_matrix.csv")}


def relaunch_needed_rows() -> list[dict[str, str]]:
    rows = [row for row in read_csv(REPAIR / "remaining_case_relaunch_queue.csv") if row["relaunch_needed"] == "true"]
    return sorted(rows, key=lambda row: row["case_key"])


def build_isolated_relaunch_case_matrix() -> list[dict[str, Any]]:
    candidates = candidate_by_case()
    rows = []
    for index, row in enumerate(relaunch_needed_rows()):
        case_key = row["case_key"]
        source = candidates.get(case_key, {})
        source_id = row["source_id"] or source.get("source_id", "")
        time_s = row["representative_time_s"] or source.get("representative_time_s", "")
        rows.append(
            {
                "array_index": index,
                "case_key": case_key,
                "source_id": source_id,
                "representative_time_s": time_s,
                "relaunch_reason": row["relaunch_reason"],
                "source_case_dir": source.get("source_case_dir", ""),
                "existing_recon_dir": source.get("existing_recon_dir", ""),
                "runner_command": f"bash {rel(RUNNER)} one {case_key}",
                "fit_release_after_relaunch": "false",
                "source_path": rel(REPAIR / "remaining_case_relaunch_queue.csv"),
            }
        )
    return rows


def source_or_recon_available(row: dict[str, Any]) -> bool:
    time_s = str(row["representative_time_s"])
    if row["existing_recon_dir"]:
        recon = abs_path(str(row["existing_recon_dir"]))
        return (recon / time_s).exists()
    if row["source_case_dir"]:
        source = abs_path(str(row["source_case_dir"]))
        return (source / "processors64" / time_s).exists() or (source / time_s).exists()
    return False


def build_preflight_gate(matrix: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for row in matrix:
        mesh_path = MESH_ROOT / geometry_source_id(str(row["source_id"])) / "mesh_stations.json"
        checks = {
            "runner_exists": RUNNER.exists(),
            "of_env_exists": OF_ENV.exists(),
            "time_present": bool(row["representative_time_s"]),
            "source_or_recon_time_available": source_or_recon_available(row),
            "mesh_stations_exists": mesh_path.exists(),
        }
        failed = [name for name, passed in checks.items() if not passed]
        rows.append(
            {
                "case_key": row["case_key"],
                "preflight_status": "pass" if not failed else "blocked",
                "failed_checks": ";".join(failed),
                "runner_exists": str(checks["runner_exists"]).lower(),
                "of_env_exists": str(checks["of_env_exists"]).lower(),
                "time_present": str(checks["time_present"]).lower(),
                "source_or_recon_time_available": str(checks["source_or_recon_time_available"]).lower(),
                "mesh_stations_path": rel(mesh_path),
                "mesh_stations_exists": str(checks["mesh_stations_exists"]).lower(),
            }
        )
    return rows


def write_sbatch(matrix: list[dict[str, Any]]) -> Path:
    script = OUT / "scripts/submit_pressure_upcomer_isolated_relaunch.sbatch"
    case_keys = " ".join(row["case_key"] for row in matrix)
    script.parent.mkdir(parents=True, exist_ok=True)
    script.write_text(
        "\n".join(
            [
                "#!/usr/bin/env bash",
                "#SBATCH -J upc_iso",
                "#SBATCH -N 1",
                "#SBATCH -n 1",
                "#SBATCH -t 02:00:00",
                "#SBATCH -p development",
                "#SBATCH -A ASC23046",
                f"#SBATCH -a 0-{max(len(matrix) - 1, 0)}",
                f"#SBATCH -o {rel(OUT)}/logs/upc_iso-%A_%a.out",
                f"#SBATCH -e {rel(OUT)}/logs/upc_iso-%A_%a.err",
                "",
                "set -euo pipefail",
                f"cd {ROOT}",
                f"case_keys=({case_keys})",
                f"bash {rel(RUNNER)} one \"${{case_keys[$SLURM_ARRAY_TASK_ID]}}\"",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return script


def build_submit_plan(matrix: list[dict[str, Any]], preflight: list[dict[str, Any]], script: Path) -> list[dict[str, Any]]:
    all_pass = bool(matrix) and all(row["preflight_status"] == "pass" for row in preflight)
    return [
        {
            "submit_group": "pressure_upcomer_isolated_relaunch",
            "case_count": len(matrix),
            "sbatch_path": rel(script),
            "preflight_all_pass": str(all_pass).lower(),
            "submit_allowed": str(all_pass).lower(),
            "submit_status": "not_submitted_by_builder",
            "submit_command": f"sbatch {rel(script)}" if all_pass else "",
            "guardrail": "manual submit only after reviewing preflight; no fit release from relaunch alone",
        }
    ]


def build_post_exit_parse_rollup_contract(matrix: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "case_key": row["case_key"],
            "expected_parsed_csv": rel(RELAUNCH / "parsed" / f"matched_plane_metrics_{row['case_key']}.csv"),
            "post_exit_action": "parse-openfoam-samples then rerun pressure/upcomer admission rollup",
            "required_pass_fields": "matched planes;wall-band fields;finite metrics;quality_flags clear",
        }
        for row in matrix
    ]


def build_pressure_upcomer_fit_release_gate(matrix: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "case_key": row["case_key"],
            "fit_release_status": "blocked_pending_post_exit_parse_and_admission",
            "fit_or_model_selection_use_now": "false",
            "release_condition": "all matched-plane and wall-band gates pass after relaunch",
        }
        for row in matrix
    ]


def build_source_manifest() -> list[dict[str, Any]]:
    sources = [
        (REPAIR / "remaining_case_relaunch_queue.csv", "relaunch queue"),
        (RELAUNCH / "candidate_readiness_matrix.csv", "case source metadata"),
        (RUNNER, "existing one-case runner"),
        (OF_ENV, "OpenFOAM environment"),
    ]
    return [{"source_path": rel(path), "exists": "yes" if path.exists() else "no", "source_role": role, "mutation": "read_only"} for path, role in sources]


def write_readme(summary: dict[str, Any]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "README.md").write_text(
        f"# Pressure/Upcomer Isolated Relaunch Submission Package\n\nCases: {summary['case_count']}. Submit allowed: {summary['submit_allowed']}.\n",
        encoding="utf-8",
    )


def write_status_files(summary: dict[str, Any]) -> None:
    STATUS.parent.mkdir(parents=True, exist_ok=True)
    STATUS.write_text(f"# {TASK}\n\n- status: complete\n- case_count: {summary['case_count']}\n- submit_allowed: {summary['submit_allowed']}\n- output: {rel(OUT)}\n", encoding="utf-8")
    JOURNAL.parent.mkdir(parents=True, exist_ok=True)
    JOURNAL.write_text(f"# {DATE} pressure/upcomer isolated relaunch package\n\nBuilt guarded isolated relaunch package.\n", encoding="utf-8")
    write_json(IMPORT, {"task": TASK, "date": DATE, "output_dir": rel(OUT), "native_solver_outputs_mutated": False, "summary_path": rel(OUT / "summary.json")})


def main() -> dict[str, Any]:
    require_sources()
    matrix = build_isolated_relaunch_case_matrix()
    preflight = build_preflight_gate(matrix)
    script = write_sbatch(matrix)
    submit = build_submit_plan(matrix, preflight, script)
    contract = build_post_exit_parse_rollup_contract(matrix)
    release = build_pressure_upcomer_fit_release_gate(matrix)
    sources = build_source_manifest()
    summary = {
        "task": TASK,
        "date": DATE,
        "generated_at_utc": utc_now(),
        "case_count": len(matrix),
        "expected_case_count": len(EXPECTED_RELAUNCH_CASES),
        "expected_cases_present": {row["case_key"] for row in matrix} == EXPECTED_RELAUNCH_CASES,
        "preflight_pass_rows": sum(row["preflight_status"] == "pass" for row in preflight),
        "submit_allowed": submit[0]["submit_allowed"] == "true",
        "submit_status": submit[0]["submit_status"],
        "fit_rows_released_now": 0,
        "native_solver_outputs_mutated": False,
        "registry_mutation": "none",
    }
    write_csv(OUT / "isolated_relaunch_case_matrix.csv", matrix)
    write_csv(OUT / "preflight_gate.csv", preflight)
    write_csv(OUT / "submit_plan.csv", submit)
    write_csv(OUT / "post_exit_parse_rollup_contract.csv", contract)
    write_csv(OUT / "pressure_upcomer_fit_release_gate.csv", release)
    write_csv(OUT / "source_manifest.csv", sources)
    write_json(OUT / "summary.json", summary)
    write_readme(summary)
    write_status_files(summary)
    return summary


if __name__ == "__main__":
    print(json.dumps(main(), indent=2, sort_keys=True))
