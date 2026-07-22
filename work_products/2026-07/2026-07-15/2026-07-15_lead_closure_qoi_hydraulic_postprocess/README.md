# AGENT-409 Lead Closure-QOI / Hydraulic Postprocess

Created: `2026-07-15T14:05:23.773469+00:00`

## Result

This package makes the unblock plan executable without mutating native CFD
outputs. Closure-QOI rows are classified, Salt2/Salt3/Salt4 test-section
two-tap diagnostics are harvested from the AGENT-409 scratch OpenFOAM
`agent409RawTwoTapSurfaces` outputs, and a scratch-only OpenFOAM runner is
available at `scripts/run_staged_raw_two_tap.sh`.

Final forward-v1 remains blocked. Internal Nu remains zero fit-admissible.

## Assumptions And Methods

- Native solver outputs were read-only; new commands write only under `tmp/2026-07-15_lead_closure_qoi_hydraulic_postprocess`.
- Two-tap convention: lower `left_lower_leg__s00`, upper `left_upper_leg__s04`;
  both reduced-pressure signs are reported.
- The scratch raw two-tap surfaces are equal-face proxy diagnostics, not
  mesh/GCI admitted component-K evidence.
- `p_rgh` is reported as reduced pressure and is not silently promoted to a
  universal static-pressure coefficient.
- CFD `rcExternalTemperature` wallHeatFlux includes radiation when present; no
  separate exported radiation term is invented.
- Internal Nu cannot absorb heater, cooler, passive loss, wall storage, or
  radiation residuals.

## Current Blockers

- Closure-QOI mesh/GCI: {'blocked_non_monotone_or_oscillatory': 16, 'blocked_missing_triplet': 6, 'blocked_sign_or_semantics_review': 3}
- Raw two-tap: diagnostic rows landed, but fit use is blocked by mesh/GCI,
  pressure-definition, centerline length, and recirculation policy.
- PM5/F6: AGENT-406 rows are useful diagnostics with wallHeatFlux present in
  the scratch VTKs; no final F6 scorecard has admitted rows.
