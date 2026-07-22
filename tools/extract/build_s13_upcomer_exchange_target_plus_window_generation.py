#!/usr/bin/env python3
"""Stage and preflight S13 nominal Salt target-plus continuation windows."""

from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[2]
TASK_ID = "TODO-S13-UPCOMER-EXCHANGE-TARGET-PLUS-WINDOW-GENERATION-2026-07-22"
OUT = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_target_plus_window_generation"
STAGING = ROOT / "staging/s13_target_plus_window_generation_2026-07-22"
RUNNER = ROOT / "tools/run_openfoam_case.sh"
OPENFOAM_ENV = ROOT / "jadyn_runs/salt2/2026-06-02_runtime_recovery/scripts/of13-env.sh"
RCWALL_LIBDIR = ROOT / "jadyn_runs/modern_runs/2026-06-25_ethan_normal_relaunch_and_recirculation_boundary_wave/runtime_libs"
PRIOR_SAMPLING = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_qwall_neighbor_window_sampling"


@dataclass(frozen=True)
class CaseSpec:
    case_id: str
    job_name: str
    source_case: Path
    restart_time_s: str
    target_plus_time_s: str

    @property
    def staged_case(self) -> Path:
        return STAGING / self.case_id / "case_stage" / self.source_case.name


CASES = [
    CaseSpec(
        "salt_2",
        "s13_s2_tplus",
        ROOT
        / "jadyn_runs/modern_runs/2026-06-18_convergence_and_jin_envelope_wave/runs/salt2_jin/case_stage/viscosity_screening_salt_test_2_jin_coarse_mesh_continuation",
        "7915",
        "7916",
    ),
    CaseSpec(
        "salt_3",
        "s13_s3_tplus",
        ROOT
        / "jadyn_runs/modern_runs/2026-06-18_convergence_and_jin_envelope_wave/runs/salt3_jin/case_stage/viscosity_screening_salt_test_3_jin_coarse_mesh_continuation",
        "7618",
        "7619",
    ),
    CaseSpec(
        "salt_4",
        "s13_s4_tplus",
        ROOT
        / "jadyn_runs/modern_runs/2026-06-18_convergence_and_jin_envelope_wave/runs/salt4_jin/case_stage/viscosity_screening_salt_test_4_jin_coarse_mesh_continuation",
        "10000",
        "10001",
    ),
]

COPY_ITEMS = ["0", "constant", "system", "case_config.yaml", "dynamicCode"]
TARGET_FIELDS = ["U", "T", "rho", "wallHeatFlux"]


def now_iso() -> str:
    return datetime.now(ZoneInfo("America/Chicago")).replace(microsecond=0).isoformat()


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def numeric_times(processors: Path) -> list[float]:
    out = []
    for child in processors.iterdir():
        if not child.is_dir():
            continue
        try:
            out.append(float(child.name))
        except ValueError:
            pass
    return sorted(out)


def csv_dump(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def replace_control_value(text: str, key: str, value: str) -> str:
    pattern = rf"(?m)^(\s*{re.escape(key)}\s+)\S+(\s*;)"
    new, count = re.subn(pattern, rf"\g<1>{value}\2", text, count=1)
    if count != 1:
        raise RuntimeError(f"controlDict key not found exactly once: {key}")
    return new


def patch_control_dict(path: Path, end_time_s: str) -> dict[str, str]:
    text = path.read_text()
    replacements = {
        "startFrom": "latestTime",
        "stopAt": "endTime",
        "endTime": end_time_s,
        "writeControl": "adjustableRunTime",
        "writeInterval": "1",
        "purgeWrite": "0",
        "timeFormat": "general",
        "timePrecision": "9",
    }
    for key, value in replacements.items():
        text = replace_control_value(text, key, value)
    path.write_text(text)
    return replacements


def control_values(path: Path, keys: list[str]) -> dict[str, str]:
    text = path.read_text()
    out = {}
    for key in keys:
        match = re.search(rf"(?m)^\s*{re.escape(key)}\s+(\S+)\s*;", text)
        out[key] = match.group(1) if match else ""
    return out


def copy_path(src: Path, dst: Path) -> None:
    if not src.exists():
        return
    if dst.exists():
        return
    if src.is_dir():
        shutil.copytree(src, dst, symlinks=False)
    else:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)


