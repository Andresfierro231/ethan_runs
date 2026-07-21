---
provenance:
  - ../papers/UTexas_Research/LitRev-start---Closure-and-Modeling-Decisions-for-Developing-HITEC-Flow-TAMU-MSFL/AGENTS.md
  - ../papers/UTexas_Research/LitRev-start---Closure-and-Modeling-Decisions-for-Developing-HITEC-Flow-TAMU-MSFL/README.md
  - ../papers/UTexas_Research/LitRev-start---Closure-and-Modeling-Decisions-for-Developing-HITEC-Flow-TAMU-MSFL/chapters/06_minor_losses_quartz_transition.tex
  - ../papers/UTexas_Research/LitRev-start---Closure-and-Modeling-Decisions-for-Developing-HITEC-Flow-TAMU-MSFL/chapters/14_final_integration_cfd_postprocessing.tex
  - ../papers/UTexas_Research/LitRev-start---Closure-and-Modeling-Decisions-for-Developing-HITEC-Flow-TAMU-MSFL/appendices/S_equation_threshold_admission_registry.tex
  - ../papers/UTexas_Research/LitRev-start---Closure-and-Modeling-Decisions-for-Developing-HITEC-Flow-TAMU-MSFL/appendices/V_final_model_form_candidates.tex
tags: [litrev-synthesis, pressure-corner, model-forms, cfd-postprocessing, one-d-model]
related:
  - .agent/status/2026-07-21_TODO-LITREV-MODEL-FORM-EXTRACTION-2026-07-21.md
  - imports/2026-07-21_litrev_model_form_extraction.json
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_model_form_extraction/README.md
task: TODO-LITREV-MODEL-FORM-EXTRACTION-2026-07-21
date: 2026-07-21
role: Coordinator/Writer/Reviewer
type: journal
status: complete
---
# LitRev Model-Form Extraction

Task: TODO-LITREV-MODEL-FORM-EXTRACTION-2026-07-21

## Attempted

Converted the new standalone LitRev into an Ethan-local extraction package for
future modeling-agent dispatch. The target was not to implement any model, but
to preserve source-bounded information in a form that can be claimed by pressure,
thermal, CFD-postprocessing, and Fluid/API agents later.

## Observed

The LitRev is a modular LaTeX project with source-audited chapters, appendices,
schema CSVs, and final PDFs. Its README states the key modeling shift: fully
developed laminar friction and fully developed Nusselt numbers are reference
limits, while the active architecture is branchwise developing/redeveloping
pressure loss, branchwise developing/mixed heat transfer, explicit fitting
losses, and resistance-network heat loss with residual accounting.

For pressure/corner questions, the strongest relevant LitRev material is in
`chapters/06_minor_losses_quartz_transition.tex`,
`appendices/N_cfd_postprocessing_equations.tex`,
`appendices/S_equation_threshold_admission_registry.tex`, and
`chapters/14_final_integration_cfd_postprocessing.tex`. Those sources require
pressure basis, velocity basis, hydrostatic correction, kinetic correction,
straight/developing correction, component isolation, recovery, recirculation
metrics, source status, and same-QOI uncertainty before a coefficient can be
named as an admitted component `K`.

## Inferred

Static pressure increasing around a corner is not by itself a sign error or an
admitted negative loss. It can be pressure recovery, hydrostatic/kinetic basis,
a source-defined reduced-static junction coefficient, cluster recovery, or an
unresolved residual. The next pressure agents should classify that mechanism
before scoring any K. Negative source-defined tee/junction coefficients may be
physically legitimate under the source's definition, but importing them into a
TAMU circular-pipe dynamic-K ledger without basis conversion would be an
overclaim.

The reduced-model ladder implied by the LitRev is: keep a gated one-stream
developing branch while diagnostics pass; use section/cluster K when local
disturbance is bracketed but not universal; use signed-flow junction network
only for discrete branch reversal; use throughflow plus recirculation/exchange
cell for persistent local exchange; keep transient and ROM forms optional until
their evidence bases exist.

## Caveats

This package is a literature extraction and dispatch artifact. It does not
validate a numerical threshold, select coefficients, run CFD postprocessing, or
change admission state. The forward-predictive topic map was intentionally left
unchanged because an active-board row still claims it.

## Next Useful Actions

Use `next_agent_task_matrix.csv` to create separate rows for:
fitting inventory/source envelope, pressure-corner basis/recovery audit,
recirculation switching calibration template, throughflow-plus-recirculation
model design, CFD postprocessing schema gap audit, thermal heat-loss contract
alignment, and model-form wave dispatch.
