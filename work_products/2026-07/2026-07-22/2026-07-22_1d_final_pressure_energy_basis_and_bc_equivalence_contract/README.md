---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_study_pressure_basis_ladder_evidence_packet/pressure_basis_ladder.csv
  - work_products/2026-07/2026-07-22/2026-07-22_source_property_cp_viscosity_pressure_basis_preflight/pressure_basis_contract.csv
  - work_products/2026-07/2026-07-22/2026-07-22_1d_conservative_thermal_ledger_residual_owner_contract/conservative_equation_ledger.csv
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_pressure_f6_ordinary_basis_failure_packet/f6_component_k_gate_waterfall.csv
  - work_products/2026-07/2026-07-22/2026-07-22_s10_s14_pressure_f6_cand001_retry_and_uq_gate/pressure_claim_boundary_table.csv
tags: [pressure-basis, energy-basis, boundary-conditions, admission-contract]
related:
  - .agent/status/2026-07-22_TODO-1D-FINAL-PRESSURE-ENERGY-BASIS-AND-BC-EQUIVALENCE-CONTRACT-2026-07-22.md
  - .agent/journal/2026-07-22/1d-final-pressure-energy-basis-and-bc-equivalence-contract.md
  - imports/2026-07-22_1d_final_pressure_energy_basis_and_bc_equivalence_contract.json
task: TODO-1D-FINAL-PRESSURE-ENERGY-BASIS-AND-BC-EQUIVALENCE-CONTRACT-2026-07-22
date: 2026-07-22
role: Hydraulics / Thermal-modeling / Forward-pred / Writer / Reviewer / Tester
type: work_product
status: complete
---
# 1D Pressure/Energy Basis And BC Equivalence Contract

Decision: `pressure_energy_bc_contract_ready_no_component_k_or_nu_admission`.

This package fixes the basis rules for pressure, velocity, energy, and boundary
condition equivalence before any future pressure or thermal closure is admitted.
It preserves existing negative results: section-effective residuals are useful
diagnostic evidence, but ordinary component `K`, `F6`, clipped `K`, hidden
multipliers, and runtime internal-`Nu` residual absorption remain blocked.

## Controlling Rules

1. Compare pressures only after naming the basis: static `p`, reduced-static
   `p_rgh`, or total pressure.
2. Hydrostatic head and kinetic corrections are separate owners, not loss
   coefficients.
3. A component `K` or `F6` candidate requires ordinary-flow topology, endpoint
   consistency, velocity/area basis, straight/developing subtraction, recovery
   planes, source/property release, and same-QOI UQ.
4. Negative or section-effective residuals may be reported as pressure-model
   evidence but may not be clipped into positive loss coefficients.
5. Thermal BCs must map to heat-path lanes. UHF, UWT, conjugate, nonuniform,
   jacket/cooler, passive external loss, radiation, storage, and residual terms
   cannot be merged into internal `Nu`.

## Outputs

- `pressure_energy_basis_contract.csv`
- `bc_equivalence_map.csv`
- `pressure_admission_guardrails.csv`
- `scorecard_handoff_requirements.csv`
- `source_manifest.csv`
- `no_mutation_guardrails.csv`
- `summary.json`

No scheduler, solver, sampler, protected score, admission, source/property
release, native-output mutation, registry mutation, Fluid edit, external edit,
or thesis body edit occurred.
