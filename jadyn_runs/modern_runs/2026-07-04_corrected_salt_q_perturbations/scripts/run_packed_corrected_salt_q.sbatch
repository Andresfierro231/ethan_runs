#!/bin/bash
#SBATCH -p NuclearEnergy
#SBATCH -A ASC23046
#SBATCH -N 1
#SBATCH -n 256
#SBATCH -t 120:00:00
#SBATCH -o /scratch/09748/andresfierro231/projects_scratch/ethan_runs/jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations/slurm-%x-%j.out
#SBATCH -e /scratch/09748/andresfierro231/projects_scratch/ethan_runs/jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations/slurm-%x-%j.err

set -euo pipefail

ROOT="/scratch/09748/andresfierro231/projects_scratch/ethan_runs"
CAMPAIGN="$ROOT/jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations"
OPENFOAM_ENV_SH="${OPENFOAM13_ENV_SH:-$ROOT/jadyn_runs/salt2/2026-06-02_runtime_recovery/scripts/of13-env.sh}"
RCWALLBC_LIBDIR="${RCWALLBC_LIBDIR:-/home1/09748/andresfierro231/bubble_flow_loop/tamu_loop_box/ethan_data}"
MANIFEST="$CAMPAIGN/corrected_case_manifest.csv"
JOB_GROUPS="$CAMPAIGN/job_groups.tsv"
PATCHER="$CAMPAIGN/scripts/patch_q_fields.py"
PYTHON_BIN="${PYTHON_BIN:-/usr/bin/python3.11}"

CASE_GROUP="${CASE_GROUP:-}"
if [[ -z "$CASE_GROUP" ]]; then
    echo "CASE_GROUP must name a row in $JOB_GROUPS" >&2
    exit 1
fi
group_line="$(awk -F '\t' -v group="$CASE_GROUP" '$1 == group { print; found = 1; exit } END { if (!found) exit 1 }' "$JOB_GROUPS")" || {
    echo "Could not find CASE_GROUP=$CASE_GROUP in $JOB_GROUPS" >&2
    exit 1
}
IFS=$'\t' read -r _group_name case_keys_csv case_dirs_csv <<< "$group_line"
IFS=',' read -r -a CASE_KEYS <<< "$case_keys_csv"
IFS=',' read -r -a CASE_DIRS <<< "$case_dirs_csv"
if [[ ${#CASE_KEYS[@]} -eq 0 || ${#CASE_KEYS[@]} -ne ${#CASE_DIRS[@]} ]]; then
    echo "Case group $CASE_GROUP does not contain equal case key and dir counts" >&2
    exit 1
fi

if [[ ! -r "$OPENFOAM_ENV_SH" ]]; then
    echo "OpenFOAM env script not readable: $OPENFOAM_ENV_SH" >&2
    exit 1
fi
if [[ ! -r "$RCWALLBC_LIBDIR/libRCWallBC.so" ]]; then
    echo "Missing libRCWallBC.so under: $RCWALLBC_LIBDIR" >&2
    exit 1
fi
if [[ ! -x "$PYTHON_BIN" ]]; then
    echo "PYTHON_BIN is not executable: $PYTHON_BIN" >&2
    exit 1
fi

set +eu
source "$OPENFOAM_ENV_SH"
source_status=$?
set -eu
if [[ $source_status -ne 0 ]]; then
    echo "Failed to source $OPENFOAM_ENV_SH" >&2
    exit "$source_status"
fi

unset FOAM_SIGFPE
export OMP_NUM_THREADS=1
export LD_LIBRARY_PATH="$RCWALLBC_LIBDIR:${LD_LIBRARY_PATH:-}"
export I_MPI_PMI_LIBRARY="${I_MPI_PMI_LIBRARY:-/usr/lib64/libpmi2.so}"
if [[ ! -r "$I_MPI_PMI_LIBRARY" ]]; then
    echo "I_MPI_PMI_LIBRARY not readable: $I_MPI_PMI_LIBRARY" >&2
    exit 1
fi

FOAMRUN_BIN="$(command -v foamRun || true)"
if [[ -z "$FOAMRUN_BIN" || ! -x "$FOAMRUN_BIN" ]]; then
    echo "foamRun not found after sourcing runtime" >&2
    exit 1
fi

latest_restart_time() {
    find "$1/processors64" -mindepth 1 -maxdepth 1 -type d -printf '%f\n' | awk '/^[0-9.]+$/ {print}' | sort -g | tail -1
}

prepare_case() {
    local key="$1"
    local dir="$2"
    if [[ ! -d "$dir/processors64" ]]; then
        local source_processors
        source_processors="$(tr -d '\n' < "$dir/SOURCE_PROCESSORS64.txt")"
        cp -a "$source_processors" "$dir/processors64"
    fi
    "$PYTHON_BIN" "$PATCHER" --manifest "$MANIFEST" --case-key "$key" --patch-processors --audit-out "$dir/logs/preflight_patch_audit_${SLURM_JOB_ID}.csv" > "$dir/logs/preflight_patch_stdout_${SLURM_JOB_ID}.log" || {
        echo "Patch preflight failed for $key under $dir" >&2
        return 1
    }
    latest_restart_time "$dir"
}

launch_case() {
    local key="$1"
    local dir="$2"
    local latest="$3"
    printf "\n--- corrected salt q job %s start (%s, restart %s) ---\n" "$SLURM_JOB_ID" "$key" "$latest" >> "$dir/logs/log.foamRun_corrected_q"
    srun --exclusive --exact --nodes=1 --ntasks=64 --cpu-bind=cores --distribution=block:block --chdir="$dir" --mpi=pmi2 \
        "$FOAMRUN_BIN" -parallel >> "$dir/logs/log.foamRun_corrected_q" 2>&1 &
}

echo "Corrected Salt Q packed job $SLURM_JOB_ID"
echo "Group: $CASE_GROUP"
echo "Cases: ${CASE_KEYS[*]}"
echo "Using foamRun: $FOAMRUN_BIN"
echo "Using I_MPI_PMI_LIBRARY: $I_MPI_PMI_LIBRARY"
echo "Using RCWallBC libdir: $RCWALLBC_LIBDIR"
echo "Using Python patcher: $PYTHON_BIN"
for idx in "${!CASE_KEYS[@]}"; do
    latest="$(prepare_case "${CASE_KEYS[$idx]}" "${CASE_DIRS[$idx]}")"
    launch_case "${CASE_KEYS[$idx]}" "${CASE_DIRS[$idx]}" "$latest"
done
wait
