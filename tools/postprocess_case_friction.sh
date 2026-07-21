#!/usr/bin/env bash
# =============================================================================
# postprocess_case_friction.sh
#
# PURPOSE
# -------
# Extract the full hydraulic friction closure (f/f_lam, Re, buoyancy-corrected
# friction gradient) from a single OpenFOAM case that exists only in decomposed
# form (processors<N>/ directories).  Produces the same segment_friction.csv
# and momentum_budget.json outputs used by the 1D gap-analysis pipeline.
#
# The script is the direct equivalent of the Salt 2/3/4 postprocessing
# campaign (AGENT-162/T1b) but written as a single self-contained driver so
# any future case can be processed without reconstructing the full pipeline
# from journal notes.
#
# WHAT IT DOES (in order)
# -----------------------
#   Step 0  Validate inputs and locate the OF13 environment.
#   Step 1  (optional) Build mesh-true centerlines via build_mesh_centerlines.py
#             – skipped automatically if mesh_stations.json already exists for
#             the requested source_id OR a same-mesh donor case is specified.
#             Runtime: ~30 s (pure Python, no OF calls).
#   Step 2  Reconstruct a single time step from the decomposed case.
#             Uses reconstructPar with -fields (T p_rgh U rho) so only the
#             fields needed for section-pressure sampling are written.
#             Runtime: ~5–15 min depending on Lustre I/O.
#             Disk: ~500 MB per time step (all 64 procs merged into one dir).
#   Step 3  Sample cross-section mean pressure + velocity profiles at each
#             loop station using foamPostProcess (cutting planes).
#             Runtime: ~1–2 min (mesh re-stitch dominates).
#             Writes: section_mean_pressure_<source_id>.json/.csv
#   Step 4  Derive segment friction (f, Re, f/f_lam) from section profiles.
#             Uses --auto-mu-jin: infers T from rho EoS then evaluates Jin mu.
#             Runtime: <1 min (pure Python).
#             Writes: segment_friction.csv/.json (appends to existing file)
#   Step 5  Derive streamwise momentum budget (buoyancy-corrected dP/ds).
#             The buoyancy correction strips the hydrostatic body force from
#             the p_rgh gradient so only the friction component remains.
#             Runtime: <1 min (pure Python).
#             Writes: momentum_budget.json/.csv (appends)
#
# USAGE
# -----
#   bash tools/postprocess_case_friction.sh [OPTIONS]
#
# REQUIRED OPTIONS
#   --case-dir PATH       Absolute path to the OpenFOAM continuation case dir.
#                         Must contain processors<N>/ subdirs.
#   --source-id STRING    Canonical case identifier, e.g.
#                         viscosity_screening_salt_test_1_jin_coarse_mesh
#   --time FLOAT          Simulation time (seconds) to reconstruct and sample.
#                         Should be a converged pseudo-steady time.
#
# OPTIONAL
#   --output-dir PATH     Where to write section_mean_pressure, segment_friction,
#                         and momentum_budget outputs.
#                         Default: work_products/2026-07-04_salt1_friction/
#   --donor-source-id ID  Another source_id whose mesh_stations.json can be
#                         reused (valid when both cases share the same mesh
#                         group ID).  Use for Salt 1, which shares mesh
#                         7ab7fb2650596980 with Salt 2/3/4.
#                         Default: viscosity_screening_salt_test_2_jin_coarse_mesh
#   --recon-dir PATH      Where to write the reconstructed serial time directory.
#                         Default: /tmp/recon_<source_id>_<time>/
#                         (You can point this at scratch to save /tmp quota.)
#   --of-env-script PATH  Relative path to the OF13 env script from REPO root.
#                         Default: tools/ofenv/of13_env.sh
#   --skip-recon          Skip Step 2 (reconstruction) if the time directory
#                         already exists in --recon-dir.
#   --skip-mesh           Skip Step 1 (centerline build) even if
#                         mesh_stations.json is missing (use with care).
#   --dry-run             Print the commands that would be run without running.
#
# EXAMPLES
# --------
#   # Salt 1 Jin — first time (all steps):
#   bash tools/postprocess_case_friction.sh \
#     --case-dir jadyn_runs/modern_runs/2026-06-18_convergence_and_jin_envelope_wave/runs/salt1_jin/case_stage/viscosity_screening_salt_test_1_jin_coarse_mesh_continuation \
#     --source-id viscosity_screening_salt_test_1_jin_coarse_mesh \
#     --time 3756 \
#     --donor-source-id viscosity_screening_salt_test_2_jin_coarse_mesh \
#     --recon-dir /tmp/recon_salt1_jin_3756
#
#   # Re-run analysis only (reconstruction already done):
#   bash tools/postprocess_case_friction.sh \
#     --case-dir <...> --source-id <...> --time 3756 --skip-recon
#
#   # Dry run to preview commands:
#   bash tools/postprocess_case_friction.sh \
#     --case-dir <...> --source-id <...> --time 3756 --dry-run
#
# TIMING ESTIMATE (interactive compute node, Lustre scratch)
#   Step 1: ~30 s
#   Step 2: ~5–15 min   (bottleneck; depends on proc count and Lustre load)
#   Step 3: ~1–2 min
#   Step 4: ~30 s
#   Step 5: ~30 s
#   TOTAL:  ~7–18 min
#
# OUTPUTS
#   <output-dir>/section_mean_pressure_<source_id>.json    — per-station p/U/rho
#   <output-dir>/section_mean_pressure_<source_id>.csv
#   <output-dir>/foampostprocess_<source_id>.log           — OF13 run log
#   <output-dir>/segment_friction.json                     — f, Re, f/f_lam
#   <output-dir>/segment_friction.csv
#   <output-dir>/momentum_budget.json                      — buoyancy-corrected
#   <output-dir>/momentum_budget.csv
#
# NOTES ON THE OF13 ENVIRONMENT
#   The OF13 binaries were built with gcc/15.2.0.  The system default
#   gcc/9.4.0 lacks GLIBCXX_3.4.32 → reconstructPar / foamPostProcess crash
#   with "version not found".  of13_env.sh prepends the gcc/15.2.0 lib64 to
#   LD_LIBRARY_PATH before invoking any OF13 binary.
#
# NOTES ON MESH CENTERLINES
#   All cases in the coarse-mesh family share mesh group ID 7ab7fb2650596980
#   (same blockMesh / NCC geometry).  mesh_stations.json is mesh-geometry only
#   (station XYZ + normal vectors) and is therefore identical across all cases
#   in the family.  Building it once for Salt 2 and reusing for Salt 1 is
#   correct by construction.  --donor-source-id makes this explicit.
#
# NOTES ON THE BUOYANCY CORRECTION (Step 5)
#   The raw p_rgh gradient includes the gravitational body force on the fluid
#   column, which is the DRIVE of the natural circulation, not friction.
#   derive_streamwise_momentum_budget strips ρg·ŝ (where ŝ is the streamwise
#   unit vector) from each span's mean gradient so that the residual is pure
#   friction.  Only the interior stations (not fitting ends) are used so that
#   local minor-loss spikes at bends don't contaminate the straight-leg
#   gradient.  Single-leg values on heated/cooled legs can still go slightly
#   negative due to coarse-mesh buoyancy-source accumulation artefacts;
#   see memory/friction-buoyancy-source-finding.md for context.
# =============================================================================

