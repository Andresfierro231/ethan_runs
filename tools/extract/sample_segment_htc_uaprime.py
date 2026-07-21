#!/usr/bin/env python3
"""Per-segment thermal closure: HTC, UA', Nu, R' from a reconstructed CFD case.

LANE L3 of .agent/journal/2026-06-30/1d-model-status-and-plan.md. Companion spec:
operational_notes/06-26/30/2026-06-30_thermal_extraction_spec.md (read it for the full WHY).

WHAT IT COMPUTES (per LOCKED-map segment, at a converged time t)
---------------------------------------------------------------
  q_w          = area-weighted mean wall flux over the segment's wall patches  [W/m^2]
  q'_wall      = (sum of patch wall duty Q) / segment length                    [W/m]
  T_wall       = area-weighted mean wall-face T over the segment's wall patches [K]
  T_bulk       = ENTHALPY-FLUX-weighted mixed mean  (int rho*u_n*cp(T)*T dA /
                 int rho*u_n*cp(T) dA) on the masked single-leg cut plane       [K]
  HTC  h       = q_w / (T_wall - T_bulk)                                        [W/m^2/K]
  UA'          = q'_wall / (T_wall - T_bulk)                                    [W/m/K]   (PRIMARY)
  R'_thermal   = 1 / UA'                                                        [m*K/W]
  Nu           = h * D_h / k(T_bulk)                                            [1] (direct only on left_lower_leg)

WHY enthalpy-flux (rho*u*cp) weighting and NOT mass-flux-only / area-average: the
mixed-mean bulk T is the temperature that carries the correct advected enthalpy
(int rho*u*cp*T dA); salt cp is in general strongly T-dependent so a mass-flux-only
weight mis-weights hot vs cold faces and biases ΔT, h, UA', Nu. See spec §2.

BLOCKER B1 (RESOLVED 2026-06-30)
---------------------------------------------
B1 ("T cannot be reconstructed with the LS6 toolchain") is RESOLVED: T now
reconstructs natively under OpenFOAM 13 (tools/ofenv/of13_env.sh). A reconstructed
case WITH T lives at tmp/2026-06-30_claude_action_items/recon_salt2_of13/7915/
(T U p_rgh rho ascii, 2.17M cells). Consequently:
  * T_wall is now produced WITHOUT any new OF run, by parsing the reconstructed
    `T` field's boundaryField `value` entries on the segment's wall patches
    (parse_wall_T_means / segment_wall_T). Works on the field file alone.
  * T_bulk still needs T,U,rho on a cut plane. sample_section_mean_pressure dumps
    8 cols (no T); the human generates a T-AUGMENTED 9-col dump (... p_rgh rho T)
    that enthalpy_flux_bulk_t consumes. Without it, T_bulk (hence ΔT/h/UA'/Nu) is
    reported as needing the augmented dump rather than crashing.
The wall duty Q (wallHeatFlux FO .dat) never needed reconstruction, so
q_w / q'_wall / perimeter assemble regardless. `--dry-run` still prints the plan.

SIGN CONVENTION (heated vs cooled segments)
---------------------------------------------
q_w and ΔT = (T_wall - T_bulk) are carried SIGNED (not |.|): h, UA' come out
positive where the wall is hotter than the bulk (heated leg) and negative where
the wall is colder (cooler leg). Outputs also report |ΔT| (`abs_delta_T_k`) and
the sign of q (`q_sign`) so a reversed sign surfaces a physical inconsistency
instead of being hidden. HTC magnitude should be read with |ΔT|; the sign tells
the direction of heat flow. Single-branch Nu (direct only on left_lower_leg).

NEEDS MORE ANALYSIS / TODO (still approximate)
---------------------------------------------
  * AREA WEIGHTING of T_wall uses per-patch area A_p=|Q_p|/|q_p| from the
    wallHeatFlux FO and the PATCH-MEAN face T (not per-face area weighting within
    a patch). True per-face area weighting would need the patch face areas from
    the mesh; the patch-mean is an equal-per-face approximation INSIDE each patch.
    When a patch lacks an FO area, T_wall falls back to face-count weighting
    (flagged `equal_weight_fallback`).
  * T_BULK DUMP DEPENDENCY: T_bulk requires the human-generated T-augmented
    cut-plane dump; until present, ΔT/h/UA'/Nu are gated (reported, not crashed).
  * MESH INDEPENDENCE UNESTABLISHED (coarse mesh only, B2): no GCI bound; every
    row stamped mesh=coarse. Required before any publishable thermal closure.
  * qr RADIATIVE EXCLUSION: wallHeatFlux has no qr column -> convective-only HTC
    for rad_on cases (stamped qr_caveat).
  * Salt 1 weaker convergence (-2.08%) -> provisional.

USAGE (system python; do NOT source the OpenFOAM env in this shell)
  # plan + input validation, no T needed:
  python tools/extract/sample_segment_htc_uaprime.py \
      --case-dir <case> --time <t> \
      --source-id viscosity_screening_salt_test_2_jin_coarse_mesh --dry-run
  # full run (only after B1, case must have reconstructed T U rho + wallHeatFlux):
  python tools/extract/sample_segment_htc_uaprime.py \
      --case-dir tmp/<recon_salt2_jin_continuation> --time 7915 \
      --source-id viscosity_screening_salt_test_2_jin_coarse_mesh
"""
from __future__ import annotations

import argparse
import math
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.common import (  # noqa: E402
    WORKSPACE_ROOT,
    csv_dump,
    ensure_dir,
    iso_timestamp,
    json_dump,
    load_yaml,
    relative_to_workspace,
)
from tools.case_analysis_profiles import (  # noqa: E402  (read-only import)
    get_case_analysis_profile,
    load_station_centers_from_file,
)

DEFAULT_OUTPUT_DIR = WORKSPACE_ROOT / "work_products" / "2026-06-30_claude_segment_htc_uaprime"
# Same masking radius as sample_section_mean_pressure.py: ~0.04 m captures one bore
# (radius ~0.016 m) with margin while excluding neighbouring counter-flowing legs.
DEFAULT_LEG_RADIUS_M = 0.04
FLOW_ALIGNMENT_GATE = 0.8  # |meanU|/<|U|> below this => mask still mixes directions
DELTA_T_MIN_K = 0.5  # below this |T_wall - T_bulk| HTC/UA' are ill-conditioned

