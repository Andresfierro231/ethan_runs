---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_s13_coarse_equivalence_open_cv_heatflow_contract/coarse_basis_resolution.csv
  - work_products/2026-07/2026-07-22/2026-07-22_s13_coarse_equivalence_open_cv_heatflow_contract/auditable_coarse_equivalence_contract.csv
  - work_products/2026-07/2026-07-22/2026-07-22_s13_coarse_equivalence_open_cv_heatflow_contract/averaged_value_policy.csv
tags: [journal, s13, recirculation, open-cv, coarse-equivalence, source-side-heat-flow]
related:
  - .agent/status/2026-07-22_TODO-S13-COARSE-EQUIVALENCE-OPEN-CV-HEATFLOW-CONTRACT-2026-07-22.md
  - imports/2026-07-22_s13_coarse_equivalence_open_cv_heatflow_contract.json
task: TODO-S13-COARSE-EQUIVALENCE-OPEN-CV-HEATFLOW-CONTRACT-2026-07-22
date: 2026-07-22
role: Hydraulics / Thermal-modeling / cfd-pp / Mesh-GCI / Implementer / Tester / Writer / Reviewer
type: journal
status: complete
---
# S13 Coarse-Equivalence / Open-CV / Heat-Flow Contract

## Attempted

Resolved the same-label coarse blocker using existing evidence only. The
package consumes the current-coarse reconstructed rows, medium/fine mesh
disposition, source-side heat-flow contract, and same-QOI heat-flow diagnostics.

## Observed

There are `12` current-coarse reference rows across Salt2/Salt3/Salt4 and four
QOI labels. Those rows have useful formulas and finite values, but the prior
preflight still reports zero strict same-label mesh-level rows for
coarse/medium/fine. The medium/fine rows are from a separate exact-label
sampler family, so the current coarse rows cannot be silently joined into a
formal GCI triplet.

Open CVs are scientifically usable for diagnostics if the missing or crossing
terms are explicit. They are not enough for exchange-cell coefficient admission
unless the energy and pressure residual equations include the open boundaries
and close within documented uncertainty.

## Inferred

The right policy is not "closed CV always or nothing." It is:
diagnostics may use an open CV; admitted reduced-model coefficients require a
closed or residual-complete CV. Averaged `T_recirc` and similar intensive states
are acceptable with a stated weighting basis. Averaged substitutes for fluxes,
integrals, and residuals are not acceptable.

## Caveats

This package does not run a sampler, mutate native outputs, release Qwall or
source/property evidence, fit any coefficient, or unlock formal GCI. It defines
the contract needed to clear those gates later.

## Next Useful Actions

Either rerun coarse through the repaired exact-label sampler with the same
schema as medium/fine, or perform a joined equivalence audit across geometry,
time-window, field/source/property, and residual-complete CV criteria. In
parallel, build the heat-flow residual using `Q_wall_W`,
`Q_source_side_net_static_bc_W`, enthalpy exchange terms, and cp/property
provenance on the same window and mask.
