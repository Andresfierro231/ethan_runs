#!/usr/bin/env bash
#SBATCH -J saltq_sel_cont
#SBATCH -A ASC23046
#SBATCH -p NuclearEnergy
#SBATCH -N 1
#SBATCH -n 256
#SBATCH -t 120:00:00
#SBATCH -o /scratch/09748/andresfierro231/projects_scratch/ethan_runs/jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations/slurm-%x-%j.out
#SBATCH -e /scratch/09748/andresfierro231/projects_scratch/ethan_runs/jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations/slurm-%x-%j.err

set -euo pipefail

CAMPAIGN="/scratch/09748/andresfierro231/projects_scratch/ethan_runs/jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations"
REPO_ROOT="/scratch/09748/andresfierro231/projects_scratch/ethan_runs"
SCRIPT_DIR="${CAMPAIGN}/scripts"
PATCHER="${SCRIPT_DIR}/patch_q_fields.py"
PREFLIGHT_CHECKER="${REPO_ROOT}/tools/analyze/check_corrected_salt_preflight.py"
MANIFEST="${CAMPAIGN}/corrected_case_manifest.csv"
PYTHON_BIN="${PYTHON_BIN:-/usr/bin/python3.11}"
OPENFOAM_ENV_SH="${OPENFOAM13_ENV_SH:-/scratch/09748/andresfierro231/projects_scratch/ethan_runs/jadyn_runs/salt2/2026-06-02_runtime_recovery/scripts/of13-env.sh}"
RCWALLBC_LIBDIR="${RCWALLBC_LIBDIR:-/scratch/09748/andresfierro231/projects_scratch/ethan_runs/jadyn_runs/modern_runs/2026-06-25_ethan_normal_relaunch_and_recirculation_boundary_wave/runtime_libs}"
TIME_FORMAT=general
TIME_PRECISION=6

CASE_KEYS=(
  "salt2_jin_lo10q_corrected"
  "salt2_jin_hi10q_corrected"
  "salt4_jin_lo10q_corrected"
  "salt4_jin_hi10q_corrected"
)

CASE_NAMES=(
  "salt2_lo10q"
  "salt2_hi10q"
  "salt4_lo10q"
  "salt4_hi10q"
)

CASE_DIRS=(
  "${CAMPAIGN}/runs/salt2_jin_lo10q_corrected/case_stage/viscosity_screening_salt_test_2_jin_coarse_mesh_continuation"
  "${CAMPAIGN}/runs/salt2_jin_hi10q_corrected/case_stage/viscosity_screening_salt_test_2_jin_coarse_mesh_continuation"
  "${CAMPAIGN}/runs/salt4_jin_lo10q_corrected/case_stage/viscosity_screening_salt_test_4_jin_coarse_mesh_continuation"
  "${CAMPAIGN}/runs/salt4_jin_hi10q_corrected/case_stage/viscosity_screening_salt_test_4_jin_coarse_mesh_continuation"
)

RESTART_OVERRIDES=(
  "10291"
  "9674"
  "11655"
  "12639"
)

NTASKS_PER_CASE=64
MAX_CONCURRENT_CASES=4
ALLOCATED_TASKS="${SLURM_NTASKS:-256}"
mkdir -p "${CAMPAIGN}/logs"

