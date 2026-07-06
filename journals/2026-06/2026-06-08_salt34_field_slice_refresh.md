# Salt 3/4 Field Slice Refresh

Generated: `2026-06-08T13:46:21-05:00`

## Observed output

- Reconstructed `U` into the staged latest-time mirrors for `viscosity_screening_salt_test_3_jin_coarse_mesh` at `t = 2514 s` and `viscosity_screening_salt_test_4_jin_coarse_mesh` at `t = 2082 s`.
- Rendered new individual temperature and velocity slices for Salt 3 Jin and Salt 4 Jin in PNG/SVG/PDF form.
- Rebuilt `reports/2026-06-08_ethan_presentation_figure_package/` so Salt 3/4 slices are included by default.

## Interpretation

- The presentation package now covers Salt 1 caution contrast, Salt 2 validation anchor, and Salt 3/4 representative sensitivity visuals with consistent timestep stamping.
- The existing June 4 transient-axial package remains the source for `Nu(x)` and `q''(x)` style plots; no new explicit `HTC(x)` or distance-resolved `Delta p(x)` curve was produced in this pass.

## Contradictions / anomalies

- Slurm marked three of the four Salt 3/4 render jobs as `FAILED ExitCode=11`, but all requested figure outputs were written successfully and verified on disk.

## Next suggested actions

- If a true hydraulic-evolution slide is needed, build transient `p_rgh` histories or a distance-resolved pressure reconstruction rather than reusing the latest-time ranking bar chart.
- If the deck needs an explicit heat-transfer coefficient label, decide whether `Nu(x)` is sufficient as the scientific proxy or derive `HTC(x)` from a documented conductivity and length scale definition.

## June 22 Retrospective Status

- The Salt 3/4 slice refresh itself stayed valid and needed no further render
  repair.
- The two suggested actions remain optional presentation/product decisions, not
  stale render-pipeline debt.
