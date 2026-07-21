---
provenance:
  task: AGENT-342
  generated_by: codex
tags: [journal, cfd-pp, corrected-q, harvest, slurm]
related:
  - .agent/status/2026-07-14_AGENT-342.md
  - imports/2026-07-14_corrected_q_postprocess_harvest_submission.json
---
# Corrected-Q Postprocess Harvest Submission

## Why

The coordinator asked why Salt1 remains diagnostic after a continuation and asked to submit harvest/postprocessing for Salt2/Salt4 perturbed corrected-Q CFD runs that may be steady.

## Decision

Two Slurm jobs were submitted from `login3.ls6.tacc.utexas.edu`:

- Immediate stopped-row harvest for Salt2/Salt4 +/-5Q rows: `3295437`.
- Dependency-gated selected-row harvest for Salt2/Salt4 +/-10Q rows after live solver job `3293924`: `3295438`.

This separates live solver output from terminal harvest. The selected +/-10Q rows are still being written by job `3293924`, so the harvest is submitted but dependency-held until that job exits.

## Salt1 Interpretation

Salt1 is not diagnostic because a continuation was never submitted. It is diagnostic because the documented corrected-Q terminal/stop evidence is not yet a Salt1-admitted steady operating point. The known issue is the weak global `convergenceMonitor` / early-stop path plus unresolved Salt1 admission policy. A converged terminal window may override old `too_short` context, but Salt1 needs the Salt1-specific policy/gate and operating-point UQ before fit use.

## Submitted Artifacts

- `work_products/2026-07/2026-07-14/2026-07-14_corrected_q_postprocess_harvest_submission/run_salt2_salt4_stopped_corrected_q_harvest.sbatch`
- `work_products/2026-07/2026-07-14/2026-07-14_corrected_q_postprocess_harvest_submission/run_salt2_salt4_selected_corrected_q_harvest_after_3293924.sbatch`
- `work_products/2026-07/2026-07-14/2026-07-14_corrected_q_postprocess_harvest_submission/README.md`

## Next Monitoring Commands

```bash
squeue -j 3295437,3295438,3293924
sacct -j 3295437,3295438,3293924 --format JobID,JobName%30,State,ExitCode,Elapsed,Start,End -P
tail -80 work_products/2026-07/2026-07-14/2026-07-14_corrected_q_postprocess_harvest_submission/slurm-saltq_s24_done_harv-3295437.out
tail -80 work_products/2026-07/2026-07-14/2026-07-14_corrected_q_postprocess_harvest_submission/slurm-saltq_s24_done_harv-3295437.err
```

