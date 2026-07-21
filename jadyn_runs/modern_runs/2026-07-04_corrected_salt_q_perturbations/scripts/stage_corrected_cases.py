#!/usr/bin/env python3
from __future__ import annotations

import csv
import shutil
import subprocess
from pathlib import Path

ROOT = Path("/scratch/09748/andresfierro231/projects_scratch/ethan_runs")
CAMPAIGN = ROOT / "jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations"
RUNS = CAMPAIGN / "runs"
MANIFEST = CAMPAIGN / "corrected_case_manifest.csv"
PATCH = CAMPAIGN / "scripts/patch_q_fields.py"
WALLTIME = "120:00:00"
ADVANCE = 6000.0

PARENTS = {
    1: ("salt1", ROOT / "jadyn_runs/modern_runs/2026-06-18_convergence_and_jin_envelope_wave/runs/salt1_jin/case_stage/viscosity_screening_salt_test_1_jin_coarse_mesh_continuation", 232.3),
    2: ("salt2", ROOT / "jadyn_runs/modern_runs/2026-06-18_convergence_and_jin_envelope_wave/runs/salt2_jin/case_stage/viscosity_screening_salt_test_2_jin_coarse_mesh_continuation", 265.7),
    3: ("salt3", ROOT / "jadyn_runs/modern_runs/2026-06-18_convergence_and_jin_envelope_wave/runs/salt3_jin/case_stage/viscosity_screening_salt_test_3_jin_coarse_mesh_continuation", 297.5),
    4: ("salt4", ROOT / "jadyn_runs/modern_runs/2026-06-18_convergence_and_jin_envelope_wave/runs/salt4_jin/case_stage/viscosity_screening_salt_test_4_jin_coarse_mesh_continuation", 337.6),
}
RATIOS = {1: [0.90, 1.10], 2: [0.90, 0.95, 1.05, 1.10], 3: [0.90, 0.95, 1.05, 1.10], 4: [0.90, 0.95, 1.05, 1.10]}
LABEL = {0.90: "lo10q", 0.95: "lo5q", 1.05: "hi5q", 1.10: "hi10q"}
COOLER_PATCHES = ["pipeleg_upper_04_reducer", "pipeleg_upper_05_cooler", "pipeleg_upper_06_reducer"]


def latest_time(processors64: Path) -> float:
    vals = [float(p.name) for p in processors64.iterdir() if p.is_dir() and p.name.replace(".", "", 1).isdigit()]
    return max(vals)


def block_q_values(path: Path, patches: list[str]) -> dict[str, float]:
    text = path.read_text(errors="ignore").splitlines()
    out = {}
    for i, line in enumerate(text):
        if line.strip().strip('"') not in patches:
            continue
        patch = line.strip().strip('"')
        for j in range(i, min(i + 60, len(text))):
            stripped = text[j].strip()
            if stripped.startswith("Q") and "constant" in stripped:
                out[patch] = float(stripped.split()[-1].rstrip(";"))
                break
    return out


def stage_case(source: Path, target: Path) -> None:
    if target.exists():
        shutil.rmtree(target)
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
    (target / "SOURCE_PROCESSORS64.txt").write_text(str(source / "processors64") + "\n")


def main() -> int:
    rows = []
    for salt, (salt_key, parent, nominal_q) in PARENTS.items():
        parent_latest = latest_time(parent / "processors64")
        parent_cool = block_q_values(parent / "0/T", COOLER_PATCHES)
        for ratio in RATIOS[salt]:
            case_key = f"salt{salt}_jin_{LABEL[ratio]}_corrected"
            case_dir = RUNS / case_key / "case_stage" / parent.name
            stage_case(parent, case_dir)
            target_q = nominal_q * ratio
            row = {
                "case_key": case_key,
                "salt": str(salt),
                "q_ratio": f"{ratio:.2f}",
                "nominal_heater_power_W": f"{nominal_q:.12g}",
                "target_heater_power_W": f"{target_q:.12g}",
                "parent_case_dir": str(parent),
                "parent_restart_time_s": f"{parent_latest:.12g}",
                "target_end_time_s": f"{parent_latest + ADVANCE:.12g}",
                "walltime": WALLTIME,
                "case_dir": str(case_dir),
                "source_processors64": str(parent / "processors64"),
                "target_cooler_q04_W": f"{parent_cool['pipeleg_upper_04_reducer'] * ratio:.12g}",
                "target_cooler_q05_W": f"{parent_cool['pipeleg_upper_05_cooler'] * ratio:.12g}",
                "target_cooler_q06_W": f"{parent_cool['pipeleg_upper_06_reducer'] * ratio:.12g}",
            }
            rows.append(row)
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    with MANIFEST.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    subprocess.run(["python", str(PATCH), "--manifest", str(MANIFEST), "--audit-out", str(CAMPAIGN / "root_patch_audit.csv")], check=True)
    print(f"Wrote {MANIFEST}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
