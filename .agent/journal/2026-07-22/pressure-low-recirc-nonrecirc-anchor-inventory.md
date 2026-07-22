---
provenance:
  - work_products/2026-07/2026-07-20/2026-07-20_f6_non_upcomer_branch_modeling_analysis/non_upcomer_f6_candidate_matrix.csv
  - work_products/2026-07/2026-07-21/2026-07-21_f6_endpoint_raw_face_sampler/ordinary_flow_gate.csv
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_study_pressure_basis_ladder_evidence_packet/summary.json
tags: [pressure, f6, nonrecirculating-anchor, section-effective, no-admission]
related:
  - .agent/status/2026-07-22_TODO-PRESSURE-LOW-RECIRC-NONRECIRC-ANCHOR-INVENTORY-2026-07-22.md
  - imports/2026-07-22_pressure_low_recirc_nonrecirc_anchor_inventory.json
  - work_products/2026-07/2026-07-22/2026-07-22_pressure_low_recirc_nonrecirc_anchor_inventory/README.md
task: TODO-PRESSURE-LOW-RECIRC-NONRECIRC-ANCHOR-INVENTORY-2026-07-22
date: 2026-07-22
role: Hydraulics / Implementer / Tester / Writer / Reviewer
type: journal
status: complete
---
# Pressure Low-Recirculation / Nonrecirculating Anchor Inventory

## Attempted

Built a pressure unblock packet from existing F6 non-upcomer candidate,
endpoint raw-face, pressure-basis ladder, and low-recirculation source-recovery
packages.

The intent was to advance pressure without revisiting the failed lower-right
component-K route. The packet explicitly asks what can support future ordinary
F6/F3/Shah comparison and what must remain section-effective evidence.

## Observed

The non-upcomer inventory has `36` candidate rows. Six rows are preferred future
ordinary anchors: Salt2/Salt3/Salt4 `right_leg` and `test_section_span`. They
remain not fit-ready.

The current sampled medium/fine endpoint evidence has `8` ordinary-flow rows
and all `8` fail the RAF/RMF ordinary-flow gate. Same-QOI UQ-ready rows remain
`0`. F6 fit-ready rows remain `0`.

The lower-right two-tap packet still preserves `3` section-effective residual
rows and has `0` component-K rows, `0` F6 rows, and no F3/F6/Shah numeric
comparison release.

## Inferred

The immediate pressure unblock is not F6 fitting. It is anchor discovery. The
best current pressure sequence is:

1. monitor CAND001 terminal disposition without duplicate submit or harvest;
2. search right-leg or test-section-span evidence for a lower-recirculation
   anchor;
3. build same-QOI mesh/time UQ only after a same-label residual QOI exists;
4. revisit F3/F6/Shah only after ordinary-flow, endpoint, UQ, and
   source/property gates pass.

## Caveats

No scheduler action was taken. No native fields were sampled. No F6,
component-K, clipped-K, cluster-K, or hidden multiplier was admitted.

## Next Useful Actions

1. If job `3308712` or its successor reaches terminal success, claim a terminal
   disposition/readiness row before any staged-copy sampler work.
2. If CAND001 fails or remains unavailable, seek a different right-leg or
   test-section-span lower-recirculation anchor with RAF/RMF below `0.01`.
3. Keep lower-right two-tap pressure as `Delta_p_recirc_section` thesis
   evidence.
