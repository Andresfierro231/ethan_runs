# Tomorrow Presentation Package

Date: `2026-07-08`
Task: `AGENT-219`
Role: Coordinator / Implementer / Writer

## Objective

Expand the July 8 presentation story into a usable slide script with slide
titles, bullet points, figure calls, and speaker notes. Identify missing or
high-value figures, then create the figures that can be made from existing
evidence with a reusable script.

## Files Changed

- `.agent/BOARD.md`
- `.agent/status/2026-07-08_AGENT-219.md`
- `.agent/journal/2026-07-08/tomorrow-presentation-package.md`
- `tools/analyze/build_tomorrow_presentation_package.py`
- `tools/analyze/test_tomorrow_presentation_package.py`
- `work_products/2026-07/2026-07-08/2026-07-08_tomorrow_presentation_package/**`

## Inputs Used

- `work_products/2026-07-08_postprocessor_summary_charts/presentation_story.md`
- `work_products/2026-07-08_postprocessor_summary_charts/figures/*.svg`
- `work_products/2026-07-08_minor_loss_two_tap/minor_loss_two_tap.csv`
- `work_products/2026-07-08_minor_loss_separation/minor_loss_separation.csv`
- `work_products/2026-07-08_cfd_informed_fixed_mdot_1d_runs/path_summary.csv`
- `work_products/2026-07-08_cfd_informed_fixed_mdot_1d_runs/README.md`
- `operational_notes/07-26/08/2026-07-08_t13_run_campaign_proposal.md`
- `.agent/BOARD.md`

## Outputs

Presentation package:

- `work_products/2026-07/2026-07-08/2026-07-08_tomorrow_presentation_package/README.md`
- `work_products/2026-07/2026-07-08/2026-07-08_tomorrow_presentation_package/slide_outline_with_speaker_notes.md`
- `work_products/2026-07/2026-07-08/2026-07-08_tomorrow_presentation_package/missing_and_nice_to_have_figures.md`
- `work_products/2026-07/2026-07-08/2026-07-08_tomorrow_presentation_package/figure_manifest.csv`
- `work_products/2026-07/2026-07-08/2026-07-08_tomorrow_presentation_package/source_inventory.csv`
- `work_products/2026-07/2026-07-08/2026-07-08_tomorrow_presentation_package/summary.json`

Created figures:

- `figures/minor_loss_k_apparent_vs_local.svg`
- `figures/minor_loss_separation_phi.svg`
- `figures/fixed_mdot_thermal_replay_error.svg`
- `figures/t13_re_sweep_plan.svg`

Generated tables:

- `tables/minor_loss_k_summary.csv`
- `tables/minor_loss_separation_summary.csv`
- `tables/thermal_replay_summary.csv`
- `tables/thermal_replay_path_labels.csv`
- `tables/t13_re_sweep_plan.csv`

## Observed Facts

- The base postprocessor chart package already contains the main story figures:
  pressure decomposition, heat accounting, heat residuals, friction-form mdot
  error, per-leg pressure drop, F5/Ri screen, upcomer backflow, and corrected
  Salt gate status.
- `minor_loss_two_tap.csv` contains four preserved corner features for Salt
  2/3/4 and distinguishes `K_apparent` from `K_local`; test-section complex
  remains unavailable from preserved rows.
- `minor_loss_separation.csv` supports a main-pipe comparison of `phi_original`
  versus `phi_pipe_only`; upcomer rows are excluded from the presentation figure
  because recirculation invalidates ordinary friction interpretation.
- `path_summary.csv` from AGENT-211 contains seven fixed-mdot thermal replay
  paths. P1, CFD cooler duty only, is the strongest single thermal correction,
  but no path passes the strict thermal gate.
- The T13 campaign proposal provides a Q-to-Re planning table from Salt 3 anchor
  to proposed high-Q runs. These rows are planned CFD, not admitted evidence.

## Inferred Interpretation

The presentation should lead with the evidence discipline, not with a closure
victory claim. The clean narrative is:

1. CFD evidence has been reduced into traceable pressure, heat, and regime
   ledgers.
2. These ledgers show why mass flow alone is insufficient for a predictive 1D
   model.
3. The most immediate 1D thermal mismatch is cooler/HX heat removal.
4. F3 Shah remains the current mdot baseline, but pressure distribution,
   thermal state, minor losses, and upcomer regime all require separate scoring.
5. Mesh/GCI, time-window uncertainty, corrected Salt admission, raw two-tap
   features, and development analysis are the next rigor gates.

## Missing Or Nice-To-Have Figures

Created in this task:

- Minor-loss apparent versus corrected/local K.
- Main-pipe phi before/after corner attribution.
- Fixed-mdot thermal replay error by path.
- T13 Q-to-Re planning curve.

Still missing before stronger claims:

- Mesh/GCI uncertainty chart.
- Time-window uncertainty chart.
- Raw two-tap reducer/junction/test-section-complex chart.
- Station-resolved development chart.
- Detailed upcomer invalidity chart with backflow, reverse momentum,
  wrong-sign area, pressure recovery, and total-pressure monotonicity.

## Validation

- `python -m py_compile tools/analyze/build_tomorrow_presentation_package.py tools/analyze/test_tomorrow_presentation_package.py`: passed.
- `python tools/analyze/build_tomorrow_presentation_package.py`: generated the target package.
- `python -m pytest tools/analyze/test_tomorrow_presentation_package.py -q`: `3 passed in 0.35s`.

## Recommended Next Action

Assemble the tomorrow deck from
`work_products/2026-07/2026-07-08/2026-07-08_tomorrow_presentation_package/slide_outline_with_speaker_notes.md`.
Use the original postprocessor figures as the core deck and the four new
figures as support/backup slides. Do not add mesh/GCI or time-window uncertainty
figures until those packages exist.
