---
provenance:
  - .agent/BOARD.md
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_external_writer_evidence_packet_contract/README.md
  - reports/thesis_dossier/Chapters_and_sections/current/01_modeling_approach.md
  - reports/thesis_dossier/Chapters_and_sections/current/02_model_form_fluid_walls.md
  - reports/thesis_dossier/Chapters_and_sections/current/03_split_policy_and_evidence_classes.md
  - reports/thesis_dossier/Chapters_and_sections/current/08_thesis_claim_ledger.md
  - reports/thesis_dossier/Chapters_and_sections/current/14_csem_narrative_integration_plan.md
  - reports/thesis_dossier/Chapters_and_sections/current/15_ch1_csem_motivation_and_contribution.md
  - reports/thesis_dossier/Chapters_and_sections/current/16_ch3_csem_cfd_evidence_database.md
  - reports/thesis_dossier/Chapters_and_sections/current/25_litrev_csem_thesis_incorporation.md
  - ../papers/UTexas_Research/csem-Masters_dissertation/chapters/04_cfd_to_1d_reduction.tex
  - ../papers/UTexas_Research/csem-Masters_dissertation/intro_adjacent/introduction.tex
  - ../papers/UTexas_Research/3d_analysis/sections/01_introduction_and_claim.tex
  - ../papers/UTexas_Research/3d_analysis/sections/02_dataset.tex
  - ../papers/UTexas_Research/3d_analysis/sections/03_methods.tex
tags: [thesis, csem, evidence-packet, chapter-1, chapter-4, runtime-leakage]
related:
  - source_path_ledger.csv
  - equations_definitions_ledger.csv
  - claim_boundary_ledger.csv
  - figure_table_targets.csv
  - external_writer_brief.md
task: TODO-THESIS-EVIDENCE-PACKET-CH1-CH4-FOUNDATIONS-2026-07-22
date: 2026-07-22
role: Coordinator/Writer/Reviewer
type: work-product
status: current
---
# Ch1-Ch4 Foundations Evidence Packet

## Purpose

This packet gives an external thesis writer the compact evidence needed to write
Chapter 1 motivation/contribution material and Chapter 4 CFD-to-1D reduction
foundations without uploading raw CFD trees or generated figure folders. It is a
claim-control package, not a new analysis result and not a LaTeX edit.

## Target LaTeX Areas

- `../papers/UTexas_Research/csem-Masters_dissertation/intro_adjacent/introduction.tex`
- `../papers/UTexas_Research/csem-Masters_dissertation/intro_adjacent/motivation.tex`
- `../papers/UTexas_Research/csem-Masters_dissertation/chapters/04_cfd_to_1d_reduction.tex`
- Later compact appendix or evidence directory, if a papers-board task creates
  one.

## Writer Thesis Frame

The thesis should be framed as a provenance-controlled CFD-to-1D
closure/admission workflow for CSEM/SAM-relevant reduced modeling. The current
high-fidelity reference is CFD, not experiment. The contribution is the
workflow, evidence map, split discipline, model-form ladder, and negative-result
logic needed before a closure can be used predictively.

The writer may say that the CFD evidence identifies physical and reduction
failure modes that matter for 1D modeling. The writer must not say that the
current package validates SAM, validates a predictive CSEM model against
experiment, admits a final thermal or pressure closure, or reports a final
frozen predictive scorecard.

## Chapter 1 Content Ready Now

The following prose topics are ready for external writing from existing
evidence:

- Motivation: system-code and 1D models need closure discipline when used for a
  high-Prandtl-number natural-circulation molten-salt loop.
- Problem statement: CFD and 1D reduction evidence show that global correction
  factors can hide branch-specific residual owners.
- Thesis contribution: a split-aware admission workflow that keeps model slots,
  diagnostic evidence, training support, holdout tests, and external tests in
  separate roles.
- Non-claim: CFD evidence is high-fidelity reference evidence only; it is not
  experimental validation.
- SAM/CSEM relevance: the thesis contributes a CSEM-facing evidence and
  admission map that can inform SAM closure transfer, not a SAM validation.

Use `reports/thesis_dossier/Chapters_and_sections/current/15_ch1_csem_motivation_and_contribution.md`
as the safest starting prose skeleton.

## Chapter 4 Content Ready Now

The following methodology sections can be enriched immediately:

- CFD-to-1D reduction contract: each reduced quantity must carry case role,
  evidence class, pressure/thermal basis, source/property lane, uncertainty
  status, and admission state.
- Pressure lane: reduction must distinguish hydrostatic, kinetic, developing
  straight-loss, component/section/cluster, transient, and residual terms.
- Thermal lane: reduction must distinguish heater input, cooler/jacket/passive
  wall/exchange/storage owners, and residuals before fitting internal heat
  transfer.
- Split discipline: training rows, training-support perturbations, holdout
  rows, and external tests have different legal uses.
- Runtime-leakage policy: predictive runtime claims cannot use CFD mass flow,
  realized CFD wall heat flux, imposed CFD cooler duty, validation temperatures,
  row-local pressure-loss targets, holdout data, or external-test data as hidden
  inputs.
- Source/property gates: a literature equation or CFD diagnostic can populate a
  model slot before any coefficient is admitted, but slot population is not
  admission.

## Current Split Roles

Final training rows:

- `salt1_nominal`
- `salt2_jin_nominal`
- `salt3_jin_nominal`
- `salt4_nominal`

Training-support rows:

- `salt1_lo10q`
- `salt1_hi10q`
- `salt4_lo5q`
- `salt4_hi5q`

Holdout/testing rows:

