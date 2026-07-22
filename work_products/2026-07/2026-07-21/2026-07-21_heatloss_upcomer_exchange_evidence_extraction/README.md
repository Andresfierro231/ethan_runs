---
task: TODO-HEATLOSS-UPCOMER-EXCHANGE-EVIDENCE-EXTRACTION
date: 2026-07-21
role: Thermal-modeling / Implementer / Tester / Writer
type: work_product
status: complete
tags: [heat-loss, upcomer, recirculation, exchange-cell, evidence-contract]
related:
  - work_products/2026-07/2026-07-21/2026-07-21_heatloss_phase_4_upcomer_exchange_and_internal_nu_gate
  - work_products/2026-07/2026-07-21/2026-07-21_heatloss_phase_5_frozen_scorecard_and_thesis_handoff
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_matched_plane_recirc_field_harvest
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_throughflow_recirc_exchange_cell
---
# Heat-Loss Upcomer Exchange Evidence Extraction Contract

This package converts the Phase 4/5 heat-loss blockers into a concrete
pre-extraction contract for the upcomer exchange path. It is intentionally
no-solver and no-admission.

## Decision

- Mainline case/time queues: `3`
- Contract rows: `21`
- Required field groups: `7`
- Sampler launched: `false`
- Exchange fit allowed now: `false`
- Scoring allowed now: `false`

The current proxy evidence supports a recirculation guard, but it does not yet
support exchange-cell calibration, internal-Nu reopening, or final scorecard
use. `V_recirc`, `mdot_exchange`, `tau_recirc`, paired main/cell thermal state,
same-window pressure residual, and same-QOI UQ remain blockers.

## Outputs

- `upcomer_exchange_extraction_contract.csv`: case-by-field-group runtime and
  admission contract.
- `sampler_field_map.csv`: required fields, current tool support, sampler gaps,
  and blocked behavior.
- `case_time_window_queue.csv`: salt 2/3/4 mainline windows for the later
  compute-node sampler row.
- `no_admission_guardrail.csv`: guardrails preserving residual and runtime
  split lanes.
- `next_agent_handoff.csv`: ordered next work packages.
- `source_manifest.csv`: read-only provenance.

## Guardrails

No native CFD/OpenFOAM outputs, registry/admission state, scheduler state,
Fluid source, external repositories, generated indexes, or blocker register were
mutated. No solver, postprocessor, sampler, fitting, model selection, closure
admission, or scorecard trigger was run. Heat residual remains separate from
internal Nu.
