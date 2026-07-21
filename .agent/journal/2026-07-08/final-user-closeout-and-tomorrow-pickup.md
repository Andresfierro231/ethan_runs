# Final User Closeout And Tomorrow Pickup

Date: `2026-07-08`
Task: `AGENT-221`
Role: Coordinator / Writer

## Objective

The user is closing for the day and asked that the presentation work, context,
and today's state be documented in today's journal for tomorrow's pickup.

## Files Changed

- `.agent/BOARD.md`
- `.agent/status/2026-07-08_AGENT-221.md`
- `.agent/journal/2026-07-08/final-user-closeout-and-tomorrow-pickup.md`
- `journals/2026-07/2026-07-08_ethan_runs.md`

## Observed Facts

- `AGENT-219` completed a reusable tomorrow-presentation package:
  `work_products/2026-07/2026-07-08/2026-07-08_tomorrow_presentation_package/**`.
- The package includes:
  - `slide_outline_with_speaker_notes.md`
  - `missing_and_nice_to_have_figures.md`
  - `figure_manifest.csv`
  - `source_inventory.csv`
  - `summary.json`
  - `figures/minor_loss_k_apparent_vs_local.svg`
  - `figures/minor_loss_separation_phi.svg`
  - `figures/fixed_mdot_thermal_replay_error.svg`
  - `figures/t13_re_sweep_plan.svg`
- The reusable script is
  `tools/analyze/build_tomorrow_presentation_package.py`.
- Focused tests passed:
  `python -m pytest tools/analyze/test_tomorrow_presentation_package.py -q`
  reported `3 passed in 0.35s`.
- The intended presentation claim remains conservative: pressure, heat, and
  regime terms are decomposed with provenance and admission boundaries; final
  publication-grade closure coefficients are not yet claimed.

## Inferred Interpretation

Tomorrow's presentation should be built from the 12-slide outline and should
keep the main deck centered on:

1. evidence/admission contract;
2. pressure decomposition;
3. heat accounting;
4. thermal residuals and fixed-mdot replay;
5. friction-form screen;
6. minor-loss support evidence;
7. F5/Ri negative screen and T13 plan;
8. upcomer recirculation regime;
9. gate/uncertainty blockers and next work.

## Blockers / Work In Progress

- Mesh/GCI uncertainty remains missing.
- Time-window uncertainty remains missing.
- Corrected Salt perturbations remain status-only until formal gate admission.
- Raw two-tap reducer/junction/test-section-complex extraction remains missing.
- Station-resolved development analysis remains missing.
- Predictive heater fluid-entry and cooler-removal models remain future work.
- Overnight rigor-study submission was blocked by allocation/SU encumbrance;
  tomorrow should monitor existing jobs/gates before launching replacements.

## Recommended Tomorrow Pickup

1. Open
   `work_products/2026-07/2026-07-08/2026-07-08_tomorrow_presentation_package/slide_outline_with_speaker_notes.md`.
2. Use the original postprocessor figures as the core deck and the four new
   AGENT-219 figures as support/backup.
3. Check scheduler/gate status for Salt1 nominal continuation, corrected Salt
   Q jobs, and the queued corrected-Salt gate before interpreting new rows.
4. Assign new rows only for bounded follow-ups: mesh/GCI, time-window UQ, raw
   feature two-tap extraction, station-resolved development, and predictive
   heater/cooler models.
5. Preserve the claim boundary: tomorrow is ready for a decomposed-evidence
   presentation, not a final closure-law announcement.

## Validation

This AGENT-221 task was documentation-only. No numerical scripts or tests were
run for this closeout.
