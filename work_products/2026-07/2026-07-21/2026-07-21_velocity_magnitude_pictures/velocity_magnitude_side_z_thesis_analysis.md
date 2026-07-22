---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_velocity_magnitude_pictures/figures/velocity_magnitude_side_z_composite_labeled.png
  - work_products/2026-07/2026-07-21/2026-07-21_velocity_magnitude_pictures/y_velocity_side_z_status.json
  - work_products/2026-07/2026-07-21/2026-07-21_velocity_magnitude_pictures/velocity_magnitude_side_z_status.json
  - work_products/2026-07/2026-07-17/2026-07-17_upcomer_pipe_cell_hybrid_model/recirculation_feature_scorecard.csv
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_study_s9_upcomer_onset_anchor_exchange_uq/onset_anchor_ledger.csv
  - reports/thesis_dossier/Chapters_and_sections/current/04_upcomer_recirculation_modeling.md
tags: [thesis, cfd-pp, figures, upcomer, velocity, recirculation, explanation]
related:
  - TODO-THESIS-SALT-UPCOMER-MATCHED-SIDE-Z-VELOCITY-PICTURES-2026-07-21
  - work_products/2026-07/2026-07-21/2026-07-21_velocity_magnitude_pictures/README.md
task: TODO-THESIS-SALT-UPCOMER-MATCHED-SIDE-Z-VELOCITY-PICTURES-2026-07-21
date: 2026-07-21
role: Figures/cfd-pp/Writer/Reviewer
type: thesis-analysis
status: current
supersedes: []
superseded_by:
---
# Velocity-Magnitude Side-Z Upcomer Figure Analysis

## Figure Use

Use this note with:

```text
work_products/2026-07/2026-07-21/2026-07-21_velocity_magnitude_pictures/figures/velocity_magnitude_side_z_composite_labeled.png
```

The figure is a matched `side_z` qualitative CFD visualization of the upcomer
for four Salt cases. All panels use the same view, component clip, glyph scale
basis, and shared velocity-magnitude color range. The scalar bar range is
`0.0` to `0.07704159866519554 m/s`. The annotated `max down U_y` values come
from the exact rendered-source `y_velocity_side_z_status.json`, not from a
separate postprocessing harvest.

## Thesis-Ready Caption

Matched side-view OpenFOAM velocity-arrow visualization of the upcomer in four
representative Salt cases. The arrows show local velocity direction and are
colored by velocity magnitude using a shared range across all panels. Each case
retains a net upward path, but the side view also exposes coherent downward
velocity pockets along the upcomer, with exact rendered-source maximum downward
`U_y` values of `0.068`, `0.069`, `0.072`, and `0.077 m/s` for Salt1-Salt4,
respectively. This structure is diagnostic evidence that the upcomer is not an
ordinary single-stream vertical pipe in the current CFD regime; it requires a
recirculation-aware model form.

## What The Image Shows

The dominant flow in each panel is upward, as expected for the loop upcomer.
However, the glyphs are not uniformly aligned with the upward branch direction.
Each panel contains localized downward arrows on one side of the upcomer, and
the downward component persists across the Salt1-Salt4 set. The effect is not a
single isolated outlier in one case; it is visible under the same camera,
component clip, color range, glyph basis, and postprocessing script.

The exact rendered-source local extrema support the visual reading:

| Panel | Source ID | Last time [s] | Local max `|U|` [m/s] | Max down `U_y` [m/s] |
| --- | --- | ---: | ---: | ---: |
| Salt1 | `viscosity_screening_salt_test_1_jin_coarse_mesh` | `3229.0` | `0.0676597920` | `0.0676477924` |
| Salt2 | `val_salt_test_2_coarse_mesh_laminar` | `1724.0` | `0.0686873035` | `0.0686238632` |
| Salt3 | `viscosity_screening_salt_test_3_jin_coarse_mesh` | `2514.0` | `0.0717233588` | `0.0716750324` |
| Salt4 | `viscosity_screening_salt_test_4_jin_coarse_mesh` | `2082.0` | `0.0770415987` | `0.0770250484` |

