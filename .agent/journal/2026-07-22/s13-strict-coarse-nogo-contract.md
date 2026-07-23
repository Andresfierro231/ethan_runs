---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_s13_strict_coarse_nogo_contract/strict_coarse_equivalence_criteria.csv
  - work_products/2026-07/2026-07-22/2026-07-22_s13_strict_coarse_nogo_contract/qoi_formal_gci_no_go_matrix.csv
  - work_products/2026-07/2026-07-22/2026-07-22_s13_coarse_equivalence_open_cv_heatflow_contract/coarse_basis_resolution.csv
tags: [journal, s13, recirculation, coarse-equivalence, mesh-gci]
related:
  - .agent/status/2026-07-22_TODO-S13-STRICT-COARSE-NOGO-CONTRACT-2026-07-22.md
  - work_products/2026-07/2026-07-22/2026-07-22_s13_strict_coarse_nogo_contract/README.md
  - imports/2026-07-22_s13_strict_coarse_nogo_contract.json
task: TODO-S13-STRICT-COARSE-NOGO-CONTRACT-2026-07-22
date: 2026-07-22
role: Hydraulics / Thermal-modeling / cfd-pp / Mesh-GCI / Implementer / Tester / Writer / Reviewer
type: journal
status: complete
---
# S13 Strict Coarse No-Go Contract

## Attempted

I addressed the next clean S13 blocker after sampler/GCI readiness: strict
same-label coarse equivalence. The work consumed the existing coarse/open-CV
contract, current coarse basis-resolution rows, candidate coarse/medium/fine
reconciliation, and latest medium/fine exact-label sampler gate.

## Observed

Current coarse candidate values exist for all `12` Salt2/Salt3/Salt4 case/QOI
rows, but they are reconstructed reference candidates. The existing strict
mesh-level preflight reports `0;0;0` admitted coarse/medium/fine rows and
`direct_same_label_coarse_admitted=false` for every case/QOI row.

The latest medium/fine exact-label sampler evidence is complete with `72`
QOI rows. That solves medium/fine availability, but it does not solve coarse
equivalence.

## Inferred

Formal GCI should remain closed. The no-go is not a numerical spread problem
alone; it is an evidence-basis problem. A candidate coarse value, even one close
to medium/fine for `Q_wall_W`, cannot be promoted unless geometry masks, time
window, field/property basis, residual/accounting basis, and same-QOI UQ/mesh
disposition are admitted on the exact labels.

`Q_wall_W` is still the highest-value heat-flow direction because its medium/fine
spread is small. The clean path is source-side heat-flow equivalence on the
same basis, not relabeling source-side heat flow as wall `Q_wall_W`.

## Caveats

This pass did not sample new coarse fields and did not run formal GCI. It is a
contract/disposition package over existing evidence. If a later row produces
direct same-label coarse rows, this no-go package should be treated as the
pre-admission baseline and rerun.

`task_context.py` noted a broad trigger-gated S11 row overlapping
`tools/analyze/` by pattern. This work stayed in fresh S13-specific paths and
did not touch S11 candidate/source-property files.

## Next Useful Actions

1. Generate or admit direct same-label coarse rows with topology-derived coarse
   CV, exchange interface, wall/core band, face normals/areas, field/property
   basis, and same window role matching medium/fine exact labels.
2. Rerun the formal GCI gate only after admitted same-label coarse rows exist.
3. Execute same-QOI UQ for exact exchange-cell QOIs before production harvest,
   exchange-cell residual admission, or coefficient fitting.

Hardening update: added `replacement_coarse_dataset_contract.csv` so the
replacement path is machine-readable. The required artifacts are coarse face
geometry, coarse QOI rows, a coarse open-CV residual ledger, and triplet
admission-gate rows. Candidate face ids, reconstructed current coarse rows,
two-level evidence, and source-side heat flow relabeled as `Q_wall_W` are
explicitly forbidden substitutions.
