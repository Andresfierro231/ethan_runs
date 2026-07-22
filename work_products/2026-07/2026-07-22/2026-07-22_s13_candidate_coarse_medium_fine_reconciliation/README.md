---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_s13_medium_fine_exact_label_split_rerun/aggregated_exact_label_qoi_rows.csv
  - work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_same_label_mesh_family_generation/same_label_mesh_family_generated_rows.csv
  - work_products/2026-07/2026-07-22/2026-07-22_s13_coarse_equivalence_open_cv_heatflow_contract/coarse_basis_resolution.csv
tags: [work-product, s13, recirculation, exchange-cell, mesh-gci, fail-closed]
related:
  - .agent/status/2026-07-22_TODO-S13-CANDIDATE-COARSE-MEDIUM-FINE-RECONCILIATION-2026-07-22.md
  - .agent/journal/2026-07-22/s13-candidate-coarse-medium-fine-reconciliation.md
task: TODO-S13-CANDIDATE-COARSE-MEDIUM-FINE-RECONCILIATION-2026-07-22
date: 2026-07-22
role: Hydraulics / Thermal-modeling / cfd-pp / Mesh-GCI / Implementer / Tester / Writer
type: work_product
status: complete
---
# S13 Candidate Coarse/Medium/Fine Reconciliation

Decision: `candidate_triplets_quantified_formal_gci_fail_closed_coarse_equivalence_not_admitted`.

This package joins the canonical medium/fine exact-label split rerun with the
current-coarse candidate rows from the same-label mesh-family generation
package. It reports candidate three-level behavior, but it does not run or admit
formal GCI because the completed coarse-equivalence contract admits `0`
current-coarse rows as same-label coarse mesh evidence.

`Q_wall_W` remains the only low-spread medium/fine diagnostic lane. The exchange
flux, residence-time, and wall/core/bulk contrast proxies remain diagnostic and
not coefficient-admissible.

## Guardrails

No native solver output, registry/admission state, scheduler state, Fluid source,
external repo, thesis body, source/property release, Qwall release, coefficient
fit, validation/holdout/external score, production harvest, or formal GCI
admission was mutated.
