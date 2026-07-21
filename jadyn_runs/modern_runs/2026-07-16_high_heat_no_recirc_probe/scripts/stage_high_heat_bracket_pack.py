#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import re
import shutil
import subprocess
from pathlib import Path


ROOT = Path("/scratch/09748/andresfierro231/projects_scratch/ethan_runs")
CAMPAIGN = ROOT / "jadyn_runs/modern_runs/2026-07-16_high_heat_no_recirc_probe"
RUNS = CAMPAIGN / "runs"
WORK_PRODUCT = ROOT / "work_products/2026-07/2026-07-16/2026-07-16_high_heat_no_recirc_probe"
MANIFEST = CAMPAIGN / "high_heat_bracket_pack_manifest.csv"
PATCH = ROOT / "jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations/scripts/patch_q_fields.py"

SOURCE_ID = "viscosity_screening_salt_test_4_jin_coarse_mesh_continuation"
PARENT = (
    ROOT
    / "jadyn_runs/modern_runs/2026-06-18_convergence_and_jin_envelope_wave"
    / "runs/salt4_jin/case_stage"
    / SOURCE_ID
)
NOMINAL_HEATER_POWER_W = 337.6
TARGET_HEATER_POWERS_W = [500.0, 1000.0, 1500.0]
ADVANCE_S = 12000.0
WALLTIME = "120:00:00"

COOLER_PATCHES = [
    "pipeleg_upper_04_reducer",
    "pipeleg_upper_05_cooler",
    "pipeleg_upper_06_reducer",
]


def latest_time(processors64: Path) -> float:
    vals = []
    for child in processors64.iterdir():
        if child.is_dir():
            try:
                vals.append(float(child.name))
            except ValueError:
                pass
    if not vals:
        raise RuntimeError(f"No numeric processor times under {processors64}")
    return max(vals)


def block_q_values(path: Path, patches: list[str]) -> dict[str, float]:
    text = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    out: dict[str, float] = {}
    for i, line in enumerate(text):
        patch = line.strip().strip('"')
        if patch not in patches:
            continue
        for j in range(i, min(i + 60, len(text))):
            stripped = text[j].strip()
            if stripped.startswith("Q") and "constant" in stripped:
                out[patch] = float(stripped.split()[-1].rstrip(";"))
                break
    missing = sorted(set(patches) - set(out))
    if missing:
        raise RuntimeError(f"Missing Q values in {path}: {missing}")
    return out


def stage_case(source: Path, target: Path) -> None:
    if target.exists():
        raise FileExistsError(f"Refusing to replace existing staged case: {target}")
    target.mkdir(parents=True)
    for name in ["0", "constant", "system", "case_config.yaml", "dynamicCode"]:
        src = source / name
        if not src.exists():
            continue
        dst = target / name
        if src.is_dir():
            subprocess.run(["cp", "-a", str(src), str(dst)], check=True)
        else:
            shutil.copy2(src, dst)
    (target / "logs").mkdir()
    (target / "SOURCE_PROCESSORS64.txt").write_text(str(source / "processors64") + "\n", encoding="utf-8")


def force_runtime_controls(case_dir: Path, restart_time: float, end_time: float) -> None:
    path = case_dir / "system/controlDict"
    text = path.read_text(encoding="utf-8")
    replacements = {
        "startFrom": "startTime",
        "startTime": f"{restart_time:.12g}",
        "endTime": f"{end_time:.12g}",
        "timeFormat": "general",
        "timePrecision": "6",
        "purgeWrite": "21",
    }
    for key, value in replacements.items():
        text = re.sub(rf"(?m)^(\s*{key}\s+)\S+(\s*;)", rf"\g<1>{value}\2", text, count=1)
    path.write_text(text, encoding="utf-8")


def disable_weak_write_now_monitor(case_dir: Path) -> None:
    path = case_dir / "system/functions"
    text = path.read_text(encoding="utf-8")
    text = re.sub(
        r"\s*const_cast<Time&>\(mesh\(\)\.time\(\)\)\.stopAt\(\s*Time::stopAtControl::writeNow\);",
        "\n            // AGENT-475: keep convergenceMonitor diagnostic-only for high-heat bracket runs.",
        text,
        count=1,
        flags=re.DOTALL,
    )
    path.write_text(text, encoding="utf-8")


