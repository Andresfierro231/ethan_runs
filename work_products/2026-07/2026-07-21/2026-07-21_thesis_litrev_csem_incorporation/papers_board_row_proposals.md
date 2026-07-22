---
task: TODO-THESIS-LITREV-CSEM-INCORPORATION-PACKAGE-2026-07-21
date: 2026-07-21
role: Coordinator / Writer / Reviewer
type: board-proposal
status: proposed
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_litrev_csem_incorporation/latex_insertion_manifest.csv
  - ../papers/.agent/BOARD.md
  - ../papers/UTexas_Research/csem-Masters_dissertation/README.txt
tags: [papers-board, csem-thesis, litrev-incorporation]
related:
  - operational_notes/07-26/21/2026-07-21_THESIS_LITREV_CSEM_INCORPORATION_START_HERE.md
---
# Proposed Papers-Board Rows

These rows are intended for `../papers/.agent/BOARD.md`. They are not applied
by this Ethan task because the papers workspace is a separate coordination
root and is read-only from this task scope.

## Backlog Rows To Add

| Task ID | Requested role | Goal | Likely paths | Notes |
| --- | --- | --- | --- | --- |
| `csem-litrev-background-source-envelope-2026-07-21` | Writer / Reviewer | Add LitRev source-envelope and safe/unsafe closure wording to the CSEM background/literature chapter. | `UTexas_Research/csem-Masters_dissertation/chapters/02_background_literature.tex`, papers status/journal files. | Use Ethan package `source_envelope_thesis_table.csv`. No TAMU coefficient admission. |
| `csem-litrev-reduction-pressure-contract-2026-07-21` | Writer / Reviewer | Add CFD-to-1D pressure and thermal reduction contracts, including pressure-corner basis and coefficient naming rules. | `UTexas_Research/csem-Masters_dissertation/chapters/04_cfd_to_1d_reduction.tex`, papers status/journal files. | Use `pressure_corner_thesis_rules.csv` and LitRev `cfd_postprocessing_contract.csv`. |
| `csem-litrev-model-form-admission-2026-07-21` | Writer / Reviewer | Integrate MF-01 to MF-06 model-form hierarchy and no-silent-threshold admission rules. | `UTexas_Research/csem-Masters_dissertation/chapters/05_coupled_fluid_walls_model.tex`, `UTexas_Research/csem-Masters_dissertation/chapters/06_closure_admission_uncertainty.tex`, papers status/journal files. | Main body: MF-01, MF-02, MF-04. Conditional/future: MF-03, MF-05, MF-06. |
| `csem-litrev-results-limits-futurework-2026-07-21` | Writer / Reviewer | Use LitRev rules to interpret current diagnostic pressure/thermal evidence and future work. | `UTexas_Research/csem-Masters_dissertation/chapters/07_reduced_cfd_evidence.tex`, `UTexas_Research/csem-Masters_dissertation/chapters/08_predictive_model_assessment.tex`, `UTexas_Research/csem-Masters_dissertation/chapters/09_implications_conclusions_future_work.tex`, papers status/journal files. | No final predictive score, no closure admission, no SAM validation. |
| `csem-litrev-appendix-ledger-refresh-2026-07-21` | Writer / Reviewer | Refresh appendix claim/source tables only for new LitRev incorporation claims not already covered by CL-01..CL-26. | `UTexas_Research/csem-Masters_dissertation/chapters/appendix_claim_ledger.tex`, optional appendix/source table files, papers status/journal files. | Optional; skip if chapter edits can cite existing claim IDs plus this package. |
| `csem-litrev-integration-review-build-2026-07-21` | Reviewer | Review the integrated CSEM dissertation for guardrail violations and buildability. | `UTexas_Research/csem-Masters_dissertation/**` read-only except papers status/journal files. | Run targeted `rg` checks and `latexmk` if available. |

## Review Checks For Final Row

- `rg -n "experimental validation|component K|component_K|negative K|global multiplier|internal Nu|SAM validation" UTExas_Research/csem-Masters_dissertation/chapters`
- `rg -n "source envelope|pressure basis|velocity basis|hydrostatic|kinetic|recovery|same-QOI|MF-01|MF-02|MF-04" UTExas_Research/csem-Masters_dissertation/chapters`
- `latexmk -pdf -interaction=nonstopmode -halt-on-error masterthesis.tex` from `UTexas_Research/csem-Masters_dissertation` if TeX is available.

## Required Guardrails

- CFD remains high-fidelity reference evidence, not experimental validation.
- LitRev does not admit new TAMU closures.
- Current corner pressure rows remain diagnostic unless future pressure gates pass.
- Runtime-forbidden CFD target outputs remain forbidden.
- SAM/CSEM relevance is methodological transfer, not SAM validation.
