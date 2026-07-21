#!/usr/bin/env bash
set -euo pipefail

usage() {
    cat <<'EOF'
Usage:
  rsync_ethan_runs_backup.sh ACTION [options]

Actions:
  prepare   Create the backup directory layout and top-level README only.
  plan      Run a dry-run rsync and write manifest logs showing new/changed files.
  sync      Run the additive rsync copy and write a sync log plus latest manifests.

Purpose:
  Maintain a readable, incremental backup of the local ethan_runs workspace under
  /home1/09748/andresfierro231/bubble_flow_loop/tamu_loop_box/cfd_runs.

Default destination layout:
  <backup-root>/
    README.md
    manifests/
      latest/
      history/<stamp>/
    mirror/ethan_runs/

Safety:
  - Default mode is additive/update-only. It does not delete files already in
    the backup mirror.
  - Default scope excludes control-state and scratch-only trees such as .git,
    .agent, cache, tmp, and linked_cases.
  - Use --include-tmp only if the extra scratch payload is intentionally part
    of the backup contract.

Options:
  --source-root PATH        Source workspace root. Default: repo root
  --backup-root PATH        Backup root. Default:
                            /home1/09748/andresfierro231/bubble_flow_loop/tamu_loop_box/cfd_runs/ethan_runs_backup
  --mirror-name NAME        Mirror subdirectory name. Default: ethan_runs
  --manifest-stamp STAMP    Override manifest stamp. Default: YYYYMMDDTHHMMSS
  --rsync-bin PATH          rsync executable. Default: rsync
  --checksum                Compare by checksum instead of size+mtime
  --include-tmp             Include tmp/ in the backup scope
  --top-level-pass          Run one rsync pass per top-level included path
                            instead of one whole-tree rsync
  --help, -h                Show this help text

Examples:
  bash tools/publish/rsync_ethan_runs_backup.sh prepare
  bash tools/publish/rsync_ethan_runs_backup.sh plan
  bash tools/publish/rsync_ethan_runs_backup.sh sync
  bash tools/publish/rsync_ethan_runs_backup.sh plan --checksum
  bash tools/publish/rsync_ethan_runs_backup.sh sync --include-tmp
  bash tools/publish/rsync_ethan_runs_backup.sh sync --top-level-pass
EOF
}

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DEFAULT_BACKUP_ROOT="/home1/09748/andresfierro231/bubble_flow_loop/tamu_loop_box/cfd_runs/ethan_runs_backup"

if [[ $# -lt 1 ]]; then
    usage >&2
    exit 1
fi

ACTION="$1"
shift

SOURCE_ROOT="${SOURCE_ROOT:-$ROOT}"
BACKUP_ROOT="${BACKUP_ROOT:-$DEFAULT_BACKUP_ROOT}"
MIRROR_NAME="ethan_runs"
MANIFEST_STAMP=""
RSYNC_BIN="${RSYNC_BIN:-rsync}"
USE_CHECKSUM=0
INCLUDE_TMP=0
TOP_LEVEL_PASS=0

while [[ $# -gt 0 ]]; do
    case "$1" in
        --source-root)
            SOURCE_ROOT="$2"
            shift 2
            ;;
        --backup-root)
            BACKUP_ROOT="$2"
            shift 2
            ;;
        --mirror-name)
            MIRROR_NAME="$2"
            shift 2
            ;;
        --manifest-stamp)
            MANIFEST_STAMP="$2"
            shift 2
            ;;
        --rsync-bin)
            RSYNC_BIN="$2"
            shift 2
            ;;
        --checksum)
            USE_CHECKSUM=1
            shift
            ;;
        --include-tmp)
            INCLUDE_TMP=1
            shift
            ;;
        --top-level-pass)
            TOP_LEVEL_PASS=1
            shift
            ;;
        --help|-h)
            usage
            exit 0
            ;;
        *)
            echo "Unknown option: $1" >&2
            usage >&2
            exit 1
            ;;
    esac
done

case "$ACTION" in
    prepare|plan|sync)
        ;;
    *)
        echo "Unknown action: $ACTION" >&2
        usage >&2
        exit 1
        ;;
esac

