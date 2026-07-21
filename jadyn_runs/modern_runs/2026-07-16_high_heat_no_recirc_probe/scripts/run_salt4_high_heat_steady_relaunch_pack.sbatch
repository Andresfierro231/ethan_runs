#!/usr/bin/env bash
#SBATCH -J salt4_heat2_pack
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
MANIFEST="${CAMPAIGN}/high_heat_steady_relaunch_manifest.csv"
PATCHER="${REPO_ROOT}/jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations/scripts/patch_q_fields.py"
PREFLIGHT_CHECKER="${REPO_ROOT}/tools/analyze/check_corrected_salt_preflight.py"
PYTHON_BIN="${PYTHON_BIN:-/usr/bin/python3.11}"
OPENFOAM_ENV_SH="${OPENFOAM13_ENV_SH:-${REPO_ROOT}/jadyn_runs/salt2/2026-06-02_runtime_recovery/scripts/of13-env.sh}"
RCWALLBC_LIBDIR="${RCWALLBC_LIBDIR:-${REPO_ROOT}/jadyn_runs/modern_runs/2026-06-25_ethan_normal_relaunch_and_recirculation_boundary_wave/runtime_libs}"
TIME_FORMAT=general
TIME_PRECISION=6
NTASKS_PER_CASE=64
ALLOCATED_TASKS="${SLURM_NTASKS:-256}"

CASE_KEYS=(
  "salt4_jin_q0500w_no_recirc_probe"
  "salt4_jin_q1000w_no_recirc_probe"
  "salt4_jin_q1500w_no_recirc_probe"
  "salt4_jin_q3x_no_recirc_probe"
)

CASE_NAMES=(
  "salt4_q0500w_no_recirc_probe"
  "salt4_q1000w_no_recirc_probe"
  "salt4_q1500w_no_recirc_probe"
  "salt4_q3x_no_recirc_probe"
)

CASE_DIRS=(
  "${CAMPAIGN}/runs/salt4_jin_q0500w_no_recirc_probe/case_stage/viscosity_screening_salt_test_4_jin_coarse_mesh_continuation"
  "${CAMPAIGN}/runs/salt4_jin_q1000w_no_recirc_probe/case_stage/viscosity_screening_salt_test_4_jin_coarse_mesh_continuation"
  "${CAMPAIGN}/runs/salt4_jin_q1500w_no_recirc_probe/case_stage/viscosity_screening_salt_test_4_jin_coarse_mesh_continuation"
  "${CAMPAIGN}/runs/salt4_jin_q3x_no_recirc_probe/case_stage/viscosity_screening_salt_test_4_jin_coarse_mesh_continuation"
)

RESTART_TIMES=(
  "11658"
  "11031"
  "10795"
  "11395"
)

LOG_NAMES=(
  "log.foamRun_high_heat_steady_relaunch"
  "log.foamRun_high_heat_steady_relaunch"
  "log.foamRun_high_heat_steady_relaunch"
  "log.foamRun_high_heat_steady_relaunch"
)

mkdir -p "${CAMPAIGN}/logs"

