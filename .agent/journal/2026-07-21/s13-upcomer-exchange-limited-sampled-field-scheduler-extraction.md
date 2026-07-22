---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_limited_sampled_field_scheduler_extraction/sampled_field_summary.csv
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_limited_sampled_field_scheduler_extraction/sampled_interface_fields.csv
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_limited_sampled_field_scheduler_extraction/sampled_wall_core_temperature.csv
tags: [journal, s13, upcomer-exchange, limited-sampled-field, scheduler]
related:
  - .agent/status/2026-07-21_TODO-S13-UPCOMER-EXCHANGE-LIMITED-SAMPLED-FIELD-SCHEDULER-EXTRACTION-2026-07-21.md
  - imports/2026-07-21_s13_upcomer_exchange_limited_sampled_field_scheduler_extraction.json
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_limited_sampled_field_scheduler_extraction/README.md
task: TODO-S13-UPCOMER-EXCHANGE-LIMITED-SAMPLED-FIELD-SCHEDULER-EXTRACTION-2026-07-21
date: 2026-07-21
role: Hydraulics / Thermal-modeling / cfd-pp / Scheduler / Implementer / Tester / Writer
type: journal
status: complete
---
# S13 Limited Sampled-Field Scheduler Extraction

Observed: the sampled-field/Qwall contract opened only the limited field
extraction lane. It did not open `Q_wall_W`, production sampler harvest,
same-QOI UQ, fitting, or admission.

Attempted: used the task-owned scheduler row to extract interface `U/T/rho` and
trusted wall-owner `T` from existing whole-mesh cell VTKs and released seeded
geometry. A submitted batch job `3308952` was canceled before execution with no
node assigned. The extraction step `3307325.0` completed with exit `0:0` on
`c318-008`.

Observed: all three cases produced summary rows. The detailed tables contain
`116640` interface rows and `116640` wall/core temperature rows. The headline
summary preserves the same exchange mass-flow proxy values as the diagnostic
average row and adds wall-owner temperature context for trusted wall faces.

Observed: every production gate remains closed: `Q_wall_W_released=false`,
`sampler_ready=false`, `production_harvest_allowed=false`,
`same_qoi_uq_ready=false`, and `admission_allowed=false` for Salt2/Salt3/Salt4.

Inferred: S13 now has stronger finite diagnostic field evidence than the
average-only proxy, but not the wall-heat or production-QOI support needed for
coefficient admission or S11/S15/S6 triggers.

Caveat: `wall_owner_T_K` is the owner-cell temperature adjacent to trusted wall
faces. It is not wallHeatFlux, not an integrated `Q_wall_W`, and not a thermal
coefficient.

Next useful action: build a post-extraction production gate that compares the
new limited sampled fields against the prior proxy manifest and decides the
smallest remaining compute/source step for `Q_wall_W` or a clearly documented
source-side equivalent plus same-QOI UQ.
