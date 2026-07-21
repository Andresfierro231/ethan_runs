---
provenance:
  - tools/extract/sample_upcomer_exchange_cell.py
  - tools/extract/test_sample_upcomer_exchange_cell.py
  - work_products/2026-07/2026-07-21/2026-07-21_heatloss_upcomer_exchange_sampler_implementation/exchange_sampler_rows.csv
  - work_products/2026-07/2026-07-21/2026-07-21_heatloss_upcomer_exchange_sampler_implementation/IMPLEMENTATION_NOTE.md
tags: [journal, heat-loss, upcomer, exchange-cell, sampler-implementation, fail-closed]
related:
  - .agent/status/2026-07-21_TODO-HEATLOSS-UPCOMER-EXCHANGE-SAMPLER-IMPLEMENTATION.md
  - imports/2026-07-21_heatloss_upcomer_exchange_sampler_implementation.json
  - work_products/2026-07/2026-07-21/2026-07-21_heatloss_upcomer_source_field_audit/README.md
task: TODO-HEATLOSS-UPCOMER-EXCHANGE-SAMPLER-IMPLEMENTATION
date: 2026-07-21
role: Implementer/Tester/Writer/Thermal-modeling/Hydraulics/cfd-pp
type: journal
status: complete
supersedes: []
superseded_by:
---
# Heat-Loss Upcomer Exchange Sampler Implementation

## Attempted

Extended the existing dry upcomer exchange sampler so it can write explicit
extraction rows from supplied VTK products and fail-closed unavailable rows when
required inputs are missing. The implementation was kept in the existing
sampler file and fixture-test suite, with no production read of native CFD
fields.

## Observed

The row writer now preserves extraction status, missing inputs, same-window ID,
pressure residual status, energy residual status, no-fit/no-score guards, and
the explicit residual policy. A dry CLI run for Salt2 `7915` emitted a
fail-closed row because `cell_vtk` and `interface_vtk` were not supplied.

The fixture suite now has eight tests. The new tests verify unavailable-row
serialization and guard-column persistence for computed rows. The existing
tests continue to cover volume, bidirectional exchange flux, residence time,
thermal weighting, missing viscosity status, and pressure/energy residual
failure modes.

## Inferred

The sampler interface is now ready to be called by a separate execution row,
but the source-field audit shows that production extraction is still blocked by
missing generated inputs. The correct next work package is therefore input
generation or execution preflight, not fitting or scorecard release.

## Contradictions Or Caveats

The implementation package reuses the design sampler's generated README and
summary, so those files still name the original design task. The current-task
record is `IMPLEMENTATION_NOTE.md`, `implementation_summary.json`, this
journal, the status file, and the import manifest. The dry fail-closed row is
not a production result and should not be interpreted as a zero exchange flow.

## Next Useful Actions

1. Claim a narrow input-generation row for `cellVolume`, `recircMask`,
   exchange-interface VTK, wall/core surface VTK, and source/sink ledgers.
2. If OpenFOAM surface generation or large field sampling is required, submit
   that work through Slurm with a background handoff rather than running it
   unbounded in the foreground.
3. Run the sampler against ready VTK inputs and check row counts, finite
   `V_recirc`, finite `mdot_exchange`, and explicit pressure/energy residual
   statuses.
4. Pair same-QOI UQ before Phase 4B rescore.
