#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CAMPAIGN_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
RUNS_ROOT="$CAMPAIGN_ROOT/runs"

mkdir -p "$RUNS_ROOT"

stage_case() {
    local case_key="$1"
    local source_case="$2"
    local target_case="$3"
    local target_outer_m="$4"

    if [[ ! -d "$source_case" ]]; then
        echo "Missing source case: $source_case" >&2
        exit 1
    fi
    if [[ -e "$target_case" ]]; then
        echo "Target already exists: $target_case" >&2
        exit 1
    fi

    mkdir -p "$(dirname "$target_case")"
    cp -a "$source_case" "$target_case"

    if [[ ! -d "$target_case/0" ]]; then
        echo "Staged case missing 0/: $target_case" >&2
        exit 1
    fi
    if [[ ! -d "$target_case/constant" ]]; then
        echo "Staged case missing constant/: $target_case" >&2
        exit 1
    fi
    if [[ ! -d "$target_case/system" ]]; then
        echo "Staged case missing system/: $target_case" >&2
        exit 1
    fi
    if [[ ! -d "$target_case/processors64" ]]; then
        echo "Staged case missing processors64/: $target_case" >&2
        exit 1
    fi

    perl -0pi -e "s/0\\.035559999999999994/${target_outer_m}/g" "$target_case/0/T"

    if grep -Fq "0.035559999999999994" "$target_case/0/T"; then
        echo "Baseline outer insulation remains in $target_case/0/T" >&2
        exit 1
    fi
    if ! grep -Fq "$target_outer_m" "$target_case/0/T"; then
        echo "Target outer insulation value missing in $target_case/0/T" >&2
        exit 1
    fi

    echo "Staged $case_key at $target_case"
}

stage_case \
    "salt1_jin_optins" \
    "/scratch/09748/andresfierro231/projects_scratch/ethan_runs/jadyn_runs/salt1/2026-06-04_jin_continuation_candidate/case_stage/viscosity_screening_salt_test_1_jin_coarse_mesh_continuation" \
    "$RUNS_ROOT/salt1_jin_optins/case_stage/viscosity_screening_salt_test_1_jin_coarse_mesh_continuation" \
    "0.060960000000"

stage_case \
    "salt2_jin_optins" \
    "/scratch/09748/andresfierro231/projects_scratch/ethan_runs/staging/modern_runs/2026-06-01_full_extractable_batch/salt/viscosity_screening_salt_test_2_jin_coarse_mesh" \
    "$RUNS_ROOT/salt2_jin_optins/case_stage/viscosity_screening_salt_test_2_jin_coarse_mesh" \
    "0.043919140000"

stage_case \
    "salt3_jin_optins" \
    "/scratch/09748/andresfierro231/projects_scratch/ethan_runs/staging/modern_runs/2026-06-01_full_extractable_batch/salt/viscosity_screening_salt_test_3_jin_coarse_mesh" \
    "$RUNS_ROOT/salt3_jin_optins/case_stage/viscosity_screening_salt_test_3_jin_coarse_mesh" \
    "0.042407840000"

stage_case \
    "salt4_jin_optins" \
    "/scratch/09748/andresfierro231/projects_scratch/ethan_runs/jadyn_runs/salt4/2026-06-04_jin_continuation_candidate/case_stage/viscosity_screening_salt_test_4_jin_coarse_mesh_continuation" \
    "$RUNS_ROOT/salt4_jin_optins/case_stage/viscosity_screening_salt_test_4_jin_coarse_mesh_continuation" \
    "0.046423580000"

echo "All four optimum-insulation Salt Jin cases staged successfully under: $RUNS_ROOT"
