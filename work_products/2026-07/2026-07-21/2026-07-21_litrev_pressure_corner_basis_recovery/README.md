---
task: TODO-LITREV-PRESSURE-CORNER-BASIS-RECOVERY
date: 2026-07-21
role: Hydraulics / cfd-pp / Tester / Writer
type: work_product
status: complete
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_model_form_extraction/pressure_corner_extraction_findings.csv
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_model_form_extraction/cfd_postprocessing_contract.csv
  - work_products/2026-07/2026-07-18/2026-07-18_two_tap_pressure_basis_recirc_audit/pressure_velocity_basis_audit.csv
  - work_products/2026-07/2026-07-18/2026-07-18_two_tap_pressure_basis_recirc_audit/endpoint_recirculation_metrics.csv
  - work_products/2026-07/2026-07-20/2026-07-20_two_tap_recirc_section_effective_model/recirc_pressure_basis_table.csv
tags: [pressure-ledger, pressure-corner, two-tap, section-effective, litrev-synthesis]
related:
  - operational_notes/maps/pressure-and-momentum-budget.md
  - .agent/status/2026-07-21_TODO-LITREV-PRESSURE-CORNER-BASIS-RECOVERY.md
  - .agent/journal/2026-07-21/litrev-pressure-corner-basis-recovery.md
---
# LitRev Pressure-Corner Basis Recovery Audit

## Decision

The current pressure-increasing corner candidates are the three `corner_lower_right` Salt2/Salt3/Salt4 endpoint pairs. All three are `section_effective`, not `component_K`, `cluster_K`, or F6 evidence.

Gross static pressure rises by about 3.0 kPa from the lower-leg endpoint to the right-leg endpoint. That rise is hydrostatic dominated. After hydrostatic and kinetic correction, the remaining available mechanical residual is negative and is preserved with its sign as pressure-recovery or recirculating-section diagnostic evidence. It is not clipped into a positive loss and not interpreted as energy-generating negative loss.

## Outputs

- `pressure_corner_basis_recovery_audit.csv`
- `source_manifest.csv`
- `summary.json`
- `build_litrev_pressure_corner_basis_recovery.py`
- `test_litrev_pressure_corner_basis_recovery.py`

## Counts

- Audit rows: `3`
- Label counts: `{'section_effective': 3}`
- Component-K admitted rows: `0`
- F6 fit rows: `0`
- Clipped-K rows: `0`
- Global multiplier rows: `0`

## Interpretation

The decomposition used here is the available same-endpoint identity:

```text
dp_static(down-up) = dp_hydrostatic + dp_kinetic + dp_available_residual
```

Same-basis straight/developing correction is explicitly missing, so the available residual is not a coefficient-ready irreversible loss. Recovery diagnostics are also missing, and the endpoint planes have material reverse flow (`RAF` about 0.76, `RMF` about 0.50). The correct current publication use is therefore a section-effective pressure residual or pressure-recovery diagnostic.

## Guardrails

No native CFD/OpenFOAM outputs, registry/admission state, scheduler state, Fluid source, external repo files, F6 fit, component-K admission, global multiplier, or clipped K were changed or introduced.
