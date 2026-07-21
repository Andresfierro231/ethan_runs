# Water Provisional And Corrected Salt Gate

Date: `2026-07-07`  
Task: `AGENT-181`

## Bottom Line

The July 6 Water outputs may be used for provisional reporting only. They come from Water job `3265970`, which ended as `TIMEOUT`, and the postprocess rerun `3278452` reclassified the four Water cases as `quasi_stationary` hydraulically and `stationary` thermally from monitor data. This is useful status evidence, not closure-fit evidence.

Corrected Salt is still not ready for fitting. The staged Q-field preflight now passes for all 14 corrected cases, but the solver parent jobs `3275448`, `3275449`, and `3275560` are still running. The July 6 gate job `3278453` was canceled, so replacement gate job `3279646` was submitted with `afterany:3275448:3275449:3275560`.

## Observed Evidence

- Water `run_status_inventory.csv` from `work_products/2026-07-06_overnight_postprocess_jobs/water_postprocess_after_3265970/run_status/` reports Water 1-4 as `quasi_stationary` overall, `quasi_stationary` hydraulic, and `stationary` thermal.
- The same inventory lists job `3265970` as `TIMEOUT`, so the final Water window is a frozen timeout endpoint rather than a clean solver-completed endpoint.
- The July 6 consolidated closure table has no Water rows; it remains a Salt nominal/false-steady status package.
- `tools/analyze/check_corrected_salt_preflight.py` audits `case_config.yaml`, root `0/T`, and latest `processors64/<time>/T` values. The July 7 run found `14/14` corrected Salt cases with `overall_ok=True`, `processor_blocks=64`, and `processor_frame_error_count=0`.
- Slurm check after replacement submission showed `3279646` pending on dependency while `3275448`, `3275449`, and `3275560` continued running.
- Live corrected-Salt sanity monitor output now records 14 cases, 4 special-scrutiny flags, and 2 fatal/error-marker cases:
  `work_products/2026-07-07_corrected_salt_live_monitor/live_salt_sanity_monitor.csv`.
- `salt1_jin_hi10q_corrected` ended after `254.259 s` past restart, only `4.24%` of the intended target extension, with `convergence_monitor_triggered=True`; it is `needs_special_gate_scrutiny=True`.
- `salt3_jin_hi5q_corrected` and `salt3_jin_hi10q_corrected` are tied to canceled Slurm job `3275450` and advanced only about `21.5 s` and `19.9 s` past restart; both are `recommendation=investigate`.

## Interpretation

Water can support provisional narrative statements about current monitor behavior and approximate final-window flow/thermal status. Do not use it yet to fit friction, HTC, Re-response, or ROM closure correlations unless a later package adds explicit Water extraction rows and records the timeout caveat.

Corrected Salt preflight evidence removes the known BC/restart-field mismatch as of the latest written processor fields, but it does not prove physical re-equilibration. The admission test remains the operating-point gate: mdot must move from the nominal baseline by the expected Q response and then re-plateau.

The live sanity monitor is a guardrail, not an admission gate. Rows carrying `needs_special_gate_scrutiny=True` are not closure-fit admissible without coordinator review even if later postprocessing appears to requalify them.

## Water Language Audit

The Water provisional-output language was audited in the report README, report summary, work-product README, journal, operational note, and import manifest. The audit found the required timeout/frozen-window caveat and closure/ROM-fit block present in all six inspected artifacts:

- `work_products/2026-07-07_water_provisional_and_corrected_salt_gate/water_provisional_language_audit.csv`
- `work_products/2026-07-07_water_provisional_and_corrected_salt_gate/water_provisional_language_audit.json`

## ROM Correlation Boundary

False-steady perturbations remain excluded. Current `f(Re)` screens are still labeled `screen_only_needs_more_true_steady_cfd`; the best prior Salt-only model-form score remains the `global_mean_mult` prior trial at mean absolute mdot error `3.6615%` over 3 cases. That number is useful for ROM direction, not a final cross-fluid correlation.

## Key Sources

- `work_products/2026-07-07_water_provisional_and_corrected_salt_gate/water_provisional_run_status.csv`
- `work_products/2026-07-07_water_provisional_and_corrected_salt_gate/corrected_salt_preflight_audit.csv`
- `work_products/2026-07-07_water_provisional_and_corrected_salt_gate/salt_gate_submission_status.csv`
- `work_products/2026-07-07_corrected_salt_live_monitor/live_salt_sanity_monitor.csv`
- `work_products/2026-07-07_corrected_salt_live_monitor/live_salt_sanity_monitor.json`
- `work_products/2026-07-07_water_provisional_and_corrected_salt_gate/water_provisional_language_audit.csv`
- `tmp/2026-07-07_corrected_salt_gate/run_corrected_salt_gate_after_live_jobs.sbatch`
- `work_products/2026-07-06_overnight_postprocess_jobs/water_postprocess_after_3265970/run_status/run_status_inventory.csv`
- `work_products/2026-07-06_overnight_postprocess_jobs/water_postprocess_after_3265970/consolidated_closure_table/consolidated_closure_table.csv`
