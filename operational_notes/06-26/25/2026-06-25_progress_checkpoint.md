# Progress Checkpoint

Date: `2026-06-25`
Checkpoint writer: `AGENT-132`

## Purpose

This note is the restart package for tomorrow. It captures the exact state of
today’s two active user-facing threads:

1. backing up the current `ethan_runs` workspace to
   `/home1/09748/andresfierro231/bubble_flow_loop/tamu_loop_box/cfd_runs`
2. producing a reusable hydrostatic-corrected corner-pressure-drop table with
   documented math

## Big picture

Today’s work produced:

- a real external backup root with documentation and an active Slurm copy job
- a reusable corner-pressure summarizer plus a generated table package

The main things still worth watching tomorrow are:

- whether the backup job completes cleanly and whether it needs a follow-up
  incremental pass because the source tree is live
- whether the current corner-pressure summary should be narrowed, extended, or
  fed by refreshed case-analysis roots with more retained times

## Thread 1: Backup

### What exists now

External backup root:

`/home1/09748/andresfierro231/bubble_flow_loop/tamu_loop_box/cfd_runs/ethan_runs_backup`

Important local files:

- [rsync_ethan_runs_backup.sh](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/tools/publish/rsync_ethan_runs_backup.sh:1)
- [submit_ethan_runs_backup_sbatch.sh](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/tools/publish/submit_ethan_runs_backup_sbatch.sh:1)
- [2026-06-25_ethan_runs_backup_plan.md](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/operational_notes/06-26/25/2026-06-25_ethan_runs_backup_plan.md:1)
- [2026-06-25_ethan_runs_backup_inventory.json](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/imports/2026-06-25_ethan_runs_backup_inventory.json:1)

Backup layout:

```text
/home1/.../cfd_runs/ethan_runs_backup/
  README.md
  manifests/
    latest/
    history/<timestamp>/
  mirror/
    ethan_runs/
```

### Current job state

As checked on `2026-06-25` at about `17:48 CDT`:

- live job id: `3259614`
- job name: `ethan_backup_sync`
- partition: `NuclearEnergy`
- state: `RUNNING`
- elapsed at last check: `02:45:54`
- walltime request: `10:00:00`
- node: `c318-020`

Key command used:

```bash
ssh login3.ls6.tacc.utexas.edu \
  'cd /scratch/09748/andresfierro231/projects_scratch/ethan_runs && \
   bash tools/publish/submit_ethan_runs_backup_sbatch.sh --mode sync --time 10:00:00'
```

Job files:

- [ethan_backup_sync.sbatch](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/tmp/slurm_ethan_runs_backup_jobs/20260625T150232_sync/ethan_backup_sync.sbatch:1)
- stdout:
  `/scratch/09748/andresfierro231/projects_scratch/ethan_runs/tmp/slurm_ethan_runs_backup_jobs/20260625T150232_sync/slurm-3259614.out`
- stderr:
  `/scratch/09748/andresfierro231/projects_scratch/ethan_runs/tmp/slurm_ethan_runs_backup_jobs/20260625T150232_sync/slurm-3259614.err`

### Important history

The first submitted backup job failed immediately:

- failed job id: `3259225`
- cause: the wrapper incorrectly emitted `test -x rsync` instead of checking
  `rsync` on `PATH`

That bug was fixed in:

- [submit_ethan_runs_backup_sbatch.sh](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/tools/publish/submit_ethan_runs_backup_sbatch.sh:1)

### Observed live caveat

While `3259614` is running, the stderr log shows many lines of the form:

- `file has vanished: ...`

Interpretation:

- the backup is reading a live workspace whose staged run trees are changing
- this is usually not a fatal permissions issue
- it likely means a follow-up incremental sync should be expected after the
  current job finishes

### Backup size assumptions

From the backup inventory:

- included default scope: about `786,074,703,912` bytes (`732.1 GiB`)
- file count estimate: about `1,197,130`
- dominant trees:
  - `jadyn_runs`: about `497G`
  - `tmp_extract`: about `163G`
  - `staging`: about `72G`

### Tomorrow TODO for backup

- [ ] Check whether job `3259614` is still running, failed, or completed:
  ```bash
  ssh login3.ls6.tacc.utexas.edu 'squeue -j 3259614 -o "%.18i %.9P %.24j %.8T %.10M %.9l %.20S %.20R"'
  ssh login3.ls6.tacc.utexas.edu 'sacct -j 3259614 --format=JobID,JobName%24,Partition,State,ExitCode,Elapsed,Start,End,NodeList%20'
  ```
- [ ] Inspect the tail of stdout/stderr:
  ```bash
  tail -40 tmp/slurm_ethan_runs_backup_jobs/20260625T150232_sync/slurm-3259614.out
  tail -40 tmp/slurm_ethan_runs_backup_jobs/20260625T150232_sync/slurm-3259614.err
  ```
- [ ] If the job completed, inspect:
  - `/home1/.../ethan_runs_backup/manifests/latest/summary.txt`
  - `/home1/.../ethan_runs_backup/manifests/latest/new_files.txt`
  - `/home1/.../ethan_runs_backup/manifests/latest/changed_files.txt`
- [ ] If `file has vanished` noise is present but the run otherwise completed,
  plan a second incremental pass:
  ```bash
  bash tools/publish/submit_ethan_runs_backup_sbatch.sh --mode sync --time 02:00:00
  ```
- [ ] If a stricter audit is wanted before the second pass, dry-run with
  checksums:
  ```bash
  bash tools/publish/rsync_ethan_runs_backup.sh plan --checksum
  ```

