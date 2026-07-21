---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_litrev_csem_incorporation/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_litrev_csem_incorporation/chapter_incorporation_matrix.csv
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_litrev_csem_incorporation/source_envelope_thesis_table.csv
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_litrev_csem_incorporation/pressure_corner_thesis_rules.csv
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_litrev_csem_incorporation/model_form_thesis_ladder.csv
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_litrev_csem_incorporation/latex_insertion_manifest.csv
  - reports/thesis_dossier/Chapters_and_sections/current/14_csem_narrative_integration_plan.md
  - ../papers/UTexas_Research/csem-Masters_dissertation/README.txt
tags: [thesis-section, current-section, litrev, csem-thesis, source-envelope, pressure-corner, model-form-ladder]
related:
  - operational_notes/07-26/21/2026-07-21_THESIS_LITREV_CSEM_INCORPORATION_START_HERE.md
  - reports/thesis_dossier/Chapters_and_sections/current/14_csem_narrative_integration_plan.md
task: TODO-THESIS-LITREV-CSEM-INCORPORATION-PACKAGE-2026-07-21
date: 2026-07-21
role: Coordinator/Writer/Reviewer
type: thesis-section
status: current-draft
---
# LitRev CSEM Thesis Incorporation

## Purpose

This note is the bridge from the new LitRev extraction to the external CSEM
master's dissertation scaffold at
`../papers/UTexas_Research/csem-Masters_dissertation/`. It is not a manuscript
edit. It is the decision-complete routing package for future writers.

The core thesis use is:

1. source-envelope discipline for the background/literature chapter;
2. pressure-basis and coefficient-naming discipline for the CFD-to-1D reduction
   and closure-admission chapters;
3. an MF-01 to MF-06 model-form hierarchy for the coupled `fluid+walls` and
   predictive-assessment chapters;
4. heat-loss resistance-network separation for the thermal model;
5. future-work trigger conditions for transient and ROM paths.

## Chapter Placement

| CSEM chapter | LitRev addition | Source table | Write status |
| --- | --- | --- | --- |
| Ch. 2 Background and Literature Review | Source-envelope table; safe/unsafe wording for `64/Re`, developed `Nu`, K, and heat-loss terms. | `source_envelope_thesis_table.csv` | Ready for manuscript task. |
| Ch. 4 CFD-to-1D Reduction | Pressure/thermal postprocessing contract; pressure-corner basis rules. | `pressure_corner_thesis_rules.csv`; `latex_insertion_manifest.csv` | Ready for manuscript task. |
| Ch. 5 Coupled Fluid-and-wall Model | MF-01 through MF-06 hierarchy; main-body emphasis on MF-01, MF-02, and MF-04. | `model_form_thesis_ladder.csv` | Ready for manuscript task. |
| Ch. 6 Closure Admission and Uncertainty | No-silent-threshold rule; source envelope, runtime legality, same-QOI UQ, and naming gates. | `chapter_incorporation_matrix.csv` | Ready for manuscript task. |
| Ch. 7 Reduced CFD Evidence | Interpret current pressure and thermal rows as diagnostic, negative, or blocked according to LitRev gates. | `pressure_corner_thesis_rules.csv` | Ready for manuscript task. |
| Ch. 8 Predictive Model Assessment | Use the model-form ladder as the assessment structure, but do not claim final frozen scores until a frozen candidate exists. | `model_form_thesis_ladder.csv` | Ready for manuscript task. |
| Ch. 9 Implications/Future Work | Park MF-05 transient fitting loss and MF-06 CFD/POD/ROM; list same-QOI UQ, pressure instrumentation, switching calibration, and SAM implementation as future work. | `model_form_thesis_ladder.csv` | Ready for manuscript task. |

## Thesis-Safe Claims

- A source-supported equation is not automatically a source-supported TAMU
  closure.
- Fully developed `64/Re` and fully developed `Nu` are reference limits unless
  branch-specific gates support active use.
- A pressure increase around a corner is not by itself negative loss, negative
  dissipation, or an admitted negative component `K`.
- Component `K` requires component isolation and recovery diagnostics. Otherwise
  the allowed names are `K_section`, `K_cluster`, `section_effective`, or
  `diagnostic_residual`.
- Internal `Nu` must not absorb wall conduction, external convection,
  radiation, jacket/cooler removal, storage, source-placement error, or heat
  residual.
- Literature thresholds for `F_A`, `F_m`, `Ri`, `Gz`, stratification, or
  recovery are diagnostics until TAMU calibration establishes tolerances.
- CFD is the present high-fidelity reference, not experimental validation.
- SAM/CSEM relevance is transfer of closure discipline, not SAM validation.

## Board-Aware Implementation Sequence

The Ethan board already has completed CSEM current-section drafts for several
chapters and open rows for the remaining CH1/CH8 and trigger-gated refreshes.
The actual external dissertation should be edited through the papers board with
non-overlapping rows:

1. `csem-litrev-background-source-envelope-2026-07-21`
2. `csem-litrev-reduction-pressure-contract-2026-07-21`
3. `csem-litrev-model-form-admission-2026-07-21`
4. `csem-litrev-results-limits-futurework-2026-07-21`
5. `csem-litrev-appendix-ledger-refresh-2026-07-21`
6. `csem-litrev-integration-review-build-2026-07-21`

Each row should cite this package, edit only its assigned external CSEM files,
and leave a papers-workspace status/journal entry. The final review row should
run targeted `rg` checks and, if TeX is available, build `masterthesis.tex`.

## Do Not Do

- Do not edit `../papers/**` from an Ethan task row.
- Do not add numeric LitRev coefficients to the CSEM thesis unless source
  envelope, geometry, basis, and admission evidence are present.
- Do not use held-out or external CFD rows for fitting/model selection.
- Do not relax runtime-forbidden fields such as CFD `mdot`, realized
  `wallHeatFlux`, imposed CFD cooler duty, pressure loss from the scored row,
  or validation temperatures.