if [[ ${#CASE_KEYS[@]} -ne ${#CASE_NAMES[@]} || ${#CASE_KEYS[@]} -ne ${#CASE_DIRS[@]} || ${#CASE_KEYS[@]} -ne ${#RESTART_TIMES[@]} ]]; then
  echo "Internal launcher error: case arrays have mismatched lengths" >&2
  exit 20
fi
if (( ${#CASE_KEYS[@]} * NTASKS_PER_CASE > ALLOCATED_TASKS )); then
  echo "Refusing to launch ${#CASE_KEYS[@]} x ${NTASKS_PER_CASE} tasks into ${ALLOCATED_TASKS} allocated tasks" >&2
  exit 21
fi

echo "[$(date --iso-8601=seconds)] Salt4 high-heat steady-state relaunch pack"
echo "SLURM_JOB_ID=${SLURM_JOB_ID:-unknown}"
echo "CASE_NAMES=${CASE_NAMES[*]}"
echo "RESTART_TIMES=${RESTART_TIMES[*]}"
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
  local restart_time="$2"
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
' "${control_dict}" "${restart_time}" "${TIME_FORMAT}" "${TIME_PRECISION}"
}

preflight_case() {
  local key="$1"
  local display_name="$2"
  local case_dir="$3"
  local restart_time="$4"

  if [[ ! -d "${case_dir}" ]]; then
    echo "ERROR: missing case directory for ${display_name}: ${case_dir}" >&2
    exit 2
  fi
  if grep -R -n -E 'stopAtControl::writeNow|stopAt[[:space:]]*\([[:space:]]*writeNow' \
      "${case_dir}/system/controlDict" "${case_dir}/system/functions"; then
    echo "ERROR: ${display_name} still contains a writeNow stop monitor" >&2
    exit 3
  fi
  if [[ ! -r "${case_dir}/processors64/${restart_time}/T" ]]; then
    echo "ERROR: ${display_name} restart ${restart_time} is missing processors64 T" >&2
    exit 5
  fi

  mkdir -p "${case_dir}/logs"
  echo "[$(date --iso-8601=seconds)] verifying and patching restart field for ${display_name} at ${restart_time}"
  "${PYTHON_BIN}" "${PATCHER}" \
    --manifest "${MANIFEST}" \
    --case-key "${key}" \
    --processor-time "${restart_time}" \
    --patch-processors \
    --audit-out "${case_dir}/logs/steady_relaunch_restart_patch_audit_${SLURM_JOB_ID:-manual}.csv" \
    > "${case_dir}/logs/steady_relaunch_restart_patch_stdout_${SLURM_JOB_ID:-manual}.log"

  force_runtime_controls "${case_dir}/system/controlDict" "${restart_time}"
}

runtime_preflight_selected_cases() {
  local audit_csv="${CAMPAIGN}/logs/steady_relaunch_runtime_preflight_${SLURM_JOB_ID:-manual}.csv"
  local audit_json="${CAMPAIGN}/logs/steady_relaunch_runtime_preflight_${SLURM_JOB_ID:-manual}.json"
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
    args+=(--case-key "${CASE_KEYS[$idx]}")
    args+=(--restart-time "${CASE_KEYS[$idx]}=${RESTART_TIMES[$idx]}")
  done
  echo "[$(date --iso-8601=seconds)] running steady relaunch runtime preflight audit"
  "${args[@]}"
}

launch_case() {
  local key="$1"
  local display_name="$2"
  local case_dir="$3"
  local restart_time="$4"
  local log_name="$5"

  (
    cd "${case_dir}"
    {
      echo ""
      echo "==== ${display_name} steady relaunch job ${SLURM_JOB_ID:-manual} $(date --iso-8601=seconds) ===="
      echo "case_key=${key}"
      echo "restart_time=${restart_time}"
      echo "startFrom=$(awk '/^[[:space:]]*startFrom[[:space:]]+/ { print $2 }' system/controlDict | tr -d ';')"
      echo "startTime=$(awk '/^[[:space:]]*startTime[[:space:]]+/ { print $2 }' system/controlDict | tr -d ';')"
      echo "endTime=$(awk '/^[[:space:]]*endTime[[:space:]]+/ { print $2 }' system/controlDict | tr -d ';')"
      echo "timeFormat=$(awk '/^[[:space:]]*timeFormat[[:space:]]+/ { print $2 }' system/controlDict | tr -d ';')"
      echo "timePrecision=$(awk '/^[[:space:]]*timePrecision[[:space:]]+/ { print $2 }' system/controlDict | tr -d ';')"
    } >> "logs/${log_name}"

    srun --exclusive --exact --nodes=1 --ntasks="${NTASKS_PER_CASE}" \
      --cpu-bind=cores --distribution=block:block --mpi=pmi2 \
      "${FOAMRUN_BIN}" -parallel >> "logs/${log_name}" 2>&1
  ) &
}

for idx in "${!CASE_KEYS[@]}"; do
  preflight_case "${CASE_KEYS[$idx]}" "${CASE_NAMES[$idx]}" "${CASE_DIRS[$idx]}" "${RESTART_TIMES[$idx]}"
done

runtime_preflight_selected_cases

for idx in "${!CASE_KEYS[@]}"; do
  echo "[$(date --iso-8601=seconds)] launching ${CASE_NAMES[$idx]} from ${RESTART_TIMES[$idx]}"
  launch_case "${CASE_KEYS[$idx]}" "${CASE_NAMES[$idx]}" "${CASE_DIRS[$idx]}" "${RESTART_TIMES[$idx]}" "${LOG_NAMES[$idx]}"
done

wait
echo "[$(date --iso-8601=seconds)] Salt4 high-heat steady-state relaunch pack finished"
