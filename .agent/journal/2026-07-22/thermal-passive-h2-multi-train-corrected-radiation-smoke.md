---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_thermal_passive_h2_radiation_runtime_basis_reconciliation/summary.json
  - work_products/2026-07/2026-07-13/2026-07-13_predictive_external_bc_implementation_wave/cfd_external_boundary_dictionary.csv
  - work_products/2026-07/2026-07-22/2026-07-22_1d_train_only_setup_uq_smoke_execution/summary.json
tags: [journal, thermal, passive-h2, multi-train, corrected-radiation]
related:
  - .agent/status/2026-07-22_TODO-THERMAL-PASSIVE-H2-MULTI-TRAIN-CORRECTED-RADIATION-SMOKE-2026-07-22.md
  - imports/2026-07-22_thermal_passive_h2_multi_train_corrected_radiation_smoke.json
task: TODO-THERMAL-PASSIVE-H2-MULTI-TRAIN-CORRECTED-RADIATION-SMOKE-2026-07-22
date: 2026-07-22
role: Thermal-modeling / Forward-pred / Uncertainty / Implementer / Tester / Writer / Reviewer
type: journal
status: complete
---
# PASSIVE-H2 multi-train corrected radiation smoke

## Attempted

Extended the corrected outer-insulation-surface PASSIVE-H2 operator from the
Salt2 reconciliation to Salt2/Salt3/Salt4 using existing train-only setup-UQ
model outputs and case-specific source-backed passive external-boundary rows.

## Observed

The earlier high radiation term is not stable once the emitting surface is
moved from the hot inner wall/pipe state to the outer insulation surface. The
corrected case totals are small relative to the naive inner-wall radiation
basis and are bounded enough to justify continued train-context development.

## Inferred

PASSIVE-H2 has predictive-model potential as a physically bounded passive
operator, but only after split-label conflicts and implementation semantics are
resolved. Salt3/4 are included here under the existing setup-UQ train-only
labels, not as protected scores or admission evidence.

## Caveats

This row performs no fitting, no new Fluid solve, and no protected scoring. It
does not release numeric q-loss, Qwall, source properties, coefficients, a
candidate freeze, or a final score.

## Next Useful Actions

If continuing, claim a separate Fluid execution row that implements the
corrected outer-surface operator directly and runs only explicitly admitted
development/train cases. Keep radiation semantics and split labels visible in
the output contract.
