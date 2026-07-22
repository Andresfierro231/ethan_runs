---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_study_s8_wall_test_section_axial_mixing_candidate/negative_or_admission_ready_summary.csv
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_figtable_s9_upcomer_exchange_evidence/exchange_qoi_figure_contract.csv
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_figtable_s10_pressure_f6_gate_waterfall/pressure_f6_gate_waterfall.csv
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_study_s14_pressure_f6_nonrecirc_anchor_evidence/f6_branch_use_scorecard.csv
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_extbc_phase_h2_passive_heat_loss_attribution/tw5_response_waterfall.csv
tags: [thesis, negative-results, admission, csem]
task: TODO-THESIS-MAINTEXT-WRITEUP-TABLE-POLISH-PACK-2026-07-21
date: 2026-07-21
role: Writer/Reviewer
type: work_product
status: complete
---
# Negative Results As A Thesis Contribution

The current negative results are not failed attempts to hide in an appendix.
They are the evidence that keeps the reduced model from becoming a tuned replay
of the CFD. S8, S9, S10, S13, S14, and H2 each remove a tempting shortcut and
replace it with a narrower physical requirement.

S8 shows that the current wall/test-section and axial-mixing candidate family
does not produce an S11-ready candidate. Its result is a falsification of the
available setup-only candidates, not a statement that wall physics is
irrelevant. S9 shows that the upcomer cannot be treated as an ordinary
single-stream pipe while exchange-state variables remain missing or
uncertain. S10 and S14 show that finite pressure evidence does not become an
ordinary component `K` or F6 correction when pressure basis, ordinary-flow,
component isolation, and same-QOI UQ gates fail. H2 shows that passive heat
loss is responsive, but the response is broad enough that an independent
physical basis is required before any repair.

The thesis claim is therefore methodological and scientific: the workflow
turns high-fidelity CFD evidence into a controlled admission ledger. It records
which rows can explain a residual, which rows can motivate a model-form slot,
which rows are score-only, and which rows are forbidden as predictive inputs.
The blocked scorecard is part of that result because it prevents a premature
accuracy number before a runtime-legal candidate exists.
