---
provenance:
  - work_products/2026-07/2026-07-08/2026-07-08_patchwise_heat_ledger_enthalpy_interfaces/segment_enthalpy_residuals.csv
  - work_products/2026-06/2026-06-30/2026-06-30_claude_downcomer_recirculation/downcomer_recirculation.csv
  - work_products/2026-07/2026-07-16/2026-07-16_branch_local_internal_nu_unblock/final_use_closure_qoi_gci.csv
  - work_products/2026-07/2026-07-16/2026-07-16_downcomer_internal_nu_unlock_and_blocker_roadmap/downcomer_admission_gate.csv
tags: [downcomer, internal-nu, admission, sign-enthalpy, recirculation, mesh-gci]
related:
  - .agent/blockers.yml
  - operational_notes/maps/thermal-closures-and-internal-nu.md
  - operational_notes/maps/mesh-gci-and-uncertainty.md
task: AGENT-469
date: 2026-07-16
role: Coordinator/Thermal-modeling/Internal-Nu/Mesh-GCI/Implementer/Tester/Writer
type: work_product
status: complete
---
# Downcomer Policy Admission Artifact

Generated: `2026-07-16T22:47:26+00:00`

## Decision

Downcomer ordinary Internal-Nu fit admission: `not_admitted_downcomer_policy_failed`.

Current evidence does not admit a downcomer Nu fit. The downcomer core station
velocity metrics are low-recirculation on TW4/TW5/TW6, but the thermal
interface evidence has opposed wallHeatFlux/enthalpy direction, large residuals,
and high interface recirculation flags. Same-QOI publication-ready thermal GCI
is also absent.

## Results

- Sign/enthalpy rows reviewed: `3`.
- Low-recirculation case summaries: `3`.
- Downcomer GCI rows reviewed: `4`.
- Ordinary Nu fit rows admitted: `0`.

## Outputs

- `downcomer_sign_enthalpy_gate.csv`
- `downcomer_low_recirculation_gate.csv`
- `downcomer_same_qoi_gci_gate.csv`
- `downcomer_admission_decision.csv`
- `source_manifest.csv`
- `summary.json`
