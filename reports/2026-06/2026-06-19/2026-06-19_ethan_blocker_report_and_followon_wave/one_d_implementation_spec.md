# Salt-First 1D Implementation Spec

Generated: `2026-06-19`

## Objective

Build a lightweight defended v1 model that is:

- Salt only;
- steady and buoyancy-driven;
- explicit about which closures are fitted, which are table-driven, and which
  remain lumped residuals;
- compatible with either the current 1D codebase or a small new solver.

This is a hybrid model, not a full feature-resolved geometry closure. The
first defended version resolves only the closure-supported parts of the loop
and carries the rest as calibrated remainder buckets.

## V1 boundary

Admit now:

- straight hydraulic closure on `lower_leg` and `test_section_span`
- primary thermal state surface `UA'(x)` on:
  - `left_lower_leg`
  - `test_section_span`
  - `left_upper_leg`
  - `upcomer`
- secondary thermal surface `HTC(x)` on the same safe subset
- direct Salt Nu only on `left_lower_leg`
- visible case inputs:
  - heater `Q`
  - fixed cooler `Q`
  - ambient temperature
  - insulation choice / thickness
  - explicit salt material branch

Exclude from defended v1:

- feature-resolved `K_eff`
- Water-family fits
- direct fitted Nu on `right_leg`
- direct fitted Nu on derived `upcomer`
- live cooler-side `h` control

## Recommended control-volume layout

Use seven loop elements at minimum:

1. `lower_leg_heater`
   - imposed heater `Q`
   - straight friction closure admitted
2. `test_section_span`
   - straight friction closure admitted
   - primary thermal surface admitted
3. `left_lower_leg`
   - primary thermal surface admitted
   - optional direct Nu closure admitted
4. `left_upper_leg`
   - primary thermal surface admitted
5. `upcomer`
   - primary thermal surface admitted
6. `cooler_sink_bucket`
   - fixed negative `Q`
   - no direct cooler `h` fit
7. `unresolved_return_and_feature_bucket`
   - hydraulic residual for corners, reducers, right-leg effects, and blocked
     feature losses
   - thermal residual for unsupported wall-loss remainder

If the existing 1D code already uses a finer mesh, preserve that mesh but map
each cell onto one of these closure families.

## Governing structure

### Loop hydraulic balance

Solve one loop mass-flow state `mdot_loop` from:

`Delta p_buoyancy(T, rho) = Sum Delta p_straight_i(mdot, rho, mu) + Delta p_residual`

where:

- `Delta p_buoyancy` comes from the segment-wise density field and elevation
  map;
- defended straight losses use the admitted Salt friction fit;
- `Delta p_residual` is a calibrated positive remainder term until feature-path
  closure exists.

### Thermal march

March bulk temperature around the loop with segment energy balances:

`mdot * cp * (T_out - T_in) = Q_heater - Q_cooler - Q_ambient`

For supported wall-loss segments:

- primary mode: use `UA'(x)` or segment-averaged `UA'`
- optional direct left-lower-leg mode: use fitted `Nu(Re)` to recover
  `HTC = Nu * k / D_h`, then `UA' = HTC * P_w`

For unsupported remainder:

- use a lumped thermal residual bucket calibrated to the preserved CFD heat
  partition, not an invented branchwise coefficient.

## Material-property contract

Do not use a generic undifferentiated salt branch.

The v1 model should accept an explicit material branch input such as:

- `salt_jin`
- `salt_kirst`
- `salt_val` or direct case-config-derived validation salt branch

Minimum rule:

- evaluate `rho(T)`, `mu(T)`, `cp(T)`, and `k(T)` from the readable CFD-side
  material branch for the case family being reproduced
- do not silently fold Jin, Kirst, and validation salt into one hidden default

This follows the June 2 discrepancy report and avoids replaying the earlier 1D
property mismatch.

## State contract

See `one_d_state_vector.csv`.

Recommended interpretation:

- solved states:
  - `mdot_loop`
  - `T_bulk_node[j]`
- derived segment states:
  - `rho_seg[j]`
  - `mu_seg[j]`
  - `cp_seg[j]`
  - `k_seg[j]`
  - `Re_seg[j]`
  - `Pr_seg[j]`
  - `fD_seg[j]`
  - `UAprime_seg[j]`
- calibrated but not defended geometry closures:
  - `Deltap_residual`
  - `UA_lumped_residual`

## Closure contract

See `one_d_closure_map.csv`.

The core defended hydraulic and thermal closures are:

- straight friction:
  - model: `class_aware_re_power_law`
  - form: `log(f_D) = 5.2316378122 - 0.9477837868 log(Re) + 2.9210668439 I[test_section_span]`
  - defended use range: approximately `80 <= Re <= 174`
- left-lower-leg direct Nu:
  - model: `branch_aware_re_power_law`
  - form: `log(Nu) = -3.0042709988 + 0.9607621733 log(Re)`
  - defended use range: approximately `76 <= Re <= 166`
- branch thermal state surface:
  - primary: `UA'(x)`
  - secondary: `HTC(x)`
  - safe subset only: `left_lower_leg`, `test_section_span`,
    `left_upper_leg`, `upcomer`

## Calibration tables

See `one_d_calibration_table_spec.csv`.

The minimum durable tables are:

1. geometry segment table
2. case operating table
3. hydraulic training rows
4. thermal training rows
5. `UA'` profile library on the safe branch subset
6. per-case hydraulic residual calibration table
7. per-case thermal residual calibration table
8. validation target table

## Build order

1. Build geometry and operating-point tables.
2. Wire explicit salt material branches into the 1D model.
3. Implement the straight friction fit exactly as published.
4. Implement primary `UA'` thermal tables on the safe subset.
5. Add the optional direct left-lower-leg `Nu(Re)` mode as a cross-check, not
   as the only thermal path.
6. Add one hydraulic residual bucket and one thermal residual bucket.
7. Calibrate first on:
   - `Salt 2 Val`
   - `Salt 2 Jin`
   - `Salt 2 Kirst`
   - `Salt 3 Jin`
   - `Salt 3 Kirst`
   - `Salt 4 Jin`
   - `Salt 4 Kirst`
8. Use the new Salt 2 / Salt 4 bracket jobs as out-of-sample checks once they
   finish.

## What new CFD is still useful for the 1D model

Useful now:

- longer retained-time windows on the existing continuations
- the submitted Salt 2 / Salt 4 heater-plus-insulation bracket
- the deferred Salt 3 Jin midpoint bracket after the first bracket wave clears

Not useful by itself:

- more feature-focused runtime without a retained-time path extractor
- literal cooler-`h` DOE from the readable artifacts
- new Water scenario expansion before Water closure hardening

## Checkpoints

- `M1`: geometry and operating tables exist in machine-readable form
- `M2`: explicit Jin / Kirst / validation salt property branches are wired
- `M3`: the 1D solver reproduces the admitted straight friction fit exactly on
  the published training rows
- `M4`: the solver reproduces Salt 2 validation `mdot` and bulk-temperature
  ordering with residual buckets enabled
- `M5`: the solver holds the defended Salt training cases with bounded error
  before any new feature closure is attempted
- `M6`: bracket-wave cases are compared as out-of-sample stress tests
