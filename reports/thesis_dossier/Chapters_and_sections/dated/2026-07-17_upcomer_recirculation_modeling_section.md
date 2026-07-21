---
provenance:
  - reference/geometry_reference.md
  - work_products/2026-07/2026-07-17/2026-07-17_upcomer_pipe_cell_hybrid_model/upcomer_admission_decision.csv
  - work_products/2026-07/2026-07-17/2026-07-17_upcomer_pipe_cell_hybrid_model/recirculation_feature_scorecard.csv
  - work_products/2026-07/2026-07-17/2026-07-17_branch_specific_ordinary_pipe_scorecard/ordinary_pipe_branch_mask.csv
  - work_products/2026-07/2026-07-17/2026-07-17_predict_coupled_segment_m3ts_scorecard/admission_status_scorecard.csv
tags: [thesis-dossier, upcomer, recirculation, hybrid-model, admission]
related:
  - .agent/status/2026-07-17_TODO-THESIS-UPCOMER-RECIRCULATION-SECTION.md
  - .agent/journal/2026-07-17/thesis-upcomer-recirculation-section.md
  - imports/2026-07-17_thesis_upcomer_recirculation_section.json
task: TODO-THESIS-UPCOMER-RECIRCULATION-SECTION
date: 2026-07-17
role: Writer/Reviewer/Thermal-modeling/Hydraulics
type: report
status: complete
---
# Upcomer Recirculation Modeling Section

## Observed Geometry And Flow Path

The upcomer is not a single anonymous vertical pipe segment in the current
model. The authoritative geometry reference defines the natural-circulation
flow path as:

`heater (lower_leg) -> upcomer (left_lower_leg -> test_section_span -> left_upper_leg) -> cooler (upper_leg) -> downcomer (right_leg) -> heater`.

Thus, the physical upcomer span is `left_lower_leg -> test_section_span ->
left_upper_leg`, with the test section as the middle upcomer span. The test
section also differs geometrically and thermally from the adjacent pipe: it has
a smaller bore, fused-quartz wall, no mineral insulation, and a net heat-sink
role in the current mainline CFD evidence. These facts make it unsafe to fold
the test section into a generic vertical-pipe closure.

## Observed Recirculation Evidence

The current upcomer hybrid package reports material reverse-flow evidence in
the repaired PM5 upcomer rows. The scorecard records maximum reverse area
fraction `0.7901396438`, maximum reverse mass fraction `0.5000672828`, and
maximum Richardson number `108.7458056`. These are not small perturbations to a
one-dimensional throughflow profile; they are evidence of a recirculating
section-effective regime.

The branch-specific ordinary-pipe scorecard therefore excludes the upcomer from
ordinary aggregate fits and hands it to the hybrid lane. The coupled scorecard
keeps the final forward-v1 model blocked because this hybrid lane is not yet
calibrated as a predictive closure.

## Interpretation

Current CFD evidence supports the claim that the upcomer requires a special
recirculation-aware model form. It does not support fitting or labeling
ordinary single-stream `Nu`, `f_D`, or component `K` values on the recirculating
upcomer rows. Such labels would imply that the observed heat transfer and
pressure response are produced by an ordinary pipe throughflow, when the actual
evidence shows large reverse-flow fractions and mixed-convection structure.

The appropriate model form is a throughflow-pipe plus recirculation-cell model:
one lane carries the net loop throughflow, while a separate named lane carries
section-effective exchange, mixing, or penalty terms associated with the
recirculating cell. This keeps the upcomer physics separate from ordinary pipe
closures and prevents a global multiplier or residual internal-Nu fit from
absorbing unresolved source/sink behavior.

## Paper-Safe Claims

- The upcomer path includes `left_lower_leg`, `test_section_span`, and
  `left_upper_leg`; the test section is the middle upcomer span.
- Current CFD-derived upcomer evidence shows material recirculation by reverse
  area/mass fraction and high mixed-convection metrics.
- Current recirculating upcomer rows are diagnostic evidence for model-form
  selection, not admitted ordinary-pipe `Nu`, `f_D`, or `K` closures.
- A throughflow-pipe plus recirculation-cell model is the defensible next model
  form, but it remains diagnostic-only until onset anchors and split-safe
  scoring admit a frozen candidate.

## Unresolved Blockers

- The ordinary-to-recirculating onset is not calibrated. Needed anchors include
  low-recirculation and transition cases, ideally bracketing `Re` ranges near
  the expected onset.
- The hybrid lane needs a frozen candidate with legal runtime inputs: reverse
  area fraction, reverse mass fraction, secondary velocity fraction,
  `Ri/Gr/Ra/Re/Pr/Gz`, and wall-core or wall-bulk temperature drive.
- Mesh/time uncertainty is still needed before a coarse-only recirculation
  feature can become a predictive closure.
- The final coupled M3+TS scorecard must remain blocked until pressure,
  test-section passive-loss, upcomer hybrid, and boundary-layer gates pass.
