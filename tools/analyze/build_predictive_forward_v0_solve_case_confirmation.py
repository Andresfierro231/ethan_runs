#!/usr/bin/env python3
"""Build the forward-v0 full solve_case confirmation package.

This script does not run Fluid's expensive ``solve_case`` path by default. It
writes a no-submit compute-node harness and, after the harness has produced both
engine outputs, can compare ``solve_case`` against the existing ``fast_scan``
engine on the same six forward-v0 rows.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import shlex
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PACKAGE = (
    REPO_ROOT
    / "work_products/2026-07/2026-07-13/2026-07-13_predictive_forward_v0_solve_case_confirmation"
)
FORWARD_RUNNER = REPO_ROOT / "tools/analyze/run_predictive_forward_v0_imposed_cooler.py"
FAST_SCAN_PACKAGE = (
    REPO_ROOT / "work_products/2026-07/2026-07-13/2026-07-13_predictive_forward_v0_imposed_cooler"
)
INPUT_CONTRACT_PACKAGE = (
    REPO_ROOT / "work_products/2026-07/2026-07-13/2026-07-13_predictive_input_contract"
)

RESULT_COLUMNS = [
    "case_id",
    "variant_id",
    "fast_scan_present",
    "solve_case_present",
    "fast_scan_accepted_for_validation",
    "solve_case_accepted_for_validation",
    "accepted_for_validation_match",
    "fast_scan_root_status",
    "solve_case_root_status",
    "mdot_fast_scan_kg_s",
    "mdot_solve_case_kg_s",
    "mdot_delta_solve_minus_fast_kg_s",
    "pressure_residual_fast_scan_Pa",
    "pressure_residual_solve_case_Pa",
    "pressure_residual_delta_solve_minus_fast_Pa",
    "temperature_periodicity_error_fast_scan_K",
    "temperature_periodicity_error_solve_case_K",
    "temperature_periodicity_error_delta_solve_minus_fast_K",
    "model_Tmean_fast_scan_K",
    "model_Tmean_solve_case_K",
    "model_Tmean_delta_solve_minus_fast_K",
    "model_loop_delta_fast_scan_K",
    "model_loop_delta_solve_case_K",
    "model_loop_delta_delta_solve_minus_fast_K",
    "qambient_fast_scan_W",
    "qambient_solve_case_W",
    "qambient_delta_solve_minus_fast_W",
    "qhx_fast_scan_W",
    "qhx_solve_case_W",
    "qhx_delta_solve_minus_fast_W",
    "comparison_status",
    "notes",
]

METRIC_CONTRACT_COLUMNS = [
    "metric_id",
    "source_file",
    "comparison",
    "confirmation_band",
    "interpretation",
]

EXPECTED_OUTPUT_COLUMNS = [
    "path",
    "producer",
    "required_for_confirmation",
    "notes",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT.resolve()))
    except ValueError:
        return str(path)


def q(path: Path) -> str:
    return shlex.quote(str(path))


def csv_value(value: Any) -> Any:
    if value is None:
        return ""
    if isinstance(value, float):
        if not math.isfinite(value):
            return ""
        return f"{value:.12g}"
    return value


def fnum(row: dict[str, str] | None, key: str) -> float | None:
    if row is None:
        return None
    value = row.get(key, "")
    if value == "":
        return None
    try:
        parsed = float(value)
    except ValueError:
        return None
    return parsed if math.isfinite(parsed) else None


def bool_text(value: Any) -> str:
    text = str(value).strip().lower()
    if text in {"true", "1", "yes"}:
        return "true"
    if text in {"false", "0", "no"}:
        return "false"
    return str(value)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({column: csv_value(row.get(column, "")) for column in columns})


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str, *, executable: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    if executable:
        path.chmod(0o755)


def engine_command(output_dir: Path, engine: str) -> str:
    return (
        f"python3 {q(FORWARD_RUNNER)} "
        f"--output-dir {q(output_dir)} "
        "--strict-input-contract --sensor-source both "
        f"--engine {shlex.quote(engine)}"
    )


def compare_command(package_dir: Path) -> str:
    return f"python3 {q(Path(__file__).resolve())} --package-dir {q(package_dir)} --compare"


def shell_runner_text(package_dir: Path) -> str:
    fast_dir = package_dir / "fast_scan_reference"
    solve_dir = package_dir / "solve_case_full"
    logs_dir = package_dir / "logs"
    return f"""#!/usr/bin/env bash
