#!/usr/bin/env python3
"""Stage heater-only, residual-balanced Salt bracket children.

This script preserves the original unbalanced hiQ_hiIns / loQ_loIns trees and
creates new sibling staged cases whose baseline insulation matches the parent
source while the cooling-branch fixed-Q sinks are solved from the preserved
parent late-window heat ledger.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


REPO_ROOT = Path("/scratch/09748/andresfierro231/projects_scratch/ethan_runs")
CAMPAIGN_ROOT = REPO_ROOT / "jadyn_runs/modern_runs/2026-06-19_ethan_blocker_and_1d_followon_wave"
RUNS_ROOT = CAMPAIGN_ROOT / "runs"


CASES = [
    {
        "case_key": "salt2_jin_hiq_balq",
        "parent_case_dir": REPO_ROOT / "staging/modern_runs/2026-06-01_full_extractable_batch/salt/viscosity_screening_salt_test_2_jin_coarse_mesh",
        "target_case_dir": RUNS_ROOT / "salt2_jin_hiq_balq/case_stage/viscosity_screening_salt_test_2_jin_coarse_mesh",
        "heater_old": "265.7",
        "heater_new": "292.27",
        "heater_patch_old": "88.56666666666666",
        "heater_patch_new": "97.42333333333333",
        "cool_q04_old": "-16.13860204279952",
        "cool_q04_new": "-19.326299487574108",
        "cool_q05_old": "-104.07353581998868",
        "cool_q05_new": "-124.63014557603952",
        "cool_q06_old": "-16.13860204279952",
        "cool_q06_new": "-19.326299487574108",
    },
    {
        "case_key": "salt2_jin_loq_balq",
        "parent_case_dir": REPO_ROOT / "staging/modern_runs/2026-06-01_full_extractable_batch/salt/viscosity_screening_salt_test_2_jin_coarse_mesh",
        "target_case_dir": RUNS_ROOT / "salt2_jin_loq_balq/case_stage/viscosity_screening_salt_test_2_jin_coarse_mesh",
        "heater_old": "265.7",
        "heater_new": "239.13",
        "heater_patch_old": "88.56666666666666",
        "heater_patch_new": "79.71",
        "cool_q04_old": "-16.13860204279952",
        "cool_q04_new": "-13.036599019881805",
        "cool_q05_old": "-104.07353581998868",
        "cool_q05_new": "-84.06954651142411",
        "cool_q06_old": "-16.13860204279952",
        "cool_q06_new": "-13.036599019881805",
    },
    {
        "case_key": "salt3_jin_hiq_balq",
        "parent_case_dir": REPO_ROOT / "staging/modern_runs/2026-06-01_full_extractable_batch/salt/viscosity_screening_salt_test_3_jin_coarse_mesh",
        "target_case_dir": RUNS_ROOT / "salt3_jin_hiq_balq/case_stage/viscosity_screening_salt_test_3_jin_coarse_mesh",
        "heater_old": "297.5",
        "heater_new": "327.25",
        "heater_patch_old": "99.16666666666667",
        "heater_patch_new": "109.08333333333333",
        "cool_q04_old": "-18.095730767834933",
        "cool_q04_new": "-21.783117871182853",
        "cool_q05_old": "-114.57817713779176",
        "cool_q05_new": "-137.92589921232593",
        "cool_q06_old": "-18.095730767834933",
        "cool_q06_new": "-21.783117871182853",
    },
    {
        "case_key": "salt3_jin_loq_balq",
        "parent_case_dir": REPO_ROOT / "staging/modern_runs/2026-06-01_full_extractable_batch/salt/viscosity_screening_salt_test_3_jin_coarse_mesh",
        "target_case_dir": RUNS_ROOT / "salt3_jin_loq_balq/case_stage/viscosity_screening_salt_test_3_jin_coarse_mesh",
        "heater_old": "297.5",
        "heater_new": "267.75",
        "heater_patch_old": "99.16666666666667",
        "heater_patch_new": "89.25",
        "cool_q04_old": "-18.095730767834933",
        "cool_q04_new": "-14.641786299658046",
        "cool_q05_old": "-114.57817713779176",
        "cool_q05_new": "-92.7085623553755",
        "cool_q06_old": "-18.095730767834933",
        "cool_q06_new": "-14.641786299658046",
    },
    {
        "case_key": "salt4_jin_hiq_balq",
        "parent_case_dir": REPO_ROOT / "jadyn_runs/salt4/2026-06-04_jin_continuation_candidate/case_stage/viscosity_screening_salt_test_4_jin_coarse_mesh_continuation",
        "target_case_dir": RUNS_ROOT / "salt4_jin_hiq_balq/case_stage/viscosity_screening_salt_test_4_jin_coarse_mesh_continuation",
        "heater_old": "337.6",
        "heater_new": "371.36",
        "heater_patch_old": "112.53333333333333",
        "heater_patch_new": "123.78666666666666",
        "cool_q04_old": "-20.539119272541168",
        "cool_q04_new": "-24.681782121688833",
        "cool_q05_old": "-128.1485764924187",
        "cool_q05_new": "-153.9956607788434",
        "cool_q06_old": "-20.539119272541168",
        "cool_q06_new": "-24.681782121688833",
    },
    {
        "case_key": "salt4_jin_loq_balq",
        "parent_case_dir": REPO_ROOT / "jadyn_runs/salt4/2026-06-04_jin_continuation_candidate/case_stage/viscosity_screening_salt_test_4_jin_coarse_mesh_continuation",
        "target_case_dir": RUNS_ROOT / "salt4_jin_loq_balq/case_stage/viscosity_screening_salt_test_4_jin_coarse_mesh_continuation",
        "heater_old": "337.6",
        "heater_new": "303.84",
        "heater_patch_old": "112.53333333333333",
        "heater_patch_new": "101.28",
        "cool_q04_old": "-20.539119272541168",
        "cool_q04_new": "-16.48685549038243",
        "cool_q05_old": "-128.1485764924187",
        "cool_q05_new": "-102.86551404145615",
        "cool_q06_old": "-20.539119272541168",
        "cool_q06_new": "-16.48685549038243",
    },
]


def replace_exact(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count == 0:
        raise RuntimeError(f"Expected to find {label!r} value {old!r}")
    return text.replace(old, new)


def stage_case(case: dict[str, str | Path]) -> None:
    parent_case_dir = Path(case["parent_case_dir"])
    target_case_dir = Path(case["target_case_dir"])

    if not parent_case_dir.is_dir():
        raise RuntimeError(f"Missing parent case dir: {parent_case_dir}")

    target_case_dir.parent.mkdir(parents=True, exist_ok=True)
    target_case_dir.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "cp",
            "-a",
            "--reflink=auto",
            str(parent_case_dir) + "/.",
            str(target_case_dir) + "/",
        ],
        check=True,
    )

    case_config = target_case_dir / "case_config.yaml"
    control_dict = target_case_dir / "system/controlDict"
    temp_bc = target_case_dir / "0/T"

    for required in (case_config, control_dict, temp_bc, target_case_dir / "processors64"):
        if not required.exists():
            raise RuntimeError(f"Missing staged requirement: {required}")

    case_config_text = case_config.read_text()
    case_config_text = replace_exact(case_config_text, f"heater_power_W: {case['heater_old']}", f"heater_power_W: {case['heater_new']}", "heater_power_W")
    case_config_text = replace_exact(case_config_text, f"    Q: {case['heater_old']}", f"    Q: {case['heater_new']}", "bc_params.heater.Q")
    case_config.write_text(case_config_text)

    temp_text = temp_bc.read_text()
    temp_text = replace_exact(temp_text, f"Q               constant {case['heater_patch_old']};", f"Q               constant {case['heater_patch_new']};", "heater patch Q")
    temp_text = replace_exact(temp_text, f"Q               constant {case['cool_q04_old']};", f"Q               constant {case['cool_q04_new']};", "cooler reducer 04 Q")
    temp_text = replace_exact(temp_text, f"Q               constant {case['cool_q05_old']};", f"Q               constant {case['cool_q05_new']};", "cooler body Q")
    temp_text = replace_exact(temp_text, f"Q               constant {case['cool_q06_old']};", f"Q               constant {case['cool_q06_new']};", "cooler reducer 06 Q")
    temp_bc.write_text(temp_text)

    control_text = control_dict.read_text()
    control_text = replace_exact(control_text, "purgeWrite      5;", "purgeWrite      21;", "purgeWrite")
    control_dict.write_text(control_text)

    print(f"Staged {case['case_key']} -> {target_case_dir}")


def main() -> None:
    RUNS_ROOT.mkdir(parents=True, exist_ok=True)
    for case in CASES:
        stage_case(case)
    print("Balanced Salt bracket cases staged successfully.")


if __name__ == "__main__":
    main()
