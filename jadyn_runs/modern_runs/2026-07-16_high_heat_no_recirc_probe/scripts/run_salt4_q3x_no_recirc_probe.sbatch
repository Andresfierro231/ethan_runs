#!/usr/bin/env bash
#SBATCH -J salt4_q3x_probe
#SBATCH -A ASC23046
#SBATCH -p NuclearEnergy
#SBATCH -N 1
#SBATCH -n 64
#SBATCH -t 120:00:00
#SBATCH -o /scratch/09748/andresfierro231/projects_scratch/ethan_runs/jadyn_runs/modern_runs/2026-07-16_high_heat_no_recirc_probe/slurm-%x-%j.out
#SBATCH -e /scratch/09748/andresfierro231/projects_scratch/ethan_runs/jadyn_runs/modern_runs/2026-07-16_high_heat_no_recirc_probe/slurm-%x-%j.err

set -euo pipefail

REPO_ROOT="/scratch/09748/andresfierro231/projects_scratch/ethan_runs"
CAMPAIGN="${REPO_ROOT}/jadyn_runs/modern_runs/2026-07-16_high_heat_no_recirc_probe"
CASE_KEY="salt4_jin_q3x_no_recirc_probe"
DISPLAY_NAME="salt4_q3x_no_recirc_probe"
CASE_DIR="${CAMPAIGN}/runs/${CASE_KEY}/case_stage/viscosity_screening_salt_test_4_jin_coarse_mesh_continuation"
MANIFEST="${CAMPAIGN}/high_heat_probe_manifest.csv"
PATCHER="${REPO_ROOT}/jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations/scripts/patch_q_fields.py"
PREFLIGHT_CHECKER="${REPO_ROOT}/tools/analyze/check_corrected_salt_preflight.py"
PYTHON_BIN="${PYTHON_BIN:-/usr/bin/python3.11}"
OPENFOAM_ENV_SH="${OPENFOAM13_ENV_SH:-${REPO_ROOT}/jadyn_runs/salt2/2026-06-02_runtime_recovery/scripts/of13-env.sh}"
RCWALLBC_LIBDIR="${RCWALLBC_LIBDIR:-${REPO_ROOT}/jadyn_runs/modern_runs/2026-06-25_ethan_normal_relaunch_and_recirculation_boundary_wave/runtime_libs}"
TIME_FORMAT=general
TIME_PRECISION=6
NTASKS_PER_CASE=64
RESTART_TIME=10000

mkdir -p "${CAMPAIGN}/logs" "${CASE_DIR}/logs"

echo "[$(date --iso-8601=seconds)] ${DISPLAY_NAME} high-heat no-recirc probe"
echo "SLURM_JOB_ID=${SLURM_JOB_ID:-unknown}"
echo "CASE_DIR=${CASE_DIR}"
echo "RESTART_TIME=${RESTART_TIME}"
echo "MANIFEST=${MANIFEST}"

if [[ ! -r "${OPENFOAM_ENV_SH}" ]]; then
  echo "OpenFOAM env script not readable: ${OPENFOAM_ENV_SH}" >&2
  exit 10
fi
if [[ ! -r "${RCWALLBC_LIBDIR}/libRCWallBC.so" ]]; then
  echo "Missing libRCWallBC.so under: ${RCWALLBC_LIBDIR}" >&2
  exit 11
fi
if grep -R -n -E 'stopAtControl::writeNow|stopAt[[:space:]]*\([[:space:]]*writeNow' \
    "${CASE_DIR}/system/controlDict" "${CASE_DIR}/system/functions"; then
  echo "ERROR: writeNow stop monitor remains active; refusing high-heat continuation." >&2
  exit 12
fi

set +eu
source "${OPENFOAM_ENV_SH}"
source_status=$?
set -eu
if [[ ${source_status} -ne 0 ]]; then
  echo "Failed to source ${OPENFOAM_ENV_SH}" >&2
  exit "${source_status}"
fi

unset FOAM_SIGFPE
export OMP_NUM_THREADS=1
export LD_LIBRARY_PATH="${RCWALLBC_LIBDIR}:${LD_LIBRARY_PATH:-}"
export I_MPI_PMI_LIBRARY="${I_MPI_PMI_LIBRARY:-/usr/lib64/libpmi2.so}"
if [[ ! -r "${I_MPI_PMI_LIBRARY}" ]]; then
  echo "I_MPI_PMI_LIBRARY not readable: ${I_MPI_PMI_LIBRARY}" >&2
  exit 13
fi
FOAMRUN_BIN="${FOAMRUN_BIN:-$(command -v foamRun)}"
if [[ -z "${FOAMRUN_BIN}" || ! -x "${FOAMRUN_BIN}" ]]; then
  echo "foamRun not found after sourcing runtime" >&2
  exit 14
