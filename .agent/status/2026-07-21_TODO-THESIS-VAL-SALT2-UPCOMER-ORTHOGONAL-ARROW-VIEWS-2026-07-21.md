---
provenance:
  - .agent/BOARD.md
  - tools/extract/render_branch_velocity_arrow_images.py
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_val_salt2_upcomer_orthogonal_arrow_views/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_val_salt2_upcomer_orthogonal_arrow_views/output_manifest.csv
tags: [status, thesis, figures, paraview, upcomer, val-salt2]
related:
  - TODO-THESIS-VAL-SALT2-UPCOMER-ORTHOGONAL-ARROW-VIEWS-2026-07-21
task: TODO-THESIS-VAL-SALT2-UPCOMER-ORTHOGONAL-ARROW-VIEWS-2026-07-21
date: 2026-07-21
role: Figures/cfd-pp/Implementer/Tester/Writer
type: status
status: complete
supersedes: []
superseded_by:
---
# TODO-THESIS-VAL-SALT2-UPCOMER-ORTHOGONAL-ARROW-VIEWS-2026-07-21

## Objective

Render page-aligned Salt2 validation/external upcomer velocity-arrow companions
for the requested `side_x`, `side_y`, and `side_z` views, starting from the
existing liked front-view artifact and staged ParaView render input.

## Outcome

Complete. Slurm job `3308677` rendered and validated PNG/SVG/PDF artifacts for
all three requested views under:

```text
figures/figures_rendered/paraview_velocity_arrows_orthogonal/val_salt_test_2_coarse_mesh_laminar/upcomer/
```

The `side_y` render is the strongest single page-aligned horizontal loop-head
view. `side_x` is a thin orthogonal projection normal to `x`. `side_z` preserves
the original/front axis convention while using the requested `side_z` suffix.

## Changes Made

- Added explicit `side_y` and `side_z` view presets to
  `tools/extract/render_branch_velocity_arrow_images.py`.
- Changed branch status output naming so suffix-bearing renders write
  `status_<suffix>.json` instead of overwriting `status.json`.
- Added task package and Slurm wrapper:
  `work_products/2026-07/2026-07-21/2026-07-21_thesis_val_salt2_upcomer_orthogonal_arrow_views/`.
- Updated thesis figure ledgers:
  - `reports/thesis_dossier/Chapters_and_sections/current/12_thesis_figures_and_diagrams_plan.md`
  - `reports/thesis_dossier/Chapters_and_sections/current/21_csem_figure_table_incorporation_package.md`
  - `reports/thesis_dossier/figures/README.md`
  - `reports/thesis_dossier/figures/figure_claim_crosswalk.csv`
  - `reports/thesis_dossier/figures/source_manifest.csv`

## Validation

- `python3.11 -m py_compile tools/extract/render_branch_velocity_arrow_images.py`
  passed.
- `bash -n work_products/2026-07/2026-07-21/2026-07-21_thesis_val_salt2_upcomer_orthogonal_arrow_views/scripts/render_val_salt2_upcomer_side_xyz.sbatch`
  passed.
- `git diff --check` on the task-edited paths passed before submission.
- `sacct -j 3308677 --format JobID,JobName,Partition,Account,State,Elapsed,ExitCode -P`
  reported `COMPLETED|0:0`.
- The Slurm wrapper validated `9` non-empty artifacts in
  `output_manifest.csv`.
- Visual sanity checks passed for all three generated PNGs.

ParaView/OSMesa produced post-write signal-11 messages for `side_x` and
`side_z`; the artifacts were already written, per-view status JSON reported
`rendered`, and the wrapper validation passed.

## Unresolved Blockers

None for the requested figure-generation task. Scientific use remains bounded:
these Salt2 validation/external visuals are diagnostic/test evidence only.

## Guardrails

- Native OpenFOAM source outputs mutated: no.
- Registry/admission state mutated: no.
- Scheduler action: yes, task-owned ParaView/OSMesa render job `3308677` only.
- OpenFOAM solver/postprocessing/sampler/harvest launched: no.
- Fluid/external repository mutation: no.
- Fitting/tuning/model selection/admission/final score claim: no.
- Runtime-leakage rules relaxed: no.