These values should be described as rendered-slice diagnostics. They are useful
for explaining the image and the direction of the flow structure, but they do
not replace full control-volume recirculation metrics.

## Why The Velocity Behaves This Way

The upcomer is a buoyancy-driven vertical branch embedded in a closed loop, not
an isolated fully developed pipe. Heating and cooling around the loop establish
the pressure and density imbalance that drives the net upward circulation in the
upcomer. At the same time, the upcomer path includes distinct subregions:
`left_lower_leg`, `test_section_span`, and `left_upper_leg`. The middle
test-section span has a different physical role and wall/source condition than
a generic insulated vertical pipe.

That combination naturally supports a throughflow-plus-recirculation structure:
one part of the cross-section carries the net upward loop flow, while another
part can move downward or weakly exchange with the upward core. In a vertical
mixed-convection branch, buoyancy, wall heat transfer, fittings/connectors, and
area/source-role changes can create nonuniform axial momentum and secondary
motion. The downward pockets in the figure are the visual signature of that
section-effective exchange, not a small perturbation to a uniform 1D profile.

The broader recirculation evidence agrees with this interpretation. The current
thesis recirculation section reports maximum reverse area fraction
`0.7901396438`, maximum reverse mass fraction `0.5000672828`, and maximum
Richardson number `108.7458056` from repaired PM5 rows. The S9 onset/exchange
ledger records diagnostic recirculation validity for nominal Salt2/Salt3/Salt4
matched-plane upcomer rows, while also preserving that exchange-state QOIs such
as `V_recirc`, `mdot_exchange`, and `tau_recirc` remain missing or blocked.

## How To Use The Figure In The Argument

Use the figure to motivate model-form choice. The safe thesis claim is:

> The upcomer CFD fields show a persistent upward throughflow coupled to
> localized downward/recirculating motion. Therefore, the upcomer should not be
> reduced to an ordinary single-stream pipe closure in the current regime.

That claim supports a hybrid modeling lane: a throughflow path for the net loop
circulation plus a separately named recirculation/exchange path. It also
supports why ordinary upcomer `Nu`, `f_D`, component `K`, or F6-style labels
remain blocked for these recirculating rows.

## Claim Boundaries

Do not use this image by itself to admit an exchange-cell coefficient or a
predictive closure. It is a visual diagnostic. The current blockers are:

- no accepted exact-source same-QOI mesh/time uncertainty for the displayed
  recirculation features;
- no admitted exact-source `V_recirc`, `mdot_exchange`, or `tau_recirc`;
- no final split-safe scorecard proving that a frozen recirculation model
  improves prediction without runtime leakage;
- no ordinary-pipe coefficient admission for the upcomer under these
  recirculating conditions.

Recirculation fraction and Richardson number are not printed on the composite
because the available RAF/Ri values are from related matched-plane diagnostic
packages, not from an exact four-source table for the rendered Salt1,
validation-Salt2, Salt3, and Salt4 image panels.

## Suggested Thesis Paragraph

Figure X shows why the upcomer was separated from the ordinary pipe-closure
pool. Although the net loop circulation is upward through the upcomer, the
matched side-view velocity arrows show localized downward motion in every
displayed Salt case. The maximum downward y-velocity in the rendered slices is
of the same order as the local velocity-magnitude scale, ranging from
`0.068 m/s` to `0.077 m/s`. This is consistent with the independent
recirculation evidence, where repaired matched-plane rows show large reverse
area and reverse mass fractions and high Richardson numbers. The upcomer was
therefore treated as a recirculation-aware branch: a net throughflow path plus a
separate exchange or recirculation lane. This figure is used as model-form
evidence only; it does not admit an ordinary upcomer heat-transfer, friction, or
component-loss coefficient.