fi

force_runtime_controls() {
  local control_dict="$1"
  "${PYTHON_BIN}" -c 'from pathlib import Path; import re, sys
p = Path(sys.argv[1])
restart = sys.argv[2]
time_format = sys.argv[3]
time_precision = sys.argv[4]
text = p.read_text(encoding="utf-8")
replacements = {
    "startFrom": "startTime",
    "startTime": restart,
    "timeFormat": time_format,
    "timePrecision": time_precision,
}
for key, value in replacements.items():
    text = re.sub(rf"(?m)^(\s*{key}\s+)\S+(\s*;)", rf"\g<1>{value}\2", text, count=1)
p.write_text(text, encoding="utf-8")
' "${control_dict}" "${RESTART_TIME}" "${TIME_FORMAT}" "${TIME_PRECISION}"
}

if [[ ! -d "${CASE_DIR}/processors64" ]]; then
  source_file="${CASE_DIR}/SOURCE_PROCESSORS64.txt"
  if [[ ! -f "${source_file}" ]]; then
    echo "ERROR: missing ${source_file}" >&2
    exit 15
  fi
  source_processors="$(< "${source_file}")"
  echo "[$(date --iso-8601=seconds)] copying processors64 from ${source_processors}"
  cp -a "${source_processors}" "${CASE_DIR}/processors64"
fi

if [[ ! -r "${CASE_DIR}/processors64/${RESTART_TIME}/T" ]]; then
  echo "ERROR: restart ${RESTART_TIME} missing processor T field" >&2
  exit 16
fi

echo "[$(date --iso-8601=seconds)] patching restart T at ${RESTART_TIME}"
"${PYTHON_BIN}" "${PATCHER}" \
  --manifest "${MANIFEST}" \
  --case-key "${CASE_KEY}" \
  --processor-time "${RESTART_TIME}" \
  --patch-processors \
  --audit-out "${CASE_DIR}/logs/restart_patch_audit_${SLURM_JOB_ID:-manual}.csv" \
  > "${CASE_DIR}/logs/restart_patch_stdout_${SLURM_JOB_ID:-manual}.log"

force_runtime_controls "${CASE_DIR}/system/controlDict"

echo "[$(date --iso-8601=seconds)] running selected runtime preflight"
"${PYTHON_BIN}" "${PREFLIGHT_CHECKER}" \
  --manifest "${MANIFEST}" \
  --case-key "${CASE_KEY}" \
  --audit-out "${CAMPAIGN}/logs/runtime_preflight_${SLURM_JOB_ID:-manual}.csv" \
  --json-out "${CAMPAIGN}/logs/runtime_preflight_${SLURM_JOB_ID:-manual}.json" \
  --check-runtime-controls \
  --min-time-precision "${TIME_PRECISION}" \
  --max-time-precision "${TIME_PRECISION}" \
  --required-time-format "${TIME_FORMAT}" \
  --expected-processors "${NTASKS_PER_CASE}" \
  --restart-time "${CASE_KEY}=${RESTART_TIME}"

(
  cd "${CASE_DIR}"
  {
    echo ""
    echo "==== ${DISPLAY_NAME} job ${SLURM_JOB_ID:-manual} $(date --iso-8601=seconds) ===="
    echo "case_key=${CASE_KEY}"
    echo "restart_time=${RESTART_TIME}"
    echo "startFrom=$(awk '/^[[:space:]]*startFrom[[:space:]]+/ { print $2 }' system/controlDict | tr -d ';')"
    echo "startTime=$(awk '/^[[:space:]]*startTime[[:space:]]+/ { print $2 }' system/controlDict | tr -d ';')"
    echo "endTime=$(awk '/^[[:space:]]*endTime[[:space:]]+/ { print $2 }' system/controlDict | tr -d ';')"
    echo "timeFormat=$(awk '/^[[:space:]]*timeFormat[[:space:]]+/ { print $2 }' system/controlDict | tr -d ';')"
    echo "timePrecision=$(awk '/^[[:space:]]*timePrecision[[:space:]]+/ { print $2 }' system/controlDict | tr -d ';')"
  } >> logs/log.foamRun_high_heat_probe

  srun --exclusive --exact --nodes=1 --ntasks="${NTASKS_PER_CASE}" \
    --cpu-bind=cores --distribution=block:block --mpi=pmi2 \
    "${FOAMRUN_BIN}" -parallel >> logs/log.foamRun_high_heat_probe 2>&1
)

echo "[$(date --iso-8601=seconds)] ${DISPLAY_NAME} finished"
