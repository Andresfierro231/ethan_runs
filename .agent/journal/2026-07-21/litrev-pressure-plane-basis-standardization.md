---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_pressure_plane_basis_standardization/pressure_plane_basis_standardization.csv
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_pressure_plane_basis_standardization/next_extraction_queue.csv
tags: [cfd-postprocessing, pressure-ledger, pressure-basis, litrev-contract]
related:
  - .agent/status/2026-07-21_TODO-LITREV-PRESSURE-PLANE-BASIS-STANDARDIZATION.md
  - imports/2026-07-21_litrev_pressure_plane_basis_standardization.json
task: TODO-LITREV-PRESSURE-PLANE-BASIS-STANDARDIZATION
date: 2026-07-21
role: cfd-pp/Hydraulics/Tester/Writer
type: journal
status: complete
---
# LitRev Pressure Plane/Basis Standardization Journal

## Attempted

Claimed the open pressure-plane basis standardization row and built a
package-local inventory from existing pressure artifacts only. The task was
kept to metadata and provenance: no scheduler action, solver launch,
postprocessing launch, native-output mutation, registry mutation, Fluid edit, or
external-repo edit.

## Observed

The current pressure evidence is broad but uneven:

- Station pressure maps are numerous and already carry `p`, `p_rgh`, `mean_un`,
  density, and RAF proxy fields.
- Branch pressure screens summarize 66 branch aggregates but intentionally omit
  several row-level basis fields.
- The pressure-term ledger has the best span-level hydrostatic/kinetic/total
  pressure decomposition, but it is a span momentum budget rather than a
  standardized plane ledger.
- The `corner_lower_right` two-tap rows are the best resolved endpoint pressure
  rows, with static, `p_rgh`, hydrostatic, kinetic, density, face q-ref, RAF,
  RMF, and SVF evidence.
- F6 endpoint rows are planned candidates, not harvested evidence.
- PM10/upcomer targets retain `p_rgh`, density, speed, and dynamic pressure, but
  not static pressure, unit normals, signed/absolute mdot, RAF/RMF/SVF, or
  same-window residuals.

## Inferred

The next pressure-side blocker is not "find any pressure field"; it is
admission-grade consistency. Same-QOI UQ needs a stable pressure-source index,
and this package supplies that index. Current two-tap rows can support a
same-QOI uncertainty audit from existing endpoint faces, but they still cannot
support ordinary component-K or F6 admission because the recirculation and
component-isolation gates fail.

## Contradictions / Caveats

- Some pressure-term rows have `fit_target` status in their source ledger, while
  the LitRev pressure/corner rows remain diagnostic or section-effective. This
  package preserves that distinction instead of promoting component K.
- The PM10/upcomer pressure target rows are terminal evidence from older
  selected runs, but the newer corrected-Q continuation `3307441` supersedes
  them for latest selected corrected-Q promotion until terminal harvest proves
  otherwise.
- A parallel validation attempt failed because the checker read the generated
  CSV while the builder was rewriting it; the sequential validation passed.

## Next Useful Actions

1. Claim `TODO-LITREV-SAME-QOI-UQ-EXECUTION`.
2. Use `pressure_plane_basis_standardization.csv` as the pressure-source index.
3. Start with existing two-tap endpoint faces for same-QOI UQ.
4. Keep F6 and PM10/upcomer rows terminal/sampler-gated until separately
   claimed.
