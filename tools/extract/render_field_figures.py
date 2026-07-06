#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
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

PARAVIEW_BACKENDS = [
    {
        "name": "paraview_osmesa_5_13",
        "module_load": "module load gcc/11.2.0 impi/19.0.9 paraview_osmesa/5.13.3",
        "bin_env": "TACC_PARAVIEW_OSMESA_BIN",
    },
    {
        "name": "paraview_5_13",
        "module_load": "module load gcc/11.2.0 paraview/5.13.3",
        "bin_env": "TACC_PARAVIEW_BIN",
    },
    {
        "name": "paraview_5_10",
        "module_load": "module load intel/19.1.1 swr/21.2.5 qt5/5.14.2 oneapi_rk/2021.4.0 paraview/5.10.0",
        "bin_env": "TACC_PARAVIEW_BIN",
    },
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Attempt a scripted field render for a registered case.")
    parser.add_argument("--source-id", required=True, help="Registered source identifier.")
    parser.add_argument(
        "--backend",
        choices=["auto", "pyvista", "paraview"],
        default="auto",
        help="Rendering backend preference.",
    )
    return parser.parse_args()


def locate_candidate(source_root: Path) -> Path | None:
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


def locate_prepared_candidate(source_id: str) -> Path | None:
    stage_root = WORKSPACE_ROOT / "staging" / "render_inputs" / source_id
    reconstructed_candidate = stage_root / "reconstructed_case" / f"{source_id}.foam"
    if reconstructed_candidate.exists():
        return reconstructed_candidate

    status_path = stage_root / "render_input_status.json"
    if not status_path.exists():
        return None
    with status_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    candidate = payload.get("preferred_candidate_path", "")
    if not candidate:
        return None
    path = Path(candidate)
    return path if path.exists() else None


def looks_like_openfoam_case(source_root: Path) -> bool:
    return all((source_root / name).exists() for name in ("0", "constant", "system"))


def ensure_openfoam_mirror(source_root: Path, source_id: str) -> Path:
    mirror_root = ensure_dir(WORKSPACE_ROOT / "cache" / "paraview_cases" / source_id)
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


def numeric_dir_values(root: Path) -> list[float]:
    values: list[float] = []
    if not root.exists():
        return values
    for item in root.iterdir():
        if not item.is_dir():
            continue
        try:
            values.append(float(item.name))
        except ValueError:
            continue
    return values


def discover_case_times(source_root: Path) -> list[float]:
    candidates = numeric_dir_values(source_root)
    candidates.extend(numeric_dir_values(source_root / "processors64"))
    for processor_dir in sorted(source_root.glob("processor*")):
        candidates.extend(numeric_dir_values(processor_dir))
    return sorted(set(candidates))


def case_type_for_candidate(candidate: Path) -> str:
    case_root = candidate.parent
    if numeric_dir_values(case_root):
        return "Reconstructed Case"
    if (case_root / "processors64").exists() or any(case_root.glob("processor*")):
        return "Decomposed Case"
    return "Reconstructed Case"


def latest_time_for_candidate(candidate: Path) -> float | None:
    times = discover_case_times(candidate.parent)
    return times[-1] if times else None


def write_paraview_driver(
    driver_path: Path,
    candidate: Path,
    screenshot_path: Path,
    metadata_path: Path,
    *,
    case_type: str,
    render_time: float | None,
) -> None:
    lines = [
        "from paraview.simple import *",
        "import json",
        "",
        f'reader = OpenFOAMReader(FileName=r"{candidate}")',
        f'reader.CaseType = "{case_type}"',
        'reader.MeshRegions = ["internalMesh"]',
        "",
        'renderView = CreateView("RenderView")',
        "renderView.ViewSize = [1600, 1200]",
        "renderView.Background = [1.0, 1.0, 1.0]",
        "",
        "display = Show(reader, renderView)",
        'display.Representation = "Surface"',
        "display.DiffuseColor = [0.75, 0.75, 0.75]",
        "display.AmbientColor = [0.75, 0.75, 0.75]",
        "",
        "UpdatePipeline(proxy=reader)",
    ]
    if render_time is not None:
        lines.extend(
            [
                'if hasattr(reader, "ListtimestepsaccordingtocontrolDict"):',
                "    reader.ListtimestepsaccordingtocontrolDict = 0",
                f"UpdatePipeline(time={render_time!r}, proxy=reader)",
            ]
        )
    lines.extend(
        [
            "bounds = [float(value) for value in reader.GetDataInformation().GetBounds()]",
            "xmin, xmax, ymin, ymax, zmin, zmax = bounds",
            "xmid = 0.5 * (xmin + xmax)",
            "ymid = 0.5 * (ymin + ymax)",
            "zmid = 0.5 * (zmin + zmax)",
            "xy_span = max(abs(xmax - xmin), abs(ymax - ymin), 1.0)",
            "z_span = max(abs(zmax - zmin), 1.0)",
            "renderView.CameraParallelProjection = 1",
            "renderView.CameraPosition = [xmid, ymid, zmid - (2.0 * z_span)]",
            "renderView.CameraFocalPoint = [xmid, ymid, zmid]",
            "renderView.CameraViewUp = [0.0, 1.0, 0.0]",
            "renderView.CameraParallelScale = 0.55 * xy_span",
            "",
            "Render(renderView)",
            f'SaveScreenshot(r"{screenshot_path}", renderView)',
            f'with open(r"{metadata_path}", "w", encoding="utf-8") as handle:',
            "    json.dump(",
            "        {",
            '            "bounds": bounds,',
            '            "camera_position": [float(value) for value in renderView.CameraPosition],',
            '            "camera_focal_point": [float(value) for value in renderView.CameraFocalPoint],',
            '            "camera_view_up": [float(value) for value in renderView.CameraViewUp],',
            '            "camera_parallel_scale": float(renderView.CameraParallelScale),',
            "        },",
            "        handle,",
            "        indent=2,",
            "    )",
        ]
    )
    driver_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_pyvista(candidate: Path, figure_root: Path) -> tuple[bool, str, list[str], str, dict[str, object]]:
    try:
        import pyvista as pv  # type: ignore
    except ImportError:
        return False, "PyVista is not installed in the active Python environment.", [], "pyvista_vtk", {}

    try:
        dataset = pv.read(candidate)
        plotter = pv.Plotter(off_screen=True)
        if hasattr(dataset, "outline"):
            plotter.add_mesh(dataset.outline(), color="black")
        else:
            plotter.add_mesh(dataset, color="lightgray")
        plotter.view_isometric()
        screenshot_path = figure_root / "overview.png"
        plotter.screenshot(str(screenshot_path))
        plotter.close()
        return True, "", [str(screenshot_path)], "pyvista_vtk", {}
    except Exception as exc:  # pragma: no cover
        return False, f"PyVista failed to render candidate: {exc}", [], "pyvista_vtk", {}


def run_paraview(candidate: Path, figure_root: Path, source_id: str) -> tuple[bool, str, list[str], str, dict[str, object]]:
    screenshot_path = figure_root / "overview.png"
    driver_path = WORKSPACE_ROOT / "tmp" / f"paraview_render_{source_id}.py"
    metadata_path = WORKSPACE_ROOT / "tmp" / f"paraview_render_{source_id}_camera.json"
    case_type = case_type_for_candidate(candidate)
    render_time = latest_time_for_candidate(candidate)
    write_paraview_driver(
        driver_path,
        candidate,
        screenshot_path,
        metadata_path,
        case_type=case_type,
        render_time=render_time,
    )

    def load_metadata() -> dict[str, object]:
        if not metadata_path.exists():
            return {}
        with metadata_path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def has_valid_bounds(metadata: dict[str, object]) -> bool:
        bounds = metadata.get("bounds")
        if not isinstance(bounds, list) or len(bounds) != 6:
            return False
        try:
            xmin, xmax, ymin, ymax, zmin, zmax = [float(value) for value in bounds]
        except (TypeError, ValueError):
            return False
        return (
            abs(xmin) < 1.0e298
            and abs(xmax) < 1.0e298
            and abs(ymin) < 1.0e298
            and abs(ymax) < 1.0e298
            and abs(zmin) < 1.0e298
            and abs(zmax) < 1.0e298
            and xmin < xmax
            and ymin < ymax
            and zmin <= zmax
        )

    def needs_srun() -> bool:
        return bool(os.environ.get("SLURM_JOB_ID")) and not os.environ.get("SLURM_STEP_ID") and shutil.which("srun")

    def clear_outputs() -> None:
        screenshot_path.unlink(missing_ok=True)
        metadata_path.unlink(missing_ok=True)

    executable_names = ("pvbatch", "pvpython")

    try:
        env_candidates = [
            ("paraview_osmesa_env", os.environ.get("TACC_PARAVIEW_OSMESA_BIN")),
            ("paraview_env", os.environ.get("TACC_PARAVIEW_BIN")),
        ]
        for backend_name, bin_root in env_candidates:
            if not bin_root:
                continue
            for executable_name in executable_names:
                executable_path = Path(bin_root) / executable_name
                if not executable_path.exists():
                    continue
                clear_outputs()
                command = [str(executable_path), str(driver_path)]
                if needs_srun():
                    command = ["srun", "-n", "1", *command]
                result = subprocess.run(
                    command,
                    cwd=str(WORKSPACE_ROOT),
                    capture_output=True,
                    text=True,
                )
                metadata = load_metadata()
                if result.returncode == 0 and screenshot_path.exists() and has_valid_bounds(metadata):
                    return (
                        True,
                        f"Rendered with {backend_name}:{executable_name}.",
                        [str(screenshot_path)],
                        backend_name,
                        metadata,
                    )

        last_error = "No ParaView backend succeeded."
        launcher = "srun -n 1 " if needs_srun() else ""
        for backend in PARAVIEW_BACKENDS:
            for executable_name in executable_names:
                clear_outputs()
                command = (
                    f"{backend['module_load']} >/dev/null 2>&1 && "
                    f"{launcher}${backend['bin_env']}/{executable_name} {driver_path}"
                )
                result = subprocess.run(
                    ["bash", "-lc", command],
                    cwd=str(WORKSPACE_ROOT),
                    capture_output=True,
                    text=True,
                )
                metadata = load_metadata()
                if result.returncode == 0 and screenshot_path.exists() and has_valid_bounds(metadata):
                    return (
                        True,
                        f"Rendered with {backend['name']}:{executable_name}.",
                        [str(screenshot_path)],
                        backend["name"],
                        metadata,
                    )

                stderr = result.stderr.strip()
                stdout = result.stdout.strip()
                if result.returncode == 0 and screenshot_path.exists() and metadata:
                    last_error = "ParaView wrote an overview image but reported invalid dataset bounds."
                else:
                    last_error = stderr or stdout or f"{backend['name']}:{executable_name} failed without output."

        return False, last_error, [], "paraview", {}
    finally:
        driver_path.unlink(missing_ok=True)
        metadata_path.unlink(missing_ok=True)


def explain_failure(source_root: Path, candidate: Path, reason: str) -> str:
    if (source_root / "processors64").exists():
        if "PMI server not found" in reason or "no usable transports/devices" in reason:
            return (
                "ParaView reached the decomposed-case reader but the current node lacks the MPI/runtime "
                "setup needed for processor-partition rendering. Run this under a compatible allocation "
                "or reconstruct a local staging copy before rendering."
            )
        if "OpenFOAMReader" in reason and "representation object" in reason:
            return (
                "ParaView found the mirrored OpenFOAM entrypoint, but this decomposed processor-only case "
                "did not produce a renderable representation in the current runtime. The next likely fixes "
                "are running under a compatible ParaView/MPI allocation or reconstructing a local staging copy."
            )
    if candidate.suffix == ".foam":
        return reason
    return reason


def main() -> int:
    args = parse_args()
    registry_path = WORKSPACE_ROOT / "registry" / "case_registry.csv"
    row = get_registry_row(registry_path, args.source_id)
    source_root = Path(row["source_root"]).resolve()
    figure_root = ensure_dir(WORKSPACE_ROOT / "figures_rendered" / row["source_id"])
    status_path = figure_root / "status.json"

    status = {
        "generated_at": iso_timestamp(),
        "source_id": row["source_id"],
        "backend": args.backend,
        "status": "skipped",
        "reason": "",
        "candidate_path": "",
        "outputs": [],
        "bounds": [],
        "camera_position": [],
        "camera_focal_point": [],
        "camera_view_up": [],
        "camera_parallel_scale": None,
    }

    candidate = locate_prepared_candidate(row["source_id"])
    if candidate is None:
        candidate = locate_candidate(source_root)
    if candidate is None and looks_like_openfoam_case(source_root):
        candidate = ensure_openfoam_mirror(source_root, row["source_id"])

    if candidate is None:
        status["reason"] = (
            "No .foam or .vtk file was found, and the case did not match the "
            "minimal OpenFOAM mirror pattern."
        )
        json_dump(status_path, status)
        print(json.dumps(status, indent=2))
        return 0

    status["candidate_path"] = str(candidate)

    if args.backend in {"auto", "pyvista"}:
        rendered, reason, outputs, backend_name, metadata = run_pyvista(candidate, figure_root)
        if rendered:
            status["status"] = "rendered"
            status["backend"] = backend_name
            status["reason"] = reason
            status["outputs"] = outputs
            status.update(metadata)
        elif args.backend == "pyvista":
            status["reason"] = reason

    if status["status"] != "rendered" and args.backend in {"auto", "paraview"}:
        rendered, reason, outputs, backend_name, metadata = run_paraview(candidate, figure_root, row["source_id"])
        if rendered:
            status["status"] = "rendered"
            status["backend"] = backend_name
            status["reason"] = reason
            status["outputs"] = outputs
            status.update(metadata)
        elif args.backend == "paraview" or not status["reason"]:
            status["reason"] = explain_failure(source_root, candidate, reason)

    json_dump(status_path, status)
    print(json.dumps(status, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