set -euo pipefail

# ── locate repo root ──────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${ROOT}"

# ── defaults ──────────────────────────────────────────────────────────────────
CASE_DIR=""
SOURCE_ID=""
TIME_VAL=""
OUTPUT_DIR=""                                # filled in after parsing if empty
DONOR_SOURCE_ID="viscosity_screening_salt_test_2_jin_coarse_mesh"
RECON_DIR=""                                  # filled in after parsing if empty
OF_ENV_SCRIPT="tools/ofenv/of13_env.sh"
SKIP_RECON=false
SKIP_MESH=false
DRY_RUN=false

# ── argument parsing ──────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
    case "$1" in
        --case-dir)        CASE_DIR="$(realpath "$2")"; shift 2 ;;
        --source-id)       SOURCE_ID="$2";               shift 2 ;;
        --time)            TIME_VAL="$2";                shift 2 ;;
        --output-dir)      OUTPUT_DIR="$2";              shift 2 ;;
        --donor-source-id) DONOR_SOURCE_ID="$2";         shift 2 ;;
        --recon-dir)       RECON_DIR="$2";               shift 2 ;;
        --of-env-script)   OF_ENV_SCRIPT="$2";           shift 2 ;;
        --skip-recon)      SKIP_RECON=true;              shift   ;;
        --skip-mesh)       SKIP_MESH=true;               shift   ;;
        --dry-run)         DRY_RUN=true;                 shift   ;;
        --help|-h)
            sed -n '/^# PURPOSE/,/^# ===/p' "${BASH_SOURCE[0]}" | head -n -1 | sed 's/^# \{0,1\}//'
            exit 0 ;;
        *) echo "ERROR: unknown option '$1'" >&2; exit 1 ;;
    esac
