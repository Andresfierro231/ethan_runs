# 2026-06-08 Render-Only Figure Refresh TODO

Status as of `2026-06-22`:

- The render-only pattern is now the proven ParaView figure path rather than an
  open experiment; see `tools/extract/2026-06-15_paraview_field_render_workflow.md`.
- The generic field renderer and the later AGENT-073/075 ParaView work
  superseded the June 8 smoke-only state.
- The remaining bullets below should be read as optional hardening or cleanup,
  not live blockers.

- Promote the render-only Slurm pattern to the default plotting workflow for staged OpenFOAM cases.
- Fold the black scalar-bar styling into any remaining legacy field renderers that still emit non-black labels.
- Investigate why job `3216687` wrote complete outputs but still reported `ExitCode=11:0` in Slurm accounting.
- Decide whether to keep or prune the `_tonly_backup_2026-06-08` staging directories after downstream consumers no longer need the pre-refresh state.
