# Kirst Visualization Campaign

This note stages the first steady-state field-visualization pass for the two
currently converged salt viscosity-screen cases.

## Target cases

- `viscosity_screening_salt_test_1_kirst_coarse_mesh`
- `viscosity_screening_salt_test_2_kirst_coarse_mesh`

Both are currently marked `comparison_candidate` in
`reports/2026-06-02_ethan_case_metadata_index/ethan_case_metadata_index.csv`
and `reports/2026-06-02_ethan_closure_and_visualization_scaffold/closure_scaffold.csv`.

## Reproducible submission workflow

Run from the workspace root:

```bash
sbatch --parsable staging/render_jobs/viscosity_screening_salt_test_1_kirst_coarse_mesh_render.sbatch
sbatch --parsable staging/render_jobs/viscosity_screening_salt_test_2_kirst_coarse_mesh_render.sbatch
```

## Expected products

- staged render-entry status under `staging/render_inputs/<source_id>/`
- rendered output status under `figures_rendered/<source_id>/status.json`
- first-pass screenshots under `figures_rendered/<source_id>/`

## Interpretation boundary

- This pass is only a first visualization pass.
- If the rendered outputs are too coarse or fail on decomposed-case handling,
  the next fixes should be:
  - reconstruct a render-ready local case copy, or
  - add more explicit ParaView driver logic for selected scalar fields and cuts.
