#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CAMPAIGN_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
RUNS_ROOT="$CAMPAIGN_ROOT/runs"
LAUNCHER="$SCRIPT_DIR/run_packed_two_case_normal.sbatch"
SUBMISSION_CSV="$CAMPAIGN_ROOT/submitted_jobs.csv"
OPENFOAM_ENV_SH="${OPENFOAM13_ENV_SH:-/scratch/09748/andresfierro231/projects_scratch/ethan_runs/jadyn_runs/salt2/2026-06-02_runtime_recovery/scripts/of13-env.sh}"
RCWALLBC_LIBDIR="${RCWALLBC_LIBDIR:-$CAMPAIGN_ROOT/runtime_libs}"
SEGMENT_WALLTIME="${SEGMENT_WALLTIME:-48:00:00}"
SEGMENT_COUNT="${SEGMENT_COUNT:-5}"

if [[ ! -x "$LAUNCHER" ]]; then
    echo "Missing launcher: $LAUNCHER" >&2
    exit 1
fi
if [[ ! -r "$RCWALLBC_LIBDIR/libRCWallBC.so" ]]; then
    echo "Missing runtime library copy under: $RCWALLBC_LIBDIR" >&2
    exit 1
fi

if ! [[ "$SEGMENT_COUNT" =~ ^[0-9]+$ ]] || [[ "$SEGMENT_COUNT" -lt 1 ]]; then
    echo "SEGMENT_COUNT must be a positive integer; got: $SEGMENT_COUNT" >&2
    exit 1
fi

echo "chain_name,segment_index,job_name,job_id,dependency_job_id,case_key_1,case_key_2,case_dir_1,case_dir_2,segment_walltime" > "$SUBMISSION_CSV"

submit_sbatch() {
    local output
    local job_id

    output="$(sbatch "$@")"
    job_id="$(printf '%s\n' "$output" | awk '/^[0-9]+$/ {id=$1} END {print id}')"
    if [[ -z "$job_id" ]]; then
        echo "Unable to parse job id from sbatch output:" >&2
        printf '%s\n' "$output" >&2
        exit 1
    fi
    printf '%s\n' "$job_id"
}

submit_chain() {
    local chain_name="$1"
    local case_key_1="$2"
    local case_dir_1="$3"
    local case_key_2="$4"
    local case_dir_2="$5"
    local prior_job_id=""
    local first_job_id=""
    local final_job_id=""
    local segment_index
    local segment_job_name
    local job_id

    for ((segment_index = 1; segment_index <= SEGMENT_COUNT; segment_index++)); do
        segment_job_name="${chain_name}_s${segment_index}"
        if [[ -n "$prior_job_id" ]]; then
            job_id="$(submit_sbatch --parsable -t "$SEGMENT_WALLTIME" --dependency="afterany:${prior_job_id}" -J "$segment_job_name" --export=ALL,OPENFOAM13_ENV_SH="$OPENFOAM_ENV_SH",RCWALLBC_LIBDIR="$RCWALLBC_LIBDIR",CASE_DIR_1="$case_dir_1",CASE_LABEL_1="$case_key_1",CASE_DIR_2="$case_dir_2",CASE_LABEL_2="$case_key_2" "$LAUNCHER")"
        else
            job_id="$(submit_sbatch --parsable -t "$SEGMENT_WALLTIME" -J "$segment_job_name" --export=ALL,OPENFOAM13_ENV_SH="$OPENFOAM_ENV_SH",RCWALLBC_LIBDIR="$RCWALLBC_LIBDIR",CASE_DIR_1="$case_dir_1",CASE_LABEL_1="$case_key_1",CASE_DIR_2="$case_dir_2",CASE_LABEL_2="$case_key_2" "$LAUNCHER")"
            first_job_id="$job_id"
        fi

        echo "$chain_name,$segment_index,$segment_job_name,$job_id,${prior_job_id:-},$case_key_1,$case_key_2,$case_dir_1,$case_dir_2,$SEGMENT_WALLTIME" >> "$SUBMISSION_CSV"
        prior_job_id="$job_id"
        final_job_id="$job_id"
    done

    echo "$chain_name -> first=$first_job_id final=$final_job_id segments=$SEGMENT_COUNT walltime=$SEGMENT_WALLTIME"
}

