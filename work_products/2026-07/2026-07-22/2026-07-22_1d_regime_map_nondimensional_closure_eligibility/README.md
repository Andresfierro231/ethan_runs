---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_gated_single_stream_developing_branch/single_stream_developing_branch_gate.csv
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_model_form_extraction/litrev_source_inventory.csv
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_model_form_extraction/model_form_candidates.csv
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_throughflow_recirc_exchange_cell/README.md
tags: [predictive-1d, regime-map, nondimensional, closure-eligibility, no-admission]
related:
  - .agent/status/2026-07-22_TODO-1D-REGIME-MAP-NONDIMENSIONAL-CLOSURE-ELIGIBILITY-2026-07-22.md
  - .agent/journal/2026-07-22/1d-regime-map-nondimensional-closure-eligibility.md
  - imports/2026-07-22_1d_regime_map_nondimensional_closure_eligibility.json
task: TODO-1D-REGIME-MAP-NONDIMENSIONAL-CLOSURE-ELIGIBILITY-2026-07-22
date: 2026-07-22
role: Forward-pred / Hydraulics / Thermal-modeling / LitRev / Writer / Reviewer
type: work_product
status: complete
---
# 1D Regime Map And Nondimensional Closure Eligibility

Generated: `2026-07-22T15:16:52.597295+00:00`

Decision: `regime_map_ready_fail_closed_no_closure_admission`.

This package builds the case/span nondimensional regime map from existing
LitRev and diagnostic gate artifacts. It is a closure-eligibility and
source-overlap packet, not a coefficient admission.

## Main Finding

All closure families fail closed for fitting. Ordinary single-stream developing
forms are at most precheck-only where recirculation is not directly flagged, and
many spans are blocked by recirculation evidence. Throughflow-plus-recirculation
exchange remains the preferred architecture for persistent local exchange, but
it is diagnostic only until same-label mesh/GCI and source/property gates pass.

## Files

- `formula_validity_table.csv`: 8 formula/provenance rows.
- `segment_case_regime_map.csv`: 18 case/span regime rows.
- `tamu_overlap_matrix.csv`: 7 source-overlap rows.
- `closure_eligibility_decisions.csv`: 5 fail-closed model-family decisions.
- `figures/svg/regime_eligibility_map.svg`: compact map for publication planning.
- `source_manifest.csv`, `no_mutation_guardrails.csv`, `summary.json`.

## Scientific Use

Use this to justify why the 1D model ladder should not admit ordinary
single-stream `Nu`, `f_D`, component `K`, or F6 coefficients from current
evidence. It supports model-form selection and next-study design only.

## Guardrails

No native CFD output, scheduler job, Fluid/external repository, registry,
admission state, blocker register, fit, model selection, source/property
release, or coefficient admission was changed.
