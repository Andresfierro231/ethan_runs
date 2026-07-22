---
provenance:
  - tools/extract/render_branch_velocity_arrow_images.py
  - work_products/2026-07/2026-07-21/2026-07-21_velocity_magnitude_pictures/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_velocity_magnitude_pictures/output_manifest.csv
  - work_products/2026-07/2026-07-21/2026-07-21_velocity_magnitude_pictures/shared_velocity_ranges.csv
tags: [journal, thesis, figures, paraview, upcomer, recirculation, salt, matched-range]
related:
  - TODO-THESIS-SALT-UPCOMER-MATCHED-SIDE-Z-VELOCITY-PICTURES-2026-07-21
  - .agent/status/2026-07-21_TODO-THESIS-SALT-UPCOMER-MATCHED-SIDE-Z-VELOCITY-PICTURES-2026-07-21.md
  - work_products/2026-07/2026-07-21/2026-07-21_velocity_magnitude_pictures/README.md
task: TODO-THESIS-SALT-UPCOMER-MATCHED-SIDE-Z-VELOCITY-PICTURES-2026-07-21
date: 2026-07-21
role: Figures/cfd-pp/Implementer/Tester/Writer
type: journal
status: complete
supersedes: []
superseded_by:
---
# Matched Salt Upcomer Side-Z Velocity Pictures

## Attempted

The user requested all-four-Salt versions of the Salt2 `side_z` upcomer
velocity images, with a common color spectrum and velocity range, and asked that
the new figure folder live under a dated work-products folder. I extended the
renderer to support shared velocity ranges across selected cases and rendered
two matched families: signed y-velocity component arrows and resultant velocity
magnitude arrows.

The user then requested that all composite pictures have much larger color bars,
more aggressive left-white-edge cropping so the upcomers sit closer together,
color bars moved closer to the pipes, and much larger readable titles between
each upcomer and velocity color bar. I added a package-local composite rebuild
script and regenerated the four review composite PNGs from the existing rendered
panel PNGs. No ParaView, OpenFOAM, sampler, harvest, scheduler, registry, or
native-output action was used for this layout refresh.

The user then noted that the axes/ranges are shared and asked to keep only the
far-right color bar, crop the other panels closer, put titles on top of the
upcomers, make the upcomer visually thicker, and include a useful quantitative
recirculation-related number such as recirculation fraction, maximum downward
velocity, or average Richardson number. I updated the same composite rebuild
script to keep only the far-right scalar bar, tighten panel spacing, draw large
Salt labels above each upcomer, horizontally emphasize the raster upcomer crop,
and annotate exact-source maximum downward y-velocity from
`y_velocity_side_z_status.json`.

The user then identified the velocity-magnitude composite as a thesis figure
candidate and requested accompanying analysis explaining why the velocity
behaves this way. I added
`velocity_magnitude_side_z_thesis_analysis.md` beside the figure package. The
note includes a thesis-ready caption, exact rendered-source velocity-extrema
table, physical explanation of upward throughflow plus localized downward
motion, a suggested thesis paragraph, and claim boundaries.

## Observed

- Source IDs rendered:
  - `viscosity_screening_salt_test_1_jin_coarse_mesh`
  - `val_salt_test_2_coarse_mesh_laminar`
  - `viscosity_screening_salt_test_3_jin_coarse_mesh`
  - `viscosity_screening_salt_test_4_jin_coarse_mesh`
- Component: `upcomer`
- View preset: `side_z`
- Slurm job: `3308857`
- Scheduler result: `COMPLETED|0:0`
- Primary artifacts: `24` non-empty PNG/SVG/PDF panels.
- Shared y-component color range:
  `[-0.07702504843473434, 0.07702504843473434] m/s`.
- Shared velocity-magnitude color range:
  `[0.0, 0.07704159866519554] m/s`.
- Visual checks confirmed that the trimmed side-by-side composites are nonblank,
  consistently framed, and suitable for quick manuscript-layout review.
- Refreshed composite files:
  - `figures/y_velocity_side_z_composite_labeled.png`
  - `figures/velocity_magnitude_side_z_composite_labeled.png`
  - `figures/composites/y_velocity_side_z_trimmed_composite_labeled.png`
  - `figures/composites/velocity_magnitude_side_z_trimmed_composite_labeled.png`
- The refreshed composites are about `5292-5297 x 2520` pixels instead of the
  earlier `~14560 x 2459-2556` pixel wide layouts.
- The rebuild script writes
  `figures/composites/review_composite_layout_manifest.csv`, recording detected
  pipe and scalar-bar crop boxes and scalar-bar scale factors for each panel.
- The single-scalar-bar refresh reduced the composite dimensions to about
  `2520-2525 x 2695` pixels. The rendered-source `max down U_y` annotations are
  Salt1 `0.068 m/s`, Salt2 `0.069 m/s`, Salt3 `0.072 m/s`, and Salt4
  `0.077 m/s`.
- The analysis note ties the visual to the existing upcomer-recirc evidence:
  repaired PM5 rows report maximum reverse area fraction `0.7901396438`,
  maximum reverse mass fraction `0.5000672828`, and maximum Richardson number
  `108.7458056`; the S9 ledger keeps exchange QOIs blocked while preserving the
  recirculation-validity diagnostic use.

## Inferred

These figures can support thesis prose about upcomer recirculation-aware model
validity and the visual reason a single-stream or purely axisymmetric model form
is insufficient in this branch. They should remain diagnostic visual evidence,
not closure-admission evidence. Quantitative recirculation fraction, exchange
flow, and same-window uncertainty still belong to the dedicated S9/S13 study
path.

## Contradictions Or Caveats

The resultant-velocity ParaView/OSMesa invocation emitted a post-export
signal-11 message and returned `rc=255`, while all per-panel status files
reported `rendered`, all files existed, the wrapper validator accepted all
artifacts, and Slurm reported `COMPLETED|0:0`. This matches previous renderer
behavior and should be cited as a rendering-runtime caveat, not as a failed
artifact set.

The final composite refresh retains only the far-right scalar bar because the
color/velocity ranges are shared. The displayed `max down U_y` values are exact
to the rendered sources. RAF/Ri annotations were not used because the available
recirculation-fraction and Richardson-number evidence belongs to related
matched-plane diagnostic packages and is not an exact four-source table for the
rendered Salt1/val-Salt2/Salt3/Salt4 panels. For the thesis or paper, the
individual SVG/PDF panels should still be the preferred source when a
vector-native layout is needed; the refreshed PNG composites are appropriate
for quick review and raster figure insertion.

The analysis note intentionally uses the figure as model-form evidence only. It
does not claim an admitted exchange-cell coefficient, ordinary upcomer `Nu`,
ordinary `f_D`, component `K`, F6 coefficient, final predictive score, or
same-QOI UQ acceptance.

## Next Useful Actions

- Add the individual SVG/PDF paths to the thesis figure incorporation ledger if
  the thesis body figure package is being updated.
- Build a manuscript-native multi-panel figure from the SVG/PDF panels rather
  than relying on the preview PNG composites.
- Keep captions explicit that the evidence is diagnostic CFD visualization and
  does not admit ordinary upcomer or exchange-cell closures.
- If final thesis layout requires vector output with the same larger scalar-bar
  style, add explicit ParaView scalar-bar sizing/title-font controls to
  `tools/extract/render_branch_velocity_arrow_images.py` under a new figure
  row, then rerender on a compute node.
- If per-panel recirculation fraction or Richardson number is desired on this
  exact four-panel figure, first build an exact-source metric table for the four
  rendered sources rather than borrowing related matched-plane PM5/PM10 values.
