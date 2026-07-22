---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_extbc_source_sink_provenance_recovery/setup_source_sink_provenance_ledger.csv
tags: [journal, external-bc, source-sink, provenance]
related:
  - .agent/status/2026-07-21_TODO-EXTBC-SOURCE-SINK-PROVENANCE-RECOVERY-2026-07-21.md
  - imports/2026-07-21_extbc_source_sink_provenance_recovery.json
task: TODO-EXTBC-SOURCE-SINK-PROVENANCE-RECOVERY-2026-07-21
date: 2026-07-21
role: Forward-pred / Thermal-modeling / Writer / Reviewer
type: journal
status: complete
---
# External-BC Source/Sink Provenance Recovery

Observed: Phase I had classified heater/cooler/test-section source/sink rows as
forbidden when their available basis was realized CFD `wallHeatFlux`.

Observed: staged `0/T` setup files contain explicit setup-side `Q` values for
lower-leg heater segments, the cooler, and the test section for Salt1-Salt4.

Inferred: the provenance basis can move from realized-CFD-only to
setup-known-candidate for these source/sink families. Runtime admission still
cannot move because Fluid/source-model and source/property gates have not
released these source rows.

Caveat: Salt3/Salt4 remain protected split rows for provenance only. No
validation/holdout score or tuning is allowed from this package.

Next useful action: implement a separate deterministic Fluid source-lane API
for Salt1/Salt2 train-only heater/test-section/cooler source rows, then rerun
train residual ownership before any freeze/admission row.