# LOCKED CFD->1D segment map (operational_notes/06-26/30/2026-06-30_cfd_to_1d_segment_map.md).
SEGMENT_TO_SPANS: dict[str, list[str]] = {
    "lower_leg": ["lower_leg"],  # heated bottom leg (== heated_incline); NOT left_lower_leg
    "upcomer": ["left_lower_leg", "test_section_span", "left_upper_leg"],
    "downcomer": ["right_leg"],
}
THERMALLY_BLOCKED_SEGMENTS = {"downcomer"}  # right_leg: THERMAL_BLOCKED_BRANCHES
# Direct Nu admitted for 1D use only on this CFD span (closure map row
# left_lower_leg_nu_branch_aware_re_power_law).
NU_DIRECT_ADMITTED_SPANS = {"left_lower_leg"}

# Populated by main() when --mesh-length is set: {span: mesh-centerline arc length (m)}.
# Used to override the schematic-label segment length (T8 fix).
MESH_SPAN_LENGTHS: dict[str, float] = {}


def load_mesh_span_lengths(mesh_stations_path: Path) -> dict[str, float]:
    """Per-span mesh-centerline arc length from build_mesh_centerlines mesh_stations.json."""
    import json as _json
    payload = _json.loads(Path(mesh_stations_path).read_text(encoding="utf-8"))
    by_span: dict[str, list[list[float]]] = {}
    for s in payload.get("stations", []):
        by_span.setdefault(s["span"], []).append([float(s["x"]), float(s["y"]), float(s["z"])])
    out: dict[str, float] = {}
    for span, pts in by_span.items():
        L = 0.0
        for i in range(1, len(pts)):
            a, b = pts[i - 1], pts[i]
            L += float(((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2) ** 0.5)
        out[span] = L
    return out
# Convergence assertions from assess_time_convergence.py (spec §7). Salt 2/3/4 Jin
# stationary; Salt 1 weaker (-2.08%) -> provisional.
CONVERGENCE_STATUS = {
    "viscosity_screening_salt_test_2_jin_coarse_mesh": "stationary",
    "viscosity_screening_salt_test_3_jin_coarse_mesh": "stationary",
    "viscosity_screening_salt_test_4_jin_coarse_mesh": "stationary",
    "viscosity_screening_salt_test_1_jin_coarse_mesh": "provisional_-2.08pct",
}


# ---------------------------------------------------------------------------
# Salt property polynomials.
# Replicated (read-only) from tools/analyze/ethan_salt_hardening_common.py
# (polynomial_eval / evaluate_cp / evaluate_k): k, cp are Σ c_i * T^i over the
# `fluid_properties` coeffs in the case's own case_config.yaml. We read the model
# from the case config so a Jin/Kirst swap or a refit cannot silently desync.
# ---------------------------------------------------------------------------
def polynomial_eval(coeffs: list[float], temperature_k: float) -> float:
    if not math.isfinite(temperature_k):
        return math.nan
    return float(sum(float(c) * (temperature_k ** i) for i, c in enumerate(coeffs)))


def find_case_config(case_dir: Path) -> Path | None:
    """case_config.yaml may live in the case dir, its parent, or a sibling
    reconstructed_case / processors64 target."""
    candidates = [case_dir, case_dir.parent]
    proc = case_dir / "processors64"
    if proc.exists():
        try:
            candidates.append(proc.resolve().parent)
        except OSError:
            pass
    for base in candidates:
        for name in ("case_config.yaml",):
            hit = base / name
            if hit.exists():
                return hit
    # last resort: shallow search
    hits = list(case_dir.glob("**/case_config.yaml"))
    return hits[0] if hits else None


def load_property_model(case_dir: Path) -> dict[str, Any]:
    cfg_path = find_case_config(case_dir)
    if cfg_path is None:
        return {"ok": False, "reason": "case_config.yaml not found", "cp_coeffs": None, "k_coeffs": None}
    try:
        cfg = load_yaml(cfg_path)
        fp = cfg["fluid_properties"]
        cp = [float(v) for v in fp["Cp_coeffs"]]
        k = [float(v) for v in fp["kappa_spec"]["coeffs"]]
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "reason": f"could not parse fluid_properties: {exc}", "cp_coeffs": None, "k_coeffs": None}
    return {"ok": True, "config_path": relative_to_workspace(cfg_path), "cp_coeffs": cp, "k_coeffs": k}


# ---------------------------------------------------------------------------
# Station geometry (reuse the loop polyline builder from the section-mean tool so
# the cut-plane station frame is identical).
# ---------------------------------------------------------------------------
def build_station_frame(source_id: str) -> dict[str, dict[str, Any]]:
    """Map every centerline label -> {x,y,z, nx,ny,nz, span} using the locked profile."""
    profile = get_case_analysis_profile(source_id)
    centers = load_station_centers_from_file(profile.tp_tw_locations)
    ordered: list[str] = []
    seen: set[str] = set()
    label_span: dict[str, str] = {}
    for span in profile.major_span_order:
        for lab in profile.major_spans[span]["centerline_labels"]:
            if lab not in seen:
                ordered.append(lab)
                seen.add(lab)
            label_span.setdefault(lab, span)
    pts = [np.array(centers[lab], dtype=float) for lab in ordered]
    n = len(pts)
    frame: dict[str, dict[str, Any]] = {}
    for i, lab in enumerate(ordered):
        prev_p = pts[i - 1] if i > 0 else pts[i]
        next_p = pts[i + 1] if i < n - 1 else pts[i]
        tangent = next_p - prev_p
        norm = float(np.linalg.norm(tangent)) or 1.0
        tangent = tangent / norm
        frame[lab] = {
            "label": lab, "span": label_span.get(lab, ""),
            "x": float(pts[i][0]), "y": float(pts[i][1]), "z": float(pts[i][2]),
            "nx": float(tangent[0]), "ny": float(tangent[1]), "nz": float(tangent[2]),
        }
    return frame


