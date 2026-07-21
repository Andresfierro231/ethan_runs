---
provenance:
  - work_products/2026-07/2026-07-13/2026-07-13_predictive_forward_v0_imposed_cooler/forward_v0_results.csv
  - work_products/2026-07/2026-07-13/2026-07-13_predictive_h1_proxy_rerun/h1_proxy_k_source.csv
  - work_products/2026-07/2026-07-14/2026-07-14_fluid_localized_h1_and_boundary_api/README.md
  - work_products/2026-07/2026-07-14/2026-07-14_localized_fixed_k_forward_score/README.md
tags: [journal, forward-model, hydraulics, localized-fixed-k, rigor-gate]
related:
  - .agent/status/2026-07-14_AGENT-328.md
  - imports/2026-07-14_localized_fixed_k_forward_score.json
task: AGENT-328
date: 2026-07-14
role: Implementer/Tester/Writer
type: journal
status: complete
---
# Localized Fixed-K Forward Score

## Objective

Execute the next hydraulic gate packet by scoring Salt2 train / Salt3
validation / Salt4 holdout with Fluid's existing
`localized_fixed_k_by_segment` hook.

## Method

- Consumed Salt2 train finite `K_local` rows from the prior H1 proxy source
  table.
- Applied three localized keys: `lower_leg`, `right_leg`, and `upper_leg`.
- Compared against the existing forward-v0 baseline rows.
- Preserved the locked split: `salt_2=train`, `salt_3=validation`,
  `salt_4=holdout`.
- Used no thermal fitting, no CFD mdot runtime input, no realized CFD
  `wallHeatFlux` runtime input, and no validation-temperature runtime input.

## Result

The localized-only score is negative evidence:

- `F0_current_fluid_sources`: mean mdot error worsened from
  `0.0080817 kg/s` to `0.0089150 kg/s`.
- `F1_heater_only`: mean mdot error worsened from `0.0054775 kg/s` to
  `0.0058942 kg/s`.
- All localized rows still overpredict CFD mdot.
- Both variants fail the directional screen.

This means the previous aggregate H1 proxy improvement should not be promoted
as a final localized closure. The current Fluid hook is useful, but
localized-only fixed K is insufficient without reset/redevelopment semantics
and setup-only boundary/HX support.

## Rigor Gate Outcome

- R1 provenance: pass.
- R2 no native CFD mutation: pass.
- R5 predictive input discipline: pass.
- R6 locked split: pass.
- R8 no global hydraulic fudge: pass.
- Final forward-v1 admission: blocked.

## Files Created

- `tools/analyze/build_localized_fixed_k_forward_score.py`
- `tools/analyze/test_localized_fixed_k_forward_score.py`
- `work_products/2026-07/2026-07-14/2026-07-14_localized_fixed_k_forward_score/README.md`
- `work_products/2026-07/2026-07-14/2026-07-14_localized_fixed_k_forward_score/localized_fixed_k_source.csv`
- `work_products/2026-07/2026-07-14/2026-07-14_localized_fixed_k_forward_score/localized_fixed_k_scorecard.csv`
- `work_products/2026-07/2026-07-14/2026-07-14_localized_fixed_k_forward_score/localized_fixed_k_variant_summary.csv`
- `work_products/2026-07/2026-07-14/2026-07-14_localized_fixed_k_forward_score/rigor_gate_audit.csv`
- `work_products/2026-07/2026-07-14/2026-07-14_localized_fixed_k_forward_score/source_manifest.csv`
- `work_products/2026-07/2026-07-14/2026-07-14_localized_fixed_k_forward_score/summary.json`

## Next Action

Do not spend more effort on localized-only fixed K as a gate unlock. The next
hydraulic path needs reset/redevelopment semantics or a different bounded
candidate, while the boundary lane needs setup-only HX/wall/radiation inputs.
