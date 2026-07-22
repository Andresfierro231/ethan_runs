---
provenance:
  - work_products/2026-07/2026-07-18/2026-07-18_two_tap_pressure_basis_recirc_audit/endpoint_recirculation_metrics.csv
  - work_products/2026-07/2026-07-14/2026-07-14_upcomer_matched_plane_compute_extraction/matched_plane_metrics_admission.csv
  - work_products/2026-07/2026-07-20/2026-07-20_pm10_same_window_residual_targets/pm10_plane_pressure_targets.csv
tags: [cfd-postprocessing, recirculation, pressure-ledger, litrev-contract]
related:
  - .agent/status/2026-07-21_TODO-LITREV-MATCHED-PLANE-RECIRC-FIELD-HARVEST.md
  - .agent/journal/2026-07-21/litrev-matched-plane-recirc-field-harvest.md
task: TODO-LITREV-MATCHED-PLANE-RECIRC-FIELD-HARVEST
date: 2026-07-21
role: cfd-pp/Hydraulics/Thermal-modeling/Tester/Writer
type: work_product
status: complete
---
# LitRev Matched-Plane Recirculation Field Harvest

This package inventories current matched-plane recirculation evidence from
existing artifacts only. It does not launch postprocessing or infer missing
RMF/SVF from RAF proxies.

## Outputs

- `matched_plane_recirc_field_harvest.csv`: 53 rows.
- `recirc_harvest_readiness.csv`: 5 source-family rows.
- `source_manifest.csv`, `summary.json`, builder, and test.

## Findings

- Current lower-right two-tap rows carry RAF/RMF/SVF and fail ordinary
  recirculation gates, so they remain section-effective diagnostics.
- Upcomer rows provide diagnostic/proxy or parse-incomplete evidence; scalar
  secondary-flow fractions are not full transverse component fields.
- PM10 pressure targets are pressure-only rows and cannot be used as
  recirculation-field evidence.
- Corrected-Q continuation `3307441` and high-heat jobs remain terminal-gated.

## Guardrails

No native-output mutation, scheduler action, solver/postprocessing launch,
registry/admission mutation, Fluid/external edit, ordinary K/F6/Nu admission, or
generated-index refresh was performed.
