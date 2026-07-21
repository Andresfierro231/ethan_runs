---
provenance:
  - work_products/2026-07/2026-07-17/2026-07-17_upcomer_hybrid_frozen_candidate_score/README.md
  - work_products/2026-07/2026-07-17/2026-07-17_upcomer_hybrid_frozen_candidate_score/summary.json
tags: [status, upcomer, hybrid-model]
related:
  - .agent/journal/2026-07-17/upcomer-hybrid-frozen-candidate-score.md
  - imports/2026-07-17_upcomer_hybrid_frozen_candidate_score.json
task: TODO-UPCOMER-HYBRID-FROZEN-CANDIDATE-SCORE
date: 2026-07-17
role: Hydraulics/Thermal-modeling/Forward-pred/Implementer/Tester/Writer
type: status
status: complete
---
# TODO-UPCOMER-HYBRID-FROZEN-CANDIDATE-SCORE Status

## Observed Facts

- A frozen hybrid candidate can be specified from existing feature and model-form evidence.
- It cannot be admitted because onset anchors are design-only and split-safe scores are not run.
- Ordinary `Nu`, `f_D`, and `K` labels remain forbidden for current recirculating rows.

## Validation

- `python3 -m unittest tools.analyze.test_upcomer_hybrid_frozen_candidate_score`
- Parsed generated `summary.json` and import manifest with `python3 -m json.tool`.
