# Ethan Transport Interpretation Package

Generated: `2026-06-17`

This package is the internal evidence-first interpretation layer for the
current postprocessed transport outputs. It sits on top of the finished
per-case packages and the regenerated campaign builders. It is not a new
extraction workflow.

## Canonical inputs

- Math and definition reference:
  - `reports/2026-06-17_ethan_streamwise_transport_math_reference/MATH_COMPANION.md`
- Representative Salt 2 comparison:
  - `reports/2026-06-15_ethan_representative_transport_comparison/summary.json`
  - `reports/2026-06-15_ethan_representative_transport_comparison/representative_transport_profiles.csv`
  - `reports/2026-06-15_ethan_representative_transport_comparison/representative_branch_thermal_summary.csv`
- Salt-family campaign:
  - `reports/2026-06-15_ethan_field_transport_campaign/summary.json`
  - `reports/2026-06-15_ethan_field_transport_campaign/field_transport_branch_thermal_comparison.csv`
  - `reports/2026-06-15_ethan_field_transport_campaign/field_transport_streamwise_heat_comparison.csv`
- All-Ethan campaign:
  - `reports/2026-06-15_ethan_all_runs_field_transport_campaign/summary.json`
  - `reports/2026-06-15_ethan_all_runs_field_transport_campaign/field_transport_branch_thermal_comparison.csv`

## What is now stable

- All 13 per-case packages exist on one schema.
- Salt-family and all-Ethan campaign packages both publish:
  - streamwise heat-loss comparisons
  - azimuthal mean comparisons
  - branch thermal comparisons
  - branch thermal QC comparisons
- The representative Salt 2 package now also publishes branch thermal summary
  outputs alongside the existing loopwise hydraulic, thermal, and
  boundary-layer comparisons.

## How to read the current outputs

### Hydraulic comparisons

- Use shear-based `darcy_f` and direct wall-registered `dp/ds` together.
- Do not treat the direct reduction as a centerline pressure trace. The current
  direct path is a wall-area-averaged `p_rgh` diagnostic on the repaired
  coordinate.
- The representative Salt 2 package remains the right place to inspect
  mechanism-level disagreement or agreement between the two reductions.

### Thermal comparisons

- Effective `HTC`, `UA'`, and `R'_th` are support-gated effective indicators,
  not intrinsic coefficients.
- The new branch summaries make the bulk-state and thermal-driving-force story
  easier to read than the loopwise curves alone, but they inherit the same
  masking logic.
- If a branch has weak `|T_bulk - T_wall|` support or large masked fractions,
  use the QC outputs first and the HTC/UA values second.

### Branch interpretation

- The six repaired sections remain first-class outputs.
- The derived `upcomer` branch is a concatenation of
  `left_lower_leg + test_section_span + left_upper_leg`.
- Corners and junctions are still intentionally omitted from that derived
  branch coordinate.

## Observed current patterns

### Representative Salt 2 trio

- The `upcomer` branch is currently one of the cleaner thermal comparison
  surfaces in the trio:
  - `Salt 2 val` mean effective HTC: about `130.9 W/m^2/K`
  - `Salt 2 Jin` mean effective HTC: about `117.2 W/m^2/K`
  - `Salt 2 Kirst` mean effective HTC: about `92.8 W/m^2/K`
  - usable fraction for all three: about `0.96`
- The `right_leg` branch is comparatively weak thermally in the trio:
  - mean effective HTC is only about `30-32 W/m^2/K`
  - usable fraction is only about `0.73`
  - this is still a usable comparison, but the support is materially weaker
    than the `upcomer` or `upper_leg`
- The `test_section_span` branch is currently the cleanest thermal anchor in
  the representative trio:
  - zero masked fraction in the current branch summary
  - minimum resolved `|T_bulk - T_wall|` remains comfortably above the thermal
    masking floor in the current campaign QC tables

### All-Ethan QC patterns

- The worst masked branch/section fractions in the current all-case branch QC
  comparison are concentrated in the water-family path rather than the
  Salt-family path:
  - `val_water_test_1_coarse_mesh_laminar` has the highest current masked
    fraction on `left_lower_leg`, `upcomer`, and `upper_leg`
  - `val_water_test_2_coarse_mesh_laminar` has the highest current masked
    fraction on `lower_leg`
- The strongest warning in the current Salt-family thermal QC is the
  `right_leg` branch/section in `val_salt_test_2_coarse_mesh_laminar`
  with masked fraction about `0.269`
- Some of the worst current QC rows also have very small minimum resolved
  `|T_bulk - T_wall|`, for example:
  - `upper_leg` in `val_water_test_1_coarse_mesh_laminar`
  - `left_lower_leg` and `upcomer` in `val_water_test_1_coarse_mesh_laminar`
  These are exactly the kinds of cases where the effective thermal ratios can
  become unstable or disappear by design.

## Interpretation boundary

Safe:

- compare where transport resistance accumulates around the loop
- compare where effective thermal transfer is well supported versus support
  limited
- use branch summaries to separate robust trends from masking-heavy branches

Not safe:

- promote the current effective HTC or `UA'` results into intrinsic local heat
  transfer coefficients
- explain every large branch-to-branch difference as physics before checking
  the branch QC comparison
- use the derived `upcomer` distance as if it includes corners or junctions

## Next recommended checks

1. Use the representative Salt 2 branch summary and the loopwise
   hydraulic/thermal overlays together before writing any mechanism narrative.
2. For any branch with large masked fraction, check the branch QC figure before
   discussing the corresponding HTC/UA values.
3. Treat the water-family branch QC figures as the first place to look when
   comparing Salt and Water thermal behavior, because that is where the largest
   current support differences show up.
