---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_heatloss_upcomer_exchange_evidence_extraction/sampler_field_map.csv
  - work_products/2026-07/2026-07-21/2026-07-21_heatloss_upcomer_exchange_evidence_extraction/case_time_window_queue.csv
  - tools/extract/sample_upcomer_convection_cell.py
  - work_products/2026-07/2026-07-21/2026-07-21_heatloss_upcomer_sampler_design/README.md
tags: [journal, heat-loss, upcomer, sampler-design, exchange-cell]
related:
  - .agent/status/2026-07-21_TODO-HEATLOSS-UPCOMER-SAMPLER-DESIGN.md
  - imports/2026-07-21_heatloss_upcomer_sampler_design.json
task: TODO-HEATLOSS-UPCOMER-SAMPLER-DESIGN
date: 2026-07-21
role: Implementer/Tester/Writer/Thermal-modeling/Hydraulics
type: journal
status: complete
supersedes: []
superseded_by:
---
# Heat-Loss Upcomer Sampler Design

## Attempted

Implemented the design-only Phase 1 package for the upcomer exchange-state
sampler. The work translated the prior heat-loss extraction contract into
explicit sampler output fields, algorithm stages, dry-run emission expectations,
future extractor change IDs, execution preflight cases, and validation cases.

## Observed

The current `tools/extract/sample_upcomer_convection_cell.py` supports
upcomer plane-based reverse-flow/nondimensional metrics. The completed
heat-loss extraction contract identifies the missing exchange-state fields:
`V_recirc`, `mdot_exchange`, `tau_recirc`, paired `T_main`/`T_recirc`,
wall-core Delta T, pressure residual, energy residual, and same-QOI UQ hooks.
The mainline execution windows remain salt 2 at `7915` s, salt 3 at `7618` s,
and salt 4 at `10000` s.

## Inferred

The next useful implementation should first extend the extractor interface and
dry-run/schema behavior before compute-node execution. This avoids spending
scheduler time before the output contract, missing-field behavior, and residual
guardrails are testable. Residual terms must remain diagnostic and cannot be
converted into internal Nu.

## Contradictions Or Caveats

This package does not prove that the recirculation mask or exchange interface
can be recovered from the available case fields. It defines the required
fields, methods, and fail-closed outputs. The next implementation row must
verify actual source-field availability against the selected case directories.

## Next Useful Actions

1. Claim an extractor implementation row for
   `tools/extract/sample_upcomer_convection_cell.py`.
2. Add schema/dry-run mode, output headers, missing-field status behavior, and
   no-admission guard columns before adding heavy OpenFOAM paths.
3. Claim a separate compute-node execution row after implementation tests pass.
4. Pair same-QOI UQ after extracted QOI rows exist, then run Phase 4B rescore.

## Guardrails

No native CFD/OpenFOAM outputs, registry/admission state, scheduler state,
Fluid source, external repo files, `tools/extract`, staged-copy/postprocessing
jobs, fitting/tuning/model selection, blocker register, generated docs index,
or scientific admission state were changed.
