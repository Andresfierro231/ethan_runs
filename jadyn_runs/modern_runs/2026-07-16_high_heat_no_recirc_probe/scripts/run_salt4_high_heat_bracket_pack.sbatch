#!/usr/bin/env bash
#SBATCH -J salt4_heat_pack
#SBATCH -A ASC23046
#SBATCH -p NuclearEnergy
#SBATCH -N 1
#SBATCH -n 256
#SBATCH -t 120:00:00
#SBATCH -o /scratch/09748/andresfierro231/projects_scratch/ethan_runs/jadyn_runs/modern_runs/2026-07-16_high_heat_no_recirc_probe/slurm-%x-%j.out
#SBATCH -e /scratch/09748/andresfierro231/projects_scratch/ethan_runs/jadyn_runs/modern_runs/2026-07-16_high_heat_no_recirc_probe/slurm-%x-%j.err

set -euo pipefail

REPO_ROOT="/scratch/09748/andresfierro231/projects_scratch/ethan_runs"
CAMPAIGN="${REPO_ROOT}/jadyn_runs/modern_runs/2026-07-16_high_heat_no_recirc_probe"
MANIFEST="${CAMPAIGN}/high_heat_bracket_pack_manifest.csv"
PATCHER="${REPO_ROOT}/jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations/scripts/patch_q_fields.py"
PREFLIGHT_CHECKER="${REPO_ROOT}/tools/analyze/check_corrected_salt_preflight.py"
PYTHON_BIN="${PYTHON_BIN:-/usr/bin/python3.11}"
OPENFOAM_ENV_SH="${OPENFOAM13_ENV_SH:-${REPO_ROOT}/jadyn_runs/salt2/2026-06-02_runtime_recovery/scripts/of13-env.sh}"
RCWALLBC_LIBDIR="${RCWALLBC_LIBDIR:-${REPO_ROOT}/jadyn_runs/modern_runs/2026-06-25_ethan_normal_relaunch_and_recirculation_boundary_wave/runtime_libs}"
TIME_FORMAT=general
TIME_PRECISION=6
NTASKS_PER_CASE=64
ALLOCATED_TASKS="${SLURM_NTASKS:-256}"
RESTART_TIME=10000

CASE_KEYS=(
  "salt4_jin_q0500w_no_recirc_probe"
  "salt4_jin_q1000w_no_recirc_probe"
  "salt4_jin_q1500w_no_recirc_probe"
)

CASE_NAMES=(
  "salt4_q0500w_no_recirc_probe"
  "salt4_q1000w_no_recirc_probe"
  "salt4_q1500w_no_recirc_probe"
)

CASE_DIRS=(
  "${CAMPAIGN}/runs/salt4_jin_q0500w_no_recirc_probe/case_stage/viscosity_screening_salt_test_4_jin_coarse_mesh_continuation"
  "${CAMPAIGN}/runs/salt4_jin_q1000w_no_recirc_probe/case_stage/viscosity_screening_salt_test_4_jin_coarse_mesh_continuation"
  "${CAMPAIGN}/runs/salt4_jin_q1500w_no_recirc_probe/case_stage/viscosity_screening_salt_test_4_jin_coarse_mesh_continuation"
)

mkdir -p "${CAMPAIGN}/logs"

