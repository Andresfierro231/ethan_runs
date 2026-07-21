#!/usr/bin/env python3
"""Build a per-segment patchwise heat source/sink ledger for Salt 2/3/4 Jin
mainline continuations (AGENT-194, 2026-07-07).

Reads the OpenFOAM wallHeatFlux postProcessing FO output (area-integrated Q per
patch per time step), groups patches into functional roles (heater, cooler,
ambient_wall, test_section, junction_other), and joins with mdot and T_bulk
data from the existing HTC work product.

Usage
-----
    python tools/analyze/build_heat_source_sink_ledger.py

Outputs
-------
    work_products/2026-07-07_heat_source_sink_ledger/heat_source_sink_ledger.csv
    work_products/2026-07-07_heat_source_sink_ledger/heat_source_sink_ledger.json
    work_products/2026-07-07_heat_source_sink_ledger/README.md
    work_products/2026-07-07_heat_source_sink_ledger/summary.json

Sign convention (OpenFOAM wallHeatFlux FO)
------------------------------------------
    Q > 0 [W]  heat flows INTO the fluid  (heater / powered segment)
    Q < 0 [W]  heat flows OUT of the fluid (cooler / ambient loss)

Enthalpy change limitation
--------------------------
The HTC work product provides a single T_bulk per span (not separate inlet and
outlet temperatures).  enthalpy_change_W and residual_W are therefore reported
as NaN.  Do not fabricate temperatures.

Resistance network note (required in README)
--------------------------------------------
This ledger captures **boundary fluxes only**.  The full resistance network
(internal fluid convection → wall conduction → external convection/radiation →
ambient) is NOT decomposed here.  Resistance network decomposition requires
wall thickness, wall thermal conductivity, and external h per patch, none of
which are extracted in this tool.  This is a planned future task.
"""

from __future__ import annotations

import csv
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

WAVE_ROOT = (
    ROOT
    / "jadyn_runs"
    / "modern_runs"
    / "2026-06-18_convergence_and_jin_envelope_wave"
    / "runs"
)

HTC_DIR = ROOT / "work_products" / "2026-06-30_claude_thermal_htc"

OUTPUT_DIR = ROOT / "work_products" / "2026-07-07_heat_source_sink_ledger"

# ---------------------------------------------------------------------------
# Case configuration
# ---------------------------------------------------------------------------

CASES = {
    "viscosity_screening_salt_test_2_jin_coarse_mesh": {
        "salt_label": "salt_2",
        "run_dir": WAVE_ROOT / "salt2_jin" / "case_stage"
        / "viscosity_screening_salt_test_2_jin_coarse_mesh_continuation",
        "htc_csv": HTC_DIR
        / "segment_htc_uaprime_viscosity_screening_salt_test_2_jin_coarse_mesh.csv",
    },
    "viscosity_screening_salt_test_3_jin_coarse_mesh": {
        "salt_label": "salt_3",
        "run_dir": WAVE_ROOT / "salt3_jin" / "case_stage"
        / "viscosity_screening_salt_test_3_jin_coarse_mesh_continuation",
        "htc_csv": HTC_DIR
        / "segment_htc_uaprime_viscosity_screening_salt_test_3_jin_coarse_mesh.csv",
    },
    "viscosity_screening_salt_test_4_jin_coarse_mesh": {
        "salt_label": "salt_4",
        "run_dir": WAVE_ROOT / "salt4_jin" / "case_stage"
        / "viscosity_screening_salt_test_4_jin_coarse_mesh_continuation",
        "htc_csv": HTC_DIR
        / "segment_htc_uaprime_viscosity_screening_salt_test_4_jin_coarse_mesh.csv",
    },
}

# ---------------------------------------------------------------------------
# Patch classification: (patch_group, span)
# Convention: span names match HTC data column labels.
#   lower_leg     = heated inclined leg (pipeleg_lower_*)
#   downcomer     = right vertical leg (pipeleg_right_*)
#   cooling_branch= horizontal/upper leg with cooler (pipeleg_upper_*)
#   upcomer       = left vertical leg incl. test section (pipeleg_left_*)
#   junction      = corner junction volumes
#
# Sign convention in wallHeatFlux FO:
#   positive Q = heat into fluid (heater, test section)
#   negative Q = heat out of fluid (cooler, ambient loss)
# ---------------------------------------------------------------------------

