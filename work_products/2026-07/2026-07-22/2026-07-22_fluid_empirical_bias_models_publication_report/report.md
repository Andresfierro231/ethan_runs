---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_empirical_leg_bias_correction_diagnostic/leg_bias_correction_coefficients.csv
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_reduced_dof_bias_transfer_screen/frozen_coefficients.csv
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_reduced_dof_bias_transfer_screen/transfer_summary.csv
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_reduced_dof_bias_transfer_screen/split_runtime_leakage_audit.csv
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_reduced_dof_bias_transfer_screen/source_property_gate_todo.csv
tags: [forward-model, empirical-bias, discrepancy-model, publication-report]
related:
  - README.md
task: TODO-FLUID-EMPIRICAL-BIAS-MODELS-PUBLICATION-REPORT-2026-07-22
date: 2026-07-22
role: Writer/Reviewer/Tester
type: report
status: complete
---
# Empirical Bias and Correction Models for the 1D Thermal Prediction Path

## Abstract

The current setup-only 1D Fluid model predicts mass flow and loop
temperatures from experimental setup inputs, but recent full-loop thermal
diagnostics show large temperature residuals. A train-only Phase E external-BC
solve produced all-probe temperature mean absolute error (MAE) near `81.6 K`.
An empirical per-leg affine diagnostic compressed this train-only residual to
`7.28 K`, but its per-leg coefficients were too flexible and in several cases
not physically interpretable. A follow-on reduced-degree-of-freedom (reduced
DOF) study therefore tested whether simpler frozen correction structures
transfer beyond the fit rows.

The reduced-DOF screen fit six predeclared correction families using only
Salt1/Salt2 train/support sensor rows from an existing TSWFC2 bounded nominal
scorecard, then applied the frozen coefficients unchanged to Salt3/Salt4
legacy validation/holdout-style stress rows. The best transfer family,
`F5_thermal_family_offset_shared_multiplier`, reduced frozen-transfer MAE from
`106.12 K` to `13.32 K`. The best lower-complexity family,
`F2_global_affine`, used only two degrees of freedom and transferred at
`13.87 K`. These results support a rigorous diagnostic conclusion: a large
portion of the current 1D/3D temperature discrepancy is systematic and
low-dimensional. They do not yet support final predictive admission because
external-test rows were not scored, source/property gates remain blocked, and
the source candidate itself remains `not_admitted_no_grid_expansion`.

## Purpose and Claim Boundary

The empirical layer is introduced as a discrepancy model, not as a replacement
for heat-transfer physics. The intended scientific use is to quantify how much
of the residual can be represented by a small number of stable correction
parameters and to guide the next physical discrepancy studies.

Allowed claim:

The existing evidence shows that a small empirical temperature correction
family, trained only on train/support rows and frozen before transfer scoring,
substantially reduces legacy Salt3/Salt4 stress-row temperature residuals.
This indicates that the current thermal error has a strong systematic
component.

Forbidden claims:

- The empirical coefficients are not admitted physical closures.
- The corrected model is not a final predictive model.
- Salt3/Salt4 stress-row performance is not an external-test score.
- The result does not release source/property labels.
- The result does not justify hiding heat residuals in internal Nusselt number,
  friction, or other unrelated closure terms.

## Data Sources and Split Handling

Two completed packages are central.

1. The train-only empirical leg-bias diagnostic:
   `work_products/2026-07/2026-07-21/2026-07-21_fluid_empirical_leg_bias_correction_diagnostic/`.
   This package fit a per-leg affine correction to Salt2 Phase E residuals only.
   It was useful as an upper-bound diagnostic, but scored no protected split.

2. The reduced-DOF frozen transfer screen:
   `work_products/2026-07/2026-07-21/2026-07-21_fluid_reduced_dof_bias_transfer_screen/`.
   This package used existing TSWFC2 Salt1/Salt2 sensor rows as train/support
   fit rows (`32` usable rows) and Salt3/Salt4 rows as frozen transfer stress
   rows (`32` usable rows). Coefficients were fit before transfer scoring and
   not refit afterward.

The transfer screen explicitly states that no compatible sensor-level
external-test TSWFC2 prediction artifact was available, so `val_salt2` remains
unscored in this report. The runtime audit from the source TSWFC2 package
states that validation records were loaded only after `solve_case` returned;
this report itself runs no solver and consumes no target temperatures as
runtime inputs.

## Model Forms

All empirical models operate on a raw 1D predicted temperature `T_1D` and
produce a corrected temperature `T_c`.

The generic affine form is:

```text
T_c = a_g T_1D + b_g
```

