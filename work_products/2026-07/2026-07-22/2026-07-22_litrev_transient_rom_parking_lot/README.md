# LitRev Transient/ROM Parking Lot

Decision: `mf05_mf06_parked_future_only_no_implementation`.

This package parks MF-05 and MF-06 as future-only lanes. It adds no code and
does not touch native CFD outputs, scheduler state, registry/admission state,
Fluid, external repositories, fitting/tuning, or generated docs index files.

## Trigger Conditions

- MF-05: reopen only with repeatable positive-mean periodic pressure/flow
  evidence, unchanged topology, no zero crossing, and source-range overlap.
- MF-06: reopen only with a verified FOM snapshot ensemble, retained-mode or
  energy criterion, conservation checks, extrapolation detector, and held-out
  validation.

## Outputs

- `parking_lot_trigger_table.csv`
- `parking_lot_note.md`
- `source_manifest.csv`
- `no_mutation_guardrails.csv`
- `summary.json`
