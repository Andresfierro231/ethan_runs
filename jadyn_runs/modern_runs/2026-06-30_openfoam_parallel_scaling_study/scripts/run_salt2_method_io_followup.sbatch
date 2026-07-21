#!/bin/bash
#SBATCH -p NuclearEnergy
#SBATCH -A ASC23046
#SBATCH -J of_s2_opt
#SBATCH -N 1
#SBATCH -n 256
#SBATCH -t 12:00:00
#SBATCH -o /scratch/09748/andresfierro231/projects_scratch/ethan_runs/jadyn_runs/modern_runs/2026-06-30_openfoam_parallel_scaling_study/slurm-%j.out
#SBATCH -e /scratch/09748/andresfierro231/projects_scratch/ethan_runs/jadyn_runs/modern_runs/2026-06-30_openfoam_parallel_scaling_study/slurm-%j.err

set -euo pipefail

CAMPAIGN_ROOT="/scratch/09748/andresfierro231/projects_scratch/ethan_runs/jadyn_runs/modern_runs/2026-06-30_openfoam_parallel_scaling_study"
SOURCE_CASE="/scratch/09748/andresfierro231/projects_scratch/ethan_runs/jadyn_runs/modern_runs/2026-06-18_convergence_and_jin_envelope_wave/runs/salt2_jin/case_stage/viscosity_screening_salt_test_2_jin_coarse_mesh_continuation"
OPENFOAM_ENV_SH="${OPENFOAM13_ENV_SH:-/scratch/09748/andresfierro231/projects_scratch/ethan_runs/jadyn_runs/salt2/2026-06-02_runtime_recovery/scripts/of13-env.sh}"
RCWALL_LIBDIR="${RCWALLBC_LIBDIR:-/home1/09748/andresfierro231/bubble_flow_loop/tamu_loop_box/ethan_data}"
BENCHMARK_RANKS="${BENCHMARK_RANKS:-64}"
BENCHMARK_DELTA="${BENCHMARK_DELTA:-4.0}"
RUN_TIMEOUT_SECONDS="${RUN_TIMEOUT_SECONDS:-5400}"
DECOMPOSE_TIMEOUT_SECONDS="${DECOMPOSE_TIMEOUT_SECONDS:-3600}"
RECONSTRUCT_TIMEOUT_SECONDS="${RECONSTRUCT_TIMEOUT_SECONDS:-7200}"
CUTOFF_TS="${CUTOFF_TS:-2026-07-02 08:00:00}"

WORK_ROOT="$CAMPAIGN_ROOT/work/job_${SLURM_JOB_ID:-manual}"
RESULTS_DIR="$CAMPAIGN_ROOT/results/job_${SLURM_JOB_ID:-manual}"
RECON_CASE="$WORK_ROOT/reconstruct_from_processors64"
SERIAL_BASE="$WORK_ROOT/serial_base"
SUMMARY_CSV="$RESULTS_DIR/optimization_summary.csv"

timestamp() {
    date '+%Y-%m-%dT%H:%M:%S%z'
}

cutoff_epoch() {
    date -d "$CUTOFF_TS" '+%s'
}

remaining_seconds() {
    echo $(( $(cutoff_epoch) - $(date '+%s') ))
}

bounded_timeout_seconds() {
    local requested="$1"
    local reserve="$2"
    local remaining
    remaining="$(remaining_seconds)"
    if (( remaining <= reserve )); then
        echo 0
    elif (( requested < remaining - reserve )); then
        echo "$requested"
    else
        echo $((remaining - reserve))
    fi
}

fail() {
    echo "[$(timestamp)] ERROR: $*" >&2
    exit 1
}

latest_processor_time() {
    find "$SOURCE_CASE/processors64" -mindepth 1 -maxdepth 1 -type d -printf '%f\n' \
        | awk '/^[0-9.]+$/ {print}' \
        | sort -g \
        | tail -1
}

