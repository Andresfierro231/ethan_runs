---
provenance:
  - .agent/BOARD.md
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_study_s14_pressure_f6_nonrecirc_anchor_evidence/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_study_s9_upcomer_onset_anchor_exchange_uq/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_geometry_release/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_sampler_reusable_harvest_scaffold/README.md
tags: [coordination, s13, s14, upcomer, exchange-cell, board-hygiene]
related:
  - .agent/status/2026-07-21_AGENT-579.md
  - .agent/journal/2026-07-21/s14-hygiene-and-s13-prereq-dispatch.md
  - imports/2026-07-21_s14_hygiene_and_s13_prereq_dispatch.json
task: AGENT-579
date: 2026-07-21
role: Coordinator/Cleaner/Writer
type: operational_note
status: complete
---
# S14 Hygiene And S13 Prerequisite Dispatch

## Meaning Of S14 Board Hygiene

Closing out S14 board hygiene means removing
`TODO-THESIS-STUDY-S14-PRESSURE-F6-NONRECIRC-ANCHOR-EVIDENCE-2026-07-21`
from Active after it passed `finish_task.py`.

It does not mean pressure/F6 science was reopened. The S14 result remains a
completed diagnostic/negative branch-use package: `0` admitted rows, no
component K, no F6 fit, no clipped K, no hidden multiplier, and no S11 trigger.

## Open First

1. `.agent/BOARD.md`
2. `work_products/2026-07/2026-07-21/2026-07-21_thesis_study_s9_upcomer_onset_anchor_exchange_uq/README.md`
3. `work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_geometry_release/README.md`
4. `work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_input_generation/README.md`
5. `work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_surface_source_generation/README.md`
6. `work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_sampler_reusable_harvest_scaffold/README.md`

## S13 Prerequisite Rows Added

| Row | Purpose |
| --- | --- |
| `TODO-S13-UPCOMER-EXCHANGE-GEOMETRY-CONTRACT-2026-07-21` | Define or fail-close the trusted exchange-interface and wall/core recirculation-band geometry contract. |
| `TODO-S13-UPCOMER-EXCHANGE-SURFACE-VTK-EXTRACTION-2026-07-21` | After geometry and Salt3/Salt4 cell VTKs exist, extract same-window interface and wall/core VTK inputs. |
| `TODO-S13-UPCOMER-EXCHANGE-SAMPLER-MANIFEST-PREFLIGHT-2026-07-21` | Assemble the populated exchange-case matrix and run scaffold validators before any harvest. |
| `TODO-S13-UPCOMER-EXCHANGE-SAME-WINDOW-UQ-DESIGN-2026-07-21` | Define time/mesh/UQ acceptance for exchange QOIs before production harvest. |

## Suggested Task Order

1. Finish or monitor `TODO-UPCOMER-EXCHANGE-CELL-VTK-SALT3-SALT4-MATRIX-2026-07-21`.
2. Claim the S13 geometry-contract row.
3. Claim the S13 same-window UQ design row in parallel with geometry if a writer/reviewer is available.
4. Claim the S13 surface/VTK extraction row only after geometry and cell VTKs are ready.
5. Claim the S13 sampler-manifest preflight row after surface inputs exist or are explicitly fail-closed.
6. Claim the main S13 production harvest/UQ row only after the manifest and UQ design give a clear run/fail-close decision.

## Guardrails

Do not use these enabling rows to admit ordinary upcomer `Nu`, `f_D`, or `K`.
Do not admit exchange-cell coefficients without same-window UQ. Do not launch
samplers from the geometry or UQ design rows. Do not mutate native solver
outputs, registry/admission state, Fluid source, blocker register, generated
docs indexes, or external repositories.