if [[ -z "$MANIFEST_STAMP" ]]; then
    MANIFEST_STAMP="$(date +%Y%m%dT%H%M%S)"
fi

README_PATH="$BACKUP_ROOT/README.md"
MANIFEST_ROOT="$BACKUP_ROOT/manifests"
LATEST_DIR="$MANIFEST_ROOT/latest"
HISTORY_DIR="$MANIFEST_ROOT/history/$MANIFEST_STAMP"
MIRROR_ROOT="$BACKUP_ROOT/mirror/$MIRROR_NAME"
STATUS_PATH="$HISTORY_DIR/rsync_status.txt"

EXCLUDE_DIRS=(
    ".git"
    ".agent"
    ".agents"
    ".codex"
    "cache"
    "linked_cases"
    "__pycache__"
    ".pytest_cache"
)
if [[ "$INCLUDE_TMP" -eq 0 ]]; then
    EXCLUDE_DIRS+=("tmp")
fi
EXCLUDE_NAMES=(".DS_Store")
RSYNC_ARGS=()
TOP_LEVEL_INCLUDE_DIRS=(
    "staging"
    "jadyn_runs"
    "tmp_extract"
    "reports"
    "figures"
    "work_products"
    "imports"
    "registry"
    "config"
    "tools"
    "journals"
    "operational_notes"
)

