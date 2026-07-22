---
task: TODO-HEATLOSS-UPCOMER-SOURCE-FIELD-AUDIT
date: 2026-07-21
role: Thermal-modeling / Hydraulics / cfd-pp / Implementer / Tester / Writer
type: work_product
status: complete
tags: [heat-loss, upcomer, source-field-audit, exchange-cell, no-solver]
related:
  - work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_sampler_design
  - work_products/2026-07/2026-07-21/2026-07-21_heatloss_upcomer_sampler_design
  - work_products/2026-07/2026-07-21/2026-07-21_heatloss_upcomer_exchange_evidence_extraction
---
# Heat-Loss Upcomer Source-Field Audit

This package audits whether the three queued mainline upcomer exchange windows
are ready for production extraction. It is a lightweight compute-node audit and
does not launch OpenFOAM or a sampler.

## Decision

- Case windows audited: `3`
- Required field/artifact rows: `45`
- Blocker rows: `18`
- Primary native fields ready: `true`
- Production exchange extraction ready: `false`
- Scheduler action taken: `false`

The three target time directories contain the primary same-window native fields
needed for a future extraction design (`U`, `T`, `p`, `p_rgh`, `rho`, `phi`, and
diagnostic wall heat output). They do not already contain the exchange-cell
products needed for direct production extraction: direct `mu`, generated
`cellVolume`, `recircMask`, named exchange-interface surfaces, confirmed
wall/core surface products, and same-window source/sink ledgers remain blockers.

## Outputs

- `case_window_source_audit.csv`: case/time path readiness.
- `required_field_availability.csv`: per-case field/artifact availability.
- `missing_field_blockers.csv`: blocker rows that prevent direct extraction.
- `extraction_readiness_decision.csv`: per-case launch/no-launch decision.
- `sbatch_recommendation.csv`: under-5-minute vs Slurm routing.
- `source_manifest.csv`: read-only provenance.

## Guardrails

No native CFD/OpenFOAM outputs, case directories, registry/admission state,
scheduler state, Fluid source, external repositories, `tools/extract`,
generated indexes, or blocker register were mutated. No solver, postprocessor,
sampler, fitting, model selection, closure admission, Phase 4B rescore, or
scorecard trigger was run. Heat residual remains separate from internal Nu.
