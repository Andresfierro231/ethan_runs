---
provenance:
  - work_products/2026-07/2026-07-20/2026-07-20_two_tap_recirc_residual_scorer/lower_apparent_k_diagnosis.csv
  - work_products/2026-07/2026-07-20/2026-07-20_two_tap_recirc_residual_scorer/q_ref_orientation_audit.csv
  - work_products/2026-07/2026-07-20/2026-07-20_two_tap_recirc_residual_scorer/recirc_residual_scorecard.csv
tags: [paper-diagnostic, two-tap, lower-apparent-k, recirculation]
task: TODO-TWO-TAP-RECIRC-RESIDUAL-SCORER
date: 2026-07-20
role: Hydraulics/cfd-pp/Writer
type: paper-diagnostic-note
status: complete
---
# Paper Diagnostic Note: Lower Apparent K In Recirculating Two-Tap Rows

## Result

The lower static apparent `K` trend is diagnostic, not an admitted component
loss trend. In the current `corner_lower_right` rows, static pressure is
hydrostatic/buoyancy dominated, local dynamic pressure grows across Salt2 to
Salt4, and material reverse flow invalidates ordinary single-stream
normalization.

## Interpretation

The apparent static `K` decreases mainly because the denominator grows while
the static pressure difference changes only modestly and remains dominated by
the hydrostatic correction. The `p_rgh` residuals are small and negative under
the preserved downstream-minus-upstream sign convention. That pattern supports
model-form selection, not coefficient admission.

## q_ref Status

The raw endpoint rows include normal velocity and mass flux, but the current
normal mass flux is tiny relative to speed-based mass flux. This package
therefore marks throughflow `q_ref` as untrusted until a single-leg
orientation/masking audit proves the denominator.

## Allowed Claims

- Current rows explain why ordinary component `K` is blocked.
- Lower apparent `K` can be caused by hydrostatic basis and denominator effects.
- A named recirculating section-effective residual is the right next model
  candidate.

## Forbidden Claims

- Do not claim lower admitted component `K`.
- Do not use tiny normal mass flux as a fitted denominator.
- Do not promote `K_eff_recirc_diagnostic` to ordinary `component_K`.
- Do not claim same-QOI UQ or non-recirculating anchor evidence exists today.

Generated rows: `3` current pressure pairs and
`6` endpoint q-ref audit rows.
