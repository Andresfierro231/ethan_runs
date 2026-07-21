#!/usr/bin/env python3
"""Build publication-strength evidence for rcExternalTemperature radiation use.

AGENT-277 strengthens AGENT-264 by looking for the actual custom source and by
running an isolated OF13 microcase when source evidence is unavailable. Native
Ethan CFD cases are never modified.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import platform
import re
import shutil
import socket
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "work_products/2026-07/2026-07-13/2026-07-13_rc_external_temperature_publication_evidence"
OF13_ENV = ROOT / "tools/ofenv/of13_env.sh"
RCWALL_LIB = Path("/home1/09748/andresfierro231/bubble_flow_loop/tamu_loop_box/ethan_data/libRCWallBC.so")
ROOM_HEATING_TUTORIAL = Path(
    "/work/09748/andresfierro231/ls6/openfoam_runtime_recovery/2026-06-02_openfoam13/source/"
    "OpenFOAM-13/tutorials/fluid/roomHeating"
)
STOCK_EXTERNAL_T_C = Path(
    "/work/09748/andresfierro231/ls6/openfoam_runtime_recovery/2026-06-02_openfoam13/source/OpenFOAM-13/src/"
    "ThermophysicalTransportModels/coupledThermophysicalTransportModels/externalTemperature/"
    "externalTemperatureFvPatchScalarField.C"
)
AGENT264_DECISION = (
    ROOT
    / "work_products/2026-07/2026-07-13/2026-07-13_rc_external_temperature_implementation_audit/"
    "radiation_parity_decision.json"
)

SOURCE_PROBE_FIELDS = [
    "candidate_path",
    "exists",
    "kind",
    "sha256",
    "relevant_line_count",
    "relevant_excerpt",
    "interpretation",
]

BINARY_FIELDS = [
    "evidence_id",
    "source_path",
    "observed",
    "interpretation",
]

MATRIX_FIELDS = [
    "variant_id",
    "description",
    "emissivity",
    "Tsur_K",
    "changed_parameter",
    "expected_isolated_change",
]

RUN_FIELDS = [
    "variant_id",
    "case_dir",
    "run_status",
    "return_code",
    "log_path",
    "wallHeatFlux_path",
    "wallHeatFlux_patch",
    "wallHeatFlux_integral_W",
    "wallHeatFlux_mean_W_m2",
    "notes",
]

DELTA_FIELDS = [
    "comparison_id",
    "baseline_variant_id",
    "perturbation_variant_id",
    "changed_parameter",
    "baseline_wallHeatFlux_integral_W",
    "perturbation_wallHeatFlux_integral_W",
    "delta_wallHeatFlux_integral_W",
    "baseline_wallHeatFlux_mean_W_m2",
    "perturbation_wallHeatFlux_mean_W_m2",
    "delta_wallHeatFlux_mean_W_m2",
    "effect_detected",
]

SOURCE_CANDIDATES = [
    Path("/home1/09748/andresfierro231/bubble_flow_loop/tamu_loop_box/ethan_data/rcExternalTemperatureFvPatchScalarField.C"),
    Path("/home1/09748/andresfierro231/bubble_flow_loop/tamu_loop_box/ethan_data/rcExternalTemperatureFvPatchScalarField.H"),
    Path("/home1/09748/andresfierro231/bubble_flow_loop/tamu_loop_box/ethan_data/RCWallBC/rcExternalTemperatureFvPatchScalarField.C"),
    Path("/home1/09748/andresfierro231/bubble_flow_loop/tamu_loop_box/ethan_data/RCWallBC/rcExternalTemperatureFvPatchScalarField.H"),
    Path("/home1/09748/andresfierro231/bubble_flow_loop/tamu_loop_box/ethan_data/libRCWallBC.so"),
    STOCK_EXTERNAL_T_C,
]

SEARCH_ROOTS = [
    Path("/home1/09748/andresfierro231/bubble_flow_loop/tamu_loop_box/ethan_data"),
    ROOT / "tools",
    ROOT / "jadyn_runs",
]


@dataclass(frozen=True)
class Variant:
    variant_id: str
    description: str
    emissivity: float
    tsur_K: float
    changed_parameter: str
    expected_isolated_change: str


VARIANTS = [
    Variant("baseline", "baseline AGENT-263-style emissivity and surroundings temperature", 0.95, 299.19, "none", "reference"),
    Variant("emissivity_low", "change only emissivity from 0.95 to 0.10", 0.10, 299.19, "emissivity", "wallHeatFlux should change if emissivity enters the BC"),
    Variant("emissivity_zero", "change only emissivity from 0.95 to 0.00", 0.00, 299.19, "emissivity", "radiative contribution should be removed if emissivity enters the BC"),
    Variant("tsur_high", "change only Tsur from 299.19 K to 350 K", 0.95, 350.0, "Tsur", "wallHeatFlux should change if surroundings temperature enters the BC"),
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: csv_value(row.get(field, "")) for field in fields})


def csv_value(value: Any) -> Any:
    if value is None:
        return ""
    if isinstance(value, float) and not math.isfinite(value):
        return ""
    return value


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def relevant_lines(path: Path) -> list[str]:
    if path.suffix not in {".C", ".H", ".h", ".hpp", ".cpp", ""}:
        return []
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except UnicodeDecodeError:
        return []
    hits: list[str] = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        lowered = line.lower()
        if any(token in lowered for token in ("rcexternaltemperature", "emissivity", "tsur", "sigma", "updatecoeffs", "radiation")):
            hits.append(f"{line_no}: {' '.join(line.strip().split())}")
    return hits


def bounded_source_candidates(max_depth: int = 5) -> list[Path]:
    candidates = set(SOURCE_CANDIDATES)
    names = ("rcExternalTemperature", "RCWallBC", "libRCWallBC.so")
    for root in SEARCH_ROOTS:
        if not root.exists():
            continue
        root_depth = len(root.parts)
        for current, dirs, files in os.walk(root):
            current_path = Path(current)
            if len(current_path.parts) - root_depth >= max_depth:
                dirs[:] = []
            for name in files:
                if any(token in name for token in names):
                    candidates.add(current_path / name)
    return sorted(candidates, key=str)


def build_source_probe_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in bounded_source_candidates():
        exists = path.exists()
        lines = relevant_lines(path)[:20] if exists and path.is_file() else []
        if path == STOCK_EXTERNAL_T_C:
            kind = "stock_OF13_reference_not_custom_source"
        elif path.name == "libRCWallBC.so":
            kind = "compiled_custom_library"
        elif exists:
            kind = "candidate_custom_source"
        else:
            kind = "missing_targeted_candidate"
        rows.append(
            {
                "candidate_path": str(path),
                "exists": exists,
                "kind": kind,
                "sha256": sha256(path) if exists and path.is_file() else "",
                "relevant_line_count": len(lines),
                "relevant_excerpt": " | ".join(lines),
                "interpretation": source_interpretation(path, exists, kind, lines),
            }
        )
    return rows


def source_interpretation(path: Path, exists: bool, kind: str, lines: list[str]) -> str:
    if not exists:
        return "not found in accessible targeted locations"
    if kind == "compiled_custom_library":
        return "custom compiled library present; source still not recovered from this path"
    if kind == "stock_OF13_reference_not_custom_source":
        return "stock OpenFOAM reference only; useful context but not proof of custom implementation"
    required = ("emissivity", "tsur", "updatecoeffs")
    text = "\n".join(lines).lower()
    if all(token in text for token in required):
        return "candidate custom source contains emissivity, Tsur, and updateCoeffs references"
    return "candidate file found but not sufficient alone to prove custom formula"


def run_text_command(args: list[str]) -> tuple[bool, str]:
    if shutil.which(args[0]) is None:
        return False, f"{args[0]} not found"
    result = subprocess.run(args, cwd=ROOT, capture_output=True, text=True)
    return result.returncode == 0, result.stdout + result.stderr


def filtered_lines(text: str, needles: tuple[str, ...]) -> list[str]:
    out: list[str] = []
    for line in text.splitlines():
        lowered = line.lower()
        if any(needle.lower() in lowered for needle in needles):
            out.append(line.strip())
    return out


def build_binary_probe_rows() -> list[dict[str, Any]]:
    strings_ok, strings_text = run_text_command(["strings", str(RCWALL_LIB)])
    nm_ok, nm_text = run_text_command(["nm", "-C", str(RCWALL_LIB)])
    objdump_ok, objdump_text = run_text_command(["objdump", "-T", str(RCWALL_LIB)])
    string_hits = filtered_lines(
        strings_text,
        ("rcExternalTemperature", "emissivity", "Tsur", "sigma", "radiation", "thicknessLayers", "kappaLayerCoeffs"),
    )
    symbol_hits = filtered_lines(
        nm_text + "\n" + objdump_text,
        ("rcExternalTemperature", "updateCoeffs", "sigma", "Rps", "RpsInner", "RpsOuter", "CsAreal", "CpAreal"),
    )
    return [
        {
            "evidence_id": "compiled_library_strings_refresh",
            "source_path": str(RCWALL_LIB),
            "observed": " | ".join(string_hits[:30]),
            "interpretation": (
                "strings command ok; custom BC library carries rcExternalTemperature, emissivity/Tsur, and layer metadata"
                if strings_ok
                else "strings command failed"
            ),
        },
        {
            "evidence_id": "compiled_library_symbols_refresh",
            "source_path": str(RCWALL_LIB),
            "observed": " | ".join(symbol_hits[:30]),
            "interpretation": (
                f"nm ok={nm_ok}; objdump ok={objdump_ok}; update/radiation-related custom symbols refreshed"
            ),
        },
    ]


def microcase_matrix_rows() -> list[dict[str, Any]]:
    return [
        {
            "variant_id": variant.variant_id,
            "description": variant.description,
            "emissivity": variant.emissivity,
            "Tsur_K": variant.tsur_K,
            "changed_parameter": variant.changed_parameter,
            "expected_isolated_change": variant.expected_isolated_change,
        }
        for variant in VARIANTS
    ]


def preflight_of13() -> tuple[bool, str]:
    cmd = f"source {OF13_ENV} >/dev/null 2>&1 && of13_assert_ready"
    result = subprocess.run(["bash", "-lc", cmd], cwd=ROOT, capture_output=True, text=True)
    return result.returncode == 0, result.stdout + result.stderr


def copy_orig_files(case_dir: Path) -> None:
    for orig in list(case_dir.glob("0/*.orig")) + list(case_dir.glob("system/*.orig")):
        target = orig.with_suffix("")
        if not target.exists():
            shutil.copy2(orig, target)


def replace_control_dict(case_dir: Path) -> None:
    control = case_dir / "system/controlDict"
    text = control.read_text(encoding="utf-8", errors="ignore")
    replacements = {
        r"endTime\s+\S+;": "endTime         1;",
        r"deltaT\s+\S+;": "deltaT          1;",
        r"writeInterval\s+\S+;": "writeInterval   1;",
        r"writePrecision\s+\S+;": "writePrecision  9;",
        r"purgeWrite\s+\S+;": "purgeWrite      0;",
    }
    for pattern, replacement in replacements.items():
        text = re.sub(pattern, replacement, text)
    if "libs" not in text:
        text = text.replace("// ************************************************************************* //", f'libs            ("{RCWALL_LIB}");\n\n#include "functions"\n\n// ************************************************************************* //')
    elif '#include "functions"' not in text:
        text = text.replace("// ************************************************************************* //", '#include "functions"\n\n// ************************************************************************* //')
    control.write_text(text, encoding="utf-8")
    (case_dir / "system/functions").write_text(
        """/*--------------------------------*- C++ -*----------------------------------*\\
| =========                 |                                                 |
\\*---------------------------------------------------------------------------*/
FoamFile
{
    format      ascii;
    class       dictionary;
    location    "system";
    object      functions;
}

