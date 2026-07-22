---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_salt14_postprocessing_inventory_model_form_package/README.md
  - work_products/2026-07/2026-07-22/2026-07-22_salt14_postprocessing_inventory_model_form_package/salt14_model_form_use_cases.csv
tags: [salt1-4, postprocessing, model-form, start-here]
related:
  - .agent/status/2026-07-22_TODO-SALT14-POSTPROCESSING-INVENTORY-MODEL-FORM-PACKAGE-2026-07-22.md
  - .agent/journal/2026-07-22/salt14-postprocessing-inventory-model-form-package.md
task: TODO-SALT14-POSTPROCESSING-INVENTORY-MODEL-FORM-PACKAGE-2026-07-22
date: 2026-07-22
role: Writer/Implementer
type: operational_note
status: complete
---
# Salt1-4 postProcessing inventory start-here

## Why this exists

The Salt1-4 OpenFOAM `postProcessing` folders contain high-value diagnostic
evidence for model-form work: flow monitors, wall heat-flow, total heat flow,
temperature probes, wall-temperature probes, PIV slab values, yPlus,
wallShearStress, and velocity profiles. This package makes those values usable
without mutating native solver outputs or relaxing predictive runtime-input
guardrails.

## Files to open first

1. `work_products/2026-07/2026-07-22/2026-07-22_salt14_postprocessing_inventory_model_form_package/README.md`
2. `work_products/2026-07/2026-07-22/2026-07-22_salt14_postprocessing_inventory_model_form_package/summary.json`
3. `work_products/2026-07/2026-07-22/2026-07-22_salt14_postprocessing_inventory_model_form_package/salt14_model_form_use_cases.csv`
4. `work_products/2026-07/2026-07-22/2026-07-22_salt14_postprocessing_inventory_model_form_package/salt14_postprocessing_window_stats.csv`
5. `work_products/2026-07/2026-07-22/2026-07-22_salt14_postprocessing_inventory_model_form_package/salt14_case_delta_matrix.csv`

## Trusted package

The task-owned builder is
`tools/analyze/build_salt14_postprocessing_inventory_model_form_package.py`.
It reuses parser semantics from `tools/extract/postprocessing_registry_common.py`
but writes a separate work-product package.

## Output contract

- `salt14_postprocessing_tidy.csv`: tidy function-object values with explicit
  `function_object`, `quantity`, `sign_convention`, and `admissibility_role`.
- `salt14_postprocessing_window_stats.csv`: terminal-window mean/std/drift.
- `salt14_case_delta_matrix.csv`: selected nominal/variant/source-family
  deltas.
- `salt14_model_form_use_cases.csv`: documented thermal and hydraulic use
  cases.
- `salt14_inventory_manifest.csv`: source coverage and bounded parsing metadata.

## Unresolved blockers

- Full velocity-profile histories are not expanded by default; latest profile
  time is parsed and full profile coverage is recorded.
- Any setup-safe feature or model-form candidate derived from this evidence
  requires a new gate row before fitting, release, or admission.

## Next task sequence

1. Thermal use case: rank heat-flow and TP/TW drift patterns, then propose a
   setup-safe source/sink or passive-loss feature if one exists.
2. Hydraulic use case: compare mdot stability, profile shape, yPlus, and wall
   shear to propose pressure/recirculation model-form diagnostics.
3. If either use case identifies a candidate feature, open a separate release
   gate with split-role and runtime-input audits.

## Do-not-do guardrails

Do not mutate native `postProcessing` folders. Do not use realized CFD `mdot`,
realized `wallHeatFlux`, `total_Q`, or probe/wall temperatures as forbidden predictive
runtime inputs. Do not fit, tune, admit, release source/property labels, release
Qwall, claim a final score, or trigger S11/S12/S13/S15/S6 from this package
alone.
