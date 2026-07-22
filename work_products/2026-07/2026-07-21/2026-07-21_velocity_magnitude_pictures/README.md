---
provenance:
  - tools/extract/render_branch_velocity_arrow_images.py
  - work_products/2026-07/2026-07-21/2026-07-21_velocity_magnitude_pictures/output_manifest.csv
  - work_products/2026-07/2026-07-21/2026-07-21_velocity_magnitude_pictures/shared_velocity_ranges.csv
tags: [thesis, cfd-pp, figures, paraview, upcomer, recirculation, salt, matched-range]
related:
  - TODO-THESIS-SALT-UPCOMER-MATCHED-SIDE-Z-VELOCITY-PICTURES-2026-07-21
  - .agent/status/2026-07-21_TODO-THESIS-VAL-SALT2-UPCOMER-Y-VELOCITY-ARROW-VIEWS-2026-07-21.md
  - .agent/status/2026-07-21_TODO-THESIS-VAL-SALT2-UPCOMER-ORTHOGONAL-ARROW-VIEWS-2026-07-21.md
task: TODO-THESIS-SALT-UPCOMER-MATCHED-SIDE-Z-VELOCITY-PICTURES-2026-07-21
date: 2026-07-21
role: Figures/cfd-pp/Implementer/Tester/Writer
type: work_product
status: complete
supersedes: []
superseded_by:
---
# Matched Salt Upcomer Side-Z Velocity Pictures

## Purpose

This package contains matched `side_z` upcomer velocity-arrow figures for the
four representative Salt cases. It was made for side-by-side thesis/paper
figures where all panels in a family must share the same camera, color spectrum,
velocity range, and glyph scale basis.

Two figure families are present:

- `y_velocity_side_z`: y-component arrows with signed `U_y` color and
  `abs(U_y)` glyph length.
- `velocity_magnitude_side_z`: resultant velocity arrows with `|U|` color and
  `|U|` glyph length.

These figures are qualitative diagnostic CFD evidence for upcomer flow
structure and recirculation-aware model-form discussion. They do not admit a
predictive closure, validate SAM/CSEM, train an ordinary upcomer `Nu/f_D/K`, or
support a final predictive score.

## Source Cases

| Panel | Source ID | Case role |
| --- | --- | --- |
| Salt1 | `viscosity_screening_salt_test_1_jin_coarse_mesh` | representative Salt1/Jin diagnostic source |
| Salt2 | `val_salt_test_2_coarse_mesh_laminar` | Salt2 validation/external diagnostic source named by the existing figure |
| Salt3 | `viscosity_screening_salt_test_3_jin_coarse_mesh` | representative Salt3/Jin diagnostic source |
| Salt4 | `viscosity_screening_salt_test_4_jin_coarse_mesh` | representative Salt4/Jin diagnostic source |

All renders read staged ParaView inputs under `staging/render_inputs/**`; native
OpenFOAM source outputs were not mutated.

## Matched Ranges

The shared ranges are recorded in `shared_velocity_ranges.csv`.

| Family | Velocity mode | Color range [m/s] | Glyph scale range [m/s] |
| --- | --- | --- | --- |
| `y_velocity_side_z` | `y_component` | `[-0.07702504843473434, 0.07702504843473434]` | `[0.0, 0.07702504843473434]` |
| `velocity_magnitude_side_z` | `magnitude` | `[0.0, 0.07704159866519554]` | `[0.0, 0.07704159866519554]` |

Both families use `side_z`, the same upcomer component selection, and the same
reference span (`0.44822875372000004`) for glyph scale normalization.

## Outputs

Primary publication-format panel outputs are listed in `output_manifest.csv`.
Each family has four non-empty PNG, SVG, and PDF panels:

- `figures/y_velocity_side_z/<source_id>/upcomer/{png,svg,pdf}/...`
- `figures/velocity_magnitude_side_z/<source_id>/upcomer/{png,svg,pdf}/...`

Convenience preview composites are:

- `figures/y_velocity_side_z_composite_labeled.png`
- `figures/velocity_magnitude_side_z_composite_labeled.png`
- `figures/composites/y_velocity_side_z_trimmed_composite_labeled.png`
- `figures/composites/velocity_magnitude_side_z_trimmed_composite_labeled.png`

