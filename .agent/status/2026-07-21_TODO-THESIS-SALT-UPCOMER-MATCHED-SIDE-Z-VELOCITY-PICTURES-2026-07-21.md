---
provenance:
  - .agent/BOARD.md
  - tools/extract/render_branch_velocity_arrow_images.py
  - work_products/2026-07/2026-07-21/2026-07-21_velocity_magnitude_pictures/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_velocity_magnitude_pictures/output_manifest.csv
  - work_products/2026-07/2026-07-21/2026-07-21_velocity_magnitude_pictures/shared_velocity_ranges.csv
tags: [status, thesis, figures, paraview, upcomer, recirculation, salt, matched-range]
related:
  - TODO-THESIS-SALT-UPCOMER-MATCHED-SIDE-Z-VELOCITY-PICTURES-2026-07-21
  - .agent/journal/2026-07-21/thesis-salt-upcomer-matched-side-z-velocity-pictures.md
  - work_products/2026-07/2026-07-21/2026-07-21_velocity_magnitude_pictures/README.md
task: TODO-THESIS-SALT-UPCOMER-MATCHED-SIDE-Z-VELOCITY-PICTURES-2026-07-21
date: 2026-07-21
role: Figures/cfd-pp/Implementer/Tester/Writer
type: status
status: complete
supersedes: []
superseded_by:
---
# TODO-THESIS-SALT-UPCOMER-MATCHED-SIDE-Z-VELOCITY-PICTURES-2026-07-21

## Objective

Produce matched `side_z` upcomer arrow pictures for the four representative Salt
cases: one `U_y`-component set and one resultant velocity-magnitude set, each
with a shared color/velocity range suitable for side-by-side thesis/paper use.

## Outcome

Complete. Slurm job `3308857` generated and validated the requested matched
Salt1-Salt4 `side_z` panels under:

```text
work_products/2026-07/2026-07-21/2026-07-21_velocity_magnitude_pictures/
```

The package contains `24` primary panel artifacts: four Salt cases times two
velocity families times PNG/SVG/PDF. It also contains two trimmed composite PNG
previews for quick side-by-side review.

User-requested preview refresh complete. The four composite PNGs were rebuilt
from the existing rendered panel PNGs with one far-right shared scalar bar,
tighter left-side cropping, closer inter-panel spacing, larger Salt labels above
the upcomers, visually thicker raster upcomer crops, and exact-source
`max down U_y` annotations for each rendered source.

Thesis-facing analysis is now complete for the velocity-magnitude composite at
`work_products/2026-07/2026-07-21/2026-07-21_velocity_magnitude_pictures/velocity_magnitude_side_z_thesis_analysis.md`.
It provides a caption, exact rendered-source velocity-extrema table, physical
explanation, suggested thesis paragraph, and claim boundaries.

## Shared Ranges

- `y_velocity_side_z`: color range
  `[-0.07702504843473434, 0.07702504843473434] m/s`; glyph scale range
  `[0.0, 0.07702504843473434] m/s`.
- `velocity_magnitude_side_z`: color range
  `[0.0, 0.07704159866519554] m/s`; glyph scale range
  `[0.0, 0.07704159866519554] m/s`.

## Changes Made

- Extended `tools/extract/render_branch_velocity_arrow_images.py` with
  task-needed shared velocity range handling across all selected source IDs.
- Added a task-owned Slurm wrapper at
  `work_products/2026-07/2026-07-21/2026-07-21_velocity_magnitude_pictures/scripts/render_salt_upcomer_matched_side_z_velocity_pictures.sbatch`.
- Generated matched primary panel artifacts under:
  - `work_products/2026-07/2026-07-21/2026-07-21_velocity_magnitude_pictures/figures/y_velocity_side_z/`
  - `work_products/2026-07/2026-07-21/2026-07-21_velocity_magnitude_pictures/figures/velocity_magnitude_side_z/`
- Added review composites under:
  `work_products/2026-07/2026-07-21/2026-07-21_velocity_magnitude_pictures/figures/composites/`.
- Added package-local review-composite rebuild script:
  `work_products/2026-07/2026-07-21/2026-07-21_velocity_magnitude_pictures/scripts/rebuild_review_composites.py`.