done

# ── validate required args ────────────────────────────────────────────────────
[[ -z "$CASE_DIR"   ]] && { echo "ERROR: --case-dir is required"   >&2; exit 1; }
[[ -z "$SOURCE_ID"  ]] && { echo "ERROR: --source-id is required"  >&2; exit 1; }
[[ -z "$TIME_VAL"   ]] && { echo "ERROR: --time is required"       >&2; exit 1; }

# ── fill defaults that depend on parsed values ────────────────────────────────
if [[ -z "$OUTPUT_DIR" ]]; then
    # Timestamped subdirectory inside the canonical salt1 work product dir.
    # Using a fixed path so results accumulate predictably.
    OUTPUT_DIR="${ROOT}/work_products/2026-07-04_salt1_friction"
fi
if [[ -z "$RECON_DIR" ]]; then
    RECON_DIR="/tmp/recon_${SOURCE_ID}_${TIME_VAL}"
fi
MESH_CENTER_DIR="${ROOT}/work_products/2026-07-01_claude_mesh_centerlines"
MESH_STATIONS="${MESH_CENTER_DIR}/${SOURCE_ID}/mesh_stations.json"
DONOR_STATIONS="${MESH_CENTER_DIR}/${DONOR_SOURCE_ID}/mesh_stations.json"

# ── helpers ───────────────────────────────────────────────────────────────────
log() { echo "[$(date +%H:%M:%S)] $*"; }
run() {
    # Print the command; execute it only when not in dry-run mode.
    echo "  CMD: $*"
    if [[ "$DRY_RUN" == false ]]; then
        eval "$@"
    fi
}
elapsed_since() {
    # Print wall-clock seconds since the given epoch second.
    echo "$(( $(date +%s) - $1 )) s"
}

# ── banner ────────────────────────────────────────────────────────────────────
log "========================================================"
log "postprocess_case_friction.sh"
log "  source_id  : ${SOURCE_ID}"
log "  time       : ${TIME_VAL} s"
log "  case_dir   : ${CASE_DIR}"
log "  recon_dir  : ${RECON_DIR}"
log "  output_dir : ${OUTPUT_DIR}"
log "  dry_run    : ${DRY_RUN}"
log "========================================================"

# ── Step 0: validate inputs ───────────────────────────────────────────────────
log "Step 0: validating inputs..."

[[ -d "$CASE_DIR" ]] || { echo "ERROR: case_dir not found: $CASE_DIR" >&2; exit 1; }

