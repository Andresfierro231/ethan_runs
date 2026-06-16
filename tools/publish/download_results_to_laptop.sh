#!/usr/bin/env bash
set -euo pipefail

usage() {
    cat <<'EOF'
Usage:
  download_results_to_laptop.sh DEST_DIR [SOURCE_ID ...]

Purpose:
  Run this script from a personal laptop, not from LS6. It pulls the current
  report packages, typed figure outputs, and reconstructed-case mirrors needed
  to open selected simulation results locally in ParaView. Reconstructed-case
  downloads are dereferenced so absolute LS6 symlinks become real local files.

Environment overrides:
  REMOTE_USER   Defaults to andresfierro231
  REMOTE_HOST   Defaults to login3.ls6.tacc.utexas.edu
  REMOTE_ROOT   Defaults to /scratch/09748/andresfierro231/projects_scratch/ethan_runs
  RSYNC_FLAGS   Extra rsync flags, appended after the defaults

Examples:
  ./tools/publish/download_results_to_laptop.sh ~/Downloads/ethan_runs_laptop     viscosity_screening_salt_test_1_kirst_coarse_mesh     val_salt_test_2_coarse_mesh_laminar

  REMOTE_HOST=login3.ls6.tacc.utexas.edu     ./tools/publish/download_results_to_laptop.sh ~/Downloads/ethan_runs_laptop
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
    usage
    exit 0
fi

if [[ $# -lt 1 ]]; then
    usage >&2
    exit 1
fi

DEST_DIR=$1
shift

REMOTE_USER=${REMOTE_USER:-andresfierro231}
REMOTE_HOST=${REMOTE_HOST:-login3.ls6.tacc.utexas.edu}
REMOTE_ROOT=${REMOTE_ROOT:-/scratch/09748/andresfierro231/projects_scratch/ethan_runs}
REMOTE_TARGET="${REMOTE_USER}@${REMOTE_HOST}"

mkdir -p "${DEST_DIR}"

BASE_PATHS=(
    "registry/case_registry.csv"
    "figures/last_timestep_temperature_slice_status.json"
    "figures/png"
    "figures/svg"
    "figures/pdf"
    "reports/2026-06-08_sponsor_salt_status_deck"
    "reports/2026-06-08_ethan_presentation_figure_package"
    "reports/2026-06-05_ethan_continuation_diagnosis"
    "reports/2026-06-05_ethan_convergence_and_salt1_campaign"
    "reports/2026-06-05_ethan_wall_loss_resistance_coupling"
    "reports/2026-06-04_salt2_behavior_package"
    "reports/2026-06-04_ethan_transient_axial_package"
    "reports/2026-06-01_weekly_status"
)

if [[ $# -eq 0 ]]; then
    SOURCE_IDS=(
        "viscosity_screening_salt_test_1_kirst_coarse_mesh"
        "val_salt_test_2_coarse_mesh_laminar"
        "viscosity_screening_salt_test_3_jin_coarse_mesh"
        "viscosity_screening_salt_test_4_jin_coarse_mesh"
    )
else
    SOURCE_IDS=("$@")
fi

sync_one() {
    local relative_path=$1
    local rsync_mode=(-av --relative --info=progress2)
    if [[ "${relative_path}" == staging/render_inputs/*/reconstructed_case* ]]; then
        rsync_mode=(-avL --relative --info=progress2)
    fi
    if ssh "${REMOTE_TARGET}" "test -e '${REMOTE_ROOT}/${relative_path}'"; then
        rsync "${rsync_mode[@]}" ${RSYNC_FLAGS:-}             "${REMOTE_TARGET}:${REMOTE_ROOT}/./${relative_path}"             "${DEST_DIR}/"
    else
        printf 'Skipping missing remote path: %s
' "${relative_path}" >&2
    fi
}

printf 'Syncing shared reports and figures from %s:%s
' "${REMOTE_TARGET}" "${REMOTE_ROOT}"
for relative_path in "${BASE_PATHS[@]}"; do
    sync_one "${relative_path}"
done

printf 'Syncing reconstructed cases and work products for selected source IDs
'
for source_id in "${SOURCE_IDS[@]}"; do
    sync_one "staging/render_inputs/${source_id}/reconstructed_case"
    sync_one "work_products/${source_id}"
done

printf 'Download complete. Local root: %s
' "${DEST_DIR}"
