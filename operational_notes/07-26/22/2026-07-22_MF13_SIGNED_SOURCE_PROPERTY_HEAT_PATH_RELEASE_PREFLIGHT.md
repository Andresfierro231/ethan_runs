---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_mf12_bulk_to_tp_formula_gate/next_study_queue.csv
  - work_products/2026-07/2026-07-22/2026-07-22_mf13_signed_source_property_heat_path_release_preflight/README.md
tags: [operational-note, mf13, predictive-model, source-property]
related:
  - operational_notes/07-26/22/2026-07-22_MF12_BULK_TO_TP_FORMULA_GATE.md
  - .agent/status/2026-07-22_TODO-MF13-SIGNED-SOURCE-PROPERTY-HEAT-PATH-RELEASE-PREFLIGHT-2026-07-22.md
task: TODO-MF13-SIGNED-SOURCE-PROPERTY-HEAT-PATH-RELEASE-PREFLIGHT-2026-07-22
date: 2026-07-22
role: Thermal-modeling / Forward-pred / Implementer / Tester / Writer / Reviewer
type: operational_note
status: complete
---
# MF13 Signed Source/Property Heat-Path Release Preflight

## Why This Exists

MF12 proposed physically interpretable bulk-to-TP formulas, but those formulas
need signed heat-path inputs: heater/cooler/test-section/passive source terms,
source placement, and property basis. MF13 is the strict preflight that decides
whether those inputs are released now.

## Open First

- `work_products/2026-07/2026-07-22/2026-07-22_mf13_signed_source_property_heat_path_release_preflight/README.md`
- `work_products/2026-07/2026-07-22/2026-07-22_mf13_signed_source_property_heat_path_release_preflight/signed_heat_path_release_preflight.csv`
- `work_products/2026-07/2026-07-22/2026-07-22_mf13_signed_source_property_heat_path_release_preflight/source_property_release_gate.csv`
- `work_products/2026-07/2026-07-22/2026-07-22_mf13_signed_source_property_heat_path_release_preflight/next_study_queue.csv`
- `work_products/2026-07/2026-07-22/2026-07-22_mf12_bulk_to_tp_formula_gate/next_study_queue.csv`

## Trusted Packages

- MF08 signed wall-flux/developing thermal branches package.
- MF12 bulk-to-TP formula gate.
- Thesis thermal-accounting traceability evidence packet.
- Setup-known source/sink runtime contract package.

## Result

Decision: `signed_source_property_release_preflight_fail_closed`.

The package has four source-family rows. Three active source/sink families have
setup-known sign and magnitude metadata:

- `heater/lower_leg`: positive fluid heating.
- `cooler/cooling_branch`: negative fluid cooling.
- `test_section/upcomer`: positive fluid heating.

None are runtime/source-property released. Passive/downcomer is still blocked
by missing independent hA/source-family basis.

## Output Contract

MF13 outputs diagnostic evidence only. It does not release source/property
fields and does not authorize a Fluid solve, train smoke run, protected scoring,
coefficient admission, final score, or residual absorption into internal Nu.

## Next Task Sequence

1. `same_qoi_tp_projection_uq`
2. `runtime_wall_profile_basis_for_tp_projection`
3. `source_property_label_release_candidate_after_exact_fields`
4. `train_only_mf12_formula_smoke_after_release`
5. `tw_after_tp_residual_ownership`

## Do Not Do

Do not use Salt3/Salt4 values for fitting or model selection. Do not treat
setup-known source signs as runtime source/property releases. Do not repair
passive heat loss with a global multiplier. Do not run MF12 formulas until both
source/property and TP-projection gates pass.
