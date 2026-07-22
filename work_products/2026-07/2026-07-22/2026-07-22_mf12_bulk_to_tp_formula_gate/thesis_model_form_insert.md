---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_mf12_bulk_to_tp_formula_gate/summary.json
tags: [mf12, bulk-to-tp, model-form, diagnostic-only]
status: draft_insert
---
# MF12 Bulk-to-TP Projection Formula Gate

The corrected model-form scoreboard indicates that part of the thermal
discrepancy is not a loop-energy error alone. For the M3 comparator, the
Salt2 train TP rows are uniformly cold relative to the TP targets
(`5/5` rows; mean signed error
`-15.091 K`). A sensor-kind projection correction reduces
transfer TP RMSE from `13.5673279702 K` to
`4.38159298515 K`, which is an existence proof that a
bulk-to-probe layer can matter.

The physically admissible form is therefore not an arbitrary offset, but a
source-bounded projection term:

```text
T_TP,j = T_bulk,s(j)(x_j) + Delta T_proj,j
Delta T_proj,j = sigma_q,j A_source,j Phi(Gz_j, x_j/D_h, reset_j, BC_j)
```

Here `sigma_q,j` is the sign of the local setup heat exchange, `A_source,j`
must come from a released source/property basis, and `Phi` is a developing-flow
or reset-memory shape function. This form is not admitted yet. The current
evidence supports the model-form direction but fails the release gate because
the source/property basis, TP projection UQ, and runtime wall/profile basis are
not released.

The same result explains why empirical corrections worked. D3 wall-shape
diagnostics reduced transfer RMSE by `51.6919381995%`,
and D4 segment source-placement diagnostics reduced transfer RMSE by
`54.272279139%`. MF11 concluded that F2/F5
are useful discrepancy diagnostics but are non-unique and not physical
closures. MF12 converts that lesson into a source-basis requirement: before a
new scorecard is credible, the projection term must be tied to setup heat
sign, development coordinate, source placement, and same-QOI uncertainty.

Claim boundary: MF12 is diagnostic-only. It supports a missing-physics
explanation and a next-study sequence, but it does not release a correction,
coefficient, source/property label, validation score, holdout score, external
score, or final predictive model.
