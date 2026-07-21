---
task: AGENT-352
date: 2026-07-14
role: Writer / Synthesizer
status: complete
---
# LitRev Current Model-Form Crosswalk

Updated the July 13 LitRev lessons package in place rather than starting a
duplicate synthesis. The update maps literature recommendations and modeling
forms into the current Ethan evidence state so future agents can see what has
been tried, what was demoted, and what still needs an admission gate.

## Evidence Used

- `work_products/2026-07/2026-07-14/2026-07-14_localized_fixed_k_forward_score/README.md`
- `work_products/2026-07/2026-07-14/2026-07-14_h1_faithful_gap_and_f6_decision/README.md`
- `work_products/2026-07/2026-07-14/2026-07-14_hydraulic_tap_length_admission_refresh/README.md`
- `work_products/2026-07/2026-07-14/2026-07-14_upcomer_recirculation_internal_nu_admissibility/README.md`
- `work_products/2026-07/2026-07-14/2026-07-14_thermal_admission_internal_nu_final_gate/README.md`
- `work_products/2026-07/2026-07-14/2026-07-14_heater_source_split_screen/README.md`
- `work_products/2026-07/2026-07-14/2026-07-14_boundary_model_task_matrix/README.md`
- `work_products/2026-07/2026-07-14/2026-07-14_boundary_internal_nu_residual_guardrails/README.md`
- `work_products/2026-07/2026-07-14/2026-07-14_upcomer_matched_plane_compute_extraction/README.md`
- `work_products/2026-07/2026-07-14/2026-07-14_corrected_q_postprocess_harvest_submission/README.md`
- LitRev source files under
  `../papers/LitRev-start---Closure-and-Modeling-Decisions-for-Developing-HITEC-Flow-TAMU-MSFL/`
  were read-only inputs.

## Decisions Recorded

- Branchwise pressure and heat ledgers remain the controlling model-selection
  rule.
- Global multiplier shortcuts for friction, internal heat transfer, minor
  losses, and heat loss are demoted because they hide branch/local physics.
- Fully developed pipe `f_D` and `Nu` are retained only as references, sanity
  checks, or limit cases.
- F6 `phi(Re)` is the preferred bounded hydraulic next step after corrected-Q
  or equivalent Re-variation rows are terminal/admitted.
- H1 cannot be revived as faithful until reset/development semantics and
  component/cluster K separation are first-class model terms.
- The current upcomer evidence is a scientific result: Salt2-4 are
  recirculating in the sampled upcomer regime, so single-stream `Nu`, `f_D`,
  and `K` labels are invalid there.
- Matched upcomer plane extraction and corrected-Q rows remain pending or
  admission-gated; the summary does not consume them as admitted results.

## Artifacts

- `litrev_to_current_evidence_crosswalk.csv` is the primary crosswalk from
  literature form/lesson to current evidence status.
- `untried_litrev_model_forms.csv` is the execution queue for model forms that
  remain untried or incomplete.
- `rejected_or_demoted_litrev_shortcuts.csv` records shortcuts that should not
  re-enter the narrative as if they were viable predictive closures.

No source LitRev files, native CFD outputs, registry/admission state,
scheduler state, generated indexes, or external Fluid sources were modified.