def update_case_config_cooling(case_dir: Path, total_cooling_power_w: float) -> None:
    path = case_dir / "case_config.yaml"
    text = path.read_text(encoding="utf-8")
    text = re.sub(
        r"(?m)^(\s*cooling_power_W:\s*)[-+0-9.eE]+",
        rf"\g<1>{total_cooling_power_w:.12g}",
        text,
        count=1,
    )
    path.write_text(text, encoding="utf-8")


def write_rows(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parent_latest = latest_time(PARENT / "processors64")
    end_time = parent_latest + ADVANCE_S
    parent_cooler = block_q_values(PARENT / "0/T", COOLER_PATCHES)
    rows: list[dict[str, str]] = []

    for target_heater_power in TARGET_HEATER_POWERS_W:
        label = f"q{int(target_heater_power):04d}w"
        case_key = f"salt4_jin_{label}_no_recirc_probe"
        display_name = f"salt4_{label}_no_recirc_probe"
        ratio = target_heater_power / NOMINAL_HEATER_POWER_W
        case_dir = RUNS / case_key / "case_stage" / SOURCE_ID
        stage_case(PARENT, case_dir)
        target_cooler = {patch: value * ratio for patch, value in parent_cooler.items()}

        row = {
            "case_key": case_key,
            "display_name": display_name,
            "salt": "4",
            "q_ratio": f"{ratio:.12g}",
            "nominal_heater_power_W": f"{NOMINAL_HEATER_POWER_W:.12g}",
            "target_heater_power_W": f"{target_heater_power:.12g}",
            "target_heater_patch_Q_W": f"{target_heater_power / 3.0:.12g}",
            "parent_case_dir": str(PARENT),
            "parent_restart_time_s": f"{parent_latest:.12g}",
            "target_end_time_s": f"{end_time:.12g}",
            "walltime": WALLTIME,
            "case_dir": str(case_dir),
            "source_processors64": str(PARENT / "processors64"),
            "target_cooler_q04_W": f"{target_cooler['pipeleg_upper_04_reducer']:.12g}",
            "target_cooler_q05_W": f"{target_cooler['pipeleg_upper_05_cooler']:.12g}",
            "target_cooler_q06_W": f"{target_cooler['pipeleg_upper_06_reducer']:.12g}",
            "cooler_scaling_policy": "parent_salt4_cooler_patch_Q_times_target_heater_power_over_337.6W",
            "prediction_class": "high_heat_bracket_not_admitted_no_recirc_prediction",
        }
        rows.append(row)

    write_rows(MANIFEST, rows)
    subprocess.run(
        [
            "/usr/bin/python3.11",
            str(PATCH),
            "--manifest",
            str(MANIFEST),
            "--audit-out",
            str(CAMPAIGN / "bracket_pack_root_patch_audit.csv"),
        ],
        check=True,
    )

    for row in rows:
        case_dir = Path(row["case_dir"])
        force_runtime_controls(case_dir, parent_latest, end_time)
        disable_weak_write_now_monitor(case_dir)
        update_case_config_cooling(
            case_dir,
            abs(
                float(row["target_cooler_q04_W"])
                + float(row["target_cooler_q05_W"])
                + float(row["target_cooler_q06_W"])
            ),
        )

    WORK_PRODUCT.mkdir(parents=True, exist_ok=True)
    write_rows(WORK_PRODUCT / "heat_input_bracket_pack.csv", rows)
    (WORK_PRODUCT / "bracket_pack_summary.json").write_text(
        json.dumps(
            {
                "task": "AGENT-475",
                "case_count": len(rows),
                "case_keys": [row["case_key"] for row in rows],
                "target_heater_powers_W": TARGET_HEATER_POWERS_W,
                "cooler_policy": "scale three fixed cooler/sink Q patches by target/337.6",
                "runtime_policy": "explicit integer restart, general timeFormat, timePrecision 6, diagnostic-only convergenceMonitor",
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {MANIFEST}")
    for row in rows:
        print(f"Staged {row['case_key']} -> {row['case_dir']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
