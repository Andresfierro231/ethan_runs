---
provenance:
  - work_products/2026-07/2026-07-14/2026-07-14_upcomer_recirculation_internal_nu_admissibility/README.md
  - work_products/2026-07/2026-07-14/2026-07-14_upcomer_recirculation_internal_nu_admissibility/blocked_missing_metrics.csv
  - work_products/2026-07/2026-07-14/2026-07-14_thermal_admission_internal_nu_final_gate/README.md
tags: [internal-nu, upcomer-recirculation, extraction-contract, therm-reconstr]
related:
  - operational_notes/maps/thermal-closures-and-internal-nu.md
task: AGENT-339
date: 2026-07-14
role: Implementer/Tester/Writer
type: work_product
status: complete
---
# Upcomer Internal-Nu Extraction Contract

## Purpose

This package turns the zero-fit upcomer/internal-Nu admission decision into an executable extraction and admission contract for `therm-reconstr`. It defines the exact matched-plane fields, formulas, row classifications, coefficient names, and evidence required before internal-Nu fitting can be reopened.

## Contract Summary

- Extraction rows: `45`.
- Admission classifications: `4`.
- Required planes: `upcomer_inlet`, `upcomer_mid`, `upcomer_outlet`.
- Current fit-admissible upcomer Nu rows remain `0`.

The plane normal is the geometric upcomer station tangent oriented in nominal inlet-to-outlet flow direction. Do not use a mean-velocity normal for admission because it can rotate with the recirculation cell and hide reverse flow.

## Admission Rule

Rows are `invalid_single_stream_coefficient` when `reverse_area_fraction >= 0.10`, `reverse_mass_fraction >= 0.10`, `Ri >= 1.0`, or an explicit recirculation flag is `yes`. Such rows may use `Nu_section_effective_upcomer_diagnostic`, but they cannot become fit rows.

Rows are `fit_admissible_Nu` only when every required metric is finite, exact time windows are known, reverse area and mass fractions are below `0.02` at all three planes, `Ri < 0.30`, secondary velocity fraction is below `0.20`, `|T_wall - T_bulk| >= 0.5 K`, wallHeatFlux/enthalpy residual is within `10%`, mesh/time uncertainty is accepted, sign/radiation semantics pass, and no heater, cooler, passive loss, wall storage, branch mixing, radiation, or recirculation residual is assigned to Nu.

## Reopen Evidence

Internal-Nu fitting reopens only after at least three admitted upcomer rows pass `fit_admissible_Nu`, including an ordinary-pipe non-recirculating anchor and a near-transition or higher-Re row. Until then, forward work uses baseline/literature/default internal Nu behavior and treats upcomer section-effective Nu as diagnostic or validation-only.

## Outputs

- `upcomer_extraction_contract.csv`
- `upcomer_nu_admission_criteria.csv`
- `coefficient_naming_policy.md`
- `source_manifest.csv`
- `summary.json`
