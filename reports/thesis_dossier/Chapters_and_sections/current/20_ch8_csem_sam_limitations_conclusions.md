---
provenance:
  - reports/thesis_dossier/Chapters_and_sections/current/08_thesis_claim_ledger.md
  - reports/thesis_dossier/Chapters_and_sections/current/10_uncertainty_chapter_package.md
  - reports/thesis_dossier/Chapters_and_sections/current/11_sam_facing_interpretation.md
  - reports/thesis_dossier/Chapters_and_sections/current/14_csem_narrative_integration_plan.md
  - reports/thesis_dossier/Chapters_and_sections/current/18_ch6_csem_closure_admission_uncertainty.md
  - reports/thesis_dossier/Chapters_and_sections/current/19_ch7_csem_pressure_thermal_predictive_results.md
  - .agent/BLOCKERS.md
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_csem_enrichment_writing_pass/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_study_s7_sensor_map_tp_tw_contract/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_study_s8_wall_test_section_axial_mixing_candidate/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_study_s9_upcomer_onset_anchor_exchange_uq/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_study_s10_pressure_f6_low_recirc_anchor_uq/README.md
  - operational_notes/07-26/21/2026-07-21_THESIS_POST_S8_S10_EVIDENCE_AND_STUDY_REQUIREMENTS.md
  - ../papers/UTexas_Research/3d_analysis/sections/06_trust_limits_and_interpretation.tex
  - ../papers/UTexas_Research/3d_analysis/sections/07_conclusions.tex
tags: [thesis-section, current-section, csem, limitations, sam, future-work]
related:
  - reports/thesis_dossier/Chapters_and_sections/current/15_ch1_csem_motivation_and_contribution.md
  - reports/thesis_dossier/Chapters_and_sections/current/18_ch6_csem_closure_admission_uncertainty.md
  - reports/thesis_dossier/Chapters_and_sections/current/21_csem_figure_table_incorporation_package.md
task: TODO-THESIS-CH8-CSEM-SAM-LIMITATIONS-DRAFT
date: 2026-07-21
role: Writer/Reviewer
type: thesis-section
status: current-draft
supersedes: []
superseded_by:
---
# CSEM Limitations, SAM Relevance, And Conclusions

## Purpose

This section provides chapter-ready limitations and conclusion prose for the
CSEM thesis package. It states what can transfer to SAM-facing model
construction, what remains blocked, and what cannot be claimed from the current
evidence.

## Limitations Of The Current Evidence

The current thesis package supports a CFD-to-1D closure workflow, a steady
`fluid+walls` model form, a split-aware admission ledger, and several
diagnostic or negative results. It does not yet support final predictive
performance claims for a frozen model. Claim CL-24 remains bounded by the final
predictive scorecard shell: the shell defines the score contract, but final
scores wait on a frozen candidate.

The current blocker register leaves six open limits that should remain visible
in the thesis:

- wall/test-section/passive-boundary submodels remain unresolved;
- the lower-right two-tap corner lacks admissible component isolation;
- the same corner lacks same-QOI mesh/time uncertainty;
- the same corner fails the ordinary low-recirculation gate;
- upcomer recirculation onset has too few near-onset or non-recirculating
  anchors;
- F6 friction/Re recorrection remains narrowed but unadmitted.

These limitations do not invalidate the methodology. They define the boundary
between thesis-ready evidence and future closure admission. The thesis should
therefore report pressure and thermal blockers as results of the admission
process, not as missing prose.

## Pressure And Thermal Limits

Current pressure evidence is useful for model-form design and residual
attribution, but it is not an ordinary component-loss admission. Claims CL-13,
CL-16, and CL-26 keep the current corner rows diagnostic or section-effective.
The allowed conclusion is that recirculating two-tap pressure features need a
named section-effective pressure lane, same-QOI uncertainty, and better
component isolation before becoming predictive coefficients.

Current thermal evidence is stronger for separating heater, cooler/HX, passive
wall, test-section, junction, and residual roles than for admitting a complete
wall/test-section closure. Claims CL-09 through CL-12 and CL-17 through CL-18
support this distinction. The PB2/PB3 wall/test-section candidates are a
valuable negative result because they improve mass-flow behavior while
worsening TP/TW or all-probe temperature shape. They should be described as
falsification evidence, not as admitted passive-boundary models.

The S8 candidate review makes the thermal limit more explicit. Current
setup-only wall/test-section, axial-mixing, upcomer-stratification, UMX1, and
TSWFC2 candidate families produce `0` admitted candidates and `0` S11-ready
candidates. That is a completed negative result, not merely missing work. It
means the next candidate must bring a new physical ownership argument or new
later upcomer/pressure evidence before the S6 final scorecard can be thawed.

S9 and S10 now show that those adjacent evidence paths are also negative at
the current frontier. S9 releases `0` S11-ready upcomer candidates while
preserving the required exchange-QOI contract. S10 releases `0` S11-ready
pressure/F6 candidates while preserving the pressure-basis and same-QOI
requirements. The limitation is therefore sharper than "more model work is
needed": the next thesis evidence must either introduce a new physical
thermal-shape owner, produce missing upcomer exchange QOIs with uncertainty,
or supply nonrecirculating/low-reverse pressure anchors.