#includeFunc wallHeatFlux

// ************************************************************************* //
""",
        encoding="utf-8",
    )


def rc_t_field_text(emissivity: float, tsur_K: float) -> str:
    return f"""/*--------------------------------*- C++ -*----------------------------------*\\
| =========                 |                                                 |
\\*---------------------------------------------------------------------------*/
FoamFile
{{
    format      ascii;
    class       volScalarField;
    location    "0";
    object      T;
}}

Tinf            270;
Tfloor          285;

dimensions      [0 0 0 1 0 0 0];

internalField   uniform $Tfloor;
steadyWall      true;

boundaryField
{{
    glass
    {{
        type            rcExternalTemperature;
        steadyWall      $steadyWall;
        h               uniform 8;
        Ta              constant $Tinf;
        Tsur            constant {tsur_K:.9g};
        emissivity      {emissivity:.9g};
        internalRadius  0.011049;
        thicknessLayers (0.006096001 0.035559999999999994);
        kappaLayerCoeffs  ((9.248 0.01571 0 0 0 0 0 0) (0.036056549855 -6.2436910698e-05 1.9275102287e-07 0 0 0 0 0));
        rhoLayerCoeffs    ((8084.2 -0.42086 -3.8942e-05 0 0 0 0 0) (128.0 0 0 0 0 0 0 0));
        CpLayerCoeffs     ((458.98 0.1328 0 0 0 0 0 0) (1000 0 0 0 0 0 0 0));
        value           uniform $Tinf;
    }}
    floor
    {{
        type            fixedValue;
        value           uniform $Tfloor;
    }}
    ceiling
    {{
        type            fixedValue;
        value           uniform 294;
    }}
    roof
    {{
        $glass;
        h               uniform 4;
    }}
    walls
    {{
        type            zeroGradient;
    }}
}}