where `g` is a group label. The additive term `b_g` is called the empirical
offset or bias. The multiplicative term `a_g` is called the empirical
correction factor. This naming is deliberately conservative: the offset and
multiplier are statistical discrepancy parameters unless later source-released
physics justifies a physical interpretation.

The reduced-DOF transfer screen used these predeclared families:

| Family | Form | DOF | Interpretation |
| --- | --- | ---: | --- |
| `F0_null_baseline` | `T_c = T_1D` | 0 | No empirical correction. |
| `F1_global_offset` | `T_c = T_1D + b` | 1 | Single common temperature bias. |
| `F2_global_affine` | `T_c = a T_1D + b` | 2 | Common scale and offset mismatch. |
| `F3_sensor_kind_offset` | `T_c = T_1D + b_TP` or `b_TW` | 2 | Bulk sensor versus wall sensor reference bias. |
| `F4_thermal_family_offset` | `T_c = T_1D + b_family` | 3 | Heat-path family offsets. |
| `F5_thermal_family_offset_shared_multiplier` | `T_c = a T_1D + b_family` | 4 | Shared scale mismatch plus heat-path offsets. |

The prior per-leg affine model used the same affine structure but allowed a
separate multiplier and offset for each leg. This created about ten potential
degrees of freedom and gave a useful upper-bound train diagnostic, but it is
too flexible and insufficiently source-released for publication as a closure.

## Numerical Results

The Phase E per-leg affine diagnostic compressed Salt2 train all-sensor MAE
from `81.581515 K` to `7.280898 K`. This was a useful bound on possible
residual compression, but several coefficients were not physically plausible
as direct closures: for example the upcomer fit had multiplier `-1.467820` and
offset `998.333409 K`, while the cooling branch fit had multiplier
`7.360668` and offset `-2262.557696 K`. These values are evidence of residual
structure, not admissible heat-transfer coefficients.

The reduced-DOF screen gives the publication-relevant result:

| Family | Train/support corrected MAE (K) | Transfer baseline MAE (K) | Transfer corrected MAE (K) | Transfer verdict |
| --- | ---: | ---: | ---: | --- |
| `F0_null_baseline` | `88.749900` | `106.121666` | `106.121666` | no improvement |
| `F1_global_offset` | `12.349545` | `106.121666` | `19.061398` | transfers directionally |
| `F2_global_affine` | `8.501470` | `106.121666` | `13.873169` | transfers directionally |
| `F3_sensor_kind_offset` | `12.370867` | `106.121666` | `19.146684` | transfers directionally |
| `F4_thermal_family_offset` | `11.562923` | `106.121666` | `17.514273` | transfers directionally |
| `F5_thermal_family_offset_shared_multiplier` | `9.014440` | `106.121666` | `13.324483` | transfers directionally |

Two observations matter most. First, even the one-parameter global offset
removes most of the transfer residual. Second, the two-parameter global affine
model transfers nearly as well as the four-parameter heat-family model. That is
strong parsimony evidence: the main discrepancy is not primarily a collection
of unrelated local sensor errors. It resembles a coherent temperature-reference
or temperature-scale mismatch plus smaller heat-path-specific residuals.

## Why the Model May Work

The empirical models work because the raw 1D predictions have a large coherent
temperature bias relative to the sensor references in the TSWFC2 scorecard.
The baseline transfer residual is positive and large, with Salt3/Salt4
frozen-transfer MAE `106.12 K`. A global offset directly removes a common
temperature-level error, improving transfer MAE to `19.06 K`.

The global affine model improves further. Its fitted form is:

```text
T_c = 0.3729829182408737 T_1D + 246.55192842685844 K
```

This form does not merely shift all predictions; it compresses the predicted
temperature range. A multiplier below one is consistent with a 1D model whose
temperature excursions are too large relative to the sensor reference frame.
Possible physical or numerical explanations include:

- a wall/bulk projection mismatch, where 1D segment states and probe
  measurements are not the same thermodynamic quantity;
- source/sink distribution mismatch, where heat is deposited or removed at the
  wrong axial location in the 1D reduction;
- material-property or source-envelope mismatch that shifts the global energy
  balance and gradient;
- missing thermal storage, recirculation, or 3D mixing that damps the true
  temperature variation relative to the 1D path;
- sensor-map/reference-position mismatch that creates a consistent offset
  between model states and extracted probe targets.

The heat-family model adds offsets for `cooling_branch`, `heated_lower_leg`,
and `vertical_loop` while keeping the same shared multiplier. Its best transfer
MAE (`13.32 K`) is only `0.55 K` lower than the global affine transfer MAE
(`13.87 K`). That small difference suggests that heat-path-local corrections
are useful but secondary to the global scale/offset correction.

## Assumptions

The report rests on the following assumptions:

