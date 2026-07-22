---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_evidence_packet_ch1_ch4_foundations/README.md
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_evidence_packet_ch1_ch4_foundations/source_path_ledger.csv
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_evidence_packet_ch1_ch4_foundations/equations_definitions_ledger.csv
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_evidence_packet_ch1_ch4_foundations/claim_boundary_ledger.csv
tags: [thesis, external-writer, chapter-1, chapter-4]
related:
  - README.md
  - source_path_ledger.csv
  - equations_definitions_ledger.csv
  - claim_boundary_ledger.csv
task: TODO-THESIS-EVIDENCE-PACKET-CH1-CH4-FOUNDATIONS-2026-07-22
date: 2026-07-22
role: Coordinator/Writer/Reviewer
type: writer-brief
status: current
---
# External Writer Brief: Ch1-Ch4 Foundations

## One-sentence Thesis Frame

This thesis develops a provenance-controlled CFD-to-1D closure/admission
workflow for a CSEM-relevant molten-salt natural-circulation loop, using CFD as
high-fidelity reference evidence rather than experimental validation.

## Write Now

- Chapter 1 can describe the motivation, problem, contribution, scope, research
  questions, and non-claims.
- Chapter 4 can describe the reduction method, pressure and thermal ledgers,
  evidence classes, split roles, runtime-leakage policy, source/property gates,
  and admission labels.

## Do Not Write Yet

- Do not report final predictive model performance.
- Do not admit a final Nu, f_D, K, F6, wall, test-section, or recirculation
  closure.
- Do not claim SAM validation or experimental validation.
- Do not use holdout or external-test rows to tune, select, or justify a
  closure.

## Phrases That Are Safe

- "high-fidelity CFD reference"
- "closure/admission workflow"
- "diagnostic evidence"
- "source-bounded model slot"
- "split-aware predictive-use contract"
- "residual-owner separation before fitting"
- "section-effective pressure residual"
- "blocked admission path"

## Phrases To Avoid

- "validated against experiment"
- "SAM-validated"
- "final predictive closure"
- "calibrated using the validation temperature"
- "CFD wall heat flux was supplied to the predictor"
- "negative component loss coefficient" unless a future source-matched task
  admits it.

## Minimum Evidence To Cite In Prose

- Ch1 frame: `reports/thesis_dossier/Chapters_and_sections/current/15_ch1_csem_motivation_and_contribution.md`.
- Ch4 model forms: `reports/thesis_dossier/Chapters_and_sections/current/01_modeling_approach.md` and `02_model_form_fluid_walls.md`.
- Split/leakage: `03_split_policy_and_evidence_classes.md`.
- Claim boundaries: `08_thesis_claim_ledger.md`.
- LitRev/source gate: `25_litrev_csem_thesis_incorporation.md` and
  `work_products/2026-07/2026-07-21/2026-07-21_litrev_model_form_extraction/`.
- Current target Chapter 4: `../papers/UTexas_Research/csem-Masters_dissertation/chapters/04_cfd_to_1d_reduction.tex`.

