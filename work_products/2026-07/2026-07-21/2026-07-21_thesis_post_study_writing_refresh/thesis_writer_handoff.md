---
provenance:
  - reports/thesis_dossier/Chapters_and_sections/current/14_csem_narrative_integration_plan.md
  - reports/thesis_dossier/Chapters_and_sections/current/18_ch6_csem_closure_admission_uncertainty.md
  - reports/thesis_dossier/Chapters_and_sections/current/19_ch7_csem_pressure_thermal_predictive_results.md
  - reports/thesis_dossier/Chapters_and_sections/current/21_csem_figure_table_incorporation_package.md
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_post_study_writing_refresh/thesis_artifact_priority_queue.csv
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_post_study_writing_refresh/analysis_explanation_gap_register.csv
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_post_study_writing_refresh/figure_table_polish_backlog.csv
tags: [thesis, writer-handoff, csem, figure-table, explanation-gaps]
related:
  - reports/thesis_dossier/Chapters_and_sections/current/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_csem_current_draft_packet/README.md
task: TODO-THESIS-POST-STUDY-WRITING-REFRESH-2026-07-21
date: 2026-07-21
role: Writer/Reviewer
type: work_product
status: complete
supersedes: []
superseded_by:
---
# Thesis Writer Handoff: Best Next Work

## Purpose

This handoff tells the LaTeX thesis writer what to import next from
`ethan_runs`, where the story still needs explanation, and which tables or
figures need polish before they become main-text material. It uses existing
evidence only. It does not admit closures, launch postprocessing, score a
final predictive model, or edit the dissertation repository.

## Chapter 3: CFD Evidence Database

Use the Salt-family and matched Salt2 CFD figures from the 3D paper package as
the evidence base. The point is that the CFD shows structured heat and pressure
redistribution that motivates local 1D ledgers. The writer should not present
these figures as experimental validation or as blanket admission of local HTC,
friction, or component-K coefficients.

Main writer action: import the CFD evidence/database prose from
`reports/thesis_dossier/Chapters_and_sections/current/16_ch3_csem_cfd_evidence_database.md`
and use the figure/table routing in
`reports/thesis_dossier/Chapters_and_sections/current/21_csem_figure_table_incorporation_package.md`.

Caption rule: every quantitative CFD figure should say "CFD diagnostic
evidence" or equivalent wording when the figure is used to motivate a reduced
model term.

## Chapter 5: `fluid+walls` Model And Upcomer Form

The chapter should present the steady `fluid+walls` model as a ledgered model
form: each pressure, heat, recirculation, and uncertainty slot can exist before
it is admitted as a predictive coefficient. This is the right place for the
runtime-input contract and the upcomer hybrid model form.

Use the matched Salt1-Salt4 upcomer velocity composite as the main visual
bridge from CFD to model form:

- `work_products/2026-07/2026-07-21/2026-07-21_velocity_magnitude_pictures/figures/velocity_magnitude_side_z_composite_labeled.png`
- `work_products/2026-07/2026-07-21/2026-07-21_velocity_magnitude_pictures/velocity_magnitude_side_z_thesis_analysis.md`

The explanation should say that the upcomer field is not a single uniform
upward pipe stream. It contains asymmetric high-speed paths and downward or
weak-flow regions that make ordinary single-stream `Nu`, `f_D`, and `K`
language unsafe in recirculating rows. The defensible model-form direction is
a throughflow lane plus a recirculation/exchange lane, but the exchange-cell
coefficients are still blocked until same-window exchange QOIs and UQ exist.

## Chapter 6: Admission, Split, And Uncertainty

The strongest methods contribution is the admission discipline. Use Ch. 6 to
show that the project does not turn every CFD diagnostic into a closure.

Must-use tables:

- `work_products/2026-07/2026-07-21/2026-07-21_thesis_figtable_s6_blocked_scorecard_shell/s0_s11_gate_flow_table.csv`
- `work_products/2026-07/2026-07-21/2026-07-21_thesis_figtable_s7_sensor_map_overlay/sensor_overlay_table.csv`
- `work_products/2026-07/2026-07-21/2026-07-21_thesis_figtable_s9_upcomer_exchange_evidence/exchange_qoi_figure_contract.csv`
- `work_products/2026-07/2026-07-21/2026-07-21_s13_seeded_heat_path_lane_release/heat_path_lane_table.csv`

These should become compact main-text tables. Full CSVs can move to the
appendix. The captions must preserve that TP/TW temperatures are score-only,
same-QOI UQ is still missing for admitted pressure/exchange rows, S13 is an
input scaffold rather than a harvest, and S6 contains zero final score values.

## Chapter 7: Pressure, Thermal, Upcomer, And Negative Results

The Ch. 7 sequence should be:

1. CFD redistribution motivates local ownership.
2. Junction/stub and heat-path ledgers show why segment-only ownership is not
   enough.
3. Upcomer velocity and S9/S13 show why ordinary upcomer closure is disabled.
4. S10/S14 show why pressure/F6 evidence remains diagnostic.
5. S8 and H2 show thermal candidate falsification and residual ownership.
6. The blocked scorecard is the final current result, with zero final scores.

Must-use result artifacts:

- `work_products/2026-07/2026-07-21/2026-07-21_thesis_study_s8_wall_test_section_axial_mixing_candidate/negative_or_admission_ready_summary.csv`
- `work_products/2026-07/2026-07-21/2026-07-21_thesis_figtable_s10_pressure_f6_gate_waterfall/pressure_f6_gate_waterfall.csv`
- `work_products/2026-07/2026-07-21/2026-07-21_thesis_study_s14_pressure_f6_nonrecirc_anchor_evidence/f6_branch_use_scorecard.csv`
- `work_products/2026-07/2026-07-21/2026-07-21_fluid_extbc_phase_h2_passive_heat_loss_attribution/tw5_response_waterfall.csv`
- `work_products/2026-07/2026-07-21/2026-07-21_thesis_figtable_s6_blocked_scorecard_shell/blocked_scorecard_visual_table.csv`

The thesis should explicitly treat negative results as findings. S8, S9, S10,
S12, S13, S14, and H2 narrow the physics and the allowed future work. They do
not authorize passive-wall closure, ordinary component K, F6 recorrection,
ordinary upcomer closure, or final predictive accuracy.

## Chapter 8: Limitations And Best Future Work

The next-work sequence should be written as a controlled release path:

1. Finish same-QOI UQ only for exact pressure/exchange QOIs.
2. Complete S13 production harvest after geometry/surface/sampler inputs are
   released or explicitly fail-closed.
3. Build physical-basis evidence for passive external heat loss before any
   passive `hA` repair run.
4. Pursue pressure anchors in `right_leg` and `test_section_span` before any
   F6 recorrection.
5. Run S11/S15/S6 only after exactly one runtime-legal candidate is named.

SAM/CSEM wording must stay narrow: the thesis transfers a closure-admission
discipline that is useful for systems-code coupling. It does not validate SAM.

## Immediate Polish Queue

Use `figure_table_polish_backlog.csv` as the next implementation queue. The
highest-value polish tasks are the upcomer composite caption, S6 gate-flow
diagram, S10 pressure waterfall, S14 branch-use summary, and H2 passive
heat-loss response figure/table.

## Forbidden Wording

Do not write that the current thesis has:

- final frozen predictive accuracy;
- admitted passive wall/test-section closure;
- admitted ordinary lower-right corner component `K`;
- F6 recorrection;
- admitted ordinary upcomer `Nu`, `f_D`, or `K`;
- admitted exchange-cell coefficient;
- SAM validation;
- Salt-versus-Water synthesis.
