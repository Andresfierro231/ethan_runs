---
provenance:
  task: AGENT-406
  generated_by: codex
tags: [cfd-pp, pm5, matched-plane, vtk, f6, diagnostic]
related:
  - work_products/2026-07/2026-07-15/2026-07-15_pm5_matched_plane_parser_repair/README.md
  - work_products/2026-07/2026-07-14/2026-07-14_pm5_corrected_q_matched_plane_unlock/README.md
---
# PM5 Wall-Band VTK and F6 Unlock Repair

Date: 2026-07-15
Task: AGENT-406

## Result

Resampled representative-time staged plane and wall-band VTKs for
`salt2_lo5q`, `salt2_hi5q`, `salt4_lo5q`, and `salt4_hi5q` in an AGENT-406
scratch tree. The output plane VTKs now carry cell fields `rho`, `Re`, `Pr`,
`Ri`, `Gr`, and `Ra` alongside `U`, `T`, and `p_rgh`; the wall-band VTKs are
checked for `wallHeatFlux`.

The earlier July 14 samples were time `0` fallbacks because `reconstructPar`
failed on a stale `#include "functions"` in `controlDict`. This package fixes
that include only in copied scratch cases and leaves native solver outputs
unchanged.

## Outputs

- `resampled_pm5_matched_plane_metrics.csv`: combined parsed metrics for the
  requested PM5 cases.
- `resampled_vtk_field_validation.csv`: per-plane field-presence check.
- `pm5_f6_internal_nu_unlock_scorecard.csv`: gate status for F6 and internal-Nu.
- `pm5_case_unlock_status.csv`: per-case F6/internal-Nu readiness summary.
- `command_log_manifest.csv`: reconstruct/sample/parse command logs.
- `source_manifest.csv`: source and generated artifact provenance.
- `summary.json`: machine-readable status.

## Guardrails

- Native CFD source trees were read-only.
- The July 14 staged output tree was not edited.
- The generated VTK files are diagnostic until a later admission gate consumes
  them.
- Repaired rows remain diagnostic until a later gate explicitly admits them.
  Internal-Nu availability here means the VTK field blocker is cleared, not that
  Nu/HTC rows have passed sign, heat-balance, recirculation, or admission review.

## Summary

- Cases requested: salt2_lo5q, salt2_hi5q, salt4_lo5q, salt4_hi5q
- VTK validation rows: 12
- Failed VTK validation rows: 0
- Parsed metric rows: 12
- Plane/wall-T rows ready: 12
- wallHeatFlux rows ready: 12
- F6 bounded review unlocked: True
- Internal-Nu review unlocked: True
- Metric status counts: `{'complete_with_wallHeatFlux': 12}`
