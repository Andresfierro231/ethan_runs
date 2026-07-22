# Hydraulic Reset/K Admission Contract

Date: 2026-07-14

## Decision

The current H1 evidence remains a proxy, not a faithful hydraulic closure. This package creates the tables needed to make a faithful path executable: a reset/development contract, a component/cluster K admission table, tap-length gap rows, and an F6 readiness handoff. No thermal fitting, native CFD output mutation, or global friction/K multiplier is used.

## Outputs

- `hydraulic_reset_development_contract.csv` lists reset/development rows and requires a first-class Fluid reset/development term before H1 can be relaunched faithfully.
- `component_cluster_k_admission_table.csv` keeps component K, cluster/branch context, recirculation diagnostics, and fit/validation status separate.
- `tap_length_gap_table.csv` identifies the centerline tap-length, upper-bound K, coarse/no-GCI, and recirculation gaps blocking local-K admission.
- `f6_readiness_handoff.csv` keeps F6 as the next bounded candidate but blocks launch until admitted Re-variation evidence exists.
- `summary.json` records the guardrails and row counts.

## Recommended Next Hydraulic Run/Edit

1. Add a Fluid-side reset/development input contract that reports reset/development pressure separately from straight friction, component K, cluster K, branch-apparent diagnostics, and recirculation diagnostics.
2. Extract true centerline tap-to-tap lengths and mesh-family pressure terms for the two-tap minor-loss rows before fitting any component or cluster K.
3. Do not launch F6 until corrected-Q or equivalent Re-variation rows are terminal and admitted. When admitted, score F6 first on pressure-loss validation, then mdot as a secondary guardrail.

## Counts

- Reset contract rows: 33
- Reset candidate rows blocked on API/mesh admission: 18
- Component/cluster K rows: 15
- Component/cluster K fit-admissible rows: 0
- Tap-length/gap rows: 15
- F6 ready for bounded test: false
