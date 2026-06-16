# 2026-06-08 Timestep Stamp Refresh

## Observed Output

- Updated the temperature and velocity slice renderers so the exported field images include a black timestep stamp in the upper-right corner.
- Re-rendered the current Salt 1 Kirst and Salt 2 validation slice figures.
- Rebuilt the presentation figure package so the temperature/velocity panel now uses the stamped source PNGs.

## Interpretation

- The timestep is now visible directly on the field figures, which makes slide reuse safer because the image itself carries its simulation-time context.

## Caveat

- The render-only Slurm jobs still reported `ExitCode=11`, but the stamped PNG/SVG/PDF outputs were successfully written and verified from the exported files.