# Check processors directory exists (case is decomposed)
PROC_DIR=$(ls -d "${CASE_DIR}"/processors* 2>/dev/null | head -1 || true)
if [[ -z "$PROC_DIR" ]]; then
    echo "ERROR: no processors<N> directory found in ${CASE_DIR}" >&2
    echo "       Is this actually a decomposed case?" >&2
    exit 1
fi
log "  Found decomposed data: $(basename $PROC_DIR)"

# Check OF13 env script
[[ -f "${ROOT}/${OF_ENV_SCRIPT}" ]] || {
    echo "ERROR: OF13 env script not found: ${ROOT}/${OF_ENV_SCRIPT}" >&2
    echo "       Required for GLIBCXX_3.4.32 (gcc/15.2.0 libstdc++)." >&2
    exit 1
}
log "  OF env script: OK (${OF_ENV_SCRIPT})"

# Make output directory
mkdir -p "${OUTPUT_DIR}"
log "  Output dir: ${OUTPUT_DIR}"

T_TOTAL_START=$(date +%s)

# ── Step 1: mesh centerlines ──────────────────────────────────────────────────
log ""
log "Step 1: mesh-true centerlines (mesh_stations.json)..."
T1_START=$(date +%s)

if [[ -f "$MESH_STATIONS" ]]; then
    log "  SKIP: mesh_stations.json already exists for ${SOURCE_ID}."
    log "       ${MESH_STATIONS}"

elif [[ -f "$DONOR_STATIONS" && "$SKIP_MESH" == false ]]; then
    # All coarse-mesh cases share mesh group 7ab7fb2650596980.
    # The mesh_stations.json encodes only geometry (station XYZ + tangents),
    # so the donor's file is identical for any same-mesh case.
    log "  Reusing donor mesh_stations.json (same mesh group 7ab7fb2650596980)."
    log "  Donor: ${DONOR_SOURCE_ID}"
    mkdir -p "${MESH_CENTER_DIR}/${SOURCE_ID}"
    run "cp '${DONOR_STATIONS}' '${MESH_STATIONS}'"
    log "  Copied to: ${MESH_STATIONS}"

elif [[ "$SKIP_MESH" == true ]]; then
    log "  WARNING: --skip-mesh set but ${MESH_STATIONS} is missing."
    log "           foamPostProcess will fall back to profile (schematic) centerlines."
    log "           These mis-orient the heater / swap lower<->right labels."
    log "           Only proceed if you know what you're doing."

else
    # Full build: run the mesh centerline extractor.
    # This is a parallel-safe pure-Python + OF13 postProcess tool.
    # It reads only the mesh geometry (constant/polyMesh), not field data.
    log "  Building mesh centerlines from scratch (no donor available)..."
    run "python3 tools/extract/build_mesh_centerlines.py \
        --case-dir '${CASE_DIR}' \
        --source-id '${SOURCE_ID}' \
        --time '${TIME_VAL}' \
        --output-dir '${MESH_CENTER_DIR}/${SOURCE_ID}'"
    log "  Built: ${MESH_STATIONS}"
fi
log "  Step 1 done in $(elapsed_since $T1_START)"

# ── Step 2: reconstruct single time step ─────────────────────────────────────
log ""
log "Step 2: reconstructPar  (t = ${TIME_VAL} s)..."
T2_START=$(date +%s)

RECON_TIME_DIR="${RECON_DIR}/${TIME_VAL}"

if [[ "$SKIP_RECON" == true ]]; then
    log "  SKIP: --skip-recon set."
    if [[ ! -d "$RECON_TIME_DIR" ]]; then
        echo "ERROR: --skip-recon set but reconstructed time dir not found:" >&2
        echo "       ${RECON_TIME_DIR}" >&2
        exit 1
    fi
    log "  Found existing: ${RECON_TIME_DIR}"

elif [[ -d "$RECON_TIME_DIR" ]]; then
    log "  SKIP: reconstructed time dir already exists: ${RECON_TIME_DIR}"

