---
provenance:
  - staging/upload_jobs/2026-06-16_ethan_runs_box_upload.sbatch
  - staging/upload_jobs/slurm-3297384.out
  - staging/upload_jobs/slurm-3297384.err
  - tmp/2026-06-16_ethan_box_upload_probe/rclone_full_upload.log
tags: [journal, agent-436, box, rclone, sbatch]
related:
  - .agent/status/2026-07-15_AGENT-436.md
  - operational_notes/06-26/16/2026-06-16_ethan_box_upload_plan.md
task: AGENT-436
date: 2026-07-15
role: Coordinator/Scheduler/Writer
type: journal
status: complete
---
# rclone Box Upload sbatch Submit

The user requested the rclone Box upload to be submitted through sbatch.

Verified before submission:

- `staging/upload_jobs/2026-06-16_ethan_runs_box_upload.sbatch` exists.
- `/home1/09748/andresfierro231/bin/rclone` exists and is executable.
- `/home1/09748/andresfierro231/.config/rclone/rclone.conf` exists.
- No `ethan_box_upload` job was already visible via `squeue -n ethan_box_upload`.

Direct `sbatch` from the current compute node failed with:

```text
NOTIFICATION: sbatch not available on compute nodes. Use a login node.
```

Submitted via login node:

```bash
ssh login3.ls6.tacc.utexas.edu 'cd /scratch/09748/andresfierro231/projects_scratch/ethan_runs && sbatch staging/upload_jobs/2026-06-16_ethan_runs_box_upload.sbatch'
```

Result:

- Slurm job id: `3297384`
- Initial state: `RUNNING`
- Initial node: `c318-011`

Monitor commands:

```bash
squeue -j 3297384
sacct -j 3297384 --format=JobID,JobName,State,ExitCode,Elapsed,Start,End,NodeList -P
tail -f staging/upload_jobs/slurm-3297384.out
tail -f tmp/2026-06-16_ethan_box_upload_probe/rclone_full_upload.log
```

Initial rclone evidence showed new files being copied. The job is intentionally
large and may take a long time; this journal records submission and initial
health only, not terminal completion.
