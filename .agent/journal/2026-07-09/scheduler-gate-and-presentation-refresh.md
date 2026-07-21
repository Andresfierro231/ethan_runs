# Scheduler Gate And Presentation Refresh

Date: `2026-07-09`
Task: `AGENT-225`
Role: Coordinator / Writer

## Objective

The user asked to check scheduler/gate state and identify what can be done to
improve the July 8 presentation package.

## Files Inspected

- `.agent/BOARD.md`
- `work_products/2026-07/2026-07-08/2026-07-08_tomorrow_presentation_package/README.md`
- `work_products/2026-07/2026-07-08/2026-07-08_tomorrow_presentation_package/slide_outline_with_speaker_notes.md`
- `work_products/2026-07/2026-07-08/2026-07-08_tomorrow_presentation_package/missing_and_nice_to_have_figures.md`
- `work_products/2026-07/2026-07-08/2026-07-08_tomorrow_presentation_package/figure_manifest.csv`
- `work_products/2026-07/2026-07-08/2026-07-08_tomorrow_presentation_package/source_inventory.csv`
- `tools/analyze/build_tomorrow_presentation_package.py`
- `tools/analyze/test_tomorrow_presentation_package.py`
- `jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations/submitted_jobs.csv`
- corrected-Salt preflight audit and solver log paths under the July 4 campaign
- `tmp/2026-07-06_overnight_postprocess_jobs/run_corrected_salt_postprocess_afterany.sbatch`

## Commands Run

- `date '+%Y-%m-%d %H:%M:%S %Z'`
- `squeue -j 3275448,3275449,3275560,3280969,3282992,3285548 -o '%i|%j|%T|%P|%M|%l|%D|%R'`
- `sacct -j 3275448,3275449,3275560,3280969,3282992 --format=JobIDRaw,JobID,JobName%34,State,ExitCode,Submit,Start,End,Elapsed,Timelimit,NNodes,AllocCPUS -P`
- `find ... -name 'preflight_patch_audit_*.csv'`
- `find ... -name 'log.foamRun_corrected_q'`
- `rg -n "FOAM FATAL|Fatal error|FOAM exiting|Segmentation|floating point" .../log.foamRun_corrected_q`
- `tail -20` sampled corrected-Salt logs

## Observed Facts

- Corrected Salt parent jobs were still running at `2026-07-09 07:41:25 CDT`:
  `3275448`, `3275449`, and `3275560`.
- Gate `3280969` was pending by dependency and had not emitted logs.
- Salt1 nominal continuation `3282992` was running.
- `14` corrected-Salt solver logs exist.
- `18` corrected-Salt preflight audit CSV files exist, including superseded
  Salt4 preflight audits from canceled/replaced jobs.
- A sampled preflight audit showed `root_patch_ok=True` and
  `processor_patch_ok=True`.
- A targeted fatal-marker scan found no matches.

## Interpretation

The scheduler/gate state can improve the presentation only as live status. It
does not add closure evidence yet. The best July 9 improvement is to make Slide
11 precise and current, and to sharpen the deck's claim boundaries.

## Files Changed

- `.agent/BOARD.md`
- `.agent/status/2026-07-09_AGENT-225.md`
- `.agent/journal/2026-07-09/scheduler-gate-and-presentation-refresh.md`
- `work_products/2026-07/2026-07-08/2026-07-08_tomorrow_presentation_package/README.md`
- `work_products/2026-07/2026-07-08/2026-07-08_tomorrow_presentation_package/july9_live_gate_status.md`
- `work_products/2026-07/2026-07-08/2026-07-08_tomorrow_presentation_package/july9_deck_upgrade_brief.md`
- `work_products/2026-07/2026-07-08/2026-07-08_tomorrow_presentation_package/tables/july9_scheduler_snapshot.csv`

## Next Steps

1. Recheck `3280969` after corrected-Salt parents leave the queue.
2. If the gate runs, inspect logs and outputs before adding corrected-Q claims.
3. Use the July 9 addenda for today's deck polish; leave the generated figures
   unchanged until there is new admitted evidence.

## Validation

Documentation-only. No numerical tests or model builders were run.
