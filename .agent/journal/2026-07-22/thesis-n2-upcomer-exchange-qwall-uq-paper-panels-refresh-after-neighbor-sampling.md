---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_n2_upcomer_exchange_qwall_uq_paper_panels_refresh_after_neighbor_sampling/qwall_target_minus_time_drift_table.csv
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_n2_upcomer_exchange_qwall_uq_paper_panels_refresh_after_neighbor_sampling/same_qoi_neighbor_uq_blocker_table.csv
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_n2_upcomer_exchange_qwall_uq_paper_panels_refresh_after_neighbor_sampling/caption_bank.md
tags: [thesis, n2, s13, upcomer-exchange, qwall, panels]
related:
  - .agent/status/2026-07-22_TODO-THESIS-N2-UPCOMER-EXCHANGE-QWALL-UQ-PAPER-PANELS-REFRESH-AFTER-NEIGHBOR-SAMPLING-2026-07-22.md
  - imports/2026-07-22_thesis_n2_upcomer_exchange_qwall_uq_paper_panels_refresh_after_neighbor_sampling.json
task: TODO-THESIS-N2-UPCOMER-EXCHANGE-QWALL-UQ-PAPER-PANELS-REFRESH-AFTER-NEIGHBOR-SAMPLING-2026-07-22
date: 2026-07-22
role: Hydraulics / Thermal-modeling / cfd-pp / Figures / Tester / Writer / Reviewer
type: journal
status: complete
---
# N2 Qwall/UQ Panel Refresh After Neighbor Sampling

## Attempted

Built an addendum package for the completed N2 upcomer exchange/Qwall/UQ thesis
panel package so the new S13 target-minus sampling result can be cited without
editing thesis current files.

## Observed

The prior N2 package remains valid as a diagnostic package. The new target-minus
sampling package adds `12` sampled target-minus rows across four QOIs and three
cases, including `3` direct `Q_wall_W` target-minus rows. It still has `0`
target-plus rows and `0` same-QOI UQ-ready labels.

For `Q_wall_W`, the target-minus to target deltas are:
Salt2 `6.64561e-05 W`, Salt3 `1.4179e-05 W`, and Salt4 `0.0010252426 W`.

## Inferred

The strongest thesis-safe S13/N2 figure now shows both the encouraging
one-sided stability and the decisive target-plus blocker. This is a better
negative result than the previous inventory-only statement, but it is still not
production evidence.

## Caveats

No solver, sampler, UQ, harvest, admission, fitting, thesis edit, registry edit,
source/property release, or native-output mutation occurred. The addendum does
not make a closure or coefficient claim.

## Next Useful Actions

Generate or locate later target-plus windows. If those exist, rerun same-QOI
neighbor UQ and then consider mesh/GCI UQ. If they do not, use this panel
package as the thesis/paper fail-closed evidence for why S13 remains diagnostic.