else
    # reconstructPar needs:
    #   1. The case to be linked/staged in RECON_DIR (constant/ system/ 0/)
    #   2. The processors64/ dirs symlinked or present
    # Simplest approach: run reconstructPar directly on the original CASE_DIR
    # with -time to limit scope, writing serial output into the CASE_DIR itself,
    # then move the time dir to RECON_DIR.
    #
    # IMPORTANT: reconstructPar needs OF13's gcc/15.2.0 libstdc++ (see of13_env.sh).
    # The system default gcc/9.4.0 fails with GLIBCXX_3.4.32 not found.
    #
    # We only reconstruct (T p_rgh U rho) — the 4 fields needed for section
    # pressure + friction analysis.  This is ~4× faster than reconstructing all
    # fields (avoids Re, Ra, Ri, Nu, phi, nuEff, etc.).

    log "  Staging reconstruction directory: ${RECON_DIR}"
    mkdir -p "${RECON_DIR}"

    # Soft-link or stage the case so reconstructPar writes to RECON_DIR
    # Strategy: copy constant/ and system/, symlink processors<N>
    if [[ ! -d "${RECON_DIR}/constant" ]]; then
        run "cp -r '${CASE_DIR}/constant' '${RECON_DIR}/constant'"
        run "cp -r '${CASE_DIR}/system'   '${RECON_DIR}/system'"
        # Copy the initial 0/ dir (mesh boundary conditions; no large fields)
        run "cp -r '${CASE_DIR}/0'        '${RECON_DIR}/0'"
    fi

    # Symlink the processors directory into RECON_DIR
    PROC_BASENAME=$(basename "$PROC_DIR")
    if [[ ! -e "${RECON_DIR}/${PROC_BASENAME}" ]]; then
        run "ln -s '${PROC_DIR}' '${RECON_DIR}/${PROC_BASENAME}'"
    fi

    # Remove system/functions if present — it contains yPlus/turbulenceFields/mdot
    # monitors from the live run, which crash foamPostProcess with
    # "Unable to find turbulence model" because there's no running solver.
    # Our written controlDict (Step 3 / write_controldict) replaces controlDict
    # only; system/functions is read additionally by OF13 and must be removed.
    if [[ -f "${RECON_DIR}/system/functions" ]]; then
        log "  Removing system/functions (live-run monitors not compatible with postProcess)."
        run "rm '${RECON_DIR}/system/functions'"
    fi

    RECON_LOG="${OUTPUT_DIR}/reconstructpar_${SOURCE_ID}_t${TIME_VAL}.log"
    log "  Running reconstructPar (log: $(basename $RECON_LOG))..."
    log "  Estimated time: 5–15 min"

    # Source the OF13 env (for GLIBCXX_3.4.32) before running reconstructPar
    run "bash -lc \"
        source '${ROOT}/${OF_ENV_SCRIPT}' >/dev/null 2>&1
        reconstructPar \
            -case '${RECON_DIR}' \
            -time '${TIME_VAL}' \
            -fields '(T p_rgh U rho)' \
        2>&1 | tee '${RECON_LOG}'
    \""
fi

# Always ensure system/functions is absent before foamPostProcess, regardless
# of whether we just reconstructed or skipped reconstruction.
if [[ -f "${RECON_DIR}/system/functions" && "$DRY_RUN" == false ]]; then
    log "  Removing system/functions from recon dir (incompatible with postProcess)."
    rm "${RECON_DIR}/system/functions"
fi

log "  Step 2 done in $(elapsed_since $T2_START)"
log "  Reconstructed fields in: ${RECON_DIR}/${TIME_VAL}"

# ── Step 3: section mean pressure ────────────────────────────────────────────
log ""
log "Step 3: foamPostProcess — cross-section mean p/U/rho..."
T3_START=$(date +%s)
log "  Estimated time: 1–2 min (cutting plane mesh re-stitch)"

SECTION_JSON="${OUTPUT_DIR}/section_mean_pressure_${SOURCE_ID}.json"

