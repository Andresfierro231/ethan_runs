# Forward-v1 Next-Step Execution From Overnight

Date: 2026-07-15

Task: AGENT-394

## Result

Final forward-v1 remains **blocked**. The overnight work made useful progress:
AGENT-391 completed its mdot/temperature queue, and AGENT-392 completed all
eight thermal rescue stages with zero failed stages. These rows are evidence
for candidate selection, residual attribution, and setup contracts; they are
not a final forward-v1 score.

## What Is Admitted Now

- The completion/status facts for AGENT-391 and AGENT-392 are admitted as
  operational evidence.
- AGENT-392 external-boundary metadata may be used as setup-contract evidence.
- AGENT-391/392 cooler and HX rows may be consumed as candidate-screen inputs
  by the next gate package.

No final predictive HX, fitted internal Nu, realized wallHeatFlux, imposed
cooler duty, or diagnostic test-section negative-source row is admitted as a
predictive closure.

## What Is Pending

- AGENT-373 hydraulic dependent chain: jobs `3295989 -> 3295990 -> 3295991`.
- Corrected-Q continuation and harvest: `3293924` running, `3295438` pending at
  package generation time.
- PM5 matched pressure/upcomer extraction: `3295901` was cancelled and needs a
  cfd-pp/therm-reconstr relaunch decision.
- Sensor-map policy refresh: evidence exists from AGENT-391 but the policy
  table still needs to be written.

## Math, Assumptions, And Theory

- Train/validation/holdout discipline is unchanged: `salt_2=train`,
  `salt_3=validation`, and `salt_4=holdout`.
- Cooler/HX candidate screens are split-aware. A Salt2 scalar fit can only be
  scored on Salt3 and Salt4 without refitting; imposed or realized CFD cooler
  heat remains leakage/diagnostic evidence.
- Pressure-root diagnostics solve for mdot where the 1D pressure residual
  crosses zero. They explain hydraulic sensitivity but do not replace the
  pending H1/F6 hydraulic gate.
- External-boundary parity treats CFD wallHeatFlux as already including
  rcExternalTemperature radiation. Adding separate radiation would double-count
  heat loss; realized wallHeatFlux replay is diagnostic only.
- Test-section negative-source compatibility rows are mathematical residual
  probes, not physical boundary-condition proof.
- Internal Nu fitting remains closed. Upcomer diagnostic/effective Nu rows are
  validation-only until cfd-pp onset candidates and matched-plane extraction
  reopen the admission gate.

## Files

- `current_scheduler_state.csv`: read-only Slurm snapshot with interpretation.
- `overnight_output_intake.csv`: what landed and how each artifact can be used.
- `forward_v1_blocker_delta.csv`: blocker-by-blocker delta after overnight
  intake.
- `today_action_queue.csv`: collision-aware next work.
- `setup_only_hx_and_test_section_action_table.csv`: candidate/diagnostic lane
  table for cooler, HX, external BC, and test-section rows.
- `source_manifest.csv`: package inputs.
- `summary.json`: machine-readable package summary.

## Guardrails

This package did not mutate native CFD solver outputs, registry/admission
state, scheduler state, or external `../cfd-modeling-tools`.
