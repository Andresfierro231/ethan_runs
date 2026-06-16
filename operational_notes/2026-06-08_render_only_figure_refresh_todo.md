# 2026-06-08 Render-Only Figure Refresh TODO

- Promote the render-only Slurm pattern to the default plotting workflow for staged OpenFOAM cases.
- Fold the black scalar-bar styling into any remaining legacy field renderers that still emit non-black labels.
- Investigate why job `3216687` wrote complete outputs but still reported `ExitCode=11:0` in Slurm accounting.
- Decide whether to keep or prune the `_tonly_backup_2026-06-08` staging directories after downstream consumers no longer need the pre-refresh state.