if [[ -f "$SECTION_JSON" ]]; then
    log "  Note: ${SECTION_JSON} already exists — will be overwritten."
fi

run "python3 tools/extract/sample_section_mean_pressure.py \
    --case-dir '${RECON_DIR}' \
    --time '${TIME_VAL}' \
    --source-id '${SOURCE_ID}' \
    --output-dir '${OUTPUT_DIR}' \
    --of-env-script '${OF_ENV_SCRIPT}' \
    --centerline-source mesh \
    --dump-temperature"

# Note: --dump-temperature requires T to be present in the reconstructed case,
# which is why we included T in the reconstructPar -fields list.
# If T is absent, remove --dump-temperature and rerun.

log "  Step 3 done in $(elapsed_since $T3_START)"
log "  Section mean pressure written to: ${SECTION_JSON}"

# ── Step 4: segment friction ──────────────────────────────────────────────────
log ""
log "Step 4: derive_segment_friction (f, Re, f/f_lam)..."
T4_START=$(date +%s)

# --auto-mu-jin: infers bulk T from section mean rho via the salt EoS
#   (T = (2293.6 - rho) / 0.7497) and evaluates the Jin viscosity correlation.
#   This is the correct choice for all Salt Jin cases.
#   For Kirst cases, omit --auto-mu-jin and pass --mu-pa-s <value> instead.
#
# --drop-fitting-ends: excludes stations flagged as is_fitting_end (the first
#   and last stations of each span, placed just inside the fittings/bends).
#   Their one-sided pressure tangents and minor-loss pressure jumps contaminate
#   the straight-pipe friction gradient.  Always use this with mesh centerlines.

run "python3 tools/analyze/derive_segment_friction.py \
    --input-dir '${OUTPUT_DIR}' \
    --auto-mu-jin \
    --drop-fitting-ends \
    --output-dir '${OUTPUT_DIR}'"

log "  Step 4 done in $(elapsed_since $T4_START)"
log "  Segment friction written to: ${OUTPUT_DIR}/segment_friction.csv"

# ── Step 5: streamwise momentum budget ───────────────────────────────────────
log ""
log "Step 5: derive_streamwise_momentum_budget (buoyancy-corrected dP/ds)..."
T5_START=$(date +%s)

# The momentum budget strips the gravitational body force (ρg·ŝ per unit
# length along the pipe axis) from the measured p_rgh gradient.  The residual
# is the pure friction component, the correct quantity for f/f_lam comparison.
#
# Sign convention: the body force contribution is POSITIVE on upward legs
# (opposes flow / resists buoyancy) and NEGATIVE on downward legs (aids flow).
# The corrected gradient represents the TRUE friction loss magnitude.
#
# Output: friction_grad_corrected_pa_m per span (used in 1D ΔP comparison).

run "python3 tools/analyze/derive_streamwise_momentum_budget.py \
    --input-dir '${OUTPUT_DIR}' \
    --output-dir '${OUTPUT_DIR}'"

log "  Step 5 done in $(elapsed_since $T5_START)"
log "  Momentum budget written to: ${OUTPUT_DIR}/momentum_budget.json"

# ── summary ───────────────────────────────────────────────────────────────────
log ""
log "========================================================"
log "ALL STEPS COMPLETE in $(elapsed_since $T_TOTAL_START)"
log "Outputs in: ${OUTPUT_DIR}"
log ""
log "Key files:"
log "  section_mean_pressure_${SOURCE_ID}.csv   — raw per-station profiles"
log "  segment_friction.csv                      — f, Re, f/f_lam per span"
log "  momentum_budget.json                      — buoyancy-corrected friction"
log ""
log "To add Salt 1 to the f(Re) fit, run:"
log "  python3 work_products/2026-07-04_jin_perleg_gap_analysis/run_jin_perleg_gap_analysis.py"
log "  (Step 4 of that script reads segment_friction.csv for all available salts)"
log "========================================================"