- `salt2_lo5q`
- `salt2_hi5q`

External test:

- `val_salt2`, after matching heat-loss/admission package.

The Salt2 validation retained time window documented in the dossier and 3D
paper sources is `8598-8602 s`. This window is provenance for extracted
diagnostics and figures, not a predictive runtime input.

## Governing Forms To Preserve

Use the detailed ledger in `equations_definitions_ledger.csv`. The core forms
are:

```tex
\Delta p_{\mathrm{drive}}(\dot{m},T) \approx
\Delta p_{\mathrm{loss}}(\dot{m},T,\mathrm{geometry},\mathrm{closures})
```

```tex
\Delta p_{\mathrm{drive}} =
\int_{\mathrm{loop}} \rho(T(s),p(s),x) g dz(s)
```

```tex
\Delta p_{\mathrm{loss}} =
\sum_i \left[
f_i \frac{L_i}{D_i} + K_i
\right] \frac{1}{2}\rho_i V_i^2
```

```tex
\dot{m}\bar{c}_{p,i}(T_{\mathrm{out},i}-T_{\mathrm{in},i}) =
Q_{\mathrm{heater},i} - Q_{\mathrm{cooler},i} - Q_{\mathrm{passive},i}
+ Q_{\mathrm{test},i} + Q_{\mathrm{junction},i} + Q_{\mathrm{residual},i}
```

```tex
Q_{\mathrm{wall\,loss},i} =
\frac{T_{\mathrm{drive},i}-T_{\mathrm{env},i}}
{R_{\mathrm{int},i}+R_{\mathrm{wall},i}+R_{\mathrm{layer},i}+R_{\mathrm{ext},i}}
```

These equations are architecture and bookkeeping forms. They do not admit a
specific coefficient by themselves.

## Key Numbers Already Safe

- Salt2 validation retained window: `8598-8602 s`.
- Junction/stub heat-path diagnostic value cited in the thesis ledger:
  approximately `40.926087 W`.
- Pressure-basis diagnostic negative result cited in the narrative integration
  plan: PB2/PB3 temperature-shape results worsen by about `35-49 K`.
- Pressure/F6 admission snapshot from claim ledger: S14/F6 pressure path admits
  zero coefficient and should be written as non-admission.

Each number must be tied to the source-path ledger before it is moved into
LaTeX prose.

## Figure And Table Targets

The packet recommends compact figure/table targets in
`figure_table_targets.csv`. Highest-value foundations targets are:

- TAMU MSFL loop image already present in the LaTeX repo for Chapter 1 context.
- A Chapter 4 pressure reduction contract table.
- A Chapter 4 heat-ledger table separating heater, cooler/jacket, passive wall,
  test section, junction/stub, storage, exchange, and residual roles.
- A Chapter 4 runtime-leakage audit table.
- A Chapter 4 split-role table.
- A Chapter 4 source/property label table.

Do not copy heavy raw CFD outputs into the LaTeX repo for these targets.

## Allowed Claims

- The thesis studies a CFD-to-1D closure/admission workflow for CSEM-relevant
  reduced modeling.
- CFD is used as high-fidelity reference evidence.
- The target model form is a steady `fluid+walls` model with pressure and
  thermal lanes.
- Split discipline and runtime-leakage prevention are methodological
  contributions.
- Negative pressure, wall/test-section, and recirculation findings can be
  written as evidence for model-form limits and blocked admission paths.

## Forbidden Claims

- Do not claim experimental validation.
- Do not claim SAM validation.
- Do not claim a final frozen predictive 1D model or final scorecard.
- Do not claim a diagnostic CFD pressure coefficient, heat-transfer
  coefficient, recirculation metric, or wall heat flux as an admitted runtime
  closure.
- Do not use CFD `mdot`, realized `wallHeatFlux`, imposed cooler duty,
  validation temperatures, holdout rows, or external-test rows as predictive
  inputs.
- Do not turn pressure increases around corners into admitted negative-loss
  coefficients unless a future source-matched task admits them.

## What To Move To LaTeX Next

Move compact text and small ledgers, not raw data:

- A Chapter 1 contribution-boundary paragraph sourced from this README and
  `15_ch1_csem_motivation_and_contribution.md`.
- A Chapter 4 split/evidence-class subsection sourced from
  `03_split_policy_and_evidence_classes.md`.
- A Chapter 4 runtime-leakage subsection and table sourced from this packet.
- A Chapter 4 reduction contract table sourced from
  `cfd_postprocessing_contract.csv` and `equations_definitions_ledger.csv`.
- A Chapter 4 source/property gate paragraph sourced from the LitRev extraction
  packet.

## Open Questions

- Final property-correlation wording should be checked against the source
  references before the external writer tightens units or temperature basis.
- Chapter 3 should receive a separate CFD database/provenance packet before
  adding detailed case matrices to LaTeX.
- Chapters 7 and 8 should receive a separate results/negative/blocked packet
  before any final result prose is expanded.
- Figure import should wait for a papers-board row that claims exact LaTeX
  figure paths.

## Next Board Tasks

- `TODO-THESIS-LATEX-CH4-REDUCTION-SPLIT-SYNC-2026-07-22`
- `TODO-THESIS-GOVERNING-EQUATIONS-DEFINITIONS-GLOSSARY-PACKET-2026-07-22`
- `TODO-THESIS-EVIDENCE-PACKET-CH7-CH8-RESULTS-NEGATIVE-BLOCKED-2026-07-22`
- `TODO-THESIS-LATEX-COMPACT-EVIDENCE-APPENDIX-PLAN-2026-07-22`

