---
provenance:
  task: AGENT-406
  generated_by: codex
tags: [journal, cfd-pp, pm5, matched-plane, wallHeatFlux, f6, internal-nu]
related:
  - .agent/status/2026-07-15_AGENT-406.md
  - work_products/2026-07/2026-07-15/2026-07-15_pm5_wall_band_vtk_and_f6_unlock_repair/README.md
---
# PM5 Wall-Band VTK and F6 Unlock Repair

Date: 2026-07-15
Task: AGENT-406

## What changed

The previous PM5 repair showed that the July 14 staged samples were incomplete:
three cases sampled time `0` because `reconstructPar` failed on a stale
`system/functions` include, and all cases lacked wall-band `wallHeatFlux`.

AGENT-406 created a separate staged postprocessing path under
`tmp/2026-07-15_pm5_wall_band_vtk_and_f6_unlock_repair`. The repair keeps native
CFD outputs read-only, symlinks processor data into scratch, disables source
function objects only in scratch, reconstructs the representative fields, and
samples matched upcomer plane/wall-band VTKs.

## Outcome

Final scorecard:

- PM5 full plane fields for F6: unlocked for bounded review, not admitted.
- Wall-band `wallHeatFlux` for internal-Nu: unlocked for review, not admitted.
- Parsed rows: 12/12 complete with `wallHeatFlux`.
- VTK validation: 12/12 pass for the F6 plane field set.

The rows remain diagnostic until downstream gates admit them. Internal-Nu still
needs sign, heat-balance, recirculation, and admission review before any Nu/HTC
claim.

## Next work

Run the bounded F6/Re review using
`resampled_pm5_matched_plane_metrics.csv`, preserving train/holdout labels and
keeping thermal fitting out of the task.

Run the internal-Nu extraction/review from the repaired wall-band `wallHeatFlux`
VTKs, then apply the existing admission gates before using values in thesis or
forward-model claims.
