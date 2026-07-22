---
provenance:
  - operational_notes/maps/forward-predictive-model.md
  - operational_notes/maps/thermal-closures-and-internal-nu.md
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_thermal_heat_loss_contract_alignment/heat_loss_path_contract.csv
  - work_products/2026-07/2026-07-21/2026-07-21_extbc_source_sink_provenance_recovery/setup_source_sink_provenance_ledger.csv
  - work_products/2026-07/2026-07-22/2026-07-22_s12_thermal_residual_candidate_disposition_and_thesis_panels/README.md
tags: [predictive-1d, thermal-ledger, residual-owner, runtime-leakage, publication-evidence]
related:
  - .agent/status/2026-07-22_TODO-1D-CONSERVATIVE-THERMAL-LEDGER-RESIDUAL-OWNER-CONTRACT-2026-07-22.md
  - .agent/journal/2026-07-22/1d-conservative-thermal-ledger-residual-owner-contract.md
  - imports/2026-07-22_1d_conservative_thermal_ledger_residual_owner_contract.json
task: TODO-1D-CONSERVATIVE-THERMAL-LEDGER-RESIDUAL-OWNER-CONTRACT-2026-07-22
date: 2026-07-22
role: Forward-pred / Thermal-modeling / Writer / Reviewer / Tester
type: work_product
status: complete
---
# 1D Conservative Thermal Ledger Residual-Owner Contract

Generated: `2026-07-22T14:30:47.473520+00:00`

Decision: `contract_ready_no_candidate_release_no_runtime_leakage`.

This package defines the model-facing heat ledger before any fitting. It keeps
heater input, cooler/HX removal, passive wall exchange, test-section/quartz
terms, wall/layer resistance, radiation, storage, recirculation/exchange, and
the final residual as separate terms. The residual is an output and owner label,
not a closure.

## Core Equation

With positive heat into the salt-side control volume,

`R_s = sum(Q_known_s) - mdot_model * cp * (T_out_s - T_in_s)`.

For predictive runtime, `mdot_model`, wall states, and temperatures must be
computed by the 1D model from setup inputs. CFD `mdot`, realized CFD
`wallHeatFlux`, imposed CFD cooler duty, realized test-section heat, and
validation/holdout temperatures are forbidden runtime inputs.

## Files

- `conservative_equation_ledger.csv`: 12 equation/term rows.
- `runtime_allowed_input_list.csv`: 10 setup/model-state input rows.
- `runtime_forbidden_audit.csv`: 8 forbidden runtime inputs, all marked `false`.
- `missing_setup_fields.csv`: 7 missing or incomplete setup fields.
- `candidate_handoff_table.csv`: 5 next-task handoff rows.
- `residual_owner_contract.csv`: 8 residual owner families.
- `source_manifest.csv`, `no_mutation_guardrails.csv`, `summary.json`.

## Scientific Use

Use this as the thermal accounting contract for the next 1D model stages and for
publication methods prose. It supports a claim that current negative thermal
results are organized residual-owner evidence, not proof that internal `Nu` or a
global heat multiplier should be fitted.

## Guardrails

No solver, sampler, scheduler job, Fluid edit, external thesis/LaTeX edit,
registry/admission mutation, source/property release, fit, model selection, or
final score was performed.
