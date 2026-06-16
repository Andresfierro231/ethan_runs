# 2026-06-08 Rendering And Runner TODO

- Submit the June 8 smoke temperature rerender jobs so the scalar-bar labels are regenerated in black.
- Submit the June 8 smoke velocity jobs and verify the first two velocity slice outputs before wider rollout.
- Decide whether to consolidate the older temperature-only renderer into the new generic field renderer after smoke validation.
- Migrate future OpenFOAM continuation sbatches to `tools/run_openfoam_case.sh` once the current live jobs are no longer sensitive to launcher changes.
- If velocity smoke rendering succeeds, choose whether the next figure expansion should be streamlines, pressure slices, or Jin-vs-Kirst delta visuals.
