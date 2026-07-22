# F4 Evidence Freeze Review

Date: `2026-07-07`  
Task: `AGENT-189`  
Role: Coordinator / Reviewer / Writer

## Purpose

Review the current F4 state against the requested attack plan and set the
coordination boundary for the next work. This is a review and handoff package,
not a solver-code implementation.

## Immediate Decision

Freeze the admitted evidence set as:

- `viscosity_screening_salt_test_2_jin_coarse_mesh`
- `viscosity_screening_salt_test_3_jin_coarse_mesh`
- `viscosity_screening_salt_test_4_jin_coarse_mesh`

These are the mainline Salt 2/3/4 Jin rows already used by `AGENT-187`.

Hold out of closure fitting:

- Salt 1 nominal and Salt 1 corrected-Q rows until a Salt 1 qualification
  package explicitly clears them.
- All corrected Salt Q rows until the formal operating-point gate emits
  `operating_point_verdict=requalified`.
- Any row with `needs_special_gate_scrutiny=True` unless a coordinator reviews
  and clears the row. Current flagged rows include
  `salt1_jin_lo10q_corrected`, `salt1_jin_hi10q_corrected`,
  `salt3_jin_hi5q_corrected`, and `salt3_jin_hi10q_corrected`.

## Review Finding

`AGENT-187` completed a useful 18-row mainline Salt 2/3/4 data-driven
calibration and documented it clearly. However, it also edited external
`friction_closures.py` before the full requested sequence was complete. The
existing `F4_leg_class` should therefore be treated as an experimental
data-driven pressure-resistance model-form comparison, not as the final
Ri-corrected F4 law.

The requested sequence should resume with a read-only analysis task before any
more solver edits:

1. freeze admitted evidence;
2. build the joined F4/Ri calibration table;
3. audit the Ri definition;
4. fit a minimal bounded F4 candidate to residual `f_corrected/f_F3h`;
5. compare F1, F3, F4 candidate, and F5 on pressure distribution and mdot;
6. only then open a separate Implementer task for `friction_closures.py` /
   `solver.py` edits.

## What AGENT-187 Already Did

Inputs:

- `work_products/2026-07-01_claude_momentum_budget/momentum_budget.json`
- `work_products/2026-07-01_claude_segment_friction/segment_friction.csv`

Outputs:

- `work_products/2026-07-07_f4_buoyancy_friction/f4_calibration_dataset.csv`
- `work_products/2026-07-07_f4_buoyancy_friction/f4_fit_summary.json`
- `work_products/2026-07-07_f4_buoyancy_friction/f4_fit_summary.csv`
- `work_products/2026-07-07_f4_buoyancy_friction/run_f4_calibration.py`
- external `../cfd-modeling-tools/.../friction_closures.py` now contains
  `F4_leg_class`

Fit form:

```text
f_corrected / f_lam = a + b / Re
```

This is explicitly not Ri-corrected. It has only three points each for heater,
cooler, and downcomer. The upcomer aggregate fit is physically weak
(`R2=0.015`) because the three upcomer sub-spans behave differently.

## Required Next Read-Only Task

Open a new Implementer task for a read-only table builder. Suggested ownership:

- `work_products/2026-07-08_f4_ri_calibration_table/**`
- optional `tools/analyze/build_f4_ri_calibration_table.py`
- status and journal files for that task

Do not grant `../cfd-modeling-tools/**` edit paths for that task.

### Required Inputs

- De-buoyed momentum budget:
  `work_products/2026-07-01_claude_momentum_budget/momentum_budget.json`
- F1/F3 comparison:
  `work_products/2026-07-04_friction_forms/friction_forms_comparison.csv`
- Segment geometry:
  `work_products/2026-07-01_claude_segment_friction/segment_friction.csv`
- Current F4 first-pass table:
  `work_products/2026-07-07_f4_buoyancy_friction/f4_calibration_dataset.csv`
- Ri/Ra/Re source artifacts, once identified, with exact paths recorded.
- Corrected-Salt admission monitor:
  `work_products/2026-07-07_corrected_salt_live_monitor/live_salt_sanity_monitor.csv`

### Minimum Output Columns

- `case_id`, `source_id`, `run_class`, `span`, `leg_class`
- `admission_status`, `closure_fit_admissible`,
  `needs_special_gate_scrutiny`, `coordinator_review_status`
- `Re`, `Ra`, `Ri_median`, `Ri_streamwise`, `Pr`
- `ri_definition`, `deltaT_basis`, `property_basis`, `length_scale_basis`
- `theta_from_gravity_deg`, `streamwise_projection_basis`
- `D_m`, `L_m`, `x_plus`
- `f_lam`, `f_corrected`, `f_corrected_over_flam`
- `f_F1`, `f_F3h`, `f3h_ratio`, `f_corrected_over_f3h`
- `F5_per_leg_multiplier` if available
- `fit_group`, `fit_weight`, `fit_use_status`, `fit_exclusion_reason`

### Ri Definition Acceptance Criteria

- Use median section Ri, not mean Ri, unless the artifact is explicitly labeled
  as a diagnostic-only mean.
- For inclined heater/cooler spans, record the streamwise gravity projection and
  angle basis. A projection convention such as `Ri_streamwise = Ri_median *
  cos(theta_from_gravity)` is acceptable only if the angle source and sign
  convention are documented.
- Record `Delta T` basis: wall-bulk, wall-centerline, enthalpy-bulk, or derived
  from `Q_wall/(HTC*A_wall)`.
- Record property basis: bulk temperature, film temperature, local section
  temperature, or campaign constant.
- Record length scale basis: hydraulic diameter unless a documented alternate
  is used.
- Do not mix field-output Ri and reconstructed wall-bulk Ri in one fit without a
  conversion/audit column.

## Minimal F4 Candidate Acceptance Criteria

The next fit may be accepted for review only if it:

- fits the residual `f_corrected/f_F3h`, not raw apparent friction;
- groups by physical leg class and does not collapse all upcomer sub-spans into
  a high-confidence single law;
- uses bounded coefficients or bounded predictions so extrapolation cannot
  create unphysical resistance;
- reports leave-one-case-out behavior or an equivalent small-sample warning;
- carries row-level provenance and admission flags through every output;
- labels the result as a candidate, not a validated correlation.

## Solver-Edit Gate

Do not open another `friction_closures.py` / `solver.py` edit until the read-only
Ri table and model comparison are complete.

The later solver task must prove:

- no buoyancy double-counting with `buoyancy_pressure()`;
- default solver behavior remains unchanged;
- F1, F3, current `F4_leg_class`, Ri-F4 candidate, and F5 per-leg multipliers can
  be compared from one common scenario runner;
- mdot interpretation carries the thermal-driver caveat from the July 2
  driver-side thermal comparison;
- any corrected-Salt Q rows are joined against `needs_special_gate_scrutiny`
  before fit admission.

## Blockers

- Formal corrected-Salt gate output is not yet available.
- Salt 1 is not yet qualified for normal coefficient fitting.
- Ri/Ra/Delta-T source artifacts have not been joined to the F4 table.
- Existing external Fluid edits are outside this task's write scope.

## Exact Next Action

Open the read-only `F4 Ri calibration table` Implementer task, with the
acceptance criteria above. Treat existing `F4_leg_class` as provisional
model-form evidence until that task completes.
