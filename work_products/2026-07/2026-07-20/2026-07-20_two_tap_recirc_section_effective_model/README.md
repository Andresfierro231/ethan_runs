---
provenance:
  - work_products/2026-07/2026-07-18/2026-07-18_two_tap_pressure_basis_recirc_audit/pressure_velocity_basis_audit.csv
  - work_products/2026-07/2026-07-18/2026-07-18_two_tap_pressure_basis_recirc_audit/endpoint_recirculation_metrics.csv
  - work_products/2026-07/2026-07-18/2026-07-18_two_tap_component_isolation_decision/component_isolation_audit.csv
  - work_products/2026-07/2026-07-18/2026-07-18_two_tap_same_qoi_uq_status/same_qoi_uncertainty_audit.csv
  - work_products/2026-07/2026-07-18/2026-07-18_two_tap_separated_admission_review/final_gate_review.csv
  - work_products/2026-07/2026-07-18/2026-07-18_f6_legwise_pressure_anchor_plan/legwise_pressure_residual_contract.csv
  - work_products/2026-07/2026-07-20/2026-07-20_two_tap_nonrecirc_anchor_plan/README.md
tags: [pressure-ledger, two-tap, recirculation, section-effective, paper-dossier]
related:
  - .agent/status/2026-07-20_TODO-TWO-TAP-RECIRC-SECTION-EFFECTIVE-MODEL.md
  - .agent/journal/2026-07-20/two-tap-recirc-section-effective-model.md
task: TODO-TWO-TAP-RECIRC-SECTION-EFFECTIVE-MODEL
date: 2026-07-20
role: Hydraulics/cfd-pp/Writer
type: work_product
status: complete
---
# Two-Tap Recirculating Section-Effective Model

Generated: `2026-07-20T16:33:42+00:00`

## Decision

Current `corner_lower_right` rows remain blocked for ordinary component `K` and
F6 promotion. The pressure evidence is still valuable, but the admissible
scientific interpretation is a recirculating section-effective pressure residual
contract. Static pressure drops are hydrostatic/buoyancy dominated, while the
`p_rgh` residuals and reverse-flow metrics motivate a named recirculation lane.

## Model Form

The package defines the diagnostic residual as:

```text
Delta_p_resid = Delta_p_rgh - Delta_p_kin - Delta_p_straight - Delta_p_dev
K_eff_recirc = Delta_p_resid / q_ref
```

`q_ref` is a same-window throughflow dynamic-pressure basis from net positive
mass flux. A near-zero denominator returns a no-fit status, not a large `K`.

## Outputs

- `recirc_pressure_basis_table.csv`
- `section_effective_model_contract.csv`
- `current_corner_lower_right_recirc_rows.csv`
- `same_qoi_uq_sampling_contract.csv`
- `model_form_decision_table.csv`
- `paper_claims_and_limitations.csv`
- `artifact_crosswalk.csv`
- `figure_table_manifest.csv`
- `source_manifest.csv`
- `summary.json`

## Paper-Safe Claims

- Current two-tap corner rows show material recirculation and are not ordinary
  single-stream component `K` evidence.
- Static apparent `K` is hydrostatic/buoyancy dominated and is diagnostic only.
- The appropriate next hydraulic model form is throughflow plus an explicit
  recirculating section-effective pressure residual.
- Same-QOI mesh/time UQ and split-safe scoring remain required before any
  coefficient admission.

## Counts

- Current rows reviewed: `3`.
- Rows with ordinary component `K` admitted: `0`.
- Rows with F6 fit performed: `0`.
- Paper claim rows: `4`.

## Guardrails

No native CFD outputs, registry/admission state, scheduler state, Fluid source,
or external paths were mutated. No F6 fit, component-K admission, global
multiplier, clipped `K`, or scheduler launch was performed.
