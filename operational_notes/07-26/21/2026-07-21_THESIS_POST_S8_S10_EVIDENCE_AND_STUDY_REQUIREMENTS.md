---
provenance:
  - .agent/BOARD.md
  - reports/thesis_dossier/Chapters_and_sections/current/18_ch6_csem_closure_admission_uncertainty.md
  - reports/thesis_dossier/Chapters_and_sections/current/19_ch7_csem_pressure_thermal_predictive_results.md
  - reports/thesis_dossier/Chapters_and_sections/current/20_ch8_csem_sam_limitations_conclusions.md
  - reports/thesis_dossier/Chapters_and_sections/current/26_predictive_model_studies_roadmap.md
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_study_s8_wall_test_section_axial_mixing_candidate/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_study_s9_upcomer_onset_anchor_exchange_uq/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_study_s10_pressure_f6_low_recirc_anchor_uq/README.md
tags: [thesis-dossier, csem, study-requirements, negative-results, writing-handoff]
related:
  - reports/thesis_dossier/README.md
  - reports/thesis_dossier/Chapters_and_sections/current/README.md
  - reports/thesis_dossier/Chapters_and_sections/current/26_predictive_model_studies_roadmap.md
task: TODO-THESIS-POST-S8-S10-EVIDENCE-REFRESH-2026-07-21
date: 2026-07-21
role: Writer/Reviewer/Coordinator
type: operational_note
status: complete
supersedes: []
superseded_by:
---
# Thesis Post-S8/S10 Evidence And Study Requirements

## Why This Avenue Exists

The thesis evidence state changed after S8, S9, and S10 completed as
negative/diagnostic studies. All three release `0` S11-ready candidates. The
next scientific work must therefore generate the missing evidence named by
those gates instead of reopening final scoring or repeating the same
candidate families.

This note is the handoff for writing and future study agents. It records what
can be written now and what must remain blocked until new evidence lands.

## Open First

1. `.agent/BOARD.md`
2. `.agent/BLOCKERS.md`
3. `reports/thesis_dossier/Chapters_and_sections/current/18_ch6_csem_closure_admission_uncertainty.md`
4. `reports/thesis_dossier/Chapters_and_sections/current/19_ch7_csem_pressure_thermal_predictive_results.md`
5. `reports/thesis_dossier/Chapters_and_sections/current/20_ch8_csem_sam_limitations_conclusions.md`
6. `reports/thesis_dossier/Chapters_and_sections/current/26_predictive_model_studies_roadmap.md`
7. `work_products/2026-07/2026-07-21/2026-07-21_thesis_study_s8_wall_test_section_axial_mixing_candidate/README.md`
8. `work_products/2026-07/2026-07-21/2026-07-21_thesis_study_s9_upcomer_onset_anchor_exchange_uq/README.md`
9. `work_products/2026-07/2026-07-21/2026-07-21_thesis_study_s10_pressure_f6_low_recirc_anchor_uq/README.md`

## Trusted Packages

| Package | Trusted use |
| --- | --- |
| S8 wall/test-section axial-mixing candidate | Negative result: current wall/test-section and axial-mixing families admit `0` candidates and release `0` S11-ready candidates. |
| S9 upcomer onset/exchange UQ | Negative/diagnostic result: ordinary upcomer closures remain disabled and exchange-QOI requirements are named. |
| S10 pressure/F6 low-recirculation anchor UQ | Negative/diagnostic result: component-K/F6 pressure claims remain unadmitted and next pressure anchors are named. |
| S6 blocked scorecard shell | Scorecard contract only; contains `0` final score values. |
| S7 sensor-map overlay | TP/TW scoring discipline only; allows `0` runtime-temperature, fit, or model-selection inputs. |

## Board Rows To Claim

| Row | Purpose |
| --- | --- |
| `TODO-THESIS-STUDY-S12-THERMAL-SHAPE-OWNERSHIP-CANDIDATE-2026-07-21` | Find or falsify a new physical owner for TW5/TW6 and wall/test-section residuals. |
| `TODO-THESIS-STUDY-S13-UPCOMER-EXCHANGE-PRODUCTION-HARVEST-UQ-2026-07-21` | Produce or fail-close production exchange QOIs and same-window UQ. |
| `TODO-THESIS-STUDY-S14-PRESSURE-F6-NONRECIRC-ANCHOR-EVIDENCE-2026-07-21` | Find or falsify nonrecirculating/low-reverse pressure anchors with same-QOI UQ. |
| `TODO-THESIS-STUDY-S15-CANDIDATE-FREEZE-SOURCE-PROPERTY-SCORE-RELEASE-2026-07-21` | Run only after exactly one candidate is released by S12, S13, or S14. |

## Next Task Sequence

1. Writing agents should integrate completed S0-S10 material as methods,
   diagnostic results, negative results, and limitations.
2. Thermal-modeling agents should claim S12 before any final-score attempt if
   the target is thermal prediction.
3. Upcomer/cfd-pp agents should claim S13 only when sampler inputs and
   same-window exchange-QOI extraction are ready to execute or fail-close.
4. Hydraulic/cfd-pp agents should claim S14 before any pressure/F6 admission
   language changes.
5. Forward-pred agents should claim S15 only after one named candidate exists.
6. S6 final scoring remains blocked unless S15 releases a frozen candidate.

## Output Contract

Each study row must publish, at minimum:

- source manifest with exact paths;
- runtime-leakage audit;
- split-role/protected-row audit where scoring is involved;
- gate matrix with admitted/diagnostic/blocked labels;
- figure/table manifest with thesis target section;
- status, journal, import manifest, and package README.

## Do-Not-Do Guardrails

- Do not invent final scores.
- Do not promote diagnostic CFD evidence to admitted predictive closure.
- Do not use CFD `mdot`, realized CFD `wallHeatFlux`, imposed cooler duty,
  realized test-section heat, validation temperatures, holdout temperatures, or
  external-test temperatures as predictive runtime inputs.
- Do not admit ordinary upcomer `Nu`, `f_D`, or `K` from current recirculating
  evidence.
- Do not admit component K, F6, clipped K, or hidden pressure multipliers from
  current pressure/F6 evidence.
- Do not call the current work SAM validation.
