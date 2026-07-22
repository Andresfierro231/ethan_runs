---
provenance:
  - reports/thesis_dossier/Chapters_and_sections/current/08_thesis_claim_ledger.md
  - reports/thesis_dossier/Chapters_and_sections/current/18_ch6_csem_closure_admission_uncertainty.md
  - reports/thesis_dossier/Chapters_and_sections/current/21_csem_figure_table_incorporation_package.md
  - .agent/BLOCKERS.md
tags: [work-product, thesis-review, csem, checklist]
related:
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_csem_current_draft_packet/README.md
task: TODO-THESIS-CSEM-CURRENT-DRAFT-PACKET-2026-07-21
date: 2026-07-21
role: Reviewer/Writer
type: work_product
status: complete
supersedes: []
superseded_by:
---
# Reviewer Checklist

Use this checklist before importing the current CSEM thesis packet into an
external manuscript.

## Claim Control

- Every major result maps to a claim ID in
  `reports/thesis_dossier/Chapters_and_sections/current/08_thesis_claim_ledger.md`.
- CFD is described as the current high-fidelity reference, not experimental
  validation.
- LitRev equations and correlations are described as source-envelope gates
  unless a TAMU admission package exists.
- Negative results remain visible and are not rewritten as successful closure
  admissions.

## Runtime Leakage

Confirm predictive prose does not use these as runtime inputs:

- CFD `mdot`;
- realized CFD `wallHeatFlux`;
- imposed CFD cooler duty;
- realized test-section heat;
- validation or holdout temperatures;
- scored-row pressure or heat targets.

Allowed use: target evidence, diagnostic replay evidence, blocker evidence, or
caption caveat.

## Blocker Boundary

Do not convert any of these into completed claims:

- final frozen predictive performance;
- passive wall/test-section closure;
- lower-right corner ordinary component `K`;
- F6 friction/Re recorrection;
- ordinary upcomer single-stream `Nu`, `f_D`, or `K`;
- SAM validation;
- Salt-versus-Water synthesis.

## Figure And Table Captions

- Every figure/table caption names source path or package.
- Diagnostic pressure figures state that current corner rows are not admitted
  ordinary component `K`.
- Thermal figures distinguish heater/cooler setup-facing evidence from passive
  wall/test-section blockers.
- SAM-facing figures say transfer of closure discipline, not validation.
