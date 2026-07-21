# Tomorrow Handoff: F4/Ri, Corrected Salt Gate, And Postprocessing Queue

Date written: `2026-07-07`  
Intended pickup date: `2026-07-08`  
Writer: codex  
Related task: `AGENT-191`

## Executive State

Today we completed the F4/Ri evidence-gate pass and hardened the Fluid F4
solver route. The scientific state is conservative:

- Mainline Salt 2/3/4 Jin is the only closure-fit admitted F4 evidence set.
- Salt 1 remains out of coefficient fitting.
- Corrected Salt Q rows remain out of closure/ROM fitting until a formal gate
  requalifies them and any `needs_special_gate_scrutiny=True` row receives
  coordinator review.
- The new bounded F4/Ri candidate is diagnostic-only. It is not a validated ROM
  correlation.
- A replacement corrected-Salt postprocess/gate job was submitted for overnight:
  `3280969` `saltq_gate_after`.

## Read First Tomorrow

Required startup files:

- `AGENTS.md`
- `.agent/BOARD.md`
- `.agent/FILE_OWNERSHIP.md`
- `.agent/ROLES.md`

Task handoff files:

- `.agent/status/2026-07-07_AGENT-191.md`
- `.agent/journal/2026-07-07/implementer-f4-ri-calibration-and-solver-gate.md`
- `work_products/2026-07-07_f4_ri_calibration_and_solver_gate/README.md`
- `work_products/2026-07-07_f4_ri_calibration_and_solver_gate/corrected_salt_gate_monitor_snapshot.md`
- `work_products/2026-07-07_f4_evidence_freeze_review/README.md`
- `work_products/2026-07-07_time_window_quasi_steady_contract/README.md`
- `operational_notes/07-26/07/2026-07-07_cfd_postprocessing_closure_rigor_deep_dive.md`

Source/provenance tables:

- `work_products/2026-07-01_claude_momentum_budget/momentum_budget.csv`
- `work_products/2026-07-04_friction_forms/friction_forms_comparison.csv`
- `work_products/2026-07-01_claude_segment_friction/segment_friction.csv`
- `work_products/2026-07-01_claude_allspan_convection/**`
- `work_products/2026-07-01_claude_thermal_downcomer/**`
- `work_products/2026-07-07_corrected_salt_live_monitor/live_salt_sanity_monitor.csv`
- `work_products/2026-07-07_water_provisional_and_corrected_salt_gate/**`

External Fluid files touched:

- `../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/friction_closures.py`
- `../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/solver.py`
- `../cfd-modeling-tools/tamu_first_order_model/Fluid/tests/test_friction_closures.py`

## What Was Done Today

### F4/Ri Read-Only Gate

Created:

- `tools/analyze/build_f4_ri_calibration_and_solver_gate.py`
- `tools/analyze/test_build_f4_ri_calibration_and_solver_gate.py`
- `work_products/2026-07-07_f4_ri_calibration_and_solver_gate/**`

Key outputs:

- `f4_ri_calibration_table.csv/json`: 18 admitted Salt 2/3/4 Jin rows.
- `admitted_evidence_freeze.csv/json`: includes held Salt 1 and corrected-Q
  rows.
- `ri_definition_audit.md`: documents median section Ri, streamwise projection,
  property basis, length-scale basis, and Delta-T basis.
- `f4_candidate_fit_report.md`: bounded residual F4/Ri candidate screen.
- `model_comparison_f1_f3_f4_f5.csv/json/md`: pressure-distribution and mdot
  comparison with the thermal-driver caveat.
- `corrected_salt_gate_monitor_snapshot.csv/json/md`: job IDs, partition,
  dependency, latest times, fatal/error counts, flags, and recommendations.

Important result:

- The bounded F4/Ri screen is not strong enough to promote as a final
  correlation. It has only three points per physical group and negative R2 in
  several groups. Keep it diagnostic-only until more admissible operating
  points exist.

### Admission Rules Preserved

Held out of closure fitting:

- Salt 1 nominal and corrected Salt Q rows.
- All corrected Salt Q rows until formal gate requalification.
- Every `needs_special_gate_scrutiny=True` row.
- False-steady or short/canceled rows.

Explicitly documented flags:

- `salt1_jin_hi10q_corrected`: ended after `254.259 s` past restart, `4.24%`
  of target extension.
- `salt1_jin_lo10q_corrected`: missing Salt 1 nominal mdot reference.
- `salt3_jin_hi5q_corrected`: canceled job `3275450`, only `21.476 s` past
  restart; fatal/error markers present.
- `salt3_jin_hi10q_corrected`: canceled job `3275450`, only `19.876 s` past
  restart; fatal/error markers present.

Interpretation:

- Quarantine Salt 3 high-Q corrected rows.
- Keep Salt 1 corrected rows out until Salt 1 qualification resolves nominal
  mdot reference and short-window/heat-balance issues.

### Fluid F4 Hardening

External Fluid was already dirty/untracked before this task. We did not revert
or overwrite unrelated state.

Narrow hardening applied:

- `F4_leg_class` now requires explicit `leg_class`; missing context raises.
- `solver.py` maps parent segments to F4 classes:
  - `heated_incline` -> `heater`
  - `right_vertical` -> `downcomer`
  - `left_lower_vertical`, `test_section`, `left_upper_vertical` -> `upcomer`
  - `cooled_incline_pre_hx`, `cooled_incline_hx_active`,
    `cooled_incline_post_hx` -> `cooler`
