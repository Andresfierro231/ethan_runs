#!/usr/bin/env bash
set -euo pipefail

MODE="${1:-preflight}"
ATTACH_JOB_ID="${ATTACH_JOB_ID:-3288671}"
ATTACH_NODE="${ATTACH_NODE:-c318-017}"
NTASKS="${NTASKS:-64}"

CAMPAIGN="/scratch/09748/andresfierro231/projects_scratch/ethan_runs/jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations"
CASE_KEY="salt4_jin_hi10q_corrected"
CASE_DIR="${CAMPAIGN}/runs/${CASE_KEY}/case_stage/viscosity_screening_salt_test_4_jin_coarse_mesh_continuation"
OPENFOAM_ENV_SH="${OPENFOAM13_ENV_SH:-/scratch/09748/andresfierro231/projects_scratch/ethan_runs/jadyn_runs/salt2/2026-06-02_runtime_recovery/scripts/of13-env.sh}"
RCWALLBC_LIBDIR="${RCWALLBC_LIBDIR:-/scratch/09748/andresfierro231/projects_scratch/ethan_runs/jadyn_runs/modern_runs/2026-06-25_ethan_normal_relaunch_and_recirculation_boundary_wave/runtime_libs}"
RESTART_TIME="11536"
LOG_PATH="${CASE_DIR}/logs/log.foamRun_salt4_hi10q_weekend_attach"

if [[ "${MODE}" != "preflight" && "${MODE}" != "launch" ]]; then
  echo "Usage: $0 [preflight|launch]" >&2
  exit 2
fi

if [[ ! -d "${CASE_DIR}" ]]; then
  echo "Missing case directory: ${CASE_DIR}" >&2
  exit 3
fi
if [[ ! -r "${OPENFOAM_ENV_SH}" ]]; then
  echo "OpenFOAM env script not readable: ${OPENFOAM_ENV_SH}" >&2
  exit 4
fi
if [[ ! -r "${RCWALLBC_LIBDIR}/libRCWallBC.so" ]]; then
  echo "Missing libRCWallBC.so under ${RCWALLBC_LIBDIR}" >&2
  exit 5
fi
if [[ ! -r "${CASE_DIR}/processors64/${RESTART_TIME}/T" ]]; then
  echo "Restart ${RESTART_TIME} is missing decomposed T" >&2
  exit 6
fi
if grep -R -n -E 'stopAtControl::writeNow|stopAt[[:space:]]*\([[:space:]]*writeNow' \
    "${CASE_DIR}/system/controlDict" "${CASE_DIR}/system/functions"; then
  echo "Unsafe writeNow stop monitor remains in Salt4 +10Q case" >&2
  exit 7
fi
if ! grep -q 'startFrom[[:space:]]*startTime' "${CASE_DIR}/system/controlDict"; then
  echo "Salt4 +10Q controlDict is not pinned to startTime" >&2
  exit 8
fi
if ! grep -q 'startTime[[:space:]]*11536' "${CASE_DIR}/system/controlDict"; then
  echo "Salt4 +10Q controlDict is not pinned to restart time 11536" >&2
  exit 9
fi
if ! grep -q 'timeFormat[[:space:]]*general' "${CASE_DIR}/system/controlDict"; then
  echo "Salt4 +10Q controlDict is not using general time names" >&2
  exit 10
fi
if ! grep -q 'timePrecision[[:space:]]*6' "${CASE_DIR}/system/controlDict"; then
  echo "Salt4 +10Q controlDict is not using repaired timePrecision 6" >&2
  exit 11
fi

set +eu
source "${OPENFOAM_ENV_SH}"
source_status=$?
set -eu
if [[ "${source_status}" -ne 0 ]]; then
  echo "Failed to source ${OPENFOAM_ENV_SH}" >&2
  exit "${source_status}"
fi

unset FOAM_SIGFPE
export OMP_NUM_THREADS=1
export LD_LIBRARY_PATH="${RCWALLBC_LIBDIR}:${LD_LIBRARY_PATH:-}"
export I_MPI_PMI_LIBRARY="${I_MPI_PMI_LIBRARY:-/usr/lib64/libpmi2.so}"

FOAMRUN_BIN="${FOAMRUN_BIN:-$(command -v foamRun)}"
if [[ -z "${FOAMRUN_BIN}" || ! -x "${FOAMRUN_BIN}" ]]; then
  echo "foamRun not found after sourcing runtime" >&2
  exit 12
fi

mkdir -p "${CASE_DIR}/logs"
if [[ "${MODE}" == "preflight" ]]; then
  echo "preflight_ok case=${CASE_KEY} restart=${RESTART_TIME} attach_job=${ATTACH_JOB_ID} node=${ATTACH_NODE} ntasks=${NTASKS}"
  exit 0
fi

{
  echo ""
  echo "==== Salt4 +10Q weekend attach $(date --iso-8601=seconds) ===="
  echo "case=${CASE_KEY}"
  echo "attach_job=${ATTACH_JOB_ID}"
  echo "attach_node=${ATTACH_NODE}"
  echo "restart_time=${RESTART_TIME}"
  echo "ntasks=${NTASKS}"
} >> "${LOG_PATH}"

cd "${CASE_DIR}"
srun --jobid="${ATTACH_JOB_ID}" --exclusive --exact --nodes=1 --ntasks="${NTASKS}" \
  --nodelist="${ATTACH_NODE}" --cpu-bind=cores --distribution=block:block --mpi=pmi2 \
  "${FOAMRUN_BIN}" -parallel >> "${LOG_PATH}" 2>&1
