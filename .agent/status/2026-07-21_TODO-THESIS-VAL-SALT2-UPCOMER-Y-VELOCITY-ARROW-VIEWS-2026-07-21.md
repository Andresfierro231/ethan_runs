---
provenance:
  - .agent/BOARD.md
  - tools/extract/render_branch_velocity_arrow_images.py
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_val_salt2_upcomer_y_velocity_arrow_views/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_val_salt2_upcomer_y_velocity_arrow_views/output_manifest.csv
tags: [status, thesis, figures, paraview, upcomer, val-salt2, y-velocity]
related:
  - TODO-THESIS-VAL-SALT2-UPCOMER-Y-VELOCITY-ARROW-VIEWS-2026-07-21
task: TODO-THESIS-VAL-SALT2-UPCOMER-Y-VELOCITY-ARROW-VIEWS-2026-07-21
date: 2026-07-21
role: Figures/cfd-pp/Implementer/Tester/Writer
type: status
status: complete
supersedes: []
superseded_by:
---
# TODO-THESIS-VAL-SALT2-UPCOMER-Y-VELOCITY-ARROW-VIEWS-2026-07-21

## Objective

Create a second Salt2 validation/external upcomer view family that shows only
the y-direction velocity component instead of velocity magnitude.

## Outcome

Complete. The renderer now has a non-default `--velocity-mode y_component` path
that uses `U_y*jHat` as the arrow vector, `abs(U_y)` for glyph scaling, and
signed `U_y` for coloring. Slurm job `3308809` generated and validated
`side_x`, `side_neg_x`, `side_y`, and `side_z` PNG/SVG/PDF outputs under:

```text
figures/figures_rendered/paraview_velocity_y_arrows/val_salt_test_2_coarse_mesh_laminar/upcomer/
```

## Changes Made

- Extended `tools/extract/render_branch_velocity_arrow_images.py` with
  `--velocity-mode` choices `magnitude` and `y_component`.
- Preserved default magnitude behavior and filenames.
- Added y-component output stem `velocity_y_component_arrows`.
- Added task-owned Slurm wrapper, README, logs, statuses, and manifest under:
  `work_products/2026-07/2026-07-21/2026-07-21_thesis_val_salt2_upcomer_y_velocity_arrow_views/`.
- Updated thesis figure ledgers and manifests:
  - `reports/thesis_dossier/Chapters_and_sections/current/12_thesis_figures_and_diagrams_plan.md`
  - `reports/thesis_dossier/Chapters_and_sections/current/21_csem_figure_table_incorporation_package.md`
  - `reports/thesis_dossier/figures/README.md`
  - `reports/thesis_dossier/figures/figure_claim_crosswalk.csv`
  - `reports/thesis_dossier/figures/source_manifest.csv`

## Validation

- `python3.11 -m py_compile tools/extract/render_branch_velocity_arrow_images.py`
  passed.
- `bash -n work_products/2026-07/2026-07-21/2026-07-21_thesis_val_salt2_upcomer_y_velocity_arrow_views/scripts/render_val_salt2_upcomer_y_velocity_side_views.sbatch`
  passed.
- `git diff --check` passed for task-edited files before render submission.
- `sacct -j 3308809 --format JobID,JobName,Partition,Account,State,Elapsed,ExitCode -P`
  reported `COMPLETED|0:0`.
- The wrapper validated `12` non-empty PNG/SVG/PDF artifacts.
- Visual sanity checks passed for all four PNGs.

ParaView/OSMesa returned post-write `rc=255` signal-11 messages for `side_x`,
`side_neg_x`, and `side_y`; each per-view status reports `rendered`, all files
exist, and wrapper/visual validation passed.

## Unresolved Blockers

None for the requested figure set. The `side_y` y-component view needs a caption
caveat because looking along y makes y-directed arrows appear mostly as circular
glyph ends.

## Guardrails

- Native OpenFOAM source outputs mutated: no.
- Registry/admission state mutated: no.
- Scheduler action: yes, task-owned ParaView/OSMesa render job `3308809` only.
- OpenFOAM solver/postprocessing/sampler/harvest launched: no.
- Fluid/external repository mutation: no.
- Fitting/tuning/model selection/admission/final score claim: no.
- Runtime-leakage rules relaxed: no.