set -euo pipefail

ROOT={q(REPO_ROOT)}
PKG={q(package_dir)}
LOGS={q(logs_dir)}

cd "${{ROOT}}"
mkdir -p "${{LOGS}}"
module load python/3.12.11 2>/dev/null || true

echo "started_at=$(date +%Y-%m-%dT%H:%M:%S%z) host=$(hostname) job=${{SLURM_JOB_ID:-none}}" > "${{LOGS}}/run_provenance.env"
{engine_command(fast_dir, "fast_scan")} > "${{LOGS}}/fast_scan_reference.log" 2>&1
{engine_command(solve_dir, "solve_case")} > "${{LOGS}}/solve_case_full.log" 2>&1
{compare_command(package_dir)} > "${{LOGS}}/comparison.log" 2>&1
echo "completed_at=$(date +%Y-%m-%dT%H:%M:%S%z)" >> "${{LOGS}}/run_provenance.env"
"""


def sbatch_text(package_dir: Path) -> str:
    script = package_dir / "scripts/run_forward_v0_solve_case_confirmation.sh"
    logs = package_dir / "logs"
    return f"""#!/usr/bin/env bash
#SBATCH -J fwdv0_solve
#SBATCH -A ASC23046
#SBATCH -p NuclearEnergy
#SBATCH -N 1
#SBATCH -n 1
#SBATCH -c 4
#SBATCH -t 06:00:00
#SBATCH -o {logs}/slurm_%j.out
#SBATCH -e {logs}/slurm_%j.err

