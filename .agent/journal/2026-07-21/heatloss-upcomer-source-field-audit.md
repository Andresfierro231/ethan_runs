---
provenance:
  - tools/analyze/build_heatloss_upcomer_source_field_audit.py
  - tools/analyze/test_heatloss_upcomer_source_field_audit.py
  - work_products/2026-07/2026-07-21/2026-07-21_heatloss_upcomer_source_field_audit/case_window_source_audit.csv
  - work_products/2026-07/2026-07-21/2026-07-21_heatloss_upcomer_source_field_audit/missing_field_blockers.csv
tags: [journal, heat-loss, upcomer, source-field-audit, exchange-cell, no-solver]
related:
  - .agent/status/2026-07-21_TODO-HEATLOSS-UPCOMER-SOURCE-FIELD-AUDIT.md
  - imports/2026-07-21_heatloss_upcomer_source_field_audit.json
  - work_products/2026-07/2026-07-21/2026-07-21_heatloss_upcomer_source_field_audit/README.md
task: TODO-HEATLOSS-UPCOMER-SOURCE-FIELD-AUDIT
date: 2026-07-21
role: Implementer/Tester/Writer/Thermal-modeling/Hydraulics/cfd-pp
type: journal
status: complete
supersedes: []
superseded_by:
---
# Heat-Loss Upcomer Source-Field Audit

## Attempted

Implemented a lightweight source-field audit for the current mainline upcomer
exchange windows: salt 2 at `7915` s, salt 3 at `7618` s, and salt 4 at
`10000` s. The audit checked filesystem presence and package provenance only.
It did not read large native fields, generate surfaces, run OpenFOAM, launch a
sampler, submit scheduler work, fit coefficients, or change admission state.

## Observed

All three target time directories exist under the continuation case stages and
contain the primary native fields `U`, `T`, `p`, `p_rgh`, and `rho`. They also
have `phi`, `nuEff`, and diagnostic `wallHeatFlux`, and each case has a mesh
station file in the July 1 mesh-centerline work product.

The blocker table has six blocked inputs per case: direct `mu`, `cellVolume`,
`recircMask`, exchange-interface VTK, wall/core surface VTK, and source/sink
ledger. `nuEff` plus `rho` may be useful for a future viscosity proxy, but this
audit did not admit it as `R_mu`.

## Inferred

The next useful implementation step is not production extraction. The rigorous
path is to harden the sampler interface and fail-closed row emission first,
then claim a separate execution row to generate or point to the missing VTK,
mask, volume, and source-ledger inputs. If the next step requires OpenFOAM
surface generation or large field sampling, it should be routed through Slurm
rather than run as an unbounded foreground job.

## Contradictions Or Caveats

Primary same-window fields being present does not mean exchange-cell extraction
is ready. The missing interface/mask/volume/source-ledger products are the
actual blockers for `V_recirc`, `mdot_exchange`, `tau_recirc`, pressure
residual, and energy residual. Heat residual must remain explicit and must not
be hidden in internal Nu.

## Next Useful Actions

1. Finish the sampler implementation interface with explicit fail-closed output
   rows and no-admission guard columns.
2. Claim a separate input-generation or compute-execution row for surface,
   mask, volume, and source-ledger artifacts.
3. Run production extraction only after the missing input basis is available.
4. Pair extracted exchange QOIs with same-QOI UQ before any Phase 4B rescore.