## Thread 2: Corner pressure drops

### What exists now

Reusable script:

- [summarize_corner_pressure_drops.py](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/tools/analyze/summarize_corner_pressure_drops.py:1)

Test:

- [test_corner_pressure_drop_summary.py](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/tools/analyze/test_corner_pressure_drop_summary.py:1)

Math/provenance docs:

- [2026-06-25_ethan_corner_pressure_drop_math.md](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/operational_notes/06-26/25/2026-06-25_ethan_corner_pressure_drop_math.md:1)
- [2026-06-25_ethan_corner_pressure_drop_summary.json](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/imports/2026-06-25_ethan_corner_pressure_drop_summary.json:1)

Generated package:

- [README.md](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/work_products/2026-06-25_ethan_corner_pressure_drop_summary/README.md:1)
- [selected_case_packages.csv](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/work_products/2026-06-25_ethan_corner_pressure_drop_summary/selected_case_packages.csv:1)
- [corner_pressure_drop_window_summary.csv](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/work_products/2026-06-25_ethan_corner_pressure_drop_summary/corner_pressure_drop_window_summary.csv:1)
- [corner_pressure_drop_summary.json](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/work_products/2026-06-25_ethan_corner_pressure_drop_summary/corner_pressure_drop_summary.json:1)

### Core math

The summary uses preserved endpoint values from
`feature_minor_loss_timeseries.csv`:

- `start_p_rgh_pa`
- `end_p_rgh_pa`
- `delta_p_rgh_pa = end_p_rgh_pa - start_p_rgh_pa`

The restart-safe interpretation is:

- `p_before_rgh = start_p_rgh_pa`
- `p_after_rgh = end_p_rgh_pa`
- `delta_p_rgh = p_after_rgh - p_before_rgh`
- `pressure_drop_start_to_end_rgh = p_before_rgh - p_after_rgh = -delta_p_rgh`

The output CSV keeps both:

- `mean_delta_p_rgh_pa`
- `mean_pressure_drop_start_to_end_rgh_pa`

so the sign convention is explicit instead of hidden.

### Current data source and scope

Default search root used:

`tmp/2026-06-18_overnight_analysis_queue/case_analysis`

Current selected package counts:

- discovered package CSVs: `15`
- selected package roots: `13`
- emitted summary rows: `156`

Selected cases came from:

- `2` `*_window20` package roots
- `11` `*_window12` package roots

Important caveat:

- despite the package-root names, the currently selected corner-pressure CSVs
  contain only `4` or `5` retained times per case
- that means the `10`-step and `20`-step summaries collapse to the same
  retained rows as the `5`-step summary in the current output

### Example current values

For `val_salt_test_2_coarse_mesh_laminar`, requested window `5`:

- `corner_lower_left`:
  - `mean_start_p_rgh_pa = -6.1151494798`
  - `mean_end_p_rgh_pa = -5.5868133192`
  - `mean_delta_p_rgh_pa = 0.5283361606`
  - `mean_pressure_drop_start_to_end_rgh_pa = -0.5283361606`
- `corner_lower_right`:
  - `mean_delta_p_rgh_pa = 2.646708314`
- `corner_upper_right`:
  - `mean_delta_p_rgh_pa = 7.8426060166`
- `corner_upper_left`:
  - `mean_delta_p_rgh_pa = 2.4385526680`

### Validation already done

- `python3.11 -m py_compile tools/analyze/summarize_corner_pressure_drops.py tools/analyze/test_corner_pressure_drop_summary.py`
- `python3.11 tools/analyze/test_corner_pressure_drop_summary.py`
- `python3.11 tools/analyze/summarize_corner_pressure_drops.py`

### Tomorrow TODO for pressure-drop work

- [ ] Decide whether the table should stay all-case or be reduced to a smaller
  presentation/modeling subset.
- [ ] Decide whether the preferred sign to present is:
  - `mean_delta_p_rgh_pa = end - start`
  - or `mean_pressure_drop_start_to_end_rgh_pa = start - end`
- [ ] If the real intent is “pressure drop along flow” rather than “start-to-end
  patch order,” add a flow-aligned sign layer on top of the current endpoint
  convention.
- [ ] If the user truly needs `10-20` distinct retained times, refresh the
  underlying case-analysis roots because the current CSVs only expose `4-5`
  retained corner times.
- [ ] If the question shifts from endpoint comparison to a stricter feature-path
  loss, plan a separate extractor for a dedicated feature-path hydro integral
  instead of reusing endpoint `p_rgh` deltas.

## One-command restart context

If the first question tomorrow is “where are we?”:

1. Check the backup job:
   ```bash
   ssh login3.ls6.tacc.utexas.edu 'squeue -j 3259614 -o "%.18i %.9P %.24j %.8T %.10M %.9l %.20S %.20R"'
   ```
2. Read the checkpoint note:
   - [2026-06-25_progress_checkpoint.md](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/operational_notes/06-26/25/2026-06-25_progress_checkpoint.md:1)
3. For backup details:
   - [2026-06-25_ethan_runs_backup_plan.md](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/operational_notes/06-26/25/2026-06-25_ethan_runs_backup_plan.md:1)
4. For corner-pressure details:
   - [2026-06-25_ethan_corner_pressure_drop_math.md](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/operational_notes/06-26/25/2026-06-25_ethan_corner_pressure_drop_math.md:1)
   - [corner_pressure_drop_window_summary.csv](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/work_products/2026-06-25_ethan_corner_pressure_drop_summary/corner_pressure_drop_window_summary.csv:1)