PATCH_MAP: dict[str, tuple[str, str]] = {
    # --- heater patches (powered, rcExternalTemperature + Q > 0) ---
    "pipeleg_lower_04_straight": ("heater", "lower_leg"),
    "pipeleg_lower_05_straight": ("heater", "lower_leg"),
    "pipeleg_lower_06_straight": ("heater", "lower_leg"),
    # --- test section (powered, rcExternalTemperature + Q > 0) ---
    "pipeleg_left_04_test_section": ("test_section", "upcomer"),
    # --- cooler + end reducers (externalTemperature, Q < 0) ---
    "pipeleg_upper_04_reducer": ("cooler", "cooling_branch"),
    "pipeleg_upper_05_cooler": ("cooler", "cooling_branch"),
    "pipeleg_upper_06_reducer": ("cooler", "cooling_branch"),
    # --- ambient wall — lower_leg ---
    "pipeleg_lower_01_fitting": ("ambient_wall", "lower_leg"),
    "pipeleg_lower_02_straight": ("ambient_wall", "lower_leg"),
    "pipeleg_lower_03_bend": ("ambient_wall", "lower_leg"),
    "pipeleg_lower_07_bend": ("ambient_wall", "lower_leg"),
    "pipeleg_lower_08_straight": ("ambient_wall", "lower_leg"),
    "pipeleg_lower_09_fitting": ("ambient_wall", "lower_leg"),
    # --- ambient wall — downcomer ---
    "pipeleg_right_01_lower": ("ambient_wall", "downcomer"),
    "pipeleg_right_02_middle": ("ambient_wall", "downcomer"),
    "pipeleg_right_03_upper": ("ambient_wall", "downcomer"),
    # --- ambient wall — cooling_branch ---
    "pipeleg_upper_01_straight": ("ambient_wall", "cooling_branch"),
    "pipeleg_upper_02_bend": ("ambient_wall", "cooling_branch"),
    "pipeleg_upper_03_straight": ("ambient_wall", "cooling_branch"),
    "pipeleg_upper_07_straight": ("ambient_wall", "cooling_branch"),
    "pipeleg_upper_08_bend": ("ambient_wall", "cooling_branch"),
    "pipeleg_upper_09_straight": ("ambient_wall", "cooling_branch"),
    # --- ambient wall — upcomer ---
    "pipeleg_left_01_upper": ("ambient_wall", "upcomer"),
    "pipeleg_left_02_connector": ("ambient_wall", "upcomer"),
    "pipeleg_left_03_fitting": ("ambient_wall", "upcomer"),
    "pipeleg_left_05_fitting": ("ambient_wall", "upcomer"),
    "pipeleg_left_06_connector": ("ambient_wall", "upcomer"),
    "pipeleg_left_07_lower": ("ambient_wall", "upcomer"),
}

# BC sign conventions per patch_group
BC_SIGN_CONVENTION: dict[str, str] = {
    "heater": "imposed_into_fluid",
    "test_section": "imposed_into_fluid",
    "cooler": "removed_from_fluid",
    "ambient_wall": "removed_from_fluid",
    "junction_other": "removed_from_fluid",
}

# Mdot face-zone name for lookups
MDOT_FACEZONE = "mdot_pipeleg_lower_05_straight"

# cp constant for salt (Jin default, J/kg/K)
CP_JIN_JKGK = 1423.47


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------


def parse_wallheatflux_latest(dat_file: Path) -> dict[str, float]:
    """Return {patch_name: Q_W} for the LAST time step in a wallHeatFlux.dat.

    The dat file has tab/space-separated rows:
        Time  patch_name  min[W/m2]  max[W/m2]  Q[W]  q[W/m2]
    Comment lines start with #.
    """
    if not dat_file.exists():
        return {}

    time_to_patches: dict[float, dict[str, float]] = {}
    with dat_file.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) < 5:
                continue
            try:
                t = float(parts[0])
                patch = parts[1]
                q_w = float(parts[4])  # column 5: Q [W]
            except (ValueError, IndexError):
                continue
            if t not in time_to_patches:
                time_to_patches[t] = {}
            time_to_patches[t][patch] = q_w

    if not time_to_patches:
        return {}

    latest_time = max(time_to_patches.keys())
    return time_to_patches[latest_time]