set -euo pipefail
cd {q(REPO_ROOT)}
mkdir -p {q(logs)}
srun -N1 -n1 -c4 bash {q(script)}
"""


def expected_output_rows(package_dir: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for engine_dir, producer in [
        ("fast_scan_reference", "fast_scan command"),
        ("solve_case_full", "solve_case command"),
    ]:
        for filename in [
            "forward_v0_run_plan.csv",
            "forward_v0_results.csv",
            "forward_v0_variant_summary.csv",
            "forward_v0_sensor_predictions_experimental.csv",
            "forward_v0_sensor_predictions_cfd.csv",
            "forward_v0_segment_states.csv",
            "forward_v0_input_audit.csv",
            "forward_v0_litrev_gate_reference_audit.csv",
            "summary.json",
            "README.md",
        ]:
            rows.append(
                {
                    "path": rel(package_dir / engine_dir / filename),
                    "producer": producer,
                    "required_for_confirmation": "true" if filename in {"forward_v0_results.csv", "summary.json"} else "false",
                    "notes": "same schema as completed forward-v0 package",
                }
            )
    rows.extend(
        [
            {
                "path": rel(package_dir / "solve_case_vs_fast_scan_comparison.csv"),
                "producer": "comparison pass",
                "required_for_confirmation": "true",
                "notes": "row-level solve_case minus fast_scan deltas",
            },
            {
                "path": rel(package_dir / "comparison_summary.json"),
                "producer": "comparison pass",
                "required_for_confirmation": "true",
                "notes": "aggregate row counts, status, and metric bands",
            },
        ]
    )
    return rows


def metric_contract_rows() -> list[dict[str, str]]:
    return [
        {
            "metric_id": "row_identity",
            "source_file": "forward_v0_results.csv",
            "comparison": "same case_id and variant_id in fast_scan_reference and solve_case_full",
            "confirmation_band": "all 6 rows present in both engines",
            "interpretation": "missing rows block confirmation",
        },
        {
            "metric_id": "accepted_for_validation",
            "source_file": "forward_v0_results.csv",
            "comparison": "solve_case accepted_for_validation and fast_scan accepted_for_validation",
            "confirmation_band": "all solve_case rows true; mismatches reported",
            "interpretation": "solve_case is authoritative; a false solve_case row blocks thesis use",
        },
        {
            "metric_id": "mdot_delta_kg_s",
            "source_file": "forward_v0_results.csv",
            "comparison": "solve_case mdot_kg_s minus fast_scan mdot_kg_s",
            "confirmation_band": "report all rows; <= 1e-3 kg/s supports fast_scan as a proxy",
            "interpretation": "larger deltas do not invalidate solve_case, but fast_scan must be labeled approximate",
        },
        {
            "metric_id": "pressure_residual_delta_Pa",
            "source_file": "forward_v0_results.csv",
            "comparison": "solve_case pressure_residual_Pa minus fast_scan pressure_residual_Pa",
            "confirmation_band": "report all rows; solve_case should be near its internal validity policy",
            "interpretation": "used to diagnose whether fast_scan residual tolerances are materially different",
        },
        {
            "metric_id": "model_Tmean_delta_K",
            "source_file": "forward_v0_results.csv",
            "comparison": "solve_case model_Tmean_proxy_K minus fast_scan model_Tmean_proxy_K",
            "confirmation_band": "report all rows; <= 1 K supports fast_scan thermal proxy",
            "interpretation": "larger thermal deltas mean thesis tables should use solve_case only",
        },
        {
            "metric_id": "model_loop_delta_delta_K",
            "source_file": "forward_v0_results.csv",
            "comparison": "solve_case model_loop_delta_proxy_K minus fast_scan model_loop_delta_proxy_K",
            "confirmation_band": "report all rows; <= 1 K supports fast_scan loop-span proxy",
            "interpretation": "checks whether local thermal gradients shift under full solve",
        },
        {
            "metric_id": "qambient_delta_W",
            "source_file": "forward_v0_results.csv",
            "comparison": "solve_case qambient_total_W minus fast_scan qambient_total_W",
            "confirmation_band": "report all rows; <= 5 W supports fast_scan heat-ledger proxy",
            "interpretation": "larger deltas require heat-ledger claims from solve_case package",
        },
        {
            "metric_id": "sensor_streams",
            "source_file": "forward_v0_sensor_predictions_experimental.csv and forward_v0_sensor_predictions_cfd.csv",
            "comparison": "row counts and downstream error summaries after solve",
            "confirmation_band": "expected 102 experimental and 102 CFD sensor rows per engine",
            "interpretation": "sensor rows remain validation outputs, not runtime inputs",
        },
    ]


def rows_by_key(rows: list[dict[str, str]]) -> dict[tuple[str, str], dict[str, str]]:
    return {(row.get("case_id", ""), row.get("variant_id", "")): row for row in rows}


def delta(solve: dict[str, str] | None, fast: dict[str, str] | None, field: str) -> float | None:
    solve_value = fnum(solve, field)
    fast_value = fnum(fast, field)
    if solve_value is None or fast_value is None:
        return None
    return solve_value - fast_value


def compare_results(fast_rows: list[dict[str, str]], solve_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    fast = rows_by_key(fast_rows)
    solve = rows_by_key(solve_rows)
    keys = sorted(set(fast) | set(solve))
    rows: list[dict[str, Any]] = []
    for case_id, variant_id in keys:
        fast_row = fast.get((case_id, variant_id))
        solve_row = solve.get((case_id, variant_id))
        fast_present = fast_row is not None
        solve_present = solve_row is not None
        fast_accepted = bool_text(fast_row.get("accepted_for_validation", "")) if fast_row else ""
        solve_accepted = bool_text(solve_row.get("accepted_for_validation", "")) if solve_row else ""
        notes: list[str] = []
        status = "pass"
        if not fast_present:
            status = "blocked"
            notes.append("missing fast_scan row")
        if not solve_present:
            status = "blocked"
            notes.append("missing solve_case row")
        if solve_present and solve_accepted != "true":
            status = "blocked"
            notes.append("solve_case row not accepted for validation")
        if fast_present and solve_present and fast_accepted != solve_accepted:
            notes.append("accepted_for_validation mismatch")
        rows.append(
            {
                "case_id": case_id,
                "variant_id": variant_id,
                "fast_scan_present": str(fast_present).lower(),
                "solve_case_present": str(solve_present).lower(),
                "fast_scan_accepted_for_validation": fast_accepted,
                "solve_case_accepted_for_validation": solve_accepted,
                "accepted_for_validation_match": str(fast_accepted == solve_accepted).lower() if fast_present and solve_present else "",
                "fast_scan_root_status": fast_row.get("root_status", "") if fast_row else "",
                "solve_case_root_status": solve_row.get("root_status", "") if solve_row else "",
                "mdot_fast_scan_kg_s": fnum(fast_row, "mdot_kg_s"),
                "mdot_solve_case_kg_s": fnum(solve_row, "mdot_kg_s"),
                "mdot_delta_solve_minus_fast_kg_s": delta(solve_row, fast_row, "mdot_kg_s"),
                "pressure_residual_fast_scan_Pa": fnum(fast_row, "pressure_residual_Pa"),
                "pressure_residual_solve_case_Pa": fnum(solve_row, "pressure_residual_Pa"),
                "pressure_residual_delta_solve_minus_fast_Pa": delta(solve_row, fast_row, "pressure_residual_Pa"),
                "temperature_periodicity_error_fast_scan_K": fnum(fast_row, "temperature_periodicity_error_K"),
                "temperature_periodicity_error_solve_case_K": fnum(solve_row, "temperature_periodicity_error_K"),
                "temperature_periodicity_error_delta_solve_minus_fast_K": delta(solve_row, fast_row, "temperature_periodicity_error_K"),
                "model_Tmean_fast_scan_K": fnum(fast_row, "model_Tmean_proxy_K"),
                "model_Tmean_solve_case_K": fnum(solve_row, "model_Tmean_proxy_K"),
                "model_Tmean_delta_solve_minus_fast_K": delta(solve_row, fast_row, "model_Tmean_proxy_K"),
                "model_loop_delta_fast_scan_K": fnum(fast_row, "model_loop_delta_proxy_K"),
                "model_loop_delta_solve_case_K": fnum(solve_row, "model_loop_delta_proxy_K"),
                "model_loop_delta_delta_solve_minus_fast_K": delta(solve_row, fast_row, "model_loop_delta_proxy_K"),
                "qambient_fast_scan_W": fnum(fast_row, "qambient_total_W"),
                "qambient_solve_case_W": fnum(solve_row, "qambient_total_W"),
                "qambient_delta_solve_minus_fast_W": delta(solve_row, fast_row, "qambient_total_W"),
                "qhx_fast_scan_W": fnum(fast_row, "qhx_total_W"),
                "qhx_solve_case_W": fnum(solve_row, "qhx_total_W"),
                "qhx_delta_solve_minus_fast_W": delta(solve_row, fast_row, "qhx_total_W"),
                "comparison_status": status,
                "notes": "; ".join(notes),
            }
        )
    return rows


def abs_max(rows: list[dict[str, Any]], field: str) -> float | None:
    values = [abs(float(row[field])) for row in rows if row.get(field) not in ("", None)]
    return max(values) if values else None


def comparison_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    blocked = [row for row in rows if row.get("comparison_status") != "pass"]
    return {
        "generated_utc": utc_now(),
        "n_comparison_rows": len(rows),
        "n_pass_rows": len(rows) - len(blocked),
        "n_blocked_rows": len(blocked),
        "overall_status": "pass" if rows and not blocked else "blocked_or_pending",
        "max_abs_mdot_delta_kg_s": abs_max(rows, "mdot_delta_solve_minus_fast_kg_s"),
        "max_abs_Tmean_delta_K": abs_max(rows, "model_Tmean_delta_solve_minus_fast_K"),
        "max_abs_loop_delta_delta_K": abs_max(rows, "model_loop_delta_delta_solve_minus_fast_K"),
        "max_abs_qambient_delta_W": abs_max(rows, "qambient_delta_solve_minus_fast_W"),
        "interpretation": "solve_case rows are authoritative; fast_scan is a proxy only where deltas stay inside the documented bands",
    }


def comparison_inputs_exist(package_dir: Path) -> bool:
    return (package_dir / "fast_scan_reference/forward_v0_results.csv").exists() and (
        package_dir / "solve_case_full/forward_v0_results.csv"
    ).exists()


def run_comparison(package_dir: Path) -> dict[str, Any]:
    fast_path = package_dir / "fast_scan_reference/forward_v0_results.csv"
    solve_path = package_dir / "solve_case_full/forward_v0_results.csv"
    rows = compare_results(read_csv(fast_path), read_csv(solve_path))
    write_csv(package_dir / "solve_case_vs_fast_scan_comparison.csv", rows, RESULT_COLUMNS)
    summary = comparison_summary(rows)
    write_json(package_dir / "comparison_summary.json", summary)
    return summary


def write_pending_comparison(package_dir: Path) -> dict[str, Any]:
    summary = {
        "generated_utc": utc_now(),
        "overall_status": "pending_compute_node_run",
        "required_inputs": [
            rel(package_dir / "fast_scan_reference/forward_v0_results.csv"),
            rel(package_dir / "solve_case_full/forward_v0_results.csv"),
        ],
        "next_command": rel(package_dir / "scripts/run_forward_v0_solve_case_confirmation.sbatch"),
    }
    write_csv(package_dir / "solve_case_vs_fast_scan_comparison.csv", [], RESULT_COLUMNS)
    write_json(package_dir / "comparison_summary.json", summary)
    return summary


def write_readme(package_dir: Path, summary: dict[str, Any]) -> None:
    fast_dir = package_dir / "fast_scan_reference"
    solve_dir = package_dir / "solve_case_full"
    text = f"""# Forward V0 solve_case Confirmation