1. The TSWFC2 sensor-level rows are internally comparable across Salt1-Salt4.
2. The post-solve measured temperatures are valid scoring references but were
   not used as runtime inputs.
3. Salt1/Salt2 rows are acceptable train/support rows for this diagnostic
   screen.
4. Salt3/Salt4 rows are acceptable legacy validation/holdout-style stress rows
   for frozen transfer diagnostics, but not final protected-score claims.
5. Sensor mapping, segment labels, and TP/TW classification are held fixed.
6. Residuals are interpreted as prediction minus reference, in kelvin.
7. The empirical coefficients are mathematical discrepancy parameters unless
   later studies connect them to source-released physical mechanisms.

## Caveats and Failure Modes

The main caveat is that the reduced-DOF screen is cross-artifact evidence. It
uses TSWFC2 bounded nominal scorecard rows, while the earlier Phase E
external-BC package contains only Salt2 train rows. The next decisive study
must run or harvest a compatible runtime-legal Fluid external-BC multi-split
sensor table.

The source/property gate remains blocked. The task-owned
`source_property_gate_todo.csv` reports `204` source/property findings,
including missing required label columns and missing source-property gate
status. This is why the corrected rows must remain diagnostic and cannot be
used for fit/admission prose.

The source TSWFC2 candidate remains `not_admitted_no_grid_expansion`. The
empirical layer can reduce residuals even when the underlying physical
candidate is not admitted, so good empirical accuracy does not by itself prove
that the model form is physically right.

The per-leg affine diagnostic warns against overinterpretation. Extreme or
sign-changing multipliers can be useful as residual ownership signals, but not
as publishable heat-transfer closures.

Finally, no external-test row was scored. The report therefore cannot claim
external generalization.

## Publication-Quality Interpretation

The strongest rigorous interpretation is:

The current 1D thermal model has a large systematic discrepancy relative to
the available TP/TW temperature references. A frozen empirical correction with
only one or two degrees of freedom transfers strongly across nominal Salt cases
within the existing TSWFC2 scorecard, reducing legacy Salt3/Salt4 stress-row
MAE from approximately `106 K` to approximately `14-19 K`. This behavior is
consistent with a stable temperature-reference or scale mismatch rather than
purely random or sensor-local error. The empirical layer should be used as a
diagnostic residual model and as a guide to physical discrepancy studies, not
as an admitted predictive closure.

For a numerical scientific publication, the best model to emphasize is
`F2_global_affine`, not `F5`, because `F2` is almost as accurate on transfer
rows and has only two degrees of freedom. The `F5` result is valuable as an
upper reduced-DOF bound showing that heat-family offsets can provide small
additional improvement.

## Recommended Next Studies

1. Runtime-legal multi-split Fluid score

   Generate a compatible sensor-level table from the current Fluid external-BC
   path for train/support, validation/support, holdout, and external-test
   partitions. Freeze coefficients before any protected score. This is the
   required study before final predictive claims.

2. Leave-one-case-out empirical stability

   Fit `F1` and `F2` on each allowed pair or triplet of nominal Salt cases and
   score the held-out nominal case without refitting. The goal is coefficient
   stability, not model selection.

3. Wall/bulk projection audit

   Compare TP and TW corrections against segment bulk, pipe-wall, and outer
   wall prediction sources. If the global affine multiplier mostly removes a
   wall/bulk projection mismatch, the correction should correlate with
   prediction-source kind and wall-to-bulk thermal resistance.

4. Source/sink redistribution audit

   Reconcile heater, cooler/HX, passive wall, and test-section heat ledgers
   against the corrected residual pattern. A stable global offset suggests
   energy-level mismatch; remaining family offsets suggest axial source/sink
   placement mismatch.

5. Source/property release gate

   Add required property-mode, source-envelope, source-use, and provenance
   labels to any row used for fit or admission. Until this passes, empirical
   results must stay diagnostic.

6. External-test freeze

   Once the runtime-legal candidate and source/property gates pass, score an
   external-test artifact such as `val_salt2` without coefficient changes. The
   external-test result should be reported whether it passes or fails.

## Conclusion

The empirical bias/correction study is scientifically useful because it turns a
large thermal residual into a structured discrepancy. The low-DOF transfer
result suggests that the 1D model is not failing in an arbitrary way. Instead,
the discrepancy is largely coherent and may be traceable to temperature
reference, source/sink placement, wall/bulk reduction, material/source
properties, or missing 3D mixing/storage physics.

The publication should present this as a diagnostic result: physics takes the
model to the current residual; the empirical layer shows the residual has a
simple structure; the remaining work is to identify which physical or numerical
reduction assumption creates that structure.

