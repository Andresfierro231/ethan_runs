---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_heatloss_phase_2_split_heat_loss_evidence/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_thermal_heat_loss_contract_alignment/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_cfd_postprocessing_schema_gap/README.md
tags: [litrev, heat-loss, junction, storage, radiation, no-admission]
related:
  - .agent/status/2026-07-21_TODO-LITREV-SPLIT-JUNCTION-STORAGE-RADIATION-EXTRACTION.md
  - .agent/journal/2026-07-21/litrev-split-junction-storage-radiation-extraction.md
task: TODO-LITREV-SPLIT-JUNCTION-STORAGE-RADIATION-EXTRACTION
date: 2026-07-21
role: Thermal-modeling/cfd-pp/Tester/Writer
type: work_product
status: complete
supersedes: []
superseded_by:
---
# LitRev Split Junction Storage Radiation Extraction

## Decision

The current split-junction rows are diagnostic extraction/readiness evidence
only. They separate lower-left, lower-right, upper-left, and upper-right
junction/stub families, but the split is still from grouped junction
wallHeatFlux and is not an admitted per-family target.

## Results

- Split junction/stub rows: `12`.
- Junction family summary rows: `4`.
- Missing field rows: `5`.
- Radiation `qr` admitted rows: `0`.
- Storage admitted rows: `0`.
- Internal-Nu residual absorption rows: `0`.

## Outputs

- `split_heat_extraction_readiness.csv`
- `junction_family_summary.csv`
- `heat_path_owner_separation.csv`
- `missing_field_do_not_infer.csv`
- `runtime_legality_guardrail.csv`
- `source_manifest.csv`
- `summary.json`

## Guardrails

No native source-output mutation, scheduler action, staged-copy/postprocessing
launch, registry/admission mutation, Fluid edit, external edit, fitting, model
selection, generated-index refresh, or internal-`Nu` residual absorption was
performed.
