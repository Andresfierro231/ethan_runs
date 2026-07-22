---
provenance:
  - work_products/2026-07/2026-07-20/2026-07-20_two_tap_recirc_section_effective_model/section_effective_model_contract.csv
  - work_products/2026-07/2026-07-20/2026-07-20_two_tap_recirc_section_effective_model/recirc_pressure_basis_table.csv
  - work_products/2026-07/2026-07-18/2026-07-18_f6_legwise_pressure_anchor_plan/legwise_pressure_residual_contract.csv
tags: [paper-methods, pressure-basis, two-tap, recirculation]
task: TODO-TWO-TAP-RECIRC-SECTION-EFFECTIVE-MODEL
date: 2026-07-20
role: Hydraulics/cfd-pp/Writer
type: paper-methods-note
status: complete
---
# Paper Methods Note: Two-Tap Recirculating Pressure Basis

## Purpose

This note is the paper-facing methods bridge for the `corner_lower_right`
two-tap pressure evidence. It should be cited when explaining why the current
rows are not ordinary component `K` rows and how a recirculation-aware pressure
model should be defined.

## Pressure Basis

The raw endpoint audit reports static pressure, `p_rgh`, hydrostatic
correction, local dynamic pressure, and same-window velocity terms. The static
pressure difference is not a local loss coefficient by itself in this geometry:
the hydrostatic correction is approximately the same size as the static
endpoint pressure difference. For the current rows the paper-safe statement is:

```text
static apparent K = hydrostatic/buoyancy-dominated diagnostic only
```

The model-facing pressure basis must therefore use the hydrostatic-checked
mechanical pressure term and keep the sign convention visible:

```text
Delta_p_rgh = p_rgh_downstream - p_rgh_upstream
```

## Section-Effective Residual

The recirculation-aware residual contract is:

```text
Delta_p_resid = Delta_p_rgh - Delta_p_kin - Delta_p_straight - Delta_p_dev
K_eff_recirc = Delta_p_resid / q_ref
```

`q_ref` is a same-window throughflow dynamic-pressure basis from the net
positive mass flux across the endpoint surfaces. If that denominator is
near zero, the result is a no-fit diagnostic status, not a large coefficient.

## Required Carried Fields

Every model row must carry endpoint labels, time window, property mode,
hydrostatic basis, `p_rgh` sign convention, velocity/kinetic basis, `RAF`,
`RMF`, `SVF`, `Re`, `Ri`, component-isolation label, and same-QOI UQ status.
Rows missing those fields can support blocker diagnosis but cannot admit a
coefficient.

## Paper Claim Boundary

Allowed claim: current evidence motivates a throughflow plus recirculating
section-effective pressure-residual model.

Forbidden claim: current evidence admits a clean local `component_K`, ordinary
single-stream `K`, F6 fit, or hidden global hydraulic multiplier.

Generated package row count: `3` current rows;
ordinary component-K admissions: `0`.
