# Ethan Case Analysis Package

Generated: `2026-06-10T17:49:24-05:00`

Method companion: `METHODOLOGY_MATH_COMPANION.md`

## Observed Outputs

- Source case: `val_salt_test_2_coarse_mesh_laminar` under profile `salt2_val_case_v1`.
- Requested retained field times: `7483, 7484, 7485, 7486, 7487` s.
- Major-loss times present: `7483, 7484, 7485, 7486, 7487` s.
- Feature-budget times present: `7483, 7484, 7485, 7486, 7487` s.
- Matched streamwise thermal times present: `7483, 7484, 7485, 7486, 7487` s.
- Heat tail ends at `7506` s.
- Hydraulic raw extraction source: `/scratch/09748/andresfierro231/projects_scratch/ethan_runs/reports/2026-06-10_ethan_salt2_case_analysis_package/raw_extraction`.

## Inferred Interpretation

- The package uses one shared manifest so the hydraulic streams operate from one frozen late-time window rather than self-selecting different retained times.
- Major losses are reported legwise with centerline bins, while corner and connector effects remain in the feature-based minor-loss budget.
- The hydraulic package now carries two parallel major-loss reductions on the same repaired bins: a shear-based estimate and a direct wall-pressure-drop view from area-averaged `p_rgh`.
- The streamwise thermal extension now reports wall temperature, matched cross-sectional fluid temperature from OpenFOAM cut planes using connected-region, mass-flux-weighted support selection, the legacy TP-endpoint bulk estimate for comparison, wall heat flux, effective HTC, and effective `UA'` on the same repaired loop coordinate.
- Heat accounting follows the existing wallHeatFlux section semantics so the hydraulic and thermal products can sit in one per-case report package.
- The mathematical details, reduction rules, notation, and stated limitations are documented in `METHODOLOGY_MATH_COMPANION.md`.

## Contradictions And Caveats

- `profile_dp_pa` remains deferred; feature `wall_dp_pa` is still inferred from adjacent major-span gradients.
- Hydraulic diameter and flow area remain geometry estimates from wall area per unit length using a circular-perimeter approximation.
- The direct hydraulic comparison uses wall-area-averaged `p_rgh`, not a volume-centerline probe, so it is best interpreted as a wall-registered pressure-drop diagnostic on the repaired span coordinate.
- The local thermal extension now uses OpenFOAM sampled cut-plane `T` and `U`, selects one connected support region per bin, and mass-flux-weights `T` over aligned positive flux on that chosen region. The older TP-endpoint interpolation is retained as a comparison diagnostic.
- Effective HTC and `UA'` are masked whenever the chosen support region fails the current quality gates: wrong-sign/fallback support, chosen-area ratio outside `[0.5, 2.0]` relative to the monitor reference area, or `|T_bulk - T_wall| < 0.25 K`.
- Reconstructed retained `T` files required local sanitization of invalid `-nan` tokens before OpenFOAM could read the field on cut planes: `7484: 4, 7485: 5, 7487: 2` replacements.
- No major-loss spans were quarantined by the current projection-distance diagnostic.
- Features with negative minor residuals over the retained window: `corner_lower_left, corner_lower_right, corner_upper_left`. Treat these as reference-budget caveats, not as settled negative-loss physics.
- Heat validation metrics still depend on the older June 4 direct-validation package; the live heat tail is `7506` s while the reused validation reference ends at `3871` s.

## Next Actions

- Review the now-unquarantined major-loss spans against the raw centerline-distance and warning diagnostics before tightening any hydraulic interpretation.
- Split `test_section_complex` into smaller feature objects if a connector-level minor-loss narrative is needed.
- Review the thermal support-QC figure and any masked gaps before using local HTC / `UA'` language in the report text.
- Add the next case profile under `tools/case_analysis_profiles.py` only after this Salt 2 package is review-clean on both provenance and interpretation.
