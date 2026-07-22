---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_two_tap_section_effective_hybrid_pressure_scorecard/section_effective_pressure_scorecard.csv
  - work_products/2026-07/2026-07-21/2026-07-21_hybrid_pressure_no_fit_performance_bakeoff/no_fit_performance_table.csv
  - work_products/2026-07/2026-07-22/2026-07-22_s10_s14_pressure_f6_cand001_retry_and_uq_gate/timeout_source_ordinary_uq_gate_matrix.csv
tags: [thesis, pressure, section-effective, f6, negative-result]
related:
  - .agent/status/2026-07-22_TODO-THESIS-STUDY-PRESSURE-BASIS-LADDER-EVIDENCE-PACKET-2026-07-22.md
  - imports/2026-07-22_thesis_study_pressure_basis_ladder_evidence_packet.json
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_study_pressure_basis_ladder_evidence_packet/README.md
task: TODO-THESIS-STUDY-PRESSURE-BASIS-LADDER-EVIDENCE-PACKET-2026-07-22
date: 2026-07-22
role: Hydraulics / Writer / Reviewer / Tester
type: journal
status: complete
---
# Thesis Pressure Basis Ladder Evidence Packet

## Attempted

Built an external-writer pressure packet from the existing section-effective
hybrid pressure scorecard, no-fit bakeoff, F6 retry/UQ gate, source/property
preflight, and S14 pressure use map.

The purpose was not to improve a pressure model. The purpose was to make the
negative pressure result usable in the thesis without accidentally promoting it
to component `K`, F6, clipped `K`, or hidden-multiplier evidence.

## Observed

The three current `corner_lower_right` rows have gross static pressure rise of
about 3 kPa. Hydrostatic head accounts for approximately the full gross rise.
After hydrostatic and kinetic correction, the available signed residuals are:

- Salt2: `-1.25366731683 Pa`
- Salt3: `-1.84957005859 Pa`
- Salt4: `-1.67833900273 Pa`

All three rows fail ordinary component interpretation because material reverse
flow is present, same-basis straight/development reference subtraction is
missing, and same-QOI UQ is missing.

The no-fit hybrid pressure bakeoff has one useful diagnostic transfer number:
the Salt2-frozen section-effective transfer has max absolute error
`0.47046606946166093438399 Pa`. This remains diagnostic and does not create a
frozen predictive candidate.

F3/Shah-vs-F6 is not numerically evaluated because admitted F6 rows remain `0`.

## Inferred

The pressure/F6 blocker can be explained cleanly in the thesis. The current rows
are negative-result evidence showing that an ordinary single-stream component
loss model is the wrong interpretation for this recirculating lower-right
section. The physically safer model slot is section-effective:
`Delta_p_recirc_section`.

That statement is weaker than model admission but stronger than saying the data
are unusable. It gives a defensible reason for the hybrid pressure route and a
clear checklist for future candidate work.

## Caveats

No new CFD fields were sampled. No endpoint rows were admitted. No protected
split rows were scored. No F3/F6 numeric comparison was released. The claim
boundary depends on the existing July 21 pressure packages and the July 22
source/property preflight.

## Next Useful Actions

1. Keep lower-right two-tap rows as section-effective/diagnostic thesis
   evidence.
2. Seek different low-recirculation or nonrecirculating pressure anchors for F6:
   RAF/RMF below `0.01`, finite endpoint fields, same-window pressure loss,
   Re/Ri/properties, and same-QOI UQ.
3. If pursuing the hybrid route, build a throughflow-plus-recirculation pressure
   model that predicts `Delta_p_recirc_section` without using clipped residuals
   or hidden multipliers.
4. Do not publish F3/Shah-vs-F6 numeric comparison until an ordinary admissible
   F6 candidate exists.