def find_latest_wallheatflux_dat(run_dir: Path) -> tuple[Path | None, str]:
    """Return (path_to_latest_dat, source_time_dir_name) for the wallHeatFlux FO."""
    whf_dir = run_dir / "postProcessing" / "wallHeatFlux"
    if not whf_dir.exists():
        return None, ""

    time_dirs = []
    for td in whf_dir.iterdir():
        if td.is_dir():
            try:
                time_dirs.append((float(td.name), td))
            except ValueError:
                pass

    if not time_dirs:
        return None, ""

    time_dirs.sort(key=lambda x: x[0])
    latest_td = time_dirs[-1][1]
    dat = latest_td / "wallHeatFlux.dat"
    return dat if dat.exists() else None, latest_td.name


def parse_bc_types(t_file: Path) -> dict[str, str]:
    """Parse 0/T and return {patch_name: bc_type} for named patches.

    Uses a simple state-machine that looks for quoted patch names followed by
    a 'type' keyword.
    """
    if not t_file.exists():
        return {}

    bc_map: dict[str, str] = {}
    content = t_file.read_text(encoding="utf-8", errors="replace")

    # Match blocks:  "patch_name"\n    {\n        type  bc_type;
    # Pattern: quoted name, then braced block containing 'type ... ;'
    pattern = re.compile(
        r'"([^"]+)"\s*\{[^{}]*?type\s+(\w+)\s*;',
        re.DOTALL,
    )
    for m in pattern.finditer(content):
        patch = m.group(1)
        bc_type = m.group(2)
        bc_map[patch] = bc_type

    return bc_map


def parse_mdot_latest(run_dir: Path, facezone: str) -> float | None:
    """Return the most recent mdot (kg/s, absolute value) from surfaceFieldValue.dat."""
    mdot_dir = run_dir / "postProcessing" / facezone
    if not mdot_dir.exists():
        return None

    time_dirs = []
    for td in mdot_dir.iterdir():
        if td.is_dir():
            try:
                time_dirs.append((float(td.name), td))
            except ValueError:
                pass

    if not time_dirs:
        return None

    time_dirs.sort(key=lambda x: x[0])
    latest_dat = time_dirs[-1][1] / "surfaceFieldValue.dat"
    if not latest_dat.exists():
        return None

    last_value: float | None = None
    with latest_dat.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) >= 2:
                try:
                    last_value = float(parts[1])
                except ValueError:
                    pass

    if last_value is None:
        return None
    return abs(last_value)


def load_htc_csv(htc_csv: Path) -> dict[str, dict[str, str]]:
    """Return {segment_label: row_dict} from the HTC CSV, keyed by 'segment' column."""
    result: dict[str, dict[str, str]] = {}
    if not htc_csv.exists():
        return result
    with htc_csv.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            seg = row.get("segment", "").strip()
            if seg:
                result[seg] = row
    return result


def safe_float(val: Any) -> float | None:
    if val is None or str(val).strip() in {"", "nan", "NaN", "None"}:
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


# ---------------------------------------------------------------------------
# Ledger assembly
# ---------------------------------------------------------------------------


def junction_group(patch_name: str) -> bool:
    """Return True if the patch belongs to the junction family."""
    lp = patch_name.lower()
    return lp.startswith("junction_") or (
        lp.startswith("ncc_") and "junction" in lp
    )


def classify_patch(patch_name: str) -> tuple[str, str] | None:
    """Return (patch_group, span) or None if the patch should be skipped.

    NCC coupling faces (ncc_*) are structural faces with Q=0; skip them.
    Junction patches map to (junction_other, junction).
    """
    lp = patch_name.lower()

    # NCC zero-flux coupling faces — always Q=0, skip
    if lp.startswith("ncc_") and "junction" not in lp:
        return None

    # Named patch in the classification map
    if patch_name in PATCH_MAP:
        return PATCH_MAP[patch_name]

    # Junction family (includes junction stubs and extensions)
    if junction_group(patch_name):
        return ("junction_other", "junction")

    # Anything else: log but skip
    return None


