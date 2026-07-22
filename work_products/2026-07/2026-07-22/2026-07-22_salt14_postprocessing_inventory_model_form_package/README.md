---
provenance:
  generated_by: TODO-SALT14-POSTPROCESSING-INVENTORY-MODEL-FORM-PACKAGE-2026-07-22
  generated_at: 2026-07-22T10:43:25-05:00
tags: [salt1-4, postprocessing, model-form, diagnostic-evidence]
related:
  - tools/extract/postprocessing_registry_common.py
  - registry/case_registry.csv
---

# Salt1-4 postProcessing inventory and model-form evidence package

This package normalizes registered Salt1-4 OpenFOAM `postProcessing` outputs
into a tidy diagnostic table. It is designed to make the existing function
objects usable for model-form reasoning: heat-flow balance, mass-flow
stability, profile-shape comparison, wall-resolution checks, wall-shear support,
and case-to-case/source-family deltas.

Decision: `postprocessing_inventory_published_diagnostic_only_no_runtime_release`.

## Outputs

- `salt14_postprocessing_tidy.csv`: one row per parsed function-object value.
- `salt14_postprocessing_window_stats.csv`: window mean/std/drift/min/max by
  source/function/quantity/entity.
- `salt14_case_delta_matrix.csv`: nominal and variant deltas for selected
  model-form diagnostic quantities.
- `salt14_model_form_use_cases.csv`: two documented model-form use cases.
- `salt14_inventory_manifest.csv`: source coverage, missing function objects,
  and profile scan metadata.

Velocity-profile mode: `latest`. The default task mode parses the
latest available velocity-profile time per source and records total profile
directory/file coverage in the manifest. Use `--profile-mode all` only in a
separate heavy row if full profile history is needed.

## Guardrails

Native solver outputs are read-only. No OpenFOAM `postProcess`, solver launch,
scheduler action, registry/admission mutation, Fluid edit, coefficient
admission, source/property release, Qwall release, final-score claim, or S13
label substitution is performed.

Realized CFD `mdot`, realized `wallHeatFlux`, `total_Q`, and probe/wall
temperatures are marked `diagnostic_only_forbidden_runtime_input`. They may be
used to explain errors, compare cases, quantify drift/UQ support, and design
candidate model forms; they are not predictive runtime inputs.