- Tests now cover required F4 context and invalid leg classes.

Validation:

- `python3.11 tools/analyze/test_build_f4_ri_calibration_and_solver_gate.py`:
  3 tests passed.
- `python3.11 -m py_compile ...`: passed.
- External Fluid `pytest tests/test_friction_closures.py`: 45 tests passed
  under Python 3.9.
- Python 3.9 solver-routing smoke passed.
- Python 3.11 Fluid import is not usable in this environment because that
  interpreter lacks `yaml`; Python 3.11 also lacks `pytest`.

## Current Scheduler State

Checked at the end of day with `squeue`.

Running corrected Salt parent jobs:

- `3275448` `corr_saltq_g1`: `RUNNING`, `NuclearEnergy`,
  elapsed about `3-09:35:56`, no dependency.
- `3275449` `corr_saltq_g2`: `RUNNING`, `NuclearEnergy`,
  elapsed about `3-09:26:08`, no dependency.
- `3275560` `corr_saltq_salt4_all`: `RUNNING`, `NuclearEnergy`,
  elapsed about `3-07:40:53`, no dependency.

Canceled/obsolete gate jobs:

- `3278453` `saltq_gate_after`: canceled before producing useful outputs.
- `3279646` `saltq_gate_0707`: `CANCELLED by 890970`, elapsed `00:00:00`,
  ended `2026-07-07T19:27:23`.

New overnight job submitted:

- `3280969` `saltq_gate_after`: `PENDING`, `NuclearEnergy`, walltime `1:30:00`,
  dependency
  `afterany:3275448(unfulfilled),afterany:3275449(unfulfilled),afterany:3275560(unfulfilled)`,
  reason `Dependency`.

Submit command used:

```bash
ssh login3 "cd /scratch/09748/andresfierro231/projects_scratch/ethan_runs && sbatch --dependency=afterany:3275448:3275449:3275560 tmp/2026-07-06_overnight_postprocess_jobs/run_corrected_salt_postprocess_afterany.sbatch"
```

Output:

```text
Submitted batch job 3280969
```

## Overnight Runs / Jobs

Submitted:

- Replacement corrected-Salt postprocess/gate job `3280969`.

Not submitted:

- No new CFD solver production runs were submitted.
- No Salt 3 high-Q replacement solver run was submitted; inspect failure logs
  first.
- No pressure-ledger postprocessing job was submitted yet; it needs a scoped
  task/tool pass or an existing validated script invocation.
- No time-window UQ postprocessing job was submitted yet; the tool exists in
  `tools/analyze/build_time_window_quasi_steady_observations.py`, but should be
  claimed and run with a dated task package.

## Tomorrow Morning Checks

Run:

```bash
squeue -j 3275448,3275449,3275560,3280969 -o "%i|%j|%T|%P|%M|%l|%E|%r"
sacct -j 3280969 --format=JobID,JobName%30,State,ExitCode,Elapsed,Start,End -P
tail -80 tmp/2026-07-06_overnight_postprocess_jobs/slurm-saltq_gate_after-3280969.out
tail -80 tmp/2026-07-06_overnight_postprocess_jobs/slurm-saltq_gate_after-3280969.err
```

Expected output directory if the job runs:

- `work_products/2026-07-06_overnight_postprocess_jobs/corrected_salt_after_3275448_3275449_3275560/`

Admission rule after it finishes:

- Admit only rows with formal `operating_point_verdict=requalified`.
- Even if requalified, any row with `needs_special_gate_scrutiny=True` remains
  non-admissible until coordinator review.

## TODOs For Tomorrow

Priority 0:

- Inspect `3280969` result. If it fails, read the slurm stdout/stderr and fix
  the wrapper or status script before any corrected-Q admission decision.
- Keep corrected Salt Q out of closure/ROM fitting until the gate lands.

Priority 1:

- Build the pressure-ledger postprocessing package for Salt 2/3/4 Jin:
  `p`, `p_rgh`, dynamic head, total-pressure proxy, density-gradient buoyancy,
  inertia, distributed mechanical loss, minor/local-loss proxies, residual, and
  recirculation/backflow flags.
- Build a Salt 1 qualification package:
  nominal mdot reference, heat closure, retained-window length, corrected-Q
  behavior, and final verdict: exclude, sensitivity-only, or extend nominal.
- Run the time-window quasi-steady UQ curation:
  drift, oscillation envelope, block means, effective sample size, and
  independence groups.

Priority 2:

- Improve wall-bulk Delta-T coverage for F4/Ri, especially cooler rows where the
  thermal join is currently incomplete in the AGENT-191 package.
- Revisit the F4/Ri model only after pressure ledger and time-window UQ are
  complete. Do not promote today’s bounded screen.
- Audit Water July 6 provisional language once more before any reporting: keep
  the timeout/frozen-final-window caveat.

Priority 3:

- After Salt 3 high-Q failure-log review, decide whether to rerun only those
  two corrected cases or keep them quarantined.
- Plan mesh/GCI next step separately; do not mix mesh-uncertainty work into the
  closure-fit task.

## Cautions

- Do not use corrected Salt Q rows in closure fitting by default.
- Do not use Salt 1 in coefficient fitting until qualified.
- Do not treat `F4_Ri_candidate` as final correlation evidence.
- Do not interpret mdot improvement/failure as a pure friction result while the
  1D thermal driver remains mismatched.
- Do not edit native solver outputs.
- External Fluid still has broader dirty/untracked state outside the AGENT-191
  edits; inspect before changing anything there.