write_decompose_dict() {
    local case_dir="$1"
    local ranks="$2"
    local method="$3"
    local split

    if [[ "$method" == "hierarchical" ]]; then
        case "$ranks" in
            32)
                split="(4 4 2)"
                ;;
            64)
                split="(4 4 4)"
                ;;
            128)
                split="(4 4 8)"
                ;;
            256)
                split="(4 8 8)"
                ;;
            *)
                fail "No predefined hierarchical split for $ranks ranks"
                ;;
        esac
        cat > "$case_dir/system/decomposeParDict" <<EOF
FoamFile
{
    format      ascii;
    class       dictionary;
    location    "system";
    object      decomposeParDict;
}

numberOfSubdomains  $ranks;

method              hierarchical;

hierarchicalCoeffs
{
    n               $split;
    delta           0.001;
    order           xyz;
}

EOF
    else
        cat > "$case_dir/system/decomposeParDict" <<EOF
FoamFile
{
    format      ascii;
    class       dictionary;
    location    "system";
    object      decomposeParDict;
}

numberOfSubdomains  $ranks;

method              scotch;

EOF
    fi
}

set_control_entry() {
    local case_dir="$1"
    local entry="$2"
    local value="$3"
    foamDictionary -entry "$entry" -set "$value" "$case_dir/system/controlDict"
}

stage_reconstruct_case() {
    local latest_time="$1"
    mkdir -p "$RECON_CASE/processors64" "$RESULTS_DIR"
    cp -a "$SOURCE_CASE/0" "$RECON_CASE/0"
    cp -a "$SOURCE_CASE/constant" "$RECON_CASE/constant"
    cp -a "$SOURCE_CASE/system" "$RECON_CASE/system"
    cp -a "$SOURCE_CASE/dynamicCode" "$RECON_CASE/dynamicCode"
    cp -a "$SOURCE_CASE/processors64/constant" "$RECON_CASE/processors64/constant"
    cp -a "$SOURCE_CASE/processors64/$latest_time" "$RECON_CASE/processors64/$latest_time"
}

prepare_serial_base() {
    local latest_time="$1"
    mkdir -p "$SERIAL_BASE"
    cp -a "$RECON_CASE/0" "$SERIAL_BASE/0"
    cp -a "$RECON_CASE/constant" "$SERIAL_BASE/constant"
    cp -a "$RECON_CASE/system" "$SERIAL_BASE/system"
    cp -a "$RECON_CASE/dynamicCode" "$SERIAL_BASE/dynamicCode"
    cp -a "$RECON_CASE/$latest_time" "$SERIAL_BASE/$latest_time"
    set_control_entry "$SERIAL_BASE" startFrom latestTime
    set_control_entry "$SERIAL_BASE" stopAt endTime
    set_control_entry "$SERIAL_BASE" endTime "$END_TIME"
}

prepare_variant_case() {
    local label="$1"
    local method="$2"
    local write_interval="$3"
    local compression="$4"
    local case_dir="$WORK_ROOT/$label"
    mkdir -p "$case_dir"
    cp -a "$SERIAL_BASE/0" "$case_dir/0"
    cp -a "$SERIAL_BASE/constant" "$case_dir/constant"
    cp -a "$SERIAL_BASE/system" "$case_dir/system"
    cp -a "$SERIAL_BASE/dynamicCode" "$case_dir/dynamicCode"
    cp -a "$SERIAL_BASE/$LATEST_TIME" "$case_dir/$LATEST_TIME"
    write_decompose_dict "$case_dir" "$BENCHMARK_RANKS" "$method"
    set_control_entry "$case_dir" writeInterval "$write_interval"
    set_control_entry "$case_dir" purgeWrite 2
    set_control_entry "$case_dir" writeCompression "$compression"
    echo "$case_dir"
}

