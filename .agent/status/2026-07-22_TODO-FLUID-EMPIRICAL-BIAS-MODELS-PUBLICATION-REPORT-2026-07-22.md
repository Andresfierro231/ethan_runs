---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_fluid_empirical_bias_models_publication_report/report.md
  - work_products/2026-07/2026-07-22/2026-07-22_fluid_empirical_bias_models_publication_report/model_family_publication_table.csv
tags: [forward-model, empirical-bias, publication-report]
related:
  - .agent/journal/2026-07-22/fluid-empirical-bias-models-publication-report.md
  - imports/2026-07-22_fluid_empirical_bias_models_publication_report.json
task: TODO-FLUID-EMPIRICAL-BIAS-MODELS-PUBLICATION-REPORT-2026-07-22
date: 2026-07-22
role: Writer/Reviewer/Tester
type: status
status: complete
---
# TODO-FLUID-EMPIRICAL-BIAS-MODELS-PUBLICATION-REPORT-2026-07-22

## Objective

Write a rigorous numerical-scientific publication report for the empirical
temperature bias/correction models, including equations, assumptions, caveats,
why the model may work, claim boundaries, and recommended discrepancy studies.

## Outcome

Published
`work_products/2026-07/2026-07-22/2026-07-22_fluid_empirical_bias_models_publication_report/`.

The main report argues for a bounded diagnostic claim: the empirical correction
results show a stable low-dimensional 1D/3D temperature discrepancy, not an
admitted physical closure. The recommended publication-facing diagnostic model
is `F2_global_affine` because it transfers nearly as well as `F5` with only two
degrees of freedom.

## Changes Made

- Added `README.md`.
- Added `report.md`.
- Added `model_family_publication_table.csv`.
- Added `claim_boundary_table.csv`.
- Added `follow_on_studies.csv`.
- Added `source_manifest.csv`.
- Updated `.agent/BOARD.md`.
- Added status, journal, and import manifest.

## Validation

- `python3.11 -c "import csv, pathlib; ..."` parsed all report CSVs:
  `model_family_publication_table.csv` (`6` rows),
  `claim_boundary_table.csv` (`7` rows),
  `follow_on_studies.csv` (`6` rows), and `source_manifest.csv` (`10` rows).
- `wc -l .../report.md .../README.md` reported `304` report lines and `36`
  README lines.
- `rg -n "admitted|admission|external-test|source/property|forbidden|diagnostic" .../report.md`
  confirmed explicit claim-boundary and caveat language.

## Guardrails

- Native CFD/OpenFOAM outputs mutated: no.
- Registry/admission state mutated: no.
- Scheduler action: no.
- Solver/postprocessing/sampler/harvest/UQ launch: no.
- Fluid/external edit: no.
- Thesis current-file edit: no.
- Validation/holdout/external-test scoring: no new scoring.
- New fitting/tuning/model selection: no.
- Source/property release: no.
- Coefficient or final predictive admission: no.
- Blocker register changed: no.
- Generated docs index changed: no.
- Residual absorbed into internal Nu: no.

## Remaining Blockers

The publication report remains diagnostic until a runtime-legal Fluid
multi-split sensor table exists, source/property labels pass, and an
external-test artifact is scored after freeze with no coefficient changes.

