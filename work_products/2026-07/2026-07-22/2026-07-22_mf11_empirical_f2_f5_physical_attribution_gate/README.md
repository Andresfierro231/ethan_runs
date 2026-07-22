---
provenance:
  generated_by: tools/analyze/build_mf11_empirical_f2_f5_physical_attribution_gate.py
  task_id: TODO-MF11-EMPIRICAL-F2-F5-PHYSICAL-ATTRIBUTION-GATE-2026-07-22
  generated_at_utc: 2026-07-22T14:04:10.220341+00:00
task: TODO-MF11-EMPIRICAL-F2-F5-PHYSICAL-ATTRIBUTION-GATE-2026-07-22
tags:
  - MF11
  - empirical-bias
  - attribution
related:
  - work_products/2026-07/2026-07-22/2026-07-22_fluid_empirical_bias_models_publication_report
  - work_products/2026-07/2026-07-22/2026-07-22_mf07_entrance_development_and_reset_source_basis
  - work_products/2026-07/2026-07-22/2026-07-22_mf08_signed_wall_flux_developing_thermal_branches
  - work_products/2026-07/2026-07-22/2026-07-22_mf09_recirculating_upcomer_thermal_model_alternatives
---

# MF11 Empirical F2/F5 Physical Attribution Gate

## Decision

Decision: `empirical_diagnostic_only`.

F2 and F5 are scientifically useful because they locate the thermal discrepancy:
F2 shows that a low-DOF global affine correction explains much of the transfer
error, while F5 shows that thermal-family structure can explain slightly more.
They are not physical closures. The candidate physics are plausible but
non-unique and still blocked by source/property, mesh/GCI, runtime-input, or
admission gates.

## Use In Publication

Use this package to write that empirical discrepancy models motivate the next
physical studies: entrance/development, signed wall/source heat, recirculating
upcomer exchange, wall-shape/axial mixing, source placement, and sensor/QOI
projection. Do not cite F2/F5 as admitted coefficients, final scores, source
properties, or hidden internal-Nu corrections.