run_variant() {
    local label="$1"
    local method="$2"
    local write_interval="$3"
    local compression="$4"
    local case_dir="$5"
    local log_dir="$RESULTS_DIR/$label"
    local decomp_log="$log_dir/decomposePar.log"
    local run_log="$log_dir/foamRun.log"
    local start_ts
    local end_ts
    local status="unknown"
    local decomp_status="unknown"
    local run_status="not-run"
    local decomp_timeout
    local run_timeout
    local final_exec
    local output_bytes

    mkdir -p "$log_dir"
    start_ts="$(timestamp)"
    if (( "$(remaining_seconds)" <= 900 )); then
        printf '%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,"%s",%s,%s\n' \
            "$label" "$BENCHMARK_RANKS" "$method" "$write_interval" "$compression" \
            "skipped-cutoff" "not-run" "not-run" "$start_ts" "$start_ts" "" "" 0 "$case_dir" >> "$SUMMARY_CSV"
        echo "[$start_ts] $label skipped: less than 15 minutes to cutoff"
        return
    fi

    echo "[$start_ts] $label decompose start"
    decomp_timeout="$(bounded_timeout_seconds "$DECOMPOSE_TIMEOUT_SECONDS" 900)"
    if (( decomp_timeout <= 0 )); then
        decomp_status="skipped-cutoff"
    elif timeout "$decomp_timeout" bash -lc "cd '$case_dir' && /usr/bin/time -p decomposePar -force -latestTime" > "$decomp_log" 2>&1; then
        decomp_status="ok"
    else
        decomp_status="failed"
    fi

    if [[ "$decomp_status" == "ok" ]]; then
        echo "[$(timestamp)] $label foamRun start"
        run_timeout="$(bounded_timeout_seconds "$RUN_TIMEOUT_SECONDS" 600)"
        if (( run_timeout <= 0 )); then
            run_status="skipped-cutoff"
            status="skipped-cutoff"
        elif timeout "$run_timeout" srun \
            --exclusive \
            --exact \
            --nodes=1 \
            --ntasks="$BENCHMARK_RANKS" \
            --cpu-bind=cores \
            --distribution=block:block \
            --chdir="$case_dir" \
            --mpi=pmi2 \
            "$FOAMRUN_BIN" -parallel > "$run_log" 2>&1; then
            run_status="ok"
            status="ok"
        else
            run_status="failed-or-timeout"
            status="failed"
        fi
    else
        status="failed"
    fi

    end_ts="$(timestamp)"
    final_exec="$(grep 'ExecutionTime =' "$run_log" 2>/dev/null | tail -1 | sed 's/,/;/g' || true)"
    output_bytes="$(du -sb "$case_dir" 2>/dev/null | awk '{print $1}' || echo 0)"
    printf '%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,"%s",%s,%s\n' \
        "$label" "$BENCHMARK_RANKS" "$method" "$write_interval" "$compression" \
        "$status" "$decomp_status" "$run_status" "$start_ts" "$end_ts" "$final_exec" "" "$output_bytes" "$case_dir" >> "$SUMMARY_CSV"
    echo "[$end_ts] $label status=$status decompose=$decomp_status run=$run_status output_bytes=$output_bytes"
}

mkdir -p "$WORK_ROOT" "$RESULTS_DIR"
echo "label,ranks,method,write_interval,write_compression,status,decompose_status,run_status,start_ts,end_ts,final_execution_line,notes,output_bytes,case_dir" > "$SUMMARY_CSV"

echo "[$(timestamp)] optimization follow-up starting"
echo "Campaign root: $CAMPAIGN_ROOT"
echo "Source case: $SOURCE_CASE"
echo "Benchmark ranks: $BENCHMARK_RANKS"
echo "Benchmark delta: $BENCHMARK_DELTA"
echo "Hard cutoff timestamp: $CUTOFF_TS"

[[ -d "$SOURCE_CASE" ]] || fail "Source case missing: $SOURCE_CASE"
[[ -r "$OPENFOAM_ENV_SH" ]] || fail "OpenFOAM env script not readable: $OPENFOAM_ENV_SH"
[[ -r "$RCWALL_LIBDIR/libRCWallBC.so" ]] || fail "Missing libRCWallBC.so under: $RCWALL_LIBDIR"