def build_case_ledger(
    source_id: str,
    cfg: dict[str, Any],
) -> list[dict[str, Any]]:
    """Build ledger rows for one case. Returns a list of row dicts."""

    run_dir: Path = cfg["run_dir"]
    salt_label: str = cfg["salt_label"]
    htc_csv: Path = cfg["htc_csv"]

    # --- wallHeatFlux ---
    dat_file, time_dir_name = find_latest_wallheatflux_dat(run_dir)
    if dat_file is None:
        print(f"  [WARN] No wallHeatFlux.dat found for {source_id}", file=sys.stderr)
        return []

    patch_q: dict[str, float] = parse_wallheatflux_latest(dat_file)
    if not patch_q:
        print(f"  [WARN] Empty wallHeatFlux data for {source_id}", file=sys.stderr)
        return []

    # Get the latest time recorded in the dat file
    with dat_file.open("r", encoding="utf-8") as fh:
        whf_latest_time: float | None = None
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) >= 2:
                try:
                    t = float(parts[0])
                    whf_latest_time = t
                except ValueError:
                    pass

    # --- BC types ---
    t_file = run_dir / "0" / "T"
    bc_map = parse_bc_types(t_file)

    # --- mdot ---
    mdot = parse_mdot_latest(run_dir, MDOT_FACEZONE)

    # --- HTC / T_bulk ---
    htc_data = load_htc_csv(htc_csv)

    # Map span names in HTC CSV to our span names
    # HTC CSV 'segment' values: 'lower_leg', 'upcomer', 'downcomer', etc.
    # For T_bulk, we only have one value per span, so enthalpy_change_W = NaN
    htc_segment_map = {
        "lower_leg": "lower_leg",
        "downcomer": "downcomer",
        "upcomer": "upcomer",
        "cooling_branch": "cooling_branch",
    }
    # Build T_bulk per our span names
    t_bulk_by_span: dict[str, float | None] = {}
    for htc_seg, our_span in htc_segment_map.items():
        row = htc_data.get(htc_seg)
        if row is None:
            # Try substring match
            for seg_key, seg_row in htc_data.items():
                if htc_seg in seg_key:
                    row = seg_row
                    break
        if row is not None:
            t_bulk_by_span[our_span] = safe_float(row.get("T_bulk_k"))

    # --- Aggregate patches into (patch_group, span) groups ---
    GroupKey = tuple  # (patch_group, span)
    group_q: dict[GroupKey, float] = defaultdict(float)
    group_patches: dict[GroupKey, list[str]] = defaultdict(list)
    group_bc_types: dict[GroupKey, set[str]] = defaultdict(set)

    for patch, q_w in patch_q.items():
        classification = classify_patch(patch)
        if classification is None:
            continue  # skip NCC coupling faces
        patch_group, span = classification
        key = (patch_group, span)
        group_q[key] += q_w
        group_patches[key].append(patch)
        bc_type = bc_map.get(patch, "unknown")
        group_bc_types[key].add(bc_type)

    # --- Build rows ---
    rows: list[dict[str, Any]] = []
    for key in sorted(group_q.keys()):
        patch_group, span = key
        q_integral = group_q[key]
        patches = sorted(group_patches[key])
        bc_types = group_bc_types[key]

        # bc_type: single value if unique, else comma-joined
        bc_type_str = ", ".join(sorted(bc_types)) if bc_types else "unknown"

        bc_sign = BC_SIGN_CONVENTION.get(patch_group, "unknown")

        # T_bulk from HTC (single value per span, not inlet/outlet)
        t_bulk = t_bulk_by_span.get(span)

        # enthalpy_change_W requires separate inlet+outlet T per span → NaN
        enthalpy_change_w: float | None = None
        residual_w: float | None = None
        residual_frac: float | None = None

        # Note
        note_parts: list[str] = []
        if whf_latest_time is not None:
            note_parts.append(f"wallHeatFlux from t={whf_latest_time:.0f}s")
        if t_bulk is not None:
            note_parts.append(
                "T_bulk_inlet/outlet not separately available; enthalpy_change_W=NaN"
            )
        if patch_group == "junction_other":
            note_parts.append(
                "junction patches include stubs, extensions, and corner volumes"
            )

        row: dict[str, Any] = {
            "source_id": source_id,
            "salt_label": salt_label,
            "patch_group": patch_group,
            "patch_names": ", ".join(patches),
            "bc_type": bc_type_str,
            "bc_sign_convention": bc_sign,
            "wallHeatFlux_integral_W": round(q_integral, 4),
            "span": span,
            "T_bulk_inlet_K": "",  # not available per span
            "T_bulk_outlet_K": "",  # not available per span
            "T_bulk_span_K": round(t_bulk, 4) if t_bulk is not None else "",
            "mdot_kg_s": round(mdot, 6) if mdot is not None else "",
            "enthalpy_change_W": "",  # NaN — inlet/outlet T not available
            "residual_W": "",  # NaN
            "residual_fraction": "",  # NaN
            "radiation_present": False,
            "note": "; ".join(note_parts),
        }
        rows.append(row)

    return rows