Generated: `{summary['generated_utc']}`

Task: `AGENT-293`

## Why This Exists

The completed forward-v0 imposed-cooler package used `--engine fast_scan`
because Fluid's full nested `solve_case` path was too slow interactively. This
package prepares the full confirmation path for a compute node without
submitting a job from the login session.

## Open First

- `work_products/2026-07/2026-07-13/2026-07-13_predictive_forward_v0_imposed_cooler/README.md`
- `work_products/2026-07/2026-07-13/2026-07-13_predictive_input_contract/README.md`
- `tools/analyze/run_predictive_forward_v0_imposed_cooler.py`
- `tools/analyze/build_predictive_forward_v0_solve_case_confirmation.py`

## Exact Commands

Login-node smoke, plan regeneration only:

```bash
python3 tools/analyze/build_predictive_forward_v0_solve_case_confirmation.py
```

Compute-node full confirmation command:

```bash
bash {rel(package_dir / "scripts/run_forward_v0_solve_case_confirmation.sh")}
```

Prepared Slurm command, not submitted by this package:

```bash
sbatch {rel(package_dir / "scripts/run_forward_v0_solve_case_confirmation.sbatch")}
```

The shell runner executes:

```bash
{engine_command(fast_dir, "fast_scan")}
{engine_command(solve_dir, "solve_case")}
{compare_command(package_dir)}
```