set +eu
source "$OPENFOAM_ENV_SH"
source_status=$?
set -eu
[[ $source_status -eq 0 ]] || fail "Failed to source $OPENFOAM_ENV_SH"

unset FOAM_SIGFPE
export OMP_NUM_THREADS=1
export LD_LIBRARY_PATH="$RCWALL_LIBDIR:${LD_LIBRARY_PATH:-}"
export I_MPI_PMI_LIBRARY="${I_MPI_PMI_LIBRARY:-/usr/lib64/libpmi2.so}"
[[ -r "$I_MPI_PMI_LIBRARY" ]] || fail "I_MPI_PMI_LIBRARY not readable: $I_MPI_PMI_LIBRARY"

FOAMRUN_BIN="$(command -v foamRun || true)"
[[ -n "$FOAMRUN_BIN" && -x "$FOAMRUN_BIN" ]] || fail "foamRun not found after sourcing runtime"
command -v reconstructPar >/dev/null 2>&1 || fail "reconstructPar not found after sourcing runtime"
command -v decomposePar >/dev/null 2>&1 || fail "decomposePar not found after sourcing runtime"
command -v foamDictionary >/dev/null 2>&1 || fail "foamDictionary not found after sourcing runtime"

if [[ "${SMOKE_ONLY:-0}" == "1" ]]; then
    echo "[$(timestamp)] smoke-only check passed"
    exit 0
fi

if (( "$(remaining_seconds)" <= 0 )); then
    fail "Current time is already past cutoff timestamp: $CUTOFF_TS"
fi

LATEST_TIME="$(latest_processor_time)"
[[ -n "$LATEST_TIME" ]] || fail "No numeric latest time under source processors64"
END_TIME="$(awk -v start="$LATEST_TIME" -v delta="$BENCHMARK_DELTA" 'BEGIN { printf "%.9f", start + delta }')"
echo "Latest source processor time: $LATEST_TIME"
echo "Benchmark endTime: $END_TIME"

stage_reconstruct_case "$LATEST_TIME"
set_control_entry "$RECON_CASE" startFrom latestTime
set_control_entry "$RECON_CASE" stopAt endTime
set_control_entry "$RECON_CASE" endTime "$END_TIME"

echo "[$(timestamp)] reconstructPar -latestTime start"
reconstruct_timeout="$(bounded_timeout_seconds "$RECONSTRUCT_TIMEOUT_SECONDS" 1800)"
if (( reconstruct_timeout <= 0 )); then
    fail "Not enough time before cutoff to run reconstructPar"
fi
timeout "$reconstruct_timeout" bash -lc "cd '$RECON_CASE' && /usr/bin/time -p reconstructPar -latestTime" > "$RESULTS_DIR/reconstructPar.log" 2>&1
[[ -d "$RECON_CASE/$LATEST_TIME" ]] || fail "Expected reconstructed latest time missing: $RECON_CASE/$LATEST_TIME"
echo "[$(timestamp)] reconstructPar -latestTime done"

prepare_serial_base "$LATEST_TIME"

case_dir="$(prepare_variant_case scotch_prod_io scotch 1 off)"
run_variant scotch_prod_io scotch 1 off "$case_dir"

case_dir="$(prepare_variant_case scotch_sparse_io scotch 1000 off)"
run_variant scotch_sparse_io scotch 1000 off "$case_dir"

case_dir="$(prepare_variant_case scotch_sparse_compressed scotch 1000 on)"
run_variant scotch_sparse_compressed scotch 1000 on "$case_dir"

case_dir="$(prepare_variant_case hierarchical_sparse_io hierarchical 1000 off)"
run_variant hierarchical_sparse_io hierarchical 1000 off "$case_dir"

echo "[$(timestamp)] optimization follow-up complete"
