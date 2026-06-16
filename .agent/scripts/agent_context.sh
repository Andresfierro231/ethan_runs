#!/usr/bin/env bash
set -euo pipefail

find_repo_root() {
  if git_root="$(git rev-parse --show-toplevel 2>/dev/null)"; then
    printf '%s\n' "$git_root"
    return 0
  fi

  local dir
  dir="${PWD}"
  while [ "$dir" != "/" ]; do
    if [ -f "$dir/AGENTS.md" ] && [ -d "$dir/.agent" ]; then
      printf '%s\n' "$dir"
      return 0
    fi
    dir="$(dirname "$dir")"
  done
  return 1
}

repo_root="$(find_repo_root)"
board_path="$repo_root/.agent/BOARD.md"
ownership_path="$repo_root/.agent/FILE_OWNERSHIP.md"
roles_path="$repo_root/.agent/ROLES.md"
journal_policy_path="$repo_root/.agent/JOURNAL_POLICY.md"
cleanup_policy_path="$repo_root/.agent/CLEANUP_POLICY.md"
root_agents_path="$repo_root/AGENTS.md"

collect_local_instructions() {
  local dir rel instructions=()
  dir="$PWD"
  while :; do
    for candidate in AGENTS.override.md README.md TODO.md; do
      if [ -f "$dir/$candidate" ]; then
        rel="${dir#$repo_root/}"
        if [ "$dir" = "$repo_root" ]; then
          instructions+=("$candidate")
        elif [ "$rel" = "$dir" ]; then
          instructions+=("$dir/$candidate")
        else
          instructions+=("$rel/$candidate")
        fi
      fi
    done

    if [ "$dir" = "$repo_root" ] || [ "$dir" = "/" ]; then
      break
    fi
    dir="$(dirname "$dir")"
  done

  if [ "${#instructions[@]}" -eq 0 ]; then
    printf '%s\n' "none"
    return 0
  fi

  printf '%s\n' "${instructions[@]}"
}

branch_name="$(git -C "$repo_root" rev-parse --abbrev-ref HEAD 2>/dev/null || true)"
if [ -z "$branch_name" ] || [ "$branch_name" = "HEAD" ]; then
  branch_name="no-HEAD"
fi

active_summary="No active task summary found."
if [ -f "$board_path" ]; then
  active_line="$(
    awk '
      /^## Active/ { in_active=1; next }
      /^## / && in_active { exit }
      in_active && /^\| AGENT-/ { print; exit }
    ' "$board_path"
  )"
  if [ -n "$active_line" ]; then
    active_summary="$active_line"
  fi
fi

local_instruction_list="$(collect_local_instructions)"

cat <<EOF
Repo root: $repo_root
Current branch: $branch_name
Current working directory: $PWD
Task board: $board_path

Read these first:
- $root_agents_path
- $board_path
- $ownership_path
- $roles_path
- $journal_policy_path
- $cleanup_policy_path

Local instructions from here toward repo root:
$(printf '%s\n' "$local_instruction_list" | sed 's/^/- /')

Active task summary:
$active_summary
EOF
