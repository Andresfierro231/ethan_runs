# 2026-06-08 Figure Refresh Addendum

## Observed Output

- Re-rendered the Salt 1 Kirst and Salt 2 temperature last-timestep slice figures after forcing scalar-bar tick labels and titles to black.
- Generated new Salt 1 Kirst and Salt 2 velocity magnitude last-timestep slice figures in PNG, SVG, and PDF.
- Verified the exported SVG text nodes for the temperature scalar bars use `fill="#000000"`.

## Inferred Interpretation

- The reliable batch path on LS6 is to reconstruct the required fields first, then run ParaView-only Slurm jobs against the staged reconstructed cases.
- Mixing the OpenFOAM bootstrap and ParaView launch in one short render job was less robust than the render-only path.

## Contradictions / Caveats

- The mixed OpenFOAM-plus-ParaView smoke jobs failed quickly and were not used for the final artifacts.
- Slurm recorded one render-only velocity job (`3216687`) as failed with a segmentation fault even though the status JSON and all expected figure outputs were written successfully for that case.

## Next Suggested Actions

- Normalize the render-only job wrapper so the successful path is the default for future figure refreshes.
- If the batch accounting anomaly for `3216687` matters operationally, rerun that case once more under the same render-only path and compare exit behavior.
- Generalize the render workflow if more fields beyond `T` and `U` are needed.

## June 22 Retrospective Status

- The first and third suggested actions are now resolved in substance by the
  later generic field-renderer and ParaView family work.
- The remaining unresolved point is only whether cleaner Slurm accounting is
  worth additional hardening; the render family no longer treats that exit code
  anomaly as a scientific blocker.