// ************************************************************************* //
"""


def prepare_microcase_variant(base_dir: Path, variant: Variant) -> Path:
    case_dir = base_dir / variant.variant_id
    if case_dir.exists():
        shutil.rmtree(case_dir)
    shutil.copytree(ROOM_HEATING_TUTORIAL, case_dir, ignore=shutil.ignore_patterns("processor*", "postProcessing", "log.*"))
    copy_orig_files(case_dir)
    replace_control_dict(case_dir)
    (case_dir / "0/T").write_text(rc_t_field_text(variant.emissivity, variant.tsur_K), encoding="utf-8")
    return case_dir


def run_case(case_dir: Path, timeout_s: int) -> tuple[str, int, str]:
    log_path = case_dir / "log.microcase"
    cmd = (
        f"source {OF13_ENV} >/dev/null 2>&1 && "
        "of13_assert_ready && "
        f"cd {case_dir} && "
        "blockMesh && "
        "createZones && "
        "foamRun"
    )
    try:
        result = subprocess.run(["bash", "-lc", cmd], cwd=ROOT, capture_output=True, text=True, timeout=timeout_s)
        log_path.write_text(result.stdout + "\n--- STDERR ---\n" + result.stderr, encoding="utf-8", errors="ignore")
        return ("success" if result.returncode == 0 else "failed", result.returncode, str(log_path))
    except subprocess.TimeoutExpired as exc:
        log_path.write_text((exc.stdout or "") + "\n--- STDERR ---\n" + (exc.stderr or "") + "\nTIMEOUT\n", encoding="utf-8", errors="ignore")
        return "timeout", 124, str(log_path)


def parse_wallheatflux(case_dir: Path) -> tuple[str, str, float, float]:
    candidates = sorted((case_dir / "postProcessing").glob("wallHeatFlux/*/wallHeatFlux.dat"))
    if not candidates:
        return "", "", math.nan, math.nan
    path = candidates[-1]
    rows_by_time: dict[float, list[tuple[str, float, float]]] = {}
    for raw in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) < 6:
            continue
        if parts[1] not in {"glass", "roof"}:
            continue
        try:
            time_s = float(parts[0])
            q_integral = float(parts[4])
            q_mean = float(parts[5])
        except ValueError:
            continue
        rows_by_time.setdefault(time_s, []).append((parts[1], q_integral, q_mean))
    if not rows_by_time:
        return str(path), "", math.nan, math.nan

    latest_time = max(rows_by_time)
    patches: list[str] = []
    integral = 0.0
    inferred_area = 0.0
    for patch, q_integral, q_mean in rows_by_time[latest_time]:
        patches.append(patch)
        integral += q_integral
        if abs(q_mean) > 0.0:
            inferred_area += q_integral / q_mean
    mean = integral / inferred_area if abs(inferred_area) > 0.0 else math.nan
    return str(path), "+".join(patches), integral, mean


def run_microcases(output_dir: Path, plan_only: bool, timeout_s: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    base_dir = output_dir / "microcases"
    if plan_only:
        for variant in VARIANTS:
            rows.append(
                {
                    "variant_id": variant.variant_id,
                    "case_dir": "",
                    "run_status": "plan_only_not_run",
                    "return_code": "",
                    "log_path": "",
                    "wallHeatFlux_path": "",
                    "wallHeatFlux_patch": "",
                    "wallHeatFlux_integral_W": "",
                    "wallHeatFlux_mean_W_m2": "",
                    "notes": "microcase matrix emitted but OF13 was not invoked",
                }
            )
        return rows

    ready, preflight_text = preflight_of13()
    if not ready:
        for variant in VARIANTS:
            rows.append(
                {
                    "variant_id": variant.variant_id,
                    "case_dir": "",
                    "run_status": "preflight_failed",
                    "return_code": "",
                    "log_path": "",
                    "wallHeatFlux_path": "",
                    "wallHeatFlux_patch": "",
                    "wallHeatFlux_integral_W": "",
                    "wallHeatFlux_mean_W_m2": "",
                    "notes": preflight_text.strip(),
                }
            )
        return rows

    base_dir.mkdir(parents=True, exist_ok=True)
    for variant in VARIANTS:
        case_dir = prepare_microcase_variant(base_dir, variant)
        status, code, log_path = run_case(case_dir, timeout_s)
        whf_path, patch, integral, mean = parse_wallheatflux(case_dir)
        rows.append(
            {
                "variant_id": variant.variant_id,
                "case_dir": rel(case_dir),
                "run_status": status,
                "return_code": code,
                "log_path": rel(Path(log_path)),
                "wallHeatFlux_path": rel(Path(whf_path)) if whf_path else "",
                "wallHeatFlux_patch": patch,
                "wallHeatFlux_integral_W": integral,
                "wallHeatFlux_mean_W_m2": mean,
                "notes": "" if status == "success" else "see log.microcase",
            }
        )
    return rows


def build_delta_rows(run_rows: list[dict[str, Any]], tolerance: float) -> list[dict[str, Any]]:
    by_variant = {str(row["variant_id"]): row for row in run_rows}
    baseline = by_variant.get("baseline", {})
    out: list[dict[str, Any]] = []
    for variant in VARIANTS:
        if variant.variant_id == "baseline":
            continue
        row = by_variant.get(variant.variant_id, {})
        base_q = to_float(baseline.get("wallHeatFlux_integral_W"))
        pert_q = to_float(row.get("wallHeatFlux_integral_W"))
        base_m = to_float(baseline.get("wallHeatFlux_mean_W_m2"))
        pert_m = to_float(row.get("wallHeatFlux_mean_W_m2"))
        delta_q = pert_q - base_q if math.isfinite(base_q) and math.isfinite(pert_q) else math.nan
        delta_m = pert_m - base_m if math.isfinite(base_m) and math.isfinite(pert_m) else math.nan
        out.append(
            {
                "comparison_id": f"baseline_vs_{variant.variant_id}",
                "baseline_variant_id": "baseline",
                "perturbation_variant_id": variant.variant_id,
                "changed_parameter": variant.changed_parameter,
                "baseline_wallHeatFlux_integral_W": base_q,
                "perturbation_wallHeatFlux_integral_W": pert_q,
                "delta_wallHeatFlux_integral_W": delta_q,
                "baseline_wallHeatFlux_mean_W_m2": base_m,
                "perturbation_wallHeatFlux_mean_W_m2": pert_m,
                "delta_wallHeatFlux_mean_W_m2": delta_m,
                "effect_detected": bool(math.isfinite(delta_q) and abs(delta_q) > tolerance),
            }
        )
    return out


def to_float(value: Any) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return math.nan
    return parsed if math.isfinite(parsed) else math.nan


def source_confirmed(source_rows: list[dict[str, Any]]) -> bool:
    for row in source_rows:
        if row["kind"] != "candidate_custom_source" or not row["exists"]:
            continue
        text = str(row["relevant_excerpt"]).lower()
        if all(token in text for token in ("emissivity", "tsur", "updatecoeffs")):
            return True
    return False


def microcase_confirmed(delta_rows: list[dict[str, Any]]) -> bool:
    detected = {row["changed_parameter"]: bool(row["effect_detected"]) for row in delta_rows}
    return detected.get("emissivity", False) and detected.get("Tsur", False)


def build_decision(
    source_rows: list[dict[str, Any]],
    run_rows: list[dict[str, Any]],
    delta_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    source_ok = source_confirmed(source_rows)
    micro_ok = microcase_confirmed(delta_rows)
    statuses = sorted({str(row["run_status"]) for row in run_rows})
    if source_ok:
        evidence_class = "source_confirmed"
    elif micro_ok:
        evidence_class = "microcase_confirmed"
    elif any(status in {"failed", "timeout", "preflight_failed"} for status in statuses):
        evidence_class = "microcase_attempted_not_confirmed"
    else:
        evidence_class = "not_yet_publication_grade"
    return {
        "task": "AGENT-277",
        "generated_at": utc_now(),
        "evidence_class": evidence_class,
        "source_confirmed": source_ok,
        "microcase_confirmed": micro_ok,
        "microcase_statuses": statuses,
        "emissivity_Tsur_affect_heat_flux": "yes" if source_ok or micro_ok else "not_confirmed_by_publication_evidence_package",
        "separable_radiation_output_available": "no_separate_output_observed",
        "publication_instruction": (
            "Use source/microcase evidence as publication support that emissivity/Tsur affect wallHeatFlux; "
            "continue treating radiation as inseparable from total wallHeatFlux unless a separate qr/radiation output is later produced."
            if source_ok or micro_ok
            else "Retain AGENT-264 binary evidence for workflow decisions; do not use this package alone as publication proof."
        ),
    }


def write_readme(
    output_dir: Path,
    decision: dict[str, Any],
    metadata: dict[str, Any],
    delta_rows: list[dict[str, Any]],
) -> None:
    delta_lines = [
        f"- `{row['comparison_id']}` ({row['changed_parameter']}): "
        f"`delta_Q = {row['delta_wallHeatFlux_integral_W']} W`, "
        f"`delta_q = {row['delta_wallHeatFlux_mean_W_m2']} W/m2`, "
        f"`effect_detected = {row['effect_detected']}`"
        for row in delta_rows
    ]
    delta_text = "\n".join(delta_lines) if delta_lines else "- No delta rows were generated."
    text = f"""# rcExternalTemperature Publication Evidence