submit_chain "ethan_w12_nq9d"     "water1" "$PWD/jadyn_runs/modern_runs/2026-06-18_convergence_and_jin_envelope_wave/runs/water1/case_stage/val_water_test_1_coarse_mesh_laminar_continuation"     "water2" "$PWD/jadyn_runs/modern_runs/2026-06-18_convergence_and_jin_envelope_wave/runs/water2/case_stage/val_water_test_2_coarse_mesh_laminar_continuation"

submit_chain "ethan_w34_nq9d"     "water3" "$PWD/jadyn_runs/modern_runs/2026-06-18_convergence_and_jin_envelope_wave/runs/water3/case_stage/val_water_test_3_coarse_mesh_laminar_continuation"     "water4" "$PWD/jadyn_runs/modern_runs/2026-06-18_convergence_and_jin_envelope_wave/runs/water4/case_stage/val_water_test_4_coarse_mesh_laminar_continuation"

submit_chain "ethan_s1cont_s1hi_nq9d"     "salt1_jin_basecont" "$RUNS_ROOT/salt1_jin_basecont/case_stage/viscosity_screening_salt_test_1_jin_coarse_mesh_continuation"     "salt1_jin_hiq_balq" "$RUNS_ROOT/salt1_jin_hiq_balq/case_stage/viscosity_screening_salt_test_1_jin_coarse_mesh_continuation"

submit_chain "ethan_s23hi_nq9d"     "salt2_jin_hiq_balq" "$PWD/jadyn_runs/modern_runs/2026-06-19_ethan_blocker_and_1d_followon_wave/runs/salt2_jin_hiq_hiins/case_stage/viscosity_screening_salt_test_2_jin_coarse_mesh"     "salt3_jin_hiq_balq" "$PWD/jadyn_runs/modern_runs/2026-06-19_ethan_blocker_and_1d_followon_wave/runs/salt3_jin_hiq_hiins/case_stage/viscosity_screening_salt_test_3_jin_coarse_mesh"

submit_chain "ethan_s4hi_s1lo_nq9d"     "salt4_jin_hiq_balq" "$PWD/jadyn_runs/modern_runs/2026-06-19_ethan_blocker_and_1d_followon_wave/runs/salt4_jin_hiq_hiins/case_stage/viscosity_screening_salt_test_4_jin_coarse_mesh_continuation"     "salt1_jin_loq_balq" "$RUNS_ROOT/salt1_jin_loq_balq/case_stage/viscosity_screening_salt_test_1_jin_coarse_mesh_continuation"

submit_chain "ethan_s2mid_nq9d"     "salt2_jin_hi5q_balq" "$RUNS_ROOT/salt2_jin_hi5q_balq/case_stage/viscosity_screening_salt_test_2_jin_coarse_mesh"     "salt2_jin_lo5q_balq" "$RUNS_ROOT/salt2_jin_lo5q_balq/case_stage/viscosity_screening_salt_test_2_jin_coarse_mesh"

submit_chain "ethan_s3mid_nq9d"     "salt3_jin_hi5q_balq" "$RUNS_ROOT/salt3_jin_hi5q_balq/case_stage/viscosity_screening_salt_test_3_jin_coarse_mesh"     "salt3_jin_lo5q_balq" "$RUNS_ROOT/salt3_jin_lo5q_balq/case_stage/viscosity_screening_salt_test_3_jin_coarse_mesh"

submit_chain "ethan_s4mid_nq9d"     "salt4_jin_hi5q_balq" "$RUNS_ROOT/salt4_jin_hi5q_balq/case_stage/viscosity_screening_salt_test_4_jin_coarse_mesh_continuation"     "salt4_jin_lo5q_balq" "$RUNS_ROOT/salt4_jin_lo5q_balq/case_stage/viscosity_screening_salt_test_4_jin_coarse_mesh_continuation"
