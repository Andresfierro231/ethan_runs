#!/usr/bin/env python3
"""Recommend sbatch, srun, or tmux+srun for repo compute work."""
from __future__ import annotations

import argparse
import socket


def infer_host_kind(hostname: str) -> str:
    if hostname.startswith("login") or ".login" in hostname:
        return "login"
    if hostname.startswith("c") and "-" in hostname:
        return "compute"
    return "unknown"


def recommend(host_kind: str, duration: str, openfoam: bool, persistent: bool) -> str:
    long = duration in {"long", "overnight"}
    if long or persistent:
        if host_kind == "login":
            return "sbatch"
        if host_kind == "compute":
            return "prepare sbatch script, submit from login node"
        return "sbatch from login node"
    if host_kind == "compute":
        return "srun" if openfoam else "direct compute-node command or srun for accounting"
    if host_kind == "login":
        return "sbatch for heavy work; no login-node heavy run"
    return "sbatch or obtain an interactive allocation, then srun"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--duration", choices=["short", "medium", "long", "overnight"], required=True)
    parser.add_argument("--openfoam", action="store_true")
    parser.add_argument("--persistent", action="store_true", help="Must survive shell/session loss.")
    parser.add_argument("--host-kind", choices=["login", "compute", "unknown"], default=None)
    args = parser.parse_args()

    hostname = socket.gethostname()
    host_kind = args.host_kind or infer_host_kind(hostname)
    rec = recommend(host_kind, args.duration, args.openfoam, args.persistent)
    print(f"host={hostname} host_kind={host_kind}")
    print(f"recommendation={rec}")
    print("pattern=principal_agent_launches_and_documents; monitor_agent_checks_read_only")
    print(
        "handoff_fields=principal_task,monitor_task,job_id,step_id_or_tmux_session,"
        "node,command,stdout_log,stderr_log,heartbeat,completion_condition,"
        "safe_kill_or_cancel_rule"
    )
    print(
        "monitor_policy=check_squeue_sacct_logs_outputs; no_duplicate_submit;"
        "no_cancel_requeue_harvest_admit_without_explicit_board_scope"
    )
    print(
        "policy=long durable work uses sbatch from login; compute work uses srun; "
        "tmux only preserves launchers; principal agent stays available to user"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
