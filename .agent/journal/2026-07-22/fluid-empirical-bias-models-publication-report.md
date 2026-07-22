---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_empirical_leg_bias_correction_diagnostic/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_reduced_dof_bias_transfer_screen/README.md
  - work_products/2026-07/2026-07-22/2026-07-22_fluid_empirical_bias_models_publication_report/report.md
tags: [journal, forward-model, empirical-bias, publication-report]
related:
  - .agent/status/2026-07-22_TODO-FLUID-EMPIRICAL-BIAS-MODELS-PUBLICATION-REPORT-2026-07-22.md
  - imports/2026-07-22_fluid_empirical_bias_models_publication_report.json
task: TODO-FLUID-EMPIRICAL-BIAS-MODELS-PUBLICATION-REPORT-2026-07-22
date: 2026-07-22
role: Writer/Reviewer/Tester
type: journal
status: complete
---
# Empirical Bias Models Publication Report

## Attempted

Converted the empirical leg-bias and reduced-DOF transfer packages into a
publication-facing numerical-scientific report. The report defines the model
forms, explains offset versus multiplier language, summarizes the numerical
evidence, and draws a strict boundary between diagnostic discrepancy modeling
and physical closure admission.

## Observed

The strongest reportable pattern is that low-DOF corrections transfer well on
the existing TSWFC2 stress rows. `F1_global_offset` reduces transfer MAE from
`106.121666 K` to `19.061398 K`, while `F2_global_affine` reaches
`13.873169 K` with two degrees of freedom. `F5` is best numerically at
`13.324483 K` but has four degrees of freedom.

The source/property blocker remains active: the reduced-DOF package has a
task-owned source-property TODO with `204` findings. No external-test row was
scored.

## Inferred

The best rigorous interpretation is not that the empirical coefficients are
physics, but that the current 1D temperature error has a coherent, low-rank
structure. This points toward temperature-reference mismatch, wall/bulk
projection, source/sink placement, source/property mismatch, or missing 3D
mixing/storage as the next physical explanations.

## Caveats

The report uses completed diagnostic artifacts only and does not create a new
score. The TSWFC2 source candidate remains non-admitted. The Phase E Fluid
external-BC path does not yet have a compatible multi-split sensor score table.

## Next Useful Actions

1. Run or harvest a runtime-legal Fluid external-BC multi-split sensor table.
2. Repeat `F1`/`F2` as frozen fits on that current Fluid artifact.
3. Perform leave-one-case-out stability checks.
4. Audit wall/bulk projection, source/sink redistribution, and source/property
   label release before any admission prose.