if [[ ${#CASE_KEYS[@]} -ne ${#CASE_NAMES[@]} || ${#CASE_KEYS[@]} -ne ${#CASE_DIRS[@]} ]]; then
  echo "Internal launcher error: case arrays have mismatched lengths" >&2
  exit 20
fi
if (( ${#CASE_KEYS[@]} * NTASKS_PER_CASE > ALLOCATED_TASKS )); then
  echo "Refusing to launch ${#CASE_KEYS[@]} x ${NTASKS_PER_CASE} tasks into ${ALLOCATED_TASKS} allocated tasks" >&2
  exit 21
fi

echo "[$(date --iso-8601=seconds)] Salt4 500/1000/1500 W high-heat bracket pack"
echo "SLURM_JOB_ID=${SLURM_JOB_ID:-unknown}"
echo "CASE_NAMES=${CASE_NAMES[*]}"
echo "RESTART_TIME=${RESTART_TIME}"
echo "ALLOCATED_TASKS=${ALLOCATED_TASKS}"
echo "NTASKS_PER_CASE=${NTASKS_PER_CASE}"

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

preflight_case() {
  local key="$1"
  local display_name="$2"
  local case_dir="$3"

  if [[ ! -d "${case_dir}" ]]; then
    echo "ERROR: missing case directory for ${display_name}: ${case_dir}" >&2
    exit 2
  fi
  if grep -R -n -E 'stopAtControl::writeNow|stopAt[[:space:]]*\([[:space:]]*writeNow' \
      "${case_dir}/system/controlDict" "${case_dir}/system/functions"; then
    echo "ERROR: ${display_name} still contains a writeNow stop monitor" >&2
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
    echo "[$(date --iso-8601=seconds)] copying processors64 for ${display_name} from ${source_processors}"
    cp -a "${source_processors}" "${case_dir}/processors64"
  fi

  if [[ ! -r "${case_dir}/processors64/${RESTART_TIME}/T" ]]; then
    echo "ERROR: ${display_name} restart ${RESTART_TIME} is missing processors64 T" >&2
    exit 5
  fi

  mkdir -p "${case_dir}/logs"
  echo "[$(date --iso-8601=seconds)] patching restart field for ${display_name} at ${RESTART_TIME}"
  "${PYTHON_BIN}" "${PATCHER}" \
    --manifest "${MANIFEST}" \
    --case-key "${key}" \
    --processor-time "${RESTART_TIME}" \
    --patch-processors \
    --audit-out "${case_dir}/logs/bracket_restart_patch_audit_${SLURM_JOB_ID:-manual}.csv" \
    > "${case_dir}/logs/bracket_restart_patch_stdout_${SLURM_JOB_ID:-manual}.log"

  force_runtime_controls "${case_dir}/system/controlDict"
}

runtime_preflight_selected_cases() {
  local audit_csv="${CAMPAIGN}/logs/bracket_runtime_preflight_${SLURM_JOB_ID:-manual}.csv"
  local audit_json="${CAMPAIGN}/logs/bracket_runtime_preflight_${SLURM_JOB_ID:-manual}.json"
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
  for key in "${CASE_KEYS[@]}"; do
    args+=(--case-key "${key}")
    args+=(--restart-time "${key}=${RESTART_TIME}")
  done
  echo "[$(date --iso-8601=seconds)] running bracket runtime preflight audit"
  "${args[@]}"
}

launch_case() {
  local key="$1"
  local display_name="$2"
  local case_dir="$3"

  (
    cd "${case_dir}"
    {
      echo ""
      echo "==== ${display_name} job ${SLURM_JOB_ID:-manual} $(date --iso-8601=seconds) ===="
      echo "case_key=${key}"
      echo "restart_time=${RESTART_TIME}"
      echo "startFrom=$(awk '/^[[:space:]]*startFrom[[:space:]]+/ { print $2 }' system/controlDict | tr -d ';')"
      echo "startTime=$(awk '/^[[:space:]]*startTime[[:space:]]+/ { print $2 }' system/controlDict | tr -d ';')"
      echo "endTime=$(awk '/^[[:space:]]*endTime[[:space:]]+/ { print $2 }' system/controlDict | tr -d ';')"
      echo "timeFormat=$(awk '/^[[:space:]]*timeFormat[[:space:]]+/ { print $2 }' system/controlDict | tr -d ';')"
      echo "timePrecision=$(awk '/^[[:space:]]*timePrecision[[:space:]]+/ { print $2 }' system/controlDict | tr -d ';')"
    } >> logs/log.foamRun_high_heat_bracket

    srun --exclusive --exact --nodes=1 --ntasks="${NTASKS_PER_CASE}" \
      --cpu-bind=cores --distribution=block:block --mpi=pmi2 \
      "${FOAMRUN_BIN}" -parallel >> logs/log.foamRun_high_heat_bracket 2>&1
  ) &
}

for idx in "${!CASE_KEYS[@]}"; do
  preflight_case "${CASE_KEYS[$idx]}" "${CASE_NAMES[$idx]}" "${CASE_DIRS[$idx]}"
done

runtime_preflight_selected_cases

for idx in "${!CASE_KEYS[@]}"; do
  echo "[$(date --iso-8601=seconds)] launching ${CASE_NAMES[$idx]}"
  launch_case "${CASE_KEYS[$idx]}" "${CASE_NAMES[$idx]}" "${CASE_DIRS[$idx]}"
done

wait
echo "[$(date --iso-8601=seconds)] Salt4 high-heat bracket pack finished"