## SAM And CSEM Relevance

The SAM-facing implication is transfer of closure discipline. The thesis
identifies the information that should travel with a systems-code component:
branch label, source path, split role, runtime legality, pressure basis,
thermal role, recirculation status, property lane, uncertainty status, and
admission decision.

That transfer matters because a systems code can reproduce the same failure
modes as a custom 1D model if it collapses pressure and heat evidence into
undocumented multipliers. The CSEM workflow developed here argues for local
ownership:

- branchwise pressure losses instead of one global hydraulic correction;
- junction/stub and connector heat roles instead of one total heat-leak term;
- separate heater, cooler, passive wall, radiation, and test-section lanes;
- explicit recirculation flags before ordinary pipe correlations are applied;
- holdout and external rows reserved for scoring rather than tuning.

The thesis should not claim SAM validation, SAM calibration, or experimental
confirmation. No SAM model, frozen SAM input deck, SAM scorecard, or independent
experimental comparison is part of the current evidence base.

## Thesis Completion Path From Current Evidence

The thesis can be completed coherently even if the final predictive model
remains blocked at the deadline. The current evidence supports these completed
deliverables:

| Deliverable | Current evidence status |
| --- | --- |
| CFD evidence database | Ready as high-fidelity reference and diagnostic reduction layer. |
| `fluid+walls` model architecture | Ready as segment-local pressure/thermal/wall/source/recirculation interface. |
| Runtime and split discipline | Ready as methods contribution and release guard. |
| Heat-loss accounting | Ready as residual-owner evidence; wall/test-section closure remains blocked. |
| Pressure source-envelope result | Ready as diagnostic non-admission and next-evidence path. |
| Recirculation validity boundary | Ready as ordinary-closure exclusion and S9 exchange-QOI release gate. |
| Source/property split release | Ready as a blocked release gate with `0` fit/model-selection rows released. |
| TP/TW sensor-map discipline | Ready as score-only sensor mapping with `0` runtime-temperature, fit, or model-selection permissions. |
| Wall/test-section candidate falsification | Ready as S8 negative result with `0` admitted or S11-ready candidates. |
| Upcomer exchange candidate review | Ready as S9 negative result with `0` exchange-cell admissions and `0` S11-ready candidates. |
| Pressure/F6 candidate review | Ready as S10 negative result with `0` component-K/F6 admissions and `0` S11-ready candidates. |
| Final scorecard shell | Ready as contract; final scores remain trigger-gated. |

This path lets the conclusion stay positive without overstating the endpoint:
the thesis delivers a vetted route to prediction and documents exactly why
some terms are not yet predictive.

## Future Work

The next scientific work should follow the blocker frontier rather than open a
new tuning lane. S7 through S10 are complete: TP/TW sensors are score-only
evidence, the current wall/test-section candidate families produced no
S11-ready candidate, the upcomer exchange review produced no S11-ready
candidate, and the pressure/F6 review produced no S11-ready candidate. The
priority sequence is now:

1. run S12 thermal-shape ownership discovery only with a new physical owner for
   TW5/TW6 and wall/test-section residuals;
2. run S13 upcomer exchange production harvest/UQ only after sampler inputs are
   production-ready, including recirculation-region band definition, exchange
   surfaces, finite same-window QOIs, and UQ;
3. run S14 pressure/F6 nonrecirculating-anchor evidence before changing
   pressure-admission language, with `CAND-001` terminal refresh and ordinary
   RAF/RMF gates called out explicitly;
4. run S15 only if S12, S13, or S14 releases exactly one named candidate with
   legal runtime inputs and source/property labels;
5. reopen S11/S6 only after S15 permits candidate-specific source/property
   release and score-freeze handling.

The immediate writing follow-up is figure/table incorporation, not another
broad literature or CFD sweep. Completed S0-S10 evidence can be written as
methods, diagnostic results, negative results, and limitations. Final-score,
pressure-admission, upcomer-exchange, and wall/test-section closure claims
remain trigger-gated.

External dissertation editing and SAM implementation should be opened as
separate board rows in the appropriate workspace. The current `ethan_runs`
package is the evidence and thesis-dossier source, not the final manuscript
repository.

## Conclusion

The defensible conclusion is that the TAMU molten-salt loop requires a
provenance-controlled, branchwise CFD-to-1D closure workflow. The current CFD
and LitRev evidence justify the `fluid+walls` model structure, the split and
runtime-input policy, the pressure and thermal admission gates, and the
SAM-facing transfer of closure metadata. They also show where ordinary
coefficient language is unsafe: recirculating corner pressure, upcomer
single-stream closures, and passive wall/test-section heat distribution remain
blocked or diagnostic.

The contribution is therefore not a final universal correlation. It is a
thesis-ready method for deciding which reduced-order terms are admissible,
which are diagnostic, which are score-only, and which require more evidence
before they can be used predictively.
