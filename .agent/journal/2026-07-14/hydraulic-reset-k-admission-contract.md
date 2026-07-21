---
task: AGENT-338
date: 2026-07-14
role: Hydraulics / Implementer / Tester / Writer
status: complete
---
# Hydraulic Reset/K Admission Contract

Implemented the next hydraulics plan slice from existing evidence only. The
package converts H1 proxy lessons into executable admission artifacts without
mutating CFD outputs, editing external Fluid code, fitting thermal terms, or
exporting a global hydraulic multiplier.

Outcome:

- `hydraulic_reset_development_contract.csv` records `33` reset/development
  rows. `18` are candidate rows blocked on API and mesh admission, `12` are
  diagnostic-only recirculation-invalid rows, and `3` are reference rows.
- `component_cluster_k_admission_table.csv` records `15` component/cluster K
  rows with `0` fit-admissible rows under current evidence.
- `tap_length_gap_table.csv` records `15` rows requiring centerline tap lengths,
  upper-bound K cleanup, mesh/GCI evidence, or recirculation-aware exclusion.
- `f6_readiness_handoff.csv` keeps F6 as next bounded candidate but blocks
  launch while corrected-Q admitted rows remain `0`.

Recommended next hydraulic work is to implement the first-class
reset/development input/reporting API and extract centerline tap-to-tap lengths
plus mesh-qualified pressure terms. F6 should wait until admitted Re-variation
evidence exists and should then be scored on pressure-loss validation before
mdot.