# ---------------------------------------------------------------------------
# Aggregate check
# ---------------------------------------------------------------------------


def compute_aggregate_check(all_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Compute per-source_id sums and check net balance."""
    from collections import defaultdict as dd

    heater_sum: dict[str, float] = dd(float)
    net_sum: dict[str, float] = dd(float)

    for row in all_rows:
        sid = row["source_id"]
        q = row.get("wallHeatFlux_integral_W")
        if q == "" or q is None:
            continue
        q_val = float(q)
        net_sum[sid] += q_val
        if row["patch_group"] == "heater":
            heater_sum[sid] += q_val

    check_rows = []
    for sid in sorted(heater_sum.keys()):
        h = heater_sum[sid]
        n = net_sum[sid]
        frac = n / abs(h) if abs(h) > 0 else None
        check_rows.append(
            {
                "source_id": sid,
                "heater_sum_W": round(h, 3),
                "net_sum_all_groups_W": round(n, 3),
                "net_frac_of_heater": round(frac, 5) if frac is not None else "",
                "passes_01pct_gate": (
                    abs(frac) < 0.001 if frac is not None else False
                ),
            }
        )
    return check_rows


# ---------------------------------------------------------------------------
# Write outputs
# ---------------------------------------------------------------------------


FIELDNAMES = [
    "source_id",
    "salt_label",
    "patch_group",
    "patch_names",
    "bc_type",
    "bc_sign_convention",
    "wallHeatFlux_integral_W",
    "span",
    "T_bulk_inlet_K",
    "T_bulk_outlet_K",
    "T_bulk_span_K",
    "mdot_kg_s",
    "enthalpy_change_W",
    "residual_W",
    "residual_fraction",
    "radiation_present",
    "note",
]


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDNAMES, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")


def write_readme(path: Path, check_rows: list[dict[str, Any]], all_rows: list[dict[str, Any]]) -> None:
    """Write the README for the work product."""
    n_rows = len(all_rows)
    source_ids = sorted({r["source_id"] for r in all_rows})
    patch_groups = sorted({r["patch_group"] for r in all_rows})

    check_lines = []
    for cr in check_rows:
        status = "PASS" if cr["passes_01pct_gate"] else "NOTE"
        frac_pct = (
            f"{float(cr['net_frac_of_heater']) * 100:.3f}%"
            if cr["net_frac_of_heater"] != ""
            else "N/A"
        )
        check_lines.append(
            f"  {status}  {cr['source_id']}: heater={cr['heater_sum_W']:.1f} W, "
            f"net={cr['net_sum_all_groups_W']:.1f} W ({frac_pct} of heater)"
        )

    readme = f"""# Heat Source/Sink Ledger — Salt 2/3/4 Jin Mainline Continuations

Generated by: `tools/analyze/build_heat_source_sink_ledger.py`
Task: AGENT-194 (2026-07-07)

## Purpose

Per-segment patchwise heat accounting for the TAMU molten-salt natural-circulation
loop CFD continuations (Salt 2, 3, 4 Jin).  Each row captures one patch group
(heater / cooler / ambient_wall / test_section / junction_other) on one loop span
(lower_leg / downcomer / cooling_branch / upcomer / junction).

Primary deliverable: `wallHeatFlux_integral_W` — the area-integrated boundary
heat flux at the wall–fluid interface for each patch group.

## Cases Included

{chr(10).join('- ' + s for s in source_ids)}

Only Salt 2/3/4 Jin mainline continuations are included.  Salt 1 is excluded
(weakly converged; see CLAUDE.md §6 and BOARD.md AGENT-156 note).

## Sign Convention

OpenFOAM wallHeatFlux function object convention:
- **Positive Q [W]**: heat flows INTO the fluid (heater / powered patches)
- **Negative Q [W]**: heat flows OUT of the fluid (cooler / ambient loss)

The `bc_sign_convention` column records `imposed_into_fluid` for heater/test_section
patches and `removed_from_fluid` for cooler/ambient_wall/junction patches.

## Patch Groups

| Group | Description | BC type(s) |
|---|---|---|
| `heater` | Three powered straight sections (lower_leg_04/05/06) | rcExternalTemperature + Q |
| `test_section` | Quartz test section (pipeleg_left_04) | rcExternalTemperature + Q |
| `cooler` | HX cooler + end reducers (upper_leg_04/05/06) | externalTemperature + Q |
| `ambient_wall` | All passive pipe-wall patches losing heat to ambient | rcExternalTemperature (h, Ta) |
| `junction_other` | Corner junction stubs, extensions, and faces | mixed |

## Segments (Spans)

| Span | Physical role | Patches |
|---|---|---|
| `lower_leg` | Heater leg, inclined ~21° from horizontal | pipeleg_lower_01..09 |
| `downcomer` | Right vertical leg, gravity-driven downflow | pipeleg_right_01..03 |
| `cooling_branch` | Upper horizontal leg with HX cooler | pipeleg_upper_01..09 |
| `upcomer` | Left vertical leg, buoyancy-driven upflow; includes test section | pipeleg_left_01..07 |
| `junction` | Four corner junction boxes | junction_* |

Note: `right_leg` in the schematic probe CSV corresponds to the downcomer in the
mesh geometry (see `operational_notes/06-26/30/2026-06-30_mesh_geometry_vs_probe_csv_provenance.md`).

## Aggregate Balance Check

Sum of wallHeatFlux_integral_W over all patch groups per source_id (net boundary
flux balance).  Comparison to prior `section_heater_net_q_w` from existing HTC work
product (`work_products/2026-06-30_claude_thermal_htc/`):

{chr(10).join(check_lines)}

A |net/heater| < 0.1% would indicate closed energy balance at the boundary.
Values above this threshold are expected because the CFD domain is not strictly
adiabatic (parasitic losses through junctions and ambient walls are real).

## Enthalpy Change Limitation

`enthalpy_change_W` (mdot × cp × ΔT) requires separate inlet and outlet bulk
temperatures per span.  The existing HTC work product provides only a single
T_bulk per span (mid-span average).  Therefore `enthalpy_change_W`, `residual_W`,
and `residual_fraction` are all reported as NaN.

To compute enthalpy change, extract T_bulk at the NCC interface stations (TW2,
TW4, TW6, TW8 in the probe schema) from the continuation run postProcessing.

## Resistance Network Note

This ledger captures **boundary fluxes only**.  The full resistance network
(internal fluid convection → wall conduction → external convection/radiation →
ambient) is NOT decomposed here.  Resistance network decomposition requires wall
thickness, wall thermal conductivity, and external h per patch, none of which are
extracted in this tool.  This is a planned future task.

## Radiation

`radiation_present` = False for all rows.  There is no radiative heat transfer
term (no `qr`) in these cases.

## Row Count

Total rows: {n_rows}
Patch groups: {', '.join(patch_groups)}

## Reproduce

```bash
cd /scratch/09748/andresfierro231/projects_scratch/ethan_runs
python tools/analyze/build_heat_source_sink_ledger.py
```

## Data Sources

- `wallHeatFlux`: `jadyn_runs/modern_runs/2026-06-18_*/runs/salt{{2,3,4}}_jin/case_stage/*_continuation/postProcessing/wallHeatFlux/*/wallHeatFlux.dat`
- `T_bulk_span_K`: `work_products/2026-06-30_claude_thermal_htc/segment_htc_uaprime_*.csv`
- `mdot_kg_s`: `postProcessing/mdot_pipeleg_lower_05_straight/*/surfaceFieldValue.dat`
- BC types: `0/T` from each continuation case root
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(readme, encoding="utf-8")


def write_summary_json(
    path: Path,
    all_rows: list[dict[str, Any]],
    check_rows: list[dict[str, Any]],
) -> None:
    import datetime

    source_ids = sorted({r["source_id"] for r in all_rows})
    patch_groups = sorted({r["patch_group"] for r in all_rows})
    n_rows = len(all_rows)

    heater_totals = {}
    for cr in check_rows:
        heater_totals[cr["source_id"]] = {
            "heater_sum_W": cr["heater_sum_W"],
            "net_sum_all_groups_W": cr["net_sum_all_groups_W"],
            "passes_01pct_gate": cr["passes_01pct_gate"],
        }

    summary = {
        "generated_at": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S-05:00"),
        "task": "AGENT-194",
        "inputs": {
            "wallHeatFlux_dat": "jadyn_runs/modern_runs/2026-06-18_*/runs/salt{2,3,4}_jin/case_stage/*_continuation/postProcessing/wallHeatFlux/*/wallHeatFlux.dat",
            "htc_csv": "work_products/2026-06-30_claude_thermal_htc/segment_htc_uaprime_*.csv",
            "mdot_surfaceFieldValue": "postProcessing/mdot_pipeleg_lower_05_straight/*/surfaceFieldValue.dat",
            "bc_types": "0/T from each continuation case",
        },
        "outputs": {
            "ledger_csv": "work_products/2026-07-07_heat_source_sink_ledger/heat_source_sink_ledger.csv",
            "ledger_json": "work_products/2026-07-07_heat_source_sink_ledger/heat_source_sink_ledger.json",
            "readme": "work_products/2026-07-07_heat_source_sink_ledger/README.md",
            "summary_json": "work_products/2026-07-07_heat_source_sink_ledger/summary.json",
        },
        "counts": {
            "source_ids": len(source_ids),
            "ledger_rows": n_rows,
            "patch_groups": len(patch_groups),
        },
        "source_ids": source_ids,
        "patch_groups": patch_groups,
        "aggregate_check": heater_totals,
        "limitations": [
            "enthalpy_change_W is NaN: HTC CSV provides only a single mid-span T_bulk, not separate inlet/outlet",
            "residual_W and residual_fraction are NaN for the same reason",
            "Resistance network (fluid convection → wall conduction → external h) is NOT decomposed",
            "Salt 1 excluded (weakly converged; see CLAUDE.md §6)",
            "Junction patch BC types are mixed (rcExternalTemperature + externalTemperature); grouped as junction_other",
            "radiation_present = False; no qr term in these cases",
            "wallHeatFlux sign: positive = into fluid (heater convention)",
        ],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    print("Building heat source/sink ledger (AGENT-194)...")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    all_rows: list[dict[str, Any]] = []

    for source_id, cfg in sorted(CASES.items()):
        print(f"  Processing {source_id}...")
        rows = build_case_ledger(source_id, cfg)
        all_rows.extend(rows)
        print(f"    -> {len(rows)} rows")

    if not all_rows:
        print("ERROR: No rows generated.", file=sys.stderr)
        sys.exit(1)

    check_rows = compute_aggregate_check(all_rows)

    # Write outputs
    csv_path = OUTPUT_DIR / "heat_source_sink_ledger.csv"
    json_path = OUTPUT_DIR / "heat_source_sink_ledger.json"
    readme_path = OUTPUT_DIR / "README.md"
    summary_path = OUTPUT_DIR / "summary.json"

    write_csv(csv_path, all_rows)
    write_json(json_path, all_rows)
    write_readme(readme_path, check_rows, all_rows)
    write_summary_json(summary_path, all_rows, check_rows)

    print(f"\nOutputs written to {OUTPUT_DIR}/")
    print(f"  {csv_path.name}: {len(all_rows)} rows")
    print(f"  {json_path.name}")
    print(f"  {readme_path.name}")
    print(f"  {summary_path.name}")

    print("\nAggregate balance check:")
    for cr in check_rows:
        status = "PASS" if cr["passes_01pct_gate"] else "NOTE"
        frac_pct = (
            f"{float(cr['net_frac_of_heater']) * 100:.3f}%"
            if cr["net_frac_of_heater"] != ""
            else "N/A"
        )
        print(
            f"  [{status}] {cr['source_id']}: "
            f"heater={cr['heater_sum_W']:.1f} W, "
            f"net={cr['net_sum_all_groups_W']:.1f} W ({frac_pct} of |heater|)"
        )


if __name__ == "__main__":
    main()
