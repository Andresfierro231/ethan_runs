---
provenance:
  - work_products/2026-07/2026-07-18/2026-07-18_two_tap_pressure_basis_recirc_audit/endpoint_recirculation_metrics.csv
  - work_products/2026-07/2026-07-14/2026-07-14_upcomer_matched_plane_compute_extraction/matched_plane_metrics_admission.csv
  - work_products/2026-07/2026-07-20/2026-07-20_pm10_same_window_residual_targets/pm10_plane_pressure_targets.csv
tags: [cfd-postprocessing, recirculation, pressure-ledger, litrev-contract]
related:
  - .agent/status/2026-07-21_TODO-LITREV-MATCHED-PLANE-RECIRC-FIELD-HARVEST.md
  - imports/2026-07-21_litrev_matched_plane_recirc_field_harvest.json
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_matched_plane_recirc_field_harvest/README.md
task: TODO-LITREV-MATCHED-PLANE-RECIRC-FIELD-HARVEST
date: 2026-07-21
role: cfd-pp/Hydraulics/Thermal-modeling/Tester/Writer
type: journal
status: complete
---
# LitRev Matched-Plane Recirculation Field Harvest

## Attempted

Built a recirculation evidence inventory from existing endpoint and
matched-plane artifacts only. The package avoids scheduler/postprocessing work
and does not infer missing RMF/SVF from pressure-only targets.

## Observed

Current lower-right two-tap rows have RAF/RMF/SVF fields and fail ordinary
single-stream gates by material reverse flow. Upcomer matched-plane rows carry
diagnostic/proxy or parse-incomplete recirculation evidence, but not the full
transverse component and signed/absolute mdot basis required for admission.
PM10 upcomer pressure targets contain pressure, density, speed, and dynamic
pressure but no RAF/RMF/SVF fields.

## Inferred

The immediate use of the current recirculation evidence is gating, not fitting.
Lower-right corner and test-section/upcomer rows should remain section-effective
or exchange-cell candidates unless a later terminal harvest provides coherent
low-reverse or exchange-field evidence.

## Caveats

The newer corrected-Q continuation `3307441` and high-heat jobs are explicitly
blocked rows here. No scheduler state was inspected, and no live harvest was
performed.

## Next Useful Actions

Use this package as the recirculation input to the gated single-stream
developing-branch precheck. Rows with missing RAF/RMF/SVF or pressure-only
targets should fail ordinary single-stream admission until separately harvested.
