#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.common import (  # noqa: E402
    WORKSPACE_ROOT,
    ensure_dir,
    get_registry_row,
    iso_timestamp,
    json_dump,
)

PARAVIEW_EXPORT_BACKEND = {
    "name": "paraview_osmesa_5_13",
    "module_load": "module load gcc/11.2.0 impi/19.0.9 paraview_osmesa/5.13.3",
    "bin_env": "TACC_PARAVIEW_OSMESA_BIN",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Stage a render-ready input for a registered CFD case.")
    parser.add_argument("--source-id", required=True, help="Registered source identifier.")
    parser.add_argument(
        "--format",
        choices=["auto", "foam-mirror", "vtm"],
        default="auto",
        help="Preferred staged format.",
    )
    return parser.parse_args()


def locate_existing_candidate(source_root: Path) -> Path | None:
    top_level = sorted(source_root.glob("*.foam"))
    if top_level:
        return top_level[0]
    recursive = sorted(source_root.rglob("*.foam"))
    if recursive:
        return recursive[0]
    vtk_files = sorted(source_root.rglob("*.vtk"))
    if vtk_files:
        return vtk_files[0]
    return None


def looks_like_openfoam_case(source_root: Path) -> bool:
    return all((source_root / name).exists() for name in ("0", "constant", "system"))


def stage_openfoam_mirror(source_root: Path, source_id: str) -> Path:
    mirror_root = ensure_dir(WORKSPACE_ROOT / "staging" / "render_inputs" / source_id / "foam_case")
    for item in source_root.iterdir():
        target = mirror_root / item.name
        if target.is_symlink():
            if target.resolve() == item.resolve():
                continue
            target.unlink()
        elif target.exists():
            continue
        target.symlink_to(item, target_is_directory=item.is_dir())

    foam_path = mirror_root / f"{source_id}.foam"
    foam_path.write_text("\n", encoding="utf-8")
    return foam_path


def attempt_vtm_export(foam_candidate: Path, source_id: str) -> tuple[bool, Path, str]:
    stage_root = ensure_dir(WORKSPACE_ROOT / "staging" / "render_inputs" / source_id)
    vtm_path = stage_root / f"{source_id}_preview.vtm"
    driver_path = WORKSPACE_ROOT / "tmp" / f"paraview_export_{source_id}.py"
    script = textwrap.dedent(
        f"""
        from paraview.simple import *

        reader = OpenFOAMReader(FileName=r"{foam_candidate}")
        reader.CaseType = "Decomposed Case" if "{(foam_candidate.parent / 'processors64').exists()}" == "True" else "Reconstructed Case"
        reader.MeshRegions = ["internalMesh"]
        reader.CellArrays = []
        reader.PointArrays = []
        reader.UpdatePipeline()
        SaveData(r"{vtm_path}", proxy=reader)
        print("export_attempt_complete")
        """
    ).strip()
    driver_path.write_text(script + "\n", encoding="utf-8")

    command = (
        f"{PARAVIEW_EXPORT_BACKEND['module_load']} >/dev/null 2>&1 && "
        f"${PARAVIEW_EXPORT_BACKEND['bin_env']}/pvpython {driver_path}"
    )
    try:
        result = subprocess.run(
            ["bash", "-lc", command],
            cwd=str(WORKSPACE_ROOT),
            capture_output=True,
            text=True,
        )
    finally:
        driver_path.unlink(missing_ok=True)

    stdout = result.stdout.strip()
    stderr = result.stderr.strip()
    if result.returncode == 0 and vtm_path.exists() and vtm_path.stat().st_size > 0:
        return True, vtm_path, stdout or "VTM export completed."

    reason = stderr or stdout or "ParaView VTM export failed without output."
    return False, vtm_path, reason


def main() -> int:
    args = parse_args()
    registry_path = WORKSPACE_ROOT / "registry" / "case_registry.csv"
    row = get_registry_row(registry_path, args.source_id)
    source_root = Path(row["source_root"]).resolve()
    stage_root = ensure_dir(WORKSPACE_ROOT / "staging" / "render_inputs" / row["source_id"])
    status_path = stage_root / "render_input_status.json"

    status = {
        "generated_at": iso_timestamp(),
        "source_id": row["source_id"],
        "requested_format": args.format,
        "status": "skipped",
        "preferred_candidate_path": "",
        "prepared_foam_path": "",
        "prepared_vtm_path": "",
        "reason": "",
    }

    existing = locate_existing_candidate(source_root)
    if existing is not None:
        status["status"] = "ready"
        status["preferred_candidate_path"] = str(existing)
        status["reason"] = "Using existing case-level render candidate."
        if existing.suffix == ".foam":
            status["prepared_foam_path"] = str(existing)
        elif existing.suffix in {".vtk", ".vtm"}:
            status["prepared_vtm_path"] = str(existing)
        json_dump(status_path, status)
        print(json.dumps(status, indent=2))
        return 0

    if not looks_like_openfoam_case(source_root):
        status["reason"] = "Case does not match the minimal OpenFOAM mirror layout."
        json_dump(status_path, status)
        print(json.dumps(status, indent=2))
        return 0

    foam_candidate = stage_openfoam_mirror(source_root, row["source_id"])
    status["prepared_foam_path"] = str(foam_candidate)
    status["preferred_candidate_path"] = str(foam_candidate)
    status["status"] = "ready"
    status["reason"] = "Prepared local mirrored OpenFOAM entrypoint."

    if args.format in {"auto", "vtm"}:
        exported, vtm_candidate, reason = attempt_vtm_export(foam_candidate, row["source_id"])
        status["prepared_vtm_path"] = str(vtm_candidate)
        if exported:
            status["preferred_candidate_path"] = str(vtm_candidate)
            status["reason"] = "Prepared local mirrored OpenFOAM entrypoint and VTM export."
        elif args.format == "vtm":
            status["status"] = "skipped"
            status["reason"] = reason
        else:
            status["reason"] = (
                "Prepared local mirrored OpenFOAM entrypoint. VTM export was attempted but not promoted: "
                + reason
            )

    json_dump(status_path, status)
    print(json.dumps(status, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
