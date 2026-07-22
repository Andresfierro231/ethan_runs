---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_s13_medium_fine_mesh_gci_disposition/summary.json
  - work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_same_label_mesh_family_generation/same_label_mesh_family_generated_rows.csv
  - work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_same_label_mesh_family_generation/qoi_mesh_level_preflight_matrix.csv
  - work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_same_qoi_neighbor_uq_after_target_plus/heat_flow_match_diagnostics.csv
tags: [work-product, s13, recirculation, open-cv, coarse-equivalence, source-side-heat-flow]
related:
  - .agent/status/2026-07-22_TODO-S13-COARSE-EQUIVALENCE-OPEN-CV-HEATFLOW-CONTRACT-2026-07-22.md
  - .agent/journal/2026-07-22/s13-coarse-equivalence-open-cv-heatflow-contract.md
task: TODO-S13-COARSE-EQUIVALENCE-OPEN-CV-HEATFLOW-CONTRACT-2026-07-22
date: 2026-07-22
role: Hydraulics / Thermal-modeling / cfd-pp / Mesh-GCI / Implementer / Tester / Writer
type: work_product
status: complete
---
# S13 Coarse-Equivalence / Open-CV / Heat-Flow Contract

Decision: `coarse_reference_candidate_only_equivalence_contract_defined_no_gci_no_admission`.

Current-coarse reconstructed rows exist and are useful as reference candidates,
but they are not admitted as same-label coarse evidence for formal GCI. The
contract in this package states the criteria required to admit them later.

Open recirculation CVs are allowed for diagnostics if all open-boundary terms,
signs, and residuals are explicit. A closed or residual-complete CV is required
before exchange-cell coefficient fitting or admission.

`Q_wall_W` is the only S13 exchange QOI with low medium/fine spread, so heat-flow
matching should focus on source-side heat-flow equivalence and the same-basis
energy residual. Source-side heat flow remains a distinct QOI and must not be
relabeled as `Q_wall_W`.