if [[ ${#CASE_KEYS[@]} -ne ${#CASE_NAMES[@]} || ${#CASE_KEYS[@]} -ne ${#CASE_DIRS[@]} || ${#CASE_KEYS[@]} -ne ${#RESTART_OVERRIDES[@]} ]]; then
  echo "Internal launcher error: case arrays have mismatched lengths" >&2
  exit 20
fi
if [[ ${#CASE_KEYS[@]} -gt ${MAX_CONCURRENT_CASES} ]]; then
  echo "Refusing to launch ${#CASE_KEYS[@]} cases; max concurrent cases is ${MAX_CONCURRENT_CASES}" >&2
  exit 21
fi
if (( ${#CASE_KEYS[@]} * NTASKS_PER_CASE > ALLOCATED_TASKS )); then
  echo "Refusing to launch ${#CASE_KEYS[@]} x ${NTASKS_PER_CASE} tasks into ${ALLOCATED_TASKS} allocated tasks" >&2
  exit 22
fi

echo "[$(date --iso-8601=seconds)] selected corrected Salt Q continuation"
echo "SLURM_JOB_ID=${SLURM_JOB_ID:-unknown}"
echo "CAMPAIGN=${CAMPAIGN}"
echo "CASES=${CASE_NAMES[*]}"
echo "SOURCE_CASE_KEYS=${CASE_KEYS[*]}"
echo "MAX_CONCURRENT_CASES=${MAX_CONCURRENT_CASES}"
echo "NTASKS_PER_CASE=${NTASKS_PER_CASE}"
echo "ALLOCATED_TASKS=${ALLOCATED_TASKS}"
echo "TIME_FORMAT=${TIME_FORMAT}"
echo "TIME_PRECISION=${TIME_PRECISION}"

if [[ ! -r "${OPENFOAM_ENV_SH}" ]]; then
  echo "OpenFOAM env script not readable: ${OPENFOAM_ENV_SH}" >&2
  exit 10
fi
if [[ ! -r "${RCWALLBC_LIBDIR}/libRCWallBC.so" ]]; then
  echo "Missing libRCWallBC.so under: ${RCWALLBC_LIBDIR}" >&2
  exit 11
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
  exit 12
fi
FOAMRUN_BIN="${FOAMRUN_BIN:-$(command -v foamRun)}"
if [[ -z "${FOAMRUN_BIN}" || ! -x "${FOAMRUN_BIN}" ]]; then
  echo "foamRun not found after sourcing runtime" >&2
  exit 13
fi

latest_restart_time() {
  local case_dir="$1"
  find "${case_dir}/processors64" -mindepth 1 -maxdepth 1 -type d -printf '%f\n' \
    | awk '/^[0-9.]+$/ { print }' \
    | sort -g \
    | tail -n 1
}

force_selected_runtime_controls() {
  local control_dict="$1"
  local restart_override="$2"
  local time_format="$3"
  local time_precision="$4"
  "${PYTHON_BIN}" -c 'from pathlib import Path; import re, sys
p = Path(sys.argv[1])
restart = sys.argv[2]
time_format = sys.argv[3]
time_precision = sys.argv[4]
text = p.read_text(encoding="utf-8")
text = re.sub(r"(?m)^(\s*endTime\s+)[-+0-9.eE]+(\s*;)", r"\g<1>30000\2", text, count=1)
text = re.sub(r"(?m)^(\s*timeFormat\s+)\S+(\s*;)", rf"\g<1>{time_format}\2", text, count=1)
text = re.sub(r"(?m)^(\s*timePrecision\s+)[-+0-9.eE]+(\s*;)", rf"\g<1>{time_precision}\2", text, count=1)
if restart:
    text = re.sub(r"(?m)^(\s*startFrom\s+)\S+(\s*;)", r"\g<1>startTime\2", text, count=1)
    text = re.sub(r"(?m)^(\s*startTime\s+)[-+0-9.eE]+(\s*;)", rf"\g<1>{restart}\2", text, count=1)
else:
    text = re.sub(r"(?m)^(\s*startFrom\s+)\S+(\s*;)", r"\g<1>latestTime\2", text, count=1)
    text = re.sub(r"(?m)^(\s*startTime\s+)[-+0-9.eE]+(\s*;)", r"\g<1>0\2", text, count=1)
p.write_text(text, encoding="utf-8")
' "${control_dict}" "${restart_override}" "${time_format}" "${time_precision}"
}

preflight_case() {
  local key="$1"
  local display_name="$2"
  local case_dir="$3"
  local restart_override="$4"

  if [[ ! -d "${case_dir}" ]]; then
    echo "ERROR: missing case directory for ${display_name} (${key}): ${case_dir}" >&2
    exit 2
  fi

  if grep -R -n -E 'stopAtControl::writeNow|stopAt[[:space:]]*\([[:space:]]*writeNow' \
      "${case_dir}/system/controlDict" "${case_dir}/system/functions"; then
    echo "ERROR: ${display_name} (${key}) still contains a writeNow stop monitor; refusing to submit unsafe continuation." >&2
    exit 3
  fi

  if [[ ! -d "${case_dir}/processors64" ]]; then
    local source_file="${case_dir}/SOURCE_PROCESSORS64.txt"
    if [[ ! -f "${source_file}" ]]; then
      echo "ERROR: ${key} has no processors64 and no SOURCE_PROCESSORS64.txt" >&2
      exit 4
    fi
    local source_processors
    source_processors="$(< "${source_file}")"
    echo "[$(date --iso-8601=seconds)] copying processors64 for ${display_name} (${key}) from ${source_processors}"
    cp -a "${source_processors}" "${case_dir}/processors64"
  fi

  mkdir -p "${case_dir}/logs"

  local restart_time
  restart_time="${restart_override:-$(latest_restart_time "${case_dir}")}"
  if [[ -z "${restart_time}" ]]; then
    echo "ERROR: ${display_name} (${key}) has no numeric processors64 restart directories" >&2
    exit 5
  fi
  if [[ ! -r "${case_dir}/processors64/${restart_time}/T" ]]; then
    echo "ERROR: ${display_name} (${key}) restart ${restart_time} is missing processors64 T" >&2
    exit 6
  fi

  echo "[$(date --iso-8601=seconds)] patching restart field for ${display_name} (${key}) at ${restart_time}"
  "${PYTHON_BIN}" "${PATCHER}" \
    --manifest "${MANIFEST}" \
    --case-key "${key}" \
    --processor-time "${restart_time}" \
    --patch-processors \
    --audit-out "${case_dir}/logs/preflight_patch_audit_${SLURM_JOB_ID:-manual}.csv" \
    > "${case_dir}/logs/preflight_patch_stdout_${SLURM_JOB_ID:-manual}.log"

  force_selected_runtime_controls "${case_dir}/system/controlDict" "${restart_override}" "${TIME_FORMAT}" "${TIME_PRECISION}"
}

runtime_preflight_selected_cases() {
  local audit_csv="${CAMPAIGN}/logs/selected_runtime_preflight_${SLURM_JOB_ID:-manual}.csv"
  local audit_json="${CAMPAIGN}/logs/selected_runtime_preflight_${SLURM_JOB_ID:-manual}.json"
  local args=(
    "${PYTHON_BIN}" "${PREFLIGHT_CHECKER}"
    --manifest "${MANIFEST}"
    --audit-out "${audit_csv}"
    --json-out "${audit_json}"
    --check-runtime-controls
    --min-time-precision "${TIME_PRECISION}"
    --max-time-precision "${TIME_PRECISION}"
    --required-time-format "${TIME_FORMAT}"
    --expected-processors "${NTASKS_PER_CASE}"
  )
  for idx in "${!CASE_KEYS[@]}"; do
    local restart_time="${RESTART_OVERRIDES[$idx]:-$(latest_restart_time "${CASE_DIRS[$idx]}")}"
    args+=(--case-key "${CASE_KEYS[$idx]}")
    args+=(--restart-time "${CASE_KEYS[$idx]}=${restart_time}")
  done
  echo "[$(date --iso-8601=seconds)] running selected runtime preflight audit"
  "${args[@]}"
}

launch_case() {
  local key="$1"
  local display_name="$2"
  local case_dir="$3"
  local restart_override="$4"
  local restart_time
  restart_time="${restart_override:-$(latest_restart_time "${case_dir}")}"

  (
    cd "${case_dir}"
    {
      echo ""
      echo "==== selected continuation ${display_name} job ${SLURM_JOB_ID:-manual} $(date --iso-8601=seconds) ===="
      echo "display_case=${display_name}"
      echo "source_case_key=${key}"
      echo "restart_time=${restart_time}"
      echo "endTime=$(awk '/^[[:space:]]*endTime[[:space:]]+/ { print $2 }' system/controlDict | tr -d ';')"
      echo "startFrom=$(awk '/^[[:space:]]*startFrom[[:space:]]+/ { print $2 }' system/controlDict | tr -d ';')"
      echo "startTime=$(awk '/^[[:space:]]*startTime[[:space:]]+/ { print $2 }' system/controlDict | tr -d ';')"
      echo "timeFormat=$(awk '/^[[:space:]]*timeFormat[[:space:]]+/ { print $2 }' system/controlDict | tr -d ';')"
      echo "timePrecision=$(awk '/^[[:space:]]*timePrecision[[:space:]]+/ { print $2 }' system/controlDict | tr -d ';')"
    } >> logs/log.foamRun_corrected_q

    srun --exclusive --exact --nodes=1 --ntasks="${NTASKS_PER_CASE}" \
      --cpu-bind=cores --distribution=block:block --mpi=pmi2 \
      "${FOAMRUN_BIN}" -parallel >> logs/log.foamRun_corrected_q 2>&1
  ) &
}

for idx in "${!CASE_KEYS[@]}"; do
  preflight_case "${CASE_KEYS[$idx]}" "${CASE_NAMES[$idx]}" "${CASE_DIRS[$idx]}" "${RESTART_OVERRIDES[$idx]}"
done

runtime_preflight_selected_cases

for idx in "${!CASE_KEYS[@]}"; do
  echo "[$(date --iso-8601=seconds)] launching ${CASE_NAMES[$idx]} (${CASE_KEYS[$idx]})"
  launch_case "${CASE_KEYS[$idx]}" "${CASE_NAMES[$idx]}" "${CASE_DIRS[$idx]}" "${RESTART_OVERRIDES[$idx]}"
done

wait
echo "[$(date --iso-8601=seconds)] selected corrected Salt Q continuation finished"
