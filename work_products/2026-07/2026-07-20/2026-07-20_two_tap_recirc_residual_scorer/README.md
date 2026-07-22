---
provenance:
  - work_products/2026-07/2026-07-18/2026-07-18_two_tap_staged_endpoint_sampler/raw_endpoint_pressure_velocity.csv
  - work_products/2026-07/2026-07-18/2026-07-18_two_tap_pressure_basis_recirc_audit/pressure_velocity_basis_audit.csv
  - work_products/2026-07/2026-07-20/2026-07-20_two_tap_recirc_section_effective_model/section_effective_model_contract.csv
tags: [pressure-ledger, two-tap, recirculation, residual-scorer, lower-apparent-k]
related:
  - .agent/status/2026-07-20_TODO-TWO-TAP-RECIRC-RESIDUAL-SCORER.md
  - .agent/journal/2026-07-20/two-tap-recirc-residual-scorer.md
task: TODO-TWO-TAP-RECIRC-RESIDUAL-SCORER
date: 2026-07-20
role: Hydraulics/cfd-pp/Writer
type: work_product
status: complete
---
# Two-Tap Recirculating Residual Scorer

Generated: `2026-07-20T16:48:34+00:00`

## Decision

The lower apparent `K` trend in current `corner_lower_right` rows is explained
as diagnostic evidence, not coefficient admission. Static apparent `K` remains
hydrostatic/buoyancy dominated, throughflow `q_ref` is untrusted until a
single-leg orientation audit passes, and current rows remain section-effective
diagnostics only.

## Outputs

- `q_ref_orientation_audit.csv`
- `lower_apparent_k_diagnosis.csv`
- `recirc_residual_scorecard.csv`
- `model_hypothesis_matrix.csv`
- `next_extraction_contract.csv`
- `paper_diagnostic_note.md`
- `source_manifest.csv`
- `summary.json`

## Counts

- Current pressure pairs: `3`.
- Endpoint q-ref audit rows: `6`.
- Rows with component K admitted: `0`.
- Rows with F6 fit performed: `0`.

## Guardrails

No scheduler work, native CFD/OpenFOAM mutation, registry/admission mutation,
Fluid edit, solver/postprocessing launch, F6 fit, component-K admission, hidden
global multiplier, clipped K, or endpoint-pressure invention was performed.