def bulk_station_for_span(frame: dict[str, dict[str, Any]], source_id: str, span: str) -> dict[str, Any] | None:
    """Pick a representative mid-leg TW station for the span's bulk-T cut plane.

    Prefer an interior 'TW' label (mid-leg, cleanest cross-section); fall back to
    the middle of the span's centerline labels.
    """
    profile = get_case_analysis_profile(source_id)
    labels = profile.major_spans[span]["centerline_labels"]
    tws = [lab for lab in labels if lab.startswith("TW")]
    chosen = tws[len(tws) // 2] if tws else labels[len(labels) // 2]
    return frame.get(chosen)


# ---------------------------------------------------------------------------
# wallHeatFlux FO parsing (Time, patch, min, max, Q[W], q[W/m^2]).
# ---------------------------------------------------------------------------
def find_wallheatflux_dat(case_dir: Path, time_name: str) -> Path | None:
    bases = [case_dir]
    proc = case_dir / "processors64"
    if proc.exists():
        try:
            bases.append(proc.resolve().parent)
        except OSError:
            pass
    for base in bases:
        d = base / "postProcessing" / "wallHeatFlux"
        if not d.exists():
            continue
        exact = d / time_name / "wallHeatFlux.dat"
        if exact.exists():
            return exact
        hits = sorted(d.rglob("wallHeatFlux.dat"))
        if hits:
            return hits[-1]
    return None


def parse_wallheatflux(path: Path) -> dict[str, dict[str, float]]:
    """Return {patch: {'Q_w': Q[W], 'q_wm2': q[W/m^2]}} from the LAST time block."""
    rows: dict[str, dict[str, float]] = {}
    last_time: float | None = None
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            s = line.strip()
            if not s or s.startswith("#"):
                continue
            parts = s.split("\t") if "\t" in s else s.split()
            if len(parts) < 6:
                continue
            try:
                t = float(parts[0])
            except ValueError:
                continue
            patch = parts[1]
            try:
                q_total = float(parts[4])  # Q [W]
                q_flux = float(parts[5])   # q [W/m^2]
            except ValueError:
                continue
            if last_time is None or t > last_time:
                last_time = t
                rows = {}
            if t == last_time:
                rows[patch] = {"Q_w": q_total, "q_wm2": q_flux}
    return rows


# ---------------------------------------------------------------------------
# T_wall: parse the reconstructed scalar field's boundaryField directly.
#
# WHY parse the field file rather than run a sampler FO: the reconstructed
# OpenFOAM-13 `T` field already carries the converged wall-face temperature on
# every wall patch, stored under the patch's `value` entry. This is true for ALL
# wall BC types in these cases (rcExternalTemperature heated/junction patches,
# externalTemperature cooler patch, etc.): each writes a `value uniform X` or
# `value nonuniform List<scalar> N (...)` holding the patch face temperatures.
# (rcExternalTemperature also writes a `Tp` field = the same wall temperature; we
# deliberately key on `value` because it is the OpenFOAM-standard patch field
# value and is present uniformly across every BC type, so one parser covers all
# patches.) Parsing the file needs NO OpenFOAM runtime, so it works under B1.
#
# Verified on .../recon_salt2_of13/7915/T: heated lower-leg patches ~455-467 K
# (hottest), cooler patch (pipeleg_upper_05_cooler) ~434 K (coldest) -> physical.
# ---------------------------------------------------------------------------
def find_T_field(case_dir: Path, time_name: str) -> Path | None:
    """Locate the reconstructed scalar T field at the requested time."""
    bases = [case_dir]
    proc = case_dir / "processors64"
    if proc.exists():
        try:
            bases.append(proc.resolve().parent)
        except OSError:
            pass
    for base in bases:
        cand = base / time_name / "T"
        if cand.is_file():
            return cand
    return None


def _extract_boundary_section(text: str) -> str:
    """Return the text from the `boundaryField` keyword onward (where patch
    sub-dicts live). Cheap substring slice; the internalField list above it is
    huge so we avoid re-parsing it."""
    idx = text.find("boundaryField")
    return text[idx:] if idx >= 0 else ""


def _find_patch_block(bf_text: str, patch: str) -> str | None:
    """Brace-match the body of a named patch sub-dict inside boundaryField.

    Returns the inner text between the patch's opening/closing braces, or None
    if the patch is absent. Brace matching (not regex) is used so nested
    sub-dicts (h{...}, Ta{...}, kappaLayerCoeffs(...)) do not terminate early.
    """
    m = re.search(r"(?:^|\n)[ \t]*" + re.escape(patch) + r"[ \t]*\n[ \t]*\{", bf_text)
    if not m:
        return None
    open_idx = bf_text.index("{", m.start())
    depth = 0
    for i in range(open_idx, len(bf_text)):
        c = bf_text[i]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return bf_text[open_idx + 1 : i]
    return None


def parse_patch_scalar_field(block: str, key: str = "value") -> np.ndarray | None:
    """Extract a patch scalar field (`value` by default) from a patch block.

    Handles both forms OpenFOAM writes:
      * `value uniform 451.3;`                       -> single scalar
      * `value nonuniform List<scalar> N ( a b c );` -> N per-face scalars
    Returns a 1-D numpy array of the face values, or None if the key is absent.
    Used for T_wall; also reusable for `Tp` / `refValue` if ever needed.
    """
    # uniform scalar
    m = re.search(r"\b" + re.escape(key) + r"\s+uniform\s+([-\d.eE+]+)\s*;", block)
    if m:
        return np.array([float(m.group(1))])
    # nonuniform List<scalar> N ( ... )
    m = re.search(
        r"\b" + re.escape(key) + r"\s+nonuniform\s+List<scalar>\s*\n?\s*(\d+)\s*\n?\s*\(",
        block,
    )
    if not m:
        return None
    open_idx = block.index("(", m.end() - 1)
    depth = 0
    close_idx = open_idx
    for i in range(open_idx, len(block)):
        if block[i] == "(":
            depth += 1
        elif block[i] == ")":
            depth -= 1
            if depth == 0:
                close_idx = i
                break
    nums = block[open_idx + 1 : close_idx].split()
    return np.array([float(x) for x in nums]) if nums else np.empty(0)


def parse_wall_T_means(t_field_path: Path, patches: list[str]) -> dict[str, dict[str, float]]:
    """For each requested wall patch, return its face-T stats from the field's
    boundaryField. {patch: {'T_mean': K, 'n_faces': int}}. Missing patches and
    patches without a `value` entry are reported with NaN/0 so the caller can
    decide how to weight them (and surface the gap)."""
    text = t_field_path.read_text(encoding="utf-8", errors="replace")
    bf = _extract_boundary_section(text)
    out: dict[str, dict[str, float]] = {}
    for p in patches:
        block = _find_patch_block(bf, p)
        if block is None:
            out[p] = {"T_mean": float("nan"), "n_faces": 0}
            continue
        vals = parse_patch_scalar_field(block, "value")
        if vals is None or vals.size == 0:
            out[p] = {"T_mean": float("nan"), "n_faces": 0}
            continue
        out[p] = {"T_mean": float(vals.mean()), "n_faces": int(vals.size)}
    return out


def segment_wall_T(
    t_field_path: Path,
    patches: list[str],
    whf: dict[str, dict[str, float]],
) -> dict[str, Any]:
    """Area-weighted segment mean wall temperature across a segment's patches.

    Weighting: per-patch face area A_p = |Q_p| / |q_p| from the wallHeatFlux FO
    (Q [W] and q [W/m^2] are both on disk), so T_wall = Σ A_p T_p / Σ A_p. This
    is the same area accounting already used for q_w (Σ Q / Σ A), keeping T_wall
    and q_w on a consistent area basis. If a patch's q is ~0 (no usable area) or
    the patch is absent from the FO, it falls back to EQUAL (face-count) weighting
    and the result is flagged `equal_weight_fallback` so the approximation is
    never silent. See module-docstring TODO on area-weighting fidelity.
    """
    per_patch = parse_wall_T_means(t_field_path, patches)
    num = 0.0
    den = 0.0
    used_area = False
    used_equal = False
    n_used = 0
    for p in patches:
        stat = per_patch.get(p, {"T_mean": float("nan"), "n_faces": 0})
        t_mean = stat["T_mean"]
        if not math.isfinite(t_mean):
            continue
        n_used += 1
        area = float("nan")
        if p in whf and abs(whf[p].get("q_wm2", 0.0)) > 1e-12:
            area = abs(whf[p]["Q_w"] / whf[p]["q_wm2"])
        if math.isfinite(area) and area > 0:
            num += area * t_mean
            den += area
            used_area = True
        else:
            # equal-weight fallback: weight by face count (best proxy for area
            # when the FO area is unavailable for this patch).
            w = float(stat["n_faces"]) or 1.0
            num += w * t_mean
            den += w
            used_equal = True
    if den <= 0:
        return {"T_wall_k": float("nan"), "wall_T_weighting": "none", "n_patches_used": 0,
                "per_patch_T": per_patch}
    weighting = (
        "area_weighted_Qoverq" if (used_area and not used_equal)
        else "mixed_area_and_equal_weight_fallback" if (used_area and used_equal)
        else "equal_weight_fallback_facecount"
    )
    return {
        "T_wall_k": float(num / den),
        "wall_T_weighting": weighting,
        "n_patches_used": n_used,
        "per_patch_T": per_patch,
    }


# ---------------------------------------------------------------------------
# Raw cut-plane .xy parsing + single-leg masking (matches sample_section_mean_pressure).
#
# CUT-PLANE COLUMN SCHEMA (parsed DEFENSIVELY by column count):
#   8 cols  x y z Ux Uy Uz p_rgh rho        -> NO T  (what sample_section_mean_pressure
#                                              dumps today). T_bulk cannot be formed;
#                                              we report `missing_T_columns` (no crash).
#   9 cols  x y z Ux Uy Uz p_rgh rho T      -> T APPENDED (the spec's T-augmented dump,
#                                              "8->9 columns: ... p_rgh rho T", which the
#                                              human generates by adding T to the FO
#                                              `fields`). This is the DEFAULT/expected.
#   9 cols  x y z Ux Uy Uz T p_rgh rho      -> T in the MIDDLE (what this tool's own
#                                              write_controldict emits, fields (U T p_rgh
#                                              rho)). Disambiguated from the appended
#                                              form by a physical range check on the T
#                                              column (T ~ [250, 1500] K).
# Either 9-col order is handled; we pick the column whose values are in a plausible
# absolute-temperature range, and document the choice in the returned status.
# ---------------------------------------------------------------------------
def find_plane_xy(case_dir: Path, label: str) -> Path | None:
    base = case_dir / "postProcessing" / "segthermSurfaces"
    if not base.exists():
        return None
    hits = list(base.rglob(f"plane_{label}.xy")) + list(base.rglob(f"*plane_{label}*.xy"))
    return hits[0] if hits else None


def write_controldict(case_dir: Path, stations: list[dict[str, Any]]) -> None:
    """Single `surfaces` FO (raw) dumping U T p_rgh rho at each bulk station plane."""
    lines = [
        "FoamFile { version 2.0; format ascii; class dictionary; object controlDict; }",
        "application foamRun; startTime 0; stopAt endTime; endTime 1000000; deltaT 1;",
        "writeControl timeStep; writeInterval 1; writeFormat ascii; writePrecision 10;",
        "writeCompression off; timeFormat general; timePrecision 10; runTimeModifiable false;",
        "functions {",
        "  segthermSurfaces {",
        "    type            surfaces;",
        '    libs            ("libsampling.so");',
        "    writeControl    writeTime;",
        "    surfaceFormat   raw;",
        "    interpolate     false;",
        "    interpolationScheme cell;",
        "    fields          (U T p_rgh rho);",
        "    surfaces (",
    ]
    for st in stations:
        lines += [
            f"      plane_{st['label']} {{",
            "        type        cuttingPlane;",
            "        planeType   pointAndNormal;",
            f"        pointAndNormalDict {{ point ({st['x']} {st['y']} {st['z']}); normal ({st['nx']} {st['ny']} {st['nz']}); }}",
            "      }",
        ]
    lines += ["    );", "  }", "}"]
    (case_dir / "system" / "controlDict").write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_foampostprocess(case_dir: Path, time_name: str, log_path: Path) -> int:
    env_script = ROOT / "tools" / "ofenv" / "of12_env.sh"
    inner = f"source '{env_script}' >/dev/null 2>&1 && foamPostProcess -case '{case_dir}' -time '{time_name}'"
    with log_path.open("w", encoding="utf-8") as log:
        return subprocess.run(["bash", "-lc", inner], cwd=str(case_dir), stdout=log, stderr=subprocess.STDOUT).returncode


T_PLAUSIBLE_MIN_K = 250.0   # well below any salt freeze point but excludes p_rgh/rho
T_PLAUSIBLE_MAX_K = 1500.0  # above any operating salt T but excludes large p_rgh


def _resolve_cutplane_columns(data: np.ndarray) -> dict[str, int] | None:
    """Resolve {'T','rho'} column indices for a 9-column raw cut-plane dump.

    Two 9-col orders are supported (see section comment):
      appended : ... p_rgh rho T   -> T=8, rho=7   (spec default)
      middle   : ... T p_rgh rho   -> T=6, rho=8   (this tool's own dump)
    We disambiguate by which candidate T column has a physically plausible
    absolute-temperature median; rho is then the remaining density column. If
    neither candidate is in range we give up (returns None) rather than guess.
    """
    if data.shape[1] < 9:
        return None

    def _plausible(col: int) -> bool:
        med = float(np.median(data[:, col]))
        return T_PLAUSIBLE_MIN_K <= med <= T_PLAUSIBLE_MAX_K

    appended_ok = _plausible(8) and not _plausible(6)
    middle_ok = _plausible(6) and not _plausible(8)
    if appended_ok:
        return {"T": 8, "rho": 7, "schema": 1}  # ...p_rgh rho T
    if middle_ok:
        return {"T": 6, "rho": 8, "schema": 2}  # ...T p_rgh rho
    # ambiguous (both or neither plausible): prefer the spec's appended schema if
    # col 8 is in range, else fail rather than silently mislabel.
    if _plausible(8):
        return {"T": 8, "rho": 7, "schema": 1}
    return None


def enthalpy_flux_bulk_t(
    xy_path: Path, station: dict[str, Any], leg_radius: float, cp_coeffs: list[float],
) -> dict[str, Any]:
    """Enthalpy-flux-weighted mixed-mean bulk T on the masked single leg.

    T_bulk = Σ rho*u_n*cp(T)*T  /  Σ rho*u_n*cp(T)  over masked faces, signed u_n.
    Returns T_bulk_k, flow_alignment, n_masked, and a status.
    """
    out: dict[str, Any] = {"status": "ok"}
    try:
        data = np.loadtxt(xy_path)
    except Exception:  # noqa: BLE001
        return {"status": "unreadable"}
    if data.ndim == 1:
        data = data.reshape(1, -1)
    # Defensive schema detection by column count (see module section comment).
    if data.size == 0 or data.shape[1] < 9:
        # 8-col dump (no T) is the section-mean tool's current output. We need the
        # T-augmented (9-col) dump to form the mixed-mean bulk T; report rather
        # than crash so the rest of the record (q_w, T_wall) still populates.
        return {"status": "missing_T_columns_need_T_augmented_dump"}
    pts = data[:, :3]
    U = data[:, 3:6]
    cols = _resolve_cutplane_columns(data)
    if cols is None:
        return {"status": "cutplane_T_column_unresolved"}
    T = data[:, cols["T"]]
    rho = data[:, cols["rho"]]
    center = np.array([station["x"], station["y"], station["z"]], dtype=float)
    mask = np.linalg.norm(pts - center, axis=1) < leg_radius
    n_masked = int(mask.sum())
    if n_masked < 8:
        return {"status": "too_few_masked_faces", "n_masked": n_masked}
    Um = U[mask]
    Tm = T[mask]
    rhom = rho[mask]
    normal = np.array([station["nx"], station["ny"], station["nz"]], dtype=float)
    normal = normal / (np.linalg.norm(normal) or 1.0)
    u_n = Um @ normal
    speed = np.linalg.norm(Um, axis=1)
    alignment = float(np.linalg.norm(Um.mean(axis=0)) / speed.mean()) if speed.mean() > 0 else float("nan")
    cp = np.array([polynomial_eval(cp_coeffs, float(t)) for t in Tm])
    weight = rhom * u_n * cp  # signed: reverse-flow faces contribute negatively
    denom = float(weight.sum())
    if not math.isfinite(denom) or abs(denom) < 1e-30:
        return {"status": "zero_enthalpy_flux", "n_masked": n_masked, "flow_alignment": alignment}
    t_bulk = float((weight * Tm).sum() / denom)
    out.update({
        "T_bulk_k": t_bulk,
        "T_bulk_simple_area_mean_k": float(Tm.mean()),  # diagnostic only
        "cp_bulk_jkgk": polynomial_eval(cp_coeffs, t_bulk),
        "flow_alignment": alignment,
        "n_masked": n_masked,
        "cutplane_schema": {1: "x y z U(3) p_rgh rho T", 2: "x y z U(3) T p_rgh rho"}.get(cols["schema"], "unknown"),
    })
    if math.isfinite(alignment) and alignment < FLOW_ALIGNMENT_GATE:
        out["status"] = "low_flow_alignment_mask_mixes_directions"
    return out


# ---------------------------------------------------------------------------
def segment_record(
    segment: str, spans: list[str], frame: dict[str, dict[str, Any]],
    whf: dict[str, dict[str, float]], source_id: str, t_have: bool,
    cp_coeffs: list[float] | None, k_coeffs: list[float] | None,
    case_dir: Path, leg_radius: float, radiation_mode: str, time_name: str,
) -> dict[str, Any]:
    profile = get_case_analysis_profile(source_id)
    # gather wall patches + duties across the component spans
    patches: list[str] = []
    for span in spans:
        patches.extend(profile.major_spans[span]["wall_patches"])
    present = [p for p in patches if p in whf]
    missing = [p for p in patches if p not in whf]
    q_sum_w = float(sum(whf[p]["Q_w"] for p in present)) if present else float("nan")
    # area-weighted mean flux: Q_p = q_p * A_p so A_p = Q_p/q_p (q!=0); q_w = ΣQ/ΣA
    area = 0.0
    for p in present:
        q = whf[p]["q_wm2"]
        if abs(q) > 1e-12:
            area += abs(whf[p]["Q_w"] / q)
    q_w_wm2 = float(q_sum_w / area) if area > 0 and math.isfinite(q_sum_w) else float("nan")

    nu_admitted = any(s in NU_DIRECT_ADMITTED_SPANS for s in spans)
    rec: dict[str, Any] = {
        "segment": segment,
        "cfd_spans": "+".join(spans),
        "n_wall_patches": len(patches),
        "n_wall_patches_present": len(present),
        "wall_patches_missing": ",".join(missing),
        "wall_duty_Q_w": q_sum_w,
        "wall_area_m2": area if area > 0 else float("nan"),
        "q_w_wm2": q_w_wm2,
        "radiation_mode": radiation_mode,
        "convergence_status": CONVERGENCE_STATUS.get(source_id, "convergence_unverified"),
        "mesh": "coarse",
        "mesh_independence": "UNESTABLISHED",
        "qr_caveat": "convective_only_qr_excluded" if radiation_mode == "rad_on" else "qr_not_applicable",
        "nu_direct_admitted": nu_admitted,
        "thermally_blocked": segment in THERMALLY_BLOCKED_SEGMENTS,
        "blocker_B1": not t_have,
    }
    if segment in THERMALLY_BLOCKED_SEGMENTS:
        rec["status"] = "thermally_blocked_segment_right_leg"
        return rec

    # bulk-T station + length. Prefer the MESH centerline length (T8 fix: the
    # schematic centerline_labels swap lower<->right and inflate L ~1.3x, biasing
    # UA'/q'); fall back to the label polyline when mesh lengths are unavailable.
    L_seg = 0.0
    if MESH_SPAN_LENGTHS and all(s in MESH_SPAN_LENGTHS for s in spans):
        L_seg = float(sum(MESH_SPAN_LENGTHS[s] for s in spans))
        rec["segment_length_source"] = "mesh_centerline"
    else:
        for span in spans:
            labs = profile.major_spans[span]["centerline_labels"]
            for a, b in zip(labs[:-1], labs[1:]):
                if a in frame and b in frame:
                    pa = np.array([frame[a]["x"], frame[a]["y"], frame[a]["z"]])
                    pb = np.array([frame[b]["x"], frame[b]["y"], frame[b]["z"]])
                    L_seg += float(np.linalg.norm(pb - pa))
        rec["segment_length_source"] = "schematic_labels"
    rec["segment_length_m"] = L_seg if L_seg > 0 else float("nan")
    rec["qprime_wall_wm"] = float(q_sum_w / L_seg) if L_seg > 0 and math.isfinite(q_sum_w) else float("nan")
    rec["wetted_perimeter_m"] = float(area / L_seg) if (area > 0 and L_seg > 0) else float("nan")

    # choose a representative bulk station on the *primary* span (last span for
    # upcomer is arbitrary; use the first component span)
    bulk_st = bulk_station_for_span(frame, source_id, spans[0])
    rec["station_label"] = bulk_st["label"] if bulk_st else ""

    if not t_have:
        rec["status"] = "blocked_on_B1_no_T"
        rec["T_bulk_k"] = float("nan")
        rec["T_wall_k"] = float("nan")
        rec["htc_wm2k"] = float("nan")
        rec["uaprime_wmk"] = float("nan")
        rec["R_prime_thermal_mkw"] = float("nan")
        rec["Nu"] = float("nan")
        return rec

    # --- T available: compute bulk T from the cut plane, T_wall from wall patches ---
    xy = find_plane_xy(case_dir, bulk_st["label"]) if bulk_st else None
    if xy is None:
        rec["status"] = "no_cutplane_output"
        return rec
    bulk = enthalpy_flux_bulk_t(xy, bulk_st, leg_radius, cp_coeffs or [0.0])
    rec.update({k: v for k, v in bulk.items() if k != "status"})
    if bulk["status"] not in ("ok", "low_flow_alignment_mask_mixes_directions"):
        rec["status"] = bulk["status"]
        return rec

    # T_wall: area-weighted mean wall-face T over the segment's wall patches,
    # parsed straight from the reconstructed T field's boundaryField (no OF run
    # needed; works under B1). Area weight A_p = |Q_p|/|q_p| from wallHeatFlux;
    # equal-weight fallback when the FO area is unavailable (flagged).
    t_field = find_T_field(case_dir, time_name)
    twall = {"T_wall_k": float("nan"), "wall_T_weighting": "none", "n_patches_used": 0}
    if t_field is not None:
        twall = segment_wall_T(t_field, patches, whf)
    rec["T_wall_k"] = twall["T_wall_k"]
    rec["wall_T_weighting"] = twall["wall_T_weighting"]
    rec["n_wall_patches_T_used"] = twall["n_patches_used"]
    t_bulk = rec.get("T_bulk_k", float("nan"))
    t_wall = rec.get("T_wall_k", float("nan"))
    if not math.isfinite(t_wall):
        rec["status"] = "T_wall_unavailable_no_T_field_or_value_entries"
        return rec
    if not math.isfinite(t_bulk):
        rec["status"] = "T_bulk_unavailable_need_T_augmented_cutplane_dump"
        return rec
    delta_t = t_wall - t_bulk  # SIGNED: + heated wall, - cooled wall (see docstring)
    rec["delta_T_k"] = delta_t
    rec["abs_delta_T_k"] = abs(delta_t)
    # q sign: solver writes q<0 for heat INTO the fluid (heated wall). Report it so
    # a sign mismatch with ΔT (e.g. q<0 with T_wall<T_bulk) surfaces an inconsistency.
    q_seg = rec.get("q_w_wm2", float("nan"))
    rec["q_sign"] = ("negative_into_fluid_heated" if q_seg < 0 else
                     "positive_out_of_fluid_cooled" if q_seg > 0 else "zero_or_nan")
    rec["sign_consistent_heated_wall"] = bool(
        math.isfinite(q_seg) and ((q_seg < 0) == (delta_t > 0))
    )
    if abs(delta_t) < DELTA_T_MIN_K:
        rec["status"] = "delta_T_too_small_ill_conditioned"
        return rec
    rec["htc_wm2k"] = rec["q_w_wm2"] / delta_t if math.isfinite(rec["q_w_wm2"]) else float("nan")
    rec["uaprime_wmk"] = rec["qprime_wall_wm"] / delta_t if math.isfinite(rec.get("qprime_wall_wm", float("nan"))) else float("nan")
    rec["R_prime_thermal_mkw"] = 1.0 / rec["uaprime_wmk"] if rec.get("uaprime_wmk") not in (0.0, None) and math.isfinite(rec.get("uaprime_wmk", float("nan"))) else float("nan")
    # consistency cross-check UA' ~ h * perimeter
    if math.isfinite(rec.get("htc_wm2k", float("nan"))) and math.isfinite(rec.get("wetted_perimeter_m", float("nan"))):
        rec["htc_times_perimeter_check_wmk"] = rec["htc_wm2k"] * rec["wetted_perimeter_m"]
    k_bulk = polynomial_eval(k_coeffs, t_bulk) if k_coeffs else float("nan")
    rec["k_bulk_wmk"] = k_bulk
    # D_h: measured from the masked cut (reuse section-mean geometry helper).
    rec["D_h_m"] = _measured_dh(xy, bulk_st, leg_radius)
    if nu_admitted and math.isfinite(rec.get("htc_wm2k", float("nan"))) and math.isfinite(k_bulk) and k_bulk > 0 and math.isfinite(rec.get("D_h_m", float("nan"))):
        rec["Nu"] = rec["htc_wm2k"] * rec["D_h_m"] / k_bulk
    else:
        rec["Nu"] = float("nan")
        if not nu_admitted:
            rec["nu_note"] = "Nu_direct_not_admitted_on_these_spans"
    rec["status"] = "computed" if bulk["status"] == "ok" else "computed_low_alignment_provisional"
    return rec


def _measured_dh(xy_path: Path, station: dict[str, Any], leg_radius: float) -> float:
    """4A/P from the masked convex hull on the cut plane (matches the geometry
    helper in sample_section_mean_pressure.py)."""
    try:
        from scipy.spatial import ConvexHull
        data = np.loadtxt(xy_path)
        if data.ndim == 1:
            data = data.reshape(1, -1)
        pts = data[:, :3]
        center = np.array([station["x"], station["y"], station["z"]])
        mask = np.linalg.norm(pts - center, axis=1) < leg_radius
        mp = pts[mask]
        if mp.shape[0] < 3:
            return float("nan")
        n = np.array([station["nx"], station["ny"], station["nz"]])
        n = n / (np.linalg.norm(n) or 1.0)
        ref = np.array([1.0, 0.0, 0.0]) if abs(n[0]) < 0.9 else np.array([0.0, 1.0, 0.0])
        e1 = ref - np.dot(ref, n) * n
        e1 = e1 / (np.linalg.norm(e1) or 1.0)
        e2 = np.cross(n, e1)
        proj = np.column_stack([mp @ e1, mp @ e2])
        hull = ConvexHull(proj)
        area = float(hull.volume)
        perim = float(hull.area)
        return 4.0 * area / perim if perim > 0 else float("nan")
    except Exception:  # noqa: BLE001
        return float("nan")


# ---------------------------------------------------------------------------
def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--case-dir", required=True, help="Reconstructed case dir (needs T U rho + wallHeatFlux FO).")
    p.add_argument("--time", required=True, help="Converged time to extract.")
    p.add_argument("--source-id", required=True, help="Case source_id (selects locked profile + property model).")
    p.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    p.add_argument("--leg-radius-m", type=float, default=DEFAULT_LEG_RADIUS_M)
    p.add_argument("--radiation-mode", choices=["rad_off", "rad_on"], default="rad_off",
                   help="If rad_on, HTC/UA' are convective-only (wallHeatFlux has no qr column).")
    p.add_argument("--skip-run", action="store_true", help="Parse existing cut-plane dumps; do not call foamPostProcess.")
    p.add_argument("--dry-run", action="store_true",
                   help="Validate inputs + print the per-segment plan WITHOUT requiring T; report B1 if T is missing.")
    p.add_argument("--mesh-length", action="store_true",
                   help="Derive segment length from the MESH centerline (build_mesh_centerlines.py "
                        "mesh_stations.json) instead of the schematic centerline_labels. Corrects the "
                        "T8 lower<->right label swap + ~1.3x length inflation that biases UA'/q' low.")
    p.add_argument("--mesh-stations", default=None,
                   help="Path to mesh_stations.json (default: standard work_products location).")
    p.add_argument("--admit-downcomer", action="store_true",
                   help="Unblock the downcomer (right_leg) thermal segment and admit an INDICATIVE Nu for it "
                        "(T4). Justified: q_w is reconstructed and T is available, and the downcomer is an "
                        "ordinary f(Re)+Nu leg with no recirculation (U3). The downcomer is vertical, so the "
                        "schematic cut-plane orientation is acceptable for its bulk T. Nu is flagged indicative.")
    return p.parse_args()


def detect_T_available(case_dir: Path, time_name: str) -> tuple[bool, str]:
    """Heuristic: is a usable reconstructed T present? (B1 detector)."""
    bases = [case_dir]
    proc = case_dir / "processors64"
    if proc.exists():
        try:
            bases.append(proc.resolve().parent)
        except OSError:
            pass
    # A usable reconstructed T must be at the requested TIME dir (not the decomposed
    # 0/ initial field, which is present even on a source case that cannot be
    # reconstructed). Requiring the time-dir T is what makes B1 detectable.
    for base in bases:
        cand = base / time_name / "T"
        if cand.is_file():
            return True, f"found reconstructed T at {relative_to_workspace(cand)}"
    return False, ("no reconstructed T at the requested time on disk (BLOCKER B1: T carries "
                   "custom BC rcExternalTemperature/libRCWallBC.so; cannot reconstruct with "
                   "the v12 toolchain)")


def main() -> int:
    args = parse_args()
    if args.admit_downcomer:
        # T4: unblock the downcomer and admit an indicative Nu for right_leg.
        THERMALLY_BLOCKED_SEGMENTS.discard("downcomer")
        NU_DIRECT_ADMITTED_SPANS.add("right_leg")
    if args.mesh_length:
        # T8 fix: use mesh-centerline segment lengths (not schematic labels).
        ms_path = Path(args.mesh_stations) if args.mesh_stations else (
            WORKSPACE_ROOT / "work_products" / "2026-07-01_claude_mesh_centerlines"
            / args.source_id / "mesh_stations.json")
        if not ms_path.exists():
            print(f"ERROR: --mesh-length but {relative_to_workspace(ms_path)} missing. "
                  f"Run build_mesh_centerlines.py first.", file=sys.stderr)
            return 2
        MESH_SPAN_LENGTHS.update(load_mesh_span_lengths(ms_path))
        print(f"Using MESH segment lengths (T8 fix): {relative_to_workspace(ms_path)}")
    case_dir = Path(args.case_dir).resolve()
    output_dir = Path(args.output_dir)
    ensure_dir(output_dir)

    # ---- input validation (always) ----
    problems: list[str] = []
    if not case_dir.exists():
        problems.append(f"case-dir does not exist: {case_dir}")
    try:
        frame = build_station_frame(args.source_id)
    except Exception as exc:  # noqa: BLE001
        print(f"FATAL: could not build station frame for source-id {args.source_id!r}: {exc}", file=sys.stderr)
        return 2

    prop = load_property_model(case_dir)
    whf_path = find_wallheatflux_dat(case_dir, args.time) if case_dir.exists() else None
    whf = parse_wallheatflux(whf_path) if whf_path else {}
    t_have, t_msg = detect_T_available(case_dir, args.time) if case_dir.exists() else (False, "case-dir missing")

    print(f"# Segment HTC / UA' / Nu / R' extraction plan")
    print(f"  source_id      : {args.source_id}")
    print(f"  case_dir       : {relative_to_workspace(case_dir)}")
    print(f"  time           : {args.time}")
    print(f"  convergence    : {CONVERGENCE_STATUS.get(args.source_id, 'convergence_unverified')}")
    print(f"  radiation_mode : {args.radiation_mode}"
          + ("  (HTC/UA' convective-only; wallHeatFlux has no qr column)" if args.radiation_mode == "rad_on" else ""))
    print(f"  property model : {'OK ' + str(prop.get('config_path')) if prop['ok'] else 'MISSING (' + prop['reason'] + ')'}")
    print(f"  wallHeatFlux   : {relative_to_workspace(whf_path) if whf_path else 'NOT FOUND'}"
          + (f"  ({len(whf)} patches)" if whf else ""))
    print(f"  T (B1 gate)    : {'AVAILABLE - ' + t_msg if t_have else 'BLOCKED - ' + t_msg}")
    print(f"  bulk T weight  : enthalpy-flux  Σ rho*u_n*cp(T)*T / Σ rho*u_n*cp(T)  (spec §2)")
    print(f"\n  segment      cfd_spans                                   wall_patches(present)  thermal")
    for seg, spans in SEGMENT_TO_SPANS.items():
        profile = get_case_analysis_profile(args.source_id)
        npat = sum(len(profile.major_spans[s]["wall_patches"]) for s in spans)
        present = sum(1 for s in spans for pp in profile.major_spans[s]["wall_patches"] if pp in whf)
        blocked = "BLOCKED(right_leg)" if seg in THERMALLY_BLOCKED_SEGMENTS else (
            "Nu+UA'+HTC" if any(s in NU_DIRECT_ADMITTED_SPANS for s in spans) else "UA'+HTC")
        print(f"  {seg:11s}  {'+'.join(spans):42s}  {present:2d}/{npat:<2d}                 {blocked}")

    if not whf:
        problems.append("wallHeatFlux .dat not found or empty -> cannot compute q_w / q'_wall")
    if not prop["ok"]:
        problems.append(f"property model unavailable: {prop['reason']} -> cannot evaluate cp(T)/k(T)")

    if args.dry_run:
        print("\n[--dry-run] No extraction performed.")
        if not t_have:
            print("[--dry-run] BLOCKER B1 ACTIVE: T cannot be reconstructed with the v12 toolchain")
            print("            (custom BC rcExternalTemperature / libRCWallBC.so not on LS6).")
            print("            q_w / q'_wall / perimeter ARE computable now; T_wall, T_bulk, ΔT, HTC,")
            print("            UA', R', Nu require B1 (recover OF13 runtime + libRCWallBC.so; lane L4).")
        if problems:
            print("\n[--dry-run] input issues:")
            for pr in problems:
                print(f"    - {pr}")
        else:
            print("[--dry-run] inputs OK for the duty (q_w/q') stage; thermal stage gated on B1.")
        # still emit the plan as JSON so the dry-run is a durable artifact
        json_dump(output_dir / f"thermal_extraction_plan_{args.source_id}.json", {
            "generated_at": iso_timestamp(),
            "mode": "dry-run",
            "source_id": args.source_id,
            "case_dir": relative_to_workspace(case_dir),
            "time": args.time,
            "T_available": t_have,
            "blocker_B1_active": not t_have,
            "blocker_B1": ("T carries custom BC rcExternalTemperature/libRCWallBC.so; "
                           "cannot reconstruct with OF v12 on LS6"),
            "property_model_ok": prop["ok"],
            "wallheatflux_found": bool(whf),
            "segment_map": SEGMENT_TO_SPANS,
            "thermally_blocked_segments": sorted(THERMALLY_BLOCKED_SEGMENTS),
            "nu_direct_admitted_spans": sorted(NU_DIRECT_ADMITTED_SPANS),
            "bulk_T_definition": "enthalpy-flux-weighted mixed mean: int rho*u_n*cp(T)*T dA / int rho*u_n*cp(T) dA",
            "input_problems": problems,
        })
        print(f"\nWrote {relative_to_workspace(output_dir / ('thermal_extraction_plan_' + args.source_id + '.json'))}")
        return 0

    # ---- full run ----
    if problems:
        print("\nFATAL input issues (use --dry-run to inspect the plan):", file=sys.stderr)
        for pr in problems:
            print(f"  - {pr}", file=sys.stderr)
        return 2
    if not t_have:
        print("\nFATAL: BLOCKER B1 — reconstructed T not found; cannot compute thermal closure.", file=sys.stderr)
        print(f"  {t_msg}", file=sys.stderr)
        print("  Re-run with --dry-run for the plan, or clear B1 (OF13 runtime + libRCWallBC.so).", file=sys.stderr)
        return 3

    if not args.skip_run:
        stations = []
        for spans in SEGMENT_TO_SPANS.values():
            st = bulk_station_for_span(frame, args.source_id, spans[0])
            if st:
                stations.append(st)
        write_controldict(case_dir, stations)
        log = output_dir / f"foampostprocess_{args.source_id}.log"
        print(f"\nRunning foamPostProcess (raw plane dump; mesh re-stitch 1-2 min)... {relative_to_workspace(log)}")
        rc = run_foampostprocess(case_dir, args.time, log)
        if rc != 0:
            print(f"WARNING: foamPostProcess rc={rc}; parsing whatever exists.")

    records = [
        segment_record(seg, spans, frame, whf, args.source_id, t_have,
                       prop["cp_coeffs"], prop["k_coeffs"], case_dir, args.leg_radius_m,
                       args.radiation_mode, args.time)
        for seg, spans in SEGMENT_TO_SPANS.items()
    ]
    payload = {
        "generated_at": iso_timestamp(),
        "source_id": args.source_id,
        "case_dir": relative_to_workspace(case_dir),
        "time": args.time,
        "definitions": {
            "HTC": "h = q_w / (T_wall - T_bulk)  [W/m^2/K]",
            "UAprime": "q'_wall / (T_wall - T_bulk)  [W/m/K]  (PRIMARY)",
            "R_prime_thermal": "1 / UAprime  [m*K/W]",
            "Nu": "h * D_h / k(T_bulk)  [1]  (direct only on left_lower_leg)",
            "T_bulk": "enthalpy-flux-weighted mixed mean: int rho*u_n*cp(T)*T dA / int rho*u_n*cp(T) dA",
        },
        "caveats": {
            "mesh": "coarse only; mesh-independence UNESTABLISHED (B2)",
            "qr": ("convective-only; wallHeatFlux FO has no qr column"
                   if args.radiation_mode == "rad_on" else "qr not applicable (rad_off)"),
            "nu": "Nu(Re,Pr) not identifiable; direct Nu defended on left_lower_leg only, narrow laminar Re",
            "convergence": CONVERGENCE_STATUS.get(args.source_id, "convergence_unverified"),
        },
        "segments": records,
    }
    json_dump(output_dir / f"segment_htc_uaprime_{args.source_id}.json", payload)
    keys = sorted({k for r in records for k in r.keys()})
    csv_dump(output_dir / f"segment_htc_uaprime_{args.source_id}.csv", keys,
             [{k: r.get(k, "") for k in keys} for r in records])

    print(f"\n# Segment thermal closure  {args.source_id}  t={args.time}")
    print(f"{'segment':11s} {'q_w':>10s} {'q_prime':>10s} {'Tbulk':>8s} {'Twall':>8s} {'HTC':>9s} {'UAprime':>9s} {'Rprime':>9s} {'Nu':>7s}  status")
    for r in records:
        print(f"{r['segment']:11s} {r.get('q_w_wm2', float('nan')):10.2f} {r.get('qprime_wall_wm', float('nan')):10.2f} "
              f"{r.get('T_bulk_k', float('nan')):8.2f} {r.get('T_wall_k', float('nan')):8.2f} "
              f"{r.get('htc_wm2k', float('nan')):9.3f} {r.get('uaprime_wmk', float('nan')):9.3f} "
              f"{r.get('R_prime_thermal_mkw', float('nan')):9.4f} {r.get('Nu', float('nan')):7.3f}  {r.get('status','')}")
    print(f"\nWrote {relative_to_workspace(output_dir / ('segment_htc_uaprime_' + args.source_id + '.json'))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