write_backup_readme() {
    cat > "$README_PATH" <<EOF
# Ethan Runs Backup

Prepared: $(date --iso-8601=seconds)

## Purpose

This directory stores a readable incremental backup of the local workspace:

- source workspace: $SOURCE_ROOT
- mirrored data root: mirror/$MIRROR_NAME
- latest manifests: manifests/latest
- dated manifest history: manifests/history/<timestamp>

## Layout

- \`mirror/$MIRROR_NAME/\`
  Additive rsync mirror of the selected workspace scope.
- \`manifests/latest/\`
  Most recent dry-run or sync outputs for quick inspection.
- \`manifests/history/<timestamp>/\`
  Immutable per-run record of the exact rsync command, plan log, and summary.

## Default exclusions

The default backup scope excludes local control-state and scratch-only trees:

$(for item in "${EXCLUDE_DIRS[@]}"; do printf -- "- %s\n" "$item"; done)
$(for item in "${EXCLUDE_NAMES[@]}"; do printf -- "- %s\n" "$item"; done)

Use \`--include-tmp\` if \`tmp/\` should also be preserved in the mirror.

## How to inspect diffs

Dry-run delta manifests are written by:

\`\`\`bash
bash tools/publish/rsync_ethan_runs_backup.sh plan
\`\`\`

Key files:

- \`manifests/latest/summary.txt\`
- \`manifests/latest/new_files.txt\`
- \`manifests/latest/changed_files.txt\`
- \`manifests/latest/rsync_plan.log\`

## How to run the real copy

Preferred compute-node submission wrapper:

\`\`\`bash
bash tools/publish/submit_ethan_runs_backup_sbatch.sh --mode sync --time 10:00:00
\`\`\`

For a live source tree where case files may change during transfer, prefer:

\`\`\`bash
bash tools/publish/rsync_ethan_runs_backup.sh sync --top-level-pass
\`\`\`

That runs one rsync pass per top-level included directory so a single volatile
subtree does not prevent the rest of the workspace from syncing.
EOF
}

write_scope_manifest() {
    cat > "$LATEST_DIR/backup_scope.txt" <<EOF
source_root=$SOURCE_ROOT
backup_root=$BACKUP_ROOT
mirror_root=$MIRROR_ROOT
include_tmp=$INCLUDE_TMP
checksum_mode=$USE_CHECKSUM
top_level_pass=$TOP_LEVEL_PASS
exclude_dirs=$(IFS=,; printf '%s' "${EXCLUDE_DIRS[*]}")
exclude_names=$(IFS=,; printf '%s' "${EXCLUDE_NAMES[*]}")
EOF
    cp -f "$LATEST_DIR/backup_scope.txt" "$HISTORY_DIR/backup_scope.txt"
}

prepare_layout() {
    mkdir -p "$LATEST_DIR" "$HISTORY_DIR" "$MIRROR_ROOT"
    write_backup_readme
    write_scope_manifest
}

build_rsync_args() {
    RSYNC_ARGS=(
        "-aH"
        "--human-readable"
        "--itemize-changes"
        "--out-format=%i|%l|%n%L"
        "--partial"
    )
    if [[ "$USE_CHECKSUM" -eq 1 ]]; then
        RSYNC_ARGS+=("--checksum")
    fi
    local exclude_dir
    for exclude_dir in "${EXCLUDE_DIRS[@]}"; do
        RSYNC_ARGS+=("--exclude=${exclude_dir}/**" "--exclude=${exclude_dir}")
    done
    local exclude_name
    for exclude_name in "${EXCLUDE_NAMES[@]}"; do
        RSYNC_ARGS+=("--exclude=${exclude_name}")
    done
}

write_command_file() {
    local path="$1"
    local include_dir
    if [[ "$TOP_LEVEL_PASS" -eq 1 ]]; then
        {
            printf '# top-level-pass sync order\n'
            for include_dir in "${TOP_LEVEL_INCLUDE_DIRS[@]}"; do
                printf '%q ' "$RSYNC_BIN" "${RSYNC_ARGS[@]}" "$SOURCE_ROOT/$include_dir/" "$MIRROR_ROOT/$include_dir/"
                printf '\n'
            done
        } > "$path"
        return
    fi
    printf '%q ' "$RSYNC_BIN" "${RSYNC_ARGS[@]}" "$SOURCE_ROOT/" "$MIRROR_ROOT/" > "$path"
    printf '\n' >> "$path"
}

render_summary() {
    local mode="$1"
    local summary_path="$2"
    local log_path="$3"
    local new_count changed_count dir_count link_count
    new_count=$(wc -l < "$HISTORY_DIR/new_files.txt")
    changed_count=$(wc -l < "$HISTORY_DIR/changed_files.txt")
    dir_count=$(wc -l < "$HISTORY_DIR/created_dirs.txt")
    link_count=$(wc -l < "$HISTORY_DIR/symlink_updates.txt")

    cat > "$summary_path" <<EOF
stamp: $MANIFEST_STAMP
mode: $mode
source_root: $SOURCE_ROOT
backup_root: $BACKUP_ROOT
mirror_root: $MIRROR_ROOT
checksum_mode: $USE_CHECKSUM
include_tmp: $INCLUDE_TMP
top_level_pass: $TOP_LEVEL_PASS
new_files: $new_count
changed_files: $changed_count
created_dirs: $dir_count
symlink_updates: $link_count
rsync_log: $log_path
status_file: $STATUS_PATH
EOF
}

extract_change_lists() {
    local log_path="$1"
    awk -F'|' '$1 ~ /^>f\+{9}$/ {print $3}' "$log_path" > "$HISTORY_DIR/new_files.txt"
    awk -F'|' '$1 ~ /^>f/ && $1 !~ /^>f\+{9}$/ {print $3}' "$log_path" > "$HISTORY_DIR/changed_files.txt"
    awk -F'|' '$1 ~ /^cd/ {print $3}' "$log_path" > "$HISTORY_DIR/created_dirs.txt"
    awk -F'|' '$1 ~ /^cL/ || $1 ~ /^>L/ {print $3}' "$log_path" > "$HISTORY_DIR/symlink_updates.txt"
}

copy_latest_manifests() {
    local mode="$1"
    local log_basename="$2"
    cp -f "$HISTORY_DIR/$log_basename" "$LATEST_DIR/$log_basename"
    cp -f "$HISTORY_DIR/new_files.txt" "$LATEST_DIR/new_files.txt"
    cp -f "$HISTORY_DIR/changed_files.txt" "$LATEST_DIR/changed_files.txt"
    cp -f "$HISTORY_DIR/created_dirs.txt" "$LATEST_DIR/created_dirs.txt"
    cp -f "$HISTORY_DIR/symlink_updates.txt" "$LATEST_DIR/symlink_updates.txt"
    cp -f "$HISTORY_DIR/${mode}_summary.txt" "$LATEST_DIR/summary.txt"
    cp -f "$HISTORY_DIR/rsync_command.txt" "$LATEST_DIR/rsync_command.txt"
    cp -f "$STATUS_PATH" "$LATEST_DIR/rsync_status.txt"
    printf '%s\n' "$MANIFEST_STAMP" > "$LATEST_DIR/latest_stamp.txt"
}

write_status_header() {
    cat > "$STATUS_PATH" <<EOF
stamp: $MANIFEST_STAMP
source_root: $SOURCE_ROOT
mirror_root: $MIRROR_ROOT
include_tmp: $INCLUDE_TMP
checksum_mode: $USE_CHECKSUM
top_level_pass: $TOP_LEVEL_PASS
EOF
}

append_pass_status() {
    local label="$1"
    local rc="$2"
    local meaning
    case "$rc" in
        0)
            meaning="ok"
            ;;
        24)
            meaning="ok_with_vanished_files"
            ;;
        *)
            meaning="error"
            ;;
    esac
    printf '%s|%s|%s\n' "$label" "$rc" "$meaning" >> "$STATUS_PATH"
}

run_one_rsync_pass() {
    local log_path="$1"
    shift
    local source_path="$1"
    shift
    local dest_path="$1"
    shift
    local rc=0

    mkdir -p "$dest_path"

    set +e
    "$RSYNC_BIN" "${RSYNC_ARGS[@]}" "$@" "$source_path" "$dest_path" | tee -a "$log_path"
    rc=${PIPESTATUS[0]}
    set -e

    return "$rc"
}

run_rsync_with_scope() {
    local mode="$1"
    local log_path="$2"
    local dry_run_flag=()
    local include_dir
    local pass_rc=0
    local overall_rc=0

    if [[ "$mode" == "plan" ]]; then
        dry_run_flag=("--dry-run")
    fi

    write_status_header

    if [[ "$TOP_LEVEL_PASS" -eq 1 ]]; then
        for include_dir in "${TOP_LEVEL_INCLUDE_DIRS[@]}"; do
            if [[ "$include_dir" == "tmp" && "$INCLUDE_TMP" -eq 0 ]]; then
                continue
            fi
            if [[ ! -e "$SOURCE_ROOT/$include_dir" ]]; then
                printf 'missing_top_level|%s\n' "$include_dir" >> "$STATUS_PATH"
                continue
            fi
            pass_rc=0
            run_one_rsync_pass \
                "$log_path" \
                "$SOURCE_ROOT/$include_dir/" \
                "$MIRROR_ROOT/$include_dir/" \
                "${dry_run_flag[@]}" || pass_rc=$?
            append_pass_status "$include_dir" "$pass_rc"
            if [[ "$pass_rc" -ne 0 && "$pass_rc" -ne 24 ]]; then
                overall_rc="$pass_rc"
                break
            fi
        done
        return "$overall_rc"
    fi

    run_one_rsync_pass \
        "$log_path" \
        "$SOURCE_ROOT/" \
        "$MIRROR_ROOT/" \
        "${dry_run_flag[@]}" || pass_rc=$?
    append_pass_status "whole_tree" "$pass_rc"
    if [[ "$pass_rc" -ne 0 && "$pass_rc" -ne 24 ]]; then
        return "$pass_rc"
    fi
    return 0
}

run_plan() {
    local log_path="$HISTORY_DIR/rsync_plan.log"
    prepare_layout
    build_rsync_args
    write_command_file "$HISTORY_DIR/rsync_command.txt"
    : > "$log_path"
    run_rsync_with_scope "plan" "$log_path"
    extract_change_lists "$log_path"
    render_summary "plan" "$HISTORY_DIR/plan_summary.txt" "$log_path"
    copy_latest_manifests "plan" "rsync_plan.log"
}

run_sync() {
    local log_path="$HISTORY_DIR/rsync_sync.log"
    prepare_layout
    build_rsync_args
    write_command_file "$HISTORY_DIR/rsync_command.txt"
    : > "$log_path"
    run_rsync_with_scope "sync" "$log_path"
    extract_change_lists "$log_path"
    render_summary "sync" "$HISTORY_DIR/sync_summary.txt" "$log_path"
    copy_latest_manifests "sync" "rsync_sync.log"
}

if [[ "$ACTION" == "prepare" ]]; then
    prepare_layout
elif [[ "$ACTION" == "plan" ]]; then
    run_plan
else
    run_sync
fi
