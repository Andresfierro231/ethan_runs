---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_limited_sampled_field_evidence_synthesis/README.md
  - work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_limited_sampled_field_evidence_synthesis/thesis_insert_package.md
tags: [s13, upcomer-exchange, thesis-handoff, fail-closed]
related:
  - .agent/status/2026-07-22_TODO-S13-UPCOMER-EXCHANGE-LIMITED-SAMPLED-FIELD-EVIDENCE-SYNTHESIS-2026-07-22.md
  - .agent/journal/2026-07-22/s13-upcomer-exchange-limited-sampled-field-evidence-synthesis.md
task: TODO-S13-UPCOMER-EXCHANGE-LIMITED-SAMPLED-FIELD-EVIDENCE-SYNTHESIS-2026-07-22
date: 2026-07-22
role: Writer / Reviewer
type: operational_note
status: complete
---
# Start Here: S13 Limited Sampled-Field Evidence Synthesis

## Why This Exists

The limited S13 sampled-field extraction is now strong enough for thesis analysis but still blocked for production harvest. This note points the next agent to the exact package and the remaining unlock sequence.

## Open First

1. `work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_limited_sampled_field_evidence_synthesis/README.md`
2. `work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_limited_sampled_field_evidence_synthesis/thesis_insert_package.md`
3. `work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_limited_sampled_field_evidence_synthesis/s13_next_unblock_queue.csv`

## Trusted Packages

- Limited sampled-field extraction:
  `work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_limited_sampled_field_scheduler_extraction/`
- Average-field thermal reduction:
  `work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_average_field_thermal_reduction/`
- Qwall contract:
  `work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_sampled_field_qwall_contract_from_seeded_vtk/`
- Qwall/UQ unblock gate:
  `work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_sampled_field_qwall_uq_unblock/`

## Active Board Rows To Respect

- `TODO-S13-UPCOMER-EXCHANGE-EXACT-PRESSURE-QWALL-COMPUTE-2026-07-21` owns exact pressure and trusted-wall heat-flow compute.
- `TODO-HYBRID-PRESSURE-NO-FIT-PERFORMANCE-BAKEOFF-2026-07-21` owns pressure no-fit bakeoff files.
- `TODO-S8-S12-THERMAL-RESIDUAL-OWNERSHIP-GATE-2026-07-21` owns thermal residual ownership files.
- Active thesis Ch. 6/7 rows own current thesis body edits.

## Next Task Sequence

1. Wait for or consume the exact pressure/Qwall compute closeout.
2. If exact `Q_wall_W` remains unavailable, claim a source-side heat-flow QOI contract row.
3. Run same-QOI neighbor-window and mesh/GCI UQ only after exact QOI labels, formulas, signs, and bases are fixed.
4. Use the thesis insert package as chapter material once thesis-file ownership is clear.

## Output Contract

The S13 synthesis package is allowed to support diagnostic thesis claims and negative-result framing. It is not allowed to release production harvest, source/property labels, a coefficient, a freeze, or a final predictive score.

## Do Not Do

- Do not relabel source-side `q_net_W` as `Q_wall_W`.
- Do not use these rows to trigger S11/S12/S13/S15/S6.
- Do not score validation, holdout, or external-test rows from this package.
- Do not absorb the residual into internal Nu.
