---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_thermal_passive_h2_multi_train_corrected_radiation_smoke/README.md
  - work_products/2026-07/2026-07-22/2026-07-22_thermal_passive_h2_multi_train_corrected_radiation_smoke/split_scope_audit.csv
  - work_products/2026-07/2026-07-22/2026-07-22_thermal_passive_h2_radiation_runtime_basis_reconciliation/README.md
  - work_products/2026-07/2026-07-22/2026-07-22_thermal_passive_h2_source_backed_basis_table/README.md
tags: [work-product, thesis, fail-closed, evidence-packet]
related:
  - .agent/status/2026-07-22_TODO-PASSIVE-H2-EXTBC-SPLIT-CONFLICT-RESOLUTION-2026-07-22.md
  - .agent/journal/2026-07-22/passive-h2-extbc-split-conflict-resolution-2026-07-22.md
task: TODO-PASSIVE-H2-EXTBC-SPLIT-CONFLICT-RESOLUTION-2026-07-22
date: 2026-07-22
role: Writer/Reviewer/Tester
type: work_product
status: complete
---
# PASSIVE-H2 External-BC Split Conflict Resolution

Decision: `passive_h2_extbc_split_conflicts_resolved_fail_closed_train_context_only`.

- Salt3 and Salt4 retain split conflicts and are train-context diagnostics only.
- Salt2 is split-consistent but still not an admitted candidate by this row.
- PASSIVE-H2-CAND001 may only proceed to future preflight if split scope is narrowed and no numeric q-loss is released here.

Guardrails preserved: no global hA multiplier, no realized wallHeatFlux runtime use, no numeric q-loss release, no protected scoring, no fitting/model selection, no repair/freeze execution.
