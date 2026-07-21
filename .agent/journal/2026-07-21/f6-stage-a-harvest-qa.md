---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_f6_stage_a_harvest_qa/endpoint_face_qa.csv
  - work_products/2026-07/2026-07-21/2026-07-21_f6_stage_a_harvest_qa/endpoint_pair_qa.csv
  - work_products/2026-07/2026-07-21/2026-07-21_f6_stage_a_harvest_qa/summary.json
tags: [f6, endpoint-sampler, harvest-qa, raw-face, no-admission]
related:
  - .agent/status/2026-07-21_TODO-F6-STAGE-A-HARVEST-QA.md
  - imports/2026-07-21_f6_stage_a_harvest_qa.json
task: TODO-F6-STAGE-A-HARVEST-QA
date: 2026-07-21
role: cfd-pp / Hydraulics / Tester / Writer
type: journal
status: complete
---

# F6 Stage A Harvest QA

## Attempted

I built a reproducible QA package for the Stage A F6 endpoint raw-face harvest.
The builder reads the harvested raw metrics and Stage A matrix, checks expected
surface presence, finite required fields, face/area validity, RAF/RMF/SVF, and
medium/fine pair consistency, then emits face-level, pair-level, gate-level, and
mesh-diagnostic tables.

## Observed

The first builder run failed because the script resolved the repo root one
directory too high. I corrected the parent-path calculation and reran the
builder and tests successfully.

After repair, all eight endpoint faces had present VTK files and finite
required metrics. Every endpoint pair failed ordinary-flow criteria:

- right-leg medium/fine max RAF is about `0.383-0.385`, max RMF about `0.500`.
- test-section medium/fine max RAF is about `0.634-0.636`, max RMF about `0.500`.

The resulting pair labels are `recirc_diagnostic` for all four pair/mesh rows.

## Inferred

The sampler is now working, but the selected Stage A F6 endpoint pairs are not
ordinary single-stream evidence. The raw faces show material reverse-flow
content, so the evidence is useful diagnostically but not admissible for F6 or
component K.

Medium/fine gross static pressure deltas are numerically close for each branch,
but that does not create GCI-quality evidence because the coarse family remains
blocked and the ordinary-flow gate fails.

## Contradictions Or Caveats

No orientation failure is asserted here. The safer interpretation is
recirculation diagnostic because RAF/RMF are material; an orientation-only
failure would require low reverse-flow fractions with coherent opposite signed
flux, which is not the current evidence pattern.

## Next Useful Actions

Run `TODO-F6-COARSE-PATH-UQ-REPAIR` to repair or formally close the twelve
blocked coarse endpoint rows. Then use `TODO-F6-SAME-QOI-UQ-AND-ADMISSION-GATE`
to keep all current Stage A rows diagnostic unless ordinary-flow and same-QOI
evidence can be supplied.