The composites are for review/layout only. On `2026-07-21`, they were rebuilt
with the package-local script `scripts/rebuild_review_composites.py` to crop the
large left-side whitespace, keep only the far-right shared scalar bar, move the
remaining scalar bar closer to the Salt4 pipe, place larger Salt labels above
the upcomers, make the upcomer crops visually thicker in the raster preview,
and annotate each case with exact-source `max down U_y` from
`y_velocity_side_z_status.json`. The rebuild writes
`figures/composites/review_composite_layout_manifest.csv` with the detected
pipe/scalar-bar crop boxes, scalar-bar scaling, pipe x-scale, shared-scalar-bar
flag, and downward-velocity annotation used for each panel. Use the individual
SVG/PDF panels for manuscript assembly when possible.

The `max down U_y` values are exact to the rendered-source status file:
Salt1 `0.068 m/s`, Salt2 `0.069 m/s`, Salt3 `0.072 m/s`, and Salt4
`0.077 m/s`. Recirculation fraction and Richardson-number annotations were not
added to the composite because the available RAF/Ri evidence is from related
matched-plane diagnostic packages, not from an exact four-source metric table
for these rendered panels.

Thesis-facing interpretation for the velocity-magnitude composite is in
`velocity_magnitude_side_z_thesis_analysis.md`. That note includes a proposed
caption, a table of exact rendered-source velocity extrema, a physical
explanation of the upward-throughflow plus downward-pocket structure, and
claim boundaries for using the image as model-form evidence without admitting
ordinary upcomer coefficients.

## Runtime

- Slurm job: `3308857`
- Node: `c318-009.ls6.tacc.utexas.edu`
- Script:
  `scripts/render_salt_upcomer_matched_side_z_velocity_pictures.sbatch`
- Renderer:
  `tools/extract/render_branch_velocity_arrow_images.py`
- View preset: `side_z`
- Component: `upcomer`

The `y_velocity_side_z` ParaView invocation returned `rc=0`. The
`velocity_magnitude_side_z` invocation returned a post-export ParaView/OSMesa
signal-11 message (`rc=255`), but all requested PNG/SVG/PDF artifacts were
written, all per-panel status files report `rendered`, and the wrapper
validated `24` non-empty artifacts before the Slurm job completed with
`COMPLETED|0:0`.

## Validation

- `python3.11 -m py_compile tools/extract/render_branch_velocity_arrow_images.py`
  passed.
- `bash -n scripts/render_salt_upcomer_matched_side_z_velocity_pictures.sbatch`
  passed.
- `git diff --check` passed before render submission.
- `sacct -j 3308857 --format JobID,JobName,Partition,Account,State,Elapsed,ExitCode -P`
  reported `COMPLETED|0:0`.
- Package validator wrote `output_manifest.csv` with `24` panel artifacts and
  `shared_velocity_ranges.csv` with two matched-range rows.
- Visual checks passed for the trimmed `U_y` and magnitude side-by-side preview
  composites: panels are nonblank, consistently framed, and show the requested
  `side_z` angle.
- `python3.11 -m py_compile scripts/rebuild_review_composites.py` passed.
- `python3.11 scripts/rebuild_review_composites.py` rebuilt the two top-level
  composites and two trimmed composites from the existing rendered PNG panels.
- Visual checks passed for the refreshed `U_y` and magnitude composites: the
  single shared scalar bar is retained only on the far-right panel, panels are
  closer together, left whitespace is tightly cropped, Salt labels are readable
  above the upcomers, and exact-source `max down U_y` annotations are readable.

## Guardrails

- Native OpenFOAM source outputs mutated: no.
- Registry/admission state mutated: no.
- Scheduler action: yes, task-owned ParaView/OSMesa render job `3308857` only.
  No additional scheduler action was used for the later preview-composite
  layout refresh.
- OpenFOAM solver/postprocessing/sampler/harvest launched: no.
- Fluid/external repository mutation: no.
- Fitting/tuning/model selection/admission/final score claim: no.
- Runtime-leakage rules relaxed: no.
- Diagnostic-only evidence: yes.
