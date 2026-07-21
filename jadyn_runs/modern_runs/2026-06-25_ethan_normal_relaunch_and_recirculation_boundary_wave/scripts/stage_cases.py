#!/usr/bin/env python3
"""Stage fresh June 25 relaunch and recirculation-boundary cases."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

REPO_ROOT = Path("/scratch/09748/andresfierro231/projects_scratch/ethan_runs")
CAMPAIGN_ROOT = REPO_ROOT / "jadyn_runs/modern_runs/2026-06-25_ethan_normal_relaunch_and_recirculation_boundary_wave"
RUNS_ROOT = CAMPAIGN_ROOT / "runs"
RUNTIME_LIB_ROOT = CAMPAIGN_ROOT / "runtime_libs"
RUNTIME_LIB_SRC = Path("/home1/09748/andresfierro231/bubble_flow_loop/tamu_loop_box/ethan_data/libRCWallBC.so")
WALLTIME = "216:00:00"

CASES = [
    {
        "case_key": "salt1_jin_basecont",
        "source_case_dir": REPO_ROOT / "jadyn_runs/modern_runs/2026-06-18_convergence_and_jin_envelope_wave/runs/salt1_jin/case_stage/viscosity_screening_salt_test_1_jin_coarse_mesh_continuation",
        "target_case_dir": RUNS_ROOT / "salt1_jin_basecont/case_stage/viscosity_screening_salt_test_1_jin_coarse_mesh_continuation",
        "mode": "copy",
    },
    {
        "case_key": "salt1_jin_hiq_balq",
        "source_case_dir": REPO_ROOT / "jadyn_runs/salt1/2026-06-04_jin_continuation_candidate/case_stage/viscosity_screening_salt_test_1_jin_coarse_mesh_continuation",
        "target_case_dir": RUNS_ROOT / "salt1_jin_hiq_balq/case_stage/viscosity_screening_salt_test_1_jin_coarse_mesh_continuation",
        "mode": "heater_only",
        "heater_old": "232.3",
        "heater_new": "255.530",
        "heater_patch_old": "77.43333333333334",
        "heater_patch_new": "85.1766666666666740",
        "cool_q04_old": "-16.22051188331554",
        "cool_q04_new": "-19.05234064309004643171025866",
        "cool_q05_old": "-103.16215407994024",
        "cool_q05_new": "-121.1725323556318440610904590",
        "cool_q06_old": "-16.22051188331554",
        "cool_q06_new": "-19.05234064309004643171025866",
    },
    {
        "case_key": "salt1_jin_loq_balq",
        "source_case_dir": REPO_ROOT / "jadyn_runs/salt1/2026-06-04_jin_continuation_candidate/case_stage/viscosity_screening_salt_test_1_jin_coarse_mesh_continuation",
        "target_case_dir": RUNS_ROOT / "salt1_jin_loq_balq/case_stage/viscosity_screening_salt_test_1_jin_coarse_mesh_continuation",
        "mode": "heater_only",
        "heater_old": "232.3",
        "heater_new": "209.070",
        "heater_patch_old": "77.43333333333334",
        "heater_patch_new": "69.6900000000000060",
        "cool_q04_old": "-16.22051188331554",
        "cool_q04_new": "-13.49491201887661592931242636",
        "cool_q05_old": "-103.16215407994024",
        "cool_q05_new": "-85.82738960405870506588612356",
        "cool_q06_old": "-16.22051188331554",
        "cool_q06_new": "-13.49491201887661592931242636",
    },
    {
        "case_key": "salt2_jin_hi5q_balq",
        "source_case_dir": REPO_ROOT / "staging/modern_runs/2026-06-01_full_extractable_batch/salt/viscosity_screening_salt_test_2_jin_coarse_mesh",
        "target_case_dir": RUNS_ROOT / "salt2_jin_hi5q_balq/case_stage/viscosity_screening_salt_test_2_jin_coarse_mesh",
        "mode": "heater_only",
        "heater_old": "265.7",
        "heater_new": "278.985",
        "heater_patch_old": "88.56666666666666",
        "heater_patch_new": "92.9949999999999930",
        "cool_q04_old": "-16.13860204279952",
        "cool_q04_new": "-17.732450765186814",
        "cool_q05_old": "-104.07353581998868",
        "cool_q05_new": "-114.35184069801410",
        "cool_q06_old": "-16.13860204279952",
        "cool_q06_new": "-17.732450765186814",
    },
    {
        "case_key": "salt2_jin_lo5q_balq",
        "source_case_dir": REPO_ROOT / "staging/modern_runs/2026-06-01_full_extractable_batch/salt/viscosity_screening_salt_test_2_jin_coarse_mesh",
        "target_case_dir": RUNS_ROOT / "salt2_jin_lo5q_balq/case_stage/viscosity_screening_salt_test_2_jin_coarse_mesh",
        "mode": "heater_only",
        "heater_old": "265.7",
        "heater_new": "252.415",
        "heater_patch_old": "88.56666666666666",
        "heater_patch_new": "84.1383333333333270",
        "cool_q04_old": "-16.13860204279952",
        "cool_q04_new": "-14.5876005313406625",
        "cool_q05_old": "-104.07353581998868",
        "cool_q05_new": "-94.071541165706395",
        "cool_q06_old": "-16.13860204279952",
        "cool_q06_new": "-14.5876005313406625",
    },
    {
        "case_key": "salt3_jin_hi5q_balq",
        "source_case_dir": REPO_ROOT / "staging/modern_runs/2026-06-01_full_extractable_batch/salt/viscosity_screening_salt_test_3_jin_coarse_mesh",
        "target_case_dir": RUNS_ROOT / "salt3_jin_hi5q_balq/case_stage/viscosity_screening_salt_test_3_jin_coarse_mesh",
        "mode": "heater_only",
        "heater_old": "297.5",
        "heater_new": "312.375",
        "heater_patch_old": "99.16666666666667",
        "heater_patch_new": "104.1250000000000035",
        "cool_q04_old": "-18.095730767834933",
        "cool_q04_new": "-19.939424319508893",
        "cool_q05_old": "-114.57817713779176",
        "cool_q05_new": "-126.252038175058845",
        "cool_q06_old": "-18.095730767834933",
        "cool_q06_new": "-19.939424319508893",
    },
    {
        "case_key": "salt3_jin_lo5q_balq",
        "source_case_dir": REPO_ROOT / "staging/modern_runs/2026-06-01_full_extractable_batch/salt/viscosity_screening_salt_test_3_jin_coarse_mesh",
        "target_case_dir": RUNS_ROOT / "salt3_jin_lo5q_balq/case_stage/viscosity_screening_salt_test_3_jin_coarse_mesh",
        "mode": "heater_only",
        "heater_old": "297.5",
        "heater_new": "282.625",
        "heater_patch_old": "99.16666666666667",
        "heater_patch_new": "94.2083333333333365",
        "cool_q04_old": "-18.095730767834933",
        "cool_q04_new": "-16.3687585337464895",
        "cool_q05_old": "-114.57817713779176",
        "cool_q05_new": "-103.64336974658363",
        "cool_q06_old": "-18.095730767834933",
        "cool_q06_new": "-16.3687585337464895",
    },
    {
        "case_key": "salt4_jin_hi5q_balq",
        "source_case_dir": REPO_ROOT / "jadyn_runs/salt4/2026-06-04_jin_continuation_candidate/case_stage/viscosity_screening_salt_test_4_jin_coarse_mesh_continuation",
        "target_case_dir": RUNS_ROOT / "salt4_jin_hi5q_balq/case_stage/viscosity_screening_salt_test_4_jin_coarse_mesh_continuation",
        "mode": "heater_only",
        "heater_old": "337.6",
        "heater_new": "354.480",
        "heater_patch_old": "112.53333333333333",
        "heater_patch_new": "118.1599999999999965",
        "cool_q04_old": "-20.539119272541168",
        "cool_q04_new": "-22.6104506971150005",
        "cool_q05_old": "-128.1485764924187",
        "cool_q05_new": "-141.07211863563105",
        "cool_q06_old": "-20.539119272541168",
        "cool_q06_new": "-22.6104506971150005",
    },
    {
        "case_key": "salt4_jin_lo5q_balq",
        "source_case_dir": REPO_ROOT / "jadyn_runs/salt4/2026-06-04_jin_continuation_candidate/case_stage/viscosity_screening_salt_test_4_jin_coarse_mesh_continuation",
        "target_case_dir": RUNS_ROOT / "salt4_jin_lo5q_balq/case_stage/viscosity_screening_salt_test_4_jin_coarse_mesh_continuation",
        "mode": "heater_only",
        "heater_old": "337.6",
        "heater_new": "320.720",
        "heater_patch_old": "112.53333333333333",
        "heater_patch_new": "106.9066666666666635",
        "cool_q04_old": "-20.539119272541168",
        "cool_q04_new": "-18.512987381461799",
        "cool_q05_old": "-128.1485764924187",
        "cool_q05_new": "-115.507045266937425",
        "cool_q06_old": "-20.539119272541168",
        "cool_q06_new": "-18.512987381461799",
    },
]


def replace_exact(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise RuntimeError(f"Expected {label} value {old!r} to exist")
    return text.replace(old, new, 1)


def stage_snapshot(case: dict[str, object]) -> Path:
    source_case_dir = Path(case["source_case_dir"])
    target_case_dir = Path(case["target_case_dir"])
    if not source_case_dir.is_dir():
        raise RuntimeError(f"Missing source case dir: {source_case_dir}")
    if target_case_dir.exists():
        shutil.rmtree(target_case_dir)
    target_case_dir.mkdir(parents=True, exist_ok=True)

    for entry in source_case_dir.iterdir():
        if entry.name in {"processors64", "logs", "postProcessing"}:
            continue
        target_entry = target_case_dir / entry.name
        if entry.is_dir():
            subprocess.run(["cp", "-a", str(entry), str(target_entry)], check=True)
        else:
            shutil.copy2(entry, target_entry)

    (target_case_dir / "logs").mkdir(parents=True, exist_ok=True)
    (target_case_dir / "SOURCE_PROCESSORS64.txt").write_text(str(source_case_dir / "processors64") + "\n")
    return target_case_dir


def validate(target_case_dir: Path, case_key: str) -> None:
    required = [
        target_case_dir / "0",
        target_case_dir / "constant",
        target_case_dir / "system",
        target_case_dir / "system/controlDict",
        target_case_dir / "logs",
        target_case_dir / "SOURCE_PROCESSORS64.txt",
    ]
    for path in required:
        if not path.exists():
            raise RuntimeError(f"[{case_key}] missing required staged path: {path}")


def normalize_control_dict(control_dict: Path) -> None:
    text = control_dict.read_text()
    if "purgeWrite      5;" in text:
        text = text.replace("purgeWrite      5;", "purgeWrite      21;")
    elif "purgeWrite      21;" not in text:
        raise RuntimeError(f"Unsupported purgeWrite block in {control_dict}")
    control_dict.write_text(text)


def normalize_walltime(case_config: Path) -> None:
    if not case_config.exists():
        return
    text = case_config.read_text()
    if "walltime:" in text:
        import re
        text, count = re.subn(r"walltime:\s*'[^']+'", f"walltime: '{WALLTIME}'", text)
        if count == 0:
            raise RuntimeError(f"Failed to normalize walltime in {case_config}")
        case_config.write_text(text)


def mutate_heater_only(case: dict[str, object], target_case_dir: Path) -> None:
    case_config = target_case_dir / "case_config.yaml"
    temp_bc = target_case_dir / "0/T"
    control_dict = target_case_dir / "system/controlDict"

    case_config_text = case_config.read_text()
    case_config_text = replace_exact(case_config_text, f"heater_power_W: {case['heater_old']}", f"heater_power_W: {case['heater_new']}", "heater_power_W")
    case_config_text = replace_exact(case_config_text, f"    Q: {case['heater_old']}", f"    Q: {case['heater_new']}", "bc_params.heater.Q")
    case_config.write_text(case_config_text)

    temp_text = temp_bc.read_text()
    temp_text = replace_exact(temp_text, f"Q               constant {case['heater_patch_old']};", f"Q               constant {case['heater_patch_new']};", "heater patch Q")
    temp_text = replace_exact(temp_text, f"Q               constant {case['cool_q04_old']};", f"Q               constant {case['cool_q04_new']};", "cool q04")
    temp_text = replace_exact(temp_text, f"Q               constant {case['cool_q05_old']};", f"Q               constant {case['cool_q05_new']};", "cool q05")
    temp_text = replace_exact(temp_text, f"Q               constant {case['cool_q06_old']};", f"Q               constant {case['cool_q06_new']};", "cool q06")
    temp_bc.write_text(temp_text)

    normalize_control_dict(control_dict)
    normalize_walltime(case_config)


def main() -> None:
    if not RUNTIME_LIB_SRC.is_file():
        raise RuntimeError(f"Missing runtime library source: {RUNTIME_LIB_SRC}")
    RUNTIME_LIB_ROOT.mkdir(parents=True, exist_ok=True)
    shutil.copy2(RUNTIME_LIB_SRC, RUNTIME_LIB_ROOT / "libRCWallBC.so")

    for case in CASES:
        target_case_dir = stage_snapshot(case)
        validate(target_case_dir, str(case["case_key"]))
        normalize_control_dict(target_case_dir / "system/controlDict")
        normalize_walltime(target_case_dir / "case_config.yaml")
        if case["mode"] == "heater_only":
            mutate_heater_only(case, target_case_dir)
        print(f"staged {case['case_key']} -> {target_case_dir}", flush=True)

    print(f"runtime lib copied to {RUNTIME_LIB_ROOT / 'libRCWallBC.so'}", flush=True)


if __name__ == "__main__":
    main()
