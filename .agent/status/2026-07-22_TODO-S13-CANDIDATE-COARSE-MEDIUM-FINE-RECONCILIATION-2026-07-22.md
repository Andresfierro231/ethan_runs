---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_s13_candidate_coarse_medium_fine_reconciliation/summary.json
  - work_products/2026-07/2026-07-22/2026-07-22_s13_candidate_coarse_medium_fine_reconciliation/candidate_triplet_reconciliation.csv
  - work_products/2026-07/2026-07-22/2026-07-22_s13_candidate_coarse_medium_fine_reconciliation/qoi_reconciliation_summary.csv
tags: [status, s13, recirculation, exchange-cell, mesh-gci, coarse-equivalence]
related:
  - .agent/journal/2026-07-22/s13-candidate-coarse-medium-fine-reconciliation.md
  - imports/2026-07-22_s13_candidate_coarse_medium_fine_reconciliation.json
task: TODO-S13-CANDIDATE-COARSE-MEDIUM-FINE-RECONCILIATION-2026-07-22
date: 2026-07-22
role: Hydraulics / Thermal-modeling / cfd-pp / Mesh-GCI / Implementer / Tester / Writer / Reviewer
type: status
status: complete
---
# TODO-S13-CANDIDATE-COARSE-MEDIUM-FINE-RECONCILIATION-2026-07-22

## Objective

Reconcile current-coarse S13 candidate rows with the canonical medium/fine
exact-label split rerun after the split rerun landed, quantify diagnostic
coarse/medium/fine behavior, and decide whether this clears formal GCI or
production/admission gates.

## Outcome

Complete. The package decision is
`candidate_triplets_quantified_formal_gci_fail_closed_coarse_equivalence_not_admitted`.

The row produced `12` candidate triplet rows and `4` QOI summary rows. Current
coarse candidate rows exist for all Salt2/Salt3/Salt4 and all four S13 QOIs, and
medium/fine exact-label rows now exist from the canonical split rerun. However,
the completed coarse-equivalence contract admits `0` current-coarse rows as
same-label coarse mesh evidence, so formal GCI was not run and production,
release, fitting, scoring, and downstream triggers remain closed.

Key quantified results:

- `Q_wall_W`: maximum candidate coarse/fine spread is
  `1.5759092529218661%` versus fine; maximum medium/fine spread remains
  `0.5029174998089355%`. This is useful diagnostic heat-flow evidence only.
- Proxy QOIs: maximum candidate coarse/fine spread reaches
  `304.85360007488%`, so exchange flux, residence time, and wall/core/bulk
  contrast remain non-admissible.

## Changes Made

- Added reusable builder:
  `tools/analyze/build_s13_candidate_coarse_medium_fine_reconciliation.py`.
- Added focused tests:
  `tools/analyze/test_s13_candidate_coarse_medium_fine_reconciliation.py`.
- Generated work-product package:
  `work_products/2026-07/2026-07-22/2026-07-22_s13_candidate_coarse_medium_fine_reconciliation/`.
- Generated:
  `candidate_triplet_reconciliation.csv`,
  `qoi_reconciliation_summary.csv`,
  `production_admission_gate.csv`,
  `source_manifest.csv`, `summary.json`, and `README.md`.
- Updated this status, matching journal, import manifest, and own board row.

## Validation

- `python3.11 tools/analyze/build_s13_candidate_coarse_medium_fine_reconciliation.py`:
  passed; generated `12` candidate triplet rows and `4` QOI summary rows.
- `python3.11 -m pytest tools/analyze/test_s13_candidate_coarse_medium_fine_reconciliation.py`:
  passed, `5` tests.
- `python3.11 -m py_compile tools/analyze/build_s13_candidate_coarse_medium_fine_reconciliation.py tools/analyze/test_s13_candidate_coarse_medium_fine_reconciliation.py`:
  passed.

## Guardrails

- Native CFD/OpenFOAM outputs mutated: `false`.
- Registry/admission state mutated: `false`.
- Scheduler action: `false`.
- Solver/OpenFOAM postProcess/sampler/harvest/UQ launched: `false`.
- Formal GCI run/admitted: `false`.
- Production harvest/admission: `false`.
- Source/property or Qwall release: `false`.
- Coefficient fitting/admission: `false`.
- Validation/holdout/external-test scoring: `false`.
- S11/S12/S13/S15/S6 trigger: `false`.
- Fluid/external/thesis body mutation: `false`.

## Next Useful Action

Use this result as the terminal S13 mesh/GCI diagnostic for now. Additional S13
coefficient work is not justified until either the coarse-equivalence criteria
are satisfied by auditable same-basis evidence or a new strict coarse/medium/fine
same-label extraction family is generated. For thesis progress, route
`Q_wall_W` as diagnostic heat-flow evidence and keep proxy coefficients closed.
