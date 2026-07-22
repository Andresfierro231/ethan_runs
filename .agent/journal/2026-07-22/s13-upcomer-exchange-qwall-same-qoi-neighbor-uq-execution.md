---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_qwall_same_qoi_neighbor_uq_execution/neighbor_window_inventory.csv
  - work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_qwall_same_qoi_neighbor_uq_execution/same_qoi_uq_matrix.csv
  - work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_qwall_same_qoi_neighbor_uq_execution/clean_fail_closed_thesis_result.md
tags: [s13, upcomer-exchange, qwall, same-qoi-uq, fail-closed]
related:
  - .agent/status/2026-07-22_TODO-S13-UPCOMER-EXCHANGE-QWALL-SAME-QOI-NEIGHBOR-UQ-EXECUTION-2026-07-22.md
  - imports/2026-07-22_s13_upcomer_exchange_qwall_same_qoi_neighbor_uq_execution.json
task: TODO-S13-UPCOMER-EXCHANGE-QWALL-SAME-QOI-NEIGHBOR-UQ-EXECUTION-2026-07-22
date: 2026-07-22
role: Hydraulics / Thermal-modeling / cfd-pp / Implementer / Tester / Writer / Reviewer
type: journal
status: complete
---
# S13 Qwall Same-QOI Neighbor UQ Execution

## Attempted

Built a narrow, evidence-only same-QOI neighbor-window package for four S13 QOI
labels: direct `Q_wall_W`, positive exchange `mdot` proxy, `tau_recirc` proxy,
and wall/core/bulk thermal contrast.

## Observed

Target-window evidence exists for all four labels across Salt2, Salt3, and
Salt4. Direct trusted-wall `Q_wall_W` is available from the exact-Qwall package.
The `mdot`, `tau`, and thermal-contrast labels are retained-window diagnostic
proxy evidence from the limited sampled-field and average-field packages.

No exact same-label target-minus or target-plus rows were found for any of the
four labels. The generated matrix reports `12` target rows, `0` target-minus
rows, `0` target-plus rows, and `0` same-QOI neighbor UQ-ready labels.

## Inferred

S13 cannot move to mesh/GCI UQ yet. The first missing scientific input is exact
neighboring-window evidence for the same labels/formulas/sign conventions. The
right thesis result is fail-closed: target-window exchange and heat-flow
evidence is real and useful diagnostically, but it does not support production
harvest or coefficient admission.

## Caveats

This row did not sample native case directories, run a scheduler job, execute
UQ, run production harvest, admit coefficients, edit thesis current files, or
mutate any registry/admission state. It consumes prior `Q_wall_W` output
read-only and does not re-release it.

## Next Useful Actions

Generate or locate exact same-label target-minus and target-plus values for the
four S13 QOI labels. If those appear, claim a separate mesh/GCI UQ gate. Only
after both gates pass should a production harvest row be considered.
