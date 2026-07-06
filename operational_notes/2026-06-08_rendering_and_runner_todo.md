# 2026-06-08 Rendering And Runner TODO

Status as of `2026-06-22`:

- The smoke-render submission items below are resolved.
- The broader velocity/pressure/component-family expansion was completed later
  under AGENT-073 and AGENT-075.
- The only item below that remains potentially useful is the non-ParaView
  launcher migration note for future OpenFOAM continuation sbatches.

- Submit the June 8 smoke temperature rerender jobs so the scalar-bar labels are regenerated in black.
- Submit the June 8 smoke velocity jobs and verify the first two velocity slice outputs before wider rollout.
- Decide whether to consolidate the older temperature-only renderer into the new generic field renderer after smoke validation.
- Migrate future OpenFOAM continuation sbatches to `tools/run_openfoam_case.sh` once the current live jobs are no longer sensitive to launcher changes.
- If velocity smoke rendering succeeds, choose whether the next figure expansion should be streamlines, pressure slices, or Jin-vs-Kirst delta visuals.
