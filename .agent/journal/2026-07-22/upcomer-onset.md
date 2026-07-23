---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_upcomer_onset/README.md
  - work_products/2026-07/2026-07-22/2026-07-22_upcomer_onset/upcomer_onset_regime_table.csv
tags: [upcomer, onset, recirculation, diagnostic-only]
related:
  - TODO-UPCOMER-ONSET
task: TODO-UPCOMER-ONSET
date: 2026-07-22
role: Writer/Implementer/Tester
type: journal
status: complete
---
# Upcomer Onset

## Attempted

Validated the current upcomer onset regime package and its task-owned test.

## Observed

The package has `3` mainline Salt2/Salt3/Salt4 rows and all remain
`recirculation_cell_observed`. It carries current UQ context but no formal
mesh/GCI or exchange-coefficient release.

## Inferred

The upcomer still requires a hybrid throughflow plus recirculation-cell lane.
Current evidence supports a diagnostic/onset narrative, not ordinary pipe
`Nu`, `f_D`, `K`, or exchange-cell coefficient admission.

## Next Actions

Add designed CFD points near the inferred onset band, especially around Re 150,
200, and 250, before fitting or admitting an onset threshold.

## Caveats

No scheduler action, Fluid edit, protected scoring, source/property release,
coefficient admission, final score, or internal-`Nu` residual absorption
occurred.