def assert_no_symlinks(path: Path) -> None:
    for child in path.rglob("*"):
        if child.is_symlink():
            raise RuntimeError(f"staged clone contains symlink: {child}")


def stage_case(case: CaseSpec) -> dict[str, object]:
    source = case.source_case
    target = case.staged_case
    if not (source / "processors64" / case.restart_time_s).is_dir():
        raise RuntimeError(f"missing source restart time for {case.case_id}: {source / 'processors64' / case.restart_time_s}")
    for field in TARGET_FIELDS:
        if not (source / "processors64" / case.restart_time_s / field).is_file():
            raise RuntimeError(f"missing source field {field} for {case.case_id}")

    target.mkdir(parents=True, exist_ok=True)
    for item in COPY_ITEMS:
        copy_path(source / item, target / item)
    (target / "processors64").mkdir(exist_ok=True)
    copy_path(source / "processors64/constant", target / "processors64/constant")
    copy_path(source / "processors64" / case.restart_time_s, target / "processors64" / case.restart_time_s)
    (target / "logs").mkdir(exist_ok=True)

    source_pointer = target / "SOURCE_PROCESSORS64.txt"
    if not source_pointer.exists():
        source_pointer.write_text(str(source / "processors64") + "\n")
    patch_control_dict(target / "system/controlDict", case.target_plus_time_s)
    assert_no_symlinks(target)

    values = control_values(
        target / "system/controlDict",
        ["startFrom", "stopAt", "endTime", "writeControl", "writeInterval", "purgeWrite", "timeFormat", "timePrecision"],
    )
    return {
        "case_id": case.case_id,
        "source_case": rel(source),
        "staged_case": rel(target),
        "restart_time_s": case.restart_time_s,
        "target_plus_time_s": case.target_plus_time_s,
        "source_latest_time_s": f"{numeric_times(source / 'processors64')[-1]:.12g}",
        "target_plus_already_exists_in_staged_case": str((target / "processors64" / case.target_plus_time_s).is_dir()).lower(),
        "native_source_mutated": "false",
        **{f"control_{key}": value for key, value in values.items()},
    }


def write_sbatch(case: CaseSpec) -> Path:
    path = STAGING / "jobs" / f"{case.job_name}.sbatch"
    log_path = case.staged_case / "logs/log.foamRun_target_plus"
    path.parent.mkdir(parents=True, exist_ok=True)
    text = f"""#!/usr/bin/env bash
#SBATCH --job-name={case.job_name}
#SBATCH --account=ASC23046
#SBATCH --partition=NuclearEnergy
#SBATCH --nodes=1
#SBATCH --ntasks=64
#SBATCH --time=02:00:00
#SBATCH --output={case.staged_case}/logs/slurm-%x-%j.out
#SBATCH --error={case.staged_case}/logs/slurm-%x-%j.err

set -euo pipefail
cd {ROOT}
export OMP_NUM_THREADS=1
export OPENFOAM13_ENV_SH={OPENFOAM_ENV}
export RCWALLBC_LIBDIR={RCWALL_LIBDIR}

bash {RUNNER} \\
  --case-dir {case.staged_case} \\
  --rcwall-libdir "$RCWALLBC_LIBDIR" \\
  --openfoam-env-sh "$OPENFOAM13_ENV_SH" \\
  --log-path {log_path} \\
  --truncate-log
"""
    path.write_text(text)
    path.chmod(0o750)
    return path