## Compute-Node Requirements

- Run on a compute node, not a login node.
- Slurm template: account `ASC23046`, partition `NuclearEnergy`, `1` node,
  `1` task, `4` CPUs per task, walltime `06:00:00`.
- Expected workload: six forward-v0 rows (`3` Salt cases x `2` source variants)
  using Fluid only; no OpenFOAM solver output is read or mutated.
- If `06:00:00` expires, preserve logs and rerun only after inspecting
  `logs/solve_case_full.log`.

## Expected Output Package

- `{rel(fast_dir)}/`
- `{rel(solve_dir)}/`
- `{rel(package_dir / "solve_case_vs_fast_scan_comparison.csv")}`
- `{rel(package_dir / "comparison_summary.json")}`

## Comparison Metrics

See `comparison_metric_contract.csv`. The core row-level metrics are mdot,
pressure residual, temperature periodicity error, model Tmean proxy, loop delta
proxy, ambient heat loss, cooler heat, root status, and validation acceptance.
Full `solve_case` rows are authoritative. `fast_scan` is thesis-grade only as a
proxy where deltas remain inside the documented bands.

## Current Status

`{summary['comparison_status']}`. No scheduler job was submitted by this
package builder.

## Guardrails

- Do not run the full `--engine solve_case` matrix on a login node.
- Do not edit the completed `TODO-PRED-FORWARD-V0` package.
- Do not mutate native CFD/OpenFOAM outputs.
- Do not treat imposed cooler duty as predictive HX closure.
"""
    write_text(package_dir / "README.md", text)


def build_package(package_dir: Path = DEFAULT_PACKAGE, *, compare: bool = False) -> dict[str, Any]:
    scripts = package_dir / "scripts"
    (package_dir / "logs").mkdir(parents=True, exist_ok=True)
    write_text(scripts / "run_forward_v0_solve_case_confirmation.sh", shell_runner_text(package_dir), executable=True)
    write_text(scripts / "run_forward_v0_solve_case_confirmation.sbatch", sbatch_text(package_dir), executable=True)
    write_csv(package_dir / "expected_outputs.csv", expected_output_rows(package_dir), EXPECTED_OUTPUT_COLUMNS)
    write_csv(package_dir / "comparison_metric_contract.csv", metric_contract_rows(), METRIC_CONTRACT_COLUMNS)

    if compare and comparison_inputs_exist(package_dir):
        comparison = run_comparison(package_dir)
        comparison_status = comparison["overall_status"]
    elif comparison_inputs_exist(package_dir):
        comparison = run_comparison(package_dir)
        comparison_status = comparison["overall_status"]
    else:
        comparison = write_pending_comparison(package_dir)
        comparison_status = comparison["overall_status"]

    summary = {
        "task_id": "AGENT-293",
        "generated_utc": utc_now(),
        "package": rel(package_dir),
        "comparison_status": comparison_status,
        "job_submitted": False,
        "source_packages": {
            "fast_scan_completed_package": rel(FAST_SCAN_PACKAGE),
            "input_contract_package": rel(INPUT_CONTRACT_PACKAGE),
            "forward_runner": rel(FORWARD_RUNNER),
        },
        "commands": {
            "fast_scan_reference": engine_command(package_dir / "fast_scan_reference", "fast_scan"),
            "solve_case_full": engine_command(package_dir / "solve_case_full", "solve_case"),
            "compare": compare_command(package_dir),
            "sbatch": f"sbatch {rel(scripts / 'run_forward_v0_solve_case_confirmation.sbatch')}",
        },
        "compute_node_requirements": {
            "account": "ASC23046",
            "partition": "NuclearEnergy",
            "nodes": 1,
            "tasks": 1,
            "cpus_per_task": 4,
            "walltime": "06:00:00",
            "login_node_policy": "do not run solve_case full matrix on a login node",
        },
        "expected_rows": {
            "cases": 3,
            "variants": 2,
            "result_rows_per_engine": 6,
            "experimental_sensor_rows_per_engine": 102,
            "cfd_sensor_rows_per_engine": 102,
        },
        "comparison_summary": comparison,
    }
    write_json(package_dir / "summary.json", summary)
    write_readme(package_dir, summary)
    return summary


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package-dir", type=Path, default=DEFAULT_PACKAGE)
    parser.add_argument("--compare", action="store_true", help="compare existing fast_scan and solve_case outputs")
    args = parser.parse_args(list(argv) if argv is not None else None)
    summary = build_package(args.package_dir, compare=args.compare)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
