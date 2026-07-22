---
provenance:
  - tools/extract/postprocessing_registry_common.py
  - tools/analyze/build_salt14_postprocessing_inventory_model_form_package.py
  - work_products/2026-07/2026-07-22/2026-07-22_salt14_postprocessing_inventory_model_form_package/summary.json
tags: [salt1-4, postprocessing, model-form, journal]
related:
  - .agent/status/2026-07-22_TODO-SALT14-POSTPROCESSING-INVENTORY-MODEL-FORM-PACKAGE-2026-07-22.md
  - imports/2026-07-22_salt14_postprocessing_inventory_model_form_package.json
task: TODO-SALT14-POSTPROCESSING-INVENTORY-MODEL-FORM-PACKAGE-2026-07-22
date: 2026-07-22
role: Implementer/Tester/Writer/Reviewer
type: journal
status: complete
---
# Salt1-4 postProcessing inventory model-form package

## Attempted

Built a task-scoped inventory that scans registered Salt1-4 `postProcessing`
trees and normalizes function-object values into one tidy schema with explicit
function object, quantity, sign convention, and admissibility role columns.

## Observed

The existing `postprocessing_registry_common.py` parser covered most required
families, but full histories are dense. The initial direct parser path was too
slow for a single filtered case because dense function-object files can contain
large histories. The builder was changed to terminal-window parsing by default:
it scans all relevant source folders, seeks from the end of each function-object
file, and parses the last `500` data rows per file. Velocity profiles are
parsed at the latest profile time by default while total profile directory/file
coverage is recorded in the manifest.

The final package parsed all `23` registered Salt1-4 sources and wrote
`1,405,596` tidy rows, `16,353` window-stat rows, `110` case-delta rows, and
`2` model-form use-case rows.

## Inferred

The postProcessing inventory is immediately useful for diagnostic model-form
work: thermal source/sink imbalance, flow stability, profile-shape comparison,
wall-resolution adequacy, and source-family/perturbation deltas. It does not
release any realized CFD quantity into predictive runtime.

## Caveats

This is a terminal-window diagnostic package, not a full-history profile
archive. A later heavy row can rerun with `--profile-mode all` if full velocity
profile histories are needed. The package is large because the tidy CSV keeps
absolute source paths and terminal rows for dense function-object families.

## Next Useful Actions

1. Use `salt14_postprocessing_window_stats.csv` to rank stable windows and
   drift-sensitive QOIs.
2. Use `salt14_case_delta_matrix.csv` to identify nominal Salt1-4 trends,
   Kirst/Jin differences, and corrected-Q response slopes.
3. Start a separate model-form gate if a derived feature looks setup-safe.
4. Do not use realized CFD `mdot`, realized `wallHeatFlux`, `total_Q`, or probe
   temperatures as predictive runtime inputs.