- Rebuilt all four review composite PNGs:
  - `work_products/2026-07/2026-07-21/2026-07-21_velocity_magnitude_pictures/figures/y_velocity_side_z_composite_labeled.png`
  - `work_products/2026-07/2026-07-21/2026-07-21_velocity_magnitude_pictures/figures/velocity_magnitude_side_z_composite_labeled.png`
  - `work_products/2026-07/2026-07-21/2026-07-21_velocity_magnitude_pictures/figures/composites/y_velocity_side_z_trimmed_composite_labeled.png`
  - `work_products/2026-07/2026-07-21/2026-07-21_velocity_magnitude_pictures/figures/composites/velocity_magnitude_side_z_trimmed_composite_labeled.png`
- Added composite layout provenance:
  `work_products/2026-07/2026-07-21/2026-07-21_velocity_magnitude_pictures/figures/composites/review_composite_layout_manifest.csv`.
- Updated the composite builder to retain only the far-right scalar bar and to
  annotate exact-source maximum downward y-velocity from
  `work_products/2026-07/2026-07-21/2026-07-21_velocity_magnitude_pictures/y_velocity_side_z_status.json`:
  Salt1 `0.068 m/s`, Salt2 `0.069 m/s`, Salt3 `0.072 m/s`, Salt4
  `0.077 m/s`.
- Recirculation fraction/Ri annotations were deliberately not placed on the
  composites because the current RAF/Ri evidence is not an exact four-source
  metric table for these rendered panels.
- Added thesis analysis note:
  `work_products/2026-07/2026-07-21/2026-07-21_velocity_magnitude_pictures/velocity_magnitude_side_z_thesis_analysis.md`.
- Added package README, output manifest, shared range table, status, journal,
  and import manifest.

## Validation

- `python3.11 -m py_compile tools/extract/render_branch_velocity_arrow_images.py`
  passed.
- `bash -n work_products/2026-07/2026-07-21/2026-07-21_velocity_magnitude_pictures/scripts/render_salt_upcomer_matched_side_z_velocity_pictures.sbatch`
  passed.
- `git diff --check` passed before render submission.
- `sacct -j 3308857 --format JobID,JobName,Partition,Account,State,Elapsed,ExitCode -P`
  reported `COMPLETED|0:0`.
- The wrapper validated `24` non-empty PNG/SVG/PDF artifacts.
- Visual sanity checks passed for both trimmed composite PNGs.
- `python3.11 -m py_compile work_products/2026-07/2026-07-21/2026-07-21_velocity_magnitude_pictures/scripts/rebuild_review_composites.py`
  passed.
- `python3.11 work_products/2026-07/2026-07-21/2026-07-21_velocity_magnitude_pictures/scripts/rebuild_review_composites.py`
  rebuilt `4` composite PNGs and wrote
  `figures/composites/review_composite_layout_manifest.csv`.
- Refreshed composite dimensions are approximately `2520-2525 x 2695`, down
  from the previous `5292-5297 x 2520` layout and original
  `14560 x 2459-2556` layout; visual checks confirm the requested single
  far-right colorbar, tighter crop, closer spacing, readable above-upcomer
  labels, and exact-source downward-velocity annotations.
- Thesis analysis note was cross-checked against
  `y_velocity_side_z_status.json`, `velocity_magnitude_side_z_status.json`,
  `recirculation_feature_scorecard.csv`, `onset_anchor_ledger.csv`, and the
  current thesis upcomer recirculation section.

The magnitude ParaView/OSMesa invocation returned a post-export signal-11
message (`rc=255`), consistent with previous rendering behavior. All requested
artifacts were already written, per-panel status files report `rendered`, and
the package validator passed.

## Unresolved Blockers

None for the requested figure set. For manuscript layout, use the individual
SVG/PDF panels rather than the PNG composites when possible.

## Guardrails

- Native OpenFOAM source outputs mutated: no.
- Registry/admission state mutated: no.
- Scheduler action: yes, task-owned ParaView/OSMesa render job `3308857` only.
  The preview-composite refresh used no scheduler action.
- OpenFOAM solver/postprocessing/sampler/harvest launched: no.
- Fluid/external repository mutation: no.
- Fitting/tuning/model selection/admission/final score claim: no.
- Runtime-leakage rules relaxed: no.
- Diagnostic-only figure evidence: yes.
