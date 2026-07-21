#!/usr/bin/env python3
"""Run Salt2 coarse reconstructed-T thermal repair smoke.

This is an AGENT-305 wrapper around the validated AGENT-267/291 repair-trial
functions. It stages a fresh coarse mirror, reconstructs T first, scans it, then
adds non-T fields and runs the same section/segment thermal samplers. It does
not mutate native solver outputs.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.analyze import build_reconstructed_t_repair_trial as repair  # noqa: E402

TASK_ID = "AGENT-305"
DEFAULT_OUTPUT = ROOT / "work_products/2026-07/2026-07-13/2026-07-13_salt2_coarse_thermal_repair_smoke"
COARSE_CASE = repair.Case(
    "coarse",
    repair.BASE / "coarse/viscosity_screening_salt_test_2_jin_coarse_mesh",
    "2431",
    "processors64",
)


def configure_package(output_dir: Path) -> None:
    repair.PKG = output_dir
    repair.LOGS = output_dir / "logs"
    repair.OUTPUTS = output_dir / "outputs"
    repair.RECON = output_dir / "recon"
    repair.SCRIPTS = output_dir / "scripts"
    repair.TASK_ID = TASK_ID


def build(output_dir: Path, reconstruct_timeout_s: int, foam_timeout_s: int) -> dict[str, object]:
    configure_package(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    for path in (repair.LOGS, repair.OUTPUTS, repair.RECON, repair.SCRIPTS):
        path.mkdir(parents=True, exist_ok=True)

    trial = repair.reconstruct_split_full(
        COARSE_CASE,
        "cwd_controlDict_collated",
        command_timeout_s=reconstruct_timeout_s,
    )
    results: dict[str, object] = {
        "task_id": TASK_ID,
        "generated_at": repair.now(),
        "native_solver_outputs_mutated": False,
        "source_case": str(COARSE_CASE.source),
        "level": COARSE_CASE.level,
        "time": COARSE_CASE.time,
        "processor_dir": COARSE_CASE.proc,
        "reconstruction_trials": [trial],
        "section_temperature_sampling": [],
        "segment_thermal_extraction": [],
    }
    if trial["clean_T"]:
        section = repair.run_section_temperature_sampling(COARSE_CASE, str(trial["stage"]), timeout_s=foam_timeout_s)
        segment = repair.run_segment_thermal(COARSE_CASE, str(trial["stage"]), timeout_s=foam_timeout_s)
        results["section_temperature_sampling"] = [section]
        results["segment_thermal_extraction"] = [segment]
        if section["gate_pass"] and segment["gate_pass"]:
            decision = (
                "Coarse repair smoke passed: clean reconstructed T, successful "
                "temperature section sampling, and segment thermal extraction completed. "
                "Closure admission still requires sign, heat-balance, and mesh gates."
            )
        else:
            decision = "Coarse clean T passed, but section or segment thermal sampling did not pass."
    else:
        decision = "Coarse reconstructed T did not pass scan gates; thermal extraction skipped."
    results["decision"] = decision
    repair.write_summary(results)
    (output_dir / "agent305_command.json").write_text(
        json.dumps(
            {
                "command": [
                    "python3.11",
                    "tools/analyze/build_salt2_coarse_thermal_repair_smoke.py",
                    "--output-dir",
                    str(output_dir),
                    "--reconstruct-timeout-s",
                    str(reconstruct_timeout_s),
                    "--foam-timeout-s",
                    str(foam_timeout_s),
                ],
                "native_solver_outputs_mutated": False,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return results


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--reconstruct-timeout-s", type=int, default=3600)
    parser.add_argument("--foam-timeout-s", type=int, default=1800)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    build(Path(args.output_dir), args.reconstruct_timeout_s, args.foam_timeout_s)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
