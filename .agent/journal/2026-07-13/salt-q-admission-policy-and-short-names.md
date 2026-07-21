# Salt-Q Admission Policy And Short Names

Date: `2026-07-13`
Task: `AGENT-269`
Role: Coordinator / Implementer / Tester / Writer

## Correction

The user corrected the admission policy:

- if a Salt-Q perturbation row is converged, it is closure-fit admissible;
- the old `too_short` post-restart-advance gate must not exclude an otherwise
  converged row;
- the current run names should not carry the historical `corrected` suffix in
  presentation or launch logs.

Implemented that correction in
`tools/analyze/build_registry_corrected_q_status_table.py`. The builder now
marks stationary/converged terminal-window rows as `closure_fit_admissible=yes`
and emits short display keys while preserving source keys.

Additional active-code cleanup:

- `tools/analyze/build_f4_ri_calibration_and_solver_gate.py` no longer treats
  Salt-Q rows as categorically excluded; it admits rows with explicit
  converged/admissible evidence and no special-scrutiny flag.
- `tools/analyze/build_upcomer_onset_regime_table.py` summary status now says
  converged Salt-Q rows are closure-fit admissible.
- `tools/analyze/build_presentation_readiness_and_rom_agenda.py` and
  `tools/analyze/build_tomorrow_presentation_package.py` no longer present
  converged Salt-Q perturbations as non-evidence.

## Short Names

The selected repack names are:

- `salt2_lo10q` from source key `salt2_jin_lo10q_corrected`.
- `salt2_hi10q` from source key `salt2_jin_hi10q_corrected`.
- `salt4_lo10q` from source key `salt4_jin_lo10q_corrected`.

The old source keys remain in manifests, registry rows, and physical paths so
the patcher can still locate the correct source row and provenance remains
auditable.

## Launcher Change

Updated
`jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations/scripts/run_selected_corrected_salt_q_continuation.sbatch`
to target:

- `salt2_jin_lo10q_corrected`
- `salt2_jin_hi10q_corrected`
- `salt4_jin_lo10q_corrected`

The script now logs display names `salt2_lo10q`, `salt2_hi10q`, and
`salt4_lo10q`. No submission or attach launch was run.

## Validation

- `python3.11 -m unittest tools.analyze.test_registry_corrected_q_status_table`
  passed.
- `bash -n jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations/scripts/run_selected_corrected_salt_q_continuation.sbatch`
  passed.
- `python3.11 tools/analyze/build_registry_corrected_q_status_table.py --strict-registry --output-dir work_products/2026-07/2026-07-13/2026-07-13_salt_q_policy_corrected_status_smoke`
  passed and emitted `closure_fit_admissible=yes` for `salt2_lo10q`,
  `salt2_hi10q`, and `salt4_lo10q`.
- `python3.11 -m py_compile` passed for the patched F4, upcomer, presentation,
  and tomorrow-package builders.
- Active Python stale-string scan found no remaining categorical corrected-Q
  exclusion messages.
- `pytest` is not installed for `python3.11`; direct invocation of
  `test_upcomer_onset_regime_table` is blocked by missing pre-existing input
  `work_products/2026-07-07_upcomer_correlation_v2/upcomer_correlation_fit.csv`.

## Quarantined Cleanup

Identified old invalid Salt perturbation roots, received path-specific
destructive approval, and deleted:

June 19 wave:

- `jadyn_runs/modern_runs/2026-06-19_ethan_blocker_and_1d_followon_wave/runs/salt4_jin_hiq_hiins` (`54G`)
- `jadyn_runs/modern_runs/2026-06-19_ethan_blocker_and_1d_followon_wave/runs/salt4_jin_loq_loins` (`32G`)
- `jadyn_runs/modern_runs/2026-06-19_ethan_blocker_and_1d_followon_wave/runs/salt3_jin_hiq_hiins` (`48G`)
- `jadyn_runs/modern_runs/2026-06-19_ethan_blocker_and_1d_followon_wave/runs/salt3_jin_loq_loins` (`37G`)
- `jadyn_runs/modern_runs/2026-06-19_ethan_blocker_and_1d_followon_wave/runs/salt2_jin_loq_loins` (`40G`)
- `jadyn_runs/modern_runs/2026-06-19_ethan_blocker_and_1d_followon_wave/runs/salt2_jin_hiq_hiins` (`51G`)
- `jadyn_runs/modern_runs/2026-06-19_ethan_blocker_and_1d_followon_wave/runs/salt2_jin_hiq_balq` (`3.6G`)

June 25 wave:

- `jadyn_runs/modern_runs/2026-06-25_ethan_normal_relaunch_and_recirculation_boundary_wave/runs/salt1_jin_loq_balq` (`28G`)
- `jadyn_runs/modern_runs/2026-06-25_ethan_normal_relaunch_and_recirculation_boundary_wave/runs/salt2_jin_lo5q_balq` (`26G`)
- `jadyn_runs/modern_runs/2026-06-25_ethan_normal_relaunch_and_recirculation_boundary_wave/runs/salt4_jin_hi5q_balq` (`30G`)
- `jadyn_runs/modern_runs/2026-06-25_ethan_normal_relaunch_and_recirculation_boundary_wave/runs/salt3_jin_hi5q_balq` (`25G`)
- `jadyn_runs/modern_runs/2026-06-25_ethan_normal_relaunch_and_recirculation_boundary_wave/runs/salt3_jin_lo5q_balq` (`25G`)
- `jadyn_runs/modern_runs/2026-06-25_ethan_normal_relaunch_and_recirculation_boundary_wave/runs/salt4_jin_lo5q_balq` (`30G`)
- `jadyn_runs/modern_runs/2026-06-25_ethan_normal_relaunch_and_recirculation_boundary_wave/runs/salt2_jin_hi5q_balq` (`26G`)
- `jadyn_runs/modern_runs/2026-06-25_ethan_normal_relaunch_and_recirculation_boundary_wave/runs/salt1_jin_hiq_balq` (`28G`)

Verification:

- `find jadyn_runs/modern_runs/2026-06-19_ethan_blocker_and_1d_followon_wave/runs -maxdepth 1 -type d | rg 'salt[234]_jin_.*q|salt2_jin_hiq_balq'` returned no matches.
- `find jadyn_runs/modern_runs/2026-06-25_ethan_normal_relaunch_and_recirculation_boundary_wave/runs -maxdepth 1 -type d | rg 'salt[1234]_jin_.*q_.*balq|salt1_jin_hiq_balq'` returned no matches.
- The July 4 repaired roots for `salt2_jin_lo10q_corrected`,
  `salt2_jin_hi10q_corrected`, `salt4_jin_lo10q_corrected`,
  `salt4_jin_hi10q_corrected`, and `salt1_jin_hi10q_corrected` remain present.