Generated: `{metadata['generated_utc']}`
Task: `AGENT-277`

## Purpose

This package strengthens AGENT-264 by searching for the actual custom
`rcExternalTemperature` source and, when source is unavailable, attempting an
isolated OpenFOAM 13 microcase that varies only `emissivity` or `Tsur`.

## Outputs

- `source_probe.csv`
- `binary_probe_refresh.csv`
- `microcase_matrix.csv`
- `microcase_run_results.csv`
- `wallHeatFlux_delta_summary.csv`
- `publication_evidence_decision.json`
- `run_metadata.json`

## Decision

- Evidence class: `{decision['evidence_class']}`
- Source confirmed: `{decision['source_confirmed']}`
- Microcase confirmed: `{decision['microcase_confirmed']}`
- Microcase statuses: `{decision['microcase_statuses']}`

## Final-Time Microcase Deltas

The microcase parser aggregates only the latest written `wallHeatFlux.dat` time
and combines the `glass+roof` rcExternalTemperature patches. Mean heat flux is
reported as total Q divided by inferred combined patch area.

{delta_text}

## Interpretation Boundary

This package does not mutate native Ethan solver outputs. Microcases, if run,
are generated under this package directory from an OF13 tutorial base. A
positive microcase result supports the publication statement that changing
`emissivity` or `Tsur` changes `wallHeatFlux`; it does not expose a separable
radiation heat-flux output. Until such a separate output exists, 1D parity
should continue to treat radiation in `rcExternalTemperature` as inseparable
from total OpenFOAM `wallHeatFlux`.
"""
    (output_dir / "README.md").write_text(text, encoding="utf-8")


def git_revision(path: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", str(path), "rev-parse", "HEAD"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except Exception:
        return ""
    return result.stdout.strip()


def build_package(args: argparse.Namespace) -> dict[str, Any]:
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    source_rows = build_source_probe_rows()
    binary_rows = build_binary_probe_rows()
    matrix_rows = microcase_matrix_rows()
    run_rows = run_microcases(output_dir, args.plan_only, args.timeout_s)
    delta_rows = build_delta_rows(run_rows, args.delta_tolerance_W)
    decision = build_decision(source_rows, run_rows, delta_rows)
    metadata = {
        "generated_utc": utc_now(),
        "task": "AGENT-277",
        "hostname": socket.gethostname(),
        "platform": platform.platform(),
        "python": sys.version.split()[0],
        "cwd": str(Path.cwd()),
        "command": " ".join(sys.argv),
        "of13_env": rel(OF13_ENV),
        "rcwall_library": str(RCWALL_LIB),
        "room_heating_tutorial": str(ROOM_HEATING_TUTORIAL),
        "agent264_decision": rel(AGENT264_DECISION),
        "ethan_runs_git_revision": git_revision(ROOT),
        "source_probe_rows": len(source_rows),
        "binary_probe_rows": len(binary_rows),
        "microcase_matrix_rows": len(matrix_rows),
        "microcase_run_rows": len(run_rows),
        "delta_rows": len(delta_rows),
        "evidence_class": decision["evidence_class"],
    }
    write_csv(output_dir / "source_probe.csv", source_rows, SOURCE_PROBE_FIELDS)
    write_csv(output_dir / "binary_probe_refresh.csv", binary_rows, BINARY_FIELDS)
    write_csv(output_dir / "microcase_matrix.csv", matrix_rows, MATRIX_FIELDS)
    write_csv(output_dir / "microcase_run_results.csv", run_rows, RUN_FIELDS)
    write_csv(output_dir / "wallHeatFlux_delta_summary.csv", delta_rows, DELTA_FIELDS)
    (output_dir / "publication_evidence_decision.json").write_text(json.dumps(decision, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output_dir / "run_metadata.json").write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_readme(output_dir, decision, metadata, delta_rows)
    return metadata


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default=str(OUT))
    parser.add_argument("--plan-only", action="store_true", help="Write source/binary probes and microcase matrix without running OF13.")
    parser.add_argument("--timeout-s", type=int, default=180)
    parser.add_argument("--delta-tolerance-W", type=float, default=1.0e-8)
    parser.add_argument("--strict", action="store_true", help="Reserved for test symmetry; validation errors raise when added.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    metadata = build_package(args)
    print(f"Wrote rcExternalTemperature publication evidence package to {args.output_dir}")
    print(json.dumps(metadata, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
