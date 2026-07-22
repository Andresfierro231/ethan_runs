---
provenance:
  generated_by: tools/analyze/build_mf_recirc_upcomer_alternatives_gate.py
  task_id: TODO-MF-RECIRCULATING-UPCOMER-ALTERNATIVES-GATE-2026-07-22
  generated_at_utc: 2026-07-22T14:17:27.579688+00:00
task: TODO-MF-RECIRCULATING-UPCOMER-ALTERNATIVES-GATE-2026-07-22
tags: [journal, recirculating-upcomer, alternatives-gate]
related:
  - work_products/2026-07/2026-07-22/2026-07-22_mf_recirc_upcomer_alternatives_gate
---
# Recirculating-upcomer alternatives gate

## Attempted

Synthesized the high-level upcomer alternatives after the detailed MF09/MF10
packages closed.

## Observed

MF09 identified throughflow-plus-recirculation exchange cell as the best science
lane but with 0 smoke-ready variants. MF10 carried only existing numeric context
and ran no new train/support scoring. The S13 mesh/GCI gate has 0 accepted
same-label QOIs, and onset data sparsity has 0 anchor candidates.

## Inferred

The recirculating upcomer should remain in a diagnostic exchange-cell lane, not
ordinary single-stream `Nu/f_D/K`. The next useful work is prerequisite release,
not fitting.

## Contradictions or Caveats

Direct `Q_wall_W` exists read-only, but source-side heat remains a separate lane
and cannot be relabeled as wall heat. Missing heat/energy residuals must remain
named residuals.

## Next Useful Actions

Finish same-label mesh-family generation, release source-property/cp basis, and
harvest same-window production exchange-cell fields before any train-only smoke.