def dry_run(case: CaseSpec) -> dict[str, object]:
    log = OUT / "dry_runs" / f"{case.case_id}_dry_run.txt"
    log.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "bash",
        str(RUNNER),
        "--case-dir",
        str(case.staged_case),
        "--rcwall-libdir",
        str(RCWALL_LIBDIR),
        "--openfoam-env-sh",
        str(OPENFOAM_ENV),
        "--log-path",
        str(case.staged_case / "logs/log.foamRun_target_plus"),
        "--dry-run",
    ]
    proc = subprocess.run(cmd, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    log.write_text(proc.stdout)
    return {
        "case_id": case.case_id,
        "dry_run_returncode": proc.returncode,
        "dry_run_log": rel(log),
        "dry_run_passed": str(proc.returncode == 0).lower(),
    }


def source_manifest_rows() -> list[dict[str, str]]:
    rows = [
        {
            "path": rel(PRIOR_SAMPLING / "summary.json"),
            "role": "completed target-minus/target inventory showing target-plus gap",
            "mutation": "read_only",
        },
        {
            "path": rel(RUNNER),
            "role": "trusted OpenFOAM launch wrapper",
            "mutation": "read_only",
        },
    ]
    for case in CASES:
        rows.append({"path": rel(case.source_case), "role": f"{case.case_id} native nominal source case", "mutation": "read_only"})
        rows.append(
            {
                "path": rel(case.source_case / "processors64" / case.restart_time_s),
                "role": f"{case.case_id} native restart time copied into staged clone",
                "mutation": "read_only",
            }
        )
    return rows


def guardrail_rows() -> list[dict[str, str]]:
    flags = {
        "native_output_mutation": "false",
        "registry_or_admission_mutation": "false",
        "solver_launched_by_prepare_script": "false",
        "scheduler_submission_by_prepare_script": "false",
        "production_harvest": "false",
        "same_qoi_uq_execution": "false",
        "mesh_gci_uq_execution": "false",
        "Qwall_source_property_or_coefficient_release": "false",
        "s11_s12_s13_s15_s6_trigger": "false",
        "residual_absorbed_into_internal_nu": "false",
    }
    return [{"guardrail": key, "value": value} for key, value in flags.items()]


def write_readme(summary: dict[str, object]) -> None:
    lines = [
        "---",
        "provenance:",
        f"  - {rel(OUT / 'staged_case_manifest.csv')}",
        f"  - {rel(OUT / 'dry_run_manifest.csv')}",
        f"  - {rel(OUT / 'submission_manifest.csv')}",
        "tags: [s13, upcomer-exchange, target-plus, openfoam, slurm]",
        "related:",
        "  - .agent/status/2026-07-22_TODO-S13-UPCOMER-EXCHANGE-TARGET-PLUS-WINDOW-GENERATION-2026-07-22.md",
        f"  - {rel(PRIOR_SAMPLING / 'README.md')}",
        f"task: {TASK_ID}",
        "date: 2026-07-22",
        "role: Hydraulics / Thermal-modeling / cfd-pp / Scheduler / Implementer / Tester / Writer / Reviewer",
        "type: work_product",
        "status: active",
        "---",
        "# S13 Target-Plus Window Generation",
        "",
        f"Decision: `{summary['decision']}`.",
        "",
        "This package stages minimal restart clones for the nominal Salt2/Salt3/Salt4",
        "S13 source cases and prepares Slurm jobs to generate the missing target-plus",
        "windows needed before same-QOI neighbor-window UQ can be rerun.",
        "",
        "- Salt2 target-plus: `7916`",
        "- Salt3 target-plus: `7619`",
        "- Salt4 target-plus: `10001`",
        f"- staged cases: `{summary['staged_case_count']}`",
        f"- dry-run passed cases: `{summary['dry_run_passed_count']}`",
        "",
        "The native source cases are read-only provenance. Only the staged clones under",
        f"`{rel(STAGING)}` may be advanced.",
        "",
        "Do not run S13 harvest, same-QOI UQ, mesh/GCI UQ, or admission from this",
        "package. A later harvest row must wait until the submitted target-plus jobs",
        "reach terminal success and the required fields are present.",
    ]
    (OUT / "README.md").write_text("\n".join(lines) + "\n")


def build() -> dict[str, object]:
    OUT.mkdir(parents=True, exist_ok=True)
    STAGING.mkdir(parents=True, exist_ok=True)
    staged_rows = [stage_case(case) for case in CASES]
    sbatch_rows = []
    for case in CASES:
        sbatch_path = write_sbatch(case)
        sbatch_rows.append(
            {
                "case_id": case.case_id,
                "job_name": case.job_name,
                "sbatch_script": rel(sbatch_path),
                "staged_case": rel(case.staged_case),
                "restart_time_s": case.restart_time_s,
                "target_plus_time_s": case.target_plus_time_s,
                "walltime": "02:00:00",
                "ntasks": "64",
                "partition": "NuclearEnergy",
                "account": "ASC23046",
            }
        )
    dry_rows = [dry_run(case) for case in CASES]
    submission_rows = [
        {
            "case_id": row["case_id"],
            "job_name": row["job_name"],
            "sbatch_script": row["sbatch_script"],
            "submitted_job_id": "",
            "submission_status": "not_submitted_by_prepare_script",
            "terminal_status": "",
            "expected_target_plus_dir": rel(CASES[i].staged_case / "processors64" / CASES[i].target_plus_time_s),
        }
        for i, row in enumerate(sbatch_rows)
    ]

    csv_dump(
        OUT / "staged_case_manifest.csv",
        [
            "case_id",
            "source_case",
            "staged_case",
            "restart_time_s",
            "target_plus_time_s",
            "source_latest_time_s",
            "target_plus_already_exists_in_staged_case",
            "native_source_mutated",
            "control_startFrom",
            "control_stopAt",
            "control_endTime",
            "control_writeControl",
            "control_writeInterval",
            "control_purgeWrite",
            "control_timeFormat",
            "control_timePrecision",
        ],
        staged_rows,
    )
    csv_dump(
        OUT / "sbatch_manifest.csv",
        ["case_id", "job_name", "sbatch_script", "staged_case", "restart_time_s", "target_plus_time_s", "walltime", "ntasks", "partition", "account"],
        sbatch_rows,
    )
    csv_dump(OUT / "dry_run_manifest.csv", ["case_id", "dry_run_returncode", "dry_run_log", "dry_run_passed"], dry_rows)
    csv_dump(
        OUT / "submission_manifest.csv",
        ["case_id", "job_name", "sbatch_script", "submitted_job_id", "submission_status", "terminal_status", "expected_target_plus_dir"],
        submission_rows,
    )
    csv_dump(OUT / "source_manifest.csv", ["path", "role", "mutation"], source_manifest_rows())
    csv_dump(OUT / "no_mutation_guardrails.csv", ["guardrail", "value"], guardrail_rows())

    summary = {
        "task_id": TASK_ID,
        "generated_at": now_iso(),
        "decision": "staged_target_plus_jobs_ready_for_submission",
        "staged_case_count": len(staged_rows),
        "dry_run_passed_count": sum(1 for row in dry_rows if row["dry_run_passed"] == "true"),
        "submitted_job_count": 0,
        "target_plus_rows_harvested": 0,
        "same_qoi_uq_executed": False,
        "production_harvest_allowed": False,
        "native_output_mutation": False,
        "registry_or_admission_mutation": False,
        "solver_launched_by_prepare_script": False,
        "scheduler_submission_by_prepare_script": False,
        "Qwall_source_property_or_coefficient_release": False,
        "s11_s12_s13_s15_s6_trigger": False,
        "blocker_register_change": False,
        "generated_index_refresh": False,
        "residual_absorbed_into_internal_nu": False,
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    write_readme(summary)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true", help="print summary JSON")
    args = parser.parse_args()
    summary = build()
    print(json.dumps(summary, indent=2) if args.json else f"wrote {rel(OUT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
