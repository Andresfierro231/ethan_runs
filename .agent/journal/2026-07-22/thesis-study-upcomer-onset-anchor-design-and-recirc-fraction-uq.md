---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_study_recirculation_fraction_onset_evidence_packet/README.md
  - work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_qwall_mesh_gci_uq_gate/summary.json
  - work_products/2026-07/2026-07-22/2026-07-22_1d_regime_map_nondimensional_closure_eligibility/segment_case_regime_map.csv
tags: [journal, upcomer, recirculation, onset, fail-closed]
related:
  - .agent/status/2026-07-22_TODO-THESIS-STUDY-UPCOMER-ONSET-ANCHOR-DESIGN-AND-RECIRC-FRACTION-UQ-2026-07-22.md
  - imports/2026-07-22_thesis_study_upcomer_onset_anchor_design_and_recirc_fraction_uq.json
task: TODO-THESIS-STUDY-UPCOMER-ONSET-ANCHOR-DESIGN-AND-RECIRC-FRACTION-UQ-2026-07-22
date: 2026-07-22
role: Hydraulics / Thermal-modeling / cfd-pp / Writer / Reviewer / Tester
status: complete
---
# Journal: Upcomer Onset Anchor Design And Recirculation-Fraction UQ

## Attempted

Claimed the upcomer onset/design row and synthesized existing recirculation
topology, current-coarse S13 exchange/tau, same-QOI temporal UQ, mesh/GCI, and
regime-map evidence. The active S13 sampler smoke row was treated as read-only
and was not touched.

## Observed

Salt2/Salt3/Salt4 have reverse-candidate fractions of the right-leg ROI between
0.157702688614 and 0.162167108784. The largest component fractions of the ROI
are between 0.0831431649426 and 0.0860171209471, with fragmented topology.
Current-coarse S13 exchange/tau proxies are finite, with tau decreasing from
868.807159089 s in Salt2 to 301.390653047 s in Salt4. Same-QOI temporal UQ is
executed for four labels, but accepted same-label mesh/GCI rows are zero.

## Inferred

The thesis can describe persistent recirculation diagnostics and motivate a
throughflow-plus-recirculation model form. It cannot yet publish a closed
recirculation-fraction map, an onset threshold, or an admitted exchange
coefficient. Ordinary upcomer `Nu/f_D/K/F6` should remain disabled for the
recirculating spans.

## Caveats

This was a synthesis/design package only. It did not run the active sampler,
extract new fields, score a candidate, or alter any release/admission state.

## Next Useful Actions

Wait for the active S13 smoke row. If it passes, run the post-sampler same-label
mesh/GCI and production-harvest gate. If it fails, refine near-onset anchor
designs with predeclared RAF/RMF, closed CV fraction, same-window Ri, and
exchange-QOI harvest requirements.
